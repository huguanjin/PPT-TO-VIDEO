<!--
统一配置API测试页面 - 阶段一：API端点标准化
测试新创建的统一配置API端点
-->
<template>
  <div class="unified-config-test">
    <div class="test-header">
      <h1>🧪 统一配置API测试页面</h1>
      <p class="test-description">阶段一：API端点标准化 - 测试新的统一配置API</p>
    </div>

    <div class="test-panels">
      <!-- API端点测试 -->
      <div class="test-panel">
        <h2>📡 API端点测试</h2>
        
        <div class="test-section">
          <h3>1. 获取配置结构定义</h3>
          <button @click="testGetSchema" :disabled="loading.schema" class="test-btn">
            {{ loading.schema ? '获取中...' : '获取配置结构' }}
          </button>
          <div v-if="results.schema" class="test-result">
            <pre>{{ JSON.stringify(results.schema, null, 2) }}</pre>
          </div>
        </div>

        <div class="test-section">
          <h3>2. 获取默认配置</h3>
          <button @click="testGetConfig" :disabled="loading.config" class="test-btn">
            {{ loading.config ? '获取中...' : '获取默认配置' }}
          </button>
          <div v-if="results.config" class="test-result">
            <h4>配置数据:</h4>
            <pre>{{ JSON.stringify(results.config.config, null, 2) }}</pre>
            <h4>元数据:</h4>
            <pre>{{ JSON.stringify(results.config.metadata, null, 2) }}</pre>
          </div>
        </div>

        <div class="test-section">
          <h3>3. 验证配置</h3>
          <button @click="testValidateConfig" :disabled="loading.validate" class="test-btn">
            {{ loading.validate ? '验证中...' : '验证默认配置' }}
          </button>
          <div v-if="results.validation" class="test-result">
            <div :class="['validation-status', results.validation.valid ? 'valid' : 'invalid']">
              {{ results.validation.valid ? '✅ 配置有效' : '❌ 配置无效' }}
            </div>
            <div v-if="!results.validation.valid" class="validation-errors">
              <h4>验证错误:</h4>
              <ul>
                <li v-for="error in results.validation.errors" :key="error">{{ error }}</li>
              </ul>
            </div>
            <p>{{ results.validation.message }}</p>
          </div>
        </div>

        <div class="test-section">
          <h3>4. 保存配置</h3>
          <button @click="testSaveConfig" :disabled="loading.save" class="test-btn">
            {{ loading.save ? '保存中...' : '保存测试配置' }}
          </button>
          <div v-if="results.save" class="test-result">
            <div class="save-success">
              ✅ 配置保存成功 - ID: {{ results.save.config_id }}
            </div>
          </div>
        </div>

        <div class="test-section">
          <h3>5. 更新配置段落</h3>
          <button @click="testUpdateSection" :disabled="loading.updateSection" class="test-btn">
            {{ loading.updateSection ? '更新中...' : '更新视频配置' }}
          </button>
          <div v-if="results.updateSection" class="test-result">
            <div class="update-success">
              ✅ {{ results.updateSection.message }}
            </div>
          </div>
        </div>
      </div>

      <!-- 配置编辑器 -->
      <div class="test-panel">
        <h2>⚙️ 配置编辑器</h2>
        
        <div v-if="currentConfig" class="config-editor">
          <div class="config-tabs">
            <button 
              v-for="section in configSections" 
              :key="section"
              @click="activeSection = section"
              :class="['tab-btn', { active: activeSection === section }]"
            >
              {{ getSectionLabel(section) }}
            </button>
          </div>

          <div class="config-content">
            <!-- 视频配置 -->
            <div v-if="activeSection === 'video'" class="section-editor">
              <h3>📺 视频配置</h3>
              <div class="form-grid">
                <div class="form-item">
                  <label>分辨率</label>
                  <select v-model="currentConfig.video.resolution">
                    <option value="1920x1080">1920x1080 (Full HD)</option>
                    <option value="1280x720">1280x720 (HD)</option>
                    <option value="3840x2160">3840x2160 (4K)</option>
                  </select>
                </div>
                <div class="form-item">
                  <label>帧率</label>
                  <input type="number" v-model="currentConfig.video.fps" min="24" max="60" />
                </div>
                <div class="form-item">
                  <label>比特率</label>
                  <input type="text" v-model="currentConfig.video.bitrate" placeholder="2000k" />
                </div>
                <div class="form-item">
                  <label>背景颜色</label>
                  <input type="color" v-model="currentConfig.video.background_color" />
                </div>
                <div class="form-item checkbox-item">
                  <label>
                    <input type="checkbox" v-model="currentConfig.video.include_subtitles" />
                    包含字幕
                  </label>
                </div>
              </div>
            </div>

            <!-- 字幕配置 -->
            <div v-if="activeSection === 'subtitle'" class="section-editor">
              <h3>📝 字幕配置</h3>
              <div class="form-grid">
                <div class="form-item checkbox-item">
                  <label>
                    <input type="checkbox" v-model="currentConfig.subtitle.enabled" />
                    启用字幕
                  </label>
                </div>
                <div class="form-item">
                  <label>字体</label>
                  <select v-model="currentConfig.subtitle.font_family">
                    <option value="微软雅黑">微软雅黑</option>
                    <option value="Arial">Arial</option>
                    <option value="宋体">宋体</option>
                  </select>
                </div>
                <div class="form-item">
                  <label>字体大小</label>
                  <input type="number" v-model="currentConfig.subtitle.font_size" min="12" max="72" />
                </div>
                <div class="form-item">
                  <label>字体颜色</label>
                  <input type="color" v-model="currentConfig.subtitle.font_color" />
                </div>
                <div class="form-item">
                  <label>背景颜色</label>
                  <input type="color" v-model="currentConfig.subtitle.background_color" />
                </div>
                <div class="form-item">
                  <label>位置</label>
                  <select v-model="currentConfig.subtitle.position">
                    <option value="top">顶部</option>
                    <option value="center">中间</option>
                    <option value="bottom">底部</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- TTS配置 -->
            <div v-if="activeSection === 'tts'" class="section-editor">
              <h3>🎙️ TTS配置</h3>
              <div class="form-grid">
                <div class="form-item">
                  <label>首选引擎</label>
                  <select v-model="currentConfig.tts.preferred_engine">
                    <option value="edge_tts">Edge TTS</option>
                    <option value="fish_tts">Fish TTS</option>
                    <option value="azure_tts">Azure TTS</option>
                  </select>
                </div>
                
                <!-- Edge TTS 配置 -->
                <div v-if="currentConfig.tts.preferred_engine === 'edge_tts'" class="engine-config">
                  <h4>Edge TTS 设置</h4>
                  <div class="form-item">
                    <label>语音角色</label>
                    <select v-model="currentConfig.tts.engines.edge_tts.voice">
                      <option value="zh-CN-XiaoxiaoNeural">晓晓 (女声)</option>
                      <option value="zh-CN-YunxiNeural">云希 (男声)</option>
                      <option value="zh-CN-YunyangNeural">云扬 (男声)</option>
                    </select>
                  </div>
                  <div class="form-item">
                    <label>语速</label>
                    <input type="text" v-model="currentConfig.tts.engines.edge_tts.rate" placeholder="+0%" />
                  </div>
                  <div class="form-item">
                    <label>音调</label>
                    <input type="text" v-model="currentConfig.tts.engines.edge_tts.pitch" placeholder="+0Hz" />
                  </div>
                </div>
              </div>
            </div>

            <!-- AI配置 -->
            <div v-if="activeSection === 'ai'" class="section-editor">
              <h3>🤖 AI配置</h3>
              <div class="form-grid">
                <div class="form-item">
                  <label>默认服务</label>
                  <select v-model="currentConfig.ai.default_service">
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="custom">自定义</option>
                  </select>
                </div>
                
                <!-- OpenAI 配置 -->
                <div v-if="currentConfig.ai.default_service === 'openai'" class="service-config">
                  <h4>OpenAI 设置</h4>
                  <div class="form-item">
                    <label>API密钥</label>
                    <input type="password" v-model="currentConfig.ai.services.openai.api_key" placeholder="sk-..." />
                  </div>
                  <div class="form-item">
                    <label>API地址</label>
                    <input type="text" v-model="currentConfig.ai.services.openai.base_url" />
                  </div>
                  <div class="form-item">
                    <label>模型</label>
                    <select v-model="currentConfig.ai.services.openai.model">
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                      <option value="gpt-4">GPT-4</option>
                      <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- 高级配置 -->
            <div v-if="activeSection === 'advanced'" class="section-editor">
              <h3>🔧 高级配置</h3>
              <div class="form-grid">
                <div class="form-item">
                  <label>输出路径</label>
                  <input type="text" v-model="currentConfig.advanced.output_path" placeholder="留空使用默认路径" />
                </div>
                <div class="form-item">
                  <label>命名规则</label>
                  <select v-model="currentConfig.advanced.naming_rule">
                    <option value="timestamp">时间戳</option>
                    <option value="title">标题</option>
                    <option value="custom">自定义</option>
                  </select>
                </div>
                <div class="form-item">
                  <label>最大并发数</label>
                  <input type="number" v-model="currentConfig.advanced.max_concurrency" min="1" max="8" />
                </div>
                <div class="form-item">
                  <label>内存限制 (MB)</label>
                  <input type="number" v-model="currentConfig.advanced.memory_limit" min="512" max="8192" step="256" />
                </div>
                <div class="form-item checkbox-item">
                  <label>
                    <input type="checkbox" v-model="currentConfig.advanced.auto_clean_temp" />
                    自动清理临时文件
                  </label>
                </div>
                <div class="form-item checkbox-item">
                  <label>
                    <input type="checkbox" v-model="currentConfig.advanced.enable_progress" />
                    显示详细进度
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div class="config-actions">
            <button @click="validateCurrentConfig" class="btn btn-outline">验证配置</button>
            <button @click="saveCurrentConfig" class="btn btn-primary">保存配置</button>
          </div>
        </div>
      </div>

      <!-- 阶段二：实时验证与测试 -->
      <div class="test-panel validation-panel">
        <h2>🚀 阶段二：实时验证与测试</h2>
        <p class="panel-description">实时配置验证、冲突检测和性能分析</p>
        
        <RealTimeValidationSimple 
          v-if="currentConfig" 
          :config="currentConfig" 
        />
      </div>
    </div>

    <!-- 错误显示 -->
    <div v-if="error" class="error-panel">
      <h3>❌ 错误信息</h3>
      <pre>{{ error }}</pre>
      <button @click="error = null" class="btn btn-outline">清除错误</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { UnifiedConfigAPI, type UnifiedConfig, type ConfigSchema } from '@/api/unifiedConfig'
import RealTimeValidationSimple from '@/components/RealTimeValidationSimple.vue'

// 响应式数据
const loading = ref({
  schema: false,
  config: false,
  validate: false,
  save: false,
  updateSection: false
})

const results = ref<{
  schema?: ConfigSchema
  config?: { config: UnifiedConfig; metadata: any }
  validation?: { valid: boolean; errors: string[]; message: string }
  save?: { config_id: string }
  updateSection?: { message: string }
}>({})

const error = ref<string | null>(null)
const currentConfig = ref<UnifiedConfig | null>(null)
const activeSection = ref<keyof UnifiedConfig>('video')

const configSections: (keyof UnifiedConfig)[] = ['video', 'subtitle', 'tts', 'ai', 'advanced']

// 计算属性
const getSectionLabel = (section: keyof UnifiedConfig): string => {
  const labels = {
    video: '📺 视频',
    subtitle: '📝 字幕',
    tts: '🎙️ TTS',
    ai: '🤖 AI',
    advanced: '🔧 高级'
  }
  return labels[section] || section
}

// 方法
const testGetSchema = async () => {
  loading.value.schema = true
  error.value = null
  
  try {
    const schema = await UnifiedConfigAPI.getConfigSchema()
    results.value.schema = schema
  }
  catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
  finally {
    loading.value.schema = false
  }
}

const testGetConfig = async () => {
  loading.value.config = true
  error.value = null
  
  try {
    const configData = await UnifiedConfigAPI.getUnifiedConfig()
    results.value.config = configData
    currentConfig.value = JSON.parse(JSON.stringify(configData.config)) // 深拷贝
  }
  catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
  finally {
    loading.value.config = false
  }
}

const testValidateConfig = async () => {
  if (!currentConfig.value) {
    error.value = '请先获取配置'
    return
  }
  
  loading.value.validate = true
  error.value = null
  
  try {
    const validation = await UnifiedConfigAPI.validateConfig(currentConfig.value)
    results.value.validation = validation
  }
  catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
  finally {
    loading.value.validate = false
  }
}

const testSaveConfig = async () => {
  if (!currentConfig.value) {
    error.value = '请先获取配置'
    return
  }
  
  loading.value.save = true
  error.value = null
  
  try {
    const configId = await UnifiedConfigAPI.saveUnifiedConfig(currentConfig.value, {
      name: '阶段一测试配置',
      description: 'API端点标准化测试',
      tags: ['test', 'stage1', 'api-standardization']
    })
    results.value.save = { config_id: configId }
  }
  catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
  finally {
    loading.value.save = false
  }
}

const testUpdateSection = async () => {
  if (!currentConfig.value) {
    error.value = '请先获取配置'
    return
  }
  
  loading.value.updateSection = true
  error.value = null
  
  try {
    const updateResult = await UnifiedConfigAPI.updateConfigSection('video', {
      ...currentConfig.value.video,
      bitrate: '4000k', // 修改比特率作为测试
      fps: 60 // 修改帧率作为测试
    })
    results.value.updateSection = updateResult
  }
  catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
  finally {
    loading.value.updateSection = false
  }
}

const validateCurrentConfig = async () => {
  await testValidateConfig()
}

const saveCurrentConfig = async () => {
  await testSaveConfig()
}

// 初始化
onMounted(async () => {
  // 自动获取默认配置
  await testGetConfig()
})
</script>

<style scoped>
.unified-config-test {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.test-header {
  text-align: center;
  margin-bottom: 30px;
}

.test-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.test-description {
  color: #7f8c8d;
  font-size: 16px;
}

.test-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.test-panel {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.test-panel h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 20px;
}

.test-section {
  margin-bottom: 25px;
  padding: 15px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #3498db;
}

.test-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 16px;
}

.test-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.test-btn:hover:not(:disabled) {
  background: #2980b9;
}

.test-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.test-result {
  margin-top: 15px;
  padding: 15px;
  background: #ecf0f1;
  border-radius: 6px;
  border: 1px solid #bdc3c7;
}

.test-result pre {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  margin: 10px 0;
}

.test-result h4 {
  color: #2c3e50;
  margin: 15px 0 10px 0;
  font-size: 14px;
}

.validation-status.valid {
  color: #27ae60;
  font-weight: bold;
}

.validation-status.invalid {
  color: #e74c3c;
  font-weight: bold;
}

.validation-errors ul {
  margin: 10px 0;
  padding-left: 20px;
}

.validation-errors li {
  color: #e74c3c;
  margin-bottom: 5px;
}

.save-success, .update-success {
  color: #27ae60;
  font-weight: bold;
  padding: 10px;
  background: #d5f5d5;
  border-radius: 4px;
}

/* 配置编辑器样式 */
.config-tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 2px solid #ecf0f1;
}

.tab-btn {
  padding: 10px 20px;
  background: none;
  border: none;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  font-size: 14px;
}

.tab-btn.active {
  border-bottom-color: #3498db;
  color: #3498db;
  font-weight: bold;
}

.tab-btn:hover:not(.active) {
  background: #ecf0f1;
}

.section-editor {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.section-editor h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 18px;
}

.section-editor h4 {
  color: #34495e;
  margin: 20px 0 15px 0;
  font-size: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-item label {
  font-weight: 500;
  margin-bottom: 5px;
  color: #2c3e50;
  font-size: 14px;
}

.form-item input,
.form-item select {
  padding: 8px 12px;
  border: 2px solid #ecf0f1;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-item input:focus,
.form-item select:focus {
  outline: none;
  border-color: #3498db;
}

.checkbox-item {
  flex-direction: row;
  align-items: center;
}

.checkbox-item label {
  margin-bottom: 0;
  margin-left: 8px;
  cursor: pointer;
}

.checkbox-item input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
}

.engine-config,
.service-config {
  grid-column: 1 / -1;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-top: 15px;
}

.config-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  padding: 20px;
}

.btn {
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.btn-outline {
  background: transparent;
  color: #3498db;
  border-color: #3498db;
}

.btn-outline:hover {
  background: #3498db;
  color: white;
}

.btn-primary {
  background: #27ae60;
  color: white;
  border-color: #27ae60;
}

.btn-primary:hover {
  background: #229954;
  border-color: #229954;
}

.error-panel {
  margin-top: 30px;
  padding: 20px;
  background: #fdf2f2;
  border: 2px solid #e74c3c;
  border-radius: 8px;
}

.error-panel h3 {
  color: #e74c3c;
  margin-bottom: 15px;
}

.error-panel pre {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 12px;
  margin-bottom: 15px;
}

/* 实时验证面板样式 */
.validation-panel {
  grid-column: 1 / -1; /* 占满整行 */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.validation-panel h2 {
  color: white;
  margin-bottom: 8px;
}

.panel-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  margin-bottom: 20px;
}

.validation-panel .real-time-validation {
  background: rgba(255, 255, 255, 0.95);
  color: #1f2937;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

@media (max-width: 1200px) {
  .test-panels {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .config-actions {
    flex-direction: column;
  }
  
  .test-panels {
    gap: 20px;
  }
  
  .test-panel {
    padding: 15px;
  }
}
</style>
