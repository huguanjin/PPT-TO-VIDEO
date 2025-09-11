<!--
智能字幕配置组件
提供AI字幕分割的配置界面
-->
<template>
  <div class="smart-subtitle-config">
    <!-- 主开关 -->
    <div class="config-section">
      <h3>🤖 智能字幕处理</h3>
      <div class="form-group">
        <label class="switch-label">
          <input 
            type="checkbox" 
            v-model="localConfig.enabled"
            @change="handleConfigChange"
          />
          启用智能字幕处理
        </label>
        <small class="help-text">使用AI和规则混合的智能分割算法</small>
      </div>
    </div>

    <!-- 基础配置 -->
    <div v-if="localConfig.enabled" class="config-section">
      <h4>📏 基础配置</h4>
      
      <div class="form-group">
        <label>最大字符权重：</label>
        <input 
          type="number" 
          v-model.number="localConfig.max_length"
          :min="30" 
          :max="150"
          @change="handleConfigChange"
        />
        <small class="help-text">控制每行字幕的显示长度 (推荐75)</small>
      </div>

      <div class="form-group">
        <label>目标权重倍数：</label>
        <input 
          type="number" 
          v-model.number="localConfig.target_multiplier"
          :min="1.1" 
          :max="2.0"
          :step="0.1"
          @change="handleConfigChange"
        />
        <small class="help-text">分割目标权重的倍数 (推荐1.2)</small>
      </div>

      <div class="form-group">
        <label class="switch-label">
          <input 
            type="checkbox" 
            v-model="localConfig.smart_split"
            @change="handleConfigChange"
          />
          启用智能分割
        </label>
        <small class="help-text">基于语义和标点符号的智能分割</small>
      </div>
    </div>

    <!-- AI配置 -->
    <div v-if="localConfig.enabled" class="config-section">
      <h4>🧠 AI语义分割</h4>
      
      <div class="form-group">
        <label class="switch-label">
          <input 
            type="checkbox" 
            v-model="localConfig.use_ai_splitting"
            @change="handleAIToggle"
          />
          启用AI语义分割
        </label>
        <small class="help-text">使用大模型进行语义理解分割 (需要API密钥)</small>
      </div>

      <!-- AI服务配置 -->
      <div v-if="localConfig.use_ai_splitting" class="ai-config-panel">
        <div class="form-group">
          <label>AI服务类型：</label>
          <select v-model="aiConfig.service_type" @change="handleAIConfigChange">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="custom">自定义API</option>
          </select>
        </div>

        <div class="form-group">
          <label>API密钥：</label>
          <div class="api-key-input">
            <input 
              :type="showApiKey ? 'text' : 'password'"
              v-model="aiConfig.api_key"
              placeholder="输入API密钥"
              @blur="handleAIConfigChange"
            />
            <button 
              type="button" 
              class="toggle-btn"
              @click="showApiKey = !showApiKey"
            >
              {{ showApiKey ? '🙈' : '👁️' }}
            </button>
          </div>
          <small class="help-text">
            {{ getAPIKeyHelpText() }}
          </small>
        </div>

        <!-- 自定义API地址 -->
        <div class="form-group">
          <label>API地址：</label>
          <input 
            type="url" 
            v-model="aiConfig.base_url"
            :placeholder="getDefaultBaseURL()"
            @blur="handleAIConfigChange"
          />
          <small class="help-text">
            {{ aiConfig.service_type === 'custom' ? '请输入完整的API地址' : '留空使用默认地址，支持自定义API代理' }}
          </small>
        </div>

        <!-- 模型配置 -->
        <div class="form-group">
          <label>模型：</label>
          <div v-if="aiConfig.service_type === 'custom'" class="custom-model-input">
            <input 
              type="text"
              v-model="aiConfig.model"
              placeholder="输入模型名称，如: gpt-3.5-turbo"
              @blur="handleAIConfigChange"
            />
            <small class="help-text">请输入准确的模型名称</small>
          </div>
          <select v-else v-model="aiConfig.model" @change="handleAIConfigChange">
            <template v-if="aiConfig.service_type === 'openai'">
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo (推荐)</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
            </template>
            <template v-else>
              <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
              <option value="claude-3-sonnet-20240229">Claude 3 Sonnet (推荐)</option>
              <option value="claude-3-opus-20240229">Claude 3 Opus</option>
            </template>
          </select>
        </div>

        <!-- 高级配置 -->
        <div class="advanced-config">
          <div class="form-group">
            <label class="switch-label">
              <input 
                type="checkbox" 
                v-model="showAdvancedConfig"
              />
              显示高级配置
            </label>
          </div>

          <div v-if="showAdvancedConfig" class="advanced-options">
            <div class="form-group">
              <label>请求超时 (秒)：</label>
              <input 
                type="number" 
                v-model.number="aiConfig.timeout"
                :min="30" 
                :max="600"
                @change="handleAIConfigChange"
              />
              <small class="help-text">API请求超时时间 (默认300秒)</small>
            </div>

            <div class="form-group">
              <label>重试次数：</label>
              <input 
                type="number" 
                v-model.number="aiConfig.max_retries"
                :min="1" 
                :max="5"
                @change="handleAIConfigChange"
              />
              <small class="help-text">API请求失败时的重试次数 (默认3次)</small>
            </div>

            <div v-if="aiConfig.service_type === 'openai' || aiConfig.service_type === 'custom'" class="form-group">
              <label class="switch-label">
                <input 
                  type="checkbox" 
                  v-model="aiConfig.support_json"
                  @change="handleAIConfigChange"
                />
                支持JSON格式输出
              </label>
              <small class="help-text">启用结构化JSON响应 (推荐)</small>
            </div>
          </div>
        </div>

        <!-- API密钥验证 -->
        <div class="form-group">
          <button 
            class="test-btn"
            @click="testAPIKey"
            :disabled="!aiConfig.api_key || isTestingAPI"
          >
            {{ isTestingAPI ? '验证中...' : '验证API密钥' }}
          </button>
          
          <div v-if="apiKeyStatus !== null" class="api-status">
            <span :class="{ 'status-success': apiKeyStatus, 'status-error': !apiKeyStatus }">
              {{ apiKeyStatus ? '✅ API密钥有效' : '❌ API密钥无效' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 测试区域 -->
    <div v-if="localConfig.enabled" class="config-section">
      <h4>🧪 分割测试</h4>
      
      <div class="form-group">
        <label>测试文本：</label>
        <textarea 
          v-model="testText"
          placeholder="输入要测试分割的文本..."
          rows="3"
        ></textarea>
      </div>

      <div class="form-group">
        <button 
          class="test-btn"
          @click="testSplit"
          :disabled="!testText.trim() || isTesting"
        >
          {{ isTesting ? '分割中...' : '测试分割' }}
        </button>
      </div>

      <!-- 分割结果 -->
      <div v-if="splitResult" class="split-result">
        <h5>分割结果 ({{ splitResult.split_result.length }} 行):</h5>
        <div class="result-lines">
          <div 
            v-for="(line, index) in splitResult.lines_detail" 
            :key="index"
            class="result-line"
            :class="{ 'line-valid': line.is_valid, 'line-invalid': !line.is_valid }"
          >
            <span class="line-number">{{ index + 1 }}.</span>
            <span class="line-text">{{ line.text }}</span>
            <span class="line-weight">权重: {{ line.weight.toFixed(1) }}</span>
            <span class="line-status">{{ line.is_valid ? '✅' : '❌' }}</span>
          </div>
        </div>
        
        <div class="result-metrics">
          <p><strong>统计信息:</strong></p>
          <ul>
            <li>原文权重: {{ splitResult.metrics.original_weight.toFixed(1) }}</li>
            <li>分割方法: {{ splitResult.metrics.processing_method === 'ai' ? 'AI分割' : '规则分割' }}</li>
            <li>权重分布: {{ getDistributionText(splitResult.metrics.weight_distribution) }}</li>
            <li>平均权重: {{ splitResult.metrics.avg_line_weight.toFixed(1) }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 状态信息 -->
    <div v-if="status" class="config-section">
      <h4>📊 功能状态</h4>
      <div class="status-grid">
        <div class="status-item">
          <span class="status-label">智能分割:</span>
          <span :class="getStatusClass(status.features.smart_splitting)">
            {{ status.features.smart_splitting ? '可用' : '不可用' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">AI分割:</span>
          <span :class="getStatusClass(status.features.ai_splitting)">
            {{ status.features.ai_splitting ? '可用' : '不可用' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">配置有效:</span>
          <span :class="getStatusClass(status.config_status.smart_config_valid)">
            {{ status.config_status.smart_config_valid ? '有效' : '无效' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
/* eslint-disable-next-line no-duplicate-imports */
import type { 
  SmartSubtitleConfig, 
  AIConfig, 
  SplitTestResult, 
  SmartSubtitleStatus 
} from '@/services/smartSubtitle'
/* eslint-disable-next-line no-duplicate-imports */
import { 
  getSmartSubtitleConfig,
  updateSmartSubtitleConfig,
  testSmartSubtitleSplit,
  getSmartSubtitleStatus,
  getAIConfig,
  updateAIConfig,
  validateAPIKey,
  getRecommendedConfig,
  testAISplit
} from '@/services/smartSubtitle'

// 简单的消息提示函数
function showMessage(message: string, type: 'success' | 'error' | 'warning' = 'success') {
  // 创建一个简单的提示框
  const messageEl = document.createElement('div')
  messageEl.textContent = message
  messageEl.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 4px;
    color: white;
    z-index: 9999;
    font-size: 14px;
    background-color: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#ffc107'};
  `
  document.body.appendChild(messageEl)
  
  setTimeout(() => {
    if (messageEl.parentNode) {
      messageEl.parentNode.removeChild(messageEl)
    }
  }, 3000)
}

// Props
const props = defineProps<{
  modelValue?: Partial<SmartSubtitleConfig>
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: Partial<SmartSubtitleConfig>]
  'change': [value: Partial<SmartSubtitleConfig>]
}>()

// 响应式数据
const localConfig = reactive<Partial<SmartSubtitleConfig>>({
  enabled: false,
  max_length: 75,
  target_multiplier: 1.2,
  smart_split: true,
  use_ai_splitting: false,
  ...getRecommendedConfig()
})

const aiConfig = reactive<AIConfig>({
  service_type: 'openai',
  api_key: '',
  model: 'gpt-3.5-turbo',
  base_url: '',
  timeout: 300,
  max_retries: 3,
  support_json: true
})

const showApiKey = ref(false)
const showAdvancedConfig = ref(false)
const isTestingAPI = ref(false)
const apiKeyStatus = ref<boolean | null>(null)
const testText = ref('')
const isTesting = ref(false)
const splitResult = ref<SplitTestResult | null>(null)
const status = ref<SmartSubtitleStatus | null>(null)

// 初始化
onMounted(async () => {
  await loadConfig()
  await loadStatus()
})

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    Object.assign(localConfig, newValue)
  }
}, { immediate: true })

// 加载配置
async function loadConfig() {
  try {
    const config = await getSmartSubtitleConfig()
    Object.assign(localConfig, config)
    
    if (config.use_ai_splitting && config.ai_config) {
      Object.assign(aiConfig, config.ai_config)
    }
  } 
  catch (error) {
    // 静默处理错误
  }
}

// 加载状态
async function loadStatus() {
  try {
    status.value = await getSmartSubtitleStatus()
  } 
  catch (error) {
    // 静默处理错误
  }
}

// 处理配置变化
function handleConfigChange() {
  emit('update:modelValue', { ...localConfig })
  emit('change', { ...localConfig })
  
  // 保存到后端
  saveConfig()
}

// 处理AI开关
async function handleAIToggle() {
  if (localConfig.use_ai_splitting) {
    // 加载AI配置
    try {
      const aiConfigData = await getAIConfig()
      Object.assign(aiConfig, aiConfigData.ai_config)
    } 
    catch (error) {
      // 静默处理错误
    }
  }
  
  handleConfigChange()
}

// 保存配置
async function saveConfig() {
  try {
    await updateSmartSubtitleConfig(localConfig)
    
    // 如果启用了AI，也保存AI配置
    if (localConfig.use_ai_splitting) {
      await updateAIConfig({
        enabled: true,
        ai_config: aiConfig
      })
    }
  } 
  catch (error) {
    showMessage('配置保存失败', 'error')
  }
}

// 处理AI配置变化
async function handleAIConfigChange() {
  // 如果切换了服务类型，更新默认模型
  if (aiConfig.service_type === 'openai') {
    if (!aiConfig.model || aiConfig.model.startsWith('claude-')) {
      aiConfig.model = 'gpt-3.5-turbo'
    }
    if (!aiConfig.base_url) {
      aiConfig.base_url = 'https://api.openai.com'
    }
  } 
  else if (aiConfig.service_type === 'anthropic') {
    if (!aiConfig.model || aiConfig.model.startsWith('gpt-')) {
      aiConfig.model = 'claude-3-sonnet-20240229'
    }
    if (!aiConfig.base_url) {
      aiConfig.base_url = 'https://api.anthropic.com'
    }
  } 
  else if (aiConfig.service_type === 'custom') {
    if (!aiConfig.model) {
      aiConfig.model = 'gpt-3.5-turbo'
    }
  }
  
  // 重置API验证状态
  apiKeyStatus.value = null
  
  // 保存AI配置
  try {
    await updateAIConfig({
      enabled: localConfig.use_ai_splitting || false,
      ai_config: aiConfig
    })
  } 
  catch (error) {
    // 静默处理错误
  }
  
  handleConfigChange()
}

// 获取API密钥帮助文本
function getAPIKeyHelpText(): string {
  switch (aiConfig.service_type) {
    case 'openai':
      return 'OpenAI API密钥'
    case 'anthropic':
      return 'Anthropic API密钥'
    case 'custom':
      return '自定义API服务的密钥'
    default:
      return 'API密钥'
  }
}

// 获取默认Base URL
function getDefaultBaseURL(): string {
  switch (aiConfig.service_type) {
    case 'openai':
      return 'https://api.openai.com'
    case 'anthropic':
      return 'https://api.anthropic.com'
    case 'custom':
      return 'https://your-api.example.com'
    default:
      return ''
  }
}

// 测试API密钥
async function testAPIKey() {
  if (!aiConfig.api_key) {
    showMessage('请先输入API密钥', 'warning')
    return
  }
  
  isTestingAPI.value = true
  
  try {
    const isValid = await validateAPIKey(aiConfig)
    apiKeyStatus.value = isValid
    
    if (isValid) {
      showMessage('API密钥验证成功')
    } 
    else {
      showMessage('API密钥验证失败，请检查密钥和网络连接', 'error')
    }
  } 
  catch (error) {
    apiKeyStatus.value = false
    showMessage('API密钥验证异常', 'error')
  } 
  finally {
    isTestingAPI.value = false
  }
}

// 测试分割
async function testSplit() {
  if (!testText.value.trim()) {
    showMessage('请输入测试文本', 'warning')
    return
  }
  
  if (!aiConfig.api_key && localConfig.use_ai_splitting) {
    showMessage('使用AI分割需要先配置API密钥', 'warning')
    return
  }
  
  isTesting.value = true
  
  try {
    if (localConfig.use_ai_splitting && aiConfig.api_key) {
      // 使用AI分割测试
      const aiResult = await testAISplit(testText.value, aiConfig, localConfig.max_length || 75)
      splitResult.value = {
        original_text: testText.value,
        split_result: aiResult.split_result,
        lines_detail: aiResult.split_result.map((line: string) => ({
          text: line,
          weight: line.length * 1.2, // 简单权重计算
          is_valid: line.length <= (localConfig.max_length || 75),
          length: line.length
        })),
        metrics: {
          original_weight: testText.value.length * 1.2,
          split_count: aiResult.lines_count,
          total_weight: aiResult.split_result.reduce((sum: number, line: string) => sum + line.length * 1.2, 0),
          max_line_weight: Math.max(...aiResult.split_result.map((line: string) => line.length * 1.2)),
          min_line_weight: Math.min(...aiResult.split_result.map((line: string) => line.length * 1.2)),
          avg_line_weight: aiResult.split_result.reduce((sum: number, line: string) => sum + line.length * 1.2, 0) / aiResult.lines_count,
          weight_distribution: 'balanced',
          processing_method: 'ai',
          processed_at: new Date().toISOString()
        },
        processing_method: 'AI语义分割'
      }
    } 
    else {
      // 使用传统字幕分割测试
      splitResult.value = await testSmartSubtitleSplit(testText.value, localConfig)
    }
    showMessage('分割测试完成')
  } 
  catch (error) {
    showMessage('分割测试失败', 'error')
  } 
  finally {
    isTesting.value = false
  }
}

// 获取权重分布文本
function getDistributionText(distribution: string): string {
  const map = {
    'balanced': '均衡',
    'moderate': '中等',
    'unbalanced': '不均衡'
  }
  return map[distribution as keyof typeof map] || distribution
}

// 获取状态样式类
function getStatusClass(status: boolean): string {
  return status ? 'status-success' : 'status-error'
}
</script>

<style scoped>
.smart-subtitle-config {
  padding: 20px;
  max-width: 800px;
}

.config-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.config-section h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
}

.config-section h4 {
  margin: 0 0 15px 0;
  color: #555;
  font-size: 16px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.switch-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.switch-label input[type="checkbox"] {
  margin-right: 8px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.help-text {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 12px;
}

.ai-config-panel {
  background: #f0f8ff;
  padding: 15px;
  border-radius: 6px;
  margin-top: 10px;
}

.api-key-input {
  display: flex;
  gap: 8px;
}

.api-key-input input {
  flex: 1;
}

.toggle-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}

.test-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.test-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.api-status {
  margin-top: 10px;
}

.status-success {
  color: #28a745;
}

.status-error {
  color: #dc3545;
}

.split-result {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.result-lines {
  margin: 10px 0;
}

.result-line {
  display: flex;
  align-items: center;
  padding: 8px;
  margin: 5px 0;
  background: white;
  border-radius: 4px;
  gap: 10px;
}

.line-valid {
  border-left: 4px solid #28a745;
}

.line-invalid {
  border-left: 4px solid #dc3545;
}

.line-number {
  font-weight: bold;
  min-width: 30px;
}

.line-text {
  flex: 1;
}

.line-weight {
  font-size: 12px;
  color: #666;
}

.result-metrics {
  margin-top: 15px;
  padding: 10px;
  background: #e9ecef;
  border-radius: 4px;
}

.result-metrics ul {
  margin: 5px 0;
  padding-left: 20px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.status-label {
  font-weight: 500;
}
</style>
