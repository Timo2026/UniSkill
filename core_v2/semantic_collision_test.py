#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Collision Test - 语义碰撞测试
每生成100条案例，随机抽取2条进行盲测，校验路由准确率

大帅指示：实时校验 ChromaDB 检索准确率
"""

import json
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

# 添加路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from model_router_v2 import ModelRouter


class SemanticCollisionTest:
    """
    语义碰撞测试
    
    目的：实时校验路由系统的检索准确率
    方法：随机抽取已生成案例，让路由器盲测
    """
    
    def __init__(self, golden_path: str = None):
        self.router = ModelRouter()
        self.golden_path = golden_path or str(
            Path(__file__).parent.parent / "data" / "golden_dataset.jsonl"
        )
        self.results_path = Path(__file__).parent.parent / "data" / "collision_test_results.json"
        
        # 测试统计
        self.tests_run = 0
        self.tests_passed = 0
        self.accuracy_log: List[Dict] = []
    
    def load_golden_cases(self) -> List[Dict]:
        """加载黄金案例"""
        cases = []
        if Path(self.golden_path).exists():
            with open(self.golden_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        cases.append(json.loads(line))
        return cases
    
    def run_collision_test(self, sample_size: int = 2) -> Dict:
        """
        执行语义碰撞测试
        
        Args:
            sample_size: 抽取样本数量
        
        Returns:
            测试结果统计
        """
        cases = self.load_golden_cases()
        
        if len(cases) < sample_size:
            return {
                "status": "SKIP",
                "reason": f"案例数不足({len(cases)}<{sample_size})"
            }
        
        # 随机抽取样本
        samples = random.sample(cases, min(sample_size, len(cases)))
        
        print(f"\n{'='*50}")
        print(f"🧪 语义碰撞测试 (抽取{len(samples)}条)")
        print(f"{'='*50}")
        
        results = []
        for case in samples:
            task_text = case.get("task_text", "")
            expected_model = case.get("model", "unknown")
            expected_intent = case.get("intent", "unknown")
            
            # 路由器盲测
            route_result = self.router.route(
                task_text=task_text,
                convergence_score=0.9  # 假设高收敛
            )
            
            actual_model = route_result.get("model", "unknown")
            match = actual_model == expected_model
            
            result = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "task_text": task_text[:50],
                "expected_model": expected_model,
                "actual_model": actual_model,
                "match": match,
                "intent": expected_intent
            }
            
            results.append(result)
            
            # 输出结果
            status = "✅" if match else "❌"
            print(f"\n{status} 测试案例: {task_text[:30]}...")
            print(f"  预期模型: {expected_model}")
            print(f"  实际模型: {actual_model}")
            
            if match:
                self.tests_passed += 1
            self.tests_run += 1
        
        # 计算准确率
        accuracy = self.tests_passed / self.tests_run if self.tests_run > 0 else 0
        
        # 保存结果
        self.accuracy_log.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "accuracy": accuracy,
            "samples": results
        })
        
        self._save_results()
        
        return {
            "status": "COMPLETE",
            "tests_run": len(samples),
            "tests_passed": sum(1 for r in results if r["match"]),
            "accuracy": accuracy,
            "details": results
        }
    
    def _save_results(self):
        """保存测试结果"""
        with open(self.results_path, 'w', encoding='utf-8') as f:
            json.dump(self.accuracy_log, f, ensure_ascii=False, indent=2)
    
    def get_accuracy_report(self) -> str:
        """获取准确率报告"""
        accuracy = self.tests_passed / self.tests_run if self.tests_run > 0 else 0
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║   🧪 语义碰撞测试报告                                        ║
╚══════════════════════════════════════════════════════════════╝

测试次数: {self.tests_run}
通过次数: {self.tests_passed}
准确率: {accuracy*100:.1f}%

{'✅ 准确率达标' if accuracy >= 0.8 else '⚠️ 准确率偏低，需要优化'}

{'='*60}
"""
        return report
    
    def auto_test_loop(self, interval: int = 100, max_tests: int = 10):
        """
        自动测试循环
        
        Args:
            interval: 每新增多少案例触发一次测试
            max_tests: 最大测试次数
        """
        print(f"🤖 自动碰撞测试启动 (每{interval}条案例测试一次)")
        
        test_count = 0
        while test_count < max_tests:
            cases = self.load_golden_cases()
            
            # 检查是否达到测试阈值
            if len(cases) >= interval * (test_count + 1):
                result = self.run_collision_test(sample_size=2)
                print(self.get_accuracy_report())
                test_count += 1
            
            # 等待新数据
            time.sleep(5)
        
        print("✅ 自动测试完成")


# CLI 测试
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   🧪 语义碰撞测试系统                                       ║")
    print("║   实时校验路由准确率                                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    tester = SemanticCollisionTest()
    
    # 执行测试
    result = tester.run_collision_test(sample_size=2)
    print(tester.get_accuracy_report())