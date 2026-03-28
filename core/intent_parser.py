#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
意图解析器 - Intent Parser
从用户输入中提取关键词、识别意图、拆解子任务
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# 导入schema
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from schemas.skill_schema import Intent


class IntentParser:
    """
    意图解析器
    
    功能：
    1. 关键词提取 - 从自然语言中提取关键实体
    2. 意图分类 - 判断用户想要什么类型的操作
    3. 任务拆解 - 将复杂任务分解为子任务
    """
    
    # 意图类型映射 - 优化版v2
    INTENT_PATTERNS = {
        # 生成类 ⭐最高优先级
        "generate": {
            "keywords": ["生成", "创建", "制作", "写", "导出", "输出", "帮我", "做一个", "搞一个", "弄一个"],
            "examples": ["生成报价单", "创建PDF", "写报告", "做一个网页"],
            "priority": 100  # 最高优先级
        },
        # 分析类
        "analyze": {
            "keywords": ["分析", "评估", "检查", "诊断", "审查", "对比", "统计"],
            "examples": ["分析数据", "评估风险", "检查代码"],
            "priority": 80
        },
        # 查询类
        "query": {
            "keywords": ["查询", "搜索", "查找", "获取", "列出", "显示", "看看", "是什么"],
            "examples": ["查询订单", "搜索文件", "列出所有"],
            "priority": 70
        },
        # 转换类 ⭐翻译优先级提高
        "transform": {
            "keywords": ["转换", "翻译", "格式化", "修改", "编辑", "更新"],
            "examples": ["转换格式", "翻译文档", "修改配置"],
            "priority": 90
        },
        # 删除类 ⭐降低优先级，避免误判
        "delete": {
            "keywords": ["删除", "移除", "卸载"],  # 移除"清理"
            "examples": ["删除文件", "移除插件"],
            "priority": 50
        },
        # 安装类
        "install": {
            "keywords": ["安装", "部署", "配置", "设置"],
            "examples": ["安装插件", "配置环境"],
            "priority": 60
        }
    }
    
    # 领域关键词
    DOMAIN_KEYWORDS = {
        "manufacturing": ["报价", "零件", "加工", "CNC", "材料", "工艺", "图纸", "尺寸", "公差"],
        "document": ["PDF", "文档", "报告", "表格", "Excel", "Word", "Markdown"],
        "code": ["代码", "脚本", "程序", "函数", "API", "模块", "包"],
        "data": ["数据", "分析", "统计", "图表", "数据库"],
        "system": ["服务", "进程", "日志", "配置", "环境", "部署"],
        "communication": ["消息", "邮件", "通知", "发送", "回复"],
        "media": ["图片", "视频", "音频", "语音", "文件"],
        "translation": ["翻译", "英文", "中文", "语言", "translate"],
        "search": ["搜索", "查找", "查询", "检索", "search"]
    }
    
    # 常见任务模板
    TASK_TEMPLATES = {
        "报价单PDF": {
            "intent": "generate",
            "domain": "manufacturing",
            "subtasks": [
                {"type": "data_parse", "desc": "解析产品数据"},
                {"type": "price_calc", "desc": "计算价格"},
                {"type": "pdf_gen", "desc": "生成PDF文档"}
            ]
        },
        "数据分析报告": {
            "intent": "analyze",
            "domain": "data",
            "subtasks": [
                {"type": "data_load", "desc": "加载数据"},
                {"type": "stat_analysis", "desc": "统计分析"},
                {"type": "report_gen", "desc": "生成报告"}
            ]
        },
        "代码审查": {
            "intent": "analyze",
            "domain": "code",
            "subtasks": [
                {"type": "code_parse", "desc": "解析代码"},
                {"type": "lint_check", "desc": "语法检查"},
                {"type": "security_audit", "desc": "安全审计"},
                {"type": "report_gen", "desc": "生成审查报告"}
            ]
        }
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or {}
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """构建关键词索引 - 优化版"""
        self.keyword_to_intent = {}
        self.keyword_priority = {}  # 新增优先级
        
        for intent_type, data in self.INTENT_PATTERNS.items():
            priority = data.get("priority", 50)
            for kw in data["keywords"]:
                self.keyword_to_intent[kw] = intent_type
                self.keyword_priority[kw] = priority
        
        self.keyword_to_domain = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                self.keyword_to_domain[kw] = domain
    
    def parse(self, user_input: str) -> Intent:
        """
        解析用户输入
        
        Args:
            user_input: 用户输入的自然语言
            
        Returns:
            Intent: 解析后的意图对象
        """
        # 1. 提取关键词
        keywords = self._extract_keywords(user_input)
        
        # 2. 识别意图类型
        intent_type, confidence = self._classify_intent(user_input, keywords)
        
        # 3. 识别领域
        domain = self._identify_domain(keywords)
        
        # 4. 拆解子任务
        subtasks = self._decompose_tasks(user_input, intent_type, domain)
        
        # 5. 提取约束条件
        constraints = self._extract_constraints(user_input)
        
        # 6. 判断是否需要确认 ⭐苏格拉底提问集成
        needs_confirmation = self._needs_socratic_confirmation(
            user_input, confidence, intent_type, domain
        )
        
        return Intent(
            raw_input=user_input,
            keywords=keywords,
            intent_type=intent_type,
            domain=domain,
            confidence=confidence,
            subtasks=subtasks,
            constraints=constraints,
            needs_confirmation=needs_confirmation
        )
    
    def _needs_socratic_confirmation(self, text: str, confidence: float, 
                                       intent_type: str, domain: str) -> bool:
        """
        判断是否需要苏格拉底式确认
        
        规则：
        1. 置信度>=0.85 → 直接执行（不确认）
        2. 输入>50字 且 置信度<0.7 → 需要确认
        3. 意图类型为unknown → 需要确认
        4. 领域为general 且 置信度<0.6 → 需要确认
        
        Returns:
            bool: 是否需要确认
        """
        # ⭐高置信度直接执行
        if confidence >= 0.85:
            return False
        
        # 字数判断
        char_count = len(text)
        
        # 短输入（≤50字）且置信度够高 → 直接执行
        if char_count <= 50 and confidence >= 0.6:
            return False
        
        # 长输入（>50字）且 置信度<0.7 → 启动苏格拉底提问
        if char_count > 50 and confidence < 0.7:
            return True
        
        # 意图不明确
        if intent_type == "unknown" or confidence < 0.4:
            return True
        
        # 领域不明确 且 置信度低
        if domain == "general" and confidence < 0.6:
            return True
        
        return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词 - 增强版"""
        keywords = []
        
        # 1. 从意图模式中提取
        for kw in self.keyword_to_intent.keys():
            if kw in text:
                keywords.append(kw)
        
        # 2. 从领域关键词中提取
        for domain, domain_kws in self.DOMAIN_KEYWORDS.items():
            for kw in domain_kws:
                if kw in text and kw not in keywords:
                    keywords.append(kw)
        
        # 3. 提取文件类型
        file_types = ["PDF", "Excel", "Word", "JSON", "CSV", "XML", "Markdown", "TXT", "HTML"]
        for ft in file_types:
            if ft.lower() in text.lower():
                keywords.append(ft)
        
        # 4. 提取技术关键词 ⭐新增
        tech_keywords = [
            "Canvas", "WebGL", "Three.js", "D3", "Chart",
            "API", "REST", "GraphQL", "WebSocket",
            "Python", "JavaScript", "TypeScript", "Go", "Rust",
            "Docker", "Kubernetes", "Linux", "Nginx",
            "MySQL", "PostgreSQL", "MongoDB", "Redis",
            "AI", "ML", "深度学习", "机器学习",
            "DJ", "蹦迪", "夜店", "灯光", "音乐",
            "监控", "性能", "CPU", "内存", "磁盘", "GPU"
        ]
        for kw in tech_keywords:
            if kw.lower() in text.lower() and kw not in keywords:
                keywords.append(kw)
        
        # 5. 提取地名/地标 ⭐新增
        landmarks = [
            "陆家嘴", "东方明珠", "上海中心", "环球金融", "金茂",
            "外滩", "南京路", "浦东", "静安"
        ]
        for lm in landmarks:
            if lm in text and lm not in keywords:
                keywords.append(lm)
        
        # 6. 提取风格关键词 ⭐新增
        style_keywords = [
            "赛博朋克", "霓虹", "科技感", "未来感",
            "简约", "复古", "工业风", "赛博"
        ]
        for kw in style_keywords:
            if kw in text and kw not in keywords:
                keywords.append(kw)
        
        # 7. 提取数字（可能是数量）
        numbers = re.findall(r'\d+', text)
        keywords.extend([f"数量:{n}" for n in numbers if int(n) > 1])
        
        return list(set(keywords))
    
    def _classify_intent(self, text: str, keywords: List[str]) -> Tuple[str, float]:
        """分类意图 - 优化版v3（使用优先级）"""
        scores = {}
        priority_scores = {}
        
        # ⭐优先检查创建/生成关键词（最高优先级）
        generate_keywords = ["创建", "生成", "制作", "写", "导出", "输出", "帮我", "做一个", "搞一个"]
        if any(kw in text for kw in generate_keywords):
            first_30_chars = text[:30]
            for kw in generate_keywords:
                if kw in first_30_chars:
                    base_confidence = 0.85
                    # 有技术关键词加分
                    if any(kw in keywords for kw in ["Canvas", "CPU", "内存", "监控", "网页", "代码", "函数"]):
                        base_confidence += 0.10
                    return "generate", min(base_confidence, 1.0)
        
        # 基于关键词打分（使用优先级）
        for kw in keywords:
            if kw in self.keyword_to_intent:
                intent = self.keyword_to_intent[kw]
                priority = self.keyword_priority.get(kw, 50)
                
                # 优先级越高，分数越高
                weight = priority / 50.0  # 归一化
                scores[intent] = scores.get(intent, 0) + weight
                priority_scores[intent] = priority_scores.get(intent, 0) + priority
        
        # 计算置信度
        matched_keywords = len([k for k in keywords if k in self.keyword_to_intent])
        total_keywords = len(keywords)
        
        if scores:
            # 选择得分最高的意图
            best_intent = max(scores, key=scores.get)
            
            # 基础置信度
            base_confidence = matched_keywords / max(total_keywords, 1)
            
            # 加分项
            bonus = 0
            
            # 关键词数量多，加分
            if total_keywords >= 4:
                bonus += 0.15
            elif total_keywords >= 2:
                bonus += 0.10
            
            # 有技术关键词，加分
            tech_keywords = ["Canvas", "CPU", "内存", "API", "监控", "DJ", "蹦迪", "代码", "函数", "Python"]
            if any(kw in keywords for kw in tech_keywords):
                bonus += 0.15
            
            # 有地名，加分
            if any(kw in keywords for kw in ["陆家嘴", "上海", "浦东"]):
                bonus += 0.10
            
            # 文本短且关键词明确，加分
            if len(text) <= 30 and matched_keywords >= 1:
                bonus += 0.15
            
            final_confidence = min(base_confidence + bonus, 1.0)
            
            return best_intent, final_confidence
        
        # 默认为查询
        return "query", 0.30
    
    def _identify_domain(self, keywords: List[str]) -> str:
        """识别领域"""
        domain_scores = {}
        
        for kw in keywords:
            if kw in self.keyword_to_domain:
                domain = self.keyword_to_domain[kw]
                domain_scores[domain] = domain_scores.get(domain, 0) + 1
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        
        return "general"
    
    def _decompose_tasks(self, text: str, intent_type: str, domain: str) -> List[Dict]:
        """拆解子任务"""
        # 检查是否匹配已知模板
        for template_name, template_data in self.TASK_TEMPLATES.items():
            if template_name in text or any(kw in text for kw in template_name.split()):
                return template_data["subtasks"]
        
        # 通用拆解
        if intent_type == "generate":
            return [
                {"type": "data_prepare", "desc": "准备数据"},
                {"type": "generate", "desc": "生成内容"},
                {"type": "output", "desc": "输出结果"}
            ]
        elif intent_type == "analyze":
            return [
                {"type": "load", "desc": "加载数据"},
                {"type": "analyze", "desc": "分析处理"},
                {"type": "report", "desc": "生成报告"}
            ]
        elif intent_type == "query":
            return [
                {"type": "search", "desc": "搜索查找"},
                {"type": "format", "desc": "格式化输出"}
            ]
        else:
            return [
                {"type": intent_type, "desc": f"执行{intent_type}操作"}
            ]
    
    def _extract_constraints(self, text: str) -> List[str]:
        """提取约束条件"""
        constraints = []
        
        # 格式约束
        if "PDF" in text.upper():
            constraints.append("输出格式:PDF")
        if "Excel" in text or "表格" in text:
            constraints.append("输出格式:Excel")
        
        # 语言约束
        if "中文" in text:
            constraints.append("语言:中文")
        if "英文" in text:
            constraints.append("语言:英文")
        
        # 数量约束
        numbers = re.findall(r'(\d+)[件个份]', text)
        if numbers:
            constraints.append(f"数量:{numbers[0]}")
        
        return constraints
    
    def suggest_skills(self, intent: Intent) -> List[str]:
        """
        根据意图建议技能关键词
        
        Args:
            intent: 解析后的意图
            
        Returns:
            建议的技能搜索关键词列表
        """
        suggestions = []
        
        # 基于意图类型
        intent_skill_map = {
            "generate": ["generator", "creator", "builder"],
            "analyze": ["analyzer", "inspector", "checker"],
            "query": ["finder", "searcher", "query"],
            "transform": ["transformer", "converter", "editor"]
        }
        suggestions.extend(intent_skill_map.get(intent.intent_type, []))
        
        # 基于领域
        domain_skill_map = {
            "manufacturing": ["cnc", "quote", "manufacturing", "machining"],
            "document": ["pdf", "document", "report", "office"],
            "code": ["code", "script", "developer", "programming"],
            "data": ["data", "analytics", "statistics", "visualization"]
        }
        suggestions.extend(domain_skill_map.get(intent.domain, []))
        
        # 基于关键词
        for kw in intent.keywords:
            if kw not in self.keyword_to_intent and kw not in self.keyword_to_domain:
                suggestions.append(kw.lower())
        
        return list(set(suggestions))


# 测试
if __name__ == "__main__":
    parser = IntentParser()
    
    test_inputs = [
        "帮我生成一份铝合金零件的报价单PDF",
        "分析这批销售数据，生成报告",
        "查询上周的所有订单",
        "把这个Word文档转换成PDF格式"
    ]
    
    for inp in test_inputs:
        intent = parser.parse(inp)
        print(f"\n输入: {inp}")
        print(f"关键词: {intent.keywords}")
        print(f"意图: {intent.intent_type} (置信度: {intent.confidence:.2f})")
        print(f"领域: {intent.domain}")
        print(f"子任务: {[s['desc'] for s in intent.subtasks]}")
        print(f"建议技能: {parser.suggest_skills(intent)}")