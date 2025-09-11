# 前端API调用分析报告

## 🔍 前端API调用现状分析

### 1. API服务架构分析

#### 1.1 核心API文件结构
```
PPTist/src/api/
├── base.ts              # 基础HTTP请求类
├── index.ts             # API服务主入口
├── interceptors.ts      # 请求/响应拦截器
├── performance.ts       # 性能监控
├── pptStorage.ts        # PPT存储API
├── test.ts              # API测试工具
├── testReporter.ts      # 测试报告
├── unifiedConfig.ts     # 统一配置API
├── services/            # 业务服务层
│   ├── aiService.ts     # AI服务
│   ├── ttsService.ts    # TTS服务
│   └── workflowService.ts # 工作流服务
└── types/               # 类型定义
    ├── ai.ts
    ├── common.ts
    ├── tts.ts
    └── workflow.ts
```

#### 1.2 当前API调用方式
```typescript
// 智能API调用（支持降级）
await smartApiCall(async (api) => {
  return await api.get('/api/config')
})

// 直接服务调用
const aiService = getAIService()
await aiService.analyzeContent(content)
```

### 2. 主要API调用点分析

#### 2.1 配置管理相关调用

**文件**: `PPTist/src/views/UnifiedConfigSimple.vue`
```typescript
// 当前调用方式
api.get('/api/config/presets')    // 获取配置预设
api.get('/api/version')           // 获取版本信息

// 需要对接的后端接口
GET /api/config/presets
GET /api/version
```

**文件**: `PPTist/src/views/UnifiedConfigTest.vue`
```typescript
// 统一配置API调用
const schema = await UnifiedConfigAPI.getConfigSchema()
const configData = await UnifiedConfigAPI.getUnifiedConfig()
const validation = await UnifiedConfigAPI.validateConfig(config)
await UnifiedConfigAPI.saveUnifiedConfig(config, options)
await UnifiedConfigAPI.updateConfigSection('video', data)

// 对应后端接口
GET /api/config/schema
GET /api/config
POST /api/config/validate
POST /api/config
PUT /api/config/video
```

**文件**: `PPTist/src/views/VideoConfig.vue`
```typescript
// 配置读取和保存
const response = await apiRequest('/api/config')
const response = await apiRequest('/api/config', {
  method: 'POST',
  body: JSON.stringify(configData)
})

// 对应后端接口
GET /api/config
POST /api/config
```

#### 2.2 视频导出相关调用

**文件**: `PPTist/src/hooks/videoExport/backendExport.ts`
```typescript
// 后端导出调用（需要实现）
await fetch('/api/export/start', {
  method: 'POST',
  body: JSON.stringify(exportConfig)
})

// 进度查询
await fetch(`/api/export/progress/${taskId}`)
```

**文件**: `PPTist/src/hooks/useVideoExport.ts`
```typescript
// 当前导出流程（需要集成后端）
const exportResult = await exportSlides({
  slides: slides,
  options: exportOptions
})
```

**需要对接的后端接口**:
```
POST /api/workflow/start      # 启动导出工作流
GET /api/workflow/progress/{id}  # 获取导出进度
GET /api/workflow/status/{id}    # 获取工作流状态
POST /api/workflow/stop/{id}     # 停止工作流
```

#### 2.3 TTS语音合成调用

**文件**: `PPTist/src/components/TTSConfig.vue`
```typescript
// 当前TTS配置（需要连接后端）
const ttsConfig = {
  provider: 'edge-tts',
  voice: 'zh-CN-XiaoxiaoNeural',
  speed: 1.0,
  pitch: 0
}

// 需要的API调用
await ttsService.getVoices()          # 获取语音列表
await ttsService.synthesize(text, config)  # 语音合成
await ttsService.preview(text, voice)      # 语音预览
```

**对应后端接口**:
```
GET /api/tts/voices           # 获取可用语音列表
POST /api/tts/synthesize      # 单个文本合成
POST /api/tts/batch          # 批量合成
POST /api/tts/preview        # 语音预览
```

#### 2.4 项目管理调用

**文件**: `PPTist/src/components/ProjectManager.vue`
```typescript
// 项目管理功能（需要后端支持）
await saveProject(projectData)    # 保存项目
await loadProject(projectId)      # 加载项目
await getProjectList()            # 获取项目列表
await deleteProject(projectId)    # 删除项目
```

**对应后端接口**:
```
GET /api/projects             # 获取项目列表
POST /api/project            # 创建项目
GET /api/project/{id}        # 获取项目详情
PUT /api/project/{id}        # 更新项目
DELETE /api/project/{id}     # 删除项目
```

### 3. API配置分析

#### 3.1 环境配置
**文件**: `PPTist/src/config/env.ts`
```typescript
// 当前配置
export const createRequestConfig = (): RequestConfig => {
  return {
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  }
}

// 备用配置
export const getFallbackRequestConfig = (): RequestConfig | null => {
  const fallbackUrl = import.meta.env.VITE_FALLBACK_API_URL
  if (!fallbackUrl) return null
  
  return {
    baseURL: fallbackUrl,
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json'
    }
  }
}
```

#### 3.2 拦截器配置
**文件**: `PPTist/src/api/interceptors.ts`
```typescript
// 请求拦截器
export const defaultInterceptors = {
  request: [
    (config: RequestInit) => {
      // 添加认证头
      // 请求日志
      // 参数处理
      return config
    }
  ],
  
  response: [
    (response: Response) => {
      // 响应处理
      // 数据转换
      return response
    }
  ],
  
  error: [
    (error: Error) => {
      // 错误处理
      // 重试逻辑
      // 降级处理
      throw error
    }
  ]
}
```

### 4. 组件中的API调用

#### 4.1 智能内容分析
**文件**: `PPTist/src/components/SmartContentAnalyzer.vue`
```typescript
// AI内容分析调用
import { aiService } from '@/api/services'

const analyzeContent = async () => {
  const result = await aiService.analyzeContent({
    slides: currentSlides.value,
    options: analysisOptions.value
  })
}
```

#### 4.2 实时预览
**文件**: `PPTist/src/components/RealTimePreview.vue`
```typescript
// 实时预览API调用（需要实现）
const startPreview = async () => {
  await fetch('/api/preview/start', {
    method: 'POST',
    body: JSON.stringify(previewConfig)
  })
}
```

#### 4.3 工作流进度
**文件**: `PPTist/src/components/WorkflowProgress.vue`
```typescript
// 工作流进度监控
const trackProgress = async (workflowId: string) => {
  const progress = await workflowService.getProgress(workflowId)
  updateProgressDisplay(progress)
}
```

### 5. 数据流分析

#### 5.1 PPT数据流
```
PPTist编辑器 
    ↓ (保存)
本地存储/Vuex状态
    ↓ (导出)
后端API (/api/pptist/import)
    ↓ (处理)
工作流引擎
    ↓ (生成)
视频文件
```

#### 5.2 配置数据流
```
前端配置界面
    ↓ (保存)
统一配置API (/api/config)
    ↓ (存储)
后端配置存储
    ↓ (应用)
各个处理模块
```

#### 5.3 TTS数据流
```
文本输入
    ↓ (合成请求)
TTS API (/api/tts/synthesize)
    ↓ (处理)
语音文件生成
    ↓ (返回)
音频文件URL
```

## 🔧 需要修改的文件清单

### 1. 高优先级修改

#### 1.1 配置管理
- [ ] `PPTist/src/views/UnifiedConfig.vue` - 连接后端配置API
- [ ] `PPTist/src/views/VideoConfig.vue` - 使用统一配置API
- [ ] `PPTist/src/api/unifiedConfig.ts` - 完善API调用方法

#### 1.2 基础连通性
- [ ] `PPTist/src/config/env.ts` - 配置正确的后端地址
- [ ] `PPTist/src/api/base.ts` - 完善错误处理
- [ ] `PPTist/src/api/interceptors.ts` - 添加后端兼容拦截器

#### 1.3 健康检查
- [ ] `PPTist/src/api/index.ts` - 添加健康检查方法
- [ ] 新建 `PPTist/src/utils/healthCheck.ts` - 健康检查工具

### 2. 中等优先级修改

#### 2.1 TTS集成
- [ ] `PPTist/src/components/TTSConfig.vue` - 连接后端TTS API
- [ ] `PPTist/src/api/services/ttsService.ts` - 完善TTS API调用
- [ ] `PPTist/src/components/EdgeTTSConfig.vue` - 使用后端语音列表

#### 2.2 项目管理
- [ ] `PPTist/src/components/ProjectManager.vue` - 连接后端项目API
- [ ] `PPTist/src/hooks/useProjectManager.ts` - 使用后端存储
- [ ] 新建 `PPTist/src/api/services/projectService.ts` - 项目API服务

#### 2.3 视频导出
- [ ] `PPTist/src/hooks/videoExport/backendExport.ts` - 实现后端导出
- [ ] `PPTist/src/components/VideoExportButton.vue` - 使用后端工作流
- [ ] `PPTist/src/components/WorkflowProgress.vue` - 连接进度API

### 3. 低优先级修改

#### 3.1 高级功能
- [ ] `PPTist/src/components/SmartContentAnalyzer.vue` - AI分析集成
- [ ] `PPTist/src/components/SmartSubtitleConfig.vue` - 智能字幕API
- [ ] `PPTist/src/components/RealTimePreview.vue` - 实时预览API

#### 3.2 优化功能
- [ ] `PPTist/src/api/performance.ts` - 性能监控完善
- [ ] `PPTist/src/utils/chunkedUploader.ts` - 大文件上传优化
- [ ] 新建 `PPTist/src/utils/offline.ts` - 离线支持

## 🚀 实施建议

### 1. 第一阶段：建立连接（立即开始）
1. 修改 `env.ts` 配置正确的后端地址
2. 测试 `/api/health` 接口连通性
3. 完善错误处理和日志记录
4. 实现基础的配置读取和保存

### 2. 第二阶段：核心功能（1周内）
1. 实现TTS API连接
2. 完成项目管理API集成
3. 建立基础的视频导出工作流
4. 添加进度监控功能

### 3. 第三阶段：高级功能（2周内）
1. 实现智能分析功能
2. 添加实时预览支持
3. 完善用户体验
4. 性能优化和错误处理

### 4. 关键技术决策
- 使用现有的 `smartApiCall` 机制支持API降级
- 保持现有的组件结构，只修改数据源
- 逐步迁移，确保功能不中断
- 添加离线模式支持作为备选方案

---

*分析报告生成时间: 2025年9月11日*
