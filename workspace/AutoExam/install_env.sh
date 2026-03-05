#!/bin/bash
# AutoExam环境安装脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "AutoExam 环境安装"
echo "======================================"
echo ""

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "错误: conda未安装"
    echo "请先安装Anaconda或Miniconda"
    exit 1
fi

echo "检测到conda: $(conda --version)"
echo ""

# 检查环境是否已存在
ENV_NAME="autoexam"
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "环境 ${ENV_NAME} 已存在"
    read -p "是否删除并重新创建? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "删除旧环境..."
        conda env remove -n $ENV_NAME -y
    else
        echo "使用现有环境"
        exit 0
    fi
fi

# 创建conda环境
echo "创建conda环境: $ENV_NAME"
conda env create -f environment.yml

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "环境创建成功！"
    echo "======================================"
    echo ""
    echo "激活环境:"
    echo "  conda activate autoexam"
    echo ""
    echo "或者使用source (bash/zsh):"
    echo "  source activate autoexam"
    echo ""
    echo "退出环境:"
    echo "  conda deactivate"
    echo "======================================"
else
    echo ""
    echo "错误: 环境创建失败"
    exit 1
fi
