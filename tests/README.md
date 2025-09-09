# 测试文件目录

这个目录包含项目的主要测试文件。

## 测试文件说明

### AI功能测试
- `test_ai_optimization_direct.py` - AI内容优化功能直接测试
- `test_ai_preprocessing_complete.py` - AI前置处理完整工作流测试
- `analyze_ai_result.py` - AI优化结果分析工具

## 运行测试

```bash
# 运行AI优化直接测试
python tests/test_ai_optimization_direct.py

# 运行完整工作流测试（需要Flask服务器运行）
python tests/test_ai_preprocessing_complete.py

# 分析AI优化结果
python tests/analyze_ai_result.py
```

## 测试说明

这些测试主要用于验证AI前置断句内容优化功能：
- 验证长句是否能被正确拆分为短句段
- 检查分段长度是否符合35字符限制
- 确认语义完整性和自然流畅度
- 测试多行字幕问题的解决效果
