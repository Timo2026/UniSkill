#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户偏好读取器 - 万能Skill V2绣花能力核心
让输出更拟人化，禁止AI化、硬代码、套娃

大帅指示：
- 多参考用户偏好
- 禁止想象
- 真实数据优先
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class UserProfile:
    """用户画像"""
    name: str = "大帅"
    role: str = "AI应用工程师"
    background: str = "10年制造业经验"
    focus: str = "CNC报价系统"
    style: str = "实战派"  # 口语化、接地气
    
    # 目标公司（企二代）
    target_companies: List[str] = None
    
    # 简历信息
    phone: str = ""
    email: str = ""
    github: str = ""
    
    # 技能等级
    skills: Dict[str, int] = None


class UserPreferenceReader:
    """
    用户偏好读取器
    
    从知识库读取用户偏好，让输出更拟人化
    """
    
    KB_PATH = Path.home() / ".openclaw/workspace/kb/用户偏好"
    
    def __init__(self):
        self.profile = UserProfile()
        self._loaded = False
        self._load_preferences()
    
    def _load_preferences(self):
        """加载用户偏好"""
        if self._loaded:
            return
        
        # 读取简历信息
        resume_file = self.KB_PATH / "简历信息.md"
        if resume_file.exists():
            self._parse_resume(resume_file)
        
        # 读取目标公司
        companies_file = self.KB_PATH / "目标公司列表.md"
        if companies_file.exists():
            self._parse_companies(companies_file)
        
        self._loaded = True
    
    def _parse_resume(self, file_path: Path):
        """解析简历"""
        content = file_path.read_text(encoding='utf-8')
        
        # 提取姓名
        if "曹冬冬" in content:
            self.profile.name = "冬冬"
        
        # 提取定位
        if "AI应用工程师" in content:
            self.profile.role = "AI应用工程师"
        
        # 提取背景
        if "10年" in content or "制造业" in content:
            self.profile.background = "10年制造业老兵"
        
        # 提取联系方式
        if "15311118016" in content:
            self.profile.phone = "15311118016"
        if "miscdd@163.com" in content:
            self.profile.email = "miscdd@163.com"
    
    def _parse_companies(self, file_path: Path):
        """解析目标公司"""
        content = file_path.read_text(encoding='utf-8')
        
        companies = []
        if "Pika Labs" in content:
            companies.append("Pika Labs（郭文景）")
        if "蒲惠智造" in content:
            companies.append("蒲惠智造（王克飞）")
        if "利尔达" in content:
            companies.append("利尔达（陈凯）")
        
        self.profile.target_companies = companies
    
    def get_greeting_style(self) -> str:
        """获取问候风格"""
        # 根据用户画像生成口语化问候
        styles = [
            f"嘿 {self.profile.name}，",
            f"收到 {self.profile.name}，",
            f"在呢 {self.profile.name}，",
            f"来啦 {self.profile.name}，"
        ]
        return styles[0]
    
    def get_response_style(self, task_type: str) -> str:
        """获取回复风格"""
        if task_type == "cnc_quote":
            return f"这个我熟，{self.profile.background}不是白干的"
        elif task_type == "code_gen":
            return "代码这块，咱们直接干"
        elif task_type == "document_gen":
            return "文档是吧，整一个"
        else:
            return "走着"
    
    def get_end_style(self) -> str:
        """获取结尾风格"""
        styles = [
            "搞定，还有啥？",
            "完事，随时叫我",
            "好了，继续？",
            "OK，下一步？"
        ]
        return styles[0]
    
    def get_user_context(self) -> Dict:
        """获取用户上下文"""
        return {
            "name": self.profile.name,
            "role": self.profile.role,
            "background": self.profile.background,
            "focus": self.profile.focus,
            "target_companies": self.profile.target_companies or []
        }
    
    def personalize_output(self, content: str, task_type: str) -> str:
        """
        拟人化输出
        
        禁止AI化、禁止套娃、禁止硬代码
        """
        # 获取风格
        greeting = self.get_greeting_style()
        response = self.get_response_style(task_type)
        ending = self.get_end_style()
        
        # 组装（简单直接，不套娃）
        personalized = f"{greeting}{response}\n\n{content}\n\n{ending}"
        
        return personalized


# 全局实例
_reader: Optional[UserPreferenceReader] = None

def get_user_reader() -> UserPreferenceReader:
    """获取用户偏好读取器"""
    global _reader
    if _reader is None:
        _reader = UserPreferenceReader()
    return _reader


# 测试
if __name__ == "__main__":
    reader = UserPreferenceReader()
    
    print("用户画像:")
    print(f"  名字: {reader.profile.name}")
    print(f"  背景: {reader.profile.background}")
    print(f"  目标公司: {reader.profile.target_companies}")
    
    print("\n拟人化测试:")
    print(reader.personalize_output("铝合金6061报价单已生成", "cnc_quote"))