<template>
  <div class="real-time-validation">
    <div class="validation-header">
      <h3>实时验证 & 测试</h3>
      <p class="subtitle">配置实时验证、冲突检测和性能分析</p>
    </div>

    <!-- 验证控制面板 -->
    <div class="validation-controls">
      <div class="control-group">
        <label class="control-label">验证模式：</label>
        <select v-model="validationLevel" class="control-select">
          <option value="basic">基础验证</option>
          <option value="full">完整验证</option>
        </select>
      </div>
      
      <div class="control-group">
        <label class="toggle-label">
          <input 
            type="checkbox" 
            v-model="autoValidation"
            @change="toggleAutoValidation"
          />
          自动验证
        </label>
      </div>
      
      <button 
        class="btn btn-primary"
        @click="runValidation"
        :disabled="isValidating"
      >
        {{ isValidating ? '验证中...' : '立即验证' }}
      </button>
    </div>

    <!-- 验证结果仪表盘 -->
    <div class="validation-dashboard" v-if="lastValidation">
      <!-- 总体状态 -->
      <div class="status-card" :class="getStatusClass()">
        <div class="status-content">
          <h4>{{ getStatusTitle() }}</h4>
          <p>{{ getStatusDescription() }}</p>
        </div>
        <div class="status-score">
          <div class="score-circle">
            {{ Math.round(lastValidation.performance_score) }}
          </div>
          <span class="score-label">性能分数</span>
        </div>
      </div>

      <!-- 详细结果 -->
      <div class="validation-results">
        <div class="result-tabs">
          <button 
            v-for="tab in resultTabs" 
            :key="tab.key"
            class="tab-btn"
            :class="{ active: activeResultTab === tab.key }"
            @click="activeResultTab = tab.key"
          >
            {{ tab.label }}
            <span v-if="getTabCount(tab.key)" class="tab-count">{{ getTabCount(tab.key) }}</span>
          </button>
        </div>

        <div class="result-content">
          <!-- 错误列表 -->
          <div v-if="activeResultTab === 'errors'" class="result-section">
            <div v-if="lastValidation.errors.length === 0" class="empty-state">
              <p>太好了！没有发现任何错误</p>
            </div>
            <div v-else class="message-list">
              <div 
                v-for="(error, index) in lastValidation.errors" 
                :key="index"
                class="message-item error"
              >
                <span>{{ error }}</span>
              </div>
            </div>
          </div>

          <!-- 警告列表 -->
          <div v-if="activeResultTab === 'warnings'" class="result-section">
            <div v-if="lastValidation.warnings.length === 0" class="empty-state">
              <p>没有警告信息</p>
            </div>
            <div v-else class="message-list">
              <div 
                v-for="(warning, index) in lastValidation.warnings" 
                :key="index"
                class="message-item warning"
              >
                <span>{{ warning }}</span>
              </div>
            </div>
          </div>

          <!-- 建议列表 -->
          <div v-if="activeResultTab === 'suggestions'" class="result-section">
            <div v-if="lastValidation.suggestions.length === 0" class="empty-state">
              <p>当前配置已优化，无额外建议</p>
            </div>
            <div v-else class="message-list">
              <div 
                v-for="(suggestion, index) in lastValidation.suggestions" 
                :key="index"
                class="message-item suggestion"
              >
                <span>{{ suggestion }}</span>
              </div>
            </div>
          </div>

          <!-- 冲突检测 -->
          <div v-if="activeResultTab === 'conflicts'" class="result-section">
            <div class="conflict-header">
              <button 
                class="btn btn-outline"
                @click="detectConflicts"
                :disabled="isDetectingConflicts"
              >
                {{ isDetectingConflicts ? '检测中...' : '检测冲突' }}
              </button>
            </div>
            
            <div v-if="conflictResult" class="conflict-results">
              <div class="conflict-summary" :class="conflictResult.severity">
                <div class="conflict-info">
                  <h5>{{ conflictResult.has_conflicts ? '发现配置冲突' : '未发现冲突' }}</h5>
                  <p>{{ conflictResult.impact_description }}</p>
                </div>
              </div>
              
              <div v-if="conflictResult.conflicts.length > 0" class="conflict-list">
                <div 
                  v-for="(conflict, index) in conflictResult.conflicts"
                  :key="index"
                  class="conflict-item"
                >
                  <div class="conflict-title">{{ conflict.description }}</div>
                  <div class="conflict-sections">
                    影响配置：{{ conflict.sections.join(', ') }}
                  </div>
                  <div class="conflict-recommendation">
                    {{ conflict.recommendation }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 性能分析 -->
          <div v-if="activeResultTab === 'performance'" class="result-section">
            <div class="performance-header">
              <button 
                class="btn btn-outline"
                @click="analyzePerformance"
                :disabled="isAnalyzingPerformance"
              >
                {{ isAnalyzingPerformance ? '分析中...' : '性能分析' }}
              </button>
            </div>
            
            <div v-if="performanceResult" class="performance-results">
              <div class="performance-grid">
                <div class="performance-card">
                  <h5>预计处理时间</h5>
                  <div class="metric-value">
                    {{ performanceResult.estimated_processing_time.estimated_minutes }} 分钟
                  </div>
                </div>
                
                <div class="performance-card">
                  <h5>内存使用</h5>
                  <div class="metric-value">
                    {{ performanceResult.resource_usage.estimated_memory_mb }} MB
                  </div>
                </div>
                
                <div class="performance-card">
                  <h5>复杂度</h5>
                  <div class="metric-value" :class="performanceResult.estimated_processing_time.factors.complexity">
                    {{ performanceResult.estimated_processing_time.factors.complexity.toUpperCase() }}
                  </div>
                </div>
              </div>
              
              <div v-if="performanceResult.performance_suggestions.length > 0" class="performance-suggestions">
                <h5>性能优化建议</h5>
                <div class="suggestion-list">
                  <div 
                    v-for="(suggestion, index) in performanceResult.performance_suggestions"
                    :key="index"
                    class="suggestion-item"
                  >
                    <span>{{ suggestion }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { apiRequest } from '@/config/api'

interface ValidationResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
  suggestions: string[]
  performance_score: number
  validation_time: number
  timestamp: string
}

interface ConflictResult {
  has_conflicts: boolean
  conflicts: Array<{
    type: string
    description: string
    sections: string[]
    recommendation: string
  }>
  severity: string
  impact_description: string
}

interface PerformanceResult {
  estimated_processing_time: {
    estimated_seconds: number
    estimated_minutes: number
    factors: {
      resolution_impact: string
      complexity: string
    }
  }
  resource_usage: {
    estimated_memory_mb: number
    estimated_cpu_percent: number
    disk_usage_estimate: string
    network_usage: string
  }
  performance_suggestions: string[]
  analysis_time: number
  timestamp: string
}

const props = defineProps<{
  config: Record<string, any>
}>()

// 状态管理
const validationLevel = ref<'basic' | 'full'>('full')
const autoValidation = ref(false)
const isValidating = ref(false)
const isDetectingConflicts = ref(false)
const isAnalyzingPerformance = ref(false)

const lastValidation = ref<ValidationResult | null>(null)
const conflictResult = ref<ConflictResult | null>(null)
const performanceResult = ref<PerformanceResult | null>(null)

const activeResultTab = ref('errors')

// 自动验证定时器
let autoValidationTimer: number | null = null

// 结果标签页配置
const resultTabs = [
  { key: 'errors', label: '错误' },
  { key: 'warnings', label: '警告' },
  { key: 'suggestions', label: '建议' },
  { key: 'conflicts', label: '冲突' },
  { key: 'performance', label: '性能' }
]

// 方法
const runValidation = async () => {
  if (isValidating.value) return
  
  isValidating.value = true
  try {
    const response = await apiRequest('/api/config/validate/realtime', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        config: props.config,
        level: validationLevel.value
      })
    })
    
    if (response.success) {
      lastValidation.value = response.data
    }
  }
  catch (error) {
    // 处理错误
  }
  finally {
    isValidating.value = false
  }
}

const detectConflicts = async () => {
  if (isDetectingConflicts.value) return
  
  isDetectingConflicts.value = true
  try {
    const response = await apiRequest('/api/config/conflicts/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        config: props.config
      })
    })
    
    if (response.success) {
      conflictResult.value = response.data
    }
  }
  catch (error) {
    // 处理错误
  }
  finally {
    isDetectingConflicts.value = false
  }
}

const analyzePerformance = async () => {
  if (isAnalyzingPerformance.value) return
  
  isAnalyzingPerformance.value = true
  try {
    const response = await apiRequest('/api/config/performance/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        config: props.config
      })
    })
    
    if (response.success) {
      performanceResult.value = response.data
    }
  }
  catch (error) {
    // 处理错误
  }
  finally {
    isAnalyzingPerformance.value = false
  }
}

const toggleAutoValidation = () => {
  if (autoValidation.value) {
    startAutoValidation()
  }
  else {
    stopAutoValidation()
  }
}

const startAutoValidation = () => {
  stopAutoValidation() // 确保清除之前的定时器
  autoValidationTimer = setInterval(() => {
    runValidation()
  }, 5000) // 每5秒验证一次
}

const stopAutoValidation = () => {
  if (autoValidationTimer) {
    clearInterval(autoValidationTimer)
    autoValidationTimer = null
  }
}

// 计算属性和工具方法
const getStatusClass = () => {
  if (!lastValidation.value) return 'pending'
  return lastValidation.value.is_valid ? 'valid' : 'invalid'
}

const getStatusTitle = () => {
  if (!lastValidation.value) return '等待验证'
  return lastValidation.value.is_valid ? '配置有效' : '配置无效'
}

const getStatusDescription = () => {
  if (!lastValidation.value) return '点击"立即验证"开始检查配置'
  
  const { errors, warnings, suggestions } = lastValidation.value
  const parts = []
  
  if (errors.length > 0) parts.push(`${errors.length}个错误`)
  if (warnings.length > 0) parts.push(`${warnings.length}个警告`)
  if (suggestions.length > 0) parts.push(`${suggestions.length}个建议`)
  
  return parts.length > 0 ? parts.join('，') : '配置完美！'
}

const getTabCount = (tabKey: string) => {
  if (!lastValidation.value) return 0
  
  switch (tabKey) {
    case 'errors': return lastValidation.value.errors.length
    case 'warnings': return lastValidation.value.warnings.length
    case 'suggestions': return lastValidation.value.suggestions.length
    case 'conflicts': return conflictResult.value?.conflicts.length || 0
    default: return 0
  }
}

// 监听配置变化
watch(() => props.config, () => {
  if (autoValidation.value) {
    runValidation()
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  // 初始验证
  runValidation()
})

onUnmounted(() => {
  stopAutoValidation()
})
</script>

<style scoped>
.real-time-validation {
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
}

.validation-header {
  margin-bottom: 24px;
}

.validation-header h3 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 20px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

/* 验证控制面板 */
.validation-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.control-select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
}

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline:hover:not(:disabled) {
  background: #f9fafb;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 验证结果仪表盘 */
.status-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  margin-bottom: 20px;
}

.status-card.valid {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, white 100%);
}

.status-card.invalid {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, white 100%);
}

.status-card.pending {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, white 100%);
}

.status-content {
  flex: 1;
}

.status-content h4 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.status-content p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.status-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: #3b82f6;
}

.score-label {
  font-size: 12px;
  color: #6b7280;
}

/* 结果标签页 */
.result-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 20px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border: none;
  background: none;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.tab-btn.active {
  color: #3b82f6;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: #3b82f6;
}

.tab-count {
  background: #ef4444;
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

/* 消息列表 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-item {
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid;
}

.message-item.error {
  background: #fef2f2;
  border-left-color: #ef4444;
}

.message-item.warning {
  background: #fffbeb;
  border-left-color: #f59e0b;
}

.message-item.suggestion {
  background: #f0f9ff;
  border-left-color: #3b82f6;
}

/* 冲突检测 */
.conflict-header {
  margin-bottom: 16px;
}

.conflict-summary {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.conflict-summary.low {
  background: #f0f9ff;
  border: 1px solid #bfdbfe;
}

.conflict-summary.medium {
  background: #fffbeb;
  border: 1px solid #fed7aa;
}

.conflict-summary.high {
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.conflict-summary.critical {
  background: #991b1b;
  color: white;
  border: 1px solid #dc2626;
}

.conflict-info h5 {
  margin: 0 0 4px 0;
  font-weight: 600;
}

.conflict-info p {
  margin: 0;
  font-size: 14px;
}

.conflict-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.conflict-item {
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.conflict-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.conflict-sections {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
}

.conflict-recommendation {
  font-size: 14px;
  color: #3b82f6;
}

/* 性能分析 */
.performance-header {
  margin-bottom: 16px;
}

.performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.performance-card {
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  text-align: center;
}

.performance-card h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.metric-value.low {
  color: #10b981;
}

.metric-value.medium {
  color: #f59e0b;
}

.metric-value.high {
  color: #ef4444;
}

.performance-suggestions h5 {
  margin: 0 0 12px 0;
  color: #1f2937;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
  font-size: 14px;
  color: #1e40af;
}
</style>
