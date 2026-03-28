#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行器降级链 + 人性化输出
让系统更健壮、更贴心
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ExecutorStatus(Enum):
    """执行器状态"""
    SUCCESS = "success"
    FALLBACK = "fallback"  # 降级成功
    FAILED = "failed"


@dataclass
class ExecutorResult:
    """执行结果"""
    status: ExecutorStatus
    output: Dict
    executor_name: str
    is_fallback: bool = False
    human_message: str = ""  # 人性化消息


class ExecutorChain:
    """
    执行器降级链
    
    核心能力：
    1. 主执行器失败 → 自动尝试备选
    2. 人性化输出模板
    3. 错误友好提示
    """
    
    # 人性化输出模板
    OUTPUT_TEMPLATES = {
        "translation": {
            "success": "✅ 已为您翻译完成！如需调整语气，随时告诉我。",
            "fallback": "✅ 已通过备用方式完成翻译。",
            "partial": "翻译已完成，部分内容可能需要人工校对。",
            "tips": "💡 小提示：如需更正式/口语化表达，可以告诉我哦~"
        },
        "code_gen": {
            "success": "✅ 代码已生成！请根据您的环境适当调整。",
            "fallback": "✅ 已通过备用模型生成代码。",
            "tips": "💡 建议先在测试环境运行，确保符合预期。"
        },
        "analysis": {
            "success": "✅ 数据分析完成！以下是关键洞察。",
            "fallback": "✅ 已通过备用方式完成分析。",
            "tips": "💡 如需深入分析特定维度，告诉我即可。"
        },
        "cnc_quote": {
            "success": "✅ 报价单已生成！价格仅供参考，具体以实际为准。",
            "tips": "💡 如需调整参数或生成正式合同，请告诉我。"
        },
        "search": {
            "success": "✅ 已找到相关结果，按相关度排序。",
            "empty": "未找到完全匹配的结果，试试换个关键词？",
            "tips": "💡 需要更精准的结果？告诉我具体要求。"
        },
        "document_gen": {
            "success": "✅ 文档已生成！如需修改风格，随时告诉我。",
            "tips": "💡 可以要求更正式/活泼/简洁的风格。"
        },
        "default": {
            "success": "✅ 任务完成！",
            "tips": "有其他需要，随时说~"
        }
    }
    
    # 错误友好提示
    ERROR_MESSAGES = {
        "timeout": "服务响应较慢，正在为您切换备用方式...",
        "model_unavailable": "本地模型暂时不可用，正在尝试其他方式...",
        "api_error": "服务遇到小问题，马上帮您换个方式重试。",
        "unknown": "遇到意外情况，正在尝试恢复...",
        "all_failed": "抱歉，当前所有方式都暂时不可用。请稍后再试，或换个方式描述您的需求？"
    }
    
    def __init__(self):
        # 执行器降级配置
        self.fallback_chains = {
            "translation": [
                ("ollama_local", self._translate_ollama),
                ("simple_dict", self._translate_simple),
                ("user_hint", self._translate_hint)
            ],
            "code_gen": [
                ("ollama_local", self._codegen_ollama),
                ("template", self._codegen_template)
            ],
            "analysis": [
                ("ollama_local", self._analyze_ollama),
                ("simple", self._analyze_simple)
            ]
        }
    
    def execute_with_fallback(
        self,
        task_type: str,
        primary_executor: Callable,
        inputs: Dict,
        max_attempts: int = 3
    ) -> ExecutorResult:
        """
        执行任务，支持降级
        
        Args:
            task_type: 任务类型
            primary_executor: 主执行器
            inputs: 输入参数
            max_attempts: 最大尝试次数
            
        Returns:
            执行结果
        """
        # 获取降级链
        chain = self.fallback_chains.get(task_type, [])
        
        # 尝试主执行器
        try:
            result = primary_executor(inputs)
            if result.get("success"):
                return ExecutorResult(
                    status=ExecutorStatus.SUCCESS,
                    output=result.get("outputs", result),
                    executor_name="primary",
                    human_message=self._get_success_message(task_type, result)
                )
        except Exception as e:
            print(f"[ExecutorChain] 主执行器失败: {e}")
        
        # 尝试降级
        for i, (name, executor) in enumerate(chain[:max_attempts-1]):
            try:
                print(f"[ExecutorChain] 尝试备选执行器: {name}")
                result = executor(inputs)
                
                if result.get("success"):
                    return ExecutorResult(
                        status=ExecutorStatus.FALLBACK,
                        output=result.get("outputs", result),
                        executor_name=name,
                        is_fallback=True,
                        human_message=self._get_fallback_message(task_type, name)
                    )
            except Exception as e:
                print(f"[ExecutorChain] {name} 失败: {e}")
                continue
        
        # 全部失败
        return ExecutorResult(
            status=ExecutorStatus.FAILED,
            output={},
            executor_name="none",
            human_message=self.ERROR_MESSAGES["all_failed"]
        )
    
    def _get_success_message(self, task_type: str, result: Dict) -> str:
        """获取成功消息"""
        template = self.OUTPUT_TEMPLATES.get(task_type, self.OUTPUT_TEMPLATES["default"])
        msg = template.get("success", "✅ 完成")
        tips = template.get("tips", "")
        return f"{msg}\n{tips}" if tips else msg
    
    def _get_fallback_message(self, task_type: str, executor_name: str) -> str:
        """获取降级消息"""
        template = self.OUTPUT_TEMPLATES.get(task_type, self.OUTPUT_TEMPLATES["default"])
        return template.get("fallback", "✅ 已通过备用方式完成")
    
    # ========== 备选执行器实现 ==========
    
    def _translate_ollama(self, inputs: Dict) -> Dict:
        """Ollama翻译备选"""
        try:
            from core.local_model_executor import LocalModelExecutor
            executor = LocalModelExecutor()
            return executor.translate(
                inputs.get("text", ""),
                inputs.get("target_lang", "中文")
            )
        except:
            return {"success": False}
    
    def _translate_simple(self, inputs: Dict) -> Dict:
        """简单字典翻译（紧急备选）"""
        # 常用词字典
        simple_dict = {
            "hello": "你好",
            "world": "世界",
            "thank you": "谢谢",
            "good morning": "早上好",
            "goodbye": "再见"
        }
        text = inputs.get("text", "").lower().strip()
        translated = simple_dict.get(text, f"[{text}]")
        return {"success": True, "translated": translated}
    
    def _translate_hint(self, inputs: Dict) -> Dict:
        """提示用户"""
        return {
            "success": True,
            "translated": "翻译服务暂时不可用，建议稍后重试或使用在线翻译工具。",
            "is_hint": True
        }
    
    def _codegen_ollama(self, inputs: Dict) -> Dict:
        """Ollama代码生成"""
        try:
            from core.local_model_executor import LocalModelExecutor
            executor = LocalModelExecutor()
            return executor.generate_code(
                inputs.get("description", ""),
                inputs.get("language", "python")
            )
        except:
            return {"success": False}
    
    def _codegen_template(self, inputs: Dict) -> Dict:
        """模板代码生成"""
        lang = inputs.get("language", "python")
        desc = inputs.get("description", "")
        return {
            "success": True,
            "code": f"""# {desc}
# 请根据实际需求完善以下代码

def main():
    # TODO: 实现功能
    pass

if __name__ == "__main__":
    main()
""",
            "language": lang,
            "is_template": True
        }
    
    def _analyze_ollama(self, inputs: Dict) -> Dict:
        """Ollama分析"""
        try:
            from core.local_model_executor import LocalModelExecutor
            executor = LocalModelExecutor()
            return executor.analyze_data(
                inputs.get("data", inputs.get("text", "")),
                inputs.get("analysis_type", "综合分析")
            )
        except:
            return {"success": False}
    
    def _analyze_simple(self, inputs: Dict) -> Dict:
        """简单分析"""
        data = inputs.get("data", inputs.get("text", ""))
        return {
            "success": True,
            "analysis": f"数据分析：{data[:50]}...（已截断）\n\n建议：请提供更详细的数据描述以获取深入分析。",
            "is_simple": True
        }


# 人性化输出包装器
def humanize_output(task_type: str, result: Dict) -> str:
    """
    将执行结果转换为人性化消息
    
    Args:
        task_type: 任务类型
        result: 执行结果
        
    Returns:
        人性化消息
    """
    templates = ExecutorChain.OUTPUT_TEMPLATES.get(
        task_type, 
        ExecutorChain.OUTPUT_TEMPLATES["default"]
    )
    
    if not result.get("success"):
        return "抱歉，任务执行遇到问题。" + ExecutorChain.ERROR_MESSAGES.get("all_failed", "")
    
    # 构建消息
    parts = []
    
    # 成功消息
    parts.append(templates.get("success", "✅ 完成"))
    
    # 主要输出
    output = result.get("outputs", result)
    if "translated" in output:
        parts.append(f"\n\n📝 翻译结果：\n{output['translated']}")
    elif "code" in output:
        parts.append(f"\n\n💻 代码：\n```{output.get('language', 'python')}\n{output['code']}\n```")
    elif "analysis" in output:
        parts.append(f"\n\n📊 分析结果：\n{output['analysis']}")
    
    # 提示
    if templates.get("tips"):
        parts.append(f"\n\n{templates['tips']}")
    
    return "\n".join(parts)


# 测试
if __name__ == "__main__":
    chain = ExecutorChain()
    
    # 测试人性化输出
    print("测试人性化输出:")
    print("-" * 50)
    
    result = {"success": True, "outputs": {"translated": "你好，世界！"}}
    msg = humanize_output("translation", result)
    print(msg)