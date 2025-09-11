<template>
  <ResponsiveLayout>
    <template #header>
      <div class="config-header">
        <h1>PPTist 配置中心</h1>
        <div class="header-actions">
          <button 
            class="btn-save"
            @click="saveAllConfigs"
            :disabled="saving"
          >
            <Icon name="save" />
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <button 
            class="btn-test"
            @click="testAllConfigs"
            :disabled="testing"
          >
            <Icon name="play" />
            {{ testing ? '测试中...' : '测试配置' }}
          </button>
        </div>
      </div>
    </template>

    <template #sidebar>
      <nav class="config-nav">
        <h3>配置分类</h3>
        <ul class="nav-list">
          <li 
            v-for="section in configSections" 
            :key="section.key"
            :class="{ active: activeSection === section.key }"
            @click="activeSection = section.key"
          >
            <Icon :name="section.icon" />
            {{ section.title }}
            <span 
              v-if="hasErrors(section.key)"
              class="error-badge"
            >
              !
            </span>
          </li>
        </ul>
      </nav>
    </template>

    <template #main>
      <AnimatedContainer :loading="loading">
        <div class="config-content">
          <!-- AI配置 -->
          <section 
            v-if="activeSection === 'ai'"
            class="config-section"
          >
            <div class="section-header">
              <h2>AI配置</h2>
              <p>配置AI服务提供商和相关参数</p>
            </div>
            
            <div class="config-grid">
              <div class="config-group">
                <label>AI服务提供商</label>
                <select v-model="configs.ai.provider">
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="azure">Azure OpenAI</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>API Key</label>
                <input 
                  type="password"
                  v-model="configs.ai.apiKey"
                  placeholder="输入API密钥"
                >
              </div>
              
              <div class="config-group">
                <label>模型</label>
                <select v-model="configs.ai.model">
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3">Claude 3</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>温度</label>
                <input 
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  v-model="configs.ai.temperature"
                >
                <span>{{ configs.ai.temperature }}</span>
              </div>
            </div>
          </section>

          <!-- TTS配置 -->
          <section 
            v-if="activeSection === 'tts'"
            class="config-section"
          >
            <div class="section-header">
              <h2>语音合成配置</h2>
              <p>配置文本转语音服务</p>
            </div>
            
            <div class="config-grid">
              <div class="config-group">
                <label>TTS服务</label>
                <select v-model="configs.tts.service">
                  <option value="edge">Edge TTS</option>
                  <option value="openai">OpenAI TTS</option>
                  <option value="fish">Fish TTS</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>语音角色</label>
                <select v-model="configs.tts.voice">
                  <option value="zh-CN-XiaoxiaoNeural">晓晓</option>
                  <option value="zh-CN-YunxiNeural">云希</option>
                  <option value="zh-CN-YunyangNeural">云扬</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>语速</label>
                <input 
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  v-model="configs.tts.rate"
                >
                <span>{{ configs.tts.rate }}x</span>
              </div>
              
              <div class="config-group">
                <label>音调</label>
                <input 
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  v-model="configs.tts.pitch"
                >
                <span>{{ configs.tts.pitch }}</span>
              </div>
            </div>
          </section>

          <!-- 视频配置 -->
          <section 
            v-if="activeSection === 'video'"
            class="config-section"
          >
            <div class="section-header">
              <h2>视频配置</h2>
              <p>配置视频输出参数</p>
            </div>
            
            <div class="config-grid">
              <div class="config-group">
                <label>视频分辨率</label>
                <select v-model="configs.video.resolution">
                  <option value="1920x1080">1920x1080 (Full HD)</option>
                  <option value="1280x720">1280x720 (HD)</option>
                  <option value="3840x2160">3840x2160 (4K)</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>帧率</label>
                <select v-model="configs.video.fps">
                  <option value="24">24 FPS</option>
                  <option value="30">30 FPS</option>
                  <option value="60">60 FPS</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>视频格式</label>
                <select v-model="configs.video.format">
                  <option value="mp4">MP4</option>
                  <option value="avi">AVI</option>
                  <option value="mov">MOV</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>质量</label>
                <select v-model="configs.video.quality">
                  <option value="high">高质量</option>
                  <option value="medium">中等质量</option>
                  <option value="low">低质量</option>
                </select>
              </div>
            </div>
          </section>

          <!-- 字幕配置 -->
          <section 
            v-if="activeSection === 'subtitle'"
            class="config-section"
          >
            <div class="section-header">
              <h2>字幕配置</h2>
              <p>配置字幕样式和行为</p>
            </div>
            
            <div class="config-grid">
              <div class="config-group">
                <label>字体</label>
                <select v-model="configs.subtitle.font">
                  <option value="Microsoft YaHei">微软雅黑</option>
                  <option value="SimHei">黑体</option>
                  <option value="SimSun">宋体</option>
                </select>
              </div>
              
              <div class="config-group">
                <label>字体大小</label>
                <input 
                  type="range"
                  min="12"
                  max="48"
                  v-model="configs.subtitle.fontSize"
                >
                <span>{{ configs.subtitle.fontSize }}px</span>
              </div>
              
              <div class="config-group">
                <label>字体颜色</label>
                <input 
                  type="color"
                  v-model="configs.subtitle.color"
                >
              </div>
              
              <div class="config-group">
                <label>背景颜色</label>
                <input 
                  type="color"
                  v-model="configs.subtitle.backgroundColor"
                >
              </div>
              
              <div class="config-group full-width">
                <label>
                  <input 
                    type="checkbox"
                    v-model="configs.subtitle.outline"
                  >
                  启用字体描边
                </label>
              </div>
            </div>
          </section>

          <!-- 高级配置 -->
          <section 
            v-if="activeSection === 'advanced'"
            class="config-section"
          >
            <div class="section-header">
              <h2>高级配置</h2>
              <p>高级功能和性能调优</p>
            </div>
            
            <div class="config-grid">
              <div class="config-group">
                <label>并发处理数</label>
                <input 
                  type="number"
                  min="1"
                  max="10"
                  v-model="configs.advanced.concurrency"
                >
              </div>
              
              <div class="config-group">
                <label>缓存大小 (MB)</label>
                <input 
                  type="number"
                  min="100"
                  max="2048"
                  v-model="configs.advanced.cacheSize"
                >
              </div>
              
              <div class="config-group full-width">
                <label>
                  <input 
                    type="checkbox"
                    v-model="configs.advanced.enableGPU"
                  >
                  启用GPU加速
                </label>
              </div>
              
              <div class="config-group full-width">
                <label>
                  <input 
                    type="checkbox"
                    v-model="configs.advanced.enableCache"
                  >
                  启用智能缓存
                </label>
              </div>
              
              <div class="config-group full-width">
                <label>
                  <input 
                    type="checkbox"
                    v-model="configs.advanced.debugMode"
                  >
                  调试模式
                </label>
              </div>
            </div>
          </section>
        </div>

        <!-- 实时验证结果 -->
        <div 
          v-if="validationResults.length > 0"
          class="validation-panel"
        >
          <h3>配置验证结果</h3>
          <div class="validation-list">
            <div 
              v-for="result in validationResults" 
              :key="result.field"
              class="validation-item"
              :class="result.status"
            >
              <Icon 
                :name="result.status === 'success' ? 'check' : 'alert-triangle'" 
              />
              <span>{{ result.message }}</span>
            </div>
          </div>
        </div>
      </AnimatedContainer>
    </template>
  </ResponsiveLayout>

  <!-- 错误处理 -->
  <ErrorHandler ref="errorHandler" />
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import ResponsiveLayout from '../components/ResponsiveLayout.vue'
import AnimatedContainer from '../components/AnimatedContainer.vue'
import ErrorHandler from '../components/ErrorHandler.vue'

// 配置分类
const configSections = [
  { key: 'ai', title: 'AI配置', icon: 'brain' },
  { key: 'tts', title: '语音合成', icon: 'volume-2' },
  { key: 'video', title: '视频配置', icon: 'video' },
  { key: 'subtitle', title: '字幕配置', icon: 'type' },
  { key: 'advanced', title: '高级配置', icon: 'settings' }
]

// 状态管理
const activeSection = ref('ai')
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

// 配置数据
const configs = reactive({
  ai: {
    provider: 'openai',
    apiKey: '',
    model: 'gpt-4',
    temperature: 0.7
  },
  tts: {
    service: 'edge',
    voice: 'zh-CN-XiaoxiaoNeural',
    rate: 1.0,
    pitch: 1.0
  },
  video: {
    resolution: '1920x1080',
    fps: 30,
    format: 'mp4',
    quality: 'high'
  },
  subtitle: {
    font: 'Microsoft YaHei',
    fontSize: 24,
    color: '#ffffff',
    backgroundColor: '#000000',
    outline: true
  },
  advanced: {
    concurrency: 4,
    cacheSize: 512,
    enableGPU: false,
    enableCache: true,
    debugMode: false
  }
})

// 验证结果
const validationResults = ref<Array<{
  field: string
  status: 'success' | 'error' | 'warning'
  message: string
}>>([])

// 错误处理
const errorHandler = ref()

// 生命周期
onMounted(() => {
  loadConfigs()
})

// 监听配置变化，实时验证
watch(configs, () => {
  validateConfigs()
}, { deep: true })

// 方法定义
async function loadConfigs() {
  loading.value = true
  
  try {
    // 这里应该从API加载配置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟加载配置数据
    // const response = await fetch('/api/config/unified')
    // const data = await response.json()
    // Object.assign(configs, data)
  }
  catch (error) {
    errorHandler.value?.addError({
      type: 'api',
      message: '加载配置失败',
      details: String(error),
      retryable: true
    })
  }
  finally {
    loading.value = false
  }
}

async function saveAllConfigs() {
  saving.value = true
  
  try {
    // 这里应该保存到API
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟保存
    // await fetch('/api/config/unified', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(configs)
    // })
    
    // 显示成功消息
    errorHandler.value?.addError({
      type: 'user',
      message: '配置保存成功！',
      retryable: false
    })
  }
  catch (error) {
    errorHandler.value?.addError({
      type: 'api',
      message: '保存配置失败',
      details: String(error),
      retryable: true
    })
  }
  finally {
    saving.value = false
  }
}

async function testAllConfigs() {
  testing.value = true
  
  try {
    // 这里应该测试所有配置
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    // 模拟测试结果
    validationResults.value = [
      { field: 'ai.apiKey', status: 'success', message: 'AI API密钥验证成功' },
      { field: 'tts.service', status: 'success', message: 'TTS服务连接正常' },
      { field: 'video.resolution', status: 'warning', message: '4K分辨率可能影响性能' }
    ]
  }
  catch (error) {
    errorHandler.value?.addError({
      type: 'api',
      message: '测试配置失败',
      details: String(error),
      retryable: true
    })
  }
  finally {
    testing.value = false
  }
}

function validateConfigs() {
  const results: typeof validationResults.value = []
  
  // AI配置验证
  if (!configs.ai.apiKey) {
    results.push({
      field: 'ai.apiKey',
      status: 'error',
      message: 'AI API密钥不能为空'
    })
  }
  
  // TTS配置验证
  if (configs.tts.rate < 0.5 || configs.tts.rate > 2) {
    results.push({
      field: 'tts.rate',
      status: 'warning',
      message: '语速建议在0.5-2倍之间'
    })
  }
  
  // 视频配置验证
  if (configs.video.resolution === '3840x2160' && configs.video.fps === 60) {
    results.push({
      field: 'video.performance',
      status: 'warning',
      message: '4K 60FPS可能需要大量计算资源'
    })
  }
  
  validationResults.value = results
}

function hasErrors(section: string): boolean {
  return validationResults.value.some(
    result => result.field.startsWith(section) && result.status === 'error'
  )
}
</script>

<style scoped>
.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.config-header h1 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.btn-save {
  background: #3498db;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: #2980b9;
}

.btn-test {
  background: #2ecc71;
  color: white;
}

.btn-test:hover:not(:disabled) {
  background: #27ae60;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.config-nav {
  padding: 20px;
}

.config-nav h3 {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-list li {
  padding: 12px 16px;
  margin: 4px 0;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  transition: all 0.2s;
  position: relative;
}

.nav-list li:hover {
  background: #f8f9fa;
  color: #333;
}

.nav-list li.active {
  background: #3498db;
  color: white;
}

.error-badge {
  position: absolute;
  right: 8px;
  background: #e74c3c;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.config-content {
  padding: 20px;
}

.config-section {
  max-width: 800px;
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  margin: 0 0 8px 0;
  color: #333;
}

.section-header p {
  margin: 0;
  color: #666;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.config-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-group.full-width {
  grid-column: 1 / -1;
}

.config-group label {
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-group input,
.config-group select {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.config-group input:focus,
.config-group select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.config-group input[type="range"] {
  padding: 0;
}

.config-group input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
}

.validation-panel {
  margin-top: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.validation-panel h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.validation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.validation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
}

.validation-item.success {
  background: #d4edda;
  color: #155724;
}

.validation-item.warning {
  background: #fff3cd;
  color: #856404;
}

.validation-item.error {
  background: #f8d7da;
  color: #721c24;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .config-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .config-grid {
    grid-template-columns: 1fr;
  }
}

/* 暗色主题 */
@media (prefers-color-scheme: dark) {
  .config-header {
    border-bottom-color: #444;
  }
  
  .config-header h1 {
    color: #fff;
  }
  
  .config-nav h3 {
    color: #aaa;
  }
  
  .nav-list li {
    color: #aaa;
  }
  
  .nav-list li:hover {
    background: #333;
    color: #fff;
  }
  
  .section-header h2 {
    color: #fff;
  }
  
  .section-header p {
    color: #aaa;
  }
  
  .config-group label {
    color: #fff;
  }
  
  .config-group input,
  .config-group select {
    background: #333;
    border-color: #555;
    color: #fff;
  }
  
  .validation-panel {
    background: #333;
  }
  
  .validation-panel h3 {
    color: #fff;
  }
}
</style>
