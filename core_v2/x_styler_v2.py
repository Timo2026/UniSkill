#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X-Styler V2.2 - "Sea-Glass" 模板引擎
内圣外王：逻辑硬、交互美

核心升级：
1. Jinja2 模板引擎（告别字符串拼接）
2. 思考指纹（Socratic Thinking Trace）
3. 状态机联动（收敛度实时反映）
4. 资产看板（10855条数据可视化）
5. 流式渲染（2C 2G 兼容）
"""

import os
import time
import json
import psutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("[X-StylerV2] ⚠️ Jinja2未安装，使用内置模板渲染")

from core_v2.state_machine import StateMachine, ExecutionState


class XStylerV2:
    """
    X-Styler V2 渲染器
    
    "Sea-Glass" 模板：毛玻璃拟物设计
    """
    
    # 配色方案
    COLORS = {
        "primary": "#1e3a8a",      # 工业蓝
        "secondary": "#1f2937",    # 石墨灰
        "success": "#17BF63",      # 成功绿
        "warning": "#FFAD1F",      # 警示橙
        "error": "#E0245E",        # 错误红
        "accent": "#8b5cf6",       # 强调紫
    }
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        初始化渲染器
        
        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.state_machine = StateMachine()
        
        # 初始化 Jinja2
        if JINJA2_AVAILABLE and self.template_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml']),
                # 自定义过滤器
            )
            self.env.filters['convergence_color'] = self._convergence_color_filter
            self.env.filters['truncate'] = self._truncate_filter
            self.use_jinja = True
        else:
            self.use_jinja = False
        
        # 资产统计
        self._asset_cache = None
        self._asset_cache_time = 0
    
    def _convergence_color_filter(self, value: float) -> str:
        """收敛度颜色过滤器"""
        if value >= 0.7:
            return self.COLORS["success"]
        elif value >= 0.4:
            return self.COLORS["warning"]
        else:
            return self.COLORS["error"]
    
    def _truncate_filter(self, value: str, length: int = 200) -> str:
        """截断过滤器"""
        if len(value) > length:
            return value[:length] + "..."
        return value
    
    def _get_system_stats(self) -> Dict:
        """获取系统状态"""
        try:
            mem = psutil.virtual_memory()
            return {
                "mem_usage": mem.percent,
                "mem_available": mem.available / (1024 * 1024),  # MB
                "cpu_count": psutil.cpu_count(),
            }
        except:
            return {"mem_usage": 50, "mem_available": 1024, "cpu_count": 2}
    
    def _get_asset_stats(self) -> Dict:
        """
        获取资产统计
        
        Returns:
            资产看板数据
        """
        # 缓存5分钟
        if self._asset_cache and time.time() - self._asset_cache_time < 300:
            return self._asset_cache
        
        data_dir = Path(__file__).parent.parent / "data"
        
        stats = {
            "golden_cases": 0,
            "indexed": False,
            "last_update": "N/A",
            "api_remaining": 70000,  # 默认值
        }
        
        # 统计黄金数据集
        golden_file = data_dir / "golden_dataset.jsonl"
        if golden_file.exists():
            try:
                with open(golden_file, 'r') as f:
                    stats["golden_cases"] = sum(1 for _ in f)
            except:
                pass
        
        # 检查向量索引
        index_file = data_dir / "vector_index.faiss"
        stats["indexed"] = index_file.exists()
        
        # API额度（从配置读取）
        api_quota_file = Path.home() / ".openclaw" / "workspace" / "api_quota.json"
        if api_quota_file.exists():
            try:
                with open(api_quota_file, 'r') as f:
                    quota_data = json.load(f)
                    stats["api_remaining"] = quota_data.get("remaining", 70000)
            except:
                pass
        
        self._asset_cache = stats
        self._asset_cache_time = time.time()
        return stats
    
    def render_thinking_trace(self, duration_ms: int = 800) -> str:
        """
        渲染思考指纹
        
        展示苏格拉底追问的思考过程
        
        Args:
            duration_ms: 动画持续时间
            
        Returns:
            HTML 思考轨迹卡片
        """
        if self.use_jinja:
            template = self.env.get_template("thinking_trace.html")
            return template.render(
                duration_ms=duration_ms,
                colors=self.COLORS,
                timestamp=datetime.now().strftime("%H:%M:%S"),
            )
        else:
            return self._render_inline_thinking_trace(duration_ms)
    
    def _render_inline_thinking_trace(self, duration_ms: int) -> str:
        """内联思考轨迹模板"""
        return f'''<!-- 海狸思考指纹 -->
<div class="beaver-thinking-container" style="animation: fadeIn {duration_ms}ms ease-out">
    <div class="flex items-center gap-2 mb-2">
        <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
        <span class="text-sm text-slate-600 font-mono">🦫 海狸正在检索 10855 条黄金数据...</span>
    </div>
    <div class="bg-slate-50 rounded-lg p-3 border-l-4 border-blue-500">
        <div class="space-y-1 text-xs text-slate-500">
            <p>→ 解析意图关键词</p>
            <p>→ 计算收敛系数</p>
            <p>→ 路由模型决策</p>
        </div>
    </div>
</div>

<style>
.beaver-thinking-container {{
    opacity: 0;
    animation: fadeIn {duration_ms}ms ease-out forwards;
}}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
</style>'''
    
    def render_decision_card(
        self,
        convergence: float,
        model: str,
        intent: str,
        route_reason: str,
        latency: float = 0.0,
        content: str = "",
        show_trace: bool = True
    ) -> str:
        """
        渲染决策卡片
        
        展示完整的执行决策链
        
        Args:
            convergence: 收敛度
            model: 选中的模型
            intent: 意图类型
            route_reason: 路由原因
            latency: 响应延迟
            content: 主要内容
            show_trace: 是否显示思考轨迹
            
        Returns:
            HTML 决策卡片
        """
        # 更新状态机
        self.state_machine.transition(
            ExecutionState.COMPLETED,
            convergence=convergence,
            model_selected=model,
            intent=intent,
            route_reason=route_reason,
            latency=latency
        )
        
        # 获取渲染变量
        render_vars = self.state_machine.get_render_vars()
        render_vars["content"] = content
        render_vars["colors"] = self.COLORS
        render_vars["system_stats"] = self._get_system_stats()
        render_vars["asset_stats"] = self._get_asset_stats()
        render_vars["show_trace"] = show_trace
        
        if self.use_jinja:
            template = self.env.get_template("decision_card.html")
            return template.render(**render_vars)
        else:
            return self._render_inline_decision_card(render_vars)
    
    def _render_inline_decision_card(self, vars: Dict) -> str:
        """内联决策卡片模板"""
        # 根据收敛度决定背景
        bg_class = "bg-slate-50" if vars["convergence"] >= 0.3 else "bg-orange-50"
        warning_border = "border-orange-500" if vars["show_warning"] else "border-slate-200"
        
        html = f'''<div class="beaver-container p-6 {bg_class} rounded-xl shadow-lg border {warning_border}">
    <!-- 头部 -->
    <div class="flex justify-between items-center mb-4 border-b pb-2">
        <h3 class="text-lg font-bold text-slate-800">🦫 万能 Skill V2 执行决策</h3>
        <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-xs font-mono">
            Mem: {vars["mem_usage"]} | API: {vars["asset_stats"]["api_remaining"]}
        </span>
    </div>
    
    <!-- 思考轨迹 -->
    {self._render_inline_thinking_trace(800) if vars["show_trace"] else ''}
    
    <!-- 三大指标 -->
    <div class="grid grid-cols-3 gap-3 mb-4">
        <div class="p-3 bg-white rounded-lg border-l-4 border-blue-500 shadow-sm">
            <p class="text-xs text-slate-500 mb-1">执行引擎 / Router</p>
            <p class="text-sm font-mono text-blue-600">{vars["model_selected"]}</p>
            <p class="text-xs text-slate-400 truncate">{vars["route_reason"]}</p>
        </div>
        
        <div class="p-3 bg-white rounded-lg border-l-4 border-green-500 shadow-sm">
            <p class="text-xs text-slate-500 mb-1">沙盒校验 / Sandbox</p>
            <p class="text-sm font-mono text-green-600">{vars["sandbox_status"]} ({vars["latency"]}s)</p>
        </div>
        
        <div class="p-3 bg-white rounded-lg border-l-4 border-purple-500 shadow-sm">
            <p class="text-xs text-slate-500 mb-1">意图收敛 / Align</p>
            <span class="px-2 py-1 {vars["convergence_color"]} rounded text-sm font-bold">{vars["convergence_pct"]}</span>
        </div>
    </div>
    
    <!-- 内容区 -->
    <div class="bg-white rounded-lg p-4 mb-4 prose max-w-none">
        {vars["content"]}
    </div>
    
    <!-- 来源标签 -->
    <div class="flex items-center gap-2 text-xs text-slate-500">
        <span class="px-2 py-1 bg-slate-100 rounded">{vars["intent"]}</span>
        {f'<span class="px-2 py-1 bg-green-100 text-green-700 rounded">本地向量库</span>' if vars["local_mode"] else ''}
        <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded">Golden: {vars["asset_stats"]["golden_cases"]}条</span>
    </div>
    
    <!-- 苏格拉底逻辑 -->
    <div class="mt-4 p-3 bg-slate-100 rounded-lg text-sm text-slate-600 italic">
        "{vars["socratic_logic"]}"
    </div>
</div>'''
        
        return html
    
    def render_socratic_probe(
        self,
        questions: List[Dict],
        convergence: float,
        intent: str,
        message: str = None
    ) -> str:
        """
        渲染苏格拉底追问卡片
        
        Args:
            questions: 问题列表
            convergence: 当前收敛度
            intent: 意图类型
            message: 提示消息
            
        Returns:
            HTML 追问卡片
        """
        self.state_machine.transition(
            ExecutionState.PROBING,
            convergence=convergence,
            intent=intent
        )
        
        render_vars = self.state_machine.get_render_vars()
        render_vars["questions"] = questions
        render_vars["message"] = message or "大帅，在动用沙盒前，需同步物理参数："
        render_vars["colors"] = self.COLORS
        
        if self.use_jinja:
            template = self.env.get_template("socratic_probe.html")
            return template.render(**render_vars)
        else:
            return self._render_inline_socratic_probe(render_vars)
    
    def _render_inline_socratic_probe(self, vars: Dict) -> str:
        """内联苏格拉底追问模板"""
        questions_html = ""
        for q in vars["questions"]:
            dimension = q.get("dimension", "WHAT")
            question = q.get("question", "")
            options = q.get("options", [])
            importance = q.get("importance", "IMPORTANT")
            
            border_color = "#1DA1F2" if importance == "CRITICAL" else "#6b7280"
            options_html = "".join([f'<span class="text-xs bg-slate-200 px-2 py-1 rounded">{opt}</span>' for opt in options[:4]])
            
            questions_html += f'''
            <div class="border-l-4 pl-4 py-2 my-2" style="border-color: {border_color}">
                <p class="text-xs font-bold uppercase text-blue-600">{dimension}</p>
                <p class="text-sm text-slate-700 mt-1">{question}</p>
                <div class="flex gap-2 mt-2">{options_html}</div>
            </div>'''
        
        return f'''<div class="bg-slate-900 rounded-xl p-6 text-white shadow-xl">
    <!-- 头部 -->
    <div class="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
        <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span class="text-xs font-mono text-blue-400">SOCRATIC_PROBE_V2</span>
        </div>
        <span class="text-xs font-mono" style="color: {self.COLORS["warning"]}">收敛度: {vars["convergence_pct"]}</span>
    </div>
    
    <!-- 消息 -->
    <h2 class="text-lg mb-4">{vars["message"]}</h2>
    
    <!-- 问题列表 -->
    {questions_html}
    
    <!-- 底部 -->
    <div class="mt-4 pt-4 border-t border-slate-700 flex justify-between items-center">
        <span class="text-xs text-slate-400 italic">"我思故我在" - 海狸正在探明需求...</span>
        <button class="bg-white text-slate-900 px-4 py-2 rounded-full text-xs font-bold">确认意图并执行</button>
    </div>
</div>'''
    
    def render_error_card(
        self,
        error_message: str,
        suggestion: str = None,
        convergence: float = 0.0
    ) -> str:
        """
        渲染错误卡片
        
        Args:
            error_message: 错误信息
            suggestion: 解决建议
            convergence: 收敛度
            
        Returns:
            HTML 错误卡片
        """
        self.state_machine.transition(
            ExecutionState.FAILED,
            convergence=convergence
        )
        
        render_vars = self.state_machine.get_render_vars()
        render_vars["error_message"] = error_message
        render_vars["suggestion"] = suggestion
        
        if self.use_jinja:
            template = self.env.get_template("error_card.html")
            return template.render(**render_vars)
        else:
            suggestion_html = f'<div class="mt-4 p-3 bg-red-50 rounded-lg"><p class="text-sm text-red-600">💡 建议: {suggestion}</p></div>' if suggestion else ''
            return f'''<div class="bg-red-50 rounded-xl p-6 border border-red-300 shadow-lg">
    <div class="flex items-center gap-2 mb-4">
        <div class="w-3 h-3 bg-red-500 rounded-full"></div>
        <span class="text-sm font-mono text-red-600">EXECUTION_ERROR</span>
    </div>
    
    <h3 class="text-red-700 font-bold mb-2">执行失败</h3>
    <p class="text-sm text-slate-600">{error_message}</p>
    {suggestion_html}
    
    <div class="mt-4 text-xs text-slate-400">收敛系数过低，请补充参数后重试</div>
</div>'''
    
    def render_asset_dashboard(self) -> str:
        """
        渲染资产看板
        
        Returns:
            HTML 资产看板组件
        """
        asset_stats = self._get_asset_stats()
        system_stats = self._get_system_stats()
        
        render_vars = {
            "asset_stats": asset_stats,
            "system_stats": system_stats,
            "colors": self.COLORS,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        
        if self.use_jinja:
            template = self.env.get_template("asset_dashboard.html")
            return template.render(**render_vars)
        else:
            return f'''<!-- 资产看板 -->
<div class="bg-gradient-to-r from-slate-800 to-slate-900 rounded-lg p-4 text-white">
    <div class="flex justify-between items-center mb-3">
        <span class="text-sm font-bold">📊 数据资产看板</span>
        <span class="text-xs text-slate-400">{render_vars["timestamp"]}</span>
    </div>
    
    <div class="grid grid-cols-3 gap-3">
        <div class="text-center">
            <p class="text-2xl font-bold text-blue-400">{asset_stats["golden_cases"]}</p>
            <p class="text-xs text-slate-400">黄金案例</p>
        </div>
        <div class="text-center">
            <p class="text-2xl font-bold text-green-400">{asset_stats["api_remaining"]}</p>
            <p class="text-xs text-slate-400">API额度</p>
        </div>
        <div class="text-center">
            <p class="text-2xl font-bold text-purple-400">{system_stats["mem_usage"]}%</p>
            <p class="text-xs text-slate-400">内存占用</p>
        </div>
    </div>
    
    <div class="mt-3 flex gap-2 text-xs">
        <span class="px-2 py-1 bg-slate-700 rounded">{'✅ 已索引' if asset_stats["indexed"] else '⚠️ 未索引'}</span>
        <span class="px-2 py-1 bg-blue-900/50 text-blue-300 rounded">向量库: nomic-embed-text</span>
    </div>
</div>'''
    
    def render_full_output(
        self,
        content: str,
        convergence: float,
        model: str,
        intent: str,
        show_dashboard: bool = True
    ) -> str:
        """
        渲染完整输出
        
        包含：思考轨迹 + 决策卡片 + 资产看板
        
        Args:
            content: 主要内容
            convergence: 收敛度
            model: 模型
            intent: 意图
            show_dashboard: 是否显示资产看板
            
        Returns:
            HTML 完整输出
        """
        parts = []
        
        # 1. 思考指纹（收敛度低时显示）
        if convergence < 0.5:
            parts.append(self.render_thinking_trace())
        
        # 2. 决策卡片
        parts.append(self.render_decision_card(
            convergence=convergence,
            model=model,
            intent=intent,
            route_reason="",
            content=content
        ))
        
        # 3. 资产看板
        if show_dashboard:
            parts.append(self.render_asset_dashboard())
        
        return "\n".join(parts)


# 测试
if __name__ == "__main__":
    styler = XStylerV2()
    
    # 测试决策卡片
    html = styler.render_decision_card(
        convergence=0.25,
        model="glm-5",
        intent="cnc_quote",
        route_reason="低收敛度，启用GLM-5追问",
        latency=1.5,
        content="这是一段测试内容...",
        show_trace=True
    )
    
    print("=" * 50)
    print("决策卡片测试:")
    print("=" * 50)
    print(html[:500] + "...")
    
    print("\n" + "=" * 50)
    print("资产看板测试:")
    print("=" * 50)
    print(styler.render_asset_dashboard())