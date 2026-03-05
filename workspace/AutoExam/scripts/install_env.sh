#!/bin/bash
# AutoExam 环境安装脚本

set -e

echo "=========================================="
echo "  AutoExam 环境安装脚本"
echo "  版本: 1.0.0"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "项目根目录: $PROJECT_ROOT"
echo ""

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "❌ Conda 未安装，请先安装Anaconda或Miniconda"
    echo "   下载地址: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ Conda 已安装"
echo ""

# 创建conda环境
echo "📦 创建Conda环境 'autoexam'..."
if conda env list | grep -q "autoexam"; then
    echo "⚠️  环境 'autoexam' 已存在，是否删除并重新创建? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        conda env remove -n autoexam -y
        conda env create -f "$PROJECT_ROOT/environment.yml"
    else
        echo "使用现有环境"
    fi
else
    conda env create -f "$PROJECT_ROOT/environment.yml"
fi

echo ""
echo "✅ Conda环境创建完成"
echo ""

# 激活环境并安装pip依赖
echo "📥 安装Python依赖..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate autoexam

pip install -r "$PROJECT_ROOT/requirements.txt"

echo ""
echo "✅ Python依赖安装完成"
echo ""

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p "$PROJECT_ROOT/data"/{scenarios,results,reports,openscenario,logs}

echo "✅ 数据目录创建完成"
echo ""

# 检查CARLA（可选）
echo "🔍 检查CARLA..."
if [ -d "$CARLA_ROOT" ]; then
    echo "✅ CARLA 已配置: $CARLA_ROOT"
else
    echo "⚠️  CARLA 未配置，如需使用CARLA仿真，请设置 CARLA_ROOT 环境变量"
fi
echo ""

# 完成
echo "=========================================="
echo "  🎉 安装完成!"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  1. 激活环境: conda activate autoexam"
echo "  2. 启动Web界面: python src/autoexam/ui/app.py"
echo "  3. 访问: http://localhost:5000"
echo ""
echo "更多文档:"
echo "  - 快速开始: docs/QUICK_START.md"
echo "  - 用户指南: docs/USER_GUIDE.md"
echo "  - API文档: docs/API_DOCUMENTATION.md"
echo ""
