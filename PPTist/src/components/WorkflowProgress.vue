<template>
  <div class="workflow-progress">
    <div class="progress-header">
      <h3>视频生成进度</h3>
      <button @click="handleClose" class="close-btn">✕</button>
    </div>
    
    <div class="progress-content">
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
</template>

<script lang="ts" setup>
import { reactive, onMounted, onUnmounted } from 'vue'
import { API_BASE_URL } from '@/config/api'

// Props
defineProps<{
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

// 获取工作流状态
const checkStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/workflow/status`)
    if (response.ok) {
      const data = await response.json()
      Object.assign(status, data)
    }
  } 
  catch (error) {
    // 忽略错误，避免控制台输出
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
.workflow-progress {
  width: 500px;
  
  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      font-size: 18px;
      color: #333;
    }
    
    .close-btn {
      background: none;
      border: none;
      font-size: 18px;
      cursor: pointer;
      color: #666;
      padding: 4px;
      border-radius: 4px;
      transition: background-color 0.2s;
      
      &:hover {
        background-color: #f5f5f5;
      }
    }
  }
  
  .progress-content {
    .progress-info {
      margin-bottom: 16px;
      
      div {
        margin-bottom: 8px;
        font-size: 14px;
        
        &.status {
          font-weight: 500;
          color: #1677ff;
        }
        
        &.step {
          color: #666;
        }
        
        &.message {
          color: #999;
          font-size: 13px;
        }
      }
    }
    
    .progress-bar {
      width: 100%;
      height: 8px;
      background: #f0f0f0;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 8px;
      
      .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #1677ff, #69c0ff);
        transition: width 0.3s ease;
      }
    }
    
    .progress-text {
      text-align: center;
      font-size: 14px;
      color: #666;
      margin-bottom: 20px;
    }
    
    .result-section {
      text-align: center;
      
      .success-message {
        color: #52c41a;
        font-size: 16px;
        margin-bottom: 16px;
      }
      
      .download-btn {
        background: #52c41a;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.2s;
        
        &:hover {
          background: #389e0d;
        }
      }
    }
    
    .error-section {
      text-align: center;
      
      .error-message {
        color: #ff4d4f;
        font-size: 14px;
        margin-bottom: 16px;
      }
      
      .retry-btn {
        background: #f5f5f5;
        color: #666;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.2s;
        
        &:hover {
          background: #e8e8e8;
        }
      }
    }
  }
}
</style>
