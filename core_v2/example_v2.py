#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
万能 Skill V2.2 使用示例
展示"内圣外王"的完整渲染效果
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core_v2.state_machine import StateMachine, ExecutionState
from core_v2.x_styler_v2 import XStylerV2


def demo_low_convergence():
    """低收敛度场景：启动苏格拉底追问"""
    styler = XStylerV2()
    
    # 模拟低收敛度
    questions = [
        {
            "dimension": "WHAT",
            "question": "本次报价的核心对象是什么？",
            "options": ["单个零件", "批量报价", "对比报价"],
            "importance": "CRITICAL",
            "color": "#1DA1F2"
        },
        {
            "dimension": "HOW_MUCH",
            "question": "公差精度要求是什么？",
            "options": ["±0.01mm", "±0.05mm", "±0.1mm"],
            "importance": "CRITICAL",
            "color": "#17BF63"
        },
        {
            "dimension": "WHO",
            "question": "目标客户类型？",
            "options": ["企业客户", "个人DIY", "代理商"],
            "importance": "IMPORTANT",
            "color": "#8b5cf6"
        }
    ]
    
    html = styler.render_socratic_probe(
        questions=questions,
        convergence=0.25,
        intent="cnc_quote",
        message="大帅，需求有点模糊，我得追问几句："
    )
    
    return html


def demo_successful_execution():
    """成功执行场景：完整决策链展示"""
    styler = XStylerV2()
    
    content = """
## CNC报价分析结果

### 基本信息
- **材料**: 铝合金6061-T6
- **数量**: 100件
- **公差**: ±0.05mm

### 价格分析
| 项目 | 单价 | 总价 |
|------|------|------|
| 材料费 | ¥12.5/件 | ¥1,250 |
| 加工费 | ¥35/件 | ¥3,500 |
| 表面处理 | ¥8/件 | ¥800 |
| **合计** | - | **¥5,550** |

### 交付周期
预计 **7-10个工作日** 完成。
"""
    
    html = styler.render_full_output(
        content=content,
        convergence=0.85,  # 高收敛度
        model="qwen3.5-plus",
        intent="cnc_quote",
        show_dashboard=True
    )
    
    return html


def demo_error_case():
    """错误场景：给出建议"""
    styler = XStylerV2()
    
    html = styler.render_error_card(
        error_message="材料参数缺失，无法进行价格计算",
        suggestion="请补充材料型号（如6061-T6、7075等）和数量信息",
        convergence=0.15
    )
    
    return html


def demo_asset_dashboard():
    """资产看板：数据可视化"""
    styler = XStylerV2()
    return styler.render_asset_dashboard()


def main():
    """运行所有演示"""
    print("=" * 60)
    print("🦫 万能 Skill V2.2 - 内圣外王演示")
    print("=" * 60)
    
    # 1. 低收敛度追问
    print("\n【场景1】低收敛度 - 苏格拉底追问")
    html = demo_low_convergence()
    print(f"输出长度: {len(html)} bytes")
    print(f"包含追问: {'SOCRATIC_PROBE' in html}")
    
    # 2. 成功执行
    print("\n【场景2】成功执行 - 完整决策链")
    html = demo_successful_execution()
    print(f"输出长度: {len(html)} bytes")
    print(f"包含思考轨迹: {'thinking' in html.lower()}")
    print(f"包含资产看板: {'黄金案例' in html}")
    
    # 3. 错误场景
    print("\n【场景3】错误处理 - 建议引导")
    html = demo_error_case()
    print(f"输出长度: {len(html)} bytes")
    print(f"包含建议: {'建议' in html}")
    
    # 4. 资产看板
    print("\n【场景4】资产看板")
    html = demo_asset_dashboard()
    print(f"输出长度: {len(html)} bytes")
    
    # 保存示例输出
    output_dir = Path(__file__).parent / "demo_output"
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "socratic_probe.html", "w") as f:
        f.write(demo_low_convergence())
    
    with open(output_dir / "decision_card.html", "w") as f:
        f.write(demo_successful_execution())
    
    with open(output_dir / "error_card.html", "w") as f:
        f.write(demo_error_case())
    
    with open(output_dir / "asset_dashboard.html", "w") as f:
        f.write(demo_asset_dashboard())
    
    print("\n✅ 演示完成，输出已保存到 demo_output/")
    print("=" * 60)


if __name__ == "__main__":
    main()