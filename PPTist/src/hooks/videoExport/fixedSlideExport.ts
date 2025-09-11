/**
 * 修复版PPT幻灯片导出器
 * 解决左上角1/4位置问题，确保与PPTist前端导出质量一致
 */

import { toJpeg, toPng } from 'html-to-image'
import { useSlidesStore } from '@/store'

interface ExportQuality {
  format: 'jpeg' | 'png'
  quality: number
  width: number
  height: number
}

/**
 * PPTist原生导出配置（完全复制前端导出图片功能的配置）
 */
const PPTIST_NATIVE_CONFIG: ExportQuality = {
  format: 'jpeg',
  quality: 0.9, // PPTist默认质量
  width: 1600, // PPTist默认宽度
  height: 900 // 按16:9比例计算
}

/**
 * 高质量导出配置（用于生成与前端导出一致的图片）
 */
const HIGH_QUALITY_CONFIG: ExportQuality = {
  format: 'png',
  quality: 1.0,
  width: 1920,
  height: 1080
}

/**
 * 查找正确的幻灯片编辑区域
 * 避免捕获缩略图，确保捕获实际的编辑内容
 */
function findActualSlideViewport(): HTMLElement | null {
  // 优先级1: 查找编辑器的viewport（实际编辑区域）
  const viewport = document.querySelector('.canvas .viewport') as HTMLElement
  if (viewport && isValidElement(viewport)) {
    return viewport
  }

  // 优先级2: 查找完整的canvas区域
  const canvas = document.querySelector('.canvas .viewport-wrapper') as HTMLElement
  if (canvas && isValidElement(canvas)) {
    return canvas
  }

  // 优先级3: 查找幻灯片内容区域
  const slideContent = document.querySelector('.editable-element-wrapper') as HTMLElement
  if (slideContent && isValidElement(slideContent)) {
    return slideContent
  }

  return null
}

/**
 * 检查元素是否为有效的导出目标
 */
function isValidElement(element: HTMLElement): boolean {
  const rect = element.getBoundingClientRect()
  const style = window.getComputedStyle(element)
  
  // 检查尺寸（至少300x200）
  if (rect.width < 300 || rect.height < 200) {
    return false
  }
  
  // 检查可见性
  if (style.display === 'none' || 
      style.visibility === 'hidden' || 
      style.opacity === '0') {
    return false
  }
  
  // 检查是否在视口内
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  
  if (rect.right < 0 || rect.bottom < 0 || 
      rect.left > viewportWidth || rect.top > viewportHeight) {
    return false
  }
  
  return true
}

/**
 * 获取元素的实际缩放比例
 */
function getElementScale(element: HTMLElement): { scaleX: number; scaleY: number } {
  const style = window.getComputedStyle(element)
  const transform = style.transform
  
  let scaleX = 1
  let scaleY = 1
  
  if (transform && transform !== 'none') {
    const matrix = transform.match(/matrix\(([^)]+)\)/)
    if (matrix) {
      const values = matrix[1].split(',').map(v => parseFloat(v.trim()))
      if (values.length >= 6) {
        scaleX = values[0]
        scaleY = values[3]
      }
    }
  }
  
  return { scaleX, scaleY }
}

/**
 * 计算最佳导出配置
 */
function calculateExportConfig(element: HTMLElement, targetConfig: ExportQuality) {
  const rect = element.getBoundingClientRect()
  const scale = getElementScale(element)
  
  // 计算实际内容尺寸（去除缩放影响）
  const actualWidth = rect.width / scale.scaleX
  const actualHeight = rect.height / scale.scaleY
  
  // 计算合适的输出尺寸
  const aspectRatio = actualWidth / actualHeight
  let outputWidth = targetConfig.width
  let outputHeight = targetConfig.height
  
  // 保持宽高比
  if (aspectRatio > outputWidth / outputHeight) {
    outputHeight = outputWidth / aspectRatio
  }
  else {
    outputWidth = outputHeight * aspectRatio
  }
  
  return {
    width: Math.round(outputWidth),
    height: Math.round(outputHeight),
    quality: targetConfig.quality,
    backgroundColor: '#ffffff',
    style: {
      transform: 'scale(1)', // 重置缩放
      transformOrigin: 'top left'
    },
    pixelRatio: 2 // 高清输出
  }
}

/**
 * 修复版图片导出 - 确保与PPTist前端导出一致
 */
async function captureSlideWithFixedConfig(
  element: HTMLElement, 
  slideIndex: number,
  useHighQuality = true
): Promise<File> {
  const targetConfig = useHighQuality ? HIGH_QUALITY_CONFIG : PPTIST_NATIVE_CONFIG
  const exportConfig = calculateExportConfig(element, targetConfig)
  
  // 确保元素在视口中心
  element.scrollIntoView({ 
    behavior: 'instant', 
    block: 'center', 
    inline: 'center' 
  })
  
  // 等待渲染稳定
  await new Promise(resolve => setTimeout(resolve, 300))
  
  // 优先使用JPEG（与PPTist前端一致）
  if (targetConfig.format === 'jpeg') {
    const dataUrl = await toJpeg(element, exportConfig)
    const response = await fetch(dataUrl)
    const blob = await response.blob()
    
    const filename = `slide_${String(slideIndex + 1).padStart(3, '0')}.jpg`
    return new File([blob], filename, { type: 'image/jpeg' })
  }
  
  const dataUrl = await toPng(element, exportConfig)
  const response = await fetch(dataUrl)
  const blob = await response.blob()
  
  const filename = `slide_${String(slideIndex + 1).padStart(3, '0')}.png`
  return new File([blob], filename, { type: 'image/png' })
}

/**
 * 等待幻灯片完全加载
 */
async function waitForSlideLoad(): Promise<void> {
  // 基础等待时间
  await new Promise(resolve => setTimeout(resolve, 500))
  
  // 等待可能的异步加载
  await new Promise(resolve => {
    const checkLoaded = () => {
      const viewport = findActualSlideViewport()
      if (viewport) {
        resolve(undefined)
      }
      else {
        setTimeout(checkLoaded, 100)
      }
    }
    checkLoaded()
  })
  
  // 额外稳定时间
  await new Promise(resolve => setTimeout(resolve, 200))
}

/**
 * 修复版幻灯片导出主函数
 */
export async function generateImagesWithFixedExport(): Promise<File[]> {
  const slidesStore = useSlidesStore()
  const slides = slidesStore.slides
  const originalSlideIndex = slidesStore.slideIndex
  
  if (!slides || slides.length === 0) {
    throw new Error('没有找到幻灯片数据')
  }
  
  const files: File[] = []
  
  try {
    // 逐页切换并导出
    for (let i = 0; i < slides.length; i++) {
      // 切换到指定幻灯片
      slidesStore.updateSlideIndex(i)
      
      // 等待幻灯片加载完成
      await waitForSlideLoad()
      
      // 查找实际的幻灯片编辑区域
      const slideElement = findActualSlideViewport()
      
      if (!slideElement) {
        // 创建占位符
        const placeholder = await createPlaceholder(i)
        files.push(placeholder)
        continue
      }
      
      try {
        // 使用修复版配置导出
        const file = await captureSlideWithFixedConfig(slideElement, i, true)
        files.push(file)
      }
      catch (error) {
        // 尝试备用方案
        try {
          const file = await captureSlideWithFixedConfig(slideElement, i, false)
          files.push(file)
        }
        catch (fallbackError) {
          // 创建错误占位符
          const placeholder = await createPlaceholder(i)
          files.push(placeholder)
        }
      }
      
      // 短暂延迟确保稳定
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }
  finally {
    // 恢复原始幻灯片位置
    slidesStore.updateSlideIndex(originalSlideIndex)
  }
  
  return files
}

/**
 * 创建占位符文件（当导出失败时使用）
 */
async function createPlaceholder(slideIndex: number): Promise<File> {
  const canvas = document.createElement('canvas')
  canvas.width = 1920
  canvas.height = 1080
  
  const ctx = canvas.getContext('2d')!
  
  // 绘制占位符
  ctx.fillStyle = '#f5f5f5'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  ctx.fillStyle = '#666666'
  ctx.font = '48px Arial'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(`幻灯片 ${slideIndex + 1}`, canvas.width / 2, canvas.height / 2)
  
  // 转换为文件
  const blob = await new Promise<Blob>((resolve) => {
    canvas.toBlob((blob) => resolve(blob!), 'image/jpeg', 0.9)
  })
  
  const filename = `slide_${String(slideIndex + 1).padStart(3, '0')}.jpg`
  return new File([blob], filename, { type: 'image/jpeg' })
}

/**
 * 检查当前是否可以进行导出
 */
export function canPerformFixedExport(): boolean {
  const viewport = findActualSlideViewport()
  return viewport !== null
}

/**
 * 获取导出状态诊断信息
 */
export function getExportDiagnostics() {
  const viewport = findActualSlideViewport()
  const slidesStore = useSlidesStore()
  
  return {
    hasValidViewport: viewport !== null,
    currentSlideIndex: slidesStore.slideIndex,
    totalSlides: slidesStore.slides.length,
    viewportInfo: viewport ? {
      width: viewport.getBoundingClientRect().width,
      height: viewport.getBoundingClientRect().height,
      className: viewport.className
    } : null
  }
}
