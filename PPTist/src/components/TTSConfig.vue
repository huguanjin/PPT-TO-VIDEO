<template>
  <div class="tts-config">
    <div class="config-header">
      <h2>🎙️ 配音设置</h2>
      <p class="config-description">选择您喜欢的配音引擎，并自定义语音参数</p>
      
      <!-- 自动保存状态指示器 -->
      <div v-if="autoSaveStatus || autoSaving" class="auto-save-indicator">
        <div v-if="autoSaving" class="saving">
          <span class="loading-icon">⏳</span>
          <span>正在自动保存...</span>
        </div>
        <div v-else-if="autoSaveStatus" :class="['save-status', autoSaveStatus.type]">
          {{ autoSaveStatus.message }}
        </div>
      </div>
    </div>
    
    <div class="config-content">
      <!-- 配音引擎选择卡片 -->
      <div class="engine-selector">
        <h3>配音引擎</h3>
        <div class="engine-cards">
          <div 
            class="engine-card" 
            :class="{ active: config.preferred_engine === 'edge_tts' }"
            @click="updatePreferredEngine('edge_tts')"
          >
            <div class="engine-icon">🏢</div>
            <div class="engine-info">
              <h4>Edge TTS</h4>
              <p>微软官方语音合成</p>
              <span class="engine-tag">免费</span>
            </div>
          </div>
          <div 
            class="engine-card" 
            :class="{ active: config.preferred_engine === 'fish_tts' }"
            @click="updatePreferredEngine('fish_tts')"
          >
            <div class="engine-icon">🤖</div>
            <div class="engine-info">
              <h4>Fish TTS</h4>
              <p>AI克隆语音技术</p>
              <span class="engine-tag premium">高级</span>
            </div>
          </div>
          <div 
            class="engine-card" 
            :class="{ active: config.preferred_engine === 'azure_tts' }"
            @click="updatePreferredEngine('azure_tts')"
          >
            <div class="engine-icon">☁️</div>
            <div class="engine-info">
              <h4>Azure TTS</h4>
              <p>微软云端语音服务</p>
              <span class="engine-tag">专业</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 配置参数区域 -->
      <div class="params-section">
        <h3>参数配置</h3>
        <div class="params-grid">
          <!-- Edge TTS 配置 -->
          <EdgeTTSConfig 
            v-if="config.preferred_engine === 'edge_tts'"
            :config="{
              edge_voice: config.edge_voice,
              edge_rate: config.edge_rate,
              edge_pitch: config.edge_pitch
            }"
            @update:config="updateEdgeConfig"
          />
          
          <!-- Fish TTS 配置 -->
          <FishTTSConfig 
            v-if="config.preferred_engine === 'fish_tts'"
            :config="{
              fish_api_key: config.fish_api_key,
              fish_character: config.fish_character,
              fish_character_id: config.fish_character_id,
              fish_character_name: config.fish_character_name
            }"
            @update:config="updateFishConfig"
          />
          
          <!-- Azure TTS 配置 -->
          <div v-if="config.preferred_engine === 'azure_tts'" class="azure-tts-config">
            <div class="param-group">
              <label>🔑 API密钥</label>
              <div class="input-wrapper">
                <input 
                  type="password" 
                  v-model="azureApiKey" 
                  placeholder="输入Azure语音服务API密钥" 
                  class="modern-input"
                />
              </div>
            </div>
            <div class="param-group">
              <label>🌍 服务区域</label>
              <div class="select-wrapper">
                <select v-model="azureRegion" class="modern-select">
                  <option value="eastasia">东亚 (香港)</option>
                  <option value="southeastasia">东南亚 (新加坡)</option>
                  <option value="westus">美国西部</option>
                  <option value="eastus">美国东部</option>
                  <option value="westeurope">西欧</option>
                </select>
              </div>
            </div>
            <div class="param-group">
              <label>🎭 语音角色</label>
              <div class="select-wrapper">
                <select v-model="azureVoice" class="modern-select">
                  <option value="zh-CN-XiaoxiaoNeural">晓晓 (女声)</option>
                  <option value="zh-CN-YunxiNeural">云希 (男声)</option>
                  <option value="zh-CN-YunyangNeural">云扬 (男声)</option>
                  <option value="zh-CN-XiaoyiNeural">晓伊 (女声)</option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- 通用配置 -->
          <div class="param-group">
            <label>🎚️ 采样率</label>
            <div class="select-wrapper">
              <select v-model="sampleRate" class="modern-select">
                <option :value="22050">22.05 kHz</option>
                <option :value="44100">44.1 kHz (CD质量)</option>
                <option :value="48000">48 kHz (专业)</option>
              </select>
            </div>
          </div>
          
          <div class="param-group">
            <label>🔄 最大重试次数</label>
            <div class="select-wrapper">
              <select v-model="maxRetries" class="modern-select">
                <option :value="1">1次</option>
                <option :value="3">3次</option>
                <option :value="5">5次</option>
              </select>
            </div>
          </div>
          
          <div class="param-group">
            <label>⏱️ 超时时间</label>
            <div class="select-wrapper">
              <select v-model="timeout" class="modern-select">
                <option :value="30">30秒</option>
                <option :value="60">60秒</option>
                <option :value="120">120秒</option>
              </select>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 试听区域 -->
      <TTSPreview :config="config" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import EdgeTTSConfig from './EdgeTTSConfig.vue'
import FishTTSConfig from './FishTTSConfig.vue'
import TTSPreview from './TTSPreview.vue'
import { apiRequest } from '@/config/api'

interface TTSConfig {
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

const props = defineProps<{
  config: TTSConfig
}>()

const emit = defineEmits<{
  'update:config': [config: TTSConfig]
}>()

// 自动保存状态
const autoSaving = ref(false)
const autoSaveStatus = ref<{type: 'success' | 'error' | 'info', message: string} | null>(null)

// 计算属性
const sampleRate = computed({
  get: () => props.config.sample_rate,
  set: (value) => updateConfig({ sample_rate: value })
})

const maxRetries = computed({
  get: () => props.config.max_retries,
  set: (value) => updateConfig({ max_retries: value })
})

const timeout = computed({
  get: () => props.config.timeout,
  set: (value) => updateConfig({ timeout: value })
})

// Azure TTS 配置
const azureApiKey = computed({
  get: () => props.config.azure_api_key || '',
  set: (value) => updateConfig({ azure_api_key: value })
})

const azureRegion = computed({
  get: () => props.config.azure_region || 'eastasia',
  set: (value) => updateConfig({ azure_region: value })
})

const azureVoice = computed({
  get: () => props.config.azure_voice || 'zh-CN-XiaoxiaoNeural',
  set: (value) => updateConfig({ azure_voice: value })
})

// 更新配置的通用方法
const updateConfig = (updates: Partial<TTSConfig>) => {
  const newConfig = { ...props.config, ...updates }
  emit('update:config', newConfig)
  autoSaveToBackend(newConfig)
}

// 更新首选引擎
const updatePreferredEngine = (engine: string) => {
  updateConfig({ preferred_engine: engine })
}

// 更新Edge TTS配置
const updateEdgeConfig = (edgeConfig: any) => {
  updateConfig(edgeConfig)
}

// 更新Fish TTS配置
const updateFishConfig = (fishConfig: any) => {
  updateConfig(fishConfig)
}

// 自动保存到后端
const autoSaveToBackend = async (newConfig: TTSConfig) => {
  try {
    autoSaving.value = true
    autoSaveStatus.value = {
      type: 'info',
      message: '正在自动保存配置...'
    }

    const getCurrentConfigResponse = await apiRequest('/api/config')

    if (!getCurrentConfigResponse.success) {
      throw new Error(`获取当前配置失败: ${getCurrentConfigResponse.message}`)
    }

    const currentFullConfig = getCurrentConfigResponse.data
    
    const updatedConfig = {
      ...currentFullConfig.config,
      tts: newConfig
    }

    const saveResponse = await apiRequest('/api/config/save', {
      method: 'POST',
      body: JSON.stringify({ config: updatedConfig })
    })

    if (saveResponse.success) {
      autoSaveStatus.value = {
        type: 'success',
        message: '✅ 配置已自动保存'
      }
    } 
    else {
      throw new Error(saveResponse.message || '保存失败')
    }

  } 
  catch (error) {
    autoSaveStatus.value = {
      type: 'error',
      message: `❌ 保存失败: ${error instanceof Error ? error.message : '未知错误'}`
    }
  } 
  finally {
    autoSaving.value = false
    setTimeout(() => {
      autoSaveStatus.value = null
    }, 3000)
  }
}
</script>

<style lang="scss" scoped>
.tts-config {
  padding: 24px;
  background: #f8f9fa;
  border-radius: 12px;
  margin: 20px 0;
}

.config-header {
  text-align: center;
  margin-bottom: 40px;
  
  h2 {
    color: #2c3e50;
    font-size: 2.2em;
    margin-bottom: 10px;
    font-weight: 700;
  }
  
  .config-description {
    color: #7f8c8d;
    font-size: 1.1em;
    margin-bottom: 20px;
  }
}

.auto-save-indicator {
  margin-top: 15px;
  
  .saving {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #3498db;
    font-weight: 500;
    
    .loading-icon {
      animation: spin 1s linear infinite;
    }
  }
  
  .save-status {
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 500;
    display: inline-block;
    
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
    
    &.info {
      background: #d1ecf1;
      color: #0c5460;
      border: 1px solid #bee5eb;
    }
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.engine-selector {
  margin-bottom: 40px;
  
  h3 {
    color: #2c3e50;
    font-size: 1.6em;
    margin-bottom: 20px;
    text-align: center;
  }
}

.engine-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.engine-card {
  background: white;
  border: 3px solid #e1e5e9;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 20px;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
    border-color: #3498db;
  }
  
  &.active {
    border-color: #2ecc71;
    background: linear-gradient(135deg, #a8e6cf 0%, #dcedc1 100%);
    
    .engine-tag {
      background: #2ecc71;
      color: white;
    }
  }
}

.engine-icon {
  font-size: 3em;
  min-width: 60px;
  text-align: center;
}

.engine-info {
  flex: 1;
  
  h4 {
    margin: 0 0 8px 0;
    color: #2c3e50;
    font-size: 1.3em;
    font-weight: 600;
  }
  
  p {
    margin: 0 0 12px 0;
    color: #7f8c8d;
    font-size: 0.95em;
  }
}

.engine-tag {
  display: inline-block;
  padding: 4px 12px;
  background: #95a5a6;
  color: white;
  border-radius: 12px;
  font-size: 0.8em;
  font-weight: 600;
  
  &.premium {
    background: linear-gradient(45deg, #f39c12, #e67e22);
  }
}

.params-section {
  margin-bottom: 40px;
  
  h3 {
    color: #2c3e50;
    font-size: 1.6em;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #ecf0f1;
  }
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.param-group {
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

.azure-tts-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  
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
  
  .input-wrapper {
    position: relative;
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
    
    &::placeholder {
      color: #95a5a6;
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
}
</style>
