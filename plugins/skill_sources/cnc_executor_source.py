#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNC执行器源适配器
将CNC执行器包装为Skill源
"""

import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# 导入基类和schema
sys.path.insert(0, str(Path(__file__).parent.parent))
from plugins.base import SkillSourcePlugin
from schemas.skill_schema import Skill, SkillType, SkillStatus, SkillMetadata, SkillInput, SkillOutput
from core.intent_parser import Intent


class CNCExecutorSource(SkillSourcePlugin):
    """
    CNC执行器源
    
    提供真实的CNC报价执行能力
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        
        # 技能定义
        self.skills = {
            "cnc-executor": Skill(
                id="cnc-executor",
                name="CNC报价执行器",
                description="真正的手脚，执行报价计算和PDF生成",
                skill_type=SkillType.GENERATOR,
                inputs=[
                    SkillInput(name="text", type="string", description="输入文本"),
                    SkillInput(name="quantity", type="number", description="数量", default=10),
                    SkillInput(name="material", type="string", description="材料", default="铝合金")
                ],
                outputs=[
                    SkillOutput(name="pdf_path", type="file", description="生成的PDF路径"),
                    SkillOutput(name="quote_result", type="json", description="报价结果")
                ],
                metadata=SkillMetadata(
                    author="海狸",
                    version="1.0.0",
                    tags=["报价", "CNC", "PDF", "生成", "制造"]
                ),
                source="local",
                local_path=str(Path.home() / ".openclaw" / "workspace" / "skills" / "cnc-executor"),
                status=SkillStatus.INSTALLED,
                keywords=["报价", "CNC", "PDF", "生成", "零件", "材料", "制造", "价格", "报价单"]
            )
        }
        
        # 执行器实例
        self._executor = None
    
    @property
    def name(self) -> str:
        return "cnc-executor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "CNC报价执行器"
    
    def initialize(self) -> bool:
        """初始化"""
        try:
            # 添加正确的导入路径
            skill_path = Path.home() / ".openclaw" / "workspace" / "skills" / "cnc-executor"
            if skill_path.exists():
                sys.path.insert(0, str(skill_path))
            
            from executor import CNCExecutor
            self._executor = CNCExecutor()
            self._initialized = True
            print(f"[CNCExecutorSource] 初始化完成")
            return True
        except Exception as e:
            print(f"[CNCExecutorSource] 初始化失败: {e}")
            # 尝试另一种导入方式
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "executor",
                    Path.home() / ".openclaw" / "workspace" / "skills" / "cnc-executor" / "executor.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._executor = module.CNCExecutor()
                self._initialized = True
                print(f"[CNCExecutorSource] 初始化完成（动态加载）")
                return True
            except Exception as e2:
                print(f"[CNCExecutorSource] 动态加载也失败: {e2}")
                return False
    
    def find(self, intent: Intent, top_k: int = 5) -> List[tuple]:
        """查找技能"""
        results = []
        
        # 检查意图是否匹配
        manufacturing_keywords = ["报价", "cnc", "零件", "材料", "制造", "加工"]
        pdf_keywords = ["pdf", "报价单", "生成"]
        
        is_manufacturing = any(kw in intent.intent_type.lower() or 
                               any(mk in k.lower() for mk in manufacturing_keywords for k in intent.keywords)
                               for kw in intent.keywords)
        
        is_pdf = any(pk in " ".join(intent.keywords).lower() for pk in pdf_keywords)
        
        if is_manufacturing or is_pdf or intent.domain == "manufacturing":
            skill = self.skills["cnc-executor"]
            score = self._calculate_score(skill, intent)
            results.append((skill, score))
        
        return results[:top_k]
    
    def _calculate_score(self, skill: Skill, intent: Intent) -> float:
        """计算匹配分数"""
        score = 0.0
        
        # 关键词匹配
        skill_keywords = set(k.lower() for k in skill.keywords)
        intent_keywords = set(k.lower() for k in intent.keywords)
        
        overlap = len(skill_keywords & intent_keywords)
        score += min(overlap * 0.2, 0.6)
        
        # 领域匹配
        if intent.domain == "manufacturing":
            score += 0.3
        
        # 意图类型匹配
        if intent.intent_type == "generate":
            score += 0.2
        
        return min(score, 1.0)
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_id)
    
    def execute(self, skill_id: str, task_type: str, input_data: Dict) -> Dict:
        """
        执行技能
        
        Args:
            skill_id: 技能ID
            task_type: 任务类型
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        if skill_id != "cnc-executor":
            return {"success": False, "error": "未知技能"}
        
        if not self._executor:
            return {"success": False, "error": "执行器未初始化"}
        
        return self._executor.execute(task_type, input_data)
    
    def list_available(self, keyword: str = "", page: int = 1, size: int = 20) -> List[Skill]:
        """列出可用技能"""
        if keyword:
            if any(kw in keyword.lower() for kw in ["报价", "cnc", "pdf", "制造"]):
                return [self.skills["cnc-executor"]]
        return list(self.skills.values())


# 导出
__all__ = ['CNCExecutorSource']