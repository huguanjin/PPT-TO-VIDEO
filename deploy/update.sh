#!/bin/bash
# PPT转视频工具更新脚本

set -e

echo "🔄 PPT转视频工具更新脚本开始执行..."

# 配置变量
PROJECT_NAME="ppt-video"
PROJECT_DIR="/www/wwwroot/$PROJECT_NAME"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DEPLOY_SOURCE="/tmp/ppt-to-video-deploy"
BACKUP_DIR="/www/backup/ppt-video-$(date +%Y%m%d_%H%M%S)"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root用户执行此脚本"
    exit 1
fi

# 检查项目是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    echo "请先运行安装脚本"
    exit 1
fi

# 检查更新源是否存在
if [ ! -d "$DEPLOY_SOURCE" ]; then
    echo "❌ 更新源不存在: $DEPLOY_SOURCE"
    echo "请先上传并解压新版本到 /tmp/"
    exit 1
fi

echo "💾 备份当前版本..."

# 创建备份目录
mkdir -p /www/backup
cp -r $PROJECT_DIR $BACKUP_DIR

echo "📦 备份完成: $BACKUP_DIR"

echo "🛑 停止服务..."

# 尝试通过不同方式停止服务
# 方式1: 通过宝塔API停止Python项目（需要宝塔API）
# 方式2: 通过进程停止
pkill -f "gunicorn.*flask_backend.app:app" || true

# 方式3: 通过systemd停止（如果存在）
systemctl stop ppt-video 2>/dev/null || true

sleep 3

echo "📄 更新文件..."

# 备份关键配置文件
cp $PROJECT_DIR/config/.env /tmp/.env.backup 2>/dev/null || true

# 更新前端文件
if [ -d "$DEPLOY_SOURCE/frontend" ]; then
    rm -rf $FRONTEND_DIR/dist/*
    cp -r $DEPLOY_SOURCE/frontend/* $FRONTEND_DIR/
    echo "✅ 前端文件更新完成"
fi

# 更新后端文件
if [ -d "$DEPLOY_SOURCE/backend" ]; then
    # 保留关键目录
    mv $BACKEND_DIR/uploads /tmp/uploads.backup
    mv $BACKEND_DIR/output /tmp/output.backup
    mv $BACKEND_DIR/logs /tmp/logs.backup
    mv $BACKEND_DIR/data /tmp/data.backup 2>/dev/null || true
    mv $BACKEND_DIR/venv /tmp/venv.backup
    
    # 更新后端代码
    rm -rf $BACKEND_DIR/*
    cp -r $DEPLOY_SOURCE/backend/* $BACKEND_DIR/
    
    # 恢复关键目录
    mv /tmp/uploads.backup $BACKEND_DIR/uploads
    mv /tmp/output.backup $BACKEND_DIR/output
    mv /tmp/logs.backup $BACKEND_DIR/logs
    mv /tmp/data.backup $BACKEND_DIR/data 2>/dev/null || mkdir -p $BACKEND_DIR/data
    mv /tmp/venv.backup $BACKEND_DIR/venv
    
    echo "✅ 后端文件更新完成"
fi

# 恢复配置文件
if [ -f "/tmp/.env.backup" ]; then
    cp /tmp/.env.backup $PROJECT_DIR/config/.env
    rm /tmp/.env.backup
fi

echo "🐍 更新Python依赖..."

cd $BACKEND_DIR
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade

echo "🔧 修复权限..."

chown -R www:www $PROJECT_DIR
chmod +x $PROJECT_DIR/health_check.sh

echo "🚀 启动服务..."

# 尝试启动服务
systemctl start ppt-video 2>/dev/null || true

# 等待服务启动
sleep 5

echo "🔍 检查服务状态..."

# 运行健康检查
if [ -f "$PROJECT_DIR/health_check.sh" ]; then
    if $PROJECT_DIR/health_check.sh; then
        echo "✅ 服务启动成功"
    else
        echo "❌ 服务启动失败，请检查日志"
        echo "📋 回滚命令: cp -r $BACKUP_DIR/* $PROJECT_DIR/"
        exit 1
    fi
else
    echo "⚠️  健康检查脚本不存在，请手动验证服务状态"
fi

echo "📊 更新信息..."

# 更新部署信息
cat >> $PROJECT_DIR/DEPLOYMENT_INFO.md << EOF

## 更新记录
- 更新时间: $(date '+%Y-%m-%d %H:%M:%S')
- 备份位置: $BACKUP_DIR
- 更新内容: 从 $DEPLOY_SOURCE 更新

EOF

echo ""
echo "🎉 更新完成！"
echo ""
echo "📊 更新信息:"
echo "- 备份位置: $BACKUP_DIR"
echo "- 服务状态: 请通过宝塔面板或健康检查验证"
echo "- 访问地址: https://your-domain.com"
echo ""
echo "📋 如果出现问题，可以回滚:"
echo "sudo systemctl stop ppt-video"
echo "sudo rm -rf $PROJECT_DIR/*"
echo "sudo cp -r $BACKUP_DIR/* $PROJECT_DIR/"
echo "sudo systemctl start ppt-video"
echo ""
