#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Skill - 万能技能系统
"""

from .main import UniversalSkill
from .schemas.skill_schema import Skill, Intent, ExecutionResult
from .core.intent_parser import IntentParser
from .core.skill_finder import SkillFinder
from .core.orchestrator import Orchestrator
from .core.quality_checker import QualityChecker
from .core.learning_loop import LearningLoop

__version__ = "1.0.0"
__all__ = [
    "UniversalSkill",
    "Skill", "Intent", "ExecutionResult",
    "IntentParser", "SkillFinder", "Orchestrator",
    "QualityChecker", "LearningLoop"
]