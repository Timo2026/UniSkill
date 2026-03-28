#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
检索结果注入器 - 第二阶段核心模块
将向量检索结果注入苏格拉底引擎，提升提问精准度

核心功能:
1. 在苏格拉底探明前执行检索
2. 将检索结果作为上下文注入
3. 生成更精准的提问
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RetrievalInjector")


@dataclass
class RetrievedContext:
    """检索到的上下文"""
    query: str
    intent: str
    top_results: List[Dict]
    confidence: float
    has_relevant_data: bool


class RetrievalInjector:
    """
    检索结果注入器
    
    在苏格拉底探明前注入相关案例
    """
    
    # 意图关键词映射
    INTENT_KEYWORDS = {
        "cnc_quote": ["报价", "CNC", "加工", "零件", "材料", "铝合金", "不锈钢", "精度", "公差", "批量"],
        "code_gen": ["代码", "脚本", "函数", "Python", "JavaScript", "API", "自动化", "程序"],
        "creative_design": ["设计", "网页", "界面", "UI", "logo", "海报", "原型", "视觉效果"],
        "translation": ["翻译", "英文", "中文", "日语", "文档", "合同", "说明书"],
        "data_analysis": ["分析", "数据", "统计", "报表", "趋势", "预测", "可视化"],
        "doc_edit": ["编辑", "文档", "润色", "格式", "修改", "优化", "撰写", "文档"]
    }
    
    def __init__(self, retriever_adapter):
        """
        初始化注入器
        
        Args:
            retriever_adapter: 检索适配器
        """
        self.adapter = retriever_adapter
    
    def inject_context(self, user_input: str, intent_hint: Optional[str] = None) -> RetrievedContext:
        """
        注入检索上下文
        
        Args:
            user_input: 用户输入
            intent_hint: 意图提示（可选）
            
        Returns:
            检索到的上下文
        """
        # 推断意图
        intent = intent_hint or self._infer_intent(user_input)
        
        # 执行检索
        result = self.adapter.search(user_input, intent)
        
        # 构建上下文
        top_results = result.get('results', [])[:5]
        has_relevant = len(top_results) > 0
        
        # 计算置信度
        confidence = 0.0
        if top_results:
            scores = [r.get('score', 0) for r in top_results]
            confidence = sum(scores) / len(scores) if scores else 0.0
        
        return RetrievedContext(
            query=user_input,
            intent=intent,
            top_results=top_results,
            confidence=confidence,
            has_relevant_data=has_relevant
        )
    
    def _infer_intent(self, text: str) -> str:
        """推断意图"""
        text_lower = text.lower()
        
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[intent] = score
        
        if scores:
            best = max(scores, key=scores.get)
            if scores[best] > 0:
                return best
        
        return "default"
    
    def generate_context_prompt(self, context: RetrievedContext) -> str:
        """
        生成上下文提示词
        
        Args:
            context: 检索上下文
            
        Returns:
            注入到苏格拉底引擎的提示词
        """
        if not context.has_relevant_data:
            return ""
        
        prompt_parts = [
            "\n📚 **参考案例** (来自向量检索):\n"
        ]
        
        for i, result in enumerate(context.top_results[:3], 1):
            text = result.get('text', '')[:80]
            score = result.get('score', 0)
            prompt_parts.append(f"  {i}. [{score:.0%}] {text}...")
        
        prompt_parts.append(f"\n💡 基于以上案例，针对性提问:\n")
        
        return "\n".join(prompt_parts)
    
    def suggest_parameters(self, context: RetrievedContext) -> List[str]:
        """
        基于检索结果建议参数
        
        Args:
            context: 检索上下文
            
        Returns:
            建议参数列表
        """
        suggestions = []
        
        if context.intent == "cnc_quote" and context.has_relevant_data:
            suggestions.extend([
                "材料型号 (如: 6061-T6, 304不锈钢)",
                "加工数量 (单件/小批量/大批量)",
                "公差要求 (如: ±0.05mm)",
                "表面处理 (如: 阳极氧化)"
            ])
        elif context.intent == "code_gen" and context.has_relevant_data:
            suggestions.extend([
                "编程语言 (Python/JavaScript/其他)",
                "功能需求 (具体要实现什么)",
                "输入输出格式"
            ])
        elif context.intent == "creative_design" and context.has_relevant_data:
            suggestions.extend([
                "设计风格 (科技感/简约/商务)",
                "目标用户 (企业/个人)",
                "核心元素 (logo/配色/字体)"
            ])
        
        return suggestions


def create_injector() -> RetrievalInjector:
    """创建注入器实例"""
    from retriever_adapter import get_adapter
    adapter = get_adapter()
    return RetrievalInjector(adapter)


# 测试
if __name__ == "__main__":
    injector = create_injector()
    
    print("=== 检索注入器测试 ===")
    
    # 测试CNC查询
    context = injector.inject_context("CNC铝合金报价")
    print(f"\nCNC查询:")
    print(f"  意图: {context.intent}")
    print(f"  结果数: {len(context.top_results)}")
    print(f"  置信度: {context.confidence:.2%}")
    
    if context.top_results:
        print(f"  Top1: {context.top_results[0].get('text', '')[:50]}...")
    
    # 生成提示
    prompt = injector.generate_context_prompt(context)
    print(f"\n生成的提示词:\n{prompt}")
    
    # 建议参数
    suggestions = injector.suggest_parameters(context)
    print(f"建议参数: {suggestions}")