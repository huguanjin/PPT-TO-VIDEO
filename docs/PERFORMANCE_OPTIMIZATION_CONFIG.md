# 性能优化配置文件

## 🚀 生产环境优化配置

### 1. Gunicorn配置
创建 `gunicorn.conf.py`:

```python
# Gunicorn配置文件
import multiprocessing

# 服务器套接字
bind = "0.0.0.0:5000"
backlog = 2048

# 工作进程
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 重启
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 日志
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名称
proc_name = "ppt_to_video_api"

# 用户和组
# user = "www-data"
# group = "www-data"
```

### 2. Nginx反向代理配置
创建 `nginx.conf`:

```nginx
upstream ppt_video_backend {
    server 127.0.0.1:5000;
    # 可添加多个服务器实现负载均衡
    # server 127.0.0.1:5001;
    # server 127.0.0.1:5002;
}

server {
    listen 80;
    server_name your-domain.com;  # 替换为实际域名
    
    client_max_body_size 500M;  # 支持大文件上传
    
    # 静态文件处理
    location /static/ {
        alias /path/to/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API请求代理
    location / {
        proxy_pass http://ppt_video_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # 长时间运行的任务（如视频生成）
    location /api/pptist_export/generate_video {
        proxy_pass http://ppt_video_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 延长超时
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

### 3. Redis缓存配置
创建 `redis.conf`:

```ini
# Redis配置用于API缓存和会话存储
port 6379
bind 127.0.0.1
timeout 0
keepalive 60
maxmemory 256mb
maxmemory-policy allkeys-lru

# 持久化
save 900 1
save 300 10
save 60 10000

# 日志
loglevel notice
logfile /var/log/redis/redis.log
```

### 4. 环境变量配置
创建 `.env.production`:

```env
FLASK_ENV=production
FLASK_DEBUG=False

# 数据库
DATABASE_URL=sqlite:///production.db

# Redis缓存
REDIS_URL=redis://localhost:6379/0

# 文件存储
UPLOAD_FOLDER=/var/lib/ppt_video/uploads
OUTPUT_FOLDER=/var/lib/ppt_video/output
TEMP_FOLDER=/var/lib/ppt_video/temp

# API限制
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1

# 安全设置
SECRET_KEY=your-very-secret-key-here
SECURITY_PASSWORD_SALT=your-security-salt-here

# 外部服务
OPENAI_API_KEY=your-openai-api-key
AZURE_TTS_KEY=your-azure-tts-key
```

### 5. Docker化配置
创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn redis

# 应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs output uploads temp

# 非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "flask_backend.unified_app:app"]
```

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  redis_data:
```

## 🔍 监控和日志配置

### 1. 性能监控
添加到Flask应用：

```python
from flask import request
import time
import logging

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    
    # 记录慢请求
    if duration > 2.0:
        app.logger.warning(f"慢请求: {request.method} {request.path} - {duration:.2f}s")
    
    # 添加性能头
    response.headers['X-Response-Time'] = f"{duration:.3f}s"
    
    return response
```

### 2. 健康检查增强
```python
@app.route('/health/detailed')
def detailed_health():
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': app.config.get('VERSION', '1.0.0'),
        'uptime': time.time() - app.start_time,
        'database': check_database_health(),
        'redis': check_redis_health(),
        'disk_space': check_disk_space(),
        'memory_usage': check_memory_usage()
    }
```

## 📊 部署脚本

创建 `deploy.sh`:

```bash
#!/bin/bash
# 生产部署脚本

set -e

echo "🚀 开始部署PPT转视频工具..."

# 更新代码
git pull origin main

# 安装依赖
pip install -r requirements.txt

# 数据库迁移（如果需要）
# python manage.py db upgrade

# 收集静态文件
# python manage.py collectstatic --noinput

# 重启服务
sudo systemctl restart ppt-video-api
sudo systemctl restart nginx

# 健康检查
echo "🔍 等待服务启动..."
sleep 10

if curl -f http://localhost/health; then
    echo "✅ 部署成功！"
else
    echo "❌ 部署失败！"
    exit 1
fi
```

## 📈 性能优化技巧

### 1. 数据库优化
- 添加适当索引
- 使用连接池
- 实现查询缓存

### 2. 文件处理优化
- 异步文件上传
- 分块处理大文件
- 临时文件清理机制

### 3. 内存管理
- 合理设置工作进程数
- 监控内存使用
- 实现内存限制

### 4. 缓存策略
- API响应缓存
- 静态资源缓存
- 数据库查询缓存

---

**📅 配置日期**: 2025-01-11  
**🎯 目标环境**: 生产部署  
**📊 预期提升**: 性能提升3-5倍，稳定性显著改善
