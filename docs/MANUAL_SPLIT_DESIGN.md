# PPT转视频字幕手动分割功能设计文档

**生成时间**: 2025年9月22日  
**文档版本**: v1.0  
**功能目标**: 实现灵活的字幕手动分割机制，支持用户自定义分割策略

---

## 📋 需求分析

### 当前痛点
1. **自动分割不准确**: AI分割无法完全理解用户意图
2. **缺乏用户控制**: 用户无法手动调整分割位置
3. **配置不灵活**: 分割策略无法根据具体需求调整
4. **时间戳对齐问题**: 分割后的字幕时间戳分配不合理

### 用户期望
- 能够手动控制字幕分割位置
- 支持配置文件控制分割策略
- 保持字幕与音频的准确同步
- 兼容现有的自动分割功能

---

## 🎯 方案设计

### 智能内容分割方案
**核心思路**: 在同一页PPT的讲话稿中通过分隔符或换行分割内容，生成独立音频片段，累积时长形成完整视频

#### 分割流程设计
```
PPT页面 → 分割讲话稿 → 独立配音 → 累积时长 → 完整视频
   ↓           ↓           ↓           ↓           ↓
"内容1，    ["内容1",    [音频1,     [0-3s,      [完整视频:
内容2，      "内容2",     音频2,      3-6s,       0-9s]
内容3"       "内容3"]     音频3]      6-9s]
```

#### 技术实现
```typescript
// 前端实现：简单换行分割
interface SlideContentSegment {
  slide_id: string
  slide_number: number
  segment_index: number      // 分割序号
  content: string           // 分割后的内容
  estimated_duration: number
  is_manual_split: boolean
}

// 换行分割解析（唯一方式）
function parseSlideContent(slideId: string, content: string): SlideContentSegment[] {
  const segments: SlideContentSegment[] = []
  
  // 按换行分割内容
  const splitParts = content.split('\n')
    .map(part => part.trim())
    .filter(part => part.length > 0)
  
  splitParts.forEach((part, index) => {
    segments.push({
      slide_id: slideId,
      slide_number: parseInt(slideId),
      segment_index: index + 1,
      content: part,
      estimated_duration: estimateDuration(part),
      is_manual_split: true
    })
  })
  
  return segments
}

// 示例使用
const slideContent = `内容1，
内容2，  
内容3`

const segments = parseSlideContent('1', slideContent)
// 结果：
// [
//   { segment_index: 1, content: "内容1，", estimated_duration: 2.1 },
//   { segment_index: 2, content: "内容2，", estimated_duration: 2.1 },
//   { segment_index: 3, content: "内容3", estimated_duration: 1.8 }
// ]
```

#### 配音和时长处理
```python
# 后端处理：分段配音和时长累积
async def process_content_split_slide(slide_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理内容分割的幻灯片"""
    slide_number = slide_data["slide_number"]
    segments = slide_data.get("segments", [])
    
    audio_segments = []
    cumulative_time = 0.0
    
    for segment in segments:
        # 为每个内容片段独立生成音频
        audio_result = await generate_tts_audio(
            text=segment["content"],
            voice_config=get_voice_config(),
            output_file=f"slide_{slide_number}_seg_{segment['segment_index']}.wav"
        )
        
        # 计算累积时间
        segment_audio_info = {
            "segment_index": segment["segment_index"],
            "content": segment["content"],
            "audio_file": audio_result["audio_file"],
            "duration": audio_result["duration"],
            "start_time": cumulative_time,
            "end_time": cumulative_time + audio_result["duration"]
        }
        
        audio_segments.append(segment_audio_info)
        cumulative_time += audio_result["duration"]
    
    # 合并音频片段（可选）
    combined_audio_file = None
    if len(audio_segments) > 1:
        combined_audio_file = await merge_audio_segments(
            [seg["audio_file"] for seg in audio_segments],
            output_file=f"slide_{slide_number}_combined.wav"
        )
    
    return {
        "slide_number": slide_number,
        "segments": audio_segments,
        "total_duration": cumulative_time,
        "combined_audio_file": combined_audio_file,
        "is_content_split": True,
        "segment_count": len(audio_segments)
    }
```

#### 视频时长计算
```python
# 视频生成：基于累积时长
def calculate_video_duration_for_split_slide(slide_audio_data: Dict[str, Any]) -> float:
    """计算分割后幻灯片的视频显示时长"""
    if slide_audio_data.get("is_content_split", False):
        # 内容分割模式：使用累积时长
        return slide_audio_data["total_duration"]
    else:
        # 传统模式：使用单个音频时长
        return slide_audio_data.get("duration", 3.0)

# 字幕时间戳生成
def generate_subtitles_for_split_content(slide_audio_data: Dict[str, Any]) -> List[Dict]:
    """为分割内容生成字幕时间戳"""
    subtitles = []
    
    if not slide_audio_data.get("is_content_split", False):
        # 非分割内容，使用原有逻辑
        return generate_traditional_subtitles(slide_audio_data)
    
    # 分割内容：为每个片段生成精确时间戳
    for segment in slide_audio_data.get("segments", []):
        subtitle = {
            "index": len(subtitles) + 1,
            "start_time": segment["start_time"],
            "end_time": segment["end_time"], 
            "duration": segment["duration"],
            "text": segment["content"],
            "srt_start": seconds_to_srt_time(segment["start_time"]),
            "srt_end": seconds_to_srt_time(segment["end_time"]),
            "segment_index": segment["segment_index"],
            "is_split_segment": True
        }
        subtitles.append(subtitle)
    
    return subtitles
```

#### 优势分析
- ✅ **前端简洁**: 不需要复制PPT页面，保持原有编辑体验
- ✅ **逻辑直观**: 一页PPT对应一个完整的时间段
- ✅ **时间精确**: 基于实际音频时长累积，无估算误差
- ✅ **字幕同步**: 每个内容片段都有精确的时间戳
- ✅ **灵活分割**: 支持多种分割标记方式
- ✅ **向后兼容**: 不影响现有PPT编辑和处理流程

---

## 🛠️ 配置系统设计

### 配置文件结构
```json
{
  "manual_split_config": {
    "description": "手动字幕分割功能配置",
    "version": "2.0.0",
    "enabled": true,
    
    "split_strategy": {
      "method": "newline_split",
      "fallback_to_auto": true
    },
    
    "newline_split": {
      "enabled": true,
      "audio_processing": {
        "strategy": "separate_generation",
        "merge_segments": false,
        "normalize_volume": true,
        "add_segment_gap": 0.1
      },
      "timestamp_calculation": {
        "method": "cumulative",
        "precision": "millisecond",
        "adjust_for_readability": true
      }
    },
    
    "ui_integration": {
      "show_split_preview": true,
      "real_time_duration_calculation": true,
      "visual_split_markers": true,
      "keyboard_shortcuts": {
        "toggle_split_mode": "Ctrl+Shift+S",
        "preview_split": "Ctrl+P",
        "apply_split": "Ctrl+Enter"
      }
    },
    
    "quality_control": {
      "min_segment_length": 5,              // 最小分割片段字符数
      "max_segments_per_slide": 8,          // 每页最大分割数
      "min_segment_duration": 1.0,          // 最小片段时长（秒）
      "max_segment_duration": 10.0,         // 最大片段时长（秒）
      "validate_split_points": true,        // 验证分割位置合理性
      "auto_optimize_timing": true          // 自动优化时间分配
    }
  }
}
```

### PPTist集成的用户界面设计

#### 换行分割编辑方式（唯一方案）

**核心理念：简单直观的换行编辑**
```typescript
// 用户只需在讲话稿中通过换行进行分割
const speechContent = `大家好，我是讲师
今天来给大家讲解PPT制作技巧
首先我们来看第一个要点`

// 优势：
// ✅ 操作直观 - 用户最熟悉的编辑方式
// ✅ 实时预览 - 输入时即可看到分割效果
// ✅ 快速编辑 - 无需学习额外操作
// ✅ 兼容性好 - 支持复制粘贴、撤销重做
// ✅ 键盘友好 - 纯键盘操作效率最高
```

#### PPTist集成设计

**在现有的讲话稿编辑器中添加换行分割功能**

```vue
<!-- PPTist讲话稿编辑器-换行分割版 -->
<template>
  <div class="remark-editor-enhanced">
    <!-- 讲话稿编辑区头部 -->
    <div class="editor-header">
      <span class="editor-title">页面备注（讲话稿）</span>
      
      <!-- 分割模式切换 -->
      <div class="split-mode-toggle">
        <button 
          @click="toggleSplitMode" 
          :class="['split-btn', { active: splitModeEnabled }]"
          title="启用换行分割模式"
        >
          <svg class="icon">🎯</svg>
          {{ splitModeEnabled ? '分割模式' : '普通模式' }}
        </button>
      </div>
    </div>
    
    <!-- 文本编辑区 -->
    <div class="editor-container">
      <textarea
        ref="remarkTextarea"
        v-model="remarkContent"
        @input="onRemarkInput"
        @keydown="handleKeyDown"
        :class="['remark-textarea', { 'split-mode-active': splitModeEnabled }]"
        placeholder="输入讲话稿内容...&#10;&#10;💡 提示：启用分割模式后，每行内容将作为独立片段配音"
        spellcheck="false"
      ></textarea>
      
      <!-- 分割预览面板 -->
      <div v-if="splitModeEnabled && previewSegments.length > 0" class="split-preview-panel">
        <div class="preview-header">
          <h4>📋 分割预览</h4>
          <div class="preview-stats">
            <span class="segment-count">{{ previewSegments.length }} 段</span>
            <span class="total-duration">{{ totalEstimatedDuration.toFixed(1) }}s</span>
          </div>
        </div>
        
        <div class="preview-segments">
          <div 
            v-for="(segment, index) in previewSegments"
            :key="index"
            :class="['preview-segment', { 
              'segment-warning': segment.hasWarning
            }]"
          >
            <div class="segment-header">
              <span class="segment-index">{{ index + 1 }}</span>
              <span class="segment-duration">{{ segment.duration.toFixed(1) }}s</span>
              <div class="segment-quality">
                <div class="quality-indicator" :class="getQualityClass(segment.quality)"></div>
                <span class="quality-score">{{ segment.quality }}%</span>
              </div>
            </div>
            
            <div class="segment-content">{{ segment.content }}</div>
            
            <div v-if="segment.warnings.length > 0" class="segment-warnings">
              <div v-for="warning in segment.warnings" :key="warning" class="warning-item">
                ⚠️ {{ warning }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 预览操作按钮 -->
        <div class="preview-actions">
          <button @click="applySegments" class="btn btn-primary">
            ✅ 应用分割
          </button>
        </div>
      </div>
    </div>
    
    <!-- 状态栏 -->
    <div class="editor-status-bar">
      <div class="status-left">
        <span class="char-count">{{ remarkContent.length }} 字符</span>
        <span v-if="splitModeEnabled" class="split-status">
          换行分割模式
        </span>
      </div>
      
      <div class="status-right">
        <span v-if="!splitModeEnabled" class="estimated-duration">
          预计时长: {{ estimatedDuration.toFixed(1) }}s
        </span>
        <span v-else class="split-duration">
          分割后时长: {{ totalEstimatedDuration.toFixed(1) }}s
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'

// 简化的数据结构
interface SplitSegment {
  content: string
  duration: number
  quality: number
  warnings: string[]
  hasWarning: boolean
}

// 响应式数据
const remarkContent = ref('')
const splitModeEnabled = ref(false)
const previewSegments = ref<SplitSegment[]>([])
const remarkTextarea = ref<HTMLTextAreaElement>()

// 计算属性
const estimatedDuration = computed(() => estimateTextDuration(remarkContent.value))
const totalEstimatedDuration = computed(() => 
  previewSegments.value.reduce((total, segment) => total + segment.duration, 0)
)

// 核心方法
function toggleSplitMode() {
  splitModeEnabled.value = !splitModeEnabled.value
  if (splitModeEnabled.value) {
    generatePreviewSegments()
  } else {
    previewSegments.value = []
  }
}

function onRemarkInput() {
  if (splitModeEnabled.value) {
    clearTimeout(previewUpdateTimer.value)
    previewUpdateTimer.value = setTimeout(generatePreviewSegments, 300)
  }
  emit('remark-change', remarkContent.value)
}

function handleKeyDown(event: KeyboardEvent) {
  // 快捷键：Ctrl+Shift+S 切换分割模式
  if (event.ctrlKey && event.shiftKey && event.key === 'S') {
    event.preventDefault()
    toggleSplitMode()
  }
}

function generatePreviewSegments() {
  if (!remarkContent.value.trim()) {
    previewSegments.value = []
    return
  }
  
  // 按换行分割（核心逻辑）
  const lines = remarkContent.value.split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
  
  previewSegments.value = lines.map(line => ({
    content: line,
    duration: estimateTextDuration(line),
    quality: calculateSegmentQuality(line),
    warnings: validateSegment(line),
    hasWarning: validateSegment(line).length > 0
  }))
}

function applySegments() {
  const splitData = {
    slide_id: props.slideId,
    original_content: remarkContent.value,
    segments: previewSegments.value.map((segment, index) => ({
      index: index + 1,
      content: segment.content,
      estimated_duration: segment.duration,
      quality_score: segment.quality
    })),
    split_method: 'newline',
    total_estimated_duration: totalEstimatedDuration.value,
    is_manual_split: true
  }
  
  emit('apply-manual-split', splitData)
}

// 工具函数
function estimateTextDuration(text: string): number {
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  const otherChars = text.length - chineseChars
  return Math.max(1.0, (chineseChars * 0.5 + otherChars * 0.25))
}

function calculateSegmentQuality(content: string): number {
  let score = 100
  if (content.length < 5) score -= 30
  if (content.length > 200) score -= 20
  if (!/[。！？]/.test(content)) score -= 15
  return Math.max(0, score)
}

function validateSegment(content: string): string[] {
  const warnings = []
  if (content.length < 5) warnings.push('内容过短')
  if (content.length > 200) warnings.push('内容过长')
  return warnings
}

// 定义事件和属性
const emit = defineEmits(['remark-change', 'apply-manual-split'])
const props = defineProps(['slideId', 'initialContent'])

// 初始化
if (props.initialContent) {
  remarkContent.value = props.initialContent
}
</script>
```
    
    <!-- 增强的文本编辑区 -->
    <div class="editor-container">
      <textarea
        ref="remarkTextarea"
        v-model="remarkContent"
        @input="onRemarkInput"
        @keydown="handleKeyDown"
        @selectionchange="onSelectionChange"
        :class="['remark-textarea', { 'split-mode-active': splitModeEnabled }]"
        placeholder="输入讲话稿内容...&#10;&#10;💡 提示：启用分割模式后，可直接通过换行来分割内容"
        spellcheck="false"
      ></textarea>
      
      <!-- 分割预览面板（分割模式下显示） -->
      <div v-if="splitModeEnabled && previewSegments.length > 0" class="split-preview-panel">
        <div class="preview-header">
          <h4>📋 分割预览</h4>
          <div class="preview-stats">
            <span class="segment-count">{{ previewSegments.length }} 段</span>
            <span class="total-duration">{{ totalEstimatedDuration.toFixed(1) }}s</span>
          </div>
        </div>
        
        <div class="preview-segments">
          <div 
            v-for="(segment, index) in previewSegments"
            :key="index"
            :class="['preview-segment', { 
              'segment-warning': segment.hasWarning,
              'segment-selected': selectedSegmentIndex === index 
            }]"
            @click="selectSegment(index)"
          >
            <div class="segment-header">
              <span class="segment-index">{{ index + 1 }}</span>
              <span class="segment-duration">{{ segment.duration.toFixed(1) }}s</span>
              <div class="segment-quality">
                <div class="quality-indicator" :class="getQualityClass(segment.quality)"></div>
                <span class="quality-score">{{ segment.quality }}%</span>
              </div>
            </div>
            
            <div class="segment-content">{{ segment.content }}</div>
            
            <div v-if="segment.warnings.length > 0" class="segment-warnings">
              <div v-for="warning in segment.warnings" :key="warning" class="warning-item">
                ⚠️ {{ warning }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 预览操作按钮 -->
        <div class="preview-actions">
          <button @click="optimizeSegments" class="btn btn-secondary">
            🔧 优化分割
          </button>
          <button @click="applySegments" class="btn btn-primary">
            ✅ 应用分割
          </button>
        </div>
      </div>
    </div>
    
    <!-- 状态栏 -->
    <div class="editor-status-bar">
      <div class="status-left">
        <span class="char-count">{{ remarkContent.length }} 字符</span>
        <span v-if="splitModeEnabled" class="split-status">
          分割模式: {{ splitMethodLabels[currentSplitMethod] }}
        </span>
      </div>
      
      <div class="status-right">
        <span v-if="!splitModeEnabled" class="estimated-duration">
          预计时长: {{ estimatedDuration.toFixed(1) }}s
        </span>
        <span v-else class="split-duration">
          分割后时长: {{ totalEstimatedDuration.toFixed(1) }}s
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

// 数据结构
interface SplitSegment {
  content: string
  duration: number
  quality: number
  warnings: string[]
  hasWarning: boolean
  startPosition: number
  endPosition: number
}

// 响应式数据
const remarkContent = ref('')
const splitModeEnabled = ref(false)
const currentSplitMethod = ref('newline')
const previewSegments = ref<SplitSegment[]>([])
const selectedSegmentIndex = ref(-1)
const remarkTextarea = ref<HTMLTextAreaElement>()

// 分割方式标签
const splitMethodLabels = {
  'newline': '换行分割',
  'comma_newline': '逗号+换行',
  'separator': '自定义分隔符'
}

// 计算属性
const estimatedDuration = computed(() => {
  return estimateTextDuration(remarkContent.value)
})

const totalEstimatedDuration = computed(() => {
  return previewSegments.value.reduce((total, segment) => total + segment.duration, 0)
})

// 方法实现
function toggleSplitMode() {
  splitModeEnabled.value = !splitModeEnabled.value
  
  if (splitModeEnabled.value) {
    // 进入分割模式
    generatePreviewSegments()
    nextTick(() => {
      addSplitModeListeners()
    })
  } else {
    // 退出分割模式
    previewSegments.value = []
    removeSplitModeListeners()
  }
}

function onRemarkInput() {
  // 实时更新预览（防抖处理）
  if (splitModeEnabled.value) {
    clearTimeout(previewUpdateTimer.value)
    previewUpdateTimer.value = setTimeout(() => {
      generatePreviewSegments()
    }, 300)
  }
  
  // 触发内容变更事件（通知父组件）
  emit('remark-change', remarkContent.value)
}

function handleKeyDown(event: KeyboardEvent) {
  // 快捷键处理
  if (splitModeEnabled.value) {
    // Ctrl+Enter: 在光标处插入换行
    if (event.ctrlKey && event.key === 'Enter') {
      event.preventDefault()
      insertAtCursor('\n')
    }
    
    // Ctrl+D: 智能分割建议
    if (event.ctrlKey && event.key === 'd') {
      event.preventDefault()
      autoSplitSuggestion()
    }
  }
}

function insertAtCursor(text: string) {
  const textarea = remarkTextarea.value
  if (!textarea) return
  
  const cursorStart = textarea.selectionStart
  const cursorEnd = textarea.selectionEnd
  
  const beforeCursor = remarkContent.value.substring(0, cursorStart)
  const afterCursor = remarkContent.value.substring(cursorEnd)
  
  remarkContent.value = beforeCursor + text + afterCursor
  
  // 设置新的光标位置
  nextTick(() => {
    textarea.selectionStart = textarea.selectionEnd = cursorStart + text.length
    textarea.focus()
  })
}

function generatePreviewSegments() {
  if (!remarkContent.value.trim()) {
    previewSegments.value = []
    return
  }
  
  const segments = parseContentByMethod(remarkContent.value, currentSplitMethod.value)
  
  previewSegments.value = segments.map((segment, index) => {
    const duration = estimateTextDuration(segment.content)
    const quality = calculateSegmentQuality(segment.content)
    const warnings = validateSegment(segment.content)
    
    return {
      content: segment.content,
      duration,
      quality,
      warnings,
      hasWarning: warnings.length > 0,
      startPosition: segment.startPosition,
      endPosition: segment.endPosition
    }
  })
}

function parseContentByMethod(content: string, method: string): any[] {
  switch (method) {
    case 'newline':
      return content.split('\n')
        .map((part, index, array) => ({
          content: part.trim(),
          startPosition: array.slice(0, index).join('\n').length + (index > 0 ? 1 : 0),
          endPosition: array.slice(0, index + 1).join('\n').length
        }))
        .filter(part => part.content)
    
    case 'comma_newline':
      return content.split(/，\s*\n/)
        .map((part, index) => ({
          content: part.trim(),
          startPosition: 0, // 简化处理
          endPosition: 0
        }))
        .filter(part => part.content)
    
    case 'separator':
      return content.split('|||')
        .map((part, index) => ({
          content: part.trim(),
          startPosition: 0,
          endPosition: 0
        }))
        .filter(part => part.content)
    
    default:
      return [{ content, startPosition: 0, endPosition: content.length }]
  }
}

function estimateTextDuration(text: string): number {
  // 中文字符按2字符/秒，英文按4字符/秒估算
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  const otherChars = text.length - chineseChars
  
  return Math.max(1.0, (chineseChars * 0.5 + otherChars * 0.25))
}

function calculateSegmentQuality(content: string): number {
  let score = 100
  
  if (content.length < 5) score -= 30
  if (content.length > 200) score -= 20
  if (!/[。！？]/.test(content)) score -= 15
  
  return Math.max(0, score)
}

function validateSegment(content: string): string[] {
  const warnings = []
  
  if (content.length < 5) warnings.push('内容过短')
  if (content.length > 200) warnings.push('内容过长')
  if (!content.trim()) warnings.push('内容为空')
  
  return warnings
}

function autoSplitSuggestion() {
  // AI智能分割建议（简化版）
  const content = remarkContent.value
  
  if (!content.includes('\n') && content.length > 100) {
    // 建议在句号或逗号后换行
    const suggested = content.replace(/([。！？，])\s*/g, '$1\n')
    remarkContent.value = suggested
    generatePreviewSegments()
  }
}

function applySegments() {
  // 应用分割结果，触发后端处理
  const splitData = {
    slide_id: props.slideId,
    original_content: remarkContent.value,
    segments: previewSegments.value.map((segment, index) => ({
      index: index + 1,
      content: segment.content,
      estimated_duration: segment.duration,
      quality_score: segment.quality
    })),
    split_method: currentSplitMethod.value,
    total_estimated_duration: totalEstimatedDuration.value,
    is_manual_split: true
  }
  
  emit('apply-manual-split', splitData)
}

// 监听器
watch(currentSplitMethod, () => {
  if (splitModeEnabled.value) {
    generatePreviewSegments()
  }
})

// 定义事件
const emit = defineEmits(['remark-change', 'apply-manual-split'])
const props = defineProps(['slideId', 'initialContent'])

// 初始化
if (props.initialContent) {
  remarkContent.value = props.initialContent
}
</script>

<style scoped>
.remark-editor-enhanced {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e5e9;
}

.split-mode-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
}

.split-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  background: #fff;
  color: #24292f;
  cursor: pointer;
  transition: all 0.2s;
}

.split-btn.active {
  background: #0969da;
  color: #fff;
  border-color: #0969da;
}

.split-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: #f6f8fa;
  border-radius: 6px;
}

.quick-insert-tools {
  display: flex;
  gap: 8px;
}

.tool-btn {
  padding: 4px 8px;
  border: 1px solid #d0d7de;
  border-radius: 4px;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #f3f4f6;
}

.editor-container {
  display: flex;
  min-height: 200px;
}

.remark-textarea {
  flex: 1;
  padding: 16px;
  border: none;
  outline: none;
  resize: vertical;
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
  font-size: 14px;
  line-height: 1.6;
  min-height: 200px;
}

.remark-textarea.split-mode-active {
  border-right: 1px solid #e1e5e9;
  flex: 0 0 60%;
}

.split-preview-panel {
  flex: 0 0 40%;
  padding: 16px;
  background: #f8f9fa;
  border-left: 1px solid #e1e5e9;
  overflow-y: auto;
  max-height: 400px;
}

.preview-segments {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-segment {
  padding: 12px;
  background: #fff;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.preview-segment:hover {
  border-color: #0969da;
}

.preview-segment.segment-selected {
  border-color: #0969da;
  box-shadow: 0 0 0 2px rgba(9, 105, 218, 0.1);
}

.segment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.segment-content {
  font-size: 13px;
  color: #656d76;
  line-height: 1.4;
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.editor-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f6f8fa;
  border-top: 1px solid #e1e5e9;
  font-size: 12px;
  color: #656d76;
}
</style>
```

#### 用户操作流程

**换行分割流程（唯一方式）**：
```
1. 用户点击"分割模式"按钮
2. 在讲话稿中需要分割的地方按Enter换行
3. 实时看到右侧分割预览
4. 调整分割位置（继续换行编辑）
5. 点击"应用分割"完成

总耗时：< 30秒
学习成本：极低（用户熟悉的操作）
操作准确性：高（直观可见）
```

#### 最佳用户体验设计

**核心编辑方式：换行分割**
- 用户直接通过换行完成分割
- 提供实时预览和质量评分
- 支持撤销重做等标准编辑操作
- 快捷键支持（Ctrl+Shift+S切换模式）

**智能优化**
- 自动检测内容长度和复杂度
- 质量评分和警告提示
- 预计时长实时计算

---

## 🔄 工作流集成

### PPTist前端集成

```typescript
// PPTist换行分割功能集成
class PPTistNewlineSplitManager {
  private config: ManualSplitConfig
  
  constructor(config: ManualSplitConfig) {
    this.config = config
  }
  
  // 换行分割处理（唯一方式）
  async executeNewlineSplit(slideId: string, content: string): Promise<SplitResult> {
    const segments = this.parseNewlineContent(content)
    
    return {
      slide_id: slideId,
      original_content: content,
      segments: segments,
      split_method: 'newline',
      is_manual_split: true
    }
  }
  
  // 解析换行分割内容
  parseNewlineContent(content: string): ContentSegment[] {
    // 按换行分割（核心逻辑）
    const lines = content.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
    
    return lines.map((line, index) => ({
      index: index + 1,
      content: line,
      estimated_duration: this.estimateDuration(line)
    }))
  }
}
```

### 后端处理适配
```python
# 修改现有的字幕生成器以支持换行分割
class EnhancedSubtitleGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.manual_split_config = config.get("manual_split_config", {})
        self.manual_split_enabled = self.manual_split_config.get("enabled", False)
    
    async def generate_subtitles_with_newline_split(
        self, 
        scripts_data: Dict[str, Any], 
        audio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成支持换行分割的字幕"""
        
        if not self.manual_split_enabled:
            return await self.generate_traditional_subtitles(scripts_data, audio_data)
        
        # 检测是否包含换行分割的脚本
        has_newline_splits = any(
            script.get("is_manual_split", False) and script.get("split_method") == "newline"
            for script in scripts_data.get("scripts", [])
        )
        
        if has_newline_splits:
            return await self._process_newline_split_scripts(scripts_data, audio_data)
        else:
            return await self.generate_traditional_subtitles(scripts_data, audio_data)
    
    async def _process_newline_split_scripts(
        self, 
        scripts_data: Dict[str, Any], 
        audio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理包含换行分割的脚本"""
        
        all_subtitles = []
        subtitle_index = 1
        
        for script in scripts_data.get("scripts", []):
            if script.get("is_manual_split", False):
                # 处理换行分割的片段
                subtitle_info = await self._generate_newline_split_subtitle(
                    script, audio_data, subtitle_index
                )
            else:
                # 处理常规片段
                subtitle_info = await self._generate_regular_subtitle(
                    script, audio_data, subtitle_index
                )
            
            all_subtitles.extend(subtitle_info["subtitles"])
            subtitle_index += len(subtitle_info["subtitles"])
        
        return {
            "subtitles": all_subtitles,
            "newline_split_applied": True,
            "generation_timestamp": datetime.now().isoformat()
        }
```

---

## 📊 实施计划

### 阶段一：核心功能开发（1-2周）
1. **配置系统**
   - 创建 `manual_split_config.json` 配置文件
   - 在 `app_config.json` 中添加总开关
   - 实现配置加载和验证逻辑

2. **PPTist前端集成**
   - 在讲话稿编辑器中添加分割模式切换
   - 实现换行分割的实时预览
   - 添加分割质量评分和警告提示

3. **后端处理逻辑**
   - 修改字幕生成器支持换行分割
   - 实现分割脚本的音频处理
   - 添加累积时间戳计算逻辑

### 阶段二：用户体验优化（1-2周）
1. **编辑体验优化**
   - 实现快捷键支持（Ctrl+Shift+S切换模式）
   - 添加智能分割建议功能
   - 优化分割预览界面

2. **质量控制**
   - 添加分割合理性验证
   - 实现自动优化建议
   - 开发撤销和重做功能

3. **性能优化**
   - 分割操作性能优化
   - 音频处理效率提升
   - 内存使用优化

### 阶段三：测试和文档（1周）
1. **功能测试**
   - 单元测试覆盖
   - 集成测试验证
   - 用户体验测试

2. **文档完善**
   - 用户使用指南
   - 开发者文档
   - 配置说明文档

---

## 🎯 换行分割方案总结

### 核心优势

#### 1. 用户体验极佳
```
用户操作流程：
1. 在讲话稿中按需求换行  →  内容1\n内容2\n内容3
2. 系统自动识别分割点  →  检测到3个片段
3. 实时预览分割效果    →  显示时长和质量评分
4. 一键应用分割结果    →  生成独立音频片段

总耗时：< 30秒，学习成本：零
```

#### 2. 技术实现简单
```python
# 处理流程极其简洁
slide_content = "内容1\n内容2\n内容3"
segments = slide_content.split('\n')  # ["内容1", "内容2", "内容3"]

audio_files = []
cumulative_time = 0.0

for segment in segments:
    audio = generate_tts(segment)           # 独立配音
    audio_files.append({
        "content": segment,
        "file": audio.file,
        "duration": audio.duration,
        "start_time": cumulative_time,
        "end_time": cumulative_time + audio.duration
    })
    cumulative_time += audio.duration

# 结果：精确的时间戳，完美的音频同步
```

#### 3. 完美解决痛点
- ✅ **前端简洁**: 无需复杂的分割方式选择
- ✅ **音频时长精确**: 基于实际TTS音频，无估算误差  
- ✅ **字幕时间戳准确**: 累积时长计算，毫秒级精度
- ✅ **用户控制简单**: 只需换行即可分割
- ✅ **向后兼容**: 不影响现有功能

### 实施建议

#### 第一阶段（MVP）：基础换行分割
```json
{
  "manual_split_config": {
    "enabled": true,
    "split_strategy": {
      "method": "newline_split"
    },
    "newline_split": {
      "audio_processing": {
        "strategy": "separate_generation"
      }
    }
  }
}
```

#### 第二阶段：用户体验优化
- 添加快捷键支持
- 优化分割预览界面
- 质量评分和警告

#### 配置推荐（生产环境）
```json
{
  "manual_split_config": {
    "enabled": true,
    "split_strategy": {
      "method": "newline_split",
      "fallback_to_auto": true
    },
    "newline_split": {
      "enabled": true,
      "audio_processing": {
        "strategy": "separate_generation",
        "normalize_volume": true,
        "add_segment_gap": 0.1
      }
    },
    "quality_control": {
      "min_segment_length": 5,
      "max_segments_per_slide": 8,
      "min_segment_duration": 1.0,
      "validate_split_points": true
    }
  }
}
```

### 用户使用示例

**场景**: 用户想分割讲话稿 "are you ok，我的朋友们，今天来教大家安装cherry studio"

**操作步骤**:
1. 在讲话稿中按需要添加换行：
   ```
   are you ok，我的朋友们，
   今天来教大家安装cherry studio
   ```

2. 系统自动检测并预览：
   ```
   片段1: "are you ok，我的朋友们，" (预计2.8s)
   片段2: "今天来教大家安装cherry studio" (预计3.2s)
   总时长: 6.0s
   ```

3. 配音阶段生成：
   - `audio_seg1.wav` (2.8s) - "are you ok，我的朋友们，"
   - `audio_seg2.wav` (3.2s) - "今天来教大家安装cherry studio"

4. 视频时长：6.0s（累积音频时长）

5. 字幕时间戳：
   ```
   1
   00:00:00,000 --> 00:00:02,800
   are you ok，我的朋友们，
   
   2
   00:00:02,800 --> 00:00:06,000
   今天来教大家安装cherry studio
   ```

这个方案完美实现了你的想法：**在内容层面通过换行分割，音频独立生成，时长精确累积**！ 
          :key="mode.id"
          @click="setSplitMode(mode.id)"
          :class="['mode-btn', { active: currentMode === mode.id }]"
        >
          {{ mode.icon }} {{ mode.name }}
        </button>
      </div>
    </div>
    
    <!-- 内容编辑区 -->
    <div class="content-editor-section">
      <div class="editor-header">
        <label>讲话稿内容</label>
        <div class="editor-tools">
          <span class="char-counter">{{ slideContent.length }} 字符</span>
          <button @click="autoDetectSplit" class="btn-auto">🤖 智能检测</button>
        </div>
      </div>
      
      <textarea 
        v-model="slideContent" 
        @input="onContentChange"
        @keydown="handleKeyboardShortcuts"
        class="content-textarea"
        placeholder="输入讲话稿内容，支持换行分割..."
        rows="8"
      ></textarea>
      
      <!-- 分割提示 -->
      <div v-if="splitSuggestion" class="split-suggestion">
        <div class="suggestion-header">
          <span class="suggestion-icon">💡</span>
          <span>分割建议</span>
        </div>
        <p>{{ splitSuggestion.message }}</p>
        <button @click="applySuggestion" class="btn-suggestion">
          采用建议
        </button>
      </div>
    </div>
    
    <!-- 分割预览区 -->
    <div v-if="previewSegments.length > 0" class="split-preview-section">
      <div class="preview-header">
        <h4>分割预览</h4>
        <div class="preview-stats">
          <span>{{ previewSegments.length }} 个片段</span>
          <span>总时长: {{ totalDuration.toFixed(1) }}s</span>
        </div>
      </div>
      
      <div class="preview-segments">
        <div 
          v-for="(segment, index) in previewSegments" 
          :key="index"
          class="preview-segment"
          :class="{ 'segment-warning': segment.hasIssues }"
        >
          <div class="segment-header">
            <span class="segment-index">{{ index + 1 }}</span>
            <div class="segment-timing">
              <span class="segment-duration">{{ segment.duration.toFixed(1) }}s</span>
              <span class="segment-timerange">
                {{ formatTime(segment.startTime) }} - {{ formatTime(segment.endTime) }}
              </span>
            </div>
            <button @click="editSegment(index)" class="btn-edit">✏️</button>
          </div>
          
          <div class="segment-content">{{ segment.content }}</div>
          
          <!-- 质量指标 -->
          <div class="segment-quality">
            <div class="quality-bar">
              <div 
                class="quality-fill" 
                :style="{ width: segment.qualityScore + '%' }"
                :class="getQualityClass(segment.qualityScore)"
              ></div>
            </div>
            <span class="quality-text">质量: {{ segment.qualityScore }}%</span>
          </div>
          
          <!-- 警告信息 -->
          <div v-if="segment.warnings.length > 0" class="segment-warnings">
            <div v-for="warning in segment.warnings" :key="warning" class="warning-item">
              ⚠️ {{ warning }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <button 
        @click="previewSplit" 
        :disabled="!slideContent.trim()"
        class="btn btn-secondary"
      >
        👁️ 预览分割
      </button>
      
      <button 
        @click="applySplit" 
        :disabled="previewSegments.length === 0"
        class="btn btn-primary"
      >
        ✅ 应用分割
      </button>
      
      <button 
        @click="resetSplit" 
        class="btn btn-outline"
      >
        🔄 重置
      </button>
    </div>
    
    <!-- 高级设置 -->
    <div class="advanced-settings" v-if="showAdvancedSettings">
      <h4>高级设置</h4>
      <div class="settings-grid">
        <div class="setting-item">
          <label>最小片段时长</label>
          <input v-model.number="advancedConfig.minDuration" type="number" min="0.5" max="5" step="0.1">
          <span class="unit">秒</span>
        </div>
        
        <div class="setting-item">
          <label>片段间隔</label>
          <input v-model.number="advancedConfig.segmentGap" type="number" min="0" max="1" step="0.1">
          <span class="unit">秒</span>
        </div>
        
        <div class="setting-item">
          <label>音量标准化</label>
          <input v-model="advancedConfig.normalizeVolume" type="checkbox">
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// 数据结构
interface ContentSegment {
  index: number
  content: string
  duration: number
  startTime: number
  endTime: number
  qualityScore: number
  warnings: string[]
  hasIssues: boolean
}

interface SplitMode {
  id: string
  name: string
  icon: string
  description: string
}

// 响应式数据
const slideContent = ref('')
const currentMode = ref('newline')
const previewSegments = ref<ContentSegment[]>([])
const showAdvancedSettings = ref(false)

const splitModes: SplitMode[] = [
  { id: 'newline', name: '换行分割', icon: '⏎', description: '按换行符自动分割' },
  { id: 'comma_newline', name: '逗号换行', icon: '，⏎', description: '按逗号+换行分割' },
  { id: 'separator', name: '分隔符', icon: '|||', description: '按|||分隔符分割' },
  { id: 'smart', name: '智能分割', icon: '🤖', description: 'AI智能检测分割点' }
]

const advancedConfig = ref({
  minDuration: 1.0,
  segmentGap: 0.2,
  normalizeVolume: true
})

// 计算属性
const totalDuration = computed(() => {
  return previewSegments.value.reduce((total, segment) => total + segment.duration, 0)
})

const splitSuggestion = computed(() => {
  if (!slideContent.value.trim()) return null
  
  const content = slideContent.value
  const newlineCount = (content.match(/\n/g) || []).length
  const length = content.length
  
  if (newlineCount >= 2) {
    return {
      message: `检测到 ${newlineCount} 个换行符，建议使用换行分割模式`,
      suggestedMode: 'newline'
    }
  } else if (length > 100) {
    return {
      message: '内容较长，建议手动添加换行符或使用智能分割',
      suggestedMode: 'smart'
    }
  }
  
  return null
})

// 方法
function setSplitMode(modeId: string) {
  currentMode.value = modeId
  if (previewSegments.value.length > 0) {
    previewSplit()
  }
}

function onContentChange() {
  // 实时更新预览（防抖）
  clearTimeout(previewTimer.value)
  previewTimer.value = setTimeout(() => {
    if (previewSegments.value.length > 0) {
      previewSplit()
    }
  }, 500)
}

function autoDetectSplit() {
  const content = slideContent.value
  const detectedMode = detectOptimalSplitMethod(content)
  
  if (detectedMode !== 'no_split_needed') {
    setSplitMode(detectedMode.replace('_recommended', ''))
    previewSplit()
  }
}

function previewSplit() {
  const segments = parseContentBySplitMode(slideContent.value, currentMode.value)
  previewSegments.value = segments.map((segment, index) => {
    const duration = estimateDuration(segment.content)
    const startTime = index === 0 ? 0 : previewSegments.value[index - 1]?.endTime || 0
    
    return {
      index: index + 1,
      content: segment.content,
      duration,
      startTime,
      endTime: startTime + duration,
      qualityScore: calculateQualityScore(segment.content),
      warnings: validateSegment(segment.content),
      hasIssues: validateSegment(segment.content).length > 0
    }
  })
}

function applySplit() {
  // 应用分割结果
  const splitData = {
    slide_id: currentSlideId.value,
    segments: previewSegments.value.map(segment => ({
      content: segment.content,
      duration: segment.duration,
      start_time: segment.startTime,
      end_time: segment.endTime
    })),
    split_method: currentMode.value,
    total_duration: totalDuration.value,
    is_manual_split: true
  }
  
  // 发送到后端处理
  emit('apply-split', splitData)
}

function resetSplit() {
  previewSegments.value = []
  slideContent.value = ''
  currentMode.value = 'newline'
}

// 工具函数
function estimateDuration(text: string): number {
  // 基于字符数估算时长（中文约2字符/秒，英文约4字符/秒）
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  const otherChars = text.length - chineseChars
  
  return Math.max(1.0, (chineseChars * 0.5 + otherChars * 0.25))
}

function calculateQualityScore(content: string): number {
  let score = 100
  
  // 长度检查
  if (content.length < 5) score -= 30
  if (content.length > 200) score -= 20
  
  // 标点检查
  if (!/[。！？]/.test(content)) score -= 15
  
  // 完整性检查
  if (content.startsWith('，') || content.startsWith('。')) score -= 20
  
  return Math.max(0, score)
}

function validateSegment(content: string): string[] {
  const warnings = []
  
  if (content.length < 5) {
    warnings.push('片段过短，可能影响配音效果')
  }
  
  if (content.length > 200) {
    warnings.push('片段过长，建议进一步分割')
  }
  
  if (!content.trim()) {
    warnings.push('片段为空')
  }
  
  return warnings
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(1)
  return `${mins}:${secs.padStart(4, '0')}`
}
</script>
```

---

## 🔄 工作流集成

### PPTist前端集成
```typescript
// PPTist换行分割功能集成
class PPTistNewlineSplitManager {
  private config: ManualSplitConfig
  
  constructor(config: ManualSplitConfig) {
    this.config = config
  }
  
  // 换行分割处理（唯一方式）
  async executeNewlineSplit(slideId: string, content: string): Promise<SplitResult> {
    const segments = this.parseNewlineContent(content)
    
    return {
      slide_id: slideId,
      original_content: content,
      segments: segments,
      split_method: 'newline',
      is_manual_split: true
    }
  }
  
  // 解析换行分割内容
  parseNewlineContent(content: string): ContentSegment[] {
    // 按换行分割（核心逻辑）
    const lines = content.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
    
    return lines.map((line, index) => ({
      index: index + 1,
      content: line,
      estimated_duration: this.estimateDuration(line)
    }))
  }
}
```

### 后端处理适配
```python
# 修改现有的字幕生成器以支持手动分割
class EnhancedSubtitleGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.manual_split_config = config.get("manual_split_config", {})
        self.manual_split_enabled = self.manual_split_config.get("enabled", False)
    
    async def generate_subtitles_with_manual_split(
        self, 
        scripts_data: Dict[str, Any], 
        audio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成支持手动分割的字幕"""
        
        if not self.manual_split_enabled:
            # 回退到原有处理方式
            return await self.generate_traditional_subtitles(scripts_data, audio_data)
        
        # 检测是否包含手动分割的脚本
        has_manual_splits = any(
            script.get("is_manual_split", False) 
            for script in scripts_data.get("scripts", [])
        )
        
        if has_manual_splits:
            return await self._process_manual_split_scripts(scripts_data, audio_data)
        else:
            return await self.generate_traditional_subtitles(scripts_data, audio_data)
    
    async def _process_manual_split_scripts(
        self, 
        scripts_data: Dict[str, Any], 
        audio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理包含手动分割的脚本"""
        
        all_subtitles = []
        subtitle_index = 1
        
        for script in scripts_data.get("scripts", []):
            if script.get("is_manual_split", False):
                # 处理手动分割的片段
                subtitle_info = await self._generate_manual_split_subtitle(
                    script, audio_data, subtitle_index
                )
            else:
                # 处理常规片段
                subtitle_info = await self._generate_regular_subtitle(
                    script, audio_data, subtitle_index
                )
            
            all_subtitles.extend(subtitle_info["subtitles"])
            subtitle_index += len(subtitle_info["subtitles"])
        
        return {
            "subtitles": all_subtitles,
            "manual_split_applied": True,
            "generation_timestamp": datetime.now().isoformat()
        }
```

---

## 📊 实施计划

### 阶段一：核心功能开发（1-2周）
1. **配置系统**
   - 创建 `manual_split_config.json` 配置文件
   - 在 `app_config.json` 中添加总开关
   - 实现配置加载和验证逻辑

2. **PPTist前端集成**
   - 在讲话稿编辑器中添加分割模式切换
   - 实现换行分割的实时预览
   - 添加分割质量评分和警告提示

3. **后端处理逻辑**
   - 修改字幕生成器支持内容分割
   - 实现分割脚本的音频处理
   - 添加累积时间戳计算逻辑

### 阶段二：高级功能实现（1-2周）
1. **编辑体验优化**
   - 实现快捷键支持（Ctrl+Enter插入换行）
   - 添加智能分割建议功能
   - 优化分割预览界面

2. **多种分割方式**
   - 支持逗号+换行分割
   - 添加自定义分隔符支持
   - 实现分割方式自动检测

3. **质量控制**
   - 添加分割合理性验证
   - 实现自动优化建议
   - 开发撤销和重做功能

### 阶段三：测试和优化（1周）
1. **功能测试**
   - 单元测试覆盖
   - 集成测试验证
   - 用户体验测试

2. **性能优化**
   - 分割操作性能优化
   - 音频处理效率提升
   - 内存使用优化

3. **文档完善**
   - 用户使用指南
   - 开发者文档
   - 配置说明文档

---

## 🎯 换行分割方案总结

### 核心优势

#### 1. 用户体验极佳
```
用户操作流程：
1. 在讲话稿中按需求换行  →  内容1\n内容2\n内容3
2. 系统自动识别分割点  →  检测到3个片段
3. 实时预览分割效果    →  显示时长和质量评分
4. 一键应用分割结果    →  生成独立音频片段

总耗时：< 30秒，学习成本：零
```

#### 2. 技术实现简单
```python
# 处理流程简单明了
slide_content = "内容1\n内容2\n内容3"
segments = parse_by_newline(slide_content)  # ["内容1", "内容2", "内容3"]

audio_files = []
cumulative_time = 0.0

for segment in segments:
    audio = generate_tts(segment)           # 独立配音
    audio_files.append({
        "content": segment,
        "file": audio.file,
        "duration": audio.duration,
        "start_time": cumulative_time,
        "end_time": cumulative_time + audio.duration
    })
    cumulative_time += audio.duration

# 结果：精确的时间戳，完美的音频同步
```

#### 3. 完美解决痛点
- ✅ **PPTist集成完美**: 无需破坏现有PPT编辑体验
- ✅ **换行编辑最简单**: 用户最熟悉的分割方式
- ✅ **音频时长精确**: 基于实际TTS音频，无估算误差  
- ✅ **字幕时间戳准确**: 累积时长计算，毫秒级精度
- ✅ **辅助功能丰富**: 插入按钮提供高级分割选项
- ✅ **向后兼容**: 不影响现有功能

### PPTist集成建议

#### 主要编辑方式：换行分割（⭐⭐⭐⭐⭐推荐）
- **操作简单**: 用户直接按Enter键即可分割
- **实时预览**: 右侧面板即时显示分割效果
- **学习成本低**: 用户熟悉的文本编辑操作
- **准确度高**: 直观可见，容易调整

#### 辅助功能：插入按钮
- **特殊分割符**: 支持|||、|PAUSE|等高级标记
- **智能建议**: AI自动检测最佳分割位置
- **快捷键**: Ctrl+Enter快速插入换行
- **批量操作**: 一键优化所有分割点

### 实施建议

#### 第一阶段（MVP）：基础内容分割
```json
{
  "manual_split_config": {
    "enabled": true,
    "split_strategy": {
      "default_method": "content_split",
      "auto_detect_optimal": false
    },
    "content_split": {
      "split_markers": {
        "newline": { "enabled": true, "priority": 1 }
      },
      "audio_processing": {
        "strategy": "separate_generation"
      }
    }
  }
}
```

#### 第二阶段：高级功能
- 添加逗号+换行分割
- 智能分割建议
- 质量评分和警告
- 批量处理

#### 第三阶段：AI增强
- AI辅助分割点推荐
- 语音情感连续性优化
- 智能时长平衡

### 配置推荐（生产环境）
```json
{
  "manual_split_config": {
    "enabled": true,
    "split_strategy": {
      "default_method": "content_split",
      "allow_mixed_mode": true,
      "auto_detect_optimal": true,
      "fallback_to_auto": true
    },
    "content_split": {
      "enabled": true,
      "split_markers": {
        "newline": {
          "enabled": true,
          "priority": 1,
          "description": "按换行符分割（推荐）"
        },
        "comma_newline": {
          "enabled": true,
          "priority": 2,
          "pattern": "，\\s*\\n"
        }
      },
      "audio_processing": {
        "strategy": "separate_generation",
        "normalize_volume": true,
        "add_segment_gap": 0.1
      }
    },
    "quality_control": {
      "min_segment_length": 5,
      "max_segments_per_slide": 8,
      "min_segment_duration": 1.0,
      "validate_split_points": true
    }
  }
}
```

### 用户使用示例

**场景**: 用户想分割讲话稿 "are you ok，我的朋友们，今天来教大家安装cherry studio"

**操作步骤**:
1. 在讲话稿中按需要添加换行：
   ```
   are you ok，我的朋友们，
   今天来教大家安装cherry studio
   ```

2. 系统自动检测并预览：
   ```
   片段1: "are you ok，我的朋友们，" (预计2.8s)
   片段2: "今天来教大家安装cherry studio" (预计3.2s)
   总时长: 6.0s
   ```

3. 配音阶段生成：
   - `audio_seg1.wav` (2.8s) - "are you ok，我的朋友们，"
   - `audio_seg2.wav` (3.2s) - "今天来教大家安装cherry studio"

4. 视频时长：6.0s（累积音频时长）

5. 字幕时间戳：
   ```
   1
   00:00:00,000 --> 00:00:02,800
   are you ok，我的朋友们，
   
   2
   00:00:02,800 --> 00:00:06,000
   今天来教大家安装cherry studio
   ```

这个方案完美实现了你的想法：**在内容层面分割，音频独立生成，时长精确累积**！