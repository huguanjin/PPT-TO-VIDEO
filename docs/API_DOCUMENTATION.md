# PPT转视频项目 - API接口文档

## 概述

本文档详细描述了PPT转视频项目的前后端API接口规范、调用方式和实现计划。

---

## 🔧 后端Flask API接口

### 1. 基础接口

#### 1.1 健康检查
```
GET /api/health
```
**功能**: 检查服务运行状态  
**响应**:
```json
{
  "status": "ok",
  "timestamp": "2025-09-11T10:30:00Z",
  "version": "1.0.0"
}
```

#### 1.2 版本信息
```
GET /api/version
```
**功能**: 获取API版本信息  
**响应**:
```json
{
  "version": "1.0.0",
  "build": "20250911",
  "description": "PPT转视频工具API"
}
```

#### 1.3 API文档
```
GET /docs
```
**功能**: API文档页面

### 2. PPTist集成接口

#### 2.1 PPT数据导入
```
POST /api/pptist/import
```
**功能**: 导入PPTist的PPT数据  
**请求体**:
```json
{
  "slides": [...],
  "theme": {...},
  "metadata": {...}
}
```

#### 2.2 PPT数据导出
```
GET /api/pptist/export/{project_id}
POST /api/pptist/export
```
**功能**: 导出PPT数据供PPTist使用

#### 2.3 幻灯片截图
```
POST /api/pptist/capture
```
**功能**: 生成幻灯片截图  
**请求体**:
```json
{
  "slide_data": {...},
  "options": {
    "width": 1920,
    "height": 1080,
    "format": "png"
  }
}
```

### 3. 工作流管理接口

#### 3.1 工作流状态
```
GET /api/workflow/status/{workflow_id}
```
**功能**: 获取工作流执行状态

#### 3.2 启动工作流
```
POST /api/workflow/start
```
**功能**: 启动PPT转视频工作流  
**请求体**:
```json
{
  "project_id": "string",
  "config": {
    "video_config": {...},
    "tts_config": {...},
    "subtitle_config": {...}
  }
}
```

#### 3.3 停止工作流
```
POST /api/workflow/stop/{workflow_id}
```

#### 3.4 工作流进度
```
GET /api/workflow/progress/{workflow_id}
```
**功能**: 获取实时进度信息

### 4. TTS语音合成接口

#### 4.1 获取语音列表
```
GET /api/tts/voices
```
**响应**:
```json
{
  "voices": [
    {
      "name": "zh-CN-XiaoxiaoNeural",
      "language": "zh-CN",
      "gender": "Female",
      "provider": "edge-tts"
    }
  ]
}
```

#### 4.2 语音合成
```
POST /api/tts/synthesize
```
**请求体**:
```json
{
  "text": "要合成的文本",
  "voice": "zh-CN-XiaoxiaoNeural",
  "speed": 1.0,
  "pitch": 0,
  "output_format": "wav"
}
```

#### 4.3 批量语音合成
```
POST /api/tts/batch
```

### 5. 智能字幕接口

#### 5.1 字幕生成
```
POST /api/subtitle/generate
```
**请求体**:
```json
{
  "audio_file": "audio.wav",
  "language": "zh-CN",
  "options": {
    "max_words_per_subtitle": 15,
    "subtitle_duration": 3.0
  }
}
```

#### 5.2 字幕优化
```
POST /api/subtitle/optimize
```

#### 5.3 字幕同步
```
POST /api/subtitle/sync
```

### 6. 配置管理接口

#### 6.1 获取配置
```
GET /api/config
GET /api/config/{section}
```

#### 6.2 更新配置
```
POST /api/config
PUT /api/config/{section}
```

#### 6.3 配置预设
```
GET /api/config/presets
```

### 7. 项目管理接口

#### 7.1 创建项目
```
POST /api/project
```

#### 7.2 获取项目列表
```
GET /api/projects
```

#### 7.3 获取项目详情
```
GET /api/project/{project_id}
```

#### 7.4 更新项目
```
PUT /api/project/{project_id}
```

#### 7.5 删除项目
```
DELETE /api/project/{project_id}
```

### 8. 文件管理接口

#### 8.1 文件上传
```
POST /api/upload
```

#### 8.2 文件下载
```
GET /api/download/{file_id}
```

#### 8.3 文件列表
```
GET /api/files
```

### 9. 多语言支持接口

#### 9.1 语言检测
```
POST /api/multilingual/detect-language
```

#### 9.2 多语言字幕生成
```
POST /api/multilingual/generate-subtitles
```

#### 9.3 语言配置
```
GET /api/multilingual/config/{language_code}
```

### 10. AI集成接口

#### 10.1 AI配置测试
```
POST /api/ai/test-connection
```

#### 10.2 AI内容分析
```
POST /api/ai/analyze-content
```

#### 10.3 智能内容优化
```
POST /api/ai/optimize-content
```

---

## 🎨 前端PPTist API调用

### 1. API服务架构

#### 1.1 核心API类
- `BaseApi`: 基础HTTP请求处理
- `ApiInterceptors`: 请求/响应拦截器
- `RequestConfig`: 请求配置管理

#### 1.2 业务服务
- `AIService`: AI相关API调用
- `TTSService`: 语音合成API调用  
- `WorkflowService`: 工作流API调用

#### 1.3 统一配置
- `UnifiedConfigAPI`: 统一配置管理
- `SmartApiCall`: 智能API调用（支持降级）

### 2. 主要调用点

#### 2.1 视频导出相关
**文件位置**: `PPTist/src/hooks/videoExport/`
- `backendExport.ts`: 后端导出调用
- `enhancedPPTistExport.ts`: 增强导出功能
- `useVideoExportNew.ts`: 新版视频导出Hook

**主要API调用**:
```typescript
// 启动视频导出
await workflowService.startExport({
  projectId: 'xxx',
  config: exportConfig
})

// 获取导出进度
await workflowService.getProgress(workflowId)
```

#### 2.2 配置管理相关
**文件位置**: `PPTist/src/views/`
- `UnifiedConfig.vue`: 统一配置页面
- `VideoConfig.vue`: 视频配置页面
- `ConfigCenter.vue`: 配置中心

**主要API调用**:
```typescript
// 获取配置
const config = await UnifiedConfigAPI.getUnifiedConfig()

// 保存配置
await UnifiedConfigAPI.saveUnifiedConfig(config)

// 验证配置
await UnifiedConfigAPI.validateConfig(config)
```

#### 2.3 TTS语音合成相关
**文件位置**: `PPTist/src/components/`
- `TTSConfig.vue`: TTS配置组件
- `EdgeTTSConfig.vue`: Edge TTS配置
- `FishTTSConfig.vue`: Fish TTS配置

**主要API调用**:
```typescript
// 获取语音列表
const voices = await ttsService.getVoices()

// 语音合成
await ttsService.synthesize(text, voice, options)
```

#### 2.4 项目管理相关
**文件位置**: `PPTist/src/components/`
- `ProjectManager.vue`: 项目管理器
- `EnhancedProjectManager.vue`: 增强项目管理器

**主要API调用**:
```typescript
// 保存项目到后端
await projectService.saveProject(projectData)

// 加载项目列表
const projects = await projectService.getProjects()
```

### 3. API配置

#### 3.1 环境配置
**文件**: `PPTist/src/config/env.ts`
```typescript
export const API_CONFIG = {
  primary: {
    baseURL: 'http://localhost:5000/api',
    timeout: 30000
  },
  fallback: {
    baseURL: 'http://localhost:8001/api',
    timeout: 15000
  }
}
```

#### 3.2 请求拦截器
**文件**: `PPTist/src/api/interceptors.ts`
- 请求前处理（认证、格式化）
- 响应后处理（错误处理、数据转换）
- 错误处理（重试、降级）

---

## 📋 前后端集成实现计划

### 阶段一：基础连通性（1-2天）

#### 任务1.1: 后端基础API完善
- [ ] 完善健康检查接口 `/api/health`
- [ ] 统一错误响应格式
- [ ] 添加CORS支持
- [ ] 配置接口文档

**预期结果**: 后端API能够正常响应基础请求

#### 任务1.2: 前端API配置
- [ ] 配置后端API地址
- [ ] 测试基础连通性
- [ ] 实现错误处理机制
- [ ] 添加请求日志

**预期结果**: 前端能够成功调用后端健康检查接口

### 阶段二：配置管理集成（2-3天）

#### 任务2.1: 后端配置API实现
- [ ] 实现 `/api/config` 获取配置
- [ ] 实现 `/api/config` 保存配置  
- [ ] 实现配置验证逻辑
- [ ] 添加配置预设支持

#### 任务2.2: 前端配置集成
- [ ] 修改 `UnifiedConfig.vue` 调用后端API
- [ ] 实现配置同步机制
- [ ] 添加配置验证反馈
- [ ] 实现本地配置缓存

**预期结果**: 前端配置页面能够正常读取和保存配置到后端

### 阶段三：PPT数据交互（3-4天）

#### 任务3.1: PPTist数据导入导出
- [ ] 实现 `/api/pptist/import` PPT数据导入
- [ ] 实现 `/api/pptist/export` PPT数据导出
- [ ] 处理PPT格式转换
- [ ] 添加数据验证

#### 任务3.2: 前端PPT集成
- [ ] 修改PPT保存逻辑调用后端
- [ ] 实现PPT数据同步
- [ ] 添加导入导出功能
- [ ] 处理数据格式兼容

**预期结果**: PPTist编辑的PPT能够保存到后端，并支持导入导出

### 阶段四：TTS语音合成集成（2-3天）

#### 任务4.1: 后端TTS API
- [ ] 实现 `/api/tts/voices` 获取语音列表
- [ ] 实现 `/api/tts/synthesize` 语音合成
- [ ] 实现 `/api/tts/batch` 批量合成
- [ ] 添加TTS配置管理

#### 任务4.2: 前端TTS集成  
- [ ] 修改TTS配置组件调用后端
- [ ] 实现语音预览功能
- [ ] 添加合成进度显示
- [ ] 处理音频文件管理

**预期结果**: 前端TTS配置能够正常工作，支持语音合成和预览

### 阶段五：视频导出工作流（4-5天）

#### 任务5.1: 后端工作流引擎
- [ ] 实现 `/api/workflow/start` 启动工作流
- [ ] 实现 `/api/workflow/progress` 进度追踪
- [ ] 实现 `/api/workflow/status` 状态查询
- [ ] 添加工作流控制（暂停/停止）

#### 任务5.2: 前端工作流集成
- [ ] 修改视频导出流程调用后端
- [ ] 实现实时进度显示
- [ ] 添加导出状态管理
- [ ] 处理导出结果下载

**预期结果**: 完整的PPT转视频工作流能够正常运行

### 阶段六：高级功能集成（3-4天）

#### 任务6.1: 智能字幕功能
- [ ] 实现字幕生成API
- [ ] 集成AI内容分析
- [ ] 添加字幕优化功能
- [ ] 实现多语言支持

#### 任务6.2: 项目管理功能
- [ ] 实现项目CRUD API
- [ ] 添加项目版本管理
- [ ] 实现项目分享功能
- [ ] 添加项目备份恢复

**预期结果**: 完整的项目管理和高级功能正常工作

### 阶段七：测试与优化（2-3天）

#### 任务7.1: 集成测试
- [ ] 端到端功能测试
- [ ] 性能测试与优化
- [ ] 错误处理测试
- [ ] 并发访问测试

#### 任务7.2: 用户体验优化
- [ ] 加载状态优化
- [ ] 错误提示优化
- [ ] 响应速度优化
- [ ] 界面交互优化

**预期结果**: 整个系统稳定运行，用户体验良好

---

## 🔧 技术规范

### 1. API响应格式
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "code": 200,
  "timestamp": "2025-09-11T10:30:00Z"
}
```

### 2. 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "请求参数错误",
    "details": "具体错误信息"
  },
  "timestamp": "2025-09-11T10:30:00Z"
}
```

### 3. 认证方式
- 使用JWT Token认证
- 支持API Key认证
- 会话超时处理

### 4. 请求限制
- 普通接口：1000次/小时
- 文件上传：100次/小时
- 工作流启动：10次/小时

---

## 📝 开发注意事项

### 1. 前端开发
- 使用TypeScript严格模式
- 遵循Vue 3 Composition API规范
- 使用Pinia状态管理
- 统一使用API服务类

### 2. 后端开发
- 遵循RESTful API设计
- 使用Flask-RESTX文档自动生成
- 统一异常处理和日志记录
- 支持异步任务处理

### 3. 数据库设计
- 使用SQLite/PostgreSQL
- 支持数据迁移
- 添加必要的索引
- 定期备份数据

### 4. 部署配置
- 支持Docker容器化
- 配置负载均衡
- 添加监控和日志
- 支持自动扩缩容

---

## 🚀 快速开始

### 1. 后端启动
```bash
cd flask_backend
python app.py
```

### 2. 前端启动
```bash
cd PPTist
npm install
npm run dev
```

### 3. 测试连通性
```bash
curl http://localhost:5000/api/health
```

---

## 📊 进度跟踪

| 阶段 | 任务 | 状态 | 预计完成时间 |
|------|------|------|--------------|
| 阶段一 | 基础连通性 | ⏳ 进行中 | 2天 |
| 阶段二 | 配置管理集成 | ⏸️ 待开始 | 3天 |
| 阶段三 | PPT数据交互 | ⏸️ 待开始 | 4天 |
| 阶段四 | TTS语音合成 | ⏸️ 待开始 | 3天 |
| 阶段五 | 视频导出工作流 | ⏸️ 待开始 | 5天 |
| 阶段六 | 高级功能集成 | ⏸️ 待开始 | 4天 |
| 阶段七 | 测试与优化 | ⏸️ 待开始 | 3天 |

**总预计时间**: 24-26天

---

*文档最后更新: 2025年9月11日*
