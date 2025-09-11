<template>
  <div class="api-test-panel">
    <h2>🧪 API基类功能测试</h2>
    
    <div class="test-section">
      <h3>📊 API服务状态</h3>
      <div class="status-grid">
        <div class="status-item" :class="{ 'healthy': healthStatus.primary, 'unhealthy': !healthStatus.primary }">
          <span class="label">主API服务 (8004)</span>
          <span class="status">{{ healthStatus.primary ? '✅ 正常' : '❌ 异常' }}</span>
        </div>
        <div class="status-item" :class="{ 'healthy': healthStatus.fallback, 'unhealthy': !healthStatus.fallback }">
          <span class="label">备用API服务 (5000)</span>
          <span class="status">{{ healthStatus.fallback ? '✅ 正常' : '❌ 异常' }}</span>
        </div>
      </div>
      <button @click="checkHealth" :disabled="isChecking">
        {{ isChecking ? '检查中...' : '重新检查健康状态' }}
      </button>
    </div>

    <div class="test-section">
      <h3>🚀 API调用测试</h3>
      <div class="test-buttons">
        <button @click="testGetRequest" :disabled="isLoading">测试 GET 请求</button>
        <button @click="testPostRequest" :disabled="isLoading">测试 POST 请求</button>
        <button @click="testErrorHandling" :disabled="isLoading">测试错误处理</button>
      </div>
    </div>

    <div class="test-section">
      <h3>📝 测试结果</h3>
      <div class="test-results">
        <div v-for="(result, index) in testResults" :key="index" 
             :class="['result-item', result.type]">
          <div class="result-header">
            <span class="result-title">{{ result.title }}</span>
            <span class="result-time">{{ result.time }}</span>
          </div>
          <div class="result-content">{{ result.content }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 测试结果类型
interface TestResult {
  title: string
  content: string
  type: 'success' | 'error' | 'info'
  time: string
}

// 响应式数据
const healthStatus = ref({
  primary: false,
  fallback: false
})

const isChecking = ref(false)
const isLoading = ref(false)
const testResults = ref<TestResult[]>([])

// 添加测试结果
const addResult = (title: string, content: string, type: 'success' | 'error' | 'info' = 'info') => {
  testResults.value.unshift({
    title,
    content,
    type,
    time: new Date().toLocaleTimeString()
  })
  
  // 保持最多20条记录
  if (testResults.value.length > 20) {
    testResults.value.pop()
  }
}

// 健康检查
const checkHealth = async () => {
  isChecking.value = true
  addResult('健康检查', '开始检查API服务状态...', 'info')
  
  try {
    // 手动检查主API服务
    try {
      const response = await fetch('http://localhost:8004/api/health')
      healthStatus.value.primary = response.ok
      addResult('主API服务', `状态: ${response.ok ? '正常' : '异常'}`, response.ok ? 'success' : 'error')
    }
    catch (error: unknown) {
      healthStatus.value.primary = false
      addResult('主API服务', `连接失败: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
    }
    
    // 检查备用API服务
    try {
      const response = await fetch('http://localhost:5000/health')
      healthStatus.value.fallback = response.ok
      addResult('备用API服务', `状态: ${response.ok ? '正常' : '异常'}`, response.ok ? 'success' : 'error')
    }
    catch (error: unknown) {
      healthStatus.value.fallback = false
      addResult('备用API服务', `连接失败: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
    }
    
  }
  finally {
    isChecking.value = false
  }
}

// 测试GET请求
const testGetRequest = async () => {
  isLoading.value = true
  addResult('GET请求测试', '开始测试GET请求...', 'info')
  
  try {
    const response = await fetch('http://localhost:8004/api/health')
    if (response.ok) {
      const data = await response.json()
      addResult('GET请求成功', `响应数据: ${JSON.stringify(data, null, 2)}`, 'success')
    }
    else {
      addResult('GET请求失败', `HTTP ${response.status}: ${response.statusText}`, 'error')
    }
  }
  catch (error: unknown) {
    addResult('GET请求异常', `错误: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
  }
  finally {
    isLoading.value = false
  }
}

// 测试POST请求
const testPostRequest = async () => {
  isLoading.value = true
  addResult('POST请求测试', '开始测试POST请求...', 'info')
  
  try {
    const response = await fetch('http://localhost:8004/api/config/presets', {
      method: 'GET', // 先用GET测试已知端点
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      addResult('POST请求成功', `响应数据: ${JSON.stringify(data, null, 2)}`, 'success')
    }
    else {
      addResult('POST请求失败', `HTTP ${response.status}: ${response.statusText}`, 'error')
    }
  }
  catch (error: unknown) {
    addResult('POST请求异常', `错误: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
  }
  finally {
    isLoading.value = false
  }
}

// 测试错误处理
const testErrorHandling = async () => {
  isLoading.value = true
  addResult('错误处理测试', '测试不存在的端点...', 'info')
  
  try {
    const response = await fetch('http://localhost:8004/api/nonexistent')
    if (!response.ok) {
      addResult('错误处理正常', `正确返回错误: HTTP ${response.status}`, 'success')
    }
    else {
      addResult('错误处理异常', '应该返回错误但返回了成功', 'error')
    }
  }
  catch (error: unknown) {
    addResult('网络错误处理', `捕获到网络错误: ${error instanceof Error ? error.message : '未知错误'}`, 'success')
  }
  finally {
    isLoading.value = false
  }
}

// 组件挂载时自动检查健康状态
onMounted(() => {
  checkHealth()
})
</script>

<style scoped>
.api-test-panel {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  background: #fff;
}

.test-section h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #ddd;
}

.status-item.healthy {
  background: #f0f9f0;
  border-color: #28a745;
}

.status-item.unhealthy {
  background: #fdf2f2;
  border-color: #dc3545;
}

.test-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

button {
  padding: 10px 16px;
  border: 1px solid #007bff;
  background: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover:not(:disabled) {
  background: #0056b3;
}

button:disabled {
  background: #6c757d;
  border-color: #6c757d;
  cursor: not-allowed;
}

.test-results {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e1e5e9;
  border-radius: 4px;
}

.result-item {
  padding: 12px;
  border-bottom: 1px solid #e1e5e9;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item.success {
  background: #f8f9fa;
  border-left: 4px solid #28a745;
}

.result-item.error {
  background: #f8f9fa;
  border-left: 4px solid #dc3545;
}

.result-item.info {
  background: #f8f9fa;
  border-left: 4px solid #17a2b8;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.result-title {
  font-weight: 600;
  color: #333;
}

.result-time {
  font-size: 12px;
  color: #666;
}

.result-content {
  font-size: 14px;
  color: #555;
  word-break: break-word;
  white-space: pre-wrap;
}
</style>
