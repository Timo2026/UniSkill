#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件管理器 - Plugin Manager
管理所有插件的加载、启用、禁用和调度
"""

import json
import importlib
import sys
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# 导入基类
from plugins.base import BasePlugin, SkillSourcePlugin, OrchestratorPlugin, QualityCheckerPlugin


class PluginState(Enum):
    """插件状态"""
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginInfo:
    """插件信息"""
    plugin: BasePlugin
    state: PluginState
    priority: int
    error_message: str = ""


class PluginManager:
    """
    插件管理器
    
    功能：
    1. 加载/卸载插件
    2. 启用/禁用插件
    3. 按优先级调度
    4. 健康检查
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or {}
        
        # 插件存储
        self.plugins: Dict[str, PluginInfo] = {}
        
        # 分类索引
        self.sources: Dict[str, SkillSourcePlugin] = {}
        self.orchestrators: Dict[str, OrchestratorPlugin] = {}
        self.checkers: Dict[str, QualityCheckerPlugin] = {}
        
        # 配置文件
        self.config_file = Path(__file__).parent.parent / "plugins.json"
    
    def load_config(self) -> Dict:
        """加载插件配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """保存插件配置"""
        config = {
            "sources": {},
            "orchestrators": {},
            "checkers": {}
        }
        
        for name, info in self.plugins.items():
            if isinstance(info.plugin, SkillSourcePlugin):
                config["sources"][name] = {
                    "enabled": info.state == PluginState.ENABLED,
                    "priority": info.priority
                }
            elif isinstance(info.plugin, OrchestratorPlugin):
                config["orchestrators"][name] = {
                    "enabled": info.state == PluginState.ENABLED,
                    "priority": info.priority
                }
            elif isinstance(info.plugin, QualityCheckerPlugin):
                config["checkers"][name] = {
                    "enabled": info.state == PluginState.ENABLED,
                    "priority": info.priority
                }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def register(self, plugin: BasePlugin, priority: int = 0) -> bool:
        """
        注册插件
        
        Args:
            plugin: 插件实例
            priority: 优先级（数字越小越优先）
            
        Returns:
            是否注册成功
        """
        name = plugin.name
        
        if name in self.plugins:
            print(f"[PluginManager] 插件已存在: {name}")
            return False
        
        # 初始化插件
        try:
            if not plugin.initialize():
                print(f"[PluginManager] 插件初始化失败: {name}")
                return False
        except Exception as e:
            print(f"[PluginManager] 插件初始化异常: {name} - {e}")
            return False
        
        # 存储
        self.plugins[name] = PluginInfo(
            plugin=plugin,
            state=PluginState.ENABLED,
            priority=priority
        )
        
        # 分类索引
        if isinstance(plugin, SkillSourcePlugin):
            self.sources[name] = plugin
        elif isinstance(plugin, OrchestratorPlugin):
            self.orchestrators[name] = plugin
        elif isinstance(plugin, QualityCheckerPlugin):
            self.checkers[name] = plugin
        
        print(f"[PluginManager] 注册插件: {name} v{plugin.version} (优先级: {priority})")
        return True
    
    def unregister(self, name: str) -> bool:
        """注销插件"""
        if name not in self.plugins:
            return False
        
        info = self.plugins[name]
        
        # 关闭插件
        try:
            info.plugin.shutdown()
        except:
            pass
        
        # 从索引中移除
        del self.plugins[name]
        
        if name in self.sources:
            del self.sources[name]
        if name in self.orchestrators:
            del self.orchestrators[name]
        if name in self.checkers:
            del self.checkers[name]
        
        print(f"[PluginManager] 注销插件: {name}")
        return True
    
    def enable(self, name: str) -> bool:
        """启用插件"""
        if name not in self.plugins:
            return False
        
        self.plugins[name].state = PluginState.ENABLED
        print(f"[PluginManager] 启用插件: {name}")
        return True
    
    def disable(self, name: str) -> bool:
        """禁用插件"""
        if name not in self.plugins:
            return False
        
        self.plugins[name].state = PluginState.DISABLED
        print(f"[PluginManager] 禁用插件: {name}")
        return True
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取插件"""
        if name in self.plugins:
            return self.plugins[name].plugin
        return None
    
    def get_enabled_sources(self) -> List[SkillSourcePlugin]:
        """获取所有启用的技能源插件"""
        sources = []
        for name, info in sorted(self.plugins.items(), key=lambda x: x[1].priority):
            if info.state == PluginState.ENABLED and name in self.sources:
                sources.append(info.plugin)
        return sources
    
    def get_enabled_orchestrators(self) -> List[OrchestratorPlugin]:
        """获取所有启用的编排插件"""
        return [
            info.plugin for name, info in self.plugins.items()
            if info.state == PluginState.ENABLED and name in self.orchestrators
        ]
    
    def get_enabled_checkers(self) -> List[QualityCheckerPlugin]:
        """获取所有启用的质检插件"""
        return [
            info.plugin for name, info in self.plugins.items()
            if info.state == PluginState.ENABLED and name in self.checkers
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查所有插件"""
        results = {}
        
        for name, info in self.plugins.items():
            try:
                health = info.plugin.health_check()
                results[name] = health
            except Exception as e:
                results[name] = {
                    "name": name,
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        result = []
        
        for name, info in self.plugins.items():
            result.append({
                "name": name,
                "version": info.plugin.version,
                "description": info.plugin.description,
                "state": info.state.value,
                "priority": info.priority
            })
        
        return result
    
    def auto_discover(self):
        """
        自动发现并加载插件
        
        扫描 plugins/ 目录下的所有插件模块
        """
        plugins_dir = Path(__file__).parent
        
        # 发现技能源插件
        sources_dir = plugins_dir / "skill_sources"
        if sources_dir.exists():
            for py_file in sources_dir.glob("*_source.py"):
                try:
                    module_name = py_file.stem
                    module = importlib.import_module(f"plugins.skill_sources.{module_name}")
                    
                    # 查找插件类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, SkillSourcePlugin) and attr != SkillSourcePlugin:
                            # 实例化并注册
                            plugin = attr()
                            priority = self.config.get("sources", {}).get(plugin.name, {}).get("priority", 10)
                            self.register(plugin, priority)
                except Exception as e:
                    print(f"[PluginManager] 加载插件失败: {py_file} - {e}")


# 导出
__all__ = ['PluginManager', 'PluginState', 'PluginInfo']