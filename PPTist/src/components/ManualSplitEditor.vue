<!--
手动分割编辑器组件
在配音稿编辑区域添加换行分割功能
-->
<template>
  <div class="manual-split-editor">
    <!-- 手动分割控制栏 -->
    <div class="split-control-bar" v-if="showControls">
      <div class="split-mode-toggle">
        <label class="toggle-switch">
          <input 
            type="checkbox" 
            v-model="manualSplitEnabled"
            @change="handleSplitModeChange"
          />
          <span class="toggle-slider"></span>
          <span class="toggle-label">换行分割模式</span>
        </label>
      </div>
      
      <div class="split-preview" v-if="manualSplitEnabled && showPreview">
        <div class="preview-label">分割预览：</div>
        <div class="segment-count">{{ segmentCount }} 个片段</div>
        <div class="total-duration">预计总时长：{{ totalDuration }}</div>
      </div>
      
      <div class="split-actions" v-if="manualSplitEnabled">
        <button 
          class="action-btn preview-btn"
          @click="previewSplit"
          :disabled="!hasContent"
          title="预览分割效果"
        >
          <i class="icon">👁️</i>
          预览
        </button>
        <button 
          class="action-btn clear-btn"
          @click="clearSplits"
          :disabled="!hasNewlines"
          title="清除所有换行符"
        >
          <i class="icon">🧹</i>
          清除分割
        </button>
      </div>
    </div>
    
    <!-- 分割预览面板 -->
    <div class="split-preview-panel" v-if="showDetailedPreview">
      <div class="preview-header">
        <h4>分割预览</h4>
        <button class="close-btn" @click="showDetailedPreview = false">×</button>
      </div>
      <div class="preview-content">
        <div 
          class="segment-item" 
          v-for="(segment, index) in previewSegments" 
          :key="index"
          :class="{ 'warning': segment.hasWarning }"
        >
          <div class="segment-header">
            <span class="segment-index">{{ index + 1 }}</span>
            <span class="segment-duration">{{ segment.duration }}秒</span>
            <span class="segment-chars">{{ segment.charCount }}字</span>
          </div>
          <div class="segment-content">{{ segment.content }}</div>
          <div class="segment-warnings" v-if="segment.hasWarning">
            <i class="warning-icon">⚠️</i>
            <span>{{ segment.warning }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 原始编辑器（增强版） -->
    <div class="enhanced-editor-container" :class="{ 'split-mode': manualSplitEnabled }">
      <slot></slot>
    </div>
    
    <!-- 分割辅助信息 -->
    <div class="split-help" v-if="manualSplitEnabled && showHelp">
      <div class="help-content">
        <p>💡 使用 <kbd>Enter</kbd> 键创建分割点</p>
        <p>🎯 每个段落将独立生成音频</p>
        <p>⏱️ 建议每段控制在 5-10 秒内</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'

interface SegmentPreview {
  content: string
  duration: number
  charCount: number
  hasWarning: boolean
  warning?: string
}

const props = defineProps<{
  content: string
  showControls?: boolean
  showPreview?: boolean
  showHelp?: boolean
}>()

const emit = defineEmits<{
  (event: 'splitModeChange', enabled: boolean): void
  (event: 'contentUpdate', content: string): void
}>()

// 响应式状态
const manualSplitEnabled = ref(false)
const showDetailedPreview = ref(false)

// 计算属性
const hasContent = computed(() => {
  return props.content && props.content.trim().length > 0
})

const hasNewlines = computed(() => {
  return props.content && props.content.includes('\\n')
})

const segmentCount = computed(() => {
  if (!manualSplitEnabled.value || !hasContent.value) return 0
  return props.content.split('\\n').filter(line => line.trim()).length
})

const previewSegments = computed<SegmentPreview[]>(() => {
  if (!manualSplitEnabled.value || !hasContent.value) return []
  
  const segments = props.content.split('\\n').filter(line => line.trim())
  
  return segments.map((content) => {
    const charCount = content.trim().length
    const duration = Math.max(1, Math.round(charCount / 4.2)) // 4.2字/秒的语速
    
    let hasWarning = false
    let warning = ''
    
    if (charCount < 5) {
      hasWarning = true
      warning = '片段过短，可能影响语音效果'
    }
    else if (charCount > 50) {
      hasWarning = true
      warning = '片段过长，建议进一步分割'
    }
    else if (duration > 10) {
      hasWarning = true
      warning = '预计时长过长，建议缩短'
    }
    
    return {
      content: content.trim(),
      duration,
      charCount,
      hasWarning,
      warning
    }
  })
})

const totalDuration = computed(() => {
  const total = previewSegments.value.reduce((sum, seg) => sum + seg.duration, 0)
  if (total < 60) return `${total}秒`
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}分${seconds}秒`
})

// 方法
const handleSplitModeChange = () => {
  emit('splitModeChange', manualSplitEnabled.value)
}

const previewSplit = () => {
  showDetailedPreview.value = true
}

const clearSplits = () => {
  // eslint-disable-next-line no-alert
  if (confirm('确定要清除所有换行分割吗？')) {
    const cleanContent = props.content.replace(/\\n/g, ' ').replace(/\\s+/g, ' ')
    emit('contentUpdate', cleanContent)
  }
}

// 监听分割模式变化
watch(manualSplitEnabled, (enabled) => {
  if (!enabled) {
    showDetailedPreview.value = false
  }
})
</script>

<style scoped>
.manual-split-editor {
  position: relative;
}

.split-control-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e4e8;
  border-radius: 4px 4px 0 0;
}

.split-mode-toggle {
  display: flex;
  align-items: center;
}

.toggle-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.toggle-switch input {
  position: relative;
  width: 40px;
  height: 20px;
  appearance: none;
  background: #ccc;
  border-radius: 10px;
  outline: none;
  transition: background 0.3s;
}

.toggle-switch input:checked {
  background: #4CAF50;
}

.toggle-switch input::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  transition: left 0.3s;
}

.toggle-switch input:checked::before {
  left: 22px;
}

.toggle-label {
  font-size: 14px;
  color: #333;
}

.split-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.preview-label {
  color: #333;
}

.segment-count {
  background: #007bff;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
}

.total-duration {
  background: #28a745;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
}

.split-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid #ddd;
  border-radius: 3px;
  background: white;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: #f0f0f0;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preview-btn:hover:not(:disabled) {
  border-color: #007bff;
  color: #007bff;
}

.clear-btn:hover:not(:disabled) {
  border-color: #dc3545;
  color: #dc3545;
}

.split-preview-panel {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 300px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e4e8;
}

.preview-header h4 {
  margin: 0;
  font-size: 14px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.preview-content {
  max-height: 240px;
  overflow-y: auto;
  padding: 8px;
}

.segment-item {
  margin-bottom: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-left: 3px solid #28a745;
  border-radius: 4px;
}

.segment-item.warning {
  border-left-color: #ffc107;
  background: #fff8e1;
}

.segment-header {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.segment-index {
  background: #007bff;
  color: white;
  padding: 1px 6px;
  border-radius: 2px;
  min-width: 20px;
  text-align: center;
}

.segment-duration, .segment-chars {
  background: #6c757d;
  color: white;
  padding: 1px 4px;
  border-radius: 2px;
}

.segment-content {
  font-size: 13px;
  line-height: 1.4;
  color: #333;
}

.segment-warnings {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 11px;
  color: #856404;
}

.enhanced-editor-container.split-mode {
  border: 2px dashed #4CAF50;
  border-radius: 4px;
}

.split-help {
  padding: 8px 12px;
  background: #e8f5e8;
  border-top: 1px solid #c3e6c3;
  font-size: 12px;
}

.help-content p {
  margin: 4px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

kbd {
  display: inline-block;
  padding: 2px 4px;
  font-size: 11px;
  line-height: 1;
  color: #444d56;
  vertical-align: middle;
  background-color: #fafbfc;
  border: solid 1px #c6cbd1;
  border-bottom-color: #959da5;
  border-radius: 3px;
  box-shadow: inset 0 -1px 0 #959da5;
}
</style>