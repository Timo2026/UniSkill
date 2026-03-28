#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
反馈分析与优化器 - 第三阶段
自动分析反馈数据并优化检索配置

功能:
1. 分析各意图的采纳率
2. 自动调整 retriever_config.json
3. 生成优化建议
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 路径
CONFIG_PATH = Path.home() / ".openclaw/workspace/data/retriever_config.json"
REPORT_PATH = Path.home() / ".openclaw/workspace/logs/optimization_report.jsonl"

sys.path.insert(0, str(Path(__file__).parent))
from feedback_logger import get_logger


class OptimizationEngine:
    """
    优化引擎
    
    根据反馈自动调整检索配置
    """
    
    # 采纳率阈值
    LOW_THRESHOLD = 0.4      # 低于此值关闭向量检索
    MEDIUM_THRESHOLD = 0.6   # 中等，降低权重
    HIGH_THRESHOLD = 0.8     # 高，提升权重
    
    def __init__(self):
        self.logger = get_logger()
        self.config_path = CONFIG_PATH
    
    def analyze_and_optimize(self) -> Dict:
        """
        分析并优化
        
        Returns:
            优化报告
        """
        # 加载当前配置
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # 获取反馈统计
        stats = self.logger.get_stats(days=7)
        
        # 优化建议
        optimizations = []
        
        for intent, data in stats.items():
            if intent not in config['rules']:
                continue
            
            current_rule = config['rules'][intent]
            adoption_rate = data['adoption_rate']
            total_queries = data['total_queries']
            
            # 判断是否需要优化
            if total_queries < 5:
                # 数据太少，不优化
                continue
            
            optimization = {
                'intent': intent,
                'current_use_vector': current_rule.get('use_vector', False),
                'current_vector_weight': current_rule.get('vector_weight', 0.7),
                'adoption_rate': adoption_rate,
                'total_queries': total_queries,
                'action': None,
                'new_config': None
            }
            
            if adoption_rate < self.LOW_THRESHOLD:
                # 采纳率过低，关闭向量检索
                optimization['action'] = 'disable_vector'
                optimization['reason'] = f"采纳率{adoption_rate:.1%}过低，建议关闭向量检索"
                current_rule['use_vector'] = False
                
            elif adoption_rate < self.MEDIUM_THRESHOLD:
                # 中等，降低向量权重
                optimization['action'] = 'reduce_weight'
                optimization['reason'] = f"采纳率{adoption_rate:.1%}中等，降低向量权重"
                current_rule['vector_weight'] = 0.5
                current_rule['rule_weight'] = 0.5
                
            elif adoption_rate > self.HIGH_THRESHOLD:
                # 高采纳率，提升权重
                optimization['action'] = 'increase_weight'
                optimization['reason'] = f"采纳率{adoption_rate:.1%}优秀，提升向量权重"
                current_rule['vector_weight'] = 0.8
                current_rule['rule_weight'] = 0.2
            
            else:
                optimization['reason'] = f"采纳率{adoption_rate:.1%}正常，保持当前配置"
            
            optimizations.append(optimization)
        
        # 保存优化后的配置
        if optimizations:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 记录优化报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'optimizations': optimizations
        }
        
        with open(REPORT_PATH, 'a') as f:
            f.write(json.dumps(report, ensure_ascii=False) + '\n')
        
        return report
    
    def generate_alert(self) -> Optional[str]:
        """
        生成告警
        
        Returns:
            告警文本（如果需要）
        """
        low_intents = self.logger.get_low_adoption_intents(threshold=0.4, min_queries=10)
        
        if not low_intents:
            return None
        
        alert_lines = [
            "⚠️ 检索优化告警",
            "=" * 30,
            ""
        ]
        
        for intent in low_intents:
            stats = self.logger.get_stats(days=7)
            if intent in stats:
                data = stats[intent]
                alert_lines.extend([
                    f"📌 {intent}",
                    f"   采纳率: {data['adoption_rate']:.1%}",
                    f"   查询数: {data['total_queries']}",
                    f"   💡 建议: 补充数据或调整阈值",
                    ""
                ])
        
        return "\n".join(alert_lines)


def run_daily_optimization():
    """每日优化任务"""
    engine = OptimizationEngine()
    
    print("=== 每日检索优化 ===")
    
    # 分析并优化
    report = engine.analyze_and_optimize()
    
    print(f"分析意图数: {len(report['stats'])}")
    print(f"优化项数: {len(report['optimizations'])}")
    
    # 检查告警
    alert = engine.generate_alert()
    if alert:
        print(f"\n{alert}")
    
    return report


# 测试
if __name__ == "__main__":
    # 添加更多测试数据
    logger = get_logger()
    
    # 模拟多种意图的反馈
    test_data = [
        ("CNC报价", "cnc_quote", 0.92, True),
        ("CNC报价2", "cnc_quote", 0.85, True),
        ("CNC报价3", "cnc_quote", 0.88, True),
        ("写代码", "code_gen", 0.65, False),
        ("写代码2", "code_gen", 0.70, False),
        ("写代码3", "code_gen", 0.60, False),
        ("翻译", "translation", 0.95, True),
        ("设计", "creative_design", 0.50, False),
    ]
    
    for query, intent, score, useful in test_data:
        rid = logger.log_retrieval(query, intent, score, 3, 150)
        feedback = "useful" if useful else "not_useful"
        logger.record_feedback(rid, feedback, adopted=useful)
    
    # 运行优化
    report = run_daily_optimization()
    print(f"\n优化报告: {json.dumps(report['optimizations'], indent=2, ensure_ascii=False)}")