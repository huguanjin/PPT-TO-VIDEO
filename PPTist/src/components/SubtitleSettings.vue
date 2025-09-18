<template>
  <div class="config-section">
    <h2>字幕设置</h2>
    <div class="form-grid">
      <div class="form-item checkbox-item">
        <label>
          <input type="checkbox" v-model="config.subtitle.enabled" />
          启用字幕
        </label>
      </div>
      
      <!-- Netflix级增强字幕功能 -->
      <div class="form-item checkbox-item">
        <label>
          <input type="checkbox" v-model="config.subtitle.use_enhanced_mode" />
          启用Netflix级增强字幕
        </label>
        <small class="help-text">使用精确时间对齐和智能间隙填充算法</small>
      </div>
      
      <!-- 🎯 Netflix V2配置选择器 -->
      <div class="form-item" v-if="config.subtitle.use_enhanced_mode">
        <label>Netflix配置模板</label>
        <div class="netflix-config-selector">
          <select v-model="selectedNetflixConfig" @change="onNetflixConfigChange">
            <option value="">选择Netflix配置模板...</option>
            <option v-for="configName in availableNetflixConfigs" :key="configName" :value="configName">
              {{ getNetflixConfigDisplayName(configName) }}
            </option>
          </select>
          <button @click="refreshNetflixConfigs" class="btn-refresh" title="刷新配置列表">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z" />
            </svg>
          </button>
        </div>
        <small class="help-text">选择预设的Netflix标准配置模板，或使用自定义配置</small>
      </div>
      
      <!-- Netflix配置状态显示 -->
      <div class="form-item" v-if="config.subtitle.use_enhanced_mode && netflixConfigStatus">
        <div class="netflix-status" :class="netflixConfigStatus.type">
          <div class="status-icon">
            <svg v-if="netflixConfigStatus.type === 'success'" width="16" height="16" viewBox="0 0 24 24">
              <path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z" />
            </svg>
            <svg v-else-if="netflixConfigStatus.type === 'warning'" width="16" height="16" viewBox="0 0 24 24">
              <path d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24">
              <path d="M13,14H11V10H13M13,18H11V16H13M1,21H23L12,2L1,21Z" />
            </svg>
          </div>
          <div class="status-content">
            <div class="status-title">{{ netflixConfigStatus.title }}</div>
            <div class="status-message">{{ netflixConfigStatus.message }}</div>
            <div v-if="netflixConfigStatus.details" class="status-details">
              <div v-for="detail in netflixConfigStatus.details" :key="detail">{{ detail }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <template v-if="config.subtitle.use_enhanced_mode">
        <div class="enhanced-config">
          <div class="enhanced-title">增强字幕配置</div>
          
          <div class="form-item checkbox-item">
            <label>
              <input type="checkbox" v-model="config.subtitle.enable_precise_alignment" />
              精确时间对齐
            </label>
            <small class="help-text">字符级精确匹配，提升时间轴准确性</small>
          </div>
          
          <div class="form-item checkbox-item">
            <label>
              <input type="checkbox" v-model="config.subtitle.enable_gap_filling" />
              智能间隙填充
            </label>
            <small class="help-text">消除不自然的停顿，优化观看体验</small>
          </div>
          
          <div class="form-item checkbox-item">
            <label>
              <input type="checkbox" v-model="config.subtitle.auto_punctuation_removal" />
              自动标点优化
            </label>
            <small class="help-text">自动调整标点符号以提升阅读体验</small>
          </div>
          
          <div class="form-item">
            <label>每行字符数限制</label>
            <input type="number" v-model="config.subtitle.max_chars_per_line" min="20" max="60" />
            <small class="help-text">控制字幕行长度，建议40-50字符</small>
          </div>
        </div>
      </template>
      
      <div class="form-item">
        <label>字体</label>
        <select v-model="config.subtitle.font_family">
          <option value="SimHei">黑体</option>
          <option value="SimSun">宋体</option>
          <option value="Microsoft YaHei">微软雅黑</option>
          <option value="Arial">Arial</option>
        </select>
      </div>
      <div class="form-item">
        <label>字号</label>
        <input type="number" v-model="config.subtitle.font_size" min="12" max="72" />
      </div>
      <div class="form-item">
        <label>字体颜色</label>
        <input type="color" v-model="config.subtitle.font_color" />
      </div>
      <div class="form-item">
        <label>背景颜色</label>
        <input type="color" v-model="config.subtitle.background_color" />
      </div>
      <div class="form-item">
        <label>位置</label>
        <select v-model="config.subtitle.position">
          <option value="bottom">底部</option>
          <option value="center">居中</option>
          <option value="top">顶部</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs, onMounted, watch } from 'vue'
import { apiRequest } from '@/config/api'

interface SubtitleConfig {
  enabled: boolean
  font_family: string
  font_size: number
  font_color: string
  background_color: string
  position: string
  use_enhanced_mode: boolean
  enable_precise_alignment: boolean
  enable_gap_filling: boolean
  max_chars_per_line: number
  auto_punctuation_removal: boolean
  netflix_config_name?: string // 🎯 新增Netflix配置名称
}

interface Props {
  config: {
    subtitle: SubtitleConfig
  }
}

interface NetflixConfigStatus {
  type: 'success' | 'warning' | 'error'
  title: string
  message: string
  details?: string[]
}

const props = defineProps<Props>()
const { config } = toRefs(props)

// 🎯 Netflix配置管理
const selectedNetflixConfig = ref<string>('')
const availableNetflixConfigs = ref<string[]>([])
const netflixConfigStatus = ref<NetflixConfigStatus | null>(null)
const loadingNetflixConfigs = ref(false)

// Netflix配置显示名称映射
const netflixConfigNames: Record<string, string> = {
  'netflix_standard': 'Netflix 标准配置',
  'netflix_hd': 'Netflix 高清配置',
  'videolingo_netflix': 'VideoLingo Netflix',
  'accessibility': 'Netflix 无障碍配置',
  'default': '默认配置'
}

// 获取Netflix配置显示名称
const getNetflixConfigDisplayName = (configName: string): string => {
  return netflixConfigNames[configName] || configName
}

// 加载可用的Netflix配置
const loadAvailableNetflixConfigs = async () => {
  try {
    loadingNetflixConfigs.value = true
    
    const response = await apiRequest('/api/v2/netflix/config/configs', {
      method: 'GET'
    })
    
    if (response.success && response.data) {
      availableNetflixConfigs.value = response.data
      
      // 如果当前没有选择配置，自动选择第一个
      if (!selectedNetflixConfig.value && response.data.length > 0) {
        selectedNetflixConfig.value = response.data[0]
        config.value.subtitle.netflix_config_name = response.data[0]
      }
      
      updateNetflixConfigStatus('success', '配置加载成功', `发现 ${response.data.length} 个可用配置`)
    }
    else {
      throw new Error(response.message || '配置加载失败')
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('加载Netflix配置失败:', error)
    updateNetflixConfigStatus('error', '配置加载失败', error instanceof Error ? error.message : '未知错误')
  }
  finally {
    loadingNetflixConfigs.value = false
  }
}

// 刷新Netflix配置列表
const refreshNetflixConfigs = async () => {
  updateNetflixConfigStatus('warning', '正在刷新...', '重新加载配置列表')
  await loadAvailableNetflixConfigs()
}

// Netflix配置变更处理
const onNetflixConfigChange = async () => {
  if (!selectedNetflixConfig.value) return
  
  try {
    updateNetflixConfigStatus('warning', '正在切换配置...', `切换到: ${getNetflixConfigDisplayName(selectedNetflixConfig.value)}`)
    
    // 保存到字幕配置中
    config.value.subtitle.netflix_config_name = selectedNetflixConfig.value
    
    // 验证配置
    const response = await apiRequest(`/api/v2/netflix/config/configs/${selectedNetflixConfig.value}/validate`, {
      method: 'POST'
    })
    
    if (response.success) {
      updateNetflixConfigStatus(
        'success', 
        '配置切换成功', 
        `当前使用: ${getNetflixConfigDisplayName(selectedNetflixConfig.value)}`
      )
    }
    else {
      updateNetflixConfigStatus(
        'warning',
        '配置验证警告',
        response.message || '配置可能存在问题',
        response.data?.warnings || []
      )
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('Netflix配置切换失败:', error)
    updateNetflixConfigStatus(
      'error',
      '配置切换失败',
      error instanceof Error ? error.message : '未知错误'
    )
  }
}

// 更新Netflix配置状态
const updateNetflixConfigStatus = (
  type: NetflixConfigStatus['type'], 
  title: string, 
  message: string, 
  details?: string[]
) => {
  netflixConfigStatus.value = { type, title, message, details }
  
  // 3秒后自动清除成功状态
  if (type === 'success') {
    setTimeout(() => {
      if (netflixConfigStatus.value?.type === 'success') {
        netflixConfigStatus.value = null
      }
    }, 3000)
  }
}

// 监听增强模式变化
watch(() => config.value.subtitle.use_enhanced_mode, (newValue) => {
  if (newValue && availableNetflixConfigs.value.length === 0) {
    loadAvailableNetflixConfigs()
  }
})

// 组件挂载时初始化
onMounted(() => {
  // 如果已经启用增强模式，立即加载配置
  if (config.value.subtitle.use_enhanced_mode) {
    loadAvailableNetflixConfigs()
  }
  
  // 如果已有Netflix配置名称，设置选中状态
  if (config.value.subtitle.netflix_config_name) {
    selectedNetflixConfig.value = config.value.subtitle.netflix_config_name
  }
})
</script>

<style lang="scss" scoped>
.config-section {
  margin-bottom: 40px;

  h2 {
    color: #2c3e50;
    font-size: 1.6em;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #ecf0f1;
  }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;

  label {
    margin-bottom: 8px;
    font-weight: 600;
    color: #34495e;
    font-size: 0.95em;
  }

  input, select {
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 1em;
    transition: all 0.3s ease;

    &:focus {
      outline: none;
      border-color: #5c7cfa;
      box-shadow: 0 0 0 3px rgba(92, 124, 250, 0.1);
    }
  }
}

.checkbox-item {
  grid-column: span 2;
  
  label {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    cursor: pointer;
    
    input[type="checkbox"] {
      margin-top: 2px;
    }
  }
}

.help-text {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  margin-left: 24px;
  line-height: 1.4;
  font-style: italic;
}

// 🎯 Netflix配置选择器样式
.netflix-config-selector {
  display: flex;
  gap: 8px;
  align-items: center;
  
  select {
    flex: 1;
  }
  
  .btn-refresh {
    padding: 8px;
    background: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    
    &:hover {
      background: #e9ecef;
      border-color: #5c7cfa;
    }
    
    svg {
      fill: #6c757d;
    }
  }
}

// Netflix状态显示样式
.netflix-status {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  margin-top: 8px;
  
  &.success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    
    .status-icon svg {
      fill: #28a745;
    }
  }
  
  &.warning {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    
    .status-icon svg {
      fill: #ffc107;
    }
  }
  
  &.error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    
    .status-icon svg {
      fill: #dc3545;
    }
  }
  
  .status-icon {
    flex-shrink: 0;
    margin-top: 2px;
  }
  
  .status-content {
    flex: 1;
    
    .status-title {
      font-weight: 600;
      margin-bottom: 4px;
      font-size: 14px;
    }
    
    .status-message {
      font-size: 13px;
      margin-bottom: 6px;
    }
    
    .status-details {
      font-size: 12px;
      opacity: 0.8;
      
      div {
        margin-bottom: 2px;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}

.enhanced-config {
  grid-column: span 2;
  border: 2px solid #e3f2fd;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
  background: linear-gradient(45deg, #f8f9ff, #fff);
  
  .enhanced-title {
    color: #1976d2;
    font-weight: 600;
    margin-bottom: 15px;
    font-size: 14px;
  }
  
  .form-item {
    margin-bottom: 15px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .checkbox-item {
    grid-column: span 1;
  }
  
  .enhanced-config {
    grid-column: span 1;
  }
}
</style>
