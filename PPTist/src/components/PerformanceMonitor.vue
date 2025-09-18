<template>
  <div class="performance-monitor">
    <!-- 实时指标显示 -->
    <div class="metrics-dashboard">
      <div class="metric-card">
        <div class="metric-header">
          <span>📊</span>
          <span>内存使用</span>
        </div>
        <div class="metric-value">
          {{ currentMetrics?.memory.percentage || 0 }}%
        </div>
        <div class="metric-details">
          {{ formatBytes(currentMetrics?.memory.used) }} / 
          {{ formatBytes(currentMetrics?.memory.total) }}
        </div>
        <div class="metric-bar">
          <div 
            class="metric-fill" 
            :style="{ width: `${currentMetrics?.memory.percentage || 0}%` }"
            :class="getThresholdClass(currentMetrics?.memory.percentage || 0, 80)"
          ></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span>⚡</span>
          <span>CPU使用率</span>
        </div>
        <div class="metric-value">
          {{ currentMetrics?.cpu.usage || 0 }}%
        </div>
        <div class="metric-details">
          核心数: {{ currentMetrics?.cpu.cores || 0 }}
        </div>
        <div class="metric-bar">
          <div 
            class="metric-fill" 
            :style="{ width: `${currentMetrics?.cpu.usage || 0}%` }"
            :class="getThresholdClass(currentMetrics?.cpu.usage || 0, 85)"
          ></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span>🌐</span>
          <span>网络延迟</span>
        </div>
        <div class="metric-value">
          {{ currentMetrics?.network.latency || 0 }}ms
        </div>
        <div class="metric-details">
          {{ getNetworkStatus(currentMetrics?.network.latency || 0) }}
        </div>
        <div class="metric-bar">
          <div 
            class="metric-fill" 
            :style="{ width: `${Math.min(100, (currentMetrics?.network.latency || 0) / 10)}%` }"
            :class="getThresholdClass(currentMetrics?.network.latency || 0, 500)"
          ></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span>📋</span>
          <span>任务队列</span>
        </div>
        <div class="metric-value">
          {{ (currentMetrics?.tasks.queued || 0) + (currentMetrics?.tasks.running || 0) }}
        </div>
        <div class="metric-details">
          运行中: {{ currentMetrics?.tasks.running || 0 }} | 
          排队: {{ currentMetrics?.tasks.queued || 0 }}
        </div>
        <div class="metric-bar">
          <div 
            class="metric-fill" 
            :style="{ width: `${Math.min(100, ((currentMetrics?.tasks.queued || 0) / 20) * 100)}%` }"
            :class="getThresholdClass(currentMetrics?.tasks.queued || 0, 10)"
          ></div>
        </div>
      </div>
    </div>

    <!-- 趋势图表 -->
    <div class="charts-section" v-if="showCharts">
      <div class="chart-container">
        <h3>内存使用趋势</h3>
        <canvas ref="memoryChart" width="400" height="200"></canvas>
      </div>
      <div class="chart-container">
        <h3>CPU使用趋势</h3>
        <canvas ref="cpuChart" width="400" height="200"></canvas>
      </div>
    </div>

    <!-- 警报列表 -->
    <div class="alerts-section" v-if="recentAlerts.length > 0">
      <h3>
        <span>⚠️</span>
        系统警报
      </h3>
      <div class="alerts-list">
        <div 
          v-for="alert in recentAlerts" 
          :key="alert.timestamp"
          class="alert-item"
          :class="`alert-${alert.level}`"
        >
          <div class="alert-header">
            <span>{{ getAlertIcon(alert.level) }}</span>
            <span class="alert-message">{{ alert.message }}</span>
            <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
          </div>
          <div class="alert-suggestion" v-if="alert.suggestion">
            {{ alert.suggestion }}
          </div>
        </div>
      </div>
    </div>

    <!-- 性能报告 -->
    <div class="report-section" v-if="performanceReport">
      <h3>
        <span>📈</span>
        性能总结
      </h3>
      <div class="report-content">
        <div class="report-stats">
          <div class="stat-item">
            <span class="stat-label">平均内存使用:</span>
            <span class="stat-value">{{ performanceReport.summary.averageMemoryUsage }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">平均CPU使用:</span>
            <span class="stat-value">{{ performanceReport.summary.averageCPUUsage }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已完成任务:</span>
            <span class="stat-value">{{ performanceReport.summary.totalTasks }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">警报数量:</span>
            <span class="stat-value">{{ performanceReport.summary.alertCount }}</span>
          </div>
        </div>
        
        <div class="report-trends">
          <div class="trend-item">
            <span class="trend-label">内存趋势:</span>
            <span :class="`trend-${performanceReport.trends.memoryTrend}`">
              {{ getTrendText(performanceReport.trends.memoryTrend) }}
            </span>
          </div>
          <div class="trend-item">
            <span class="trend-label">CPU趋势:</span>
            <span :class="`trend-${performanceReport.trends.cpuTrend}`">
              {{ getTrendText(performanceReport.trends.cpuTrend) }}
            </span>
          </div>
        </div>

        <div class="report-recommendations">
          <h4>优化建议:</h4>
          <ul>
            <li v-for="recommendation in performanceReport.recommendations" :key="recommendation">
              {{ recommendation }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 控制面板 -->
    <div class="controls-section">
      <button 
        @click="toggleMonitoring" 
        class="control-btn"
        :class="{ active: isMonitoring }"
      >
        <span>{{ isMonitoring ? '⏸️' : '▶️' }}</span>
        {{ isMonitoring ? '暂停监控' : '开始监控' }}
      </button>
      
      <button @click="toggleCharts" class="control-btn">
        <span>📊</span>
        {{ showCharts ? '隐藏图表' : '显示图表' }}
      </button>
      
      <button @click="clearHistory" class="control-btn">
        <span>🗑️</span>
        清除历史
      </button>
      
      <button @click="exportData" class="control-btn">
        <span>⬇️</span>
        导出数据
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { performanceMonitor, type PerformanceMetrics, type PerformanceAlert } from '@/monitoring/performance-monitor'

// 响应式数据
const currentMetrics = ref<PerformanceMetrics | null>(null)
const metricsHistory = ref<PerformanceMetrics[]>([])
const recentAlerts = ref<PerformanceAlert[]>([])
const performanceReport = ref<any>(null)
const isMonitoring = ref(false)
const showCharts = ref(false)

// 图表引用
const memoryChart = ref<HTMLCanvasElement>()
const cpuChart = ref<HTMLCanvasElement>()

// 订阅清理函数
let unsubscribeMetrics: (() => void) | null = null
let unsubscribeAlerts: (() => void) | null = null

onMounted(() => {
  initializeMonitoring()
})

onUnmounted(() => {
  cleanup()
})

/**
 * 初始化监控
 */
function initializeMonitoring() {
  // 订阅性能指标更新
  unsubscribeMetrics = performanceMonitor.subscribe((metrics: PerformanceMetrics) => {
    currentMetrics.value = metrics
    metricsHistory.value.push(metrics)
    
    // 保持历史数据在合理范围内
    if (metricsHistory.value.length > 60) { // 最近5分钟的数据
      metricsHistory.value = metricsHistory.value.slice(-60)
    }
    
    // 更新图表
    if (showCharts.value) {
      updateCharts()
    }
  })

  // 订阅警报
  unsubscribeAlerts = performanceMonitor.subscribeToAlerts((alert: PerformanceAlert) => {
    recentAlerts.value.unshift(alert)
    
    // 保持最近20个警报
    if (recentAlerts.value.length > 20) {
      recentAlerts.value = recentAlerts.value.slice(0, 20)
    }
  })

  // 生成性能报告
  generateReport()
  
  // 每30秒更新一次报告
  setInterval(generateReport, 30000)
}

/**
 * 切换监控状态
 */
function toggleMonitoring() {
  if (isMonitoring.value) {
    performanceMonitor.stop()
    isMonitoring.value = false
  }
  else {
    performanceMonitor.start()
    isMonitoring.value = true
  }
}

/**
 * 切换图表显示
 */
async function toggleCharts() {
  showCharts.value = !showCharts.value
  
  if (showCharts.value) {
    await nextTick()
    initializeCharts()
    updateCharts()
  }
}

/**
 * 清除历史数据
 */
function clearHistory() {
  performanceMonitor.clearHistory()
  metricsHistory.value = []
  recentAlerts.value = []
  currentMetrics.value = null
  performanceReport.value = null
}

/**
 * 导出数据
 */
function exportData() {
  const data = performanceMonitor.exportData()
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `performance-monitor-${new Date().toISOString().slice(0, 19)}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}

/**
 * 生成性能报告
 */
function generateReport() {
  performanceReport.value = performanceMonitor.generateReport()
}

/**
 * 初始化图表
 */
function initializeCharts() {
  if (!memoryChart.value || !cpuChart.value) return

  // 简单的图表初始化
  const memoryCtx = memoryChart.value.getContext('2d')
  const cpuCtx = cpuChart.value.getContext('2d')
  
  if (memoryCtx) {
    memoryCtx.clearRect(0, 0, 400, 200)
  }
  if (cpuCtx) {
    cpuCtx.clearRect(0, 0, 400, 200)
  }
}

/**
 * 更新图表
 */
function updateCharts() {
  if (!memoryChart.value || !cpuChart.value || metricsHistory.value.length === 0) return

  const memoryCtx = memoryChart.value.getContext('2d')
  const cpuCtx = cpuChart.value.getContext('2d')
  
  if (!memoryCtx || !cpuCtx) return

  // 清除画布
  memoryCtx.clearRect(0, 0, 400, 200)
  cpuCtx.clearRect(0, 0, 400, 200)

  const data = metricsHistory.value.slice(-30) // 最近30个数据点
  if (data.length < 2) return

  // 绘制内存使用图表
  drawChart(memoryCtx, data.map(d => d.memory.percentage), 400, 200, '#3b82f6')
  
  // 绘制CPU使用图表
  drawChart(cpuCtx, data.map(d => d.cpu.usage), 400, 200, '#10b981')
}

/**
 * 绘制简单折线图
 */
function drawChart(ctx: CanvasRenderingContext2D, data: number[], width: number, height: number, color: string) {
  if (data.length < 2) return

  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.beginPath()

  const stepX = width / (data.length - 1)
  const maxY = Math.max(...data, 100)

  data.forEach((value, index) => {
    const x = index * stepX
    const y = height - (value / maxY) * height

    if (index === 0) {
      ctx.moveTo(x, y)
    }
    else {
      ctx.lineTo(x, y)
    }
  })

  ctx.stroke()

  // 绘制网格线
  ctx.strokeStyle = '#e5e7eb'
  ctx.lineWidth = 1
  
  // 水平线
  for (let i = 0; i <= 4; i++) {
    const y = (height / 4) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
}

/**
 * 清理资源
 */
function cleanup() {
  if (unsubscribeMetrics) {
    unsubscribeMetrics()
  }
  if (unsubscribeAlerts) {
    unsubscribeAlerts()
  }
  
  performanceMonitor.stop()
}

/**
 * 工具函数
 */
function formatBytes(bytes?: number): string {
  if (!bytes) return '0 MB'
  return `${bytes.toFixed(1)} MB`
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString()
}

function getThresholdClass(value: number, threshold: number): string {
  if (value >= threshold * 1.2) return 'critical'
  if (value >= threshold) return 'warning'
  return 'normal'
}

function getNetworkStatus(latency: number): string {
  if (latency < 100) return '优秀'
  if (latency < 300) return '良好'
  if (latency < 500) return '一般'
  return '较慢'
}

function getAlertIcon(level: string): string {
  switch (level) {
    case 'critical': return '🔴'
    case 'error': return '❌'
    case 'warning': return '⚠️'
    default: return 'ℹ️'
  }
}

function getTrendText(trend: string): string {
  switch (trend) {
    case 'increasing': return '上升'
    case 'decreasing': return '下降'
    default: return '稳定'
  }
}
</script>

<style lang="scss" scoped>
.performance-monitor {
  padding: 20px;
  background: var(--color-background);
}

.metrics-dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  }

  .metric-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    color: var(--color-text-2);
    font-size: 14px;
    font-weight: 500;
  }

  .metric-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 8px;
  }

  .metric-details {
    font-size: 12px;
    color: var(--color-text-3);
    margin-bottom: 12px;
  }

  .metric-bar {
    height: 6px;
    background: var(--color-border);
    border-radius: 3px;
    overflow: hidden;

    .metric-fill {
      height: 100%;
      transition: width 0.3s ease;
      border-radius: 3px;

      &.normal {
        background: linear-gradient(90deg, #10b981, #059669);
      }

      &.warning {
        background: linear-gradient(90deg, #f59e0b, #d97706);
      }

      &.critical {
        background: linear-gradient(90deg, #ef4444, #dc2626);
      }
    }
  }
}

.charts-section {
  margin-bottom: 30px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;

  .chart-container {
    background: var(--color-background-soft);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--color-border);

    h3 {
      margin: 0 0 16px 0;
      color: var(--color-text);
      font-size: 16px;
      font-weight: 600;
    }

    canvas {
      width: 100%;
      height: 200px;
      border-radius: 8px;
    }
  }
}

.alerts-section {
  margin-bottom: 30px;

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    color: var(--color-text);
    font-size: 18px;
    font-weight: 600;
  }

  .alerts-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .alert-item {
    background: var(--color-background-soft);
    border-radius: 8px;
    padding: 16px;
    border-left: 4px solid;

    &.alert-info {
      border-left-color: #3b82f6;
    }

    &.alert-warning {
      border-left-color: #f59e0b;
    }

    &.alert-error {
      border-left-color: #ef4444;
    }

    &.alert-critical {
      border-left-color: #dc2626;
      background: rgba(239, 68, 68, 0.05);
    }

    .alert-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;

      .alert-message {
        flex: 1;
        font-weight: 500;
        color: var(--color-text);
      }

      .alert-time {
        font-size: 12px;
        color: var(--color-text-3);
      }
    }

    .alert-suggestion {
      font-size: 13px;
      color: var(--color-text-2);
      padding-left: 24px;
    }
  }
}

.report-section {
  margin-bottom: 30px;

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    color: var(--color-text);
    font-size: 18px;
    font-weight: 600;
  }

  .report-content {
    background: var(--color-background-soft);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--color-border);
  }

  .report-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 20px;

    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: var(--color-background);
      border-radius: 8px;

      .stat-label {
        color: var(--color-text-2);
        font-size: 14px;
      }

      .stat-value {
        color: var(--color-text);
        font-weight: 600;
      }
    }
  }

  .report-trends {
    margin-bottom: 20px;

    .trend-item {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;

      .trend-label {
        color: var(--color-text-2);
        min-width: 80px;
      }

      .trend-increasing {
        color: #ef4444;
      }

      .trend-decreasing {
        color: #10b981;
      }

      .trend-stable {
        color: #6b7280;
      }
    }
  }

  .report-recommendations {
    h4 {
      color: var(--color-text);
      margin-bottom: 12px;
      font-size: 14px;
      font-weight: 600;
    }

    ul {
      margin: 0;
      padding-left: 20px;
      color: var(--color-text-2);

      li {
        margin-bottom: 8px;
        font-size: 14px;
        line-height: 1.5;
      }
    }
  }
}

.controls-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;

  .control-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    background: var(--color-background-soft);
    border: 1px solid var(--color-border);
    border-radius: 8px;
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
  }
}

@media (max-width: 768px) {
  .metrics-dashboard {
    grid-template-columns: 1fr;
  }

  .charts-section {
    grid-template-columns: 1fr;
  }

  .controls-section {
    .control-btn {
      flex: 1;
      justify-content: center;
    }
  }
}
</style>