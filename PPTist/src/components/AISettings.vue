<template>
  <div class="config-section">
    <h2>AI配置</h2>
    <div class="ai-tabs">
      <button
        v-for="service in aiServices"
        :key="service.key"
        @click="currentAIService = service.key"
        :class="['tab-btn', { active: currentAIService === service.key }]"
      >
        <span>{{ service.icon }}</span>
        {{ service.name }}
      </button>
    </div>

    <!-- OpenAI配置 -->
    <div v-if="currentAIService === 'openai'" class="ai-config">
      <div class="ai-form-grid">
        <div class="ai-form-group">
          <label>API密钥</label>
          <input type="password" v-model="config.ai.openai.api_key" placeholder="sk-..." />
        </div>
        <div class="ai-form-group">
          <label>API地址</label>
          <input type="url" v-model="config.ai.openai.base_url" placeholder="https://api.openai.com" />
        </div>
        <div class="ai-form-group">
          <label>模型名称</label>
          <select v-model="config.ai.openai.model">
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
          </select>
        </div>
        <div class="ai-form-group">
          <label>请求超时 (秒)</label>
          <input type="number" v-model="config.ai.openai.timeout" min="30" max="600" />
        </div>
      </div>
      <div class="ai-actions">
        <button @click="testAIConnection" class="btn-test" :disabled="testing">
          {{ testing ? '测试中...' : '测试OpenAI连接' }}
        </button>
        <span v-if="testResult" :class="['test-result', testResult.success ? 'success' : 'error']">
          {{ testResult.message }}
        </span>
      </div>
    </div>

    <!-- Anthropic配置 -->
    <div v-if="currentAIService === 'anthropic'" class="ai-config">
      <div class="ai-form-grid">
        <div class="ai-form-group">
          <label>API密钥</label>
          <input type="password" v-model="config.ai.anthropic.api_key" placeholder="sk-ant-..." />
        </div>
        <div class="ai-form-group">
          <label>API地址</label>
          <input type="url" v-model="config.ai.anthropic.base_url" placeholder="https://api.anthropic.com" />
        </div>
        <div class="ai-form-group">
          <label>模型名称</label>
          <select v-model="config.ai.anthropic.model">
            <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
            <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
            <option value="claude-3-opus-20240229">Claude 3 Opus</option>
          </select>
        </div>
        <div class="ai-form-group">
          <label>请求超时 (秒)</label>
          <input type="number" v-model="config.ai.anthropic.timeout" min="30" max="600" />
        </div>
      </div>
      <div class="ai-actions">
        <button @click="testAIConnection" class="btn-test" :disabled="testing">
          {{ testing ? '测试中...' : '测试Anthropic连接' }}
        </button>
        <span v-if="testResult" :class="['test-result', testResult.success ? 'success' : 'error']">
          {{ testResult.message }}
        </span>
      </div>
    </div>

    <!-- 自定义API配置 -->
    <div v-if="currentAIService === 'custom'" class="ai-config">
      <div class="ai-form-grid">
        <div class="ai-form-group">
          <label>API密钥</label>
          <input type="password" v-model="config.ai.custom.api_key" placeholder="输入API密钥" />
        </div>
        <div class="ai-form-group">
          <label>API地址</label>
          <input type="url" v-model="config.ai.custom.base_url" placeholder="https://your-api.com" />
        </div>
        <div class="ai-form-group">
          <label>模型名称</label>
          <input type="text" v-model="config.ai.custom.model" placeholder="输入模型名称" />
        </div>
        <div class="ai-form-group">
          <label>请求超时 (秒)</label>
          <input type="number" v-model="config.ai.custom.timeout" min="30" max="600" />
        </div>
      </div>
      <div class="ai-actions">
        <button @click="testAIConnection" class="btn-test" :disabled="testing">
          {{ testing ? '测试中...' : '测试自定义API连接' }}
        </button>
        <span v-if="testResult" :class="['test-result', testResult.success ? 'success' : 'error']">
          {{ testResult.message }}
        </span>
      </div>
    </div>

    <!-- 通用AI设置 -->
    <div class="ai-general-settings">
      <h3>通用设置</h3>
      <div class="ai-form-grid">
        <div class="ai-form-group">
          <label>默认服务</label>
          <select v-model="config.ai.default_service">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="custom">自定义API</option>
          </select>
        </div>
        <div class="ai-form-group">
          <label>源语言</label>
          <select v-model="config.ai.source_language">
            <option value="中文">中文</option>
            <option value="English">English</option>
            <option value="日本語">日本語</option>
          </select>
        </div>
        <div class="ai-form-group">
          <label>目标语言</label>
          <select v-model="config.ai.target_language">
            <option value="中文">中文</option>
            <option value="English">English</option>
            <option value="日本語">日本語</option>
          </select>
        </div>
        <div class="ai-form-group">
          <label>最大并发数</label>
          <input type="number" v-model="config.ai.max_workers" min="1" max="10" />
        </div>
      </div>
    </div>

    <!-- AI内容优化设置 -->
    <div class="ai-optimization-settings">
      <h3>🚀 AI前置断句优化</h3>
      <div class="optimization-description">
        <p>AI前置处理将在TTS生成之前智能分段内容，从根本上解决多行字幕问题</p>
      </div>
      
      <div class="ai-form-group">
        <label class="switch-label">
          <input 
            type="checkbox" 
            v-model="config.ai_content_optimization.enabled"
            class="switch-input"
          />
          <span class="switch-slider"></span>
          启用AI前置断句优化
        </label>
        <p class="help-text">启用后将在TTS生成前进行智能分段，提升字幕显示效果</p>
      </div>

      <div v-if="config.ai_content_optimization.enabled" class="optimization-advanced">
        <div class="ai-form-grid">
          <div class="ai-form-group">
            <label>最大分段长度</label>
            <input 
              type="number" 
              v-model="config.ai_content_optimization.max_segment_length" 
              min="20" 
              max="60" 
              step="5"
            />
            <p class="help-text">每个分段的最大字符数（推荐35字）</p>
          </div>
          <div class="ai-form-group">
            <label>最小分段长度</label>
            <input 
              type="number" 
              v-model="config.ai_content_optimization.min_segment_length" 
              min="5" 
              max="30" 
              step="5"
            />
            <p class="help-text">每个分段的最小字符数（推荐10字）</p>
          </div>
        </div>

        <div class="optimization-options">
          <div class="ai-form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="config.ai_content_optimization.preserve_meaning"
              />
              <span class="checkmark"></span>
              保持语义完整性
            </label>
            <p class="help-text">确保分段后的内容语义完整</p>
          </div>
          
          <div class="ai-form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="config.ai_content_optimization.natural_breaks"
              />
              <span class="checkmark"></span>
              使用自然断句点
            </label>
            <p class="help-text">优先在标点符号等自然位置断句</p>
          </div>
          
          <div class="ai-form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="config.ai_content_optimization.fallback_to_original"
              />
              <span class="checkmark"></span>
              失败时回退到原始文本
            </label>
            <p class="help-text">AI优化失败时使用原始文本，确保稳定性</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs } from 'vue'
import { apiRequest } from '@/config/api'

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

interface Props {
  config: {
    ai: AIConfig
    ai_content_optimization: AIContentOptimizationConfig
  }
}

const props = defineProps<Props>()
const { config } = toRefs(props)

// 状态
const currentAIService = ref('openai')
const testing = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const aiServices = ref([
  { key: 'openai', name: 'OpenAI', icon: '🤖' },
  { key: 'anthropic', name: 'Anthropic (Claude)', icon: '🧠' },
  { key: 'custom', name: '自定义API', icon: '⚙️' }
])

// 测试AI连接
const testAIConnection = async () => {
  testing.value = true
  testResult.value = null
  
  try {
    const serviceConfig = config.value.ai[currentAIService.value as keyof AIConfig]
    
    if (!serviceConfig || typeof serviceConfig !== 'object') {
      throw new Error('无效的服务配置')
    }
    
    if (!('api_key' in serviceConfig) || !serviceConfig.api_key) {
      throw new Error('请先配置API密钥')
    }

    const response = await apiRequest('/api/ai/test', {
      method: 'POST',
      body: JSON.stringify({
        service: currentAIService.value,
        config: serviceConfig
      }),
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.success) {
      testResult.value = { success: true, message: '连接测试成功!' }
    }
    else {
      testResult.value = { success: false, message: response.message || '连接测试失败' }
    }
  } 
  catch (error) {
    testResult.value = { 
      success: false, 
      message: error instanceof Error ? error.message : '连接测试失败' 
    }
  } 
  finally {
    testing.value = false
  }
}
</script>

<style lang="scss" scoped>
.config-section {
  margin-bottom: 40px;

  h2 {
    color: #2c3e50;
    font-size: 1.6em;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #ecf0f1;
  }
  
  h3 {
    color: #34495e;
    font-size: 1.3em;
    margin: 30px 0 15px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #e0e0e0;
  }
}

.ai-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.tab-btn {
  padding: 10px 16px;
  border: none;
  background: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;

  &:hover {
    color: #4f46e5;
    background-color: #f8fafc;
  }

  &.active {
    color: #4f46e5;
    border-bottom-color: #4f46e5;
    background-color: #f8fafc;
  }
}

.ai-config {
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #fafafa;
  margin-bottom: 20px;
}

.ai-general-settings {
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.ai-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.ai-form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;

  label {
    font-weight: 500;
    color: #374151;
    font-size: 14px;
  }

  input, select {
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    background-color: white;
    transition: all 0.3s ease;

    &:focus {
      outline: none;
      border-color: #4f46e5;
      box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }
  }
}

.ai-actions {
  display: flex;
  align-items: center;
  gap: 15px;
  padding-top: 15px;
  border-top: 1px solid #e5e7eb;
}

.btn-test {
  padding: 8px 16px;
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #4338ca;
  }

  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
}

.test-result {
  font-size: 14px;
  font-weight: 500;

  &.success {
    color: #059669;
  }

  &.error {
    color: #dc2626;
  }
}

.ai-optimization-settings {
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f0f8ff;
  margin-top: 20px;
  
  h3 {
    color: #1e40af;
    margin-bottom: 10px;
    font-size: 16px;
  }
}

.optimization-description {
  margin-bottom: 20px;
  
  p {
    color: #6b7280;
    font-size: 14px;
    line-height: 1.5;
    margin: 0;
  }
}

.optimization-advanced {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.optimization-options {
  margin-top: 20px;
}

.switch-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
  color: #374151;
}

.switch-input {
  position: relative;
  width: 44px;
  height: 24px;
  -webkit-appearance: none;
  appearance: none;
  background: #ccc;
  border-radius: 12px;
  outline: none;
  transition: 0.3s;
  cursor: pointer;
  
  &:checked {
    background: #4f46e5;
  }
  
  &:before {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    top: 2px;
    left: 2px;
    background: white;
    transition: 0.3s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }
  
  &:checked:before {
    transform: translateX(20px);
  }
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
  color: #374151;
  
  input[type="checkbox"] {
    width: 18px;
    height: 18px;
    accent-color: #4f46e5;
    cursor: pointer;
  }
}

.help-text {
  color: #6b7280;
  font-size: 12px;
  margin: 4px 0 0 0;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .ai-form-grid {
    grid-template-columns: 1fr;
  }

  .ai-tabs {
    flex-wrap: wrap;
  }
}
</style>
