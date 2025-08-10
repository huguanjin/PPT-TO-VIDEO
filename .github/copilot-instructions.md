<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# PPT转视频工作流项目 - GitHub Copilot 指令

## 项目概述
这是一个PPT转视频教程生成工具，使用Python和Streamlit开发，包含模块化的工作流处理步骤。

## 代码规范
- 使用Python类型提示和dataclass
- 采用异步编程模式处理长时间任务
- 遵循模块化设计原则
- 包含完整的错误处理和日志记录

## 核心模块
- `core/`: 核心业务逻辑，每个步骤独立文件
- `utils/`: 通用工具模块
- `ui/`: Streamlit界面组件
- `config/`: 配置管理

## 技术栈
- Streamlit: Web应用框架
- python-pptx: PPT文件解析
- edge-tts: 语音合成
- moviepy: 视频处理
- pysrt: 字幕处理

## 开发重点
- 支持断点续传和进度跟踪
- 文件结构化存储和元数据管理
- 异步任务处理和进度回调
- 用户友好的Web界面
