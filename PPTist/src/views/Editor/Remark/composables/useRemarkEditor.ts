import { ref, computed, onMounted, type Ref } from 'vue'
import { useSlidesStore } from '@/store'
import axios from 'axios'
import { getAuthJsonHeaders } from '@/utils/authFetch'

// 字幕配置接口
export interface SubtitleConfig {
  max_chars_per_line: number
  quality_preset: string
  encoding_settings: {
    font_family: string
    font_size: number
    margin_v: number
  }
}

// 使用字幕配置的组合式函数
export function useSubtitleConfig() {
  const subtitleConfig = ref<SubtitleConfig>({
    max_chars_per_line: 20,
    quality_preset: 'netflix',
    encoding_settings: {
      font_family: 'Arial',
      font_size: 16,
      margin_v: 20
    }
  })

  const fetchSubtitleConfig = async () => {
    try {
      const response = await axios.get('/api/config/subtitle')
      if (response.data) {
        subtitleConfig.value = response.data
      }
    } 
    catch {
      // 使用默认配置，静默处理错误
    }
  }

  onMounted(() => {
    fetchSubtitleConfig()
  })

  return {
    subtitleConfig,
    fetchSubtitleConfig
  }
}

// 字符统计相关的组合式函数
export function useCharacterStats(content: Ref<string>, maxCharsPerLine: Ref<number>) {
  const refreshTrigger = ref(0)

  // 强制刷新统计
  const forceRefresh = () => {
    refreshTrigger.value += 1
  }

  // 响应式的当前行内容
  const reactiveCurrentLines = computed(() => {
    // 使用refreshTrigger触发重新计算
    refreshTrigger.value // 这行确保响应性
    
    if (!content.value) return []
    
    try {
      const temp = document.createElement('div')
      temp.innerHTML = content.value
      const textContent = temp.textContent || temp.innerText || ''
      const lines = textContent.split('\n').filter(line => line.trim())
      return lines.length > 0 ? lines : [textContent]
    } 
    catch {
      const cleanText = content.value.replace(/<[^>]*>/g, '')
      return cleanText ? [cleanText] : []
    }
  })

  // 字符计数
  const characterCount = computed(() => {
    const text = content.value.replace(/<[^>]*>/g, '')
    return text.length
  })

  // 内容检查
  const hasContent = computed(() => content.value.trim().length > 0)
  const hasNewlines = computed(() => reactiveCurrentLines.value.length > 1)
  const segmentCount = computed(() => reactiveCurrentLines.value.length)

  // 预计时长（按每分钟300字估算）
  const estimatedDuration = computed(() => {
    const charCount = characterCount.value
    if (charCount === 0) return 0
    return Math.ceil((charCount / 300) * 60)
  })

  // 预览分段
  const previewSegments = computed(() => {
    return reactiveCurrentLines.value.map((line, index) => {
      const charCount = line.length
      const maxChars = maxCharsPerLine.value
      const hasWarning = charCount > maxChars
      const ratio = `${charCount}/${maxChars}`
      
      return {
        index: index + 1,
        content: line,
        charCount,
        maxChars,
        ratio,
        hasWarning,
        warningText: hasWarning ? `超出 ${charCount - maxChars} 字符` : undefined,
        percentage: maxChars > 0 ? Math.round((charCount / maxChars) * 100) : 0
      }
    })
  })

  // 总体统计信息
  const overallStats = computed(() => {
    const totalLines = reactiveCurrentLines.value.length
    const overLimitLines = previewSegments.value.filter(segment => segment.hasWarning).length
    const averageCharsPerLine = totalLines > 0 ? Math.round(characterCount.value / totalLines) : 0
    
    return {
      totalLines,
      overLimitLines,
      withinLimitLines: totalLines - overLimitLines,
      averageCharsPerLine,
      totalChars: characterCount.value,
      maxCharsPerLine: maxCharsPerLine.value
    }
  })

  return {
    refreshTrigger,
    forceRefresh,
    reactiveCurrentLines,
    characterCount,
    hasContent,
    hasNewlines,
    segmentCount,
    estimatedDuration,
    previewSegments,
    overallStats
  }
}

// 分割操作相关的组合式函数
export function useSplitOperations() {
  const slidesStore = useSlidesStore()
  const manualSplitEnabled = ref(true)

  // 按现有换行分割
  const splitByLines = () => {
    // 这个功能主要是切换视觉模式，实际逻辑在编辑器中处理
    manualSplitEnabled.value = true
  }

  // 按句号分割
  const splitBySentences = () => {
    const currentSlide = slidesStore.currentSlide
    if (!currentSlide?.remark) return

    const text = currentSlide.remark.replace(/<[^>]*>/g, '')
    const sentences = text.split(/[。！？]/).filter((s: string) => s.trim())
    
    if (sentences.length > 1) {
      const newContent = sentences.map((s: string) => s.trim()).filter((s: string) => s).join('\n')
      slidesStore.updateSlide({ remark: newContent })
    }
  }

  // 合并所有行
  const mergeLines = () => {
    const currentSlide = slidesStore.currentSlide
    if (!currentSlide?.remark) return

    const text = currentSlide.remark.replace(/<[^>]*>/g, '')
    const merged = text.replace(/\n+/g, ' ').trim()
    
    slidesStore.updateSlide({ remark: merged })
  }

  return {
    manualSplitEnabled,
    splitByLines,
    splitBySentences,
    mergeLines
  }
}

// 音频预览相关的组合式函数
export function useAudioPreview() {
  const previewAudio = async (text: string) => {
    if (!text.trim()) return

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
      const response = await fetch(`${API_BASE_URL}/api/tts/preview`, {
        method: 'POST',
        headers: getAuthJsonHeaders(),
        body: JSON.stringify({
          text: text.replace(/<[^>]*>/g, ''),
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
    catch {
      // 静默处理错误
    }
  }

  return {
    previewAudio
  }
}