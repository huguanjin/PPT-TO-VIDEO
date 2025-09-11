/**
 * API集成测试组件 - 验证所有API服务功能
 */
<template>
  <div class="api-integration-test">
    <div class="test-header">
      <h2>🧪 API集成测试套件</h2>
      <p>全面测试API服务模块的功能和性能</p>
    </div>

    <div class="test-sections">
      <!-- 基础连接测试 -->
      <div class="test-section">
        <h3>🔗 基础连接测试</h3>
        <div class="test-grid">
          <div class="test-card" :class="getTestCardClass(basicTests.primary)">
            <div class="test-title">主API服务 (8004)</div>
            <div class="test-status">{{ basicTests.primary.status }}</div>
            <div class="test-result">{{ basicTests.primary.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(basicTests.fallback)">
            <div class="test-title">备用API服务 (5000)</div>
            <div class="test-status">{{ basicTests.fallback.status }}</div>
            <div class="test-result">{{ basicTests.fallback.message }}</div>
          </div>
        </div>
        <button @click="runBasicTests" :disabled="isRunning" class="test-btn">
          {{ isRunning ? '测试中...' : '运行基础测试' }}
        </button>
      </div>

      <!-- AI服务测试 -->
      <div class="test-section">
        <h3>🤖 AI服务测试</h3>
        <div class="test-grid">
          <div class="test-card" :class="getTestCardClass(aiTests.config)">
            <div class="test-title">配置管理</div>
            <div class="test-status">{{ aiTests.config.status }}</div>
            <div class="test-result">{{ aiTests.config.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(aiTests.openai)">
            <div class="test-title">OpenAI测试</div>
            <div class="test-status">{{ aiTests.openai.status }}</div>
            <div class="test-result">{{ aiTests.openai.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(aiTests.anthropic)">
            <div class="test-title">Anthropic测试</div>
            <div class="test-status">{{ aiTests.anthropic.status }}</div>
            <div class="test-result">{{ aiTests.anthropic.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(aiTests.custom)">
            <div class="test-title">自定义API测试</div>
            <div class="test-status">{{ aiTests.custom.status }}</div>
            <div class="test-result">{{ aiTests.custom.message }}</div>
          </div>
        </div>
        <button @click="runAITests" :disabled="isRunning" class="test-btn">
          {{ isRunning ? '测试中...' : '运行AI服务测试' }}
        </button>
      </div>

      <!-- TTS服务测试 -->
      <div class="test-section">
        <h3>🎵 TTS服务测试</h3>
        <div class="test-grid">
          <div class="test-card" :class="getTestCardClass(ttsTests.edge)">
            <div class="test-title">Edge TTS</div>
            <div class="test-status">{{ ttsTests.edge.status }}</div>
            <div class="test-result">{{ ttsTests.edge.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(ttsTests.fish)">
            <div class="test-title">Fish TTS</div>
            <div class="test-status">{{ ttsTests.fish.status }}</div>
            <div class="test-result">{{ ttsTests.fish.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(ttsTests.openai)">
            <div class="test-title">OpenAI TTS</div>
            <div class="test-status">{{ ttsTests.openai.status }}</div>
            <div class="test-result">{{ ttsTests.openai.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(ttsTests.voices)">
            <div class="test-title">语音列表</div>
            <div class="test-status">{{ ttsTests.voices.status }}</div>
            <div class="test-result">{{ ttsTests.voices.message }}</div>
          </div>
        </div>
        <button @click="runTTSTests" :disabled="isRunning" class="test-btn">
          {{ isRunning ? '测试中...' : '运行TTS服务测试' }}
        </button>
      </div>

      <!-- 工作流服务测试 -->
      <div class="test-section">
        <h3>⚙️ 工作流服务测试</h3>
        <div class="test-grid">
          <div class="test-card" :class="getTestCardClass(workflowTests.projects)">
            <div class="test-title">项目管理</div>
            <div class="test-status">{{ workflowTests.projects.status }}</div>
            <div class="test-result">{{ workflowTests.projects.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(workflowTests.execution)">
            <div class="test-title">工作流执行</div>
            <div class="test-status">{{ workflowTests.execution.status }}</div>
            <div class="test-result">{{ workflowTests.execution.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(workflowTests.export)">
            <div class="test-title">导出功能</div>
            <div class="test-status">{{ workflowTests.export.status }}</div>
            <div class="test-result">{{ workflowTests.export.message }}</div>
          </div>
          <div class="test-card" :class="getTestCardClass(workflowTests.debug)">
            <div class="test-title">调试信息</div>
            <div class="test-status">{{ workflowTests.debug.status }}</div>
            <div class="test-result">{{ workflowTests.debug.message }}</div>
          </div>
        </div>
        <button @click="runWorkflowTests" :disabled="isRunning" class="test-btn">
          {{ isRunning ? '测试中...' : '运行工作流测试' }}
        </button>
      </div>

      <!-- 性能测试 -->
      <div class="test-section">
        <h3>⚡ 性能测试</h3>
        <div class="performance-metrics">
          <div class="metric">
            <span class="metric-label">平均响应时间:</span>
            <span class="metric-value">{{ performanceMetrics.avgResponseTime }}ms</span>
          </div>
          <div class="metric">
            <span class="metric-label">成功率:</span>
            <span class="metric-value">{{ performanceMetrics.successRate }}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">总请求数:</span>
            <span class="metric-value">{{ performanceMetrics.totalRequests }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">错误重试次数:</span>
            <span class="metric-value">{{ performanceMetrics.retryCount }}</span>
          </div>
        </div>
        <button @click="runPerformanceTests" :disabled="isRunning" class="test-btn">
          {{ isRunning ? '测试中...' : '运行性能测试' }}
        </button>
      </div>

      <!-- 全面测试 -->
      <div class="test-section">
        <h3>🚀 全面集成测试</h3>
        <div class="comprehensive-test">
          <div class="test-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: `${testProgress}%` }"></div>
            </div>
            <div class="progress-text">{{ testProgress }}% 完成</div>
          </div>
          <div class="test-summary">
            <div class="summary-item">
              <span class="summary-label">通过:</span>
              <span class="summary-value success">{{ testSummary.passed }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">失败:</span>
              <span class="summary-value error">{{ testSummary.failed }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">跳过:</span>
              <span class="summary-value warning">{{ testSummary.skipped }}</span>
            </div>
          </div>
        </div>
        <button @click="runAllTests" :disabled="isRunning" class="test-btn primary">
          {{ isRunning ? '全面测试中...' : '开始全面测试' }}
        </button>
      </div>
    </div>

    <!-- 测试日志 -->
    <div class="test-logs">
      <h3>📋 测试日志</h3>
      <div class="log-container">
        <div 
          v-for="(log, index) in testLogs" 
          :key="index"
          :class="['log-entry', log.level]"
        >
          <span class="log-time">{{ log.timestamp }}</span>
          <span class="log-level">{{ log.level.toUpperCase() }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
      <button @click="clearLogs" class="clear-btn">清空日志</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { checkApiHealth } from '@/api'
import { aiService, ttsService, workflowService } from '@/api/services'

interface TestResult {
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped'
  message: string
  duration?: number
}

interface TestLog {
  timestamp: string
  level: 'info' | 'success' | 'error' | 'warning'
  message: string
}

// 测试状态
const isRunning = ref(false)
const testProgress = ref(0)

// 基础测试结果
const basicTests = ref({
  primary: { status: 'pending', message: '等待测试' } as TestResult,
  fallback: { status: 'pending', message: '等待测试' } as TestResult
})

// AI服务测试结果
const aiTests = ref({
  config: { status: 'pending', message: '等待测试' } as TestResult,
  openai: { status: 'pending', message: '等待测试' } as TestResult,
  anthropic: { status: 'pending', message: '等待测试' } as TestResult,
  custom: { status: 'pending', message: '等待测试' } as TestResult
})

// TTS服务测试结果
const ttsTests = ref({
  edge: { status: 'pending', message: '等待测试' } as TestResult,
  fish: { status: 'pending', message: '等待测试' } as TestResult,
  openai: { status: 'pending', message: '等待测试' } as TestResult,
  voices: { status: 'pending', message: '等待测试' } as TestResult
})

// 工作流测试结果
const workflowTests = ref({
  projects: { status: 'pending', message: '等待测试' } as TestResult,
  execution: { status: 'pending', message: '等待测试' } as TestResult,
  export: { status: 'pending', message: '等待测试' } as TestResult,
  debug: { status: 'pending', message: '等待测试' } as TestResult
})

// 性能指标
const performanceMetrics = ref({
  avgResponseTime: 0,
  successRate: 0,
  totalRequests: 0,
  retryCount: 0
})

// 测试摘要
const testSummary = ref({
  passed: 0,
  failed: 0,
  skipped: 0
})

// 测试日志
const testLogs = ref<TestLog[]>([])

// 添加日志
const addLog = (level: TestLog['level'], message: string) => {
  testLogs.value.unshift({
    timestamp: new Date().toLocaleTimeString(),
    level,
    message
  })
  
  // 保持最多100条日志
  if (testLogs.value.length > 100) {
    testLogs.value.pop()
  }
}

// 清空日志
const clearLogs = () => {
  testLogs.value = []
}

// 获取测试卡片样式类
const getTestCardClass = (test: TestResult) => {
  return {
    'test-pending': test.status === 'pending',
    'test-running': test.status === 'running',
    'test-success': test.status === 'success',
    'test-error': test.status === 'error',
    'test-skipped': test.status === 'skipped'
  }
}

// 运行基础连接测试
const runBasicTests = async () => {
  if (isRunning.value) return
  
  isRunning.value = true
  addLog('info', '开始基础连接测试')
  
  try {
    // 测试API健康状态
    basicTests.value.primary.status = 'running'
    basicTests.value.fallback.status = 'running'
    
    const startTime = Date.now()
    const health = await checkApiHealth()
    const duration = Date.now() - startTime
    
    // 更新测试结果
    basicTests.value.primary.status = health.primary ? 'success' : 'error'
    basicTests.value.primary.message = health.primary ? '连接正常' : '连接失败'
    basicTests.value.primary.duration = duration
    
    basicTests.value.fallback.status = health.fallback ? 'success' : 'error'
    basicTests.value.fallback.message = health.fallback ? '连接正常' : '连接失败'
    basicTests.value.fallback.duration = duration
    
    addLog(health.primary ? 'success' : 'error', `主API服务测试${health.primary ? '通过' : '失败'} (${duration}ms)`)
    addLog(health.fallback ? 'success' : 'error', `备用API服务测试${health.fallback ? '通过' : '失败'} (${duration}ms)`)
    
  }
  catch (error: any) {
    basicTests.value.primary.status = 'error'
    basicTests.value.primary.message = '测试异常'
    basicTests.value.fallback.status = 'error'
    basicTests.value.fallback.message = '测试异常'
    
    addLog('error', `基础连接测试失败: ${error.message}`)
  }
  finally {
    isRunning.value = false
  }
}

// 运行AI服务测试
const runAITests = async () => {
  if (isRunning.value) return
  
  isRunning.value = true
  addLog('info', '开始AI服务测试')
  
  try {
    // 测试配置管理
    aiTests.value.config.status = 'running'
    try {
      const startTime = Date.now()
      await aiService.getConfig()
      const duration = Date.now() - startTime
      
      aiTests.value.config.status = 'success'
      aiTests.value.config.message = `配置获取成功 (${duration}ms)`
      addLog('success', `AI配置管理测试通过 (${duration}ms)`)
    }
    catch (error: any) {
      aiTests.value.config.status = 'error'
      aiTests.value.config.message = '配置获取失败'
      addLog('error', `AI配置管理测试失败: ${error.message}`)
    }
    
    // 测试健康检查
    aiTests.value.openai.status = 'running'
    try {
      const startTime = Date.now()
      const healthy = await aiService.healthCheck()
      const duration = Date.now() - startTime
      
      aiTests.value.openai.status = healthy ? 'success' : 'error'
      aiTests.value.openai.message = `健康检查${healthy ? '通过' : '失败'} (${duration}ms)`
      addLog(healthy ? 'success' : 'error', `AI健康检查${healthy ? '通过' : '失败'} (${duration}ms)`)
    }
    catch (error: any) {
      aiTests.value.openai.status = 'error'
      aiTests.value.openai.message = '健康检查异常'
      addLog('error', `AI健康检查异常: ${error.message}`)
    }
    
    // 其他AI测试标记为跳过（需要实际配置）
    aiTests.value.anthropic.status = 'skipped'
    aiTests.value.anthropic.message = '需要API密钥配置'
    aiTests.value.custom.status = 'skipped'
    aiTests.value.custom.message = '需要API密钥配置'
    
  }
  finally {
    isRunning.value = false
  }
}

// 运行TTS服务测试
const runTTSTests = async () => {
  if (isRunning.value) return
  
  isRunning.value = true
  addLog('info', '开始TTS服务测试')
  
  try {
    // 测试语音列表获取
    ttsTests.value.voices.status = 'running'
    try {
      const startTime = Date.now()
      const voices = await ttsService.getEdgeVoices()
      const duration = Date.now() - startTime
      
      ttsTests.value.voices.status = 'success'
      ttsTests.value.voices.message = `获取${voices.length}个语音 (${duration}ms)`
      addLog('success', `TTS语音列表测试通过 (${duration}ms)`)
    }
    catch (error: any) {
      ttsTests.value.voices.status = 'error'
      ttsTests.value.voices.message = '语音列表获取失败'
      addLog('error', `TTS语音列表测试失败: ${error.message}`)
    }
    
    // 测试健康检查
    ttsTests.value.edge.status = 'running'
    try {
      const startTime = Date.now()
      const healthy = await ttsService.healthCheck()
      const duration = Date.now() - startTime
      
      ttsTests.value.edge.status = healthy ? 'success' : 'error'
      ttsTests.value.edge.message = `健康检查${healthy ? '通过' : '失败'} (${duration}ms)`
      addLog(healthy ? 'success' : 'error', `TTS健康检查${healthy ? '通过' : '失败'} (${duration}ms)`)
    }
    catch (error: any) {
      ttsTests.value.edge.status = 'error'
      ttsTests.value.edge.message = '健康检查异常'
      addLog('error', `TTS健康检查异常: ${error.message}`)
    }
    
    // 其他TTS测试标记为跳过
    ttsTests.value.fish.status = 'skipped'
    ttsTests.value.fish.message = '需要API密钥配置'
    ttsTests.value.openai.status = 'skipped'
    ttsTests.value.openai.message = '需要API密钥配置'
    
  }
  finally {
    isRunning.value = false
  }
}

// 运行工作流测试
const runWorkflowTests = async () => {
  if (isRunning.value) return
  
  isRunning.value = true
  addLog('info', '开始工作流服务测试')
  
  try {
    // 测试项目管理
    workflowTests.value.projects.status = 'running'
    try {
      const startTime = Date.now()
      await workflowService.getProjects()
      const duration = Date.now() - startTime
      
      workflowTests.value.projects.status = 'success'
      workflowTests.value.projects.message = `项目列表获取成功 (${duration}ms)`
      addLog('success', `工作流项目管理测试通过 (${duration}ms)`)
    }
    catch (error: any) {
      workflowTests.value.projects.status = 'error'
      workflowTests.value.projects.message = '项目列表获取失败'
      addLog('error', `工作流项目管理测试失败: ${error.message}`)
    }
    
    // 测试健康检查
    workflowTests.value.debug.status = 'running'
    try {
      const startTime = Date.now()
      const healthy = await workflowService.healthCheck()
      const duration = Date.now() - startTime
      
      workflowTests.value.debug.status = healthy ? 'success' : 'error'
      workflowTests.value.debug.message = `健康检查${healthy ? '通过' : '失败'} (${duration}ms)`
      addLog(healthy ? 'success' : 'error', `工作流健康检查${healthy ? '通过' : '失败'} (${duration}ms)`)
    }
    catch (error: any) {
      workflowTests.value.debug.status = 'error'
      workflowTests.value.debug.message = '健康检查异常'
      addLog('error', `工作流健康检查异常: ${error.message}`)
    }
    
    // 其他测试标记为跳过
    workflowTests.value.execution.status = 'skipped'
    workflowTests.value.execution.message = '需要项目配置'
    workflowTests.value.export.status = 'skipped'
    workflowTests.value.export.message = '需要项目配置'
    
  }
  finally {
    isRunning.value = false
  }
}

// 运行性能测试
const runPerformanceTests = async () => {
  if (isRunning.value) return
  
  isRunning.value = true
  addLog('info', '开始性能测试')
  
  const testRequests = 10
  const results: number[] = []
  let successCount = 0
  
  try {
    for (let i = 0; i < testRequests; i++) {
      try {
        const startTime = Date.now()
        await checkApiHealth()
        const duration = Date.now() - startTime
        results.push(duration)
        successCount++
      }
      catch {
        results.push(0)
      }
    }
    
    // 计算性能指标
    const validResults = results.filter(r => r > 0)
    performanceMetrics.value.avgResponseTime = validResults.length > 0 
      ? Math.round(validResults.reduce((a, b) => a + b) / validResults.length)
      : 0
    performanceMetrics.value.successRate = Math.round((successCount / testRequests) * 100)
    performanceMetrics.value.totalRequests += testRequests
    
    addLog('success', `性能测试完成: 平均响应时间 ${performanceMetrics.value.avgResponseTime}ms, 成功率 ${performanceMetrics.value.successRate}%`)
    
  }
  catch (error: any) {
    addLog('error', `性能测试失败: ${error.message}`)
  }
  finally {
    isRunning.value = false
  }
}

// 运行全面测试
const runAllTests = async () => {
  if (isRunning.value) return
  
  testProgress.value = 0
  testSummary.value = { passed: 0, failed: 0, skipped: 0 }
  
  addLog('info', '开始全面集成测试')
  
  const tests = [
    runBasicTests,
    runAITests,
    runTTSTests,
    runWorkflowTests,
    runPerformanceTests
  ]
  
  for (let i = 0; i < tests.length; i++) {
    await tests[i]()
    testProgress.value = Math.round(((i + 1) / tests.length) * 100)
  }
  
  // 计算测试摘要
  const allTests = [
    ...Object.values(basicTests.value),
    ...Object.values(aiTests.value),
    ...Object.values(ttsTests.value),
    ...Object.values(workflowTests.value)
  ]
  
  testSummary.value.passed = allTests.filter(t => t.status === 'success').length
  testSummary.value.failed = allTests.filter(t => t.status === 'error').length
  testSummary.value.skipped = allTests.filter(t => t.status === 'skipped').length
  
  addLog('success', `全面测试完成: ${testSummary.value.passed} 通过, ${testSummary.value.failed} 失败, ${testSummary.value.skipped} 跳过`)
}

// 组件挂载时运行基础测试
onMounted(() => {
  runBasicTests()
})
</script>

<style lang="scss" scoped>
.api-integration-test {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;

  .test-header {
    text-align: center;
    margin-bottom: 40px;

    h2 {
      margin: 0 0 10px 0;
      font-size: 28px;
      font-weight: 600;
    }

    p {
      margin: 0;
      font-size: 16px;
      opacity: 0.8;
    }
  }

  .test-sections {
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  .test-section {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 24px;
    backdrop-filter: blur(10px);

    h3 {
      margin: 0 0 20px 0;
      font-size: 20px;
      font-weight: 600;
    }

    .test-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }

    .test-card {
      background: rgba(255, 255, 255, 0.05);
      border: 2px solid transparent;
      border-radius: 8px;
      padding: 16px;
      transition: all 0.3s ease;

      &.test-pending {
        border-color: rgba(255, 255, 255, 0.2);
      }

      &.test-running {
        border-color: #3498db;
        background: rgba(52, 152, 219, 0.1);
      }

      &.test-success {
        border-color: #27ae60;
        background: rgba(39, 174, 96, 0.1);
      }

      &.test-error {
        border-color: #e74c3c;
        background: rgba(231, 76, 60, 0.1);
      }

      &.test-skipped {
        border-color: #f39c12;
        background: rgba(243, 156, 18, 0.1);
      }

      .test-title {
        font-weight: 600;
        margin-bottom: 8px;
      }

      .test-status {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
        opacity: 0.8;
      }

      .test-result {
        font-size: 14px;
        opacity: 0.9;
      }
    }

    .test-btn {
      background: linear-gradient(45deg, #3498db, #2980b9);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 12px 24px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4);
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
      }

      &.primary {
        background: linear-gradient(45deg, #27ae60, #229954);

        &:hover:not(:disabled) {
          box-shadow: 0 4px 12px rgba(39, 174, 96, 0.4);
        }
      }
    }
  }

  .performance-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 20px;

    .metric {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 16px;
      text-align: center;

      .metric-label {
        display: block;
        font-size: 12px;
        opacity: 0.8;
        margin-bottom: 8px;
      }

      .metric-value {
        display: block;
        font-size: 24px;
        font-weight: 600;
      }
    }
  }

  .comprehensive-test {
    .test-progress {
      margin-bottom: 20px;

      .progress-bar {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin-bottom: 8px;

        .progress-fill {
          background: linear-gradient(45deg, #27ae60, #2ecc71);
          height: 100%;
          transition: width 0.3s ease;
        }
      }

      .progress-text {
        text-align: center;
        font-size: 14px;
        opacity: 0.8;
      }
    }

    .test-summary {
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-bottom: 20px;

      .summary-item {
        text-align: center;

        .summary-label {
          display: block;
          font-size: 12px;
          opacity: 0.8;
          margin-bottom: 4px;
        }

        .summary-value {
          display: block;
          font-size: 20px;
          font-weight: 600;

          &.success {
            color: #27ae60;
          }

          &.error {
            color: #e74c3c;
          }

          &.warning {
            color: #f39c12;
          }
        }
      }
    }
  }

  .test-logs {
    margin-top: 40px;

    h3 {
      margin: 0 0 16px 0;
      font-size: 18px;
      font-weight: 600;
    }

    .log-container {
      background: rgba(0, 0, 0, 0.2);
      border-radius: 8px;
      padding: 16px;
      max-height: 300px;
      overflow-y: auto;
      margin-bottom: 16px;

      .log-entry {
        display: flex;
        gap: 12px;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 4px;
        font-family: 'Courier New', monospace;
        font-size: 12px;

        &.info {
          background: rgba(52, 152, 219, 0.1);
        }

        &.success {
          background: rgba(39, 174, 96, 0.1);
        }

        &.error {
          background: rgba(231, 76, 60, 0.1);
        }

        &.warning {
          background: rgba(243, 156, 18, 0.1);
        }

        .log-time {
          color: rgba(255, 255, 255, 0.6);
          min-width: 70px;
        }

        .log-level {
          font-weight: 600;
          min-width: 60px;
        }

        .log-message {
          flex: 1;
        }
      }
    }

    .clear-btn {
      background: rgba(231, 76, 60, 0.2);
      color: white;
      border: 1px solid rgba(231, 76, 60, 0.4);
      border-radius: 6px;
      padding: 8px 16px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        background: rgba(231, 76, 60, 0.3);
      }
    }
  }
}
</style>
