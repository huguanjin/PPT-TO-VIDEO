<template>
  <div class="unified-config">
    <div class="config-modal">
      <div class="config-header">
        <div class="header-left">
          <h2 class="title">
            <Format class="title-icon" />
            语音合成配置中心
          </h2>
          <p class="subtitle">统一管理语音合成配置，打造完美的音频体验</p>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <Close />
        </button>
      </div>
      
      <div class="config-content">
        <div class="config-sidebar">
          <div class="sidebar-nav">
            <div 
              v-for="tab in tabs" 
              :key="tab.id"
              :class="['nav-item', { active: activeTab === tab.id }]"
              @click="activeTab = tab.id"
            >
              <component :is="tab.icon" class="nav-icon" />
              <span class="nav-text">{{ tab.label }}</span>
              <div class="nav-indicator" v-if="activeTab === tab.id"></div>
            </div>
          </div>
        </div>
        
        <div class="config-main">
          <div class="tab-content">
            <!-- 语音合成设置 -->
            <div v-if="activeTab === 'tts'" class="tts-config-section">
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
                  <select class="setting-select" v-model="ttsConfig.service" @change="onServiceChange" :disabled="isLoading">
                    <option value="edge_tts">Edge TTS (免费)</option>
                    <option value="fish_tts">Fish TTS (AI克隆)</option>
                    <option value="openai_tts">OpenAI TTS (高级)</option>
                  </select>
                  <div class="form-hint">{{ getServiceDescription(ttsConfig.service) }}</div>
                </div>
                
                <div class="setting-card">
                  <label class="setting-label">语音角色</label>
                  <select class="setting-select" v-model="ttsConfig.voice" :disabled="voicesLoading">
                    <option v-if="voicesLoading" value="">🔄 加载中...</option>
                    <option v-else-if="!voices.length" value="">⚠️ 暂无可用语音</option>
                    <option 
                      v-else 
                      v-for="voice in voices" 
                      :key="voice.id" 
                      :value="voice.id"
                    >
                      {{ voice.display_name }}
                    </option>
                  </select>
                  <div class="form-hint">
                    <span v-if="voicesLoading">正在加载语音角色列表...</span>
                    <span v-else-if="voices.length">共 {{ voices.length }} 个可选角色</span>
                    <span v-else>请选择语音服务以加载角色</span>
                  </div>
                </div>
                
                <div class="setting-card">
                  <label class="setting-label">配音试听</label>
                  <div class="preview-container">
                    <div class="preview-text-input">
                      <input 
                        type="text" 
                        v-model="previewText"
                        placeholder="输入试听文本，如：大家好，欢迎观看本期视频"
                        class="preview-input"
                        maxlength="100"
                      />
                    </div>
                    <div class="preview-controls">
                      <button 
                        class="preview-btn"
                        @click="previewVoice"
                        :disabled="!ttsConfig.voice || previewLoading || voicesLoading"
                      >
                        <span v-if="previewLoading">🔄 生成中...</span>
                        <span v-else>🎵 试听配音</span>
                      </button>
                      <button 
                        v-if="previewAudioUrl"
                        class="play-btn"
                        @click="playPreview"
                        :disabled="previewLoading"
                      >
                        🔊 播放
                      </button>
                    </div>
                    <audio 
                      ref="previewAudio"
                      :src="previewAudioUrl"
                      @ended="onPreviewEnded"
                      @error="onAudioError"
                      @loadstart="onAudioLoadStart"
                      @canplay="onAudioCanPlay"
                      preload="metadata"
                      style="display: none;"
                    >
                      <!-- 添加多种格式支持 -->
                      <source :src="previewAudioUrl" type="audio/mpeg" v-if="previewAudioUrl.endsWith('.mp3')">
                      <source :src="previewAudioUrl" type="audio/wav" v-if="previewAudioUrl.endsWith('.wav')">
                      您的浏览器不支持音频播放。
                    </audio>
                  </div>
                  <div class="form-hint">选择语音角色后，输入文本进行配音试听</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="config-actions">
            <button class="action-btn secondary" @click="$emit('close')">
              取消
            </button>
            <button class="action-btn primary" @click="saveAndClose" :disabled="isLoading">
              <CheckOne class="btn-icon" />
              {{ isLoading ? '保存中...' : '保存配置' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { 
  Format, 
  Close, 
  VolumeNotice, 
  CheckOne
} from '@icon-park/vue-next'

// 基本状态
const isLoading = ref(false)
const voicesLoading = ref(false)
const activeTab = ref('tts')

// 配音试听相关
const previewText = ref('大家好，欢迎观看本期视频！')
const previewLoading = ref(false)
const previewAudioUrl = ref('')
const previewAudio = ref<HTMLAudioElement | null>(null)

// 语音列表
const voices = ref<any[]>([])

// Fish TTS元数据
const fishTTSMeta = ref<{
  default_voice: string
  character_id_dict: Record<string, string>
}>({
  default_voice: '雷军',
  character_id_dict: {}
})

// 发出事件给父组件
const emit = defineEmits<{
  close: []
}>()

// 标签页配置 - 只保留语音合成
const tabs = [
  { id: 'tts', label: '语音合成', icon: VolumeNotice }
]

// TTS配置
const ttsConfig = reactive({
  service: 'edge_tts',
  voice: 'zh-CN-XiaoxiaoNeural'
})

// 获取Fish TTS默认角色ID
const getDefaultFishCharacterId = (): string => {
  const defaultVoice = fishTTSMeta.value.default_voice
  const characterIdDict = fishTTSMeta.value.character_id_dict
  
  // 从character_id_dict中获取默认角色的ID
  return characterIdDict[defaultVoice] || '738d0cc1a3e9430a9de2b544a466a7fc'
}

// 获取服务描述
const getServiceDescription = (service: string): string => {
  const descriptions = {
    'edge_tts': 'Microsoft Edge TTS - 免费高质量语音合成',
    'fish_tts': 'Fish TTS - AI语音克隆技术，支持名人声音',
    'openai_tts': 'OpenAI TTS - 先进的AI语音合成服务'
  }
  return descriptions[service as keyof typeof descriptions] || '未知服务'
}

// 加载语音列表
const loadVoices = async (engineId: string) => {
  if (!engineId) return
  
  try {
    voicesLoading.value = true
    const response = await fetch(`/api/tts/voices/${engineId}`)
    const result = await response.json()
    
    if (result.success && result.data && result.data.voices) {
      voices.value = result.data.voices
      
      // 如果是Fish TTS，存储元数据
      if (engineId === 'fish_tts' && result.data) {
        fishTTSMeta.value = {
          default_voice: result.data.default_voice || '雷军',
          character_id_dict: result.data.character_id_dict || {}
        }
      }
      
      // 如果当前选择的语音不在新列表中，选择第一个可用语音
      if (voices.value.length > 0) {
        const currentVoiceExists = voices.value.some(v => v.id === ttsConfig.voice)
        if (!currentVoiceExists) {
          ttsConfig.voice = voices.value[0].id
        }
      }
    }
    else {
      // 加载失败时重置语音列表
      voices.value = []
    }
  }
  catch (error) {
    // 异常时重置语音列表
    voices.value = []
  }
  finally {
    voicesLoading.value = false
  }
}

// 服务切换事件
const onServiceChange = async () => {
  await loadVoices(ttsConfig.service)
}

// 配音试听功能
const previewVoice = async () => {
  if (!ttsConfig.service || !ttsConfig.voice || !previewText.value.trim()) {
    return
  }
  
  try {
    previewLoading.value = true
    previewAudioUrl.value = ''
    
    const response = await fetch('/api/tts/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        engine_id: ttsConfig.service,
        voice_id: ttsConfig.voice,
        text: previewText.value.trim()
      })
    })
    
    const result = await response.json()
    if (result.success && result.data && result.data.audio_url) {
      // 确保URL是完整的HTTP URL
      const audioUrl = result.data.audio_url.startsWith('http') 
        ? result.data.audio_url 
        : `${window.location.protocol}//${window.location.host}${result.data.audio_url}`
      
      previewAudioUrl.value = audioUrl
    }
    else {
      // 试听失败，可以在这里显示错误提示
    }
  }
  catch (error) {
    // 试听异常处理
  }
  finally {
    previewLoading.value = false
  }
}

// 播放试听音频
const playPreview = async () => {
  if (!previewAudioUrl.value) {
    return
  }
  
  try {
    // 创建新的Audio对象，避免复用问题
    const audio = new Audio(previewAudioUrl.value)
    
    // 设置音频属性
    audio.preload = 'metadata'
    audio.volume = 0.8
    
    // 添加事件监听
    audio.addEventListener('loadstart', () => {
      // 开始加载
    })
    
    audio.addEventListener('canplay', () => {
      // 可以播放
    })
    
    audio.addEventListener('error', () => {
      // 播放错误
    })
    
    // 等待音频加载并播放
    await audio.play()
  }
  catch (error) {
    // 播放失败处理
    // 可以在这里显示用户友好的错误提示
  }
}

// 试听音频播放结束
const onPreviewEnded = () => {
  // 可以在这里添加播放结束后的处理逻辑
}

// 音频加载开始
const onAudioLoadStart = () => {
  // 音频开始加载
}

// 音频可以播放
const onAudioCanPlay = () => {
  // 音频准备好可以播放
}

// 音频错误处理
const onAudioError = (event: Event) => {
  const audio = event.target as HTMLAudioElement
  if (audio && audio.error) {
    // 处理音频播放错误
    // 可以显示用户友好的错误提示
  }
}

// 加载当前配置
const loadConfig = async () => {
  try {
    isLoading.value = true
    const response = await fetch('/api/tts/config')
    const result = await response.json()
    
    if (result.success && result.data) {
      const config = result.data
      ttsConfig.service = config.current_engine || 'edge_tts'
      
      if (config.edge_config) {
        if (ttsConfig.service === 'edge_tts') {
          ttsConfig.voice = config.edge_config.voice || 'zh-CN-XiaoxiaoNeural'
        }
      }
      
      if (config.fish_config) {
        if (ttsConfig.service === 'fish_tts') {
          ttsConfig.voice = config.fish_config.character || fishTTSMeta.value.default_voice
        }
      }
    }
  }
  catch (error) {
    // 加载配置失败
  }
  finally {
    isLoading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    isLoading.value = true
    
    // 数据验证
    if (!ttsConfig.service) {
      throw new Error('请选择语音服务')
    }
    
    if (!ttsConfig.voice) {
      throw new Error('请选择语音角色')
    }
    
    // 构建保存数据 - 使用后端期望的嵌套格式
    const configData = {
      preferred_engine: ttsConfig.service,
      _updated_at: new Date().toISOString(),
      
      // Edge TTS配置
      edge_config: {
        voice: ttsConfig.service === 'edge_tts' ? ttsConfig.voice : 'zh-CN-XiaoxiaoNeural',
        rate: '+0%', // 固定为默认值
        pitch: '+0Hz' // 固定为默认值
      },
      
      // Fish TTS配置
      fish_config: {
        character: ttsConfig.service === 'fish_tts' ? ttsConfig.voice : fishTTSMeta.value.default_voice,
        // 获取当前选中voice的character_id - 使用character_id而不是id
        character_id: ttsConfig.service === 'fish_tts' ? 
          (voices.value.find(v => v.name === ttsConfig.voice)?.character_id || 
           voices.value.find(v => v.display_name === ttsConfig.voice)?.character_id ||
           getDefaultFishCharacterId()) : 
          getDefaultFishCharacterId() // 使用动态获取的默认ID
      }
    }
    
    // 额外验证Fish TTS的character_id
    if (ttsConfig.service === 'fish_tts') {
      const characterId = configData.fish_config.character_id
      // 验证character_id是否是有效的UUID格式
      if (!characterId || characterId === ttsConfig.voice || characterId.length < 30) {
        throw new Error(`无法获取Fish TTS角色ID，选中角色: ${ttsConfig.voice}，获取到ID: ${characterId}`)
      }
    }
    
    // 发送配置保存请求
    const response = await fetch('/api/tts/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(configData)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    if (result.success) {
      // 显示成功提示
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({ 
          type: 'notification', 
          message: 'TTS配置保存成功！',
          level: 'success'
        }, '*')
      }
    } 
    else {
      throw new Error(result.message || '配置保存失败')
    }
  }
  catch (error) {
    // 显示错误提示
    const errorMessage = error instanceof Error ? error.message : String(error)
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ 
        type: 'notification', 
        message: `保存失败: ${errorMessage}`,
        level: 'error'
      }, '*')
    }
  }
  finally {
    isLoading.value = false
  }
}

// 组件挂载时初始化
onMounted(async () => {
  await loadConfig()
  await loadVoices(ttsConfig.service)
})

// 监听服务变化
watch(() => ttsConfig.service, (newService) => {
  if (newService) {
    loadVoices(newService)
  }
})

// 处理关闭
const handleClose = () => {
  emit('close')
}

// 保存并关闭
const saveAndClose = async () => {
  await saveConfig()
  handleClose()
}
</script>

<style scoped lang="scss">
.unified-config {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.config-modal {
  width: 80vw;
  max-width: 1200px;
  height: 80vh;
  max-height: 800px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;

  .header-left {
    .title {
      display: flex;
      align-items: center;
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;

      .title-icon {
        margin-right: 12px;
        font-size: 28px;
      }
    }

    .subtitle {
      margin: 0;
      font-size: 14px;
      opacity: 0.9;
    }
  }

  .close-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    border-radius: 8px;
    padding: 8px;
    color: white;
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  }
}

.config-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.config-sidebar {
  width: 280px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;

  .sidebar-nav {
    padding: 24px 16px;

    .nav-item {
      display: flex;
      align-items: center;
      padding: 16px 20px;
      margin-bottom: 8px;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.2s;
      position: relative;

      .nav-icon {
        margin-right: 12px;
        font-size: 20px;
        color: #64748b;
      }

      .nav-text {
        font-size: 15px;
        font-weight: 500;
        color: #334155;
      }

      .nav-indicator {
        position: absolute;
        right: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 24px;
        background: #667eea;
        border-radius: 2px;
      }

      &:hover {
        background: #e2e8f0;
        transform: translateX(4px);
      }

      &.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateX(8px);

        .nav-icon,
        .nav-text {
          color: white;
        }
      }
    }
  }
}

.config-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}

.config-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 24px 32px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;

  .action-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;

    .btn-icon {
      font-size: 16px;
    }

    &.secondary {
      background: #e2e8f0;
      color: #64748b;

      &:hover {
        background: #cbd5e1;
      }
    }

    &.primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
      }
    }
  }
}

// TTS配置样式
.tts-config-section {
  .section-header {
    margin-bottom: 32px;
    
    h3 {
      display: flex;
      align-items: center;
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
      color: #1e293b;
      
      .section-icon {
        margin-right: 12px;
        font-size: 24px;
        color: #667eea;
      }
    }
    
    .section-desc {
      margin: 0;
      font-size: 14px;
      color: #64748b;
    }
  }
  
  .settings-grid {
    display: grid;
    gap: 24px;
    
    .setting-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 20px;
      transition: all 0.2s;
      
      &:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
      }
      
      .setting-label {
        display: block;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
      }
      
      .setting-select {
        width: 100%;
        padding: 12px 16px;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        background: white;
        font-size: 14px;
        color: #374151;
        transition: border-color 0.2s;
        
        &:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
      }
      
      .slider-container {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .setting-slider {
          flex: 1;
          height: 6px;
          border-radius: 3px;
          background: #e2e8f0;
          outline: none;
          appearance: none;
          
          &::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
          }
          
          &::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border: none;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
          }
        }
        
        .slider-value {
          font-size: 14px;
          font-weight: 500;
          color: #667eea;
          min-width: 40px;
          text-align: center;
        }
      }
      
      .form-hint {
        margin-top: 8px;
        font-size: 12px;
        color: #64748b;
        line-height: 1.4;
      }
      
      // 配音试听样式
      .preview-container {
        .preview-text-input {
          margin-bottom: 16px;
          
          .preview-input {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            background: white;
            font-size: 14px;
            color: #374151;
            transition: border-color 0.2s;
            
            &::placeholder {
              color: #9ca3af;
            }
            
            &:focus {
              outline: none;
              border-color: #667eea;
              box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
          }
        }
        
        .preview-controls {
          display: flex;
          gap: 12px;
          
          .preview-btn,
          .play-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            
            &:disabled {
              opacity: 0.5;
              cursor: not-allowed;
            }
          }
          
          .preview-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            
            &:hover:not(:disabled) {
              transform: translateY(-1px);
              box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
          }
          
          .play-btn {
            background: #10b981;
            color: white;
            
            &:hover:not(:disabled) {
              background: #059669;
              transform: translateY(-1px);
              box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .config-modal {
    width: 95vw;
    height: 95vh;
  }

  .config-content {
    flex-direction: column;
  }

  .config-sidebar {
    width: 100%;
    height: 120px;
    overflow-x: auto;

    .sidebar-nav {
      display: flex;
      padding: 16px;
      gap: 8px;

      .nav-item {
        flex-shrink: 0;
        margin-bottom: 0;
        white-space: nowrap;
      }
    }
  }

  .tab-content {
    padding: 16px;
  }
}
</style>