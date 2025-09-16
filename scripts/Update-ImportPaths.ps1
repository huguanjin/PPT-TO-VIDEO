# 批量更新导入路径脚本
param(
    [string]$RootPath = "flask_backend"
)

# 定义替换规则
$replacements = @{
    "from utils.logger import" = "from app.utils.logger import"
    "from utils.file_manager import" = "from app.utils.file_manager import"
    "from utils.config_manager import" = "from app.utils.config_manager import"
    "from utils.progress_tracker import" = "from app.utils.progress_tracker import"
    "from utils.task_manager import" = "from app.utils.task_manager import"
}

# 获取所有Python文件
$pythonFiles = Get-ChildItem -Path $RootPath -Recurse -Filter "*.py"

Write-Host "开始更新导入路径..."
Write-Host "找到 $($pythonFiles.Count) 个Python文件"

foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $originalContent = $content
    $changed = $false
    
    foreach ($pattern in $replacements.Keys) {
        $replacement = $replacements[$pattern]
        if ($content -match [regex]::Escape($pattern)) {
            $content = $content -replace [regex]::Escape($pattern), $replacement
            $changed = $true
        }
    }
    
    if ($changed) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
        Write-Host "✅ 已更新: $($file.FullName)"
    }
}

Write-Host "导入路径更新完成!"