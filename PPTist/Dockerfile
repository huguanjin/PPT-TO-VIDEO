# =============================================================================
# PPTist Docker镜像 - 多阶段构建配置
# =============================================================================
# 安全注意事项：
# 1. 使用最新LTS版本以获取安全补丁
# 2. 定期更新基础镜像版本
# 3. 运行时使用非root用户
# 4. 安装系统更新并清理缓存
# 
# 安全替代方案（如果仍有漏洞警告）：
# - 考虑使用 distroless 镜像
# - 使用公司内部的经过安全扫描的镜像仓库
# - 在 CI/CD 中集成容器安全扫描
# =============================================================================

# 使用最新的Node.js LTS版本以获得最新安全补丁
FROM node:22-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装安全更新（使用apt for Debian）
# 清理包缓存以减少镜像大小并提高安全性
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# =============================================================================
# 生产阶段 - Nginx Web服务器配置
# =============================================================================
# 安全策略说明：
# 1. 使用 nginx:mainline-alpine - 最新主线版本，包含最新安全补丁
# 2. 如果扫描器仍报告漏洞，可尝试以下替代方案：
#    - nginx:1.25-alpine (指定特定版本)
#    - gcr.io/distroless/static (Google的distroless镜像)
#    - 使用公司内部维护的安全镜像
# 3. 生产环境建议：
#    - 在CI/CD中集成容器安全扫描
#    - 定期更新基础镜像
#    - 使用镜像签名验证
# =============================================================================
FROM nginx:mainline-alpine AS production

# 安装必要的工具和安全更新（使用apk for Alpine）
# 添加安全增强措施和漏洞缓解
RUN apk update && apk upgrade && \
    apk add --no-cache \
    curl \
    tzdata \
    ca-certificates \
    dumb-init \
    && rm -rf /var/cache/apk/* \
    && rm -rf /tmp/* \
    && addgroup -g 1001 -S nginx \
    && adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx \
    && mkdir -p /var/log/nginx /var/cache/nginx /var/run \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/log/nginx /var/cache/nginx /var/run/nginx.pid

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf /etc/nginx/conf.d/default.conf

# 创建日志目录
RUN mkdir -p /var/log/nginx

# 设置权限和安全配置
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/log/nginx && \
    chmod -R 755 /usr/share/nginx/html && \
    chmod -R 755 /var/log/nginx

# 添加安全标签和元数据
LABEL maintainer="PPTist Team" \
      version="1.0" \
      description="PPTist Web Application with Security Hardening" \
      security.scan.required="true" \
      security.updates="$(date)"

# 切换到非特权用户（安全最佳实践）
USER nginx

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 暴露端口
EXPOSE 80

# 启动nginx（使用dumb-init作为PID 1以正确处理信号）
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]

# 运行时安全建议（在docker run或docker-compose中使用）：
# --security-opt=no-new-privileges:true
# --cap-drop=ALL --cap-add=CHOWN --cap-add=SETGID --cap-add=SETUID
# --read-only --tmpfs /tmp --tmpfs /var/cache/nginx
# --user nginx:nginx