#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Skill V2 主执行器 - OpenClaw核心重构
苏格拉底+5W2H深度锚定版 + Model Router V2 四大补丁集成版 + 海狸交底协议

大帅指示：
- 禁止在需求不明时执行任何真正的工作
- 引入动态收敛系数
- 本地向量库优先
- 智能模型路由（方案三）
- 沙盒反馈闭环（补丁4）
- 绝密公开协议（内省）
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from socratic_engine import SocraticEngine, ConvergenceLevel
from five_w2h_filter import FiveW2HFilter
from convergence_checker import ConvergenceChecker, ConvergenceAction
from x_styler import XStylerRenderer
from local_vector_retriever import LocalVectorRetriever, get_retriever
from model_router_v2 import ModelRouter
from introspection_trigger import trigger_introspection  # ⭐ 新增：海狸交底口令


class UniversalSkillV2:
    """
    Universal Skill V2 - 苏格拉底+5W2H深度锚定版 + 智能模型路由
    
    核心原则：
    1. 禁止直接执行
    2. 先探明再工作
    3. 收敛系数>0.7才启动沙盒
    4. 本地向量库优先
    5. 智能模型路由（根据任务自动选模型）
    """
    
    def __init__(self):
        # 核心组件
        self.socratic = SocraticEngine()
        self.filter = FiveW2HFilter()
        self.checker = ConvergenceChecker()
        self.renderer = XStylerRenderer()
        
        # ⭐ 新增：智能模型路由器
        self.router = ModelRouter()
        
        # 本地向量检索（懒加载）
        self._retriever: Optional[LocalVectorRetriever] = None
        
        # 执行状态
        self.status = "IDLE"
        self.anchor_data: Dict = {}
        self.convergence_rate = 0.0
        
        # 路由决策（新增）
        self.route_decision: Dict = {}
        
        # 反馈数据
        self.feedback_path = Path(__file__).parent.parent / "data" / "feedback_v2.json"
        self._ensure_data_dir()
    
    @property
    def retriever(self) -> LocalVectorRetriever:
        """懒加载向量检索器"""
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.feedback_path.exists():
            self.feedback_path.write_text("[]")
    
    def execute(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """
        主执行入口
        
        流程：
        0. ⭐ 口令检测（海狸交底）
        1. 苏格拉底探明
        2. 收敛检查
        3. 模型路由决策
        4. 本地向量检索
        5. 执行并返回
        
        Returns:
            X-Styler渲染的结果卡片
        """
        # ⭐ 补丁5：海狸交底口令检测
        introspection_result = trigger_introspection(user_input)
        if introspection_result.get("triggered"):
            return {
                "status": "INTROSPECTION_TRIGGERED",
                "trigger_word": introspection_result["trigger_word"],
                "report": introspection_result["report"],
                "report_path": introspection_result["report_path"],
                "persona": "🦫 海狸全量交底"
            }
        
        start_time = time.time()
        self.status = "PROBING"
        
        print(f"\n{'='*60}")
        print(f"[UniversalSkillV2] 启动")
        print(f"  输入: {user_input[:50]}...")
        print(f"{'='*60}")
        
        # === 第一步：苏格拉底探明 ===
        print("\n[1/5] 苏格拉底探明...")
        probe_result = self.socratic.start_engine(user_input)
        
        # === 第二步：收敛检查 ===
        print("\n[2/5] 收敛检查...")
        convergence_result = self.checker.check(
            self.socratic.anchor_data.__dict__,
            probe_result["intent_guess"]
        )
        
        self.convergence_rate = convergence_result.convergence_rate
        print(f"  收敛系数: {self.convergence_rate*100:.0f}%")
        print(f"  动作: {convergence_result.action.value}")
        
        # === 判断是否可以执行 ===
        if convergence_result.action == ConvergenceAction.REJECT:
            return self._reject_execution(convergence_result)
        
        if convergence_result.action == ConvergenceAction.PROBE_MORE:
            # 返回探明卡片（需要用户补充信息）
            return self._render_probe_card(probe_result, convergence_result)
        
        # === 第三步：智能模型路由 ⭐ 新增 ===
        print("\n[3/5] 模型路由决策...")
        self.route_decision = self.router.route(
            task_text=user_input,
            convergence_score=self.convergence_rate,
            task_type=probe_result["intent_guess"]
        )
        print(f"  🎯 模型: {self.route_decision['model']}")
        print(f"  📝 原因: {self.route_decision['reason']}")
        print(f"  📊 置信度: {self.route_decision['confidence']:.2f}")
        
        # 路由器拒绝（收敛度不足）
        if self.route_decision.get("action") == "probe_more":
            return self._reject_execution(convergence_result)
        
        # === 第四步：本地向量检索 ===
        print("\n[4/5] 本地向量检索...")
        local_results = self._local_search(user_input)
        
        # === 第五步：执行并返回 ===
        print("\n[5/5] 执行...")
        execution_result = self._execute_with_anchor(
            user_input, 
            probe_result["intent_guess"],
            local_results,
            self.route_decision  # ⭐ 传入路由决策
        )
        
        # ⭐ 补丁4：沙盒反馈闭环
        sandbox_passed = execution_result.get("sandbox_passed", True)
        
        # 记录反馈（包含路由决策 + 沙盒状态）
        execution_time = time.time() - start_time
        self._record_feedback(
            intent=probe_result["intent_guess"],
            success=execution_result.get("success", False),
            execution_time=execution_time,
            model=self.route_decision["model"],
            convergence_rate=self.convergence_rate,
            sandbox_passed=sandbox_passed  # ⭐ 新增
        )
        
        # 记录到路由器历史库（用于学习）+ 沙盒反馈
        self.router.record_execution(
            task_text=user_input,
            model=self.route_decision["model"],
            success=execution_result.get("success", False),
            quality_score=0.5,
            task_type=probe_result["intent_guess"],
            sandbox_passed=sandbox_passed  # ⭐ 补丁4：沙盒反馈闭环
        )
        
        # 渲染结果
        return {
            "status": "SUCCESS",
            "convergence_rate": self.convergence_rate,
            "execution_time": execution_time,
            "route_decision": self.route_decision,  # ⭐ 新增路由决策
            "result": execution_result,
            "local_sources": [r.source for r in local_results] if local_results else []
        }
    
    def _local_search(self, query: str) -> List:
        """本地向量检索"""
        try:
            results = self.retriever.search(query, top_k=3, threshold=0.4)
            print(f"  🔍 本地检索: {len(results)}条结果")
            return results
        except Exception as e:
            print(f"  ⚠️ 本地检索失败: {e}")
            return []
    
    def _execute_with_anchor(
        self, 
        user_input: str, 
        intent: str,
        local_results: List,
        route_decision: Dict  # ⭐ 新增参数
    ) -> Dict:
        """带锚点的执行"""
        # 检查本地结果是否足够
        if local_results and any(r.score > 0.7 for r in local_results):
            print("  ✅ 本地向量库命中，直接返回")
            best = local_results[0]
            return {
                "success": True,
                "content": best.content,
                "source": best.source,
                "score": best.score,
                "model": "local_vector",
                "provider": "ollama"
            }
        
        # 使用路由决策的模型
        selected_model = route_decision.get("model", "qwen3-max")
        provider = route_decision.get("provider", "dashscope")
        
        print(f"  🎯 执行模型: {selected_model} ({provider})")
        
        # 本地不够，返回需要更多信息
        print("  ⚠️ 本地向量库未命中，需要更多参数")
        return {
            "success": True,
            "content": f"基于您的需求，建议补充以下参数：\n\n{self._get_missing_params(intent)}",
            "model": selected_model,  # ⭐ 使用路由决策
            "provider": provider,
            "route_reason": route_decision.get("reason", "unknown")
        }
    
    def _get_missing_params(self, intent: str) -> str:
        """获取缺失参数说明"""
        if intent == "cnc_quote":
            return """- 材质：铝合金6061 / 不锈钢304 / 其他
- 精度：±0.01mm / ±0.05mm / ±0.1mm
- 数量：单件 / 小批量 / 大批量"""
        elif intent == "code_gen":
            return """- 语言：Python / JavaScript / 其他
- 功能：具体要实现什么？
- 输入输出：参数和返回值"""
        return "请详细描述您的需求"
    
    def _reject_execution(self, convergence_result) -> Dict:
        """拒绝执行"""
        self.status = "REJECTED"
        return {
            "status": "REJECTED",
            "convergence_rate": self.convergence_rate,
            "message": convergence_result.message,
            "missing_dimensions": convergence_result.missing_dimensions,
            "warnings": convergence_result.warnings
        }
    
    def _render_probe_card(self, probe_result: Dict, convergence_result) -> Dict:
        """渲染探明卡片"""
        self.status = "PROBING"
        return {
            "status": "PROBING",
            "convergence_rate": self.convergence_rate,
            "questions": probe_result["questions"],
            "message": convergence_result.message,
            "missing_dimensions": convergence_result.missing_dimensions
        }
    
    def _record_feedback(
        self, 
        intent: str, 
        success: bool, 
        execution_time: float,
        model: str,
        convergence_rate: float,
        sandbox_passed: bool = True  # ⭐ 补丁4：沙盒反馈
    ):
        """记录反馈（100%记录模型 + 沙盒状态）"""
        try:
            history = json.loads(self.feedback_path.read_text())
            
            record = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "intent": intent,
                "success": success,
                "execution_time": round(execution_time, 2),
                "model": model,
                "provider": "ollama" if "local" in model else "dashscope",
                "convergence_rate": round(convergence_rate, 2),
                "sandbox_passed": sandbox_passed  # ⭐ 补丁4
            }
            
            history.append(record)
            self.feedback_path.write_text(json.dumps(history, ensure_ascii=False, indent=2))
            
            print(f"  ✅ 反馈已记录")
        except Exception as e:
            print(f"  ⚠️ 记录反馈失败: {e}")
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        return {
            "status": self.status,
            "convergence_rate": self.convergence_rate,
            "anchor_data": {
                k: v for k, v in self.socratic.anchor_data.__dict__.items()
                if v and not k.endswith("_confirmed")
            },
            "retriever_status": self.retriever.get_status() if self._retriever else "未初始化"
        }


# 测试入口
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   Universal Skill V2 - 苏格拉底+5W2H深度锚定版              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    skill = UniversalSkillV2()
    
    # 测试模糊输入
    print("\n🧪 测试1: 模糊输入")
    result = skill.execute("帮我做一个报价")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试向量检索
    print("\n🧪 测试2: 本地向量检索")
    results = skill.retriever.search("铝合金加工精度", top_k=2)
    for r in results:
        print(f"  来源: {r.source}")
        print(f"  相似度: {r.score:.3f}")