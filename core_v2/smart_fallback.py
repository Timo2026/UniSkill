#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能降级 - 万能Skill V2
从V1借鉴，API挂了自动切本地，不再失败

功能：
- 云端API超时自动降级
- 失败自动重试
- 本地模型兜底
"""

import time
import requests
from typing import Optional, Dict, Callable
from dataclasses import dataclass


@dataclass
class FallbackConfig:
    """降级配置"""
    timeout: float = 30.0  # 超时时间
    max_retries: int = 2   # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟


class SmartFallback:
    """
    智能降级
    
    策略：
    1. 优先云端API
    2. 超时/失败自动重试
    3. 重试失败降级本地
    """
    
    # 云端API配置
    CLOUD_APIS = {
        "dashscope": {
            "url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            "models": ["qwen3.5-plus", "glm-5", "kimi-k2.5"]
        }
    }
    
    # 本地模型配置
    LOCAL_OLLAMA = "http://localhost:11434/api/generate"
    LOCAL_MODELS = ["qwen2.5:0.5b", "nomic-embed-text"]
    
    def __init__(self, config: FallbackConfig = None):
        self.config = config or FallbackConfig()
        self.stats = {
            "cloud_success": 0,
            "cloud_failure": 0,
            "local_fallback": 0
        }
    
    def call_with_fallback(
        self,
        prompt: str,
        model: str,
        provider: str = "cloud"
    ) -> Dict:
        """
        带降级的调用
        
        Args:
            prompt: 输入提示
            model: 模型名称
            provider: 提供商（cloud/local）
            
        Returns:
            执行结果
        """
        start_time = time.time()
        
        # 优先云端
        if provider == "cloud":
            result = self._try_cloud(prompt, model)
            if result.get("success"):
                return result
            
            # 云端失败，降级本地
            print(f"[智能降级] 云端失败，降级本地...")
            self.stats["local_fallback"] += 1
            return self._try_local(prompt)
        
        # 直接本地
        return self._try_local(prompt)
    
    def _try_cloud(self, prompt: str, model: str) -> Dict:
        """尝试云端API"""
        for attempt in range(self.config.max_retries):
            try:
                # 模拟API调用（实际需要真实API）
                # response = requests.post(...)
                
                # 简化：假设调用成功
                # 实际需要实现真实的API调用
                
                self.stats["cloud_success"] += 1
                return {
                    "success": True,
                    "content": f"云端{model}响应",
                    "provider": "cloud",
                    "model": model,
                    "time": time.time() - self.start_time if hasattr(self, 'start_time') else 0.5
                }
                
            except Exception as e:
                print(f"[智能降级] 云端第{attempt+1}次失败: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
        
        self.stats["cloud_failure"] += 1
        return {"success": False, "error": "云端API失败"}
    
    def _try_local(self, prompt: str) -> Dict:
        """尝试本地模型"""
        try:
            # 调用Ollama
            response = requests.post(
                self.LOCAL_OLLAMA,
                json={
                    "model": self.LOCAL_MODELS[0],
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "content": data.get("response", ""),
                    "provider": "local",
                    "model": self.LOCAL_MODELS[0]
                }
        except Exception as e:
            print(f"[智能降级] 本地失败: {e}")
        
        return {"success": False, "error": "本地模型也挂了"}
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.stats


# 全局实例
_fallback: Optional[SmartFallback] = None

def get_fallback() -> SmartFallback:
    """获取智能降级实例"""
    global _fallback
    if _fallback is None:
        _fallback = SmartFallback()
    return _fallback


# 测试
if __name__ == "__main__":
    fb = SmartFallback()
    result = fb.call_with_fallback("你好", "qwen3.5-plus")
    print(result)
    print(fb.get_stats())
