<template>
  <div class="fish-tts-config">
    <div class="param-group full-width">
      <label>🔑 API密钥</label>
      <div class="input-wrapper">
        <input 
          type="password" 
          v-model="fishApiKey" 
          placeholder="输入Fish TTS API密钥" 
          class="modern-input"
        />
        <div class="input-help">
          <span>💡 获取API密钥：访问 <a href="https://fish.audio" target="_blank">fish.audio</a></span>
        </div>
      </div>
    </div>
    
    <div class="param-group">
      <label>🎯 AI角色</label>
      <div class="select-wrapper">
        <select v-model="fishCharacter" class="modern-select" :disabled="isLoadingCharacters">
          <option v-if="isLoadingCharacters" disabled>加载中...</option>
          <option 
            v-for="character in availableCharacters" 
            :key="character.id" 
            :value="character.name"
          >
            {{ character.display_name }}
          </option>
          <!-- 当没有选项时显示默认提示 -->
          <option v-if="!isLoadingCharacters && availableCharacters.length === 0" disabled>
            暂无可用角色
          </option>
        </select>
      </div>
    </div>
    
    <div class="param-group">
      <label>🆔 角色ID</label>
      <div class="input-wrapper">
        <input 
          type="text" 
          v-model="fishCharacterId" 
          placeholder="角色标识符"
          class="modern-input"
          readonly
        />
      </div>
    </div>
    
    <div class="param-group">
      <label>📝 角色名称</label>
      <div class="input-wrapper">
        <input 
          type="text" 
          v-model="fishCharacterName" 
          placeholder="显示名称"
          class="modern-input"
        />
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

interface FishTTSConfig {
  fish_api_key: string
  fish_character: string
  fish_character_id: string
  fish_character_name: string
}

interface Props {
  config: FishTTSConfig
}

interface Emits {
  (e: 'update:config', config: FishTTSConfig): void
}

interface FishCharacter {
  id: string
  name: string
  display_name: string
  character_id: string
  description: string
  style: string
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式变量
const isLoadingCharacters = ref(false)
const availableCharacters = ref<FishCharacter[]>([])

// 试听相关
const previewText = ref('你好，这是Fish TTS配音试听。')
const isPreviewPlaying = ref(false)
const currentAudio = ref<HTMLAudioElement | null>(null)

// 角色映射表（备用）
const fallbackCharacterMapping = {
  '雷军': { id: 'leijun_001', name: '雷军' },
  'AD学姐': { id: 'ad_sister_001', name: 'AD学姐' },
  '丁真': { id: 'dingzhen_001', name: '丁真' },
  '赛马娘': { id: 'uma_musume_001', name: '赛马娘' },
  '蔡徐坤': { id: 'caixukun_001', name: '蔡徐坤' },
  '郭德纲': { id: 'guodegang_001', name: '郭德纲' },
  '于谦': { id: 'yuqian_001', name: '于谦' },
  '周杰伦': { id: 'zhoujielun_001', name: '周杰伦' },
  '邓紫棋': { id: 'dengziqi_001', name: '邓紫棋' },
  '罗永浩': { id: 'luoyonghao_001', name: '罗永浩' }
}

// 加载Fish TTS角色列表
const loadFishCharacters = async () => {
  isLoadingCharacters.value = true
  try {
    const response = await fetch('http://localhost:5000/api/tts/voices?engine=fish')
    const result = await response.json()
    
    if (result.success && result.data && result.data.voices) {
      availableCharacters.value = result.data.voices.map((voice: any) => ({
        id: voice.id,
        name: voice.id,
        display_name: voice.name,
        character_id: voice.id,
        description: voice.description || '',
        style: ''
      }))
    }
    else {
      // eslint-disable-next-line no-console
      console.warn('无法加载Fish TTS角色:', result.message)
      // 使用备用角色列表
      setFallbackCharacters()
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('加载Fish TTS角色失败:', error)
    // 使用备用角色列表
    setFallbackCharacters()
  }
  finally {
    isLoadingCharacters.value = false
  }
}

// 设置备用角色列表
const setFallbackCharacters = () => {
  availableCharacters.value = Object.entries(fallbackCharacterMapping).map(([name, data]) => ({
    id: data.id,
    name: name,
    display_name: name,
    character_id: data.id,
    description: '',
    style: ''
  }))
}

// 组件挂载时加载角色
onMounted(() => {
  loadFishCharacters()
})

// 试听相关计算属性和方法
const canPreview = computed(() => {
  return previewText.value.trim().length > 0 && 
         fishApiKey.value.trim().length > 0 && 
         fishCharacterId.value.trim().length > 0
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
        engine: 'fish',
        voice: fishCharacterId.value,
        api_key: fishApiKey.value
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

const fishApiKey = computed({
  get: () => props.config.fish_api_key,
  set: (value) => emit('update:config', { ...props.config, fish_api_key: value })
})

const fishCharacter = computed({
  get: () => props.config.fish_character,
  set: (value) => {
    // 找到选中的角色
    const selectedCharacter = availableCharacters.value.find(char => char.name === value)
    if (selectedCharacter) {
      emit('update:config', { 
        ...props.config, 
        fish_character: value,
        fish_character_id: selectedCharacter.character_id,
        fish_character_name: selectedCharacter.display_name
      })
    }
    else {
      // 备用映射
      const mapping = fallbackCharacterMapping[value as keyof typeof fallbackCharacterMapping]
      emit('update:config', { 
        ...props.config, 
        fish_character: value,
        fish_character_id: mapping?.id || value,
        fish_character_name: mapping?.name || value
      })
    }
  }
})

const fishCharacterId = computed({
  get: () => props.config.fish_character_id,
  set: (value) => emit('update:config', { ...props.config, fish_character_id: value })
})

const fishCharacterName = computed({
  get: () => props.config.fish_character_name,
  set: (value) => emit('update:config', { ...props.config, fish_character_name: value })
})
</script>

<style lang="scss" scoped>
.fish-tts-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.param-group {
  margin-bottom: 20px;
  
  &.full-width {
    grid-column: 1 / -1;
  }
  
  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #2c3e50;
    font-size: 14px;
  }
}

.input-wrapper {
  position: relative;
  
  .input-help {
    margin-top: 6px;
    font-size: 12px;
    color: #666;
    
    a {
      color: #3498db;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
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

.modern-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #2c3e50;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #3498db;
  }
  
  &:focus {
    outline: none;
    border-color: #2980b9;
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
  }
  
  &:read-only {
    background: #f8f9fa;
    color: #666;
  }
  
  &::placeholder {
    color: #95a5a6;
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
</style>
