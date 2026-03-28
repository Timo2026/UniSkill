#!/bin/bash
# 万能 Skill V2.2 一键发布脚本
# 使用: bash publish.sh

set -e

SKILL_DIR="$HOME/.openclaw/workspace/skills/universal-skill"
SLUG="universal-skill"
NAME="Universal Skill V2 - 内圣外王"
VERSION="2.2.0"
CHANGELOG="V2.2重大升级: Jinja2模板引擎+状态机联动+思考指纹+资产看板"
TAGS="latest,stable"

echo "🦫 万能 Skill V2.2 发布脚本"
echo "============================"

# 1. 检查登录状态
echo ""
echo "§ 1. 检查登录状态..."
if ! clawhub whoami 2>/dev/null; then
    echo "⚠️  未登录，请先执行: clawhub login"
    echo "   或直接输入 token: clawhub login --token YOUR_TOKEN"
    exit 1
fi
echo "✅ 登录有效"

# 2. 清理临时文件
echo ""
echo "§ 2. 清理临时文件..."
cd "$SKILL_DIR"
rm -rf core_v2/__pycache__ core_v2/demo_output __pycache__ plugins/__pycache__
rm -f core_v2/*.pyc *.pyc
echo "✅ 清理完成"

# 3. 检查文件
echo ""
echo "§ 3. 检查必需文件..."
files_ok=true
for f in SKILL.md README.md core_v2/state_machine.py core_v2/x_styler_v2.py; do
    if [ -f "$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ✗ $f (缺失)"
        files_ok=false
    fi
done

if [ "$files_ok" = false ]; then
    echo "⚠️  必需文件缺失，请检查"
    exit 1
fi
echo "✅ 文件检查通过"

# 4. 显示统计
echo ""
echo "§ 4. 文件统计..."
file_count=$(find . -type f \( -name "*.py" -o -name "*.html" -o -name "*.md" \) | wc -l)
size=$(du -sh . | cut -f1)
echo "  文件数: $file_count"
echo "  大小: $size"

# 5. 发布确认
echo ""
echo "§ 5. 发布参数:"
echo "  Slug: $SLUG"
echo "  Name: $NAME"
echo "  Version: $VERSION"
echo "  Tags: $TAGS"
echo ""
read -p "确认发布? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "取消发布"
    exit 0
fi

# 6. 执行发布
echo ""
echo "§ 6. 执行发布..."
clawhub publish . \
    --slug "$SLUG" \
    --name "$NAME" \
    --version "$VERSION" \
    --changelog "$CHANGELOG" \
    --tags "$TAGS"

echo ""
echo "✅ 发布完成！"
echo "→ https://clawhub.com/skills/$SLUG"