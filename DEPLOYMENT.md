# 部署配置

## 开发环境

### 后端服务启动
```bash
cd flask_backend
python app.py
```
- 服务地址: http://localhost:5000
- API文档: http://localhost:5000/docs

### 前端开发服务器
```bash
cd PPTist
npm run dev
```
- 服务地址: http://localhost:5173
- 热重载: 支持

## 生产环境部署

### 后端部署 (使用Gunicorn)

1. **安装Gunicorn**:
```bash
pip install gunicorn
```

2. **启动生产服务器**:
```bash
cd flask_backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **使用配置文件**:
```bash
# 创建 gunicorn.conf.py
cat > gunicorn.conf.py << EOF
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2
EOF

# 启动服务
gunicorn -c gunicorn.conf.py app:app
```

### 前端部署 (静态文件)

1. **构建生产版本**:
```bash
cd PPTist
npm run build
```

2. **使用Nginx部署**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/PPTist/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 文件上传大小限制
    client_max_body_size 100M;
}
```

### Docker部署

1. **后端Dockerfile**:
```dockerfile
# flask_backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

2. **前端Dockerfile**:
```dockerfile
# PPTist/Dockerfile
FROM node:16-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

3. **docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./flask_backend
    ports:
      - "5000:5000"
    volumes:
      - ./config_data:/app/config_data
      - ./output:/app/output
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      
  frontend:
    build: ./PPTist
    ports:
      - "80:80"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
```

## 环境变量配置

### 开发环境 (.env)
```bash
# Flask配置
FLASK_ENV=development
FLASK_DEBUG=True

# 数据库配置
DATABASE_URL=sqlite:///config_data/storage/app.db

# AI服务配置
OPENAI_API_KEY=your-openai-key
AZURE_API_KEY=your-azure-key

# 文件路径
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=output
LOG_FOLDER=logs
```

### 生产环境 (.env.production)
```bash
# Flask配置
FLASK_ENV=production
FLASK_DEBUG=False

# 安全配置
SECRET_KEY=your-production-secret-key

# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost/ppt_to_video

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379

# 文件存储
STORAGE_TYPE=s3
AWS_BUCKET=your-bucket-name
```

## 性能优化

### 1. 数据库优化
- 使用PostgreSQL替代SQLite
- 添加数据库索引
- 配置连接池

### 2. 缓存配置
- Redis缓存配置
- 静态文件CDN
- API响应缓存

### 3. 负载均衡
- Nginx负载均衡
- 多实例部署
- 健康检查

## 监控和日志

### 1. 应用监控
```python
# 添加到app.py
from flask import Flask
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# 配置日志
logging.basicConfig(level=logging.INFO)
```

### 2. 系统监控
- CPU和内存监控
- 磁盘空间监控
- 网络流量监控

### 3. 错误跟踪
- 集成Sentry
- 自定义错误页面
- 错误通知机制

## 安全配置

### 1. HTTPS配置
- SSL证书配置
- HTTP重定向
- 安全头设置

### 2. 访问控制
- API访问限制
- 文件上传验证
- 跨域配置

### 3. 数据保护
- API密钥加密存储
- 用户数据隐私
- 备份策略
