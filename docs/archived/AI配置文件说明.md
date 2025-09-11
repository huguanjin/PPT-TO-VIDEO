# AI配置文件说明

## 📋 概述

本项目支持通过配置文件灵活配置AI服务的API地址和模型名称，不再需要在代码中硬编码这些信息。

## 📁 配置文件位置

- **主配置文件**: `config_data/app_config.json`
- **模板文件**: `config_data/app_config_template.json`

## 🔧 AI配置结构

### 1. 基本配置

```json
{
  "ai": {
    "default_service": "openai",
    "openai": {
      "api_key": "your-api-key",
      "base_url": "https://api.openai.com",
      "model": "gpt-3.5-turbo",
      "timeout": 300,
      "max_retries": 3,
      "support_json": true
    },
    "anthropic": {
      "api_key": "your-api-key",
      "base_url": "https://api.anthropic.com",
      "model": "claude-3-sonnet-20240229",
      "timeout": 300,
      "max_retries": 3
    },
    "custom": {
      "api_key": "your-api-key",
      "base_url": "https://your-custom-api.com",
      "model": "your-model-name",
      "timeout": 300,
      "max_retries": 3,
      "support_json": true
    }
  }
}
```

### 2. 服务配置 (services_config)

用于前端界面显示和验证的服务和模型信息：

```json
{
  "ai": {
    "services_config": {
      "openai": {
        "name": "OpenAI",
        "description": "OpenAI GPT模型服务",
        "default_base_url": "https://api.openai.com",
        "supports_json": true,
        "models": [
          {
            "value": "gpt-3.5-turbo",
            "label": "GPT-3.5 Turbo",
            "description": "快速高效的对话模型",
            "is_default": true
          }
        ]
      }
    }
  }
}
```

## 🎯 使用场景

### 1. 使用官方OpenAI API

```json
{
  "ai": {
    "openai": {
      "api_key": "sk-xxxxxxxxxxxxxxxx",
      "base_url": "https://api.openai.com",
      "model": "gpt-3.5-turbo"
    }
  }
}
```

### 2. 使用代理服务

```json
{
  "ai": {
    "openai": {
      "api_key": "your-proxy-key",
      "base_url": "https://your-proxy.com/v1",
      "model": "gpt-3.5-turbo"
    }
  }
}
```

### 3. 使用自定义API服务

```json
{
  "ai": {
    "custom": {
      "api_key": "your-custom-key",
      "base_url": "https://your-api.example.com/v1",
      "model": "your-custom-model"
    },
    "default_service": "custom"
  }
}
```

### 4. 添加自定义模型

```json
{
  "ai": {
    "services_config": {
      "openai": {
        "models": [
          {
            "value": "gpt-3.5-turbo",
            "label": "GPT-3.5 Turbo",
            "description": "默认模型",
            "is_default": true
          },
          {
            "value": "my-custom-model",
            "label": "我的自定义模型",
            "description": "针对特定任务优化的模型"
          }
        ]
      }
    }
  }
}
```

## ⚙️ 配置字段说明

### 基本配置字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `api_key` | string | ✅ | API密钥 |
| `base_url` | string | ✅ | API服务地址 |
| `model` | string | ✅ | 模型名称 |
| `timeout` | number | ❌ | 请求超时时间(秒)，默认300 |
| `max_retries` | number | ❌ | 最大重试次数，默认3 |
| `support_json` | boolean | ❌ | 是否支持JSON格式响应，默认true |

### 模型配置字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `value` | string | ✅ | 模型的实际值 |
| `label` | string | ✅ | 显示名称 |
| `description` | string | ❌ | 模型描述 |
| `is_default` | boolean | ❌ | 是否为默认模型 |

## 🔄 配置更新方式

### 1. 直接编辑配置文件

编辑 `config_data/app_config.json` 文件，保存后重启应用。

### 2. 通过Web界面配置

访问前端配置界面，在AI配置部分进行修改。

### 3. 通过API接口

```bash
# 更新配置
POST /api/ai-config
{
  "enabled": true,
  "ai_config": {
    "service_type": "openai",
    "api_key": "new-key",
    "base_url": "new-url",
    "model": "new-model"
  }
}

# 获取配置
GET /api/ai-config

# 重置为默认值
POST /api/ai-config/reset
```

## 🧪 配置验证

### 1. API密钥验证

```bash
POST /api/ai-config/validate
{
  "ai_config": {
    "service_type": "openai",
    "api_key": "your-key",
    "base_url": "your-url",
    "model": "your-model"
  }
}
```

### 2. 功能测试

```bash
POST /api/ai-config/test
{
  "text": "测试文本",
  "ai_config": {...},
  "max_weight": 75
}
```

## 📝 最佳实践

### 1. 安全性
- ❌ 不要将API密钥提交到版本控制系统
- ✅ 使用环境变量或安全的配置管理工具
- ✅ 定期轮换API密钥

### 2. 性能优化
- ✅ 根据任务类型选择合适的模型
- ✅ 设置合理的超时时间和重试次数
- ✅ 使用代理服务提高访问速度

### 3. 配置管理
- ✅ 保留配置文件的备份
- ✅ 记录配置变更的原因和时间
- ✅ 测试新配置后再部署到生产环境

## 🚨 常见问题

### 1. API连接失败
- 检查网络连接
- 验证API密钥是否正确
- 确认base_url地址是否可访问

### 2. 模型不存在
- 检查模型名称是否正确
- 确认API服务支持该模型
- 查看API服务文档了解可用模型

### 3. 配置不生效
- 确认配置文件格式正确
- 重启应用使配置生效
- 检查应用日志了解错误信息

## 🔗 相关链接

- [OpenAI API文档](https://platform.openai.com/docs/api-reference)
- [Anthropic API文档](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [项目部署指南](./部署检查清单.md)
