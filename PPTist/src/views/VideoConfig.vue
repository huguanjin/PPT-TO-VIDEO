<template>
  <div class="video-config-page">
    <div class="config-container">
      <div class="config-header">
        <h1>视频导出配置</h1>
        <p>在开始PPT转视频工作流前，请先配置相关参数</p>
      </div>

      <div class="config-content">
        <!-- 视频设置 -->
        <VideoSettings :config="config" />

        <!-- 字幕设置 -->
        <SubtitleSettings :config="config" />

        <!-- TTS设置 -->
        <TTSConfig v-model:config="config.tts" />

        <!-- AI设置 -->
        <AISettings :config="config" />
      </div>

      <div class="config-footer">
        <button @click="resetToDefaults" class="btn btn-secondary">重置默认</button>
        <button @click="saveConfig" class="btn btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
        <button @click="closeConfig" class="btn btn-secondary">关闭</button>
      </div>

      <!-- 保存状态提示 -->
      <div v-if="saveStatus" class="save-status" :class="saveStatus.type">
        {{ saveStatus.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import VideoSettings from '@/components/VideoSettings.vue'
import SubtitleSettings from '@/components/SubtitleSettings.vue'
import TTSConfig from '@/components/TTSConfig.vue'
import AISettings from '@/components/AISettings.vue'
import { apiRequest } from '@/config/api'

// 定义 emits
const emit = defineEmits<{
  close: []
}>()

// 配置数据结构
interface VideoConfig {
  resolution: string
  fps: number
  video_bitrate: string
  background_color: string
  include_subtitles: boolean
}

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
}

interface LocalTTSConfig {
  preferred_engine: string
  edge_voice: string
  edge_rate: string
  edge_pitch: string
  fish_api_key: string
  fish_character: string
  fish_character_id: string
  fish_character_name: string
  openai_api_key: string
  openai_voice: string
  openai_model: string
  azure_api_key: string
  azure_region: string
  azure_voice: string
  sample_rate: number
  max_retries: number
  timeout: number
}

interface AIServiceConfig {
  api_key: string
  base_url: string
  model: string
  timeout: number
  max_retries: number
  support_json?: boolean
}

interface AIConfig {
  openai: AIServiceConfig
  anthropic: Omit<AIServiceConfig, 'support_json'>
  custom: AIServiceConfig
  default_service: string
  source_language: string
  target_language: string
  max_workers: number
}

interface AIContentOptimizationConfig {
  enabled: boolean
  max_segment_length: number
  min_segment_length: number
  preserve_meaning: boolean
  natural_breaks: boolean
  fallback_to_original: boolean
}

interface Config {
  video: VideoConfig
  subtitle: SubtitleConfig
  tts: LocalTTSConfig
  ai: AIConfig
  ai_content_optimization: AIContentOptimizationConfig
}

// 状态
const saving = ref(false)
const saveStatus = ref<{type: 'success' | 'error', message: string} | null>(null)

// 默认配置
const config = ref<Config>({
  video: {
    resolution: '1920x1080',
    fps: 30,
    video_bitrate: '2000k',
    background_color: '#ffffff',
    include_subtitles: true as boolean
  },
  subtitle: {
    enabled: true as boolean,
    font_family: '微软雅黑',
    font_size: 24,
    font_color: '#ffffff',
    background_color: '#000000',
    position: 'bottom',
    use_enhanced_mode: false as boolean,
    enable_precise_alignment: false as boolean,
    enable_gap_filling: false as boolean,
    max_chars_per_line: 40,
    auto_punctuation_removal: false as boolean
  },
  tts: {
    preferred_engine: 'edge_tts',
    edge_voice: 'zh-CN-XiaoxiaoNeural',
    edge_rate: '+0%',
    edge_pitch: '+0Hz',
    fish_api_key: '',
    fish_character: 'default',
    fish_character_id: '',
    fish_character_name: '',
    openai_api_key: '',
    openai_voice: 'alloy',
    openai_model: 'tts-1',
    azure_api_key: '',
    azure_region: '',
    azure_voice: 'zh-CN-XiaoxiaoNeural',
    sample_rate: 44100,
    max_retries: 3,
    timeout: 30
  },
  ai: {
    openai: {
      api_key: '',
      base_url: 'https://api.openai.com',
      model: 'gpt-3.5-turbo',
      timeout: 300,
      max_retries: 3,
      support_json: true as boolean
    },
    anthropic: {
      api_key: '',
      base_url: 'https://api.anthropic.com',
      model: 'claude-3-sonnet-20240229',
      timeout: 300,
      max_retries: 3
    },
    custom: {
      api_key: '',
      base_url: '',
      model: '',
      timeout: 300,
      max_retries: 3,
      support_json: true as boolean
    },
    default_service: 'openai',
    source_language: '中文',
    target_language: '中文',
    max_workers: 4
  },
  ai_content_optimization: {
    enabled: false as boolean,
    max_segment_length: 35,
    min_segment_length: 10,
    preserve_meaning: true as boolean,
    natural_breaks: true as boolean,
    fallback_to_original: true as boolean
  }
})

// 方法
const loadConfig = async () => {
  try {
    const response = await apiRequest('/api/config')
    if (response.success && response.data?.config) {
      const data = response.data.config
      
      // 合并配置，保持类型安全
      if (data.video) {
        Object.assign(config.value.video, data.video)
      }
      if (data.subtitle) {
        Object.assign(config.value.subtitle, data.subtitle)
      }
      if (data.tts) {
        Object.assign(config.value.tts, data.tts)
      }
      if (data.ai) {
        Object.assign(config.value.ai, data.ai)
      }
    }
  } 
  catch (error) {
    // 加载配置失败，使用默认配置
  }
}

const saveConfig = async () => {
  saving.value = true
  saveStatus.value = null

  try {
    const response = await apiRequest('/api/config', {
      method: 'POST',
      body: JSON.stringify({ config: config.value }),
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.success) {
      saveStatus.value = { type: 'success', message: '配置保存成功！' }
    } 
    else {
      saveStatus.value = { type: 'error', message: response.message || '保存失败' }
    }
  } 
  catch (error) {
    saveStatus.value = { 
      type: 'error', 
      message: error instanceof Error ? error.message : '保存失败' 
    }
  } 
  finally {
    saving.value = false
    // 3秒后清除状态提示
    setTimeout(() => {
      saveStatus.value = null
    }, 3000)
  }
}

const resetToDefaults = () => {
  // eslint-disable-next-line no-alert
  if (confirm('确定要重置为默认配置吗？这将清除所有当前设置。')) {
    config.value = {
      video: {
        resolution: '1920x1080',
        fps: 30,
        video_bitrate: '2000k',
        background_color: '#ffffff',
        include_subtitles: true as boolean
      },
      subtitle: {
        enabled: true as boolean,
        font_family: '微软雅黑',
        font_size: 24,
        font_color: '#ffffff',
        background_color: '#000000',
        position: 'bottom',
        use_enhanced_mode: false as boolean,
        enable_precise_alignment: false as boolean,
        enable_gap_filling: false as boolean,
        max_chars_per_line: 40,
        auto_punctuation_removal: false as boolean
      },
      tts: {
        preferred_engine: 'edge_tts',
        edge_voice: 'zh-CN-XiaoxiaoNeural',
        edge_rate: '+0%',
        edge_pitch: '+0Hz',
        fish_api_key: '',
        fish_character: 'default',
        fish_character_id: '',
        fish_character_name: '',
        openai_api_key: '',
        openai_voice: 'alloy',
        openai_model: 'tts-1',
        azure_api_key: '',
        azure_region: '',
        azure_voice: 'zh-CN-XiaoxiaoNeural',
        sample_rate: 44100,
        max_retries: 3,
        timeout: 30
      },
      ai: {
        openai: {
          api_key: '',
          base_url: 'https://api.openai.com',
          model: 'gpt-3.5-turbo',
          timeout: 300,
          max_retries: 3,
          support_json: true as boolean
        },
        anthropic: {
          api_key: '',
          base_url: 'https://api.anthropic.com',
          model: 'claude-3-sonnet-20240229',
          timeout: 300,
          max_retries: 3
        },
        custom: {
          api_key: '',
          base_url: '',
          model: '',
          timeout: 300,
          max_retries: 3,
          support_json: true as boolean
        },
        default_service: 'openai',
        source_language: '中文',
        target_language: '中文',
        max_workers: 4
      },
      ai_content_optimization: {
        enabled: false as boolean,
        max_segment_length: 35,
        min_segment_length: 10,
        preserve_meaning: true as boolean,
        natural_breaks: true as boolean,
        fallback_to_original: true as boolean
      }
    }
  }
}

const closeConfig = () => {
  emit('close')
}

// 生命周期
onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.video-config-page {
  background: white;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.config-container {
  background: white;
  overflow: hidden;
}

.config-header {
  background: linear-gradient(135deg, #5c7cfa 0%, #748ffc 100%);
  color: white;
  padding: 30px;
  text-align: center;

  h1 {
    margin: 0 0 10px 0;
    font-size: 2.5em;
    font-weight: 300;
  }

  p {
    margin: 0;
    opacity: 0.9;
    font-size: 1.1em;
  }
}

.config-content {
  padding: 30px;
}

.config-footer {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 30px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.btn {
  padding: 12px 30px;
  border: none;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &.btn-primary {
    background: linear-gradient(135deg, #5c7cfa 0%, #748ffc 100%);
    color: white;

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(92, 124, 250, 0.3);
    }

    &:disabled {
      background: #adb5bd;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }
  }

  &.btn-secondary {
    background: #6c757d;
    color: white;

    &:hover {
      background: #5a6268;
      transform: translateY(-1px);
    }
  }
}

.save-status {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 8px;
  font-weight: 600;
  z-index: 1000;
  animation: slideIn 0.3s ease;

  &.success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
  }

  &.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
  }
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .config-footer {
    flex-direction: column;
    gap: 15px;
  }
  
  .config-footer .btn {
    width: 100%;
  }
}
</style>
