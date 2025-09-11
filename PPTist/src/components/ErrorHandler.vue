<template>
  <div class="error-handler">
    <!-- 错误提示弹窗 -->
    <div 
      v-if="visibleError" 
      class="error-overlay"
      @click="dismissError"
    >
      <div 
        class="error-dialog"
        @click.stop
      >
        <div class="error-header">
          <h3 class="error-title">
            <Icon :name="getErrorIcon(visibleError.type)" />
            {{ getErrorTitle(visibleError.type) }}
          </h3>
          <button 
            class="close-btn"
            @click="dismissError"
          >
            ×
          </button>
        </div>
        
        <div class="error-content">
          <p class="error-message">{{ visibleError.message }}</p>
          
          <!-- 错误详情 -->
          <details 
            v-if="visibleError.details"
            class="error-details"
          >
            <summary>查看详情</summary>
            <pre>{{ visibleError.details }}</pre>
          </details>
          
          <!-- 恢复建议 -->
          <div 
            v-if="visibleError.suggestions?.length"
            class="error-suggestions"
          >
            <h4>建议操作：</h4>
            <ul>
              <li 
                v-for="(suggestion, index) in visibleError.suggestions" 
                :key="index"
              >
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>
        
        <div class="error-actions">
          <button 
            v-if="visibleError.retryable"
            class="btn-retry"
            @click="retryAction"
            :disabled="retrying"
          >
            <Icon name="refresh" />
            {{ retrying ? '重试中...' : '重试' }}
          </button>
          
          <button 
            class="btn-report"
            @click="reportError"
          >
            <Icon name="bug" />
            报告问题
          </button>
          
          <button 
            class="btn-dismiss"
            @click="dismissError"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
    
    <!-- 网络状态指示器 -->
    <div 
      v-if="showNetworkStatus"
      class="network-status"
      :class="networkStatus"
    >
      <Icon :name="getNetworkIcon()" />
      {{ getNetworkMessage() }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// 错误类型定义
interface ErrorInfo {
  id: string
  type: 'network' | 'validation' | 'api' | 'system' | 'user'
  message: string
  details?: string
  retryable?: boolean
  suggestions?: string[]
  timestamp: number
  context?: string
}

// 状态管理
const errors = ref<ErrorInfo[]>([])
const visibleError = ref<ErrorInfo | null>(null)
const retrying = ref(false)
const networkStatus = ref<'online' | 'offline' | 'slow'>('online')
const showNetworkStatus = ref(false)

// 计算属性
const hasErrors = computed(() => errors.value.length > 0)

// 网络状态监听
let networkCheckInterval: number | null = null

onMounted(() => {
  // 监听网络状态
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  
  // 定期检查网络状态
  networkCheckInterval = window.setInterval(checkNetworkSpeed, 30000)
  
  // 全局错误处理
  window.addEventListener('error', handleGlobalError)
  window.addEventListener('unhandledrejection', handleUnhandledRejection)
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  window.removeEventListener('error', handleGlobalError)
  window.removeEventListener('unhandledrejection', handleUnhandledRejection)
  
  if (networkCheckInterval) {
    clearInterval(networkCheckInterval)
  }
})

// 方法定义
function addError(error: Partial<ErrorInfo>) {
  const errorInfo: ErrorInfo = {
    id: Date.now().toString(),
    type: 'system',
    message: '发生未知错误',
    timestamp: Date.now(),
    ...error
  }
  
  errors.value.push(errorInfo)
  
  // 自动显示最新错误
  if (!visibleError.value) {
    visibleError.value = errorInfo
  }
}

function dismissError() {
  visibleError.value = null
  
  // 显示下一个错误
  if (errors.value.length > 0) {
    const nextError = errors.value.find(e => e.id !== visibleError.value?.id)
    if (nextError) {
      setTimeout(() => {
        visibleError.value = nextError
      }, 500)
    }
  }
}

async function retryAction() {
  if (!visibleError.value?.retryable) return
  
  retrying.value = true
  
  try {
    // 这里应该调用重试逻辑
    await new Promise(resolve => setTimeout(resolve, 1000))
    dismissError()
  }
  catch (error) {
    // 重试失败
    addError({
      type: 'system',
      message: '重试失败，请稍后再试',
      retryable: false
    })
  }
  finally {
    retrying.value = false
  }
}

function reportError() {
  if (!visibleError.value) return
  
  const report = {
    error: visibleError.value,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString(),
    url: window.location.href
  }
  
  // 这里应该发送错误报告到服务器
  // 暂时只是记录到控制台
  // eslint-disable-next-line no-console
  console.log('错误报告:', report)
}

function handleOnline() {
  networkStatus.value = 'online'
  showNetworkStatus.value = false
}

function handleOffline() {
  networkStatus.value = 'offline'
  showNetworkStatus.value = true
  
  addError({
    type: 'network',
    message: '网络连接已断开',
    suggestions: ['检查网络连接', '刷新页面重试'],
    retryable: true
  })
}

async function checkNetworkSpeed() {
  if (!navigator.onLine) return
  
  try {
    const start = Date.now()
    await fetch('/api/ping', { method: 'HEAD' })
    const duration = Date.now() - start
    
    if (duration > 5000) {
      networkStatus.value = 'slow'
      showNetworkStatus.value = true
    }
    else {
      networkStatus.value = 'online'
      showNetworkStatus.value = false
    }
  }
  catch {
    networkStatus.value = 'offline'
    showNetworkStatus.value = true
  }
}

function handleGlobalError(event: ErrorEvent) {
  addError({
    type: 'system',
    message: event.message,
    details: `${event.filename}:${event.lineno}:${event.colno}`,
    retryable: false
  })
}

function handleUnhandledRejection(event: PromiseRejectionEvent) {
  addError({
    type: 'system',
    message: '未处理的异步错误',
    details: String(event.reason),
    retryable: false
  })
}

// 工具方法
function getErrorIcon(type: string): string {
  const iconMap: Record<string, string> = {
    network: 'wifi-off',
    validation: 'alert-triangle',
    api: 'server',
    system: 'alert-circle',
    user: 'info'
  }
  return iconMap[type] || 'alert-circle'
}

function getErrorTitle(type: string): string {
  const titleMap: Record<string, string> = {
    network: '网络错误',
    validation: '验证错误',
    api: 'API错误',
    system: '系统错误',
    user: '用户提示'
  }
  return titleMap[type] || '错误'
}

function getNetworkIcon(): string {
  const iconMap: Record<string, string> = {
    online: 'wifi',
    offline: 'wifi-off',
    slow: 'clock'
  }
  return iconMap[networkStatus.value]
}

function getNetworkMessage(): string {
  const messageMap: Record<string, string> = {
    online: '网络连接正常',
    offline: '网络连接已断开',
    slow: '网络连接较慢'
  }
  return messageMap[networkStatus.value]
}

// 暴露方法给父组件
defineExpose({
  addError,
  dismissError,
  hasErrors
})
</script>

<style scoped>
.error-handler {
  position: relative;
}

.error-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.error-dialog {
  background: white;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.error-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e74c3c;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #666;
}

.error-content {
  padding: 20px;
}

.error-message {
  margin: 0 0 16px 0;
  color: #333;
}

.error-details {
  margin: 16px 0;
}

.error-details summary {
  cursor: pointer;
  color: #666;
  margin-bottom: 8px;
}

.error-details pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

.error-suggestions {
  margin: 16px 0;
}

.error-suggestions h4 {
  margin: 0 0 8px 0;
  color: #666;
}

.error-suggestions ul {
  margin: 0;
  padding-left: 20px;
}

.error-suggestions li {
  margin: 4px 0;
  color: #555;
}

.error-actions {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.error-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

.btn-retry {
  background: #3498db;
  color: white;
}

.btn-retry:hover:not(:disabled) {
  background: #2980b9;
}

.btn-retry:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-report {
  background: #f39c12;
  color: white;
}

.btn-report:hover {
  background: #e67e22;
}

.btn-dismiss {
  background: #95a5a6;
  color: white;
}

.btn-dismiss:hover {
  background: #7f8c8d;
}

.network-status {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 1000;
}

.network-status.online {
  background: #2ecc71;
  color: white;
}

.network-status.offline {
  background: #e74c3c;
  color: white;
}

.network-status.slow {
  background: #f39c12;
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-dialog {
    width: 95%;
    max-height: 90vh;
  }
  
  .error-header,
  .error-content,
  .error-actions {
    padding: 16px;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .network-status {
    position: fixed;
    top: 10px;
    right: 10px;
    left: 10px;
    text-align: center;
  }
}

/* 暗色主题 */
@media (prefers-color-scheme: dark) {
  .error-dialog {
    background: #2c3e50;
    color: white;
  }
  
  .error-header {
    border-bottom-color: #34495e;
  }
  
  .error-content {
    color: #ecf0f1;
  }
  
  .error-details pre {
    background: #34495e;
    color: #ecf0f1;
  }
  
  .error-actions {
    border-top-color: #34495e;
  }
  
  .close-btn {
    color: #bdc3c7;
  }
  
  .close-btn:hover {
    color: #ecf0f1;
  }
}
</style>
