<div align="center">

# 🎬 PPT转视频工具

### 专业级 PPT 转视频工作流系统

**智能字幕 · 多引擎语音合成 · 高质量视频输出**

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.8%2B-blue.svg" alt="Python"></a>
  <a href="https://vuejs.org"><img src="https://img.shields.io/badge/vue-3.0%2B-green.svg" alt="Vue"></a>
  <a href="https://flask.palletsprojects.com"><img src="https://img.shields.io/badge/flask-2.3%2B-red.svg" alt="Flask"></a>
  <img src="https://img.shields.io/badge/MongoDB-4.6%2B-brightgreen.svg" alt="MongoDB">
</p>

### 💬 加入交流群

<table>
<tr>
<td align="center">
  <img src="https://img.shields.io/badge/QQ群-881220679-orange.svg" alt="QQ群"><br>
  <img width="200" alt="QQ群二维码" src="https://github.com/user-attachments/assets/99f367bb-89de-4013-93e6-ba2beec7d275" /><br>
  <strong>欢迎加入讨论、反馈问题、分享经验!</strong>
</td>
</tr>
</table>

</div>

---

## 🎥 Demo 展示

<div align="center">
<table>
<tr>
<td width="33%" align="center">

### 📽️ 项目介绍
https://github.com/user-attachments/assets/69754252-9fbd-4f5b-94c7-64151462fa32

</td>
<td width="33%" align="center">

### 🎵 Edge TTS 配音示例
https://github.com/user-attachments/assets/05e070a9-9341-4292-8f26-4b5bd672db75

</td>
<td width="33%" align="center">

### 🐟 FishTTS 配音示例
https://github.com/user-attachments/assets/12c26839-078c-4d98-a0db-1e4d4819e336

</td>
</tr>
</table>
</div>

---

## ✨ 核心特性

<table>
<tr>
<td width="50%">

### 🧠 智能处理
- ✅ **智能断句**: 基于语义的字幕分割
- ✅ **单行字幕模式**: 优化显示和时间分配
- ✅ **精确时间对齐**: 毫秒级字幕时间轴
- ✅ **自适应字体**: 根据内容自动调整大小
- ✅ **手动换行支持**: 灵活的分割控制

</td>
<td width="50%">

### 🎵 多引擎语音合成
- 🎤 **Edge TTS**: 微软云端高质量语音
- 🐟 **Fish Speech**: AI 语音克隆技术
- 🤖 **OpenAI TTS**: 神经网络语音生成
- ☁️ **Azure TTS**: 企业级语音服务

</td>
</tr>
<tr>
<td width="50%">

### 🎬 专业视频制作
- 📹 **高质量输出**: 支持多种分辨率
- 🎯 **精确同步**: 音视频毫秒级对齐
- 📝 **专业字幕**: Netflix 风格渲染

</td>
<td width="50%">

### 🏗️ 现代化架构
- 🔧 **Flask 工厂模式**: 模块化设计
- 🗄️ **MongoDB 存储**: 用户数据持久化
- 🔐 **JWT 认证**: 安全的用户系统
- 📊 **实时监控**: 任务进度追踪

</td>
</tr>
</table>

---

## 🛠️ 快速启动

### 📋 系统要求

| 组件 | 版本要求 | 说明 |
|:----:|:--------:|:-----|
| 🐍 Python | 3.8+ | 推荐 3.10+ |
| 📦 Node.js | 16+ | PPTist 前端需要 |
| 🎬 FFmpeg | 最新版 | 视频处理必需 |
| 🗄️ MongoDB | 4.6+ | 数据存储 |
| 💾 内存 | 8GB+ | 推荐 16GB+ |

### 🚀 安装步骤

#### 1️⃣ 克隆项目

```bash
git clone https://github.com/huguanjin/PPT-TO-VIDEO.git
cd PPT-TO-VIDEO
```

#### 2️⃣ 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt

# 安装中文语言模型
python -m spacy download zh_core_web_md
```

#### 4️⃣ 配置文件

```bash
# 复制配置模板
cp flask_backend/config_data/app_config_template.json flask_backend/config_data/app_config.json
cp flask_backend/mongo_config.template.yaml flask_backend/mongo_config.yaml

# 编辑配置文件，填入真实 API 密钥和数据库连接信息
```

#### 5️⃣ 启动服务

**终端 1 - Flask 后端**
```bash
python flask_backend/unified_app.py
```

**终端 2 - Vue 前端**
```bash
cd PPTist
npm install
npm run dev
```

### 🌐 访问地址

| 服务 | 地址 | 功能 |
|:----:|:----:|:-----|
| 🔧 Flask 后端 | http://localhost:5000 | API 服务 |
| 🎨 PPTist 编辑器 | http://localhost:5173 | PPT 在线编辑 |
| ✅ 健康检查 | http://localhost:5000/health | 服务状态 |

---

## ⚙️ 配置指南

### 🔑 API 密钥配置

编辑 `flask_backend/config_data/app_config.json`:

```json
{
  "ai": {
    "custom": {
      "api_key": "your-api-key",
      "base_url": "https://your-api-endpoint.com/v1",
      "model": "gpt-4o-mini"
    }
  },
  "tts": {
    "fish_api_key": "your-fish-speech-key",
    "preferred_engine": "edge_tts"
  }
}
```

### 🗄️ MongoDB 配置

编辑 `flask_backend/mongo_config.yaml`:

```yaml
mongodb:
  # 本地 MongoDB
  connection_string: "mongodb://localhost:27017/"
  database_name: "PPTTOVideo"
  
  # 或使用 MongoDB Atlas
  # connection_string: "mongodb+srv://user:pass@cluster.mongodb.net/"
```

### 🔑 推荐 AI 模型提供商

| 推荐模型 | 提供商 | 价格 |
|:--------|:------|:-----|
| claude-sonnet-4-5 | [xiaohumini.site](https://xiaohumini.site) | 0.8元/刀 |
| claude-sonnet-4-5 | [xiaohuapi.site](https://xiaohuapi.site) | 0.48元/刀 |
| claude-sonnet-4-5 | [aifast.site](https://aifast.site) | 0.4元/刀 |

---

## 📖 使用流程

<div align="center">
<table>
<tr>
<td width="20%" align="center">

### 1️⃣ 编辑 PPT
在 PPTist 中<br>
创建/导入演示文稿

</td>
<td width="20%" align="center">

### 2️⃣ 添加配音稿
为每页幻灯片<br>
添加解说词

</td>
<td width="20%" align="center">

### 3️⃣ 选择配置
选择 TTS 引擎<br>
和字幕样式

</td>
<td width="20%" align="center">

### 4️⃣ 生成视频
一键生成<br>
高质量视频

</td>
<td width="20%" align="center">

### 5️⃣ 下载成品
预览并下载<br>
最终视频

</td>
</tr>
</table>
</div>

---

## 📊 性能指标

| 指标 | 性能表现 | 说明 |
|:----:|:--------:|:-----|
| 🎯 字幕准确率 | >90% | 智能断句 + 精确对齐 |
| ⏱️ 音频对齐精度 | <100ms | 毫秒级时间轴 |
| ⚡ 处理速度 | 1-3x 实时 | 根据硬件配置 |
| 🔄 并发任务 | 5 个 | 智能资源调度 |

---

## 📁 项目结构

```
PPT-TO-VIDEO/
├── flask_backend/          # Flask 后端服务
│   ├── app/               # 应用核心模块
│   │   ├── api/          # API 路由
│   │   ├── auth/         # 认证模块
│   │   ├── database/     # 数据库连接
│   │   └── services/     # 业务服务
│   ├── core/             # 核心处理模块
│   │   ├── step01_*      # PPT 图片导出
│   │   ├── step02_*      # TTS 音频生成
│   │   ├── step03_*      # 视频片段合成
│   │   ├── step04_*      # 字幕生成
│   │   └── step05_*      # 最终合并
│   ├── config_data/      # 配置文件
│   ├── all_tts_functions/ # TTS 引擎集成
│   └── unified_app.py    # 统一入口
├── PPTist/                # Vue 前端 (PPT 编辑器)
├── requirements.txt       # Python 依赖
└── README.md
```

---

## 📚 文档资源

| 文档 | 链接 | 说明 |
|:----:|:----:|:-----|
| 🏗️ 架构分析 | [FLASK_BACKEND_STRUCTURE_ANALYSIS.md](docs/FLASK_BACKEND_STRUCTURE_ANALYSIS.md) | 后端架构详解 |
| 📡 API 文档 | [FRONTEND_API_ANALYSIS.md](docs/FRONTEND_API_ANALYSIS.md) | 接口说明 |
| ⚙️ 配置说明 | [config_data/README.md](flask_backend/config_data/README.md) | 配置指南 |

---

## ⚠️ 常见问题

### 配置文件不存在
```bash
# 复制模板文件
cp flask_backend/config_data/app_config_template.json flask_backend/config_data/app_config.json
cp flask_backend/mongo_config.template.yaml flask_backend/mongo_config.yaml
```

### MongoDB 连接失败
- 确保 MongoDB 服务已启动
- 检查 `mongo_config.yaml` 中的连接字符串

### FFmpeg 未安装
- Windows: 下载 [FFmpeg](https://ffmpeg.org/download.html) 并添加到 PATH
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支: `git checkout -b feature/your-feature`
3. 提交更改: `git commit -m 'Add your feature'`
4. 推送分支: `git push origin feature/your-feature`
5. 提交 Pull Request

---

## 📄 许可证

<div align="center">

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**Made with ❤️ by PPT-TO-VIDEO Team**

</div>
