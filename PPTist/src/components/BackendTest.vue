<template>
  <div class="backend-test-panel">
    <h3>后端连接测试</h3>
    
    <div class="test-section">
      <h4>健康检查</h4>
      <button @click="testHealth" :disabled="loading.health">
        {{ loading.health ? '检查中...' : '检查健康状态' }}
      </button>
      <div v-if="results.health" class="result">
        <pre>{{ JSON.stringify(results.health, null, 2) }}</pre>
      </div>
    </div>

    <div class="test-section">
      <h4>VideoLingo集成测试</h4>
      <button @click="testVideoLingo" :disabled="loading.videoLingo">
        {{ loading.videoLingo ? '测试中...' : '测试VideoLingo' }}
      </button>
      <div v-if="results.videoLingo" class="result">
        <pre>{{ JSON.stringify(results.videoLingo, null, 2) }}</pre>
      </div>
    </div>

    <div class="test-section">
      <h4>配置获取测试</h4>
      <button @click="testConfig" :disabled="loading.config">
        {{ loading.config ? '加载中...' : '获取配置' }}
      </button>
      <div v-if="results.config" class="result">
        <pre>{{ JSON.stringify(results.config, null, 2) }}</pre>
      </div>
    </div>

    <div v-if="error" class="error">
      <h4>错误信息：</h4>
      <pre>{{ error }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import unifiedFlaskAPI from '@/api/services/unifiedFlask'

// 响应式数据
const loading = reactive({
  health: false,
  videoLingo: false,
  config: false
})

const results = reactive({
  health: null as any,
  videoLingo: null as any,
  config: null as any
})

const error = ref('')

// 测试健康检查
const testHealth = async () => {
  loading.health = true
  error.value = ''
  
  try {
    const response = await unifiedFlaskAPI.checkHealth()
    results.health = response
    // eslint-disable-next-line no-console
    console.log('健康检查结果:', response)
  }
  catch (err) {
    error.value = `健康检查失败: ${err}`
    // eslint-disable-next-line no-console
    console.error('健康检查失败:', err)
  }
  finally {
    loading.health = false
  }
}

// 测试VideoLingo集成
const testVideoLingo = async () => {
  loading.videoLingo = true
  error.value = ''
  
  try {
    const healthResponse = await unifiedFlaskAPI.checkVideoLingoHealth()
    const versionResponse = await unifiedFlaskAPI.getVideoLingoVersion()
    const statusResponse = await unifiedFlaskAPI.getVideoLingoStatus()
    
    results.videoLingo = {
      health: healthResponse,
      version: versionResponse,
      status: statusResponse
    }
    // eslint-disable-next-line no-console
    console.log('VideoLingo测试结果:', results.videoLingo)
  }
  catch (err) {
    error.value = `VideoLingo测试失败: ${err}`
    // eslint-disable-next-line no-console
    console.error('VideoLingo测试失败:', err)
  }
  finally {
    loading.videoLingo = false
  }
}

// 测试配置获取
const testConfig = async () => {
  loading.config = true
  error.value = ''
  
  try {
    const configResponse = await unifiedFlaskAPI.getConfig()
    const workspaceResponse = await unifiedFlaskAPI.getWorkspaceStatus()
    const projectsResponse = await unifiedFlaskAPI.getProjects()
    
    results.config = {
      config: configResponse,
      workspace: workspaceResponse,
      projects: projectsResponse
    }
    // eslint-disable-next-line no-console
    console.log('配置测试结果:', results.config)
  }
  catch (err) {
    error.value = `配置测试失败: ${err}`
    // eslint-disable-next-line no-console
    console.error('配置测试失败:', err)
  }
  finally {
    loading.config = false
  }
}
</script>

<style scoped>
.backend-test-panel {
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin: 20px;
}

.test-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 5px;
}

.test-section h4 {
  margin-top: 0;
  color: #333;
}

button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

button:hover {
  background: #0056b3;
}

button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.result {
  margin-top: 10px;
  padding: 10px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.error {
  margin-top: 20px;
  padding: 15px;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
}

pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
