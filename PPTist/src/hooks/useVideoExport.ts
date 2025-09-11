/**
 * PPTist视频导出Hook - 重构版本
 * 主要的导出功能入口，整合各种导出策略
 */
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'

// 导入拆分后的模块
import {
  generateImagesFromExistingThumbnails,
  generateImagesWithPPTistNative,
  generateImagesWithDirectCapture,
  generateImagesWithTruePPTistQuality,
  exportSlidesAsImages
} from './videoExport/imageGenerators'

import {
  generateCanvasImages
} from './videoExport/canvasExport'

import {
  showProgressMessage
} from './videoExport/exportUtils'

import {
  type ProjectData,
  exportToBackendWithChunkedUpload,
  exportToBackendWithChunkedUploadImproved,
  checkBackendStatus
} from './videoExport/backendExport'

import { saveAs } from 'file-saver'

export default function useVideoExport() {
  const exporting = ref(false)
  const uploadProgress = ref(0)
  const slidesStore = useSlidesStore()
  const { slides, title, theme, viewportSize, viewportRatio } = storeToRefs(slidesStore)

  /**
   * 提取幻灯片标题
   */
  const extractSlideTitle = (slide: any): string => {
    // 查找文本框元素中的标题
    const titleElement = slide.elements?.find((el: any) => 
      el.type === 'text' && 
      (el.style?.fontSize >= 24 || el.defaultFontSize >= 24)
    )
    
    if (titleElement?.content) {
      return titleElement.content.replace(/<[^>]*>/g, '').substring(0, 50)
    }
    
    return `幻灯片 ${slide.id || ''}`
  }

  /**
   * 生成项目JSON数据
   */
  const generateProjectData = (projectName?: string): ProjectData => {
    return {
      project_name: projectName || title.value || 'PPTist演示文稿',
      slides: slides.value.map((slide, index) => ({
        slide_number: index + 1,
        title: extractSlideTitle(slide),
        content: JSON.stringify({
          id: slide.id,
          remark: slide.remark || '',
          background: slide.background,
          elements: slide.elements
        })
      }))
    }
  }

  /**
   * 导出为视频生成格式（本地下载模式）
   */
  const exportForVideoGeneration = async () => {
    try {
      exporting.value = true

      // 1. 准备JSON数据
      const exportData = {
        title: title.value,
        width: viewportSize.value,
        height: viewportSize.value * viewportRatio.value,
        theme: theme.value,
        slides: slides.value.map((slide, index) => ({
          id: slide.id,
          slide_number: index + 1,
          title: extractSlideTitle(slide),
          remark: slide.remark || '',
          background: slide.background,
          elements: slide.elements,
          image_file: `slide_${String(index + 1).padStart(3, '0')}.png`
        })),
        total_slides: slides.value.length,
        exported_at: new Date().toISOString(),
        export_type: 'video_generation'
      }

      // 2. 导出JSON文件
      const jsonBlob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      })
      saveAs(jsonBlob, `${title.value || 'presentation'}.json`)

      // 3. 导出每页幻灯片为图片
      await exportSlidesAsImages()

      showProgressMessage('导出完成！文件已保存到下载目录', 'success')
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('导出失败:', error)
      showProgressMessage('导出失败！请检查控制台获取详细信息', 'error')
      throw error
    }
    finally {
      exporting.value = false
    }
  }

  /**
   * 使用现有缩略图的方案（最可靠）
   */
  const exportToBackendWithExistingThumbnails = async (projectName?: string) => {
    try {
      exporting.value = true
      uploadProgress.value = 0

      // eslint-disable-next-line no-console
      console.log('🎯 使用现有缩略图方案导出...')

      // 1. 检查后端服务
      const isBackendOnline = await checkBackendStatus()
      if (!isBackendOnline) {
        throw new Error('后端服务不可用，请确保服务器正在运行')
      }

      uploadProgress.value = 10

      // 2. 生成项目数据
      const projectData = generateProjectData(projectName)
      uploadProgress.value = 20

      // 3. 使用真正的PPTist原生导出方法（最高优先级）
      showProgressMessage('正在使用真正的PPTist原生导出方法...', 'info')
      
      let imageFiles: File[]
      try {
        // 首先尝试真正的PPTist原生方法（完全复制ThumbnailSlide逻辑）
        imageFiles = await generateImagesWithTruePPTistQuality()
        showProgressMessage(`✅ 真正PPTist导出成功，生成了 ${imageFiles.length} 个高质量图片`, 'success')
      }
      catch (truePPTistError) {
        // 如果真正PPTist方法失败，回退到直接捕获方法
        showProgressMessage('真正PPTist方法失败，回退到直接捕获方法...', 'warning')
        try {
          imageFiles = await generateImagesWithDirectCapture()
          showProgressMessage(`⚠️ 直接捕获成功，生成了 ${imageFiles.length} 个图片`, 'info')
        }
        catch (directError) {
          // 如果直接捕获也失败，最后回退到现有缩略图方法
          showProgressMessage('直接捕获失败，回退到现有缩略图方法...', 'warning')
          imageFiles = await generateImagesFromExistingThumbnails()
          showProgressMessage(`⚠️ 使用缩略图方法生成了 ${imageFiles.length} 个图片`, 'info')
        }
      }
      
      uploadProgress.value = 60

      // 4. 上传到后端
      showProgressMessage('正在上传到后端服务器...', 'info')
      const videoUrl = await exportToBackendWithChunkedUploadImproved(
        projectData,
        imageFiles
      )

      uploadProgress.value = 100
      showProgressMessage('导出成功！', 'success')

      return videoUrl
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('导出失败:', error)
      showProgressMessage('导出失败！请检查控制台获取详细信息', 'error')
      throw error
    }
    finally {
      exporting.value = false
      uploadProgress.value = 0
    }
  }

  /**
   * 使用Canvas生成图片的方案
   */
  const exportToBackendWithCanvas = async (projectName?: string) => {
    try {
      showProgressMessage('正在使用Canvas生成图片...', 'info')

      // 1. 使用Canvas生成图片
      const imageFiles = await generateCanvasImages(slides.value, {
        width: 1920,
        height: 1080,
        quality: 0.8,
        format: 'jpeg'
      })

      if (!imageFiles || imageFiles.length === 0) {
        throw new Error('Canvas图片生成失败')
      }

      showProgressMessage(`Canvas生成了 ${imageFiles.length} 张图片，开始上传...`, 'success')

      // 2. 创建项目数据
      const projectData: ProjectData = {
        project_name: projectName || `canvas_export_${Date.now()}`,
        slides: slides.value.map((slide, index) => ({
          slide_number: index + 1,
          title: extractSlideTitle(slide),
          content: slide.remark || ''
        }))
      }

      // 3. 上传项目数据和图片
      const videoUrl = await exportToBackendWithChunkedUploadImproved(projectData, imageFiles)

      showProgressMessage('Canvas导出成功！', 'success')
      return videoUrl
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('Canvas导出失败:', error)
      showProgressMessage('Canvas导出失败！', 'error')
      throw error
    }
  }

  /**
   * 使用PPTist原生方法的方案
   */
  const exportToBackendWithPPTistNative = async (projectName?: string) => {
    try {
      exporting.value = true
      uploadProgress.value = 0

      // eslint-disable-next-line no-console
      console.log('🎨 使用PPTist原生方法导出...')

      // 1. 检查后端服务
      const isBackendOnline = await checkBackendStatus()
      if (!isBackendOnline) {
        throw new Error('后端服务不可用，请确保服务器正在运行')
      }

      uploadProgress.value = 10

      // 2. 生成项目数据
      const projectData = generateProjectData(projectName)
      uploadProgress.value = 20

      // 3. 使用真正的PPTist原生导出方法（最高优先级）
      showProgressMessage('正在使用真正的PPTist原生导出方法...', 'info')
      
      let imageFiles: File[]
      try {
        // 首先尝试真正的PPTist原生方法（完全复制ThumbnailSlide逻辑）
        imageFiles = await generateImagesWithTruePPTistQuality()
        showProgressMessage(`✅ 真正PPTist导出成功，生成了 ${imageFiles.length} 个高质量图片`, 'success')
      }
      catch (truePPTistError) {
        // 如果真正PPTist方法失败，回退到直接捕获方法
        showProgressMessage('真正PPTist方法失败，回退到直接捕获方法...', 'warning')
        try {
          imageFiles = await generateImagesWithDirectCapture()
          showProgressMessage(`⚠️ 直接捕获成功，生成了 ${imageFiles.length} 个图片`, 'info')
        }
        catch (directError) {
          // 如果直接捕获也失败，最后回退到PPTist原生方法
          showProgressMessage('直接捕获失败，回退到PPTist原生方法...', 'warning')
          imageFiles = await generateImagesWithPPTistNative()
          showProgressMessage(`⚠️ 使用原生方法生成了 ${imageFiles.length} 个图片`, 'info')
        }
      }
      
      uploadProgress.value = 60

      // 4. 上传到后端
      showProgressMessage('正在上传到后端服务器...', 'info')
      const videoUrl = await exportToBackendWithChunkedUpload(
        projectData,
        imageFiles
      )

      uploadProgress.value = 100
      showProgressMessage('导出成功！', 'success')

      return videoUrl
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('导出失败:', error)
      showProgressMessage('导出失败！请检查控制台获取详细信息', 'error')
      throw error
    }
    finally {
      exporting.value = false
      uploadProgress.value = 0
    }
  }

  /**
   * 智能导出：优先使用新的直接捕获方案
   */
  const exportToBackendSmart = async (projectName?: string) => {
    try {
      // eslint-disable-next-line no-console
      console.log('🚀 开始智能导出，优先使用直接捕获方案...')

      // 优先使用新的直接幻灯片捕获方案（解决蓝色背景问题）
      try {
        // eslint-disable-next-line no-console
        console.log('🎯 尝试直接幻灯片捕获方案...')
        const result1 = await exportToBackendWithPPTistNative(projectName)
        // eslint-disable-next-line no-console
        console.log('✅ 直接捕获方案成功，返回:', result1)
        return result1
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.warn('❌ 直接捕获方案失败:', error)
      }

      // 备选方案1：Canvas生成方案
      try {
        // eslint-disable-next-line no-console
        console.log('🎨 尝试Canvas图片生成方案...')
        const result2 = await exportToBackendWithCanvas(projectName)
        // eslint-disable-next-line no-console
        console.log('✅ Canvas生成方案成功，返回:', result2)
        return result2
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.warn('❌ Canvas生成方案失败:', error)
      }

      // 备选方案2：现有缩略图方案
      try {
        // eslint-disable-next-line no-console
        console.log('📸 尝试现有缩略图方案...')
        const result3 = await exportToBackendWithExistingThumbnails(projectName)
        // eslint-disable-next-line no-console
        console.log('✅ 现有缩略图方案成功，返回:', result3)
        return result3
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.warn('❌ 现有缩略图方案失败:', error)
      }

      // 备选方案3：PPTist原生方案（需要手动操作）
      try {
        // eslint-disable-next-line no-console
        console.log('🔧 尝试PPTist原生方案...')
        const result4 = await exportToBackendWithPPTistNative(projectName)
        // eslint-disable-next-line no-console
        console.log('✅ PPTist原生方案成功，返回:', result4)
        return result4
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.error('❌ PPTist原生方案失败:', error)
        throw new Error('所有导出方案都失败了，请检查网络连接和后端服务')
      }
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('❌ 智能导出整体失败:', error)
      showProgressMessage('智能导出失败！', 'error')
      throw error
    }
  }

  /**
   * 重置状态
   */
  const resetExportState = () => {
    exporting.value = false
    uploadProgress.value = 0
  }

  return {
    // 状态
    exporting,
    uploadProgress,
    
    // 基础导出功能
    exportForVideoGeneration,
    
    // 后端导出功能
    exportToBackendWithExistingThumbnails,
    exportToBackendWithPPTistNative,
    exportToBackendSmart,
    
    // 别名和兼容性
    exportToBackend: exportToBackendSmart,
    canExport: computed(() => slides.value.length > 0),
    
    // 工具函数
    resetExportState,
    checkBackendStatus,
    
    // 数据访问
    slides,
    title,
    theme
  }
}
