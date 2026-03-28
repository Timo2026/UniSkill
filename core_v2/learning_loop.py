#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习闭环 - 万能Skill V2
从V1借鉴，自动记住失败案例，越用越聪明

功能：
- 记录每次执行结果
- 分析失败模式
- 下次自动规避
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter


class LearningLoop:
    """
    学习闭环
    
    核心能力：
    1. 记住失败案例
    2. 分析失败原因
    3. 下次自动调整策略
    """
    
    DATA_PATH = Path(__file__).parent.parent / "data"
    LEARNING_FILE = DATA_PATH / "learning_history.json"
    
    def __init__(self):
        self.history: List[Dict] = []
        self.failure_patterns: Dict = {}
        self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        self.DATA_PATH.mkdir(parents=True, exist_ok=True)
        
        if self.LEARNING_FILE.exists():
            try:
                self.history = json.loads(self.LEARNING_FILE.read_text())
                self._analyze_failures()
            except:
                self.history = []
    
    def _save_history(self):
        """保存历史记录"""
        self.LEARNING_FILE.write_text(
            json.dumps(self.history, ensure_ascii=False, indent=2)
        )
    
    def _analyze_failures(self):
        """分析失败模式"""
        failures = [h for h in self.history if not h.get("success")]
        
        if not failures:
            return
        
        # 统计失败意图
        intent_counter = Counter(f.get("intent") for f in failures)
        
        # 统计失败原因
        error_counter = Counter(f.get("error_type") for f in failures if f.get("error_type"))
        
        self.failure_patterns = {
            "failed_intents": dict(intent_counter),
            "error_types": dict(error_counter),
            "total_failures": len(failures)
        }
    
    def record(
        self,
        intent: str,
        success: bool,
        model: str,
        execution_time: float,
        error: Optional[str] = None,
        convergence_rate: float = 0.0
    ):
        """记录执行结果"""
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "intent": intent,
            "success": success,
            "model": model,
            "execution_time": execution_time,
            "convergence_rate": convergence_rate,
            "error": error
        }
        
        # 记录错误类型
        if error:
            if "timeout" in error.lower():
                record["error_type"] = "timeout"
            elif "connection" in error.lower():
                record["error_type"] = "connection"
            elif "api" in error.lower():
                record["error_type"] = "api_error"
            else:
                record["error_type"] = "unknown"
        
        self.history.append(record)
        self._save_history()
        self._analyze_failures()
    
    def should_avoid(self, intent: str) -> bool:
        """判断是否应该避免某个意图"""
        if intent not in self.failure_patterns.get("failed_intents", {}):
            return False
        
        # 失败次数超过3次，建议避免
        fail_count = self.failure_patterns["failed_intents"][intent]
        return fail_count >= 3
    
    def get_best_model(self, intent: str) -> Optional[str]:
        """获取某个意图的最佳模型"""
        success_records = [
            h for h in self.history 
            if h.get("intent") == intent and h.get("success")
        ]
        
        if not success_records:
            return None
        
        # 统计成功率最高的模型
        model_counter = Counter(h.get("model") for h in success_records)
        return model_counter.most_common(1)[0][0] if model_counter else None
    
    def get_report(self) -> Dict:
        """获取学习报告"""
        total = len(self.history)
        success = sum(1 for h in self.history if h.get("success"))
        
        return {
            "total_tasks": total,
            "success_count": success,
            "failure_count": total - success,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "failure_patterns": self.failure_patterns
        }


# 全局实例
_loop: Optional[LearningLoop] = None

def get_learning_loop() -> LearningLoop:
    """获取学习闭环实例"""
    global _loop
    if _loop is None:
        _loop = LearningLoop()
    return _loop


# 测试
if __name__ == "__main__":
    loop = LearningLoop()
    print(f"历史记录: {len(loop.history)}条")
    print(f"失败模式: {loop.failure_patterns}")
