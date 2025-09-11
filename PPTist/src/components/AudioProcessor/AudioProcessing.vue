<template>
  <div class="section">
    <div class="section-header">
      <h3>音频处理</h3>
      <p>应用各种音频处理算法提升音质</p>
    </div>

    <div v-if="!hasUploadedFile" class="no-file-message">
      <i class="info-icon">ℹ️</i>
      <p>请先上传音频文件</p>
    </div>

    <div v-else class="processing-container">
      <!-- 处理选项 -->
      <div class="processing-options">
        <h4>选择处理功能</h4>
        
        <div class="option-groups">
          <!-- 基础处理 -->
          <div class="option-group">
            <h5>基础处理</h5>
            <div class="options-grid">
              <label class="option-card">
                <input type="checkbox" v-model="selectedOptions.noiseReduction">
                <div class="option-content">
                  <i class="option-icon">🔇</i>
                  <span class="option-name">噪音消除</span>
                  <p class="option-desc">消除背景噪音和杂音</p>
                </div>
              </label>
              
              <label class="option-card">
                <input type="checkbox" v-model="selectedOptions.normalize">
                <div class="option-content">
                  <i class="option-icon">📊</i>
                  <span class="option-name">音量归一化</span>
                  <p class="option-desc">统一音量级别</p>
                </div>
              </label>
              
              <label class="option-card">
                <input type="checkbox" v-model="selectedOptions.enhance">
                <div class="option-content">
                  <i class="option-icon">✨</i>
                  <span class="option-name">音质增强</span>
                  <p class="option-desc">提升整体音质</p>
                </div>
              </label>
            </div>
          </div>

          <!-- 高级效果 -->
          <div class="option-group">
            <h5>高级效果</h5>
            <div class="options-grid">
              <label class="option-card">
                <input type="checkbox" v-model="selectedOptions.spatialEffects">
                <div class="option-content">
                  <i class="option-icon">🎧</i>
                  <span class="option-name">空间音效</span>
                  <p class="option-desc">增强立体声效果</p>
                </div>
              </label>
              
              <label class="option-card">
                <input type="checkbox" v-model="selectedOptions.backgroundMusic">
                <div class="option-content">
                  <i class="option-icon">🎵</i>
                  <span class="option-name">背景音乐</span>
                  <p class="option-desc">添加背景音乐</p>
                </div>
              </label>
              
              <label class="option-card">
                <input type="checkbox" v-model="selectedOptions.voiceOptimization">
                <div class="option-content">
                  <i class="option-icon">🎤</i>
                  <span class="option-name">语音优化</span>
                  <p class="option-desc">优化人声表现</p>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- 处理参数 -->
      <div v-if="hasSelectedOptions" class="processing-parameters">
        <h4>处理参数</h4>
        
        <div class="parameter-groups">
          <!-- 噪音消除参数 -->
          <div v-if="selectedOptions.noiseReduction" class="parameter-group">
            <h6>噪音消除设置</h6>
            <div class="parameter-controls">
              <div class="control-group">
                <label>噪音类型</label>
                <select v-model="parameters.noiseType">
                  <option value="background">背景噪音</option>
                  <option value="click">点击声</option>
                  <option value="hum">嗡嗡声</option>
                  <option value="wind">风噪</option>
                  <option value="electronic">电子噪音</option>
                </select>
              </div>
              <div class="control-group">
                <label>强度 ({{ parameters.noiseIntensity }}%)</label>
                <input 
                  type="range" 
                  v-model="parameters.noiseIntensity" 
                  min="10" 
                  max="100" 
                  step="10"
                >
              </div>
            </div>
          </div>

          <!-- 音量归一化参数 -->
          <div v-if="selectedOptions.normalize" class="parameter-group">
            <h6>音量归一化设置</h6>
            <div class="parameter-controls">
              <div class="control-group">
                <label>目标音量 ({{ parameters.targetVolume }} dB)</label>
                <input 
                  type="range" 
                  v-model="parameters.targetVolume" 
                  min="-30" 
                  max="0" 
                  step="3"
                >
              </div>
            </div>
          </div>

          <!-- 空间音效参数 -->
          <div v-if="selectedOptions.spatialEffects" class="parameter-group">
            <h6>空间音效设置</h6>
            <div class="parameter-controls">
              <div class="control-group">
                <label>效果类型</label>
                <select v-model="parameters.spatialType">
                  <option value="stereo_wide">立体声拓宽</option>
                  <option value="surround">环绕声</option>
                  <option value="hall_reverb">音厅混响</option>
                  <option value="room_reverb">房间混响</option>
                </select>
              </div>
              <div class="control-group">
                <label>强度 ({{ parameters.spatialIntensity }}%)</label>
                <input 
                  type="range" 
                  v-model="parameters.spatialIntensity" 
                  min="10" 
                  max="100" 
                  step="10"
                >
              </div>
            </div>
          </div>

          <!-- 背景音乐参数 -->
          <div v-if="selectedOptions.backgroundMusic" class="parameter-group">
            <h6>背景音乐设置</h6>
            <div class="parameter-controls">
              <div class="control-group">
                <label>音乐类型</label>
                <select v-model="parameters.musicType">
                  <option value="ambient">环境音乐</option>
                  <option value="corporate">商务音乐</option>
                  <option value="classical">古典音乐</option>
                  <option value="electronic">电子音乐</option>
                  <option value="nature">自然音效</option>
                </select>
              </div>
              <div class="control-group">
                <label>音量比例 ({{ parameters.musicVolume }}%)</label>
                <input 
                  type="range" 
                  v-model="parameters.musicVolume" 
                  min="5" 
                  max="50" 
                  step="5"
                >
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输出设置 -->
      <div class="output-settings">
        <h4>输出设置</h4>
        <div class="settings-grid">
          <div class="setting-group">
            <label>输出格式</label>
            <select v-model="outputFormat">
              <option value="wav">WAV (无损)</option>
              <option value="mp3">MP3 (压缩)</option>
              <option value="flac">FLAC (无损压缩)</option>
              <option value="aac">AAC (高质量压缩)</option>
            </select>
          </div>
          <div class="setting-group">
            <label>音质等级</label>
            <select v-model="qualityLevel">
              <option value="high">高品质</option>
              <option value="ultra">超高品质</option>
              <option value="lossless">无损品质</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 处理按钮 -->
      <div class="processing-actions">
        <button 
          class="btn-primary" 
          @click="startProcessing" 
          :disabled="!hasSelectedOptions || processing"
        >
          <i>⚡</i>
          {{ processing ? '处理中...' : '开始处理' }}
        </button>
        
        <button 
          v-if="processResult" 
          class="btn-secondary" 
          @click="downloadResult"
        >
          <i>⬇️</i>
          下载结果
        </button>
      </div>

      <!-- 处理进度 -->
      <div v-if="processing" class="processing-progress">
        <div class="progress-header">
          <span>处理进度</span>
          <span>{{ processingProgress }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: processingProgress + '%' }"></div>
        </div>
        <div class="progress-step">{{ currentProcessingStep }}</div>
        <div class="progress-details">
          <span>已用时间: {{ formatTime(elapsedTime) }}</span>
          <span v-if="estimatedTime">预计剩余: {{ formatTime(estimatedTime - elapsedTime) }}</span>
        </div>
      </div>

      <!-- 处理结果 -->
      <div v-if="processResult" class="processing-result">
        <h4>处理完成</h4>
        <div class="result-summary">
          <div class="result-info">
            <span class="label">处理时间</span>
            <span class="value">{{ formatTime(processResult.processing_time) }}</span>
          </div>
          <div class="result-info">
            <span class="label">文件大小</span>
            <span class="value">{{ formatFileSize(processResult.file_size) }}</span>
          </div>
          <div class="result-info">
            <span class="label">处理效果</span>
            <span class="value">{{ processResult.improvements.join(', ') }}</span>
          </div>
        </div>
        
        <!-- 音频播放器 -->
        <div class="audio-player">
          <h5>处理结果预览</h5>
          <audio controls class="audio-control">
            <source :src="processResult.audio_url" type="audio/mpeg">
            您的浏览器不支持音频播放
          </audio>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="processingError" class="error-message">
        处理失败: {{ processingError }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'AudioProcessing',
  props: {
    uploadedFile: {
      type: Object,
      default: null
    }
  },
  emits: ['processing-complete'],
  setup(props, { emit }) {
    const selectedOptions = ref({
      noiseReduction: false,
      normalize: false,
      enhance: false,
      spatialEffects: false,
      backgroundMusic: false,
      voiceOptimization: false
    })

    const parameters = ref({
      noiseType: 'background',
      noiseIntensity: 50,
      targetVolume: -18,
      spatialType: 'stereo_wide',
      spatialIntensity: 30,
      musicType: 'ambient',
      musicVolume: 20
    })

    const outputFormat = ref('mp3')
    const qualityLevel = ref('high')
    const processing = ref(false)
    const processingProgress = ref(0)
    const currentProcessingStep = ref('')
    const elapsedTime = ref(0)
    const estimatedTime = ref(0)
    const processResult = ref(null)
    const processingError = ref('')

    let progressTimer = null

    const hasUploadedFile = computed(() => {
      return props.uploadedFile !== null
    })

    const hasSelectedOptions = computed(() => {
      return Object.values(selectedOptions.value).some(selected => selected)
    })

    const startProcessing = async () => {
      if (!props.uploadedFile || !hasSelectedOptions.value) return

      processing.value = true
      processingError.value = ''
      processingProgress.value = 0
      elapsedTime.value = 0
      estimatedTime.value = 60 // 预估60秒

      // 启动进度计时器
      progressTimer = setInterval(() => {
        elapsedTime.value += 1
      }, 1000)

      try {
        const formData = new FormData()
        formData.append('audio_file', props.uploadedFile)
        formData.append('options', JSON.stringify(selectedOptions.value))
        formData.append('parameters', JSON.stringify(parameters.value))
        formData.append('output_format', outputFormat.value)
        formData.append('quality_level', qualityLevel.value)

        // 模拟处理步骤
        const steps = getProcessingSteps()
        
        for (let i = 0; i < steps.length; i++) {
          currentProcessingStep.value = steps[i]
          processingProgress.value = ((i + 1) / steps.length) * 100
          
          // 模拟处理时间
          await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 1000))
        }

        // 发送处理请求
        const response = await fetch('/api/audio/process', {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const result = await response.json()
        processResult.value = result
        
        emit('processing-complete', result)

      }
      catch (error) {
        processingError.value = error.message
      }
      finally {
        processing.value = false
        if (progressTimer) {
          clearInterval(progressTimer)
          progressTimer = null
        }
      }
    }

    const getProcessingSteps = () => {
      const steps = ['加载音频文件...']
      
      if (selectedOptions.value.noiseReduction) {
        steps.push('执行噪音消除...')
      }
      if (selectedOptions.value.normalize) {
        steps.push('音量归一化处理...')
      }
      if (selectedOptions.value.enhance) {
        steps.push('音质增强处理...')
      }
      if (selectedOptions.value.spatialEffects) {
        steps.push('应用空间音效...')
      }
      if (selectedOptions.value.backgroundMusic) {
        steps.push('混合背景音乐...')
      }
      if (selectedOptions.value.voiceOptimization) {
        steps.push('优化语音质量...')
      }
      
      steps.push('编码输出文件...')
      steps.push('处理完成')
      
      return steps
    }

    const downloadResult = () => {
      if (!processResult.value) return

      const link = document.createElement('a')
      link.href = processResult.value.download_url
      link.download = `processed_${props.uploadedFile.name}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    onMounted(() => {
      // 组件挂载时的初始化操作
    })

    return {
      selectedOptions,
      parameters,
      outputFormat,
      qualityLevel,
      processing,
      processingProgress,
      currentProcessingStep,
      elapsedTime,
      estimatedTime,
      processResult,
      processingError,
      hasUploadedFile,
      hasSelectedOptions,
      startProcessing,
      downloadResult,
      formatTime,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.section {
  margin-bottom: 2rem;
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-header h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.section-header p {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.no-file-message {
  text-align: center;
  padding: 2rem;
  color: #7f8c8d;
  background: #f8f9fa;
  border-radius: 8px;
}

.info-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  display: block;
}

.processing-options {
  margin-bottom: 2rem;
}

.processing-options h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.option-groups {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.option-group h5 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.option-card {
  display: block;
  position: relative;
  cursor: pointer;
  background: white;
  border: 2px solid #ecf0f1;
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.3s ease;
}

.option-card:hover {
  border-color: #3498db;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.1);
}

.option-card input[type="checkbox"] {
  position: absolute;
  top: 12px;
  right: 12px;
  cursor: pointer;
}

.option-card input[type="checkbox"]:checked + .option-content {
  color: #3498db;
}

.option-card input[type="checkbox"]:checked ~ * {
  border-color: #3498db;
}

.option-content {
  padding-right: 2rem;
}

.option-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  display: block;
}

.option-name {
  font-weight: 600;
  color: #2c3e50;
  display: block;
  margin-bottom: 0.25rem;
}

.option-desc {
  color: #7f8c8d;
  font-size: 0.85rem;
  margin: 0;
  line-height: 1.4;
}

.processing-parameters {
  margin-bottom: 2rem;
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 12px;
}

.processing-parameters h4 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  font-size: 1.2rem;
}

.parameter-groups {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.parameter-group {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
}

.parameter-group h6 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.parameter-controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  color: #7f8c8d;
  font-weight: 500;
  font-size: 0.9rem;
}

.control-group select,
.control-group input[type="range"] {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
}

.control-group select {
  background: white;
  color: #2c3e50;
}

.control-group input[type="range"] {
  appearance: none;
  -webkit-appearance: none;
  height: 6px;
  background: #ecf0f1;
  border-radius: 3px;
  outline: none;
}

.control-group input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: #3498db;
  border-radius: 50%;
  cursor: pointer;
}

.output-settings {
  margin-bottom: 2rem;
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 12px;
}

.output-settings h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-group label {
  color: #7f8c8d;
  font-weight: 500;
  font-size: 0.9rem;
}

.setting-group select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  color: #2c3e50;
  font-size: 0.9rem;
}

.processing-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.btn-secondary {
  background: #27ae60;
  color: white;
}

.btn-secondary:hover {
  background: #229954;
}

.processing-progress {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #2c3e50;
}

.progress-bar {
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s ease;
}

.progress-step {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-bottom: 0.5rem;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #95a5a6;
}

.processing-result {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.processing-result h4 {
  color: #27ae60;
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.result-info {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
}

.result-info .label {
  color: #7f8c8d;
  font-weight: 500;
}

.result-info .value {
  color: #2c3e50;
  font-weight: 600;
}

.audio-player {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
}

.audio-player h5 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.audio-control {
  width: 100%;
  height: 40px;
}

.error-message {
  color: #e74c3c;
  background: #fdf2f2;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #f5c6cb;
  margin-top: 1rem;
}
</style>
