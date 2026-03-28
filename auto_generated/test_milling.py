#!/usr/bin/env python3
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
