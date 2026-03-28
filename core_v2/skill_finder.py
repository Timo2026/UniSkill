#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能发现 - 万能Skill V2
从V1借鉴，动态发现和加载技能

功能：
- ClawHub技能搜索
- 本地技能发现
- 动态加载
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class SkillFinder:
    """
    技能发现器
    
    来源：
    1. 本地skills目录
    2. ClawHub（需联网）
    3. GitHub（需联网）
    """
    
    LOCAL_SKILLS_PATH = Path.home() / ".openclaw/workspace/skills"
    CLAWHUB_URL = "https://clawhub.com/api/skills"
    
    def __init__(self):
        self.local_skills: List[Dict] = []
        self._scan_local()
    
    def _scan_local(self):
        """扫描本地技能"""
        if not self.LOCAL_SKILLS_PATH.exists():
            return
        
        for skill_dir in self.LOCAL_SKILLS_PATH.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    self.local_skills.append({
                        "name": skill_dir.name,
                        "path": str(skill_dir),
                        "has_skill_md": True
                    })
    
    def find_local(self, keyword: str) -> List[Dict]:
        """搜索本地技能"""
        results = []
        for skill in self.local_skills:
            if keyword.lower() in skill["name"].lower():
                results.append(skill)
        return results
    
    def find_clawhub(self, keyword: str) -> List[Dict]:
        """搜索ClawHub技能"""
        # 需要clawhub CLI
        try:
            result = subprocess.run(
                ["clawhub", "search", keyword],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return [{"source": "clawhub", "keyword": keyword}]
        except:
            pass
        
        return []
    
    def install(self, skill_name: str, source: str = "clawhub") -> bool:
        """安装技能"""
        if source == "clawhub":
            try:
                result = subprocess.run(
                    ["clawhub", "install", skill_name],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.returncode == 0
            except:
                return False
        
        return False
    
    def list_local(self) -> List[Dict]:
        """列出本地技能"""
        return self.local_skills
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """获取技能信息"""
        for skill in self.local_skills:
            if skill["name"] == skill_name:
                skill_md = Path(skill["path"]) / "SKILL.md"
                if skill_md.exists():
                    return {
                        **skill,
                        "description": skill_md.read_text(encoding='utf-8')[:500]
                    }
        return None


# 全局实例
_finder: Optional[SkillFinder] = None

def get_skill_finder() -> SkillFinder:
    """获取技能发现器"""
    global _finder
    if _finder is None:
        _finder = SkillFinder()
    return _finder


# 测试
if __name__ == "__main__":
    finder = SkillFinder()
    
    print(f"本地技能: {len(finder.list_local())}个")
    for skill in finder.list_local():
        print(f"  - {skill['name']}")
