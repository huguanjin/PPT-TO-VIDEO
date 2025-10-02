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
      
      if (success && workflow_id) {
        resolve(workflow_id)
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

.workflow-progress-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 99999 !important;
  animation: fadeIn 0.3s ease-out;
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.workflow-progress-modal {
  background: white !important;
  border-radius: 20px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  width: 90% !important;
  max-width: 700px !important;
  min-width: 500px !important;
  max-height: 85vh !important;
  min-height: 400px !important;
  overflow: hidden;
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative !important;
  margin: 0 !important;
  transform: none !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(50px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  position: relative;
  overflow: hidden;
}

.modal-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.05"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.08"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  pointer-events: none;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  position: relative;
  z-index: 1;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  color: white;
  border-radius: 8px;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.modal-content {
  padding: 0;
  overflow-y: auto;
  max-height: calc(85vh - 160px); /* 减去header和footer的高度 */
  position: relative;
}

.modal-content::before {
  content: '';
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.workflow-status {
  min-height: 300px;
  padding: 28px;
}

/* 滚动区域渐变指示器 */
.modal-content::after {
  content: '';
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  height: 20px;
  background: linear-gradient(180deg, transparent 0%, rgba(255, 255, 255, 0.9) 70%, white 100%);
  pointer-events: none;
  z-index: 5;
}

.status-info h3 {
  margin: 0 0 16px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-info h3::before {
  content: '🎬';
  font-size: 24px;
}

.current-step {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  padding: 12px 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  font-weight: 500;
  color: #374151;
  border: 1px solid #d1d5db;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: #f9fafb;
  border: 2px solid transparent;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.step-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(255, 255, 255, 0.5) 50%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.step-item.running {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-color: #3b82f6;
  box-shadow: 0 8px 25px -8px rgba(59, 130, 246, 0.3);
  animation: pulse 2s infinite;
}

.step-item.running::before {
  opacity: 1;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 8px 25px -8px rgba(59, 130, 246, 0.3);
  }
  50% {
    box-shadow: 0 8px 25px -8px rgba(59, 130, 246, 0.5);
  }
}

.step-item.completed {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #10b981;
  box-shadow: 0 4px 15px -4px rgba(16, 185, 129, 0.2);
  animation: completePulse 0.6s ease-out;
}

@keyframes completePulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}

.step-item.failed {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-color: #ef4444;
  box-shadow: 0 4px 15px -4px rgba(239, 68, 68, 0.2);
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.step-number {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.1);
}

.step-item.running .step-number {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  animation: rotate 2s linear infinite;
  box-shadow: 0 6px 20px -6px rgba(59, 130, 246, 0.4);
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-item.completed .step-number {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 6px 20px -6px rgba(16, 185, 129, 0.4);
}

.step-item.completed .step-number::after {
  content: '✓';
  position: absolute;
  animation: checkmark 0.4s ease-out 0.2s both;
}

@keyframes checkmark {
  0% {
    transform: scale(0) rotate(45deg);
    opacity: 0;
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

.step-item.failed .step-number {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 6px 20px -6px rgba(239, 68, 68, 0.4);
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-name {
  font-weight: 600;
  margin-bottom: 12px;
  color: #1f2937;
  font-size: 16px;
}

.step-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-percent {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  min-width: 45px;
  text-align: right;
}

.step-message {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.4;
}

.completion-actions {
  margin-top: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-radius: 16px;
  text-align: center;
  border: 2px solid #10b981;
  animation: completionGlow 2s ease-in-out infinite alternate;
}

@keyframes completionGlow {
  from {
    box-shadow: 0 4px 20px -4px rgba(16, 185, 129, 0.3);
  }
  to {
    box-shadow: 0 8px 30px -4px rgba(16, 185, 129, 0.5);
  }
}

.success-message {
  font-size: 18px;
  font-weight: 700;
  color: #059669;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.download-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  box-shadow: 0 4px 15px -2px rgba(16, 185, 129, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.download-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -4px rgba(16, 185, 129, 0.6);
}

.error-message {
  margin-top: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-radius: 16px;
  color: #dc2626;
  text-align: center;
  border: 2px solid #ef4444;
  font-weight: 600;
}

.loading-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 24px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-status div {
  font-size: 16px;
  font-weight: 500;
  color: #6b7280;
}

.modal-footer {
  padding: 20px 28px;
  border-top: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  text-align: right;
}

.close-workflow-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.close-workflow-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
  transform: translateY(-1px);
}

.close-workflow-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 滚动条美化和增强 */
.modal-content {
  scroll-behavior: smooth;
}

.modal-content::-webkit-scrollbar {
  width: 12px;
  background: transparent;
}

.modal-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 6px;
  margin: 4px 0;
}

.modal-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  border: 2px solid #f1f5f9;
  transition: all 0.3s ease;
}

.modal-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  border-color: #e2e8f0;
  transform: scale(1.1);
}

.modal-content::-webkit-scrollbar-thumb:active {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
}

/* 滚动指示器 */
.modal-content::-webkit-scrollbar-corner {
  background: transparent;
}

/* 确保模态框显示的重置样式 */
.workflow-progress-overlay * {
  box-sizing: border-box !important;
}

.workflow-progress-overlay {
  pointer-events: auto !important;
}

.workflow-progress-modal {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

/* 高亮脉冲动画 */
@keyframes highlightPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
    background-color: rgba(74, 222, 128, 0.1);
  }
  25% {
    box-shadow: 0 0 0 10px rgba(74, 222, 128, 0.5);
    background-color: rgba(74, 222, 128, 0.2);
  }
  50% {
    box-shadow: 0 0 0 20px rgba(74, 222, 128, 0.3);
    background-color: rgba(74, 222, 128, 0.15);
  }
  75% {
    box-shadow: 0 0 0 10px rgba(74, 222, 128, 0.2);
    background-color: rgba(74, 222, 128, 0.1);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
    background-color: transparent;
  }
}

/* 调试样式 - 临时添加以确保可见性 */
.workflow-progress-overlay {
  border: 2px solid red !important; /* 临时调试边框 */
}

.workflow-progress-modal {
  border: 2px solid blue !important; /* 临时调试边框 */
}
</style>
