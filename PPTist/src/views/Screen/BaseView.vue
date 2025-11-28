<template>
  <div class="base-view" :class="{ 'laser-pen': laserPen }">
    <ScreenSlideList
      :slideWidth="slideWidth"
      :slideHeight="slideHeight"
      :animationIndex="animationIndex"
      :turnSlideToId="turnSlideToId"
      :manualExitFullscreen="manualExitFullscreen"
      @wheel="mousewheelListener"
      @touchstart="touchStartListener"
      @touchend="touchEndListener"
      v-contextmenu="contextmenus"
    />

    <SlideThumbnails 
      v-if="slideThumbnailModelVisible" 
      :turnSlideToIndex="turnSlideToIndex" 
      @close="slideThumbnailModelVisible = false"
    />

    <WritingBoardTool 
      :slideWidth="slideWidth"
      :slideHeight="slideHeight"
      v-if="writingBoardToolVisible" 
      @close="writingBoardToolVisible = false" 
    />

    <CountdownTimer 
      v-if="timerlVisible" 
      @close="timerlVisible = false" 
    />

    <div class="tools-left">
      <IconLeftTwo class="tool-btn" theme="two-tone" :fill="['#111', '#fff']" @click="execPrev()" />
      <IconRightTwo class="tool-btn" theme="two-tone" :fill="['#111', '#fff']" @click="execNext()" />
    </div>

    <div 
      class="tools-right" :class="{ 'visible': rightToolsVisible }" 
      @mouseleave="rightToolsVisible = false"
      @mouseenter="rightToolsVisible = true"
    >
      <div class="content">
        <div class="tool-btn page-number" @click="slideThumbnailModelVisible = true">幻灯片 {{slideIndex + 1}} / {{slides.length}}</div>
        <IconWrite class="tool-btn" v-tooltip="'画笔工具'" @click="writingBoardToolVisible = true" />
        <IconMagic class="tool-btn" v-tooltip="'激光笔'" :class="{ 'active': laserPen }" @click="laserPen = !laserPen" />
        <IconStopwatchStart class="tool-btn" v-tooltip="'计时器'" :class="{ 'active': timerlVisible }" @click="timerlVisible = !timerlVisible" />
        <IconListView class="tool-btn" v-tooltip="'演讲者视图'" @click="changeViewMode('presenter')" />
        <IconSendOne class="tool-btn" v-tooltip="'批量导出到后端'" :class="{ 'active': batchExporting }" @click="handleBatchExport" />
        <IconOffScreenOne class="tool-btn" v-tooltip="'退出全屏'" v-if="fullscreenState" @click="manualExitFullscreen()" />
        <IconFullScreenOne class="tool-btn" v-tooltip="'进入全屏'" v-else @click="enterFullscreen()" />
        <IconPower class="tool-btn" v-tooltip="'结束放映'" @click="exitScreening()" />
      </div>
    </div>

    <BottomThumbnails v-if="bottomThumbnailsVisible" />
    
    <!-- 批量导出进度提示 -->
    <div class="batch-export-progress" v-if="batchExporting">
      <div class="progress-content">
        <div class="progress-text">{{ batchExportStatus }}</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: batchExportProgress + '%' }"></div>
        </div>
        <div class="progress-percent">{{ batchExportProgress }}%</div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore, useScreenStore } from '@/store'
import type { ContextmenuItem } from '@/components/Contextmenu/types'
import { enterFullscreen } from '@/utils/fullscreen'
import useScreening from '@/hooks/useScreening'
import useExecPlay from './hooks/useExecPlay'
import useSlideSize from './hooks/useSlideSize'
import useFullscreen from './hooks/useFullscreen'
import { useBatchExport } from './hooks/useBatchExport'
import message from '@/utils/message'

import ScreenSlideList from './ScreenSlideList.vue'
import SlideThumbnails from './SlideThumbnails.vue'
import WritingBoardTool from './WritingBoardTool.vue'
import CountdownTimer from './CountdownTimer.vue'
import BottomThumbnails from './BottomThumbnails.vue'
import { getAuthJsonHeaders } from '@/utils/authFetch'

const props = defineProps<{
  changeViewMode: (mode: 'base' | 'presenter') => void
}>()

const { slides, slideIndex } = storeToRefs(useSlidesStore())
const screenStore = useScreenStore()

const {
  autoPlayTimer,
  autoPlay,
  closeAutoPlay,
  autoPlayInterval,
  setAutoPlayInterval,
  loopPlay,
  setLoopPlay,
  mousewheelListener,
  touchStartListener,
  touchEndListener,
  turnPrevSlide,
  turnNextSlide,
  turnSlideToIndex,
  turnSlideToId,
  execPrev,
  execNext,
  animationIndex,
} = useExecPlay()

const { slideWidth, slideHeight } = useSlideSize()
const { exitScreening } = useScreening()
const { fullscreenState, manualExitFullscreen } = useFullscreen()

// 批量导出功能
const { 
  exporting: batchExporting, 
  exportProgress: batchExportProgress,
  exportStatus: batchExportStatus
} = useBatchExport()

const rightToolsVisible = ref(false)
const writingBoardToolVisible = ref(false)
const timerlVisible = ref(false)
const slideThumbnailModelVisible = ref(false)
const bottomThumbnailsVisible = ref(false)
const laserPen = ref(false)

/**
 * 将HTML格式的remark转换为纯文本,保留段落换行
 * PPTist存储的remark是HTML格式如: <p>段落1</p><p>段落2</p>
 * 需要转换为: 段落1\n段落2
 */
const convertHtmlRemarkToPlainText = (html: string): string => {
  if (!html || html.trim() === '') return ''
  
  // 创建临时DOM元素解析HTML
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  
  // 获取所有段落元素
  const paragraphs = tempDiv.querySelectorAll('p')
  
  if (paragraphs.length === 0) {
    // 如果没有<p>标签,直接返回文本内容
    return tempDiv.textContent?.trim() || ''
  }
  
  // 提取每个段落的文本,用换行符连接
  const textLines: string[] = []
  paragraphs.forEach(p => {
    const text = p.textContent?.trim()
    if (text) {
      textLines.push(text)
    }
  })
  
  return textLines.join('\n')
}

// 批量导出处理函数 - 逐页切换并导出
const handleBatchExport = async () => {
  if (batchExporting.value) {
    message.warning('正在导出中，请稍候...')
    return
  }

  try {
    const totalSlides = slides.value.length
    
    if (totalSlides === 0) {
      message.error('没有幻灯片可导出')
      return
    }

    // eslint-disable-next-line no-console
    console.log(`🚀 开始逐页导出 ${totalSlides} 张幻灯片...`)
    message.info(`开始批量导出 ${totalSlides} 张幻灯片...`)

    // 手动控制导出状态
    batchExporting.value = true
    batchExportProgress.value = 0
    batchExportStatus.value = '准备导出...'

    const exportedImages: Array<{
      slideIndex: number
      filename: string
      dataURL: string
      size: number
      text?: string
      duration?: number
    }> = []

    // 逐页导出
    for (let i = 0; i < totalSlides; i++) {
      batchExportStatus.value = `正在导出第 ${i + 1}/${totalSlides} 张...`
      
      // 切换到目标页
      if (slideIndex.value !== i) {
        turnSlideToIndex(i)
        // 等待渲染完成
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      // 查找当前幻灯片的DOM元素
      const slideElement = document.querySelector('.screen-slide-list .slide-item.current .screen-slide')
      
      if (!slideElement) {
        // eslint-disable-next-line no-console
        console.warn(`⚠️ 幻灯片 ${i + 1} 的DOM元素不存在，跳过`)
        continue
      }

      try {
        // 移除可能导致问题的xmlns属性
        const foreignObjectSpans = slideElement.querySelectorAll('foreignObject [xmlns]')
        foreignObjectSpans.forEach((span: Element) => span.removeAttribute('xmlns'))

        // 获取元素的原始transform
        const originalTransform = (slideElement as HTMLElement).style.transform
        
        // 临时移除transform缩放，使用原始尺寸导出
        ;(slideElement as HTMLElement).style.transform = 'scale(1)'
        
        // 等待浏览器重新渲染
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // 获取实际的DOM尺寸（无缩放状态）
        const rect = slideElement.getBoundingClientRect()
        const actualWidth = Math.round(rect.width)
        const actualHeight = Math.round(rect.height)
        
        // eslint-disable-next-line no-console
        console.log(`📐 幻灯片 ${i + 1} 原始尺寸: ${actualWidth}x${actualHeight}`)

        // 使用html-to-image导出 - 使用原始尺寸（scale=1）
        const { toJpeg } = await import('html-to-image')
        const dataURL = await toJpeg(slideElement as HTMLElement, {
          quality: 1.0,
          width: actualWidth,
          height: actualHeight,
          pixelRatio: 2, // 2x 提高清晰度
          cacheBust: true,
        })
        
        // 恢复原始transform
        ;(slideElement as HTMLElement).style.transform = originalTransform

        const filename = `slide_${String(i + 1).padStart(3, '0')}.jpg`
        
        // 获取当前幻灯片的备注文本和时长
        const currentSlide = slides.value[i]
        const remarkHtml = currentSlide?.remark || ''
        
        // 将HTML格式的remark转换为纯文本,保留段落换行
        const slideText = convertHtmlRemarkToPlainText(remarkHtml)
        const slideDuration = Math.max(3.0, slideText.length * 0.1)
        
        exportedImages.push({
          slideIndex: i,
          filename,
          dataURL,
          size: dataURL.length,
          text: slideText,
          duration: slideDuration
        })

        batchExportProgress.value = Math.round(((i + 1) / totalSlides) * 100)
        
        // eslint-disable-next-line no-console
        console.log(`✅ 已导出: ${filename} (${(dataURL.length / 1024 / 1024).toFixed(2)} MB)`)
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.error(`❌ 导出幻灯片 ${i + 1} 失败:`, error)
        message.error(`导出第 ${i + 1} 张幻灯片失败`)
      }
    }

    // 发送到后端
    batchExportStatus.value = '正在发送到后端...'
    
    // 从 localStorage 获取项目名称（由 VideoExportButton.vue 设置）
    // 如果没有则使用时间戳生成默认名称
    const storedProjectName = localStorage.getItem('video_export_project_name')
    const projectName = storedProjectName || `pptist_${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '')}`
    
    const exportData = {
      projectName,
      totalSlides,
      exportedCount: exportedImages.length,
      images: exportedImages,
      timestamp: Date.now()
    }

    const response = await fetch('http://localhost:5000/api/import-slides-batch', {
      method: 'POST',
      headers: getAuthJsonHeaders(),
      body: JSON.stringify(exportData)
    })

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`)
    }

    const result = await response.json()
    
    batchExporting.value = false
    
    // eslint-disable-next-line no-console
    console.log('✅ 批量导出完成:', result)
    
    // CRITICAL FIX: 导出完成后立即退出Screen模式(无论是否启动工作流)
    screenStore.setScreening(false)
    
    // 检查是否应该自动启动工作流
    const autoStartWorkflow = localStorage.getItem('auto_start_workflow_after_export')
    
    if (autoStartWorkflow === 'true' && result.workflow_ready) {
      message.success(`批量导出成功！共 ${exportedImages.length} 张，正在启动工作流...`)
      
      try {
        // 🔧 NEW: 检查批量导入API是否已经返回了workflow_id
        const importWorkflowId = result.workflow_id
        
        if (importWorkflowId) {
          // 如果batch_import已经返回了workflow_id,直接使用
          // eslint-disable-next-line no-console
          console.log('✅ 批量导入API已自动启动工作流, ID:', importWorkflowId)
          
          message.success(`工作流已自动启动！任务ID: ${importWorkflowId}`)
          
          // 触发自定义事件通知VideoExportButton
          const event = new CustomEvent('batchExportComplete', {
            detail: {
              success: true,
              workflow_id: importWorkflowId,
              project_name: result.project_name
            }
          })
          window.dispatchEvent(event)
        }
        else {
          // 旧流程: 手动调用workflow/execute
          const workflowResponse = await fetch('http://localhost:5000/api/workflow/execute', {
            method: 'POST',
            headers: getAuthJsonHeaders(),  // 🔧 添加认证头
            body: JSON.stringify({
              project_name: result.project_name
            })
          })
          
          if (workflowResponse.ok) {
            const workflowResult = await workflowResponse.json()
            // eslint-disable-next-line no-console
            console.log('🔍 后端返回的完整数据:', workflowResult)
            
            // 兼容两种API返回格式:
            // 1. 旧版API: { success: true, data: { workflow_id, task_id } }
            // 2. 新版API: { success: true, workflow_id, task_id }
            const workflowId = workflowResult.data?.workflow_id || 
                             workflowResult.data?.task_id || 
                             workflowResult.workflow_id || 
                             workflowResult.task_id
            
            if (!workflowId) {
              // eslint-disable-next-line no-console
              console.error('❌ 未获取到工作流ID!后端返回:', workflowResult)
              throw new Error('未获取到工作流ID')
            }
            
            message.success(`工作流已启动！任务ID: ${workflowId}`)
            // eslint-disable-next-line no-console
            console.log('✅ 工作流启动成功, ID:', workflowId)
            
            // 🔧 触发自定义事件通知VideoExportButtonNew
            const event = new CustomEvent('batchExportComplete', {
              detail: {
                success: true,
                workflow_id: workflowId,
                project_name: result.project_name
              }
            })
            window.dispatchEvent(event)
          }
          else {
            message.warning('图片导出成功，但工作流启动失败，请手动启动')
            
            // 触发失败事件
            const event = new CustomEvent('batchExportComplete', {
              detail: {
                success: false,
                error: '工作流启动失败'
              }
            })
            window.dispatchEvent(event)
          }
        }
      }
      catch (workflowError) {
        // eslint-disable-next-line no-console
        console.error('工作流启动失败:', workflowError)
        message.warning('图片导出成功，但工作流启动失败，请手动启动')
        
        // 触发失败事件
        const event = new CustomEvent('batchExportComplete', {
          detail: {
            success: false,
            error: String(workflowError)
          }
        })
        window.dispatchEvent(event)
      }
    }
    else {
      message.success(`批量导出成功！共 ${exportedImages.length} 张幻灯片`)
      
      if (result.next_step) {
        message.info('提示：可以在工作流页面启动视频生成')
      }
      
      // 🔧 如果不自动启动工作流，也触发事件（用于手动模式）
      const event = new CustomEvent('batchExportComplete', {
        detail: {
          success: true,
          workflow_id: null,
          project_name: result.project_name
        }
      })
      window.dispatchEvent(event)
    }
    
    // 清除自动导出标记
    localStorage.removeItem('auto_export_on_screen')
    localStorage.removeItem('auto_start_workflow_after_export')
  } 
  catch (error) {
    batchExporting.value = false
    batchExportStatus.value = '导出失败'
    // eslint-disable-next-line no-console
    console.error('批量导出失败:', error)
    message.error('批量导出失败')
    
    // 触发失败事件
    const event = new CustomEvent('batchExportComplete', {
      detail: {
        success: false,
        error: String(error)
      }
    })
    window.dispatchEvent(event)
    
    // 清除自动导出标记
    localStorage.removeItem('auto_export_on_screen')
    localStorage.removeItem('auto_start_workflow_after_export')
  }
}

// 检查是否需要自动导出
onMounted(() => {
  nextTick(() => {
    const autoExport = localStorage.getItem('auto_export_on_screen')
    if (autoExport === 'true') {
      // eslint-disable-next-line no-console
      console.log('🚀 检测到自动导出标记，延迟2秒后开始导出...')
      message.info('检测到批量导出请求，即将自动开始...')
      
      // 延迟2秒，确保所有幻灯片都已渲染完成
      setTimeout(() => {
        handleBatchExport()
      }, 2000)
    }
  })
})

const contextmenus = (): ContextmenuItem[] => {
  return [
    {
      text: '上一页',
      subText: '↑ ←',
      disable: slideIndex.value <= 0,
      handler: () => turnPrevSlide(),
    },
    {
      text: '下一页',
      subText: '↓ →',
      disable: slideIndex.value >= slides.value.length - 1,
      handler: () => turnNextSlide(),
    },
    {
      text: '第一页',
      disable: slideIndex.value === 0,
      handler: () => turnSlideToIndex(0),
    },
    {
      text: '最后一页',
      disable: slideIndex.value === slides.value.length - 1,
      handler: () => turnSlideToIndex(slides.value.length - 1),
    },
    { divider: true },
    {
      text: autoPlayTimer.value ? '取消自动放映' : '自动放映',
      handler: autoPlayTimer.value ? closeAutoPlay : autoPlay,
      children: [
        {
          text: '2.5秒',
          subText: autoPlayInterval.value === 2500 ? '√' : '',
          handler: () => setAutoPlayInterval(2500),
        },
        {
          text: '5秒',
          subText: autoPlayInterval.value === 5000 ? '√' : '',
          handler: () => setAutoPlayInterval(5000),
        },
        {
          text: '7.5秒',
          subText: autoPlayInterval.value === 7500 ? '√' : '',
          handler: () => setAutoPlayInterval(7500),
        },
        {
          text: '10秒',
          subText: autoPlayInterval.value === 10000 ? '√' : '',
          handler: () => setAutoPlayInterval(10000),
        },
      ],
    },
    {
      text: '循环放映',
      subText: loopPlay.value ? '√' : '',
      handler: () => setLoopPlay(!loopPlay.value),
    },
    { divider: true },
    {
      text: '显示工具栏',
      handler: () => rightToolsVisible.value = true,
    },
    {
      text: '查看所有幻灯片',
      handler: () => slideThumbnailModelVisible.value = true,
    },
    {
      text: '触底显示缩略图',
      subText: bottomThumbnailsVisible.value ? '√' : '',
      handler: () => bottomThumbnailsVisible.value = !bottomThumbnailsVisible.value,
    },
    {
      text: '画笔工具',
      handler: () => writingBoardToolVisible.value = true,
    },
    {
      text: '演讲者视图',
      handler: () => props.changeViewMode('presenter'),
    },
    { divider: true },
    {
      text: '结束放映',
      subText: 'ESC',
      handler: exitScreening,
    },
  ]
}
</script>

<style lang="scss" scoped>
.base-view {
  width: 100%;
  height: 100%;

  &.laser-pen {
    cursor: url(data:image/png;base64,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) 20 20, default !important;
  }
}
.tools-left {
  position: fixed;
  bottom: 8px;
  left: 8px;
  font-size: 25px;
  color: #666;
  z-index: 10;

  .tool-btn {
    opacity: .3;
    cursor: pointer;
    transition: opacity $transitionDelay;

    &:hover {
      opacity: .95;
    }
    & + .tool-btn {
      margin-left: 8px;
    }
  }
}
.tools-right {
  height: 66px;
  position: fixed;
  bottom: -66px;
  right: 0;
  z-index: 5;
  padding: 8px;
  transition: bottom $transitionDelay;

  &.visible {
    bottom: 0;
  }

  &::after {
    content: '';
    width: 100%;
    height: 66px;
    position: absolute;
    left: 0;
    top: -66px;
  }

  .content {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: $borderRadius;
    font-size: 25px;
    background-color: #fff;
    color: $textColor;
    padding: 8px 10px;
    box-shadow: 0 2px 12px 0 rgb(56, 56, 56, .2);
    border: 1px solid #e2e6ed;
  }

  .tool-btn {
    cursor: pointer;

    &:hover, &.active {
      color: $themeColor;
    }

    & + .tool-btn {
      margin-left: 15px;
    }
  }
  .page-number {
    font-size: 12px;
    padding: 0 12px;
    cursor: pointer;
  }
}

.batch-export-progress {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 30px 40px;
  border-radius: 8px;
  z-index: 999;
  min-width: 300px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);

  .progress-content {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .progress-text {
    font-size: 16px;
    text-align: center;
    font-weight: 500;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    overflow: hidden;

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #409eff, #67c23a);
      transition: width 0.3s ease;
    }
  }

  .progress-percent {
    font-size: 24px;
    text-align: center;
    font-weight: bold;
    color: #67c23a;
  }
}
</style>