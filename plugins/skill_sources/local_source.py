#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地技能源适配器
包装现有的 SkillFinder，提供统一的插件接口
"""

import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# 导入基类和schema
sys.path.insert(0, str(Path(__file__).parent.parent))
from plugins.base import SkillSourcePlugin
from schemas.skill_schema import Skill, Intent

# 导入现有模块
from core.skill_finder import SkillFinder


class LocalSource(SkillSourcePlugin):
    """
    本地技能源
    
    包装现有的 SkillFinder，作为优先级最高的技能源
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.skill_finder = SkillFinder(config)
    
    @property
    def name(self) -> str:
        return "local"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "本地已安装技能"
    
    def initialize(self) -> bool:
        """初始化"""
        # 重建索引
        count = self.skill_finder.rebuild_index()
        self._initialized = True
        print(f"[LocalSource] 索引了 {count} 个本地技能")
        return True
    
    def find(self, intent: Intent, top_k: int = 5) -> List[tuple]:
        """查找技能"""
        return self.skill_finder.find(intent, top_k)
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.skill_finder.get_skill(skill_id)
    
    def list_available(self, keyword: str = "", page: int = 1, size: int = 20) -> List[Skill]:
        """列出技能"""
        if keyword:
            return self.skill_finder.search_by_keyword(keyword)
        return self.skill_finder.list_all_skills()
    
    def update_stats(self, skill_id: str, success: bool, latency: float):
        """更新统计"""
        self.skill_finder.update_skill_stats(skill_id, success, latency)


# 导出
__all__ = ['LocalSource']