#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多步骤编排 - 万能Skill V2
从V1借鉴，复杂任务自动拆分执行

功能：
- 任务自动拆分
- 流水线执行
- 状态跟踪
"""

import time
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Step:
    """执行步骤"""
    name: str
    action: Callable
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class Orchestrator:
    """
    多步骤编排器
    
    用法：
    1. 定义步骤
    2. 执行流水线
    3. 获取结果
    """
    
    def __init__(self):
        self.steps: List[Step] = []
        self.current_step: int = 0
        self.context: Dict = {}
    
    def add_step(self, name: str, action: Callable) -> 'Orchestrator':
        """添加步骤"""
        self.steps.append(Step(name=name, action=action))
        return self
    
    def set_context(self, context: Dict) -> 'Orchestrator':
        """设置上下文"""
        self.context = context
        return self
    
    def run(self) -> Dict:
        """执行流水线"""
        start_time = time.time()
        results = []
        
        for i, step in enumerate(self.steps):
            self.current_step = i
            step.status = StepStatus.RUNNING
            step.start_time = time.time()
            
            try:
                # 执行步骤
                step.result = step.action(self.context)
                step.status = StepStatus.SUCCESS
                
                # 更新上下文
                if step.result:
                    self.context.update(step.result)
                
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                break
            
            finally:
                step.end_time = time.time()
            
            results.append({
                "step": step.name,
                "status": step.status.value,
                "result": step.result
            })
        
        return {
            "total_steps": len(self.steps),
            "completed": sum(1 for s in self.steps if s.status == StepStatus.SUCCESS),
            "failed": sum(1 for s in self.steps if s.status == StepStatus.FAILED),
            "total_time": time.time() - start_time,
            "steps": results,
            "final_context": self.context
        }
    
    def get_progress(self) -> Dict:
        """获取进度"""
        return {
            "current": self.current_step + 1,
            "total": len(self.steps),
            "status": self.steps[self.current_step].status.value if self.steps else "idle"
        }


# 预定义流程模板
class PipelineTemplates:
    """流程模板"""
    
    @staticmethod
    def cnc_quote_pipeline():
        """CNC报价流程"""
        orch = Orchestrator()
        
        def step1_parse(ctx):
            return {"parsed": True, "material": ctx.get("input", {}).get("material")}
        
        def step2_search(ctx):
            return {"found": True, "price_base": 100}
        
        def step3_calculate(ctx):
            return {"final_price": ctx.get("price_base", 100) * 1.2}
        
        def step4_format(ctx):
            return {"output": f"报价: {ctx.get('final_price')}元"}
        
        return (orch
            .add_step("解析需求", step1_parse)
            .add_step("搜索基准", step2_search)
            .add_step("计算价格", step3_calculate)
            .add_step("格式输出", step4_format))
    
    @staticmethod
    def document_gen_pipeline():
        """文档生成流程"""
        orch = Orchestrator()
        
        def step1_outline(ctx):
            return {"outline": ["标题", "内容", "结尾"]}
        
        def step2_content(ctx):
            return {"content": "文档内容已生成"}
        
        def step3_format(ctx):
            return {"final": ctx.get("content")}
        
        return (orch
            .add_step("生成大纲", step1_outline)
            .add_step("填充内容", step2_content)
            .add_step("格式化", step3_format))


# 测试
if __name__ == "__main__":
    # 测试CNC报价流程
    pipeline = PipelineTemplates.cnc_quote_pipeline()
    pipeline.set_context({"input": {"material": "铝合金6061"}})
    
    result = pipeline.run()
    
    print(f"完成: {result['completed']}/{result['total_steps']}")
    print(f"耗时: {result['total_time']:.2f}秒")
    print(f"结果: {result['final_context']}")
