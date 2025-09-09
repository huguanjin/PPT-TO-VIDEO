#!/bin/bash

# PPT转视频工具 - 生产环境权限修复脚本
echo "=== PPT转视频工具 - 生产环境权限修复 ==="

# 获取项目根目录
PROJECT_ROOT="/www/wwwroot/ppt-video"
BACKEND_ROOT="$PROJECT_ROOT/backend"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p "$PROJECT_ROOT/output/task_status"
mkdir -p "$PROJECT_ROOT/output/projects"
mkdir -p "$PROJECT_ROOT/uploads"
mkdir -p "$PROJECT_ROOT/temp"
mkdir -p "$BACKEND_ROOT/output/audio"
mkdir -p "$BACKEND_ROOT/output/video_clips"
mkdir -p "$BACKEND_ROOT/output/subtitles"
mkdir -p "$BACKEND_ROOT/output/final_videos"
mkdir -p "$BACKEND_ROOT/output/scripts"
mkdir -p "$BACKEND_ROOT/logs"

# 设置权限
echo "设置目录权限..."
chown -R www:www "$PROJECT_ROOT"
chmod -R 755 "$PROJECT_ROOT"
chmod -R 777 "$PROJECT_ROOT/output"
chmod -R 777 "$PROJECT_ROOT/uploads"
chmod -R 777 "$PROJECT_ROOT/temp"
chmod -R 777 "$BACKEND_ROOT/output"
chmod -R 777 "$BACKEND_ROOT/logs"

# 创建必要的配置文件
echo "创建任务状态文件..."
cat > "$PROJECT_ROOT/output/task_status/task_statuses.json" << 'EOF'
{}
EOF

# 设置文件权限
chmod 666 "$PROJECT_ROOT/output/task_status/task_statuses.json"
chown www:www "$PROJECT_ROOT/output/task_status/task_statuses.json"

# 同步flask_backend到backend目录（如果存在）
if [ -d "$PROJECT_ROOT/flask_backend" ]; then
    echo "同步flask_backend到backend目录..."
    rsync -av --delete "$PROJECT_ROOT/flask_backend/" "$BACKEND_ROOT/"
    chown -R www:www "$BACKEND_ROOT"
fi

echo "权限修复完成！"
echo "项目目录: $PROJECT_ROOT"
echo "后端目录: $BACKEND_ROOT"
echo "请确保Web服务器用户为 www:www"
