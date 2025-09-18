<!--
Netflix配置预览组件 - Phase 5用户体验增强 (简化版)
整合了智能推荐、配置比较、实时预览等功能的主组件
-->
<template>
  <div class="netflix-config-preview">
    <!-- 配置预览头部 -->
    <div class="preview-header">
      <h3 class="preview-title">
        <span class="netflix-logo">📺</span>
        {{ t('netflix.title') }}
      </h3>
      <div class="preview-controls">
        <!-- 语言切换器 -->
        <LanguageSwitcher />
        
        <label class="switch-label">
          <input
            v-model="enableRealTimePreview"
            type="checkbox"
            @change="onPreviewModeChange"
          />
          <span class="switch-text">{{ t('netflix.preview.real_time') }}</span>
        </label>
        <button
          class="refresh-btn"
          @click="refreshPreview"
          :disabled="isRefreshing"
        >
          {{ isRefreshing ? t('netflix.preview.refreshing') : t('netflix.actions.refresh_preview') }}
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="preview-content">
      <!-- 左侧：配置选择器 -->
      <div class="config-selector-panel">
        <div class="selector-header">
          <h4>🎛️ {{ t('netflix.config.selector') }}</h4>
          <span class="help-text">{{ t('netflix.config.selector') }}</span>
        </div>

        <!-- 配置列表 -->
        <div class="config-list">
          <div
            v-for="config in availableConfigs"
            :key="config.name"
            class="config-item"
            :class="{
              'config-selected': selectedConfig?.name === config.name,
              'config-recommended': config.recommended
            }"
            @click="selectConfig(config)"
          >
            <div class="config-header">
              <span class="config-name">{{ config.name }}</span>
              <span v-if="config.recommended" class="recommended-badge">{{ t('netflix.badges.recommended') }}</span>
            </div>
            <div class="config-description">{{ config.description }}</div>
            <div class="config-metrics">
              <span class="metric">{{ t('performance.processing_speed') }}: {{ config.performance }}%</span>
              <span class="metric">{{ t('netflix.config.quality') }}: {{ config.quality }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：预览和推荐区域 -->
      <div class="preview-panel">
        <!-- 智能推荐组件 -->
        <NetflixSmartRecommendations
          :current-config="selectedConfig?.params || {}"
          :user-preferences="userPreferences"
          @recommendation-applied="onRecommendationApplied"
          @recommendation-previewed="onRecommendationPreviewed"
        />

        <!-- 当前配置预览 -->
        <div v-if="selectedConfig" class="config-preview">
          <div class="preview-title-section">
            <h4>📋 配置详情预览</h4>
            <div class="preview-actions">
              <button class="export-btn" @click="exportConfig">导出配置</button>
              <button class="save-btn" @click="saveConfig">保存配置</button>
            </div>
          </div>

          <div class="config-details">
            <div class="config-section">
              <h5>🎬 核心参数</h5>
              <div class="param-grid">
                <div class="param-item">
                  <label>Whisper模型:</label>
                  <span class="param-value">{{ selectedConfig.params.whisper_model || '未设置' }}</span>
                </div>
                <div class="param-item">
                  <label>批处理大小:</label>
                  <span class="param-value">{{ selectedConfig.params.batch_size || '默认' }}</span>
                </div>
                <div class="param-item">
                  <label>性能模式:</label>
                  <span class="param-value">{{ selectedConfig.params.performance_mode ? '启用' : '禁用' }}</span>
                </div>
                <div class="param-item">
                  <label>字幕样式:</label>
                  <span class="param-value">{{ selectedConfig.params.subtitle_style || 'Netflix标准' }}</span>
                </div>
              </div>
            </div>

            <div class="config-section">
              <h5>⚡ 性能优化</h5>
              <div class="performance-indicators">
                <div class="indicator">
                  <span class="indicator-label">处理速度:</span>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      :style="{ width: `${selectedConfig.performance}%` }"
                    ></div>
                  </div>
                  <span class="indicator-value">{{ selectedConfig.performance }}%</span>
                </div>
                <div class="indicator">
                  <span class="indicator-label">内存使用:</span>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill memory" 
                      :style="{ width: `${selectedConfig.memoryUsage}%` }"
                    ></div>
                  </div>
                  <span class="indicator-value">{{ selectedConfig.memoryUsage }}%</span>
                </div>
                <div class="indicator">
                  <span class="indicator-label">质量评分:</span>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill quality" 
                      :style="{ width: `${selectedConfig.quality}%` }"
                    ></div>
                  </div>
                  <span class="indicator-value">{{ selectedConfig.quality }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 配置比较组件 -->
        <NetflixConfigComparison
          :selected-config="selectedConfig"
          :available-configs="availableConfigs"
          @config-added="onConfigAddedToComparison"
          @config-removed="onConfigRemovedFromComparison"
          @comparison-cleared="onComparisonCleared"
        />
      </div>
    </div>

    <!-- 状态提示 -->
    <div v-if="statusMessage" class="status-message" :class="statusType">
      {{ statusMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useTranslation } from '../i18n/i18n'
import NetflixSmartRecommendations from './NetflixSmartRecommendations.vue'
import NetflixConfigComparison from './NetflixConfigComparison.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

// 使用国际化
const { t } = useTranslation()

// 接口定义
interface NetflixConfig {
  name: string
  description?: string
  recommended?: boolean
  performance: number
  quality: number
  memoryUsage: number
  params: Record<string, any>
}

interface SmartRecommendation {
  id: string
  title: string
  description: string
  score: number
  priority: 'high' | 'medium' | 'low'
  benefits: string[]
  config: Record<string, any>
}

// 响应式数据
const enableRealTimePreview = ref(true)
const isRefreshing = ref(false)
const selectedConfig = ref<NetflixConfig | null>(null)
const statusMessage = ref('')
const statusType = ref<'success' | 'warning' | 'error' | ''>('')

// 用户偏好设置
const userPreferences = reactive({
  preferPerformance: true,
  preferQuality: false,
  hardwareLevel: 'medium'
})

// 可用配置列表
const availableConfigs = ref<NetflixConfig[]>([
  {
    name: 'Netflix高性能配置',
    description: '针对处理速度优化的高性能配置',
    recommended: true,
    performance: 95,
    quality: 85,
    memoryUsage: 75,
    params: {
      whisper_model: 'medium',
      batch_size: 8,
      performance_mode: true,
      subtitle_style: 'netflix_v2',
      sync_accuracy: 'high'
    }
  },
  {
    name: 'Netflix质量优先配置',
    description: '注重字幕质量和准确性的配置',
    recommended: false,
    performance: 75,
    quality: 98,
    memoryUsage: 85,
    params: {
      whisper_model: 'large',
      batch_size: 4,
      performance_mode: false,
      subtitle_style: 'netflix_premium',
      sync_accuracy: 'ultra_high'
    }
  },
  {
    name: 'Netflix平衡配置',
    description: '性能与质量的完美平衡',
    recommended: false,
    performance: 85,
    quality: 88,
    memoryUsage: 70,
    params: {
      whisper_model: 'small',
      batch_size: 6,
      performance_mode: true,
      subtitle_style: 'netflix_standard',
      sync_accuracy: 'medium'
    }
  }
])

// 方法定义
const selectConfig = (config: NetflixConfig) => {
  selectedConfig.value = config
  showStatus(t('netflix.status.config_selected', { name: config.name }), 'success')
  
  if (enableRealTimePreview.value) {
    refreshPreview()
  }
}

const onPreviewModeChange = () => {
  const modeKey = enableRealTimePreview.value ? 'netflix.status.preview_mode_real_time' : 'netflix.status.preview_mode_manual'
  showStatus(t(modeKey), 'success')
}

const refreshPreview = async () => {
  if (!selectedConfig.value) return
  
  isRefreshing.value = true
  showStatus(t('netflix.preview.refreshing'), '')
  
  try {
    // 模拟刷新延迟
    await new Promise(resolve => setTimeout(resolve, 1000))
    showStatus(t('netflix.status.preview_refreshed'), 'success')
  }
  catch (error) {
    showStatus(t('netflix.status.preview_refresh_failed'), 'error')
  }
  finally {
    isRefreshing.value = false
  }
}

const exportConfig = () => {
  if (!selectedConfig.value) return
  
  const configJson = JSON.stringify(selectedConfig.value, null, 2)
  const blob = new Blob([configJson], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `netflix_config_${selectedConfig.value.name}.json`
  a.click()
  URL.revokeObjectURL(url)
  
  showStatus(t('netflix.status.config_exported'), 'success')
}

const saveConfig = () => {
  if (!selectedConfig.value) return
  
  // 模拟保存配置
  localStorage.setItem('netflix_config', JSON.stringify(selectedConfig.value))
  showStatus(t('netflix.status.config_saved'), 'success')
}

const onRecommendationApplied = (recommendation: SmartRecommendation) => {
  if (selectedConfig.value) {
    selectedConfig.value.params = { ...selectedConfig.value.params, ...recommendation.config }
    showStatus(`已应用推荐: ${recommendation.title}`, 'success')
  }
}

const onRecommendationPreviewed = (recommendation: SmartRecommendation) => {
  showStatus(`预览推荐: ${recommendation.title}`, '')
}

const onConfigAddedToComparison = (config: NetflixConfig) => {
  showStatus(`已添加 ${config.name} 到比较列表`, 'success')
}

const onConfigRemovedFromComparison = (config: NetflixConfig) => {
  showStatus(`已从比较列表移除 ${config.name}`, 'warning')
}

const onComparisonCleared = () => {
  showStatus('已清空配置比较列表', 'warning')
}

const showStatus = (message: string, type: 'success' | 'warning' | 'error' | '') => {
  statusMessage.value = message
  statusType.value = type
  
  setTimeout(() => {
    statusMessage.value = ''
    statusType.value = ''
  }, 3000)
}

// 组件挂载时初始化
onMounted(() => {
  // 默认选择推荐配置
  const recommendedConfig = availableConfigs.value.find(config => config.recommended)
  if (recommendedConfig) {
    selectConfig(recommendedConfig)
  }
})
</script>

<style scoped>
.netflix-config-preview {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.netflix-logo {
  font-size: 28px;
}

.preview-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.switch-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.switch-text {
  font-size: 14px;
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.preview-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 24px;
  min-height: 600px;
}

.config-selector-panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  height: fit-content;
}

.selector-header {
  margin-bottom: 20px;
}

.selector-header h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
}

.help-text {
  font-size: 14px;
  color: #666;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-item {
  padding: 16px;
  border: 2px solid #e1e1e1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.config-item:hover {
  border-color: #4CAF50;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.config-selected {
  border-color: #2196F3 !important;
  background: #e3f2fd !important;
}

.config-recommended {
  border-color: #FF9800;
  background: #fff3e0;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.config-name {
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.recommended-badge {
  background: #FF9800;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.config-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  line-height: 1.4;
}

.config-metrics {
  display: flex;
  gap: 12px;
}

.metric {
  font-size: 12px;
  color: #888;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
}

.preview-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-preview {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.preview-title-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.preview-title-section h4 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.export-btn, .save-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.export-btn {
  background: #2196F3;
  color: white;
}

.export-btn:hover {
  background: #1976D2;
}

.save-btn {
  background: #4CAF50;
  color: white;
}

.save-btn:hover {
  background: #45a049;
}

.config-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-section h5 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
  border-bottom: 2px solid #e1e1e1;
  padding-bottom: 8px;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item label {
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.param-value {
  font-size: 14px;
  color: #333;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  border-left: 3px solid #2196F3;
}

.performance-indicators {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.indicator-label {
  min-width: 80px;
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e1e1e1;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4CAF50;
  transition: width 0.3s ease;
}

.progress-fill.memory {
  background: #FF9800;
}

.progress-fill.quality {
  background: #2196F3;
}

.indicator-value {
  min-width: 40px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  text-align: right;
}

.status-message {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 6px;
  color: white;
  font-weight: 500;
  font-size: 14px;
  z-index: 1000;
  animation: slideInUp 0.3s ease;
}

.status-message.success {
  background: #4CAF50;
}

.status-message.warning {
  background: #FF9800;
}

.status-message.error {
  background: #f44336;
}

.status-message:not(.success):not(.warning):not(.error) {
  background: #2196F3;
}

@keyframes slideInUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@media (max-width: 1200px) {
  .preview-content {
    grid-template-columns: 1fr;
  }
  
  .param-grid {
    grid-template-columns: 1fr;
  }
}
</style>