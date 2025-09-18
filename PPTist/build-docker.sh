#!/bin/bash

# =============================================================================
# PPTist Docker构建脚本 - 多安全级别支持
# =============================================================================
# 使用方法：
# ./build-docker.sh [security-level] [tag]
#
# security-level选项：
# - standard   : 使用nginx:mainline-alpine（标准安全）
# - minimal    : 基于alpine手动构建nginx（高安全）
# - distroless : 使用Google distroless镜像（最高安全）
#
# 示例：
# ./build-docker.sh standard pptist:latest
# ./build-docker.sh minimal pptist:secure
# ./build-docker.sh distroless pptist:ultra-secure
# =============================================================================

set -e

# 默认参数
SECURITY_LEVEL=${1:-standard}
IMAGE_TAG=${2:-pptist:latest}
BUILD_DIR=$(dirname "$0")

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date +'%H:%M:%S')] ${message}${NC}"
}

# 显示用法
show_usage() {
    echo "用法: $0 [security-level] [tag]"
    echo ""
    echo "安全级别选项:"
    echo "  standard   - 标准安全级别 (nginx:mainline-alpine)"
    echo "  minimal    - 高安全级别 (自定义alpine+nginx)"
    echo "  distroless - 最高安全级别 (Google distroless镜像)"
    echo ""
    echo "示例:"
    echo "  $0 standard pptist:latest"
    echo "  $0 minimal pptist:secure"
    echo "  $0 distroless pptist:ultra-secure"
    exit 1
}

# 验证Docker是否运行
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_message $RED "错误: Docker daemon未运行"
        exit 1
    fi
}

# 选择Dockerfile
select_dockerfile() {
    case $SECURITY_LEVEL in
        standard)
            DOCKERFILE="Dockerfile"
            print_message $BLUE "使用标准安全级别: nginx:mainline-alpine"
            ;;
        minimal)
            DOCKERFILE="Dockerfile.minimal"
            print_message $YELLOW "使用高安全级别: 自定义Alpine+nginx"
            ;;
        distroless)
            DOCKERFILE="Dockerfile.distroless"
            print_message $GREEN "使用最高安全级别: Google Distroless镜像"
            ;;
        *)
            print_message $RED "错误: 未知的安全级别 '$SECURITY_LEVEL'"
            show_usage
            ;;
    esac

    if [ ! -f "$BUILD_DIR/$DOCKERFILE" ]; then
        print_message $RED "错误: Dockerfile '$DOCKERFILE' 不存在"
        exit 1
    fi
}

# 构建镜像
build_image() {
    print_message $BLUE "开始构建镜像: $IMAGE_TAG"
    print_message $BLUE "使用Dockerfile: $DOCKERFILE"
    
    docker build \
        -f "$BUILD_DIR/$DOCKERFILE" \
        -t "$IMAGE_TAG" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        "$BUILD_DIR"
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 镜像构建成功: $IMAGE_TAG"
    else
        print_message $RED "❌ 镜像构建失败"
        exit 1
    fi
}

# 运行安全扫描（如果可用）
security_scan() {
    if command -v trivy >/dev/null 2>&1; then
        print_message $BLUE "运行安全扫描..."
        trivy image --severity HIGH,CRITICAL "$IMAGE_TAG"
    elif command -v docker >/dev/null 2>&1 && docker --version | grep -q "Desktop"; then
        print_message $BLUE "运行Docker Desktop安全扫描..."
        docker scout cves "$IMAGE_TAG" || true
    else
        print_message $YELLOW "⚠️  未找到安全扫描工具，跳过扫描"
    fi
}

# 显示镜像信息
show_image_info() {
    print_message $GREEN "🔍 镜像信息:"
    docker images "$IMAGE_TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    print_message $GREEN "📋 镜像层信息:"
    docker history "$IMAGE_TAG" --format "table {{.CreatedBy}}\t{{.Size}}" | head -10
}

# 提供运行建议
show_run_suggestions() {
    print_message $GREEN "🚀 运行建议:"
    
    case $SECURITY_LEVEL in
        standard)
            echo "docker run -d -p 80:80 --name pptist-app $IMAGE_TAG"
            ;;
        minimal)
            echo "docker run -d -p 8080:8080 --name pptist-app \\"
            echo "  --security-opt=no-new-privileges:true \\"
            echo "  --cap-drop=ALL --cap-add=CHOWN --cap-add=SETGID --cap-add=SETUID \\"
            echo "  $IMAGE_TAG"
            ;;
        distroless)
            echo "docker run -d -p 8080:8080 --name pptist-app \\"
            echo "  --security-opt=no-new-privileges:true \\"
            echo "  --cap-drop=ALL \\"
            echo "  --read-only --tmpfs /tmp \\"
            echo "  $IMAGE_TAG"
            ;;
    esac
}

# 主执行流程
main() {
    print_message $BLUE "=== PPTist Docker构建工具 ==="
    
    # 验证参数
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
    fi
    
    # 检查Docker
    check_docker
    
    # 选择Dockerfile
    select_dockerfile
    
    # 构建镜像
    build_image
    
    # 显示镜像信息
    show_image_info
    
    # 运行安全扫描
    security_scan
    
    # 显示运行建议
    show_run_suggestions
    
    print_message $GREEN "🎉 构建完成!"
}

# 执行主函数
main "$@"