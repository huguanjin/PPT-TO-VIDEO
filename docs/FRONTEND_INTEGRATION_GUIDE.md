# 前端集成指南

## 🎯 目标
将PPTist前端与统一的Flask后端API集成，实现完整的PPT转视频工作流。

## 📋 当前状态

### ✅ 后端就绪
- 统一Flask服务运行在端口5000
- VideoLingo功能已集成
- 所有核心API端点可用
- 测试验证功能正常

### 🔄 待完成
- 前端API调用地址更新
- 数据格式适配
- 错误处理优化
- 用户界面增强

## 🔗 API端点映射

### 核心功能API
```typescript
// 基础服务
const API_BASE = 'http://localhost:5000'

const endpoints = {
  // 健康检查
  health: '/health',
  
  // PPTist集成
  pptist: {
    import: '/api/pptist/import',
    export: '/api/pptist_export/slides',
    generateVideo: '/api/pptist_export/generate_video'
  },
  
  // 工作流管理
  workflow: {
    status: '/api/workflow/status',
    start: '/api/workflow/start',
    pause: '/api/workflow/pause',
    resume: '/api/workflow/resume'
  },
  
  // TTS功能
  tts: {
    voices: '/api/tts/voices',
    synthesize: '/api/tts/synthesize',
    batch: '/api/tts/batch'
  },
  
  // 项目管理
  project: {
    list: '/api/project',
    create: '/api/project/create',
    get: '/api/project/{id}',
    update: '/api/project/{id}',
    delete: '/api/project/{id}'
  },
  
  // VideoLingo集成
  videolingo: {
    health: '/api/videolingo/health',
    version: '/api/videolingo/version',
    config: '/api/videolingo/config',
    test: '/api/videolingo/test'
  }
}
```

## 🔧 前端代码更新

### 1. API服务类更新
更新 `PPTist/src/services/api.ts`:

```typescript
import axios, { AxiosInstance, AxiosResponse } from 'axios'

class APIService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:5000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log(`🚀 API请求: ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('❌ 请求错误:', error)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API响应: ${response.status} ${response.config.url}`)
        return response
      },
      (error) => {
        console.error('❌ 响应错误:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  // PPT导入
  async importPPT(file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await this.client.post('/api/pptist/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  // 获取幻灯片
  async getSlides(): Promise<any> {
    const response = await this.client.get('/api/pptist_export/slides')
    return response.data
  }

  // 生成视频
  async generateVideo(config: any): Promise<any> {
    const response = await this.client.post('/api/pptist_export/generate_video', config)
    return response.data
  }

  // TTS语音合成
  async synthesizeAudio(text: string, voice: string): Promise<any> {
    const response = await this.client.post('/api/tts/synthesize', {
      text,
      voice
    })
    return response.data
  }

  // 获取可用语音列表
  async getVoices(): Promise<any> {
    const response = await this.client.get('/api/tts/voices')
    return response.data
  }

  // 工作流状态查询
  async getWorkflowStatus(): Promise<any> {
    const response = await this.client.get('/api/workflow/status')
    return response.data
  }

  // 健康检查
  async checkHealth(): Promise<any> {
    const response = await this.client.get('/health')
    return response.data
  }
}

export default new APIService()
```

### 2. 状态管理更新
更新 `PPTist/src/stores/api.ts`:

```typescript
import { defineStore } from 'pinia'
import APIService from '@/services/api'

export const useAPIStore = defineStore('api', {
  state: () => ({
    isConnected: false,
    lastError: null as string | null,
    currentWorkflow: null as any,
    availableVoices: [] as any[],
    projectData: null as any
  }),

  actions: {
    // 检查API连接
    async checkConnection() {
      try {
        await APIService.checkHealth()
        this.isConnected = true
        this.lastError = null
        console.log('✅ API连接正常')
      } catch (error) {
        this.isConnected = false
        this.lastError = '无法连接到后端服务'
        console.error('❌ API连接失败:', error)
      }
    },

    // 导入PPT
    async importPPT(file: File) {
      try {
        const result = await APIService.importPPT(file)
        this.projectData = result
        return result
      } catch (error) {
        this.lastError = '导入PPT失败'
        throw error
      }
    },

    // 获取TTS语音列表
    async loadVoices() {
      try {
        const voices = await APIService.getVoices()
        this.availableVoices = voices
      } catch (error) {
        console.error('获取语音列表失败:', error)
      }
    },

    // 生成视频
    async generateVideo(config: any) {
      try {
        return await APIService.generateVideo(config)
      } catch (error) {
        this.lastError = '视频生成失败'
        throw error
      }
    },

    // 监控工作流状态
    async monitorWorkflow() {
      try {
        const status = await APIService.getWorkflowStatus()
        this.currentWorkflow = status
        return status
      } catch (error) {
        console.error('获取工作流状态失败:', error)
      }
    }
  }
})
```

### 3. 组件更新示例
更新主要组件以使用新的API：

```vue
<!-- PPTist/src/components/ImportDialog.vue -->
<template>
  <div class="import-dialog">
    <h3>导入PPT文件</h3>
    
    <div v-if="!apiStore.isConnected" class="api-warning">
      ⚠️ 后端服务未连接，请检查服务器状态
    </div>
    
    <input 
      type="file" 
      accept=".ppt,.pptx" 
      @change="handleFileSelect"
      :disabled="!apiStore.isConnected"
    />
    
    <div v-if="importing" class="progress">
      正在导入PPT文件...
    </div>
    
    <div v-if="apiStore.lastError" class="error">
      {{ apiStore.lastError }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAPIStore } from '@/stores/api'

const apiStore = useAPIStore()
const importing = ref(false)

onMounted(async () => {
  // 组件加载时检查API连接
  await apiStore.checkConnection()
})

const handleFileSelect = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  
  importing.value = true
  
  try {
    await apiStore.importPPT(file)
    // 导入成功后的处理
    console.log('PPT导入成功')
  } catch (error) {
    console.error('导入失败:', error)
  } finally {
    importing.value = false
  }
}
</script>
```

## 🔄 数据格式适配

### 请求格式标准化
```typescript
// 统一请求格式
interface APIRequest {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  endpoint: string
  data?: any
  params?: Record<string, string>
  headers?: Record<string, string>
}

// 统一响应格式
interface APIResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  timestamp: string
}
```

### PPT数据格式
```typescript
interface PPTData {
  id: string
  title: string
  slides: Array<{
    id: string
    content: string
    notes: string
    image_path?: string
  }>
  metadata: {
    total_slides: number
    created_at: string
    file_size: number
  }
}
```

## ⚡ 性能优化

### 1. 请求缓存
```typescript
class CacheManager {
  private cache = new Map<string, any>()
  private ttl = 5 * 60 * 1000 // 5分钟

  set(key: string, value: any) {
    this.cache.set(key, {
      data: value,
      timestamp: Date.now()
    })
  }

  get(key: string) {
    const cached = this.cache.get(key)
    if (!cached) return null
    
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key)
      return null
    }
    
    return cached.data
  }
}
```

### 2. 批量处理
```typescript
// 批量TTS合成
async function batchSynthesis(texts: string[], voice: string) {
  const response = await APIService.client.post('/api/tts/batch', {
    texts,
    voice,
    options: {
      format: 'mp3',
      speed: 1.0
    }
  })
  return response.data
}
```

## 🧪 测试集成

### 1. 单元测试
```typescript
// tests/api.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import APIService from '@/services/api'

describe('API Service', () => {
  beforeEach(() => {
    // 重置API状态
  })

  it('should check health successfully', async () => {
    const health = await APIService.checkHealth()
    expect(health.status).toBe('ok')
  })

  it('should handle import PPT', async () => {
    const mockFile = new File([''], 'test.pptx')
    const result = await APIService.importPPT(mockFile)
    expect(result.success).toBe(true)
  })
})
```

### 2. 集成测试
```typescript
// tests/integration.test.ts
import { describe, it, expect } from 'vitest'
import { useAPIStore } from '@/stores/api'

describe('API Integration', () => {
  it('should complete full workflow', async () => {
    const apiStore = useAPIStore()
    
    // 1. 检查连接
    await apiStore.checkConnection()
    expect(apiStore.isConnected).toBe(true)
    
    // 2. 导入PPT
    const mockFile = new File([''], 'test.pptx')
    await apiStore.importPPT(mockFile)
    expect(apiStore.projectData).toBeTruthy()
    
    // 3. 生成视频
    const result = await apiStore.generateVideo({
      voice: 'zh-CN-XiaoxiaoNeural',
      quality: 'high'
    })
    expect(result.success).toBe(true)
  })
})
```

## 📋 集成检查清单

### 阶段1：基础连接 ✅
- [x] Flask后端服务运行
- [ ] 前端API服务类更新
- [ ] CORS配置验证
- [ ] 基础健康检查通过

### 阶段2：核心功能
- [ ] PPT导入功能测试
- [ ] 幻灯片数据获取
- [ ] TTS语音合成
- [ ] 视频生成流程

### 阶段3：用户体验
- [ ] 进度显示优化
- [ ] 错误处理完善
- [ ] 加载状态管理
- [ ] 响应式界面适配

### 阶段4：性能优化
- [ ] 请求缓存实现
- [ ] 批量处理支持
- [ ] 文件上传优化
- [ ] 内存使用监控

## 🚀 部署准备

### 开发环境
```bash
# 启动后端
cd flask_backend
python unified_app.py

# 启动前端
cd PPTist
npm run dev
```

### 生产环境
```bash
# 构建前端
npm run build

# 部署到服务器
# （参考 PERFORMANCE_OPTIMIZATION_CONFIG.md）
```

---

**📅 创建日期**: 2025-01-11  
**🎯 目标**: 完整前后端集成  
**📊 预计完成**: 2025-01-20
