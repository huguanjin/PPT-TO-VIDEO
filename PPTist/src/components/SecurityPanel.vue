<template>
  <div class="security-panel">
    <!-- 安全状态概览 -->
    <div class="security-overview">
      <div class="status-header">
        <h2>🛡️ 安全状态概览</h2>
        <div class="risk-badge" :class="`risk-${securityReport?.summary.riskLevel || 'low'}`">
          {{ getRiskLevelText(securityReport?.summary.riskLevel || 'low') }}
        </div>
      </div>

      <div class="security-stats">
        <div class="stat-card">
          <div class="stat-icon">⚠️</div>
          <div class="stat-content">
            <div class="stat-title">安全违规</div>
            <div class="stat-value">{{ securityReport?.summary.totalViolations || 0 }}</div>
            <div class="stat-subtitle">最近24小时</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🚫</div>
          <div class="stat-content">
            <div class="stat-title">阻止攻击</div>
            <div class="stat-value">{{ securityReport?.summary.blockedAttacks || 0 }}</div>
            <div class="stat-subtitle">成功拦截</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🎯</div>
          <div class="stat-content">
            <div class="stat-title">威胁类型</div>
            <div class="stat-value">{{ securityReport?.summary.uniqueThreats || 0 }}</div>
            <div class="stat-subtitle">不同威胁</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🔒</div>
          <div class="stat-content">
            <div class="stat-title">被阻止IP</div>
            <div class="stat-value">{{ blockedIPs.length }}</div>
            <div class="stat-subtitle">当前阻止</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 实时监控 -->
    <div class="real-time-monitor">
      <div class="monitor-header">
        <h3>📊 实时监控</h3>
        <div class="monitor-controls">
          <button 
            @click="toggleMonitoring" 
            class="control-btn"
            :class="{ active: isMonitoring }"
          >
            {{ isMonitoring ? '⏸️ 暂停' : '▶️ 开始' }}
          </button>
          <button @click="clearViolations" class="control-btn danger">
            🗑️ 清除记录
          </button>
        </div>
      </div>

      <!-- 最近违规 -->
      <div class="recent-violations">
        <h4>最近违规记录</h4>
        <div class="violations-list">
          <div 
            v-for="violation in recentViolations" 
            :key="violation.details?.timestamp || Math.random()"
            class="violation-item"
            :class="`severity-${violation.severity}`"
          >
            <div class="violation-header">
              <span class="violation-type">{{ getThreatIcon(violation.type) }} {{ getThreatName(violation.type) }}</span>
              <span class="violation-time">{{ formatTime(violation.timestamp) }}</span>
              <span class="violation-severity" :class="`severity-${violation.severity}`">
                {{ violation.severity.toUpperCase() }}
              </span>
            </div>
            <div class="violation-message">{{ violation.message }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 安全配置 -->
    <div class="security-config">
      <h3>⚙️ 安全配置</h3>
      <div class="config-grid">
        <div class="config-section">
          <h4>基础安全</h4>
          <div class="config-item">
            <label>
              <input 
                type="checkbox" 
                v-model="localConfig.enableXSSProtection"
                @change="updateConfig"
              />
              启用XSS防护
            </label>
          </div>
          <div class="config-item">
            <label>
              <input 
                type="checkbox" 
                v-model="localConfig.enableCSRF"
                @change="updateConfig"
              />
              启用CSRF保护
            </label>
          </div>
        </div>

        <div class="config-section">
          <h4>文件上传</h4>
          <div class="config-item">
            <label>
              <input 
                type="checkbox" 
                v-model="localConfig.enableFileValidation"
                @change="updateConfig"
              />
              启用文件验证
            </label>
          </div>
          <div class="config-item">
            <label>
              最大文件大小 (MB):
              <input 
                type="number" 
                v-model.number="localConfig.maxFileSize"
                @change="updateConfig"
                min="1"
                max="100"
              />
            </label>
          </div>
        </div>

        <div class="config-section">
          <h4>限流设置</h4>
          <div class="config-item">
            <label>
              <input 
                type="checkbox" 
                v-model="localConfig.enableRateLimiting"
                @change="updateConfig"
              />
              启用限流
            </label>
          </div>
          <div class="config-item">
            <label>
              每分钟最大请求数:
              <input 
                type="number" 
                v-model.number="localConfig.maxRequestsPerMinute"
                @change="updateConfig"
                min="10"
                max="1000"
              />
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- 安全测试工具 -->
    <div class="security-tools">
      <h3>🔧 安全测试工具</h3>
      <div class="tools-grid">
        <div class="tool-card">
          <h4>XSS测试</h4>
          <div class="tool-content">
            <input 
              v-model="testInput.xss" 
              placeholder="输入测试内容..."
              class="tool-input"
            />
            <button @click="testXSS" class="tool-btn">测试</button>
          </div>
          <div class="tool-result" v-if="testResults.xss">
            {{ testResults.xss }}
          </div>
        </div>

        <div class="tool-card">
          <h4>限流测试</h4>
          <div class="tool-content">
            <button @click="testRateLimit" class="tool-btn">发送测试请求</button>
          </div>
          <div class="tool-result" v-if="testResults.rateLimit">
            {{ testResults.rateLimit }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { securityManager, type SecurityViolation, type SecurityConfig } from '@/security/security-manager'

// 响应式数据
const securityReport = ref<any>(null)
const recentViolations = ref<SecurityViolation[]>([])
const blockedIPs = ref<string[]>([])
const isMonitoring = ref(false)
const localConfig = ref<SecurityConfig>({
  enableCSRF: true,
  enableXSSProtection: true,
  enableFileValidation: true,
  enableRateLimiting: true,
  enableInputSanitization: true,
  maxFileSize: 10,
  allowedFileTypes: [],
  maxRequestsPerMinute: 60,
  sessionTimeout: 30,
  enableSecurityHeaders: true
})

// 测试工具
const testInput = ref({
  xss: ''
})

const testResults = ref({
  xss: '',
  file: '',
  rateLimit: ''
})

// 定时器
let refreshTimer: number | null = null

onMounted(() => {
  loadData()
  startMonitoring()
})

onUnmounted(() => {
  stopMonitoring()
})

/**
 * 加载数据
 */
function loadData(): void {
  securityReport.value = securityManager.generateSecurityReport()
  recentViolations.value = securityManager.getViolations({ limit: 10 })
  // 模拟获取被阻止的IP列表
  blockedIPs.value = [] // 实际应该从securityManager获取
}

/**
 * 开始监控
 */
function startMonitoring(): void {
  isMonitoring.value = true
  refreshTimer = window.setInterval(() => {
    loadData()
  }, 5000) // 每5秒刷新一次
}

/**
 * 停止监控
 */
function stopMonitoring(): void {
  isMonitoring.value = false
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

/**
 * 切换监控状态
 */
function toggleMonitoring(): void {
  if (isMonitoring.value) {
    stopMonitoring()
  }
  else {
    startMonitoring()
  }
}

/**
 * 清除违规记录
 */
function clearViolations(): void {
  // 清除违规记录的逻辑
  recentViolations.value = []
  loadData()
}

/**
 * 更新配置
 */
function updateConfig(): void {
  securityManager.updateConfig(localConfig.value)
}

/**
 * 测试XSS
 */
function testXSS(): void {
  const sanitized = securityManager.sanitizeInput(testInput.value.xss)
  testResults.value.xss = `原始: "${testInput.value.xss}" -> 净化后: "${sanitized}"`
}

/**
 * 测试限流
 */
function testRateLimit(): void {
  const status = securityManager.checkRateLimit('test-user')
  testResults.value.rateLimit = status.limited 
    ? '❌ 请求被限制' 
    : `✅ 请求通过，剩余: ${status.remaining}`
}

/**
 * 工具函数
 */
function getRiskLevelText(level: string): string {
  const texts = {
    low: '低风险',
    medium: '中等风险',
    high: '高风险',
    critical: '严重风险'
  }
  return texts[level as keyof typeof texts] || '未知'
}

function getThreatName(type: string): string {
  const names = {
    xss: 'XSS攻击',
    csrf: 'CSRF攻击',
    file_upload: '文件上传',
    rate_limit: '限流触发',
    invalid_input: '输入验证',
    suspicious_activity: '可疑活动'
  }
  return names[type as keyof typeof names] || type
}

function getThreatIcon(type: string): string {
  const icons = {
    xss: '🕷️',
    csrf: '🎭',
    file_upload: '📁',
    rate_limit: '🚦',
    invalid_input: '❌',
    suspicious_activity: '👁️'
  }
  return icons[type as keyof typeof icons] || '⚠️'
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>

<style lang="scss" scoped>
.security-panel {
  padding: 20px;
  background: var(--color-background);
  color: var(--color-text);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.security-overview {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
  }
}

.risk-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;

  &.risk-low {
    background: rgba(34, 197, 94, 0.1);
    color: #22c55e;
  }

  &.risk-medium {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }

  &.risk-high {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  &.risk-critical {
    background: rgba(220, 38, 38, 0.1);
    color: #dc2626;
  }
}

.security-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;

  .stat-icon {
    font-size: 24px;
  }

  .stat-content {
    flex: 1;

    .stat-title {
      font-size: 12px;
      color: var(--color-text-3);
      margin-bottom: 4px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: var(--color-text);
      margin-bottom: 2px;
    }

    .stat-subtitle {
      font-size: 11px;
      color: var(--color-text-3);
    }
  }
}

.threat-breakdown {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);

  h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.breakdown-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breakdown-item {
  .breakdown-bar {
    height: 8px;
    background: var(--color-border);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 4px;

    .breakdown-fill {
      height: 100%;
      transition: width 0.3s ease;

      &.threat-xss { background: #ef4444; }
      &.threat-csrf { background: #f59e0b; }
      &.threat-file_upload { background: #3b82f6; }
      &.threat-rate_limit { background: #10b981; }
      &.threat-invalid_input { background: #8b5cf6; }
      &.threat-suspicious_activity { background: #f97316; }
    }
  }

  .breakdown-label {
    display: flex;
    justify-content: space-between;
    font-size: 14px;

    .threat-name {
      color: var(--color-text);
    }

    .threat-count {
      color: var(--color-text-3);
      font-weight: 600;
    }
  }
}

.security-recommendations {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);

  h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: var(--color-background);
  border-radius: 8px;

  .recommendation-icon {
    font-size: 18px;
    margin-top: 2px;
  }

  .recommendation-text {
    flex: 1;
    color: var(--color-text);
    line-height: 1.5;
  }
}

.real-time-monitor {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;

  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.monitor-controls {
  display: flex;
  gap: 8px;
}

.control-btn {
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

  &.danger:hover {
    background: #fee2e2;
    border-color: #ef4444;
    color: #dc2626;
  }
}

.recent-violations {
  h4 {
    margin: 0 0 12px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-2);
  }
}

.violations-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.violation-item {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;

  &.severity-low { border-left: 4px solid #10b981; }
  &.severity-medium { border-left: 4px solid #f59e0b; }
  &.severity-high { border-left: 4px solid #ef4444; }
  &.severity-critical { border-left: 4px solid #dc2626; }

  .violation-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    font-size: 14px;

    .violation-type {
      flex: 1;
      font-weight: 500;
      color: var(--color-text);
    }

    .violation-time {
      color: var(--color-text-3);
      font-size: 12px;
    }

    .violation-severity {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;

      &.severity-low { background: rgba(16, 185, 129, 0.1); color: #10b981; }
      &.severity-medium { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
      &.severity-high { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
      &.severity-critical { background: rgba(220, 38, 38, 0.1); color: #dc2626; }
    }
  }

  .violation-message {
    color: var(--color-text-2);
    font-size: 13px;
    margin-bottom: 8px;
  }

  .violation-details {
    details {
      summary {
        cursor: pointer;
        color: var(--color-text-3);
        font-size: 12px;
        margin-bottom: 4px;

        &:hover {
          color: var(--color-primary);
        }
      }

      pre {
        background: var(--color-background-mute);
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
}

.security-config {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);

  h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.config-section {
  h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-2);
  }
}

.config-item {
  margin-bottom: 12px;

  label {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-text);
    font-size: 14px;
    cursor: pointer;

    input[type="checkbox"] {
      accent-color: var(--color-primary);
    }

    input[type="number"] {
      padding: 4px 8px;
      border: 1px solid var(--color-border);
      border-radius: 4px;
      background: var(--color-background);
      color: var(--color-text);
      width: 80px;

      &:focus {
        outline: none;
        border-color: var(--color-primary);
      }
    }
  }
}

.blocked-ips {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);

  h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.ip-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ip-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--color-background);
  border-radius: 6px;

  .ip-address {
    font-family: monospace;
    color: var(--color-text);
  }

  .unblock-btn {
    padding: 4px 8px;
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;

    &:hover {
      background: #dc2626;
    }
  }
}

.security-tools {
  background: var(--color-background-soft);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-border);

  h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.tool-card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;

  h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-2);
  }

  .tool-content {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
  }

  .tool-input {
    flex: 1;
    padding: 6px 12px;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    background: var(--color-background-soft);
    color: var(--color-text);
    font-size: 14px;

    &:focus {
      outline: none;
      border-color: var(--color-primary);
    }
  }

  .tool-btn {
    padding: 6px 12px;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;

    &:hover {
      background: var(--color-primary-dark);
    }
  }

  .tool-result {
    padding: 8px;
    background: var(--color-background-mute);
    border-radius: 4px;
    font-size: 13px;
    color: var(--color-text-2);
    word-break: break-all;
  }
}

@media (max-width: 768px) {
  .security-stats {
    grid-template-columns: 1fr;
  }

  .config-grid {
    grid-template-columns: 1fr;
  }

  .tools-grid {
    grid-template-columns: 1fr;
  }

  .monitor-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .violation-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>