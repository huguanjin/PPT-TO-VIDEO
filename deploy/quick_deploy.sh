#!/bin/bash
# PPT转视频工具快速部署脚本
# 适用于从零开始的Ubuntu Server 22.04系统

set -e

echo "🚀 PPT转视频工具一键部署脚本"
echo "适用于 Ubuntu Server 22.04 + 宝塔面板"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用root用户执行此脚本${NC}"
    exit 1
fi

echo -e "${BLUE}📋 系统信息检查...${NC}"

# 检查系统版本
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ $ID != "ubuntu" ]] || [[ $VERSION_ID != "22.04" ]]; then
        echo -e "${YELLOW}⚠️  警告: 此脚本专为Ubuntu 22.04设计，当前系统: $PRETTY_NAME${NC}"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${RED}❌ 无法检测系统版本${NC}"
    exit 1
fi

# 检查网络连接
echo -e "${BLUE}🌐 检查网络连接...${NC}"
if ! ping -c 1 google.com &> /dev/null; then
    echo -e "${RED}❌ 网络连接失败，请检查网络设置${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 网络连接正常${NC}"

# 更新系统
echo -e "${BLUE}📦 更新系统包...${NC}"
apt update && apt upgrade -y

# 安装基础依赖
echo -e "${BLUE}🔧 安装基础依赖...${NC}"
apt install -y \
    wget \
    curl \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 检查宝塔面板是否已安装
if [ -f "/www/server/panel/BT-Panel" ]; then
    echo -e "${GREEN}✅ 检测到宝塔面板已安装${NC}"
else
    echo -e "${YELLOW}📥 安装宝塔面板...${NC}"
    wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh
    bash install.sh ed8484bec
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 宝塔面板安装完成${NC}"
    else
        echo -e "${RED}❌ 宝塔面板安装失败${NC}"
        exit 1
    fi
fi

# 安装系统依赖
echo -e "${BLUE}🔧 安装PPT转视频工具系统依赖...${NC}"
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
    build-essential \
    python3-pip

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}📥 安装Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l 2>/dev/null || echo "0") -eq 0 ]]; then
    echo -e "${RED}❌ Python版本过低，需要3.8+，当前版本: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"

# 检查部署包
DEPLOY_SOURCE="/tmp/ppt-to-video-deploy"
if [ ! -d "$DEPLOY_SOURCE" ]; then
    echo -e "${YELLOW}📋 未找到部署包，请按以下步骤操作：${NC}"
    echo "1. 在本地运行打包脚本: bash deploy/package.sh"
    echo "2. 上传生成的压缩包到服务器 /tmp/ 目录"
    echo "3. 解压: tar -xzf ppt-to-video-deploy-*.tar.gz -C /tmp/"
    echo "4. 重新运行此脚本"
    exit 1
fi

# 运行安装脚本
echo -e "${BLUE}🚀 开始安装PPT转视频工具...${NC}"
if [ -f "$DEPLOY_SOURCE/install.sh" ]; then
    bash $DEPLOY_SOURCE/install.sh
else
    echo -e "${RED}❌ 安装脚本不存在${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 一键部署完成！${NC}"
echo ""
echo -e "${BLUE}📋 后续步骤：${NC}"
echo "1. 访问宝塔面板: http://$(curl -s ifconfig.me):8888"
echo "2. 配置网站和Python项目"
echo "3. 上传SSL证书（推荐）"
echo "4. 测试服务功能"
echo ""
echo -e "${BLUE}📖 详细配置文档：${NC}"
echo "/www/wwwroot/ppt-video/../docs/Ubuntu宝塔面板部署指南.md"
echo ""
echo -e "${BLUE}🔍 服务状态检查：${NC}"
echo "/www/wwwroot/ppt-video/health_check.sh"
echo ""
echo -e "${YELLOW}⚠️  重要提示：${NC}"
echo "1. 请记录宝塔面板登录信息"
echo "2. 修改默认密码和端口"
echo "3. 配置防火墙规则"
echo "4. 定期备份数据"
echo ""
