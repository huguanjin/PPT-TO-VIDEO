/**
 * 直接幻灯片捕获器 - 修复蓝色背景问题
 * 直接捕获PPTist的幻灯片内容，而不依赖导出对话框
 */

import { toPng, toJpeg } from 'html-to-image'
import { useSlidesStore } from '@/store'

interface SlideElement {
  element: HTMLElement
  slideIndex: number
  slideId: string
}

/**
 * 修复版：生成所有幻灯片图片（逐页切换并捕获）
 */
export const generateImagesFromDirectSlideCaptureFixed = async (): Promise<File[]> => {
  const slidesStore = useSlidesStore()
  const slides = slidesStore.slides
  const originalSlideIndex = slidesStore.slideIndex
  
  if (!slides || slides.length === 0) {
    throw new Error('没有找到幻灯片数据')
  }
  
  // 开始捕获所有幻灯片
  const files: File[] = []
  
  try {
    // 逐个切换幻灯片并捕获
    for (let i = 0; i < slides.length; i++) {
      // 切换到指定幻灯片
      slidesStore.updateSlideIndex(i)
      
      // 等待幻灯片切换和渲染完成
      await waitForSlideToRender()
      
      // 查找当前幻灯片的编辑区域
      const slideElement = findCurrentSlideElement()
      
      if (!slideElement) {
        continue
      }
      
      // 捕获当前幻灯片
      try {
        const file = await captureSlideElement(slideElement, i)
        files.push(file)
      }
      catch (error) {
        // 创建错误占位符
        const placeholderFile = await createErrorPlaceholder(i)
        files.push(placeholderFile)
      }
      
      // 短暂延迟确保稳定性
      await new Promise(resolve => setTimeout(resolve, 200))
    }
  }
  finally {
    // 恢复原始幻灯片索引
    slidesStore.updateSlideIndex(originalSlideIndex)
  }
  
  return files
}

/**
 * 等待幻灯片渲染完成
 */
async function waitForSlideToRender(): Promise<void> {
  // 等待基础渲染
  await new Promise(resolve => setTimeout(resolve, 300))
  
  // 等待可能的动画和异步渲染
  await new Promise(resolve => {
    if (window.requestIdleCallback) {
      window.requestIdleCallback(resolve, { timeout: 1000 })
    }
    else {
      setTimeout(resolve, 500)
    }
  })
  
  // 额外等待确保所有内容加载完成
  await new Promise(resolve => setTimeout(resolve, 200))
}

/**
 * 查找当前幻灯片的DOM元素
 */
function findCurrentSlideElement(): HTMLElement | null {
  // 优先级1：编辑区域的主幻灯片
  const editAreaSelectors = [
    '.editor-area .slide',
    '.editor-area .slide-content',
    '.editor-area .canvas',
    '.slide-editor .slide',
    '.presentation-editor .slide',
    '.canvas-panel .canvas',
    '.slide-viewport .slide'
  ]
  
  for (const selector of editAreaSelectors) {
    const element = document.querySelector(selector) as HTMLElement
    if (element && isValidSlideElement(element)) {
      return element
    }
  }
  
  // 优先级2：通过data属性查找
  const dataSelectors = [
    '[data-slide-id]',
    '[data-slide]',
    '.slide[data-index]'
  ]
  
  for (const selector of dataSelectors) {
    const element = document.querySelector(selector) as HTMLElement
    if (element && isValidSlideElement(element)) {
      return element
    }
  }
  
  // 优先级3：查找最大的可能幻灯片元素
  const possibleElements = document.querySelectorAll('.slide, .canvas, .slide-content')
  let bestElement: HTMLElement | null = null
  let maxArea = 0
  
  possibleElements.forEach(element => {
    if (element instanceof HTMLElement && isValidSlideElement(element)) {
      const area = element.offsetWidth * element.offsetHeight
      if (area > maxArea) {
        maxArea = area
        bestElement = element
      }
    }
  })
  
  if (bestElement) {
    return bestElement
  }
  
  return null
}

/**
 * 验证元素是否为有效的幻灯片元素
 */
function isValidSlideElement(element: HTMLElement): boolean {
  const rect = element.getBoundingClientRect()
  
  // 检查尺寸
  if (rect.width < 200 || rect.height < 150) {
    return false
  }
  
  // 检查可见性
  if (rect.width === 0 || rect.height === 0) {
    return false
  }
  
  // 检查是否在可视区域
  const style = window.getComputedStyle(element)
  if (style.display === 'none' || style.visibility === 'hidden') {
    return false
  }
  
  return true
}

/**
 * 捕获幻灯片元素为图片文件
 */
async function captureSlideElement(element: HTMLElement, slideIndex: number): Promise<File> {
  // 确保元素在可视区域
  element.scrollIntoView({ 
    behavior: 'instant', 
    block: 'center',
    inline: 'center'
  })
  
  // 等待滚动完成
  await new Promise(resolve => setTimeout(resolve, 100))
  
  const config = getOptimalCaptureConfig(element)
  
  try {
    // 首先尝试JPEG格式
    const dataUrl = await toJpeg(element, config)
    const response = await fetch(dataUrl)
    const blob = await response.blob()
    
    // 检查文件大小
    if (blob.size < 5000) {
      // 尝试PNG格式
      const pngDataUrl = await toPng(element, {
        ...config,
        quality: 1.0
      })
      
      const pngResponse = await fetch(pngDataUrl)
      const pngBlob = await pngResponse.blob()
      
      if (pngBlob.size > blob.size) {
        return new File([pngBlob], `slide_${String(slideIndex + 1).padStart(3, '0')}.png`, {
          type: 'image/png'
        })
      }
    }
    
    return new File([blob], `slide_${String(slideIndex + 1).padStart(3, '0')}.jpg`, {
      type: 'image/jpeg'
    })
  }
  catch (error) {
    // 备用方案：使用PNG格式
    const pngDataUrl = await toPng(element, {
      ...config,
      quality: 0.95
    })
    
    const pngResponse = await fetch(pngDataUrl)
    const pngBlob = await pngResponse.blob()
    
    return new File([pngBlob], `slide_${String(slideIndex + 1).padStart(3, '0')}.png`, {
      type: 'image/png'
    })
  }
}

/**
 * 获取优化的捕获配置
 */
function getOptimalCaptureConfig(element: HTMLElement) {
  const rect = element.getBoundingClientRect()
  
  // 计算输出尺寸
  const aspectRatio = rect.width / rect.height
  let targetWidth = 1920
  let targetHeight = 1080
  
  // 保持宽高比
  if (aspectRatio > 16 / 9) {
    targetHeight = Math.round(targetWidth / aspectRatio)
  }
  else {
    targetWidth = Math.round(targetHeight * aspectRatio)
  }
  
  return {
    quality: 0.9,
    width: targetWidth,
    height: targetHeight,
    style: {
      transform: 'scale(1)',
      transformOrigin: 'top left'
    },
    filter: (node: Element) => {
      // 过滤掉可能的工具栏和控制元素
      if (node.classList) {
        return !node.classList.contains('toolbar') && 
               !node.classList.contains('controls') &&
               !node.classList.contains('menu')
      }
      return true
    },
    backgroundColor: '#ffffff'
  }
}

/**
 * 创建错误占位符
 */
function createErrorPlaceholder(slideIndex: number): Promise<File> {
  // 创建简单的错误占位符
  const canvas = document.createElement('canvas')
  canvas.width = 1920
  canvas.height = 1080
  const ctx = canvas.getContext('2d')!
  
  // 绘制错误占位符
  ctx.fillStyle = '#f0f0f0'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  ctx.fillStyle = '#666666'
  ctx.font = '48px Arial'
  ctx.textAlign = 'center'
  ctx.fillText(`幻灯片 ${slideIndex + 1}`, canvas.width / 2, canvas.height / 2 - 50)
  
  ctx.font = '24px Arial'
  ctx.fillText('捕获失败', canvas.width / 2, canvas.height / 2 + 20)
  
  // 转换为blob
  return new Promise(resolve => {
    canvas.toBlob(blob => {
      const file = new File([blob!], `slide_${String(slideIndex + 1).padStart(3, '0')}_error.jpg`, {
        type: 'image/jpeg'
      })
      resolve(file)
    }, 'image/jpeg', 0.8)
  })
}

/**
 * 查找所有实际的幻灯片元素 (原版函数，保留兼容性)
 */
function findSlideElements(): SlideElement[] {
  const slidesStore = useSlidesStore()
  const slides = slidesStore.slides
  
  const slideElements: SlideElement[] = []
  
  // 策略1: 查找编辑区域的幻灯片
  const editArea = document.querySelector('.editor-area') || 
                   document.querySelector('.slide-editor') ||
                   document.querySelector('.presentation-editor')
  
  if (editArea) {
    // 如果在编辑模式，只有一个当前幻灯片
    const currentSlide = editArea.querySelector('.slide') || 
                        editArea.querySelector('.slide-content') ||
                        editArea.querySelector('.canvas')
    
    if (currentSlide && slides.length > 0) {
      // 获取当前幻灯片索引
      const currentIndex = slidesStore.slideIndex
      slideElements.push({
        element: currentSlide as HTMLElement,
        slideIndex: currentIndex,
        slideId: slides[currentIndex]?.id || `slide_${currentIndex}`
      })
    }
  }
  
  // 策略2: 查找左侧缩略图面板中的所有幻灯片
  const thumbnailPanel = document.querySelector('.thumbnail-panel') ||
                        document.querySelector('.slides-panel') ||
                        document.querySelector('.slide-list')
  
  if (thumbnailPanel) {
    const thumbnails = thumbnailPanel.querySelectorAll('.thumbnail-slide') ||
                      thumbnailPanel.querySelectorAll('.slide-thumbnail') ||
                      thumbnailPanel.querySelectorAll('.slide-item')
    
    thumbnails.forEach((thumbnail, index) => {
      if (thumbnail instanceof HTMLElement) {
        slideElements.push({
          element: thumbnail,
          slideIndex: index,
          slideId: slides[index]?.id || `slide_${index}`
        })
      }
    })
  }
  
  // 策略3: 如果都没找到，尝试通过Vue组件查找
  if (slideElements.length === 0) {
    // 查找所有可能的幻灯片容器
    const possibleSlides = document.querySelectorAll(
      '.slide, .slide-content, .canvas, [data-slide-id], .presentation-slide'
    )
    
    possibleSlides.forEach((slide, index) => {
      if (slide instanceof HTMLElement && slide.offsetWidth > 100 && slide.offsetHeight > 100) {
        slideElements.push({
          element: slide,
          slideIndex: index,
          slideId: slides[index]?.id || `slide_${index}`
        })
      }
    })
  }
  
  return slideElements
}

/**
 * 直接幻灯片导出 - 主函数
 */
export const generateImagesFromDirectSlideCapture = async (): Promise<File[]> => {
  // 启动直接幻灯片捕获
  
  const slideElements = findSlideElements()
  
  if (slideElements.length === 0) {
    throw new Error(`
❌ 未找到任何幻灯片元素

🔍 可能的原因：
1. PPTist界面尚未完全加载
2. 没有创建任何幻灯片
3. 当前不在编辑模式

💡 建议操作：
1. 确保至少有一张幻灯片
2. 在编辑模式下执行导出
3. 或者先手动打开"导出图片"对话框`)
  }
  
  // 找到幻灯片元素
  
  const files: File[] = []
  
  for (const slideInfo of slideElements) {
    // 处理幻灯片页面
    
    // 滚动到可视区域（如果需要）
    slideInfo.element.scrollIntoView({ behavior: 'instant', block: 'center' })
    
    // 等待渲染稳定
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 获取优化的捕获配置
    const config = getOptimalCaptureConfig(slideInfo.element)
    
    // 捕获配置信息记录
    
    // 捕获图片
    const dataUrl = await toJpeg(slideInfo.element, config)
    
    // 转换为文件
    const response = await fetch(dataUrl)
    const blob = await response.blob()
    
    // 验证图片质量
    if (blob.size < 10000) { // 小于10KB可能有问题
      // 图片过小警告
      
      // 尝试PNG格式
      const pngDataUrl = await toPng(slideInfo.element, {
        ...config,
        quality: 1.0
      })
      
      const pngResponse = await fetch(pngDataUrl)
      const pngBlob = await pngResponse.blob()
      
      if (pngBlob.size > blob.size) {
        // PNG更大，使用PNG
        const file = new File([pngBlob], `slide_${String(slideInfo.slideIndex + 1).padStart(3, '0')}.png`, {
          type: 'image/png'
        })
        files.push(file)
        // 使用PNG格式
        continue
      }
    }
    
    const file = new File([blob], `slide_${String(slideInfo.slideIndex + 1).padStart(3, '0')}.jpg`, {
      type: 'image/jpeg'
    })
    
    files.push(file)
    // 页面完成处理
  }
  
  // 直接幻灯片捕获完成
  
  return files
}

/**
 * 调试幻灯片元素查找
 */
export const debugSlideElements = (): any => {
  // 调试幻灯片元素查找
  
  const slideElements = findSlideElements()
  
  const debugInfo = slideElements.map((slideInfo, index) => {
    const rect = slideInfo.element.getBoundingClientRect()
    return {
      index: index + 1,
      slideIndex: slideInfo.slideIndex + 1,
      id: slideInfo.slideId,
      element: slideInfo.element,
      size: { width: rect.width, height: rect.height },
      position: { x: rect.x, y: rect.y },
      visible: rect.width > 0 && rect.height > 0,
      className: slideInfo.element.className
    }
  })
  
  // 额外调试信息
  const allPossible = document.querySelectorAll('*[class*="slide"], *[class*="canvas"], *[class*="thumbnail"]')
  const additionalInfo = Array.from(allPossible)
    .filter(el => el instanceof HTMLElement && el.offsetWidth > 50 && el.offsetHeight > 50)
    .map((el, i) => ({
      index: i + 1,
      tagName: (el as HTMLElement).tagName,
      className: (el as HTMLElement).className,
      size: `${(el as HTMLElement).offsetWidth}x${(el as HTMLElement).offsetHeight}`
    }))
  
  return {
    slideElements: debugInfo,
    additionalElements: additionalInfo
  }
}
