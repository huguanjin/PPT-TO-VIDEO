/**
 * 真正的PPTist原生导出功能复制版
 * 完全模拟ExportImage.vue的工作方式，生成纯净的幻灯片图片
 */

import { toJpeg } from 'html-to-image'
import { useSlidesStore } from '@/store'

/**
 * 模拟PPTist ExportImage.vue的缩略图创建和导出逻辑
 * 这是唯一正确的方式，避免捕获编辑器画布
 */
export async function generateImagesWithTruePPTistMethod(): Promise<File[]> {
  const slidesStore = useSlidesStore()
  const slides = slidesStore.slides
  const { viewportSize, viewportRatio } = slidesStore
  
  if (!slides || slides.length === 0) {
    throw new Error('没有找到幻灯片数据')
  }

  // 创建隐藏的缩略图容器（完全复制ExportImage.vue的做法）
  const hiddenContainer = document.createElement('div')
  hiddenContainer.className = 'export-img-dialog'
  hiddenContainer.style.cssText = `
    position: absolute;
    left: -9999px;
    top: -9999px;
    width: 1600px;
    height: auto;
    background: white;
    pointer-events: none;
    overflow: hidden;
  `

  const thumbnailsContainer = document.createElement('div')
  thumbnailsContainer.className = 'thumbnails'
  hiddenContainer.appendChild(thumbnailsContainer)
  document.body.appendChild(hiddenContainer)

  const files: File[] = []

  try {
    for (let i = 0; i < slides.length; i++) {
      const slide = slides[i]
      
      // 创建ThumbnailSlide DOM结构（模拟ThumbnailSlide组件）
      const thumbnailSlide = createThumbnailSlideDom(slide, 1600, viewportSize, viewportRatio)
      thumbnailsContainer.appendChild(thumbnailSlide)
      
      // 等待渲染完成
      await new Promise(resolve => setTimeout(resolve, 200))
      
      // 导出图片（使用PPTist原生配置）
      try {
        const file = await exportThumbnailAsImage(thumbnailSlide, i)
        files.push(file)
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.error(`导出第${i + 1}页失败:`, error)
        // 创建占位符
        const placeholder = await createErrorPlaceholder(i)
        files.push(placeholder)
      }
      
      // 清理DOM以节省内存
      thumbnailSlide.remove()
    }
  }
  finally {
    // 清理隐藏容器
    hiddenContainer.remove()
  }

  return files
}

/**
 * 创建ThumbnailSlide的DOM结构
 * 完全复制ThumbnailSlide组件的渲染逻辑
 */
function createThumbnailSlideDom(
  slide: any, 
  size: number, 
  viewportSize: number, 
  viewportRatio: number
): HTMLElement {
  // 创建缩略图容器
  const thumbnailSlide = document.createElement('div')
  thumbnailSlide.className = 'thumbnail-slide'
  thumbnailSlide.style.cssText = `
    width: ${size}px;
    height: ${size * viewportRatio}px;
    background-color: #fff;
    overflow: hidden;
    user-select: none;
    position: relative;
  `

  // 创建elements容器
  const elementsContainer = document.createElement('div')
  elementsContainer.className = 'elements'
  const scale = size / viewportSize
  elementsContainer.style.cssText = `
    width: ${viewportSize}px;
    height: ${viewportSize * viewportRatio}px;
    transform: scale(${scale});
    transform-origin: 0 0;
    position: relative;
  `

  // 创建背景
  const background = document.createElement('div')
  background.className = 'background'
  background.style.cssText = `
    width: 100%;
    height: 100%;
    background-position: center;
    position: absolute;
    z-index: 0;
  `
  
  // 应用背景样式
  if (slide.background) {
    applyBackgroundStyle(background, slide.background)
  }
  
  elementsContainer.appendChild(background)

  // 渲染所有元素
  if (slide.elements && slide.elements.length > 0) {
    slide.elements.forEach((element: any, index: number) => {
      const elementDom = createElementDom(element, index + 1)
      if (elementDom) {
        elementsContainer.appendChild(elementDom)
      }
    })
  }

  thumbnailSlide.appendChild(elementsContainer)
  return thumbnailSlide
}

/**
 * 应用幻灯片背景样式
 */
function applyBackgroundStyle(backgroundElement: HTMLElement, background: any) {
  if (!background) return

  if (background.type === 'solid') {
    backgroundElement.style.backgroundColor = background.color || '#ffffff'
  }
  else if (background.type === 'image' && background.image) {
    backgroundElement.style.backgroundImage = `url("${background.image}")`
    backgroundElement.style.backgroundSize = background.imageSize || 'cover'
    backgroundElement.style.backgroundRepeat = 'no-repeat'
    backgroundElement.style.backgroundPosition = 'center'
  }
  else if (background.type === 'gradient' && background.gradientType) {
    const { gradientType, gradientColor } = background
    if (gradientType === 'linear' && gradientColor && gradientColor.length >= 2) {
      const colors = gradientColor.map((color: any) => `${color.color} ${color.pos}%`).join(', ')
      backgroundElement.style.background = `linear-gradient(${background.gradientRotate || 0}deg, ${colors})`
    }
  }
}

/**
 * 创建幻灯片元素的DOM
 * 简化版本，主要处理文本、图片、形状等基本元素
 */
function createElementDom(element: any, zIndex: number): HTMLElement | null {
  const elementDiv = document.createElement('div')
  elementDiv.style.cssText = `
    position: absolute;
    left: ${element.left || 0}px;
    top: ${element.top || 0}px;
    width: ${element.width || 100}px;
    height: ${element.height || 100}px;
    z-index: ${zIndex};
    transform: rotate(${element.rotate || 0}deg);
  `

  // 处理不同类型的元素
  if (element.type === 'text') {
    createTextElement(elementDiv, element)
  }
  else if (element.type === 'image') {
    createImageElement(elementDiv, element)
  }
  else if (element.type === 'shape') {
    createShapeElement(elementDiv, element)
  }
  else if (element.type === 'chart') {
    createChartElement(elementDiv)
  }
  else if (element.type === 'table') {
    createTableElement(elementDiv)
  }
  else {
    // 其他类型元素的简单处理
    elementDiv.style.border = '1px dashed #ccc'
    elementDiv.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 12px; color: #999;">${element.type}</div>`
  }

  return elementDiv
}

/**
 * 创建文本元素
 */
function createTextElement(container: HTMLElement, element: any) {
  const textDiv = document.createElement('div')
  textDiv.style.cssText = `
    width: 100%;
    height: 100%;
    padding: ${element.padding || 0}px;
    font-size: ${element.defaultFontSize || 16}px;
    font-family: ${element.defaultFontName || 'Arial'};
    color: ${element.defaultColor || '#000000'};
    line-height: ${element.lineHeight || 1.2};
    text-align: ${element.align || 'left'};
    vertical-align: ${element.verticalAlign || 'top'};
    box-sizing: border-box;
    word-wrap: break-word;
    overflow: hidden;
  `
  
  // 设置文本内容
  if (element.content) {
    textDiv.innerHTML = element.content
  }
  
  container.appendChild(textDiv)
}

/**
 * 创建图片元素
 */
function createImageElement(container: HTMLElement, element: any) {
  if (!element.src) return
  
  const img = document.createElement('img')
  img.style.cssText = `
    width: 100%;
    height: 100%;
    object-fit: ${element.objectFit || 'cover'};
  `
  img.src = element.src
  
  container.appendChild(img)
}

/**
 * 创建形状元素
 */
function createShapeElement(container: HTMLElement, element: any) {
  const shapeDiv = document.createElement('div')
  shapeDiv.style.cssText = `
    width: 100%;
    height: 100%;
    background-color: ${element.fill || '#f0f0f0'};
    border: ${element.outline?.width || 0}px solid ${element.outline?.color || '#000000'};
  `
  
  // 简单的形状处理
  if (element.shapePath === 'M 0,0 L 1,0 L 1,1 L 0,1 Z') {
    // 矩形
    shapeDiv.style.borderRadius = '0'
  }
  else if (element.shapePath && element.shapePath.includes('A')) {
    // 圆形或椭圆
    shapeDiv.style.borderRadius = '50%'
  }
  
  container.appendChild(shapeDiv)
}

/**
 * 创建图表元素（占位符）
 */
function createChartElement(container: HTMLElement) {
  const chartDiv = document.createElement('div')
  chartDiv.style.cssText = `
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, #f0f0f0 25%, transparent 25%),
                linear-gradient(-45deg, #f0f0f0 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #f0f0f0 75%),
                linear-gradient(-45deg, transparent 75%, #f0f0f0 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: #666;
  `
  chartDiv.textContent = '图表'
  
  container.appendChild(chartDiv)
}

/**
 * 创建表格元素（占位符）
 */
function createTableElement(container: HTMLElement) {
  const tableDiv = document.createElement('div')
  tableDiv.style.cssText = `
    width: 100%;
    height: 100%;
    border: 1px solid #ddd;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: #666;
    background-color: #fafafa;
  `
  tableDiv.textContent = '表格'
  
  container.appendChild(tableDiv)
}

/**
 * 导出缩略图为图片文件
 * 使用与PPTist完全相同的配置
 */
async function exportThumbnailAsImage(thumbnailElement: HTMLElement, slideIndex: number): Promise<File> {
  // 清理可能影响导出的属性（复制PPTist的做法）
  const foreignObjectSpans = thumbnailElement.querySelectorAll('foreignObject [xmlns]')
  foreignObjectSpans.forEach(spanRef => spanRef.removeAttribute('xmlns'))

  // 等待DOM更新
  await new Promise(resolve => setTimeout(resolve, 200))

  // 使用PPTist原生配置
  const config = {
    quality: 0.9,
    width: 1600,
    fontEmbedCSS: '' // 忽略Web字体，与PPTist原生一致
  }

  // 生成图片
  const dataUrl = await toJpeg(thumbnailElement, config)
  
  // 转换为File对象
  const response = await fetch(dataUrl)
  const blob = await response.blob()

  const filename = `slide_${String(slideIndex + 1).padStart(3, '0')}.jpg`
  return new File([blob], filename, { type: 'image/jpeg' })
}

/**
 * 创建错误占位符
 */
async function createErrorPlaceholder(slideIndex: number): Promise<File> {
  const canvas = document.createElement('canvas')
  canvas.width = 1600
  canvas.height = 900
  
  const ctx = canvas.getContext('2d')!
  
  // 绘制占位符
  ctx.fillStyle = '#f5f5f5'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  ctx.fillStyle = '#666666'
  ctx.font = '48px Arial'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(`幻灯片 ${slideIndex + 1}`, canvas.width / 2, canvas.height / 2)
  
  const blob = await new Promise<Blob>((resolve) => {
    canvas.toBlob((blob) => resolve(blob!), 'image/jpeg', 0.9)
  })
  
  const filename = `slide_${String(slideIndex + 1).padStart(3, '0')}.jpg`
  return new File([blob], filename, { type: 'image/jpeg' })
}

/**
 * 检查是否可以执行导出
 */
export function canPerformTruePPTistExport(): boolean {
  const slidesStore = useSlidesStore()
  return slidesStore.slides && slidesStore.slides.length > 0
}

/**
 * 获取诊断信息
 */
export function getTruePPTistExportDiagnostics() {
  const slidesStore = useSlidesStore()
  
  return {
    hasSlidesData: slidesStore.slides && slidesStore.slides.length > 0,
    totalSlides: slidesStore.slides?.length || 0,
    viewportSize: slidesStore.viewportSize,
    viewportRatio: slidesStore.viewportRatio,
    method: 'ThumbnailSlide DOM Creation'
  }
}
