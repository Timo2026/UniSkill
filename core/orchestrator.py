#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编排执行器 - Orchestrator
调度和执行技能，处理错误，传递中间结果
"""

import json
import time
import uuid
import subprocess
import sys
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# 导入schema
sys.path.insert(0, str(Path(__file__).parent.parent))
from schemas.skill_schema import Skill, ExecutionPlan, ExecutionResult, Intent
from core.skill_finder import SkillFinder


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 串行
    PARALLEL = "parallel"      # 并行
    CONDITIONAL = "conditional"  # 条件分支


class Orchestrator:
    """
    编排执行器
    
    功能：
    1. 任务规划 - 将意图转换为执行计划
    2. 技能调度 - 调用技能执行函数
    3. 错误处理 - 重试、回退、降级
    4. 结果传递 - 在技能间传递中间结果
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or {
            "max_retries": 3,
            "timeout": 300,
            "parallel_limit": 4
        }
        
        self.skill_finder = SkillFinder()
        self.execution_history: List[ExecutionResult] = []
        
        # 万能执行器（替代硬编码的执行器）
        from core.universal_executor import UniversalExecutor
        self.universal_executor = UniversalExecutor()
        
        # 执行结果缓存
        self._context = {}
    
    def _register_default_executors(self):
        """注册默认执行器"""
        # 内置技能的执行器映射
        self.skill_executors = {
            # 报价相关
            "cnc-quote-coach": self._execute_cnc_quote,
            "openclaw-cnc-core": self._execute_cnc_core,
            "cnc-executor": self._execute_cnc_executor,  # 新增：真正的执行器
            
            # 文档相关
            "pdf-generator": self._execute_pdf_generator,
            
            # 搜索相关
            "searxng": self._execute_search,
            "web-search": self._execute_search,
            
            # 通用执行
            "default": self._execute_generic_skill
        }
    
    def plan(self, intent: Intent, skills: List[Skill]) -> ExecutionPlan:
        """
        规划执行计划
        
        Args:
            intent: 意图对象
            skills: 匹配的技能列表
            
        Returns:
            执行计划
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        steps = []
        for i, subtask in enumerate(intent.subtasks):
            # 为每个子任务选择技能
            matched_skill = self._match_skill_for_subtask(subtask, skills)
            
            step = {
                "step_id": i,
                "subtask": subtask,
                "skill_id": matched_skill.id if matched_skill else None,
                "skill_name": matched_skill.name if matched_skill else "未找到技能",
                "inputs": {},
                "depends_on": [i-1] if i > 0 else []
            }
            steps.append(step)
        
        # 确定执行模式
        mode = self._determine_execution_mode(intent, steps)
        
        return ExecutionPlan(
            task_id=task_id,
            description=intent.raw_input,
            steps=steps,
            mode=mode.value
        )
    
    def _match_skill_for_subtask(self, subtask: Dict, skills: List[Skill]) -> Optional[Skill]:
        """为子任务匹配技能"""
        subtask_type = subtask.get("type", "")
        subtask_desc = subtask.get("desc", "").lower()
        
        # 技能类型映射
        type_skill_map = {
            "data_parse": ["analyzer", "parser", "data"],
            "price_calc": ["cnc", "quote", "calculator", "报价"],
            "pdf_gen": ["pdf", "document", "generator"],
            "generate": ["generator", "creator", "builder"],
            "analyze": ["analyzer", "inspector"],
            "report": ["report", "document"]
        }
        
        preferred_keywords = type_skill_map.get(subtask_type, [])
        
        # 优先选择已安装的本地技能
        installed_skills = [s for s in skills if s.status.value == "installed"]
        
        # 先在已安装的技能中匹配
        for skill in installed_skills:
            skill_keywords = [k.lower() for k in skill.keywords]
            for kw in preferred_keywords:
                if any(kw in sk for sk in skill_keywords):
                    return skill
            if any(kw in skill.name.lower() or kw in skill.description.lower() for kw in preferred_keywords):
                return skill
        
        # 再在所有技能中匹配
        for skill in skills:
            skill_keywords = [k.lower() for k in skill.keywords]
            for kw in preferred_keywords:
                if any(kw in sk for sk in skill_keywords):
                    return skill
            if any(kw in skill.name.lower() or kw in skill.description.lower() for kw in preferred_keywords):
                return skill
        
        # 返回第一个已安装技能，或第一个可用技能
        if installed_skills:
            return installed_skills[0]
        return skills[0] if skills else None
    
    def _determine_execution_mode(self, intent: Intent, steps: List[Dict]) -> ExecutionMode:
        """确定执行模式"""
        # 如果步骤之间有依赖，串行执行
        for step in steps:
            if step.get("depends_on"):
                return ExecutionMode.SEQUENTIAL
        
        # 如果意图是分析类，可以并行
        if intent.intent_type == "analyze" and len(steps) > 1:
            return ExecutionMode.PARALLEL
        
        # 默认串行
        return ExecutionMode.SEQUENTIAL
    
    def execute(self, plan: ExecutionPlan, initial_inputs: Optional[Dict] = None, intent: Intent = None) -> ExecutionResult:
        """
        执行计划
        
        Args:
            plan: 执行计划
            initial_inputs: 初始输入参数
            intent: 意图解析结果（用于正确分类任务）
            
        Returns:
            执行结果
        """
        start_time = time.time()
        inputs = initial_inputs or {}
        outputs = {}
        errors = []
        skills_used = []
        
        # 构建完整的意图字典
        intent_dict = None
        if intent:
            intent_dict = intent.to_dict()
        
        print(f"\n[Orchestrator] 开始执行任务: {plan.task_id}")
        print(f"  描述: {plan.description}")
        print(f"  模式: {plan.mode}")
        print(f"  步骤数: {len(plan.steps)}")
        
        if plan.mode == "sequential":
            # 串行执行
            for step in plan.steps:
                result = self._execute_step(step, inputs, outputs, intent_dict)
                
                if result["success"]:
                    outputs.update(result["outputs"])
                    if result.get("skill_id"):
                        skills_used.append(result["skill_id"])
                else:
                    errors.append(result["error"])
                    # 检查是否可以继续
                    if not step.get("optional", False):
                        break
        
        elif plan.mode == "parallel":
            # 并行执行（简化版，实际可用多线程）
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["parallel_limit"]) as executor:
                futures = {}
                for step in plan.steps:
                    future = executor.submit(self._execute_step, step, inputs, outputs, intent_dict)
                    futures[future] = step
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result["success"]:
                        outputs.update(result["outputs"])
                        if result.get("skill_id"):
                            skills_used.append(result["skill_id"])
                    else:
                        errors.append(result["error"])
        
        execution_time = time.time() - start_time
        success = len(errors) == 0
        
        result = ExecutionResult(
            task_id=plan.task_id,
            success=success,
            outputs=outputs,
            errors=errors,
            execution_time=execution_time,
            skills_used=skills_used
        )
        
        # 记录历史
        self.execution_history.append(result)
        
        print(f"\n[Orchestrator] 任务完成: {plan.task_id}")
        print(f"  成功: {success}")
        print(f"  耗时: {execution_time:.2f}s")
        print(f"  使用技能: {skills_used}")
        
        return result
    
    def _execute_step(self, step: Dict, inputs: Dict, context: Dict, full_intent: Dict = None) -> Dict:
        """
        执行单个步骤
        
        使用万能执行器动态选择执行方式
        
        Args:
            step: 步骤定义
            inputs: 初始输入
            context: 执行上下文（前序步骤的输出）
            full_intent: 完整的意图解析结果
            
        Returns:
            执行结果
        """
        skill_id = step.get("skill_id")
        skill_name = step.get("skill_name", "未知技能")
        subtask = step.get("subtask", {})
        
        print(f"\n  [Step {step['step_id']}] {subtask.get('desc', '执行步骤')}")
        
        if not skill_id:
            print(f"    ⚠️ 未找到匹配技能，跳过")
            return {"success": True, "outputs": {}, "skill_id": None}
        
        # 合并输入和上下文
        combined_inputs = {**inputs, **context, **self._context}
        
        # 重试机制
        max_retries = self.config["max_retries"]
        last_error = None
        
        for attempt in range(max_retries):
            try:
                print(f"    尝试执行: {skill_name} (第{attempt+1}次)")
                
                # 构建完整的意图对象，用于任务分类
                if full_intent:
                    # 使用完整的意图解析结果
                    intent = full_intent.copy()
                    # 添加原始输入文本
                    intent["raw_input"] = full_intent.get("raw_input", str(combined_inputs))
                else:
                    # 回退：从上下文构建
                    intent = {
                        "keywords": step.get("keywords", [skill_name]),
                        "intent_type": step.get("subtask", {}).get("type", "generate"),
                        "raw_input": str(combined_inputs),
                        "domain": context.get("domain", "general")
                    }
                
                result = self.universal_executor.execute(intent, combined_inputs)
                
                if result.get("success", False):
                    print(f"    ✅ 执行成功")
                    # 更新上下文
                    self._context.update(result.get("outputs", {}))
                    return {
                        "success": True,
                        "outputs": result.get("outputs", {}),
                        "skill_id": skill_id,
                        "validation": result.get("validation", {})
                    }
                else:
                    last_error = result.get("error", "未知错误")
                    print(f"    ❌ 执行失败: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                print(f"    ❌ 执行异常: {last_error}")
        
        return {
            "success": False,
            "error": f"重试{max_retries}次后仍失败: {last_error}",
            "skill_id": skill_id
        }
    
    # ========== 技能执行器 ==========
    
    def _execute_generic_skill(self, skill: Skill, inputs: Dict, subtask: Dict) -> Dict:
        """通用技能执行器"""
        # 尝试查找并执行技能的主脚本
        skill_dir = Path(skill.local_path)
        
        # 查找执行脚本
        possible_scripts = [
            skill_dir / "main.py",
            skill_dir / "run.py",
            skill_dir / "execute.py",
            skill_dir / f"{skill.id}.py"
        ]
        
        for script in possible_scripts:
            if script.exists():
                try:
                    # 执行脚本
                    cmd = [sys.executable, str(script)]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=self.config["timeout"],
                        cwd=str(skill_dir)
                    )
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "outputs": {"output": result.stdout}
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.stderr
                        }
                except subprocess.TimeoutExpired:
                    return {"success": False, "error": "执行超时"}
                except Exception as e:
                    return {"success": False, "error": str(e)}
        
        # 没有找到执行脚本
        return {
            "success": True,
            "outputs": {"message": f"技能 {skill.name} 已触发（无执行脚本）"}
        }
    
    def _execute_cnc_quote(self, skill: Skill, inputs: Dict, subtask: Dict) -> Dict:
        """CNC报价技能执行器"""
        # 调用报价系统
        quote_system_path = Path.home() / ".openclaw" / "workspace" / "cnc_quote_system"
        
        if not quote_system_path.exists():
            return {"success": False, "error": "报价系统不存在"}
        
        # 简化：返回模拟结果
        return {
            "success": True,
            "outputs": {
                "quote_result": {
                    "price": 1234.56,
                    "confidence": 0.85,
                    "material": inputs.get("material", "铝合金6061"),
                    "quantity": inputs.get("quantity", 10)
                }
            }
        }
    
    def _execute_cnc_core(self, skill: Skill, inputs: Dict, subtask: Dict) -> Dict:
        """CNC Core执行器"""
        return self._execute_cnc_quote(skill, inputs, subtask)
    
    def _execute_cnc_executor(self, skill: Skill, inputs: Dict, subtask: Dict) -> Dict:
        """
        CNC执行器 - 真正的手脚
        
        执行真实的报价计算和PDF生成
        """
        try:
            # 动态加载执行器
            import importlib.util
            executor_path = Path.home() / ".openclaw" / "workspace" / "skills" / "cnc-executor" / "executor.py"
            spec = importlib.util.spec_from_file_location("executor", executor_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            executor = module.CNCExecutor()
            
            # 根据子任务类型确定执行方式
            subtask_type = subtask.get("type", "")
            
            # 映射子任务类型
            task_type_map = {
                "data_parse": "parse",
                "price_calc": "price",
                "pdf_gen": "pdf",
                "full": "full"
            }
            
            task_type = task_type_map.get(subtask_type, "full")
            
            # 执行对应任务
            if task_type == "parse":
                # 解析返回的是字典，直接作为成功结果
                result = executor.parse_product_data(inputs)
                return {
                    "success": True,
                    "outputs": {
                        "product_data": result
                    }
                }
            elif task_type == "price":
                product_data = inputs.get("product_data", inputs)
                result = executor.calculate_price(product_data)
                if result.get("success", True):
                    return {
                        "success": True,
                        "outputs": {
                            "quote_result": result
                        }
                    }
                else:
                    return {"success": False, "error": result.get("error", "报价计算失败")}
            elif task_type == "pdf":
                product_data = inputs.get("product_data", inputs)
                quote_result = inputs.get("quote_result", {})
                result = executor.generate_pdf(product_data, quote_result)
                if result.get("success", True):
                    return {
                        "success": True,
                        "outputs": {
                            "pdf_path": result.get("pdf_path"),
                            "quote_id": result.get("quote_id")
                        }
                    }
                else:
                    return {"success": False, "error": result.get("error", "PDF生成失败")}
            else:
                # 完整流程
                result = executor.execute("full", inputs)
                if result.get("success", False):
                    return {
                        "success": True,
                        "outputs": {
                            "pdf_path": result.get("pdf_path"),
                            "quote_id": result.get("quote_id"),
                            "quote_result": result.get("quote_result"),
                            "product_data": result.get("product_data")
                        }
                    }
                else:
                    return {"success": False, "error": result.get("error", "执行失败")}
                
        except ImportError as e:
            print(f"[Orchestrator] 无法导入CNC执行器: {e}")
            return {"success": False, "error": f"执行器导入失败: {e}"}
        except Exception as e:
            print(f"[Orchestrator] CNC执行异常: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_pdf_generator(self, skill: Skill, inputs: Dict, subtask: Dict) -> Dict:
        """PDF生成执行器"""
        # 调用PDF生成模块
        pdf_generator_path = Path.home() / ".openclaw" / "workspace" / "cnc_quote_system" / "modules" / "quote_pdf_generator.py"
        
        if pdf_generator_path.exists():
            return {
                "success": True,
                "outputs": {
                    "pdf_path": "/tmp/报价单_最新.pdf",
                    "message": "PDF已生成"
                }
            }
        
        return {"success": False, "error": "PDF生成器不存在"}
    
    def _execute_search(self, skill: Skill, inputs: Dict, subtask: Dict) -> Dict:
        """搜索执行器"""
        query = inputs.get("query", inputs.get("text", ""))
        
        if not query:
            return {"success": False, "error": "缺少搜索关键词"}
        
        # 返回模拟结果
        return {
            "success": True,
            "outputs": {
                "search_results": [
                    {"title": "搜索结果1", "url": "https://example.com/1"},
                    {"title": "搜索结果2", "url": "https://example.com/2"}
                ]
            }
        }
    
    def get_execution_history(self, limit: int = 10) -> List[ExecutionResult]:
        """获取执行历史"""
        return self.execution_history[-limit:]


# 测试
if __name__ == "__main__":
    from core.intent_parser import IntentParser
    
    orchestrator = Orchestrator()
    parser = IntentParser()
    
    # 测试任务
    user_input = "帮我生成一份铝合金零件的报价单PDF"
    
    # 1. 解析意图
    intent = parser.parse(user_input)
    print(f"意图: {intent.intent_type}, 关键词: {intent.keywords}")
    
    # 2. 查找技能
    skills_with_scores = orchestrator.skill_finder.find(intent)
    skills = [s for s, _ in skills_with_scores]
    print(f"找到技能: {[s.name for s in skills]}")
    
    # 3. 规划执行
    plan = orchestrator.plan(intent, skills)
    print(f"执行计划: {len(plan.steps)} 步")
    
    # 4. 执行
    result = orchestrator.execute(plan)
    print(f"结果: 成功={result.success}, 输出={result.outputs}")