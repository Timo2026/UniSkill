#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收敛检查器 - OpenClaw核心重构
动态收敛系数监控

大帅指示：
- 引入动态收敛系数
- 如果用户回答让5W2H更模糊，拒绝工作
- 防止"智障AI"现象
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ConvergenceAction(Enum):
    """收敛动作"""
    PROBE_MORE = "probe_more"      # 需要更多探明
    REJECT = "reject"              # 拒绝执行
    ALLOW_EXECUTE = "allow"        # 允许执行
    FORCE_EXECUTE = "force"        # 强制执行


@dataclass
class ConvergenceResult:
    """收敛检查结果"""
    action: ConvergenceAction
    convergence_rate: float
    message: str
    missing_dimensions: List[str]
    warnings: List[str]


class ConvergenceChecker:
    """
    收敛检查器
    
    核心逻辑：
    - 收敛系数 > 0.8：允许执行
    - 收敛系数 0.5-0.8：建议补充信息
    - 收敛系数 < 0.5：必须追问
    - 如果用户回答让问题更模糊：拒绝执行
    """
    
    # 收敛阈值
    THRESHOLD_ALLOW = 0.8
    THRESHOLD_PROBE = 0.5
    THRESHOLD_REJECT = 0.3
    
    # 历史记录（用于检测模糊化）
    history: List[Dict] = []
    
    @classmethod
    def check(
        cls,
        anchor_data: Dict,
        intent: str,
        user_response: Optional[str] = None
    ) -> ConvergenceResult:
        """
        执行收敛检查
        
        Args:
            anchor_data: 锚点数据
            intent: 意图类型
            user_response: 用户最新回答
            
        Returns:
            收敛检查结果
        """
        # 计算收敛系数
        convergence_rate = cls._calculate_convergence(anchor_data, intent)
        
        # 检测模糊化
        is_blur = False
        if user_response:
            is_blur = cls._detect_blur(user_response)
        
        # 生成缺失维度列表
        missing = cls._get_missing_dimensions(anchor_data)
        
        # 生成警告
        warnings = []
        if is_blur:
            warnings.append("用户回答使问题更加模糊")
        if convergence_rate < cls.THRESHOLD_PROBE:
            warnings.append("关键参数缺失，无法保证执行质量")
        
        # 决定动作
        if is_blur and convergence_rate < cls.THRESHOLD_ALLOW:
            action = ConvergenceAction.REJECT
            message = "大帅，您的回答使问题更加模糊。为避免在错误路径上浪费资源，请明确参数后重试。"
        
        elif convergence_rate >= cls.THRESHOLD_ALLOW:
            action = ConvergenceAction.ALLOW_EXECUTE
            message = f"需求锚定完成（收敛{convergence_rate*100:.0f}%），可以执行。"
        
        elif convergence_rate >= cls.THRESHOLD_PROBE:
            action = ConvergenceAction.PROBE_MORE
            message = f"需求基本明确（收敛{convergence_rate*100:.0f}%），建议补充以下信息：{', '.join(missing[:3])}"
        
        else:
            action = ConvergenceAction.PROBE_MORE
            message = f"关键参数缺失（收敛{convergence_rate*100:.0f}%），必须明确：{', '.join(missing)}"
        
        # 记录历史
        cls.history.append({
            "convergence_rate": convergence_rate,
            "action": action.value,
            "missing": missing
        })
        
        return ConvergenceResult(
            action=action,
            convergence_rate=convergence_rate,
            message=message,
            missing_dimensions=missing,
            warnings=warnings
        )
    
    @classmethod
    def _calculate_convergence(cls, anchor_data: Dict, intent: str) -> float:
        """
        计算收敛系数
        
        基于已确认维度与必需维度的匹配度
        """
        # 必需维度（按意图类型）
        required = {
            "cnc_quote": ["what", "how_much", "how"],
            "code_gen": ["what"],
            "document_gen": ["what", "who"],
            "analysis": ["what", "why"],
            "query": ["what"],
            "translation": ["what"]
        }
        
        intent_required = required.get(intent, ["what"])
        
        if not intent_required:
            return 0.85  # 无特定要求，默认可执行
        
        # 计算匹配度
        confirmed = 0
        for dim in intent_required:
            if anchor_data.get(dim):
                confirmed += 1
        
        return confirmed / len(intent_required)
    
    @classmethod
    def _detect_blur(cls, user_response: str) -> bool:
        """
        检测用户回答是否使问题模糊化
        
        触发条件：
        - 回答"随便"、"都行"、"不确定"
        - 回答前后矛盾
        - 回答过于简短（<5字）且无实质信息
        """
        blur_indicators = [
            "随便", "都行", "不确定", "不知道", 
            "无所谓", "都可以", "看着办",
            "any", "whatever", "随便吧"
        ]
        
        response_lower = user_response.lower().strip()
        
        # 检测模糊词
        for indicator in blur_indicators:
            if indicator in response_lower:
                return True
        
        # 检测过短回答
        if len(response_lower) < 5 and not any(c.isdigit() for c in response_lower):
            return True
        
        return False
    
    @classmethod
    def _get_missing_dimensions(cls, anchor_data: Dict) -> List[str]:
        """获取缺失维度"""
        all_dimensions = ["who", "why", "what", "where", "when", "how", "how_much"]
        return [d for d in all_dimensions if not anchor_data.get(d)]
    
    @classmethod
    def get_convergence_trend(cls) -> Dict:
        """
        获取收敛趋势
        
        用于分析探明效果
        """
        if len(cls.history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = cls.history[-5:]
        rates = [h["convergence_rate"] for h in recent]
        
        # 计算趋势
        if rates[-1] > rates[0]:
            trend = "improving"
        elif rates[-1] < rates[0]:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "latest_rate": rates[-1],
            "avg_rate": sum(rates) / len(rates),
            "probe_count": len(cls.history)
        }


# 测试
if __name__ == "__main__":
    # 测试收敛检查
    anchor = {
        "what": "铝合金零件",
        "how_much": "±0.05mm"
    }
    
    result = ConvergenceChecker.check(anchor, "cnc_quote")
    print(f"收敛系数: {result.convergence_rate*100:.0f}%")
    print(f"动作: {result.action.value}")
    print(f"消息: {result.message}")
    print(f"缺失维度: {result.missing_dimensions}")