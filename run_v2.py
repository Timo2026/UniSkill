#!/usr/bin/env python3
"""
Universal Skill V2 启动脚本
优先使用V2，失败回退V1
"""

import sys
from pathlib import Path

def get_skill():
    """获取Skill实例，优先V2"""
    try:
        from simple_execute_v2 import SimpleUniversalSkillV2
        print("[UniversalSkill] 使用 V2 (苏格拉底+5W2H)")
        return SimpleUniversalSkillV2()
    except Exception as e:
        print(f"[UniversalSkill] V2加载失败: {e}")
        print("[UniversalSkill] 回退 V1")
        from simple_execute import SimpleUniversalSkill
        return SimpleUniversalSkill()

if __name__ == "__main__":
    skill = get_skill()
    
    # 测试
    result = skill.execute("帮我做一个报价")
    print(result)
