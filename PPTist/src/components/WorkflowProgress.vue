<template>
  <!-- 添加遮罩层和模态框结构 -->
  <div class="workflow-progress-overlay" @click="handleClose">
    <div class="workflow-progress-modal" @click.stop>
      <div class="modal-header">
        <h2>视频生成进度</h2>
        <button @click="handleClose" class="close-btn">✕</button>
      </div>
      
      <div class="modal-content">
        <div class="progress-info">
          <div class="status">状态: {{ status.status }}</div>
          <div class="step">当前步骤: {{ status.step }}</div>
          <div class="message">{{ status.message }}</div>
        </div>
        
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: status.progress + '%' }"></div>
        </div>
        <div class="progress-text">{{ status.progress }}%</div>
        
        <div v-if="status.status === 'completed' && status.result" class="result-section">
          <div class="success-message">✅ 视频生成完成！</div>
          <button @click="handleDownload" class="download-btn">下载视频</button>
        </div>
        
        <div v-if="status.status === 'error'" class="error-section">
          <div class="error-message">❌ 生成失败: {{ status.message }}</div>
          <button @click="handleClose" class="retry-btn">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive, onMounted, onUnmounted } from 'vue'
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

// 状态数据
const status = reactive({
  status: 'idle' as 'idle' | 'running' | 'completed' | 'error',
  progress: 0,
  step: '准备中...',
  message: '正在初始化工作流',
  result: null as any
})

let timer: ReturnType<typeof setInterval> | null = null

// 获取工作流状态 - 使用正确的API endpoint
const checkStatus = async () => {
  try {
    // 使用workflow_id查询状态
    const response = await fetch(`${API_BASE_URL}/api/workflow/status/${props.workflowId}`)
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // 转换API响应格式到组件需要的格式
        const workflow = data.workflow
        status.status = workflow.status === 'completed' ? 'completed' : 
          workflow.status === 'failed' ? 'error' : 'running'
        status.progress = Math.round((workflow.current_step / workflow.total_steps) * 100)
        status.step = workflow.steps?.[workflow.current_step]?.name || '处理中...'
        status.message = workflow.steps?.[workflow.current_step]?.message || ''
        status.result = workflow.final_video ? { project_name: workflow.project_name } : null
      }
    }
  } 
  catch (error) {
    // 忽略错误,避免控制台输出
  }
}

// 事件处理
const handleClose = () => {
  if (timer) {
    clearInterval(timer)
  }
  emit('close')
}

const handleDownload = () => {
  if (status.result?.project_name) {
    emit('download', status.result.project_name)
  }
}

// 组件挂载时开始轮询
onMounted(() => {
  checkStatus()
  timer = setInterval(checkStatus, 2000) // 每2秒检查一次
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style lang="scss" scoped>
/* 遮罩层样式 */
.workflow-progress-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 99999 !important;
  animation: fadeIn 0.3s ease-out;
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 模态框样式 */
.workflow-progress-modal {
  background: white !important;
  border-radius: 20px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  width: 90% !important;
  max-width: 700px !important;
  min-width: 500px !important;
  max-height: 85vh !important;
  min-height: 400px !important;
  overflow: hidden;
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative !important;
  margin: 0 !important;
  transform: none !important;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(50px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 模态框头部 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  
  h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
  }
  
  .close-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 24px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: rotate(90deg);
    }
  }
}

/* 模态框内容区 */
.modal-content {
  padding: 28px;
  
  .progress-info {
    margin-bottom: 24px;
    
    div {
      margin-bottom: 10px;
      font-size: 14px;
      
      &.status {
        font-weight: 600;
        font-size: 16px;
        color: #667eea;
      }
      
      &.step {
        color: #666;
        font-weight: 500;
      }
      
      &.message {
        color: #999;
        font-size: 13px;
      }
    }
  }
  
  .progress-bar {
    width: 100%;
    height: 12px;
    background: #f0f0f0;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 8px;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea, #764ba2);
      transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
  }
  
  .progress-text {
    text-align: center;
    font-size: 14px;
    color: #666;
    font-weight: 500;
    margin-bottom: 24px;
  }
  
  .result-section {
    text-align: center;
    padding: 20px 0;
    
    .success-message {
      color: #52c41a;
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 20px;
    }
    
    .download-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 12px 32px;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
      }
      
      &:active {
        transform: translateY(0);
      }
    }
  }
  
  .error-section {
    text-align: center;
    padding: 20px 0;
    
    .error-message {
      color: #ff4d4f;
      font-size: 15px;
      margin-bottom: 20px;
    }
    
    .retry-btn {
      background: #f5f5f5;
      color: #666;
      border: none;
      padding: 10px 24px;
      border-radius: 8px;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
      
      &:hover {
        background: #e8e8e8;
      }
    }
  }
}
</style>
