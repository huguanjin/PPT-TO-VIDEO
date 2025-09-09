#!/bin/bash

# PPT转视频工具 - 生产环境代码更新脚本
echo "=== PPT转视频工具 - 生产环境代码更新 ==="

# 设置变量
PROJECT_ROOT="/www/wwwroot/ppt-video"
BACKEND_ROOT="$PROJECT_ROOT/backend"
FRONTEND_ROOT="$PROJECT_ROOT/frontend"

# 备份当前版本
echo "备份当前版本..."
BACKUP_DIR="/www/backup/ppt-video-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$BACKEND_ROOT" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$FRONTEND_ROOT" "$BACKUP_DIR/" 2>/dev/null || true

# 确保在正确目录
cd "$PROJECT_ROOT"

# 更新代码 - 从远程拉取最新的flask_backend代码到backend目录
echo "更新后端代码..."
if [ -d ".git" ]; then
    git pull origin main
    
    # 如果存在flask_backend目录，同步到backend目录
    if [ -d "flask_backend" ]; then
        echo "同步flask_backend到backend目录..."
        rsync -av --delete flask_backend/ backend/
    fi
else
    echo "错误：未找到git仓库，请手动更新代码"
fi

# 更新前端
echo "更新前端..."
if [ -d "$FRONTEND_ROOT" ]; then
    cd "$FRONTEND_ROOT"
    
    # 如果有package.json，重新安装依赖并构建
    if [ -f "package.json" ]; then
        echo "安装前端依赖..."
        npm install
        
        echo "构建前端..."
        npm run build
    fi
fi

# 重启服务
echo "重启Flask服务..."
cd "$BACKEND_ROOT"

# 停止现有服务
pkill -f "python.*app.py" || true
sleep 2

# 启动Flask服务
nohup python app.py > /www/logs/flask.log 2>&1 &

echo "代码更新完成！"
echo "Flask日志位置: /www/logs/flask.log"
echo "备份位置: $BACKUP_DIR"
echo "请运行以下命令检查服务状态："
echo "  tail -f /www/logs/flask.log"
echo "  ps aux | grep python.*app.py"
