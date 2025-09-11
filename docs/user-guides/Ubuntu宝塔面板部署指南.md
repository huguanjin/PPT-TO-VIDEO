# PPT转视频工具 Ubuntu 宝塔面板部署指南

## 项目概述

PPT转视频工具是一个基于Vue.js前端和Flask后端的Web应用，需要在Ubuntu Server 22.04上通过宝塔面板进行部署。

### 架构说明
- **前端**: Vue.js + Vite (PPTist目录)
- **后端**: Flask API (flask_backend目录)
- **依赖**: Python 3.8+, Node.js 18+, FFmpeg, 各种Python包

## 一、服务器环境准备

### 1.1 系统要求
```bash
操作系统: Ubuntu Server 22.04 LTS
内存: 至少4GB (推荐8GB+)
磁盘: 至少20GB可用空间
CPU: 2核心以上
```

### 1.2 安装宝塔面板
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装宝塔Linux面板
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh ed8484bec
```

### 1.3 宝塔面板基础环境安装
登录宝塔面板后，安装以下组件：
- **Nginx** 1.22.x
- **Python项目管理器** 
- **PM2管理器** 4.x
- **Node.js** 18.x LTS

### 1.4 系统依赖安装
```bash
# FFmpeg (视频处理必需)
sudo apt install ffmpeg -y

# 系统字体 (字幕渲染需要)
sudo apt install fonts-liberation fonts-dejavu-core fonts-noto-cjk -y

# 图像处理依赖
sudo apt install libjpeg-dev libpng-dev libtiff-dev libwebp-dev -y

# 音频处理依赖
sudo apt install libsndfile1-dev portaudio19-dev -y
```

## 二、项目文件准备

### 2.1 项目打包结构
```
ppt-to-video-deploy/
├── frontend/              # 前端构建文件
│   ├── dist/             # Vue构建输出
│   └── nginx.conf        # Nginx配置
├── backend/              # 后端文件
│   ├── flask_backend/    # Flask应用
│   ├── requirements.txt  # Python依赖
│   ├── gunicorn.conf.py  # Gunicorn配置
│   └── start.sh         # 启动脚本
├── config/               # 配置文件
│   ├── production.json   # 生产环境配置
│   └── .env             # 环境变量
└── deploy/              # 部署脚本
    ├── install.sh       # 安装脚本
    └── update.sh        # 更新脚本
```

### 2.2 创建部署配置文件

#### 2.2.1 Gunicorn配置文件
```python
# backend/gunicorn.conf.py
import multiprocessing

# 监听地址和端口
bind = "127.0.0.1:5000"

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作进程类型
worker_class = "sync"

# 超时设置
timeout = 300
keepalive = 60

# 日志配置
accesslog = "/www/wwwlogs/ppt-video-access.log"
errorlog = "/www/wwwlogs/ppt-video-error.log"
loglevel = "info"

# 进程管理
preload_app = True
max_requests = 1000
max_requests_jitter = 100

# 安全设置
user = "www"
group = "www"
```

#### 2.2.2 Nginx配置文件
```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名
    
    # 前端静态文件
    location / {
        root /www/wwwroot/ppt-video/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
        
        # 缓存设置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 文件上传大小限制
        client_max_body_size 100M;
    }
    
    # 静态资源代理
    location /uploads/ {
        alias /www/wwwroot/ppt-video/backend/uploads/;
        expires 1d;
    }
    
    location /output/ {
        alias /www/wwwroot/ppt-video/backend/output/;
        expires 1d;
    }
}
```

#### 2.2.3 生产环境配置
```json
// config/production.json
{
  "app": {
    "name": "PPT转视频工具",
    "version": "2.0.0",
    "debug": false,
    "host": "0.0.0.0",
    "port": 5000
  },
  "database": {
    "type": "sqlite",
    "path": "/www/wwwroot/ppt-video/data/app.db"
  },
  "storage": {
    "uploads_dir": "/www/wwwroot/ppt-video/backend/uploads",
    "output_dir": "/www/wwwroot/ppt-video/backend/output",
    "temp_dir": "/www/wwwroot/ppt-video/backend/temp"
  },
  "security": {
    "secret_key": "your-production-secret-key-here",
    "cors_origins": ["https://your-domain.com"]
  },
  "logging": {
    "level": "INFO",
    "file": "/www/wwwlogs/ppt-video-app.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

#### 2.2.4 环境变量文件
```bash
# config/.env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-production-secret-key-here

# 数据库配置
DATABASE_URL=sqlite:////www/wwwroot/ppt-video/data/app.db

# 存储路径
UPLOADS_DIR=/www/wwwroot/ppt-video/backend/uploads
OUTPUT_DIR=/www/wwwroot/ppt-video/backend/output
TEMP_DIR=/www/wwwroot/ppt-video/backend/temp

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/www/wwwlogs/ppt-video-app.log

# 外部服务配置
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural
FISH_TTS_API_URL=http://localhost:8080
```

### 2.3 启动脚本
```bash
#!/bin/bash
# backend/start.sh

# 设置工作目录
cd /www/wwwroot/ppt-video/backend

# 激活虚拟环境
source venv/bin/activate

# 加载环境变量
export $(cat ../config/.env | xargs)

# 创建必要目录
mkdir -p uploads output temp logs data

# 设置权限
chown -R www:www uploads output temp logs data

# 启动Gunicorn
exec gunicorn -c gunicorn.conf.py flask_backend.app:app
```

## 三、部署步骤

### 3.1 准备部署包

#### 3.1.1 前端构建
在本地开发环境中：
```bash
cd PPTist
npm install
npm run build
```

#### 3.1.2 创建部署包
```bash
# 创建部署目录
mkdir ppt-to-video-deploy
cd ppt-to-video-deploy

# 复制前端构建文件
mkdir frontend
cp -r ../PPTist/dist frontend/

# 复制后端文件
mkdir backend
cp -r ../flask_backend backend/
cp ../requirements.txt backend/

# 创建配置目录
mkdir config
# 将上述配置文件放入config目录

# 创建部署脚本目录
mkdir deploy
```

#### 3.1.3 安装脚本
```bash
#!/bin/bash
# deploy/install.sh

set -e

echo "🚀 开始部署PPT转视频工具..."

# 设置项目目录
PROJECT_DIR="/www/wwwroot/ppt-video"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 创建项目目录
sudo mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 复制文件
echo "📁 复制项目文件..."
sudo cp -r /tmp/ppt-to-video-deploy/* .

# 设置权限
sudo chown -R www:www $PROJECT_DIR

# 安装Python依赖
echo "🐍 安装Python依赖..."
cd $BACKEND_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 创建必要目录
mkdir -p uploads output temp logs data
chown -R www:www uploads output temp logs data

# 设置日志目录
sudo mkdir -p /www/wwwlogs
sudo chown -R www:www /www/wwwlogs

echo "✅ 安装完成！"
echo "请在宝塔面板中配置Nginx站点和Python项目。"
```

### 3.2 上传到服务器
```bash
# 打包部署文件
tar -czf ppt-to-video-deploy.tar.gz ppt-to-video-deploy/

# 上传到服务器 (使用scp或宝塔面板文件管理)
scp ppt-to-video-deploy.tar.gz root@your-server:/tmp/

# 在服务器上解压
ssh root@your-server
cd /tmp
tar -xzf ppt-to-video-deploy.tar.gz
```

### 3.3 宝塔面板配置

#### 3.3.1 创建网站
1. 进入宝塔面板 → 网站 → 添加站点
2. 域名：填入您的域名
3. 根目录：`/www/wwwroot/ppt-video/frontend/dist`
4. PHP版本：纯静态

#### 3.3.2 配置Nginx
1. 点击网站设置 → 配置文件
2. 替换为上面提供的Nginx配置

#### 3.3.3 添加Python项目
1. 进入Python项目管理器
2. 添加项目：
   - 项目名称：ppt-video-backend
   - 路径：`/www/wwwroot/ppt-video/backend`
   - Python版本：3.8+
   - 启动方式：Gunicorn
   - 启动文件：`flask_backend/app.py`
   - 端口：5000

#### 3.3.4 SSL证书配置（可选）
1. 网站设置 → SSL → Let's Encrypt
2. 申请免费SSL证书

## 四、运行和维护

### 4.1 启动服务
```bash
# 方式1：通过宝塔面板
# Python项目管理器 → 启动项目

# 方式2：手动启动
cd /www/wwwroot/ppt-video/backend
bash start.sh
```

### 4.2 监控和日志
```bash
# 查看应用日志
tail -f /www/wwwlogs/ppt-video-app.log

# 查看Nginx访问日志
tail -f /www/wwwlogs/ppt-video-access.log

# 查看错误日志
tail -f /www/wwwlogs/ppt-video-error.log
```

### 4.3 更新部署
```bash
#!/bin/bash
# deploy/update.sh

echo "🔄 更新PPT转视频工具..."

PROJECT_DIR="/www/wwwroot/ppt-video"

# 备份当前版本
cp -r $PROJECT_DIR $PROJECT_DIR.backup.$(date +%Y%m%d_%H%M%S)

# 停止服务
sudo supervisorctl stop ppt-video || true

# 更新文件
cp -r /tmp/ppt-to-video-deploy/* $PROJECT_DIR/

# 更新Python依赖
cd $PROJECT_DIR/backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启服务
sudo supervisorctl start ppt-video

echo "✅ 更新完成！"
```

### 4.4 性能优化

#### 4.4.1 Redis缓存（可选）
```bash
# 安装Redis
sudo apt install redis-server -y

# 在requirements.txt中添加
echo "redis==4.5.4" >> backend/requirements.txt
```

#### 4.4.2 文件清理脚本
```bash
#!/bin/bash
# deploy/cleanup.sh

# 清理30天前的临时文件
find /www/wwwroot/ppt-video/backend/temp -type f -mtime +30 -delete

# 清理大型输出文件
find /www/wwwroot/ppt-video/backend/output -name "*.mp4" -mtime +7 -delete

# 压缩日志文件
find /www/wwwlogs -name "*.log" -size +100M -exec gzip {} \;
```

## 五、故障排除

### 5.1 常见问题

#### 5.1.1 视频处理失败
```bash
# 检查FFmpeg安装
ffmpeg -version

# 检查权限
ls -la /www/wwwroot/ppt-video/backend/
```

#### 5.1.2 内存不足
```bash
# 添加交换文件
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 5.1.3 端口冲突
```bash
# 检查端口占用
netstat -tlnp | grep :5000

# 修改端口配置
vim /www/wwwroot/ppt-video/backend/gunicorn.conf.py
```

### 5.2 性能调优
1. 根据服务器性能调整Gunicorn worker数量
2. 配置Nginx缓存和压缩
3. 使用CDN加速静态资源
4. 定期清理临时文件

## 六、安全建议

1. **防火墙配置**：只开放必要端口（80, 443, 22）
2. **文件权限**：确保www用户权限最小化
3. **定期更新**：保持系统和依赖包更新
4. **备份策略**：定期备份配置和数据
5. **监控告警**：配置服务状态监控

---

**部署完成后的访问地址：**
- 前端界面：`https://your-domain.com`
- API文档：`https://your-domain.com/api/docs`
- 健康检查：`https://your-domain.com/api/health`

**技术支持：**
如需技术支持，请查看项目文档或提交Issue。
