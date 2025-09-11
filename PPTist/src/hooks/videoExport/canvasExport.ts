/**
 * Canvas图片导出功能
 * 直接使用canvas将幻灯片转换为图片，避免依赖PPTist导出对话框
 */
import type { Slide } from '@/types/slides'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'

export interface CanvasExportOptions {
  width?: number
  height?: number
  quality?: number
  format?: 'jpeg' | 'png'
}

/**
 * 将幻灯片转换为Canvas图片
 */
export const generateCanvasImages = async (
  slides?: Slide[],
  options: CanvasExportOptions = {}
): Promise<File[]> => {
  const {
    width = 1920,
    height = 1080,
    quality = 0.9,
    format = 'jpeg'
  } = options

  try {
    // 如果没有传入slides，从store获取
    if (!slides) {
      const slidesStore = useSlidesStore()
      const { slides: storeSlides } = storeToRefs(slidesStore)
      slides = storeSlides.value
    }

    if (!slides || slides.length === 0) {
      throw new Error('没有找到幻灯片数据')
    }

    const imageFiles: File[] = []

    for (let i = 0; i < slides.length; i++) {
      const slide = slides[i]
      
      // 创建canvas
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')!

      // 设置背景
      ctx.fillStyle = slide.background?.color || '#ffffff'
      ctx.fillRect(0, 0, width, height)

      // 渲染幻灯片内容
      await renderSlideToCanvas(slide, ctx, width, height)

      // 转换为Blob
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((blob) => {
          resolve(blob!)
        }, `image/${format}`, quality)
      })

      // 创建File对象
      const filename = `slide_${String(i + 1).padStart(3, '0')}.${format}`
      const file = new File([blob], filename, { type: `image/${format}` })
      imageFiles.push(file)

      // 显示进度
      // eslint-disable-next-line no-console
      console.log(`✅ 生成第 ${i + 1}/${slides.length} 张图片: ${filename}`)
    }

    // eslint-disable-next-line no-console
    console.log(`🎉 Canvas图片生成完成，共生成 ${imageFiles.length} 张图片`)
    return imageFiles
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('❌ Canvas图片生成失败:', error)
    throw error
  }
}

/**
 * 将幻灯片渲染到Canvas
 */
const renderSlideToCanvas = async (
  slide: Slide,
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number
): Promise<void> => {
  try {
    // 如果有背景图片
    if (slide.background?.image) {
      const img = new Image()
      img.crossOrigin = 'anonymous'
      
      await new Promise((resolve, reject) => {
        img.onload = () => {
          ctx.drawImage(img, 0, 0, width, height)
          resolve(void 0)
        }
        img.onerror = reject
        img.src = slide.background?.image?.src || ''
      })
    }

    // 渲染元素
    if (slide.elements && slide.elements.length > 0) {
      for (const element of slide.elements) {
        await renderElementToCanvas(element, ctx, width, height)
      }
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('渲染幻灯片到Canvas时出错:', error)
    // 即使渲染失败，也继续生成基础背景图片
  }
}

/**
 * 将元素渲染到Canvas
 */
const renderElementToCanvas = async (
  element: any,
  ctx: CanvasRenderingContext2D,
  slideWidth: number,
  slideHeight: number
): Promise<void> => {
  try {
    const { left = 0, top = 0, width = 100, height = 100 } = element

    // 计算实际坐标
    const x = (left / 100) * slideWidth
    const y = (top / 100) * slideHeight
    const w = (width / 100) * slideWidth
    const h = (height / 100) * slideHeight

    switch (element.type) {
      case 'text':
        renderTextElement(element, ctx, x, y, w)
        break
      case 'image':
        await renderImageElement(element, ctx, x, y, w, h)
        break
      case 'shape':
        renderShapeElement(element, ctx, x, y, w, h)
        break
      default:
        // 未知类型，绘制占位符
        ctx.strokeStyle = '#cccccc'
        ctx.strokeRect(x, y, w, h)
        break
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('渲染元素时出错:', error)
  }
}

/**
 * 渲染文本元素
 */
const renderTextElement = (
  element: any,
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number
  // height: number // 暂时不需要
): void => {
  try {
    const {
      content = '',
      fontSize = 24,
      fontName = 'Arial',
      color = '#000000',
      bold = false,
      italic = false
    } = element

    // 设置字体
    let fontStyle = ''
    if (italic) fontStyle += 'italic '
    if (bold) fontStyle += 'bold '
    ctx.font = `${fontStyle}${fontSize}px ${fontName}`
    ctx.fillStyle = color
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'

    // 简单文本渲染（不处理复杂排版）
    const text = typeof content === 'string' ? content : JSON.stringify(content)
    ctx.fillText(text, x, y, width)
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('渲染文本元素时出错:', error)
  }
}

/**
 * 渲染图片元素
 */
const renderImageElement = async (
  element: any,
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number
): Promise<void> => {
  try {
    const { src } = element
    if (!src) return

    const img = new Image()
    img.crossOrigin = 'anonymous'

    await new Promise<void>((resolve) => {
      img.onload = () => {
        ctx.drawImage(img, x, y, width, height)
        resolve()
      }
      img.onerror = () => {
        // 如果图片加载失败，绘制占位符
        ctx.strokeStyle = '#cccccc'
        ctx.strokeRect(x, y, width, height)
        ctx.fillStyle = '#f0f0f0'
        ctx.fillRect(x, y, width, height)
        resolve()
      }
      img.src = src
    })
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('渲染图片元素时出错:', error)
  }
}

/**
 * 渲染形状元素
 */
const renderShapeElement = (
  element: any,
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number
): void => {
  try {
    const { fill = '#ffffff', stroke = '#000000', strokeWidth = 1 } = element

    ctx.fillStyle = fill
    ctx.strokeStyle = stroke
    ctx.lineWidth = strokeWidth

    // 简单矩形渲染
    ctx.fillRect(x, y, width, height)
    if (strokeWidth > 0) {
      ctx.strokeRect(x, y, width, height)
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('渲染形状元素时出错:', error)
  }
}

/**
 * 从现有幻灯片生成简化图片
 */
export const generateSimplifiedImages = async (): Promise<File[]> => {
  try {
    const slidesStore = useSlidesStore()
    const { slides } = storeToRefs(slidesStore)

    if (!slides.value || slides.value.length === 0) {
      throw new Error('没有找到幻灯片数据')
    }

    // eslint-disable-next-line no-console
    console.log(`🎯 开始生成 ${slides.value.length} 张简化图片...`)

    // 使用Canvas生成图片
    const images = await generateCanvasImages(slides.value, {
      width: 1920,
      height: 1080,
      quality: 0.8,
      format: 'jpeg'
    })

    // eslint-disable-next-line no-console
    console.log(`✅ 简化图片生成完成，共 ${images.length} 张`)
    return images
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('❌ 简化图片生成失败:', error)
    throw error
  }
}
