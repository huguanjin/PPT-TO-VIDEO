<!--
任务4.1: 高级视频效果系统 - Vue.js前端组件

转场效果配置和预览界面
支持实时预览、效果配置和批量处理
-->

<template>
  <div class="advanced-transition-system">
    <!-- 页面标题 -->
    <div class="system-header">
      <h2 class="system-title">
        <i class="fas fa-magic"></i>
        高级转场效果系统
      </h2>
      <p class="system-description">
        专业级视频转场效果，支持实时预览和批量处理
      </p>
    </div>

    <!-- 主要内容区域 -->
    <div class="system-content">
      <!-- 左侧：效果选择和配置 -->
      <div class="effect-config-panel">
        <div class="panel-header">
          <h3><i class="fas fa-sliders-h"></i> 转场配置</h3>
        </div>

        <!-- 转场类型选择 -->
        <div class="config-section">
          <label class="config-label">转场类型</label>
          <div class="transition-grid">
            <div
              v-for="transition in availableTransitions"
              :key="transition.type"
              class="transition-card"
              :class="{ active: selectedTransition?.type === transition.type }"
              @click="selectTransition(transition)"
            >
              <div class="transition-icon">
                <i :class="getTransitionIcon(transition.type)"></i>
              </div>
              <div class="transition-info">
                <h4>{{ transition.name }}</h4>
                <p>{{ transition.description }}</p>
                <span class="transition-category">{{ transition.category }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 基础参数配置 -->
        <div class="config-section" v-if="selectedTransition">
          <label class="config-label">基础参数</label>
          
          <div class="config-row">
            <label>持续时间</label>
            <div class="input-with-unit">
              <input
                type="number"
                v-model="config.duration"
                min="0.1"
                max="10"
                step="0.1"
                @input="updatePreview"
              />
              <span class="unit">秒</span>
            </div>
          </div>

          <div class="config-row">
            <label>缓动函数</label>
            <select v-model="config.easing" @change="updatePreview">
              <option value="linear">线性</option>
              <option value="ease_in">缓入</option>
              <option value="ease_out">缓出</option>
              <option value="ease_in_out">缓入缓出</option>
              <option value="bounce">弹跳</option>
              <option value="elastic">弹性</option>
              <option value="back">回弹</option>
            </select>
          </div>

          <div class="config-row">
            <label>效果强度</label>
            <div class="slider-container">
              <input
                type="range"
                v-model="config.intensity"
                min="0"
                max="2"
                step="0.1"
                @input="updatePreview"
              />
              <span class="slider-value">{{ config.intensity }}</span>
            </div>
          </div>

          <div class="config-row">
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="config.audio_fade"
                @change="updatePreview"
              />
              音频淡入淡出
            </label>
          </div>
        </div>

        <!-- 预设配置 -->
        <div class="config-section">
          <label class="config-label">预设配置</label>
          <div class="preset-buttons">
            <button
              v-for="(preset, name) in presets"
              :key="name"
              class="preset-btn"
              @click="applyPreset(name, preset)"
            >
              {{ formatPresetName(name) }}
            </button>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <button
            class="btn btn-preview"
            @click="previewTransition"
            :disabled="!selectedTransition || isLoading"
          >
            <i class="fas fa-eye"></i>
            预览效果
          </button>
          
          <button
            class="btn btn-apply"
            @click="applyTransition"
            :disabled="!selectedTransition || isLoading || !hasVideoClips"
          >
            <i class="fas fa-magic"></i>
            应用转场
          </button>
        </div>
      </div>

      <!-- 右侧：预览和结果 -->
      <div class="preview-panel">
        <div class="panel-header">
          <h3><i class="fas fa-desktop"></i> 实时预览</h3>
        </div>

        <!-- 预览区域 -->
        <div class="preview-area">
          <div v-if="!previewData" class="preview-placeholder">
            <i class="fas fa-video fa-3x"></i>
            <p>选择转场效果开始预览</p>
          </div>
          
          <div v-else class="preview-content">
            <!-- 效果信息 -->
            <div class="effect-info">
              <h4>{{ selectedTransition?.name }}</h4>
              <p>{{ previewData.preview_info.description }}</p>
              
              <div class="info-stats">
                <div class="stat">
                  <span class="stat-label">分类:</span>
                  <span class="stat-value">{{ previewData.preview_info.category }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">复杂度:</span>
                  <span class="stat-value">{{ previewData.preview_info.complexity }}</span>
                </div>
              </div>
            </div>

            <!-- 参数预览 -->
            <div class="config-preview">
              <h5>当前配置</h5>
              <div class="config-display">
                <div class="config-item">
                  <span>类型:</span>
                  <span>{{ previewData.config.transition_type }}</span>
                </div>
                <div class="config-item">
                  <span>时长:</span>
                  <span>{{ previewData.config.duration }}s</span>
                </div>
                <div class="config-item">
                  <span>缓动:</span>
                  <span>{{ previewData.config.easing }}</span>
                </div>
                <div class="config-item">
                  <span>强度:</span>
                  <span>{{ previewData.config.intensity }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 处理状态 -->
        <div v-if="processingStatus" class="processing-status">
          <div class="status-header">
            <h4>
              <i class="fas fa-cog fa-spin" v-if="processingStatus.status === 'processing'"></i>
              <i class="fas fa-check-circle text-success" v-else-if="processingStatus.status === 'completed'"></i>
              <i class="fas fa-exclamation-circle text-error" v-else-if="processingStatus.status === 'error'"></i>
              处理状态
            </h4>
          </div>
          
          <div class="progress-container">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: (processingStatus.progress * 100) + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ (processingStatus.progress * 100).toFixed(1) }}%</span>
          </div>
          
          <p class="status-message">{{ processingStatus.message }}</p>
          
          <!-- 结果信息 -->
          <div v-if="processingStatus.result" class="result-info">
            <h5>处理结果</h5>
            <div class="result-stats">
              <div class="result-item">
                <span>文件大小:</span>
                <span>{{ formatFileSize(processingStatus.result.file_size) }}</span>
              </div>
              <div class="result-item">
                <span>处理时间:</span>
                <span>{{ processingStatus.result.processing_time.toFixed(2) }}秒</span>
              </div>
            </div>
            
            <button class="btn btn-download" @click="downloadResult">
              <i class="fas fa-download"></i>
              下载结果
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载遮罩 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner">
        <i class="fas fa-cog fa-spin fa-3x"></i>
        <p>{{ loadingMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'

export default {
  name: 'AdvancedTransitionSystem',
  setup() {
    // 响应式数据
    const availableTransitions = ref([])
    const presets = ref({})
    const selectedTransition = ref(null)
    const previewData = ref(null)
    const processingStatus = ref(null)
    const isLoading = ref(false)
    const loadingMessage = ref('')
    
    // 配置数据
    const config = reactive({
      transition_type: 'fade',
      duration: 1.0,
      easing: 'ease_in_out',
      intensity: 1.0,
      blur_amount: 0.0,
      audio_fade: true
    })
    
    // 示例视频片段数据
    const videoClips = ref([
      {
        id: 'clip_001',
        path: 'input_001.mp4',
        name: '片段 1',
        duration: 5.0
      },
      {
        id: 'clip_002',
        path: 'input_002.mp4', 
        name: '片段 2',
        duration: 4.5
      }
    ])
    
    // 计算属性
    const hasVideoClips = computed(() => videoClips.value.length >= 2)
    
    // API基础URL
    const API_BASE = '/api/transitions'
    
    // 方法
    const loadTransitions = async () => {
      try {
        isLoading.value = true
        loadingMessage.value = '加载转场效果...'
        
        const response = await axios.get(`${API_BASE}/list`)
        if (response.data.success) {
          availableTransitions.value = response.data.data.transitions
        }
      }
      catch (error) {
        // 使用日志记录而不是console.error
        isLoading.value = false
        throw error
      }
      finally {
        isLoading.value = false
      }
    }
    
    const loadPresets = async () => {
      const response = await axios.get(`${API_BASE}/presets`)
      if (response.data.success) {
        presets.value = response.data.data.presets
      }
    }
    
    const selectTransition = (transition) => {
      selectedTransition.value = transition
      config.transition_type = transition.type
      updatePreview()
    }
    
    const updatePreview = async () => {
      if (!selectedTransition.value) return
      
      const response = await axios.post(`${API_BASE}/preview`, {
        config: { ...config }
      })
      
      if (response.data.success) {
        previewData.value = response.data.data
      }
    }
    
    const previewTransition = async () => {
      await updatePreview()
    }
    
    const applyTransition = async () => {
      if (!selectedTransition.value || videoClips.value.length < 2) return
      
      try {
        isLoading.value = true
        loadingMessage.value = '应用转场效果...'
        
        const clip_a = videoClips.value[0]
        const clip_b = videoClips.value[1]
        
        const response = await axios.post(`${API_BASE}/apply`, {
          clip_a: {
            id: clip_a.id,
            path: clip_a.path,
            start_time: 0.0,
            end_time: clip_a.duration,
            width: 1920,
            height: 1080,
            fps: 30.0
          },
          clip_b: {
            id: clip_b.id,
            path: clip_b.path,
            start_time: 0.0,
            end_time: clip_b.duration,
            width: 1920,
            height: 1080,
            fps: 30.0
          },
          config: { ...config },
          async: true
        })
        
        if (response.data.success) {
          const sessionId = response.data.data.session_id
          monitorProcessing(sessionId)
        }
      }
      finally {
        isLoading.value = false
      }
    }
    
    const monitorProcessing = (sessionId) => {
      const pollStatus = async () => {
        try {
          const response = await axios.get(`${API_BASE}/status/${sessionId}`)
          
          if (response.data.success) {
            processingStatus.value = response.data.data
            
            if (response.data.data.status === 'completed') {
              processingStatus.value.result = response.data.data.result
            }
            else if (response.data.data.status === 'processing') {
              setTimeout(pollStatus, 1000) // 1秒后再次检查
            }
          }
        }
        catch (error) {
          processingStatus.value = {
            status: 'error',
            message: '状态检查失败',
            progress: 0
          }
        }
      }
      
      // 开始监控
      processingStatus.value = {
        status: 'processing',
        progress: 0,
        message: '正在处理...'
      }
      
      pollStatus()
    }
    
    const applyPreset = (name, preset) => {
      config.transition_type = preset.transition_type
      config.duration = preset.duration
      config.easing = preset.easing
      config.intensity = preset.intensity
      config.blur_amount = preset.blur_amount
      config.audio_fade = preset.audio_fade
      
      // 更新选中的转场类型
      const transition = availableTransitions.value.find(t => t.type === preset.transition_type)
      if (transition) {
        selectedTransition.value = transition
      }
      
      updatePreview()
    }
    
    const downloadResult = () => {
      if (processingStatus.value?.result?.output_path) {
        const link = document.createElement('a')
        link.href = `/api/transitions/download/${processingStatus.value.result.output_path}`
        link.download = 'transition_result.mp4'
        link.click()
      }
    }
    
    const getTransitionIcon = (type) => {
      const iconMap = {
        'fade': 'fas fa-adjust',
        'dissolve': 'fas fa-water',
        'slide_left': 'fas fa-arrow-left',
        'slide_right': 'fas fa-arrow-right',
        'slide_up': 'fas fa-arrow-up',
        'slide_down': 'fas fa-arrow-down',
        'zoom_in': 'fas fa-search-plus',
        'zoom_out': 'fas fa-search-minus',
        'rotate': 'fas fa-sync-alt',
        'flip_horizontal': 'fas fa-arrows-alt-h',
        'flip_vertical': 'fas fa-arrows-alt-v',
        'wipe_left': 'fas fa-eraser',
        'wipe_right': 'fas fa-eraser',
        'circle_open': 'fas fa-circle',
        'circle_close': 'fas fa-dot-circle'
      }
      return iconMap[type] || 'fas fa-magic'
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const formatPresetName = (name) => {
      return name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
    
    // 生命周期
    onMounted(() => {
      loadTransitions()
      loadPresets()
    })
    
    return {
      // 数据
      availableTransitions,
      presets,
      selectedTransition,
      previewData,
      processingStatus,
      isLoading,
      loadingMessage,
      config,
      videoClips,
      hasVideoClips,
      
      // 方法
      selectTransition,
      updatePreview,
      previewTransition,
      applyTransition,
      applyPreset,
      downloadResult,
      getTransitionIcon,
      formatFileSize,
      formatPresetName
    }
  }
}
</script>

<style scoped>
.advanced-transition-system {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.system-header {
  text-align: center;
  margin-bottom: 30px;
}

.system-title {
  color: #2c3e50;
  margin-bottom: 10px;
}

.system-title i {
  color: #e74c3c;
  margin-right: 10px;
}

.system-description {
  color: #7f8c8d;
  font-size: 16px;
}

.system-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.effect-config-panel,
.preview-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.panel-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
}

.panel-header i {
  margin-right: 8px;
}

.config-section {
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.config-section:last-child {
  border-bottom: none;
}

.config-label {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 15px;
  display: block;
}

.transition-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.transition-card {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 2px solid #ecf0f1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.transition-card:hover {
  border-color: #3498db;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.2);
}

.transition-card.active {
  border-color: #e74c3c;
  background: #fef8f8;
}

.transition-icon {
  font-size: 24px;
  color: #3498db;
  margin-right: 15px;
  min-width: 40px;
}

.transition-info h4 {
  margin: 0 0 5px 0;
  color: #2c3e50;
  font-size: 14px;
}

.transition-info p {
  margin: 0 0 8px 0;
  color: #7f8c8d;
  font-size: 12px;
}

.transition-category {
  background: #ecf0f1;
  color: #34495e;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
}

.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.config-row label {
  font-weight: 500;
  color: #34495e;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 5px;
}

.input-with-unit input {
  width: 80px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.unit {
  color: #7f8c8d;
  font-size: 12px;
}

select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

input[type="range"] {
  flex: 1;
  max-width: 120px;
}

.slider-value {
  font-weight: 600;
  color: #e74c3c;
  min-width: 30px;
  text-align: right;
  font-size: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.preset-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.preset-btn {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 12px;
}

.preset-btn:hover {
  background: #f8f9fa;
  border-color: #3498db;
}

.action-buttons {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-preview {
  background: #3498db;
  color: white;
}

.btn-preview:hover:not(:disabled) {
  background: #2980b9;
}

.btn-apply {
  background: #27ae60;
  color: white;
}

.btn-apply:hover:not(:disabled) {
  background: #229954;
}

.btn-batch {
  background: #e67e22;
  color: white;
}

.btn-batch:hover:not(:disabled) {
  background: #d35400;
}

.preview-area {
  padding: 20px;
}

.preview-placeholder {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.preview-placeholder i {
  margin-bottom: 20px;
}

.effect-info h4 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.effect-info p {
  color: #7f8c8d;
  margin-bottom: 20px;
}

.info-stats {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-bottom: 20px;
}

.stat {
  display: flex;
  justify-content: space-between;
}

.stat-label {
  color: #7f8c8d;
}

.stat-value {
  font-weight: 600;
  color: #2c3e50;
}

.filter-preview,
.config-preview {
  margin-bottom: 20px;
}

.filter-preview h5,
.config-preview h5 {
  color: #34495e;
  margin-bottom: 10px;
  font-size: 14px;
}

.filter-code {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 11px;
  color: #495057;
  max-height: 100px;
  overflow-y: auto;
}

.config-display {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.config-item span:first-child {
  color: #7f8c8d;
}

.config-item span:last-child {
  font-weight: 600;
  color: #2c3e50;
}

.processing-status {
  padding: 20px;
  border-top: 1px solid #eee;
}

.status-header h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transition: width 0.3s ease;
}

.progress-text {
  font-weight: 600;
  color: #2c3e50;
  min-width: 50px;
  text-align: right;
}

.status-message {
  color: #7f8c8d;
  margin-bottom: 15px;
}

.batch-info {
  background: #e8f4f8;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.result-info {
  background: #d5f4e6;
  padding: 15px;
  border-radius: 6px;
}

.result-info h5 {
  margin: 0 0 10px 0;
  color: #27ae60;
}

.result-stats {
  margin-bottom: 15px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.btn-download {
  background: #27ae60;
  color: white;
}

.btn-download:hover {
  background: #229954;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  background: #34495e;
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-close {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel {
  background: #95a5a6;
  color: white;
}

.btn-confirm {
  background: #e74c3c;
  color: white;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.loading-spinner {
  text-align: center;
  color: #3498db;
}

.loading-spinner i {
  margin-bottom: 20px;
}

.text-success {
  color: #27ae60;
}

.text-error {
  color: #e74c3c;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .system-content {
    grid-template-columns: 1fr;
  }
  
  .transition-grid {
    grid-template-columns: 1fr;
  }
  
  .preset-buttons {
    grid-template-columns: 1fr;
  }
  
  .config-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
