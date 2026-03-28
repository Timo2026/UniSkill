# Universal Skill V2 部署记录

**部署时间**: 2026-03-27 19:27
**版本**: V2.0.0

## 文件结构

```
universal-skill/
├── core_v2/                    # V2核心模块
│   ├── socratic_engine.py
│   ├── five_w2h_filter.py
│   ├── convergence_checker.py
│   ├── x_styler.py
│   ├── local_vector_retriever.py
│   └── universal_skill_v2.py
├── simple_execute_v2.py        # V2入口 ⭐
├── run_v2.py                   # 启动脚本（带回退）
├── simple_execute.py           # V1（保留）
└── simple_execute_v1_backup.py # V1备份
```

## 使用方式

```python
# 方式1: 直接使用V2
from simple_execute_v2 import SimpleUniversalSkillV2
skill = SimpleUniversalSkillV2()
result = skill.execute("你的任务")

# 方式2: 使用启动脚本（自动回退）
from run_v2 import get_skill
skill = get_skill()
result = skill.execute("你的任务")
```

## 新功能

1. 苏格拉底探明 - 先问后做
2. 收敛系数 - 避免错误路径
3. 本地向量检索 - 减少云端依赖
4. 模型记录 - 100%记录

## 回退方式

```python
# 回退V1
from simple_execute import SimpleUniversalSkill
skill = SimpleUniversalSkill()
```
