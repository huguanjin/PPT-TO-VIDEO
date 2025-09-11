/**
 * 图片生成相关函数
 * 包含多种图片生成策略和方法
 */
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'
import { toPng, toJpeg } from 'html-to-image'
import html2canvas from 'html2canvas'
import { saveAs } from 'file-saver'

// 导入修复版导出功能（最高优先级）
import { generateImagesWithFixedExport, canPerformFixedExport, getExportDiagnostics } from './fixedSlideExport'

// 导入真正的PPTist原生导出功能（最新最优方案）
import { generateImagesWithTruePPTistMethod, canPerformTruePPTistExport, getTruePPTistExportDiagnostics } from './truePPTistExport'

// 导入其他PPTist导出功能  
import { smartPPTistNativeExport } from './pptistNativeExport'
import { generateImagesWithEnhancedPPTist, inspectExportDialog } from './enhancedPPTistExport'
import { generateImagesWithCorrectScaling, debugScalingIssue } from './scalingFixExport'
import { executeNativeExportWorkflow } from './nativeExportFixed'

// 导入新的直接幻灯片捕获解决方案（第二优先级）
import { generateImagesFromDirectSlideCaptureFixed, debugSlideElements } from './directSlideCapture'

/**
 * 使用真正的PPTist原生导出方法（最新最优方案）
 * 完全复制PPTist的ThumbnailSlide导出逻辑，解决左上角1/4位置问题
 */
export const generateImagesWithTruePPTistQuality = async (): Promise<File[]> => {
  try {
    // 检查是否可以执行真正的PPTist导出
    if (!canPerformTruePPTistExport()) {
      throw new Error('无法执行PPTist原生导出：缺少必要的幻灯片数据')
    }

    // 获取诊断信息
    const diagnostics = getTruePPTistExportDiagnostics()
    // eslint-disable-next-line no-console
    console.log('🎯 真正PPTist导出诊断信息:', diagnostics)

    // 执行导出
    // eslint-disable-next-line no-console
    console.log('🚀 开始执行真正的PPTist原生导出...')
    const files = await generateImagesWithTruePPTistMethod()
    
    if (!files || files.length === 0) {
      throw new Error('PPTist原生导出返回了空结果')
    }

    // eslint-disable-next-line no-console
    console.log(`✅ 真正PPTist导出成功! 生成了 ${files.length} 个图片文件`)
    return files

  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('❌ 真正PPTist导出失败:', error)
    throw error
  }
}

/**
 * 使用修复版幻灯片导出功能（备用方案）
 * 解决左上角1/4位置问题，确保与PPTist前端导出质量一致
 */
export const generateImagesWithFixedQuality = async (): Promise<File[]> => {
  try {
    // 检查是否可以执行修复版导出
    if (!canPerformFixedExport()) {
      throw new Error('当前环境不支持修复版导出')
    }
    
    // eslint-disable-next-line no-console
    console.log('🎯 使用修复版导出功能...')
    const diagnostics = getExportDiagnostics()
    // eslint-disable-next-line no-console
    console.log('📊 导出环境诊断:', diagnostics)
    
    const files = await generateImagesWithFixedExport()
    return files
  }
  catch (error) {
    throw new Error(`修复版导出失败: ${(error as Error).message}`)
  }
}

/**
 * 使用直接幻灯片捕获功能（新增 - 最高优先级方法）
 * 解决蓝色背景问题，直接捕获实际幻灯片内容
 */
export const generateImagesWithDirectCapture = async (): Promise<File[]> => {
  try {
    const files = await generateImagesFromDirectSlideCaptureFixed()
    return files
  }
  catch (error) {
    throw new Error(`直接捕获失败: ${(error as Error).message}`)
  }
}

/**
 * 使用PPTist原生导出功能（推荐方法 - 多层回退策略）
 */
export const generateImagesWithPPTistNative = async (): Promise<File[]> => {
  try {
    // 优先级1: 修复版导出（解决左上角1/4问题）
    try {
      // eslint-disable-next-line no-console
      console.log('🎯 尝试使用修复版导出...')
      const files = await generateImagesWithFixedQuality()
      // eslint-disable-next-line no-console
      console.log(`✅ 修复版导出成功，生成了 ${files.length} 个高质量图片文件`)
      return files
    }
    catch (fixedError) {
      // eslint-disable-next-line no-console
      console.warn('⚠️ 修复版导出失败，尝试直接捕获...', fixedError)
    }

    // 优先级2: 直接幻灯片捕获
    try {
      const files = await generateImagesWithDirectCapture()
      return files
    }
    catch (directError) {
      // 直接捕获失败，继续使用原有逻辑
      // eslint-disable-next-line no-console
      console.warn('⚠️ 直接捕获失败，尝试原生导出...', directError)
    }
    
    // 优先级3: PPTist原生导出
    // eslint-disable-next-line no-console
    console.log('🎨 尝试使用PPTist原生导出功能...')
    
    // 首先尝试新的原生导出修复版本（直接调用PPTist原生逻辑）
    const projectName = `pptist_${Date.now()}`
    const result = await executeNativeExportWorkflow(projectName)
    
    if (result.success) {
      // eslint-disable-next-line no-console
      console.log(`✅ PPTist原生导出成功: ${result.message}`)
      return result.files
    }
    
    // 优先级4: 缩放修复版（如果原生导出失败）
    // eslint-disable-next-line no-console
    console.warn(`⚠️ PPTist原生导出失败: ${result.message}，尝试缩放修复版...`)
    
    // 缩放修复版导出（解决左上角1/4问题）
    const files = await generateImagesWithCorrectScaling()
    
    // eslint-disable-next-line no-console
    console.log(`✅ 缩放修复版PPTist导出成功，生成了 ${files.length} 个图片文件`)
    
    return files
  } 
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('⚠️ 缩放修复版导出失败，尝试增强版...', error)
    
    try {
      // 回退到增强版导出
      const files = await generateImagesWithEnhancedPPTist()
      
      // eslint-disable-next-line no-console
      console.log(`✅ 增强版PPTist导出成功，生成了 ${files.length} 个图片文件`)
      
      return files
    }
    catch (enhancedError) {
      // eslint-disable-next-line no-console
      console.warn('⚠️ 增强版导出失败，尝试标准版...', enhancedError)
      
      try {
        // 最后回退到标准版导出
        const files = await smartPPTistNativeExport()
        
        // eslint-disable-next-line no-console
        console.log(`✅ 标准版PPTist导出成功，生成了 ${files.length} 个图片文件`)
        
        return files
      }
      catch (fallbackError) {
        // eslint-disable-next-line no-console
        console.error('❌ 所有PPTist导出方法都失败了:')
        // eslint-disable-next-line no-console
        console.error('缩放修复版错误:', error)
        // eslint-disable-next-line no-console
        console.error('增强版错误:', enhancedError)
        // eslint-disable-next-line no-console
        console.error('标准版错误:', fallbackError)
        
        throw new Error(`PPTist导出失败。

🔧 可能的解决方案：
1. 在PPTist界面点击"导出图片"按钮
2. 等待导出对话框完全加载显示所有缩略图
3. 保持对话框打开状态
4. 然后再执行视频导出功能

📋 错误详情：
- 缩放修复版: ${(error as Error).message}
- 增强版: ${(enhancedError as Error).message}  
- 标准版: ${(fallbackError as Error).message}`)
      }
    }
  }
}

/**
 * 调试直接幻灯片捕获功能（新增）
 * 帮助诊断幻灯片元素识别问题
 */
export const debugDirectSlideCapture = (): any => {
  return debugSlideElements()
}

/**
 * 调试PPTist导出对话框 - 帮助诊断问题
 */
export const debugPPTistExportDialog = (): void => {
  // eslint-disable-next-line no-console
  console.log('🔧 开始调试PPTist导出对话框...')
  
  // 使用增强版检查器
  inspectExportDialog()
  
  // 额外的诊断信息
  const dialog = document.querySelector('.export-img-dialog')
  if (dialog) {
    // eslint-disable-next-line no-console
    console.log('📋 额外诊断信息:')
    // eslint-disable-next-line no-console
    console.log('对话框类名:', dialog.className)
    // eslint-disable-next-line no-console
    console.log('对话框子元素数量:', dialog.children.length)
    
    // 列出所有子元素
    Array.from(dialog.children).forEach((child, index) => {
      // eslint-disable-next-line no-console
      console.log(`子元素${index + 1}: ${child.tagName}.${child.className}`)
    })
  }
}

/**
 * 专门调试缩放问题 - 解决左上角1/4区域问题
 */
export const debugScalingProblem = (): void => {
  // eslint-disable-next-line no-console
  console.log('🔍 专门调试缩放问题（左上角1/4区域问题）...')
  
  // 使用缩放调试功能
  debugScalingIssue()
  
  // 额外的缩放相关检查
  const dialog = document.querySelector('.export-img-dialog')
  if (dialog) {
    const thumbnails = dialog.querySelectorAll('.thumbnail')
    
    // eslint-disable-next-line no-console
    console.log('\n🎯 缩放问题分析:')
    // eslint-disable-next-line no-console
    console.log('问题描述: 导出图片内容被缩小到左上角约1/4区域')
    // eslint-disable-next-line no-console
    console.log('预期效果: 内容应该铺满整个画布')
    
    if (thumbnails.length > 0) {
      const first = thumbnails[0] as HTMLElement
      const rect = first.getBoundingClientRect()
      
      // eslint-disable-next-line no-console
      console.log('\n📐 关键尺寸信息:')
      // eslint-disable-next-line no-console
      console.log(`缩略图显示尺寸: ${rect.width}x${rect.height}`)
      // eslint-disable-next-line no-console
      console.log(`目标输出尺寸: 1920x1080`)
      // eslint-disable-next-line no-console
      console.log(`缩放比例计算: ${1920 / rect.width}x (宽度), ${1080 / rect.height}x (高度)`)
      
      // eslint-disable-next-line no-console
      console.log('\n💡 解决策略:')
      // eslint-disable-next-line no-console
      console.log('1. 使用transform: scale()正确缩放元素')
      // eslint-disable-next-line no-console
      console.log('2. 设置正确的输出尺寸')
      // eslint-disable-next-line no-console
      console.log('3. 调整transformOrigin确保从左上角开始缩放')
    }
  }
}

/**
 * 使用画布viewport元素生成高质量图片（备选方法）
 */
export const generateImagesFromExistingThumbnails = async (): Promise<File[]> => {
  // 首先尝试PPTist原生导出
  try {
    return await generateImagesWithPPTistNative()
  } 
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('⚠️ PPTist原生导出失败，使用备选方法...')
  }

  // 首先尝试查找主画布的viewport元素（这是最佳选择）
  let viewportElement = document.querySelector('.canvas .viewport') as HTMLElement
  
  if (!viewportElement) {
    // 备选：查找其他可能的viewport元素
    const viewportSelectors = ['.viewport', '.slide-canvas', '[data-slide-canvas]']
    for (const selector of viewportSelectors) {
      viewportElement = document.querySelector(selector) as HTMLElement
      if (viewportElement) break
    }
  }
  
  if (viewportElement) {
    // eslint-disable-next-line no-console
    console.log('🎯 使用viewport元素生成高质量图片，元素信息:')
    // eslint-disable-next-line no-console
    console.log('   - 尺寸:', viewportElement.offsetWidth, 'x', viewportElement.offsetHeight)
    // eslint-disable-next-line no-console
    console.log('   - 类名:', viewportElement.className)
    // eslint-disable-next-line no-console
    console.log('   - 选择器:', viewportElement.tagName.toLowerCase() + (viewportElement.id ? '#' + viewportElement.id : '') + (viewportElement.className ? '.' + viewportElement.className.split(' ').join('.') : ''))
    return await generateImagesFromViewport(viewportElement)
  }

  // 如果没有找到viewport，尝试查找大尺寸的缩略图
  let thumbnailElements = document.querySelectorAll('.thumbnail-slide')
  
  // eslint-disable-next-line no-console
  console.log(`🔍 找到 ${thumbnailElements.length} 个现有的 thumbnail-slide 元素`)
  
  if (thumbnailElements.length === 0) {
    // 如果没有找到，尝试查找缩略图列表
    const thumbnailList = document.querySelector('.thumbnail-list')
    if (thumbnailList) {
      thumbnailElements = thumbnailList.querySelectorAll('.thumbnail')
      // eslint-disable-next-line no-console
      console.log(`📋 在缩略图列表中找到 ${thumbnailElements.length} 个缩略图`)
    }
  }

  // 如果还是没有找到，尝试查找ExportImage对话框中的缩略图
  if (thumbnailElements.length === 0) {
    const exportDialog = document.querySelector('.export-img-dialog')
    if (exportDialog) {
      thumbnailElements = exportDialog.querySelectorAll('.thumbnail')
      // eslint-disable-next-line no-console
      console.log(`🎭 在导出对话框中找到 ${thumbnailElements.length} 个缩略图`)
    }
  }
  
  if (thumbnailElements.length === 0) {
    // eslint-disable-next-line no-console
    console.log('⚠️ 未找到任何缩略图元素，尝试使用原生导出方法')
    return await generateImagesWithExportDialog()
  }

  // 检查缩略图尺寸，如果太小则创建新的大尺寸元素
  const firstThumbnail = thumbnailElements[0] as HTMLElement
  const thumbnailRect = firstThumbnail.getBoundingClientRect()
  
  if (thumbnailRect.width < 800) {
    // eslint-disable-next-line no-console
    console.log('⚠️ 缩略图尺寸太小，创建大尺寸ThumbnailSlide元素')
    return await generateImagesWithLargeThumbnails()
  }

  // 使用现有的大尺寸缩略图
  return await generateImagesFromThumbnailElements(thumbnailElements)
}

/**
 * 从viewport元素生成图片（最优质量）
 */
const generateImagesFromViewport = async (viewportElement: HTMLElement): Promise<File[]> => {
  const slidesStore = useSlidesStore()
  const { slides, viewportSize, viewportRatio } = storeToRefs(slidesStore)
  const files: File[] = []

  // 计算正确的导出尺寸，基于PPTist的画布设置
  const baseWidth = viewportSize.value || 1000
  const baseHeight = Math.round(baseWidth * viewportRatio.value)
  
  // 计算高质量导出尺寸（保持比例的情况下尽可能大）
  const maxExportSize = 1920
  let exportWidth: number
  let exportHeight: number
  
  if (baseWidth >= baseHeight) {
    // 横向布局
    exportWidth = maxExportSize
    exportHeight = Math.round(maxExportSize * viewportRatio.value)
  } 
  else {
    // 纵向布局
    exportHeight = maxExportSize
    exportWidth = Math.round(maxExportSize / viewportRatio.value)
  }

  // eslint-disable-next-line no-console
  console.log(`📐 PPTist画布设置: ${baseWidth}×${baseHeight} (比例: ${viewportRatio.value.toFixed(3)})`)
  // eslint-disable-next-line no-console
  console.log(`📸 导出尺寸: ${exportWidth}×${exportHeight}`)

  // 保存当前幻灯片索引
  const originalSlideIndex = slidesStore.slideIndex

  for (let i = 0; i < slides.value.length; i++) {
    try {
      // 切换到对应的幻灯片
      slidesStore.updateSlideIndex(i)
      
      // 等待渲染完成
      await new Promise(resolve => setTimeout(resolve, 300))

      // eslint-disable-next-line no-console
      console.log(`📸 从viewport生成第 ${i + 1} 页图片...`)

      // 等待图片加载完成
      const images = viewportElement.querySelectorAll('img')
      for (const img of images) {
        if (!img.complete) {
          await new Promise((resolve) => {
            const timeout = setTimeout(resolve, 2000)
            img.onload = () => {
              clearTimeout(timeout)
              resolve(null)
            }
            img.onerror = () => {
              clearTimeout(timeout)
              resolve(null)
            }
          })
        }
      }

      // 使用toJpeg生成图片，使用正确的尺寸比例
      const dataUrl = await toJpeg(viewportElement, {
        quality: 0.9,
        width: exportWidth,
        height: exportHeight,
        backgroundColor: '#ffffff',
        style: {
          transform: 'scale(1)',
          transformOrigin: 'top left',
        },
        pixelRatio: 1,
      })

      // 转换为Blob并创建File
      const response = await fetch(dataUrl)
      const blob = await response.blob()

      const file = new File([blob], `slide_${String(i + 1).padStart(3, '0')}.jpg`, {
        type: 'image/jpeg'
      })

      files.push(file)
      
      // eslint-disable-next-line no-console
      console.log(`✅ 第 ${i + 1} 页图片生成成功: ${(blob.size / 1024).toFixed(1)}KB`)

    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`❌ 生成第 ${i + 1} 页图片失败:`, error)
      throw error
    }
  }

  // 恢复原来的幻灯片索引
  slidesStore.updateSlideIndex(originalSlideIndex)
  return files
}

/**
 * 创建大尺寸ThumbnailSlide元素生成图片（模拟PPTist原生导出）
 */
const generateImagesWithLargeThumbnails = async (): Promise<File[]> => {
  const slidesStore = useSlidesStore()
  const { slides, viewportSize, viewportRatio } = storeToRefs(slidesStore)
  const files: File[] = []

  // 计算正确的导出尺寸，基于PPTist的画布设置
  const baseWidth = viewportSize.value || 1000
  const baseHeight = Math.round(baseWidth * viewportRatio.value)
  
  // 计算高质量导出尺寸（保持比例的情况下尽可能大）
  const maxExportSize = 1920
  let exportWidth: number
  let exportHeight: number
  
  if (baseWidth >= baseHeight) {
    // 横向布局
    exportWidth = maxExportSize
    exportHeight = Math.round(maxExportSize * viewportRatio.value)
  } 
  else {
    // 纵向布局
    exportHeight = maxExportSize
    exportWidth = Math.round(maxExportSize / viewportRatio.value)
  }

  // eslint-disable-next-line no-console
  console.log(`📐 PPTist画布设置: ${baseWidth}×${baseHeight} (比例: ${viewportRatio.value.toFixed(3)})`)
  // eslint-disable-next-line no-console
  console.log(`📸 大尺寸缩略图导出尺寸: ${exportWidth}×${exportHeight}`)

  // 动态创建缩略图容器（模拟ExportImage.vue的做法）
  const tempContainer = document.createElement('div')
  tempContainer.style.cssText = `
    position: absolute;
    left: -9999px;
    top: -9999px;
    width: 1600px;
    background: white;
    pointer-events: none;
  `
  
  // 创建缩略图模拟容器
  const thumbnailsContainer = document.createElement('div')
  thumbnailsContainer.className = 'thumbnails'
  tempContainer.appendChild(thumbnailsContainer)
  document.body.appendChild(tempContainer)

  try {
    // 等待DOM渲染
    await new Promise(resolve => setTimeout(resolve, 100))

    // 为每个slide生成图片
    for (let i = 0; i < slides.value.length; i++) {
      const slide = slides.value[i]
      
      try {
        // eslint-disable-next-line no-console
        console.log(`📸 正在生成第 ${i + 1} 页大尺寸缩略图...`)

        // 创建单个缩略图元素
        const thumbnailElement = document.createElement('div')
        thumbnailElement.className = 'thumbnail-slide-large'
        thumbnailElement.style.cssText = `
          width: 1600px;
          height: ${Math.round(1600 * viewportRatio.value)}px;
          background: ${slide.background?.color || '#ffffff'};
          position: relative;
          overflow: hidden;
        `
        
        // 渲染slide内容（简化版）
        thumbnailElement.innerHTML = `
          <div class="slide-content" style="
            width: 100%;
            height: 100%;
            position: relative;
            background: ${slide.background?.color || '#ffffff'};
          ">
            <!-- 这里应该渲染slide的elements，但由于复杂性先使用基础方法 -->
          </div>
        `
        
        thumbnailsContainer.appendChild(thumbnailElement)

        // 等待渲染完成
        await new Promise(resolve => setTimeout(resolve, 200))

        // 使用toJpeg生成图片
        const dataUrl = await toJpeg(thumbnailElement, {
          quality: 0.9,
          width: exportWidth,
          height: exportHeight,
          backgroundColor: '#ffffff',
          pixelRatio: 1,
        })

        // 转换为Blob并创建File
        const response = await fetch(dataUrl)
        const blob = await response.blob()

        const file = new File([blob], `slide_${String(i + 1).padStart(3, '0')}.jpg`, {
          type: 'image/jpeg'
        })

        files.push(file)
        
        // eslint-disable-next-line no-console
        console.log(`✅ 第 ${i + 1} 页大尺寸缩略图生成成功: ${(blob.size / 1024).toFixed(1)}KB`)

        // 清理当前缩略图
        thumbnailsContainer.removeChild(thumbnailElement)

      } 
      catch (error) {
        // eslint-disable-next-line no-console
        console.error(`❌ 生成第 ${i + 1} 页大尺寸缩略图失败:`, error)
      }
    }

    return files

  } 
  finally {
    // 清理临时容器
    if (document.body.contains(tempContainer)) {
      document.body.removeChild(tempContainer)
    }
  }
}

/**
 * 从现有缩略图元素生成图片
 */
const generateImagesFromThumbnailElements = async (thumbnailElements: NodeListOf<Element>): Promise<File[]> => {
  const slidesStore = useSlidesStore()
  const { slides, viewportSize, viewportRatio } = storeToRefs(slidesStore)
  const files: File[] = []
  const totalSlides = Math.min(thumbnailElements.length, slides.value.length)

  // 计算正确的导出尺寸，基于PPTist的画布设置
  const baseWidth = viewportSize.value || 1000
  const baseHeight = Math.round(baseWidth * viewportRatio.value)
  
  // 计算高质量导出尺寸（保持比例的情况下尽可能大）
  const maxExportSize = 1920
  let exportWidth: number
  let exportHeight: number
  
  if (baseWidth >= baseHeight) {
    // 横向布局
    exportWidth = maxExportSize
    exportHeight = Math.round(maxExportSize * viewportRatio.value)
  } 
  else {
    // 纵向布局
    exportHeight = maxExportSize
    exportWidth = Math.round(maxExportSize / viewportRatio.value)
  }

  // eslint-disable-next-line no-console
  console.log(`📐 PPTist画布设置: ${baseWidth}×${baseHeight} (比例: ${viewportRatio.value.toFixed(3)})`)
  // eslint-disable-next-line no-console
  console.log(`📸 缩略图导出尺寸: ${exportWidth}×${exportHeight}`)

  for (let i = 0; i < totalSlides; i++) {
    const thumbnailElement = thumbnailElements[i] as HTMLElement
    
    try {
      // eslint-disable-next-line no-console
      console.log(`📸 从缩略图生成第 ${i + 1} 页图片...`)

      // 等待图片加载完成
      const images = thumbnailElement.querySelectorAll('img')
      for (const img of images) {
        if (!img.complete) {
          await new Promise((resolve) => {
            const timeout = setTimeout(resolve, 2000)
            img.onload = () => {
              clearTimeout(timeout)
              resolve(null)
            }
            img.onerror = () => {
              clearTimeout(timeout)
              resolve(null)
            }
          })
        }
      }

      // 使用toJpeg生成图片，使用正确的PPTist画布比例
      const dataUrl = await toJpeg(thumbnailElement, {
        quality: 0.9,
        width: exportWidth,
        height: exportHeight,
        backgroundColor: '#ffffff'
      })

      // 转换为Blob并创建File
      const response = await fetch(dataUrl)
      const blob = await response.blob()

      const file = new File([blob], `slide_${String(i + 1).padStart(3, '0')}.jpg`, {
        type: 'image/jpeg'
      })

      files.push(file)
      
      // eslint-disable-next-line no-console
      console.log(`✅ 第 ${i + 1} 页图片生成成功: ${(blob.size / 1024).toFixed(1)}KB`)

    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`❌ 生成第 ${i + 1} 页图片失败:`, error)
      throw error
    }
  }

  return files
}

/**
 * 智能图片生成 - 尝试使用ExportImage对话框中的ThumbnailSlide组件
 */
const generateImagesWithExportDialog = (): Promise<File[]> => {
  // eslint-disable-next-line no-console
  console.log('🎭 尝试使用ExportImage对话框方法生成图片')
  
  return new Promise((resolve) => {
    // 模拟用户触发导出图片功能
    // 这需要与PPTist的UI交互
    
    // 检查是否已经有导出对话框
    const exportDialog = document.querySelector('.export-img-dialog')
    
    if (!exportDialog) {
      // eslint-disable-next-line no-console
      console.log('⚠️ 未找到导出对话框，请先打开"导出图片"功能')
      // 返回一个提示用户的错误
      resolve([])
      return
    }
    
    // eslint-disable-next-line no-console
    console.log('✅ 找到导出对话框，开始使用其中的缩略图')
    
    // 查找对话框中的ThumbnailSlide组件
    const thumbnails = exportDialog.querySelectorAll('.thumbnail')
    
    if (thumbnails.length === 0) {
      // eslint-disable-next-line no-console
      console.log('⚠️ 导出对话框中没有找到缩略图，等待渲染...')
      
      // 等待一段时间后重试
      setTimeout(() => {
        const retryThumbnails = exportDialog!.querySelectorAll('.thumbnail')
        if (retryThumbnails.length > 0) {
          generateImagesFromThumbnailElements(retryThumbnails).then(resolve)
        } 
        else {
          // eslint-disable-next-line no-console
          console.log('❌ 仍未找到缩略图，使用备用方案')
          resolve([])
        }
      }, 1000)
      return
    }
    
    // 使用找到的缩略图
    generateImagesFromThumbnailElements(thumbnails).then(resolve)
  })
}

/**
 * 安全的图片生成函数，处理跨域和加载问题
 */
export const captureSlideImage = async (slideElement: HTMLElement, slideIndex: number): Promise<Blob> => {
  // 1. 预处理：等待所有图片加载
  const images = slideElement.querySelectorAll('img')
  // eslint-disable-next-line no-console
  console.log(`🖼️ 第 ${slideIndex + 1} 页包含 ${images.length} 个图片元素`)
  
  for (let i = 0; i < images.length; i++) {
    const img = images[i]
    if (!img.complete) {
      // eslint-disable-next-line no-console
      console.log(`⏳ 等待第 ${i + 1} 个图片加载...`)
      await new Promise((resolve) => {
        const timeout = setTimeout(() => {
          // eslint-disable-next-line no-console
          console.warn(`⚠️ 图片 ${i + 1} 加载超时`)
          resolve(null)
        }, 3000)
        
        img.onload = () => {
          clearTimeout(timeout)
          resolve(null)
        }
        img.onerror = () => {
          clearTimeout(timeout)
          // eslint-disable-next-line no-console
          console.warn(`❌ 图片 ${i + 1} 加载失败`)
          resolve(null)
        }
      })
    }
  }

  // 2. 尝试多种截图策略
  const strategies = [
    // 策略1：标准配置
    {
      name: '标准配置',
      options: {
        width: 1920,
        height: 1080,
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
        logging: false
      }
    },
    // 策略2：忽略跨域图片
    {
      name: '忽略跨域',
      options: {
        width: 1920,
        height: 1080,
        scale: 2,
        useCORS: false,
        allowTaint: false,
        backgroundColor: '#ffffff',
        logging: false,
        ignoreElements: (element: Element) => {
          // 忽略可能有问题的图片
          if (element.tagName === 'IMG') {
            const img = element as HTMLImageElement
            return !img.complete || img.src.startsWith('blob:') || img.src.startsWith('data:')
          }
          return false
        }
      }
    },
    // 策略3：最简配置
    {
      name: '最简配置',
      options: {
        backgroundColor: '#ffffff',
        logging: false
      }
    }
  ]

  for (const strategy of strategies) {
    try {
      // eslint-disable-next-line no-console
      console.log(`🎯 尝试策略: ${strategy.name}`)
      
      const canvas = await html2canvas(slideElement, strategy.options)
      
      // 检查生成的canvas是否有效
      if (canvas.width > 0 && canvas.height > 0) {
        const blob = await new Promise<Blob>((resolve) => {
          canvas.toBlob((blob) => {
            resolve(blob!)
          }, 'image/jpeg', 0.9)
        })
        
        // 检查生成的图片大小
        if (blob.size > 10000) { // 大于10KB认为是有效图片
          // eslint-disable-next-line no-console
          console.log(`✅ 策略 ${strategy.name} 成功，图片大小: ${blob.size} bytes`)
          return blob
        }
      }
      
      // eslint-disable-next-line no-console
      console.warn(`⚠️ 策略 ${strategy.name} 生成的图片无效`)
      
    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.warn(`⚠️ 策略 ${strategy.name} 失败:`, error)
    }
  }
  
  throw new Error(`所有截图策略都失败了`)
}

/**
 * 导出所有幻灯片为图片（用于本地下载）
 */
export const exportSlidesAsImages = async () => {
  const slidesStore = useSlidesStore()
  const { slides } = storeToRefs(slidesStore)
  
  // 尝试多种可能的选择器，与generateImageFiles保持一致
  const selectors = [
    '.viewport', // PPTist的主要视口
    '.slide-canvas', // 原始选择器
    '.canvas .viewport', // Canvas组件中的viewport
    '[data-slide-canvas]',
    '.slide-content',
    '.screen-slide'
  ]
  
  let slideElements: NodeListOf<Element> | null = null
  let usedSelector = ''
  
  for (const selector of selectors) {
    const elements = document.querySelectorAll(selector)
    if (elements.length > 0) {
      slideElements = elements
      usedSelector = selector
      break
    }
  }
  
  if (!slideElements || slideElements.length === 0) {
    throw new Error('未找到幻灯片元素，请确保在编辑器页面执行导出操作')
  }
  
  // eslint-disable-next-line no-console
  console.log(`本地导出使用选择器: ${usedSelector}，找到 ${slideElements.length} 个元素`)
  
  // 如果找到的是单个viewport，我们需要切换幻灯片来导出所有页面
  if (usedSelector === '.viewport' || usedSelector === '.canvas .viewport') {
    const totalSlides = slides.value.length
    const originalSlideIndex = slidesStore.slideIndex // 保存当前幻灯片索引
    
    for (let i = 0; i < totalSlides; i++) {
      try {
        // 切换到对应的幻灯片
        slidesStore.updateSlideIndex(i)
        
        // 等待渲染完成
        await new Promise(resolve => setTimeout(resolve, 500))

        const slideElement = slideElements[0] as HTMLElement
        
        // 转换为PNG图片
        const dataUrl = await toPng(slideElement, {
          width: 1920,
          height: 1080,
          style: {
            transform: 'scale(1)',
            transformOrigin: 'top left',
          },
          pixelRatio: 1,
        })

        // 将base64转换为blob并下载
        const response = await fetch(dataUrl)
        const blob = await response.blob()
        const fileName = `slide_${String(i + 1).padStart(3, '0')}.png`
        saveAs(blob, fileName)

        // eslint-disable-next-line no-console
        console.log(`成功导出第${i + 1}页幻灯片`)
        
        // 短暂延迟避免浏览器阻止多文件下载
        await new Promise(resolve => setTimeout(resolve, 200))
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.error(`导出第${i + 1}页幻灯片失败:`, error)
      }
    }
    
    // 恢复原来的幻灯片索引
    slidesStore.updateSlideIndex(originalSlideIndex)
  }
  else {
    // 对于其他选择器，按元素数量导出
    for (let i = 0; i < slideElements.length; i++) {
      const slideElement = slideElements[i] as HTMLElement
      if (!slideElement) continue

      try {
        await new Promise(resolve => setTimeout(resolve, 100))

        const dataUrl = await toPng(slideElement, {
          width: 1920,
          height: 1080,
          style: {
            transform: 'scale(1)',
            transformOrigin: 'top left',
          },
          pixelRatio: 1,
        })

        // 将base64转换为blob并下载
        const response = await fetch(dataUrl)
        const blob = await response.blob()
        const fileName = `slide_${String(i + 1).padStart(3, '0')}.png`
        saveAs(blob, fileName)

        // 短暂延迟避免浏览器阻止多文件下载
        await new Promise(resolve => setTimeout(resolve, 200))
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.error(`导出第${i + 1}页幻灯片失败:`, error)
      }
    }
  }
}
