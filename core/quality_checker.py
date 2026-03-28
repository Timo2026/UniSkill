#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量检查器 - Quality Checker
验证输出质量，确保符合预期
"""

import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class CheckResult(Enum):
    """检查结果"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class QualityReport:
    """质量报告"""
    overall_score: float
    checks: Dict[str, Tuple[CheckResult, str, float]]  # {检查项: (结果, 消息, 分数)}
    suggestions: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "overall_score": self.overall_score,
            "checks": {k: (v[0].value, v[1], v[2]) for k, v in self.checks.items()},
            "suggestions": self.suggestions
        }


class QualityChecker:
    """
    质量检查器
    
    功能：
    1. 格式检查 - 验证输出格式是否正确
    2. 内容检查 - 验证内容是否完整、合理
    3. 安全检查 - 检查是否有敏感信息泄露
    4. 性能评估 - 评估执行效率
    """
    
    # 格式验证规则
    FORMAT_RULES = {
        "pdf": {
            "check": lambda f: f.endswith(".pdf") or f.startswith("%PDF"),
            "message": "必须是有效的PDF文件"
        },
        "json": {
            "check": lambda s: QualityChecker._is_valid_json(s),
            "message": "必须是有效的JSON格式"
        },
        "number": {
            "check": lambda n: isinstance(n, (int, float)) and n >= 0,
            "message": "必须是非负数字"
        },
        "email": {
            "check": lambda s: bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(s))),
            "message": "必须是有效的邮箱格式"
        }
    }
    
    # 敏感信息模式
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?', "密码"),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?', "API密钥"),
        (r'secret["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?', "密钥"),
        (r'token["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?', "令牌"),
        (r'\b\d{17,19}x?\b', "身份证号"),
        (r'\b1[3-9]\d{9}\b', "手机号"),
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or {
            "min_score": 0.7,
            "auto_fix": True,
            "strict_mode": False
        }
    
    def check(self, outputs: Dict[str, Any], expected: Optional[Dict] = None) -> QualityReport:
        """
        执行质量检查
        
        Args:
            outputs: 执行输出
            expected: 预期结果（可选）
            
        Returns:
            质量报告
        """
        checks = {}
        suggestions = []
        total_score = 0.0
        check_count = 0
        
        # 1. 格式检查
        format_result, format_msg, format_score = self._check_format(outputs)
        checks["format"] = (format_result, format_msg, format_score)
        total_score += format_score
        check_count += 1
        
        # 2. 内容检查
        content_result, content_msg, content_score = self._check_content(outputs)
        checks["content"] = (content_result, content_msg, content_score)
        total_score += content_score
        check_count += 1
        
        # 3. 安全检查
        security_result, security_msg, security_score = self._check_security(outputs)
        checks["security"] = (security_result, security_msg, security_score)
        total_score += security_score
        check_count += 1
        
        # 4. 完整性检查
        completeness_result, completeness_msg, completeness_score = self._check_completeness(outputs)
        checks["completeness"] = (completeness_result, completeness_msg, completeness_score)
        total_score += completeness_score
        check_count += 1
        
        # 5. 与预期对比（如果提供）
        if expected:
            match_result, match_msg, match_score = self._check_against_expected(outputs, expected)
            checks["expectation_match"] = (match_result, match_msg, match_score)
            total_score += match_score
            check_count += 1
        
        # 计算总分
        overall_score = total_score / check_count if check_count > 0 else 0.0
        
        # 生成建议
        if overall_score < self.config["min_score"]:
            suggestions.append("输出质量未达标，建议检查执行过程")
        
        for check_name, (result, msg, score) in checks.items():
            if result == CheckResult.WARNING:
                suggestions.append(f"[{check_name}] {msg}")
            elif result == CheckResult.FAIL:
                suggestions.append(f"[{check_name}] ⚠️ {msg} - 需要修复")
        
        return QualityReport(
            overall_score=overall_score,
            checks=checks,
            suggestions=suggestions
        )
    
    def _check_format(self, outputs: Dict) -> Tuple[CheckResult, str, float]:
        """检查格式"""
        if not outputs:
            return CheckResult.WARNING, "输出为空", 0.5
        
        # 检查常见格式问题
        for key, value in outputs.items():
            # 检查PDF格式
            if "pdf" in key.lower() or (isinstance(value, str) and value.endswith(".pdf")):
                if not self.FORMAT_RULES["pdf"]["check"](value):
                    return CheckResult.FAIL, "PDF格式无效", 0.3
            
            # 检查JSON格式
            if "json" in key.lower() or (isinstance(value, str) and value.startswith("{")):
                if not self.FORMAT_RULES["json"]["check"](value):
                    return CheckResult.WARNING, "JSON格式可能有问题", 0.6
            
            # 检查数值
            if isinstance(value, (int, float)):
                if not self.FORMAT_RULES["number"]["check"](value):
                    return CheckResult.WARNING, f"{key} 数值异常", 0.5
        
        return CheckResult.PASS, "格式检查通过", 1.0
    
    def _check_content(self, outputs: Dict) -> Tuple[CheckResult, str, float]:
        """检查内容"""
        if not outputs:
            return CheckResult.WARNING, "无输出内容", 0.3
        
        # 检查关键字段
        critical_fields = ["price", "result", "output", "data", "file_path", "pdf_path"]
        has_critical = any(field in outputs for field in critical_fields)
        
        if not has_critical:
            return CheckResult.WARNING, "缺少关键字段", 0.6
        
        # 检查数值合理性
        for key, value in outputs.items():
            if isinstance(value, dict):
                # 检查嵌套字典
                if "price" in value and value["price"] <= 0:
                    return CheckResult.FAIL, "价格必须大于0", 0.3
                if "confidence" in value and not (0 <= value["confidence"] <= 1):
                    return CheckResult.WARNING, "置信度应在0-1之间", 0.6
        
        return CheckResult.PASS, "内容检查通过", 1.0
    
    def _check_security(self, outputs: Dict) -> Tuple[CheckResult, str, float]:
        """检查安全"""
        # 将输出转为字符串进行检查
        output_str = json.dumps(outputs, ensure_ascii=False)
        
        warnings = []
        for pattern, name in self.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, output_str, re.IGNORECASE)
            if matches:
                warnings.append(f"可能包含{name}信息")
        
        if warnings:
            return CheckResult.WARNING, f"安全警告: {', '.join(warnings)}", 0.7
        
        return CheckResult.PASS, "安全检查通过", 1.0
    
    def _check_completeness(self, outputs: Dict) -> Tuple[CheckResult, str, float]:
        """检查完整性"""
        if not outputs:
            return CheckResult.FAIL, "输出为空", 0.0
        
        # 检查是否有错误
        if "error" in outputs or "errors" in outputs:
            errors = outputs.get("errors", [outputs.get("error", "未知错误")])
            return CheckResult.FAIL, f"执行有错误: {errors}", 0.3
        
        # 检查输出字段数量
        field_count = len(outputs)
        if field_count == 0:
            return CheckResult.FAIL, "无输出字段", 0.2
        elif field_count == 1:
            return CheckResult.WARNING, "输出字段较少", 0.7
        
        return CheckResult.PASS, "完整性检查通过", 1.0
    
    def _check_against_expected(self, outputs: Dict, expected: Dict) -> Tuple[CheckResult, str, float]:
        """与预期对比"""
        match_score = 0.0
        total_fields = len(expected)
        matched_fields = 0
        
        for key, expected_value in expected.items():
            if key in outputs:
                actual_value = outputs[key]
                # 简单匹配
                if actual_value == expected_value:
                    matched_fields += 1
                elif isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                    # 数值允许一定误差
                    if expected_value != 0:
                        error_rate = abs(actual_value - expected_value) / abs(expected_value)
                        if error_rate < 0.1:
                            matched_fields += 1
                    else:
                        if abs(actual_value) < 0.01:
                            matched_fields += 1
        
        match_score = matched_fields / total_fields if total_fields > 0 else 1.0
        
        if match_score >= 0.9:
            return CheckResult.PASS, f"与预期匹配度: {match_score:.1%}", match_score
        elif match_score >= 0.7:
            return CheckResult.WARNING, f"与预期匹配度: {match_score:.1%}", match_score
        else:
            return CheckResult.FAIL, f"与预期匹配度较低: {match_score:.1%}", match_score
    
    @staticmethod
    def _is_valid_json(s: str) -> bool:
        """检查是否为有效JSON"""
        try:
            json.loads(s)
            return True
        except:
            return False
    
    def auto_fix(self, outputs: Dict, report: QualityReport) -> Dict:
        """
        自动修复问题
        
        Args:
            outputs: 原始输出
            report: 质量报告
            
        Returns:
            修复后的输出
        """
        if not self.config["auto_fix"]:
            return outputs
        
        fixed_outputs = outputs.copy()
        
        # 修复常见问题
        for check_name, (result, msg, score) in report.checks.items():
            if result == CheckResult.FAIL:
                # 格式问题
                if check_name == "format":
                    # 尝试修复JSON
                    for key, value in fixed_outputs.items():
                        if isinstance(value, str) and value.startswith("{"):
                            try:
                                fixed_outputs[key] = json.loads(value)
                            except:
                                pass
                
                # 内容问题
                elif check_name == "content":
                    if "价格必须大于0" in msg:
                        for key in fixed_outputs:
                            if isinstance(fixed_outputs[key], dict) and "price" in fixed_outputs[key]:
                                if fixed_outputs[key]["price"] <= 0:
                                    fixed_outputs[key]["price"] = 1.0  # 默认最小值
        
        return fixed_outputs


# 测试
if __name__ == "__main__":
    checker = QualityChecker()
    
    # 测试用例
    test_outputs = {
        "pdf_path": "/tmp/报价单.pdf",
        "quote_result": {
            "price": 1234.56,
            "confidence": 0.85,
            "material": "铝合金6061"
        }
    }
    
    report = checker.check(test_outputs)
    print(f"总体得分: {report.overall_score:.2f}")
    print("\n检查结果:")
    for name, (result, msg, score) in report.checks.items():
        print(f"  {name}: {result.value} - {msg} ({score:.2f})")
    
    if report.suggestions:
        print("\n建议:")
        for s in report.suggestions:
            print(f"  - {s}")