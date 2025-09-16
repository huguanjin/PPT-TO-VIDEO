# 🚀 Flask后端清理 - 快速开始指南

## 📋 执行前检查清单

### ✅ 环境准备
- [ ] 确认在项目根目录 (`PPTist/ppt_to_video`)
- [ ] Flask应用当前可正常启动
- [ ] 已备份重要数据（可选，脚本会自动备份）
- [ ] 关闭正在运行的Flask服务

### ✅ Git准备（推荐）
```bash
# 提交当前状态
git add .
git commit -m "backup: 准备进行后端结构清理"
git tag "v1.0-before-cleanup"

# 创建清理分支
git checkout -b refactor/backend-cleanup
```

---

## 🎯 开始执行

### 第一步：模拟运行（安全检查）
```powershell
# 查看将要执行的操作（不实际删除文件）
.\scripts\Phase1-Cleanup.ps1 -DryRun
```

### 第二步：执行阶段1清理
```powershell
# 实际执行清理操作
.\scripts\Phase1-Cleanup.ps1
```

### 第三步：验证结果
```powershell
# 测试应用启动
python .\flask_backend\unified_app.py

# 在浏览器中访问
# http://localhost:5000/health
```

---

## 📊 阶段1清理内容

### 🗑️ 将被删除的文件
- `core/step01_ppt_parser_backup.py` - PPT解析器备份
- `app/api/workflow_backup.py` - 工作流API备份  
- `core/*.disabled` - 所有禁用文件
- `**/__pycache__/` - Python缓存目录
- `**/*.pyc` - Python编译文件

### 📦 将被移动的文件（保存到temp/）
- `core/week10_integration_test.py` - 集成测试
- `core/audio_test_suite.py` - 音频测试套件
- `api/ai_config_test_api.py` - AI配置测试API

### 🔒 不会被删除的文件
- 所有核心业务逻辑文件
- 配置文件
- 数据文件
- 日志文件

---

## ⚠️ 如果出现问题

### 快速回滚
```powershell
# 方法1: 使用Git回滚
git checkout v1.0-before-cleanup

# 方法2: 使用自动备份恢复
# 查找备份目录
Get-ChildItem .\backup\ | Sort-Object LastWriteTime -Descending

# 恢复备份（替换backup_timestamp为实际时间戳）
Remove-Item .\flask_backend -Recurse -Force
Copy-Item -Recurse .\backup\flask_backend_backup_timestamp\flask_backend .\
```

### 常见问题
1. **应用启动失败**: 检查是否有重要文件被误删，使用备份恢复
2. **权限错误**: 以管理员身份运行PowerShell
3. **路径错误**: 确保在项目根目录执行脚本

---

## 📈 预期收益

### 即时收益（阶段1完成后）
- ✅ 清理约10-15个无用文件
- ✅ 减少项目大小约5-10%
- ✅ 移除潜在的混淆代码
- ✅ 清理缓存文件

### 后续阶段
- **阶段2**: 目录重组（API、Utils合并）
- **阶段3**: 代码重构（配置管理器统一）

---

## 🔄 后续步骤

### 阶段1完成后
1. 测试所有核心功能
2. 提交阶段1的清理结果
3. 继续执行阶段2（如需要）

### 提交清理结果
```bash
git add .
git commit -m "clean: 完成阶段1清理 - 删除备份文件、禁用文件和测试文件"
```

---

## 📞 需要帮助？

### 执行过程中的问题
1. 记录具体的错误信息
2. 检查控制台输出的详细日志
3. 使用Git或备份恢复到清理前状态
4. 重新检查执行环境和权限

### 脚本选项
```powershell
# 查看帮助
.\scripts\Phase1-Cleanup.ps1 -Help

# 详细输出模式
.\scripts\Phase1-Cleanup.ps1 -Verbose

# 模拟运行
.\scripts\Phase1-Cleanup.ps1 -DryRun
```

---

**开始清理，让代码更简洁！** 🎉