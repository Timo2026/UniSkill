#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 技能源适配器
从 GitHub 搜索和安装开源技能项目
"""

import json
import os
import subprocess
import sys
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

# 导入基类和schema
sys.path.insert(0, str(Path(__file__).parent.parent))
from plugins.base import SkillSourcePlugin
from schemas.skill_schema import Skill, SkillType, SkillStatus, SkillMetadata, SkillInput, SkillOutput
from core.intent_parser import Intent


class GitHubSource(SkillSourcePlugin):
    """
    GitHub 技能源
    
    功能：
    1. 搜索 GitHub 上的技能项目
    2. 克隆并安装到本地
    3. 解析 README 和元数据
    """
    
    # GitHub API 配置
    API_BASE = "https://api.github.com"
    
    # 搜索关键词映射
    SKILL_KEYWORDS = [
        "openclaw-skill", "openclaw-plugin", "agent-skill",
        "ai-agent-tool", "llm-tool", "claude-skill"
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache" / "github"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.skills_cache_file = self.cache_dir / "skills_cache.json"
        self.skills_cache: Dict[str, Dict] = {}
        
        self.github_token = self.config.get("github_token", os.environ.get("GITHUB_TOKEN", ""))
        self.enabled = self.config.get("enabled", False)  # 默认关闭
    
    @property
    def name(self) -> str:
        return "github"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "GitHub开源技能适配器"
    
    def initialize(self) -> bool:
        """初始化"""
        self._load_cache()
        self._initialized = True
        print(f"[GitHubSource] 初始化完成，缓存 {len(self.skills_cache)} 个项目")
        return True
    
    def _load_cache(self):
        """加载缓存"""
        if self.skills_cache_file.exists():
            try:
                with open(self.skills_cache_file, 'r', encoding='utf-8') as f:
                    self.skills_cache = json.load(f)
            except:
                self.skills_cache = {}
    
    def _save_cache(self):
        """保存缓存"""
        with open(self.skills_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.skills_cache, f, ensure_ascii=False, indent=2)
    
    def find(self, intent: Intent, top_k: int = 5) -> List[tuple]:
        """
        从 GitHub 搜索技能
        
        Args:
            intent: 意图对象
            top_k: 返回数量
            
        Returns:
            [(Skill, score)] 列表
        """
        if not self.enabled:
            return []
        
        results = []
        
        # 1. 搜索缓存
        cache_results = self._search_cache(intent.keywords)
        for repo_data in cache_results[:top_k]:
            skill = self._repo_to_skill(repo_data)
            score = self._calculate_score(skill, intent)
            results.append((skill, score))
        
        # 2. 在线搜索
        try:
            online_results = self._search_github(intent.keywords)
            for repo_data in online_results[:top_k]:
                # 添加到缓存
                full_name = repo_data.get("full_name", repo_data.get("id"))
                self.skills_cache[full_name] = repo_data
                
                skill = self._repo_to_skill(repo_data)
                score = self._calculate_score(skill, intent)
                
                if not any(s.id == skill.id for s, _ in results):
                    results.append((skill, score))
        except Exception as e:
            print(f"[GitHubSource] 在线搜索失败: {e}")
        
        self._save_cache()
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _search_cache(self, keywords: List[str]) -> List[Dict]:
        """搜索缓存"""
        results = []
        keywords_lower = [k.lower() for k in keywords]
        
        for repo_full_name, repo_data in self.skills_cache.items():
            name = repo_data.get("name", "").lower()
            desc = repo_data.get("description", "") or ""
            topics = repo_data.get("topics", [])
            
            match_score = 0
            for kw in keywords_lower:
                if kw in name:
                    match_score += 2
                if kw in desc.lower():
                    match_score += 1
                if any(kw in t.lower() for t in topics):
                    match_score += 1.5
            
            if match_score > 0:
                results.append({**repo_data, "_match_score": match_score})
        
        results.sort(key=lambda x: x.get("_match_score", 0), reverse=True)
        return results
    
    def _search_github(self, keywords: List[str]) -> List[Dict]:
        """
        搜索 GitHub
        
        使用 GitHub API 或 web_fetch
        """
        try:
            import requests
            
            # 构建搜索查询
            skill_query = " OR ".join(self.SKILL_KEYWORDS[:3])
            keyword_query = " ".join(keywords[:3])
            query = f"{skill_query} {keyword_query}"
            
            url = f"{self.API_BASE}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 10
            }
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            else:
                print(f"[GitHubSource] API错误: {response.status_code}")
                return []
                
        except ImportError:
            # requests 不可用
            return self._get_mock_results()
        except Exception as e:
            print(f"[GitHubSource] 搜索异常: {e}")
            return self._get_mock_results()
    
    def _get_mock_results(self) -> List[Dict]:
        """获取模拟结果"""
        return [
            {
                "full_name": "openclaw/awesome-skills",
                "name": "awesome-skills",
                "description": "精选OpenClaw技能集合",
                "html_url": "https://github.com/openclaw/awesome-skills",
                "stargazers_count": 256,
                "topics": ["openclaw", "skills", "ai-agent"],
                "language": "Python"
            },
            {
                "full_name": "openclaw/cnc-skill-pack",
                "name": "cnc-skill-pack",
                "description": "CNC制造领域技能包",
                "html_url": "https://github.com/openclaw/cnc-skill-pack",
                "stargazers_count": 128,
                "topics": ["cnc", "manufacturing", "openclaw"],
                "language": "Python"
            }
        ]
    
    def _repo_to_skill(self, repo_data: Dict) -> Skill:
        """将仓库数据转换为Skill对象"""
        full_name = repo_data.get("full_name", repo_data.get("id", "unknown"))
        
        return Skill(
            id=f"github:{full_name}",
            name=repo_data.get("name", "Unknown"),
            description=repo_data.get("description", "") or "",
            skill_type=self._infer_skill_type(repo_data),
            inputs=[],
            outputs=[],
            metadata=SkillMetadata(
                author=repo_data.get("owner", {}).get("login", ""),
                version="latest",
                homepage=repo_data.get("html_url", ""),
                repository=repo_data.get("html_url", ""),
                tags=repo_data.get("topics", [])
            ),
            source="github",
            source_url=repo_data.get("html_url", ""),
            status=SkillStatus.AVAILABLE,
            keywords=repo_data.get("topics", []) + [repo_data.get("name", "")]
        )
    
    def _infer_skill_type(self, repo_data: Dict) -> SkillType:
        """推断技能类型"""
        topics = [t.lower() for t in repo_data.get("topics", [])]
        desc = (repo_data.get("description") or "").lower()
        
        if any(t in topics for t in ["generator", "tool", "cli"]):
            return SkillType.UTILITY
        elif any(t in topics for t in ["api", "connector", "integration"]):
            return SkillType.CONNECTOR
        elif any(t in topics for t in ["analyzer", "analysis"]):
            return SkillType.ANALYZER
        else:
            return SkillType.UTILITY
    
    def _calculate_score(self, skill: Skill, intent: Intent) -> float:
        """计算匹配分数"""
        score = 0.0
        
        # 关键词匹配
        skill_keywords = set(k.lower() for k in skill.keywords)
        intent_keywords = set(k.lower() for k in intent.keywords)
        
        if skill_keywords and intent_keywords:
            overlap = len(skill_keywords & intent_keywords)
            score += min(overlap * 0.15, 0.4)
        
        # 星标加权
        stars = skill.metadata.tags.count("stars") if hasattr(skill.metadata, 'tags') else 0
        score += min(stars / 1000, 0.2)
        
        return min(score, 1.0)
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """获取指定技能"""
        if skill_id.startswith("github:"):
            full_name = skill_id[7:]
            if full_name in self.skills_cache:
                return self._repo_to_skill(self.skills_cache[full_name])
        return None
    
    def install(self, skill_id: str) -> bool:
        """
        安装技能（克隆仓库）
        
        Args:
            skill_id: 格式为 "github:owner/repo"
        """
        if not skill_id.startswith("github:"):
            return False
        
        full_name = skill_id[7:]
        
        if full_name not in self.skills_cache:
            print(f"[GitHubSource] 仓库不存在: {full_name}")
            return False
        
        repo_data = self.skills_cache[full_name]
        repo_url = repo_data.get("html_url", "") or repo_data.get("clone_url", "")
        
        if not repo_url:
            return False
        
        try:
            skills_dir = Path.home() / ".openclaw" / "workspace" / "skills"
            target_dir = skills_dir / repo_data.get("name", full_name.split("/")[-1])
            
            # 克隆仓库
            cmd = ["git", "clone", repo_url, str(target_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"[GitHubSource] 克隆成功: {full_name}")
                self.skills_cache[full_name]["status"] = "installed"
                self.skills_cache[full_name]["local_path"] = str(target_dir)
                self._save_cache()
                return True
            else:
                print(f"[GitHubSource] 克隆失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[GitHubSource] 克隆超时: {full_name}")
            return False
        except Exception as e:
            print(f"[GitHubSource] 安装异常: {e}")
            return False
    
    def list_available(self, keyword: str = "", page: int = 1, size: int = 20) -> List[Skill]:
        """列出可用技能"""
        results = []
        for repo_data in self.skills_cache.values():
            if not keyword or keyword.lower() in repo_data.get("name", "").lower():
                results.append(self._repo_to_skill(repo_data))
        
        return results[(page-1)*size : page*size]


# 导出
__all__ = ['GitHubSource']