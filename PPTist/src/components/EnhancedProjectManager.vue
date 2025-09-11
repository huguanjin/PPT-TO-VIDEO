<template>
  <div class="enhanced-project-manager">
    <!-- 头部操作栏 -->
    <div class="manager-header">
      <h2>📁 项目管理</h2>
      <div class="header-actions">
        <button @click="showCreateProject = true" class="btn btn-primary">
          <span class="icon">➕</span>
          新建项目
        </button>
        <button @click="refreshProjects" class="btn btn-secondary" :disabled="isLoading">
          <span class="icon">🔄</span>
          {{ isLoading ? '刷新中...' : '刷新' }}
        </button>
        <button v-if="currentProject" @click="saveCurrentProject" class="btn btn-success" :disabled="isAutoSaving">
          <span class="icon">💾</span>
          {{ isAutoSaving ? '保存中...' : '手动保存' }}
        </button>
        <button @click="$emit('close')" class="close-btn">
          ✕
        </button>
      </div>
    </div>

    <!-- 当前项目信息 -->
    <div v-if="currentProject" class="current-project-section">
      <h3>🎯 当前项目</h3>
      <div class="project-card current">
        <div class="project-info">
          <div class="project-title">{{ currentProject.title }}</div>
          <div class="project-meta">
            <span class="slides-count">📄 {{ currentProject.slides_count }} 页</span>
            <span class="last-saved">⏰ {{ formatDateTime(currentProject.updated_at) }}</span>
            <span v-if="hasUnsavedChanges" class="unsaved-indicator">● 有未保存更改</span>
          </div>
          <div v-if="currentProject.description" class="project-description">
            {{ currentProject.description }}
          </div>
          <div class="auto-save-status">
            <label class="auto-save-toggle">
              <input 
                type="checkbox" 
                v-model="autoSaveConfig.enabled" 
                @change="toggleAutoSave"
              >
              自动保存 ({{ autoSaveConfig.interval / 1000 }}s)
            </label>
            <span v-if="lastSaveTime" class="last-save-time">
              上次保存: {{ formatTime(lastSaveTime || 0) }}
            </span>
          </div>
        </div>
        <div class="project-actions">
          <button @click="showWorkflowHistory(currentProject.project_id || currentProject.id)" class="btn btn-info">
            📊 工作流历史
          </button>
          <button @click="startVideoGeneration" class="btn btn-primary">
            🎬 生成视频
          </button>
        </div>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-section">
      <input 
        type="text" 
        placeholder="搜索项目..."
        v-model="searchQuery"
        class="search-input"
      >
    </div>

    <!-- 项目列表 -->
    <div class="projects-section">
      <h3>📚 所有项目 ({{ filteredProjects.length }})</h3>
      
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner">🔄</div>
        <div>加载项目列表...</div>
      </div>
      
      <div v-else-if="filteredProjects.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-text">
          {{ searchQuery ? '没有找到匹配的项目' : '暂无项目' }}
        </div>
        <button v-if="!searchQuery" @click="showCreateProject = true" class="btn btn-primary">
          创建第一个项目
        </button>
      </div>
      
      <div v-else class="projects-grid">
        <div 
          v-for="project in filteredProjects" 
          :key="project.project_id || project.id"
          class="project-card"
          :class="{ 
            active: (project.project_id || project.id) === (currentProject?.project_id || currentProject?.id),
            'has-workflows': (project.workflow_count || 0) > 0
          }"
        >
          <div class="project-info">
            <div class="project-title">{{ project.title }}</div>
            <div class="project-meta">
              <span class="slides-count">📄 {{ project.slides_count }} 页</span>
              <span class="last-updated">⏰ {{ formatDateTime(project.updated_at) }}</span>
            </div>
            <div v-if="project.description" class="project-description">
              {{ project.description }}
            </div>
            <div v-if="(project.workflow_count || 0) > 0" class="workflow-summary">
              <span class="workflow-count">🔄 {{ project.workflow_count || 0 }} 个工作流</span>
              <span 
                class="last-workflow-status" 
                :class="project.last_workflow_status || ''"
              >
                {{ getStatusText(project.last_workflow_status || '') }}
              </span>
            </div>
          </div>
          <div class="project-actions">
            <button 
              @click="loadProject(project.project_id || project.id)" 
              class="btn btn-primary"
              :disabled="isLoading"
            >
              {{ (project.project_id || project.id) === (currentProject?.project_id || currentProject?.id) ? '当前项目' : '打开' }}
            </button>
            <button 
              @click="showWorkflowHistory(project.project_id || project.id)" 
              class="btn btn-secondary"
            >
              历史
            </button>
            <div class="dropdown">
              <button class="btn btn-secondary dropdown-toggle">⋯</button>
              <div class="dropdown-menu">
                <button @click="showDuplicateDialog(project)">📋 复制</button>
                <button @click="showEditDialog(project)">✏️ 编辑</button>
                <button @click="confirmDelete(project)" class="danger">🗑️ 删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建项目弹窗 -->
    <div v-if="showCreateProject" class="modal-overlay" @click="closeCreateProject">
      <div class="create-project-modal" @click.stop>
        <div class="modal-header">
          <h3>➕ 新建项目</h3>
          <button @click="closeCreateProject" class="close-btn">✕</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>项目名称 *</label>
            <input 
              v-model="newProject.title" 
              type="text" 
              placeholder="请输入项目名称"
              class="form-input"
              required
            >
          </div>
          <div class="form-group">
            <label>项目描述</label>
            <textarea 
              v-model="newProject.description" 
              placeholder="请输入项目描述（可选）"
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>
          <div class="form-actions">
            <button @click="closeCreateProject" class="btn btn-secondary">取消</button>
            <button 
              @click="confirmCreateProject" 
              class="btn btn-primary"
              :disabled="!newProject.title.trim()"
            >
              创建项目
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 复制项目弹窗 -->
    <div v-if="showDuplicateProject" class="modal-overlay" @click="closeDuplicateProject">
      <div class="duplicate-project-modal" @click.stop>
        <div class="modal-header">
          <h3>📋 复制项目</h3>
          <button @click="closeDuplicateProject" class="close-btn">✕</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>新项目名称 *</label>
            <input 
              v-model="duplicateTitle" 
              type="text" 
              :placeholder="`${duplicateSourceProject?.title} - 副本`"
              class="form-input"
            >
          </div>
          <div class="form-actions">
            <button @click="closeDuplicateProject" class="btn btn-secondary">取消</button>
            <button 
              @click="confirmDuplicateProject" 
              class="btn btn-primary"
              :disabled="!duplicateTitle.trim()"
            >
              复制项目
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectManager } from '@/hooks/useProjectManager'
import message from '@/utils/message'

// 定义事件
const emit = defineEmits<{
  close: []
}>()

// 使用项目管理器Hook
const {
  currentProject,
  projects,
  isAutoSaving,
  isLoading,
  lastSaveTime,
  autoSaveConfig,
  hasUnsavedChanges,
  createProject,
  loadProject,
  saveProject,
  loadProjects,
  deleteProject,
  duplicateProject,
  startWorkflow,
  startAutoSave,
  stopAutoSave
} = useProjectManager()

// 本地状态
const showCreateProject = ref(false)
const showDuplicateProject = ref(false)
const searchQuery = ref('')
const newProject = ref({
  title: '',
  description: ''
})
const duplicateSourceProject = ref<any>(null)
const duplicateTitle = ref('')

// 计算属性
const filteredProjects = computed(() => {
  if (!searchQuery.value) return projects.value
  
  const query = searchQuery.value.toLowerCase()
  return projects.value.filter(project => 
    project.title.toLowerCase().includes(query) ||
    project.description?.toLowerCase().includes(query)
  )
})

// 工具函数
const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = diffMs / (1000 * 60 * 60)
  
  if (diffHours < 1) {
    const diffMins = Math.floor(diffMs / (1000 * 60))
    return diffMins < 1 ? '刚刚' : `${diffMins}分钟前`
  }
  
  if (diffHours < 24) {
    return `${Math.floor(diffHours)}小时前`
  }
  
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const formatTime = (timestamp: number | Date) => {
  if (typeof timestamp === 'number') {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    })
  }
  return timestamp.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'idle': '空闲',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 项目操作方法
const refreshProjects = async () => {
  await loadProjects()
  message.success('项目列表已刷新')
}

const saveCurrentProject = async () => {
  const success = await saveProject(undefined, true)
  if (success) {
    message.success('项目保存成功')
  }
}

const confirmCreateProject = async () => {
  if (!newProject.value.title.trim()) {
    message.error('请输入项目名称')
    return
  }
  
  const projectId = await createProject(newProject.value.title, newProject.value.description)
  if (projectId) {
    closeCreateProject()
    await refreshProjects()
    message.success('项目创建成功')
  }
}

const closeCreateProject = () => {
  showCreateProject.value = false
  newProject.value = { title: '', description: '' }
}

const showDuplicateDialog = (project: any) => {
  duplicateSourceProject.value = project
  duplicateTitle.value = `${project.title} - 副本`
  showDuplicateProject.value = true
}

const confirmDuplicateProject = async () => {
  if (!duplicateSourceProject.value || !duplicateTitle.value.trim()) return
  
  await duplicateProject(duplicateSourceProject.value.project_id || duplicateSourceProject.value.id, duplicateTitle.value)
  closeDuplicateProject()
  await refreshProjects()
  message.success('项目复制成功')
}

const closeDuplicateProject = () => {
  showDuplicateProject.value = false
  duplicateSourceProject.value = null
  duplicateTitle.value = ''
}

const confirmDelete = async (project: any) => {
  // eslint-disable-next-line no-alert
  if (window.confirm(`确定要删除项目 "${project.title}" 吗？此操作不可撤销。`)) {
    await deleteProject(project.project_id || project.id)
    await refreshProjects()
    message.success('项目删除成功')
  }
}

const showEditDialog = (project: any) => {
  // TODO: 实现编辑项目弹窗
  // eslint-disable-next-line no-console
  console.log('编辑项目:', project)
  message.info('编辑功能开发中...')
}

const showWorkflowHistory = (projectId: string) => {
  // TODO: 实现工作流历史弹窗
  // eslint-disable-next-line no-console
  console.log('显示工作流历史:', projectId)
  message.info('工作流历史功能开发中...')
}

const startVideoGeneration = async () => {
  if (!currentProject.value) return
  
  try {
    await startWorkflow()
    message.success('视频生成工作流已启动')
    emit('close')
  } 
  catch (error) {
    message.error('启动工作流失败')
  }
}

const toggleAutoSave = () => {
  if (autoSaveConfig.value.enabled) {
    startAutoSave()
    message.success('自动保存已启用')
  }
  else {
    stopAutoSave()
    message.info('自动保存已关闭')
  }
}

// 生命周期
onMounted(() => {
  refreshProjects()
})
</script>

<style scoped>
.enhanced-project-manager {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  background: #f8f9fa;
  border-radius: 8px;
  max-height: 80vh;
  overflow-y: auto;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.manager-header h2 {
  margin: 0;
  color: #343a40;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.close-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 16px;
}

.current-project-section {
  margin-bottom: 30px;
}

.current-project-section h3 {
  margin-bottom: 15px;
  color: #343a40;
}

.project-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border: 2px solid transparent;
  transition: all 0.2s;
}

.project-card.current {
  border-color: #007bff;
  background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
}

.project-card.active {
  border-color: #28a745;
}

.project-card.has-workflows {
  border-left: 4px solid #17a2b8;
}

.project-info {
  flex: 1;
}

.project-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.project-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
  flex-wrap: wrap;
}

.project-description {
  color: #888;
  font-size: 14px;
  margin-bottom: 10px;
}

.auto-save-status {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  flex-wrap: wrap;
}

.auto-save-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

.last-save-time {
  font-size: 12px;
  color: #999;
}

.unsaved-indicator {
  color: #ff6b6b;
  font-weight: 500;
}

.search-section {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  max-width: 400px;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.projects-section h3 {
  margin-bottom: 20px;
  color: #343a40;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.loading-spinner {
  font-size: 24px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 20px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.project-actions {
  display: flex;
  gap: 8px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  flex-wrap: wrap;
}

.workflow-summary {
  display: flex;
  gap: 10px;
  margin-top: 8px;
  font-size: 13px;
  flex-wrap: wrap;
}

.workflow-count {
  color: #17a2b8;
}

.last-workflow-status {
  font-weight: 500;
}

.last-workflow-status.completed {
  color: #28a745;
}

.last-workflow-status.failed {
  color: #dc3545;
}

.last-workflow-status.running {
  color: #ffc107;
}

.dropdown {
  position: relative;
}

.dropdown-toggle::after {
  content: '';
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 120px;
  display: none;
}

.dropdown:hover .dropdown-menu {
  display: block;
}

.dropdown-menu button {
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  font-size: 13px;
  color: #333;
}

.dropdown-menu button:hover {
  background: #f8f9fa;
}

.dropdown-menu button.danger {
  color: #dc3545;
}

.dropdown-menu button.danger:hover {
  background: #f8d7da;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.create-project-modal,
.duplicate-project-modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  padding: 20px 25px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
}

.modal-header .close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #999;
  padding: 0;
}

.modal-content {
  padding: 25px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #333;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
</style>
