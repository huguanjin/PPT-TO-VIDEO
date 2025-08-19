@echo off
title PPT转视频工具启动器
echo.
echo ========================================
echo    PPT转视频工具 - 统一启动器
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python环境，请先安装Python
    pause
    exit /b 1
)

REM 检查Node.js环境
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js环境，请先安装Node.js
    pause
    exit /b 1
)

echo [信息] 环境检查通过
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [警告] 未找到Python虚拟环境，正在创建...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo [信息] 激活Python虚拟环境
    call venv\Scripts\activate.bat
)

REM 检查Node依赖
cd PPTist
if not exist "node_modules" (
    echo [警告] 未找到Node.js依赖，正在安装...
    npm install
)
cd ..

echo.
echo [信息] 启动服务...
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

REM 启动完整工作流API (后台)
echo [1/2] 启动工作流API服务器 (端口8502)...
start "工作流API" cmd /k "title 工作流API服务 && venv\Scripts\python.exe api_full_workflow.py > logs\api_workflow.log 2>&1"

REM 等待API启动
timeout /t 3 /nobreak >nul

REM 启动Vue前端
echo [2/2] 启动Vue前端 (端口3000)...
cd PPTist
start "Vue前端" cmd /k "title Vue前端服务 && npm run dev"
cd ..

echo.
echo ========================================
echo    所有服务启动完成！
echo ========================================
echo.
echo 服务地址:
echo   Vue前端:      http://localhost:3000
echo   工作流API:    http://localhost:8502
echo.
echo 使用说明:
echo   1. 在浏览器打开 http://localhost:3000
echo   2. 编辑PPT内容
echo   3. 点击顶部的"配置"按钮设置视频参数
echo   4. 点击"视频导出"按钮开始生成视频
echo.
echo 按任意键退出启动器...
pause >nul

REM 询问是否关闭服务
echo.
set /p close_services="是否关闭所有服务? (y/N): "
if /i "%close_services%"=="y" (
    echo 正在关闭服务...
    taskkill /f /im python.exe >nul 2>&1
    taskkill /f /im node.exe >nul 2>&1
    echo 服务已关闭
)
