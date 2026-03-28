#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Skill V2 入口 - 苏格拉底+5W2H深度锚定版
替代旧版simple_execute.py

使用方式:
    from simple_execute_v2 import SimpleUniversalSkillV2
    skill = SimpleUniversalSkillV2()
    result = skill.execute("你的任务")
"""

import sys
from pathlib import Path

# 添加core_v2路径
sys.path.insert(0, str(Path(__file__).parent / "core_v2"))

from universal_skill_v2 import UniversalSkillV2


class SimpleUniversalSkillV2:
    """
    简化版入口 - 兼容旧版API
    
    新增功能:
    - 苏格拉底探明（先问后做）
    - 收敛系数检查（避免错误路径）
    - 本地向量检索优先
    """
    
    def __init__(self):
        self._skill = None
    
    @property
    def skill(self):
        """懒加载"""
        if self._skill is None:
            self._skill = UniversalSkillV2()
        return self._skill
    
    def execute(self, user_input: str, context: dict = None) -> dict:
        """
        执行任务
        
        Args:
            user_input: 用户输入
            context: 可选上下文
            
        Returns:
            执行结果
        """
        return self.skill.execute(user_input, context)
    
    def get_status(self) -> dict:
        """获取状态"""
        return self.skill.get_status_report()


# 便捷函数
def execute(user_input: str, context: dict = None) -> dict:
    """便捷执行函数"""
    skill = SimpleUniversalSkillV2()
    return skill.execute(user_input, context)


if __name__ == "__main__":
    # 命令行测试
    import json
    
    print("Universal Skill V2 - 测试模式")
    print("="*50)
    
    skill = SimpleUniversalSkillV2()
    
    # 测试用例
    test_cases = [
        "帮我做一个报价",
        "铝合金6061加工",
        "写一个Python函数"
    ]
    
    for case in test_cases:
        print(f"\n输入: {case}")
        result = skill.execute(case)
        print(f"状态: {result.get('status')}")
        print(f"收敛: {result.get('convergence_rate', 0)*100:.0f}%")
