<template>
  <div class="log-viewer">
    <!-- 控制面板 -->
    <div class="controls-panel">
      <div class="filter-controls">
        <div class="filter-group">
          <label>日志级别:</label>
          <select v-model="filters.level" @change="applyFilters">
            <option value="">全部</option>
            <option value="debug">调试</option>
            <option value="info">信息</option>
            <option value="warn">警告</option>
            <option value="error">错误</option>
            <option value="fatal">致命</option>
          </select>
        </div>

        <div class="filter-group">
          <label>组件:</label>
          <select v-model="filters.component" @change="applyFilters">
            <option value="">全部组件</option>
            <option v-for="component in availableComponents" :key="component" :value="component">
              {{ component }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>时间范围:</label>
          <select v-model="timeRange" @change="updateTimeFilter">
            <option value="all">全部时间</option>
            <option value="1h">最近1小时</option>
            <option value="6h">最近6小时</option>
            <option value="24h">最近24小时</option>
            <option value="custom">自定义</option>
          </select>
        </div>

        <div class="filter-group" v-if="timeRange === 'custom'">
          <label>开始时间:</label>
          <input 
            type="datetime-local" 
            v-model="customTimeStart" 
            @change="updateTimeFilter"
          />
          <label>结束时间:</label>
          <input 
            type="datetime-local" 
            v-model="customTimeEnd" 
            @change="updateTimeFilter"
          />
        </div>

        <div class="filter-group">
          <label>搜索:</label>
          <input 
            type="text" 
            v-model="searchText" 
            placeholder="搜索日志内容..."
            @input="applyFilters"
          />
        </div>
      </div>

      <div class="action-controls">
        <button @click="refreshLogs" class="action-btn">
          <span>🔄</span>
          刷新
        </button>
        
        <button @click="clearLogs" class="action-btn danger">
          <span>🗑️</span>
          清除日志
        </button>
        
        <button @click="exportLogs" class="action-btn">
          <span>📁</span>
          导出
        </button>
        
        <button @click="showReport = !showReport" class="action-btn">
          <span>📊</span>
          {{ showReport ? '隐藏' : '显示' }}报告
        </button>
        
        <button @click="toggleAutoScroll" class="action-btn" :class="{ active: autoScroll }">
          <span>📜</span>
          {{ autoScroll ? '停止' : '开始' }}自动滚动
        </button>
      </div>
    </div>

    <!-- 错误报告 -->
    <div class="error-report" v-if="showReport && errorReport">
      <h3>📊 错误报告</h3>
      
      <div class="report-summary">
        <div class="summary-card">
          <div class="summary-title">总日志数</div>
          <div class="summary-value">{{ errorReport.summary.totalLogs }}</div>
        </div>
        
        <div class="summary-card error">
          <div class="summary-title">错误数</div>
          <div class="summary-value">{{ errorReport.summary.errorCount }}</div>
        </div>
        
        <div class="summary-card warning">
          <div class="summary-title">警告数</div>
          <div class="summary-value">{{ errorReport.summary.warningCount }}</div>
        </div>
        
        <div class="summary-card">
          <div class="summary-title">平均响应时间</div>
          <div class="summary-value">{{ errorReport.performance.averageResponseTime }}ms</div>
        </div>
      </div>

      <div class="report-details">
        <div class="detail-section">
          <h4>Top 错误</h4>
          <div class="error-list">
            <div 
              v-for="error in errorReport.summary.topErrors" 
              :key="error.message"
              class="error-item"
            >
              <span class="error-message">{{ error.message }}</span>
              <span class="error-count">{{ error.count }}次</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>慢操作</h4>
          <div class="slow-operations">
            <div 
              v-for="op in errorReport.performance.slowestOperations" 
              :key="op.name"
              class="operation-item"
            >
              <span class="operation-name">{{ op.name }}</span>
              <span class="operation-duration">{{ op.duration.toFixed(2) }}ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 日志统计 -->
    <div class="log-stats">
      <div class="stat-item">
        <span class="stat-label">显示:</span>
        <span class="stat-value">{{ filteredLogs.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">总计:</span>
        <span class="stat-value">{{ allLogs.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">会话:</span>
        <span class="stat-value">{{ sessionId }}</span>
      </div>
      <div class="stat-item" v-if="userId">
        <span class="stat-label">用户:</span>
        <span class="stat-value">{{ userId }}</span>
      </div>
    </div>

    <!-- 日志列表 -->
    <div class="log-container" ref="logContainer">
      <div class="log-list">
        <div 
          v-for="log in displayedLogs" 
          :key="log.id"
          class="log-entry"
          :class="`log-${log.level}`"
        >
          <div class="log-header">
            <span class="log-timestamp">
              {{ formatTimestamp(log.timestamp) }}
            </span>
            <span class="log-level" :class="`level-${log.level}`">
              {{ getLevelIcon(log.level) }} {{ log.level.toUpperCase() }}
            </span>
            <span class="log-component" v-if="log.component">
              {{ log.component }}
            </span>
          </div>
          
          <div class="log-message">
            {{ log.message }}
          </div>
          
          <div class="log-context" v-if="log.context && Object.keys(log.context).length > 0">
            <details>
              <summary>详细信息</summary>
              <pre>{{ JSON.stringify(log.context, null, 2) }}</pre>
            </details>
          </div>
          
          <div class="log-stack" v-if="log.stack">
            <details>
              <summary>堆栈跟踪</summary>
              <pre class="stack-trace">{{ log.stack }}</pre>
            </details>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div class="load-more" v-if="canLoadMore">
        <button @click="loadMore" class="load-more-btn">
          加载更多日志
        </button>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-if="filteredLogs.length === 0">
        <div class="empty-icon">📝</div>
        <div class="empty-message">没有找到匹配的日志</div>
        <div class="empty-suggestion">
          尝试调整过滤条件或清除搜索文本
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { logger, type LogEntry, type LogLevel } from '@/utils/logger'

// 响应式数据
const allLogs = ref<LogEntry[]>([])
const filteredLogs = ref<LogEntry[]>([])
const displayedLogs = ref<LogEntry[]>([])
const errorReport = ref<any>(null)

// 过滤器状态
const filters = ref({
  level: '' as LogLevel | '',
  component: '',
  timeRange: null as { start: number; end: number } | null
})

const searchText = ref('')
const timeRange = ref('all')
const customTimeStart = ref('')
const customTimeEnd = ref('')

// UI状态
const showReport = ref(false)
const autoScroll = ref(true)
const pageSize = 100
const currentPage = ref(1)

// 元素引用
const logContainer = ref<HTMLElement>()

// 计算属性
const availableComponents = computed(() => {
  const components = new Set<string>()
  allLogs.value.forEach(log => {
    if (log.component) {
      components.add(log.component)
    }
  })
  return Array.from(components).sort()
})

const canLoadMore = computed(() => {
  return displayedLogs.value.length < filteredLogs.value.length
})

const sessionId = computed(() => {
  return allLogs.value[0]?.sessionId || 'N/A'
})

const userId = computed(() => {
  return allLogs.value[0]?.userId
})

// 生命周期
onMounted(() => {
  loadLogs()
  generateReport()
  
  // 定期刷新
  const interval = setInterval(() => {
    loadLogs()
    generateReport()
  }, 5000)

  onUnmounted(() => {
    clearInterval(interval)
  })
})

// 监听器
watch(autoScroll, (enabled) => {
  if (enabled) {
    scrollToBottom()
  }
})

watch(() => filteredLogs.value.length, () => {
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom()
    })
  }
})

/**
 * 加载日志
 */
function loadLogs(): void {
  allLogs.value = logger.getLogs()
  applyFilters()
}

/**
 * 应用过滤器
 */
function applyFilters(): void {
  let logs = [...allLogs.value]

  // 级别过滤
  if (filters.value.level) {
    const levelPriority = {
      debug: 0, info: 1, warn: 2, error: 3, fatal: 4
    }
    const minPriority = levelPriority[filters.value.level]
    logs = logs.filter(log => levelPriority[log.level] >= minPriority)
  }

  // 组件过滤
  if (filters.value.component) {
    logs = logs.filter(log => log.component === filters.value.component)
  }

  // 时间范围过滤
  if (filters.value.timeRange) {
    logs = logs.filter(log => 
      log.timestamp >= filters.value.timeRange!.start &&
      log.timestamp <= filters.value.timeRange!.end
    )
  }

  // 搜索过滤
  if (searchText.value) {
    const searchLower = searchText.value.toLowerCase()
    logs = logs.filter(log => 
      log.message.toLowerCase().includes(searchLower) ||
      (log.component && log.component.toLowerCase().includes(searchLower)) ||
      JSON.stringify(log.context || {}).toLowerCase().includes(searchLower)
    )
  }

  filteredLogs.value = logs.reverse() // 最新的在前面
  currentPage.value = 1
  updateDisplayedLogs()
}

/**
 * 更新显示的日志
 */
function updateDisplayedLogs(): void {
  const startIndex = 0
  const endIndex = currentPage.value * pageSize
  displayedLogs.value = filteredLogs.value.slice(startIndex, endIndex)
}

/**
 * 加载更多
 */
function loadMore(): void {
  currentPage.value++
  updateDisplayedLogs()
}

/**
 * 更新时间过滤器
 */
function updateTimeFilter(): void {
  if (timeRange.value === 'all') {
    filters.value.timeRange = null
  }
  else if (timeRange.value === 'custom') {
    if (customTimeStart.value && customTimeEnd.value) {
      filters.value.timeRange = {
        start: new Date(customTimeStart.value).getTime(),
        end: new Date(customTimeEnd.value).getTime()
      }
    }
  }
  else {
    const now = Date.now()
    const hours = parseInt(timeRange.value.replace('h', ''))
    filters.value.timeRange = {
      start: now - (hours * 60 * 60 * 1000),
      end: now
    }
  }
  
  applyFilters()
}

/**
 * 刷新日志
 */
function refreshLogs(): void {
  loadLogs()
  generateReport()
}

/**
 * 清除日志
 */
function clearLogs(): void {
  // 简化确认逻辑
  const shouldClear = true // 可以通过UI状态控制
  if (shouldClear) {
    logger.clearLogs()
    allLogs.value = []
    filteredLogs.value = []
    displayedLogs.value = []
    errorReport.value = null
  }
}

/**
 * 导出日志
 */
function exportLogs(): void {
  // 默认使用JSON格式
  const format = 'json'
  const data = logger.exportLogs(format)
  const extension = format === 'json' ? 'json' : 'csv'
  const mimeType = format === 'json' ? 'application/json' : 'text/csv'
  
  const blob = new Blob([data], { type: mimeType })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `logs-${new Date().toISOString().slice(0, 19)}.${extension}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}

/**
 * 生成报告
 */
function generateReport(): void {
  errorReport.value = logger.generateErrorReport()
}

/**
 * 切换自动滚动
 */
function toggleAutoScroll(): void {
  autoScroll.value = !autoScroll.value
}

/**
 * 滚动到底部
 */
function scrollToBottom(): void {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

/**
 * 格式化时间戳
 */
function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp)
  const formatted = date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
  
  // 手动添加毫秒
  const ms = date.getMilliseconds().toString().padStart(3, '0')
  return `${formatted}.${ms}`
}

/**
 * 获取级别图标
 */
function getLevelIcon(level: LogLevel): string {
  const icons = {
    debug: '🐛',
    info: 'ℹ️',
    warn: '⚠️',
    error: '❌',
    fatal: '💀'
  }
  return icons[level] || 'ℹ️'
}
</script>

<style lang="scss" scoped>
.log-viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-background);
  color: var(--color-text);
}

.controls-panel {
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;

  label {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-2);
    white-space: nowrap;
  }

  select,
  input {
    padding: 6px 12px;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    background: var(--color-background);
    color: var(--color-text);
    font-size: 14px;
    min-width: 120px;

    &:focus {
      outline: none;
      border-color: var(--color-primary);
    }
  }

  input[type="text"] {
    min-width: 200px;
  }

  input[type="datetime-local"] {
    min-width: 180px;
  }
}

.action-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: var(--color-background-mute);
    border-color: var(--color-primary);
  }

  &.active {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  &.danger {
    &:hover {
      background: #fee2e2;
      border-color: #ef4444;
      color: #dc2626;
    }
  }
}

.error-report {
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
  padding: 16px;

  h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.report-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.summary-card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  text-align: center;

  &.error {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.05);
  }

  &.warning {
    border-color: #f59e0b;
    background: rgba(245, 158, 11, 0.05);
  }

  .summary-title {
    font-size: 12px;
    color: var(--color-text-3);
    margin-bottom: 4px;
  }

  .summary-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-text);
  }
}

.report-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.detail-section {
  h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-2);
  }
}

.error-list,
.slow-operations {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-item,
.operation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-background);
  border-radius: 6px;
  font-size: 13px;

  .error-message,
  .operation-name {
    flex: 1;
    color: var(--color-text);
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .error-count,
  .operation-duration {
    color: var(--color-text-3);
    font-weight: 600;
    margin-left: 12px;
  }
}

.log-stats {
  background: var(--color-background-mute);
  border-bottom: 1px solid var(--color-border);
  padding: 8px 16px;
  display: flex;
  gap: 24px;
  font-size: 13px;
}

.stat-item {
  display: flex;
  gap: 6px;

  .stat-label {
    color: var(--color-text-3);
  }

  .stat-value {
    color: var(--color-text);
    font-weight: 600;
  }
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-entry {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;

  &.log-debug {
    border-left: 4px solid #6b7280;
  }

  &.log-info {
    border-left: 4px solid #3b82f6;
  }

  &.log-warn {
    border-left: 4px solid #f59e0b;
  }

  &.log-error {
    border-left: 4px solid #ef4444;
  }

  &.log-fatal {
    border-left: 4px solid #dc2626;
    background: rgba(220, 38, 38, 0.05);
  }
}

.log-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
}

.log-timestamp {
  color: var(--color-text-3);
  font-weight: 500;
}

.log-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 11px;

  &.level-debug {
    background: rgba(107, 114, 128, 0.1);
    color: #6b7280;
  }

  &.level-info {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  &.level-warn {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }

  &.level-error {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  &.level-fatal {
    background: rgba(220, 38, 38, 0.1);
    color: #dc2626;
  }
}

.log-component {
  background: rgba(156, 163, 175, 0.1);
  color: var(--color-text-2);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.log-message {
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
  word-break: break-word;
}

.log-context,
.log-stack {
  margin-top: 8px;

  details {
    summary {
      cursor: pointer;
      color: var(--color-text-2);
      font-size: 12px;
      font-weight: 500;
      margin-bottom: 4px;

      &:hover {
        color: var(--color-primary);
      }
    }

    pre {
      background: var(--color-background);
      border: 1px solid var(--color-border);
      border-radius: 4px;
      padding: 8px;
      font-size: 11px;
      color: var(--color-text-2);
      overflow-x: auto;
      margin: 0;
    }
  }
}

.stack-trace {
  color: #dc2626 !important;
  background: rgba(220, 38, 38, 0.05) !important;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}

.load-more-btn {
  padding: 10px 20px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;

  &:hover {
    background: var(--color-primary-dark);
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-3);

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .empty-message {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 8px;
  }

  .empty-suggestion {
    font-size: 14px;
  }
}

@media (max-width: 768px) {
  .filter-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;

    input,
    select {
      min-width: auto;
    }
  }

  .report-details {
    grid-template-columns: 1fr;
  }

  .log-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>