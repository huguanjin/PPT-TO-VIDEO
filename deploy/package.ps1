# PPT转视频工具打包脚本 - PowerShell版本
# 用于创建生产环境部署包

Write-Host "📦 开始创建部署包..." -ForegroundColor Green

# 配置变量
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DeployDir = Join-Path $ProjectRoot "ppt-to-video-deploy"
$BuildDir = Join-Path $ProjectRoot "build"

# 清理并创建部署目录
if (Test-Path $DeployDir) {
    Remove-Item $DeployDir -Recurse -Force
}
New-Item -ItemType Directory -Path $DeployDir -Force | Out-Null

Write-Host "🏗️  构建前端..." -ForegroundColor Blue

# 构建前端
$PPTistDir = Join-Path $ProjectRoot "PPTist"
Push-Location $PPTistDir

# 检查是否需要安装依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 安装前端依赖..." -ForegroundColor Yellow
    npm install
}

Write-Host "🔨 构建生产版本..." -ForegroundColor Yellow
npm run build

# 复制前端构建文件
$FrontendDeployDir = Join-Path $DeployDir "frontend"
New-Item -ItemType Directory -Path $FrontendDeployDir -Force | Out-Null
Copy-Item -Path "dist\*" -Destination $FrontendDeployDir -Recurse -Force

Pop-Location

Write-Host "📁 复制后端文件..." -ForegroundColor Blue

# 复制后端文件
$BackendDeployDir = Join-Path $DeployDir "backend"
$FlaskBackendDir = Join-Path $ProjectRoot "flask_backend"
Copy-Item -Path $FlaskBackendDir -Destination $BackendDeployDir -Recurse -Force

# 复制根目录的requirements.txt（如果存在且更完整）
$RootRequirements = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $RootRequirements) {
    Copy-Item $RootRequirements -Destination (Join-Path $BackendDeployDir "requirements.txt") -Force
}

Write-Host "⚙️  创建生产配置..." -ForegroundColor Blue

# 创建配置目录
$ConfigDeployDir = Join-Path $DeployDir "config"
New-Item -ItemType Directory -Path $ConfigDeployDir -Force | Out-Null

# 创建生产环境配置模板
$ProductionConfig = @'
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
    "secret_key": "CHANGE-THIS-IN-PRODUCTION",
    "cors_origins": ["https://your-domain.com"]
  },
  "logging": {
    "level": "INFO",
    "file": "/www/wwwlogs/ppt-video-app.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "subtitle": {
    "style": "netflix_standard",
    "font_family": "Arial",
    "font_size": 24,
    "font_color": "#FFFFFF",
    "background_color": "rgba(0,0,0,0.8)",
    "position": "bottom",
    "margin": 50
  },
  "video": {
    "quality": "high",
    "fps": 30,
    "resolution": "1920x1080",
    "format": "mp4"
  }
}
'@

Set-Content -Path (Join-Path $ConfigDeployDir "production.json") -Value $ProductionConfig -Encoding UTF8

# 创建环境变量模板
$EnvTemplate = @'
# 生产环境配置模板
# 复制为 .env 并修改相应值

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

# 域名配置（用于CORS）
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
'@

Set-Content -Path (Join-Path $ConfigDeployDir ".env.template") -Value $EnvTemplate -Encoding UTF8

Write-Host "🐍 创建Gunicorn配置..." -ForegroundColor Blue

# 创建Gunicorn配置
$GunicornConfig = @'
import multiprocessing
import os

# 基础配置
bind = "127.0.0.1:5000"
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
worker_class = "sync"
worker_connections = 1000

# 超时配置
timeout = 300
keepalive = 60
graceful_timeout = 30

# 日志配置
accesslog = "/www/wwwlogs/ppt-video-access.log"
errorlog = "/www/wwwlogs/ppt-video-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程管理
preload_app = True
max_requests = 1000
max_requests_jitter = 100

# 安全配置
user = "www"
group = "www"

# 性能优化
worker_tmp_dir = "/dev/shm"
tmp_upload_dir = None

# SSL配置（如果需要）
# keyfile = "/path/to/private.key"
# certfile = "/path/to/certificate.crt"

# 监控配置
proc_name = "ppt-video-backend"

def when_ready(server):
    """服务器准备就绪时的回调"""
    server.log.info("PPT转视频工具后端服务启动完成")

def worker_int(worker):
    """工作进程中断时的回调"""
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    """fork工作进程前的回调"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """fork工作进程后的回调"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)
'@

Set-Content -Path (Join-Path $BackendDeployDir "gunicorn.conf.py") -Value $GunicornConfig -Encoding UTF8

Write-Host "🌐 创建Nginx配置模板..." -ForegroundColor Blue

# 创建Nginx配置模板
$NginxConfig = @'
# PPT转视频工具 Nginx 配置
# 请在宝塔面板中使用此配置

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # 替换为您的域名
    
    # HTTP跳转到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;  # 替换为您的域名
    
    # SSL配置 (由宝塔面板自动管理)
    # ssl_certificate /path/to/certificate.crt;
    # ssl_certificate_key /path/to/private.key;
    
    # 文件上传大小限制
    client_max_body_size 500M;
    client_body_timeout 300s;
    
    # 前端静态文件
    location / {
        root /www/wwwroot/ppt-video/frontend;
        try_files $uri $uri/ /index.html;
        index index.html;
        
        # 缓存设置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options nosniff;
        }
        
        # 安全头
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy strict-origin-when-cross-origin;
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
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # 上传文件访问
    location /uploads/ {
        alias /www/wwwroot/ppt-video/backend/uploads/;
        expires 1d;
        add_header Cache-Control "public, no-transform";
        
        # 安全设置
        location ~ \.(php|jsp|asp|aspx)$ {
            deny all;
        }
    }
    
    # 输出文件访问
    location /output/ {
        alias /www/wwwroot/ppt-video/backend/output/;
        expires 1h;
        add_header Cache-Control "private, no-cache";
        
        # 防止直接访问敏感文件
        location ~ \.(log|ini|conf)$ {
            deny all;
        }
    }
    
    # 禁止访问敏感文件
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(log|ini|conf|sql|bak)$ {
        deny all;
    }
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1k;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
'@

Set-Content -Path (Join-Path $ConfigDeployDir "nginx.conf") -Value $NginxConfig -Encoding UTF8

Write-Host "📜 创建启动脚本..." -ForegroundColor Blue

# 创建启动脚本
$StartScript = @'
#!/bin/bash
# PPT转视频工具启动脚本

set -e

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd $SCRIPT_DIR

# 加载环境变量
if [ -f "../config/.env" ]; then
    export $(cat ../config/.env | grep -v '^#' | xargs)
fi

# 创建必要目录
mkdir -p uploads output temp logs data

# 设置权限
chown -R www:www uploads output temp logs data

# 激活虚拟环境
source venv/bin/activate

echo "🚀 启动PPT转视频工具后端服务..."
echo "📊 监听地址: http://127.0.0.1:5000"
echo "📖 API文档: http://127.0.0.1:5000/docs"

# 启动Gunicorn
exec gunicorn -c gunicorn.conf.py flask_backend.app:app
'@

Set-Content -Path (Join-Path $BackendDeployDir "start.sh") -Value $StartScript -Encoding UTF8

Write-Host "📋 创建部署文档..." -ForegroundColor Blue

# 复制部署脚本
Copy-Item -Path (Join-Path $ScriptDir "install.sh") -Destination $DeployDir -Force
Copy-Item -Path (Join-Path $ScriptDir "update.sh") -Destination $DeployDir -Force

# 创建README
$ReadmeContent = @"
# PPT转视频工具部署包

## 包含内容

- `frontend/` - 前端构建文件 (Vue.js)
- `backend/` - 后端应用 (Flask)
- `config/` - 配置文件模板
- `install.sh` - 安装脚本
- `update.sh` - 更新脚本

## 快速部署

1. 上传此部署包到服务器 `/tmp/` 目录并解压
2. 运行安装脚本: `sudo bash install.sh`
3. 在宝塔面板中配置网站和Python项目
4. 访问您的域名

## 详细说明

请参考 `../docs/Ubuntu宝塔面板部署指南.md` 获取完整部署文档。

## 版本信息

- 构建时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- 项目版本: 2.0.0
- 部署目标: Ubuntu Server 22.04 + 宝塔面板
"@

Set-Content -Path (Join-Path $DeployDir "README.md") -Value $ReadmeContent -Encoding UTF8

Write-Host "📦 创建压缩包..." -ForegroundColor Blue

# 创建构建目录
if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
}

# 创建压缩包
$TimeStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchiveName = "ppt-to-video-deploy-$TimeStamp.zip"
$ArchivePath = Join-Path $BuildDir $ArchiveName

# 使用PowerShell 5+ 的 Compress-Archive
Push-Location $ProjectRoot
Compress-Archive -Path "ppt-to-video-deploy\*" -DestinationPath $ArchivePath -Force
Pop-Location

Write-Host ""
Write-Host "🎉 部署包创建完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📦 部署包位置:" -ForegroundColor Yellow
Write-Host "- 目录: $DeployDir" -ForegroundColor White
Write-Host "- 压缩包: $ArchivePath" -ForegroundColor White
Write-Host ""
Write-Host "📋 部署步骤:" -ForegroundColor Yellow
Write-Host "1. 上传压缩包到服务器 /tmp/ 目录" -ForegroundColor White
Write-Host "2. 解压: unzip ppt-to-video-deploy-*.zip" -ForegroundColor White
Write-Host "3. 运行: sudo bash ppt-to-video-deploy/install.sh" -ForegroundColor White
Write-Host "4. 在宝塔面板中配置网站" -ForegroundColor White
Write-Host ""
Write-Host "📖 详细文档: docs/Ubuntu宝塔面板部署指南.md" -ForegroundColor Yellow
Write-Host ""
