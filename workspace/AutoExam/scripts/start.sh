#!/bin/bash
# AutoExam 启动脚本

set -e

echo "=========================================="
echo "  AutoExam 启动脚本"
echo "  版本: 1.0.0"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 检查conda环境
if ! conda info --envs | grep -q "autoexam"; then
    echo "❌ Conda环境 'autoexam' 不存在"
    echo "   请先运行: bash scripts/install_env.sh"
    exit 1
fi

# 激活环境
echo "🔄 激活Conda环境..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate autoexam

echo "✅ 环境激活成功"
echo ""

# 检查数据目录
echo "📁 检查数据目录..."
mkdir -p "$PROJECT_ROOT/data"/{scenarios,results,reports,openscenario,logs}
echo "✅ 数据目录就绪"
echo ""

# 启动Web服务
echo "🚀 启动AutoExam Web服务..."
echo "   访问地址: http://localhost:5000"
echo "   按 Ctrl+C 停止服务"
echo ""

python "$PROJECT_ROOT/src/autoexam/ui/app.py"
