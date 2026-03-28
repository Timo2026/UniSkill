# 万能 Skill V2.2 发布教程

## 一、发布前准备

### 1. 检查文件清单

必需文件：
- SKILL.md（技能描述）
- README.md（用户文档）
- core_v2/state_machine.py（状态机）
- core_v2/x_styler_v2.py（渲染器）
- core_v2/templates/*.html（模板文件）

### 2. 清理临时文件

```bash
cd ~/.openclaw/workspace/skills/universal-skill
rm -rf core_v2/__pycache__
rm -rf core_v2/demo_output
rm -rf __pycache__
```

## 二、ClawHub 登录

### 安装CLI

```bash
npm i -g clawhub
```

### 登录认证

```bash
# 浏览器登录（推荐）
clawhub login

# 或直接输入token
clawhub login --token YOUR_TOKEN

# 验证登录状态
clawhub whoami
```

## 三、发布命令

### 基础发布

```bash
cd ~/.openclaw/workspace/skills

clawhub publish ./universal-skill \
  --slug universal-skill \
  --name "Universal Skill V2 - 内圣外王" \
  --version 2.2.0 \
  --changelog "Jinja2模板引擎+状态机联动+思考指纹+资产看板" \
  --tags "latest,stable"
```

### 参数说明

- slug: 技能唯一标识（如universal-skill）
- name: 显示名称
- version: 版本号（如2.2.0）
- changelog: 更新日志
- tags: 标签（逗号分隔，如latest,stable）

## 四、常见问题

### Q1: 发布失败提示需要登录

解决：执行 clawhub login，然后 clawhub whoami 验证

### Q2: 文件过大

解决：移除大文件（向量索引、缓存等）
```bash
rm -f core_v2/data/vector_index.faiss
rm -f data/*.faiss
```

### Q3: 版本号冲突

解决：查看当前版本 clawhub inspect universal-skill，使用新版本号

### Q4: 移除敏感数据

检查并移除敏感信息：
```bash
grep -r "token\|password\|secret" . --include="*.py" --include="*.json"
rm -f config/api_keys.json
```

## 五、一键发布脚本

项目目录下已有 publish.sh，执行：

```bash
cd ~/.openclaw/workspace/skills/universal-skill
bash publish.sh
```

脚本会自动：
1. 检查登录状态
2. 清理临时文件
3. 检查必需文件
4. 显示发布参数
5. 等待确认后发布

## 六、发布清单检查

- SKILL.md 已更新：完成
- README.md 已创建：完成
- __pycache__ 已清理：待执行
- ClawHub 已登录：待执行
- 版本号：2.2.0
- 更新日志：已准备

---

作者: OpenClaw Team
日期: 2026-03-28