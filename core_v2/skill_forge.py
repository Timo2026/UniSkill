#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkillForge - 造物引擎
从"无中生有"到"永久固化"

大帅指示：
- 遇到未知任务 → 现场写代码 → 沙盒测试 → 动态加载
- 只用标准库（禁止 numpy/pandas）
- 3秒超时熔断（2C 2G 防崩盘）
- 沙盒通过后永久固化

核心流程：
[未知任务] → [LLM生成代码] → [沙盒自检] → [动态加载] → [执行交付]
"""

import os
import sys
import subprocess
import hashlib
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class ForgeResult:
    """锻造结果"""
    success: bool
    skill_path: Optional[str] = None
    skill_name: Optional[str] = None
    error: Optional[str] = None
    latency: float = 0.0
    sandbox_passed: bool = False


class SkillForge:
    """
    造物引擎
    
    让系统在没有现成技能时，当场手搓一个出来
    
    用法：
        forge = SkillForge(api_key="YOUR_API_KEY_HERE")
        result = forge.forge("计算钛合金铣削转速")
        
        if result.success:
            # 动态加载并执行
            module = forge.load_module(result.skill_path)
            output = module.execute({"D": 12, "Vc_recomm": 40})
    """
    
    # API配置
    API_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    # 模型选择（根据任务复杂度）
    MODEL_HIGH = "qwen3-max"      # 复杂任务
    MODEL_LOW = "qwen3.5-plus"    # 简单任务
    
    # 沙盒超时（秒）
    SANDBOX_TIMEOUT = 3
    
    # 生成技能目录
    SKILL_DIR = Path(__file__).parent.parent / "auto_generated"
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "qwen3.5-plus",
        sandbox_timeout: int = 3
    ):
        """
        初始化造物引擎
        
        Args:
            api_key: DashScope API Key（如无则从环境变量读取）
            model: 默认模型
            sandbox_timeout: 沙盒超时秒数
        """
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        self.model = model
        self.sandbox_timeout = sandbox_timeout
        
        # 确保目录存在
        self.SKILL_DIR.mkdir(parents=True, exist_ok=True)
        
        # 统计
        self.stats = {
            "total_forge": 0,
            "success_forge": 0,
            "sandbox_timeout": 0,
            "sandbox_error": 0,
        }
        
        print(f"🦫 [Forge] 造物引擎已初始化")
        print(f"  技能目录: {self.SKILL_DIR}")
        print(f"  沙盒超时: {self.sandbox_timeout}s")
    
    def forge(self, intent_desc: str, params_example: Dict = None) -> ForgeResult:
        """
        核心锻造：根据意图手搓 Python 技能
        
        Args:
            intent_desc: 任务意图描述
            params_example: 参数示例（用于沙盒自检）
            
        Returns:
            ForgeResult: 锻造结果
        """
        start_time = time.time()
        self.stats["total_forge"] += 1
        
        print(f"\n{'='*60}")
        print(f"🦫 [Forge] 发现未知任务，启动造物引擎")
        print(f"  任务: {intent_desc[:50]}...")
        print(f"{'='*60}")
        
        # 1. 生成严格的提示词
        prompt = self._build_prompt(intent_desc, params_example)
        
        # 2. 调用大模型生成代码
        print("\n[1/3] 调用大模型生成代码...")
        code_str = self._call_llm(prompt)
        
        if not code_str:
            return ForgeResult(
                success=False,
                error="LLM调用失败",
                latency=time.time() - start_time
            )
        
        # 清理 markdown 标记
        code_str = self._clean_code(code_str)
        
        # 3. 生成唯一文件名
        skill_id = hashlib.md5(intent_desc.encode()).hexdigest()[:8]
        skill_filename = f"skill_{skill_id}.py"
        skill_path = self.SKILL_DIR / skill_filename
        
        # 4. 写入文件
        print(f"\n[2/3] 代码写入: {skill_filename}")
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(code_str)
        
        # 5. 沙盒测试
        print(f"\n[3/3] 沙盒试爆（{self.sandbox_timeout}s超时）...")
        sandbox_result = self._sandbox_test(skill_path)
        
        if sandbox_result["passed"]:
            print(f"✅ [Forge] 沙盒测试通过！新技能已永久固化。")
            self.stats["success_forge"] += 1
            
            return ForgeResult(
                success=True,
                skill_path=str(skill_path),
                skill_name=skill_filename,
                latency=time.time() - start_time,
                sandbox_passed=True
            )
        else:
            print(f"❌ [Forge] 沙盒测试失败: {sandbox_result['error']}")
            
            # 根据错误类型统计
            if "timeout" in sandbox_result["error"].lower():
                self.stats["sandbox_timeout"] += 1
            else:
                self.stats["sandbox_error"] += 1
            
            # 销毁残次品
            skill_path.unlink(missing_ok=True)
            
            return ForgeResult(
                success=False,
                error=sandbox_result["error"],
                latency=time.time() - start_time,
                sandbox_passed=False
            )
    
    def _build_prompt(self, intent_desc: str, params_example: Dict = None) -> str:
        """
        构建严格的提示词
        
        要求生成规范的 OpenClaw 插件
        """
        params_str = ""
        if params_example:
            params_str = f"\n参数示例: {json.dumps(params_example, ensure_ascii=False)}"
        
        return f"""你是一个资深工业AI工程师。请为 OpenClaw 系统编写一个 Python 插件来解决以下任务：

任务描述: "{intent_desc}"
{params_str}

严格要求：
1. 必须包含一个主函数 `def execute(params: dict) -> dict:`，返回值必须包含 'success' 和 'result' 字段
2. 必须且只能使用 Python 标准库，绝对禁止 import numpy/pandas/request 等第三方库
3. 必须包含 `if __name__ == '__main__':` 块，在里面写死一组模拟参数传入 execute() 并使用 assert 进行结果自检！
4. 代码必须有完整的注释说明功能
5. 只输出纯 Python 代码，不要 markdown 标记，不要任何解释废话

现在请开始编写代码："""
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        调用大模型生成代码
        
        Returns:
            生成的代码字符串，失败返回 None
        """
        if not REQUESTS_AVAILABLE:
            print("⚠️ requests 未安装，无法调用云端 API")
            return None
        
        if not self.api_key:
            print("⚠️ API Key 未配置")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个资深Python工程师，擅长编写简洁高效的工业计算代码。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,  # 低温度保证稳定输出
                "max_tokens": 2048
            }
            
            response = requests.post(
                self.API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  ✅ LLM返回: {len(content)} 字符")
                return content
            else:
                print(f"  ⚠️ API错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ⚠️ LLM调用异常: {e}")
            return None
    
    def _clean_code(self, code_str: str) -> str:
        """
        清理 markdown 标记
        
        移除 ```python 和 ``` 等标记
        """
        # 移除 markdown 代码块标记
        code_str = code_str.replace("```python", "").replace("```", "")
        
        # 移除前后空白
        code_str = code_str.strip()
        
        # 确保有函数定义
        if "def execute" not in code_str:
            print("⚠️ 生成的代码缺少 execute 函数")
        
        return code_str
    
    def _sandbox_test(self, file_path: Path) -> Dict:
        """
        沙盒测试
        
        在独立进程中运行代码的自检部分
        
        Args:
            file_path: Python 文件路径
            
        Returns:
            {'passed': bool, 'error': str}
        """
        try:
            # 执行 __main__ 自检 (Python 3.6兼容)
            result = subprocess.run(
                ["python3", str(file_path.resolve())],  # 使用绝对路径
                timeout=self.sandbox_timeout,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 检查输出是否有自检成功标记
            stdout = result.stdout if result.stdout else ""
            if "自检通过" in stdout or "passed" in stdout.lower() or "✅" in stdout:
                return {"passed": True, "error": None}
            
            # 没有明确成功标记，但有输出也算通过
            if stdout:
                print(f"  沙盒输出: {stdout[:200]}")
                return {"passed": True, "error": None}
            
            return {"passed": False, "error": "沙盒无输出"}
            
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": f"沙盒超时（>{self.sandbox_timeout}s）- 可能是死循环或计算过重"}
            
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if e.stderr else ""
            return {"passed": False, "error": f"执行错误: {stderr[:200] if stderr else str(e)}"}
            
        except Exception as e:
            return {"passed": False, "error": f"沙盒异常: {str(e)}"}
    
    def load_module(self, skill_path: str) -> Optional[object]:
        """
        动态加载技能模块
        
        Args:
            skill_path: 技能文件路径
            
        Returns:
            动态加载的模块对象（可直接调用 execute）
        """
        try:
            import importlib.util
            
            skill_path = Path(skill_path)
            module_name = skill_path.stem
            
            spec = importlib.util.spec_from_file_location(module_name, str(skill_path))
            if not spec or not spec.loader:
                print(f"⚠️ 无法加载模块: {skill_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            print(f"✅ 动态加载成功: {module_name}")
            return module
            
        except Exception as e:
            print(f"⚠️ 动态加载失败: {e}")
            return None
    
    def execute_skill(self, skill_path: str, params: Dict) -> Dict:
        """
        加载并执行技能
        
        Args:
            skill_path: 技能文件路径
            params: 执行参数
            
        Returns:
            执行结果
        """
        module = self.load_module(skill_path)
        if not module:
            return {"success": False, "error": "模块加载失败"}
        
        try:
            # 调用 execute 函数
            if hasattr(module, "execute"):
                result = module.execute(params)
                return result
            else:
                return {"success": False, "error": "模块缺少 execute 函数"}
                
        except Exception as e:
            return {"success": False, "error": f"执行异常: {str(e)}"}
    
    def list_generated_skills(self) -> list:
        """
        列出已生成的技能
        
        Returns:
            技能文件列表
        """
        if not self.SKILL_DIR.exists():
            return []
        
        return [f.name for f in self.SKILL_DIR.glob("skill_*.py")]
    
    def get_stats(self) -> Dict:
        """
        获取锻造统计
        
        Returns:
            统计数据
        """
        success_rate = (
            self.stats["success_forge"] / self.stats["total_forge"] * 100
            if self.stats["total_forge"] > 0 else 0
        )
        
        return {
            **self.stats,
            "success_rate": f"{success_rate:.1f}%",
            "generated_skills": self.list_generated_skills()
        }


# 测试
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   SkillForge 造物引擎 - 从无中生有到永久固化                ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # 测试沙盒（不调用 API）
    forge = SkillForge(api_key="", model="qwen3.5-plus")
    
    # 模拟一个已经存在的技能文件
    test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能: 计算铣削转速"""

import math

def execute(params: dict) -> dict:
    """
    计算铣削转速
    
    公式: S = (1000 * Vc) / (pi * D)
    
    Args:
        params: {D: 直径mm, Vc_recomm: 推荐线速度 m/min}
        
    Returns:
        {success, result: {S: 转速rpm, Vc: 线速度}}
    """
    D = params.get("D", 10)  # 刀具直径 mm
    Vc = params.get("Vc_recomm", 30)  # 推荐线速度 m/min
    
    # 主轴转速公式
    S = (1000 * Vc) / (math.pi * D)
    
    return {
        "success": True,
        "result": {
            "S": round(S, 1),  # 转速 rpm
            "Vc": Vc,  # 线速度 m/min
            "D": D  # 直径 mm
        },
        "formula": "S = (1000 * Vc) / (π * D)"
    }

if __name__ == "__main__":
    # 自检测试
    test_params = {"D": 12, "Vc_recomm": 40}
    result = execute(test_params)
    assert result["success"], "自检失败"
    assert result["result"]["S"] > 0, "转速计算错误"
    print(f"✅ 自检通过: S={result['result']['S']} rpm")
'''
    
    # 写入测试文件
    test_file = forge.SKILL_DIR / "test_milling.py"
    test_file.write_text(test_code)
    
    # 测试沙盒
    print("\n🧪 沙盒测试...")
    sandbox_result = forge._sandbox_test(test_file)
    print(f"  结果: {sandbox_result}")
    
    # 测试动态加载
    print("\n🧪 动态加载测试...")
    module = forge.load_module(str(test_file))
    if module:
        result = module.execute({"D": 12, "Vc_recomm": 40})
        print(f"  执行结果: {result}")
    
    # 清理
    test_file.unlink()
    
    print("\n" + "=" * 60)
    print("✅ SkillForge 测试完成")