# 🦫 海狸全量交底报告
**时间**: 2026-03-28 02:17:25

---

## 一、咱们的"脑容量"还剩多少？

| 资源 | 状态 | 数值 |
|------|------|------|
| 内存 | 正常 | 0.98GB / 1.83GB |
| CPU | 正常 | 0.0% |
| 磁盘 | - | 70.8% |

> **海狸实话**：咱们这台 **2C 2G 老爷车**，内存正常。要是客户需求太复杂，我就得把任务推给云端API，不然咱俩一起宕机。

---

## 二、核心路由是怎么"选妃"的？

**真实代码位置**：`core_v2/model_router_v2.py`

### 关键决策逻辑：

#### 收敛熔断
- **触发条件**：收敛度<70%
- **执行动作**：打回苏格拉底
- **真实代码**：
```python
if convergence_score < 0.7:
    return 'INTERNAL_PROMPT_REFINER'
```

#### 硬件降级
- **触发条件**：内存>85%
- **执行动作**：惩罚本地模型
- **真实代码**：
```python
if mem_percent > 0.85:
    return 0.2
```

#### 沙盒闭环
- **触发条件**：沙盒执行失败
- **执行动作**：扣除模型权重
- **真实代码**：
```python
self.sandbox_feedback[model] = 0.5
```

---

## 三、我有哪些功能模块？

### `quality_checker.py`
- 函数数：8
- 类数：1
- 核心函数：get_quality_checker, __init__, check, _check_ai_words, _check_required

### `smart_fallback.py`
- 函数数：6
- 类数：2
- 核心函数：get_fallback, __init__, call_with_fallback, _try_cloud, _try_local

### `x_styler.py`
- 函数数：4
- 类数：1
- 核心函数：render_socratic_card, _render_questions, render_execution_result, render_error_card

### `socratic_engine.py`
- 函数数：15
- 类数：4
- 核心函数：convergence_rate, __init__, start_engine, _infer_intent, _check_industrial_keywords

### `humanized_output.py`
- 函数数：6
- 类数：1
- 核心函数：__init__, clean_ai_words, make_colloquial, format_task_result, format_probe_questions

### `five_w2h_filter.py`
- 函数数：6
- 类数：2
- 核心函数：__init__, check_required_dimensions, generate_probe_questions, _generate_industrial_questions, validate_industrial_params

### `orchestrator.py`
- 函数数：14
- 类数：4
- 核心函数：__init__, add_step, set_context, run, get_progress

### `local_vector_retriever.py`
- 函数数：9
- 类数：2
- 核心函数：get_retriever, __init__, _load_knowledge_base, _chunk_text, get_embedding

### `user_preference_reader.py`
- 函数数：10
- 类数：2
- 核心函数：get_user_reader, __init__, _load_preferences, _parse_resume, _parse_companies

### `convergence_checker.py`
- 函数数：5
- 类数：3
- 核心函数：check, _calculate_convergence, _detect_blur, _get_missing_dimensions, get_convergence_trend

### `universal_skill_v2.py`
- 函数数：11
- 类数：1
- 核心函数：__init__, retriever, _ensure_data_dir, execute, _local_search

### `skill_finder.py`
- 函数数：8
- 类数：1
- 核心函数：get_skill_finder, __init__, _scan_local, find_local, find_clawhub

### `model_router_v2.py`
- 函数数：17
- 类数：1
- 核心函数：__init__, _load_golden_dataset, _load_capabilities, _default_capabilities, _embed

### `sys_introspection.py`
- 函数数：10
- 类数：1
- 核心函数：__init__, get_real_code, scan_capabilities, get_hardware_truth, analyze_failures

### `introspection_trigger.py`
- 函数数：1
- 类数：0
- 核心函数：trigger_introspection

### `learning_loop.py`
- 函数数：9
- 类数：1
- 核心函数：get_learning_loop, __init__, _load_history, _save_history, _analyze_failures

---

## 四、翻车记录（不留面子）

过去24小时内，我翻了0次车，低质量案例0个

---

## 五、数据资产

- 黄金案例库：1 个JSONL
- 配置文件：2 个JSON

---

> **海狸声明**：以上数据均为物理扫描真实结果，不含模型幻觉。大帅，你想拆哪块儿，直接点名。

🦫 海狸 | 靠得住、能干事、在状态
