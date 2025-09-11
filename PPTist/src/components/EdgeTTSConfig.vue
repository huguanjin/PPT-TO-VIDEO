<template>
  <div class="edge-tts-config">
    <div class="param-group">
      <label>🎭 声音角色</label>
      <div class="select-wrapper">
        <select v-model="edgeVoice" class="modern-select" :disabled="isLoadingVoices">
          <option v-if="isLoadingVoices" disabled>加载中...</option>
          <option 
            v-for="voice in availableVoices" 
            :key="voice.id" 
            :value="voice.id"
          >
            {{ voice.display_name }}
          </option>
          <!-- 当没有选项时显示默认提示 -->
          <option v-if="!isLoadingVoices && availableVoices.length === 0" disabled>
            暂无可用声音
          </option>
        </select>
      </div>
    </div>
    
    <div class="param-group">
      <label>⚡ 语速</label>
      <div class="select-wrapper">
        <select v-model="edgeRate" class="modern-select">
          <option value="-50%">很慢 (-50%)</option>
          <option value="-25%">慢 (-25%)</option>
          <option value="+0%">正常 (0%)</option>
          <option value="+25%">快 (+25%)</option>
          <option value="+50%">很快 (+50%)</option>
          <option value="+75%">极快 (+75%)</option>
        </select>
      </div>
    </div>
    
    <div class="param-group">
      <label>🎵 音调</label>
      <div class="select-wrapper">
        <select v-model="edgePitch" class="modern-select">
          <option value="-50Hz">很低 (-50Hz)</option>
          <option value="-25Hz">低 (-25Hz)</option>
          <option value="+0Hz">正常 (0Hz)</option>
          <option value="+25Hz">高 (+25Hz)</option>
          <option value="+50Hz">很高 (+50Hz)</option>
        </select>
      </div>
    </div>

    <!-- 试听功能 -->
    <div class="param-group full-width">
      <label>🎵 试听配音</label>
      <div class="preview-wrapper">
        <div class="input-wrapper" style="flex: 1;">
          <input 
            type="text" 
            v-model="previewText" 
            placeholder="输入试听文本（最多200字）"
            class="modern-input"
            maxlength="200"
          />
        </div>
        <button 
          @click="playPreview" 
          :disabled="!canPreview || isPreviewPlaying"
          class="preview-btn"
        >
          <span v-if="!isPreviewPlaying">🎵 试听</span>
          <span v-else>⏸️ 播放中...</span>
        </button>
      </div>
      <div class="input-help">
        <span>💡 点击试听按钮可以预览当前配置的声音效果</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'

interface EdgeTTSConfig {
  edge_voice: string
  edge_rate: string
  edge_pitch: string
}

interface Props {
  config: EdgeTTSConfig
}

interface Emits {
  (e: 'update:config', config: EdgeTTSConfig): void
}

interface EdgeVoice {
  id: string
  name: string
  display_name: string
  gender: string
  region: string
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式变量
const isLoadingVoices = ref(false)
const availableVoices = ref<EdgeVoice[]>([])

// 试听相关
const previewText = ref('你好，这是Edge TTS配音试听。')
const isPreviewPlaying = ref(false)
const currentAudio = ref<HTMLAudioElement | null>(null)

// 备用语音列表
const fallbackVoices = [
  { id: 'zh-CN-XiaoxiaoNeural', name: 'zh-CN-XiaoxiaoNeural', display_name: '晓晓 (女声)', gender: '女', region: 'zh-CN' },
  { id: 'zh-CN-YunxiNeural', name: 'zh-CN-YunxiNeural', display_name: '云希 (男声)', gender: '男', region: 'zh-CN' },
  { id: 'zh-CN-YunyangNeural', name: 'zh-CN-YunyangNeural', display_name: '云扬 (男声)', gender: '男', region: 'zh-CN' },
  { id: 'zh-CN-XiaoyiNeural', name: 'zh-CN-XiaoyiNeural', display_name: '晓伊 (女声)', gender: '女', region: 'zh-CN' },
  { id: 'zh-CN-YunjianNeural', name: 'zh-CN-YunjianNeural', display_name: '云健 (男声)', gender: '男', region: 'zh-CN' }
]

// 加载Edge TTS语音列表
const loadEdgeVoices = async () => {
  isLoadingVoices.value = true
  try {
    const response = await fetch('http://localhost:5000/api/tts/voices?engine=edge')
    const result = await response.json()
    
    if (result.success && result.data && result.data.voices) {
      availableVoices.value = result.data.voices.map((voice: any) => ({
        id: voice.id,
        name: voice.id,
        display_name: voice.name,
        gender: '',
        region: voice.language || ''
      }))
    }
    else {
      // eslint-disable-next-line no-console
      console.warn('无法加载Edge TTS语音:', result.message)
      // 使用备用语音列表
      availableVoices.value = fallbackVoices
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('加载Edge TTS语音失败:', error)
    // 使用备用语音列表
    availableVoices.value = fallbackVoices
  }
  finally {
    isLoadingVoices.value = false
  }
}

// 组件挂载时加载语音
onMounted(() => {
  loadEdgeVoices()
})

// 试听相关计算属性和方法
const canPreview = computed(() => {
  return previewText.value.trim().length > 0 && edgeVoice.value.trim().length > 0
})

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
    
    const response = await fetch('/api/tts/preview', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: previewText.value,
        engine: 'edge',
        voice: edgeVoice.value,
        rate: edgeRate.value,
        pitch: edgePitch.value
      })
    })
    
    if (!response.ok) {
      throw new Error(`试听失败: ${response.status}`)
    }
    
    // 获取音频数据
    const audioBlob = await response.blob()
    const audioUrl = URL.createObjectURL(audioBlob)
    
    // 创建音频元素并播放
    currentAudio.value = new Audio(audioUrl)
    currentAudio.value.onended = () => {
      isPreviewPlaying.value = false
      URL.revokeObjectURL(audioUrl)
    }
    currentAudio.value.onerror = () => {
      isPreviewPlaying.value = false
      URL.revokeObjectURL(audioUrl)
      // eslint-disable-next-line no-console
      console.error('音频播放失败')
    }
    
    await currentAudio.value.play()
  }
  catch (error) {
    isPreviewPlaying.value = false
    // eslint-disable-next-line no-console
    console.error('试听失败:', error)
    // eslint-disable-next-line no-alert
    alert('试听失败，请检查配置')
  }
}

const edgeVoice = computed({
  get: () => props.config.edge_voice,
  set: (value) => emit('update:config', { ...props.config, edge_voice: value })
})

const edgeRate = computed({
  get: () => props.config.edge_rate,
  set: (value) => emit('update:config', { ...props.config, edge_rate: value })
})

const edgePitch = computed({
  get: () => props.config.edge_pitch,
  set: (value) => emit('update:config', { ...props.config, edge_pitch: value })
})
</script>

<style lang="scss" scoped>
.edge-tts-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.param-group {
  margin-bottom: 20px;
  
  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #2c3e50;
    font-size: 14px;
  }
}

.select-wrapper {
  position: relative;
  
  &::after {
    content: '▼';
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
    color: #666;
    font-size: 12px;
  }
}

.modern-select {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #2c3e50;
  appearance: none;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #3498db;
  }
  
  &:focus {
    outline: none;
    border-color: #2980b9;
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
  }
  
  option {
    padding: 8px;
    background: white;
    color: #2c3e50;
    
    &:hover {
      background: #f8f9fa;
    }
    
    &:checked {
      background: #3498db;
      color: white;
    }
  }
}

/* 试听功能样式 */
.preview-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
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

.input-help {
  margin-top: 6px;
  font-size: 12px;
  color: #7f8c8d;
  
  a {
    color: #3498db;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
