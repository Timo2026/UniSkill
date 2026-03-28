#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合模型执行器 - Hybrid Model Executor
云端API优先，本地Ollama备用
"""

import json
import subprocess
import sys
from typing import Dict, Optional, Any
from pathlib import Path

# 导入混合模型路由器
try:
    from core.hybrid_model_router import HybridModelRouter
    HAS_HYBRID_ROUTER = True
except ImportError:
    HAS_HYBRID_ROUTER = False

# DashScope Coding API配置 (OpenAI兼容模式)
DASHSCOPE_CODING_URL = "https://coding.dashscope.aliyuncs.com/v1"
DASHSCOPE_CODING_KEY = "YOUR_API_KEY_HERE"


class LocalModelExecutor:
    """
    混合模型执行器
    
    优先级: 云端API (DashScope) > 本地Ollama
    """
    
    def __init__(self, model: str = "qwen2.5:0.5b", prefer_cloud: bool = True):
        """
        初始化
        
        Args:
            model: 本地模型名称（备用）
            prefer_cloud: 是否优先使用云端API（默认True）
        """
        self.model = model
        self.prefer_cloud = prefer_cloud
        self.ollama_url = "http://localhost:11434"
        
        # 初始化混合路由器
        if HAS_HYBRID_ROUTER:
            self.router = HybridModelRouter(prefer_cloud=prefer_cloud)
        else:
            self.router = None
        
        self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """检查Ollama是否可用"""
        try:
            import requests
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                print(f"[LocalModelExecutor] Ollama可用，模型: {model_names}")
                return True
        except Exception as e:
            print(f"[LocalModelExecutor] Ollama不可用: {e}")
        return False
    
    def generate(self, prompt: str, system: str = "") -> str:
        """
        调用Ollama生成文本
        
        Args:
            prompt: 用户提示
            system: 系统提示
            
        Returns:
            生成的文本
        """
        try:
            import requests
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system:
                payload["system"] = system
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return f"[错误] Ollama返回: {response.status_code}"
                
        except ImportError:
            # 如果没有requests，用subprocess
            return self._generate_subprocess(prompt, system)
        except Exception as e:
            return f"[错误] {str(e)}"
    
    def _generate_subprocess(self, prompt: str, system: str = "") -> str:
        """使用subprocess调用ollama"""
        try:
            cmd = ["ollama", "run", self.model, prompt]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"[错误] {result.stderr}"
        except Exception as e:
            return f"[错误] {str(e)}"
    
    def translate(self, text: str, target_lang: str = "中文") -> Dict:
        """
        翻译文本 - 云端API优先
        
        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            
        Returns:
            翻译结果
        """
        if not text:
            return {"success": False, "error": "文本为空"}
        
        # 1. 优先使用混合路由器（云端API）
        if self.router:
            result = self.router.translate(text, target_lang)
            if result.get("success"):
                provider = "云端" if not result.get("fallback") else "本地"
                print(f"[LocalModelExecutor] ✅ {provider}模型翻译成功")
                return result
            print(f"[LocalModelExecutor] 混合路由器失败，降级到本地")
        
        # 2. 降级到本地Ollama
        prompt = f"将以下文本翻译成{target_lang}，只输出翻译结果，不要解释：\n\n{text}"
        system = "你是一个专业的翻译助手，只输出翻译结果，不要添加任何解释或评论。"
        
        translated = self.generate(prompt, system)
        
        if translated.startswith("[错误]"):
            return {"success": False, "error": translated}
        
        return {
            "success": True,
            "original": text,
            "translated": translated,
            "target_lang": target_lang,
            "model": self.model,
            "provider": "ollama",
            "fallback": True
        }
    
    def generate_code(self, description: str, language: str = "python") -> Dict:
        """
        生成代码 - 云端API优先
        
        Args:
            description: 代码描述
            language: 编程语言
            
        Returns:
            代码生成结果
        """
        if not description:
            return {"success": False, "error": "描述为空"}
        
        # 1. 优先使用混合路由器（云端API）
        if self.router:
            result = self.router.generate_code(description, language)
            if result.get("success"):
                provider = "云端" if not result.get("fallback") else "本地"
                print(f"[LocalModelExecutor] ✅ {provider}模型代码生成成功")
                return result
        
        # 2. 降级到本地Ollama
        prompt = f"""用{language}编写代码，实现以下功能：

{description}

只输出代码，不要解释。用```{language}包裹代码。"""
        
        system = f"你是一个{language}编程专家，只输出代码，代码要简洁高效。"
        
        code = self.generate(prompt, system)
        
        if code.startswith("[错误]"):
            return {"success": False, "error": code}
        
        return {
            "success": True,
            "code": code,
            "language": language,
            "description": description,
            "model": self.model
        }
    
    def analyze_data(self, data_description: str, analysis_type: str = "综合分析") -> Dict:
        """
        分析数据
        
        Args:
            data_description: 数据描述
            analysis_type: 分析类型
            
        Returns:
            分析结果
        """
        if not data_description:
            return {"success": False, "error": "数据描述为空"}
        
        prompt = f"""对以下数据进行{analysis_type}：

{data_description}

请提供：
1. 数据概览
2. 关键洞察
3. 建议措施"""
        
        analysis = self.generate(prompt)
        
        if analysis.startswith("[错误]"):
            return {"success": False, "error": analysis}
        
        return {
            "success": True,
            "analysis": analysis,
            "type": analysis_type,
            "model": self.model
        }
    
    def write_document(self, topic: str, format: str = "markdown") -> Dict:
        """
        写作文档
        
        Args:
            topic: 文档主题
            format: 文档格式
            
        Returns:
            文档内容
        """
        if not topic:
            return {"success": False, "error": "主题为空"}
        
        prompt = f'请写一篇关于"{topic}"的{format}格式文档，内容要专业、有条理。'
        
        content = self.generate(prompt)
        
        if content.startswith("[错误]"):
            return {"success": False, "error": content}
        
        return {
            "success": True,
            "content": content,
            "topic": topic,
            "format": format,
            "model": self.model
        }
    
    def chat(self, message: str, context: str = "") -> Dict:
        """
        对话问答
        
        Args:
            message: 用户消息
            context: 上下文
            
        Returns:
            回复
        """
        if not message:
            return {"success": False, "error": "消息为空"}
        
        prompt = f"{context}\n\n{message}" if context else message
        response = self.generate(prompt)
        
        if response.startswith("[错误]"):
            return {"success": False, "error": response}
        
        return {
            "success": True,
            "response": response,
            "model": self.model
        }


# 测试
if __name__ == "__main__":
    executor = LocalModelExecutor()
    
    print("="*50)
    print("本地模型执行器测试")
    print("="*50)
    
    # 测试翻译
    print("\n1. 翻译测试:")
    result = executor.translate("Hello, World!", "中文")
    print(f"   原文: Hello, World!")
    print(f"   翻译: {result.get('translated', result.get('error'))}")
    
    # 测试代码生成
    print("\n2. 代码生成测试:")
    result = executor.generate_code("计算斐波那契数列第n项", "python")
    print(f"   结果: {result.get('code', result.get('error'))[:200]}...")
    
    # 测试对话
    print("\n3. 对话测试:")
    result = executor.chat("你好，介绍一下自己")
    print(f"   回复: {result.get('response', result.get('error'))[:200]}...")