#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5W2H过滤器 - OpenClaw核心重构
基于苏格拉底引擎的深度锚定

核心原则：
- 禁止废话
- 真实指标
- 物理隔离
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class W2HDimension:
    """5W2H维度定义"""
    key: str
    name: str
    description: str
    required_for: List[str]  # 该维度对哪些意图必需


class FiveW2HFilter:
    """
    5W2H过滤器
    
    大帅指示：
    - 必须与工业参数对齐
    - 材质/精度是CNC报价的核心锚点
    """
    
    # 维度定义
    DIMENSIONS = {
        "who": W2HDimension(
            key="who",
            name="目标用户",
            description="谁看这个结果？",
            required_for=["cnc_quote", "document_gen"]
        ),
        "why": W2HDimension(
            key="why",
            name="目的",
            description="为什么需要这个？",
            required_for=["analysis", "query"]
        ),
        "what": W2HDimension(
            key="what",
            name="核心对象",
            description="具体是什么？",
            required_for=["cnc_quote", "code_gen", "document_gen"]
        ),
        "where": W2HDimension(
            key="where",
            name="上下文",
            description="在什么场景下？",
            required_for=[]
        ),
        "when": W2HDimension(
            key="when",
            name="时效",
            description="什么时候需要？",
            required_for=["cnc_quote"]
        ),
        "how": W2HDimension(
            key="how",
            name="方法",
            description="怎么执行？",
            required_for=["cnc_quote", "analysis"]
        ),
        "how_much": W2HDimension(
            key="how_much",
            name="量化",
            description="数量/精度/误差容忍？",
            required_for=["cnc_quote"]
        )
    }
    
    # 工业参数映射（CNC专用）
    INDUSTRIAL_PARAMS = {
        "material": {
            "铝合金6061": {"density": 2.7, "machinability": "良好"},
            "不锈钢304": {"density": 7.93, "machinability": "中等"},
            "铜": {"density": 8.96, "machinability": "良好"},
            "塑料ABS": {"density": 1.05, "machinability": "简单"}
        },
        "precision": {
            "±0.01mm": {"level": "精密", "cost_multiplier": 1.5},
            "±0.05mm": {"level": "标准", "cost_multiplier": 1.0},
            "±0.1mm": {"level": "普通", "cost_multiplier": 0.8}
        },
        "quantity": {
            "单件": {"setup_cost": 50},
            "小批量(1-10)": {"setup_cost": 100},
            "中批量(10-100)": {"setup_cost": 200},
            "大批量(100+)": {"setup_cost": 500}
        }
    }
    
    def __init__(self):
        self.anchor_map: Dict[str, any] = {}
    
    def check_required_dimensions(self, intent: str) -> Tuple[List[str], List[str]]:
        """
        检查必需维度
        
        Returns:
            (已确认维度, 缺失维度)
        """
        confirmed = []
        missing = []
        
        for key, dim in self.DIMENSIONS.items():
            if intent in dim.required_for:
                if self.anchor_map.get(key):
                    confirmed.append(key)
                else:
                    missing.append(key)
        
        return confirmed, missing
    
    def generate_probe_questions(
        self, 
        intent: str,
        existing_anchors: Dict[str, str]
    ) -> List[Dict]:
        """
        生成探明问题
        
        基于已确认和缺失的维度，生成针对性问题
        """
        questions = []
        confirmed, missing = self.check_required_dimensions(intent)
        
        # 优先问缺失的必需维度
        for key in missing:
            dim = self.DIMENSIONS[key]
            
            # 工业参数特殊处理
            if key == "how_much" and intent == "cnc_quote":
                questions.extend(self._generate_industrial_questions())
            else:
                questions.append({
                    "dimension": key,
                    "question": dim.description,
                    "importance": "CRITICAL" if key in ["what", "how_much"] else "IMPORTANT"
                })
        
        return questions
    
    def _generate_industrial_questions(self) -> List[Dict]:
        """生成工业参数问题（CNC专用）"""
        return [
            {
                "dimension": "how_much",
                "question": "公差精度要求？",
                "options": list(self.INDUSTRIAL_PARAMS["precision"].keys()),
                "importance": "CRITICAL"
            },
            {
                "dimension": "what",
                "question": "材质锁定？",
                "options": list(self.INDUSTRIAL_PARAMS["material"].keys()),
                "importance": "CRITICAL"
            },
            {
                "dimension": "how_much",
                "question": "加工数量？",
                "options": list(self.INDUSTRIAL_PARAMS["quantity"].keys()),
                "importance": "IMPORTANT"
            }
        ]
    
    def validate_industrial_params(
        self, 
        material: str = None,
        precision: str = None,
        quantity: str = None
    ) -> Tuple[bool, Dict]:
        """
        验证工业参数
        
        Returns:
            (是否有效, 参数详情)
        """
        result = {
            "valid": True,
            "params": {},
            "warnings": []
        }
        
        if material:
            if material in self.INDUSTRIAL_PARAMS["material"]:
                result["params"]["material"] = self.INDUSTRIAL_PARAMS["material"][material]
            else:
                result["warnings"].append(f"未知材质: {material}")
        
        if precision:
            if precision in self.INDUSTRIAL_PARAMS["precision"]:
                result["params"]["precision"] = self.INDUSTRIAL_PARAMS["precision"][precision]
            else:
                result["warnings"].append(f"未知精度: {precision}")
        
        if quantity:
            if quantity in self.INDUSTRIAL_PARAMS["quantity"]:
                result["params"]["quantity"] = self.INDUSTRIAL_PARAMS["quantity"][quantity]
            else:
                result["warnings"].append(f"未知数量级: {quantity}")
        
        return result["valid"], result
    
    def calculate_convergence(
        self, 
        intent: str,
        anchors: Dict[str, str]
    ) -> float:
        """
        计算收敛系数
        
        基于维度完整度计算
        """
        confirmed, missing = self.check_required_dimensions(intent)
        
        if not confirmed and not missing:
            # 无必需维度，默认收敛
            return 0.85
        
        if not confirmed:
            # 无任何确认
            return 0.0
        
        # 收敛系数 = 已确认 / (已确认 + 缺失)
        total = len(confirmed) + len(missing)
        return len(confirmed) / total if total > 0 else 0.85


# 测试
if __name__ == "__main__":
    filter = FiveW2HFilter()
    
    # 测试CNC报价
    confirmed, missing = filter.check_required_dimensions("cnc_quote")
    print(f"CNC报价必需维度:")
    print(f"  已确认: {confirmed}")
    print(f"  缺失: {missing}")
    
    # 生成问题
    questions = filter.generate_probe_questions("cnc_quote", {})
    print(f"\n生成问题: {len(questions)}个")