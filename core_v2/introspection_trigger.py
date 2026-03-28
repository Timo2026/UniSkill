#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口令触发入口：海狸，交底

当用户输入"海狸，交底"时，触发全量内省
"""

import sys
import json
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from sys_introspection import SystemIntrospector


def trigger_introspection(user_input: str) -> dict:
    """
    检测口令并触发内省
    
    Args:
        user_input: 用户输入
    
    Returns:
        如果触发，返回内省报告；否则返回 None
    """
    # 口令列表
    triggers = [
        "海狸，交底",
        "交底",
        "系统真相",
        "绝密公开",
        "海狸交底"
    ]
    
    # 检测触发
    input_lower = user_input.lower().strip()
    
    for trigger in triggers:
        if trigger.lower() in input_lower:
            print(f"🦫 检测到口令: {trigger}")
            print("  执行全量交底...")
            
            # 调用内省工具
            introspector = SystemIntrospector()
            report = introspector.full_reveal()
            
            # 生成 Markdown 报告
            md_report = introspector.generate_report(format="markdown")
            
            # 保存报告
            report_path = Path(__file__).parent.parent / "data" / "introspection_report.md"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(md_report, encoding="utf-8")
            
            print(f"✅ 报告已保存: {report_path}")
            
            return {
                "triggered": True,
                "trigger_word": trigger,
                "report_path": str(report_path),
                "report": md_report,
                "raw_data": report
            }
    
    return {"triggered": False}


# CLI 测试
if __name__ == "__main__":
    test_input = "海狸，交底"
    result = trigger_introspection(test_input)
    
    if result["triggered"]:
        print("\n" + result["report"])
    else:
        print("口令未触发")