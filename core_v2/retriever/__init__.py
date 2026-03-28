#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
统一检索器接口 - 统一所有检索后端
支持：JSON / FAISS / ChromaDB

使用方法：
    from retriever import get_retriever
    
    retriever = get_retriever()
    result = retriever.search(query="CNC报价", intent="cnc_quote")
"""

from .intent_aware_retriever import (
    IntentAwareRetriever,
    RetrievalResult,
    get_intent_aware_retriever
)

__all__ = [
    'IntentAwareRetriever',
    'RetrievalResult',
    'get_intent_aware_retriever'
]