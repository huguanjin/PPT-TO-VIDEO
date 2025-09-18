<template>
  <div class="template-card">
    <div class="card-thumbnail">
      <img 
        v-if="template.metadata.thumbnail" 
        :src="template.metadata.thumbnail" 
        :alt="template.metadata.name"
        @error="handleImageError"
      />
      <div v-else class="thumbnail-placeholder">
        <FileImageOutlined />
        <span>{{ template.metadata.name.charAt(0).toUpperCase() }}</span>
      </div>
      
      <div class="card-overlay">
        <div class="overlay-actions">
          <Button type="primary" size="small" @click="$emit('use', template)">
            使用模板
          </Button>
          <Button size="small" @click="$emit('preview', template)">
            <template #icon>
              <EyeOutlined />
            </template>
          </Button>
        </div>
      </div>
      
      <!-- 分类标签 -->
      <div class="category-tag">
        {{ getCategoryLabel(template.metadata.category) }}
      </div>
      
      <!-- 评分 -->
      <div class="rating-badge">
        <StarFilled />
        {{ template.metadata.rating.toFixed(1) }}
      </div>
    </div>
    
    <div class="card-content">
      <div class="card-header">
        <h3 class="template-name" :title="template.metadata.name">
          {{ template.metadata.name }}
        </h3>
        
        <div class="template-meta">
          <span class="author">{{ template.metadata.author }}</span>
          <span class="version">v{{ template.metadata.version }}</span>
        </div>
      </div>
      
      <p class="template-description" :title="template.metadata.description">
        {{ template.metadata.description }}
      </p>
      
      <div class="template-tags" v-if="template.metadata.tags.length > 0">
        <Tag 
          v-for="tag in template.metadata.tags.slice(0, 3)" 
          :key="tag" 
          size="small"
        >
          {{ tag }}
        </Tag>
        <span v-if="template.metadata.tags.length > 3" class="more-tags">
          +{{ template.metadata.tags.length - 3 }}
        </span>
      </div>
      
      <div class="template-stats">
        <div class="stat-item">
          <DownloadOutlined />
          <span>{{ formatNumber(template.metadata.downloads) }}</span>
        </div>
        
        <div class="stat-item">
          <ClockCircleOutlined />
          <span>{{ formatDate(template.metadata.updatedAt) }}</span>
        </div>
        
        <div class="stat-item">
          <DatabaseOutlined />
          <span>{{ formatFileSize(template.metadata.size) }}</span>
        </div>
      </div>
      
      <div class="card-actions">
        <div class="primary-actions">
          <Button 
            type="primary" 
            block 
            @click="$emit('use', template)"
          >
            使用模板
          </Button>
        </div>
        
        <div class="secondary-actions">
          <Dropdown :trigger="['click']">
            <Button type="text" size="small">
              <template #icon>
                <MoreOutlined />
              </template>
            </Button>
            
            <template #overlay>
              <Menu>
                <MenuItem @click="$emit('preview', template)">
                  <EyeOutlined />
                  预览
                </MenuItem>
                
                <MenuItem @click="$emit('clone', template)">
                  <CopyOutlined />
                  复制
                </MenuItem>
                
                <MenuItem @click="$emit('download', template)">
                  <DownloadOutlined />
                  下载
                </MenuItem>
                
                <template v-if="showManagement">
                  <MenuDivider />
                  
                  <MenuItem @click="$emit('edit', template)">
                    <EditOutlined />
                    编辑
                  </MenuItem>
                  
                  <MenuItem @click="$emit('export', template)">
                    <ExportOutlined />
                    导出
                  </MenuItem>
                  
                  <MenuItem 
                    @click="$emit('delete', template)"
                    class="danger-item"
                  >
                    <DeleteOutlined />
                    删除
                  </MenuItem>
                </template>
              </Menu>
            </template>
          </Dropdown>
        </div>
      </div>
    </div>
    
    <!-- 配置预览模态框 -->
    <Modal
      v-model:open="previewModalVisible"
      :title="`模板预览 - ${template.metadata.name}`"
      width="800px"
      :footer="null"
    >
      <TemplatePreview :template="template" />
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  Button,
  Tag,
  Dropdown,
  Menu,
  MenuItem,
  MenuDivider,
  Modal
} from 'ant-design-vue'
import {
  FileImageOutlined,
  EyeOutlined,
  StarFilled,
  DownloadOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  MoreOutlined,
  CopyOutlined,
  EditOutlined,
  ExportOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'

import type { Template } from '../templates/template-config'
import TemplatePreview from './TemplatePreview.vue'

// Props
interface Props {
  template: Template
  showManagement?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showManagement: false
})

// Emits
defineEmits<{
  use: [template: Template]
  preview: [template: Template]
  edit: [template: Template]
  delete: [template: Template]
  download: [template: Template]
  export: [template: Template]
  clone: [template: Template]
}>()

// State
const previewModalVisible = ref(false)

// Methods
const getCategoryLabel = (category: string) => {
  const labels: Record<string, string> = {
    business: '商务',
    education: '教育',
    entertainment: '娱乐',
    marketing: '营销',
    tutorial: '教程',
    presentation: '演示',
    documentary: '纪录片',
    social: '社交',
    news: '新闻',
    gaming: '游戏',
    medical: '医疗',
    legal: '法律',
    finance: '金融',
    technology: '技术',
    other: '其他'
  }
  return labels[category] || category
}

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDate = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days < 1) {
    return '今天'
  }
  if (days === 1) {
    return '昨天'
  }
  if (days < 7) {
    return `${days}天前`
  }
  if (days < 30) {
    return `${Math.floor(days / 7)}周前`
  }
  if (days < 365) {
    return `${Math.floor(days / 30)}月前`
  }
  return `${Math.floor(days / 365)}年前`
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) {
    return bytes + ' B'
  }
  if (bytes < 1024 * 1024) {
    return (bytes / 1024).toFixed(1) + ' KB'
  }
  if (bytes < 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<style scoped>
.template-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
}

.template-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.card-thumbnail {
  position: relative;
  height: 200px;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
}

.card-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.template-card:hover .card-thumbnail img {
  transform: scale(1.05);
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
  font-size: 48px;
}

.thumbnail-placeholder span {
  font-size: 24px;
  font-weight: bold;
  margin-top: 8px;
}

.card-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.template-card:hover .card-overlay {
  opacity: 1;
}

.overlay-actions {
  display: flex;
  gap: 12px;
}

.category-tag {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(24, 144, 255, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.rating-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 193, 7, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-content {
  padding: 16px;
}

.card-header {
  margin-bottom: 8px;
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #262626;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #8c8c8c;
}

.template-description {
  font-size: 14px;
  color: #595959;
  margin: 0 0 12px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

.template-tags {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.more-tags {
  font-size: 12px;
  color: #8c8c8c;
}

.template-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8c8c8c;
  flex: 1;
  justify-content: center;
}

.stat-item:not(:last-child) {
  border-right: 1px solid #f0f0f0;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.primary-actions {
  flex: 1;
}

.secondary-actions {
  display: flex;
}

.danger-item {
  color: #ff4d4f !important;
}

.danger-item:hover {
  background-color: #fff2f0 !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-thumbnail {
    height: 160px;
  }
  
  .template-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .stat-item {
    justify-content: flex-start;
    border-right: none !important;
  }
  
  .overlay-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .card-content {
    padding: 12px;
  }
  
  .template-name {
    font-size: 14px;
  }
  
  .template-description {
    font-size: 13px;
  }
}
</style>