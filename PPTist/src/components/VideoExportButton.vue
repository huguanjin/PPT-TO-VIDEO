<!-- 简化的视频导出按钮组件 -->
<template>
  <div class="video-export-group">
    <!-- 视频导出按钮 -->
    <div 
      class="menu-item video-export-btn" 
      v-tooltip="'导出为视频'" 
      @click="startVideoExport"
      :class="{ disabled: isExporting || !canExport }"
    >
      <span class="icon" v-if="!isExporting">🎬</span>
      <span class="loading-icon" v-else>⏳</span>
      <span class="text">视频导出</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore, useScreenStore, useWorkflowStore } from '@/store'

const slidesStore = useSlidesStore()
const screenStore = useScreenStore()
const workflowStore = useWorkflowStore()
const { slides } = storeToRefs(slidesStore)

const isExporting = ref(false)

// 检查是否可以导出
const canExport = computed(() => {
  return slides.value && slides.value.length > 0
})

// 等待批量导出完成
const waitForBatchExportComplete = (): Promise<string> => {
  return new Promise((resolve, reject) => {
    // 进入Screen模式
    screenStore.setScreening(true)
    
    // 设置超时（60秒）
    const timeout = setTimeout(() => {
      cleanup()
      reject(new Error('批量导出超时'))
    }, 60000)
    
    // 监听批量导出完成事件
    const handleExportComplete = (event: CustomEvent) => {
      const { success, workflow_id, error } = event.detail
      
      cleanup()
      
      // 只要 success 为 true 就算成功（workflow_id 可能为 null，表示不自动启动工作流）
      if (success) {
        resolve(workflow_id || 'export_only')
      }
      else {
        reject(new Error(error || '批量导出失败'))
      }
    }
    
    // 清理函数
    const cleanup = () => {
      clearTimeout(timeout)
      window.removeEventListener('batchExportComplete', handleExportComplete as EventListener)
    }
    
    // 添加事件监听
    window.addEventListener('batchExportComplete', handleExportComplete as EventListener)
  })
}

// 开始视频导出
const startVideoExport = async () => {
  if (isExporting.value || !canExport.value) return
  
  try {
    isExporting.value = true
    
    // 生成项目名称
    const projectName = `pptist_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_')}`
    
    // 🔧 新流程：使用批量导出功能
    // eslint-disable-next-line no-console
    console.log('🚀 开始批量导出图片，项目名称:', projectName)
    
    // 1. 触发批量导出（自动进入Screen模式并导出）
    localStorage.setItem('auto_export_on_screen', 'true')
    localStorage.setItem('auto_start_workflow_after_export', 'true')
    localStorage.setItem('video_export_project_name', projectName)
    
    // eslint-disable-next-line no-console
    console.log('🎬 准备进入Screen模式进行批量导出...')
    
    // 等待批量导出完成的监听器
    let result
    try {
      result = await waitForBatchExportComplete()
      // eslint-disable-next-line no-console
      console.log('✅ 批量导出完成，工作流已自动启动, workflow_id:', result)
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('❌ 批量导出失败:', error)
      throw error
    }
    
    // 新的导出方法成功时返回workflowId字符串
    // eslint-disable-next-line no-console
    console.log('🔍 导出结果:', result, '类型:', typeof result)
    
    if (result) {
      // 使用全局workflowStore显示进度对话框
      workflowStore.showWorkflowProgress(result)
    }
    else {
      // eslint-disable-next-line no-console
      console.error('❌ 导出失败：未返回有效结果，result值为:', result)
      throw new Error('导出失败：未返回有效结果')
    }
  }
  catch (error) {
    // 处理错误但不使用console.error和alert
    isExporting.value = false
    throw error
  }
  finally {
    isExporting.value = false
  }
}
</script>

<style scoped>
.video-export-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 12px;
  min-height: 28px;
  position: relative;
  overflow: hidden;
}

.menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.menu-item:hover:not(.disabled) {
  background-color: #f1f5f9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.menu-item:hover:not(.disabled)::before {
  left: 100%;
}

.menu-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.config-btn {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #cbd5e1;
}

.video-export-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.video-export-btn:hover:not(.disabled) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.icon, .loading-icon {
  font-size: 14px;
}

.text {
  font-size: 11px;
  font-weight: 500;
}
</style>
