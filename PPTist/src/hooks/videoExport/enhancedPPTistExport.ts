/**
 * 改进版PPTist原生导出功能 - 增强调试和多策略支持
 */

import { toJpeg } from 'html-to-image'

/**
 * 调试函数：分析导出对话框结构
 */
function debugExportDialog() {
  // eslint-disable-next-line no-console
  console.log('🔍 调试导出对话框结构...')
  
  const dialog = document.querySelector('.export-img-dialog') as HTMLElement
  if (!dialog) {
    // eslint-disable-next-line no-console
    console.log('❌ 未找到导出对话框')
    return null
  }
  
  // eslint-disable-next-line no-console
  console.log('✅ 找到导出对话框:', dialog)
  // eslint-disable-next-line no-console
  console.log('对话框尺寸:', dialog.offsetWidth, 'x', dialog.offsetHeight)
  
  // 查找所有可能的缩略图元素
  const possibleSelectors = [
    '.thumbnail',
    '.thumbnail-slide', 
    '.slide-thumbnail',
    '.export-slide',
    '.slide-item',
    '[data-slide]',
    'canvas',
    '.slide-content'
  ]
  
  const results: Record<string, number> = {}
  
  possibleSelectors.forEach(selector => {
    const elements = dialog.querySelectorAll(selector)
    results[selector] = elements.length
    
    if (elements.length > 0) {
      // eslint-disable-next-line no-console
      console.log(`${selector}: 找到 ${elements.length} 个元素`)
      const first = elements[0] as HTMLElement
      // eslint-disable-next-line no-console
      console.log(`  第一个元素尺寸: ${first.offsetWidth}x${first.offsetHeight}`)
      // eslint-disable-next-line no-console
      console.log(`  可见性: ${first.offsetWidth > 0 && first.offsetHeight > 0}`)
      
      // 检查内容
      const hasText = first.textContent && first.textContent.trim().length > 0
      const hasImages = first.querySelectorAll('img').length > 0
      const hasCanvas = first.querySelectorAll('canvas').length > 0
      const hasSvg = first.querySelectorAll('svg').length > 0
      
      // eslint-disable-next-line no-console
      console.log(`  内容: 文字=${hasText}, 图片=${hasImages}, Canvas=${hasCanvas}, SVG=${hasSvg}`)
    }
  })
  
  return results
}

/**
 * 多策略查找最佳截图元素
 */
function findBestElements(): HTMLElement[] {
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    throw new Error('未找到导出对话框')
  }
  
  // 按优先级尝试不同的选择器
  const strategies = [
    // 策略1: 标准缩略图
    { name: '标准缩略图', selector: '.thumbnail' },
    // 策略2: 幻灯片缩略图
    { name: '幻灯片缩略图', selector: '.thumbnail-slide' },
    // 策略3: 导出幻灯片
    { name: '导出幻灯片', selector: '.export-slide' },
    // 策略4: 数据属性选择
    { name: '数据幻灯片', selector: '[data-slide]' },
    // 策略5: Canvas元素
    { name: 'Canvas元素', selector: 'canvas' },
    // 策略6: 通用选择器
    { name: '所有子元素', selector: ':scope > *' }
  ]
  
  for (const strategy of strategies) {
    const elements = Array.from(dialog.querySelectorAll(strategy.selector)) as HTMLElement[]
    
    if (elements.length > 0) {
      // 过滤出有效的元素（有尺寸且可能包含内容）
      const validElements = elements.filter(el => {
        const rect = el.getBoundingClientRect()
        return rect.width > 100 && rect.height > 100 // 至少100x100像素
      })
      
      if (validElements.length > 0) {
        // eslint-disable-next-line no-console
        console.log(`✅ 使用策略: ${strategy.name}，找到 ${validElements.length} 个有效元素`)
        return validElements
      }
    }
  }
  
  throw new Error('未找到有效的截图元素')
}

/**
 * 增强版图片生成函数
 */
export const generateImagesWithEnhancedPPTist = async (): Promise<File[]> => {
  // eslint-disable-next-line no-console
  console.log('🎨 启动增强版PPTist原生导出...')
  
  // 调试对话框结构
  debugExportDialog()
  
  // 查找最佳元素
  const elements = findBestElements()
  const files: File[] = []
  
  // eslint-disable-next-line no-console
  console.log(`🎯 准备处理 ${elements.length} 个元素`)
  
  for (let i = 0; i < elements.length; i++) {
    const element = elements[i]
    
    try {
      // eslint-disable-next-line no-console
      console.log(`📸 处理第 ${i + 1} 个元素...`)
      // eslint-disable-next-line no-console
      console.log(`元素信息:`, {
        tagName: element.tagName,
        className: element.className,
        id: element.id,
        offsetWidth: element.offsetWidth,
        offsetHeight: element.offsetHeight
      })
      
      // 多种配置策略
      const configs = [
        // 配置1: PPTist原生配置
        {
          name: 'PPTist原生',
          config: {
            quality: 0.9,
            width: 1600,
            fontEmbedCSS: ''
          }
        },
        // 配置2: 高质量配置
        {
          name: '高质量',
          config: {
            quality: 0.95,
            width: 1920,
            height: 1080,
            style: {
              transform: 'scale(1)',
              transformOrigin: 'top left'
            }
          }
        },
        // 配置3: 简化配置
        {
          name: '简化',
          config: {
            quality: 0.9,
            backgroundColor: '#ffffff'
          }
        }
      ]
      
      let success = false
      
      for (const { name, config } of configs) {
        try {
          // eslint-disable-next-line no-console
          console.log(`🔧 尝试配置: ${name}`)
          
          // 等待一下确保渲染完成
          await new Promise(resolve => setTimeout(resolve, 300))
          
          // 清理可能影响截图的属性
          const foreignObjects = element.querySelectorAll('foreignObject [xmlns]')
          foreignObjects.forEach(el => el.removeAttribute('xmlns'))
          
          // 生成图片
          const dataUrl = await toJpeg(element, config)
          
          // 检查生成的图片大小
          const response = await fetch(dataUrl)
          const blob = await response.blob()
          
          if (blob.size > 10000) { // 大于10KB认为有效
            const file = new File([blob], `slide_${String(i + 1).padStart(3, '0')}.jpg`, {
              type: 'image/jpeg'
            })
            
            files.push(file)
            
            // eslint-disable-next-line no-console
            console.log(`✅ 配置 ${name} 成功: ${(blob.size / 1024).toFixed(1)}KB`)
            success = true
            break
          } 
          else {
            // eslint-disable-next-line no-console
            console.warn(`⚠️ 配置 ${name} 生成的图片太小: ${blob.size} bytes`)
          }
          
        } 
        catch (error) {
          // eslint-disable-next-line no-console
          console.warn(`⚠️ 配置 ${name} 失败:`, error)
        }
      }
      
      if (!success) {
        throw new Error(`所有配置都失败了`)
      }
      
    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`❌ 第 ${i + 1} 个元素处理失败:`, error)
      throw error
    }
  }
  
  // eslint-disable-next-line no-console
  console.log(`🎉 增强版导出完成，生成 ${files.length} 个文件`)
  
  return files
}

/**
 * 导出对话框元素检查器
 */
export const inspectExportDialog = (): void => {
  // eslint-disable-next-line no-console
  console.log('🔍 检查导出对话框...')
  
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    // eslint-disable-next-line no-console
    console.log('❌ 请先打开PPTist的"导出图片"对话框')
    return
  }
  
  // eslint-disable-next-line no-console
  console.log('✅ 找到导出对话框')
  
  // 详细检查
  debugExportDialog()
  
  try {
    const elements = findBestElements()
    // eslint-disable-next-line no-console
    console.log(`🎯 建议使用的元素数量: ${elements.length}`)
    
    elements.forEach((el, index) => {
      // eslint-disable-next-line no-console
      console.log(`元素 ${index + 1}:`, {
        tagName: el.tagName,
        className: el.className,
        width: el.offsetWidth,
        height: el.offsetHeight
      })
    })
    
  } 
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('❌ 查找元素失败:', error)
  }
}
