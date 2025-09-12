# 🤖 自定义AI大模型接入指南

## 📋 概述

本系统支持接入多种自定义AI大模型，实现**人类级别的句子分析**能力。支持本地部署模型、云端API服务、以及各种兼容OpenAI格式的自定义接口。

## 🎯 核心功能

### 1. **人类级别句子理解**
- 🧠 **语法结构分析**: 句子成分、修辞手法、语言特点
- 💭 **语义深度理解**: 核心含义、隐含信息、歧义分析  
- 😊 **情感色彩识别**: 情感倾向、语调分析、情感强度
- 🎯 **语用功能分析**: 交际意图、表达效果、适用场景
- 🔗 **逻辑关系提取**: 因果关系、时间顺序、重要性层级
- 🏛️ **文化背景理解**: 文化内涵、社会语境、表达习惯

### 2. **智能字幕处理**
- ✂️ **语义分割**: 按语义单元智能分割长文本
- 🎬 **内容分析**: 主题提取、结构分析、重点识别
- 🎭 **情感分析**: 情感识别、语调分析、情感增强

## 🛠️ 支持的AI模型类型

### 1. **本地部署模型**

#### 🦙 Ollama (推荐)
```json
{
  "model_name": "local_chatglm",
  "name": "本地ChatGLM模型",
  "provider": "ollama",
  "model_id": "chatglm3:6b",
  "base_url": "http://localhost:11434",
  "api_key": null,
  "temperature": 0.7,
  "max_tokens": 4000,
  "support_json": true
}
```

**设置步骤:**
1. 安装Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. 启动服务: `ollama serve`
3. 下载模型: `ollama pull chatglm3:6b`
4. 使用API注册模型

#### 🏗️ XInference
```json
{
  "model_name": "xinference_qwen",
  "name": "XInference通义千问",
  "provider": "xinference",
  "model_id": "qwen-chat",
  "base_url": "http://localhost:9997/v1",
  "api_key": "dummy-key",
  "temperature": 0.7,
  "support_json": true
}
```

**设置步骤:**
1. 安装: `pip install xinference[all]`
2. 启动: `xinference-local --host 0.0.0.0 --port 9997`
3. 部署模型: `xinference launch --model-name qwen-chat --size-in-billions 7`

#### 🤗 HuggingFace本地模型
```json
{
  "model_name": "local_huggingface",
  "name": "本地HuggingFace模型",
  "provider": "local_huggingface", 
  "model_id": "THUDM/chatglm3-6b",
  "local_model_path": "/path/to/model",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

### 2. **云端API服务**

#### 🤖 智谱AI ChatGLM
```json
{
  "model_name": "chatglm_official",
  "name": "智谱AI ChatGLM",
  "provider": "chatglm",
  "model_id": "glm-4",
  "base_url": "https://open.bigmodel.cn/api/paas/v4",
  "api_key": "your-chatglm-api-key",
  "temperature": 0.7,
  "support_json": true
}
```

#### 🌟 通义千问
```json
{
  "model_name": "qwen_official",
  "name": "通义千问",
  "provider": "qwen",
  "model_id": "qwen-turbo",
  "base_url": "https://dashscope.aliyuncs.com/api/v1",
  "api_key": "your-qwen-api-key",
  "support_json": true
}
```

#### 🚀 百川AI
```json
{
  "model_name": "baichuan_official",
  "name": "百川AI",
  "provider": "baichuan", 
  "model_id": "Baichuan2-Turbo",
  "base_url": "https://api.baichuan-ai.com/v1",
  "api_key": "your-baichuan-api-key",
  "support_json": true
}
```

### 3. **自定义兼容API**

#### 🔗 OpenAI兼容接口
```json
{
  "model_name": "custom_gpt",
  "name": "自定义GPT服务",
  "provider": "custom_api",
  "model_id": "gpt-3.5-turbo",
  "base_url": "https://your-api-endpoint.com/v1",
  "api_key": "your-custom-api-key",
  "custom_headers": {
    "User-Agent": "PPT-Video-Tool",
    "X-Custom-Header": "custom-value"
  },
  "support_json": true
}
```

## 🚀 快速开始

### 1. **启动后端服务**
```bash
# 进入项目目录
cd /path/to/ppt_to_video

# 激活虚拟环境  
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 启动统一Flask服务器
python flask_backend/unified_app.py
```

### 2. **注册AI模型**

#### 方式一: HTTP API
```bash
curl -X POST http://localhost:5000/api/custom-ai/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "my_local_model",
    "name": "我的本地模型",
    "provider": "ollama",
    "model_id": "chatglm3:6b", 
    "base_url": "http://localhost:11434",
    "temperature": 0.7,
    "support_json": true
  }'
```

#### 方式二: Python代码
```python
from flask_backend.core.custom_ai_models import CustomAIModelManager, ModelConfig, ModelProvider

# 创建管理器
manager = CustomAIModelManager()

# 配置模型
config = ModelConfig(
    name="本地ChatGLM",
    provider=ModelProvider.OLLAMA,
    model_id="chatglm3:6b",
    base_url="http://localhost:11434",
    support_json=True
)

# 注册模型
success = manager.register_model("local_chatglm", config)
print(f"注册结果: {success}")
```

### 3. **测试模型连接**
```bash
curl -X POST http://localhost:5000/api/custom-ai/models/local_chatglm/test
```

### 4. **使用AI分析功能**

#### 句子分析
```bash
curl -X POST http://localhost:5000/api/custom-ai/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天天气真不错，我们去公园散步吧！",
    "model_name": "local_chatglm",
    "task_type": "sentence_analysis",
    "language": "zh"
  }'
```

#### 批量分析
```bash
curl -X POST http://localhost:5000/api/custom-ai/batch-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "第一个句子。", 
      "第二个句子。",
      "第三个句子。"
    ],
    "model_name": "local_chatglm",
    "task_type": "semantic_split",
    "language": "zh"
  }'
```

## 📊 API接口文档

### 系统状态
- `GET /api/custom-ai/status` - 获取系统状态
- `GET /api/custom-ai/templates` - 获取模型配置模板  
- `GET /api/custom-ai/examples` - 获取示例配置

### 模型管理
- `POST /api/custom-ai/models` - 注册新模型
- `GET /api/custom-ai/models` - 获取模型列表
- `DELETE /api/custom-ai/models/{name}` - 注销模型
- `POST /api/custom-ai/models/{name}/test` - 测试模型连接

### AI分析功能
- `POST /api/custom-ai/analyze` - 单文本分析
- `POST /api/custom-ai/batch-analyze` - 批量文本分析

## 🔧 高级配置

### 性能优化
```json
{
  "context_length": 4096,
  "batch_size": 1,
  "enable_streaming": false,
  "enable_cache": true,
  "max_retries": 3,
  "retry_delay": 1.0
}
```

### 自定义请求头
```json
{
  "custom_headers": {
    "Authorization": "Bearer your-token",
    "User-Agent": "PPT-Video-Tool/1.0",
    "X-RateLimit-Bypass": "true"
  }
}
```

### 本地模型路径
```json
{
  "local_model_path": "/data/models/chatglm3-6b",
  "context_length": 8192,
  "enable_function_calling": true
}
```

## 🧪 测试工具

运行完整测试套件:
```bash
python test_custom_ai_models.py
```

测试包括:
- ✅ 系统状态检查
- 📋 配置模板验证  
- 🔧 模型注册测试
- 🔍 连接性测试
- 📖 文本分析功能
- 📚 批量处理测试

## 🎯 实际应用场景

### 1. **PPT内容智能分析**
```python
# 分析PPT文本内容
result = await analyze_sentence_with_ai(
    text="本章介绍机器学习的基本概念和应用领域",
    model_name="local_chatglm", 
    task_type="content_analysis"
)

# 获取分析结果
if result.success:
    analysis = result.result
    main_topic = analysis.get('main_topic')
    key_points = analysis.get('key_points', [])
    content_type = analysis.get('content_type')
```

### 2. **智能字幕分割**
```python
# 长文本语义分割
result = await analyze_sentence_with_ai(
    text="人工智能是一门研究如何让机器模拟人类智能的学科。它包括机器学习、深度学习、自然语言处理等多个分支。",
    task_type="semantic_split"
)

segments = result.result.get('segments', [])
# ["人工智能是一门研究如何让机器模拟人类智能的学科。", "它包括机器学习、深度学习、自然语言处理等多个分支。"]
```

### 3. **情感语调分析**
```python
# 分析文本情感
result = await analyze_sentence_with_ai(
    text="今天的演示真是太精彩了！",
    task_type="emotion_analysis"
)

emotion_data = result.result
primary_emotion = emotion_data.get('primary_emotion')  # "excitement"
intensity = emotion_data.get('emotion_intensity')      # 0.85
sentiment = emotion_data.get('sentiment_polarity')     # "positive"
```

## 🚨 故障排除

### 常见问题

**1. Ollama连接失败**
```bash
# 检查Ollama服务状态
curl http://localhost:11434/api/tags

# 启动Ollama服务
ollama serve

# 重新拉取模型
ollama pull chatglm3:6b
```

**2. 内存不足错误**  
```python
# 调整模型配置
config.max_tokens = 1024  # 减少最大token数
config.batch_size = 1     # 使用单批次处理
```

**3. API密钥错误**
```bash
# 验证API密钥
curl -H "Authorization: Bearer your-api-key" \
     https://api.example.com/models
```

**4. 网络连接超时**
```python
config.timeout = 60      # 增加超时时间
config.max_retries = 5   # 增加重试次数
```

## 📈 性能监控

系统提供详细的性能统计:
```bash
curl http://localhost:5000/api/custom-ai/status
```

响应包含:
- 总请求数和成功率
- 平均处理时间  
- 各模型使用统计
- 错误率分析

## 🎉 总结

本系统已经为您提供了完整的自定义AI大模型接入能力:

✅ **即插即用**: 支持多种主流AI模型和部署方式  
✅ **人类级理解**: 深度句子分析，不只是简单的文本处理  
✅ **高度灵活**: 自定义配置、请求头、超时等参数  
✅ **生产就绪**: 错误处理、重试机制、性能监控  
✅ **易于集成**: RESTful API接口，支持各种前端框架

现在您可以轻松接入自己的AI大模型，实现真正的**人类级别句子分析**能力！

## 📞 支持

如需更多帮助，请查看:
- 📖 完整API文档: `http://localhost:5000/docs`
- 🧪 在线测试: `python test_custom_ai_models.py`
- 💡 示例配置: `http://localhost:5000/api/custom-ai/examples`