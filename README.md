# PPT转视频工具 🎬

> 专业级PPT转视频工作流系统，集成Netflix级AI字幕技术和多引擎语音合成

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/vue-3.0%2B-green.svg)](https://vuejs.org)
[![Flask](https://img.shields.io/badge/flask-2.3%2B-red.svg)](https://flask.palletsprojects.com)
[![AI](https://img.shields.io/badge/AI-Netflix级字幕-purple.svg)](#)

## ✨ 核心特性

### � **Netflix级字幕技术**
- **AI语义分割**: 基于spaCy和Transformer模型的智能断句
- **专业质量监控**: 实时字幕质量评估和自动优化
- **精确时间对齐**: DTW算法驱动的音频智能同步

### 🤖 **AI智能处理**
- **多AI服务支持**: OpenAI GPT-4、Claude 3、自定义API
- **智能内容优化**: AI驱动的文本结构优化和语义增强
- **自适应配置**: 基于内容类型的智能参数调整

### 🎵 **多引擎语音合成**
- **Edge TTS**: 微软云端语音合成，支持多语言多音色
- **Fish Speech**: 高质量AI语音克隆技术
- **OpenAI TTS**: 先进的神经网络语音生成
- **Azure Cognitive**: 企业级语音服务

### � **专业视频制作**
- **4K高质量输出**: 支持多种分辨率和编码格式
- **智能转场动画**: AI驱动的场景过渡效果
- **精确音视频同步**: 毫秒级时间轴对齐技术

### 🔧 **现代化架构**
- **Flask工厂模式**: 支持多环境配置的现代Web架构
- **异步任务处理**: 支持长时间任务的断点续传
- **模块化设计**: 60+ 核心模块，高度可扩展
- **实时监控**: 完善的性能监控和错误追踪

## 🏗️ 技术架构

```
PPT转视频系统 (企业级架构)
├── 🎨 前端层 (PPTist + Streamlit)
│   ├── PPTist编辑器       # Vue 3 + TypeScript + Vite
│   ├── Streamlit界面      # Python + Streamlit UI
│   └── 配置管理面板       # 实时配置和监控
├── 🚀 API网关层 (Flask Backend)
│   ├── 统一Flask后端      # unified_app.py (主入口)
│   ├── RESTful API       # 25+ 标准化API端点
│   ├── 工作流管理        # enhanced_workflow.py
│   └── 实时预览          # WebSocket支持
├── 🧠 AI处理层 (Core Modules)
│   ├── Netflix字幕系统   # netflix_*.py (8个模块)
│   ├── 智能音频对齐      # DTW + librosa算法
│   ├── AI内容优化        # GPT-4/Claude集成
│   └── 语义分析处理      # spaCy + Transformers
├── 🔄 工作流引擎
│   ├── Step 1: PPT解析   # python-pptx + 图像处理
│   ├── Step 2: TTS合成   # 多引擎语音生成
│   ├── Step 3: 视频生成  # moviepy + OpenCV
│   ├── Step 4: 字幕处理  # Netflix级智能字幕
│   └── Step 5: 最终合成  # FFmpeg高质量输出
└── 📊 基础设施层
    ├── 配置管理          # 环境配置 + API密钥管理
    ├── 任务调度          # 异步任务 + 进度跟踪
    ├── 文件存储          # 分类存储 + 缓存管理
    └── 监控日志          # 实时监控 + 错误追踪
```

## 🎯 核心优势

### 🏆 **技术领先性**
| 维度 | 技术水平 | 说明 |
|------|----------|------|
| **AI字幕技术** | 业界领先 | Netflix级别专业字幕生成系统 |
| **音频对齐** | 先进算法 | DTW + 特征提取的毫秒级精度 |
| **架构设计** | 企业级 | 现代Flask + 模块化 + 可扩展 |
| **工程质量** | 生产就绪 | 完善日志 + 错误处理 + 监控 |

### ⚡ **性能特点**
- **并发处理**: 最大5个并发任务，智能资源调度
- **断点续传**: 支持大型项目的可靠处理和恢复
- **内存优化**: 实时内存监控和自动释放机制
- **缓存机制**: 智能缓存策略，提升处理效率
- **AI智能分割**: 基于语义的智能断句
- **Netflix级效果**: 专业字幕样式和动画
- **多语言支持**: 自动翻译和本地化

### 4. 视频生成引擎
- **高质量渲染**: 4K视频输出支持
- **转场动画**: 多种专业转场效果
- **音视频同步**: 精确的时间轴对齐

## 🛠️ 快速启动

### 📋 系统要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| **Python** | 3.8+ | 推荐 3.10+ |
| **Node.js** | 16+ | PPTist前端需要 |
| **FFmpeg** | 最新版 | 视频处理必需 |
| **内存** | 8GB+ | 推荐 16GB+ |
| **存储** | 10GB+ | 用于模型和缓存 |

### 🚀 一键部署

#### 推荐启动方式 (统一Flask后端)
```bash
# 1. 环境准备
git clone https://github.com/huguanjin/PPT-TO-VIDEO.git
cd PPT-TO-VIDEO
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装spaCy中文模型
python -m spacy download zh_core_web_sm
python -m spacy download zh_core_web_md

# 4. 配置API密钥
cp flask_backend/config_data/app_config_template.json flask_backend/config_data/app_config.json
# 编辑 app_config.json，填入真实API密钥

# 5. 启动统一后端服务
python flask_backend/unified_app.py
```

#### Vue前端启动
```bash
# 终端2 - Vue前端  
cd PPTist
npm install && npm run dev
浏览器访问 http://localhost:5173
```

### 🌐 访问地址

| 服务 | 地址 | 功能 |
|------|------|------|
| **统一Flask后端** | http://localhost:5000 | 主要业务API |
| **PPTist编辑器** | http://localhost:5173 | PPT在线编辑 |
| **API健康检查** | http://localhost:5000/health | 服务状态监控 |
| **实时预览** | http://localhost:5000/api/real_time_preview | 实时预览功能 |

### ⚙️ 配置指南

#### 1. API密钥配置
编辑 `flask_backend/config_data/app_config.json`:

```json
{
  "ai": {
    "custom": {
      "api_key": "your-custom-api-key-here",
      "base_url": "https://your-api-endpoint.com/v1",
      "model": "gemini-2.0-flash"
    }
  },
  "tts": {
    "fish_api_key": "your-fish-speech-key-here",
    "preferred_engine": "edge_tts"
  }
}
```

#### 2. 高级配置选项
```json
{
  "netflix_v2": {
    "enabled": true,
    "max_chars_per_line": 36,
    "quality_threshold": 0.7
  },
  "phase3_intelligent_alignment": {
    "enabled": true,
    "precision_level": "enhanced"
  }
}
```

## 📖 使用指南

### 🎯 工作流程

#### 1️⃣ **项目初始化**
```bash
# 启动统一后端服务
python flask_backend/unified_app.py

# 访问Streamlit界面进行操作
streamlit run main.py
```

#### 2️⃣ **内容导入**
- **PPT文件上传**: 支持 .pptx 格式文件直接导入
- **PPTist编辑**: 在线可视化编辑器创建内容
- **文本输入**: 直接输入或粘贴文本内容

#### 3️⃣ **AI配置**
- **选择AI服务**: OpenAI GPT-4、Claude 3、自定义API
- **TTS引擎设置**: Edge TTS、Fish Speech、OpenAI TTS
- **字幕样式**: Netflix级字幕效果配置

#### 4️⃣ **智能处理**
- **AI内容优化**: 自动优化文本结构和表达
- **语音合成**: 多引擎并行处理
- **字幕生成**: Netflix级智能断句和时间对齐
- **视频合成**: 高质量视频输出

#### 5️⃣ **质量监控**
- **实时进度**: 工作流处理进度实时显示
- **质量评估**: 自动字幕质量检测和优化
- **错误恢复**: 支持断点续传和错误重试

## � 核心亮点

### ✨ **Netflix级AI字幕系统**
```python
# 智能字幕分割示例
{
  "netflix_v2": {
    "enabled": true,
    "style_preset": "videolingo_netflix",
    "max_chars_per_line": 36,
    "validation_level": "netflix",
    "chinese_weight": 1.75,
    "quality_threshold": 0.7
  }
}
```
- **AI语义理解**: 基于spaCy和Transformer的深度语义分析
- **专业断句算法**: 动态规划优化的句子分割
- **实时质量监控**: Netflix级别字幕质量标准验证

### � **多引擎TTS集成**
```python
# 支持的TTS引擎
{
  "edge_tts": "微软云端高质量语音",
  "fish_speech": "AI语音克隆技术", 
  "openai_tts": "神经网络语音生成",
  "azure_tts": "企业级语音服务"
}
```

### 🔧 **企业级架构特点**
- **高并发**: 支持5个并发任务处理
- **容错性**: 完善的错误处理和自动恢复
- **监控体系**: 实时性能监控和日志追踪
- **扩展性**: 模块化设计，支持功能扩展

## � 性能指标

| 指标 | 性能表现 | 说明 |
|------|----------|------|
| **字幕准确率** | >95% | Netflix级别质量标准 |
| **音频对齐精度** | <50ms | DTW算法毫秒级对齐 |
| **处理速度** | 1-5x实时 | 根据硬件配置变化 |
| **并发任务** | 5个任务 | 智能资源调度 |
| **支持格式** | 10+种 | 主流视频音频格式 |

## 🔧 高级功能

### Phase 3: 智能音频对齐
```json
{
  "phase3_intelligent_alignment": {
    "enabled": true,
    "precision_level": "enhanced",
    "dtw_algorithm": true,
    "audio_feature_extraction": true
  }
}
```

### AI内容理解与优化
```json
{
  "ai_content_understanding": {
    "enabled": true,
    "semantic_analysis": true,
    "intelligent_splitting": true,
    "transformer_models": true
  }
}
```

## 📁 项目结构

```
PPT-TO-VIDEO/
├── 📱 前端界面
│   ├── main.py                    # Streamlit主界面
│   ├── PPTist/                    # Vue.js编辑器
│   └── ui/                        # UI组件库
├── 🚀 Flask后端 (企业级架构)
│   ├── unified_app.py            # ✅ 统一后端入口
│   ├── app/                      # Flask应用 (工厂模式)
│   │   ├── api/                 # 25+ RESTful API端点
│   │   ├── utils/               # 核心工具模块
│   │   └── __init__.py          # 应用工厂
│   ├── core/                    # 60+ 核心处理模块
│   │   ├── enhanced_workflow_executor.py  # 增强工作流
│   │   ├── netflix_*.py         # Netflix级字幕系统 (8个模块)
│   │   ├── step01_*.py          # PPT解析处理
│   │   ├── step02_*.py          # TTS语音合成
│   │   ├── step03_*.py          # 视频生成
│   │   ├── step04_*.py          # 智能字幕处理
│   │   └── step05_*.py          # 最终合成
│   ├── config/                  # 配置管理
│   └── config_data/             # 配置文件存储
├── 📚 文档和配置
│   ├── docs/                    # 详细文档
│   │   ├── FLASK_BACKEND_STRUCTURE_ANALYSIS.md  # 后端架构分析
│   │   └── README.md
│   ├── requirements.txt         # 统一依赖管理
│   └── .gitignore              # Git忽略规则
└── 🔧 部署和工具
    ├── deploy/                  # 部署脚本
    ├── logs/                    # 日志文件
    └── output/                  # 输出文件
```

详细的项目结构和架构分析请参考：
- [Flask后端结构分析](docs/FLASK_BACKEND_STRUCTURE_ANALYSIS.md) - 完整的后端架构分析
- [前端API分析](docs/FRONTEND_API_ANALYSIS.md) - API接口文档


## 🔧 开发指南

### 环境配置
```bash
# 开发环境安装
pip install -r requirements.txt
python -m spacy download zh_core_web_sm
python -m spacy download zh_core_web_md

# 配置API密钥
cp flask_backend/config_data/app_config_template.json flask_backend/config_data/app_config.json
```

### 调试模式
```bash
# Flask调试模式
export FLASK_ENV=development
python flask_backend/unified_app.py

# Streamlit调试模式
streamlit run main.py --logger.level=debug
```

### 测试运行
```bash
# 运行单元测试
pytest flask_backend/tests/

# API健康检查
curl http://localhost:5000/health
```

## 📚 文档资源

| 文档类型 | 链接 | 内容 |
|----------|------|------|
| **架构分析** | [FLASK_BACKEND_STRUCTURE_ANALYSIS.md](docs/FLASK_BACKEND_STRUCTURE_ANALYSIS.md) | 完整后端架构分析 |
| **API文档** | [FRONTEND_API_ANALYSIS.md](docs/FRONTEND_API_ANALYSIS.md) | API接口详细说明 |
| **配置说明** | [flask_backend/config_data/README.md](flask_backend/config_data/README.md) | 配置文件使用指南 |
| **部署指南** | [deploy/README.md](deploy/README.md) | 生产环境部署 |

## ⚠️ 重要提醒

### 🔐 API密钥安全
```bash
# ❌ 错误：直接使用模板文件
python flask_backend/unified_app.py  # 会提示配置文件不存在

# ✅ 正确：复制并配置密钥
cp flask_backend/config_data/app_config_template.json flask_backend/config_data/app_config.json
# 编辑 app_config.json 填入真实API密钥
python flask_backend/unified_app.py  # 正常启动
```

### 📋 系统要求检查
- **Python版本**: 确保使用 Python 3.8+
- **spaCy模型**: 必须安装中文语言模型
- **FFmpeg**: 视频处理必需组件
- **内存要求**: 推荐 16GB+ 用于AI模型处理

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
