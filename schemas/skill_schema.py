#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Skill Schema - 统一技能数据结构
所有外部技能源都转换为此格式
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class SkillType(Enum):
    """技能类型"""
    GENERATOR = "generator"      # 生成类（PDF、报告、代码）
    ANALYZER = "analyzer"        # 分析类（数据、日志、代码）
    TRANSFORMER = "transformer"  # 转换类（格式转换、翻译）
    CONNECTOR = "connector"      # 连接类（API调用、数据获取）
    ORCHESTRATOR = "orchestrator"  # 编排类（组合其他技能）
    UTILITY = "utility"          # 工具类（计算、验证）


class ExecutionMode(Enum):
    """执行模式"""
    SYNC = "sync"        # 同步执行
    ASYNC = "async"      # 异步执行
    STREAMING = "streaming"  # 流式输出


class SkillStatus(Enum):
    """技能状态"""
    INSTALLED = "installed"    # 已安装
    CACHED = "cached"          # 已缓存
    AVAILABLE = "available"    # 可用（未安装）
    BROKEN = "broken"          # 损坏
    DEPRECATED = "deprecated"  # 已废弃


@dataclass
class SkillInput:
    """技能输入定义"""
    name: str
    type: str  # string, number, file, json, etc.
    required: bool = True
    default: Any = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "default": self.default,
            "description": self.description
        }


@dataclass
class SkillOutput:
    """技能输出定义"""
    name: str
    type: str  # string, file, json, etc.
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description
        }


@dataclass
class SkillMetadata:
    """技能元数据"""
    author: str = ""
    version: str = "1.0.0"
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "tags": self.tags,
            "dependencies": self.dependencies
        }


@dataclass
class Skill:
    """
    统一技能数据结构
    所有外部源的技能都转换为此格式
    """
    id: str                              # 唯一标识
    name: str                            # 技能名称
    description: str                     # 描述
    skill_type: SkillType                # 类型
    inputs: List[SkillInput]             # 输入定义
    outputs: List[SkillOutput]           # 输出定义
    metadata: SkillMetadata              # 元数据
    
    # 来源信息
    source: str = "local"                # 来源：local/clawhub/github
    source_url: str = ""                 # 原始URL
    local_path: str = ""                 # 本地路径
    
    # 状态
    status: SkillStatus = SkillStatus.INSTALLED
    execution_mode: ExecutionMode = ExecutionMode.SYNC
    
    # 匹配信息
    keywords: List[str] = field(default_factory=list)  # 关键词
    examples: List[str] = field(default_factory=list)  # 使用示例
    
    # 统计信息
    usage_count: int = 0                 # 使用次数
    success_rate: float = 0.0            # 成功率
    avg_latency: float = 0.0             # 平均延迟
    
    # 执行函数
    execute_func: Optional[str] = ""     # 执行函数路径
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "skill_type": self.skill_type.value,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "metadata": self.metadata.to_dict(),
            "source": self.source,
            "source_url": self.source_url,
            "local_path": self.local_path,
            "status": self.status.value,
            "execution_mode": self.execution_mode.value,
            "keywords": self.keywords,
            "examples": self.examples,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "avg_latency": self.avg_latency
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Skill':
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            skill_type=SkillType(data["skill_type"]),
            inputs=[SkillInput(**i) for i in data.get("inputs", [])],
            outputs=[SkillOutput(**o) for o in data.get("outputs", [])],
            metadata=SkillMetadata(**data.get("metadata", {})),
            source=data.get("source", "local"),
            source_url=data.get("source_url", ""),
            local_path=data.get("local_path", ""),
            status=SkillStatus(data.get("status", "installed")),
            execution_mode=ExecutionMode(data.get("execution_mode", "sync")),
            keywords=data.get("keywords", []),
            examples=data.get("examples", []),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0),
            avg_latency=data.get("avg_latency", 0.0),
            execute_func=data.get("execute_func", "")
        )


@dataclass
class ExecutionPlan:
    """执行计划"""
    task_id: str
    description: str
    steps: List[Dict]  # [{"skill_id": "xxx", "inputs": {...}, "condition": "optional"}]
    mode: str = "sequential"  # sequential/parallel/conditional
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "steps": self.steps,
            "mode": self.mode
        }


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str
    success: bool
    outputs: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    skills_used: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "outputs": self.outputs,
            "errors": self.errors,
            "execution_time": self.execution_time,
            "skills_used": self.skills_used,
            "quality_score": self.quality_score
        }


@dataclass
class Intent:
    """意图解析结果"""
    raw_input: str                       # 原始输入
    keywords: List[str]                  # 提取的关键词
    intent_type: str                     # 意图类型
    domain: str                          # 领域
    confidence: float                    # 置信度
    subtasks: List[Dict]                 # 子任务列表
    constraints: List[str] = field(default_factory=list)  # 约束条件
    needs_confirmation: bool = False     # 是否需要确认 ⭐新增
    
    def to_dict(self) -> Dict:
        return {
            "raw_input": self.raw_input,
            "keywords": self.keywords,
            "intent_type": self.intent_type,
            "domain": self.domain,
            "confidence": self.confidence,
            "subtasks": self.subtasks,
            "constraints": self.constraints,
            "needs_confirmation": self.needs_confirmation
        }


# 导出
__all__ = [
    'SkillType', 'ExecutionMode', 'SkillStatus',
    'SkillInput', 'SkillOutput', 'SkillMetadata',
    'Skill', 'ExecutionPlan', 'ExecutionResult', 'Intent'
]