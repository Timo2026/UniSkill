# 苏格拉底提问集成方案

## 一、现有资产

### target-locator Skill (苏格拉底提问)

**已有能力**:
- 3轮确认流程
- 5W2H分析
- 字数判断（≤50字直接执行，>50字启动反问）
- 推荐机制

**核心原则**: 禁止假设，强制确认

---

## 二、集成方案

### 方案A: 最小改动 - 置信度触发 ⭐ 推荐

```python
# intent_parser.py 添加置信度

def parse_with_confidence(user_input):
    # 1. 常规解析
    intent = self.parse(user_input)
    
    # 2. 计算置信度
    confidence = self._calculate_confidence(intent)
    
    # 3. 低置信度触发苏格拉底
    if confidence < 0.7:
        from skills.target_locator import TargetLocator
        locator = TargetLocator()
        
        # 启动3轮确认
        clarified_intent = locator.locate(user_input)
        return clarified_intent
    
    return intent

def _calculate_confidence(self, intent):
    """计算置信度"""
    score = 0
    
    # 关键词覆盖率
    if intent.keywords:
        score += len(intent.keywords) * 0.2
    
    # 意图类型明确度
    if intent.intent_type != "unknown":
        score += 0.3
    
    # 领域识别
    if intent.domain != "general":
        score += 0.2
    
    # 子任务明确度
    if intent.subtasks and len(intent.subtasks) > 0:
        score += 0.2
    
    return min(score, 1.0)
```

**优点**: 改动小，快速见效
**工作量**: 半天

---

### 方案B: 深度集成 - 智能路由

```
用户输入
    │
    ▼
┌─────────────────────────────┐
│ 字数判断                     │
│ ≤50字 → 快速执行             │
│ >50字 → 启动苏格拉底         │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 苏格拉底3轮确认              │
│ 第1轮: 目标定位              │
│ 第2轮: 范围确认              │
│ 第3轮: 规范确认              │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 澄清后的意图 → 执行          │
└─────────────────────────────┘
```

**优点**: 完整覆盖
**工作量**: 1-2天

---

## 三、具体代码修改

### Step 1: intent_parser.py 增加置信度

```python
# 在 Intent 类中添加
@dataclass
class Intent:
    raw_input: str
    keywords: List[str]
    intent_type: str
    domain: str
    confidence: float = 0.0  # 新增
    needs_confirmation: bool = False  # 新增
```

### Step 2: orchestrator.py 增加确认分支

```python
def execute(self, intent, inputs):
    # 检查是否需要确认
    if intent.needs_confirmation:
        return self._confirm_and_execute(intent, inputs)
    
    return self._direct_execute(intent, inputs)

def _confirm_and_execute(self, intent, inputs):
    """苏格拉底确认后执行"""
    from skills.target_locator import TargetLocator
    
    locator = TargetLocator()
    
    # 第1轮：目标定位
    target = locator.locate_target(intent.raw_input)
    if not target.confirmed:
        return {
            "status": "need_confirmation",
            "question": target.question,
            "options": target.options
        }
    
    # 第2轮：范围确认
    scope = locator.confirm_scope(target)
    if not scope.confirmed:
        return {
            "status": "need_confirmation",
            "question": scope.question,
            "options": scope.options
        }
    
    # 第3轮：规范确认
    plan = locator.confirm_plan(scope)
    if not plan.confirmed:
        return {
            "status": "need_confirmation",
            "question": plan.question,
            "options": plan.options
        }
    
    # 执行
    return self._direct_execute(plan.refined_intent, inputs)
```

### Step 3: main.py 增加交互处理

```python
def execute(self, user_input):
    result = self.orchestrator.execute(intent, {})
    
    # 处理确认请求
    if result.get("status") == "need_confirmation":
        print(result["question"])
        for opt in result["options"]:
            print(f"  {opt}")
        
        user_choice = input("请选择: ")
        # 继续下一轮...
    
    return result
```

---

## 四、预期效果

| 场景 | 改进前 | 改进后 |
|------|--------|--------|
| "陆家嘴蹦迪局" | 直接执行→失败 | 3轮确认→成功 |
| 复杂任务 | 用户反复调整 | 一次到位 |
| 成功率 | 72% | **85%+** |

---

## 五、实施时间表

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 1 | 置信度计算+触发 | 半天 |
| Phase 2 | 集成target-locator | 半天 |
| Phase 3 | 测试+调优 | 半天 |
| **总计** | - | **1.5天** |

---

## 六、立即可执行

我可以现在就开始实施：

1. 在 intent_parser.py 添加置信度计算
2. 在 orchestrator.py 添加确认分支
3. 测试效果

开始吗？🦫

---

*分析完成*