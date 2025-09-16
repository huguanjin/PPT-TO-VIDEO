# Flask后端清理 - 阶段1执行脚本
# 用于安全清理无用文件（低风险操作）

param(
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Info { Write-ColorOutput Cyan $args }

# 主函数
function Start-Phase1Cleanup {
    Write-Info "=== Flask后端清理 - 阶段1开始 ==="
    Write-Info "执行模式: $(if($DryRun){'模拟运行(不实际删除)'}else{'实际执行'})"
    
    # 检查当前目录
    if (-not (Test-Path "flask_backend")) {
        Write-Error "错误: 未找到flask_backend目录，请在项目根目录下运行此脚本"
        exit 1
    }
    
    # 1. 创建备份
    Create-Backup
    
    # 2. 删除备份文件
    Remove-BackupFiles
    
    # 3. 删除禁用文件
    Remove-DisabledFiles
    
    # 4. 移动测试文件
    Move-TestFiles
    
    # 5. 清理缓存
    Clean-CacheFiles
    
    # 6. 验证操作
    Verify-Phase1
    
    Write-Success "=== 阶段1清理完成 ==="
}

function Create-Backup {
    Write-Info "步骤1: 创建备份..."
    
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = ".\backup\flask_backend_$timestamp"
    
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
        Copy-Item -Recurse ".\flask_backend" "$backupPath\" -Force
        Write-Success "✅ 备份已创建: $backupPath"
    } else {
        Write-Info "🔍 [模拟] 将创建备份: $backupPath"
    }
}

function Remove-BackupFiles {
    Write-Info "步骤2: 删除备份文件..."
    
    $backupFiles = @(
        ".\flask_backend\core\step01_ppt_parser_backup.py",
        ".\flask_backend\app\api\workflow_backup.py"
    )
    
    foreach ($file in $backupFiles) {
        if (Test-Path $file) {
            if (-not $DryRun) {
                Remove-Item $file -Force
                Write-Success "✅ 已删除: $file"
            } else {
                Write-Info "🔍 [模拟] 将删除: $file"
            }
        } else {
            Write-Warning "⚠️ 文件不存在: $file"
        }
    }
}

function Remove-DisabledFiles {
    Write-Info "步骤3: 删除禁用文件..."
    
    $disabledFiles = Get-ChildItem -Path ".\flask_backend" -Recurse -Name "*.disabled"
    
    if ($disabledFiles.Count -eq 0) {
        Write-Warning "⚠️ 未找到.disabled文件"
        return
    }
    
    foreach ($file in $disabledFiles) {
        $fullPath = ".\flask_backend\$file"
        if (-not $DryRun) {
            Remove-Item $fullPath -Force
            Write-Success "✅ 已删除: $file"
        } else {
            Write-Info "🔍 [模拟] 将删除: $file"
        }
    }
}

function Move-TestFiles {
    Write-Info "步骤4: 移动测试文件..."
    
    $testFiles = @(
        ".\flask_backend\core\week10_integration_test.py",
        ".\flask_backend\core\audio_test_suite.py",
        ".\flask_backend\api\ai_config_test_api.py"
    )
    
    $tempDir = ".\temp\removed_test_files"
    
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    }
    
    foreach ($file in $testFiles) {
        if (Test-Path $file) {
            $fileName = Split-Path $file -Leaf
            $destPath = "$tempDir\$fileName"
            
            if (-not $DryRun) {
                Move-Item $file $destPath -Force
                Write-Success "✅ 已移动: $fileName -> temp/"
            } else {
                Write-Info "🔍 [模拟] 将移动: $fileName -> temp/"
            }
        } else {
            Write-Warning "⚠️ 文件不存在: $file"
        }
    }
}

function Clean-CacheFiles {
    Write-Info "步骤5: 清理缓存文件..."
    
    # 清理__pycache__目录
    $pycacheDirs = Get-ChildItem -Path ".\flask_backend" -Recurse -Directory -Name "__pycache__"
    
    foreach ($dir in $pycacheDirs) {
        $fullPath = ".\flask_backend\$dir"
        if (-not $DryRun) {
            Remove-Item $fullPath -Recurse -Force
            Write-Success "✅ 已删除缓存目录: $dir"
        } else {
            Write-Info "🔍 [模拟] 将删除缓存目录: $dir"
        }
    }
    
    # 清理.pyc文件
    $pycFiles = Get-ChildItem -Path ".\flask_backend" -Recurse -Name "*.pyc"
    
    foreach ($file in $pycFiles) {
        $fullPath = ".\flask_backend\$file"
        if (-not $DryRun) {
            Remove-Item $fullPath -Force
            Write-Success "✅ 已删除.pyc文件: $file"
        } else {
            Write-Info "🔍 [模拟] 将删除.pyc文件: $file"
        }
    }
}

function Verify-Phase1 {
    Write-Info "步骤6: 验证阶段1完成..."
    
    # 检查应用是否仍能启动
    Write-Info "测试应用启动..."
    
    try {
        if (-not $DryRun) {
            # 启动应用进行测试
            $job = Start-Job -ScriptBlock {
                Set-Location $using:PWD
                python .\flask_backend\unified_app.py
            }
            
            Start-Sleep -Seconds 5
            
            # 检查进程是否正在运行
            if ($job.State -eq "Running") {
                Write-Success "✅ 应用启动正常"
                Stop-Job $job
                Remove-Job $job
            } else {
                Write-Error "❌ 应用启动失败"
                Receive-Job $job
                Remove-Job $job
            }
        } else {
            Write-Info "🔍 [模拟] 应用启动测试"
        }
    } catch {
        Write-Error "❌ 应用测试过程中出现错误: $_"
    }
}

# 显示帮助信息
function Show-Help {
    Write-Info @"
Flask后端清理脚本 - 阶段1

用法:
    .\Phase1-Cleanup.ps1                # 实际执行清理
    .\Phase1-Cleanup.ps1 -DryRun        # 模拟运行（不实际删除）
    .\Phase1-Cleanup.ps1 -Verbose       # 详细输出模式

参数:
    -DryRun     模拟运行模式，不实际删除文件
    -Verbose    显示详细的执行信息
    -Help       显示此帮助信息

安全提示:
    1. 建议先使用-DryRun参数查看将要执行的操作
    2. 确保在项目根目录下运行此脚本
    3. 脚本会自动创建备份，但仍建议手动备份重要文件
"@
}

# 主执行逻辑
if ($args -contains "-Help" -or $args -contains "/?") {
    Show-Help
    exit 0
}

# 确认执行
if (-not $DryRun) {
    Write-Warning "⚠️ 即将执行阶段1清理操作，这将删除一些文件"
    $confirm = Read-Host "确认继续? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Info "操作已取消"
        exit 0
    }
}

# 执行清理
try {
    Start-Phase1Cleanup
} catch {
    Write-Error "执行过程中出现错误: $_"
    Write-Error "建议检查错误信息并从备份恢复"
    exit 1
}