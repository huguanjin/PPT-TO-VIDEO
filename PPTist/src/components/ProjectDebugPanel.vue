<template>
  <div class="project-debug-panel">
    <div class="debug-header">
      <h4>🔍 项目调试信息</h4>
      <button @click="togglePanel" class="toggle-btn">
        {{ isExpanded ? '收起' : '展开' }}
      </button>
    </div>
    
    <div v-if="isExpanded" class="debug-content">
      <div class="debug-section">
        <h5>📋 当前项目状态</h5>
        <div class="info-item">
          <span class="label">项目ID:</span>
          <span class="value">{{ currentProject?.id || '无' }}</span>
        </div>
        <div class="info-item">
          <span class="label">项目标题:</span>
          <span class="value">{{ currentProject?.title || '无' }}</span>
        </div>
        <div class="info-item">
          <span class="label">是否活跃:</span>
          <span class="value" :class="{ active: isProjectActive }">
            {{ isProjectActive ? '是' : '否' }}
          </span>
        </div>
        <div class="info-item">
          <span class="label">最后保存:</span>
          <span class="value">{{ formatLastSaveTime }}</span>
        </div>
      </div>

      <div class="debug-section">
        <h5>💾 本地存储</h5>
        <div class="info-item">
          <span class="label">存储的项目ID:</span>
          <span class="value">{{ storedProjectId || '无' }}</span>
        </div>
        <div class="info-item">
          <span class="label">是否匹配:</span>
          <span class="value" :class="{ 
            active: storedProjectId === currentProject?.id,
            inactive: storedProjectId !== currentProject?.id 
          }">
            {{ storedProjectId === currentProject?.id ? '匹配' : '不匹配' }}
          </span>
        </div>
      </div>

      <div class="debug-section">
        <h5>📊 状态统计</h5>
        <div class="info-item">
          <span class="label">项目总数:</span>
          <span class="value">{{ projects.length }}</span>
        </div>
        <div class="info-item">
          <span class="label">自动保存:</span>
          <span class="value" :class="{ active: autoSaveConfig.enabled }">
            {{ autoSaveConfig.enabled ? '开启' : '关闭' }}
          </span>
        </div>
        <div class="info-item">
          <span class="label">正在保存:</span>
          <span class="value" :class="{ active: isAutoSaving }">
            {{ isAutoSaving ? '是' : '否' }}
          </span>
        </div>
      </div>

      <div class="debug-section">
        <h5>🛠️ 调试操作</h5>
        <div class="debug-actions">
          <button @click="refreshStoredId" class="debug-btn">刷新存储ID</button>
          <button @click="clearStoredId" class="debug-btn">清除存储ID</button>
          <button @click="forceLoadProject" class="debug-btn">强制加载项目</button>
          <button @click="testSave" class="debug-btn">测试保存</button>
        </div>
      </div>

      <div class="debug-section">
        <h5>🔧 API测试</h5>
        <div class="debug-actions">
          <button @click="testApiConnection" class="debug-btn">测试API连接</button>
          <button @click="testLoadProject" class="debug-btn">测试加载项目</button>
          <button @click="debugCurrentState" class="debug-btn">调试当前状态</button>
        </div>
        <div v-if="apiTestResult" class="api-result">
          <pre>{{ apiTestResult }}</pre>
        </div>
      </div>

      <div class="debug-section">
        <h5>📝 项目列表</h5>
        <div class="project-list">
          <div 
            v-for="project in projects" 
            :key="project.id"
            class="project-item"
            :class="{ current: project.id === currentProject?.id }"
            @click="loadDebugProject(project.id)"
          >
            <strong>{{ project.title }}</strong>
            <small>{{ project.id }}</small>
          </div>
          <div v-if="projects.length === 0" class="no-projects">
            暂无项目
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useProjectManager } from '@/hooks/useProjectManager'
import message from '@/utils/message'

const isExpanded = ref(false)
const storedProjectId = ref<string | null>(null)
const apiTestResult = ref<string>('')

const {
  currentProject,
  projects,
  isProjectActive,
  lastSaveTime,
  autoSaveConfig,
  isAutoSaving,
  loadProject,
  saveProject
} = useProjectManager()

const formatLastSaveTime = computed(() => {
  if (!lastSaveTime.value) return '从未保存'
  return new Date(lastSaveTime.value).toLocaleString()
})

const togglePanel = () => {
  isExpanded.value = !isExpanded.value
}

const refreshStoredId = () => {
  storedProjectId.value = localStorage.getItem('currentProjectId')
  message.info(`存储的项目ID: ${storedProjectId.value || '无'}`)
}

const clearStoredId = () => {
  localStorage.removeItem('currentProjectId')
  storedProjectId.value = null
  message.success('已清除存储的项目ID')
}

const forceLoadProject = async () => {
  if (storedProjectId.value) {
    try {
      await loadProject(storedProjectId.value)
      message.success('强制加载项目成功')
    }
    catch (error) {
      message.error('强制加载项目失败: ' + (error instanceof Error ? error.message : '未知错误'))
    }
  }
  else {
    message.warning('没有存储的项目ID')
  }
}

const testSave = async () => {
  try {
    const result = await saveProject(undefined, false) // 不显示保存消息
    if (result) {
      refreshStoredId()
    }
  }
  catch (error) {
    message.error('测试保存失败: ' + (error instanceof Error ? error.message : '未知错误'))
  }
}

const loadDebugProject = async (projectId: string) => {
  try {
    await loadProject(projectId)
    refreshStoredId()
    message.success(`已加载项目: ${projectId}`)
  }
  catch (error) {
    message.error('加载项目失败: ' + (error instanceof Error ? error.message : '未知错误'))
  }
}

const testApiConnection = async () => {
  try {
    apiTestResult.value = '正在测试API连接...'
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
    const response = await fetch(`${API_BASE_URL}/pm/api/projects`)
    const data = await response.json()
    apiTestResult.value = `API连接成功\n项目数量: ${data.projects?.length || 0}\n响应状态: ${data.success}`
    message.success('API连接测试成功')
  }
  catch (error) {
    apiTestResult.value = `API连接失败: ${error instanceof Error ? error.message : '未知错误'}`
    message.error('API连接测试失败')
  }
}

const testLoadProject = async () => {
  try {
    const projectId = storedProjectId.value || '1d3f2798-a4d6-4538-8250-2da8754314a3'
    apiTestResult.value = `正在测试加载项目: ${projectId}...`
    
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
    const response = await fetch(`${API_BASE_URL}/pm/api/projects/${projectId}`)
    const data = await response.json()
    
    apiTestResult.value = `项目加载测试结果:\n项目ID: ${projectId}\n成功: ${data.success}\n标题: ${data.project?.project_info?.title || 'N/A'}\n幻灯片数量: ${data.project?.project_info?.slides_data?.slides?.length || 0}`
    
    if (data.success) {
      message.success('项目加载测试成功')
    }
    else {
      message.error('项目加载测试失败')
    }
  }
  catch (error) {
    apiTestResult.value = `项目加载测试失败: ${error instanceof Error ? error.message : '未知错误'}`
    message.error('项目加载测试失败')
  }
}

const debugCurrentState = () => {
  const state = {
    currentProject: currentProject.value,
    storedProjectId: storedProjectId.value,
    isProjectActive: isProjectActive.value,
    projectsCount: projects.value.length,
    lastSaveTime: lastSaveTime.value
  }
  
  apiTestResult.value = `当前状态:\n${JSON.stringify(state, null, 2)}`
  message.info('已输出当前状态到调试区域')
}

onMounted(() => {
  refreshStoredId()
})
</script>

<style scoped>
.project-debug-panel {
  position: fixed;
  top: 10px;
  right: 10px;
  background: white;
  border: 2px solid #007bff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 9999;
  max-width: 400px;
  font-size: 14px;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #007bff;
  color: white;
  border-radius: 6px 6px 0 0;
}

.debug-header h4 {
  margin: 0;
  font-size: 16px;
}

.toggle-btn {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 12px;
}

.toggle-btn:hover {
  background: rgba(255,255,255,0.3);
}

.debug-content {
  padding: 15px;
  max-height: 70vh;
  overflow-y: auto;
}

.debug-section {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.debug-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.debug-section h5 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 14px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.api-result {
  margin-top: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
}

.api-result pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.label {
  color: #666;
  font-weight: 500;
}

.value {
  color: #333;
  font-family: monospace;
}

.value.active {
  color: #28a745;
  font-weight: 600;
}

.value.inactive {
  color: #dc3545;
  font-weight: 600;
}

.debug-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.debug-btn {
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.debug-btn:hover {
  background: #5a6268;
}

.project-list {
  max-height: 150px;
  overflow-y: auto;
}

.project-item {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.project-item:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.project-item.current {
  background: #e3f2fd;
  border-color: #007bff;
  border-width: 2px;
}

.project-item strong {
  display: block;
  color: #333;
  margin-bottom: 2px;
}

.project-item small {
  color: #666;
  font-family: monospace;
  font-size: 11px;
}

.no-projects {
  text-align: center;
  color: #999;
  padding: 20px;
  font-style: italic;
}
</style>
