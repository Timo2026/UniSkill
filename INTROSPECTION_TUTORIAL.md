# 🦫 海狸绝密公开协议 - 完整教程

## 概述

这套协议让 OpenClaw 具备**源代码级的内省能力**。它不靠大模型"联想"回答，而是通过 Python 直接读取物理文件、解析 AST 结构、调取真实数据，然后把冷冰冰的代码翻译成有温度的"战友式人话"。

---

## §1 一键触发

**口令列表**：
- `海狸，交底`
- `交底`
- `系统真相`
- `绝密公开`

**示例**：
```
用户: 海狸，交底。我想知道你的路由器怎么工作的。

海狸: 大帅，既然你要看家底，我把内裤都翻出来了...
```

---

## §2 核心组件

| 文件 | 功能 | 位置 |
|------|------|------|
| `sys_introspection.py` | 物理扫描器 + AST解析 | `core_v2/` |
| `introspection_trigger.py` | 口令检测入口 | `core_v2/` |
| `introspection_skill.json` | 技能配置 | `config/` |
| `SKILL.md` | 技能入口文档 | `skills/universal-skill/` |

---

## §3 三层映射架构

### 第一层：物理扫描器
```python
def get_real_code(self, file_name):
    file_path = os.path.join(self.root_dir, file_name)
    with open(file_path, "r") as f:
        return f.readlines()[:50]  # 2C 2G 保护截断
```

### 第二层：逻辑解码器
```python
def scan_capabilities(self):
    tree = ast.parse(code)
    functions = [node.name for node in ast.walk(tree) 
                 if isinstance(node, ast.FunctionDef)]
```

### 第三层：海狸人格化翻译
```
禁词：可能、大约、系统错误
必含：源代码片段、物理路径、硬件限制
```

---

## §4 输出内容

交底报告包含以下板块：

### 1. 硬件真相
```
内存: 正常 (0.91GB / 1.83GB)
CPU: 1.0%
环境: 2C 2G 老爷车
```

### 2. 路由决策逻辑
```python
if convergence_score < 0.7:
    return 'INTERNAL_PROMPT_REFINER'  # 收敛熔断
```

### 3. 功能模块清单
```
model_router_v2.py: 18个函数, 1个类
socratic_engine.py: 15个函数, 4个类
```

### 4. 翻车记录
```
过去24小时: 3次失败, 2个低质量案例
```

---

## §5 部署步骤

```bash
# 1. 确认依赖
pip3.8 install psutil

# 2. 测试运行
python3.8 core_v2/sys_introspection.py

# 3. 触发口令
用户输入: "海狸，交底"

# 4. 查看报告
cat data/introspection_report.md
```

---

## §6 人格设定详解

```
你现在是海狸——大帅的硬核技术战友。

交底原则：
1. 代码必须真实（物理扫描）
2. 数据不许美化（原样输出）
3. 翻车不留面子（暴露失败）
4. 限制直接拆穿（2C 2G短板）

禁止词：可能、大约、系统错误、请联系管理员
必含元素：源代码片段、物理文件路径、硬件限制提醒
```

---

## §7 示例输出

> **"大帅，既然你要看家底，我把内裤都翻出来了。咱这套系统的命门和本事都在这儿了："**
>
> ### 内存状态：正常 (50%)
> 咱们这台 2C 2G 老爷车，内存刚好够跑。要是客户需求太复杂，我就得把任务推给云端API。
>
> ### 路由熔断逻辑：
> ```python
> if convergence_score < 0.7:
>     return "INTERNAL_PROMPT_REFINER"
> ```
> **海狸解读**：客户需求云里雾里，收敛度不到 70%，直接打回苏格拉底引擎，绝不浪费那 7600 次云端额度。
>
> ### 翻车统计：
> 过去 24 小时，我翻了 3 次车，低质量案例 2 个。
>
> **"大帅，这代码没掺水。你想拆哪块儿，直接点名，海狸接着给你播报。"**

---

## §8 技术亮点

| 特性 | 评分 | 说明 |
|------|------|------|
| 真实性 | ⭐⭐⭐⭐⭐ | AST解析源码，不含幻觉 |
| 无遗漏 | ⭐⭐⭐⭐⭐ | os.listdir物理扫描 |
| 拟人性 | ⭐⭐⭐⭐ | 战友式语气，不打太极 |
| 性能安全 | ⭐⭐⭐⭐⭐ | 50行截断保护2C 2G |

---

## §9 扩展建议

### 1. 添加更多内省目标
```json
"introspection_targets": [
  "core_v2/*.py",
  "config/*.json",
  "data/*.jsonl",
  "logs/*.log"
]
```

### 2. 定时自动交底
```cron
0 8 * * * python3.8 sys_introspection.py --save
```

### 3. 失败记录深度分析
```python
def analyze_failures(self, hours=72):
    # 分析3天内所有翻车
```

---

## §10 常见问题

**Q: 为什么不用模型生成报告？**
A: 模型会产生幻觉，物理扫描才是真数据。

**Q: 2C 2G 能跑吗？**
A: 代码做了50行截断保护，不会内存溢出。

**Q: 翻车记录会不会太丢脸？**
A: 绝密公开协议的核心就是不留面子，真实暴露问题才能改进。

---

🦫 海狸 | 靠得住、能干事、在状态
**"大帅，交底这事儿，咱们从不含糊。"**