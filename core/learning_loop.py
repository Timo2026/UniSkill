#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习闭环 - Learning Loop
收集反馈、优化策略、持续进化
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
import math


@dataclass
class FeedbackRecord:
    """反馈记录"""
    task_id: str
    timestamp: str
    intent: str
    skills_used: List[str]
    success: bool
    user_rating: Optional[int] = None  # 1-5
    user_comment: Optional[str] = None
    execution_time: float = 0.0
    quality_score: float = 0.0


@dataclass 
class SkillPerformance:
    """技能性能统计"""
    skill_id: str
    total_uses: int = 0
    successes: int = 0
    failures: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    success_rate: float = 0.0
    user_ratings: List[int] = field(default_factory=list)
    avg_rating: float = 0.0
    
    def update(self, success: bool, time: float, rating: Optional[int] = None):
        """更新统计"""
        self.total_uses += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1
        
        self.success_rate = self.successes / self.total_uses
        
        self.total_time += time
        self.avg_time = self.total_time / self.total_uses
        
        if rating is not None:
            self.user_ratings.append(rating)
            self.avg_rating = sum(self.user_ratings) / len(self.user_ratings)


class LearningLoop:
    """
    学习闭环
    
    功能：
    1. 反馈收集 - 记录每次执行的结果和用户反馈
    2. 性能统计 - 统计各技能的成功率、耗时等
    3. 权重调整 - 根据历史表现调整推荐权重
    4. 策略优化 - 学习最佳实践
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """初始化"""
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件
        self.feedback_file = self.data_dir / "feedback.json"
        self.performance_file = self.data_dir / "performance.json"
        self.weights_file = self.data_dir / "learning_weights.json"
        
        # 加载数据
        self.feedbacks: List[FeedbackRecord] = []
        self.performances: Dict[str, SkillPerformance] = {}
        self.weights: Dict[str, float] = {}
        
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        # 加载反馈
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedbacks = [FeedbackRecord(**r) for r in data]
            except:
                self.feedbacks = []
        
        # 加载性能统计
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for skill_id, perf in data.items():
                        self.performances[skill_id] = SkillPerformance(
                            skill_id=skill_id,
                            total_uses=perf.get("total_uses", 0),
                            successes=perf.get("successes", 0),
                            failures=perf.get("failures", 0),
                            total_time=perf.get("total_time", 0.0),
                            avg_time=perf.get("avg_time", 0.0),
                            success_rate=perf.get("success_rate", 0.0),
                            user_ratings=perf.get("user_ratings", []),
                            avg_rating=perf.get("avg_rating", 0.0)
                        )
            except:
                self.performances = {}
        
        # 加载权重
        if self.weights_file.exists():
            try:
                with open(self.weights_file, 'r', encoding='utf-8') as f:
                    self.weights = json.load(f)
            except:
                self.weights = {}
    
    def _save_data(self):
        """保存数据"""
        # 保存反馈
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            data = [vars(r) for r in self.feedbacks]
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存性能统计
        with open(self.performance_file, 'w', encoding='utf-8') as f:
            data = {
                skill_id: {
                    "total_uses": p.total_uses,
                    "successes": p.successes,
                    "failures": p.failures,
                    "total_time": p.total_time,
                    "avg_time": p.avg_time,
                    "success_rate": p.success_rate,
                    "user_ratings": p.user_ratings,
                    "avg_rating": p.avg_rating
                }
                for skill_id, p in self.performances.items()
            }
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存权重
        with open(self.weights_file, 'w', encoding='utf-8') as f:
            json.dump(self.weights, f, ensure_ascii=False, indent=2)
    
    def record_feedback(
        self,
        task_id: str,
        intent: str,
        skills_used: List[str],
        success: bool,
        execution_time: float,
        quality_score: float,
        user_rating: Optional[int] = None,
        user_comment: Optional[str] = None
    ):
        """
        记录反馈
        
        Args:
            task_id: 任务ID
            intent: 用户意图
            skills_used: 使用的技能列表
            success: 是否成功
            execution_time: 执行时间
            quality_score: 质量分数
            user_rating: 用户评分 (1-5)
            user_comment: 用户评论
        """
        # 创建反馈记录
        record = FeedbackRecord(
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
            intent=intent,
            skills_used=skills_used,
            success=success,
            user_rating=user_rating,
            user_comment=user_comment,
            execution_time=execution_time,
            quality_score=quality_score
        )
        
        self.feedbacks.append(record)
        
        # 更新性能统计
        for skill_id in skills_used:
            if skill_id not in self.performances:
                self.performances[skill_id] = SkillPerformance(skill_id=skill_id)
            
            self.performances[skill_id].update(success, execution_time, user_rating)
        
        # 更新权重
        self._update_weights(intent, skills_used, success, quality_score, user_rating)
        
        # 保存
        self._save_data()
        
        print(f"[LearningLoop] 已记录反馈: {task_id}")
    
    def _update_weights(
        self,
        intent: str,
        skills_used: List[str],
        success: bool,
        quality_score: float,
        user_rating: Optional[int]
    ):
        """更新权重"""
        # 意图-技能权重
        intent_skill_key = f"intent:{intent}:skill"
        
        for skill_id in skills_used:
            key = f"{intent_skill_key}:{skill_id}"
            
            # 基础权重更新
            old_weight = self.weights.get(key, 0.5)
            
            # 根据结果调整
            if success:
                adjustment = 0.05 * (quality_score if quality_score > 0 else 0.8)
            else:
                adjustment = -0.1
            
            # 用户评分影响
            if user_rating is not None:
                rating_factor = (user_rating - 3) / 10  # -0.2 到 0.2
                adjustment += rating_factor
            
            # 更新权重（限制在0.1-1.0之间）
            new_weight = max(0.1, min(1.0, old_weight + adjustment))
            self.weights[key] = new_weight
    
    def get_skill_weight(self, intent: str, skill_id: str) -> float:
        """获取技能权重"""
        key = f"intent:{intent}:skill:{skill_id}"
        return self.weights.get(key, 0.5)
    
    def get_recommended_skills(self, intent: str, top_k: int = 5) -> List[str]:
        """
        获取推荐技能
        
        Args:
            intent: 意图类型
            top_k: 返回数量
            
        Returns:
            推荐的技能ID列表
        """
        # 找出该意图相关的所有技能
        intent_skills = {}
        prefix = f"intent:{intent}:skill:"
        
        for key, weight in self.weights.items():
            if key.startswith(prefix):
                skill_id = key.replace(prefix, "")
                intent_skills[skill_id] = weight
        
        # 按权重排序
        sorted_skills = sorted(intent_skills.items(), key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in sorted_skills[:top_k]]
    
    def get_skill_stats(self, skill_id: str) -> Optional[SkillPerformance]:
        """获取技能统计"""
        return self.performances.get(skill_id)
    
    def get_overall_stats(self) -> Dict:
        """获取整体统计"""
        if not self.feedbacks:
            return {
                "total_tasks": 0,
                "success_rate": 0,
                "avg_time": 0,
                "avg_quality": 0
            }
        
        total = len(self.feedbacks)
        successes = sum(1 for f in self.feedbacks if f.success)
        total_time = sum(f.execution_time for f in self.feedbacks)
        total_quality = sum(f.quality_score for f in self.feedbacks if f.quality_score > 0)
        quality_count = sum(1 for f in self.feedbacks if f.quality_score > 0)
        
        return {
            "total_tasks": total,
            "success_rate": successes / total,
            "avg_time": total_time / total,
            "avg_quality": total_quality / quality_count if quality_count > 0 else 0
        }
    
    def generate_report(self) -> str:
        """生成学习报告"""
        stats = self.get_overall_stats()
        
        report = []
        report.append("=" * 50)
        report.append("学习闭环报告")
        report.append("=" * 50)
        report.append(f"总任务数: {stats['total_tasks']}")
        report.append(f"成功率: {stats['success_rate']:.1%}")
        report.append(f"平均耗时: {stats['avg_time']:.2f}s")
        report.append(f"平均质量: {stats['avg_quality']:.2f}")
        report.append("")
        
        report.append("技能性能排行:")
        report.append("-" * 50)
        
        # 按成功率排序
        sorted_perf = sorted(
            self.performances.items(),
            key=lambda x: (x[1].success_rate, x[1].total_uses),
            reverse=True
        )
        
        for skill_id, perf in sorted_perf[:10]:
            report.append(
                f"  {skill_id}: {perf.total_uses}次, "
                f"成功率{perf.success_rate:.1%}, "
                f"平均{perf.avg_time:.2f}s"
            )
        
        report.append("")
        report.append("最近反馈:")
        report.append("-" * 50)
        
        for fb in self.feedbacks[-5:]:
            status = "✅" if fb.success else "❌"
            rating = f" ⭐{fb.user_rating}" if fb.user_rating else ""
            report.append(f"  {status} {fb.task_id}: {fb.intent[:30]}{rating}")
        
        return "\n".join(report)
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """分析模式"""
        patterns = {
            "best_skills": [],      # 最佳技能
            "problem_skills": [],   # 问题技能
            "peak_hours": [],       # 高峰时段
            "common_intents": []    # 常见意图
        }
        
        # 最佳技能（成功率>80%，使用>5次）
        for skill_id, perf in self.performances.items():
            if perf.success_rate > 0.8 and perf.total_uses > 5:
                patterns["best_skills"].append({
                    "skill_id": skill_id,
                    "success_rate": perf.success_rate,
                    "uses": perf.total_uses
                })
            elif perf.success_rate < 0.5 and perf.total_uses > 3:
                patterns["problem_skills"].append({
                    "skill_id": skill_id,
                    "success_rate": perf.success_rate,
                    "uses": perf.total_uses
                })
        
        # 常见意图
        intent_counts = {}
        for fb in self.feedbacks:
            intent_counts[fb.intent] = intent_counts.get(fb.intent, 0) + 1
        
        patterns["common_intents"] = sorted(
            intent_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return patterns


# 测试
if __name__ == "__main__":
    loop = LearningLoop()
    
    # 模拟反馈
    loop.record_feedback(
        task_id="task_001",
        intent="generate",
        skills_used=["pdf-generator", "cnc-quote-coach"],
        success=True,
        execution_time=2.5,
        quality_score=0.85,
        user_rating=4
    )
    
    loop.record_feedback(
        task_id="task_002",
        intent="analyze",
        skills_used=["data-analyzer"],
        success=True,
        execution_time=1.2,
        quality_score=0.92,
        user_rating=5
    )
    
    # 打印报告
    print(loop.generate_report())