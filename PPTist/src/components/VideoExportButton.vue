<!--
  完整视频导出组件 - 支持配置、工作流、项目管理
-->
<template>
  <div class="video-export-group">
    <!-- 配置按钮 -->
    <div class="menu-item config-btn" v-tooltip="'视频导出配置'" @click="handleShowConfig">
      <span class="icon">⚙️</span>
    </div>
    
    <!-- 视频导出按钮组 -->
    <div class="group-menu-item">
      <div 
        class="menu-item video-export-btn" 
        v-tooltip="'导出为视频'" 
        @click="handleStartExport"
        :class="{ disabled: exportState.isExporting }"
      >
        <span class="icon" v-if="!exportState.isExporting">🎬</span>
        <span class="loading-icon" v-else>⏳</span>
        <span class="text">视频导出</span>
      </div>
      <div class="arrow-btn" @click="handleToggleMenu">
        <span class="arrow">▼</span>
      </div>
    </div>

    <!-- 下拉菜单 -->
    <div v-if="uiState.showMenu" class="export-menu" @click.stop>
      <div class="menu-option" @click="handleStartExport">
        <span class="menu-icon">🚀</span>
        <span>快速导出</span>
      </div>
      <div class="menu-option" @click="handleConfigExport">
        <span class="menu-icon">⚙️</span>
        <span>配置后导出</span>
      </div>
      <div class="menu-option" @click="handleShowProjects">
        <span class="menu-icon">📁</span>
        <span>查看项目</span>
      </div>
    </div>

    <!-- 简化的状态提示 -->
    <div v-if="uiState.showConfigPage" class="config-notice">
      配置功能开发中...
      <button @click="handleHideConfig">关闭</button>
    </div>
    
    <div v-if="uiState.showWorkflowProgress" class="progress-notice">
      工作流正在执行中...
      <button @click="handleCloseProgress">关闭</button>
    </div>
    
    <div v-if="uiState.showProjectList" class="projects-notice">
      项目列表功能开发中...
      <button @click="handleHideProjects">关闭</button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, reactive } from 'vue'
import message from '@/utils/message'
import useVideoExport from '@/hooks/useVideoExport'

// 使用导出功能
const { 
  exporting, 
  exportToBackend,
  canExport 
} = useVideoExport()

// UI状态管理
const uiState = reactive({
  showMenu: false,
  showConfigPage: false,
  showWorkflowProgress: false,
  showProjectList: false,
  backendAvailable: false
})

// 导出状态管理
const exportState = reactive({
  isExporting: computed(() => exporting.value),
  currentWorkflowId: ''
})

// API配置
import { API_BASE_URL } from '@/config/api'

// 事件处理函数
const handleShowConfig = () => {
  uiState.showConfigPage = true
}

const handleHideConfig = () => {
  uiState.showConfigPage = false
}

const handleToggleMenu = () => {
  uiState.showMenu = !uiState.showMenu
}

const handleShowProjects = () => {
  uiState.showMenu = false
  uiState.showProjectList = true
}

const handleHideProjects = () => {
  uiState.showProjectList = false
}

const handleCloseProgress = () => {
  uiState.showWorkflowProgress = false
  exportState.currentWorkflowId = ''
}

// 检查后端状态
const checkBackend = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    uiState.backendAvailable = response.ok
  } 
  catch (error) {
    uiState.backendAvailable = false
  }
}

// 主要导出函数
const handleStartExport = async () => {
  if (!canExport.value || exportState.isExporting) return
  
  uiState.showMenu = false
  
  if (!uiState.backendAvailable) {
    message.warning('后端服务不可用，请确保工作流服务已启动')
    return
  }

  try {
    // 1. 先导出PPT数据到后端
    const projectName = `project_${Date.now()}`
    await exportToBackend(projectName)
    
    // 2. 启动工作流
    const response = await fetch(`${API_BASE_URL}/api/workflow/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        project_name: projectName
      })
    })

    if (!response.ok) {
      throw new Error('工作流启动失败')
    }

    const result = await response.json()
    exportState.currentWorkflowId = result.workflow_id || 'default'
    
    // 显示进度窗口
    uiState.showWorkflowProgress = true
    
    message.success('工作流已启动，正在生成视频...')
    
  } 
  catch (error) {
    message.error('导出失败：' + (error as Error).message)
  }
}

// 配置后导出
const handleConfigExport = () => {
  uiState.showMenu = false
  uiState.showConfigPage = true
}

// 关闭菜单的点击外部监听
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.video-export-group')) {
    uiState.showMenu = false
  }
}

// 组件挂载时设置监听和检查状态
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  checkBackend()
  // 定期检查后端状态（每30秒）
  setInterval(checkBackend, 30000)
})

// 组件卸载时清理
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style lang="scss" scoped>
.video-export-group {
  display: flex;
  gap: 4px;
  position: relative;
  
  .menu-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
    user-select: none;

    &:hover:not(.disabled) {
      background-color: rgba(0, 0, 0, 0.05);
    }

    &.disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .icon, .loading-icon {
      font-size: 16px;
      line-height: 1;
    }

    .loading-icon {
      animation: rotate 2s linear infinite;
    }

    .text {
      font-size: 12px;
      font-weight: 500;
      color: #333;
    }
  }

  .group-menu-item {
    display: flex;
    align-items: center;
    background: white;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    overflow: hidden;

    .video-export-btn {
      border: none;
      border-radius: 0;
      padding: 8px 12px;
    }

    .arrow-btn {
      padding: 8px 6px;
      border-left: 1px solid #d9d9d9;
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background-color: rgba(0, 0, 0, 0.05);
      }

      .arrow {
        font-size: 10px;
        color: #666;
      }
    }
  }

  .export-menu {
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 140px;
    background: white;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    padding: 4px 0;
    margin-top: 4px;

    .menu-option {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      cursor: pointer;
      font-size: 13px;
      transition: background-color 0.2s;

      &:hover:not(.disabled) {
        background-color: #f5f5f5;
      }

      &.disabled {
        opacity: 0.5;
        cursor: not-allowed;
        color: #999;
      }

      .menu-icon {
        font-size: 14px;
      }
    }
  }

  // 简化的通知样式
  .config-notice,
  .progress-notice,
  .projects-notice {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    padding: 12px;
    margin-top: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    
    button {
      margin-left: 8px;
      padding: 4px 8px;
      background: #1677ff;
      color: white;
      border: none;
      border-radius: 3px;
      cursor: pointer;
      font-size: 12px;
      
      &:hover {
        background: #1454d4;
      }
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
