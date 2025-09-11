/**
 * 解决PPTist导出图片缩放问题的专用函数
 * 
 * 问题：导出的图片内容被缩小到左上角约1/4区域
 * 原因：缩略图元素的显示尺寸与目标输出尺寸不匹配
 * 解决：使用正确的缩放配置和尺寸计算
 */

import { toJpeg } from 'html-to-image'

/**
 * 分析元素的实际内容尺寸
 */
function analyzeElementDimensions(element: HTMLElement) {
  const rect = element.getBoundingClientRect()
  const computedStyle = window.getComputedStyle(element)
  
  // 获取元素的实际渲染尺寸
  const displayWidth = rect.width
  const displayHeight = rect.height
  
  // 获取元素的内在尺寸（CSS尺寸）
  const cssWidth = parseInt(computedStyle.width) || displayWidth
  const cssHeight = parseInt(computedStyle.height) || displayHeight
  
  // 检查是否有transform缩放
  const transform = computedStyle.transform
  let scaleX = 1, scaleY = 1
  
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
  
  return {
    displayWidth,
    displayHeight,
    cssWidth,
    cssHeight,
    scaleX,
    scaleY,
    aspectRatio: displayWidth / displayHeight
  }
}

/**
 * 计算最佳的输出配置
 */
function calculateOptimalConfig(element: HTMLElement, targetWidth = 1920, targetHeight = 1080) {
  const dimensions = analyzeElementDimensions(element)
  
  // eslint-disable-next-line no-console
  console.log('🔍 元素尺寸分析:', dimensions)
  
  // 计算缩放比例以铺满目标尺寸
  const scaleToFitWidth = targetWidth / dimensions.displayWidth
  const scaleToFitHeight = targetHeight / dimensions.displayHeight
  
  // 使用较小的缩放比例以确保内容完全可见
  const optimalScale = Math.min(scaleToFitWidth, scaleToFitHeight)
  
  // eslint-disable-next-line no-console
  console.log('📐 缩放计算:', {
    scaleToFitWidth,
    scaleToFitHeight,
    optimalScale,
    finalWidth: dimensions.displayWidth * optimalScale,
    finalHeight: dimensions.displayHeight * optimalScale
  })
  
  return {
    width: targetWidth,
    height: targetHeight,
    style: {
      transform: `scale(${optimalScale})`,
      transformOrigin: 'top left',
      width: `${dimensions.displayWidth}px`,
      height: `${dimensions.displayHeight}px`
    },
    pixelRatio: 2, // 高分辨率
    quality: 0.95
  }
}

/**
 * 使用正确缩放的PPTist导出
 */
export const generateImagesWithCorrectScaling = async (): Promise<File[]> => {
  // eslint-disable-next-line no-console
  console.log('🎯 启动正确缩放的PPTist导出...')
  
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    throw new Error('请先打开PPTist的"导出图片"对话框')
  }
  
  const thumbnails = dialog.querySelectorAll('.thumbnail')
  if (thumbnails.length === 0) {
    throw new Error('导出对话框中没有找到缩略图')
  }
  
  // eslint-disable-next-line no-console
  console.log(`📝 找到 ${thumbnails.length} 个缩略图`)
  
  const files: File[] = []
  
  for (let i = 0; i < thumbnails.length; i++) {
    const thumbnail = thumbnails[i] as HTMLElement
    
    try {
      // eslint-disable-next-line no-console
      console.log(`🖼️ 处理第 ${i + 1} 页...`)
      
      // 分析缩略图尺寸
      const analysis = analyzeElementDimensions(thumbnail)
      // eslint-disable-next-line no-console
      console.log(`第 ${i + 1} 页尺寸:`, analysis)
      
      // 清理可能影响截图的属性
      const foreignObjects = thumbnail.querySelectorAll('foreignObject [xmlns]')
      foreignObjects.forEach(el => el.removeAttribute('xmlns'))
      
      // 等待渲染稳定
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 尝试多种策略
      const strategies = [
        // 策略1: 智能缩放到1920x1080
        {
          name: '智能缩放1920x1080',
          config: calculateOptimalConfig(thumbnail, 1920, 1080)
        },
        
        // 策略2: 保持原始比例，放大到合适尺寸
        {
          name: '保持比例放大',
          config: {
            width: Math.max(1600, analysis.displayWidth * 2),
            height: Math.max(900, analysis.displayHeight * 2),
            style: {
              transform: 'scale(2)',
              transformOrigin: 'top left'
            },
            quality: 0.95
          }
        },
        
        // 策略3: 使用PPTist原生尺寸但高质量
        {
          name: 'PPTist原生高质量',
          config: {
            width: 1600,
            height: 900,
            quality: 0.95,
            pixelRatio: 2,
            fontEmbedCSS: ''
          }
        },
        
        // 策略4: 完全自适应
        {
          name: '自适应尺寸',
          config: {
            quality: 0.95,
            pixelRatio: 2,
            backgroundColor: '#ffffff'
          }
        }
      ]
      
      let success = false
      
      for (const strategy of strategies) {
        try {
          // eslint-disable-next-line no-console
          console.log(`🔧 尝试策略: ${strategy.name}`)
          
          const dataUrl = await toJpeg(thumbnail, strategy.config)
          
          // 检查生成的图片
          const response = await fetch(dataUrl)
          const blob = await response.blob()
          
          if (blob.size > 20000) { // 至少20KB
            const file = new File([blob], `slide_${String(i + 1).padStart(3, '0')}.jpg`, {
              type: 'image/jpeg'
            })
            
            files.push(file)
            
            // eslint-disable-next-line no-console
            console.log(`✅ 策略 ${strategy.name} 成功: ${(blob.size / 1024).toFixed(1)}KB`)
            success = true
            break
          } 
          else {
            // eslint-disable-next-line no-console
            console.warn(`⚠️ 策略 ${strategy.name} 生成的图片太小: ${blob.size} bytes`)
          }
          
        } 
        catch (error) {
          // eslint-disable-next-line no-console
          console.warn(`⚠️ 策略 ${strategy.name} 失败:`, error)
        }
      }
      
      if (!success) {
        throw new Error(`第 ${i + 1} 页所有策略都失败了`)
      }
      
    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`❌ 第 ${i + 1} 页处理失败:`, error)
      throw error
    }
  }
  
  // eslint-disable-next-line no-console
  console.log(`🎉 正确缩放导出完成，生成 ${files.length} 个文件`)
  
  return files
}

/**
 * 调试缩放问题的辅助函数
 */
export const debugScalingIssue = (): void => {
  // eslint-disable-next-line no-console
  console.log('🔍 调试缩放问题...')
  
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    // eslint-disable-next-line no-console
    console.log('❌ 请先打开导出对话框')
    return
  }
  
  const thumbnails = dialog.querySelectorAll('.thumbnail')
  if (thumbnails.length === 0) {
    // eslint-disable-next-line no-console
    console.log('❌ 没有找到缩略图')
    return
  }
  
  // eslint-disable-next-line no-console
  console.log(`📊 分析 ${thumbnails.length} 个缩略图的尺寸...`)
  
  thumbnails.forEach((thumb, index) => {
    const element = thumb as HTMLElement
    const analysis = analyzeElementDimensions(element)
    
    // eslint-disable-next-line no-console
    console.log(`缩略图 ${index + 1}:`, {
      tagName: element.tagName,
      className: element.className,
      ...analysis
    })
    
    // 检查父容器
    const parent = element.parentElement
    if (parent) {
      const parentAnalysis = analyzeElementDimensions(parent)
      // eslint-disable-next-line no-console
      console.log(`  父容器:`, parentAnalysis)
    }
  })
  
  // 建议解决方案
  // eslint-disable-next-line no-console
  console.log('\n💡 解决建议:')
  // eslint-disable-next-line no-console
  console.log('1. 缩略图显示尺寸可能与实际内容尺寸不匹配')
  // eslint-disable-next-line no-console
  console.log('2. 需要使用正确的缩放配置')
  // eslint-disable-next-line no-console
  console.log('3. 可能需要调整目标输出尺寸')
}
