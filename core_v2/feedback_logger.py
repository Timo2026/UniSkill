#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
反馈日志器 - 第三阶段核心模块
记录检索结果的用户反馈，用于持续优化

功能:
1. 记录每次检索的查询、结果、采纳情况
2. 支持用户反馈（有用/无用）
3. 定期分析反馈数据
4. 自动触发优化建议
"""

import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict

# 日志路径
FEEDBACK_DB = Path.home() / ".openclaw/workspace/data/retrieval_feedback.db"
FEEDBACK_JSONL = Path.home() / ".openclaw/workspace/logs/retrieval_feedback.jsonl"


@dataclass
class FeedbackRecord:
    """反馈记录"""
    retrieval_id: str
    query: str
    intent: str
    top_score: float
    results_count: int
    user_feedback: Optional[str]  # "useful", "not_useful", None
    adopted: bool  # 是否被采纳（用户是否基于结果继续操作）
    timestamp: str
    latency_ms: float


class FeedbackLogger:
    """
    反馈日志器
    
    记录用户对检索结果的反馈
    """
    
    def __init__(self):
        self.db_path = FEEDBACK_DB
        self.jsonl_path = FEEDBACK_JSONL
        
        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retrieval_feedback (
                retrieval_id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                intent TEXT NOT NULL,
                top_score REAL,
                results_count INTEGER,
                user_feedback TEXT,
                adopted INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                latency_ms REAL,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intent_timestamp 
            ON retrieval_feedback(intent, timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def log_retrieval(
        self,
        query: str,
        intent: str,
        top_score: float,
        results_count: int,
        latency_ms: float,
        session_id: Optional[str] = None
    ) -> str:
        """
        记录一次检索
        
        Returns:
            retrieval_id: 用于后续反馈关联
        """
        retrieval_id = f"ret_{int(time.time()*1000)}_{hash(query)%10000:04d}"
        timestamp = datetime.now().isoformat()
        
        record = FeedbackRecord(
            retrieval_id=retrieval_id,
            query=query,
            intent=intent,
            top_score=top_score,
            results_count=results_count,
            user_feedback=None,
            adopted=False,
            timestamp=timestamp,
            latency_ms=latency_ms
        )
        
        # 写入数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO retrieval_feedback 
            (retrieval_id, query, intent, top_score, results_count, 
             user_feedback, adopted, timestamp, latency_ms, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            retrieval_id, query, intent, top_score, results_count,
            None, 0, timestamp, latency_ms, session_id
        ))
        
        conn.commit()
        conn.close()
        
        # 同时写入JSONL（便于日志分析）
        with open(self.jsonl_path, 'a') as f:
            f.write(json.dumps({
                'retrieval_id': retrieval_id,
                'query': query,
                'intent': intent,
                'top_score': top_score,
                'results_count': results_count,
                'latency_ms': latency_ms,
                'timestamp': timestamp,
                'status': 'logged'
            }, ensure_ascii=False) + '\n')
        
        return retrieval_id
    
    def record_feedback(
        self,
        retrieval_id: str,
        feedback: str,  # "useful" or "not_useful"
        adopted: bool = False
    ):
        """
        记录用户反馈
        
        Args:
            retrieval_id: 检索ID
            feedback: 用户反馈
            adopted: 是否被采纳
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE retrieval_feedback 
            SET user_feedback = ?, adopted = ?
            WHERE retrieval_id = ?
        """, (feedback, int(adopted), retrieval_id))
        
        conn.commit()
        conn.close()
        
        # 写入JSONL
        with open(self.jsonl_path, 'a') as f:
            f.write(json.dumps({
                'retrieval_id': retrieval_id,
                'feedback': feedback,
                'adopted': adopted,
                'timestamp': datetime.now().isoformat(),
                'status': 'feedback_received'
            }, ensure_ascii=False) + '\n')
    
    def get_stats(self, days: int = 7) -> Dict:
        """
        获取反馈统计
        
        Args:
            days: 统计最近多少天
            
        Returns:
            统计数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查询最近N天的数据
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT intent, 
                   COUNT(*) as total,
                   SUM(CASE WHEN user_feedback = 'useful' THEN 1 ELSE 0 END) as useful,
                   SUM(CASE WHEN user_feedback = 'not_useful' THEN 1 ELSE 0 END) as not_useful,
                   AVG(top_score) as avg_score,
                   AVG(latency_ms) as avg_latency
            FROM retrieval_feedback
            WHERE timestamp >= ?
            GROUP BY intent
        """, (start_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for row in rows:
            intent, total, useful, not_useful, avg_score, avg_latency = row
            adoption_rate = useful / total if total > 0 else 0
            stats[intent] = {
                'total_queries': total,
                'useful_count': useful,
                'not_useful_count': not_useful,
                'adoption_rate': adoption_rate,
                'avg_score': avg_score or 0,
                'avg_latency_ms': avg_latency or 0,
                'needs_optimization': adoption_rate < 0.5 and total >= 10
            }
        
        return stats
    
    def get_low_adoption_intents(self, threshold: float = 0.5, min_queries: int = 10) -> List[str]:
        """
        获取采纳率低的意图
        
        Args:
            threshold: 采纳率阈值
            min_queries: 最小查询次数
            
        Returns:
            需要优化的意图列表
        """
        stats = self.get_stats(days=30)
        
        low_adoption = []
        for intent, data in stats.items():
            if data['adoption_rate'] < threshold and data['total_queries'] >= min_queries:
                low_adoption.append(intent)
        
        return low_adoption
    
    def generate_report(self) -> str:
        """
        生成反馈报告
        
        Returns:
            报告文本
        """
        stats = self.get_stats(days=7)
        
        if not stats:
            return "📊 最近7天无反馈数据"
        
        report_lines = [
            "📊 检索反馈周报",
            "=" * 40,
            ""
        ]
        
        for intent, data in stats.items():
            status = "✅" if data['adoption_rate'] >= 0.5 else "⚠️"
            report_lines.append(
                f"{status} {intent}: 采纳率 {data['adoption_rate']:.1%} "
                f"({data['useful_count']}/{data['total_queries']})"
            )
            
            if data['needs_optimization']:
                report_lines.append(f"   💡 建议: 补充数据或调整阈值")
        
        # 低采纳率意图
        low_intents = self.get_low_adoption_intents()
        if low_intents:
            report_lines.extend([
                "",
                "⚠️ 需优化的意图:",
                f"   {', '.join(low_intents)}"
            ])
        
        return "\n".join(report_lines)


# 全局实例（修复作用域问题）
_logger_instance = None

def get_logger() -> FeedbackLogger:
    """获取全局日志器"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = FeedbackLogger()
    return _logger_instance


# 测试
if __name__ == "__main__":
    logger = get_logger()
    
    print("=== 反馈日志器测试 ===")
    
    # 模拟检索记录
    rid1 = logger.log_retrieval(
        query="CNC铝合金报价",
        intent="cnc_quote",
        top_score=0.92,
        results_count=5,
        latency_ms=128.5
    )
    print(f"记录检索: {rid1}")
    
    # 模拟用户反馈
    logger.record_feedback(rid1, "useful", adopted=True)
    print("记录反馈: useful")
    
    # 获取统计
    stats = logger.get_stats(days=1)
    print(f"\n统计: {stats}")
    
    # 生成报告
    report = logger.generate_report()
    print(f"\n{report}")