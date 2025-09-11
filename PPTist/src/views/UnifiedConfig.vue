<template>
  <div class="unified-config-page">
    <div class="config-header">
      <div class="header-content">
        <div class="title-section">
          <h1><IconFormat /> 项目配置</h1>
          <p>统一配置视频导出、字幕处理和AI服务参数</p>
        </div>
        <button class="close-btn" @click="emit('close')" v-tooltip="'关闭配置'">
          <IconClose />
        </button>
      </div>
    </div>

    <div class="config-body">
      <!-- 左侧导航 -->
      <div class="config-sidebar">
        <div class="nav-menu">
          <div 
            v-for="tab in configTabs" 
            :key="tab.key"
            class="nav-item"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <component :is="tab.icon" class="nav-icon" />
            <span class="nav-text">{{ tab.label }}</span>
            <div class="nav-indicator" v-if="activeTab === tab.key"></div>
          </div>
        </div>
      </div>

      <!-- 右侧内容区 -->
      <div class="config-content">
        <div class="content-header">
          <h2>{{ getCurrentTabInfo().title }}</h2>
          <p class="content-desc">{{ getCurrentTabInfo().description }}</p>
        </div>

        <!-- 视频配置 -->
        <div v-if="activeTab === 'video'" class="config-panel">
          <VideoSettings :config="config" />
        </div>

        <!-- 字幕配置 -->
        <div v-if="activeTab === 'subtitle'" class="config-panel">
          <div class="panel-section">
            <h3><IconText /> 基础字幕设置</h3>
            <SubtitleSettings :config="config" />
          </div>
          
          <div class="panel-section">
            <h3><IconMagic /> 智能字幕处理</h3>
            <SmartSubtitleConfig 
              v-model="smartSubtitleConfig"
              @change="onSmartConfigChange"
            />
          </div>

          <!-- 字幕预览 -->
          <div class="panel-section">
            <h3><IconPreviewOpen /> 实时预览</h3>
            <div class="subtitle-preview-area">
              <div 
                class="subtitle-sample"
                :style="{
                  fontSize: getSubtitlePreviewStyle().fontSize,
                  color: config.subtitle.font_color,
                  backgroundColor: config.subtitle.background_color,
                  fontFamily: config.subtitle.font_family
                }"
              >
                这是字幕预览效果示例 Example Subtitle Preview
              </div>
            </div>
          </div>
        </div>

        <!-- TTS配置 -->
        <div v-if="activeTab === 'tts'" class="config-panel">
          <TTSConfig v-model:config="config.tts" />
        </div>

        <!-- AI配置 -->
        <div v-if="activeTab === 'ai'" class="config-panel">
          <AISettings :config="config" />
        </div>

        <!-- 高级配置 -->
        <div v-if="activeTab === 'advanced'" class="config-panel">
          <div class="panel-section">
            <h3><IconFormat /> 导出设置</h3>
            <div class="form-grid">
              <div class="form-item">
                <label>输出目录</label>
                <div class="input-group">
                  <input type="text" v-model="advancedConfig.outputPath" readonly />
                  <button class="browse-btn" @click="selectOutputPath">浏览</button>
                </div>
              </div>
              <div class="form-item">
                <label>文件命名规则</label>
                <select v-model="advancedConfig.namingRule">
                  <option value="timestamp">时间戳</option>
                  <option value="title">PPT标题</option>
                  <option value="custom">自定义</option>
                </select>
              </div>
              <div class="form-item checkbox-item">
                <label>
                  <input type="checkbox" v-model="advancedConfig.autoCleanTemp" />
                  自动清理临时文件
                </label>
              </div>
              <div class="form-item checkbox-item">
                <label>
                  <input type="checkbox" v-model="advancedConfig.enableProgress" />
                  显示详细进度
                </label>
              </div>
            </div>
          </div>

          <div class="panel-section">
            <h3><IconFormat /> 性能优化</h3>
            <div class="form-grid">
              <div class="form-item">
                <label>最大并发数</label>
                <input type="number" v-model="advancedConfig.maxConcurrency" min="1" max="8" />
              </div>
              <div class="form-item">
                <label>内存限制 (MB)</label>
                <input type="number" v-model="advancedConfig.memoryLimit" min="512" max="4096" step="256" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="config-footer">
      <div class="footer-left">
        <button class="btn btn-outline" @click="resetCurrentTab">
          <IconUndo /> 重置当前
        </button>
        <button class="btn btn-outline" @click="resetAllConfig">
          <IconClear /> 重置全部
        </button>
      </div>
      
      <div class="footer-right">
        <button class="btn btn-outline" @click="previewConfig">
          <IconPreviewOpen /> 预览配置
        </button>
        <button class="btn btn-primary" @click="saveConfig" :disabled="saving">
          <IconDownload />
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>

    <!-- 保存状态提示 -->
    <Transition name="fade">
      <div v-if="saveStatus" class="save-status" :class="saveStatus.type">
        <div class="status-content">
          <component :is="saveStatus.type === 'success' ? 'IconCheckOne' : 'IconCloseOne'" class="status-icon" />
          <span>{{ saveStatus.message }}</span>
        </div>
      </div>
    </Transition>

    <!-- 配置预览弹窗 -->
    <div v-if="showPreview" class="preview-modal" @click="showPreview = false">
      <div class="preview-content" @click.stop>
        <div class="preview-header">
          <h3>配置预览</h3>
          <button @click="showPreview = false">✕</button>
        </div>
        <div class="preview-body">
          <pre>{{ JSON.stringify(config, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiRequest } from '@/config/api'

// 导入组件
import VideoSettings from '@/components/VideoSettings.vue'
import SubtitleSettings from '@/components/SubtitleSettings.vue'
import TTSConfig from '@/components/TTSConfig.vue'
import AISettings from '@/components/AISettings.vue'
import SmartSubtitleConfig from '@/components/SmartSubtitleConfig.vue'

// 导入图标组件 (使用项目现有的图标系统)
// 不需要导入图标，直接在模板中使用 IconXXX 即可

// 定义事件
const emit = defineEmits<{
  close: []
}>()

// 配置标签页
const configTabs = [
  {
    key: 'video',
    label: '视频设置',
    icon: 'IconVideoTwo',
    title: '视频导出配置',
    description: '配置视频分辨率、帧率、比特率等参数'
  },
  {
    key: 'subtitle',
    label: '字幕配置',
    icon: 'IconText',
    title: '字幕生成设置',
    description: '配置字幕样式、智能处理和显示效果'
  },
  {
    key: 'tts',
    label: '语音合成',
    icon: 'IconVolumeNotice',
    title: 'TTS语音配置',
    description: '配置文字转语音引擎和语音参数'
  },
  {
    key: 'ai',
    label: 'AI服务',
    icon: 'IconMagic',
    title: 'AI模型配置',
    description: '配置OpenAI、Claude等AI服务接口'
  },
  {
    key: 'advanced',
    label: '高级设置',
    icon: 'IconFormat',
    title: '高级配置选项',
    description: '导出路径、性能优化和其他高级选项'
  }
]

// 状态管理
const activeTab = ref('video')
const saving = ref(false)
const saveStatus = ref<{type: 'success' | 'error', message: string} | null>(null)
const showPreview = ref(false)

// 智能字幕配置
const smartSubtitleConfig = ref({
  enabled: false,
  useAI: true,
  model: 'gpt-3.5-turbo',
  promptTemplate: '请优化以下字幕内容，使其更加自然流畅：',
  maxLength: 50,
  splitSentences: true
})

// 高级配置
const advancedConfig = ref({
  outputPath: '',
  namingRule: 'timestamp',
  autoCleanTemp: true,
  enableProgress: true,
  maxConcurrency: 4,
  memoryLimit: 2048
})

// 主配置对象（复用之前的结构）
const config = ref({
  video: {
    resolution: '1920x1080',
    fps: 30,
    video_bitrate: '2000k',
    background_color: '#ffffff',
    include_subtitles: true
  },
  subtitle: {
    enabled: true,
    font_family: '微软雅黑',
    font_size: 24,
    font_color: '#ffffff',
    background_color: '#000000',
    position: 'bottom',
    use_enhanced_mode: false,
    enable_precise_alignment: false,
    enable_gap_filling: false,
    max_chars_per_line: 40,
    auto_punctuation_removal: false
  },
  tts: {
    preferred_engine: 'edge_tts',
    edge_voice: 'zh-CN-XiaoxiaoNeural',
    edge_rate: '+0%',
    edge_pitch: '+0Hz',
    fish_api_key: '',
    fish_character: 'default',
    fish_character_id: '',
    fish_character_name: 'Default',
    openai_api_key: '',
    openai_voice: 'alloy',
    azure_api_key: '',
    azure_region: '',
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
      support_json: true
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
      support_json: true
    },
    default_service: 'openai',
    source_language: '中文',
    target_language: '中文',
    max_workers: 4
  },
  ai_content_optimization: {
    enabled: true,
    max_segment_length: 100,
    min_segment_length: 10,
    preserve_meaning: true,
    natural_breaks: true,
    fallback_to_original: false
  }
})

// 计算属性
const getCurrentTabInfo = () => {
  return configTabs.find(tab => tab.key === activeTab.value) || configTabs[0]
}

const getSubtitlePreviewStyle = () => {
  const sizeMap = {
    12: '12px',
    18: '18px',
    24: '24px',
    30: '30px',
    36: '36px'
  }
  return {
    fontSize: sizeMap[config.value.subtitle.font_size as keyof typeof sizeMap] || '24px'
  }
}

// 方法
const loadConfig = async () => {
  try {
    const response = await apiRequest('/api/config')
    if (response.success && response.data?.config) {
      const data = response.data.config
      // 合并配置
      Object.assign(config.value, data)
    }
  } 
  catch (error) {
    // 加载失败，使用默认配置
  }
}

const saveConfig = async () => {
  saving.value = true
  saveStatus.value = null

  try {
    const fullConfig = {
      ...config.value,
      smart_subtitle: smartSubtitleConfig.value,
      advanced: advancedConfig.value
    }

    const response = await apiRequest('/api/config', {
      method: 'POST',
      body: JSON.stringify({ config: fullConfig }),
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

const resetCurrentTab = () => {
  // eslint-disable-next-line no-alert
  if (confirm(`确定要重置${getCurrentTabInfo().label}的配置吗？`)) {
    // 根据当前标签页重置对应配置
    // 实现重置逻辑...
  }
}

const resetAllConfig = () => {
  // eslint-disable-next-line no-alert
  if (confirm('确定要重置所有配置到默认值吗？此操作不可撤销。')) {
    // 重置所有配置到默认值
    location.reload()
  }
}

const previewConfig = () => {
  showPreview.value = true
}

const selectOutputPath = () => {
  // 实现文件夹选择逻辑
  // 在实际应用中可能需要调用文件系统API
}

const onSmartConfigChange = (newConfig: any) => {
  smartSubtitleConfig.value = newConfig
}

// 生命周期
onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.unified-config-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.config-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 30px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1400px;
    margin: 0 auto;
  }
  
  .title-section {
    h1 {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0 0 8px 0;
      font-size: 2rem;
      font-weight: 600;
    }
    
    p {
      margin: 0;
      opacity: 0.9;
      font-size: 1.1rem;
    }
  }
  
  .close-btn {
    padding: 8px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
    transition: background 0.3s ease;
    
    &:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  }
}

.config-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.config-sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e5e7eb;
  padding: 30px 0;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
  
  .nav-menu {
    padding: 0 20px;
  }
  
  .nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    margin-bottom: 8px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    
    &:hover {
      background: #f8fafc;
    }
    
    &.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      transform: translateX(8px);
      
      .nav-indicator {
        position: absolute;
        left: -20px;
        width: 4px;
        height: 100%;
        background: #667eea;
        border-radius: 2px;
      }
    }
    
    .nav-icon {
      font-size: 18px;
      width: 20px;
      height: 20px;
    }
    
    .nav-text {
      font-weight: 500;
      font-size: 15px;
    }
  }
}

.config-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  background: white;
  margin: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.content-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f1f3f4;
  
  h2 {
    margin: 0 0 8px 0;
    font-size: 1.8rem;
    color: #1a202c;
    font-weight: 600;
  }
  
  .content-desc {
    margin: 0;
    color: #718096;
    font-size: 1.1rem;
  }
}

.config-panel {
  .panel-section {
    margin-bottom: 40px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 20px 0;
      color: #2d3748;
      font-size: 1.3rem;
      font-weight: 600;
      padding-bottom: 12px;
      border-bottom: 1px solid #e2e8f0;
    }
  }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  
  label {
    font-weight: 500;
    color: #374151;
    font-size: 14px;
  }
  
  input, select {
    padding: 12px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.3s ease;
    
    &:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
  }
  
  &.checkbox-item {
    flex-direction: row;
    align-items: center;
    
    label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }
  }
}

.input-group {
  display: flex;
  gap: 8px;
  
  input {
    flex: 1;
  }
  
  .browse-btn {
    padding: 12px 16px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.3s ease;
    
    &:hover {
      background: #5a67d8;
    }
  }
}

.subtitle-preview-area {
  background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  
  .subtitle-sample {
    display: inline-block;
    padding: 12px 24px;
    border-radius: 6px;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
  }
}

.config-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: white;
  border-top: 1px solid #e5e7eb;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.05);
  
  .footer-left,
  .footer-right {
    display: flex;
    gap: 12px;
  }
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &.btn-outline {
    background: white;
    color: #667eea;
    border: 2px solid #667eea;
    
    &:hover {
      background: #667eea;
      color: white;
    }
  }
  
  &.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }
  }
}

.save-status {
  position: fixed;
  top: 30px;
  right: 30px;
  padding: 16px 24px;
  border-radius: 12px;
  font-weight: 500;
  z-index: 1000;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  
  .status-content {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  &.success {
    background: rgba(72, 187, 120, 0.9);
    color: white;
  }
  
  &.error {
    background: rgba(245, 101, 101, 0.9);
    color: white;
  }
}

.preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  
  .preview-content {
    background: white;
    border-radius: 16px;
    width: 90%;
    max-width: 800px;
    max-height: 80%;
    overflow: hidden;
    
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px;
      border-bottom: 1px solid #e5e7eb;
    }
    
    .preview-body {
      padding: 20px;
      overflow-y: auto;
      max-height: 600px;
      
      pre {
        background: #f8f9fa;
        padding: 16px;
        border-radius: 8px;
        overflow-x: auto;
        font-size: 12px;
        line-height: 1.5;
      }
    }
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

// 响应式设计
@media (max-width: 1024px) {
  .config-sidebar {
    width: 240px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .unified-config-page {
    .config-body {
      flex-direction: column;
    }
    
    .config-sidebar {
      width: 100%;
      
      .nav-menu {
        display: flex;
        overflow-x: auto;
        gap: 8px;
        padding: 20px;
      }
      
      .nav-item {
        flex-shrink: 0;
        margin-bottom: 0;
      }
    }
  }
  
  .config-footer {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
