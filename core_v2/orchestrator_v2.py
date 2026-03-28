#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator V2 - 统一调度器
1 → 2/3 → 1 闭环的真正大脑

大帅指示：
- [1] 接收任务 → [2] 寻源 → [3] Forge造物 → [1] 统一交付
- 本地向量库优先
- SkillForge兜底
- 动态加载执行

核心流程：
┌─────────────────────────────────────────────────────────┐
│  [1] 接收总线任务                                        │
│      ↓                                                   │
│  [2] 寻源：本地是否有现成的 Skill？                      │
│      ├── 有 → 直接执行                                   │
│      └── 无 → [3] 触发 Forge 造物协议                    │
│               ├── LLM 生成代码                           │
│               ├── 沙盒自检                               │
│               └── 通过 → 永久固化                        │
│      ↓                                                   │
│  [1] 统一交付：动态加载并执行                            │
└─────────────────────────────────────────────────────────┘

这就是真正的"上帝模式"：
- 遇到未知任务 → 当场手搓技能 → 永久固化
- 下次再遇到 → 直接秒回（不再调用 API）
"""

import os
import sys
import time
import json
import importlib.util
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from skill_forge import SkillForge, ForgeResult
from local_vector_retriever import LocalVectorRetriever, get_retriever


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    status: str  # LOCAL / FORGED / FAILED
    content: Optional[str] = None
    data: Optional[Dict] = None
    skill_source: Optional[str] = None  # 来源技能文件
    latency: float = 0.0
    convergence: float = 0.0
    model_used: str = "unknown"
    route_trace: List[str] = field(default_factory=list)  # 路由轨迹


class OrchestratorV2:
    """
    统一调度器 V2
    
    实现 1 → 2/3 → 1 的完整闭环
    
    用法：
        boss = OrchestratorV2(api_key="sk-xxx")
        
        # 任务执行
        result = boss.process_task(
            "计算钛合金铣削转速",
            {"D": 12, "Vc_recomm": 40}
        )
        
        if result.success:
            print(result.data)
        else:
            print(result.content)  # 错误信息
    """
    
    # 技能目录
    SKILLS_DIR = Path(__file__).parent.parent / "auto_generated"
    LOCAL_SKILLS_DIR = Path(__file__).parent.parent  # 本地已有技能
    
    # 向量检索阈值
    VECTOR_THRESHOLD = 0.6
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen3.5-plus",
        sandbox_timeout: int = 3
    ):
        """
        初始化统一调度器
        
        Args:
            api_key: DashScope API Key
            model: Forge 使用模型
            sandbox_timeout: 沙盒超时
        """
        self.forge_engine = SkillForge(
            api_key=api_key,
            model=model,
            sandbox_timeout=sandbox_timeout
        )
        
        # 本地向量检索（懒加载）
        self._retriever: Optional[LocalVectorRetriever] = None
        
        # 统计
        self.stats = {
            "total_tasks": 0,
            "local_hit": 0,      # 本地向量库命中
            "skill_hit": 0,      # 本地技能命中
            "forged": 0,         # Forge生成
            "failed": 0,         # 失败
        }
        
        print(f"🦫 [OrchestratorV2] 统一调度器已初始化")
        print(f"  Forge模型: {model}")
        print(f"  沙盒超时: {sandbox_timeout}s")
    
    @property
    def retriever(self) -> LocalVectorRetriever:
        """懒加载向量检索器"""
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever
    
    def process_task(
        self,
        user_input: str,
        params_dict: Dict,
        intent_hint: str = None
    ) -> TaskResult:
        """
        核心：1 → 2/3 → 1 闭环
        
        Args:
            user_input: 用户输入/任务描述
            params_dict: 参数字典
            intent_hint: 意图提示（可选）
            
        Returns:
            TaskResult: 执行结果
        """
        start_time = time.time()
        self.stats["total_tasks"] += 1
        
        route_trace = []
        route_trace.append("[1] 接收总线任务")
        
        print(f"\n{'='*60}")
        print(f"[OrchestratorV2] 任务启动")
        print(f"  输入: {user_input[:50]}...")
        print(f"{'='*60}")
        
        # === [2] 寻源：本地是否有现成技能？ ===
        route_trace.append("[2] 寻源：检查本地资源")
        
        # 2.1 检查向量库
        print("\n[2.1] 本地向量库检索...")
        vector_results = self._vector_search(user_input)
        
        if vector_results and any(r.score > self.VECTOR_THRESHOLD for r in vector_results):
            best = vector_results[0]
            route_trace.append(f"✅ 向量库命中 (score={best.score:.2f})")
            self.stats["local_hit"] += 1
            
            return TaskResult(
                success=True,
                status="LOCAL_VECTOR",
                content=best.content,
                data={"source": best.source, "score": best.score},
                skill_source=best.source,
                latency=time.time() - start_time,
                model_used="local_vector",
                route_trace=route_trace
            )
        
        # 2.2 检查已有技能文件
        print("\n[2.2] 检查本地技能文件...")
        skill_path = self._find_local_skill(user_input, intent_hint)
        
        if skill_path:
            route_trace.append(f"✅ 本地技能命中: {skill_path.name}")
            self.stats["skill_hit"] += 1
            
            # 直接执行
            result = self._execute_dynamic_module(skill_path, params_dict)
            
            return TaskResult(
                success=result.get("success", False),
                status="LOCAL_SKILL",
                content=result.get("content", ""),
                data=result.get("data", {}),
                skill_source=str(skill_path),
                latency=time.time() - start_time,
                model_used="local_skill",
                route_trace=route_trace
            )
        
        # === [3] 本地无此技能，触发 Forge 造物协议 ===
        route_trace.append("[3] 本地无此技能 → 启动 Forge 造物")
        print("\n[3] Forge 造物协议启动...")
        self.stats["forged"] += 1
        
        forge_result = self.forge_engine.forge(
            intent_desc=user_input,
            params_example=params_dict
        )
        
        if not forge_result.success:
            route_trace.append(f"❌ Forge失败: {forge_result.error}")
            self.stats["failed"] += 1
            
            return TaskResult(
                success=False,
                status="FAILED",
                content=f"无法生成安全可靠的技能: {forge_result.error}",
                latency=time.time() - start_time,
                route_trace=route_trace
            )
        
        route_trace.append(f"✅ Forge成功: {forge_result.skill_name}")
        route_trace.append(f"  沙盒通过: {forge_result.sandbox_passed}")
        
        # === [1] 统一交付：动态加载执行 ===
        route_trace.append("[1] 统一交付：执行新生成的技能")
        print("\n[1] 执行新生成的技能...")
        
        skill_path = Path(forge_result.skill_path)
        result = self._execute_dynamic_module(skill_path, params_dict)
        
        return TaskResult(
            success=result.get("success", False),
            status="FORGED",
            content=result.get("content", ""),
            data=result.get("data", result.get("result", {})),
            skill_source=str(skill_path),
            latency=time.time() - start_time,
            model_used=self.forge_engine.model,
            route_trace=route_trace,
            convergence=1.0  # Forge 成功代表完全收敛
        )
    
    def _vector_search(self, query: str) -> List:
        """
        向量库检索
        
        Args:
            query: 查询文本
            
        Returns:
            检索结果列表
        """
        try:
            results = self.retriever.search(query, top_k=3, threshold=0.3)
            print(f"  🔍 检索结果: {len(results)} 条")
            for r in results[:2]:
                print(f"    - {r.source}: {r.score:.2f}")
            return results
        except Exception as e:
            print(f"  ⚠️ 向量检索失败: {e}")
            return []
    
    def _find_local_skill(
        self,
        user_input: str,
        intent_hint: str = None
    ) -> Optional[Path]:
        """
        查找本地技能
        
        检查：
        1. auto_generated 目录（Forge生成的）
        2. skills 目录（人工编写的）
        
        Args:
            user_input: 用户输入
            intent_hint: 意图提示
            
        Returns:
            技能文件路径，或 None
        """
        # 检查 auto_generated 目录
        if self.SKILLS_DIR.exists():
            for skill_file in self.SKILLS_DIR.glob("skill_*.py"):
                # 简单匹配：检查文件名是否相关
                if intent_hint and intent_hint.lower()[:8] in skill_file.stem.lower():
                    return skill_file
        
        # 检查 skills 目录（CNC 等）
        # TODO: 未来可以用向量检索来匹配
        
        return None
    
    def _execute_dynamic_module(
        self,
        filepath: Path,
        params: Dict
    ) -> Dict:
        """
        动态加载并执行模块
        
        Args:
            filepath: Python 文件路径
            params: 执行参数
            
        Returns:
            执行结果
        """
        try:
            module_name = filepath.stem
            spec = importlib.util.spec_from_file_location(module_name, str(filepath))
            
            if not spec or not spec.loader:
                return {"success": False, "error": "模块加载失败"}
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 调用 execute 函数
            if hasattr(module, "execute"):
                result = module.execute(params)
                print(f"  ✅ 执行成功")
                return result
            else:
                return {"success": False, "error": "模块缺少 execute 函数"}
                
        except Exception as e:
            print(f"  ⚠️ 执行异常: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict:
        """
        获取统计
        
        Returns:
            统计数据
        """
        forge_stats = self.forge_engine.get_stats()
        
        total = self.stats["total_tasks"]
        success_rate = (
            (self.stats["local_hit"] + self.stats["skill_hit"] + self.stats["forged"])
            / total * 100 if total > 0 else 0
        )
        
        return {
            "orchestrator": {
                **self.stats,
                "success_rate": f"{success_rate:.1f}%",
            },
            "forge": forge_stats,
            "generated_skills": forge_stats["generated_skills"]
        }
    
    def list_skills(self) -> List[str]:
        """
        列出所有可用技能
        
        Returns:
            技能名称列表
        """
        skills = []
        
        # Forge 生成的
        if self.SKILLS_DIR.exists():
            skills.extend([f.stem for f in self.SKILLS_DIR.glob("skill_*.py")])
        
        return skills


# 测试
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   OrchestratorV2 - 1 → 2/3 → 1 闭环调度器                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # 初始化（不填 API Key，测试本地流程）
    boss = OrchestratorV2(api_key="", model="qwen3.5-plus")
    
    # 测试 1: 模拟本地向量库命中
    print("\n" + "=" * 60)
    print("🧪 测试1: 本地向量库检索")
    print("=" * 60)
    
    # 注意：这里需要向量库有数据才能命中
    # 如果向量库没数据，会走到 Forge 流程
    
    # 测试 2: 动态加载现有技能
    print("\n" + "=" * 60)
    print("🧪 测试2: 动态加载测试")
    print("=" * 60)
    
    # 创建一个临时测试技能
    test_skill = boss.SKILLS_DIR / "test_milling_speed.py"
    test_skill.write_text('''#!/usr/bin/env python3
"""测试技能: 铣削转速计算"""

import math

def execute(params: dict) -> dict:
    """计算铣削转速"""
    D = params.get("D", 10)
    Vc = params.get("Vc_recomm", 30)
    S = (1000 * Vc) / (math.pi * D)
    return {"success": True, "result": {"S": round(S, 1), "Vc": Vc}}

if __name__ == "__main__":
    print("✅ 自检通过")
''')
    
    # 执行
    result = boss._execute_dynamic_module(test_skill, {"D": 12, "Vc_recomm": 40})
    print(f"  执行结果: {result}")
    
    # 清理
    test_skill.unlink()
    
    # 统计
    print("\n" + "=" * 60)
    print("📊 统计")
    print("=" * 60)
    stats = boss.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))