<template>
  <div class="section">
    <div class="section-header">
      <h3>音频分析</h3>
      <p>智能分析音频特征，包括情感识别、语调分析等</p>
    </div>

    <div v-if="!hasUploadedFile" class="no-file-message">
      <i class="info-icon">ℹ️</i>
      <p>请先上传音频文件</p>
    </div>

    <div v-else class="analysis-container">
      <!-- 分析按钮 -->
      <div class="analysis-actions">
        <button 
          class="btn-primary" 
          @click="startAnalysis" 
          :disabled="analyzing"
        >
          <i>🔍</i>
          {{ analyzing ? '分析中...' : '开始分析' }}
        </button>
        
        <button 
          v-if="analysisResult" 
          class="btn-secondary" 
          @click="exportAnalysis"
        >
          <i>📋</i>
          导出分析报告
        </button>
      </div>

      <!-- 分析进度 -->
      <div v-if="analyzing" class="analysis-progress">
        <div class="progress-header">
          <span>分析进度</span>
          <span>{{ analysisProgress }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: analysisProgress + '%' }"></div>
        </div>
        <div class="progress-step">{{ currentAnalysisStep }}</div>
      </div>

      <!-- 分析结果 -->
      <div v-if="analysisResult" class="analysis-results">
        <h4>分析结果</h4>
        
        <!-- 基础音频信息 -->
        <div class="result-section">
          <h5>基础信息</h5>
          <div class="info-grid">
            <div class="info-item">
              <label>时长</label>
              <span>{{ formatDuration(analysisResult.duration) }}</span>
            </div>
            <div class="info-item">
              <label>采样率</label>
              <span>{{ analysisResult.sample_rate }} Hz</span>
            </div>
            <div class="info-item">
              <label>声道数</label>
              <span>{{ analysisResult.channels }}</span>
            </div>
            <div class="info-item">
              <label>比特率</label>
              <span>{{ analysisResult.bitrate }} kbps</span>
            </div>
          </div>
        </div>

        <!-- 音频特征 -->
        <div class="result-section">
          <h5>音频特征</h5>
          <div class="feature-grid">
            <div class="feature-card">
              <h6>音量分析</h6>
              <div class="feature-content">
                <div class="metric">
                  <span class="label">RMS能量</span>
                  <span class="value">{{ analysisResult.rms_energy.toFixed(3) }}</span>
                </div>
                <div class="metric">
                  <span class="label">峰值音量</span>
                  <span class="value">{{ analysisResult.peak_volume.toFixed(1) }} dB</span>
                </div>
                <div class="volume-bar">
                  <div 
                    class="volume-fill" 
                    :style="{ width: (analysisResult.rms_energy * 100) + '%' }"
                  ></div>
                </div>
              </div>
            </div>

            <div class="feature-card">
              <h6>频谱分析</h6>
              <div class="feature-content">
                <div class="metric">
                  <span class="label">主导频率</span>
                  <span class="value">{{ analysisResult.dominant_frequency.toFixed(1) }} Hz</span>
                </div>
                <div class="metric">
                  <span class="label">频谱重心</span>
                  <span class="value">{{ analysisResult.spectral_centroid.toFixed(1) }} Hz</span>
                </div>
              </div>
            </div>

            <div class="feature-card">
              <h6>质量评估</h6>
              <div class="feature-content">
                <div class="metric">
                  <span class="label">音质评分</span>
                  <span class="value score" :class="getQualityClass(analysisResult.quality_score)">
                    {{ analysisResult.quality_score.toFixed(1) }}/10
                  </span>
                </div>
                <div class="metric">
                  <span class="label">噪音级别</span>
                  <span class="value">{{ analysisResult.noise_level }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 情感分析 -->
        <div class="result-section">
          <h5>情感识别</h5>
          <div class="emotion-analysis">
            <div class="emotion-chart">
              <div 
                v-for="emotion in analysisResult.emotions" 
                :key="emotion.type"
                class="emotion-bar"
              >
                <span class="emotion-label">{{ emotion.label }}</span>
                <div class="emotion-progress">
                  <div 
                    class="emotion-fill" 
                    :style="{ 
                      width: (emotion.confidence * 100) + '%',
                      backgroundColor: getEmotionColor(emotion.type)
                    }"
                  ></div>
                </div>
                <span class="emotion-value">{{ (emotion.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div class="emotion-summary">
              <strong>主要情感：</strong>
              {{ analysisResult.dominant_emotion.label }} 
              ({{ (analysisResult.dominant_emotion.confidence * 100).toFixed(1) }}%)
            </div>
          </div>
        </div>

        <!-- 语音特征 -->
        <div v-if="analysisResult.speech_features" class="result-section">
          <h5>语音特征</h5>
          <div class="speech-features">
            <div class="feature-metric">
              <label>语速</label>
              <span>{{ analysisResult.speech_features.speech_rate.toFixed(1) }} 字/分钟</span>
            </div>
            <div class="feature-metric">
              <label>停顿频率</label>
              <span>{{ analysisResult.speech_features.pause_frequency.toFixed(1) }} 次/分钟</span>
            </div>
            <div class="feature-metric">
              <label>平均停顿时长</label>
              <span>{{ analysisResult.speech_features.avg_pause_duration.toFixed(2) }} 秒</span>
            </div>
          </div>
        </div>

        <!-- 频谱图 -->
        <div class="result-section">
          <h5>频谱可视化</h5>
          <div class="spectrum-display">
            <canvas ref="spectrumCanvas" class="spectrum-canvas"></canvas>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="analysisError" class="error-message">
        分析失败: {{ analysisError }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick } from 'vue'

export default {
  name: 'AudioAnalysis',
  props: {
    uploadedFile: {
      type: Object,
      default: null
    }
  },
  emits: ['analysis-complete'],
  setup(props, { emit }) {
    const analyzing = ref(false)
    const analysisProgress = ref(0)
    const currentAnalysisStep = ref('')
    const analysisResult = ref(null)
    const analysisError = ref('')
    const spectrumCanvas = ref(null)

    const hasUploadedFile = computed(() => {
      return props.uploadedFile !== null
    })

    const startAnalysis = async () => {
      if (!props.uploadedFile) return

      analyzing.value = true
      analysisError.value = ''
      analysisProgress.value = 0
      currentAnalysisStep.value = '准备分析...'

      try {
        const formData = new FormData()
        formData.append('audio_file', props.uploadedFile)

        const response = await fetch('/api/audio/analyze', {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        // 模拟分析进度
        const steps = [
          '加载音频文件...',
          '提取音频特征...',
          '分析音频质量...',
          '识别情感特征...',
          '生成频谱图...',
          '完成分析'
        ]

        for (let i = 0; i < steps.length; i++) {
          currentAnalysisStep.value = steps[i]
          analysisProgress.value = ((i + 1) / steps.length) * 100
          await new Promise(resolve => setTimeout(resolve, 500))
        }

        const result = await response.json()
        analysisResult.value = result
        
        // 绘制频谱图
        await nextTick()
        drawSpectrum(result.spectrum_data)
        
        emit('analysis-complete', result)
      }
      catch (error) {
        analysisError.value = error.message
      }
      finally {
        analyzing.value = false
      }
    }

    const exportAnalysis = () => {
      if (!analysisResult.value) return

      const data = {
        file_name: props.uploadedFile.name,
        analysis_time: new Date().toISOString(),
        results: analysisResult.value
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json'
      })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audio_analysis_${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }

    const formatDuration = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const getQualityClass = (score) => {
      if (score >= 8) return 'excellent'
      if (score >= 6) return 'good'
      if (score >= 4) return 'fair'
      return 'poor'
    }

    const getEmotionColor = (emotionType) => {
      const colors = {
        neutral: '#95a5a6',
        happy: '#f39c12',
        sad: '#3498db',
        angry: '#e74c3c',
        excited: '#e67e22',
        calm: '#27ae60',
        serious: '#8e44ad'
      }
      return colors[emotionType] || '#95a5a6'
    }

    const drawSpectrum = (spectrumData) => {
      if (!spectrumCanvas.value || !spectrumData) return

      const canvas = spectrumCanvas.value
      const ctx = canvas.getContext('2d')
      
      // 设置canvas尺寸
      canvas.width = 800
      canvas.height = 200

      // 清空画布
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // 绘制频谱
      const barWidth = canvas.width / spectrumData.length
      const maxValue = Math.max(...spectrumData)

      for (let i = 0; i < spectrumData.length; i++) {
        const barHeight = (spectrumData[i] / maxValue) * canvas.height
        const hue = (i / spectrumData.length) * 240 // 从红到蓝
        
        ctx.fillStyle = `hsl(${hue}, 80%, 60%)`
        ctx.fillRect(i * barWidth, canvas.height - barHeight, barWidth - 1, barHeight)
      }
    }

    return {
      analyzing,
      analysisProgress,
      currentAnalysisStep,
      analysisResult,
      analysisError,
      spectrumCanvas,
      hasUploadedFile,
      startAnalysis,
      exportAnalysis,
      formatDuration,
      getQualityClass,
      getEmotionColor
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

.analysis-actions {
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
  background: #ecf0f1;
  color: #7f8c8d;
}

.btn-secondary:hover {
  background: #d5dbdb;
}

.analysis-progress {
  margin-bottom: 2rem;
  padding: 1rem;
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
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s ease;
}

.progress-step {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.analysis-results {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 12px;
}

.analysis-results h4 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  font-size: 1.3rem;
}

.result-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #ecf0f1;
}

.result-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.result-section h5 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
}

.info-item label {
  color: #7f8c8d;
  font-weight: 500;
}

.info-item span {
  color: #2c3e50;
  font-weight: 600;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.feature-card {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
}

.feature-card h6 {
  color: #34495e;
  margin-bottom: 0.75rem;
  font-size: 1rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.metric .label {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.metric .value {
  color: #2c3e50;
  font-weight: 600;
}

.value.score.excellent {
  color: #27ae60;
}

.value.score.good {
  color: #f39c12;
}

.value.score.fair {
  color: #e67e22;
}

.value.score.poor {
  color: #e74c3c;
}

.volume-bar {
  height: 6px;
  background: #ecf0f1;
  border-radius: 3px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.volume-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s ease;
}

.emotion-analysis {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
}

.emotion-bar {
  display: grid;
  grid-template-columns: 80px 1fr 60px;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.emotion-label {
  font-size: 0.9rem;
  color: #34495e;
}

.emotion-progress {
  height: 20px;
  background: #ecf0f1;
  border-radius: 10px;
  overflow: hidden;
}

.emotion-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 10px;
}

.emotion-value {
  font-size: 0.85rem;
  color: #7f8c8d;
  text-align: right;
}

.emotion-summary {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #ecf0f1;
  color: #2c3e50;
}

.speech-features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.feature-metric {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
}

.feature-metric label {
  color: #7f8c8d;
  font-weight: 500;
}

.feature-metric span {
  color: #2c3e50;
  font-weight: 600;
}

.spectrum-display {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #ecf0f1;
  text-align: center;
}

.spectrum-canvas {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
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
