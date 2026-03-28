#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Router V2 - 基于向量语义的智能模型路由器
四大补丁注入版：收敛熔断 + 硬件降级 + 透明决策 + Sqlite3绕过

方案三实施：让万能Skill V2学会"根据任务自动选模型"
"""

# ⭐ 补丁4：Sqlite3版本绕过（pysqlite3-binary）
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("✅ pysqlite3 已注入，ChromaDB 可用")
except ImportError:
    print("⚠️ pysqlite3-binary 未安装，使用规则兜底")

import json
import time
import psutil
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ChromaDB 向量库
CHROMA_AVAILABLE = False
try:
    import chromadb
    import sqlite3
    print(f"  sqlite3版本: {sqlite3.sqlite_version}")
    CHROMA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ChromaDB导入失败: {e}")

# 本地嵌入模型 (通过 Ollama API)
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
OLLAMA_EMBED_MODEL = "nomic-embed-text"


class ModelRouter:
    """
    智能模型路由器
    
    核心能力：
    1. 向量语义检索历史案例
    2. 收敛度熔断机制（拒绝模糊需求）
    3. 硬件压力动态降级（内存>85%惩罚本地模型）
    4. 规则兜底路由
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        chroma_path: Optional[str] = None,
        collection_name: str = "task_history"
    ):
        # 配置路径
        # model_router_v2.py -> core_v2 -> universal-skill -> config
        base_dir = Path(__file__).parent.parent  # universal-skill 目录
        self.config_path = config_path or str(
            base_dir / "config" / "model_capabilities.json"
        )
        
        # 加载模型能力配置
        self.capabilities = self._load_capabilities()
        self.default_model = "qwen3-max"
        
        # ⭐ 冷备份：JSONL扁平存储（绕过向量库）
        self.golden_path = base_dir / "data" / "golden_dataset.jsonl"
        self.golden_data: List[Dict] = self._load_golden_dataset()
        
        # ChromaDB 初始化（可选）
        self.chroma_client = None
        self.collection = None
        self.use_vector = False
        
        if CHROMA_AVAILABLE:
            try:
                chroma_path = chroma_path or str(
                    base_dir / "data" / "chroma"
                )
                self.chroma_client = chromadb.PersistentClient(path=chroma_path)
                self.collection = self.chroma_client.get_or_create_collection(
                    collection_name
                )
                self.use_vector = True
                print(f"✅ ChromaDB 已连接: {chroma_path}")
            except Exception as e:
                print(f"⚠️ ChromaDB 初始化失败: {e}，使用JSONL冷备份")
        
        # ⭐ 沙盒反馈闭环
        self.sandbox_feedback: Dict[str, float] = {}  # model -> penalty
        
        # 状态缓存
        self.last_hardware_check = 0
        self.hardware_cache = None
    
    def _load_golden_dataset(self) -> List[Dict]:
        """加载黄金案例JSONL"""
        if not self.golden_path.exists():
            return []
        try:
            data = []
            with open(self.golden_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            print(f"✅ 黄金案例库加载: {len(data)}条")
            return data
        except Exception as e:
            print(f"⚠️ 黄金案例加载失败: {e}")
            return []
    
    def _load_capabilities(self) -> Dict:
        """加载模型能力配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ 配置文件不存在，使用默认配置")
            return self._default_capabilities()
        except Exception as e:
            print(f"⚠️ 配置加载失败: {e}")
            return self._default_capabilities()
    
    def _default_capabilities(self) -> Dict:
        """默认模型能力"""
        return {
            "qwen2.5:0.5b": {
                "tags": ["快速", "简单"],
                "strengths": ["极低延迟"],
                "deployment": "local",
                "cost_weight": 0.1
            },
            "glm-5": {
                "tags": ["创意", "中文"],
                "strengths": ["拟人化表达"],
                "deployment": "cloud",
                "cost_weight": 0.6
            },
            "qwen3-max": {
                "tags": ["通用", "复杂"],
                "strengths": ["顶级理解力"],
                "deployment": "cloud",
                "cost_weight": 1.0
            }
        }
    
    def _embed(self, text: str) -> Optional[List[float]]:
        """通过 Ollama API 获取文本向量"""
        try:
            response = requests.post(
                OLLAMA_EMBED_URL,
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("embedding", [])
            return None
        except Exception as e:
            print(f"⚠️ 向量化失败: {e}")
            return None
    
    def _get_hardware_penalty(self, model_name: str) -> float:
        """
        补丁2: 硬件压力动态降级
        
        Returns:
            权重系数 (0.2-1.2)
        """
        # 缓存硬件状态（5秒内不重复查询）
        now = time.time()
        if now - self.last_hardware_check < 5 and self.hardware_cache:
            mem_percent = self.hardware_cache
        else:
            mem_percent = psutil.virtual_memory().percent / 100.0
            self.hardware_cache = mem_percent
            self.last_hardware_check = now
        
        model_info = self.capabilities.get(model_name, {})
        deployment = model_info.get("deployment", "cloud")
        
        # 内存超过85% → 重度惩罚本地模型
        if mem_percent > 0.85 and deployment == "local":
            print(f"⚠️ 物理内存告急 ({mem_percent*100:.0f}%)，降权本地模型 {model_name}")
            return 0.2
        
        # 内存充足 + 简单任务 → 提权本地模型
        if mem_percent < 0.60 and deployment == "local":
            return 1.2
        
        return 1.0
    
    def route(
        self,
        task_text: str,
        convergence_score: float = 1.0,
        task_type: Optional[str] = None
    ) -> Dict:
        """
        核心路由决策
        
        Args:
            task_text: 任务描述文本
            convergence_score: 苏格拉底收敛系数 (0-1)
            task_type: 任务类型标签（可选）
        
        Returns:
            {
                "model": "模型名称",
                "reason": "决策原因",
                "provider": "ollama/dashscope",
                "confidence": 置信度
            }
        """
        
        # === 补丁1: 收敛度熔断机制 ===
        if convergence_score < 0.7:
            print(f"🛑 意图收敛度过低 ({convergence_score*100:.0f}%)，路由器拒绝分配算力模型")
            return {
                "model": "INTERNAL_PROMPT_REFINER",
                "reason": f"收敛度不足({convergence_score*100:.0f}%)，打回苏格拉底引擎",
                "provider": "internal",
                "confidence": 0.0,
                "action": "probe_more"
            }
        
        # === 向量语义检索 ===
        if self.use_vector and self.collection:
            query_vector = self._embed(task_text)
            if query_vector:
                try:
                    results = self.collection.query(
                        query_embeddings=[query_vector],
                        n_results=5,
                        include=["metadatas", "distances"]
                    )
                    
                    retrieved = results.get('metadatas', [[]])[0]
                    distances = results.get('distances', [[]])[0]
                    
                    if retrieved and distances:
                        avg_dist = sum(distances) / len(distances)
                        
                        # 有足够相似的历史案例
                        if avg_dist < 0.7:
                            model_scores = {}
                            for item in retrieved:
                                model = item.get("model")
                                if model and model not in model_scores:
                                    model_scores[model] = self._score_model_from_history(
                                        model, retrieved
                                    )
                            
                            # 应用硬件惩罚 + 沙盒反馈
                            for model in model_scores:
                                model_scores[model] *= self._get_hardware_penalty(model)
                                model_scores[model] *= self._get_sandbox_penalty(model)
                            
                            best_model = max(model_scores, key=model_scores.get) if model_scores else self.default_model
                            
                            if model_scores.get(best_model, 0) >= 0.5:
                                return {
                                    "model": best_model,
                                    "reason": f"语义匹配(Dist:{avg_dist:.2f})+硬件检查",
                                    "provider": self._get_provider(best_model),
                                    "confidence": model_scores.get(best_model, 0),
                                    "action": "execute"
                                }
                except Exception as e:
                    print(f"⚠️ 向量检索失败: {e}")
        
        # === JSONL冷备份检索（关键词匹配）===
        if self.golden_data:
            matched = self._keyword_match(task_text)
            if matched:
                model = matched.get("model")
                score = matched.get("quality_score", 0.5)
                
                # 应用硬件惩罚 + 沙盒反馈
                score *= self._get_hardware_penalty(model)
                score *= self._get_sandbox_penalty(model)
                
                if score >= 0.5:
                    return {
                        "model": model,
                        "reason": f"关键词匹配(JSONL)+黄金案例",
                        "provider": self._get_provider(model),
                        "confidence": score,
                        "matched_case": matched.get("intent"),
                        "action": "execute"
                    }
        
        # === 规则兜底路由 ===
        best_model = self._rule_based_route(task_text)
        hardware_penalty = self._get_hardware_penalty(best_model)
        
        return {
            "model": best_model,
            "reason": "规则兜底路由",
            "provider": self._get_provider(best_model),
            "confidence": 0.6 * hardware_penalty,
            "action": "execute"
        }
    
    def _score_model_from_history(self, model: str, retrieved: List[Dict]) -> float:
        """根据历史记录计算模型得分"""
        total_score = 0
        count = 0
        
        for item in retrieved:
            if item.get("model") == model:
                score = item.get("quality_score", 0.5)
                
                # 用户反馈加权
                feedback = item.get("user_feedback", 0)
                if feedback == 1:
                    score += 0.2
                elif feedback == -1:
                    score -= 0.2
                
                # 成功与否
                if not item.get("success", True):
                    score -= 0.5
                
                total_score += max(0, min(score, 1))
                count += 1
        
        return total_score / count if count > 0 else 0
    
    def _keyword_match(self, task_text: str) -> Optional[Dict]:
        """⭐ 关键词匹配：JSONL冷备份检索"""
        text_lower = task_text.lower()
        best_match = None
        best_score = 0
        
        for case in self.golden_data:
            keywords = case.get("keywords", [])
            # 计算关键词匹配度
            match_count = sum(1 for k in keywords if k.lower() in text_lower)
            match_score = match_count / len(keywords) if keywords else 0
            
            if match_score > best_score and match_score >= 0.5:  # 至少匹配一半关键词
                best_score = match_score
                best_match = case
        
        if best_match:
            print(f"  🔍 关键词匹配: {best_match.get('intent')} (得分:{best_score:.2f})")
        return best_match
    
    def _get_sandbox_penalty(self, model: str) -> float:
        """
        ⭐ 补丁4：沙盒反馈闭环
        
        如果模型生成的代码在沙盒运行失败，临时扣除权重
        """
        penalty = self.sandbox_feedback.get(model, 1.0)
        
        if penalty < 1.0:
            print(f"  ⚠️ 沙盒反馈惩罚: {model} (系数:{penalty:.2f})")
        
        return penalty
    
    def record_sandbox_feedback(self, model: str, sandbox_passed: bool):
        """
        ⭐ 记录沙盒执行结果
        
        Args:
            model: 模型名称
            sandbox_passed: 沙盒是否通过
        """
        if sandbox_passed:
            # 通过：逐渐恢复权重
            current = self.sandbox_feedback.get(model, 1.0)
            self.sandbox_feedback[model] = min(1.0, current + 0.1)
        else:
            # 失败：惩罚权重
            self.sandbox_feedback[model] = 0.5
            print(f"🛑 沙盒失败惩罚: {model} → 权重降至0.5")
    
    def _rule_based_route(self, task_text: str) -> str:
        """规则路由（方案二）"""
        text_lower = task_text.lower()
        
        # CNC报价 → qwen3-max
        if any(k in text_lower for k in ["报价", "cnc", "工艺", "加工", "材质", "精度", "分析", "成本"]):
            return "qwen3-max"
        
        # 创意设计 → glm-5
        if any(k in text_lower for k in ["设计", "创意", "邮件", "润色", "排版", "文案", "bd"]):
            return "glm-5"
        
        # 编程 → deepseek-v3 (如果有) 或 qwen3-max
        if any(k in text_lower for k in ["代码", "编程", "python", "脚本", "函数", "算法", "调试"]):
            if "deepseek-v3" in self.capabilities:
                return "deepseek-v3"
            return "qwen3-max"
        
        # 长文本 → kimi-k2.5
        if len(task_text) > 2000 or any(k in text_lower for k in ["文档", "pdf", "总结", "报告"]):
            if "kimi-k2.5" in self.capabilities:
                return "kimi-k2.5"
        
        # 极短消息 → 本地小模型
        if len(task_text) < 50:
            return "qwen2.5:0.5b"
        
        return self.default_model
    
    def _get_provider(self, model: str) -> str:
        """获取模型提供商"""
        model_info = self.capabilities.get(model, {})
        deployment = model_info.get("deployment", "cloud")
        return "ollama" if deployment == "local" else "dashscope"
    
    def record_execution(
        self,
        task_text: str,
        model: str,
        success: bool,
        quality_score: float = 0.5,
        user_feedback: int = 0,
        task_type: Optional[str] = None,
        sandbox_passed: Optional[bool] = None,  # ⭐ 新增：沙盒反馈
        keywords: Optional[List[str]] = None    # ⭐ 新增：关键词提取
    ) -> bool:
        """
        记录执行结果到向量库 + JSONL冷备份
        
        Args:
            task_text: 任务描述
            model: 使用的模型
            success: 是否成功
            quality_score: 质量评分 (0-1)
            user_feedback: 用户反馈 (1赞, -1踩, 0无)
            task_type: 任务类型
            sandbox_passed: 沙盒是否通过
            keywords: 关键词列表
        
        Returns:
            是否成功记录
        """
        # ⭐ 记录沙盒反馈
        if sandbox_passed is not None:
            self.record_sandbox_feedback(model, sandbox_passed)
        
        # ⭐ JSONL冷备份存储（总是执行）
        jsonl_saved = self._save_to_jsonl(
            task_text, model, success, quality_score, 
            user_feedback, task_type, sandbox_passed, keywords
        )
        
        # ChromaDB向量存储（如果可用）
        if self.use_vector and self.collection:
            try:
                doc_id = f"exec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(task_text) % 10000}"
                
                metadata = {
                    "task_text": task_text[:500],
                    "model": model,
                    "success": success,
                    "quality_score": quality_score,
                    "user_feedback": user_feedback,
                    "task_type": task_type or "unknown",
                    "sandbox_passed": sandbox_passed,
                    "timestamp": datetime.now().isoformat()
                }
                
                embedding = self._embed(task_text[:500])
                if embedding:
                    self.collection.upsert(
                        ids=[doc_id],
                        embeddings=[embedding],
                        metadatas=[metadata]
                    )
                    print(f"✅ ChromaDB记录: {doc_id}")
            except Exception as e:
                print(f"⚠️ ChromaDB记录失败: {e}")
        
        return jsonl_saved
    
    def _save_to_jsonl(
        self,
        task_text: str,
        model: str,
        success: bool,
        quality_score: float,
        user_feedback: int,
        task_type: Optional[str],
        sandbox_passed: Optional[bool],
        keywords: Optional[List[str]]
    ) -> bool:
        """⭐ JSONL冷备份存储"""
        try:
            record = {
                "timestamp": datetime.now().isoformat(),
                "task_text": task_text[:200],
                "intent": task_type or "unknown",
                "model": model,
                "success": success,
                "quality_score": quality_score,
                "user_feedback": user_feedback,
                "sandbox_passed": sandbox_passed,
                "keywords": keywords or self._extract_keywords(task_text)
            }
            
            # 追加写入JSONL
            with open(self.golden_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
            # 更新内存缓存
            self.golden_data.append(record)
            
            print(f"✅ JSONL冷备份: {task_type}")
            return True
        except Exception as e:
            print(f"⚠️ JSONL存储失败: {e}")
            return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """简单关键词提取"""
        # 工业关键词词典
        industry_keywords = [
            "报价", "CNC", "工艺", "加工", "材质", "精度", "铝合金", "不锈钢",
            "设计", "创意", "网页", "邮件", "文案",
            "代码", "Python", "脚本", "函数", "算法",
            "文档", "PDF", "分析", "报告"
        ]
        
        found = [k for k in industry_keywords if k.lower() in text.lower()]
        return found[:5] if found else ["通用"]
    
    def get_stats(self) -> Dict:
        """获取路由器统计"""
        stats = {
            "chroma_available": self.use_vector,
            "jsonl_available": len(self.golden_data) > 0,
            "golden_cases": len(self.golden_data),
            "models_configured": list(self.capabilities.keys()),
            "default_model": self.default_model,
            "sandbox_feedback": dict(self.sandbox_feedback),
            "hardware_status": {
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(interval=0.1)
            }
        }
        
        if self.collection:
            try:
                stats["chroma_count"] = self.collection.count()
            except:
                stats["chroma_count"] = 0
        
        return stats


# ============ CLI 测试接口 ============

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   Model Router V2 - 向量语义智能路由器                      ║")
    print("║   四大补丁：收敛熔断+硬件降级+透明决策+沙盒闭环+Sqlite3绕过║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    router = ModelRouter()
    
    # 显示状态
    stats = router.get_stats()
    print(f"\n📊 路由器状态:")
    print(f"  ChromaDB: {'✅' if stats['chroma_available'] else '❌'}")
    print(f"  JSONL冷备份: {'✅' if stats['jsonl_available'] else '❌'} ({stats['golden_cases']}条)")
    print(f"  配置模型: {stats['models_configured']}")
    print(f"  内存使用: {stats['hardware_status']['memory_percent']}%")
    if stats['sandbox_feedback']:
        print(f"  沙盒惩罚: {stats['sandbox_feedback']}")
    print(f"  配置模型: {stats['models_configured']}")
    print(f"  内存使用: {stats['hardware_status']['memory_percent']}%")
    
    # 测试路由
    print("\n🧪 测试路由决策:")
    test_cases = [
        ("帮我做个CNC铝合金报价", 0.9),
        ("你好，今天天气怎么样", 0.95),
        ("帮我写个Python爬虫脚本", 0.85),
        ("帮我做个报价", 0.5),  # 低收敛度测试
        ("设计一个陆家嘴蹦迪网页，需要创意", 0.9),
    ]
    
    for task, convergence in test_cases:
        result = router.route(task, convergence_score=convergence)
        print(f"\n任务: {task[:30]}...")
        print(f"  收敛度: {convergence*100:.0f}%")
        print(f"  模型: {result['model']}")
        print(f"  原因: {result['reason']}")
        print(f"  置信度: {result['confidence']:.2f}")