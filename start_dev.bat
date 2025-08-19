@echo off
REM Windows开发环境启动脚本

echo 🚀 启动PPT转视频开发环境

REM 设置环境变量
set VITE_API_BASE_URL=http://localhost:8502
set VITE_API_HOST=localhost
set VITE_API_PORT=8502

echo 📡 API配置: %VITE_API_BASE_URL%

REM 检查后端是否已经在运行
curl -f http://localhost:8502/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 检测到后端API服务已在运行
) else (
    echo 🔧 启动后端API服务器...
    start "后端API" cmd /k "cd /d "%~dp0" && D:/My-LocalGitFile/makemoneyproject/01.edu-course-aotu/PPTist/ppt_to_video/venv/Scripts/python.exe -m uvicorn api_full_workflow:app --host 0.0.0.0 --port 8502 --reload"
    
    REM 等待后端启动
    echo ⏳ 等待后端服务启动...
    timeout /t 5 /nobreak > nul
)

REM 启动前端开发服务器
echo 🎨 启动前端开发服务器...
cd PPTist
npm run dev
