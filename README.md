# PPT转视频工具 🎬

> 一个完整的PPT转视频工作流系统，集成了PPTist编辑器和智能视频生成功能

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/vue-3.0%2B-green.svg)](https://vuejs.org)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-red.svg)](https://flask.palletsprojects.com)

## ✨ 特性

- 🎨 **可视化编辑**: 集成PPTist在线编辑器，支持实时预览
- 🤖 **AI智能优化**: AI驱动的内容优化和智能字幕分割
- 🎵 **多引擎TTS**: 支持Edge TTS、Azure TTS、OpenAI TTS等多种语音合成
- 🎬 **专业视频**: Netflix级别字幕效果，支持多种转场动画  
- 🔄 **工作流管理**: 完整的任务管理和进度跟踪
- 📱 **响应式设计**: 支持桌面端和移动端访问

## 🏗️ 架构设计

```
PPT转视频系统
├── 📱 PPTist前端           # Vue 3 + TypeScript + Vite
│   ├── 编辑器界面          # 可视化PPT编辑
│   ├── AI配置面板         # AI服务配置管理
│   └── 项目管理           # 项目创建和管理
├── 🔧 Flask后端           # Python + Flask + SQLite
│   ├── 核心工作流         # PPT解析→TTS→视频生成
│   ├── AI集成服务         # OpenAI/Azure API集成
│   ├── 文件管理           # 上传下载和存储管理
│   └── 任务调度           # 异步任务和进度跟踪
└── 📊 配置系统            # 统一配置管理
    ├── AI服务配置         # API密钥和模型参数
    ├── 工作流配置         # 处理流程和质量设置
    └── 用户偏好设置       # 个性化配置选项
```

## 🚀 核心功能

### 1. PPT内容处理
- **多源导入**: PPTist在线编辑 + 本地PPT文件上传
- **智能解析**: 自动提取文本、图片、布局信息
- **内容优化**: AI驱动的文本优化和结构调整

### 2. 智能语音合成  
- **多引擎支持**: Edge TTS、Azure TTS、OpenAI TTS
- **语音定制**: 语言、语速、音调、情感控制
- **批量处理**: 并行合成，提升处理效率

### 3. 专业字幕系统
- **AI智能分割**: 基于语义的智能断句
- **Netflix级效果**: 专业字幕样式和动画
- **多语言支持**: 自动翻译和本地化

### 4. 视频生成引擎
- **高质量渲染**: 4K视频输出支持
- **转场动画**: 多种专业转场效果
- **音视频同步**: 精确的时间轴对齐

## 🛠️ 快速开始

### 📋 环境要求

- **Python**: 3.8+
- **Node.js**: 16+  
- **FFmpeg**: 最新版本
- **操作系统**: Windows/macOS/Linux

### 🚀 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/huguanjin/PPT-TO-VIDEO.git
cd PPT-TO-VIDEO

# 2. 后端环境设置
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
venv\Scripts\activate

# 3. 安装后端依赖
pip install -r requirements.txt

# 4. 前端环境设置
cd PPTist && npm install

# 5. 启动服务 (需要两个终端)
# 终端1 - 后端服务
cd flask_backend && python app.py

# 终端2 - 前端服务
cd PPTist && npm run dev
```

### 🌐 访问地址

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:5000  
- **API文档**: http://localhost:5000/docs

### ⚙️ 配置指南

1. **复制配置模板**:
   ```bash
   cp config_data/app_config_template.json config_data/app_config.json
   ```

2. **配置AI服务** (编辑 `config_data/app_config.json`):
   ```json
   {
     "ai_services": {
       "openai": {
         "api_key": "your-openai-key",
         "model": "gpt-4"
       }
     }
   }
   ```

## 📖 使用指南

### 1️⃣ 创建项目
- 新建PPT项目或导入现有文件
- 使用PPTist编辑器设计幻灯片
- 添加文本内容和图片资源

### 2️⃣ 配置参数  
- 设置AI服务和API密钥
- 选择TTS语音引擎和参数
- 配置字幕样式和动画效果

### 3️⃣ 生成视频
- 启动自动化工作流
- 实时监控处理进度
- 下载最终视频文件

## 🎯 核心亮点

### ✨ AI智能优化
- **智能断句**: AI驱动的语义分割，确保字幕自然流畅
- **内容优化**: 自动优化文本结构和表达方式
- **多语言支持**: 支持中英文等多种语言处理

### 🎬 专业视频制作
- **Netflix级字幕**: 专业级字幕样式和动画效果
- **高质量渲染**: 支持4K视频输出
- **精确同步**: 音视频完美对齐

### 🔄 工作流管理
- **任务队列**: 支持批量处理和队列管理
- **进度跟踪**: 实时显示处理进度和状态
- **断点续传**: 支持任务暂停和恢复

## 📁 项目结构

详细的项目结构和架构说明请参考: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 📚 文档

- [项目架构](PROJECT_STRUCTURE.md) - 详细的系统架构说明
- [API文档](docs/) - 后端API接口文档
- [开发指南](docs/开发环境启动指南.md) - 开发环境配置
- [部署指南](deploy/) - 生产环境部署

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
