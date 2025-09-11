<template>
  <div class="unified-config">
    <div class="config-header">
      <h2>项目配置</h2>
      <div class="close-btn" @click="$emit('close')">
        <IconClose />
      </div>
    </div>
    
    <div class="config-content">
      <div class="sidebar">
        <div class="tabs">
          <div 
            v-for="tab in tabs" 
            :key="tab.id" 
            :class="['tab', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            <component :is="tab.icon" class="tab-icon" />
            <span>{{ tab.name }}</span>
          </div>
        </div>
      </div>
      
      <div class="main-content">
        <!-- 视频设置 -->
        <div v-show="activeTab === 'video'" class="tab-content">
          <h3>视频设置</h3>
          <VideoSettings :config="{ video: config.video }" @update:config="updateVideoConfig" />
        </div>
        
        <!-- 字幕设置 -->
        <div v-show="activeTab === 'subtitle'" class="tab-content">
          <h3>字幕设置</h3>
          <SubtitleSettings :config="{ subtitle: config.subtitle }" @update:config="updateSubtitleConfig" />
        </div>
        
        <!-- TTS配置 -->
        <div v-show="activeTab === 'tts'" class="tab-content">
          <h3>语音合成</h3>
          <TTSConfig v-model:config="config.tts" />
        </div>
        
        <!-- AI配置 -->
        <div v-show="activeTab === 'ai'" class="tab-content">
          <h3>AI配置</h3>
          <div class="ai-config-wrapper">
            <AISettings :config="{ ai: config.ai, ai_content_optimization: config.ai_content_optimization }" @update:config="updateAIConfig" />
          </div>
        </div>
      </div>
    </div>
    
    <div class="config-footer">
      <button class="btn btn-secondary" @click="$emit('close')">取消</button>
      <button class="btn btn-primary" @click="saveConfig">保存配置</button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue'
import VideoSettings from '@/components/VideoSettings.vue'
import SubtitleSettings from '@/components/SubtitleSettings.vue'
import TTSConfig from '@/components/TTSConfig.vue'
import AISettings from '@/components/AISettings.vue'

// 类型定义
interface VideoConfig {
  resolution: string
  fps: number
  video_bitrate: string
  background_color: string
  include_subtitles?: boolean
}

interface SubtitleConfig {
  enabled: boolean
  use_enhanced_mode: boolean
  enable_precise_alignment: boolean
  enable_gap_filling: boolean
  auto_punctuation_removal: boolean
  max_chars_per_line: number
  font_family: string
  font_size: number
  font_color: string
  outline_color: string
  background_color: string
  position: string
  margin_bottom: number
}

interface TTSConfigType {
  preferred_engine: string
  edge_voice: string
  edge_rate: string
  edge_pitch: string
  fish_api_key: string
  fish_character: string
  fish_character_id: string
  fish_character_name: string
  azure_api_key?: string
  azure_region?: string
  azure_voice?: string
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

interface AIConfigType {
  openai: AIServiceConfig
  anthropic: Omit<AIServiceConfig, 'support_json'>
  custom: AIServiceConfig
  default_service: string
  source_language: string
  target_language: string
  max_workers: number
}

const emit = defineEmits(['close'])

const activeTab = ref('video')

// 配置状态
const config = reactive({
  video: {
    resolution: '1920x1080',
    fps: 30,
    video_bitrate: '2000k',
    background_color: '#ffffff',
    include_subtitles: true
  } as VideoConfig,
  subtitle: {
    enabled: true,
    use_enhanced_mode: false,
    enable_precise_alignment: true,
    enable_gap_filling: true,
    auto_punctuation_removal: true,
    max_chars_per_line: 40,
    font_family: 'SimHei',
    font_size: 24,
    font_color: '#ffffff',
    outline_color: '#000000',
    background_color: 'rgba(0,0,0,0.5)',
    position: 'bottom',
    margin_bottom: 50
  } as SubtitleConfig,
  tts: {
    preferred_engine: 'edge_tts',
    edge_voice: 'zh-CN-XiaoxiaoNeural',
    edge_rate: '+0%',
    edge_pitch: '+0Hz',
    fish_api_key: '',
    fish_character: 'default',
    fish_character_id: '',
    fish_character_name: 'Default',
    azure_api_key: '',
    azure_region: 'eastasia',
    azure_voice: 'zh-CN-XiaoxiaoNeural',
    sample_rate: 44100,
    max_retries: 3,
    timeout: 30
  } as TTSConfigType,
  ai: {
    openai: {
      api_key: '',
      base_url: 'https://api.openai.com/v1',
      model: 'gpt-3.5-turbo',
      timeout: 30,
      max_retries: 3,
      support_json: true
    },
    anthropic: {
      api_key: '',
      base_url: 'https://api.anthropic.com',
      model: 'claude-3-haiku-20240307',
      timeout: 30,
      max_retries: 3
    },
    custom: {
      api_key: '',
      base_url: '',
      model: '',
      timeout: 30,
      max_retries: 3,
      support_json: true
    },
    default_service: 'openai',
    source_language: 'zh',
    target_language: 'zh',
    max_workers: 4
  } as AIConfigType,
  ai_content_optimization: {
    enabled: true,
    max_segment_length: 100,
    min_segment_length: 10,
    preserve_meaning: true,
    natural_breaks: true,
    fallback_to_original: false
  }
})

const tabs = [
  { id: 'video', name: '视频设置', icon: 'IconVideoTwo' },
  { id: 'subtitle', name: '字幕设置', icon: 'IconText' },
  { id: 'tts', name: '语音合成', icon: 'IconVolumeNotice' },
  { id: 'ai', name: 'AI配置', icon: 'IconMagic' }
]

// 配置更新方法
const updateVideoConfig = (newConfig: { video: VideoConfig }) => {
  Object.assign(config.video, newConfig.video)
}

const updateSubtitleConfig = (newConfig: { subtitle: SubtitleConfig }) => {
  Object.assign(config.subtitle, newConfig.subtitle)
}

const updateAIConfig = (newConfig: { ai: AIConfigType }) => {
  Object.assign(config.ai, newConfig.ai)
}

const saveConfig = () => {
  // 保存配置到localStorage或发送到后端
  localStorage.setItem('unified_config', JSON.stringify(config))
  emit('close')
}

// 初始化时从localStorage加载配置
const loadConfig = () => {
  const saved = localStorage.getItem('unified_config')
  if (saved) {
    try {
      const savedConfig = JSON.parse(saved)
      Object.assign(config, savedConfig)
    } 
    catch (e) {
      // 忽略解析错误，使用默认配置
    }
  }
}

// 组件挂载时加载配置
loadConfig()
</script>

<style scoped>
.unified-config {
  width: 900px;
  height: 600px;
  background: white;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e1e5e9;
  background: #f8f9fa;
}

.config-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #dc3545;
  color: white;
}

.config-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 200px;
  background: #f8f9fa;
  border-right: 1px solid #e1e5e9;
  padding: 0;
}

.tabs {
  display: flex;
  flex-direction: column;
}

.tab {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #e9ecef;
}

.tab:hover {
  background: #e9ecef;
}

.tab.active {
  background: #007bff;
  color: white;
}

.tab-icon {
  font-size: 18px;
  min-width: 18px;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.tab-content h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #007bff;
  padding-bottom: 10px;
}

.config-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e1e5e9;
  background: #f8f9fa;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

/* 修复组件内部样式 */
.ai-config-wrapper {
  :deep(.ai-form-group input) {
    max-width: 300px !important;
    min-width: 200px !important;
    width: 100% !important;
  }
  
  :deep(.ai-form-group input[type="password"]) {
    max-width: 280px !important;
  }
  
  /* 强化AI标签显示 */
  :deep(.ai-tabs) {
    display: flex !important;
    gap: 10px !important;
    margin-bottom: 20px !important;
    border-bottom: 2px solid #e1e5e9 !important;
    padding-bottom: 10px !important;
  }
  
  :deep(.tab-btn) {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 12px 20px !important;
    border: 2px solid transparent !important;
    background: #f8f9fa !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    color: #495057 !important;
    font-weight: 500 !important;
    min-width: 120px !important;
    justify-content: center !important;
    
    &:hover:not(.active) {
      border-color: #007bff !important;
      background: #e3f2fd !important;
      color: #007bff !important;
      transform: translateY(-1px) !important;
    }
    
    &.active {
      border-color: #28a745 !important;
      background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
      color: #155724 !important;
      font-weight: 600 !important;
    }
    
    /* 确保图标显示 */
    span:first-child {
      font-size: 16px !important;
      margin-right: 4px !important;
    }
  }
  
  /* 修复表单网格 */
  :deep(.ai-form-grid) {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)) !important;
    gap: 20px !important;
    margin-top: 20px !important;
  }
  
  :deep(.ai-form-group) {
    margin-bottom: 16px !important;
    
    label {
      display: block !important;
      margin-bottom: 8px !important;
      font-weight: 600 !important;
      color: #2c3e50 !important;
      font-size: 14px !important;
    }
    
    input, select {
      width: 100% !important;
      max-width: 300px !important;
      padding: 10px 12px !important;
      border: 2px solid #e1e5e9 !important;
      border-radius: 6px !important;
      font-size: 14px !important;
      background: white !important;
      color: #495057 !important;
      transition: all 0.3s ease !important;
      
      &:hover {
        border-color: #007bff !important;
      }
      
      &:focus {
        border-color: #007bff !important;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
        outline: none !important;
      }
    }
  }
}

.tab-content {
  /* 修复所有下拉框样式 */
  :deep(select) {
    background: white !important;
    color: #495057 !important;
    border: 2px solid #ced4da !important;
    border-radius: 6px !important;
    padding: 10px 12px !important;
    font-size: 14px !important;
    
    option {
      background: white !important;
      color: #495057 !important;
      padding: 10px !important;
      border: none !important;
    }
    
    /* 修复hover和focus状态 */
    &:hover {
      border-color: #007bff !important;
    }
    
    &:focus {
      border-color: #007bff !important;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
      outline: none !important;
    }
  }
  
  :deep(.modern-select) {
    background: white !important;
    color: #495057 !important;
    border: 2px solid #ced4da !important;
    
    option {
      background: white !important;
      color: #495057 !important;
      padding: 10px !important;
    }
    
    &:hover {
      border-color: #007bff !important;
    }
    
    &:focus {
      border-color: #007bff !important;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
    }
  }
  
  /* 修复引擎卡片显示 */
  :deep(.engine-cards) {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)) !important;
    gap: 15px !important;
  }
  
  :deep(.engine-card) {
    display: flex !important;
    align-items: center !important;
    gap: 15px !important;
    padding: 20px !important;
    background: white !important;
    border: 2px solid #e1e5e9 !important;
    border-radius: 12px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    
    &.active {
      border-color: #28a745 !important;
      background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
    }
    
    &:hover:not(.active) {
      border-color: #007bff !important;
      background: #f8f9ff !important;
      transform: translateY(-2px) !important;
    }
  }
}
</style>
