#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拟人化输出器 - 万能Skill V2绣花能力核心
让输出接地气，禁止AI化、硬代码、套娃

大帅指示：
- 口语化表达
- 真实数据优先
- 不说废话
"""

from typing import Dict, Optional
from user_preference_reader import get_user_reader


class HumanizedOutput:
    """
    拟人化输出器
    
    原则：
    1. 不说"好的"、"明白了"这种AI话
    2. 不套娃（不重复）
    3. 不硬代码（动态数据）
    4. 不想象（真实数据）
    """
    
    # 禁止的AI化词汇
    AI_WORDS = [
        "好的", "明白", "我理解", "我可以", "我将",
        "根据您的需求", "以下是", "总结如下",
        "首先", "其次", "最后", "综上所述",
        "希望对您有帮助", "如有问题请随时"
    ]
    
    # 口语化替换
    COLLOQUIAL = {
        "执行成功": "搞定",
        "执行失败": "有问题",
        "正在处理": "搞起",
        "处理完成": "完事",
        "请稍等": "等下",
        "分析完成": "看完了",
        "生成完成": "整好了"
    }
    
    def __init__(self):
        self.reader = get_user_reader()
    
    def clean_ai_words(self, text: str) -> str:
        """清除AI化词汇"""
        for word in self.AI_WORDS:
            text = text.replace(word, "")
        return text
    
    def make_colloquial(self, text: str) -> str:
        """口语化"""
        for formal, casual in self.COLLOQUIAL.items():
            text = text.replace(formal, casual)
        return text
    
    def format_task_result(
        self,
        task_type: str,
        success: bool,
        content: str,
        data: Optional[Dict] = None
    ) -> str:
        """
        格式化任务结果
        
        拟人化、接地气、不说废话
        """
        # 获取用户偏好
        user_ctx = self.reader.get_user_context()
        name = user_ctx.get("name", "大帅")
        
        # 开场（口语化）
        if success:
            if task_type == "cnc_quote":
                opening = f"嘿{name}，这单子我看过了"
            elif task_type == "code_gen":
                opening = f"{name}，代码写好了"
            elif task_type == "document_gen":
                opening = f"{name}，文档整完了"
            else:
                opening = f"{name}，搞定了"
        else:
            opening = f"{name}，这个有点问题"
        
        # 清理AI化词汇
        content = self.clean_ai_words(content)
        content = self.make_colloquial(content)
        
        # 真实数据（不想象）
        real_data = ""
        if data:
            if "price" in data:
                real_data += f"\n报价: {data['price']}元"
            if "time" in data:
                real_data += f"\n耗时: {data['time']}秒"
            if "convergence" in data:
                real_data += f"\n收敛: {data['convergence']*100:.0f}%"
        
        # 结尾（简单直接）
        if success:
            ending = "\n\n还有啥？"
        else:
            ending = "\n\n要不要再试试？"
        
        return f"{opening}\n\n{content}{real_data}{ending}"
    
    def format_probe_questions(
        self,
        questions: list,
        convergence: float
    ) -> str:
        """
        格式化探明问题
        
        不套娃、不说废话
        """
        user_ctx = self.reader.get_user_context()
        name = user_ctx.get("name", "大帅")
        
        # 直接说事
        if convergence < 0.3:
            opening = f"{name}，这需求太笼统了，得确认几个事："
        elif convergence < 0.6:
            opening = f"{name}，再确认下细节："
        else:
            opening = f"{name}，最后确认下："
        
        # 问题列表（简洁）
        q_list = []
        for i, q in enumerate(questions[:3], 1):
            dimension = q.get("dimension", "?")
            question = q.get("question", "")
            q_list.append(f"{i}. [{dimension}] {question}")
        
        return f"{opening}\n\n" + "\n".join(q_list) + "\n\n你说？"
    
    def format_error(
        self,
        error_type: str,
        message: str
    ) -> str:
        """
        格式化错误信息
        
        不说"抱歉"、"不好意思"
        """
        user_ctx = self.reader.get_user_context()
        name = user_ctx.get("name", "大帅")
        
        if "timeout" in error_type.lower():
            return f"{name}，API超时了，再试一次？"
        elif "not_found" in error_type.lower():
            return f"{name}，没找到，换个说法试试？"
        else:
            return f"{name}，{message}，怎么整？"


# 测试
if __name__ == "__main__":
    output = HumanizedOutput()
    
    # 测试成功输出
    result = output.format_task_result(
        task_type="cnc_quote",
        success=True,
        content="铝合金6061零件报价",
        data={"price": 1250, "time": 3.5}
    )
    print(result)
    
    print("\n" + "="*50 + "\n")
    
    # 测试探明问题
    probe = output.format_probe_questions(
        questions=[
            {"dimension": "WHAT", "question": "材质是啥？"},
            {"dimension": "HOW_MUCH", "question": "精度要求？"}
        ],
        convergence=0.3
    )
    print(probe)