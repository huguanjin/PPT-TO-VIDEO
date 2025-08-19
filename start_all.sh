#!/bin/bash

echo "========================================"
echo "   PPT转视频工具 - 统一启动器 (Linux/Mac)"
echo "========================================"
echo

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3环境，请先安装Python3"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到Node.js环境，请先安装Node.js"
    exit 1
fi

echo "[信息] 环境检查通过"
echo

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[警告] 未找到Python虚拟环境，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "[信息] 激活Python虚拟环境"
    source venv/bin/activate
fi

# 检查Node依赖
cd PPTist
if [ ! -d "node_modules" ]; then
    echo "[警告] 未找到Node.js依赖，正在安装..."
    npm install
fi
cd ..

echo
echo "[信息] 启动服务..."
echo

# 创建日志目录
mkdir -p logs

# 启动完整工作流API (后台)
echo "[1/2] 启动工作流API服务器 (端口8502)..."
python api_full_workflow.py > logs/api_workflow.log 2>&1 &
API_PID=$!

# 等待API启动
sleep 3

# 启动Vue前端
echo "[2/2] 启动Vue前端 (端口3000)..."
cd PPTist
npm run dev &
VUE_PID=$!
cd ..

echo
echo "========================================"
echo "    所有服务启动完成！"
echo "========================================"
echo
echo "服务地址:"
echo "  Vue前端:      http://localhost:3000"
echo "  工作流API:    http://localhost:8502"
echo
echo "使用说明:"
echo "  1. 在浏览器打开 http://localhost:3000"
echo "  2. 编辑PPT内容"
echo "  3. 点击顶部的'配置'按钮设置视频参数"
echo "  4. 点击'视频导出'按钮开始生成视频"
echo
echo "进程ID:"
echo "  工作流API: $API_PID"
echo "  Vue前端: $VUE_PID"
echo
echo "按 Ctrl+C 退出"

# 等待用户中断
trap "echo '正在关闭服务...'; kill $API_PID $VUE_PID 2>/dev/null; echo '服务已关闭'; exit 0" INT
wait
