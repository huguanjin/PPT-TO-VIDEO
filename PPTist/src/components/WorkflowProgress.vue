<template>
  <!-- 工作流进度浮动窗口 - 可收起 -->
  <div class="workflow-progress-container" :class="{ collapsed: isCollapsed }">
    <div class="progress-window" @click.stop>
      <!-- 标题栏 -->
      <div class="header" @click="toggleCollapse">
        <span class="title">{{ isCollapsed ? '📊' : '📊 视频生成进度' }}</span>
        <div class="header-actions">
          <button @click.stop="toggleCollapse" class="collapse-btn" :title="isCollapsed ? '展开' : '收起'">
            {{ isCollapsed ? '⬆' : '⬇' }}
          </button>
          <button @click.stop="handleClose" class="close-btn" title="关闭">✕</button>
        </div>
      </div>
      
      <!-- 内容区域 - 收起时隐藏 -->
      <div v-show="!isCollapsed" class="content">
        <!-- 项目信息 -->
        <div class="project-info">
          <div class="project-name">{{ workflow.project_name || '未命名项目' }}</div>
          <div class="status-badge" :class="workflow.status">
            {{ getStatusText(workflow.status) }}
          </div>
        </div>
        
        <!-- 总体进度 -->
        <div class="overall-progress">
          <div class="progress-label">
            <span>总进度</span>
            <span class="progress-percent">{{ workflow.progress }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: workflow.progress + '%' }"></div>
          </div>
        </div>
        
        <!-- 步骤详情 -->
        <div class="steps-container">
          <div 
            v-for="(step, index) in workflow.steps" 
            :key="index"
            class="step-item"
            :class="step.status"
          >
            <div class="step-icon">{{ getStepIcon(step.status) }}</div>
            <div class="step-content">
              <div class="step-name">{{ step.name }}</div>
              <div class="step-message">{{ step.message }}</div>
            </div>
            <div class="step-indicator" :class="step.status"></div>
          </div>
        </div>
        
        <!-- 完成/错误状态 -->
        <div v-if="workflow.status === 'completed'" class="result-section success">
          <div class="result-icon">✅</div>
          <div class="result-text">视频生成完成！</div>
          <button @click="handleDownload" class="action-btn download">
            📥 下载视频
          </button>
        </div>
        
        <div v-if="workflow.status === 'failed'" class="result-section error">
          <div class="result-icon">❌</div>
          <div class="result-text">生成失败</div>
          <div class="error-message">{{ workflow.error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import { API_BASE_URL } from '@/config/api'

// Props
const props = defineProps<{
  workflowId: string
}>()

// Events
const emit = defineEmits<{
  close: []
  download: [projectName: string]
}>()

// 状态
const isCollapsed = ref(false)

// 工作流数据
const workflow = reactive({
  project_name: '',
  status: 'pending' as 'pending' | 'running' | 'completed' | 'failed',
  progress: 0,
  current_step: 0,
  total_steps: 5,
  steps: [] as Array<{
    name: string
    status: 'pending' | 'running' | 'completed' | 'failed'
    message: string
  }>,
  error: ''
})

let timer: ReturnType<typeof setInterval> | null = null

// 获取工作流状态
const checkStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/workflow/status/${props.workflowId}`)
    if (response.ok) {
      const data = await response.json()
      if (data.success && data.workflow) {
        const wf = data.workflow
        workflow.project_name = wf.project_name || ''
        workflow.status = wf.status
        workflow.progress = wf.progress || 0
        workflow.current_step = wf.current_step || 0
        workflow.total_steps = wf.total_steps || 5
        workflow.steps = wf.steps || []
        workflow.error = wf.error || ''
        
        // 如果完成或失败,停止轮询
        if (workflow.status === 'completed' || workflow.status === 'failed') {
          if (timer) {
            clearInterval(timer)
            timer = null
          }
        }
      }
    }
  } 
  catch (error) {
    // 静默处理错误
  }
}

// 切换收起/展开
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 关闭
const handleClose = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  emit('close')
}

// 下载
const handleDownload = () => {
  if (workflow.project_name) {
    emit('download', workflow.project_name)
  }
}

// 状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'pending': '⏳ 等待中',
    'running': '▶️ 进行中',
    'completed': '✅ 已完成',
    'failed': '❌ 失败'
  }
  return map[status] || status
}

// 步骤图标
const getStepIcon = (status: string) => {
  const map: Record<string, string> = {
    'pending': '⏸️',
    'running': '▶️',
    'completed': '✅',
    'failed': '❌'
  }
  return map[status] || '⏸️'
}

// 组件挂载
onMounted(() => {
  checkStatus()
  timer = setInterval(checkStatus, 2000) // 每2秒检查一次
})

// 组件卸载
onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})
</script>

<style lang="scss" scoped>
.workflow-progress-container {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 9999;
  animation: slideUp 0.3s ease;
  
  &.collapsed .progress-window {
    height: 60px;
    .content {
      display: none;
    }
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.progress-window {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  width: 450px;
  max-height: 85vh;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  
  .title {
    font-size: 16px;
    font-weight: 600;
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
  }
  
  button {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  }
}

.content {
  padding: 20px;
}

.project-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .project-name {
    font-size: 15px;
    font-weight: 600;
    color: #333;
  }
  
  .status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
    
    &.pending {
      background: #f0f0f0;
      color: #999;
    }
    
    &.running {
      background: #e6f7ff;
      color: #1890ff;
    }
    
    &.completed {
      background: #f6ffed;
      color: #52c41a;
    }
    
    &.failed {
      background: #fff1f0;
      color: #ff4d4f;
    }
  }
}

.overall-progress {
  margin-bottom: 24px;
  
  .progress-label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 14px;
    color: #666;
    
    .progress-percent {
      font-weight: 600;
      color: #667eea;
    }
  }
  
  .progress-bar {
    height: 8px;
    background: #f0f0f0;
    border-radius: 4px;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea, #764ba2);
      transition: width 0.5s ease;
    }
  }
}

.steps-container {
  margin-bottom: 20px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #fafafa;
  transition: all 0.2s;
  
  &.running {
    background: #e6f7ff;
  }
  
  &.completed {
    background: #f6ffed;
  }
  
  &.failed {
    background: #fff1f0;
  }
  
  .step-icon {
    font-size: 18px;
    margin-right: 12px;
    flex-shrink: 0;
  }
  
  .step-content {
    flex: 1;
    
    .step-name {
      font-size: 14px;
      font-weight: 600;
      color: #333;
      margin-bottom: 4px;
    }
    
    .step-message {
      font-size: 12px;
      color: #999;
    }
  }
  
  .step-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-top: 6px;
    
    &.pending {
      background: #d9d9d9;
    }
    
    &.running {
      background: #1890ff;
      animation: pulse 1.5s infinite;
    }
    
    &.completed {
      background: #52c41a;
    }
    
    &.failed {
      background: #ff4d4f;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.result-section {
  text-align: center;
  padding: 20px 0;
  
  .result-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }
  
  .result-text {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
  }
  
  &.success {
    .result-text {
      color: #52c41a;
    }
  }
  
  &.error {
    .result-text {
      color: #ff4d4f;
    }
    
    .error-message {
      font-size: 13px;
      color: #999;
      margin-bottom: 16px;
    }
  }
  
  .action-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
  }
}
</style>
