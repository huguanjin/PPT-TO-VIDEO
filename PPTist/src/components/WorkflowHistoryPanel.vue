<template>
  <div class="workflow-history-panel" :class="{ collapsed: isCollapsed }">
    <!-- 折叠按钮 -->
    <div class="toggle-button" @click="togglePanel">
      <span class="icon">{{ isCollapsed ? '📋' : '❌' }}</span>
      <span v-if="!isCollapsed" class="title">任务历史</span>
    </div>
    
    <!-- 面板内容 -->
    <div v-if="!isCollapsed" class="panel-content">
      <div class="header">
        <h3>工作流任务</h3>
        <button @click="refreshTasks" class="refresh-btn" :disabled="isLoading">
          {{ isLoading ? '⏳' : '🔄' }}
        </button>
      </div>
      
      <div class="task-list">
        <div v-if="tasks.length === 0" class="empty-state">
          <p>暂无任务记录</p>
        </div>
        
        <div 
          v-for="task in tasks" 
          :key="task.task_id"
          class="task-item"
          :class="task.status"
          @click="viewTaskProgress(task.task_id)"
        >
          <div class="task-header">
            <span class="status-icon">{{ getStatusIcon(task.status) }}</span>
            <span class="task-name">{{ task.project_name || 'unnamed' }}</span>
          </div>
          
          <div class="task-info">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
            </div>
            <span class="progress-text">{{ task.progress }}%</span>
          </div>
          
          <div class="task-meta">
            <span class="step">{{ task.current_step }}/{{ task.total_steps }}</span>
            <span class="time">{{ formatTime(task.updated_at) }}</span>
          </div>
        </div>
      </div>
      
      <div class="panel-footer">
        <button @click="cleanupTasks" class="cleanup-btn">
          🗑️ 清理已完成
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useWorkflowStore } from '@/store'
import { API_BASE_URL } from '@/config/api'

const workflowStore = useWorkflowStore()

const isCollapsed = ref(true)
const isLoading = ref(false)
const tasks = ref<any[]>([])

let refreshTimer: ReturnType<typeof setInterval> | null = null

// 切换面板
const togglePanel = () => {
  isCollapsed.value = !isCollapsed.value
  if (!isCollapsed.value) {
    refreshTasks()
    // 开始自动刷新
    refreshTimer = setInterval(refreshTasks, 3000)
  } 
  else {
    // 停止自动刷新
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }
}

// 获取任务列表
const refreshTasks = async () => {
  if (isLoading.value) return
  
  try {
    isLoading.value = true
    const response = await fetch(`${API_BASE_URL}/api/workflow/list`)
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // 转换为数组并排序(最新的在前)
        const taskList = Object.entries(data.data.workflows || {}).map(([id, task]: [string, any]) => ({
          task_id: id,
          ...task
        }))
        taskList.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
        tasks.value = taskList
      }
    }
  } 
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('获取任务列表失败:', error)
  } 
  finally {
    isLoading.value = false
  }
}

// 查看任务进度
const viewTaskProgress = (taskId: string) => {
  workflowStore.showWorkflowProgress(taskId)
}

// 清理已完成任务
const cleanupTasks = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/workflow/cleanup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        types: ['completed', 'failed']
      })
    })
    
    if (response.ok) {
      await refreshTasks()
    }
  } 
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('清理任务失败:', error)
  }
}

// 状态图标
const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    'pending': '⏳',
    'running': '▶️',
    'completed': '✅',
    'failed': '❌'
  }
  return icons[status] || '❓'
}

// 格式化时间
const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString()
}

// 组件挂载
onMounted(() => {
  // 不自动展开,等用户点击
})

// 组件卸载
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style lang="scss" scoped>
.workflow-history-panel {
  position: fixed;
  right: 20px;
  top: 100px;
  z-index: 9998;
  transition: all 0.3s ease;
  
  &.collapsed {
    width: 60px;
    height: 60px;
  }
}

.toggle-button {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  overflow: hidden;
  
  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
  }
  
  .icon {
    font-size: 24px;
    flex-shrink: 0;
  }
  
  .title {
    color: white;
    font-weight: bold;
    margin-left: 8px;
    white-space: nowrap;
  }
}

.collapsed .toggle-button {
  width: 60px;
}

.panel-content {
  position: absolute;
  top: 0;
  right: 0;
  width: 400px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  
  h3 {
    margin: 0;
    font-size: 18px;
  }
  
  .refresh-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.3);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.task-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  
  p {
    margin: 0;
  }
}

.task-item {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 4px solid #ddd;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  &.running {
    border-left-color: #667eea;
    background: linear-gradient(to right, rgba(102, 126, 234, 0.05), #f8f9fa);
  }
  
  &.completed {
    border-left-color: #51cf66;
  }
  
  &.failed {
    border-left-color: #ff6b6b;
  }
}

.task-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  
  .status-icon {
    font-size: 20px;
  }
  
  .task-name {
    font-weight: 600;
    font-size: 14px;
    color: #333;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  
  .progress-bar {
    flex: 1;
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea, #764ba2);
      transition: width 0.3s ease;
    }
  }
  
  .progress-text {
    font-size: 12px;
    color: #666;
    min-width: 40px;
    text-align: right;
  }
}

.task-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  
  .step {
    font-weight: 500;
  }
}

.panel-footer {
  padding: 12px 20px;
  border-top: 1px solid #e9ecef;
  
  .cleanup-btn {
    width: 100%;
    padding: 10px;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s ease;
    
    &:hover {
      background: #e9ecef;
      border-color: #ced4da;
    }
  }
}
</style>
