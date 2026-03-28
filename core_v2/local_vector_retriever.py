#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地向量检索器 - OpenClaw核心重构
直接调用Ollama + 知识库向量检索

大帅指示：
- 本地向量库优先
- 减少云端API依赖
- 自搜系统集成
"""

import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SearchResult:
    """检索结果"""
    content: str
    source: str
    score: float
    embedding_time: float


class LocalVectorRetriever:
    """
    本地向量检索器
    
    直接调用Ollama nomic-embed-text + 知识库向量检索
    
    优势：
    - 无需云端API
    - 响应快（100-250ms）
    - 数据本地化
    """
    
    # Ollama配置
    OLLAMA_URL = "http://localhost:11434/api/embeddings"
    EMBED_MODEL = "nomic-embed-text"
    
    # 知识库路径
    KB_PATH = Path.home() / ".openclaw/workspace/kb"
    
    def __init__(self):
        self.cache: Dict[str, List[float]] = {}
        self.documents: List[Dict] = []
        self.embeddings: List[List[float]] = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """加载知识库文档"""
        if not self.KB_PATH.exists():
            print("[向量检索器] ⚠️ 知识库目录不存在")
            return
        
        md_files = list(self.KB_PATH.rglob("*.md"))
        print(f"[向量检索器] 📚 加载 {len(md_files)} 个知识文件")
        
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8')
                # 分块（每块500字符）
                chunks = self._chunk_text(content, 500)
                for i, chunk in enumerate(chunks):
                    self.documents.append({
                        "content": chunk,
                        "source": str(f.relative_to(self.KB_PATH)),
                        "chunk_id": i
                    })
            except Exception as e:
                print(f"[向量检索器] ⚠️ 读取失败: {f.name}")
        
        print(f"[向量检索器] ✅ 文档块数: {len(self.documents)}")
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """文本分块"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取文本向量
        
        直接调用Ollama nomic-embed-text
        """
        # 检查缓存
        cache_key = text[:50]  # 用前50字符做缓存key
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            start = time.time()
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.EMBED_MODEL,
                    "prompt": text
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                
                # 缓存
                self.cache[cache_key] = embedding
                
                elapsed = (time.time() - start) * 1000
                print(f"[向量检索器] ✅ 嵌入耗时: {elapsed:.0f}ms")
                
                return embedding
            else:
                print(f"[向量检索器] ❌ Ollama错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[向量检索器] ❌ 嵌入失败: {e}")
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search(
        self, 
        query: str, 
        top_k: int = 3,
        threshold: float = 0.5
    ) -> List[SearchResult]:
        """
        向量检索
        
        Args:
            query: 查询文本
            top_k: 返回top-k结果
            threshold: 相似度阈值
            
        Returns:
            检索结果列表
        """
        start_time = time.time()
        
        # 1. 获取查询向量
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []
        
        # 2. 计算所有文档的相似度
        results = []
        for doc in self.documents:
            # 获取文档向量
            doc_embedding = self.get_embedding(doc["content"][:200])
            if not doc_embedding:
                continue
            
            # 计算相似度
            score = self.cosine_similarity(query_embedding, doc_embedding)
            
            if score >= threshold:
                results.append(SearchResult(
                    content=doc["content"],
                    source=doc["source"],
                    score=score,
                    embedding_time=(time.time() - start_time) * 1000
                ))
        
        # 3. 排序并返回top-k
        results.sort(key=lambda x: x.score, reverse=True)
        
        elapsed = (time.time() - start_time) * 1000
        print(f"[向量检索器] 🔍 检索完成: {len(results)}条结果, 耗时{elapsed:.0f}ms")
        
        return results[:top_k]
    
    def search_cnc_knowledge(self, query: str) -> Optional[str]:
        """
        CNC专用知识检索
        
        直接返回相关知识点
        """
        results = self.search(query, top_k=2, threshold=0.4)
        
        if not results:
            return None
        
        # 合并结果
        output = []
        for i, r in enumerate(results, 1):
            output.append(f"【参考{i}】{r.source}\n{r.content[:300]}...")
        
        return "\n\n".join(output)
    
    def get_status(self) -> Dict:
        """获取状态报告"""
        return {
            "embed_model": self.EMBED_MODEL,
            "documents_count": len(self.documents),
            "cache_size": len(self.cache),
            "kb_path": str(self.KB_PATH),
            "ollama_url": self.OLLAMA_URL
        }


# 全局实例（懒加载）
_retriever: Optional[LocalVectorRetriever] = None

def get_retriever() -> LocalVectorRetriever:
    """获取全局检索器实例"""
    global _retriever
    if _retriever is None:
        _retriever = LocalVectorRetriever()
    return _retriever


# 测试
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   本地向量检索器 - 测试                                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    retriever = LocalVectorRetriever()
    
    # 测试检索
    print("\n🔍 测试检索: 铝合金加工")
    results = retriever.search("铝合金加工精度", top_k=2)
    
    for r in results:
        print(f"\n来源: {r.source}")
        print(f"相似度: {r.score:.3f}")
        print(f"内容: {r.content[:100]}...")