<template>
  <!-- 字符计数覆盖层 -->
  <div v-if="showOverlay" class="char-count-overlay">
    <div class="overlay-title">字符统计</div>
    <div 
      v-for="(line, index) in lines" 
      :key="index"
      class="line-counter"
      :class="{ 'warning': line.count > maxCharsPerLine }"
    >
      <span class="line-number">{{ index + 1 }}</span>
      <span class="count">{{ line.count }}</span>
    </div>
  </div>

  <!-- 侧边栏详细统计 -->
  <div v-if="showDetailedStats" class="line-stats">
    <div class="stats-header">
      <span class="title">各行字符统计</span>
      <span class="limit-info">限制：{{ maxCharsPerLine }}字/行</span>
    </div>
    <div class="line-items">
      <div 
        class="line-item" 
        v-for="(segment, index) in segments" 
        :key="index"
        :class="{ 'warning': segment.hasWarning }"
      >
        <div class="line-meta">
          <span class="line-number">第{{ index + 1 }}行</span>
          <span class="char-ratio">{{ segment.charCount }}/{{ maxCharsPerLine }}</span>
        </div>
        <div class="line-content">{{ segment.content.substring(0, 30) }}{{ segment.content.length > 30 ? '...' : '' }}</div>
        <div class="warning-text" v-if="segment.hasWarning">{{ segment.warning }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 接口定义
interface LineSegment {
  content: string
  charCount: number
  hasWarning: boolean
  warning?: string
}

interface LineInfo {
  count: number
  content: string
}

// Props
interface Props {
  content: string
  maxCharsPerLine: number
  showOverlay?: boolean
  showDetailedStats?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showOverlay: false,
  showDetailedStats: false
})

// 解析HTML内容中的行
const parseLines = (htmlContent: string): string[] => {
  if (!htmlContent) return []
  
  try {
    // 创建临时DOM元素来解析HTML
    const temp = document.createElement('div')
    temp.innerHTML = htmlContent
    
    // 获取文本内容并按行分割
    const textContent = temp.textContent || temp.innerText || ''
    
    // 按换行符分割，过滤空行
    const lines = textContent.split('\n').filter(line => line.trim())
    
    return lines.length > 0 ? lines : [textContent]
  } 
  catch (error) {
    // 备用方案：简单移除HTML标签
    const cleanText = htmlContent.replace(/<[^>]*>/g, '')
    return cleanText ? [cleanText] : []
  }
}

// 计算行信息（用于覆盖层）
const lines = computed((): LineInfo[] => {
  const parsedLines = parseLines(props.content)
  return parsedLines.map(line => ({
    count: line.length,
    content: line
  }))
})

// 计算分段信息（用于详细统计）
const segments = computed((): LineSegment[] => {
  const parsedLines = parseLines(props.content)
  
  return parsedLines.map(line => {
    const charCount = line.length
    const hasWarning = charCount > props.maxCharsPerLine
    
    return {
      content: line,
      charCount,
      hasWarning,
      warning: hasWarning ? `超出 ${charCount - props.maxCharsPerLine} 字符` : undefined
    }
  })
})

// 导出给父组件使用的计算属性
defineExpose({
  lines,
  segments,
  hasContent: computed(() => props.content.trim().length > 0),
  hasNewlines: computed(() => lines.value.length > 1),
  characterCount: computed(() => {
    const text = props.content.replace(/<[^>]*>/g, '')
    return text.length
  }),
  segmentCount: computed(() => segments.value.length)
})
</script>

<style lang="scss" scoped>
// 字符计数覆盖层样式
.char-count-overlay {
  position: absolute;
  right: 15px;
  top: 20px;
  z-index: 100;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border: 1px solid rgba(0,0,0,0.1);
  min-width: 120px;

  .overlay-title {
    font-size: 11px;
    font-weight: 700;
    color: #374151;
    margin-bottom: 4px;
    text-align: center;
  }

  .line-counter {
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2px;
    padding: 0 4px;

    .line-number {
      font-size: 10px;
      color: #6b7280;
      font-weight: 500;
    }

    .count {
      background: rgba(59, 130, 246, 0.1);
      color: #3b82f6;
      padding: 1px 6px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid rgba(59, 130, 246, 0.2);
    }

    &.warning {
      .count {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border-color: rgba(239, 68, 68, 0.3);
        font-weight: 700;
      }

      .line-number {
        color: #ef4444;
      }
    }
  }
}

// 详细统计样式（侧边栏版本）
.line-stats {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 10px;
  font-size: 11px;
  
  .stats-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #dee2e6;
    
    .title {
      font-weight: 600;
      color: #495057;
      font-size: 12px;
    }

    .limit-info {
      font-size: 10px;
      color: #6c757d;
      background: #e9ecef;
      padding: 2px 6px;
      border-radius: 8px;
      text-align: center;
    }
  }
  
  .line-items {
    max-height: 200px;
    overflow-y: auto;
  }
  
  .line-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 4px 6px;
    margin: 2px 0;
    border-radius: 4px;
    transition: all 0.2s ease;
    
    &:hover {
      background: rgba(0, 123, 255, 0.05);
    }

    &.warning {
      background: rgba(220, 53, 69, 0.1);
      border-left: 2px solid #dc3545;
      
      .char-ratio {
        color: #dc3545;
        font-weight: 600;
      }
    }
    
    .line-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 4px;
    }
    
    .line-number {
      font-size: 10px;
      color: #6c757d;
      font-weight: 500;
    }

    .char-ratio {
      font-weight: 600;
      color: #495057;
      font-size: 11px;
    }

    .line-content {
      color: #495057;
      font-size: 10px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-top: 2px;
    }

    .warning-text {
      font-size: 9px;
      color: #dc3545;
      font-weight: 500;
      margin-top: 1px;
    }
  }
}
</style>