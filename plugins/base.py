#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件基类 - Base Plugin Classes
所有插件都继承自这些基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# 导入schema
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from schemas.skill_schema import Skill, Intent


class BasePlugin(ABC):
    """
    插件基类
    
    所有插件必须实现：
    - name: 插件名称
    - version: 版本号
    - initialize(): 初始化
    - health_check(): 健康检查
    - shutdown(): 关闭清理
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._initialized = False
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """版本号"""
        pass
    
    @property
    def description(self) -> str:
        """插件描述"""
        return ""
    
    def initialize(self) -> bool:
        """
        初始化插件
        
        Returns:
            是否初始化成功
        """
        self._initialized = True
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态
        """
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy" if self._initialized else "not_initialized"
        }
    
    def shutdown(self):
        """关闭清理"""
        self._initialized = False


class SkillSourcePlugin(BasePlugin):
    """
    技能源插件基类
    
    用于从不同来源发现和获取技能
    """
    
    @abstractmethod
    def find(self, intent: Intent, top_k: int = 5) -> List[tuple]:
        """
        根据意图查找技能
        
        Args:
            intent: 意图对象
            top_k: 返回数量
            
        Returns:
            [(Skill, score)] 列表
        """
        pass
    
    @abstractmethod
    def get(self, skill_id: str) -> Optional[Skill]:
        """
        获取指定技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            Skill对象或None
        """
        pass
    
    def install(self, skill_id: str) -> bool:
        """
        安装技能到本地
        
        Args:
            skill_id: 技能ID
            
        Returns:
            是否安装成功
        """
        return False
    
    def list_available(self, keyword: str = "", page: int = 1, size: int = 20) -> List[Skill]:
        """
        列出可用技能
        
        Args:
            keyword: 搜索关键词
            page: 页码
            size: 每页数量
            
        Returns:
            技能列表
        """
        return []


class OrchestratorPlugin(BasePlugin):
    """
    编排插件基类
    
    用于控制任务执行流程
    """
    
    @abstractmethod
    def plan(self, intent: Intent, skills: List[Skill]) -> Dict:
        """
        规划执行
        
        Args:
            intent: 意图对象
            skills: 可用技能列表
            
        Returns:
            执行计划
        """
        pass
    
    @abstractmethod
    def execute(self, plan: Dict, context: Dict) -> Dict:
        """
        执行计划
        
        Args:
            plan: 执行计划
            context: 执行上下文
            
        Returns:
            执行结果
        """
        pass


class QualityCheckerPlugin(BasePlugin):
    """
    质量检查插件基类
    
    用于验证输出质量
    """
    
    @abstractmethod
    def check(self, outputs: Dict, expected: Optional[Dict] = None) -> Dict:
        """
        检查输出
        
        Args:
            outputs: 执行输出
            expected: 预期结果
            
        Returns:
            检查结果
        """
        pass
    
    def fix(self, outputs: Dict, check_result: Dict) -> Dict:
        """
        修复问题
        
        Args:
            outputs: 原始输出
            check_result: 检查结果
            
        Returns:
            修复后的输出
        """
        return outputs


# 导出
__all__ = [
    'BasePlugin',
    'SkillSourcePlugin',
    'OrchestratorPlugin',
    'QualityCheckerPlugin'
]