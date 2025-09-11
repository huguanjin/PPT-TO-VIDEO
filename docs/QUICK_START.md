# 🚀 PPT转视频项目 - 立即开始指南

## 📋 当前状态检查

在开始集成之前，让我们先确认当前的系统状态：

### 1. 后端状态检查

```bash
# 检查后端是否正常启动
curl http://localhost:5000/api/health

# 预期响应：
# {
#   "status": "ok", 
#   "timestamp": "2025-09-11T10:30:00Z"
# }
```

### 2. 前端状态检查

```bash
# 在PPTist目录下
cd PPTist
npm run dev

# 确认前端在 http://localhost:5173 正常运行
```

---

## 🔧 第一步：立即可执行的任务

### 任务1：修复前端API配置（10分钟）

**文件**: `PPTist/src/config/env.ts`

当前问题：前端API地址可能配置不正确

**修复方案**:
```typescript
// 修改这个文件，确保后端地址正确
export const createRequestConfig = (): RequestConfig => {
  return {
    baseURL: 'http://localhost:5000/api',  // 确保这个地址正确
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  }
}
```

### 任务2：创建API测试页面（20分钟）

**新建文件**: `PPTist/src/views/ApiTest.vue`
```vue
<template>
  <div class="api-test-page">
    <h2>API连接测试</h2>
    
    <div class="test-section">
      <h3>健康检查测试</h3>
      <button @click="testHealth" :disabled="loading">
        {{ loading ? '测试中...' : '测试健康检查' }}
      </button>
      <div v-if="healthResult" class="result">
        <pre>{{ JSON.stringify(healthResult, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="test-section">
      <h3>配置API测试</h3>
      <button @click="testConfig" :disabled="loading">
        测试配置接口
      </button>
      <div v-if="configResult" class="result">
        <pre>{{ JSON.stringify(configResult, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="test-section">
      <h3>错误测试</h3>
      <button @click="testError">测试错误处理</button>
      <div v-if="errorResult" class="result error">
        <pre>{{ JSON.stringify(errorResult, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { getPrimaryApi } from '@/api/index'

const loading = ref(false)
const healthResult = ref(null)
const configResult = ref(null)
const errorResult = ref(null)

const testHealth = async () => {
  loading.value = true
  try {
    const api = getPrimaryApi()
    const response = await api.get('/health')
    healthResult.value = response
    console.log('健康检查成功:', response)
  } catch (error) {
    healthResult.value = { error: error.message }
    console.error('健康检查失败:', error)
  } finally {
    loading.value = false
  }
}

const testConfig = async () => {
  try {
    const api = getPrimaryApi()
    const response = await api.get('/config')
    configResult.value = response
    console.log('配置获取成功:', response)
  } catch (error) {
    configResult.value = { error: error.message }
    console.error('配置获取失败:', error)
  }
}

const testError = async () => {
  try {
    const api = getPrimaryApi()
    const response = await api.get('/nonexistent-endpoint')
    errorResult.value = response
  } catch (error) {
    errorResult.value = { 
      error: error.message,
      code: error.code,
      status: error.status
    }
    console.log('错误处理测试:', error)
  }
}
</script>

<style scoped>
.api-test-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-section {
  margin-bottom: 30px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.result {
  margin-top: 10px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
  font-family: monospace;
}

.result.error {
  background: #ffe6e6;
  color: #d00;
}

button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
```

### 任务3：添加路由（5分钟）

**修改文件**: `PPTist/src/views/Editor/EditorHeader/index.vue`

在导航菜单中添加API测试链接：
```vue
<!-- 在适当位置添加 -->
<router-link to="/api-test" class="header-item">
  API测试
</router-link>
```

**或者直接访问**：在浏览器地址栏输入 `http://localhost:5173/#/api-test`

### 任务4：完善后端健康检查（15分钟）

**修改文件**: `flask_backend/app/api/common.py`

```python
from flask import Blueprint, jsonify
from datetime import datetime
import os
import sys

bp = Blueprint('common', __name__)

@bp.route('/health', methods=['GET'])
def health():
    """详细的健康检查接口"""
    
    # 检查各个服务状态
    services_status = {
        'database': check_database_connection(),
        'storage': check_storage_access(),
        'tts': check_tts_service(),
        'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    # 整体状态
    overall_status = 'ok' if all(
        status != 'error' for status in services_status.values()
    ) else 'degraded'
    
    return jsonify({
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'services': services_status,
        'uptime': get_uptime(),
        'endpoints': {
            'config': '/api/config',
            'workflow': '/api/workflow',
            'tts': '/api/tts',
            'project': '/api/project'
        }
    })

def check_database_connection():
    """检查数据库连接"""
    try:
        # 这里添加实际的数据库检查逻辑
        return 'ok'
    except Exception as e:
        return f'error: {str(e)}'

def check_storage_access():
    """检查存储访问"""
    try:
        # 检查输出目录是否可写
        output_dir = os.path.join(os.getcwd(), 'output')
        if os.path.exists(output_dir) and os.access(output_dir, os.W_OK):
            return 'ok'
        return 'warning: output directory not writable'
    except Exception as e:
        return f'error: {str(e)}'

def check_tts_service():
    """检查TTS服务"""
    try:
        # 这里添加TTS服务检查逻辑
        return 'ok'
    except Exception as e:
        return f'error: {str(e)}'

def get_uptime():
    """获取服务运行时间"""
    # 简单的运行时间计算
    return "运行中"
```

---

## ⚡ 立即测试步骤

### 1. 启动服务（2分钟）

```bash
# 终端1：启动后端
cd flask_backend
python app.py

# 终端2：启动前端  
cd PPTist
npm run dev
```

### 2. 执行测试（3分钟）

1. 打开浏览器访问：`http://localhost:5173/#/api-test`
2. 点击"测试健康检查"按钮
3. 观察响应结果

**预期结果**：
```json
{
  "status": "ok",
  "timestamp": "2025-09-11T...",
  "version": "1.0.0",
  "services": {...}
}
```

### 3. 问题排查

**如果测试失败**：

#### 问题1：网络错误 (ERR_CONNECTION_REFUSED)
```bash
# 检查后端是否运行
curl http://localhost:5000/api/health

# 如果失败，重新启动后端
cd flask_backend
python app.py
```

#### 问题2：CORS错误
在 `flask_backend/app/__init__.py` 中确认：
```python
from flask_cors import CORS

def create_app(config_class=None):
    app = Flask(__name__)
    
    # 确保CORS配置正确
    CORS(app, origins=['http://localhost:5173'], supports_credentials=True)
```

#### 问题3：404错误
检查路由注册：
```python
# flask_backend/app/__init__.py
def register_blueprints(app):
    from app.api.common import bp as common_bp
    app.register_blueprint(common_bp, url_prefix='/api')
```

---

## 📈 成功后的下一步

一旦健康检查测试成功，立即继续：

### 即将执行的任务

1. **配置API集成**（明天上午）
   - 实现 `/api/config` 接口
   - 修改前端配置页面

2. **项目保存功能**（明天下午）  
   - 实现 `/api/project` 接口
   - 连接PPTist项目管理

3. **TTS语音测试**（后天）
   - 实现 `/api/tts/voices` 接口
   - 测试语音合成功能

### 快速验证清单

- [ ] 前端能访问 `http://localhost:5173`
- [ ] 后端能访问 `http://localhost:5000/api/health`
- [ ] API测试页面显示正常
- [ ] 健康检查返回成功响应
- [ ] 错误处理机制正常工作

---

## 🆘 紧急联系和支持

### 常见问题快速解决

**Q: 前端无法启动？**
A: 检查 Node.js 版本，运行 `npm install` 重新安装依赖

**Q: 后端API无响应？**  
A: 检查Python环境和依赖，确认Flask正常启动

**Q: CORS跨域问题？**
A: 确认后端CORS配置包含前端地址

**Q: 端口冲突？**
A: 修改配置使用其他端口，或停止占用端口的服务

### 调试技巧

1. **使用浏览器开发者工具**
   - Network选项卡查看API请求
   - Console查看错误信息

2. **后端日志查看**  
   - 查看Flask启动日志
   - 添加debug输出

3. **API工具测试**
   ```bash
   # 使用curl测试API
   curl -X GET http://localhost:5000/api/health
   
   # 使用Postman或其他API测试工具
   ```

---

## 🎯 今日目标

**目标**：建立基础的前后端通信

**成功标准**：
- [x] 前端能成功调用后端健康检查接口
- [x] 错误处理机制正常工作
- [x] API测试页面功能完整
- [x] 为明天的配置API开发做好准备

**预计耗时**：1-2小时

---

*开始时间记录：___________*  
*完成时间记录：___________*  
*遇到的问题：_____________*  
*解决方案：_______________*
