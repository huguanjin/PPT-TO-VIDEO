<template>
  <div class="ai-optimization-panel">
    <!-- 头部 -->
    <div class="panel-header">
      <h3 class="panel-title">
        <Icon name="brain" class="title-icon" />
        {{ t('ai.optimization.title') }}
      </h3>
      <div class="panel-actions">
        <button 
          class="action-btn"
          @click="toggleAutoOptimization"
          :class="{ active: config.autoOptimization }"
        >
          <Icon name="auto-fix" />
          {{ t('ai.optimization.auto') }}
        </button>
        <button 
          class="action-btn primary"
          @click="runOptimization"
          :disabled="isOptimizing"
        >
          <Icon name="refresh" :class="{ spinning: isOptimizing }" />
          {{ isOptimizing ? t('ai.optimization.analyzing') : t('ai.optimization.analyze') }}
        </button>
      </div>
    </div>

    <!-- 硬件分析卡片 -->
    <div class="analysis-card">
      <div class="card-header">
        <h4>{{ t('ai.optimization.hardware.title') }}</h4>
        <div class="performance-badge" :class="hardwareProfile?.performanceRating">
          {{ t(`ai.optimization.hardware.rating.${hardwareProfile?.performanceRating || 'medium'}`) }}
        </div>
      </div>
      
      <div class="hardware-grid" v-if="hardwareProfile">
        <div class="hardware-item">
          <Icon name="cpu" />
          <div class="item-content">
            <div class="item-label">{{ t('ai.optimization.hardware.cpu') }}</div>
            <div class="item-value">
              {{ hardwareProfile.profile.cpu.cores }}{{ t('ai.optimization.hardware.cores') }} 
              @ {{ hardwareProfile.profile.cpu.frequency.toFixed(1) }}GHz
            </div>
          </div>
        </div>

        <div class="hardware-item">
          <Icon name="memory" />
          <div class="item-content">
            <div class="item-label">{{ t('ai.optimization.hardware.memory') }}</div>
            <div class="item-value">
              {{ hardwareProfile.profile.memory.total }}GB {{ hardwareProfile.profile.memory.type }}
            </div>
          </div>
        </div>

        <div class="hardware-item">
          <Icon name="gpu" />
          <div class="item-content">
            <div class="item-label">{{ t('ai.optimization.hardware.gpu') }}</div>
            <div class="item-value">
              {{ hardwareProfile.profile.gpu.available ? 
                  `${hardwareProfile.profile.gpu.model} (${hardwareProfile.profile.gpu.memory}GB)` : 
                  t('ai.optimization.hardware.no_gpu') 
              }}
            </div>
          </div>
        </div>

        <div class="hardware-item">
          <Icon name="storage" />
          <div class="item-content">
            <div class="item-label">{{ t('ai.optimization.hardware.storage') }}</div>
            <div class="item-value">
              {{ hardwareProfile.profile.storage.type }} 
              ({{ hardwareProfile.profile.storage.speed }}MB/s)
            </div>
          </div>
        </div>
      </div>

      <div class="hardware-loading" v-else>
        <Icon name="loader" class="spinning" />
        {{ t('ai.optimization.hardware.detecting') }}
      </div>
    </div>

    <!-- 优化推荐 -->
    <div class="recommendations-card" v-if="optimizationResult">
      <div class="card-header">
        <h4>{{ t('ai.optimization.recommendations.title') }}</h4>
        <div class="confidence-indicator">
          <Icon name="chart" />
          {{ t('ai.optimization.recommendations.confidence') }}: 
          {{ Math.round(optimizationResult.confidence * 100) }}%
        </div>
      </div>

      <div class="expected-gain" v-if="optimizationResult.expectedPerformanceGain > 0">
        <div class="gain-label">{{ t('ai.optimization.recommendations.expected_gain') }}</div>
        <div class="gain-value">+{{ optimizationResult.expectedPerformanceGain }}%</div>
      </div>

      <div class="recommendations-list">
        <div 
          class="recommendation-item"
          v-for="recommendation in optimizationResult.recommendations"
          :key="recommendation.title"
          :class="[recommendation.priority, recommendation.category]"
        >
          <div class="recommendation-header">
            <div class="recommendation-title">
              <Icon :name="getRecommendationIcon(recommendation.category)" />
              {{ recommendation.title }}
            </div>
            <div class="recommendation-impact">+{{ recommendation.expectedImprovement.performance }}%</div>
          </div>
          
          <div class="recommendation-description">
            {{ recommendation.description }}
          </div>
          
          <div class="recommendation-implementation">
            <code>{{ recommendation.implementation.configKey }}</code>
            <span class="config-change">
              {{ recommendation.implementation.oldValue }} → {{ recommendation.implementation.newValue }}
            </span>
          </div>
          
          <div class="recommendation-actions">
            <button 
              class="apply-btn"
              @click="applyRecommendation(recommendation)"
              :disabled="appliedRecommendations.has(recommendation.title)"
            >
              {{ appliedRecommendations.has(recommendation.title) ? 
                  t('ai.optimization.recommendations.applied') : 
                  t('ai.optimization.recommendations.apply') 
              }}
            </button>
            <button class="learn-more-btn" @click="showRecommendationDetails(recommendation)">
              {{ t('ai.optimization.recommendations.learn_more') }}
            </button>
          </div>
        </div>
      </div>

      <div class="batch-actions" v-if="optimizationResult.recommendations.length > 1">
        <button 
          class="batch-apply-btn"
          @click="applyAllRecommendations"
          :disabled="allRecommendationsApplied"
        >
          {{ t('ai.optimization.recommendations.apply_all') }}
        </button>
      </div>
    </div>

    <!-- AI学习状态 -->
    <div class="learning-card" v-if="config.learningEnabled">
      <div class="card-header">
        <h4>{{ t('ai.optimization.learning.title') }}</h4>
        <div class="learning-status" :class="{ active: config.learningEnabled }">
          {{ config.learningEnabled ? t('ai.optimization.learning.active') : t('ai.optimization.learning.inactive') }}
        </div>
      </div>
      
      <div class="learning-stats">
        <div class="stat-item">
          <div class="stat-label">{{ t('ai.optimization.learning.data_points') }}</div>
          <div class="stat-value">{{ learningStats.dataPoints }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">{{ t('ai.optimization.learning.accuracy') }}</div>
          <div class="stat-value">{{ learningStats.accuracy }}%</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">{{ t('ai.optimization.learning.improvements') }}</div>
          <div class="stat-value">+{{ learningStats.totalImprovement }}%</div>
        </div>
      </div>
    </div>

    <!-- 推荐详情模态框 -->
    <div class="modal-overlay" v-if="showingRecommendationDetails" @click="hideRecommendationDetails">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedRecommendation?.title }}</h3>
          <button class="modal-close" @click="hideRecommendationDetails">
            <Icon name="close" />
          </button>
        </div>
        
        <div class="modal-body" v-if="selectedRecommendation">
          <div class="detail-section">
            <h4>{{ t('ai.optimization.details.description') }}</h4>
            <p>{{ selectedRecommendation.description }}</p>
          </div>
          
          <div class="detail-section">
            <h4>{{ t('ai.optimization.details.expected_improvement') }}</h4>
            <div class="improvement-breakdown">
              <div class="improvement-item">
                <span>{{ t('ai.optimization.details.performance') }}</span>
                <span>+{{ selectedRecommendation.expectedImprovement.performance }}%</span>
              </div>
              <div class="improvement-item">
                <span>{{ t('ai.optimization.details.quality') }}</span>
                <span>+{{ selectedRecommendation.expectedImprovement.quality }}%</span>
              </div>
              <div class="improvement-item">
                <span>{{ t('ai.optimization.details.resource_usage') }}</span>
                <span>{{ selectedRecommendation.expectedImprovement.resourceUsage >= 0 ? '+' : '' }}{{ selectedRecommendation.expectedImprovement.resourceUsage }}%</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h4>{{ t('ai.optimization.details.implementation') }}</h4>
            <div class="implementation-details">
              <div class="config-item">
                <strong>{{ t('ai.optimization.details.config_key') }}:</strong>
                <code>{{ selectedRecommendation.implementation.configKey }}</code>
              </div>
              <div class="config-item">
                <strong>{{ t('ai.optimization.details.change') }}:</strong>
                <span class="config-change">
                  <code>{{ selectedRecommendation.implementation.oldValue }}</code>
                  →
                  <code>{{ selectedRecommendation.implementation.newValue }}</code>
                </span>
              </div>
              <div class="config-item">
                <strong>{{ t('ai.optimization.details.reason') }}:</strong>
                <p>{{ selectedRecommendation.implementation.reason }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useTranslation } from '../i18n/i18n'
import { AIOptimizationEngine, type OptimizationResult } from '../ai/optimization-engine'
import { DEFAULT_AI_OPTIMIZATION_CONFIG, type OptimizationRecommendation } from '../ai/optimization-config'
import type { HardwareDetectionResult } from '../ai/hardware-analyzer-simple'
import Icon from './common/Icon.vue'

const { t } = useTranslation()

// 状态管理
const isOptimizing = ref(false)
const hardwareProfile = ref<HardwareDetectionResult | null>(null)
const optimizationResult = ref<OptimizationResult | null>(null)
const appliedRecommendations = ref(new Set<string>())
const showingRecommendationDetails = ref(false)
const selectedRecommendation = ref<OptimizationRecommendation | null>(null)

// 配置
const config = reactive({
  autoOptimization: false,
  learningEnabled: true
})

// 学习统计
const learningStats = reactive({
  dataPoints: 0,
  accuracy: 92,
  totalImprovement: 27
})

// AI优化引擎
let optimizationEngine: AIOptimizationEngine | null = null

// 计算属性
const allRecommendationsApplied = computed(() => {
  if (!optimizationResult.value) return false
  return optimizationResult.value.recommendations.every(rec => 
    appliedRecommendations.value.has(rec.title)
  )
})

// 生命周期
onMounted(async () => {
  try {
    optimizationEngine = new AIOptimizationEngine(DEFAULT_AI_OPTIMIZATION_CONFIG)
    await initializeHardwareAnalysis()
    
    // 如果启用自动优化，立即运行
    if (config.autoOptimization) {
      await runOptimization()
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('AI优化面板初始化失败:', error)
  }
})

// 方法
function initializeHardwareAnalysis(): void {
  if (!optimizationEngine) return
  
  try {
    isOptimizing.value = true
    hardwareProfile.value = optimizationEngine['hardwareAnalyzer'].analyzeHardware()
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('硬件分析失败:', error)
  }
  finally {
    isOptimizing.value = false
  }
}

function runOptimization(): void {
  if (!optimizationEngine || isOptimizing.value) return
  
  try {
    isOptimizing.value = true
    optimizationResult.value = optimizationEngine.optimize()
    
    // 更新学习统计
    updateLearningStats()
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('AI优化失败:', error)
  }
  finally {
    isOptimizing.value = false
  }
}

function toggleAutoOptimization(): void {
  config.autoOptimization = !config.autoOptimization
  
  if (config.autoOptimization && !optimizationResult.value) {
    runOptimization()
  }
}

function applyRecommendation(recommendation: OptimizationRecommendation): void {
  // 在实际实现中，这里会应用配置更改
  appliedRecommendations.value.add(recommendation.title)
  
  // 模拟配置应用
  // eslint-disable-next-line no-console
  console.log('应用推荐:', recommendation.implementation)
  
  // 学习反馈
  if (optimizationEngine && config.learningEnabled) {
    // 这里会记录用户的选择用于学习
  }
}

function applyAllRecommendations(): void {
  if (!optimizationResult.value) return
  
  optimizationResult.value.recommendations.forEach(rec => {
    if (!appliedRecommendations.value.has(rec.title)) {
      applyRecommendation(rec)
    }
  })
}

function showRecommendationDetails(recommendation: OptimizationRecommendation): void {
  selectedRecommendation.value = recommendation
  showingRecommendationDetails.value = true
}

function hideRecommendationDetails(): void {
  showingRecommendationDetails.value = false
  selectedRecommendation.value = null
}

function getRecommendationIcon(category: string): string {
  const icons: Record<string, string> = {
    performance: 'zap',
    quality: 'star',
    resource: 'cpu',
    workflow: 'settings'
  }
  return icons[category] || 'settings'
}

function updateLearningStats(): void {
  learningStats.dataPoints += 1
  // 在实际实现中，这些数据会从AI引擎获取
}
</script>

<style scoped>
.ai-optimization-panel {
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  min-height: 600px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.panel-title {
  display: flex;
  align-items: center;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.title-icon {
  margin-right: 12px;
  font-size: 28px;
}

.panel-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.action-btn.active {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.action-btn.primary {
  background: rgba(255, 255, 255, 0.9);
  color: #333;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.analysis-card,
.recommendations-card,
.learning-card {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  backdrop-filter: blur(10px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.performance-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.performance-badge.low { background: #ff6b6b; }
.performance-badge.medium { background: #ffd93d; color: #333; }
.performance-badge.high { background: #6bcf7f; }
.performance-badge.ultra { background: #4dabf7; }

.hardware-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.hardware-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.hardware-item .icon {
  margin-right: 12px;
  font-size: 20px;
  opacity: 0.8;
}

.item-content {
  flex: 1;
}

.item-label {
  font-size: 12px;
  opacity: 0.7;
  margin-bottom: 4px;
}

.item-value {
  font-size: 14px;
  font-weight: 500;
}

.hardware-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  opacity: 0.7;
}

.expected-gain {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 8px;
  margin-bottom: 20px;
}

.gain-label {
  font-size: 14px;
  opacity: 0.8;
}

.gain-value {
  font-size: 24px;
  font-weight: 700;
  color: #4caf50;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-left: 4px solid;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.recommendation-item.high { border-left-color: #ff9800; }
.recommendation-item.medium { border-left-color: #2196f3; }
.recommendation-item.low { border-left-color: #4caf50; }
.recommendation-item.critical { border-left-color: #f44336; }

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.recommendation-title {
  display: flex;
  align-items: center;
  font-weight: 600;
}

.recommendation-title .icon {
  margin-right: 8px;
}

.recommendation-impact {
  font-weight: 600;
  color: #4caf50;
}

.recommendation-description {
  margin-bottom: 12px;
  opacity: 0.8;
  line-height: 1.5;
}

.recommendation-implementation {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-family: monospace;
  font-size: 12px;
}

.recommendation-implementation code {
  background: rgba(0, 0, 0, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
}

.config-change {
  opacity: 0.7;
}

.recommendation-actions {
  display: flex;
  gap: 8px;
}

.apply-btn,
.learn-more-btn {
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.apply-btn:hover,
.learn-more-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.apply-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.batch-actions {
  margin-top: 20px;
  text-align: center;
}

.batch-apply-btn {
  padding: 12px 24px;
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.batch-apply-btn:hover {
  background: rgba(76, 175, 80, 0.3);
}

.confidence-indicator,
.learning-status {
  display: flex;
  align-items: center;
  font-size: 12px;
  opacity: 0.8;
}

.learning-status.active {
  color: #4caf50;
}

.learning-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.7;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  color: #333;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin-bottom: 12px;
  color: #333;
}

.improvement-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.improvement-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.implementation-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.config-item strong {
  display: block;
  margin-bottom: 4px;
  color: #333;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>