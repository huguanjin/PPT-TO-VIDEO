@echo off
REM Flask后端启动脚本 (Windows)

echo 🚀 启动PPT转视频工具 Flask后端...

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    echo 📦 激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 设置环境变量
set FLASK_ENV=development
set FLASK_DEBUG=1

REM 安装依赖
echo 📥 安装依赖包...
pip install -r requirements.txt

REM 启动Flask应用
echo 🌟 启动Flask服务器...
python app.py

pause
