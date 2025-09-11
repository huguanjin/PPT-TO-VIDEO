<template>
  <div class="settings-section">
    <div class="section-header">
      <h3>
        <VolumeNotice class="section-icon" />
        语音合成设置
      </h3>
      <p class="section-desc">选择语音角色和调整音频参数</p>
    </div>
    
    <div class="settings-grid">
      <div class="setting-card">
        <label class="setting-label">语音服务</label>
        <select class="setting-select" v-model="service">
          <option value="edge">Edge TTS (免费)</option>
          <option value="fish">Fish TTS (AI克隆)</option>
          <option value="azure">Azure TTS (高质量)</option>
        </select>
      </div>
      
      <div class="setting-card">
        <label class="setting-label">语音角色</label>
        <select class="setting-select" v-model="voice" :disabled="isLoadingVoices">
          <option v-if="isLoadingVoices" disabled>加载中...</option>
          <option 
            v-for="voiceOption in voiceOptions" 
            :key="voiceOption.id" 
            :value="voiceOption.id"
          >
            {{ voiceOption.name }}
          </option>
          <option v-if="!isLoadingVoices && voiceOptions.length === 0" disabled>
            暂无可用角色
          </option>
        </select>
      </div>
      
      <div class="setting-card">
        <label class="setting-label">语速</label>
        <input 
          type="range" 
          min="0.5" 
          max="2" 
          step="0.1"
          v-model="speed"
          class="setting-slider"
        />
        <span class="slider-value">{{ config.speed }}x</span>
      </div>

      <!-- 试听功能 -->
      <div class="setting-card full-width">
        <label class="setting-label">🎵 试听配音</label>
        <div class="preview-wrapper">
          <input 
            type="text" 
            v-model="previewText" 
            placeholder="输入试听文本（最多200字）"
            class="preview-input"
            maxlength="200"
          />
          <button 
            @click="playPreview" 
            :disabled="!canPreview || isPreviewPlaying"
            class="preview-btn"
          >
            <span v-if="!isPreviewPlaying">🎵 试听</span>
            <span v-else>⏸️ 播放中...</span>
          </button>
        </div>
        <div class="setting-help">
          💡 点击试听按钮可以预览当前配置的声音效果
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { VolumeNotice } from '@icon-park/vue-next'
import { ttsService } from '@/api/services'
import type { TTSEngine } from '@/api/types/tts'

interface TTSConfig {
  service: string
  voice: string
  speed: number
}

interface Props {
  config: TTSConfig
}

interface Emits {
  (e: 'update:config', config: TTSConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 语音角色选项
const voiceOptions = ref<{id: string, name: string}[]>([])
const isLoadingVoices = ref(false)

// 试听相关
const previewText = ref('你好，这是语音合成试听。')
const isPreviewPlaying = ref(false)
const currentAudio = ref<HTMLAudioElement | null>(null)

// 默认语音角色映射
const defaultVoiceMap = {
  edge: 'zh-CN-XiaoxiaoNeural',
  fish: 'default',
  azure: 'zh-CN-XiaoxiaoNeural'
}

// 计算属性
const service = computed({
  get: () => props.config.service,
  set: (value) => emit('update:config', { ...props.config, service: value })
})

const voice = computed({
  get: () => props.config.voice,
  set: (value) => emit('update:config', { ...props.config, voice: value })
})

const speed = computed({
  get: () => props.config.speed,
  set: (value) => emit('update:config', { ...props.config, speed: Number(value) })
})

const canPreview = computed(() => {
  return previewText.value.trim().length > 0 && 
         props.config.voice.trim().length > 0
})

// 加载语音角色列表
const loadVoiceOptions = async (serviceType: string) => {
  isLoadingVoices.value = true
  try {
    // 使用TTS服务获取语音列表
    const voices = await ttsService.getVoices(serviceType as TTSEngine)
    
    voiceOptions.value = voices.map(voice => ({
      id: voice.id,
      name: voice.name
    }))
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error(`加载${serviceType}语音角色失败:`, error)
    setDefaultVoiceOptions(serviceType)
  }
  finally {
    isLoadingVoices.value = false
  }
}

// 设置默认语音角色选项
const setDefaultVoiceOptions = (serviceType: string) => {
  switch (serviceType) {
    case 'edge':
      voiceOptions.value = [
        { id: 'zh-CN-XiaoxiaoNeural', name: '晓晓 (女声)' },
        { id: 'zh-CN-YunxiNeural', name: '云希 (男声)' }
      ]
      break
    case 'fish':
      voiceOptions.value = [
        { id: 'default', name: '默认角色' }
      ]
      break
    case 'azure':
      voiceOptions.value = [
        { id: 'zh-CN-XiaoxiaoNeural', name: '晓晓 (女声)' },
        { id: 'zh-CN-YunxiNeural', name: '云希 (男声)' }
      ]
      break
    default:
      voiceOptions.value = []
  }
}

// 试听配音
const playPreview = async () => {
  if (!canPreview.value || isPreviewPlaying.value) return
  
  try {
    isPreviewPlaying.value = true
    
    // 停止当前播放的音频
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
    }
    
    // 使用TTS服务生成语音
    const result = await ttsService.generateSpeech(
      props.config.service as TTSEngine,
      props.config.voice,
      previewText.value,
      {
        speed: props.config.speed
      }
    )
    
    if (result.success && result.audioUrl) {
      // 创建音频元素并播放
      currentAudio.value = new Audio(result.audioUrl)
      currentAudio.value.onended = () => {
        isPreviewPlaying.value = false
      }
      currentAudio.value.onerror = () => {
        isPreviewPlaying.value = false
        // eslint-disable-next-line no-console
        console.error('音频播放失败')
      }
      
      await currentAudio.value.play()
    }
    else {
      throw new Error(result.error || '语音生成失败')
    }
  }
  catch (error) {
    isPreviewPlaying.value = false
    // eslint-disable-next-line no-console
    console.error('试听失败:', error)
    // eslint-disable-next-line no-alert
    alert('试听失败，请检查配置')
  }
}

// 监听服务类型变化，重新加载语音角色
watch(() => props.config.service, (newService) => {
  loadVoiceOptions(newService)
  
  // 设置默认语音角色
  const defaultVoice = (defaultVoiceMap as any)[newService] || ''
  if (defaultVoice && props.config.voice !== defaultVoice) {
    emit('update:config', { ...props.config, voice: defaultVoice })
  }
}, { immediate: true })

// 组件挂载时加载语音角色
onMounted(() => {
  loadVoiceOptions(props.config.service)
})
</script>

<style lang="scss" scoped>
.settings-section {
  .section-header {
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
      color: white;

      .section-icon {
        margin-right: 8px;
        font-size: 24px;
      }
    }

    .section-desc {
      margin: 0;
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
    }
  }

  .settings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;

    .full-width {
      grid-column: 1 / -1;
    }
  }

  .setting-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;

    .setting-label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      color: white;
      font-size: 14px;
    }

    .setting-select {
      width: 100%;
      padding: 12px 16px;
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.05);
      color: white;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        border-color: rgba(52, 152, 219, 0.6);
      }

      &:focus {
        outline: none;
        border-color: rgba(52, 152, 219, 0.8);
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
      }

      option {
        background: #2c3e50;
        color: white;
      }
    }

    .setting-slider {
      width: 100%;
      margin-bottom: 8px;
    }

    .slider-value {
      color: rgba(255, 255, 255, 0.8);
      font-size: 14px;
    }
  }
}

/* 试听功能样式 */
.preview-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.preview-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 14px;
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: rgba(52, 152, 219, 0.6);
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
}

.preview-btn {
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  min-width: 100px;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
  }
  
  &:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
  }
}

.setting-help {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}
</style>
