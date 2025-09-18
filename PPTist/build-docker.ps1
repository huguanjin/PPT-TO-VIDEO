# =============================================================================
# PPTist Docker构建脚本 - 多安全级别支持 (PowerShell版本)
# =============================================================================
# 使用方法：
# .\build-docker.ps1 [SecurityLevel] [Tag]
#
# SecurityLevel选项：
# - Standard   : 使用nginx:mainline-alpine（标准安全）
# - Minimal    : 基于alpine手动构建nginx（高安全）
# - Distroless : 使用Google distroless镜像（最高安全）
#
# 示例：
# .\build-docker.ps1 Standard pptist:latest
# .\build-docker.ps1 Minimal pptist:secure
# .\build-docker.ps1 Distroless pptist:ultra-secure
# =============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("Standard", "Minimal", "Distroless")]
    [string]$SecurityLevel = "Standard",
    
    [Parameter(Position=1)]
    [string]$ImageTag = "pptist:latest"
)

# 全局变量
$script:Dockerfile = ""

# 颜色输出函数
function Write-ColorMessage {
    param(
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

# 显示用法
function Show-Usage {
    Write-Host @"
用法: .\build-docker.ps1 [SecurityLevel] [Tag]

安全级别选项:
  Standard   - 标准安全级别 (nginx:mainline-alpine)
  Minimal    - 高安全级别 (自定义alpine+nginx)
  Distroless - 最高安全级别 (Google distroless镜像)

示例:
  .\build-docker.ps1 Standard pptist:latest
  .\build-docker.ps1 Minimal pptist:secure
  .\build-docker.ps1 Distroless pptist:ultra-secure
"@
}

# 验证Docker是否运行
function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-ColorMessage "错误: Docker daemon未运行" Red
        return $false
    }
}

# 选择Dockerfile
function Select-Dockerfile {
    param([string]$Level)
    
    switch ($Level) {
        "Standard" {
            $script:Dockerfile = "Dockerfile"
            Write-ColorMessage "使用标准安全级别: nginx:mainline-alpine" Cyan
        }
        "Minimal" {
            $script:Dockerfile = "Dockerfile.minimal"
            Write-ColorMessage "使用高安全级别: 自定义Alpine+nginx" Yellow
        }
        "Distroless" {
            $script:Dockerfile = "Dockerfile.distroless"
            Write-ColorMessage "使用最高安全级别: Google Distroless镜像" Green
        }
    }
    
    if (-not (Test-Path $script:Dockerfile)) {
        Write-ColorMessage "错误: Dockerfile '$script:Dockerfile' 不存在" Red
        exit 1
    }
}

# 构建镜像
function Build-Image {
    param([string]$Tag, [string]$DockerfilePath)
    
    Write-ColorMessage "开始构建镜像: $Tag" Cyan
    Write-ColorMessage "使用Dockerfile: $DockerfilePath" Cyan
    
    $buildDate = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $vcsRef = try { 
        if (Get-Command git -ErrorAction SilentlyContinue) {
            git rev-parse --short HEAD 2>$null
        } else {
            "unknown"
        }
    } catch { "unknown" }
    
    try {
        $output = docker build -f $DockerfilePath -t $Tag --build-arg "BUILD_DATE=$buildDate" --build-arg "VCS_REF=$vcsRef" . 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorMessage "✅ 镜像构建成功: $Tag" Green
            return $true
        } else {
            Write-ColorMessage "❌ 镜像构建失败" Red
            Write-Host $output
            return $false
        }
    }
    catch {
        Write-ColorMessage "❌ 构建过程中出现异常: $($_.Exception.Message)" Red
        return $false
    }
}

# 运行安全扫描
function Invoke-SecurityScan {
    param([string]$Tag)
    
    # 检查Trivy
    if (Get-Command trivy -ErrorAction SilentlyContinue) {
        Write-ColorMessage "运行Trivy安全扫描..." Cyan
        trivy image --severity HIGH,CRITICAL $Tag
    }
    # 检查Docker Desktop扫描
    elseif (docker --version | Select-String "Desktop") {
        Write-ColorMessage "运行Docker Desktop安全扫描..." Cyan
        docker scout cves $Tag
    }
    else {
        Write-ColorMessage "⚠️  未找到安全扫描工具，跳过扫描" Yellow
    }
}

# 显示镜像信息
function Show-ImageInfo {
    param([string]$Tag)
    
    Write-ColorMessage "🔍 镜像信息:" Green
    docker images $Tag --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    Write-ColorMessage "📋 镜像层信息:" Green
    docker history $Tag --format "table {{.CreatedBy}}\t{{.Size}}" | Select-Object -First 10
}

# 提供运行建议
function Show-RunSuggestions {
    param([string]$Level, [string]$Tag)
    
    Write-ColorMessage "🚀 运行建议:" Green
    
    switch ($Level) {
        "Standard" {
            Write-Host "docker run -d -p 80:80 --name pptist-app $Tag"
        }
        "Minimal" {
            Write-Host @"
docker run -d -p 8080:8080 --name pptist-app \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL --cap-add=CHOWN --cap-add=SETGID --cap-add=SETUID \
  $Tag
"@
        }
        "Distroless" {
            Write-Host @"
docker run -d -p 8080:8080 --name pptist-app \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --read-only --tmpfs /tmp \
  $Tag
"@
        }
    }
}

# 主执行流程
function Main {
    Write-ColorMessage "=== PPTist Docker构建工具 ===" Cyan
    
    # 显示帮助
    if ($args -contains "-h" -or $args -contains "--help") {
        Show-Usage
        return
    }
    
    # 检查Docker
    if (-not (Test-Docker)) {
        exit 1
    }
    
    # 选择Dockerfile
    Select-Dockerfile $SecurityLevel
    
    # 构建镜像
    if (-not (Build-Image $ImageTag $script:Dockerfile)) {
        exit 1
    }
    
    # 显示镜像信息
    Show-ImageInfo $ImageTag
    
    # 运行安全扫描
    Invoke-SecurityScan $ImageTag
    
    # 显示运行建议
    Show-RunSuggestions $SecurityLevel $ImageTag
    
    Write-ColorMessage "🎉 构建完成!" Green
}

# 执行主函数
Main