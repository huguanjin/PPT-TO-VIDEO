<template>
  <div class="unified-config">
    <div class="config-header">
      <div class="header-left">
        <h2 class="title">
          <Format class="title-icon" />
          项目配置中心
        </h2>
        <p class="subtitle">统一管理所有导出配置，打造完美的视频内容</p>
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
          <!-- 视频设置 -->
          <VideoConfigPanel 
            v-if="activeTab === 'video'" 
            :config="videoConfig"
            @update:config="videoConfig = $event"
          />
          
          <!-- 字幕设置 -->
          <SubtitleConfigPanel 
            v-else-if="activeTab === 'subtitle'" 
            :config="subtitleConfig"
            @update:config="subtitleConfig = $event"
          />
          
          <!-- 语音合成设置 -->
          <TTSConfigPanel 
            v-else-if="activeTab === 'tts'" 
            :config="ttsConfig"
            @update:config="ttsConfig = $event"
          />
          
          <!-- AI配置 -->
          <AIConfigPanel 
            v-else-if="activeTab === 'ai'" 
            :config="aiConfig"
            @update:config="aiConfig = $event"
          />
          
          <!-- API测试 -->
          <div v-else-if="activeTab === 'api-test'" class="api-test-panel">
            <div class="panel-header">
              <h3>🧪 API服务连接测试</h3>
              <p>测试前端与后端API服务的连接状态</p>
            </div>
            
            <div class="test-section">
              <h4>📊 服务状态检查</h4>
              <div class="status-grid">
                <div class="status-card" :class="{ 'healthy': healthStatus.primary, 'unhealthy': !healthStatus.primary }">
                  <div class="status-header">
                    <span class="status-label">主API服务 (8004)</span>
                    <span class="status-indicator">{{ healthStatus.primary ? '✅' : '❌' }}</span>
                  </div>
                  <div class="status-detail">
                    {{ healthStatus.primary ? '服务正常运行' : '服务无法连接' }}
                  </div>
                </div>
                
                <div class="status-card" :class="{ 'healthy': healthStatus.fallback, 'unhealthy': !healthStatus.fallback }">
                  <div class="status-header">
                    <span class="status-label">备用API服务 (5000)</span>
                    <span class="status-indicator">{{ healthStatus.fallback ? '✅' : '❌' }}</span>
                  </div>
                  <div class="status-detail">
                    {{ healthStatus.fallback ? '服务正常运行' : '服务无法连接' }}
                  </div>
                </div>
              </div>
              
              <div class="test-actions">
                <button class="test-btn" @click="checkApiHealth" :disabled="isChecking">
                  {{ isChecking ? '检查中...' : '重新检查' }}
                </button>
                <button class="test-btn" @click="testApiCalls" :disabled="isTesting">
                  {{ isTesting ? '测试中...' : '测试API调用' }}
                </button>
              </div>
            </div>
            
            <div class="test-results" v-if="testResults.length > 0">
              <h4>📝 测试日志</h4>
              <div class="results-container">
                <div v-for="(result, index) in testResults.slice(0, 5)" :key="index" 
                     :class="['result-item', result.type]">
                  <div class="result-time">{{ result.time }}</div>
                  <div class="result-title">{{ result.title }}</div>
                  <div class="result-content">{{ result.content }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="config-actions">
          <button class="action-btn secondary" @click="$emit('close')">
            取消
          </button>
          <button class="action-btn primary" @click="saveAndClose">
            <CheckOne class="btn-icon" />
            保存配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  Format, 
  Close, 
  VideoTwo, 
  Text, 
  VolumeNotice, 
  Magic,
  CheckOne,
  ApiApp
} from '@icon-park/vue-next'

// 导入组件
import VideoConfigPanel from '@/components/VideoConfigPanel.vue'
import SubtitleConfigPanel from '@/components/SubtitleConfigPanel.vue'
import TTSConfigPanel from '@/components/TTSConfigPanel.vue'
import AIConfigPanel from '@/components/AIConfigPanel.vue'

// 导入API服务
import { checkApiHealth as checkHealth, smartApiCall } from '@/api/index'
import { aiService } from '@/api/services'

const emit = defineEmits<{
  close: []
}>()

const activeTab = ref('video')

const tabs = [
  { id: 'video', label: '视频设置', icon: VideoTwo },
  { id: 'subtitle', label: '字幕设置', icon: Text },
  { id: 'tts', label: '语音合成', icon: VolumeNotice },
  { id: 'ai', label: 'AI配置', icon: Magic },
  { id: 'api-test', label: 'API测试', icon: ApiApp }
]

const videoConfig = ref({
  resolution: '1920x1080',
  fps: 30,
  quality: 'high'
})

const subtitleConfig = ref({
  fontSize: 24,
  color: '#ffffff',
  position: 'bottom'
})

const ttsConfig = ref({
  service: 'edge',
  voice: 'zh-CN-XiaoxiaoNeural',
  speed: 1.0
})

const aiConfig = ref({
  openai: {
    apiKey: '',
    enabled: false
  },
  anthropic: {
    apiKey: '',
    enabled: false
  },
  custom: {
    apiKey: '',
    baseUrl: '',
    model: '',
    enabled: false
  }
})

// API测试相关状态
const healthStatus = ref({
  primary: false,
  fallback: false
})

const isChecking = ref(false)
const isTesting = ref(false)
const testResults = ref<Array<{
  title: string
  content: string
  type: 'success' | 'error' | 'info'
  time: string
}>>([])

// 添加测试结果
const addTestResult = (title: string, content: string, type: 'success' | 'error' | 'info' = 'info') => {
  testResults.value.unshift({
    title,
    content,
    type,
    time: new Date().toLocaleTimeString()
  })
  
  // 保持最多10条记录
  if (testResults.value.length > 10) {
    testResults.value.pop()
  }
}

// 检查API健康状态
const checkApiHealth = async () => {
  isChecking.value = true
  addTestResult('健康检查', '开始检查API服务状态...', 'info')
  
  try {
    // 使用API服务检查健康状态
    const health = await checkHealth()
    
    healthStatus.value.primary = health.primary
    healthStatus.value.fallback = health.fallback
    
    if (health.primary) {
      addTestResult('主API服务 (8004)', '状态正常', 'success')
    }
    else {
      addTestResult('主API服务 (8004)', '连接失败', 'error')
    }
    
    if (health.fallback) {
      addTestResult('备用API服务 (5000)', '状态正常', 'success')
    }
    else {
      addTestResult('备用API服务 (5000)', '连接失败', 'error')
    }
    
  }
  catch (error: any) {
    addTestResult('健康检查失败', error.message, 'error')
  }
  finally {
    isChecking.value = false
  }
}

// 测试API调用
const testApiCalls = async () => {
  isTesting.value = true
  addTestResult('API调用测试', '开始测试各个API端点...', 'info')
  
  try {
    // 测试配置API
    try {
      const configData = await smartApiCall(api => 
        api.get('/api/config/presets')
      )
      addTestResult('配置API测试', `获取预设配置成功，共 ${Object.keys(configData.data || {}).length} 个预设`, 'success')
    }
    catch (error: any) {
      addTestResult('配置API测试', `调用失败: ${error.message}`, 'error')
    }
    
    // 测试版本API
    try {
      const versionData = await smartApiCall(api => 
        api.get('/api/version')
      )
      addTestResult('版本API测试', `服务版本: ${versionData.data?.version || '未知'}`, 'success')
    }
    catch (error: any) {
      addTestResult('版本API测试', `调用失败: ${error.message}`, 'error')
    }
    
  }
  catch (error: any) {
    addTestResult('API调用异常', `测试失败: ${error.message}`, 'error')
  }
  finally {
    isTesting.value = false
  }
}

// 组件挂载时自动检查API健康状态
onMounted(() => {
  checkApiHealth()
})

const saveAndClose = async () => {
  try {
    // 保存到localStorage
    localStorage.setItem('projectConfig', JSON.stringify({
      video: videoConfig.value,
      subtitle: subtitleConfig.value,
      tts: ttsConfig.value,
      ai: aiConfig.value
    }))
    
    // 保存AI配置到后端
    if (activeTab.value === 'ai') {
      await saveAIConfigToBackend()
    }
    
    // 关闭配置面板
    emit('close')
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('保存配置失败:', error)
  }
}

const saveAIConfigToBackend = async () => {
  try {
    // 确定默认提供商
    const defaultProvider = aiConfig.value.openai.enabled ? 'openai' as const :
      aiConfig.value.anthropic.enabled ? 'anthropic' as const :
        aiConfig.value.custom.enabled ? 'custom' as const : 'openai' as const
    
    // 使用AI服务更新配置
    const apiConfig = {
      openai: {
        apiKey: aiConfig.value.openai.apiKey,
        baseUrl: 'https://api.openai.com/v1',
        model: 'gpt-3.5-turbo',
        enabled: aiConfig.value.openai.enabled
      },
      anthropic: {
        apiKey: aiConfig.value.anthropic.apiKey,
        baseUrl: 'https://api.anthropic.com',
        model: 'claude-3-haiku-20240307',
        enabled: aiConfig.value.anthropic.enabled
      },
      custom: {
        apiKey: aiConfig.value.custom.apiKey,
        baseUrl: aiConfig.value.custom.baseUrl,
        model: aiConfig.value.custom.model,
        enabled: aiConfig.value.custom.enabled
      },
      defaultProvider
    }
    
    await aiService.updateConfig(apiConfig)
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('保存AI配置失败:', error)
    throw new Error('保存AI配置到后端失败')
  }
}
</script>

<style lang="scss" scoped>
.unified-config {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 32px 40px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.header-left {
  flex: 1;
}

.title {
  display: flex;
  align-items: center;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(45deg, #ffffff, #e0e7ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-icon {
  margin-right: 12px;
  font-size: 32px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.subtitle {
  margin: 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  }

  svg {
    font-size: 20px;
  }
}

.config-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.config-sidebar {
  width: 280px;
  background: rgba(0, 0, 0, 0.1);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  padding: 24px 0;
  backdrop-filter: blur(10px);
}

.sidebar-nav {
  padding: 0 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  margin-bottom: 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(4px);
  }

  &.active {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);

    .nav-indicator {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background: linear-gradient(to bottom, #60a5fa, #3b82f6);
      border-radius: 0 2px 2px 0;
    }
  }
}

.nav-icon {
  font-size: 20px;
  margin-right: 12px;
  opacity: 0.9;
}

.nav-text {
  font-size: 15px;
  font-weight: 500;
  opacity: 0.95;
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
  padding: 32px 40px;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 4px;

    &:hover {
      background: rgba(255, 255, 255, 0.4);
    }
  }
}

.config-actions {
  padding: 24px 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}

.action-btn {
  padding: 12px 24px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;

  &.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.2);

    &:hover {
      background: rgba(255, 255, 255, 0.2);
      color: white;
    }
  }

  &.primary {
    background: linear-gradient(45deg, #3b82f6, #1d4ed8);
    color: white;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);

    &:hover {
      background: linear-gradient(45deg, #2563eb, #1e40af);
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
  }

  .btn-icon {
    font-size: 16px;
  }
}

// API测试面板样式
.api-test-panel {
  .panel-header {
    margin-bottom: 24px;
    
    h3 {
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
    }
    
    p {
      margin: 0;
      opacity: 0.8;
      font-size: 14px;
    }
  }
  
  .test-section {
    margin-bottom: 24px;
    
    h4 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 500;
    }
  }
  
  .status-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
  }
  
  .status-card {
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    
    &.healthy {
      border-color: rgba(34, 197, 94, 0.5);
      background: rgba(34, 197, 94, 0.1);
    }
    
    &.unhealthy {
      border-color: rgba(239, 68, 68, 0.5);
      background: rgba(239, 68, 68, 0.1);
    }
  }
  
  .status-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .status-label {
    font-weight: 500;
    font-size: 14px;
  }
  
  .status-indicator {
    font-size: 16px;
  }
  
  .status-detail {
    font-size: 12px;
    opacity: 0.8;
  }
  
  .test-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  
  .test-btn {
    padding: 10px 20px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.2);
      border-color: rgba(255, 255, 255, 0.5);
      transform: translateY(-1px);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }
  }
  
  .test-results {
    .results-container {
      max-height: 300px;
      overflow-y: auto;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      background: rgba(0, 0, 0, 0.2);
    }
    
    .result-item {
      padding: 12px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      &:last-child {
        border-bottom: none;
      }
      
      &.success {
        border-left: 3px solid #22c55e;
      }
      
      &.error {
        border-left: 3px solid #ef4444;
      }
      
      &.info {
        border-left: 3px solid #3b82f6;
      }
    }
    
    .result-time {
      font-size: 11px;
      opacity: 0.6;
      margin-bottom: 4px;
    }
    
    .result-title {
      font-weight: 500;
      font-size: 13px;
      margin-bottom: 4px;
    }
    
    .result-content {
      font-size: 12px;
      opacity: 0.8;
      line-height: 1.4;
    }
  }
}
</style>
