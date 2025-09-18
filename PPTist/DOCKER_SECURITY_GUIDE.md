# Docker 安全配置指南

## 最新更新 (2025-09-18)
针对持续的nginx镜像安全警告，现在提供三种不同安全级别的解决方案：

### 🏗️ 可用的构建选项

#### 1. 标准安全级别 (`Dockerfile`)
- **基础镜像**: `nginx:mainline-alpine`
- **安全特性**: 最新nginx版本 + 运行时强化
- **使用场景**: 一般生产环境
- **构建命令**: `.\build-docker.ps1 Standard pptist:latest`

#### 2. 高安全级别 (`Dockerfile.minimal`)  
- **基础镜像**: `alpine:3.19` + 手动安装nginx
- **安全特性**: 完全控制安装过程，最小攻击面
- **使用场景**: 高安全要求环境
- **构建命令**: `.\build-docker.ps1 Minimal pptist:secure`

#### 3. 最高安全级别 (`Dockerfile.distroless`)
- **基础镜像**: `gcr.io/distroless/static-debian11`
- **安全特性**: 无shell、无包管理器，极小攻击面
- **使用场景**: 金融、医疗等严格安全环境
- **构建命令**: `.\build-docker.ps1 Distroless pptist:ultra-secure`

## 快速开始

### Windows用户
```powershell
# 标准安全级别
.\build-docker.ps1 Standard pptist:latest

# 高安全级别
.\build-docker.ps1 Minimal pptist:secure

# 最高安全级别
.\build-docker.ps1 Distroless pptist:ultra-secure
```

### Linux/Mac用户
```bash
# 标准安全级别
./build-docker.sh standard pptist:latest

# 高安全级别  
./build-docker.sh minimal pptist:secure

# 最高安全级别
./build-docker.sh distroless pptist:ultra-secure
```

### 2. 运行时安全
- 使用非root用户运行容器
- 设置适当的文件权限
- 清理包管理器缓存
- 安装最新安全更新

### 3. 容器配置
- 添加健康检查
- 设置合适的时区
- 限制暴露端口
- 添加安全标签

## 如果仍有安全漏洞报告

### 选项 1: 使用 Distroless 镜像
```dockerfile
# 替换生产阶段
FROM gcr.io/distroless/static-debian11 AS production
# 注意：需要调整配置文件路径和启动方式
```

### 选项 2: 使用特定版本
```dockerfile
# 使用更具体的版本号
FROM nginx:1.24-alpine AS production
```

### 选项 3: 自定义安全镜像
```dockerfile
# 基于最小基础镜像构建
FROM alpine:3.18 AS production
RUN apk add --no-cache nginx
# 手动配置nginx...
```

### 选项 4: 多层防护
- 在 Kubernetes 中使用 Network Policies
- 配置 Pod Security Standards
- 使用服务网格 (如 Istio) 进行流量加密
- 实施运行时安全监控

## 生产环境建议

### 1. CI/CD 集成
```yaml
# GitHub Actions 示例
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'your-image:latest'
    format: 'sarif'
```

### 2. 镜像扫描
- 使用 Trivy、Snyk 或 Clair 进行持续扫描
- 设置漏洞阈值策略
- 配置自动化补丁流程

### 3. 运行时保护
- 使用只读根文件系统
- 限制容器能力 (capabilities)
- 配置资源限制
- 实施网络分段

### 4. 监控和审计
- 容器运行时监控
- 日志聚合和分析
- 安全事件告警
- 定期安全评估

## 风险接受策略

如果经过评估，某些低优先级漏洞在当前环境中风险可控：

1. **文档化风险**: 记录已知漏洞和缓解措施
2. **监控策略**: 设置检测和响应机制
3. **更新计划**: 制定定期更新时间表
4. **替代控制**: 在网络层或应用层添加额外安全措施

## 联系和支持

如需进一步的安全配置支持：
- 查阅 Docker 官方安全指南
- 联系安全团队
- 考虑使用企业级容器安全解决方案

---
*最后更新: $(date)*
*版本: 1.0*