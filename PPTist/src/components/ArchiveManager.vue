<template>
  <div class="archive-manager">
    <div class="header">
      <div class="header-content">
        <h3>📚 项目归档</h3>
        <p>管理您的历史项目，可以恢复或删除归档</p>
      </div>
      <button class="close-btn" @click="$emit('close')" title="关闭">
        ✕
      </button>
    </div>
    
    <div class="toolbar">
      <button @click="$emit('refresh')" :disabled="loading" class="refresh-btn">
        🔄 刷新列表
      </button>
      <div class="summary">
        共 {{ archives.length }} 个归档项目
      </div>
    </div>
    
    <div class="archive-list" v-if="archives.length > 0">
      <div 
        v-for="archive in archives" 
        :key="archive.folder_name"
        class="archive-item"
      >
        <div class="archive-info">
          <div class="name-row">
            <h4 class="name">{{ archive.project_name }}</h4>
            <span class="time">{{ formatTime(archive.archived_at) }}</span>
          </div>
          <div class="folder-name">📁 {{ archive.name }}</div>
          <div class="details">
            <span class="detail-item">
              📄 {{ archive.slide_count }} 页
            </span>
            <span class="detail-item" v-if="archive.has_video">
              🎬 包含视频
            </span>
            <span class="detail-item">
              💾 {{ archive.size_mb }}MB
            </span>
          </div>
        </div>
        
        <div class="archive-actions">
          <button 
            v-if="archive.has_video"
            @click="previewVideo(archive.folder_name)"
            :disabled="loading"
            class="preview-btn"
            title="预览视频"
          >
            ▶️ 预览
          </button>
          <button 
            v-if="archive.has_video"
            @click="downloadBundle(archive.folder_name)"
            :disabled="loading"
            class="download-btn"
            title="下载视频和PPT数据"
          >
            ⬇️ 下载
          </button>
          <button 
            @click="$emit('restore', archive.folder_name)"
            :disabled="loading"
            class="restore-btn"
            title="恢复到工作空间"
          >
            ↩️ 恢复
          </button>
          <button 
            @click="$emit('delete', archive.folder_name)"
            :disabled="loading"
            class="delete-btn"
            title="删除归档"
          >
            🗑️ 删除
          </button>
        </div>
      </div>
    </div>
    
    <div class="empty-state" v-else-if="!loading">
      <div class="empty-icon">📂</div>
      <p>暂无归档项目</p>
      <p class="hint">使用"归档项目"按钮可以将当前工作保存到历史记录</p>
    </div>
    
    <div class="loading" v-if="loading">
      <div class="spinner">⏳</div>
      <p>加载中...</p>
    </div>
    
    <!-- 视频预览弹窗 -->
    <div v-if="showVideoPreview" class="video-preview-overlay" @click.self="closeVideoPreview">
      <div class="video-preview-modal">
        <div class="video-header">
          <h4>视频预览</h4>
          <button class="close-video-btn" @click="closeVideoPreview">✕</button>
        </div>
        <div class="video-container">
          <video 
            ref="videoPlayer"
            :src="previewVideoUrl"
            controls
            autoplay
            @error="handleVideoError"
          >
            您的浏览器不支持视频播放
          </video>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { type ArchiveItem } from '@/hooks/useWorkspaceManager'

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// 获取认证头
const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {}
  const token = localStorage.getItem('auth_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

interface Props {
  archives: ArchiveItem[]
  loading: boolean
}

defineProps<Props>()

defineEmits<{
  restore: [folderName: string]
  delete: [folderName: string]
  refresh: []
  close: []
}>()

// 视频预览状态
const showVideoPreview = ref(false)
const previewVideoUrl = ref('')
const videoPlayer = ref<HTMLVideoElement | null>(null)

// 预览视频
const previewVideo = (folderName: string) => {
  const token = localStorage.getItem('auth_token')
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : ''
  previewVideoUrl.value = `${API_BASE_URL}/api/project/history/${folderName}/preview${tokenParam}`
  showVideoPreview.value = true
}

// 关闭视频预览
const closeVideoPreview = () => {
  showVideoPreview.value = false
  previewVideoUrl.value = ''
  if (videoPlayer.value) {
    videoPlayer.value.pause()
  }
}

// 处理视频错误
const handleVideoError = () => {
  // eslint-disable-next-line no-console
  console.error('视频加载失败')
  alert('视频加载失败，请重试')
  closeVideoPreview()
}

// 下载打包文件
const downloadBundle = (folderName: string) => {
  const token = localStorage.getItem('auth_token')
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : ''
  const downloadUrl = `${API_BASE_URL}/api/project/history/${folderName}/download-bundle${tokenParam}`
  
  // 创建临时链接并触发下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = ''
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const formatTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`
  
  return date.toLocaleDateString()
}
</script>

<style lang="scss" scoped>
.archive-manager {
  max-height: 600px;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 20px 20px 16px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  
  .header-content {
    flex: 1;
    
    h3 {
      margin: 0 0 8px;
      font-size: 18px;
      color: #333;
    }
    
    p {
      margin: 0;
      color: #666;
      font-size: 14px;
    }
  }
  
  .close-btn {
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    color: #999;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &:hover {
      background: #f0f0f0;
      color: #333;
    }
  }
}

.toolbar {
  padding: 12px 20px;
  background: #f9f9f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
  
  .refresh-btn {
    padding: 6px 12px;
    border: 1px solid #d0d0d0;
    background: #fff;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    
    &:hover {
      background: #f0f0f0;
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .summary {
    font-size: 12px;
    color: #666;
  }
}

.archive-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.archive-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
  
  &:hover {
    background: #f9f9f9;
  }
  
  &:last-child {
    border-bottom: none;
  }
}

.archive-info {
  flex: 1;
  
  .name-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
    
    .name {
      margin: 0;
      font-size: 14px;
      font-weight: 500;
      color: #333;
    }
    
    .time {
      font-size: 12px;
      color: #999;
    }
  }
  
  .folder-name {
    font-size: 11px;
    color: #888;
    margin-bottom: 4px;
  }
  
  .details {
    display: flex;
    gap: 12px;
    
    .detail-item {
      font-size: 12px;
      color: #666;
    }
  }
}

.archive-actions {
  display: flex;
  gap: 8px;
  
  button {
    padding: 4px 8px;
    border: 1px solid #d0d0d0;
    background: #fff;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .preview-btn {
    color: #28a745;
    border-color: #28a745;
    
    &:hover {
      background: #e6f7e9;
    }
  }
  
  .download-btn {
    color: #6f42c1;
    border-color: #6f42c1;
    
    &:hover {
      background: #f3e8ff;
    }
  }
  
  .restore-btn {
    color: #0066cc;
    border-color: #0066cc;
    
    &:hover {
      background: #e6f2ff;
    }
  }
  
  .delete-btn {
    color: #dc3545;
    border-color: #dc3545;
    
    &:hover {
      background: #ffebee;
    }
  }
}

// 视频预览弹窗样式
.video-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.video-preview-modal {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  
  .video-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #e0e0e0;
    background: #f9f9f9;
    
    h4 {
      margin: 0;
      font-size: 16px;
      color: #333;
    }
    
    .close-video-btn {
      width: 28px;
      height: 28px;
      border: none;
      background: transparent;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
      color: #666;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      
      &:hover {
        background: #e0e0e0;
        color: #333;
      }
    }
  }
  
  .video-container {
    padding: 16px;
    background: #000;
    
    video {
      width: 100%;
      max-height: 70vh;
      display: block;
    }
  }
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #666;
  
  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }
  
  p {
    margin: 4px 0;
    text-align: center;
  }
  
  .hint {
    font-size: 12px;
    opacity: 0.7;
  }
}

.loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  
  .spinner {
    font-size: 24px;
    margin-bottom: 12px;
    animation: spin 1s linear infinite;
  }
  
  p {
    margin: 0;
    color: #666;
    font-size: 14px;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
