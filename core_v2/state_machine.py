#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态机 - The Dynamic Context Engine
控制渲染状态、收敛度检测、路由决策展示

核心功能：
1. 状态流转管理
2. 收敛度计算与警示触发
3. 路由决策可视化
"""

from typing import Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class ExecutionState(Enum):
    """执行状态枚举"""
    IDLE = "idle"              # 空闲
    ANALYZING = "analyzing"    # 分析意图
    PROBING = "probing"        # 苏格拉底追问
    ROUTING = "routing"        # 路由决策
    EXECUTING = "executing"    # 执行中
    VALIDATING = "validating"  # 验证结果
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败
    DEGRADED = "degraded"      # 降级模式（本地检索）


@dataclass
class StateContext:
    """状态上下文"""
    state: ExecutionState = ExecutionState.IDLE
    convergence: float = 0.0           # 收敛度 0.0-1.0
    model_selected: str = ""           # 选中的模型
    route_reason: str = ""             # 路由原因
    sandbox_status: str = "pending"    # 沙盒状态
    latency: float = 0.0               # 响应延迟
    mem_usage: float = 0.0             # 内存占用
    api_quota: int = 0                 # API剩余额度
    intent: str = ""                   # 意图类型
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    socratic_logic: str = ""           # 苏格拉底思考轨迹
    local_mode: bool = False           # 是否本地模式


class StateMachine:
    """
    状态机
    
    管理执行流程的状态变化，提供渲染所需的上下文数据
    """
    
    # 收敛度阈值
    CONVERGENCE_HIGH = 0.7      # 高收敛，直接执行
    CONVERGENCE_MEDIUM = 0.4    # 中等，需要追问
    CONVERGENCE_LOW = 0.3       # 低收敛，警示
    
    def __init__(self):
        """初始化状态机"""
        self.context = StateContext()
        self.history: list = []  # 状态历史
        self._state_handlers = {
            ExecutionState.IDLE: self._handle_idle,
            ExecutionState.ANALYZING: self._handle_analyzing,
            ExecutionState.PROBING: self._handle_probing,
            ExecutionState.ROUTING: self._handle_routing,
            ExecutionState.EXECUTING: self._handle_executing,
            ExecutionState.VALIDATING: self._handle_validating,
            ExecutionState.COMPLETED: self._handle_completed,
            ExecutionState.FAILED: self._handle_failed,
            ExecutionState.DEGRADED: self._handle_degraded,
        }
    
    def transition(self, new_state: ExecutionState, **kwargs) -> StateContext:
        """
        状态转换
        
        Args:
            new_state: 新状态
            **kwargs: 更新的上下文参数
            
        Returns:
            更新后的上下文
        """
        old_state = self.context.state
        self.context.state = new_state
        
        # 更新上下文
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        
        # 记录历史
        self.history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.now().isoformat(),
            "convergence": self.context.convergence
        })
        
        # 触发状态处理器
        handler = self._state_handlers.get(new_state)
        if handler:
            handler()
        
        return self.context
    
    def _handle_idle(self):
        """空闲状态处理"""
        self.context.socratic_logic = "等待输入..."
    
    def _handle_analyzing(self):
        """分析状态处理"""
        self.context.socratic_logic = "正在解析意图关键词..."
    
    def _handle_probing(self):
        """追问状态处理"""
        if self.context.convergence < self.CONVERGENCE_LOW:
            self.context.socratic_logic = "⚠️ 收敛度过低，启动苏格拉底5W2H追问引擎"
        else:
            self.context.socratic_logic = f"收敛度 {self.context.convergence:.0%}，正在补充关键参数..."
    
    def _handle_routing(self):
        """路由状态处理"""
        # 根据收敛度选择模型
        if self.context.convergence >= self.CONVERGENCE_HIGH:
            self.context.model_selected = "qwen3.5-plus"
            self.context.route_reason = "高收敛度，直连云端模型"
        elif self.context.convergence >= self.CONVERGENCE_MEDIUM:
            self.context.model_selected = "glm-5"
            self.context.route_reason = "中等收敛，启用GLM-5进行追问补充"
        else:
            self.context.model_selected = "local-qwen2:0.5b"
            self.context.route_reason = "低收敛度，降级至本地模型"
            self.context.local_mode = True
        
        self.context.socratic_logic = f"路由决策: {self.context.model_selected} ({self.context.route_reason})"
    
    def _handle_executing(self):
        """执行状态处理"""
        self.context.sandbox_status = "running"
        self.context.socratic_logic = f"沙盒执行中... 模型: {self.context.model_selected}"
    
    def _handle_validating(self):
        """验证状态处理"""
        self.context.sandbox_status = "validating"
        self.context.socratic_logic = "正在验证输出质量..."
    
    def _handle_completed(self):
        """完成状态处理"""
        self.context.sandbox_status = "passed"
        self.context.socratic_logic = f"✅ 执行完成 | 耗时: {self.context.latency:.1f}s"
    
    def _handle_failed(self):
        """失败状态处理"""
        self.context.sandbox_status = "failed"
        self.context.socratic_logic = "❌ 执行失败，检查收敛度和参数"
    
    def _handle_degraded(self):
        """降级状态处理"""
        self.context.local_mode = True
        self.context.sandbox_status = "local"
        self.context.socratic_logic = "⚡ 硬件压力过高，降级为本地关键词匹配"
    
    def get_convergence_color(self) -> str:
        """
        获取收敛度对应的颜色
        
        Returns:
            Tailwind CSS 颜色类名
        """
        if self.context.convergence >= self.CONVERGENCE_HIGH:
            return "bg-green-500 text-white"      # 绿色：高收敛
        elif self.context.convergence >= self.CONVERGENCE_MEDIUM:
            return "bg-amber-500 text-white"      # 橙色：中等
        else:
            return "bg-red-500 text-white"        # 红色：警示
    
    def get_convergence_indicator(self) -> str:
        """获取收敛度指示文本"""
        if self.context.convergence >= self.CONVERGENCE_HIGH:
            return "READY"
        elif self.context.convergence >= self.CONVERGENCE_MEDIUM:
            return "PROBING"
        else:
            return "CRITICAL"
    
    def should_show_warning(self) -> bool:
        """是否显示警示"""
        return self.context.convergence < self.CONVERGENCE_LOW
    
    def get_render_vars(self) -> Dict[str, Any]:
        """
        获取渲染变量
        
        Returns:
            Jinja2模板渲染所需的变量字典
        """
        return {
            "state": self.context.state.value,
            "convergence": self.context.convergence,
            "convergence_pct": f"{self.context.convergence:.0%}",
            "convergence_color": self.get_convergence_color(),
            "convergence_indicator": self.get_convergence_indicator(),
            "model_selected": self.context.model_selected,
            "route_reason": self.context.route_reason,
            "sandbox_status": self.context.sandbox_status,
            "latency": f"{self.context.latency:.1f}",
            "mem_usage": f"{self.context.mem_usage:.0%}",
            "api_quota": self.context.api_quota,
            "intent": self.context.intent,
            "timestamp": self.context.timestamp,
            "socratic_logic": self.context.socratic_logic,
            "local_mode": self.context.local_mode,
            "show_warning": self.should_show_warning(),
        }
    
    def snapshot(self) -> Dict:
        """获取状态快照"""
        return {
            "state": self.context.state.value,
            "convergence": self.context.convergence,
            "model": self.context.model_selected,
            "timestamp": self.context.timestamp,
            "socratic_logic": self.context.socratic_logic,
        }


# 测试
if __name__ == "__main__":
    sm = StateMachine()
    
    # 模拟执行流程
    sm.transition(ExecutionState.ANALYZING, convergence=0.2, intent="cnc_quote")
    print(f"状态: {sm.context.state}, 收敛: {sm.context.convergence:.0%}")
    print(f"警示: {sm.should_show_warning()}")
    
    sm.transition(ExecutionState.PROBING)
    print(f"苏格拉底: {sm.context.socratic_logic}")
    
    sm.transition(ExecutionState.ROUTING)
    print(f"模型: {sm.context.model_selected}, 原因: {sm.context.route_reason}")
    
    sm.transition(ExecutionState.COMPLETED, latency=2.5)
    print(f"完成: {sm.context.socratic_logic}")
    
    print("\n渲染变量:")
    print(sm.get_render_vars())