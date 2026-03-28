#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量检查 - 万能Skill V2
从V1借鉴，输出质量评估，自动修正

功能：
- 检查AI化词汇
- 评估输出质量
- 自动修正格式
"""

import re
from typing import Dict, List, Tuple, Optional


class QualityChecker:
    """
    质量检查器
    
    检查项：
    1. AI化词汇检测
    2. 内容完整性
    3. 格式规范性
    """
    
    # AI化词汇列表
    AI_WORDS = [
        "好的", "明白", "我理解", "我可以", "我将",
        "根据您的需求", "以下是", "总结如下",
        "首先", "其次", "最后", "综上所述",
        "希望对您有帮助", "如有问题请随时",
        "作为AI", "我会尽力", "让我来"
    ]
    
    # 必需内容检查
    REQUIRED_CHECKS = {
        "cnc_quote": ["材质", "数量", "价格"],
        "code_gen": ["函数", "参数", "返回"],
        "document_gen": ["标题", "内容"]
    }
    
    def __init__(self):
        self.stats = {
            "total_checks": 0,
            "ai_words_found": 0,
            "format_fixed": 0
        }
    
    def check(self, content: str, intent: str) -> Dict:
        """
        执行质量检查
        
        Returns:
            检查结果
        """
        self.stats["total_checks"] += 1
        
        result = {
            "passed": True,
            "ai_words": [],
            "missing_content": [],
            "format_issues": [],
            "score": 100
        }
        
        # 1. 检查AI化词汇
        ai_words = self._check_ai_words(content)
        if ai_words:
            result["ai_words"] = ai_words
            result["score"] -= len(ai_words) * 5
            self.stats["ai_words_found"] += len(ai_words)
        
        # 2. 检查必需内容
        missing = self._check_required(content, intent)
        if missing:
            result["missing_content"] = missing
            result["score"] -= len(missing) * 10
        
        # 3. 检查格式
        format_issues = self._check_format(content)
        if format_issues:
            result["format_issues"] = format_issues
            result["score"] -= len(format_issues) * 3
        
        # 最终判断
        result["passed"] = result["score"] >= 60
        
        return result
    
    def _check_ai_words(self, content: str) -> List[str]:
        """检查AI化词汇"""
        found = []
        for word in self.AI_WORDS:
            if word in content:
                found.append(word)
        return found
    
    def _check_required(self, content: str, intent: str) -> List[str]:
        """检查必需内容"""
        required = self.REQUIRED_CHECKS.get(intent, [])
        missing = []
        for item in required:
            if item not in content:
                missing.append(item)
        return missing
    
    def _check_format(self, content: str) -> List[str]:
        """检查格式问题"""
        issues = []
        
        # 检查过长句子
        sentences = re.split(r'[。！？]', content)
        for s in sentences:
            if len(s) > 100:
                issues.append("存在过长句子")
                break
        
        # 检查重复
        if len(content) > 50:
            for i in range(len(content) - 20):
                segment = content[i:i+20]
                if content.count(segment) > 2:
                    issues.append("存在重复内容")
                    break
        
        return issues
    
    def fix(self, content: str, issues: Dict) -> str:
        """
        自动修正
        
        Returns:
            修正后的内容
        """
        fixed = content
        
        # 移除AI化词汇
        for word in issues.get("ai_words", []):
            fixed = fixed.replace(word, "")
        
        # 清理多余空格
        fixed = re.sub(r'\s+', ' ', fixed)
        
        self.stats["format_fixed"] += 1
        
        return fixed
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.stats


# 全局实例
_checker: Optional[QualityChecker] = None

def get_quality_checker() -> QualityChecker:
    """获取质量检查器"""
    global _checker
    if _checker is None:
        _checker = QualityChecker()
    return _checker


# 测试
if __name__ == "__main__":
    checker = QualityChecker()
    
    test_content = "好的，我理解您的需求。首先，铝合金6061是一种常用材料..."
    result = checker.check(test_content, "cnc_quote")
    
    print(f"通过: {result['passed']}")
    print(f"得分: {result['score']}")
    print(f"AI词汇: {result['ai_words']}")
