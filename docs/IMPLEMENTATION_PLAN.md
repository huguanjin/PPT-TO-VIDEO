# PPT转视频项目前后端集成实施计划

## 📋 项目概述

本计划旨在将PPTist前端与Flask后端进行完整集成，实现从PPT编辑到视频生成的完整工作流。

## 🎯 总体目标

1. **建立稳定的前后端通信**
2. **实现完整的PPT转视频工作流**
3. **提供良好的用户体验**
4. **确保系统的可扩展性和维护性**

---

## 📅 详细实施计划

### 第1天：项目准备和环境配置

#### 上午任务（9:00-12:00）
- [ ] **环境检查和配置**
  - 确认Flask后端正常启动（端口5000）
  - 确认PPTist前端正常启动（端口5173）
  - 检查网络连通性和CORS配置
  - 配置开发环境变量

- [ ] **创建基础测试页面**
  ```typescript
  // 新建：PPTist/src/views/ApiTest.vue
  // 功能：测试后端API连接状态
  ```

#### 下午任务（14:00-18:00）
- [ ] **完善后端健康检查接口**
  ```python
  # 文件：flask_backend/app/api/common.py
  @bp.route('/health', methods=['GET'])
  def health():
      return {
          'status': 'ok',
          'timestamp': datetime.now().isoformat(),
          'version': '1.0.0',
          'services': {
              'database': 'ok',
              'tts': 'ok',
              'workflow': 'ok'
          }
      }
  ```

- [ ] **前端API配置**
  ```typescript
  // 修改：PPTist/src/config/env.ts
  export const API_CONFIG = {
    baseURL: 'http://localhost:5000/api',
    timeout: 30000,
    retries: 3
  }
  ```

**预期成果**：前后端能够成功通信，健康检查接口正常工作

---

### 第2天：配置管理系统集成

#### 上午任务（9:00-12:00）
- [ ] **后端配置API实现**
  ```python
  # 文件：flask_backend/app/api/config.py
  
  @bp.route('', methods=['GET'])
  def get_config():
      """获取完整配置"""
      pass
      
  @bp.route('', methods=['POST'])  
  def save_config():
      """保存配置"""
      pass
      
  @bp.route('/<section>', methods=['GET'])
  def get_config_section(section):
      """获取配置段"""
      pass
  ```

#### 下午任务（14:00-18:00）
- [ ] **前端配置页面改造**
  ```typescript
  // 修改：PPTist/src/views/UnifiedConfig.vue
  
  // 替换本地存储调用为API调用
  const loadConfig = async () => {
    const response = await api.get('/config')
    config.value = response.data
  }
  
  const saveConfig = async () => {
    await api.post('/config', config.value)
  }
  ```

- [ ] **配置验证逻辑**
  ```typescript
  // 修改：PPTist/src/api/unifiedConfig.ts
  
  export class UnifiedConfigAPI {
    static async validateConfig(config: UnifiedConfig) {
      return await api.post('/config/validate', config)
    }
  }
  ```

**预期成果**：配置管理完全基于后端，支持读取、保存、验证

---

### 第3天：PPT数据同步机制

#### 上午任务（9:00-12:00）
- [ ] **后端PPT存储API**
  ```python
  # 新建：flask_backend/app/api/pptist.py
  
  @bp.route('/import', methods=['POST'])
  def import_ppt_data():
      """导入PPT数据到后端"""
      pass
      
  @bp.route('/export/<project_id>', methods=['GET'])
  def export_ppt_data(project_id):
      """导出PPT数据"""
      pass
  ```

#### 下午任务（14:00-18:00）  
- [ ] **前端PPT同步逻辑**
  ```typescript
  // 修改：PPTist/src/hooks/useProjectManager.ts
  
  const saveProject = async (projectData: ProjectData) => {
    // 保存到后端
    const result = await api.post('/pptist/import', {
      slides: projectData.slides,
      theme: projectData.theme,
      metadata: projectData.metadata
    })
    
    return result.data.projectId
  }
  ```

- [ ] **项目列表管理**
  ```typescript
  // 修改：PPTist/src/components/ProjectManager.vue
  
  const getProjectList = async () => {
    const response = await api.get('/projects')
    projects.value = response.data.projects
  }
  ```

**预期成果**：PPT数据能够保存到后端，支持项目管理功能

---

### 第4天：TTS语音合成集成

#### 上午任务（9:00-12:00）
- [ ] **后端TTS API实现**
  ```python
  # 文件：flask_backend/app/api/tts.py
  
  @bp.route('/voices', methods=['GET'])
  def get_voices():
      """获取可用语音列表"""
      pass
      
  @bp.route('/synthesize', methods=['POST'])
  def synthesize_speech():
      """语音合成"""
      pass
  ```

#### 下午任务（14:00-18:00）
- [ ] **前端TTS组件改造**
  ```typescript
  // 修改：PPTist/src/components/TTSConfig.vue
  
  const loadVoices = async () => {
    const response = await ttsService.getVoices()
    availableVoices.value = response.data.voices
  }
  
  const previewVoice = async (text: string, voice: string) => {
    const audioUrl = await ttsService.preview(text, voice)
    playAudio(audioUrl)
  }
  ```

- [ ] **TTS服务类完善**
  ```typescript
  // 修改：PPTist/src/api/services/ttsService.ts
  
  export class TTSService {
    async getVoices() {
      return await this.api.get('/tts/voices')
    }
    
    async synthesize(text: string, voice: string, options: TTSOptions) {
      return await this.api.post('/tts/synthesize', {
        text, voice, ...options
      })
    }
  }
  ```

**预期成果**：TTS功能完全基于后端，支持语音预览和合成

---

### 第5天：视频导出工作流基础

#### 上午任务（9:00-12:00）
- [ ] **后端工作流API框架**
  ```python
  # 文件：flask_backend/app/api/workflow.py
  
  @bp.route('/start', methods=['POST'])
  def start_workflow():
      """启动视频生成工作流"""
      pass
      
  @bp.route('/progress/<workflow_id>', methods=['GET'])
  def get_workflow_progress(workflow_id):
      """获取工作流进度"""
      pass
  ```

#### 下午任务（14:00-18:00）
- [ ] **前端导出按钮改造**
  ```typescript
  // 修改：PPTist/src/components/VideoExportButton.vue
  
  const startExport = async () => {
    // 启动后端工作流
    const workflowId = await workflowService.start({
      projectId: currentProject.value.id,
      config: exportConfig.value
    })
    
    // 监控进度
    monitorProgress(workflowId)
  }
  ```

- [ ] **进度监控组件**
  ```typescript
  // 修改：PPTist/src/components/WorkflowProgress.vue
  
  const monitorProgress = async (workflowId: string) => {
    const interval = setInterval(async () => {
      const progress = await workflowService.getProgress(workflowId)
      updateProgress(progress)
      
      if (progress.status === 'completed') {
        clearInterval(interval)
        handleComplete(progress.result)
      }
    }, 1000)
  }
  ```

**预期成果**：基础的视频导出工作流能够启动和监控进度

---

### 第6-7天：工作流引擎实现

#### 第6天任务
- [ ] **后端工作流引擎核心**
  ```python
  # 新建：flask_backend/core/workflow_engine.py
  
  class VideoExportWorkflow:
      def __init__(self, project_data, config):
          self.project_data = project_data
          self.config = config
          
      async def execute(self):
          # 步骤1：生成幻灯片图片
          await self.generate_slides()
          
          # 步骤2：生成语音文件  
          await self.generate_audio()
          
          # 步骤3：合成视频
          await self.compose_video()
  ```

#### 第7天任务
- [ ] **任务调度和进度追踪**
  ```python
  # 新建：flask_backend/utils/task_manager.py
  
  class TaskManager:
      def __init__(self):
          self.tasks = {}
          
      def start_task(self, task_id, workflow):
          # 异步执行工作流
          pass
          
      def get_progress(self, task_id):
          # 返回任务进度
          pass
  ```

**预期成果**：完整的后端工作流引擎，支持异步任务处理

---

### 第8-9天：高级功能集成

#### 第8天：智能字幕功能
- [ ] **后端字幕API**
- [ ] **前端字幕配置组件**
- [ ] **字幕同步和优化**

#### 第9天：AI功能集成  
- [ ] **AI内容分析API**
- [ ] **智能配置推荐**
- [ ] **内容优化建议**

**预期成果**：智能化功能正常工作，提升用户体验

---

### 第10天：测试和优化

#### 上午任务（9:00-12:00）
- [ ] **端到端测试**
  - 完整工作流测试
  - 错误场景测试
  - 性能测试

#### 下午任务（14:00-18:00）
- [ ] **用户体验优化**
  - 加载状态优化
  - 错误提示完善
  - 界面响应优化

- [ ] **文档完善**
  - API文档更新
  - 用户手册编写
  - 部署指南完善

**预期成果**：系统稳定运行，用户体验良好

---

## 🔧 技术实施细节

### 1. API接口规范

#### 1.1 请求格式
```json
{
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer <token>"
  },
  "body": {
    "data": {...},
    "options": {...}
  }
}
```

#### 1.2 响应格式
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "timestamp": "2025-09-11T10:30:00Z",
  "requestId": "uuid"
}
```

### 2. 错误处理机制

#### 2.1 前端错误处理
```typescript
// PPTist/src/api/interceptors.ts
const errorInterceptor = (error: ApiError) => {
  switch (error.code) {
    case 404:
      showNotification('资源不存在')
      break
    case 500:
      showNotification('服务器错误，请稍后重试')
      break
    default:
      showNotification(error.message)
  }
  
  throw error
}
```

#### 2.2 后端错误处理
```python
# flask_backend/app/__init__.py
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': {
                'code': 404,
                'message': '资源不存在'
            }
        }, 404
```

### 3. 数据同步策略

#### 3.1 实时同步
- 配置变更：立即同步到后端
- PPT编辑：定时自动保存（5秒间隔）
- 工作流状态：实时监控更新

#### 3.2 离线支持
- 本地缓存重要数据
- 网络恢复后自动同步
- 冲突解决机制

### 4. 性能优化

#### 4.1 前端优化
- API请求去重
- 响应数据缓存
- 组件懒加载

#### 4.2 后端优化
- 数据库连接池
- 异步任务处理
- 文件缓存机制

---

## 📊 进度跟踪表

| 天数 | 主要任务 | 完成标准 | 状态 |
|------|----------|----------|------|
| 第1天 | 环境配置和基础连通 | 前后端成功通信 | ⏳ |
| 第2天 | 配置管理集成 | 配置读写正常 | ⏸️ |
| 第3天 | PPT数据同步 | 项目保存加载正常 | ⏸️ |
| 第4天 | TTS功能集成 | 语音合成正常工作 | ⏸️ |
| 第5天 | 视频导出基础 | 工作流启动和监控 | ⏸️ |
| 第6-7天 | 工作流引擎 | 完整视频生成流程 | ⏸️ |
| 第8-9天 | 高级功能 | AI和字幕功能 | ⏸️ |
| 第10天 | 测试优化 | 系统稳定运行 | ⏸️ |

## 🚨 风险和应对

### 1. 技术风险
- **API兼容性问题**
  - 应对：详细的接口测试
  - 预案：版本兼容处理

- **性能瓶颈**
  - 应对：分阶段性能测试
  - 预案：异步处理和缓存优化

### 2. 时间风险
- **开发进度延迟**
  - 应对：每日进度检查
  - 预案：功能优先级调整

- **测试时间不足**
  - 应对：边开发边测试
  - 预案：核心功能优先保证

### 3. 质量风险
- **用户体验问题**
  - 应对：UI/UX持续优化
  - 预案：用户反馈快速响应

---

## 🎯 成功标准

### 1. 功能完整性
- [ ] PPT编辑功能正常
- [ ] 配置管理完善
- [ ] TTS语音合成正常
- [ ] 视频导出成功
- [ ] 项目管理功能

### 2. 性能指标
- [ ] API响应时间 < 2秒
- [ ] 视频生成时间合理
- [ ] 系统稳定性 > 99%
- [ ] 用户界面响应 < 500ms

### 3. 用户体验
- [ ] 界面友好易用
- [ ] 错误提示清晰
- [ ] 操作流程顺畅
- [ ] 帮助文档完整

---

## 📞 每日检查点

### 每日站会（9:00-9:15）
- 昨日完成情况汇报
- 今日计划确认
- 问题和阻塞讨论
- 风险识别和应对

### 每日收尾（17:45-18:00）
- 任务完成度检查
- 代码提交和备份
- 明日计划预览
- 问题记录和总结

---

*计划制定时间：2025年9月11日*  
*预计完成时间：2025年9月21日*
