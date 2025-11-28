/**
 * PPTist工作流集成导出器
 * 扩展PPTist的导出功能，使其能够与后端工作流集成
 */

import { ref } from 'vue'
import { toPng, toJpeg } from 'html-to-image'
import { useSlidesStore } from '@/store'
import { getAuthHeaders, getAuthJsonHeaders } from '@/utils/authFetch'

// 导入新的直接幻灯片捕获功能
import { generateImagesWithDirectCapture } from './videoExport/imageGenerators'

interface ExportConfig {
  format: 'png' | 'jpeg'
  quality: number
  width: number
  ignoreWebfont: boolean
  projectName: string
  backendUrl: string
}

interface SlideExportResult {
  success: boolean
  slideIndex: number
  slideId: string
  filename?: string
  error?: string
}

interface BatchExportResult {
  success: boolean
  totalSlides: number
  successCount: number
  failedCount: number
  results: SlideExportResult[]
}

export class PPTistWorkflowExporter {
  private config: ExportConfig
  private isExporting = ref(false)
  
  constructor(config: ExportConfig) {
    this.config = config
  }
  
  /**
   * 导出当前PPT的所有slides到后端工作流（使用新的直接捕获功能）
   */
  async exportToWorkflow(
    progressCallback?: (progress: number) => void
  ): Promise<BatchExportResult> {
    const slidesStore = useSlidesStore()
    const slides = slidesStore.slides
    const totalSlides = slides.length
    
    // 开始导出PPT到工作流
    this.isExporting.value = true
    const results: SlideExportResult[] = []
    let successCount = 0
    let failedCount = 0
    
    try {
      // 使用新的直接幻灯片捕获功能
      if (progressCallback) {
        progressCallback(10)
      }
      
      // 直接捕获所有幻灯片
      const imageFiles = await generateImagesWithDirectCapture()
      
      if (progressCallback) {
        progressCallback(60)
      }
      
      // 上传捕获的图片到后端
      for (let i = 0; i < imageFiles.length && i < slides.length; i++) {
        const slide = slides[i]
        const imageFile = imageFiles[i]
        
        try {
          // 上传图片文件到后端
          const uploadResult = await this.uploadFileToBackend(imageFile, slide, i)
          
          results.push({
            success: true,
            slideIndex: i,
            slideId: slide.id,
            filename: uploadResult.filename
          })
          successCount++
          
          // 更新进度
          if (progressCallback) {
            const progress = 60 + Math.round(((i + 1) / imageFiles.length) * 30)
            progressCallback(progress)
          }
          
        }
        catch (error) {
          failedCount++
          results.push({
            success: false,
            slideIndex: i,
            slideId: slide.id,
            error: error instanceof Error ? error.message : String(error)
          })
        }
        
        // 短暂延迟，避免过快上传
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      // 处理缺失的slides（如果捕获的图片数量少于slide数量）
      for (let i = imageFiles.length; i < slides.length; i++) {
        failedCount++
        results.push({
          success: false,
          slideIndex: i,
          slideId: slides[i].id,
          error: '直接捕获功能未能捕获此幻灯片'
        })
      }
      
      // 完成进度
      if (progressCallback) {
        progressCallback(100)
      }
      
      // PPT导出完成统计
      
      return {
        success: successCount > 0,
        totalSlides,
        successCount,
        failedCount,
        results
      }

    }
    finally {
      this.isExporting.value = false
    }
  }
  
  /**
   * 导出单个slide
   */
  private async exportSingleSlide(slide: any, index: number): Promise<SlideExportResult> {
    try {
      // 1. 创建临时的slide渲染元素
      const slideElement = this.createSlideElement(slide, index)
      
      // 2. 渲染为图片
      const imageDataUrl = await this.renderSlideToImage(slideElement)
      
      // 3. 上传到后端
      const uploadResult = await this.uploadImageToBackend(imageDataUrl, slide, index)
      
      // 4. 清理临时元素
      this.cleanupSlideElement(slideElement)
      
      return {
        success: true,
        slideIndex: index,
        slideId: slide.id,
        filename: uploadResult.filename
      }

    }
    catch (error) {
      return {
        success: false,
        slideIndex: index,
        slideId: slide.id,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }
  
  /**
   * 创建slide渲染元素
   */
  private createSlideElement(slide: any, index: number): HTMLElement {
    // 这里需要重用PPTist的ThumbnailSlide组件逻辑
    // 由于无法直接在这里创建Vue组件，我们需要找到已渲染的slide元素
    
    // 方案1: 查找已存在的slide缩略图
    const existingThumbnail = document.querySelector(`.thumbnail-slide[data-slide-id="${slide.id}"]`) as HTMLElement
    if (existingThumbnail) {
      return existingThumbnail.cloneNode(true) as HTMLElement
    }
    
    // 方案2: 创建临时渲染容器
    const container = document.createElement('div')
    container.style.position = 'absolute'
    container.style.left = '-9999px'
    container.style.top = '0'
    container.style.width = `${this.config.width}px`
    container.style.height = `${this.config.width * 0.5625}px` // 16:9比例
    
    // 这里需要手动渲染slide内容
    // 实际实现中，您可能需要调用Vue的渲染函数或使用其他方式
    container.innerHTML = `
      <div class="slide-export-container" style="width: 100%; height: 100%; background: white;">
        <div class="slide-placeholder">Slide ${index + 1}</div>
      </div>
    `
    
    document.body.appendChild(container)
    return container
  }
  
  /**
   * 将slide元素渲染为图片
   */
  private async renderSlideToImage(element: HTMLElement): Promise<string> {
    const toImage = this.config.format === 'png' ? toPng : toJpeg
    
    const imageConfig = {
      quality: this.config.quality,
      width: this.config.width,
      pixelRatio: 1,
      fontEmbedCSS: this.config.ignoreWebfont ? '' : undefined
    }
    
    // 清理一些可能导致问题的属性
    const foreignObjectSpans = element.querySelectorAll('foreignObject [xmlns]')
    foreignObjectSpans.forEach(spanRef => spanRef.removeAttribute('xmlns'))
    
    return await toImage(element, imageConfig)
  }
  
  /**
   * 上传图片文件到后端（新增方法，用于直接上传File对象）
   */
  private async uploadFileToBackend(imageFile: File, slide: any, index: number): Promise<any> {
    const formData = new FormData()
    formData.append('file', imageFile)
    formData.append('project_name', this.config.projectName)
    formData.append('slide_index', index.toString())
    formData.append('slide_id', slide.id)
    formData.append('format', this.config.format)
    
    const response = await fetch(`${this.config.backendUrl}/api/pptist_export/upload/file`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`文件上传失败: ${response.status} ${response.statusText}`)
    }
    
    return await response.json()
  }

  /**
   * 上传图片到后端
   */
  private async uploadImageToBackend(imageDataUrl: string, slide: any, index: number): Promise<any> {
    const response = await fetch(`${this.config.backendUrl}/api/pptist_export/upload/base64`, {
      method: 'POST',
      headers: getAuthJsonHeaders(),
      body: JSON.stringify({
        image_data: imageDataUrl,
        project_name: this.config.projectName,
        slide_index: index,
        slide_id: slide.id,
        format: this.config.format
      })
    })
    
    if (!response.ok) {
      throw new Error(`上传失败: ${response.status} ${response.statusText}`)
    }
    
    const result = await response.json()
    if (!result.success) {
      throw new Error(result.message || '上传失败')
    }
    
    return result.data
  }
  
  /**
   * 清理临时元素
   */
  private cleanupSlideElement(element: HTMLElement): void {
    if (element.parentNode) {
      element.parentNode.removeChild(element)
    }
  }
  
  /**
   * 检查导出状态
   */
  async checkExportStatus(): Promise<any> {
    const response = await fetch(`${this.config.backendUrl}/api/pptist_export/export/status/${this.config.projectName}`, {
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`获取状态失败: ${response.status}`)
    }
    
    const result = await response.json()
    return result.data
  }
  
  /**
   * 获取导出状态
   */
  get exportingStatus() {
    return this.isExporting.value
  }
}

/**
 * 创建工作流导出器
 */
export function createWorkflowExporter(projectName: string, backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'): PPTistWorkflowExporter {
  const config: ExportConfig = {
    format: 'png',
    quality: 1.0,
    width: 1600,
    ignoreWebfont: true,
    projectName,
    backendUrl
  }
  
  return new PPTistWorkflowExporter(config)
}

/**
 * Vue Composition API hook
 */
export function useWorkflowExport(projectName: string) {
  const exporter = createWorkflowExporter(projectName)
  
  return {
    exportToWorkflow: exporter.exportToWorkflow.bind(exporter),
    checkExportStatus: exporter.checkExportStatus.bind(exporter),
    isExporting: exporter.exportingStatus
  }
}
