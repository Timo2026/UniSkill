#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_genesis.py - God Mode 测试脚本
测试钛合金 TC4 铣削转速计算

简化版：只测试 SkillForge 沙盒和动态加载，不依赖向量检索
"""

import sys
import os
import json
import math
from pathlib import Path

# ============================================================
# 测试案例
# ============================================================

# 刀具直径 12mm，推荐线速度 40 m/min
CLIENT_PARAMS = {
    "D": 12,           # 刀具直径 mm
    "Vc_recomm": 40    # 推荐线速度 m/min
}

# 期望结果: S = (1000 × 40) / (π × 12) ≈ 1061 rpm
EXPECTED_S = 1061


def test_skillforge_sandbox():
    """测试 SkillForge 沙盒功能"""
    print("\n" + "=" * 60)
    print("🧪 测试1: SkillForge 沙盒")
    print("=" * 60)
    
    # 导入 SkillForge
    sys.path.insert(0, str(Path(__file__).parent / "core_v2"))
    from skill_forge import SkillForge
    
    forge = SkillForge(api_key="", model="qwen3.5-plus")
    
    # 创建测试技能
    test_code = '''#!/usr/bin/env python3
"""钛合金TC4铣削转速计算"""

import math

def execute(params: dict) -> dict:
    """计算铣削主轴转速: S = (1000 × Vc) / (π × D)"""
    D = params.get("D", 10)
    Vc = params.get("Vc_recomm", 30)
    S = (1000 * Vc) / (math.pi * D)
    return {
        "success": True,
        "result": {"S": round(S, 1), "Vc": Vc, "D": D},
        "formula": "S = (1000 × Vc) / (π × D)"
    }

if __name__ == "__main__":
    test_params = {"D": 12, "Vc_recomm": 40}
    result = execute(test_params)
    assert result["success"]
    assert abs(result["result"]["S"] - 1061) < 10
    print(f"✅ 自检通过: S = {result['result']['S']} rpm")
'''
    
    test_file = forge.SKILL_DIR / "test_tc4_milling.py"
    test_file.write_text(test_code)
    print(f"  写入测试技能: {test_file.name}")
    
    # 沙盒测试
    print("\n  沙盒测试（3秒超时）...")
    sandbox_result = forge._sandbox_test(test_file)
    
    if sandbox_result["passed"]:
        print("  ✅ 沙盒通过")
        
        # 动态加载执行
        print("\n  动态加载测试...")
        module = forge.load_module(str(test_file))
        if module:
            result = module.execute(CLIENT_PARAMS)
            S = result["result"]["S"]
            print(f"  执行结果: S = {S} rpm")
            
            if abs(S - EXPECTED_S) < 10:
                print(f"  ✅ 计算正确!")
            else:
                print(f"  ⚠️ 偏差: 期望 {EXPECTED_S} rpm")
    
    # 清理
    test_file.unlink()
    return sandbox_result["passed"]


def test_orchestrator_loop():
    """测试 OrchestratorV2 闭环"""
    print("\n" + "=" * 60)
    print("🧪 测试2: OrchestratorV2 1→2/3→1 闭环")
    print("=" * 60)
    
    from orchestrator_v2 import OrchestratorV2
    
    boss = OrchestratorV2(api_key="", model="qwen3.5-plus")
    
    # 创建测试技能
    test_skill = boss.SKILLS_DIR / "skill_milling_test.py"
    test_skill.write_text('''#!/usr/bin/env python3
"""铣削转速计算"""
import math
def execute(params: dict) -> dict:
    D = params.get("D", 10)
    Vc = params.get("Vc_recomm", 30)
    S = (1000 * Vc) / (math.pi * D)
    return {"success": True, "result": {"S": round(S, 1), "Vc": Vc}}
if __name__ == "__main__":
    print("✅ 自检通过")
''')
    
    print(f"  创建技能: {test_skill.name}")
    
    # 直接执行动态加载测试（跳过向量检索）
    print("\n  动态执行测试...")
    result = boss._execute_dynamic_module(test_skill, CLIENT_PARAMS)
    
    print(f"  执行结果: {json.dumps(result, indent=2)}")
    
    # 清理
    test_skill.unlink()
    
    return result.get("success", False)


def test_formula_correctness():
    """直接验证公式计算正确性"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 公式验证")
    print("=" * 60)
    
    # S = (1000 × Vc) / (π × D)
    D = CLIENT_PARAMS["D"]
    Vc = CLIENT_PARAMS["Vc_recomm"]
    
    S = (1000 * Vc) / (math.pi * D)
    
    print(f"  公式: S = (1000 × Vc) / (π × D)")
    print(f"  参数: D={D}mm, Vc={Vc}m/min")
    print(f"  计算: S = (1000 × {Vc}) / (π × {D})")
    print(f"  结果: S = {S:.1f} rpm")
    print(f"  期望: S ≈ {EXPECTED_S} rpm")
    
    if abs(S - EXPECTED_S) < 10:
        print("  ✅ 计算正确!")
        return True
    else:
        print("  ❌ 计算错误")
        return False


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   God Mode 测试 - 钛合金 TC4 铣削转速计算                   ║")
    print("║                                                              ║")
    print("║   公式: S = (1000 × Vc) / (π × D)                           ║")
    print("║   参数: D=12mm, Vc=40m/min                                  ║")
    print("║   期望: S ≈ 1061 rpm                                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # 测试 1: 公式验证
    test1 = test_formula_correctness()
    
    # 测试 2: 沙盒
    test2 = test_skillforge_sandbox()
    
    # 测试 3: 闭环
    test3 = test_orchestrator_loop()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"  公式验证: {'✅' if test1 else '❌'}")
    print(f"  沙盒测试: {'✅' if test2 else '❌'}")
    print(f"  闭环测试: {'✅' if test3 else '❌'}")
    
    if test1 and test2 and test3:
        print("\n🎉 所有测试通过！")
        print("\nSkillForge 核心功能已验证:")
        print("  ✅ 沙盒自检机制正常")
        print("  ✅ 动态加载执行正常")
        print("  ✅ 计算公式正确")
        print("\n下一步: 配置 DASHSCOPE_API_KEY 测试完整 Forge 流程")