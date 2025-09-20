# PPT转视频工具 - Netflix级专业视频制作平台 🎬

> 基于139个专业模块构建的企业级PPT转视频系统，集成Netflix V2标准、AI深度学习和Phase 3/4智能功能

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-red.svg)](https://flask.palletsprojects.com)
[![Netflix](https://img.shields.io/badge/standard-Netflix%20V2-red.svg)](docs/NETFLIX_SUBTITLE_IMPLEMENTATION_PLAN.md)
[![AI](https://img.shields.io/badge/AI-深度集成-brightgreen.svg)](docs/AI_FEATURES.md)

## 🌟 核心亮点

### � 业界领先技术
- **139个专业模块**: 企业级模块化架构，29个API接口 + 77个核心业务模块
- **Netflix V2标准**: 15个Netflix专业模块，达到流媒体行业标准
- **AI深度集成**: 8个AI处理模块，智能内容理解和优化
- **Phase 3/4功能**: 智能对齐、高级转场、实时预览等专业特性

### 🚀 技术架构优势
- **5种TTS引擎**: Edge TTS、Azure TTS、OpenAI TTS、Fish TTS、Custom TTS
- **智能配置系统**: 13个配置模块，AI驱动的自动优化
- **语义分割V2**: 智能理解语义边界，避免"cherry studio"等错误分割
- **毫秒级对齐**: Phase 3智能对齐系统，音视频精准同步

## 🏗️ 系统架构

```
PPT转视频专业平台 (139个模块)
├── 🌐 Flask后端 (139个Python模块)
│   ├── app/api/                    # 29个API接口模块
│   │   ├── 工作流API (7个)         # 增强工作流、批量处理、智能对齐
│   │   ├── TTS音频API (6个)        # 5种引擎、情感语音、统一接口
│   │   ├── Netflix字幕API (5个)    # Netflix V2标准、语义分割
│   │   ├── 视频处理API (4个)       # 高级特效、实时预览、多格式导出
│   │   ├── PPTist集成API (3个)     # 无缝对接、数据导入导出
│   │   └── 配置管理API (4个)       # AI配置、用户偏好、智能优化
│   ├── core/                       # 77个核心业务模块
│   │   ├── Netflix专业 (15个)      # V2字幕生成、语义分割、质量验证
│   │   ├── 配置管理 (13个)         # 智能配置、迁移工具、性能优化
│   │   ├── 增强功能 (12个)         # AI内容优化、智能分析
│   │   ├── AI处理 (8个)            # 内容理解、语义分析、智能优化
│   │   ├── 基础工作流 (6个)        # PPT解析、TTS、视频、字幕、合并
│   │   ├── Phase 4任务 (4个)       # 实时预览、转场引擎、音频处理
│   │   ├── 智能对齐 (3个)          # Phase 3音视频智能同步
│   │   └── 工具算法 (16个)         # NLP、算法库、性能基准
│   ├── all_tts_functions/          # 5种TTS引擎
│   │   ├── edge_tts.py            # Edge TTS (免费高质量)
│   │   ├── azure_tts.py           # Azure TTS (企业级)
│   │   ├── fish_tts.py            # Fish TTS (技术领先)
│   │   ├── openai_tts.py          # OpenAI TTS (AI驱动)
│   │   └── custom_tts.py          # 自定义TTS引擎
│   └── utils/                      # 7个全局工具模块
├── � PPTist前端
│   ├── 可视化编辑器                # Vue 3 + TypeScript + Vite
│   ├── Netflix级预览              # 专业级实时预览
│   └── AI配置面板                # 智能参数配置
└── ⚙️ 智能配置系统
    ├── Netflix V2配置             # 专业字幕标准配置
    ├── AI服务配置                 # 多模型参数优化
    └── Phase 3/4功能配置          # 高级功能参数
```

## 🎯 核心功能特性

### 1. Netflix级字幕系统 ⭐
- **语义分割V2**: 智能语义边界识别，避免词汇错误分割
- **字符权重计算**: 精确字符显示权重，优化阅读体验
- **质量验证体系**: 多层次质量检查，确保Netflix标准
- **样式预设系统**: 专业字幕样式模板，电影级视觉效果

### 2. AI智能处理引擎 🤖
- **内容理解**: 8个AI模块深度分析PPT内容语义
- **智能优化**: AI驱动的文本优化和结构调整
- **配置自动化**: 基于使用模式的智能配置优化
- **语义对齐**: 基于内容语义的智能字幕对齐

### 3. 多引擎TTS系统 🎵
- **5种专业引擎**: Edge TTS、Azure、OpenAI、Fish TTS、Custom
- **情感语音合成**: 支持情感化语音表达
- **统一接口管理**: 智能引擎选择和参数优化
- **高质量输出**: 专业级语音质量，支持多语言

### 4. Phase 3/4高级功能 🚀
- **智能对齐系统**: 毫秒级音视频智能同步
- **实时预览**: Phase 3实时预览，所见即所得
- **高级转场引擎**: Phase 4专业转场特效
- **智能音频处理**: 高级音频优化和同步

### 5. 企业级工作流 🔄
- **批量处理**: 支持多文件并行处理
- **断点续传**: 智能任务恢复和进度跟踪
- **质量保证**: 多层次质量验证和错误处理
- **性能监控**: 完整的APM监控和优化建议

## 📊 技术指标

| 功能模块 | 技术指标 | 行业对比 |
|----------|----------|----------|
| **字幕质量** | Netflix V2标准 | 🥇 行业领先 |
| **语音合成** | 5种引擎、毫秒延迟 | 🥇 技术领先 |
| **AI集成** | 8个AI模块深度集成 | 🥇 业界少见 |
| **模块化** | 139个专业模块 | 🥇 极致模块化 |
| **对齐精度** | 毫秒级智能对齐 | 🥇 专业级精度 |
| **处理速度** | 并行处理、异步优化 | 🥈 行业先进 |

## 🛠️ 快速开始

### 📋 系统要求

```bash
# 运行环境
Python 3.8+              # 后端运行环境
Node.js 16+               # 前端构建环境  
FFmpeg 最新版             # 视频处理引擎
Redis (可选)              # 任务队列和缓存

# 硬件建议
内存: 8GB+                # 处理大型PPT文件
存储: 50GB+               # 视频文件存储空间
CPU: 4核心+               # 并行处理性能
GPU: 支持硬件加速 (可选)   # 视频渲染加速
```

### 🚀 一键启动 (推荐方式)

```bash
# 1. 克隆项目
git clone https://github.com/huguanjin/PPT-TO-VIDEO.git
cd ppt_to_video

# 2. 环境初始化
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动统一Flask后端 (推荐)
python flask_backend/unified_app.py
# 🌐 Web界面: http://localhost:5000
# 📱 PPTist编辑器: http://localhost:5000/pptist
# 🔗 API文档: http://localhost:5000/api/docs

# 5. 备选启动方式
# 方式1: Streamlit界面
streamlit run main.py

# 方式2: 分离式启动
# 终端1: cd flask_backend && python app.py  
# 终端2: cd PPTist && npm run dev
```

### ⚙️ 配置系统

#### AI服务配置
```bash
# 编辑配置文件
config_data/app_config.json

{
  "ai_services": {
    "openai": {
      "api_key": "your-openai-key",
      "model": "gpt-4o"
    },
    "azure": {
      "api_key": "your-azure-key", 
      "endpoint": "your-endpoint"
    }
  },
  "tts_engines": {
    "edge_tts": { "enabled": true },
    "azure_tts": { "enabled": true },
    "fish_tts": { "enabled": true }
  },
  "netflix_v2": {
    "enabled": true,
    "semantic_splitting": true,
    "quality_validation": true
  }
}
```

#### Netflix V2专业配置
```bash
# Netflix级字幕配置
config_data/netflix_v2_config.json

{
  "subtitle_engine": {
    "semantic_splitting_v2": true,
    "char_weight_calculation": true,
    "quality_validation": true,
    "style_presets": "professional"
  },
  "quality_standards": {
    "min_duration": 1.0,
    "max_duration": 7.0,
    "optimal_chars_per_line": 42,
    "reading_speed_cps": 17
  }
}
```

### � 使用指南

#### 基础使用流程
1. **创建项目**: 在Web界面创建新的PPT转视频项目
2. **内容导入**: 上传PPT文件或使用PPTist在线编辑
3. **AI配置**: 选择TTS引擎和字幕生成策略
4. **一键生成**: 启动智能工作流，自动完成转换
5. **结果下载**: 下载生成的高质量视频文件

#### Netflix V2专业模式
```bash
# 启用Netflix V2增强功能
{
  "advanced_features": {
    "enhanced_subtitles": {
      "use_enhanced": true,
      "enable_netflix_v2": true
    }
  }
}
```

#### Phase 3/4高级功能
```bash
# 启用智能对齐和高级功能
{
  "phase3_features": {
    "intelligent_alignment": true,
    "audio_sync_optimization": true,
    "semantic_alignment": true
  },
  "phase4_features": {
    "real_time_preview": true,
    "advanced_transitions": true,
    "smart_content_analysis": true
  }
}
```

## 📚 文档与支持

### 📖 技术文档
- [📊 Flask后端架构分析](docs/FLASK_BACKEND_STRUCTURE_ANALYSIS.md)
- [🎬 Netflix字幕实现计划](docs/NETFLIX_SUBTITLE_IMPLEMENTATION_PLAN.md)
- [🤖 AI功能深度集成](docs/AI_FEATURES.md)
- [🔧 配置管理指南](docs/CONFIG_MANAGEMENT.md)
- [🚀 Phase 3/4功能指南](docs/PHASE_FEATURES.md)

### 🛠️ 开发资源
- [🌐 API接口文档](docs/API_DOCUMENTATION.md)
- [🧩 模块开发指南](docs/MODULE_DEVELOPMENT.md)
- [🔍 测试与调试](docs/TESTING_GUIDE.md)
- [📦 部署指南](docs/DEPLOYMENT_GUIDE.md)

### 💡 使用案例
- [🎓 教育培训视频制作](docs/EDUCATION_USE_CASES.md)
- [📢 企业宣传视频](docs/BUSINESS_USE_CASES.md)
- [📱 社交媒体内容](docs/SOCIAL_MEDIA_GUIDE.md)

## 🤝 贡献指南

我们欢迎社区贡献！请参考：

- [🔧 贡献指南](CONTRIBUTING.md)
- [🐛 问题报告](ISSUE_TEMPLATE.md)
- [💻 代码规范](CODE_STYLE.md)

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🎉 致谢

感谢以下优秀的开源项目：

- [PPTist](https://github.com/pipipi-pikachu/PPTist) - PPT在线编辑器
- [Flask](https://flask.palletsprojects.com/) - Web应用框架
- [MoviePy](https://zulko.github.io/moviepy/) - 视频处理库
- [Edge TTS](https://github.com/rany2/edge-tts) - 免费TTS服务

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

[![Star History Chart](https://api.star-history.com/svg?repos=huguanjin/PPT-TO-VIDEO&type=Date)](https://star-history.com/#huguanjin/PPT-TO-VIDEO&Date)
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
