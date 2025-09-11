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
      <div class="remark-stats">
        <span class="char-count">{{ characterCount }}/2000</span>
        <span class="duration">{{ estimatedDuration }}</span>
        <button class="preview-btn" @click="previewAudio" :disabled="!remark.trim()">
          <IconVolumeNotice />
          试听
        </button>
      </div>
    </div>
    
    <!-- 原有编辑器 -->
    <div class="editor-container">
      <Editor
        :value="remark"
        ref="editorRef"
        @update="value => handleInput(value)"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, useTemplateRef, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'

import Editor from './Editor.vue'

const props = defineProps<{
  height: number
}>()

const emit = defineEmits<{
  (event: 'update:height', payload: number): void
}>()

const slidesStore = useSlidesStore()
const { currentSlide } = storeToRefs(slidesStore)

const editorRef = useTemplateRef<InstanceType<typeof Editor>>('editorRef')

// 最大字符数限制
const maxCharacters = 2000

watch(() => currentSlide.value?.id, () => {
  nextTick(() => {
    editorRef.value!.updateTextContent()
  })
}, {
  immediate: true,
})

const remark = computed(() => currentSlide.value?.remark || '')

// 字符统计
const characterCount = computed(() => {
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

const handleInput = (content: string) => {
  // 检查字符数限制
  const textContent = content.replace(/<[^>]*>/g, '')
  if (textContent.length > maxCharacters) {
    return
  }
  
  slidesStore.updateSlide({ remark: content })
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

    if (newHeight < 120) newHeight = 120 // 增加最小高度以容纳新UI
    if (newHeight > 500) newHeight = 500 // 增加最大高度

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
  background: #fff;
  display: flex;
  flex-direction: column;
  height: 100%;
}

// 拖拽调整区域
.resize-handler {
  height: 8px;
  position: absolute;
  top: -4px;
  left: 0;
  right: 0;
  cursor: n-resize;
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  
  &:hover .resize-indicator {
    opacity: 1;
    transform: scale(1.1);
  }
}

.resize-indicator {
  width: 40px;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
  opacity: 0.6;
  transition: all 0.2s ease;
}

// 信息栏
.remark-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 12px;
  min-height: 32px;
}

.remark-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  
  .title-icon {
    font-size: 14px;
    color: #ffd700;
  }
}

.remark-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.char-count {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.15);
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 11px;
}

.duration {
  color: rgba(255, 255, 255, 0.8);
  font-size: 11px;
}

.preview-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.25);
    transform: translateY(-1px);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      transform: none;
    }
  }
}

// 编辑器容器
.editor-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

// 保持原有编辑器样式
:deep(.editor) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.prosemirror-editor) {
  flex: 1;
  padding: 12px;
  outline: none;
  line-height: 1.6;
  font-size: 14px;
  overflow-y: auto;
}

:deep(.menu) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-top: 1px solid #eee;
  flex-shrink: 0;
}

:deep(.menu button) {
  padding: 4px 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #f0f0f0;
  }
  
  &.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
  }
}
</style>