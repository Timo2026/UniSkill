#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X-Styler渲染器 - OpenClaw核心重构
X.com风格高画质交付看板

大帅指示：
- 高保真容器
- 禁止废话
- 真实指标
"""

from typing import Dict, List, Optional
from datetime import datetime


class XStylerRenderer:
    """
    X-Styler渲染器
    
    将苏格拉底提问和最终交付统一装入高保真容器
    """
    
    @staticmethod
    def render_socratic_card(
        questions: List[Dict],
        convergence_rate: float,
        intent: str,
        message: str = None
    ) -> str:
        """
        渲染苏格拉底探明卡片
        
        X.com风格高画质交付
        """
        # 收敛系数颜色
        if convergence_rate >= 0.8:
            convergence_color = "#17BF63"  # 绿色
            convergence_text = "READY"
        elif convergence_rate >= 0.5:
            convergence_color = "#FFAD1F"  # 橙色
            convergence_text = "PROBING"
        else:
            convergence_color = "#E0245E"  # 红色
            convergence_text = "CRITICAL"
        
        # 生成问题HTML
        questions_html = XStylerRenderer._render_questions(questions)
        
        # 默认消息
        if not message:
            message = "大帅，在动用沙盒前，需同步物理参数："
        
        return f'''<div class="max-w-xl bg-black border border-gray-800 rounded-2xl font-sans text-white shadow-2xl overflow-hidden">
    <!-- 头部 -->
    <div class="px-4 py-3 border-b border-gray-800 flex justify-between items-center bg-gray-900/30">
        <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span class="text-xs font-mono text-blue-400 tracking-tighter">SOCRATIC_PROBE_V2</span>
        </div>
        <div class="text-[10px] text-gray-500 font-mono">
            ALIGNMENT: <span style="color: {convergence_color}">{convergence_rate*100:.0f}%</span>
        </div>
    </div>

    <!-- 主体 -->
    <div class="p-6">
        <h1 class="text-lg font-bold mb-4">{message}</h1>
        <div class="space-y-4">
            {questions_html}
        </div>
    </div>

    <!-- 底部 -->
    <div class="px-6 py-4 bg-blue-950/20 border-t border-gray-800 flex items-center justify-between">
        <span class="text-xs text-gray-500 italic">"我思故我在" - OpenClaw 正在探明需求...</span>
        <button class="bg-white text-black text-xs font-bold py-1.5 px-4 rounded-full hover:bg-gray-200 transition-all">
            确认意图并执行
        </button>
    </div>
</div>'''
    
    @staticmethod
    def _render_questions(questions: List[Dict]) -> str:
        """渲染问题列表"""
        html_parts = []
        
        for q in questions:
            dimension = q.get("dimension", "WHAT")
            question = q.get("question", "")
            options = q.get("options", [])
            importance = q.get("importance", "IMPORTANT")
            color = q.get("color", "#1DA1F2")
            
            # 重要性边框颜色
            if importance == "CRITICAL":
                border_class = "border-blue-500"
            elif importance == "IMPORTANT":
                border_class = "border-gray-600"
            else:
                border_class = "border-gray-700"
            
            # 生成选项HTML
            options_html = ""
            if options:
                options_html = '<div class="flex flex-wrap gap-2 mt-2">'
                for opt in options[:4]:  # 最多4个选项
                    options_html += f'''<span class="text-[10px] bg-gray-800 px-2 py-1 rounded text-gray-400">{opt}</span>'''
                options_html += '</div>'
            
            html_parts.append(f'''<div class="group border-l-2 {border_class} pl-4 py-1 hover:bg-gray-900 transition-all">
    <p class="text-xs font-bold uppercase tracking-widest" style="color: {color}">{dimension}</p>
    <p class="text-sm text-gray-300 mt-1">{question}</p>
    {options_html}
</div>''')
        
        return '\n            '.join(html_parts)
    
    @staticmethod
    def render_execution_result(
        task_id: str,
        success: bool,
        outputs: Dict,
        execution_time: float,
        model: str,
        convergence_rate: float
    ) -> str:
        """
        渲染执行结果卡片
        
        展示真实指标，禁止废话
        """
        status_color = "#17BF63" if success else "#E0245E"
        status_text = "SUCCESS" if success else "FAILED"
        
        # 输出预览
        output_preview = ""
        if outputs:
            content = outputs.get("content", outputs.get("code", ""))
            if content:
                # 截取预览
                preview = content[:200] + "..." if len(content) > 200 else content
                output_preview = f'''<div class="mt-4 bg-gray-900 rounded-lg p-3">
    <pre class="text-xs text-gray-400 whitespace-pre-wrap">{preview}</pre>
</div>'''
        
        return f'''<div class="max-w-xl bg-black border border-gray-800 rounded-2xl font-sans text-white shadow-2xl overflow-hidden">
    <!-- 头部 -->
    <div class="px-4 py-3 border-b border-gray-800 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full" style="background: {status_color}"></div>
            <span class="text-xs font-mono" style="color: {status_color}">{status_text}</span>
        </div>
        <div class="text-[10px] text-gray-500 font-mono">ID: {task_id[:16]}</div>
    </div>

    <!-- 统计 -->
    <div class="grid grid-cols-4 gap-px bg-gray-800">
        <div class="bg-black p-3 text-center">
            <p class="text-[10px] text-gray-500 uppercase">耗时</p>
            <p class="text-lg font-bold">{execution_time:.1f}s</p>
        </div>
        <div class="bg-black p-3 text-center">
            <p class="text-[10px] text-gray-500 uppercase">模型</p>
            <p class="text-lg font-bold">{model.split(':')[0] if model else 'N/A'}</p>
        </div>
        <div class="bg-black p-3 text-center">
            <p class="text-[10px] text-gray-500 uppercase">收敛</p>
            <p class="text-lg font-bold">{convergence_rate*100:.0f}%</p>
        </div>
        <div class="bg-black p-3 text-center">
            <p class="text-[10px] text-gray-500 uppercase">状态</p>
            <p class="text-lg font-bold" style="color: {status_color}">{'✓' if success else '✗'}</p>
        </div>
    </div>

    <!-- 输出预览 -->
    {output_preview}

    <!-- 底部 -->
    <div class="px-6 py-3 border-t border-gray-800">
        <span class="text-xs text-gray-500">OpenClaw Universal Skill V2 - 苏格拉底+5W2H深度锚定版</span>
    </div>
</div>'''
    
    @staticmethod
    def render_error_card(
        error_message: str,
        suggestion: str = None
    ) -> str:
        """
        渲染错误卡片
        
        禁止废话，给出真实原因和解决建议
        """
        suggestion_html = ""
        if suggestion:
            suggestion_html = f'''<div class="mt-4 bg-red-950/30 rounded-lg p-3">
    <p class="text-xs text-red-400">💡 建议: {suggestion}</p>
</div>'''
        
        return f'''<div class="max-w-xl bg-black border border-red-900 rounded-2xl font-sans text-white shadow-2xl overflow-hidden">
    <!-- 头部 -->
    <div class="px-4 py-3 border-b border-red-900 flex items-center gap-2">
        <div class="w-2 h-2 bg-red-500 rounded-full"></div>
        <span class="text-xs font-mono text-red-400">EXECUTION_ERROR</span>
    </div>

    <!-- 错误信息 -->
    <div class="p-6">
        <h2 class="text-red-400 font-bold mb-2">执行失败</h2>
        <p class="text-sm text-gray-400">{error_message}</p>
        {suggestion_html}
    </div>

    <!-- 底部 -->
    <div class="px-6 py-3 border-t border-gray-800">
        <span class="text-xs text-gray-500">收敛系数过低，请补充参数后重试</span>
    </div>
</div>'''


# 测试
if __name__ == "__main__":
    # 测试苏格拉底卡片
    questions = [
        {
            "dimension": "what",
            "question": "本次报价的核心对象是？",
            "options": ["单个零件", "批量报价", "对比报价"],
            "importance": "CRITICAL",
            "color": "#1DA1F2"
        },
        {
            "dimension": "how_much",
            "question": "公差精度要求？",
            "options": ["±0.01mm", "±0.05mm", "±0.1mm"],
            "importance": "CRITICAL",
            "color": "#17BF63"
        }
    ]
    
    html = XStylerRenderer.render_socratic_card(
        questions=questions,
        convergence_rate=0.3,
        intent="cnc_quote"
    )
    
    print(html[:500] + "...")