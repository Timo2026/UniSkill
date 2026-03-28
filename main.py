#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Skill v2.0 - 混合架构版
模块化、可插拔的万能技能系统
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from schemas.skill_schema import Intent, ExecutionResult, Skill
from core.intent_parser import IntentParser
from core.orchestrator import Orchestrator
from core.quality_checker import QualityChecker
from core.learning_loop import LearningLoop

# 插件系统
from plugins import PluginManager, SkillSourcePlugin


class UniversalSkillV2:
    """
    Universal Skill v2.0 - 混合架构版
    
    架构升级：
    - 模块化内核
    - 插件化扩展
    - 多源聚合
    - 可配置启用
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or self._load_config()
        
        # 核心组件
        self.intent_parser = IntentParser()
        self.orchestrator = Orchestrator()
        self.quality_checker = QualityChecker()
        self.learning_loop = LearningLoop()
        
        # 插件管理器
        self.plugin_manager = PluginManager(self.config)
        
        # 初始化插件
        self._init_plugins()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        config_file = Path(__file__).parent / "config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _init_plugins(self):
        """初始化插件"""
        # 注册本地源（优先级最高）
        from plugins.skill_sources import LocalSource
        local_config = self.config.get("sources", {}).get("local", {})
        if local_config.get("enabled", True):
            self.plugin_manager.register(
                LocalSource(local_config),
                priority=local_config.get("priority", 1)
            )
        
        # 注册 CNC执行器源
        from plugins.skill_sources import CNCExecutorSource
        self.plugin_manager.register(
            CNCExecutorSource(),
            priority=0  # 最高优先级
        )
        
        # 注册 ClawHub 源
        from plugins.skill_sources import ClawHubSource
        clawhub_config = self.config.get("sources", {}).get("clawhub", {})
        if clawhub_config.get("enabled", True):
            self.plugin_manager.register(
                ClawHubSource(clawhub_config),
                priority=clawhub_config.get("priority", 2)
            )
        
        # 注册 GitHub 源
        from plugins.skill_sources import GitHubSource
        github_config = self.config.get("sources", {}).get("github", {})
        if github_config.get("enabled", False):
            self.plugin_manager.register(
                GitHubSource(github_config),
                priority=github_config.get("priority", 3)
            )
    
    def execute(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        执行用户任务
        
        Args:
            user_input: 用户输入
            context: 上下文
            
        Returns:
            执行结果
        """
        print(f"\n{'='*60}")
        print(f"Universal Skill v2.0 - 混合架构版")
        print(f"{'='*60}")
        print(f"用户输入: {user_input}")
        
        # ========== 1. 意图解析 ==========
        print("\n[1/5] 意图解析...")
        intent = self.intent_parser.parse(user_input)
        print(f"  关键词: {intent.keywords}")
        print(f"  意图类型: {intent.intent_type}")
        print(f"  领域: {intent.domain}")
        print(f"  置信度: {intent.confidence:.2f}")
        print(f"  子任务: {[s['desc'] for s in intent.subtasks]}")
        
        # ========== 1.5 苏格拉底确认 ⭐新增 ==========
        if intent.needs_confirmation:
            print("\n[1.5/5] 需要确认...")
            confirmation = self._generate_confirmation(intent)
            print(f"  {confirmation['question']}")
            print(f"  选项: {confirmation['options']}")
            
            return {
                "success": False,
                "status": "need_confirmation",
                "intent": intent.to_dict(),
                "confirmation": confirmation,
                "message": "请确认您的意图"
            }
        
        # ========== 2. 多源技能发现 ==========
        print("\n[2/5] 多源技能发现...")
        all_skills = self._find_skills_from_all_sources(intent)
        
        if not all_skills:
            print("  ⚠️ 未找到匹配的技能")
            return {
                "success": False,
                "error": "未找到匹配的技能",
                "intent": intent.to_dict()
            }
        
        print(f"  找到 {len(all_skills)} 个技能:")
        for i, (skill, score, source) in enumerate(all_skills[:10]):
            print(f"    {i+1}. [{source}] {skill.name} (匹配度: {score:.2f})")
        
        # ========== 3. 编排执行 ==========
        print("\n[3/5] 编排执行...")
        skills = [s for s, _, _ in all_skills]
        plan = self.orchestrator.plan(intent, skills)
        print(f"  执行计划: {len(plan.steps)} 步, 模式: {plan.mode}")
        
        result = self.orchestrator.execute(plan, context, intent)  # 传递intent
        
        # ========== 4. 质量检查 ==========
        print("\n[4/5] 质量检查...")
        quality_report = self.quality_checker.check(result.outputs)
        result.quality_score = quality_report.overall_score
        
        print(f"  总体得分: {quality_report.overall_score:.2f}")
        for check_name, (check_result, msg, score) in quality_report.checks.items():
            status = "✅" if check_result.value == "pass" else "⚠️" if check_result.value == "warning" else "❌"
            print(f"    {status} {check_name}: {msg}")
        
        # ========== 5. 学习闭环 ==========
        print("\n[5/5] 学习闭环...")
        self.learning_loop.record_feedback(
            task_id=result.task_id,
            intent=intent.intent_type,
            skills_used=result.skills_used,
            success=result.success,
            execution_time=result.execution_time,
            quality_score=result.quality_score
        )
        
        # 更新源统计
        for skill_id in result.skills_used:
            # 更新本地源统计
            local_source = self.plugin_manager.get_plugin("local")
            if local_source and hasattr(local_source, 'update_stats'):
                local_source.update_stats(skill_id, result.success, result.execution_time)
        
        print(f"  已记录学习数据")
        
        # ========== 返回结果 ==========
        print(f"\n{'='*60}")
        print("执行结果:")
        print(f"{'='*60}")
        print(f"任务ID: {result.task_id}")
        print(f"状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"耗时: {result.execution_time:.2f}s")
        print(f"质量: {result.quality_score:.2f}")
        
        # 人性化消息 ⭐ 新增
        if result.outputs.get("human_message"):
            print(f"\n💬 {result.outputs['human_message']}")
        
        return {
            "success": result.success,
            "task_id": result.task_id,
            "outputs": result.outputs,
            "errors": result.errors,
            "quality_score": result.quality_score,
            "execution_time": result.execution_time,
            "skills_used": result.skills_used,
            "intent": intent.to_dict()
        }
    
    def _find_skills_from_all_sources(self, intent: Intent) -> List[tuple]:
        """
        从所有启用的技能源查找技能
        
        Returns:
            [(Skill, score, source_name)] 列表
        """
        all_results = []
        
        # 获取所有启用的技能源
        sources = self.plugin_manager.get_enabled_sources()
        
        for source in sources:
            try:
                skills_with_scores = source.find(intent)
                for skill, score in skills_with_scores:
                    all_results.append((skill, score, source.name))
            except Exception as e:
                print(f"  [{source.name}] 搜索失败: {e}")
        
        # 按分数排序
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        return all_results
    
    def _generate_confirmation(self, intent: Intent) -> Dict:
        """
        生成苏格拉底式确认问题
        
        Args:
            intent: 解析后的意图
            
        Returns:
            确认问题字典
        """
        # 基于意图生成问题
        questions = {
            "generate": f"您想要生成什么类型的内容？",
            "analyze": f"您想要分析什么数据？",
            "query": f"您想要查询什么信息？",
            "transform": f"您想要进行什么转换操作？",
            "unknown": "请告诉我您具体想要做什么？"
        }
        
        question = questions.get(intent.intent_type, "请确认您的意图")
        
        # 基于关键词生成选项
        options = []
        
        # 从关键词提取可能的选项
        if intent.keywords:
            for kw in intent.keywords[:3]:
                if kw not in ["数量", "格式"]:
                    options.append(f"与「{kw}」相关的操作")
        
        # 添加通用选项
        options.extend([
            "请详细描述我的需求",
            "换个方式表达"
        ])
        
        return {
            "question": f"🤔 {question}\n  我理解的关键词: {', '.join(intent.keywords[:5])}",
            "options": options,
            "confidence": intent.confidence,
            "hint": "请选择一个选项，或直接描述您的具体需求"
        }
    
    def list_plugins(self):
        """列出所有插件"""
        plugins = self.plugin_manager.list_plugins()
        
        print(f"\n已加载插件 ({len(plugins)} 个):")
        print("="*60)
        
        for p in plugins:
            status = "✅" if p["state"] == "enabled" else "⏸️"
            print(f"{status} [{p['priority']}] {p['name']} v{p['version']}")
            if p['description']:
                print(f"   {p['description']}")
    
    def list_skills(self):
        """列出所有可用技能"""
        all_skills = []
        
        sources = self.plugin_manager.get_enabled_sources()
        for source in sources:
            try:
                skills = source.list_available()
                for skill in skills:
                    all_skills.append((skill, source.name))
            except:
                pass
        
        print(f"\n可用技能 ({len(all_skills)} 个):")
        print("="*60)
        
        for skill, source in all_skills[:30]:
            status = "✅" if skill.status.value == "installed" else "📦"
            print(f"{status} [{source}] {skill.id}")
            print(f"   名称: {skill.name}")
            if skill.keywords:
                print(f"   关键词: {', '.join(skill.keywords[:5])}")
    
    def install_skill(self, skill_id: str, source_name: str = None) -> bool:
        """
        安装技能
        
        Args:
            skill_id: 技能ID
            source_name: 来源名称（可选）
        """
        # 找到技能所在的源
        for source in self.plugin_manager.get_enabled_sources():
            if source_name and source.name != source_name:
                continue
            
            skill = source.get(skill_id)
            if skill:
                print(f"从 {source.name} 安装 {skill_id}...")
                return source.install(skill_id)
        
        print(f"未找到技能: {skill_id}")
        return False
    
    def interactive_mode(self):
        """交互模式"""
        print("\n" + "="*60)
        print("Universal Skill v2.0 - 混合架构版")
        print("="*60)
        print("命令:")
        print("  <任务>  - 执行任务")
        print("  plugins - 列出插件")
        print("  skills  - 列出技能")
        print("  stats   - 查看统计")
        print("  report  - 学习报告")
        print("  health  - 健康检查")
        print("  quit    - 退出")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("再见！🦫")
                    break
                
                if user_input.lower() == 'plugins':
                    self.list_plugins()
                    continue
                
                if user_input.lower() == 'skills':
                    self.list_skills()
                    continue
                
                if user_input.lower() == 'stats':
                    stats = self.learning_loop.get_overall_stats()
                    print(f"\n统计: {stats['total_tasks']} 任务, 成功率 {stats['success_rate']:.1%}")
                    continue
                
                if user_input.lower() == 'report':
                    print(self.learning_loop.generate_report())
                    continue
                
                if user_input.lower() == 'health':
                    health = self.plugin_manager.health_check()
                    print("\n插件健康状态:")
                    for name, status in health.items():
                        print(f"  {name}: {status.get('status', 'unknown')}")
                    continue
                
                # 执行任务
                self.execute(user_input)
                
            except KeyboardInterrupt:
                print("\n再见！🦫")
                break


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Universal Skill v2.0")
    parser.add_argument("task", nargs="?", help="要执行的任务")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("-p", "--plugins", action="store_true", help="列出插件")
    parser.add_argument("-s", "--skills", action="store_true", help="列出技能")
    parser.add_argument("--install", help="安装技能")
    parser.add_argument("--source", help="指定来源")
    
    args = parser.parse_args()
    
    us = UniversalSkillV2()
    
    if args.plugins:
        us.list_plugins()
    elif args.skills:
        us.list_skills()
    elif args.install:
        us.install_skill(args.install, args.source)
    elif args.interactive or not args.task:
        us.interactive_mode()
    else:
        result = us.execute(args.task)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()