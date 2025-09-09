#!/bin/bash
# VideoLingo技术融合 - 第三阶段系统启动脚本 (Linux/macOS)

echo "===================================================="
echo "VideoLingo技术融合 - 第三阶段系统集成"
echo "===================================================="
echo

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "[信息] 激活虚拟环境..."
    source venv/bin/activate
else
    echo "[警告] 未找到虚拟环境，使用系统Python"
fi

# 检查依赖
echo "[信息] 检查Python依赖..."
python3 -c "import flask, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[信息] 安装必要依赖..."
    pip3 install flask flask-cors requests
fi

# 设置环境变量
export VIDEOLINGO_HOST=${VIDEOLINGO_HOST:-0.0.0.0}
export VIDEOLINGO_PORT=${VIDEOLINGO_PORT:-8004}
export VIDEOLINGO_DEBUG=${VIDEOLINGO_DEBUG:-true}

echo "[信息] 配置信息:"
echo "  - 主机地址: $VIDEOLINGO_HOST"
echo "  - 端口号: $VIDEOLINGO_PORT"
echo "  - 调试模式: $VIDEOLINGO_DEBUG"
echo

# 启动服务
echo "[信息] 启动VideoLingo技术融合服务..."
echo "[访问] http://localhost:$VIDEOLINGO_PORT"
echo "[测试] http://localhost:$VIDEOLINGO_PORT/test/api"
echo
echo "按 Ctrl+C 停止服务"
echo "===================================================="
echo

python3 videolingo_integration_app.py
