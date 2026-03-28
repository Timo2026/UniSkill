#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
检索日志与自动扩展模块
记录查询效果，自动扩展黄金数据集
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from threading import Lock

logger = logging.getLogger("RetrievalLogger")


class RetrievalLogger:
    """检索日志记录器"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".openclaw/workspace/logs/retrieval"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "queries.jsonl"
        self.lock = Lock()
        self._buffer: List[Dict] = []
        self._flush_interval = 10  # 每10条刷盘
    
    def log_query(
        self,
        query: str,
        intent: str,
        use_vector: bool,
        success: bool,
        latency_ms: float,
        result_count: int,
        top_score: Optional[float] = None
    ):
        """记录查询"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],  # 截断
            "intent": intent,
            "use_vector": use_vector,
            "success": success,
            "latency_ms": round(latency_ms, 2),
            "result_count": result_count,
            "top_score": round(top_score, 4) if top_score else None
        }
        
        with self.lock:
            self._buffer.append(entry)
            if len(self._buffer) >= self._flush_interval:
                self._flush()
    
    def _flush(self):
        """刷盘"""
        if not self._buffer:
            return
        
        try:
            with open(self.log_file, 'a') as f:
                for entry in self._buffer:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            self._buffer.clear()
            logger.debug(f"[日志] 刷盘完成")
        except Exception as e:
            logger.error(f"[日志] 刷盘失败: {e}")
    
    def get_stats(self, hours: int = 24) -> Dict:
        """获取统计"""
        if not self.log_file.exists():
            return {"total": 0}
        
        cutoff = time.time() - hours * 3600
        stats = {
            "total": 0,
            "vector_queries": 0,
            "rule_queries": 0,
            "success": 0,
            "failed": 0,
            "avg_latency_ms": 0,
            "intents": {}
        }
        
        latencies = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        # 检查时间范围
                        ts = datetime.fromisoformat(entry['timestamp']).timestamp()
                        if ts < cutoff:
                            continue
                        
                        stats['total'] += 1
                        if entry['use_vector']:
                            stats['vector_queries'] += 1
                        else:
                            stats['rule_queries'] += 1
                        
                        if entry['success']:
                            stats['success'] += 1
                        else:
                            stats['failed'] += 1
                        
                        latencies.append(entry['latency_ms'])
                        
                        # 意图分布
                        intent = entry['intent']
                        stats['intents'][intent] = stats['intents'].get(intent, 0) + 1
                        
                    except:
                        continue
        except Exception as e:
            logger.error(f"[日志] 读取失败: {e}")
        
        if latencies:
            stats['avg_latency_ms'] = round(sum(latencies) / len(latencies), 2)
        
        return stats


class AutoExpander:
    """自动扩展器"""
    
    def __init__(self, golden_path: Optional[Path] = None):
        self.golden_path = golden_path or Path.home() / ".openclaw/workspace/skills/universal-skill/data/golden_dataset.jsonl"
        self.candidates: List[Dict] = []
        self.lock = Lock()
    
    def add_candidate(
        self,
        query: str,
        intent: str,
        model: str,
        success: bool,
        quality_score: float = 0.8,
        keywords: Optional[List[str]] = None
    ):
        """添加候选数据"""
        if not success or quality_score < 0.7:
            return
        
        candidate = {
            "timestamp": datetime.now().isoformat(),
            "task_text": query,
            "intent": intent,
            "model": model,
            "success": success,
            "quality_score": quality_score,
            "keywords": keywords or []
        }
        
        with self.lock:
            self.candidates.append(candidate)
    
    def flush_to_golden(self, min_candidates: int = 100):
        """将候选写入黄金数据集"""
        if len(self.candidates) < min_candidates:
            return 0
        
        try:
            with open(self.golden_path, 'a') as f:
                for candidate in self.candidates:
                    f.write(json.dumps(candidate, ensure_ascii=False) + '\n')
            
            count = len(self.candidates)
            self.candidates.clear()
            logger.info(f"[扩展器] 写入 {count} 条黄金数据")
            return count
        except Exception as e:
            logger.error(f"[扩展器] 写入失败: {e}")
            return 0


# 单例
_logger: Optional[RetrievalLogger] = None
_expander: Optional[AutoExpander] = None

def get_logger() -> RetrievalLogger:
    global _logger
    if _logger is None:
        _logger = RetrievalLogger()
    return _logger

def get_expander() -> AutoExpander:
    global _expander
    if _expander is None:
        _expander = AutoExpander()
    return _expander