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
cp -r "$BACKEND_ROOT" "$BACKUP_DIR/"
cp -r "$FRONTEND_ROOT" "$BACKUP_DIR/"

# 更新Flask后端
echo "更新Flask后端..."
cd "$BACKEND_ROOT"
git pull origin main

# 更新前端
echo "更新前端..."
cd "$FRONTEND_ROOT"

# 如果有package.json，重新安装依赖并构建
if [ -f "package.json" ]; then
    echo "安装前端依赖..."
    npm install
    
    echo "构建前端..."
    npm run build
fi

# 重启服务
echo "重启Flask服务..."
pkill -f "python.*app.py"
sleep 2

# 启动Flask服务
cd "$BACKEND_ROOT"
nohup python app.py > /www/logs/flask.log 2>&1 &

echo "代码更新完成！"
echo "Flask日志位置: /www/logs/flask.log"
echo "备份位置: $BACKUP_DIR"
