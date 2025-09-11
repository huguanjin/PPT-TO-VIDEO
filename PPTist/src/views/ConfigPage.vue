<!-- 配置管理页面 -->
<template>
  <div class="config-page">
    <!-- 顶部导航 -->
    <div class="config-header">
      <h1>视频导出配置</h1>
      <div class="header-actions">
        <button @click="loadConfig" class="btn-secondary">刷新配置</button>
        <button @click="saveConfig" class="btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
        <button @click="saveAndExport" class="btn-success" :disabled="saving">
          保存并导出
        </button>
        <button @click="closeConfig" class="btn-secondary">关闭</button>
      </div>
    </div>

    <!-- 配置内容 -->
    <div class="config-content">
      <!-- 视频配置 -->
      <div class="config-section">
        <h2>视频设置</h2>
        <div class="config-grid">
          <div class="form-group">
            <label>分辨率</label>
            <select v-model="config.video.resolution">
              <option value="1920x1080">1920x1080 (Full HD)</option>
              <option value="1280x720">1280x720 (HD)</option>
              <option value="3840x2160">3840x2160 (4K)</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>帧率 (FPS)</label>
            <select v-model.number="config.video.fps">
              <option :value="24">24 FPS</option>
              <option :value="30">30 FPS</option>
              <option :value="60">60 FPS</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>视频码率</label>
            <select v-model="config.video.video_bitrate">
              <option value="1000k">1000k (标清)</option>
              <option value="2000k">2000k (高清)</option>
              <option value="4000k">4000k (超清)</option>
              <option value="8000k">8000k (4K)</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>背景颜色</label>
            <input type="color" v-model="config.video.background_color">
          </div>
        </div>
      </div>

      <!-- AI大模型配置 -->
      <div class="config-section">
        <h2>AI大模型配置</h2>
        <div class="ai-service-tabs">
          <button 
            v-for="service in aiServices" 
            :key="service.key"
            @click="currentAIService = service.key"
            :class="['tab-btn', { active: currentAIService === service.key }]"
          >
            {{ service.name }}
          </button>
        </div>

        <!-- OpenAI配置 -->
        <div v-if="currentAIService === 'openai'" class="ai-config">
          <div class="config-grid">
            <div class="form-group">
              <label>API密钥</label>
              <input 
                type="password" 
                v-model="config.ai.openai.api_key" 
                placeholder="请输入OpenAI API Key"
                class="input-password"
              >
              <small class="help-text">获取地址：https://platform.openai.com/account/api-keys</small>
            </div>
            
            <div class="form-group">
              <label>API地址</label>
              <input 
                type="url" 
                v-model="config.ai.openai.base_url" 
                placeholder="https://api.openai.com"
                class="input-url"
              >
              <small class="help-text">支持自定义API代理地址</small>
            </div>
            
            <div class="form-group">
              <label>模型名称</label>
              <select v-model="config.ai.openai.model">
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
              </select>
            </div>

            <div class="form-group">
              <label>超时时间 (秒)</label>
              <input type="number" v-model.number="config.ai.openai.timeout" min="30" max="600">
            </div>

            <div class="form-group">
              <label>最大重试次数</label>
              <input type="number" v-model.number="config.ai.openai.max_retries" min="1" max="10">
            </div>
          </div>
        </div>

        <!-- Anthropic配置 -->
        <div v-if="currentAIService === 'anthropic'" class="ai-config">
          <div class="config-grid">
            <div class="form-group">
              <label>API密钥</label>
              <input 
                type="password" 
                v-model="config.ai.anthropic.api_key" 
                placeholder="请输入Anthropic API Key"
                class="input-password"
              >
              <small class="help-text">获取地址：https://console.anthropic.com/</small>
            </div>
            
            <div class="form-group">
              <label>API地址</label>
              <input 
                type="url" 
                v-model="config.ai.anthropic.base_url" 
                placeholder="https://api.anthropic.com"
                class="input-url"
              >
            </div>
            
            <div class="form-group">
              <label>模型名称</label>
              <select v-model="config.ai.anthropic.model">
                <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                <option value="claude-3-opus-20240229">Claude 3 Opus</option>
              </select>
            </div>

            <div class="form-group">
              <label>超时时间 (秒)</label>
              <input type="number" v-model.number="config.ai.anthropic.timeout" min="30" max="600">
            </div>

            <div class="form-group">
              <label>最大重试次数</label>
              <input type="number" v-model.number="config.ai.anthropic.max_retries" min="1" max="10">
            </div>
          </div>
        </div>

        <!-- 自定义API配置 -->
        <div v-if="currentAIService === 'custom'" class="ai-config">
          <div class="config-grid">
            <div class="form-group">
              <label>API密钥</label>
              <input 
                type="password" 
                v-model="config.ai.custom.api_key" 
                placeholder="请输入API Key"
                class="input-password"
              >
            </div>
            
            <div class="form-group">
              <label>API地址</label>
              <input 
                type="url" 
                v-model="config.ai.custom.base_url" 
                placeholder="https://your-api.com/v1"
                class="input-url"
                required
              >
              <small class="help-text">请确保API兼容OpenAI接口格式</small>
            </div>
            
            <div class="form-group">
              <label>模型名称</label>
              <input 
                type="text" 
                v-model="config.ai.custom.model" 
                placeholder="请输入模型名称"
                class="input-text"
                required
              >
              <small class="help-text">请输入服务商提供的模型名称</small>
            </div>

            <div class="form-group">
              <label>超时时间 (秒)</label>
              <input type="number" v-model.number="config.ai.custom.timeout" min="30" max="600">
            </div>

            <div class="form-group">
              <label>最大重试次数</label>
              <input type="number" v-model.number="config.ai.custom.max_retries" min="1" max="10">
            </div>

            <div class="form-group checkbox-group">
              <label>
                <input type="checkbox" v-model="config.ai.custom.support_json">
                支持JSON格式响应
              </label>
            </div>
          </div>
        </div>

        <!-- AI通用设置 -->
        <div class="ai-general-config">
          <h3>通用设置</h3>
          <div class="config-grid">
            <div class="form-group">
              <label>默认AI服务</label>
              <select v-model="config.ai.default_service">
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="custom">自定义API</option>
              </select>
            </div>

            <div class="form-group">
              <label>源语言</label>
              <select v-model="config.ai.source_language">
                <option value="中文">中文</option>
                <option value="English">English</option>
                <option value="日本語">日本語</option>
                <option value="한국어">한국어</option>
              </select>
            </div>

            <div class="form-group">
              <label>目标语言</label>
              <select v-model="config.ai.target_language">
                <option value="中文">中文</option>
                <option value="English">English</option>
                <option value="日本語">日本語</option>
                <option value="한국어">한국어</option>
              </select>
            </div>

            <div class="form-group">
              <label>并发线程数</label>
              <input type="number" v-model.number="config.ai.max_workers" min="1" max="10">
              <small class="help-text">同时处理的AI请求数量</small>
            </div>
          </div>

          <!-- AI功能测试 -->
          <div class="ai-test-section">
            <h4>连接测试</h4>
            <div class="test-controls">
              <button @click="testAIConnection" class="btn-test" :disabled="testing">
                {{ testing ? '测试中...' : '测试AI连接' }}
              </button>
              <span v-if="testResult" :class="['test-result', testResult.success ? 'success' : 'error']">
                {{ testResult.message }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- TTS语音设置 -->
      <div class="config-section">
        <h2>语音合成设置</h2>
        <div class="config-tabs">
          <button 
            v-for="engine in ttsEngines" 
            :key="engine.key"
            @click="currentTTSEngine = engine.key"
            :class="['tab-btn', { active: currentTTSEngine === engine.key }]"
          >
            {{ engine.name }}
          </button>
        </div>
        
        <!-- Edge TTS设置 -->
        <div v-if="currentTTSEngine === 'edge'" class="tts-config">
          <div class="config-grid">
            <div class="form-group">
              <label>语音模型</label>
              <select v-model="config.tts.edge_voice">
                <option value="zh-CN-XiaoxiaoNeural">晓晓 (女声)</option>
                <option value="zh-CN-YunyangNeural">云扬 (男声)</option>
                <option value="zh-CN-XiaoyiNeural">晓伊 (女声)</option>
                <option value="zh-CN-YunjianNeural">云健 (男声)</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>语速</label>
              <select v-model="config.tts.edge_rate">
                <option value="slow">慢速</option>
                <option value="medium">正常</option>
                <option value="fast">快速</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>音调</label>
              <select v-model="config.tts.edge_pitch">
                <option value="low">低音调</option>
                <option value="medium">正常</option>
                <option value="high">高音调</option>
              </select>
            </div>
          </div>
        </div>

        <!-- OpenAI TTS设置 -->
        <div v-if="currentTTSEngine === 'openai'" class="tts-config">
          <div class="config-grid">
            <div class="form-group">
              <label>API密钥状态</label>
              <div class="api-status">
                <span v-if="config.ai.openai.api_key" class="status-good">✅ 已配置</span>
                <span v-else class="status-warning">⚠️ 需要在AI大模型配置中设置OpenAI API密钥</span>
              </div>
            </div>
            
            <div class="form-group">
              <label>语音模型</label>
              <select v-model="config.tts.openai_model">
                <option value="tts-1">TTS-1 (标准)</option>
                <option value="tts-1-hd">TTS-1-HD (高清)</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>语音角色</label>
              <select v-model="config.tts.openai_voice">
                <option value="alloy">Alloy (中性)</option>
                <option value="echo">Echo (男性)</option>
                <option value="fable">Fable (英音)</option>
                <option value="onyx">Onyx (男性)</option>
                <option value="nova">Nova (女性)</option>
                <option value="shimmer">Shimmer (女性)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Fish TTS设置 -->
        <div v-if="currentTTSEngine === 'fish'" class="tts-config">
          <div class="config-grid">
            <div class="form-group">
              <label>Fish TTS API密钥</label>
              <input type="password" v-model="config.tts.fish_api_key" placeholder="输入Fish TTS API密钥">
            </div>
            
            <div class="form-group">
              <label>角色ID</label>
              <input type="text" v-model="config.tts.fish_character_id" placeholder="输入角色ID">
            </div>
            
            <div class="form-group">
              <label>角色名称</label>
              <input type="text" v-model="config.tts.fish_character_name" placeholder="输入角色名称">
            </div>
          </div>
        </div>

        <!-- 通用TTS设置 -->
        <div class="config-grid">
          <div class="form-group">
            <label>采样率</label>
            <select v-model.number="config.tts.sample_rate">
              <option :value="16000">16000 Hz</option>
              <option :value="22050">22050 Hz</option>
              <option :value="44100">44100 Hz</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>最大重试次数</label>
            <input type="number" v-model.number="config.tts.max_retries" min="1" max="10">
          </div>
          
          <div class="form-group">
            <label>超时时间 (秒)</label>
            <input type="number" v-model.number="config.tts.timeout" min="5" max="120">
          </div>
        </div>
      </div>

      <!-- 字幕设置 -->
      <div class="config-section">
        <h2>字幕设置</h2>
        <div class="config-grid">
          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="config.video.include_subtitles">
              视频中包含字幕
            </label>
          </div>
          
          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="config.subtitle.enabled">
              启用字幕文件生成
            </label>
          </div>
          
          <div class="form-group">
            <label>字体</label>
            <select v-model="config.subtitle.font_family">
              <option value="微软雅黑">微软雅黑</option>
              <option value="宋体">宋体</option>
              <option value="黑体">黑体</option>
              <option value="Arial">Arial</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>字体大小</label>
            <input type="number" v-model.number="config.subtitle.font_size" min="12" max="72">
          </div>
          
          <div class="form-group">
            <label>字体颜色</label>
            <input type="color" v-model="config.subtitle.font_color">
          </div>
          
          <div class="form-group">
            <label>背景颜色</label>
            <input type="color" v-model="config.subtitle.background_color">
          </div>
          
          <div class="form-group">
            <label>位置</label>
            <select v-model="config.subtitle.position">
              <option value="bottom">底部</option>
              <option value="top">顶部</option>
              <option value="center">居中</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import message from '@/utils/message'
import { API_BASE_URL } from '@/config/api'

// 事件定义
const emit = defineEmits(['close', 'export'])

// 配置数据
const config = reactive({
  video: {
    resolution: '1920x1080',
    fps: 24,
    video_bitrate: '2000k',
    include_subtitles: true,
    background_color: '#FFFFFF'
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
  tts: {
    edge_voice: 'zh-CN-XiaoxiaoNeural',
    edge_rate: 'medium',
    edge_pitch: 'medium',
    fish_api_key: '',
    fish_character_id: '',
    fish_character_name: '',
    openai_voice: 'alloy',
    openai_model: 'tts-1',
    sample_rate: 22050,
    max_retries: 3,
    timeout: 30.0
  },
  subtitle: {
    font_family: '微软雅黑',
    font_size: 24,
    font_color: '#FFFFFF',
    background_color: '#000000',
    position: 'bottom',
    enabled: true
  }
})

// 状态变量
const saving = ref(false)
const currentTTSEngine = ref('edge')

// AI配置相关状态
const currentAIService = ref('openai')
const testing = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const aiServices = ref([
  { key: 'openai', name: 'OpenAI', icon: '🤖' },
  { key: 'anthropic', name: 'Anthropic (Claude)', icon: '🧠' },
  { key: 'custom', name: '自定义API', icon: '⚙️' }
])

// TTS引擎选项
const ttsEngines = [
  { key: 'edge', name: 'Edge TTS (免费)' },
  { key: 'openai', name: 'OpenAI TTS' },
  { key: 'fish', name: 'Fish TTS' }
]

// 加载配置
const loadConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`)
    const result = await response.json()
    
    if (result.success) {
      Object.assign(config.video, result.config.video)
      Object.assign(config.tts, result.config.tts)
      Object.assign(config.subtitle, result.config.subtitle)
    }
  }
  catch (error) {
    // 忽略错误，避免控制台输出
  }
}

// 保存配置
const saveConfig = async () => {
  if (saving.value) return
  
  saving.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    })
    
    const result = await response.json()
    
    if (result.success) {
      message.success('配置保存成功！')
    }
    else {
      throw new Error(result.message || '保存失败')
    }
  }
  catch (error) {
    message.error('保存配置失败: ' + (error as Error).message)
  }
  finally {
    saving.value = false
  }
}

// 测试AI连接
const testAIConnection = async () => {
  if (testing.value) return
  
  testing.value = true
  testResult.value = null
  
  try {
    const serviceKey = currentAIService.value as 'openai' | 'anthropic' | 'custom'
    const aiConfig = config.ai[serviceKey]
    
    // 检查必填字段
    if (!aiConfig.api_key) {
      testResult.value = {
        success: false,
        message: 'API密钥不能为空'
      }
      return
    }
    
    if (!aiConfig.base_url) {
      testResult.value = {
        success: false,
        message: 'API地址不能为空'
      }
      return
    }
    
    if (!aiConfig.model) {
      testResult.value = {
        success: false,
        message: '模型名称不能为空'
      }
      return
    }
    
    // 发送测试请求
    const response = await fetch(`${API_BASE_URL}/api/ai/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        service: currentAIService.value,
        config: aiConfig
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      testResult.value = {
        success: true,
        message: '连接测试成功！'
      }
    } 
    else {
      testResult.value = {
        success: false,
        message: result.message || '连接测试失败'
      }
    }
  } 
  catch (error) {
    testResult.value = {
      success: false,
      message: '连接测试失败: ' + (error as Error).message
    }
  } 
  finally {
    testing.value = false
  }
}

// 保存并导出
const saveAndExport = async () => {
  await saveConfig()
  if (!saving.value) {
    emit('export')
  }
}

// 关闭配置页面
const closeConfig = () => {
  emit('close')
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.config-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: white;
  border-bottom: 1px solid #ddd;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.config-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-primary, .btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.config-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.config-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.config-section h2 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  color: #333;
  border-bottom: 2px solid #007bff;
  padding-bottom: 0.5rem;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #555;
}

.form-group input,
.form-group select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
}

.checkbox-group input {
  margin-right: 0.5rem;
  width: auto;
}

.config-tabs {
  display: flex;
  margin-bottom: 1rem;
  border-bottom: 1px solid #ddd;
}

.tab-btn {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f8f9fa;
}

.tab-btn.active {
  border-bottom-color: #007bff;
  color: #007bff;
  font-weight: 500;
}

.tts-config {
  margin-top: 1rem;
}

.config-preview {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.config-preview h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #333;
}

.preview-content {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}

.preview-item {
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #555;
}

.preview-item:last-child {
  margin-bottom: 0;
}

.preview-item strong {
  color: #333;
}

/* AI配置样式 */
.ai-config-section { margin-bottom: 30px; }
.ai-config-section h3 { margin-bottom: 20px; color: #2c3e50; font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.ai-tabs { display: flex; gap: 12px; margin-bottom: 20px; border-bottom: 1px solid #e5e7eb; }
.tab-btn { padding: 10px 16px; border: none; background: none; color: #6b7280; cursor: pointer; font-size: 14px; font-weight: 500; border-bottom: 2px solid transparent; transition: all 0.2s ease; display: flex; align-items: center; gap: 6px; }
.tab-btn:hover { color: #4f46e5; background-color: #f8fafc; }
.tab-btn.active { color: #4f46e5; border-bottom-color: #4f46e5; background-color: #f8fafc; }
.ai-config { padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; background-color: #fafafa; margin-bottom: 20px; }
.ai-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.ai-form-group { display: flex; flex-direction: column; gap: 8px; }
.ai-form-group.full-width { grid-column: 1 / -1; }
.ai-form-group label { font-weight: 500; color: #374151; font-size: 14px; }
.ai-form-group input, .ai-form-group select { padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; transition: border-color 0.2s ease, box-shadow 0.2s ease; background-color: white; }
.ai-form-group input:focus, .ai-form-group select:focus { outline: none; border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }
.ai-form-group input[type="password"] { font-family: monospace; }
.ai-actions { display: flex; align-items: center; gap: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb; }
.btn-test { padding: 8px 16px; background-color: #4f46e5; color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background-color 0.2s ease; }
.btn-test:hover:not(:disabled) { background-color: #4338ca; }
.btn-test:disabled { background-color: #9ca3af; cursor: not-allowed; }
.test-result { font-size: 14px; font-weight: 500; padding: 4px 0; }
.test-result.success { color: #059669; }
.test-result.error { color: #dc2626; }
.api-status .status-good { color: #059669; font-weight: 500; }
.api-status .status-warning { color: #d97706; font-weight: 500; }
@media (max-width: 768px) {
  .ai-form-grid { grid-template-columns: 1fr; gap: 15px; }
  .ai-tabs { flex-direction: column; gap: 8px; }
  .tab-btn { justify-content: center; padding: 12px; }
}
</style>
