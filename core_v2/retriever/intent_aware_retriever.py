#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
意图感知检索器 - 意图感知混合检索架构
方案C实施：统一接口 + 多后端支持 + 自动扩展

核心功能：
1. 读取 retriever_config.json 配置
2. 根据意图选择检索策略
3. 支持JSON/FAISS/ChromaDB多种后端
4. 日志监控 + 自动扩展
"""

import sys
import json
import time
import logging
import requests
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntentAwareRetriever")


@dataclass
class RetrievalResult:
    """检索结果"""
    success: bool
    items: List[Dict]
    source: str
    latency_ms: float
    intent: str
    use_vector: bool
    error: Optional[str] = None


class VectorBackend(ABC):
    """向量后端抽象接口"""
    
    @abstractmethod
    def load(self, path: Path) -> bool:
        """加载索引"""
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """向量检索"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """返回索引条数"""
        pass


class JSONVectorBackend(VectorBackend):
    """JSON向量后端"""
    
    def __init__(self):
        self.data: List[Dict] = []
        self.embeddings: List[List[float]] = []
    
    def load(self, path: Path) -> bool:
        try:
            with open(path, 'r') as f:
                index = json.load(f)
            self.data = index.get('data', [])
            self.embeddings = [item.get('embedding', []) for item in self.data]
            logger.info(f"[JSON后端] 加载 {len(self.data)} 条索引")
            return True
        except Exception as e:
            logger.error(f"[JSON后端] 加载失败: {e}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        if not self.embeddings or not query_embedding:
            return []
        
        # 计算余弦相似度
        query = np.array(query_embedding)
        scores = []
        for i, emb in enumerate(self.embeddings):
            if len(emb) == 0:
                continue
            sim = np.dot(query, emb) / (np.linalg.norm(query) * np.linalg.norm(emb) + 1e-8)
            scores.append((sim, i))
        
        scores.sort(reverse=True)
        results = []
        for sim, idx in scores[:top_k]:
            item = self.data[idx].copy()
            item['score'] = float(sim)
            results.append(item)
        
        return results
    
    def count(self) -> int:
        return len(self.data)


class IntentAwareRetriever:
    """
    意图感知检索器
    
    核心逻辑：
    1. 读取 retriever_config.json
    2. 根据意图决定是否使用向量检索
    3. 调用对应后端检索
    4. 返回结果或跳过
    """
    
    DEFAULT_CONFIG = {
        "mode": "intent_aware",
        "rules": {
            "default": {"use_vector": False, "fallback_model": "qwen3.5-plus"}
        },
        "vector_index": None,
        "embedding_model": "nomic-embed-text",
        "ollama_url": "http://localhost:11434/api/embeddings"
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".openclaw/workspace/data/retriever_config.json"
        self.config: Dict = {}
        self.backend: Optional[VectorBackend] = None
        self.embedding_cache: Dict[str, List[float]] = {}
        self.stats = {
            "total_queries": 0,
            "vector_queries": 0,
            "rule_queries": 0,
            "cache_hits": 0,
            "errors": 0
        }
        
        self._load_config()
        self._init_backend()
    
    def _load_config(self):
        """加载配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"[检索器] 加载配置: {self.config_path}")
                logger.info(f"[检索器] 模式: {self.config.get('mode', 'unknown')}")
            else:
                self.config = self.DEFAULT_CONFIG
                logger.warning(f"[检索器] 配置不存在，使用默认配置")
        except Exception as e:
            self.config = self.DEFAULT_CONFIG
            logger.error(f"[检索器] 加载配置失败: {e}")
    
    def _init_backend(self):
        """初始化向量后端"""
        vector_index = self.config.get('vector_index')
        if not vector_index:
            logger.warning("[检索器] 未配置向量索引路径")
            return
        
        index_path = Path(vector_index)
        if not index_path.exists():
            logger.warning(f"[检索器] 向量索引不存在: {index_path}")
            return
        
        # 根据文件类型选择后端
        if index_path.suffix == '.json':
            self.backend = JSONVectorBackend()
            if self.backend.load(index_path):
                logger.info(f"[检索器] JSON后端初始化成功，索引数: {self.backend.count()}")
        else:
            logger.warning(f"[检索器] 不支持的索引格式: {index_path.suffix}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本向量"""
        # 缓存检查
        if text in self.embedding_cache:
            self.stats['cache_hits'] += 1
            return self.embedding_cache[text]
        
        ollama_url = self.config.get('ollama_url', 'http://localhost:11434/api/embeddings')
        model = self.config.get('embedding_model', 'nomic-embed-text')
        
        try:
            resp = requests.post(ollama_url, json={
                'model': model,
                'prompt': text
            }, timeout=30)
            embedding = resp.json().get('embedding', [])
            
            if embedding:
                self.embedding_cache[text] = embedding
            
            return embedding
        except Exception as e:
            logger.error(f"[检索器] 向量化失败: {e}")
            return None
    
    def should_use_vector(self, intent: str) -> bool:
        """判断是否使用向量检索"""
        rules = self.config.get('rules', {})
        
        # 查找意图对应的规则
        intent_rule = rules.get(intent, rules.get('default', {}))
        use_vector = intent_rule.get('use_vector', False)
        
        logger.debug(f"[检索器] 意图={intent}, use_vector={use_vector}")
        return use_vector
    
    def search(self, query: str, intent: str, top_k: int = 5) -> RetrievalResult:
        """
        执行检索
        
        Args:
            query: 查询文本
            intent: 意图类型
            top_k: 返回结果数
            
        Returns:
            检索结果
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        # 判断是否使用向量
        use_vector = self.should_use_vector(intent)
        
        if not use_vector:
            self.stats['rule_queries'] += 1
            return RetrievalResult(
                success=True,
                items=[],
                source="rule_fallback",
                latency_ms=(time.time() - start_time) * 1000,
                intent=intent,
                use_vector=False,
                error=None
            )
        
        # 向量检索
        if not self.backend:
            self.stats['errors'] += 1
            return RetrievalResult(
                success=False,
                items=[],
                source="none",
                latency_ms=(time.time() - start_time) * 1000,
                intent=intent,
                use_vector=True,
                error="向量后端未初始化"
            )
        
        # 获取向量
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            self.stats['errors'] += 1
            return RetrievalResult(
                success=False,
                items=[],
                source="none",
                latency_ms=(time.time() - start_time) * 1000,
                intent=intent,
                use_vector=True,
                error="向量化失败"
            )
        
        # 执行检索
        try:
            results = self.backend.search(query_embedding, top_k)
            self.stats['vector_queries'] += 1
            
            return RetrievalResult(
                success=True,
                items=results,
                source="vector_index",
                latency_ms=(time.time() - start_time) * 1000,
                intent=intent,
                use_vector=True
            )
        except Exception as e:
            self.stats['errors'] += 1
            return RetrievalResult(
                success=False,
                items=[],
                source="error",
                latency_ms=(time.time() - start_time) * 1000,
                intent=intent,
                use_vector=True,
                error=str(e)
            )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "backend_count": self.backend.count() if self.backend else 0,
            "config_mode": self.config.get('mode', 'unknown'),
            "cache_size": len(self.embedding_cache)
        }


# 单例
_retriever_instance: Optional[IntentAwareRetriever] = None

def get_intent_aware_retriever() -> IntentAwareRetriever:
    """获取检索器单例"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = IntentAwareRetriever()
    return _retriever_instance


# 测试
if __name__ == "__main__":
    retriever = get_intent_aware_retriever()
    
    print("=== 意图感知检索器测试 ===")
    print(f"配置: {retriever.config.get('mode')}")
    print(f"后端索引数: {retriever.backend.count() if retriever.backend else 0}")
    
    # 测试CNC意图
    print("\n测试1: CNC报价（应使用向量）")
    result = retriever.search("CNC铝合金报价", "cnc_quote")
    print(f"  use_vector: {result.use_vector}")
    print(f"  success: {result.success}")
    print(f"  items: {len(result.items)}")
    if result.items:
        print(f"  top1: {result.items[0].get('text', '')[:40]}...")
    
    # 测试非CNC意图
    print("\n测试2: 代码生成（应跳过向量）")
    result = retriever.search("写Python代码", "code_gen")
    print(f"  use_vector: {result.use_vector}")
    print(f"  source: {result.source}")
    
    print(f"\n统计: {retriever.get_stats()}")