# 配置文件使用说明

## 安全提醒 ⚠️
**请勿将包含真实API密钥的配置文件提交到版本控制系统！**

## 配置文件说明

### 1. app_config_template.json
- **用途**: 配置模板文件
- **状态**: 已提交到Git，不包含敏感信息
- **内容**: 所有配置项的结构和占位符

### 2. app_config.json
- **用途**: 实际使用的配置文件
- **状态**: 已添加到.gitignore，不会被提交
- **内容**: 包含真实的API密钥和配置

## 初始化配置

### 第一次使用
```bash
# 1. 复制模板文件
cp flask_backend/config_data/app_config_template.json flask_backend/config_data/app_config.json

# 2. 编辑配置文件，替换API密钥
# 将以下占位符替换为真实值:
# - YOUR_OPENAI_API_KEY_HERE
# - YOUR_ANTHROPIC_API_KEY_HERE  
# - YOUR_CUSTOM_API_KEY_HERE
# - YOUR_FISH_SPEECH_API_KEY_HERE
# - YOUR_CHARACTER_ID_HERE
# - YOUR_OPENAI_TTS_API_KEY_HERE
# - YOUR_AZURE_API_KEY_HERE
```

### 需要替换的主要密钥
1. **AI服务密钥**:
   ```json
   "ai": {
     "openai": {
       "api_key": "sk-your-openai-key-here"
     },
     "custom": {
       "api_key": "sk-your-custom-api-key-here",
       "base_url": "https://your-api-endpoint.com/v1"
     }
   }
   ```

2. **TTS服务密钥**:
   ```json
   "tts": {
     "fish_api_key": "your-fish-speech-api-key",
     "fish_character_id": "your-character-id"
   }
   ```

## 安全最佳实践

### ✅ 正确做法
- 使用模板文件作为参考
- 将真实配置文件添加到.gitignore
- 定期轮换API密钥
- 使用环境变量存储敏感信息

### ❌ 错误做法
- 直接编辑模板文件
- 将包含密钥的配置文件提交到Git
- 在代码中硬编码API密钥
- 在公共场合分享配置文件

## 环境变量支持 (推荐)

除了配置文件，你也可以使用环境变量：

```bash
# 设置环境变量
export OPENAI_API_KEY="your-openai-key"
export FISH_API_KEY="your-fish-key"
export CUSTOM_API_KEY="your-custom-key"
```

## 故障排除

### 配置文件不存在
如果启动时提示配置文件不存在：
```bash
cp flask_backend/config_data/app_config_template.json flask_backend/config_data/app_config.json
```

### API密钥无效
1. 检查密钥格式是否正确
2. 确认密钥没有过期
3. 验证API服务地址是否正确

### 权限问题
确保配置文件有适当的读取权限：
```bash
chmod 600 flask_backend/config_data/app_config.json
```

## 更新日志
- 2025-09-25: 创建配置文件管理说明
- 2025-09-25: 更新.gitignore规则，保护敏感配置