<template>
  <div class="section">
    <div class="section-header">
      <h3>任务管理</h3>
      <p>查看和管理所有音频处理任务</p>
    </div>

    <div class="task-controls">
      <div class="filter-controls">
        <select v-model="statusFilter" class="filter-select">
          <option value="all">所有状态</option>
          <option value="pending">等待中</option>
          <option value="running">进行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        
        <button class="btn-secondary" @click="refreshTasks">
          <i>🔄</i>
          刷新
        </button>
        
        <button class="btn-danger" @click="clearCompletedTasks">
          <i>🗑️</i>
          清除已完成
        </button>
      </div>
      
      <div class="task-stats">
        <div class="stat-item">
          <span class="stat-label">总任务</span>
          <span class="stat-value">{{ tasks.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">进行中</span>
          <span class="stat-value running">{{ runningTasks.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已完成</span>
          <span class="stat-value completed">{{ completedTasks.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">失败</span>
          <span class="stat-value failed">{{ failedTasks.length }}</span>
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="task-list">
      <div v-if="filteredTasks.length === 0" class="no-tasks">
        <i class="no-tasks-icon">📋</i>
        <p>{{ statusFilter === 'all' ? '暂无任务' : `暂无${getStatusText(statusFilter)}任务` }}</p>
      </div>

      <div 
        v-for="task in filteredTasks" 
        :key="task.id"
        class="task-card"
        :class="{ 'task-running': task.status === 'running' }"
      >
        <div class="task-header">
          <div class="task-info">
            <h4 class="task-title">{{ task.title }}</h4>
            <div class="task-meta">
              <span class="task-file">{{ task.file_name }}</span>
              <span class="task-time">{{ formatTime(task.created_at) }}</span>
            </div>
          </div>
          
          <div class="task-status">
            <span class="status-badge" :class="task.status">
              {{ getStatusText(task.status) }}
            </span>
          </div>
        </div>

        <div class="task-content">
          <!-- 进行中的任务显示进度 -->
          <div v-if="task.status === 'running'" class="task-progress">
            <div class="progress-info">
              <span class="progress-text">{{ task.current_step || '处理中...' }}</span>
              <span class="progress-percentage">{{ task.progress || 0 }}%</span>
            </div>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: (task.progress || 0) + '%' }"
              ></div>
            </div>
            <div class="progress-details">
              <span>已用时间: {{ formatDuration(task.elapsed_time || 0) }}</span>
              <span v-if="task.estimated_time">
                预计剩余: {{ formatDuration((task.estimated_time - task.elapsed_time) || 0) }}
              </span>
            </div>
          </div>

          <!-- 已完成的任务显示结果 -->
          <div v-else-if="task.status === 'completed'" class="task-result">
            <div class="result-summary">
              <div class="result-item">
                <span class="label">处理时间</span>
                <span class="value">{{ formatDuration(task.processing_time) }}</span>
              </div>
              <div class="result-item">
                <span class="label">文件大小</span>
                <span class="value">{{ formatFileSize(task.output_size) }}</span>
              </div>
              <div class="result-item">
                <span class="label">改进效果</span>
                <span class="value">{{ task.improvements?.join(', ') || '无' }}</span>
              </div>
            </div>
            
            <div class="result-actions">
              <button class="btn-primary" @click="downloadResult(task)">
                <i>⬇️</i>
                下载结果
              </button>
              <button class="btn-secondary" @click="previewResult(task)">
                <i>👁️</i>
                预览
              </button>
            </div>
          </div>

          <!-- 失败的任务显示错误信息 -->
          <div v-else-if="task.status === 'failed'" class="task-error">
            <div class="error-info">
              <span class="error-label">错误信息:</span>
              <span class="error-message">{{ task.error_message || '未知错误' }}</span>
            </div>
            <div class="error-actions">
              <button class="btn-warning" @click="retryTask(task)">
                <i>🔄</i>
                重试
              </button>
              <button class="btn-secondary" @click="viewErrorDetails(task)">
                <i>📋</i>
                详情
              </button>
            </div>
          </div>

          <!-- 等待中的任务 -->
          <div v-else class="task-pending">
            <div class="pending-info">
              <span>任务排队中，预计等待时间: {{ estimateWaitTime(task) }}</span>
            </div>
            <div class="pending-actions">
              <button class="btn-danger" @click="cancelTask(task)">
                <i>❌</i>
                取消任务
              </button>
            </div>
          </div>
        </div>

        <!-- 任务操作菜单 -->
        <div class="task-actions">
          <button 
            class="action-btn" 
            @click="toggleTaskDetails(task.id)"
            :class="{ active: expandedTasks.includes(task.id) }"
          >
            <i>{{ expandedTasks.includes(task.id) ? '🔼' : '🔽' }}</i>
          </button>
          
          <button class="action-btn" @click="deleteTask(task)">
            <i>🗑️</i>
          </button>
        </div>

        <!-- 展开的任务详情 -->
        <div v-if="expandedTasks.includes(task.id)" class="task-details">
          <div class="details-section">
            <h5>任务配置</h5>
            <div class="config-grid">
              <div class="config-item">
                <span class="label">处理选项</span>
                <span class="value">{{ formatProcessingOptions(task.options) }}</span>
              </div>
              <div class="config-item">
                <span class="label">输出格式</span>
                <span class="value">{{ task.output_format?.toUpperCase() || 'N/A' }}</span>
              </div>
              <div class="config-item">
                <span class="label">质量等级</span>
                <span class="value">{{ task.quality_level || 'N/A' }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="task.log" class="details-section">
            <h5>处理日志</h5>
            <div class="log-content">
              <pre>{{ task.log }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 预览模态框 -->
    <div v-if="previewTask" class="modal-overlay" @click="closePreview">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>音频预览</h4>
          <button class="close-btn" @click="closePreview">✕</button>
        </div>
        <div class="modal-body">
          <div class="preview-info">
            <h5>{{ previewTask.file_name }}</h5>
            <p>处理完成时间: {{ formatTime(previewTask.completed_at) }}</p>
          </div>
          <audio controls class="preview-audio">
            <source :src="previewTask.output_url" type="audio/mpeg">
            您的浏览器不支持音频播放
          </audio>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'AudioTaskManager',
  emits: ['task-deleted', 'task-retried'],
  setup(props, { emit }) {
    const tasks = ref([])
    const statusFilter = ref('all')
    const expandedTasks = ref([])
    const previewTask = ref(null)
    const loading = ref(false)

    const filteredTasks = computed(() => {
      if (statusFilter.value === 'all') {
        return tasks.value
      }
      return tasks.value.filter(task => task.status === statusFilter.value)
    })

    const runningTasks = computed(() => {
      return tasks.value.filter(task => task.status === 'running')
    })

    const completedTasks = computed(() => {
      return tasks.value.filter(task => task.status === 'completed')
    })

    const failedTasks = computed(() => {
      return tasks.value.filter(task => task.status === 'failed')
    })

    const loadTasks = async () => {
      loading.value = true
      try {
        const response = await fetch('/api/audio/tasks')
        if (response.ok) {
          const data = await response.json()
          tasks.value = data.tasks || []
        }
      }
      catch (error) {
        // 加载任务失败
      }
      finally {
        loading.value = false
      }
    }

    const refreshTasks = () => {
      loadTasks()
    }

    const clearCompletedTasks = async () => {
      const completedIds = completedTasks.value.map(task => task.id)
      if (completedIds.length === 0) return

      try {
        for (const id of completedIds) {
          await fetch(`/api/audio/task/${id}`, { method: 'DELETE' })
        }
        await loadTasks()
      }
      catch (error) {
        // 清除任务失败
      }
    }

    const downloadResult = (task) => {
      if (!task.output_url) return

      const link = document.createElement('a')
      link.href = task.output_url
      link.download = `processed_${task.file_name}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    const previewResult = (task) => {
      previewTask.value = task
    }

    const closePreview = () => {
      previewTask.value = null
    }

    const retryTask = async (task) => {
      try {
        const response = await fetch(`/api/audio/task/${task.id}/retry`, {
          method: 'POST'
        })
        
        if (response.ok) {
          emit('task-retried', task)
          await loadTasks()
        }
      }
      catch (error) {
        // 重试任务失败
      }
    }

    const cancelTask = async (task) => {
      try {
        const response = await fetch(`/api/audio/task/${task.id}/cancel`, {
          method: 'POST'
        })
        
        if (response.ok) {
          await loadTasks()
        }
      }
      catch (error) {
        // 取消任务失败
      }
    }

    const deleteTask = async (task) => {
      // 这里应该使用更好的用户确认方式，比如模态框
      const shouldDelete = true // 简化处理
      if (!shouldDelete) {
        return
      }

      try {
        const response = await fetch(`/api/audio/task/${task.id}`, {
          method: 'DELETE'
        })
        
        if (response.ok) {
          emit('task-deleted', task)
          await loadTasks()
        }
      }
      catch (error) {
        // 删除任务失败
      }
    }

    const toggleTaskDetails = (taskId) => {
      const index = expandedTasks.value.indexOf(taskId)
      if (index === -1) {
        expandedTasks.value.push(taskId)
      }
      else {
        expandedTasks.value.splice(index, 1)
      }
    }

    const viewErrorDetails = () => {
      // TODO: 实现错误详情模态框
    }

    const getStatusText = (status) => {
      const statusMap = {
        pending: '等待中',
        running: '进行中',
        completed: '已完成',
        failed: '失败',
        cancelled: '已取消'
      }
      return statusMap[status] || status
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return 'N/A'
      return new Date(timestamp).toLocaleString()
    }

    const formatDuration = (seconds) => {
      if (!seconds) return '0s'
      const hrs = Math.floor(seconds / 3600)
      const mins = Math.floor((seconds % 3600) / 60)
      const secs = Math.floor(seconds % 60)
      
      if (hrs > 0) {
        return `${hrs}h ${mins}m ${secs}s`
      }
      if (mins > 0) {
        return `${mins}m ${secs}s`
      }
      return `${secs}s`
    }

    const formatFileSize = (bytes) => {
      if (!bytes) return 'N/A'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatProcessingOptions = (options) => {
      if (!options) return 'N/A'
      const selected = Object.keys(options).filter(key => options[key])
      return selected.length > 0 ? selected.join(', ') : '无'
    }

    const estimateWaitTime = (task) => {
      const queuePosition = tasks.value
        .filter(t => t.status === 'pending' && t.created_at < task.created_at)
        .length
      
      const avgProcessingTime = 120 // 假设平均处理时间2分钟
      const estimatedSeconds = queuePosition * avgProcessingTime
      
      return formatDuration(estimatedSeconds)
    }

    onMounted(() => {
      loadTasks()
      
      // 设置定时刷新进行中的任务
      const refreshInterval = setInterval(() => {
        if (runningTasks.value.length > 0) {
          loadTasks()
        }
      }, 5000) // 每5秒刷新一次

      // 组件卸载时清理定时器
      return () => {
        clearInterval(refreshInterval)
      }
    })

    return {
      tasks,
      statusFilter,
      expandedTasks,
      previewTask,
      loading,
      filteredTasks,
      runningTasks,
      completedTasks,
      failedTasks,
      refreshTasks,
      clearCompletedTasks,
      downloadResult,
      previewResult,
      closePreview,
      retryTask,
      cancelTask,
      deleteTask,
      toggleTaskDetails,
      viewErrorDetails,
      getStatusText,
      formatTime,
      formatDuration,
      formatFileSize,
      formatProcessingOptions,
      estimateWaitTime
    }
  }
}
</script>

<style scoped>
.section {
  margin-bottom: 2rem;
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-header h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.section-header p {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.task-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.filter-select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  color: #2c3e50;
  font-size: 0.9rem;
}

.btn-secondary, .btn-danger {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-danger:hover {
  background: #c0392b;
}

.task-stats {
  display: flex;
  gap: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #ecf0f1;
  min-width: 60px;
}

.stat-label {
  font-size: 0.75rem;
  color: #7f8c8d;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.stat-value.running {
  color: #f39c12;
}

.stat-value.completed {
  color: #27ae60;
}

.stat-value.failed {
  color: #e74c3c;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.no-tasks {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
  background: #f8f9fa;
  border-radius: 12px;
}

.no-tasks-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  display: block;
}

.task-card {
  background: white;
  border: 1px solid #ecf0f1;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.task-card.task-running {
  border-left: 4px solid #f39c12;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  border-bottom: 1px solid #ecf0f1;
}

.task-info {
  flex: 1;
}

.task-title {
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

.task-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #7f8c8d;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge.pending {
  background: #f8f9fa;
  color: #6c757d;
}

.status-badge.running {
  background: #fff3cd;
  color: #856404;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.task-content {
  padding: 1rem;
}

.task-progress {
  margin-bottom: 1rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.progress-text {
  color: #2c3e50;
}

.progress-percentage {
  color: #f39c12;
  font-weight: 600;
}

.progress-bar {
  height: 6px;
  background: #ecf0f1;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: #f39c12;
  transition: width 0.3s ease;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #7f8c8d;
}

.task-result {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.result-item .label {
  font-size: 0.8rem;
  color: #7f8c8d;
}

.result-item .value {
  font-size: 0.9rem;
  color: #2c3e50;
  font-weight: 500;
}

.result-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-primary, .btn-warning {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
}

.btn-warning {
  background: #f39c12;
  color: white;
}

.btn-warning:hover {
  background: #e67e22;
}

.task-error {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.error-info {
  padding: 0.75rem;
  background: #fdf2f2;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
}

.error-label {
  font-weight: 500;
  color: #721c24;
  margin-right: 0.5rem;
}

.error-message {
  color: #e74c3c;
}

.error-actions {
  display: flex;
  gap: 0.75rem;
}

.task-pending {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pending-info {
  font-size: 0.9rem;
  color: #7f8c8d;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.pending-actions {
  display: flex;
  gap: 0.75rem;
}

.task-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid #ecf0f1;
  background: #fafbfc;
}

.action-btn {
  padding: 0.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: transparent;
  color: #7f8c8d;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: #ecf0f1;
  color: #2c3e50;
}

.action-btn.active {
  color: #3498db;
}

.task-details {
  border-top: 1px solid #ecf0f1;
  background: #fafbfc;
}

.details-section {
  padding: 1rem;
  border-bottom: 1px solid #ecf0f1;
}

.details-section:last-child {
  border-bottom: none;
}

.details-section h5 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.config-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #ecf0f1;
}

.config-item .label {
  color: #7f8c8d;
  font-size: 0.85rem;
}

.config-item .value {
  color: #2c3e50;
  font-size: 0.85rem;
  font-weight: 500;
}

.log-content {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 1rem;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.8rem;
  max-height: 200px;
  overflow-y: auto;
}

.log-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #ecf0f1;
}

.modal-header h4 { color: #2c3e50; margin: 0; }
.close-btn { background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #7f8c8d; padding: 0.25rem; border-radius: 4px; transition: all 0.3s ease; }
.close-btn:hover { background: #ecf0f1; color: #2c3e50; }
.modal-body { padding: 1.5rem; }
.preview-info { margin-bottom: 1rem; }
.preview-info h5 { color: #2c3e50; margin-bottom: 0.5rem; }
.preview-info p { color: #7f8c8d; font-size: 0.9rem; margin: 0; }
.preview-audio { width: 100%; height: 40px; }
</style>
