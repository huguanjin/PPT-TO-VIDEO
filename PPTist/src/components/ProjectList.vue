<template>
  <div class="project-list">
    <div class="list-header">
      <h3>项目列表</h3>
      <button @click="refreshProjects" class="refresh-btn">刷新</button>
    </div>
    
    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-else-if="projects.length === 0" class="empty">
      暂无项目
    </div>
    
    <div v-else class="project-items">
      <div v-for="project in projects" :key="project.name" class="project-item">
        <div class="project-info">
          <div class="project-name">{{ project.name }}</div>
          <div class="project-date">{{ formatDate(project.created_at) }}</div>
        </div>
        <div class="project-actions">
          <button 
            v-if="project.has_video" 
            @click="downloadProject(project.name)"
            class="download-btn"
          >
            下载视频
          </button>
          <button 
            @click="deleteProject(project.name)"
            class="delete-btn"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import message from '@/utils/message'
import { API_BASE_URL } from '@/config/api'

// 项目类型定义
interface Project {
  name: string
  created_at: string
  has_video: boolean
}

// 数据
const projects = ref<Project[]>([])
const loading = ref(false)

// 获取项目列表
const loadProjects = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/projects`)
    if (response.ok) {
      projects.value = await response.json()
    }
  } 
  catch (error) {
    message.error('获取项目列表失败')
  } 
  finally {
    loading.value = false
  }
}

// 刷新项目列表
const refreshProjects = () => {
  loadProjects()
}

// 下载项目视频
const downloadProject = async (projectName: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/download/${projectName}`)
    if (!response.ok) {
      throw new Error('下载失败')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${projectName}.mp4`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    message.success('下载完成')
  } 
  catch (error) {
    message.error('下载失败')
  }
}

// 删除项目
const deleteProject = async (projectName: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/projects/${projectName}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      message.success('项目已删除')
      loadProjects() // 重新加载列表
      return
    }
    
    throw new Error('删除失败')
  } 
  catch (error) {
    message.error('删除失败')
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleString()
  } 
  catch {
    return dateStr
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadProjects()
})
</script>

<style lang="scss" scoped>
.project-list {
  width: 600px;
  
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      font-size: 18px;
      color: #333;
    }
    
    .refresh-btn {
      background: #1677ff;
      color: white;
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
      transition: background-color 0.2s;
      
      &:hover {
        background: #1454d4;
      }
    }
  }
  
  .loading {
    text-align: center;
    padding: 40px;
    color: #666;
  }
  
  .empty {
    text-align: center;
    padding: 40px;
    color: #999;
  }
  
  .project-items {
    max-height: 400px;
    overflow-y: auto;
    
    .project-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      border: 1px solid #f0f0f0;
      border-radius: 4px;
      margin-bottom: 8px;
      transition: background-color 0.2s;
      
      &:hover {
        background-color: #fafafa;
      }
      
      .project-info {
        flex: 1;
        
        .project-name {
          font-size: 14px;
          font-weight: 500;
          color: #333;
          margin-bottom: 4px;
        }
        
        .project-date {
          font-size: 12px;
          color: #999;
        }
      }
      
      .project-actions {
        display: flex;
        gap: 8px;
        
        button {
          padding: 4px 8px;
          border: none;
          border-radius: 3px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
          
          &.download-btn {
            background: #52c41a;
            color: white;
            
            &:hover {
              background: #389e0d;
            }
          }
          
          &.delete-btn {
            background: #ff4d4f;
            color: white;
            
            &:hover {
              background: #d4380d;
            }
          }
        }
      }
    }
  }
}
</style>
