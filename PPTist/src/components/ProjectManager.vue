<template>
  <div class="project-manager">
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
        <button v-if="currentProject" @click="() => saveProject(true)" class="btn btn-success" :disabled="isAutoSaving">
          <span class="icon">💾</span>
          {{ isAutoSaving ? '保存中...' : '手动保存' }}
        </button>
        <button @click="$emit('close')" class="close-btn">
          ✕
        </button>
      </div>
    </div>

    <div class="content">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <input 
          type="text" 
          v-model="searchQuery"
          placeholder="搜索项目..."
          class="search-input"
        />
      </div>

      <!-- 项目列表 -->
      <div class="project-list" v-if="!isLoading">
        <div 
          v-for="project in filteredProjects" 
          :key="project.project_id || project.id"
          class="project-item"
          @click="loadProject(project.project_id || project.id)"
        >
          <div class="project-info">
            <div class="project-name">{{ project.title }}</div>
            <div class="project-meta">
              <span class="slide-count">{{ project.slides_count || 0 }} 页</span>
              <span class="update-time">{{ formatTime(project.updated_at) }}</span>
            </div>
            <div class="project-description" v-if="project.description">
              {{ project.description }}
            </div>
          </div>

          <div class="project-actions" @click.stop>
            <button 
              @click="duplicateProject(project.project_id || project.id)"
              class="action-btn duplicate"
              title="复制项目"
            >
              📋
            </button>
            <button 
              @click="deleteProject(project.project_id || project.id)"
              class="action-btn delete"
              title="删除项目"
            >
              🗑️
            </button>
          </div>
        </div>

        <div v-if="filteredProjects.length === 0" class="empty-state">
          <div class="empty-icon">📁</div>
          <div class="empty-text">
            {{ searchQuery ? '没有找到匹配的项目' : '还没有保存的项目' }}
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-icon">🔄</div>
        <div>加载项目列表...</div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="footer">
      <div class="stat-item">
        <span class="label">项目总数:</span>
        <span class="value">{{ projects.length }}</span>
      </div>
      <div class="stat-item">
        <span class="label">总页数:</span>
        <span class="value">{{ projects.reduce((sum, p) => sum + (p.slides_count || 0), 0) }}</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, getCurrentInstance } from 'vue'
import { useProjectManager } from '@/hooks/useProjectManager'
import message from '@/utils/message'

defineEmits<{
  close: []
}>()

const {
  projects: projectManagerProjects,
  loadProject: loadProjectData,
  deleteProject: deleteProjectData,
  duplicateProject: duplicateProjectData,
  loadProjects,
  isLoading,
  currentProject,
  saveProject: saveProjectFromHook,
  isAutoSaving
} = useProjectManager()

const projects = computed(() => projectManagerProjects.value)
const searchQuery = ref('')

// 添加缺失的属性 - 移除重复定义
const showCreateProject = ref(false)

// 添加缺失的方法
const refreshProjects = async () => {
  await loadProjects()
}

const saveProject = (showMessage = false) => {
  // 使用新的项目管理器保存方法
  if (currentProject.value) {
    saveProjectFromHook(undefined, showMessage)
  }
  else if (showMessage) {
    message.success('项目已保存')
  }
}

// 过滤后的项目列表
const filteredProjects = computed(() => {
  if (!searchQuery.value) return projects.value
  
  const query = searchQuery.value.toLowerCase()
  return projects.value.filter(project => 
    project.title.toLowerCase().includes(query) ||
    (project.description && project.description.toLowerCase().includes(query))
  )
})

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) return `${days}天前`
  if (hours > 0) return `${hours}小时前`
  if (minutes > 0) return `${minutes}分钟前`
  return '刚刚'
}

// 刷新项目列表
const refreshList = async () => {
  // 使用新的项目管理器加载项目
  await loadProjects()
}

// 加载项目
const loadProject = async (projectId: string) => {
  try {
    await loadProjectData(projectId)
    // 关闭弹窗
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(getCurrentInstance()?.emit as any)('close')
  }
  catch (error) {
    message.error('加载项目失败')
  }
}

// 复制项目
const duplicateProject = async (projectId: string) => {
  try {
    const project = projects.value.find(p => (p.project_id || p.id) === projectId)
    const newName = `${project?.title || '未命名'} - 副本`
    
    await duplicateProjectData(projectId, newName)
    message.success('项目复制成功')
    await loadProjects()
  }
  catch (error) {
    message.error('复制项目失败')
  }
}

// 删除项目
const deleteProject = async (projectId: string) => {
  try {
    await deleteProjectData(projectId)
    await loadProjects()
  }
  catch (error) {
    message.error('删除项目失败')
  }
}

// 生命周期
onMounted(() => {
  refreshList()
})
</script>

<style scoped>
.project-manager {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
  background: #f8f9fa;
  border-radius: 8px;
  max-height: 70vh;
  overflow-y: auto;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-success {
  background: #28a745;
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

.content {
  margin-bottom: 20px;
}

.search-bar {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.project-list {
  display: grid;
  gap: 15px;
}

.project-item {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.project-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0,123,255,0.1);
}

.project-info {
  flex: 1;
}

.project-name {
  font-size: 16px;
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
}

.project-description {
  color: #888;
  font-size: 14px;
}

.project-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f8f9fa;
}

.action-btn.delete:hover {
  background: #f8d7da;
  border-color: #dc3545;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.loading-icon {
  font-size: 24px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.footer {
  padding: 15px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-item .label {
  font-size: 12px;
  color: #666;
  display: block;
  margin-bottom: 4px;
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}
</style>
