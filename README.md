# PPT转视频教程工作流工具

一个基于Python和Streamlit的PPT转视频教程生成工具，支持自动化的PPT解析、语音合成、视频生成和字幕合并。

## 功能特性

- 📁 PPT文件解析和内容提取
- 🎙️ 多语音引擎TTS合成（支持edge-tts）
- 🎬 自动视频片段生成
- 📝 智能字幕生成和同步
- 🔄 断点续传和进度管理
- 🌐 友好的Web界面

## 快速开始

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\Activate.ps1  # Windows PowerShell
# 或
venv\Scripts\activate.bat  # Windows CMD

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行应用
```bash
streamlit run main.py
```

### 3. 使用流程
1. 上传PPT文件(.pptx格式)
2. 配置TTS和视频参数
3. 执行工作流生成视频
4. 预览和下载结果

## 项目结构

```
ppt_to_video_workflow/
├── main.py                      # Streamlit主应用
├── config/                      # 配置模块
├── core/                        # 核心业务逻辑
├── utils/                       # 工具模块
├── ui/                          # UI组件
├── tests/                       # 测试文件
├── output/                      # 输出目录
└── requirements.txt             # 项目依赖
```

## 依赖说明

- `streamlit`: Web应用框架
- `python-pptx`: PPT文件解析
- `edge-tts`: 语音合成
- `moviepy`: 视频处理
- `pillow`: 图像处理
- `pysrt`: 字幕文件处理

## 开发计划

- [✓] 项目结构搭建
- [✓] PPT解析模块
- [✓] TTS语音合成
- [✓] 视频生成模块
- [✓] 字幕生成模块
- [✓] 媒体合并模块
- [✓] Web界面完善

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
