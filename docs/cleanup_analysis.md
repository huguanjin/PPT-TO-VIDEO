# 项目根目录清理分析

## 可清理的文件分类

### 1. 测试脚本文件 (test_*.py)
- test_api_connection.py
- test_config_sync.py
- test_edge_optimized.py
- test_edge_tts.py
- test_edge_tts_direct.py
- test_edge_tts_simple.py
- test_edge_voices_api.py
- test_fish_voices_api.py
- test_preview_edge_tts.py
- test_simple_tts.py
- test_tts_config.py
- test_tts_preview_api.py
- test_venv_edge_tts.py

### 2. 临时音频文件 (test_*.wav)
- test_edge_fast.wav
- test_edge_low.wav
- test_edge_slow.wav
- test_edge_tts_yunyang.wav

### 3. 临时目录
- test_output/ (临时测试输出目录)

### 4. 需要保留的重要文件/目录
- PPTist/ (前端代码)
- flask_backend/ (后端代码)
- .git/ (Git版本控制)
- .github/ (GitHub配置)
- .vscode/ (IDE配置)
- venv/ (虚拟环境)
- logs/ (日志目录)
- output/ (输出目录)
- temp/ (临时目录)
- uploads/ (上传目录)
- README.md, README_EN.md (项目文档)
- requirements.txt (依赖配置)
- .gitignore (Git忽略配置)
- start_enhanced_demo.bat (启动脚本)
- *.md报告文件 (项目记录，可选择性保留)

## 清理建议
1. 删除所有test_*.py测试脚本
2. 删除所有test_*.wav音频文件
3. 删除test_output/目录
4. 可选：整理报告文件到单独的docs/目录
