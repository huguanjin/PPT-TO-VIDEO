<template>
  <div class="settings-section">
    <div class="section-header">
      <h3>
        <Magic class="section-icon" />
        AI 服务配置
      </h3>
      <p class="section-desc">配置 AI 服务以启用智能功能</p>
    </div>
    
    <div class="ai-services">
      <!-- AI服务选择标签 -->
      <div class="ai-tabs">
        <div 
          v-for="service in aiServices" 
          :key="service.key"
          :class="['ai-tab', { active: activeAIService === service.key }]"
          @click="activeAIService = service.key"
        >
          <span class="tab-icon">{{ service.icon }}</span>
          <span class="tab-text">{{ service.name }}</span>
        </div>
      </div>
      
      <!-- OpenAI配置 -->
      <div v-if="activeAIService === 'openai'" class="service-card">
        <div class="service-header">
          <h4>OpenAI GPT</h4>
          <span class="service-status" :class="{ connected: config.openai.enabled }">
            {{ config.openai.enabled ? '已连接' : '未配置' }}
          </span>
        </div>
        <div class="service-content">
          <div class="input-group">
            <label>API 密钥</label>
            <input 
              type="password" 
              v-model="openaiApiKey"
              placeholder="sk-..."
              class="service-input"
            />
          </div>
          <div class="service-actions">
            <button 
              @click="testOpenAIConnection" 
              :disabled="!config.openai.apiKey || testingConnection.openai"
              class="test-btn"
            >
              {{ testingConnection.openai ? '测试中...' : '测试连接' }}
            </button>
            <button 
              @click="toggleOpenAI" 
              :class="['toggle-btn', { enabled: config.openai.enabled }]"
            >
              {{ config.openai.enabled ? '禁用' : '启用' }}
            </button>
          </div>
          <div v-if="messages.openai.visible" class="message-display" :class="messages.openai.type">
            {{ messages.openai.text }}
          </div>
        </div>
      </div>
      
      <!-- Anthropic配置 -->
      <div v-if="activeAIService === 'anthropic'" class="service-card">
        <div class="service-header">
          <h4>Anthropic Claude</h4>
          <span class="service-status" :class="{ connected: config.anthropic.enabled }">
            {{ config.anthropic.enabled ? '已连接' : '未配置' }}
          </span>
        </div>
        <div class="service-content">
          <div class="input-group">
            <label>API 密钥</label>
            <input 
              type="password" 
              v-model="anthropicApiKey"
              placeholder="sk-ant-..."
              class="service-input"
            />
          </div>
          <div class="service-actions">
            <button 
              @click="testAnthropicConnection" 
              :disabled="!config.anthropic.apiKey || testingConnection.anthropic"
              class="test-btn"
            >
              {{ testingConnection.anthropic ? '测试中...' : '测试连接' }}
            </button>
            <button 
              @click="toggleAnthropic" 
              :class="['toggle-btn', { enabled: config.anthropic.enabled }]"
            >
              {{ config.anthropic.enabled ? '禁用' : '启用' }}
            </button>
          </div>
          <div v-if="messages.anthropic.visible" class="message-display" :class="messages.anthropic.type">
            {{ messages.anthropic.text }}
          </div>
        </div>
      </div>
      
      <!-- 自定义API配置 -->
      <div v-if="activeAIService === 'custom'" class="service-card">
        <div class="service-header">
          <h4>自定义 API</h4>
          <span class="service-status" :class="{ connected: config.custom.enabled }">
            {{ config.custom.enabled ? '已连接' : '未配置' }}
          </span>
        </div>
        <div class="service-content">
          <div class="input-row">
            <div class="input-group">
              <label>API 基础URL</label>
              <input 
                type="url" 
                v-model="customBaseUrl"
                placeholder="https://api.example.com"
                class="service-input"
              />
            </div>
            <div class="input-group">
              <label>模型名称</label>
              <input 
                type="text" 
                v-model="customModel"
                placeholder="gpt-3.5-turbo"
                class="service-input"
              />
            </div>
          </div>
          <div class="input-group">
            <label>API 密钥</label>
            <input 
              type="password" 
              v-model="customApiKey"
              placeholder="输入API密钥"
              class="service-input"
            />
          </div>
          <div class="input-help">
            支持OpenAI格式的API服务，如：gpt-3.5-turbo、gpt-4、claude-3-sonnet等
          </div>
          <div class="service-actions">
            <button 
              @click="testCustomConnection" 
              :disabled="!config.custom.apiKey || !config.custom.baseUrl || testingConnection.custom"
              class="test-btn"
            >
              {{ testingConnection.custom ? '测试中...' : '测试连接' }}
            </button>
            <button 
              @click="toggleCustom" 
              :class="['toggle-btn', { enabled: config.custom.enabled }]"
            >
              {{ config.custom.enabled ? '禁用' : '启用' }}
            </button>
          </div>
          <div v-if="messages.custom.visible" class="message-display" :class="messages.custom.type">
            {{ messages.custom.text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { Magic } from '@icon-park/vue-next'
import { aiService } from '@/api/services'

interface AIConfig {
  openai: {
    apiKey: string
    enabled: boolean
  }
  anthropic: {
    apiKey: string
    enabled: boolean
  }
  custom: {
    apiKey: string
    baseUrl: string
    model: string
    enabled: boolean
  }
}

interface Props {
  config: AIConfig
}

interface Emits {
  (e: 'update:config', config: AIConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 测试状态
const testingConnection = ref({
  openai: false,
  anthropic: false,
  custom: false
})

// 消息状态
const messages = ref({
  openai: { text: '', type: '', visible: false },
  anthropic: { text: '', type: '', visible: false },
  custom: { text: '', type: '', visible: false }
})

// 显示消息的函数
const showMessage = (service: 'openai' | 'anthropic' | 'custom', text: string, type: 'success' | 'error') => {
  messages.value[service] = { text, type, visible: true }
  // 3秒后自动隐藏消息
  setTimeout(() => {
    messages.value[service].visible = false
  }, 3000)
}

// 加载配置函数
const loadConfig = async () => {
  try {
    // 使用AI服务获取配置
    const apiConfig = await aiService.getConfig()
    
    // 转换API配置到组件配置格式
    const loadedConfig: AIConfig = {
      openai: {
        apiKey: apiConfig.openai.apiKey || '',
        enabled: apiConfig.openai.enabled || false
      },
      anthropic: {
        apiKey: apiConfig.anthropic.apiKey || '',
        enabled: apiConfig.anthropic.enabled || false
      },
      custom: {
        apiKey: apiConfig.custom.apiKey || '',
        baseUrl: apiConfig.custom.baseUrl || '',
        model: apiConfig.custom.model || '',
        enabled: apiConfig.custom.enabled || false
      }
    }
    
    // 发出配置更新事件
    emit('update:config', loadedConfig)
    
    // 根据默认服务设置激活的服务标签
    if (apiConfig.defaultProvider) {
      activeAIService.value = apiConfig.defaultProvider
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('加载AI配置失败:', error)
  }
}

// AI服务选择
const activeAIService = ref('openai')

const aiServices = [
  {
    key: 'openai',
    name: 'OpenAI',
    icon: '🤖'
  },
  {
    key: 'anthropic', 
    name: 'Anthropic',
    icon: '🧠'
  },
  {
    key: 'custom',
    name: '自定义API',
    icon: '⚙️'
  }
]

// 计算属性
const openaiApiKey = computed({
  get: () => props.config.openai.apiKey,
  set: (value) => emit('update:config', {
    ...props.config,
    openai: { ...props.config.openai, apiKey: value }
  })
})

const anthropicApiKey = computed({
  get: () => props.config.anthropic.apiKey,
  set: (value) => emit('update:config', {
    ...props.config,
    anthropic: { ...props.config.anthropic, apiKey: value }
  })
})

const customApiKey = computed({
  get: () => props.config.custom.apiKey,
  set: (value) => emit('update:config', {
    ...props.config,
    custom: { ...props.config.custom, apiKey: value }
  })
})

const customBaseUrl = computed({
  get: () => props.config.custom.baseUrl,
  set: (value) => emit('update:config', {
    ...props.config,
    custom: { ...props.config.custom, baseUrl: value }
  })
})

const customModel = computed({
  get: () => props.config.custom.model,
  set: (value) => emit('update:config', {
    ...props.config,
    custom: { ...props.config.custom, model: value }
  })
})

// 方法
const testOpenAIConnection = async () => {
  if (!props.config.openai.apiKey) {
    // eslint-disable-next-line no-console
    console.warn('请先输入OpenAI API密钥')
    return
  }

  testingConnection.value.openai = true
  
  try {
    // 使用AI服务测试OpenAI连接
    const result = await aiService.testOpenAI({
      apiKey: props.config.openai.apiKey,
      baseUrl: 'https://api.openai.com/v1',
      model: 'gpt-3.5-turbo',
      enabled: true
    })
    
    if (result.success) {
      showMessage('openai', 'OpenAI连接测试成功！', 'success')
    }
    else {
      showMessage('openai', `连接测试失败: ${result.error || '未知错误'}`, 'error')
    }
  }
  catch (error) {
    showMessage('openai', `连接测试失败: ${error instanceof Error ? error.message : '网络错误'}`, 'error')
  }
  finally {
    testingConnection.value.openai = false
  }
}

const testAnthropicConnection = async () => {
  if (!props.config.anthropic.apiKey) {
    // eslint-disable-next-line no-console
    console.warn('请先输入Anthropic API密钥')
    return
  }

  testingConnection.value.anthropic = true
  
  try {
    // 使用AI服务测试Anthropic连接
    const result = await aiService.testAnthropic({
      apiKey: props.config.anthropic.apiKey,
      baseUrl: 'https://api.anthropic.com',
      model: 'claude-3-haiku-20240307',
      enabled: true
    })
    
    if (result.success) {
      showMessage('anthropic', 'Anthropic连接测试成功！', 'success')
    }
    else {
      showMessage('anthropic', `连接测试失败: ${result.error || '未知错误'}`, 'error')
    }
  }
  catch (error) {
    showMessage('anthropic', `连接测试失败: ${error instanceof Error ? error.message : '网络错误'}`, 'error')
  }
  finally {
    testingConnection.value.anthropic = false
  }
}

const testCustomConnection = async () => {
  if (!props.config.custom.apiKey || !props.config.custom.baseUrl) {
    // eslint-disable-next-line no-console
    console.warn('请先输入API密钥和基础URL')
    return
  }

  testingConnection.value.custom = true
  
  try {
    // 使用AI服务测试自定义API连接
    const result = await aiService.testCustomAPI({
      apiKey: props.config.custom.apiKey,
      baseUrl: props.config.custom.baseUrl,
      model: props.config.custom.model,
      enabled: true
    })
    
    if (result.success) {
      showMessage('custom', '自定义API连接测试成功！', 'success')
    }
    else {
      showMessage('custom', `连接测试失败: ${result.error || '未知错误'}`, 'error')
    }
  }
  catch (error) {
    showMessage('custom', `连接测试失败: ${error instanceof Error ? error.message : '网络错误'}`, 'error')
  }
  finally {
    testingConnection.value.custom = false
  }
}

const toggleOpenAI = () => {
  emit('update:config', {
    ...props.config,
    openai: { ...props.config.openai, enabled: !props.config.openai.enabled }
  })
}

const toggleAnthropic = () => {
  emit('update:config', {
    ...props.config,
    anthropic: { ...props.config.anthropic, enabled: !props.config.anthropic.enabled }
  })
}

const toggleCustom = () => {
  emit('update:config', {
    ...props.config,
    custom: { ...props.config.custom, enabled: !props.config.custom.enabled }
  })
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.settings-section {
  .section-header {
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
      color: white;

      .section-icon {
        margin-right: 8px;
        font-size: 24px;
      }
    }

    .section-desc {
      margin: 0;
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

.ai-services {
  .ai-tabs {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;

    .ai-tab {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 20px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        background: rgba(255, 255, 255, 0.1);
      }

      &.active {
        background: rgba(52, 152, 219, 0.2);
        border-color: rgba(52, 152, 219, 0.5);
      }

      .tab-icon {
        font-size: 18px;
      }

      .tab-text {
        color: white;
        font-weight: 500;
      }
    }
  }

  .service-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;
    box-sizing: border-box;
    overflow: hidden;
    width: 100%;
    max-width: 100%;

    .service-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      h4 {
        margin: 0;
        color: white;
        font-size: 16px;
      }

      .service-status {
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        background: rgba(220, 53, 69, 0.2);
        color: #ff6b6b;

        &.connected {
          background: rgba(40, 167, 69, 0.2);
          color: #51cf66;
        }
      }
    }

    .service-content {
      overflow: hidden; /* 防止内容溢出 */
      
      .input-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 16px;
        width: 100%;
        box-sizing: border-box;

        @media (max-width: 768px) {
          grid-template-columns: 1fr;
          gap: 12px;
        }
      }

      .input-group {
        margin-bottom: 16px;
        min-width: 0; /* 防止flex项目溢出 */

        label {
          display: block;
          margin-bottom: 6px;
          color: white;
          font-weight: 500;
          font-size: 13px;
        }

        .service-input {
          width: 100%;
          max-width: 100%;
          padding: 10px 14px;
          border: 2px solid rgba(255, 255, 255, 0.2);
          border-radius: 6px;
          background: rgba(255, 255, 255, 0.05);
          color: white;
          font-size: 14px;
          transition: all 0.3s ease;
          box-sizing: border-box;

          &:focus {
            outline: none;
            border-color: rgba(52, 152, 219, 0.6);
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
          }

          &::placeholder {
            color: rgba(255, 255, 255, 0.4);
          }
        }

        .input-help {
          margin-top: 6px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          line-height: 1.4;
        }
      }

      .input-help {
        margin-top: -8px;
        margin-bottom: 16px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
        line-height: 1.4;
        text-align: center;
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        border-left: 3px solid rgba(52, 152, 219, 0.6);
      }

      .service-actions {
        display: flex;
        gap: 12px;
        margin-top: 16px;
        flex-wrap: wrap;

        .test-btn {
          padding: 10px 18px;
          background: linear-gradient(45deg, rgba(52, 152, 219, 0.3), rgba(52, 152, 219, 0.2));
          border: 1px solid rgba(52, 152, 219, 0.6);
          border-radius: 6px;
          color: #ffffff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

          &:hover:not(:disabled) {
            background: linear-gradient(45deg, rgba(52, 152, 219, 0.4), rgba(52, 152, 219, 0.3));
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
          }

          &:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
          }
        }

        .toggle-btn {
          padding: 10px 18px;
          background: linear-gradient(45deg, rgba(220, 53, 69, 0.3), rgba(220, 53, 69, 0.2));
          border: 1px solid rgba(220, 53, 69, 0.6);
          border-radius: 6px;
          color: #ffffff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

          &:hover {
            background: linear-gradient(45deg, rgba(220, 53, 69, 0.4), rgba(220, 53, 69, 0.3));
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
          }

          &.enabled {
            background: linear-gradient(45deg, rgba(40, 167, 69, 0.3), rgba(40, 167, 69, 0.2));
            border-color: rgba(40, 167, 69, 0.6);
            color: #ffffff;

            &:hover {
              background: linear-gradient(45deg, rgba(40, 167, 69, 0.4), rgba(40, 167, 69, 0.3));
              transform: translateY(-1px);
              box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
          }
        }
      }
    }
  }
}

// 消息显示样式
.message-display {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  
  &.success {
    background-color: rgba(34, 197, 94, 0.1);
    color: #16a34a;
    border: 1px solid rgba(34, 197, 94, 0.2);
  }
  
  &.error {
    background-color: rgba(239, 68, 68, 0.1);
    color: #dc2626;
    border: 1px solid rgba(239, 68, 68, 0.2);
  }
}
</style>
