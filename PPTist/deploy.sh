#!/bin/bash

# PPTist 生产环境部署脚本
# 版本: v2.0
# 作者: Netflix V2 Phase 6.5 Team

set -e

echo "🚀 开始 PPTist 生产环境部署..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker环境
check_docker() {
    echo -e "${BLUE}📋 检查Docker环境...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安装，请先安装Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose未安装，请先安装Docker Compose${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker服务未启动，请启动Docker服务${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker环境检查通过${NC}"
}

# 检查系统资源
check_resources() {
    echo -e "${BLUE}📊 检查系统资源...${NC}"
    
    # 检查内存
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEMORY_GB" -lt 2 ]; then
        echo -e "${YELLOW}⚠️  警告: 系统内存少于2GB，可能影响性能${NC}"
    fi
    
    # 检查磁盘空间
    DISK_AVAILABLE=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$DISK_AVAILABLE" -lt 5 ]; then
        echo -e "${RED}❌ 磁盘空间不足5GB，请清理磁盘空间${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 系统资源检查通过${NC}"
}

# 备份现有数据
backup_data() {
    echo -e "${BLUE}💾 备份现有数据...${NC}"
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份配置文件
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$BACKUP_DIR/"
        echo -e "${GREEN}✅ 配置文件已备份${NC}"
    fi
    
    # 备份数据库（如果存在）
    if [ -d "data" ]; then
        cp -r data "$BACKUP_DIR/"
        echo -e "${GREEN}✅ 数据库已备份${NC}"
    fi
    
    echo -e "${GREEN}✅ 数据备份完成: $BACKUP_DIR${NC}"
}

# 构建镜像
build_images() {
    echo -e "${BLUE}🔨 构建Docker镜像...${NC}"
    
    # 构建前端镜像
    echo -e "${YELLOW}构建前端镜像...${NC}"
    docker build -t pptist-frontend:latest .
    
    # 构建后端镜像
    echo -e "${YELLOW}构建后端镜像...${NC}"
    if [ -d "../flask_backend" ]; then
        docker build -t pptist-backend:latest ../flask_backend/
    fi
    
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# 启动服务
start_services() {
    echo -e "${BLUE}🚀 启动服务...${NC}"
    
    # 停止现有服务
    docker-compose down --remove-orphans
    
    # 拉取依赖镜像
    docker-compose pull redis monitor
    
    # 启动所有服务
    docker-compose up -d
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
}

# 健康检查
health_check() {
    echo -e "${BLUE}🔍 进行健康检查...${NC}"
    
    # 等待服务启动
    sleep 30
    
    # 检查前端
    if curl -f http://localhost/health &> /dev/null; then
        echo -e "${GREEN}✅ 前端服务健康${NC}"
    else
        echo -e "${RED}❌ 前端服务不健康${NC}"
        return 1
    fi
    
    # 检查后端
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✅ 后端服务健康${NC}"
    else
        echo -e "${RED}❌ 后端服务不健康${NC}"
        return 1
    fi
    
    # 检查Redis
    if docker exec pptist-redis redis-cli ping | grep -q PONG; then
        echo -e "${GREEN}✅ Redis服务健康${NC}"
    else
        echo -e "${RED}❌ Redis服务不健康${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ 所有服务健康检查通过${NC}"
}

# 配置监控
setup_monitoring() {
    echo -e "${BLUE}📊 配置监控...${NC}"
    
    # 创建Prometheus配置
    mkdir -p docker
    cat > docker/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend:80']
    metrics_path: '/metrics'

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF
    
    echo -e "${GREEN}✅ 监控配置完成${NC}"
}

# 设置日志轮转
setup_log_rotation() {
    echo -e "${BLUE}📝 配置日志轮转...${NC}"
    
    # 创建logrotate配置
    sudo tee /etc/logrotate.d/pptist << EOF
/var/lib/docker/volumes/pptist_nginx-logs/_data/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 nginx nginx
    postrotate
        docker exec pptist-frontend nginx -s reload
    endscript
}

/var/lib/docker/volumes/pptist_backend-logs/_data/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 root root
}
EOF
    
    echo -e "${GREEN}✅ 日志轮转配置完成${NC}"
}

# 安全加固
security_hardening() {
    echo -e "${BLUE}🔒 进行安全加固...${NC}"
    
    # 设置防火墙规则
    if command -v ufw &> /dev/null; then
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw --force enable
        echo -e "${GREEN}✅ 防火墙规则已设置${NC}"
    fi
    
    # 创建非root用户（如果不存在）
    if ! id "pptist" &>/dev/null; then
        sudo useradd -r -s /bin/false pptist
        echo -e "${GREEN}✅ 创建了专用用户${NC}"
    fi
    
    echo -e "${GREEN}✅ 安全加固完成${NC}"
}

# 性能优化
performance_tuning() {
    echo -e "${BLUE}⚡ 进行性能优化...${NC}"
    
    # 设置Docker daemon配置
    sudo tee /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "default-ulimits": {
        "nofile": {
            "Name": "nofile",
            "Hard": 64000,
            "Soft": 64000
        }
    }
}
EOF
    
    # 重启Docker服务
    sudo systemctl restart docker
    
    echo -e "${GREEN}✅ 性能优化完成${NC}"
}

# 生成部署报告
generate_report() {
    echo -e "${BLUE}📋 生成部署报告...${NC}"
    
    REPORT_FILE="deployment-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
PPTist 生产环境部署报告
======================

部署时间: $(date)
部署版本: Netflix V2 Phase 6.5

服务状态:
--------
$(docker-compose ps)

系统资源:
--------
内存使用: $(free -h | grep '^Mem:')
磁盘使用: $(df -h .)
CPU信息: $(nproc) 核心

网络端口:
--------
- 前端服务: http://localhost:80
- 后端API: http://localhost:8000
- Redis: localhost:6379
- 监控面板: http://localhost:9090

安全配置:
--------
- Nginx安全头已配置
- 防火墙规则已设置
- 专用用户已创建
- SSL证书需要单独配置

监控配置:
--------
- Prometheus监控已启用
- 日志轮转已配置
- 健康检查已启用

下一步操作:
----------
1. 配置SSL证书（推荐使用Let's Encrypt）
2. 配置域名解析
3. 设置定期备份任务
4. 配置监控告警
5. 进行压力测试

EOF
    
    echo -e "${GREEN}✅ 部署报告已生成: $REPORT_FILE${NC}"
}

# 主函数
main() {
    echo -e "${GREEN}🎯 PPTist Netflix V2 Phase 6.5 生产环境部署${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    # 执行部署步骤
    check_docker
    check_resources
    backup_data
    setup_monitoring
    build_images
    start_services
    health_check
    setup_log_rotation
    security_hardening
    performance_tuning
    generate_report
    
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo -e "${BLUE}前端访问: http://localhost${NC}"
    echo -e "${BLUE}后端API: http://localhost:8000${NC}"
    echo -e "${BLUE}监控面板: http://localhost:9090${NC}"
    echo ""
    echo -e "${YELLOW}请查看部署报告了解详细信息和后续操作${NC}"
}

# 错误处理
trap 'echo -e "${RED}❌ 部署过程中发生错误${NC}"; exit 1' ERR

# 确保脚本从正确的目录运行
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 运行主函数
main "$@"