#!/bin/bash
# Flask后端启动脚本

echo "🚀 启动PPT转视频工具 Flask后端..."

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "📦 激活虚拟环境..."
    source venv/bin/activate
fi

# 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=1

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 启动Flask应用
echo "🌟 启动Flask服务器..."
python app.py
