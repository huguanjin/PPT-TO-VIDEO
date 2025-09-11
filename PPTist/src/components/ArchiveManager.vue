<template>
  <div class="archive-manager">
    <div class="header">
      <h3>📚 项目归档</h3>
      <p>管理您的历史项目，可以恢复或删除归档</p>
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
            <h4 class="name">{{ archive.name }}</h4>
            <span class="time">{{ formatTime(archive.archived_at) }}</span>
          </div>
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
  </div>
</template>

<script lang="ts" setup>
import { type ArchiveItem } from '@/hooks/useWorkspaceManager'

interface Props {
  archives: ArchiveItem[]
  loading: boolean
}

defineProps<Props>()

defineEmits<{
  restore: [folderName: string]
  delete: [folderName: string]
  refresh: []
}>()

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
