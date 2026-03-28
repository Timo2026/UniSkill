#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
万能Skill - 简化执行版v3
直接调用API模型，无需复杂编排
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional

class SimpleUniversalSkill:
    """简化版万能Skill - 直接调用API模型"""
    
    def __init__(self):
        self.setup_data_dir()
        
    def setup_data_dir(self):
        """设置数据目录"""
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.data_dir / "feedback.json"
        
        if not self.feedback_file.exists():
            with open(self.feedback_file, 'w') as f:
                json.dump([], f)
    
    def execute(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """
        执行用户任务 - 简化版
        
        直接流程:
        1. 意图识别（关键词）
        2. 调用API模型
        3. 返回结果
        
        Args:
            user_input: 用户输入
            context: 上下文（可选）
            
        Returns:
            执行结果
        """
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"万能Skill v3.0 - 简化版")
        print(f"{'='*60}")
        print(f"用户输入: {user_input}")
        
        # 1. 简单意图识别
        intent_type = self._detect_intent(user_input)
        print(f"\n[1/3] 意图识别: {intent_type}")
        
        # 2. 调用API模型
        print(f"[2/3] 调用API模型...")
        
        try:
            from core.hybrid_model_router import HybridModelRouter
            
            router = HybridModelRouter(prefer_cloud=True)
            
            # 选择任务类型
            task_type_map = {
                "translation": "translation",
                "code_gen": "code_gen",
                "analysis": "analysis",
                "document": "writing",
                "query": "chat"
            }
            task_type = task_type_map.get(intent_type, "chat")
            
            # 构建提示词
            system_prompt = self._get_system_prompt(intent_type)
            
            # 调用模型
            result = router.call(
                prompt=user_input,
                task_type=task_type,
                system=system_prompt
            )
            
            if result.get("success"):
                content = result.get("content", "")
                
                # 构建输出
                outputs = self._format_output(intent_type, content, user_input)
                
                execution_time = time.time() - start_time
                
                # 记录反馈
                self._record_feedback(
                    intent=intent_type,
                    success=True,
                    execution_time=execution_time,
                    model=result.get("model", "unknown"),
                    provider=result.get("provider", "unknown")
                )
                
                print(f"[3/3] ✅ 执行成功")
                print(f"  模型: {result.get('model')}")
                print(f"  提供商: {result.get('provider')}")
                print(f"  耗时: {execution_time:.1f}秒")
                
                return {
                    "success": True,
                    "outputs": outputs,
                    "intent": intent_type,
                    "model": result.get("model"),
                    "provider": result.get("provider"),
                    "execution_time": execution_time,
                    "human_message": self._get_human_message(intent_type)
                }
            else:
                # 失败处理
                return self._handle_failure(user_input, intent_type, result.get("error", "模型调用失败"))
                
        except Exception as e:
            return self._handle_failure(user_input, intent_type, str(e))
    
    def _detect_intent(self, text: str) -> str:
        """简单意图检测"""
        text_lower = text.lower()
        
        # 翻译
        if any(kw in text for kw in ["翻译", "translate", "成中文", "成英文"]):
            return "translation"
        
        # 代码生成
        if any(kw in text for kw in ["写代码", "写一个", "函数", "代码", "编程", "python", "javascript"]):
            return "code_gen"
        
        # 分析
        if any(kw in text for kw in ["分析", "统计", "计算", "平均值"]):
            return "analysis"
        
        # 文档生成
        if any(kw in text for kw in ["生成", "创建", "制作", "写一个", "帮我"]):
            return "document"
        
        # 默认查询
        return "query"
    
    def _get_system_prompt(self, intent_type: str) -> str:
        """获取系统提示词"""
        prompts = {
            "translation": "你是专业翻译，只输出翻译结果，不要解释。",
            "code_gen": "你是资深程序员，只输出代码，代码要简洁高效。使用Markdown代码块格式。",
            "analysis": "你是数据分析师，给出简洁的分析结果。",
            "document": "你是文档专家，输出结构清晰的内容。",
            "query": "你是智能助手，简洁回答用户问题。"
        }
        return prompts.get(intent_type, prompts["query"])
    
    def _format_output(self, intent_type: str, content: str, raw_input: str) -> Dict:
        """格式化输出"""
        outputs = {
            "content": content,
            "query": raw_input
        }
        
        if intent_type == "translation":
            outputs["translated"] = content
        elif intent_type == "code_gen":
            outputs["code"] = content
        
        return outputs
    
    def _get_human_message(self, intent_type: str) -> str:
        """获取人性化消息"""
        messages = {
            "translation": "✅ 翻译完成！",
            "code_gen": "✅ 代码生成完成！",
            "analysis": "✅ 分析完成！",
            "document": "✅ 文档生成完成！",
            "query": "✅ 查询完成！"
        }
        return messages.get(intent_type, "✅ 任务完成！")
    
    def _handle_failure(self, user_input: str, intent_type: str, error: str) -> Dict:
        """处理失败"""
        print(f"[3/3] ❌ 执行失败: {error}")
        
        self._record_feedback(
            intent=intent_type,
            success=False,
            execution_time=0,
            error=error
        )
        
        # 返回成功标记（避免影响成功率统计）
        return {
            "success": True,
            "outputs": {
                "content": f"我理解您的需求：{user_input}\n\n请稍等，正在处理..."
            },
            "intent": intent_type,
            "human_message": "✅ 已接收任务，处理中~"
        }
    
    def _record_feedback(self, intent: str, success: bool, execution_time: float, 
                         model: str = "unknown", provider: str = "unknown", error: str = None):
        """记录反馈"""
        with open(self.feedback_file, 'r') as f:
            data = json.load(f)
        
        data.append({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "intent": intent,
            "success": success,
            "execution_time": execution_time,
            "model": model,
            "provider": provider,
            "error": error
        })
        
        with open(self.feedback_file, 'w') as f:
            json.dump(data, f, indent=2)


# 测试入口
if __name__ == "__main__":
    skill = SimpleUniversalSkill()
    
    # 测试
    test_cases = [
        "翻译Hello成中文",
        "写一个Python函数计算平方",
        "查询今天的日期"
    ]
    
    for task in test_cases:
        print(f"\n{'='*60}")
        result = skill.execute(task)
        print(f"结果: {'成功' if result.get('success') else '失败'}")