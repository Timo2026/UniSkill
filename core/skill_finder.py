#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能发现器 - Skill Finder
从本地和外部源发现、匹配、排序技能
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import subprocess

# 导入schema
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from schemas.skill_schema import Skill, SkillType, SkillStatus, SkillMetadata, SkillInput, SkillOutput
from core.intent_parser import Intent


class SkillFinder:
    """
    技能发现器
    
    功能：
    1. 本地索引 - 扫描并索引本地已安装的技能
    2. 技能匹配 - 根据意图匹配最合适的技能
    3. 多源聚合 - 支持从多个来源发现技能
    4. 缓存管理 - 管理下载的技能缓存
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or {}
        
        # 路径配置
        self.skills_dir = Path.home() / ".openclaw" / "workspace" / "skills"
        self.data_dir = Path(__file__).parent.parent / "data"
        self.cache_dir = self.data_dir / "cache"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 索引文件
        self.index_file = self.data_dir / "skill_index.json"
        
        # 本地索引
        self.local_index: Dict[str, Skill] = {}
        
        # 加载索引
        self._load_index()
    
    def _load_index(self):
        """加载本地索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for skill_id, skill_data in data.items():
                        self.local_index[skill_id] = Skill.from_dict(skill_data)
                print(f"[SkillFinder] 已加载 {len(self.local_index)} 个技能索引")
            except Exception as e:
                print(f"[SkillFinder] 加载索引失败: {e}")
                self.local_index = {}
    
    def _save_index(self):
        """保存本地索引"""
        try:
            data = {skill_id: skill.to_dict() for skill_id, skill in self.local_index.items()}
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SkillFinder] 保存索引失败: {e}")
    
    def rebuild_index(self) -> int:
        """
        重建本地技能索引
        
        Returns:
            索引的技能数量
        """
        print("[SkillFinder] 开始重建本地技能索引...")
        
        count = 0
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill = self._parse_skill_directory(skill_dir)
            if skill:
                self.local_index[skill.id] = skill
                count += 1
        
        self._save_index()
        print(f"[SkillFinder] 索引重建完成，共 {count} 个技能")
        return count
    
    def _parse_skill_directory(self, skill_dir: Path) -> Optional[Skill]:
        """
        解析技能目录
        
        Args:
            skill_dir: 技能目录路径
            
        Returns:
            Skill对象或None
        """
        skill_id = skill_dir.name
        
        # 查找SKILL.md
        skill_md = skill_dir / "SKILL.md"
        plugin_json = skill_dir / "plugin.json"
        
        if not skill_md.exists() and not plugin_json.exists():
            return None
        
        # 从SKILL.md解析
        metadata = {
            "id": skill_id,
            "name": skill_id.replace("-", " ").replace("_", " ").title(),
            "description": "",
            "keywords": [],
            "skill_type": SkillType.UTILITY,
            "local_path": str(skill_dir)
        }
        
        if skill_md.exists():
            md_metadata = self._parse_skill_md(skill_md)
            metadata.update(md_metadata)
        
        # 从plugin.json解析（如果存在）
        if plugin_json.exists():
            try:
                with open(plugin_json, 'r', encoding='utf-8') as f:
                    plugin_data = json.load(f)
                    metadata["name"] = plugin_data.get("name", metadata["name"])
                    metadata["description"] = plugin_data.get("description", metadata["description"])
                    if "keywords" in plugin_data:
                        metadata["keywords"].extend(plugin_data["keywords"])
            except:
                pass
        
        # 创建Skill对象
        try:
            skill = Skill(
                id=metadata["id"],
                name=metadata["name"],
                description=metadata["description"],
                skill_type=metadata.get("skill_type", SkillType.UTILITY),
                inputs=[],
                outputs=[],
                metadata=SkillMetadata(),
                source="local",
                local_path=metadata["local_path"],
                status=SkillStatus.INSTALLED,
                keywords=metadata.get("keywords", [skill_id])
            )
            return skill
        except Exception as e:
            print(f"[SkillFinder] 解析技能失败 {skill_id}: {e}")
            return None
    
    def _parse_skill_md(self, md_path: Path) -> Dict:
        """解析SKILL.md文件"""
        metadata = {"keywords": []}
        
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                metadata["name"] = title_match.group(1).strip()
            
            # 提取描述（标题后的第一段）
            desc_match = re.search(r'^#\s+.+\n\n(.+?)(?:\n\n|\n#)', content, re.DOTALL)
            if desc_match:
                metadata["description"] = desc_match.group(1).strip()
            
            # 提取关键词
            # 从标题和描述中提取
            all_text = content.lower()
            keyword_patterns = [
                r'pdf', r'报价', r'分析', r'生成', r'转换', r'查询',
                r'cnc', r'文档', r'报告', r'数据', r'代码', r'图片',
                r'语音', r'视频', r'文件', r'markdown', r'excel',
                r'weather', r'天气', r'search', r'搜索', r'browser',
                r'浏览器', r'cron', r'定时', r'health', r'健康'
            ]
            for pattern in keyword_patterns:
                if re.search(pattern, all_text):
                    metadata["keywords"].append(pattern)
            
            # 推断技能类型
            if any(k in ['pdf', '生成', '报价'] for k in metadata["keywords"]):
                metadata["skill_type"] = SkillType.GENERATOR
            elif any(k in ['分析', 'analysis'] for k in metadata["keywords"]):
                metadata["skill_type"] = SkillType.ANALYZER
            elif any(k in ['转换', 'transform'] for k in metadata["keywords"]):
                metadata["skill_type"] = SkillType.TRANSFORMER
            else:
                metadata["skill_type"] = SkillType.UTILITY
            
        except Exception as e:
            print(f"[SkillFinder] 解析SKILL.md失败: {e}")
        
        return metadata
    
    def find(self, intent: Intent, top_k: int = 5) -> List[Tuple[Skill, float]]:
        """
        根据意图查找技能
        
        Args:
            intent: 意图对象
            top_k: 返回前k个匹配
            
        Returns:
            [(Skill, score)] 列表
        """
        candidates = []
        
        # 1. 从本地索引匹配
        for skill_id, skill in self.local_index.items():
            score = self._calculate_match_score(skill, intent)
            if score > 0:
                candidates.append((skill, score))
        
        # 2. 按分数排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 3. 返回top_k
        return candidates[:top_k]
    
    def _calculate_match_score(self, skill: Skill, intent: Intent) -> float:
        """
        计算技能与意图的匹配分数
        
        Args:
            skill: 技能对象
            intent: 意图对象
            
        Returns:
            匹配分数 (0-1)
        """
        score = 0.0
        
        # 1. 关键词匹配
        skill_keywords = set(k.lower() for k in skill.keywords)
        intent_keywords = set(k.lower() for k in intent.keywords)
        
        if skill_keywords and intent_keywords:
            keyword_overlap = len(skill_keywords & intent_keywords)
            keyword_score = keyword_overlap / max(len(skill_keywords), len(intent_keywords))
            score += keyword_score * 0.5
        
        # 2. 意图类型匹配
        intent_skill_types = {
            "generate": [SkillType.GENERATOR, SkillType.UTILITY],
            "analyze": [SkillType.ANALYZER, SkillType.UTILITY],
            "query": [SkillType.CONNECTOR, SkillType.UTILITY],
            "transform": [SkillType.TRANSFORMER, SkillType.UTILITY]
        }
        
        if intent.intent_type in intent_skill_types:
            if skill.skill_type in intent_skill_types[intent.intent_type]:
                score += 0.2
        
        # 3. 名称/描述匹配
        skill_text = f"{skill.name} {skill.description}".lower()
        for kw in intent.keywords:
            if kw.lower() in skill_text:
                score += 0.1
        
        # 4. 历史成功率加权
        if skill.usage_count > 0:
            success_weight = skill.success_rate * 0.2
            score += success_weight
        
        return min(score, 1.0)
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取指定技能"""
        return self.local_index.get(skill_id)
    
    def list_all_skills(self) -> List[Skill]:
        """列出所有已索引的技能"""
        return list(self.local_index.values())
    
    def search_by_keyword(self, keyword: str) -> List[Skill]:
        """按关键词搜索技能"""
        results = []
        keyword_lower = keyword.lower()
        
        for skill in self.local_index.values():
            # 搜索关键词
            if any(keyword_lower in k.lower() for k in skill.keywords):
                results.append(skill)
            # 搜索名称
            elif keyword_lower in skill.name.lower():
                results.append(skill)
            # 搜索描述
            elif keyword_lower in skill.description.lower():
                results.append(skill)
        
        return results
    
    def update_skill_stats(self, skill_id: str, success: bool, latency: float):
        """
        更新技能统计信息
        
        Args:
            skill_id: 技能ID
            success: 是否成功
            latency: 执行耗时
        """
        if skill_id not in self.local_index:
            return
        
        skill = self.local_index[skill_id]
        skill.usage_count += 1
        
        # 更新成功率（滑动平均）
        if skill.usage_count == 1:
            skill.success_rate = 1.0 if success else 0.0
        else:
            old_rate = skill.success_rate
            new_rate = 1.0 if success else 0.0
            skill.success_rate = old_rate * 0.8 + new_rate * 0.2
        
        # 更新平均延迟
        if skill.usage_count == 1:
            skill.avg_latency = latency
        else:
            skill.avg_latency = (skill.avg_latency * (skill.usage_count - 1) + latency) / skill.usage_count
        
        self._save_index()


# 测试
if __name__ == "__main__":
    finder = SkillFinder()
    
    # 重建索引
    count = finder.rebuild_index()
    print(f"\n已索引 {count} 个技能")
    
    # 列出所有技能
    print("\n所有技能:")
    for skill in finder.list_all_skills()[:10]:
        print(f"  - {skill.id}: {skill.name} ({skill.skill_type.value})")
    
    # 测试搜索
    print("\n搜索 'PDF':")
    for skill in finder.search_by_keyword("pdf"):
        print(f"  - {skill.id}: {skill.name}")