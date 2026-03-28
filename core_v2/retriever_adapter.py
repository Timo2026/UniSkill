#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
检索适配器 - 将新检索器集成到UniversalSkillV2
替换原有的 LocalVectorRetriever
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# 导入新检索器
sys.path.insert(0, str(Path(__file__).parent))
from retriever import get_intent_aware_retriever, RetrievalResult


class RetrieverAdapter:
    """
    检索适配器
    
    将 IntentAwareRetriever 适配到原有接口
    """
    
    def __init__(self):
        self._retriever = get_intent_aware_retriever()
    
    def search(self, query: str, intent: str = "default", top_k: int = 5) -> Dict:
        """
        执行检索（兼容原接口）
        
        Args:
            query: 查询文本
            intent: 意图类型
            top_k: 返回结果数
            
        Returns:
            兼容原格式的结果字典
        """
        result = self._retriever.search(query, intent, top_k)
        
        # 转换为原格式
        return {
            "success": result.success,
            "results": result.items,
            "source": result.source,
            "latency_ms": result.latency_ms,
            "use_vector": result.use_vector,
            "error": result.error
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self._retriever.get_stats()


# 单例
_adapter: Optional[RetrieverAdapter] = None

def get_adapter() -> RetrieverAdapter:
    """获取适配器单例"""
    global _adapter
    if _adapter is None:
        _adapter = RetrieverAdapter()
    return _adapter


# 测试
if __name__ == "__main__":
    adapter = get_adapter()
    
    print("=== 检索适配器测试 ===")
    
    # CNC测试
    result = adapter.search("CNC铝合金报价", "cnc_quote")
    print(f"CNC查询: use_vector={result['use_vector']}, items={len(result['results'])}")
    
    # 非CNC测试
    result = adapter.search("写Python代码", "code_gen")
    print(f"代码查询: use_vector={result['use_vector']}, source={result['source']}")
    
    print(f"\n统计: {adapter.get_stats()}")