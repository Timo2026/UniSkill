"""
OpenClaw Universal Skill V2.2 - "内圣外王"版
核心原则：禁止在需求不明时执行任何真正的工作

版本: V2.2.0 (Sea-Glass模板引擎)
升级：
- Jinja2模板引擎（告别字符串拼接）
- 状态机联动（收敛度实时反映）
- 思考指纹（Socratic Thinking Trace）
- 资产看板（10855条数据可视化）
"""

# 新V2核心组件（安全导入）
try:
    from .state_machine import StateMachine, ExecutionState, StateContext
except ImportError:
    pass

try:
    from .x_styler_v2 import XStylerV2
except ImportError:
    pass

# V2原有组件（安全导入）
try:
    from .socratic_engine import SocraticEngine, AnchorData, ConvergenceLevel
except ImportError:
    pass

try:
    from .five_w2h_filter import FiveW2HFilter, W2HDimension
except ImportError:
    pass

try:
    from .convergence_checker import ConvergenceChecker, ConvergenceAction, ConvergenceResult
except ImportError:
    pass

try:
    from .x_styler import XStylerRenderer
except ImportError:
    pass

try:
    from .local_vector_retriever import LocalVectorRetriever, get_retriever
except ImportError:
    pass

try:
    from .user_preference_reader import UserPreferenceReader, get_user_reader
except ImportError:
    pass

try:
    from .humanized_output import HumanizedOutput
except ImportError:
    pass

try:
    from .universal_skill_v2 import UniversalSkillV2
except ImportError:
    pass

# V1借鉴模块（安全导入）
try:
    from .learning_loop import LearningLoop, get_learning_loop
except ImportError:
    pass

try:
    from .smart_fallback import SmartFallback, get_fallback
except ImportError:
    pass

__all__ = [
    # 主执行器
    'UniversalSkillV2',
    
    # V2核心组件
    'SocraticEngine',
    'FiveW2HFilter', 
    'ConvergenceChecker',
    'XStylerRenderer',
    'LocalVectorRetriever',
    'UserPreferenceReader',
    'HumanizedOutput',
    
    # V1借鉴模块
    'LearningLoop',
    'SmartFallback',
    'QualityChecker',
    'Orchestrator',
    'SkillFinder',
    
    # 数据类
    'AnchorData',
    'ConvergenceLevel',
    'ConvergenceAction',
    'ConvergenceResult',
    'W2HDimension',
    'Step',
    'PipelineTemplates',
    
    # 工具函数
    'get_retriever',
    'get_user_reader',
    'get_learning_loop',
    'get_fallback',
    'get_quality_checker',
    'get_skill_finder'
]

__version__ = "2.2.0"
__author__ = "OpenClaw"
