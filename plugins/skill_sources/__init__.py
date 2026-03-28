# 技能源插件
from .local_source import LocalSource
from .clawhub_source import ClawHubSource
from .github_source import GitHubSource
from .cnc_executor_source import CNCExecutorSource

__all__ = ["LocalSource", "ClawHubSource", "GitHubSource", "CNCExecutorSource"]