# PPT转视频工具

这是一个将PowerPoint演示文稿转换为视频的综合工具，支持AI智能字幕优化功能。

## 项目结构

```
├── PPTist/              # 前端项目 (Vue 3 + TypeScript)
├── flask_backend/       # Flask后端API服务
├── config_data/         # 配置文件目录
├── deploy/             # 部署脚本
├── docs/               # 项目文档
├── tests/              # 测试文件
├── logs/               # 日志文件
├── output/             # 输出文件
├── temp/               # 临时文件
├── uploads/            # 上传文件
├── venv/               # Python虚拟环境
└── requirements.txt    # Python依赖
```

## 核心功能

- **PPT解析**: 支持PPTist导入和本地PPT文件解析
- **TTS语音合成**: 支持多种TTS引擎（Edge TTS、OpenAI TTS、Fish TTS等）
- **AI智能字幕**: AI前置断句内容优化，解决多行字幕问题
- **视频生成**: 自动合成音频、字幕和视频
- **智能配置**: 支持Netflix级别字幕配置和AI参数调优

## 快速开始

### 启动后端服务
```bash
cd flask_backend
python app.py
```

### 启动前端开发服务器
```bash
cd PPTist
npm run dev
```

## 主要特性

### AI前置断句内容优化 ✨
- 智能将长句拆分为短句段
- 精确控制每段字符数（推荐35字符以内）
- 保持语义完整性和自然流畅度
- 有效解决多行字幕显示问题

### Netflix级别字幕配置
- 专业字幕样式和布局
- 精确时间对齐
- 智能间隙填充
- 自动标点处理

## 更多信息

详细文档请查看 `docs/` 目录。
