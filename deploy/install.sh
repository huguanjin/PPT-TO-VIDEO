#!/bin/bash
# PPT转视频工具安装脚本
# 适用于Ubuntu Server 22.04 + 宝塔面板

set -e

echo "🚀 PPT转视频工具部署脚本开始执行..."

# 配置变量
PROJECT_NAME="ppt-video"
PROJECT_DIR="/www/wwwroot/$PROJECT_NAME"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
CONFIG_DIR="$PROJECT_DIR/config"
LOG_DIR="/www/wwwlogs"
DEPLOY_SOURCE="/tmp/ppt-to-video-deploy"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root用户执行此脚本"
    exit 1
fi

# 检查宝塔面板是否安装
if [ ! -f "/www/server/panel/BT-Panel" ]; then
    echo "❌ 未检测到宝塔面板，请先安装宝塔面板"
    exit 1
fi

echo "📦 开始安装系统依赖..."

# 更新系统包
apt update

# 安装系统依赖
apt install -y \
    ffmpeg \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-cjk \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libsndfile1-dev \
    portaudio19-dev \
    python3-venv \
    python3-dev \
    build-essential

echo "📁 创建项目目录结构..."

# 创建项目根目录
mkdir -p $PROJECT_DIR
mkdir -p $BACKEND_DIR
mkdir -p $FRONTEND_DIR
mkdir -p $CONFIG_DIR
mkdir -p $LOG_DIR

# 检查部署源文件是否存在
if [ ! -d "$DEPLOY_SOURCE" ]; then
    echo "❌ 部署源文件不存在: $DEPLOY_SOURCE"
    echo "请先上传并解压部署包到 /tmp/"
    exit 1
fi

echo "📄 复制项目文件..."

# 复制文件
cp -r $DEPLOY_SOURCE/* $PROJECT_DIR/

# 设置目录权限
chown -R www:www $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

echo "🐍 配置Python环境..."

# 进入后端目录
cd $BACKEND_DIR

# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "📂 创建工作目录..."

# 创建必要的工作目录
mkdir -p uploads output temp logs data
chown -R www:www uploads output temp logs data

# 设置日志目录权限
chown -R www:www $LOG_DIR

echo "🔧 配置服务文件..."

# 创建systemd服务文件（作为备用）
cat > /etc/systemd/system/ppt-video.service << EOF
[Unit]
Description=PPT Video Tool Backend
After=network.target

[Service]
Type=forking
User=www
Group=www
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/venv/bin
EnvironmentFile=$CONFIG_DIR/.env
ExecStart=$BACKEND_DIR/venv/bin/gunicorn -c gunicorn.conf.py flask_backend.app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload

echo "🔐 设置安全配置..."

# 生成随机密钥（如果不存在）
if [ ! -f "$CONFIG_DIR/.env" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    cat > $CONFIG_DIR/.env << EOF
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$SECRET_KEY

# 数据库配置
DATABASE_URL=sqlite:///$PROJECT_DIR/data/app.db

# 存储路径
UPLOADS_DIR=$BACKEND_DIR/uploads
OUTPUT_DIR=$BACKEND_DIR/output
TEMP_DIR=$BACKEND_DIR/temp

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/ppt-video-app.log

# 外部服务配置
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural
EOF
fi

echo "🔧 配置定时清理任务..."

# 添加清理脚本到crontab
cat > /etc/cron.daily/ppt-video-cleanup << 'EOF'
#!/bin/bash
# PPT转视频工具清理脚本

PROJECT_DIR="/www/wwwroot/ppt-video"

# 清理30天前的临时文件
find $PROJECT_DIR/backend/temp -type f -mtime +30 -delete 2>/dev/null || true

# 清理7天前的大型输出文件
find $PROJECT_DIR/backend/output -name "*.mp4" -mtime +7 -delete 2>/dev/null || true

# 压缩超过100MB的日志文件
find /www/wwwlogs -name "ppt-video*.log" -size +100M -exec gzip {} \; 2>/dev/null || true

# 清理超过30天的日志压缩包
find /www/wwwlogs -name "ppt-video*.log.gz" -mtime +30 -delete 2>/dev/null || true
EOF

chmod +x /etc/cron.daily/ppt-video-cleanup

echo "📊 创建监控脚本..."

# 创建健康检查脚本
cat > $PROJECT_DIR/health_check.sh << 'EOF'
#!/bin/bash
# PPT转视频工具健康检查脚本

PROJECT_DIR="/www/wwwroot/ppt-video"
BACKEND_DIR="$PROJECT_DIR/backend"

# 检查进程是否运行
if pgrep -f "gunicorn.*flask_backend.app:app" > /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务未运行"
    exit 1
fi

# 检查端口是否监听
if netstat -tlnp | grep :5000 > /dev/null; then
    echo "✅ 端口5000监听正常"
else
    echo "❌ 端口5000未监听"
    exit 1
fi

# 检查关键目录
for dir in uploads output temp logs; do
    if [ -d "$BACKEND_DIR/$dir" ]; then
        echo "✅ 目录 $dir 存在"
    else
        echo "❌ 目录 $dir 不存在"
        exit 1
    fi
done

# 检查磁盘空间
DISK_USAGE=$(df $PROJECT_DIR | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "⚠️  磁盘使用率过高: ${DISK_USAGE}%"
    exit 1
else
    echo "✅ 磁盘使用率正常: ${DISK_USAGE}%"
fi

echo "✅ 所有检查通过"
EOF

chmod +x $PROJECT_DIR/health_check.sh

echo "📝 生成部署信息..."

# 创建部署信息文件
cat > $PROJECT_DIR/DEPLOYMENT_INFO.md << EOF
# PPT转视频工具部署信息

## 部署时间
$(date '+%Y-%m-%d %H:%M:%S')

## 目录结构
- 项目根目录: $PROJECT_DIR
- 前端目录: $FRONTEND_DIR
- 后端目录: $BACKEND_DIR
- 配置目录: $CONFIG_DIR
- 日志目录: $LOG_DIR

## 服务管理
\`\`\`bash
# 启动服务（通过宝塔面板Python项目管理器）
# 或使用systemd（备用）
systemctl start ppt-video
systemctl stop ppt-video
systemctl restart ppt-video
systemctl status ppt-video

# 查看日志
tail -f $LOG_DIR/ppt-video-app.log
tail -f $LOG_DIR/ppt-video-access.log
tail -f $LOG_DIR/ppt-video-error.log
\`\`\`

## 健康检查
\`\`\`bash
$PROJECT_DIR/health_check.sh
\`\`\`

## 更新部署
1. 备份当前版本
2. 上传新版本到 /tmp/ppt-to-video-deploy
3. 运行更新脚本

## 重要文件
- 环境配置: $CONFIG_DIR/.env
- Nginx配置: 通过宝塔面板配置
- Python依赖: $BACKEND_DIR/requirements.txt

## 注意事项
1. 请在宝塔面板中创建网站并配置Nginx
2. 在Python项目管理器中添加项目
3. 配置SSL证书（推荐）
4. 定期检查日志和磁盘空间
EOF

echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 接下来的步骤："
echo "1. 登录宝塔面板: http://your-server-ip:8888"
echo "2. 网站 → 添加站点 → 域名: your-domain.com → 根目录: $FRONTEND_DIR/dist"
echo "3. 网站设置 → 配置文件 → 使用提供的Nginx配置"
echo "4. Python项目管理器 → 添加项目 → 路径: $BACKEND_DIR"
echo "5. 配置项目: 启动文件app.py，端口5000，Gunicorn启动方式"
echo "6. 启动项目"
echo ""
echo "📖 详细配置请参考: $PROJECT_DIR/../docs/Ubuntu宝塔面板部署指南.md"
echo "🔍 健康检查: $PROJECT_DIR/health_check.sh"
echo "📊 部署信息: $PROJECT_DIR/DEPLOYMENT_INFO.md"
echo ""
