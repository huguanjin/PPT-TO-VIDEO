<!--
Netflix配置预览组件 - Phase 5用户体验增强
提供实时配置预览、智能推荐、配置比较等功能
-->
<template>
  <div class="netflix-config-preview">
    <!-- 配置预览头部 -->
    <div class="preview-header">
      <h3 class="preview-title">
        <span class="netflix-logo">📺</span>
        Netflix配置预览
      </h3>
      <div class="preview-controls">
        <el-switch
          v-model="enableRealTimePreview"
          active-text="实时预览"
          inactive-text="手动预览"
          @change="onPreviewModeChange"
        />
        <el-button
          type="primary"
          size="small"
          @click="refreshPreview"
          :loading="isRefreshing"
        >
          刷新预览
        </el-button>
      </div>
    </div>

    <!-- 配置选择和预览区域 -->
    <div class="preview-content">
      <!-- 左侧：配置选择器 -->
      <div class="config-selector-panel">
        <div class="selector-header">
          <h4>🎛️ 配置选择器</h4>
          <el-tooltip content="选择不同的Netflix配置进行预览对比">
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
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
            <div class="config-icon">
              <span v-if="config.recommended">⭐</span>
              <span v-else>📄</span>
            </div>
            <div class="config-info">
              <div class="config-name">{{ config.displayName }}</div>
              <div class="config-description">{{ config.description }}</div>
              <div class="config-tags">
                <el-tag
                  v-for="tag in config.tags"
                  :key="tag"
                  size="small"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            <div class="config-actions">
              <el-button
                size="small"
                circle
                @click.stop="previewConfig(config)"
              >
                👁️
              </el-button>
            </div>
          </div>
        </div>

        <!-- 智能推荐 -->
        <div v-if="smartRecommendations.length > 0" class="smart-recommendations">
          <h5>🤖 智能推荐</h5>
          <div class="recommendation-list">
            <div
              v-for="rec in smartRecommendations"
              :key="rec.configName"
              class="recommendation-item"
              @click="selectConfig(getConfigByName(rec.configName))"
            >
              <div class="rec-icon">🎯</div>
              <div class="rec-content">
                <div class="rec-title">{{ rec.title }}</div>
                <div class="rec-reason">{{ rec.reason }}</div>
                <div class="rec-score">匹配度: {{ rec.score }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：预览区域 -->
      <div class="preview-panel">
        <div class="preview-tabs">
          <el-tabs v-model="activePreviewTab" @tab-change="onTabChange">
            <!-- 字幕效果预览 -->
            <el-tab-pane label="字幕效果" name="subtitle">
              <div class="subtitle-preview">
                <div class="preview-video-container">
                  <div class="mock-video-player">
                    <div class="video-placeholder">
                      <span>📹 视频预览区域</span>
                    </div>
                    <!-- 字幕叠加层 -->
                    <div class="subtitle-overlay">
                      <div
                        v-for="(subtitle, index) in previewSubtitles"
                        :key="index"
                        class="subtitle-text"
                        :style="getSubtitleStyle(subtitle)"
                      >
                        {{ subtitle.text }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 字幕样式控制 -->
                <div class="subtitle-controls">
                  <div class="control-group">
                    <label>示例文本：</label>
                    <el-input
                      v-model="sampleText"
                      placeholder="输入示例字幕文本"
                      @input="updatePreview"
                    />
                  </div>
                  <div class="control-group">
                    <label>字体大小：</label>
                    <el-slider
                      v-model="previewSettings.fontSize"
                      :min="12"
                      :max="72"
                      @change="updatePreview"
                    />
                  </div>
                  <div class="control-group">
                    <label>位置：</label>
                    <el-select v-model="previewSettings.position" @change="updatePreview">
                      <el-option label="底部居中" value="bottom-center" />
                      <el-option label="顶部居中" value="top-center" />
                      <el-option label="左下角" value="bottom-left" />
                      <el-option label="右下角" value="bottom-right" />
                    </el-select>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- 配置详情 -->
            <el-tab-pane label="配置详情" name="details">
              <div class="config-details">
                <div v-if="selectedConfig" class="config-info-detail">
                  <h5>📋 配置信息</h5>
                  <div class="info-grid">
                    <div class="info-item">
                      <span class="info-label">配置名称：</span>
                      <span class="info-value">{{ selectedConfig.displayName }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">版本：</span>
                      <span class="info-value">{{ selectedConfig.version }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">适用场景：</span>
                      <span class="info-value">{{ selectedConfig.scene }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">语言支持：</span>
                      <span class="info-value">{{ selectedConfig.languages?.join(', ') }}</span>
                    </div>
                  </div>

                  <h5>⚙️ 字幕参数</h5>
                  <div class="parameter-list">
                    <div
                      v-for="(value, key) in selectedConfig.parameters"
                      :key="key"
                      class="parameter-item"
                    >
                      <span class="param-key">{{ formatParameterName(key) }}：</span>
                      <span class="param-value">{{ formatParameterValue(value) }}</span>
                    </div>
                  </div>

                  <h5>📊 质量指标</h5>
                  <div class="quality-metrics">
                    <div class="metric-item">
                      <span class="metric-label">可读性：</span>
                      <el-progress
                        :percentage="selectedConfig.metrics?.readability || 0"
                        color="#67c23a"
                      />
                    </div>
                    <div class="metric-item">
                      <span class="metric-label">合规性：</span>
                      <el-progress
                        :percentage="selectedConfig.metrics?.compliance || 0"
                        color="#409eff"
                      />
                    </div>
                    <div class="metric-item">
                      <span class="metric-label">美观度：</span>
                      <el-progress
                        :percentage="selectedConfig.metrics?.aesthetics || 0"
                        color="#e6a23c"
                      />
                    </div>
                  </div>
                </div>
                <div v-else class="no-config-selected">
                  <span>请选择一个配置查看详情</span>
                </div>
              </div>
            </el-tab-pane>

            <!-- 配置比较 -->
            <el-tab-pane label="配置比较" name="compare">
              <div class="config-comparison">
                <div class="comparison-controls">
                  <el-select
                    v-model="comparisonConfigs"
                    multiple
                    placeholder="选择要比较的配置"
                    @change="updateComparison"
                  >
                    <el-option
                      v-for="config in availableConfigs"
                      :key="config.name"
                      :label="config.displayName"
                      :value="config.name"
                    />
                  </el-select>
                </div>

                <div v-if="comparisonData.length > 0" class="comparison-table">
                  <table class="comparison-grid">
                    <thead>
                      <tr>
                        <th>参数</th>
                        <th v-for="config in comparisonData" :key="config.name">
                          {{ config.displayName }}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="param in comparisonParameters" :key="param.key">
                        <td class="param-name">{{ param.label }}</td>
                        <td
                          v-for="config in comparisonData"
                          :key="config.name"
                          class="param-cell"
                        >
                          <span :class="getComparisonCellClass()">
                            {{ formatParameterValue(config.parameters[param.key]) }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="no-comparison">
                  <span>请选择至少两个配置进行比较</span>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>

    <!-- 预览操作栏 -->
    <div class="preview-actions">
      <el-button @click="resetPreview">重置预览</el-button>
      <el-button type="primary" @click="applySelectedConfig">
        应用配置
      </el-button>
      <el-button type="success" @click="saveAsCustomConfig">
        保存为自定义配置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'

// 接口定义
interface NetflixConfig {
  name: string
  displayName: string
  description: string
  version: string
  scene: string
  languages: string[]
  tags: string[]
  recommended: boolean
  parameters: Record<string, any>
  metrics: {
    readability: number
    compliance: number
    aesthetics: number
  }
}

interface PreviewSubtitle {
  text: string
  startTime: number
  endTime: number
  style: Record<string, any>
}

interface SmartRecommendation {
  configName: string
  title: string
  reason: string
  score: number
}

// Props定义
interface Props {
  currentConfig?: string
  contentAnalysis?: {
    language: string
    complexity: number
    duration: number
    slideCount: number
  }
}

const props = withDefaults(defineProps<Props>(), {
  currentConfig: 'default'
})

// Emits定义
const emit = defineEmits<{
  configSelected: [config: NetflixConfig]
  configApplied: [config: NetflixConfig]
  previewUpdated: [data: any]
}>()

// 响应式数据
const enableRealTimePreview = ref(true)
const isRefreshing = ref(false)
const activePreviewTab = ref('subtitle')
const selectedConfig = ref<NetflixConfig | null>(null)
const comparisonConfigs = ref<string[]>([])

const sampleText = ref('这是一个Netflix字幕预览示例文本，展示不同配置的效果。')
const previewSettings = reactive({
  fontSize: 24,
  position: 'bottom-center'
})

// 可用配置数据
const availableConfigs = ref<NetflixConfig[]>([
  {
    name: 'default',
    displayName: '默认配置',
    description: 'Netflix标准默认字幕配置',
    version: '1.0',
    scene: '通用场景',
    languages: ['中文', '英文'],
    tags: ['标准', '通用'],
    recommended: true,
    parameters: {
      fontSize: 24,
      fontFamily: 'Arial',
      color: '#FFFFFF',
      backgroundColor: '#000000',
      opacity: 0.8,
      position: 'bottom-center',
      lineHeight: 1.2,
      maxWidth: 80
    },
    metrics: {
      readability: 85,
      compliance: 95,
      aesthetics: 75
    }
  },
  {
    name: 'accessibility',
    displayName: '无障碍配置',
    description: '适用于无障碍访问的高对比度配置',
    version: '1.1',
    scene: '无障碍场景',
    languages: ['中文', '英文'],
    tags: ['无障碍', '高对比度'],
    recommended: false,
    parameters: {
      fontSize: 28,
      fontFamily: 'Arial Bold',
      color: '#FFFF00',
      backgroundColor: '#000000',
      opacity: 0.9,
      position: 'bottom-center',
      lineHeight: 1.4,
      maxWidth: 75
    },
    metrics: {
      readability: 95,
      compliance: 100,
      aesthetics: 60
    }
  },
  {
    name: 'cinematic',
    displayName: '电影级配置',
    description: '适用于高品质影视内容的优雅配置',
    version: '1.2',
    scene: '影视制作',
    languages: ['中文', '英文', '日文'],
    tags: ['电影', '优雅', '高端'],
    recommended: false,
    parameters: {
      fontSize: 22,
      fontFamily: 'Times New Roman',
      color: '#F5F5F5',
      backgroundColor: 'rgba(0,0,0,0.7)',
      opacity: 0.85,
      position: 'bottom-center',
      lineHeight: 1.3,
      maxWidth: 85
    },
    metrics: {
      readability: 80,
      compliance: 90,
      aesthetics: 95
    }
  }
])

// 智能推荐数据
const smartRecommendations = ref<SmartRecommendation[]>([])

// 预览字幕数据
const previewSubtitles = computed<PreviewSubtitle[]>(() => {
  if (!selectedConfig.value) return []
  
  return [
    {
      text: sampleText.value,
      startTime: 0,
      endTime: 5,
      style: {
        fontSize: `${previewSettings.fontSize}px`,
        fontFamily: selectedConfig.value.parameters.fontFamily,
        color: selectedConfig.value.parameters.color,
        backgroundColor: selectedConfig.value.parameters.backgroundColor,
        opacity: selectedConfig.value.parameters.opacity,
        position: previewSettings.position
      }
    }
  ]
})

// 配置比较数据
const comparisonData = computed(() => {
  return availableConfigs.value.filter(config => 
    comparisonConfigs.value.includes(config.name)
  )
})

// 比较参数列表
const comparisonParameters = ref([
  { key: 'fontSize', label: '字体大小' },
  { key: 'fontFamily', label: '字体族' },
  { key: 'color', label: '文字颜色' },
  { key: 'backgroundColor', label: '背景颜色' },
  { key: 'opacity', label: '透明度' },
  { key: 'lineHeight', label: '行高' },
  { key: 'maxWidth', label: '最大宽度' }
])

// 方法定义
const selectConfig = (config: NetflixConfig) => {
  selectedConfig.value = config
  emit('configSelected', config)
  
  if (enableRealTimePreview.value) {
    updatePreview()
  }
}

const previewConfig = async (config: NetflixConfig) => {
  selectedConfig.value = config
  await updatePreview()
  ElMessage.success(`正在预览配置: ${config.displayName}`)
}

const updatePreview = () => {
  if (!selectedConfig.value) return
  
  // 模拟预览更新
  const previewData = {
    config: selectedConfig.value,
    subtitles: previewSubtitles.value,
    settings: previewSettings
  }
  
  emit('previewUpdated', previewData)
}

const refreshPreview = async () => {
  isRefreshing.value = true
  try {
    await updatePreview()
    ElMessage.success('预览已刷新')
  }
  catch (error) {
    ElMessage.error('预览刷新失败')
  }
  finally {
    isRefreshing.value = false
  }
}

const onPreviewModeChange = (enabled: boolean) => {
  if (enabled) {
    updatePreview()
    ElMessage.info('已启用实时预览')
  }
  else {
    ElMessage.info('已切换到手动预览模式')
  }
}

const onTabChange = (tabName: string) => {
  // 处理标签切换逻辑
  activePreviewTab.value = tabName
}

const updateComparison = () => {
  // 更新配置比较逻辑
  if (comparisonConfigs.value.length > 0) {
    // 处理比较更新
  }
}

const getConfigByName = (name: string): NetflixConfig | null => {
  return availableConfigs.value.find(config => config.name === name) || null
}

const getSubtitleStyle = (subtitle: PreviewSubtitle) => {
  const baseStyle = {
    fontSize: subtitle.style.fontSize,
    fontFamily: subtitle.style.fontFamily,
    color: subtitle.style.color,
    backgroundColor: subtitle.style.backgroundColor,
    opacity: subtitle.style.opacity
  }
  
  // 根据位置设置样式
  switch (subtitle.style.position) {
    case 'bottom-center':
      return { ...baseStyle, bottom: '20px', left: '50%', transform: 'translateX(-50%)' }
    case 'top-center':
      return { ...baseStyle, top: '20px', left: '50%', transform: 'translateX(-50%)' }
    case 'bottom-left':
      return { ...baseStyle, bottom: '20px', left: '20px' }
    case 'bottom-right':
      return { ...baseStyle, bottom: '20px', right: '20px' }
    default:
      return baseStyle
  }
}

const formatParameterName = (key: string): string => {
  const nameMap: Record<string, string> = {
    fontSize: '字体大小',
    fontFamily: '字体族',
    color: '文字颜色',
    backgroundColor: '背景颜色',
    opacity: '透明度',
    position: '位置',
    lineHeight: '行高',
    maxWidth: '最大宽度'
  }
  return nameMap[key] || key
}

const formatParameterValue = (value: any): string => {
  if (typeof value === 'number') {
    return value.toString()
  }
  if (typeof value === 'string') {
    return value
  }
  return JSON.stringify(value)
}

const getComparisonCellClass = (): string => {
  // 返回CSS类名
  return 'comparison-cell'
}

const resetPreview = () => {
  previewSettings.fontSize = 24
  previewSettings.position = 'bottom-center'
  sampleText.value = '这是一个Netflix字幕预览示例文本，展示不同配置的效果。'
  updatePreview()
  ElMessage.info('预览已重置')
}

const applySelectedConfig = () => {
  if (!selectedConfig.value) {
    ElMessage.warning('请先选择一个配置')
    return
  }
  
  emit('configApplied', selectedConfig.value)
  ElMessage.success(`已应用配置: ${selectedConfig.value.displayName}`)
}

const saveAsCustomConfig = async () => {
  if (!selectedConfig.value) {
    ElMessage.warning('请先选择一个配置')
    return
  }
  
  try {
    const { value: configName } = await ElMessageBox.prompt(
      '请输入自定义配置名称',
      '保存自定义配置',
      {
        confirmButtonText: '保存',
        cancelButtonText: '取消'
      }
    )
    
    if (configName) {
      // 这里可以调用API保存自定义配置
      ElMessage.success(`自定义配置 "${configName}" 已保存`)
    }
  } catch {
    ElMessage.info('取消保存')
  }
}

const generateSmartRecommendations = () => {
  // 基于内容分析生成智能推荐
  if (props.contentAnalysis) {
    const recommendations: SmartRecommendation[] = []
    
    if (props.contentAnalysis.complexity > 0.7) {
      recommendations.push({
        configName: 'accessibility',
        title: '推荐无障碍配置',
        reason: '内容复杂度较高，建议使用高对比度配置',
        score: 85
      })
    }
    
    if (props.contentAnalysis.slideCount > 20) {
      recommendations.push({
        configName: 'cinematic',
        title: '推荐电影级配置',
        reason: '内容较长，建议使用优雅的电影级配置',
        score: 90
      })
    }
    
    smartRecommendations.value = recommendations
  }
}

// 生命周期钩子
onMounted(() => {
  // 初始化选择默认配置
  const defaultConfig = availableConfigs.value.find(config => config.name === props.currentConfig)
  if (defaultConfig) {
    selectConfig(defaultConfig)
  }
  
  // 生成智能推荐
  generateSmartRecommendations()
})

// 监听器
watch(() => props.contentAnalysis, () => {
  generateSmartRecommendations()
}, { deep: true })

watch(enableRealTimePreview, (enabled) => {
  if (enabled) {
    updatePreview()
  }
})
</script>

<style scoped>
.netflix-config-preview {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  min-height: 600px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.preview-title {
  margin: 0;
  color: #333;
  font-size: 1.4em;
}

.netflix-logo {
  margin-right: 8px;
}

.preview-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.preview-content {
  display: flex;
  gap: 20px;
  min-height: 500px;
}

.config-selector-panel {
  flex: 0 0 350px;
  background: white;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.config-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.config-item {
  display: flex;
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.config-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.config-selected {
  border-color: #409eff;
  background-color: #f0f8ff;
}

.config-recommended {
  border-color: #f5a623;
  background-color: #fffbf0;
}

.config-icon {
  flex: 0 0 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2em;
}

.config-info {
  flex: 1;
  margin-left: 10px;
}

.config-name {
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.config-description {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 6px;
}

.config-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.config-actions {
  flex: 0 0 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.smart-recommendations {
  border-top: 1px solid #e9ecef;
  padding-top: 15px;
}

.recommendation-list {
  max-height: 150px;
  overflow-y: auto;
}

.recommendation-item {
  display: flex;
  padding: 8px;
  margin-bottom: 6px;
  background: #f8f9fa;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.recommendation-item:hover {
  background: #e9ecef;
}

.rec-icon {
  flex: 0 0 20px;
  margin-right: 8px;
}

.rec-content {
  flex: 1;
}

.rec-title {
  font-weight: bold;
  font-size: 0.9em;
  color: #333;
}

.rec-reason {
  font-size: 0.8em;
  color: #666;
  margin: 2px 0;
}

.rec-score {
  font-size: 0.8em;
  color: #409eff;
}

.preview-panel {
  flex: 1;
  background: white;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.subtitle-preview {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-video-container {
  position: relative;
  border-radius: 6px;
  overflow: hidden;
}

.mock-video-player {
  position: relative;
  width: 100%;
  height: 300px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2em;
}

.subtitle-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.subtitle-text {
  position: absolute;
  padding: 8px 16px;
  border-radius: 4px;
  text-align: center;
  white-space: nowrap;
  max-width: 80%;
}

.subtitle-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-group label {
  flex: 0 0 100px;
  font-weight: bold;
  color: #333;
}

.config-details {
  padding: 10px 0;
}

.config-info-detail h5 {
  margin: 20px 0 10px 0;
  color: #333;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 5px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.info-label {
  flex: 0 0 80px;
  font-weight: bold;
  color: #666;
}

.info-value {
  color: #333;
}

.parameter-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.parameter-item {
  display: flex;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.param-key {
  flex: 0 0 120px;
  font-weight: bold;
  color: #666;
}

.param-value {
  color: #333;
}

.quality-metrics {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.metric-label {
  flex: 0 0 80px;
  font-weight: bold;
  color: #666;
}

.no-config-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #999;
  font-size: 1.1em;
}

.config-comparison {
  padding: 10px 0;
}

.comparison-controls {
  margin-bottom: 20px;
}

.comparison-table {
  overflow-x: auto;
}

.comparison-grid {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #e9ecef;
}

.comparison-grid th,
.comparison-grid td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.comparison-grid th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #333;
}

.param-name {
  font-weight: bold;
  color: #666;
  background-color: #f8f9fa;
}

.param-cell {
  text-align: center;
}

.comparison-cell {
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #e9ecef;
}

.no-comparison {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #999;
  font-size: 1.1em;
}

.preview-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

/* 滚动条样式 */
.config-list::-webkit-scrollbar,
.recommendation-list::-webkit-scrollbar {
  width: 6px;
}

.config-list::-webkit-scrollbar-track,
.recommendation-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.config-list::-webkit-scrollbar-thumb,
.recommendation-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.config-list::-webkit-scrollbar-thumb:hover,
.recommendation-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>