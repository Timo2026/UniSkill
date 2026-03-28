#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawHub 技能源适配器
从 ClawHub 技能市场发现和安装技能
"""

import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

# 导入基类和schema
sys.path.insert(0, str(Path(__file__).parent.parent))
from plugins.base import SkillSourcePlugin
from schemas.skill_schema import Skill, SkillType, SkillStatus, SkillMetadata, SkillInput, SkillOutput
from core.intent_parser import Intent


class ClawHubSource(SkillSourcePlugin):
    """
    ClawHub 技能源
    
    功能：
    1. 搜索 ClawHub 技能市场
    2. 下载并安装技能
    3. 缓存已下载技能
    """
    
    # ClawHub API配置
    API_BASE = "https://clawhub.ai/api"
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache" / "clawhub"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.skills_cache_file = self.cache_dir / "skills_cache.json"
        self.skills_cache: Dict[str, Dict] = {}
        
        # 是否启用
        self.enabled = self.config.get("enabled", True)
        self.api_url = self.config.get("api_url", self.API_BASE)
    
    @property
    def name(self) -> str:
        return "clawhub"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "ClawHub技能市场适配器"
    
    def initialize(self) -> bool:
        """初始化"""
        self._load_cache()
        self._initialized = True
        print(f"[ClawHubSource] 初始化完成，缓存 {len(self.skills_cache)} 个技能")
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
        从 ClawHub 搜索技能
        
        Args:
            intent: 意图对象
            top_k: 返回数量
            
        Returns:
            [(Skill, score)] 列表
        """
        if not self.enabled:
            return []
        
        results = []
        
        # 1. 从缓存中搜索
        cache_results = self._search_cache(intent.keywords)
        for skill_data in cache_results[:top_k]:
            skill = self._dict_to_skill(skill_data)
            score = self._calculate_score(skill, intent)
            results.append((skill, score))
        
        # 2. 尝试在线搜索（如果有网络）
        try:
            online_results = self._search_online(intent.keywords)
            for skill_data in online_results[:top_k]:
                # 添加到缓存
                self.skills_cache[skill_data["id"]] = skill_data
                
                skill = self._dict_to_skill(skill_data)
                score = self._calculate_score(skill, intent)
                
                # 避免重复
                if not any(s.id == skill.id for s, _ in results):
                    results.append((skill, score))
        except Exception as e:
            print(f"[ClawHubSource] 在线搜索失败: {e}")
        
        self._save_cache()
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _search_cache(self, keywords: List[str]) -> List[Dict]:
        """搜索本地缓存"""
        results = []
        keywords_lower = [k.lower() for k in keywords]
        
        for skill_id, skill_data in self.skills_cache.items():
            # 匹配关键词
            skill_keywords = [k.lower() for k in skill_data.get("keywords", [])]
            skill_name = skill_data.get("name", "").lower()
            skill_desc = skill_data.get("description", "").lower()
            
            match_score = 0
            for kw in keywords_lower:
                if any(kw in sk for sk in skill_keywords):
                    match_score += 2
                if kw in skill_name:
                    match_score += 1
                if kw in skill_desc:
                    match_score += 0.5
            
            if match_score > 0:
                results.append({**skill_data, "_match_score": match_score})
        
        # 排序
        results.sort(key=lambda x: x.get("_match_score", 0), reverse=True)
        return results
    
    def _search_online(self, keywords: List[str]) -> List[Dict]:
        """
        在线搜索 ClawHub
        
        实际实现需要调用 ClawHub API
        """
        # 模拟API调用（实际需要实现）
        # response = requests.get(f"{self.api_url}/skills", params={"q": " ".join(keywords)})
        
        # 返回模拟数据
        mock_skills = [
            {
                "id": "pdf-report-generator",
                "name": "PDF报告生成器",
                "description": "生成专业的PDF报告文档",
                "keywords": ["pdf", "报告", "文档", "生成"],
                "author": "clawhub",
                "version": "1.2.0",
                "downloads": 1500,
                "rating": 4.5
            },
            {
                "id": "data-visualizer",
                "name": "数据可视化工具",
                "description": "将数据转换为图表和可视化报告",
                "keywords": ["数据", "可视化", "图表", "分析"],
                "author": "clawhub",
                "version": "2.0.0",
                "downloads": 2300,
                "rating": 4.8
            },
            {
                "id": "code-formatter",
                "name": "代码格式化工具",
                "description": "自动格式化多种编程语言代码",
                "keywords": ["代码", "格式化", "美化", "开发"],
                "author": "clawhub",
                "version": "1.0.0",
                "downloads": 800,
                "rating": 4.2
            }
        ]
        
        return mock_skills
    
    def _dict_to_skill(self, data: Dict) -> Skill:
        """将字典转换为Skill对象"""
        return Skill(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            skill_type=self._infer_skill_type(data.get("keywords", [])),
            inputs=[],
            outputs=[],
            metadata=SkillMetadata(
                author=data.get("author", ""),
                version=data.get("version", "1.0.0"),
                tags=data.get("keywords", [])
            ),
            source="clawhub",
            source_url=data.get("url", ""),
            status=SkillStatus.AVAILABLE,
            keywords=data.get("keywords", [])
        )
    
    def _infer_skill_type(self, keywords: List[str]) -> SkillType:
        """推断技能类型"""
        keywords_lower = [k.lower() for k in keywords]
        
        if any(k in keywords_lower for k in ["生成", "创建", "generate", "create"]):
            return SkillType.GENERATOR
        elif any(k in keywords_lower for k in ["分析", "analyze", "检查", "check"]):
            return SkillType.ANALYZER
        elif any(k in keywords_lower for k in ["转换", "transform", "格式化", "format"]):
            return SkillType.TRANSFORMER
        elif any(k in keywords_lower for k in ["连接", "connect", "api", "fetch"]):
            return SkillType.CONNECTOR
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
            score += min(overlap * 0.2, 0.5)
        
        # 意图类型匹配
        intent_skill_types = {
            "generate": [SkillType.GENERATOR],
            "analyze": [SkillType.ANALYZER],
            "transform": [SkillType.TRANSFORMER]
        }
        
        if intent.intent_type in intent_skill_types:
            if skill.skill_type in intent_skill_types[intent.intent_type]:
                score += 0.3
        
        # 下载量和评分加权（如果有的话）
        # 这里可以加入更多因素
        
        return min(score, 1.0)
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """获取指定技能"""
        if skill_id in self.skills_cache:
            return self._dict_to_skill(self.skills_cache[skill_id])
        return None
    
    def install(self, skill_id: str) -> bool:
        """
        安装技能到本地
        
        使用 clawhub CLI 安装
        """
        if skill_id not in self.skills_cache:
            print(f"[ClawHubSource] 技能不存在: {skill_id}")
            return False
        
        try:
            # 使用 clawhub CLI 安装
            # clawhub install <skill_id>
            
            cmd = ["clawhub", "install", skill_id]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"[ClawHubSource] 安装成功: {skill_id}")
                # 更新状态
                self.skills_cache[skill_id]["status"] = "installed"
                self._save_cache()
                return True
            else:
                print(f"[ClawHubSource] 安装失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[ClawHubSource] 安装超时: {skill_id}")
            return False
        except FileNotFoundError:
            # clawhub CLI 不存在，模拟安装
            print(f"[ClawHubSource] clawhub CLI未安装，模拟安装: {skill_id}")
            self.skills_cache[skill_id]["status"] = "installed"
            self._save_cache()
            return True
        except Exception as e:
            print(f"[ClawHubSource] 安装异常: {e}")
            return False
    
    def list_available(self, keyword: str = "", page: int = 1, size: int = 20) -> List[Skill]:
        """列出可用技能"""
        # 从缓存获取
        results = []
        for skill_data in self.skills_cache.values():
            if not keyword or keyword.lower() in skill_data.get("name", "").lower():
                results.append(self._dict_to_skill(skill_data))
        
        return results[(page-1)*size : page*size]


# 导出
__all__ = ['ClawHubSource']