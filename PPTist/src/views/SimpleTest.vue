<template>
  <div class="simple-test">
    <h2>🔗 前后端连接测试</h2>
    
    <div class="test-card">
      <h3>📊 基础连接测试</h3>
      <button @click="testBasicConnection" :disabled="loading">
        {{ loading ? '测试中...' : '测试后端连接' }}
      </button>
      
      <div v-if="result" class="result" :class="result.success ? 'success' : 'error'">
        <div class="result-header">
          <span>{{ result.success ? '✅ 连接成功' : '❌ 连接失败' }}</span>
          <span class="time">{{ result.timestamp }}</span>
        </div>
        <pre v-if="result.data">{{ JSON.stringify(result.data, null, 2) }}</pre>
        <div v-if="result.error" class="error-text">{{ result.error }}</div>
      </div>
    </div>

    <div class="test-card" v-if="result && result.success">
      <h3>🎥 VideoLingo集成测试</h3>
      <div class="button-group">
        <button @click="testVideoLingoHealth" :disabled="vlLoading.health">
          {{ vlLoading.health ? '⏳' : '🏥' }} 健康检查
        </button>
        <button @click="testVideoLingoVersion" :disabled="vlLoading.version">
          {{ vlLoading.version ? '⏳' : 'ℹ️' }} 版本信息
        </button>
      </div>
      
      <div v-if="vlResults.health" class="mini-result">
        <strong>健康状态:</strong> 
        <span :class="vlResults.health.success ? 'success-text' : 'error-text'">
          {{ vlResults.health.success ? '正常' : '异常' }}
        </span>
      </div>
      
      <div v-if="vlResults.version" class="mini-result">
        <strong>版本信息:</strong> 
        <code>{{ vlResults.version.data?.version || '未知' }}</code>
      </div>
    </div>

    <div class="test-card" v-if="result && result.success">
      <h3>🎤 TTS功能测试</h3>
      <button @click="testTTSFeature" :disabled="ttsLoading">
        {{ ttsLoading ? '⏳ 测试中...' : '🔊 测试语音合成' }}
      </button>
      
      <div v-if="ttsResult" class="mini-result">
        <strong>TTS测试:</strong>
        <span :class="ttsResult.success ? 'success-text' : 'error-text'">
          {{ ttsResult.success ? '✅ 可用' : '❌ 不可用' }}
        </span>
        <div v-if="ttsResult.error" class="error-detail">{{ ttsResult.error }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import unifiedFlaskAPI from '@/api/services/unifiedFlask'

const loading = ref(false)
const result = ref<any>(null)

const vlLoading = reactive({ health: false, version: false })
const vlResults = reactive<any>({})

const ttsLoading = ref(false)
const ttsResult = ref<any>(null)

// 基础连接测试
const testBasicConnection = async () => {
  loading.value = true
  result.value = null
  
  try {
    const response = await unifiedFlaskAPI.checkHealth()
    result.value = {
      success: true,
      timestamp: new Date().toLocaleString(),
      data: response.data
    }
  }
  catch (error) {
    result.value = {
      success: false,
      timestamp: new Date().toLocaleString(),
      error: String(error)
    }
  }
  finally {
    loading.value = false
  }
}

// VideoLingo健康测试
const testVideoLingoHealth = async () => {
  vlLoading.health = true
  try {
    const response = await unifiedFlaskAPI.checkVideoLingoHealth()
    vlResults.health = {
      success: response.success,
      data: response.data
    }
  }
  catch (error) {
    vlResults.health = {
      success: false,
      error: String(error)
    }
  }
  finally {
    vlLoading.health = false
  }
}

// VideoLingo版本测试
const testVideoLingoVersion = async () => {
  vlLoading.version = true
  try {
    const response = await unifiedFlaskAPI.getVideoLingoVersion()
    vlResults.version = {
      success: response.success,
      data: response.data
    }
  }
  catch (error) {
    vlResults.version = {
      success: false,
      error: String(error)
    }
  }
  finally {
    vlLoading.version = false
  }
}

// TTS功能测试
const testTTSFeature = async () => {
  ttsLoading.value = true
  try {
    // 先测试获取语音列表
    const voicesResponse = await unifiedFlaskAPI.getTTSVoices()
    if (voicesResponse.success) {
      ttsResult.value = {
        success: true,
        message: `获取到 ${voicesResponse.data?.length || 0} 个语音`
      }
    }
    else {
      throw new Error('获取语音列表失败')
    }
  }
  catch (error) {
    ttsResult.value = {
      success: false,
      error: String(error)
    }
  }
  finally {
    ttsLoading.value = false
  }
}
</script>

<style scoped>
.simple-test {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.test-card {
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
}

.test-card h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: #2196f3;
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

button:hover:not(:disabled) {
  background: #1976d2;
  transform: translateY(-1px);
}

button:disabled {
  background: #bbb;
  cursor: not-allowed;
  transform: none;
}

.result {
  margin-top: 15px;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #ddd;
}

.result.success {
  background: #f1f8e9;
  border-color: #4caf50;
}

.result.error {
  background: #ffebee;
  border-color: #f44336;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 500;
}

.time {
  font-size: 12px;
  color: #666;
}

pre {
  margin: 0;
  font-size: 12px;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

.mini-result {
  margin: 8px 0;
  padding: 8px 12px;
  background: #f9f9f9;
  border-radius: 4px;
  font-size: 14px;
}

.success-text {
  color: #4caf50;
  font-weight: 500;
}

.error-text {
  color: #f44336;
  font-weight: 500;
}

.error-detail {
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

code {
  background: #e8e8e8;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}
</style>
