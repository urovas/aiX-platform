#!/bin/bash
# AutoExam启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查conda环境
ENV_NAME="autoexam"

if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "错误: conda环境 ${ENV_NAME} 不存在"
    echo "请先运行: ./install_env.sh"
    exit 1
fi

echo "======================================"
echo "AutoExam 自动驾驶高危场景智能生成与测试系统"
echo "======================================"
echo ""

# 激活conda环境
echo "激活conda环境: ${ENV_NAME}"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate $ENV_NAME

echo "Python版本: $(python --version)"
echo ""

# 加载配置
CARLA_PATH=$(grep -A 5 '"carla"' config.json | grep '"carla_path"' | awk -F'"' '{print $4}')
CARLA_HOST=$(grep -A 5 '"carla"' config.json | grep '"host"' | awk -F'"' '{print $4}')
CARLA_PORT=$(grep -A 5 '"carla"' config.json | grep '"port"' | awk -F': ' '{print $2}' | tr -d ',')

# 检查CARLA路径
if [ -z "$CARLA_PATH" ]; then
    echo "错误: CARLA路径未配置"
    echo "请在config.json中配置carla_path"
    exit 1
fi

if [ ! -d "$CARLA_PATH" ]; then
    echo "错误: CARLA目录不存在: $CARLA_PATH"
    exit 1
fi

echo "CARLA路径: $CARLA_PATH"
echo ""

# 创建必要的目录
mkdir -p scenarios
mkdir -p results
mkdir -p logs
mkdir -p videos

# 启动CARLA服务器
echo "正在启动CARLA服务器..."
CARLA_SCRIPT="$CARLA_PATH/CarlaUE4.sh"

if [ ! -f "$CARLA_SCRIPT" ]; then
    echo "错误: CARLA启动脚本不存在: $CARLA_SCRIPT"
    exit 1
fi

# 在后台启动CARLA
"$CARLA_SCRIPT" > logs/carla.log 2>&1 &
CARLA_PID=$!
echo "CARLA服务器已启动 (PID: $CARLA_PID)"
echo "等待CARLA服务器初始化..."

# 等待CARLA服务器启动
sleep 15

# 检查CARLA是否成功启动
if ! kill -0 $CARLA_PID 2>/dev/null; then
    echo "错误: CARLA服务器启动失败"
    echo "请查看日志: logs/carla.log"
    exit 1
fi

echo "CARLA服务器启动成功"
echo ""

# 启动Web界面
echo "正在启动AutoExam Web界面..."
python ui/app.py > logs/web.log 2>&1 &
WEB_PID=$!
echo "Web界面已启动 (PID: $WEB_PID)"
echo ""

echo "======================================"
echo "系统启动完成！"
echo "======================================"
echo ""
echo "访问地址: http://localhost:5000"
echo ""
echo "服务进程:"
echo "  CARLA服务器: PID $CARLA_PID"
echo "  Web界面: PID $WEB_PID"
echo ""
echo "日志文件:"
echo "  CARLA日志: logs/carla.log"
echo "  Web日志: logs/web.log"
echo ""
echo "停止系统: ./stop.sh"
echo "======================================"

# 保存PID以便后续停止
echo "$CARLA_PID" > .carla.pid
echo "$WEB_PID" > .web.pid

# 保持脚本运行
wait
