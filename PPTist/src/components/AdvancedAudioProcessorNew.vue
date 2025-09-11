<template>
  <div class="advanced-audio-processor">
    <!-- 头部标题 -->
    <div class="header-section">
      <h2 class="title">
        <i class="icon-audio">🎵</i>
        高级音频处理系统
      </h2>
      <p class="subtitle">Netflix级别的专业音频处理和优化</p>
    </div>

    <!-- 功能选项卡 -->
    <div class="tabs-container">
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['tab-button', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <i :class="tab.icon"></i>
          {{ tab.name }}
        </button>
      </div>
    </div>

    <!-- 上传区域 -->
    <AudioUpload 
      v-if="activeTab === 'upload'"
      :supported-formats="supportedFormats"
      @file-uploaded="handleFileUploaded"
      @file-removed="handleFileRemoved"
    />

    <!-- 分析区域 -->
    <AudioAnalysis
      v-if="activeTab === 'analyze'"
      :uploaded-file="uploadedFile"
      @analysis-complete="handleAnalysisComplete"
    />

    <!-- 处理区域 -->
    <AudioProcessing
      v-if="activeTab === 'process'"
      :uploaded-file="uploadedFile"
      @processing-complete="handleProcessingComplete"
    />

    <!-- 任务管理 -->
    <AudioTaskManager
      v-if="activeTab === 'tasks'"
      @task-deleted="handleTaskDeleted"
      @task-retried="handleTaskRetried"
    />

    <!-- 系统状态 -->
    <div v-if="activeTab === 'status'" class="section">
      <div class="section-header">
        <h3>系统状态</h3>
        <p>查看音频处理系统的运行状态和性能指标</p>
      </div>
      
      <div class="status-grid">
        <div class="status-card">
          <h4>处理器状态</h4>
          <div class="status-indicator" :class="systemStatus.processor">
            {{ getStatusText(systemStatus.processor) }}
          </div>
          <div class="status-details">
            <span>CPU使用率: {{ systemStatus.cpu_usage }}%</span>
            <span>内存使用: {{ systemStatus.memory_usage }}MB</span>
          </div>
        </div>

        <div class="status-card">
          <h4>任务队列</h4>
          <div class="queue-stats">
            <div class="queue-item">
              <span class="queue-label">等待中</span>
              <span class="queue-count">{{ taskStats.pending }}</span>
            </div>
            <div class="queue-item">
              <span class="queue-label">进行中</span>
              <span class="queue-count running">{{ taskStats.running }}</span>
            </div>
            <div class="queue-item">
              <span class="queue-label">已完成</span>
              <span class="queue-count completed">{{ taskStats.completed }}</span>
            </div>
          </div>
        </div>

        <div class="status-card">
          <h4>性能指标</h4>
          <div class="performance-metrics">
            <div class="metric">
              <span class="metric-label">平均处理时间</span>
              <span class="metric-value">{{ performanceStats.avg_processing_time }}s</span>
            </div>
            <div class="metric">
              <span class="metric-label">成功率</span>
              <span class="metric-value">{{ performanceStats.success_rate }}%</span>
            </div>
            <div class="metric">
              <span class="metric-label">吞吐量</span>
              <span class="metric-value">{{ performanceStats.throughput }}/小时</span>
            </div>
          </div>
        </div>
      </div>

      <div class="system-actions">
        <button class="btn-primary" @click="refreshSystemStatus">
          <i>🔄</i>
          刷新状态
        </button>
        
        <button class="btn-secondary" @click="exportSystemReport">
          <i>📊</i>
          导出报告
        </button>
      </div>
    </div>

    <!-- 全局消息提示 -->
    <div v-if="globalMessage" class="global-message" :class="globalMessage.type">
      <i :class="getMessageIcon(globalMessage.type)"></i>
      <span>{{ globalMessage.text }}</span>
      <button class="close-message" @click="closeGlobalMessage">✕</button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import AudioUpload from './AudioUpload.vue'
import AudioAnalysis from './AudioAnalysis.vue'
import AudioProcessing from './AudioProcessing.vue'
import AudioTaskManager from './AudioTaskManager.vue'

export default {
  name: 'AdvancedAudioProcessorMain',
  components: {
    AudioUpload,
    AudioAnalysis,
    AudioProcessing,
    AudioTaskManager
  },
  setup() {
    const activeTab = ref('upload')
    const uploadedFile = ref(null)
    const globalMessage = ref(null)

    const supportedFormats = ['wav', 'mp3', 'flac', 'aac', 'ogg', 'm4a']

    const tabs = [
      { id: 'upload', name: '文件上传', icon: '📁' },
      { id: 'analyze', name: '音频分析', icon: '🔍' },
      { id: 'process', name: '音频处理', icon: '⚡' },
      { id: 'tasks', name: '任务管理', icon: '📋' },
      { id: 'status', name: '系统状态', icon: '📊' }
    ]

    const systemStatus = reactive({
      processor: 'online',
      cpu_usage: 25,
      memory_usage: 512
    })

    const taskStats = reactive({
      pending: 0,
      running: 1,
      completed: 15
    })

    const performanceStats = reactive({
      avg_processing_time: 45,
      success_rate: 98.5,
      throughput: 24
    })

    const handleFileUploaded = (data) => {
      uploadedFile.value = data.file
      showGlobalMessage('文件上传成功！', 'success')
      
      // 自动切换到分析标签
      setTimeout(() => {
        activeTab.value = 'analyze'
      }, 1000)
    }

    const handleFileRemoved = () => {
      uploadedFile.value = null
      showGlobalMessage('文件已移除', 'info')
    }

    const handleAnalysisComplete = () => {
      showGlobalMessage('音频分析完成！', 'success')
      
      // 可以根据分析结果自动切换到处理标签
      setTimeout(() => {
        activeTab.value = 'process'
      }, 1500)
    }

    const handleProcessingComplete = () => {
      showGlobalMessage('音频处理完成！', 'success')
      
      // 切换到任务管理查看结果
      setTimeout(() => {
        activeTab.value = 'tasks'
      }, 1500)
    }

    const handleTaskDeleted = (task) => {
      showGlobalMessage(`任务 "${task.title}" 已删除`, 'info')
    }

    const handleTaskRetried = (task) => {
      showGlobalMessage(`任务 "${task.title}" 正在重试`, 'info')
    }

    const refreshSystemStatus = async () => {
      try {
        const response = await fetch('/api/audio/system/status')
        if (response.ok) {
          const status = await response.json()
          Object.assign(systemStatus, status.system)
          Object.assign(taskStats, status.tasks)
          Object.assign(performanceStats, status.performance)
          showGlobalMessage('系统状态已刷新', 'success')
        }
      }
      catch (error) {
        showGlobalMessage('刷新系统状态失败', 'error')
      }
    }

    const exportSystemReport = () => {
      const report = {
        timestamp: new Date().toISOString(),
        system_status: systemStatus,
        task_statistics: taskStats,
        performance_metrics: performanceStats
      }

      const blob = new Blob([JSON.stringify(report, null, 2)], {
        type: 'application/json'
      })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audio_system_report_${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      showGlobalMessage('系统报告已导出', 'success')
    }

    const showGlobalMessage = (text, type = 'info') => {
      globalMessage.value = { text, type }
      
      // 3秒后自动关闭
      setTimeout(() => {
        globalMessage.value = null
      }, 3000)
    }

    const closeGlobalMessage = () => {
      globalMessage.value = null
    }

    const getStatusText = (status) => {
      const statusMap = {
        online: '在线',
        offline: '离线',
        error: '错误',
        maintenance: '维护中'
      }
      return statusMap[status] || status
    }

    const getMessageIcon = (type) => {
      const iconMap = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      }
      return iconMap[type] || 'ℹ️'
    }

    onMounted(() => {
      // 初始化系统状态
      refreshSystemStatus()
    })

    return {
      activeTab,
      uploadedFile,
      supportedFormats,
      tabs,
      systemStatus,
      taskStats,
      performanceStats,
      globalMessage,
      handleFileUploaded,
      handleFileRemoved,
      handleAnalysisComplete,
      handleProcessingComplete,
      handleTaskDeleted,
      handleTaskRetried,
      refreshSystemStatus,
      exportSystemReport,
      closeGlobalMessage,
      getStatusText,
      getMessageIcon
    }
  }
}
</script>

<style scoped>
.advanced-audio-processor {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.header-section {
  text-align: center;
  margin-bottom: 2rem;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
}

.title {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.icon-audio {
  font-size: 2rem;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
}

.tabs-container {
  margin-bottom: 2rem;
}

.tabs {
  display: flex;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 0.5rem;
  gap: 0.5rem;
  overflow-x: auto;
}

.tab-button {
  flex: 1;
  padding: 1rem 1.5rem;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.95rem;
  color: #7f8c8d;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.tab-button:hover {
  background: #ecf0f1;
  color: #2c3e50;
}

.tab-button.active {
  background: #3498db;
  color: white;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
}

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

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.status-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #ecf0f1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.status-card h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.status-indicator {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 500;
  margin-bottom: 1rem;
}

.status-indicator.online {
  background: #d4edda;
  color: #155724;
}

.status-indicator.offline {
  background: #f8d7da;
  color: #721c24;
}

.status-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.queue-stats, .performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.queue-item, .metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.queue-label, .metric-label {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.queue-count, .metric-value {
  font-weight: 600;
  color: #2c3e50;
}

.queue-count.running {
  color: #f39c12;
}

.queue-count.completed {
  color: #27ae60;
}

.system-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
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

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.global-message {
  position: fixed;
  top: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease;
}

.global-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.global-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.global-message.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.global-message.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.close-message {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.close-message:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .advanced-audio-processor {
    padding: 1rem;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .tabs {
    flex-direction: column;
  }
  
  .tab-button {
    justify-content: flex-start;
  }
  
  .status-grid {
    grid-template-columns: 1fr;
  }
  
  .global-message {
    top: 1rem;
    right: 1rem;
    left: 1rem;
  }
}
</style>
