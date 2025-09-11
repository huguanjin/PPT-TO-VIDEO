<template>
  <div class="tts-preview">
    <div class="preview-section">
      <h3>🎵 配音试听</h3>
      <div class="preview-card">
        <div class="preview-input">
          <textarea
            v-model="previewText"
            placeholder="输入要试听的文本内容，体验不同的语音效果..."
            rows="3"
            maxlength="200"
            class="preview-textarea"
          ></textarea>
          <div class="text-counter">
            <span>{{ previewText.length }}/200</span>
          </div>
        </div>
        
        <div class="preview-actions">
          <button
            @click="playTTSPreview"
            :disabled="isGeneratingPreview || !previewText.trim()"
            class="btn-preview"
          >
            <span class="btn-icon">{{ isGeneratingPreview ? '⏳' : '🎵' }}</span>
            <span>{{ isGeneratingPreview ? '生成中...' : '试听配音' }}</span>
          </button>
          <button
            v-if="currentAudio"
            @click="stopCurrentAudio"
            class="btn-stop"
          >
            <span class="btn-icon">⏹</span>
            <span>停止播放</span>
          </button>
        </div>
        
        <div v-if="previewStatus" class="preview-status">
          <div :class="['status-message', previewStatus.type]">
            <span class="status-icon">
              {{ previewStatus.type === 'success' ? '✅' : previewStatus.type === 'error' ? '❌' : 'ℹ️' }}
            </span>
            {{ previewStatus.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface TTSConfig {
  preferred_engine: string
  edge_voice: string
  edge_rate: string
  edge_pitch: string
  fish_api_key: string
  fish_character: string
  sample_rate: number
  max_retries: number
  timeout: number
}

interface Props {
  config: TTSConfig
}

interface PreviewStatus {
  type: 'success' | 'error' | 'info'
  message: string
}

const props = defineProps<Props>()

const previewText = ref('欢迎使用PPT转视频工具，这是一个语音试听示例。')
const isGeneratingPreview = ref(false)
const currentAudio = ref<HTMLAudioElement | null>(null)
const previewStatus = ref<PreviewStatus | null>(null)

const playTTSPreview = async () => {
  if (!previewText.value.trim()) {
    return
  }
  
  isGeneratingPreview.value = true
  previewStatus.value = { type: 'info', message: '正在生成语音...' }
  
  try {
    // 构建API请求
    const requestData = {
      text: previewText.value.trim(),
      engine: props.config.preferred_engine,
      voice_config: {
        edge_voice: props.config.edge_voice,
        edge_rate: props.config.edge_rate,
        edge_pitch: props.config.edge_pitch,
        fish_api_key: props.config.fish_api_key,
        fish_character: props.config.fish_character
      }
    }
    
    const response = await fetch('/api/tts/preview', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const audioBlob = await response.blob()
    const audioUrl = URL.createObjectURL(audioBlob)
    
    // 停止之前的音频
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
    }
    
    // 播放新音频
    const audio = new Audio(audioUrl)
    currentAudio.value = audio
    
    audio.onended = () => {
      currentAudio.value = null
      URL.revokeObjectURL(audioUrl)
      previewStatus.value = { type: 'success', message: '播放完成' }
    }
    
    audio.onerror = () => {
      currentAudio.value = null
      URL.revokeObjectURL(audioUrl)
      previewStatus.value = { type: 'error', message: '音频播放失败' }
    }
    
    await audio.play()
    previewStatus.value = { type: 'success', message: '正在播放...' }
    
  } 
  catch (error) {
    // TTS预览失败
    previewStatus.value = { 
      type: 'error', 
      message: `生成失败: ${error instanceof Error ? error.message : '未知错误'}` 
    }
  } 
  finally {
    isGeneratingPreview.value = false
  }
}

const stopCurrentAudio = () => {
  if (currentAudio.value) {
    currentAudio.value.pause()
    currentAudio.value = null
    previewStatus.value = { type: 'info', message: '播放已停止' }
  }
}
</script>

<style lang="scss" scoped>
.tts-preview {
  margin-top: 30px;
}

.preview-section {
  h3 {
    color: #2c3e50;
    font-size: 1.4em;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.preview-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.preview-input {
  position: relative;
  margin-bottom: 20px;
}

.preview-textarea {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-family: inherit;
  background: rgba(255, 255, 255, 0.9);
  color: #2c3e50;
  resize: vertical;
  min-height: 80px;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    background: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }
  
  &::placeholder {
    color: #7f8c8d;
  }
}

.text-counter {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 12px;
  color: #666;
  background: white;
  padding: 2px 6px;
  border-radius: 4px;
}

.preview-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.btn-preview, .btn-stop {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-preview {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
  }
}

.btn-stop {
  background: linear-gradient(45deg, #f44336, #d32f2f);
  color: white;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(244, 67, 54, 0.4);
  }
}

.btn-icon {
  font-size: 16px;
}

.preview-status {
  margin-top: 16px;
}

.status-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 500;
  
  &.success {
    background: rgba(76, 175, 80, 0.2);
    border: 1px solid rgba(76, 175, 80, 0.5);
  }
  
  &.error {
    background: rgba(244, 67, 54, 0.2);
    border: 1px solid rgba(244, 67, 54, 0.5);
  }
  
  &.info {
    background: rgba(33, 150, 243, 0.2);
    border: 1px solid rgba(33, 150, 243, 0.5);
  }
}

.status-icon {
  font-size: 16px;
}
</style>
