<template>
  <div class="enhanced-remark">
    <!-- 拖拽调整区域 -->
    <div 
      class="resize-handler"
      @mousedown="$event => resize($event)"
    >
      <div class="resize-indicator"></div>
    </div>
    
    <!-- 增强的顶部信息栏 -->
    <div class="remark-info-bar">
      <div class="remark-title">
        <IconComment class="title-icon" />
        <span>配音稿</span>
      </div>
      
      <!-- 换行分割模式控制 - 移动到标题栏 -->
      <div class="split-mode-controls">
        <label class="toggle-switch">
          <input 
            type="checkbox" 
            v-model="manualSplitEnabled"
            @change="handleSplitModeChange"
          />
          <span class="toggle-slider"></span>
          <span class="toggle-label">换行分割</span>
        </label>
        
        <!-- 分割模式操作按钮 -->
        <div class="split-actions" v-if="manualSplitEnabled">
          <button 
            class="action-btn clear-btn"
            @click="clearSplits"
            :disabled="!hasNewlines"
            title="清除所有换行符"
          >
            <span class="icon">🧹</span>
          </button>
          
          <!-- 分割统计信息 -->
          <div class="split-stats" v-if="hasNewlines">
            <span class="segment-count">{{ segmentCount }}段</span>
            <span class="char-limit-info">单行限制{{ subtitleConfig.max_chars_per_line }}字</span>
          </div>
        </div>
      </div>
      
      <div class="remark-stats">
        <span class="char-count">{{ characterCount }}/2000</span>
        <span class="duration">{{ estimatedDuration }}</span>
        <button class="preview-btn" @click="previewAudio" :disabled="!remark.trim()">
          <IconVolumeNotice />
          试听
        </button>
      </div>
    </div>
    
    <!-- 编辑器容器 -->
    <div class="editor-container" :class="{ 'split-mode': manualSplitEnabled }">
      <div class="editor-wrapper">
        <Editor
          :value="remark"
          ref="editorRef"
          @update="value => handleInput(value)"
          @keydown="forceRefresh"
          @keyup="forceRefresh"
          @input="forceRefresh"
        />
        
        <!-- 实时字符长度overlay -->
        <div class="char-count-overlay" v-if="manualSplitEnabled && hasContent">
          <div class="overlay-title">字符统计</div>
          <div 
            class="line-counter"
            v-for="(line, index) in reactiveCurrentLines" 
            :key="index"
            :class="{ 'warning': line.isOverLimit }"
          >
            <span class="line-number">第{{ index + 1 }}行:</span>
            <span class="count">{{ line.length }}/{{ subtitleConfig.max_chars_per_line }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分割辅助信息 -->
    <div class="split-help" v-if="manualSplitEnabled">
      <div class="help-content">
        <p>💡 使用 <kbd>Enter</kbd> 键创建分割点</p>
        <p>🎯 每个段落将独立生成音频</p>
        <p>⏱️ 建议每段控制在 5-10 秒内</p>
        <p>📏 单行字符限制：{{ subtitleConfig.max_chars_per_line }} 字</p>
      </div>
    </div>
    
    <!-- 实时字符长度显示 -->
    <div class="line-stats" v-if="manualSplitEnabled && hasNewlines">
      <div class="stats-header">
        <span class="title">各行字符统计</span>
        <span class="limit-info">限制：{{ subtitleConfig.max_chars_per_line }}字/行</span>
      </div>
      <div class="line-items">
        <div 
          class="line-item" 
          v-for="(segment, index) in previewSegments" 
          :key="index"
          :class="{ 'warning': segment.hasWarning }"
        >
          <span class="line-number">第{{ index + 1 }}行</span>
          <span class="char-ratio">{{ segment.charCount }}/{{ subtitleConfig.max_chars_per_line }}</span>
          <span class="line-content">{{ segment.content.substring(0, 20) }}{{ segment.content.length > 20 ? '...' : '' }}</span>
          <span class="warning-text" v-if="segment.hasWarning">{{ segment.warning }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, useTemplateRef, watch, ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'
import axios from 'axios'

import Editor from './Editor.vue'

interface SegmentPreview {
  content: string
  duration: number
  charCount: number
  hasWarning: boolean
  warning?: string
}

interface SubtitleConfig {
  max_chars_per_line: number
  font_size: number
  font_family: string
  [key: string]: any
}

const props = defineProps<{
  height: number
}>()

const emit = defineEmits<{
  (event: 'update:height', payload: number): void
}>()

const slidesStore = useSlidesStore()
const { currentSlide } = storeToRefs(slidesStore)

const editorRef = useTemplateRef<InstanceType<typeof Editor>>('editorRef')

// 字幕配置状态
const subtitleConfig = ref<SubtitleConfig>({
  max_chars_per_line: 20, // 默认值
  font_size: 40,
  font_family: 'Microsoft YaHei'
})

// 手动分割相关状态
const manualSplitEnabled = ref(true) // 默认开启换行分割模式

// 强制刷新字符统计的响应式变量
const refreshTrigger = ref(0)

// 强制刷新函数
const forceRefresh = () => {
  nextTick(() => {
    refreshTrigger.value++
  })
}

// 最大字符数限制
const maxCharacters = 2000

// 获取字幕配置
const fetchSubtitleConfig = async () => {
  try {
    const response = await axios.get('/api/config/subtitle')
    if (response.data.success) {
      subtitleConfig.value = {
        ...subtitleConfig.value,
        ...response.data.data
      }
    }
  } 
  catch {
    // 获取字幕配置失败，使用默认值
  }
}

// 组件挂载时获取配置
onMounted(() => {
  fetchSubtitleConfig()
})

watch(() => currentSlide.value?.id, () => {
  nextTick(() => {
    editorRef.value!.updateTextContent()
  })
}, {
  immediate: true,
})

const remark = computed(() => currentSlide.value?.remark || '')

// 监听remark变化，强制刷新字符统计
watch(() => remark.value, () => {
  refreshTrigger.value++
}, { flush: 'post' })

// 字符统计
const characterCount = computed(() => {
  if (!remark.value) return 0
  const text = remark.value.replace(/<[^>]*>/g, '') // 移除HTML标签
  return text.length
})

// 预计时长计算（基于中文语速约250字/分钟）
const estimatedDuration = computed(() => {
  const chars = characterCount.value
  if (chars === 0) return '0秒'
  
  const minutes = chars / 250
  if (minutes < 1) {
    const seconds = Math.round(minutes * 60)
    return `${seconds}秒`
  }
  
  const mins = Math.floor(minutes)
  const secs = Math.round((minutes - mins) * 60)
  return secs > 0 ? `${mins}分${secs}秒` : `${mins}分钟`
})

// 手动分割相关计算属性
const hasContent = computed(() => {
  return remark.value && remark.value.trim().length > 0
})

const hasNewlines = computed(() => {
  if (!remark.value) return false
  const plainText = remark.value.replace(/<[^>]*>/g, '')
  return plainText.includes('\n')
})

const segmentCount = computed(() => {
  if (!manualSplitEnabled.value || !hasContent.value || !remark.value) return 0
  const plainText = remark.value.replace(/<[^>]*>/g, '')
  return plainText.split('\n').filter(line => line.trim()).length
})

// 修改后的currentLines，确保及时响应变化
const reactiveCurrentLines = computed(() => {
  // 通过访问refreshTrigger来强制重新计算
  refreshTrigger.value
  
  // 直接使用remark.value获取内容
  const htmlContent = remark.value
  
  if (!manualSplitEnabled.value || !htmlContent || !htmlContent.trim()) return []
  
  const maxChars = subtitleConfig.value.max_chars_per_line
  
  // 尝试多种方式解析行内容
  let lines: string[] = []
  
  // 1. 优先处理ProseMirror的段落结构（p标签）
  const pMatches = htmlContent.match(/<p[^>]*>.*?<\/p>/g)
  if (pMatches && pMatches.length > 0) {
    lines = pMatches.map(pTag => {
      return pTag
        .replace(/<p[^>]*>/g, '')
        .replace(/<\/p>/g, '')
        .replace(/<br\s*\/?>/gi, '')
        .replace(/<[^>]*>/g, '')
        .replace(/&nbsp;/g, ' ')
        .trim()
    }).filter(line => line)
  }
  
  // 2. 如果没有p标签，尝试处理div标签
  if (lines.length === 0) {
    const divMatches = htmlContent.match(/<div[^>]*>.*?<\/div>/g)
    if (divMatches && divMatches.length > 0) {
      lines = divMatches.map(divTag => {
        return divTag
          .replace(/<div[^>]*>/g, '')
          .replace(/<\/div>/g, '')
          .replace(/<br\s*\/?>/gi, '')
          .replace(/<[^>]*>/g, '')
          .replace(/&nbsp;/g, ' ')
          .trim()
      }).filter(line => line)
    }
  }
  
  // 3. 如果还是没有，尝试br标签分割
  if (lines.length === 0) {
    const plainText = htmlContent
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]*>/g, '')
      .replace(/&nbsp;/g, ' ')
      .trim()
    
    if (plainText.includes('\n')) {
      lines = plainText.split('\n').filter(line => line.trim())
    }
  }
  
  // 4. 最后回退到单行
  if (lines.length === 0) {
    const plainText = htmlContent
      .replace(/<[^>]*>/g, '')
      .replace(/&nbsp;/g, ' ')
      .trim()
    if (plainText) {
      lines = [plainText]
    }
  }
  
  return lines.map((line, index) => ({
    index,
    content: line,
    length: line.length,
    isOverLimit: line.length > maxChars
  }))
})

const previewSegments = computed<SegmentPreview[]>(() => {
  if (!manualSplitEnabled.value || !hasContent.value) return []
  
  const plainText = remark.value.replace(/<[^>]*>/g, '')
  const segments = plainText.split('\n').filter(line => line.trim())
  
  return segments.map((content) => {
    const charCount = content.trim().length
    const duration = Math.max(1, Math.round(charCount / 4.2)) // 4.2字/秒的语速
    const maxChars = subtitleConfig.value.max_chars_per_line
    
    // 检查各种警告条件
    let hasWarning = false
    let warning = ''
    
    // 优先检查字符长度限制
    if (charCount > maxChars) {
      hasWarning = true
      warning = `字符数超出限制 (${charCount}/${maxChars})`
    }
    else if (charCount < 5) {
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

// 手动分割方法
const handleSplitModeChange = () => {
  // 方法暂时保留为空，可用于后续扩展
}

const clearSplits = () => {
  // eslint-disable-next-line no-alert
  if (confirm('确定要清除所有换行分割吗？')) {
    const plainText = remark.value.replace(/<[^>]*>/g, '')
    const cleanContent = plainText.replace(/\n/g, ' ').replace(/\s+/g, ' ')
    slidesStore.updateSlide({ remark: cleanContent })
  }
}

const handleInput = (content: string) => {
  // 检查字符数限制
  const textContent = content.replace(/<[^>]*>/g, '')
  if (textContent.length > maxCharacters) {
    return
  }
  
  slidesStore.updateSlide({ remark: content })
  
  // 强制刷新字符统计
  nextTick(() => {
    forceRefresh()
  })
}

// 预览音频
const previewAudio = async () => {
  if (!remark.value.trim()) {
    return
  }
  
  try {
    // 调用TTS API生成音频预览
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
    const response = await fetch(`${API_BASE_URL}/api/tts/preview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: remark.value.replace(/<[^>]*>/g, ''), // 移除HTML标签
        engine: 'edge_tts',
        config: {
          voice: 'zh-CN-XiaoxiaoNeural',
          rate: 0,
          pitch: 0
        }
      })
    })
    
    if (response.ok) {
      const audioBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      
      audio.play().catch(() => {
        // 音频播放失败处理
      })
      
      // 清理URL对象
      audio.addEventListener('ended', () => {
        URL.revokeObjectURL(audioUrl)
      })
    }
  }
  catch (error) {
    // 错误处理
  }
}

const resize = (e: MouseEvent) => {
  let isMouseDown = true
  const startPageY = e.pageY
  const originHeight = props.height

  document.onmousemove = e => {
    if (!isMouseDown) return

    const currentPageY = e.pageY

    const moveY = currentPageY - startPageY
    let newHeight = -moveY + originHeight

    if (newHeight < 180) newHeight = 180 // 提高最小高度到180px，确保足够的编辑空间
    if (newHeight > 600) newHeight = 600 // 增加最大高度到600px

    emit('update:height', newHeight)
  }

  document.onmouseup = () => {
    isMouseDown = false
    document.onmousemove = null
    document.onmouseup = null
  }
}
</script>

<style lang="scss" scoped>
.enhanced-remark {
  position: relative;
  border-top: 1px solid $borderColor;
  background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%);
  display: flex;
  flex-direction: column;
  height: 100%;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.1);
}

// 拖拽调整区域
.resize-handler {
  height: 10px;
  position: absolute;
  top: -5px;
  left: 0;
  right: 0;
  cursor: n-resize;
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  
  &:hover .resize-indicator {
    opacity: 1;
    transform: scale(1.2);
  }
  
  // 增加拖拽热区
  &::before {
    content: '';
    position: absolute;
    top: -5px;
    left: 0;
    right: 0;
    height: 20px;
  }
}

.resize-indicator {
  width: 50px;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
  opacity: 0.7;
  transition: all 0.3s ease;
  
  &::before {
    content: '拖拽调整高度';
    position: absolute;
    top: -25px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
  }
}

.resize-handler:hover .resize-indicator::before {
  opacity: 1;
}

// 编辑器容器
.editor-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e1e5e9;
  margin: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  &.split-mode {
    border: 2px solid #4CAF50;
    border-radius: 8px;
    background: linear-gradient(135deg, #f8fff8 0%, #f0fff4 100%);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
  }
  
  .editor-wrapper {
    position: relative;
    height: 100%;
  }
  
  .char-count-overlay { position: absolute; right: 15px; top: 20px; z-index: 100; pointer-events: none; background: rgba(255, 255, 255, 0.95); border-radius: 8px; padding: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 1px solid rgba(0,0,0,0.1); min-width: 120px; }
  .char-count-overlay .overlay-title { font-size: 11px; font-weight: 700; color: #374151; margin-bottom: 4px; text-align: center; }
  .char-count-overlay .line-counter { height: 20px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px; padding: 0 4px; }
  .char-count-overlay .line-counter .line-number { font-size: 10px; color: #6b7280; font-weight: 500; }
  .char-count-overlay .line-counter .count { background: rgba(59, 130, 246, 0.1); color: #3b82f6; padding: 1px 6px; border-radius: 10px; font-size: 11px; font-weight: 600; border: 1px solid rgba(59, 130, 246, 0.2); }
  .char-count-overlay .line-counter.warning .count { background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); font-weight: 700; }
  .char-count-overlay .line-counter.warning .line-number { color: #ef4444; }
}

// 信息栏
.remark-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 13px;
  min-height: 48px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
  
  .remark-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 14px;
    
    .title-icon {
      width: 18px;
      height: 18px;
      opacity: 0.9;
    }
  }
  
  // 换行分割模式控制区域
  .split-mode-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .toggle-switch {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      
      input {
        position: relative;
        width: 36px;
        height: 18px;
        appearance: none;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 9px;
        outline: none;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
        
        &:checked {
          background: rgba(255, 255, 255, 0.9);
        }
        
        &::before {
          content: '';
          position: absolute;
          top: 1px;
          left: 1px;
          width: 14px;
          height: 14px;
          background: #667eea;
          border-radius: 50%;
          transition: all 0.3s ease;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        &:checked::before {
          left: 19px;
          background: #4CAF50;
        }
      }
      
      .toggle-label {
        font-size: 13px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.95);
      }
    }
    
    .split-actions {
      display: flex;
      align-items: center;
      gap: 6px;
      
      .action-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        padding: 0;
        font-size: 12px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.9);
        cursor: pointer;
        transition: all 0.2s ease;
        
        .icon {
          font-size: 14px;
        }
        
        &:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.2);
          border-color: rgba(255, 255, 255, 0.5);
          transform: translateY(-1px);
        }
        
        &:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
      }
      
      .split-stats {
        margin-left: 8px;
        
        .segment-count {
          background: rgba(255, 255, 255, 0.2);
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 500;
          color: rgba(255, 255, 255, 0.95);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .char-limit-info {
          background: rgba(255, 255, 255, 0.15);
          padding: 3px 6px;
          border-radius: 10px;
          font-size: 10px;
          font-weight: 500;
          color: rgba(255, 255, 255, 0.9);
          border: 1px solid rgba(255, 255, 255, 0.1);
          margin-left: 4px;
        }
      }
    }
  }
  
  .remark-stats {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .char-count {
      font-size: 12px;
      opacity: 0.8;
    }
    
    .duration {
      font-size: 12px;
      opacity: 0.8;
    }
    
    .preview-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 500;
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.15);
      color: white;
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.25);
        border-color: rgba(255, 255, 255, 0.5);
        transform: translateY(-1px);
      }
      
      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      
      svg {
        width: 14px;
        height: 14px;
      }
    }
  }
}

// 分割辅助信息
.split-help {
  padding: 12px 16px;
  background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
  border-top: 2px solid #c3e6c3;
  font-size: 13px;
  flex-shrink: 0;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
}

.help-content p {
  margin: 6px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #155724;
  font-weight: 500;
}

kbd {
  display: inline-block;
  padding: 3px 6px;
  font-size: 11px;
  line-height: 1;
  color: #495057;
  vertical-align: middle;
  background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
  border: solid 1px #ced4da;
  border-bottom-color: #adb5bd;
  border-radius: 4px;
  box-shadow: inset 0 -1px 0 #adb5bd, 0 1px 2px rgba(0,0,0,0.1);
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}

// 保持原有编辑器样式
:deep(.editor) {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

:deep(.prosemirror-editor) {
  flex: 1;
  padding: 16px 20px;
  outline: none;
  line-height: 1.8;
  font-size: 16px;
  color: #2c3e50;
  background: #fff;
  overflow-y: auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  min-height: 100px; // 确保最小可编辑区域
  
  // 增强文本可读性
  p {
    margin: 8px 0;
    color: #2c3e50;
    font-weight: 400;
  }
  
  // 空状态提示
  &:empty::before {
    content: '请输入配音稿内容...\A\A💡 提示：使用换行分割模式可以精确控制字幕分段\A🎤 支持实时试听功能';
    color: #95a5a6;
    font-style: italic;
    pointer-events: none;
    white-space: pre-line;
    line-height: 1.6;
  }
  
  // 聚焦状态
  &:focus {
    background: #fafbfc;
    box-shadow: inset 0 0 0 2px rgba(102, 126, 234, 0.1);
  }
  
  // 选中文本样式
  ::selection {
    background: rgba(102, 126, 234, 0.2);
    color: #2c3e50;
  }
  
  // 响应式字体大小
  @media (max-height: 800px) {
    font-size: 15px;
    line-height: 1.7;
    padding: 14px 18px;
  }
}

// 实时字符统计样式
.line-stats {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 6px;
  margin: 8px 4px 4px 4px;
  padding: 12px;
  font-size: 13px;
  
  .stats-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #dee2e6;
    
    .title { font-weight: 600; color: #495057; }
    .limit-info { font-size: 12px; color: #6c757d; background: #e9ecef; padding: 2px 8px; border-radius: 10px; }
  }
  
  .line-items { max-height: 120px; overflow-y: auto; }
  
  .line-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    margin: 2px 0;
    border-radius: 4px;
    transition: all 0.2s ease;
    
    &:hover { background: rgba(0, 123, 255, 0.05); }
    &.warning { background: rgba(220, 53, 69, 0.1); border-left: 3px solid #dc3545; .char-ratio { color: #dc3545; font-weight: 600; } }
    
    .line-number { min-width: 50px; font-size: 11px; color: #6c757d; font-weight: 500; }
    .char-ratio { min-width: 40px; font-weight: 600; color: #495057; font-size: 12px; }
    .line-content { flex: 1; color: #495057; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .warning-text { font-size: 11px; color: #dc3545; font-weight: 500; }
  }
}

:deep(.menu) { display: flex; align-items: center; gap: 6px; padding: 10px 16px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-top: 1px solid #dee2e6; flex-shrink: 0; box-shadow: 0 -2px 8px rgba(0,0,0,0.05); }

:deep(.menu button) { padding: 6px 8px; border: 1px solid #ced4da; border-radius: 6px; background: white; color: #495057; cursor: pointer; transition: all 0.2s ease; font-size: 13px; min-width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
:deep(.menu button:hover) { background: #f8f9fa; border-color: #667eea; color: #667eea; transform: translateY(-1px); box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
:deep(.menu button.active) { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-color: #667eea; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3); }

// 响应式适配
@media (max-height: 900px) {
  .remark-info-bar { padding: 8px 16px; min-height: 44px; font-size: 12px; }
  .remark-info-bar .remark-title { font-size: 13px; }
  .remark-info-bar .split-mode-controls { gap: 8px; }
  .remark-info-bar .split-actions { gap: 4px; }
  .remark-info-bar .split-actions .action-btn { width: 24px; height: 24px; }
  .remark-info-bar .remark-stats { gap: 8px; }
  .remark-info-bar .preview-btn { padding: 5px 10px; font-size: 11px; }
}

@media (max-height: 700px) {
  .remark-info-bar { padding: 6px 14px; min-height: 40px; }
  .remark-info-bar .split-actions .action-btn { width: 22px; height: 22px; }
  :deep(.prosemirror-editor) { font-size: 14px; line-height: 1.6; padding: 12px 16px; }
}

@media (max-width: 1200px) {
  .remark-info-bar { flex-wrap: wrap; gap: 8px; min-height: auto; }
  .remark-info-bar .split-mode-controls { order: 3; flex-basis: 100%; justify-content: center; margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255, 255, 255, 0.2); }
}
</style>