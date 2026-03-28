#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合模型路由器 - 复用主系统API配置
优先级: 云端API (DashScope Coding) > 本地Ollama
"""

import os
import json
import requests
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    """模型提供商"""
    DASHSCOPE_CODING = "dashscope-coding"  # 主系统API优先
    OLLAMA = "ollama"                       # 本地备用


@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None


class HybridModelRouter:
    """
    混合模型路由器 - 复用主系统API
    
    直接使用OpenClaw主系统配置的DashScope Coding API:
    - GLM-5 (智谱AI)
    - Qwen3.5-Plus (通义千问)
    - Kimi-K2.5 (月之暗面)
    
    优先级:
    1. 云端API (DashScope Coding) - 质量高、速度快
    2. 本地Ollama - 免费、隐私、离线可用
    """
    
    # 🔑 直接复用主系统API配置
    DASHSCOPE_CODING_URL = "https://coding.dashscope.aliyuncs.com/v1"
    DASHSCOPE_CODING_KEY = "YOUR_API_KEY_HERE"
    
    # 模型映射 - 按任务类型选择最佳模型
    MODEL_MAPPING = {
        "translation": {
            "cloud": "glm-5",           # GLM-5 翻译质量好
            "local": "qwen2.5:0.5b"
        },
        "code_gen": {
            "cloud": "qwen3.5-plus",    # Qwen 代码能力强
            "local": "qwen2.5:0.5b"
        },
        "analysis": {
            "cloud": "qwen3.5-plus",    # 分析用Qwen
            "local": "qwen2.5:0.5b"
        },
        "chat": {
            "cloud": "kimi-k2.5",       # 聊天用Kimi
            "local": "qwen2.5:0.5b"
        },
        "writing": {
            "cloud": "glm-5",           # 写作用GLM
            "local": "qwen2.5:0.5b"
        }
    }
    
    def __init__(self, prefer_cloud: bool = True):
        """
        初始化
        
        Args:
            prefer_cloud: 是否优先使用云端API（默认True）
        """
        self.prefer_cloud = prefer_cloud
        self.ollama_endpoint = "http://localhost:11434"
        
        # 检查Ollama可用性
        self.ollama_available = self._check_ollama()
        
        # 云端API配置已内置
        self.dashscope_available = bool(self.DASHSCOPE_CODING_KEY)
        
        print(f"[HybridModelRouter] 云端API(DashScope Coding): {'✅' if self.dashscope_available else '❌'}")
        print(f"[HybridModelRouter] 本地Ollama: {'✅' if self.ollama_available else '❌'}")
    
    def _check_ollama(self) -> bool:
        """检查Ollama是否可用"""
        try:
            resp = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=2)
            return resp.status_code == 200
        except:
            return False
    
    def _call_dashscope_coding(self, prompt: str, model: str = "glm-5", system: str = "") -> Dict:
        """
        调用DashScope Coding API（OpenAI兼容模式）
        
        直接复用主系统配置
        
        Args:
            prompt: 提示词
            model: 模型名称 (glm-5, qwen3.5-plus, kimi-k2.5)
            system: 系统提示词
            
        Returns:
            响应结果
        """
        headers = {
            "Authorization": f"Bearer {self.DASHSCOPE_CODING_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        try:
            resp = requests.post(
                f"{self.DASHSCOPE_CODING_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "success": True,
                    "content": content,
                    "model": model,
                    "provider": "dashscope-coding"
                }
            else:
                error_data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
                return {
                    "success": False,
                    "error": f"API错误: {resp.status_code}",
                    "details": error_data.get('error', {}).get('message', resp.text[:100])
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _call_ollama(self, prompt: str, model: str = "qwen2.5:0.5b") -> Dict:
        """
        调用本地Ollama
        
        Args:
            prompt: 提示词
            model: 模型名称
            
        Returns:
            响应结果
        """
        if not self.ollama_available:
            return {"success": False, "error": "Ollama不可用"}
        
        try:
            resp = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "content": data.get("response", ""),
                    "model": model,
                    "provider": "ollama"
                }
            else:
                return {"success": False, "error": f"Ollama错误: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate(self, prompt: str, task_type: str = "chat", system: str = "") -> Dict:
        """
        生成响应（自动路由）
        
        Args:
            prompt: 提示词
            task_type: 任务类型 (translation/code_gen/analysis/chat/writing)
            system: 系统提示词
            
        Returns:
            响应结果
        """
        config = self.MODEL_MAPPING.get(task_type, self.MODEL_MAPPING["chat"])
        
        # 1. 优先尝试云端API (DashScope Coding)
        if self.prefer_cloud and self.dashscope_available:
            cloud_model = config["cloud"]
            print(f"[HybridModelRouter] 尝试云端API: {cloud_model}")
            result = self._call_dashscope_coding(prompt, cloud_model, system)
            
            if result.get("success"):
                result["fallback"] = False
                return result
            
            print(f"[HybridModelRouter] 云端API失败: {result.get('error')}")
        
        # 2. 降级到本地Ollama
        if self.ollama_available:
            local_model = config["local"]
            print(f"[HybridModelRouter] 降级到本地: {local_model}")
            result = self._call_ollama(prompt, local_model)
            
            if result.get("success"):
                result["fallback"] = True
                return result
        
        # 3. 全部失败
        return {
            "success": False,
            "error": "所有模型都不可用",
            "provider": "none"
        }
    
    def call(self, prompt: str, task_type: str = "chat", system: str = "") -> Dict:
        """
        调用模型（generate的别名）
        
        Args:
            prompt: 提示词
            task_type: 任务类型
            system: 系统提示词
            
        Returns:
            响应结果
        """
        return self.generate(prompt, task_type, system)
    
    # ========== 便捷方法 ==========
    
    def translate(self, text: str, target_lang: str = "中文") -> Dict:
        """翻译 - 使用GLM-5"""
        prompt = f"将以下文本翻译成{target_lang}，只输出翻译结果，不要解释：\n\n{text}"
        system = "你是专业的翻译助手，只输出翻译结果，不要添加任何解释。"
        result = self.generate(prompt, "translation", system)
        
        if result.get("success"):
            return {
                "success": True,
                "translated": result["content"],
                "original": text,
                "target_lang": target_lang,
                "model": result["model"],
                "provider": result["provider"],
                "fallback": result.get("fallback", False)
            }
        return result
    
    def generate_code(self, description: str, language: str = "python") -> Dict:
        """代码生成 - 使用Qwen3.5-Plus"""
        prompt = f"用{language}编写代码实现以下功能：\n\n{description}"
        system = f"你是{language}编程专家，只输出代码，代码要简洁高效。"
        result = self.generate(prompt, "code_gen", system)
        
        if result.get("success"):
            return {
                "success": True,
                "code": result["content"],
                "language": language,
                "model": result["model"],
                "provider": result["provider"],
                "fallback": result.get("fallback", False)
            }
        return result
    
    def analyze(self, data: str, analysis_type: str = "综合分析") -> Dict:
        """数据分析"""
        prompt = f"对以下数据进行{analysis_type}：\n\n{data}\n\n请给出分析结论和建议。"
        result = self.generate(prompt, "analysis")
        
        if result.get("success"):
            return {
                "success": True,
                "analysis": result["content"],
                "model": result["model"],
                "provider": result["provider"],
                "fallback": result.get("fallback", False)
            }
        return result


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("混合模型路由器测试")
    print("=" * 60)
    
    router = HybridModelRouter(prefer_cloud=True)
    
    # 测试翻译
    print("\n[测试1] 翻译 (云端优先)")
    result = router.translate("Hello, World!", "中文")
    print(f"结果: {result}")
    
    # 测试代码生成
    print("\n[测试2] 代码生成")
    result = router.generate_code("写一个计算斐波那契数列的函数")
    print(f"模型: {result.get('model')} ({result.get('provider')})")
    print(f"降级: {result.get('fallback')}")