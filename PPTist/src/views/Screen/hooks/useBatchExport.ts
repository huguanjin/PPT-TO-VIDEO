/**
 * PPTist批量导出Hook - 用于PPT转视频工作流
 * 
 * 功能：
 * 1. 批量导出所有幻灯片为高质量图片（质量=1.0）
 * 2. 将图片数据发送到后端Flask服务器
 * 3. 支持进度显示和错误处理
 * 
 * 使用场景：
 * - PPT转视频工作流：需要高质量图片输入
 * - 批量导出：一次性导出所有幻灯片
 * - 后端集成：自动发送到后端处理
 */

import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { toJpeg } from 'html-to-image'
import { useSlidesStore } from '@/store'
import message from '@/utils/message'

interface ExportResult {
  projectName: string
  totalSlides: number
  exportedCount: number
  images: Array<{
    slideIndex: number
    filename: string
    dataURL: string
    size: number
  }>
  timestamp: number
}

export const useBatchExport = () => {
  const slidesStore = useSlidesStore()
  const { title } = storeToRefs(slidesStore)
  
  const exporting = ref(false)
  const exportProgress = ref(0)
  const exportStatus = ref('')

  /**
   * 批量导出所有幻灯片
   * @param thumbnailsRef 幻灯片缩略图DOM引用数组
   * @param quality 图片质量 (0-1)，默认1.0最高质量
   * @param ignoreWebfont 是否忽略Web字体，默认true
   */
  const batchExportSlides = async (
    thumbnailsRef: any[], 
    quality: number = 1.0,
    ignoreWebfont: boolean = true
  ): Promise<ExportResult | null> => {
    if (!thumbnailsRef || thumbnailsRef.length === 0) {
      message.error('没有找到幻灯片')
      return null
    }

    exporting.value = true
    exportProgress.value = 0
    exportStatus.value = '准备导出...'

    const totalSlides = thumbnailsRef.length
    const exportedImages: Array<{
      slideIndex: number
      filename: string
      dataURL: string
      size: number
    }> = []

    try {
      message.info(`开始批量导出 ${totalSlides} 张幻灯片...`)

      // 逐张导出
      for (let i = 0; i < totalSlides; i++) {
        exportStatus.value = `正在导出第 ${i + 1}/${totalSlides} 张...`
        
        const slideElement = thumbnailsRef[i].$el || thumbnailsRef[i]
        
        if (!slideElement) {
          // eslint-disable-next-line no-console
          console.warn(`幻灯片 ${i + 1} 的DOM元素不存在`)
          continue
        }

        try {
          // 移除可能导致问题的xmlns属性
          const foreignObjectSpans = slideElement.querySelectorAll('foreignObject [xmlns]')
          foreignObjectSpans.forEach((span: Element) => span.removeAttribute('xmlns'))

          // 使用html-to-image导出高质量图片
          const dataURL = await toJpeg(slideElement, {
            quality,
            width: 1600, // 高分辨率 16:9
            height: 900,
            pixelRatio: 1, // 标准DPI
            fontEmbedCSS: ignoreWebfont ? '' : undefined,
            cacheBust: true, // 避免缓存问题
          })

          const filename = `slide_${String(i + 1).padStart(3, '0')}.jpg`
          
          exportedImages.push({
            slideIndex: i,
            filename,
            dataURL,
            size: dataURL.length
          })

          exportProgress.value = Math.round(((i + 1) / totalSlides) * 100)
          
          // eslint-disable-next-line no-console
          console.log(`✅ 已导出: ${filename} (${(dataURL.length / 1024 / 1024).toFixed(2)} MB)`)
        }
        catch (error) {
          // eslint-disable-next-line no-console
          console.error(`❌ 导出幻灯片 ${i + 1} 失败:`, error)
          message.error(`导出第 ${i + 1} 张幻灯片失败`)
        }
      }

      exportStatus.value = `导出完成: ${exportedImages.length}/${totalSlides} 张`
      message.success(`成功导出 ${exportedImages.length}/${totalSlides} 张幻灯片`)
      
      return {
        projectName: title.value,
        totalSlides,
        exportedCount: exportedImages.length,
        images: exportedImages,
        timestamp: Date.now()
      }
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('批量导出失败:', error)
      message.error('批量导出失败')
      exportStatus.value = '导出失败'
      return null
    }
    finally {
      exporting.value = false
    }
  }

  /**
   * 将导出结果发送到后端
   * @param exportData 导出数据
   * @param backendUrl 后端服务器地址
   */
  const sendToBackend = async (
    exportData: ExportResult, 
    backendUrl: string = 'http://localhost:5000'
  ): Promise<boolean> => {
    if (!exportData) {
      message.error('没有可发送的数据')
      return false
    }

    try {
      exportStatus.value = '正在发送到后端...'
      message.info('正在发送数据到后端...')

      const response = await fetch(`${backendUrl}/api/import-slides-batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
      })

      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`)
      }

      const result = await response.json()
      exportStatus.value = '发送成功'
      message.success('数据发送成功')
      // eslint-disable-next-line no-console
      console.log('后端响应:', result)
      
      return true
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('发送到后端失败:', error)
      message.error('发送到后端失败')
      exportStatus.value = '发送失败'
      return false
    }
  }

  /**
   * 完整的批量导出并发送流程
   * @param thumbnailsRef 幻灯片缩略图DOM引用数组
   * @param quality 图片质量 (0-1)
   * @param backendUrl 后端服务器地址
   */
  const exportAndSend = async (
    thumbnailsRef: any[],
    quality: number = 1.0,
    backendUrl: string = 'http://localhost:5000'
  ): Promise<boolean> => {
    // 1. 批量导出
    const exportData = await batchExportSlides(thumbnailsRef, quality)
    
    if (!exportData) {
      return false
    }

    // 2. 发送到后端
    const success = await sendToBackend(exportData, backendUrl)
    
    return success
  }

  return {
    exporting,
    exportProgress,
    exportStatus,
    batchExportSlides,
    sendToBackend,
    exportAndSend
  }
}

export default useBatchExport
