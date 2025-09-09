@echo off
REM VideoLingo技术融合 - 第三阶段系统启动脚本 (Windows)

echo ====================================================
echo VideoLingo技术融合 - 第三阶段系统集成
echo ====================================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [信息] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，使用系统Python
)

REM 检查依赖
echo [信息] 检查Python依赖...
python -c "import flask, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 安装必要依赖...
    pip install flask flask-cors requests
)

REM 设置环境变量
set VIDEOLINGO_HOST=0.0.0.0
set VIDEOLINGO_PORT=8004
set VIDEOLINGO_DEBUG=true

echo [信息] 配置信息:
echo   - 主机地址: %VIDEOLINGO_HOST%
echo   - 端口号: %VIDEOLINGO_PORT%
echo   - 调试模式: %VIDEOLINGO_DEBUG%
echo.

REM 启动服务
echo [信息] 启动VideoLingo技术融合服务...
echo [访问] http://localhost:%VIDEOLINGO_PORT%
echo [测试] http://localhost:%VIDEOLINGO_PORT%/test/api
echo.
echo 按 Ctrl+C 停止服务
echo ====================================================
echo.

python videolingo_integration_app.py

pause
