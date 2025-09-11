/**
 * 直接调用PPTist原生导出功能的解决方案
 */

import { toJpeg } from 'html-to-image'

/**
 * 使用PPTist原生导出方法生成图片文件（完全复用原生逻辑）
 */
export const generateImagesWithPPTistOriginal = async (): Promise<File[]> => {
  const files: File[] = []
  
  // eslint-disable-next-line no-console
  console.log('🎨 使用PPTist原生导出方法生成图片')
  
  // 查找ExportImage对话框中的ThumbnailSlide组件
  const exportDialog = document.querySelector('.export-img-dialog')
  if (!exportDialog) {
    throw new Error('请先打开"导出图片"对话框，然后再执行视频导出')
  }

  const thumbnails = exportDialog.querySelectorAll('.thumbnail')
  if (thumbnails.length === 0) {
    throw new Error('导出对话框中没有找到缩略图，请等待加载完成')
  }

  // eslint-disable-next-line no-console
  console.log(`✅ 找到 ${thumbnails.length} 个PPTist原生缩略图`)

  // 使用PPTist原生的导出配置
  const quality = 0.9

  for (let i = 0; i < thumbnails.length; i++) {
    const thumbnail = thumbnails[i] as HTMLElement
    
    try {
      // eslint-disable-next-line no-console
      console.log(`📸 正在使用PPTist原生方法生成第 ${i + 1} 页图片...`)

      // 移除可能影响导出的xmlns属性（复制PPTist原生逻辑）
      const foreignObjectSpans = thumbnail.querySelectorAll('foreignObject [xmlns]')
      foreignObjectSpans.forEach(spanRef => spanRef.removeAttribute('xmlns'))

      // 等待一下让DOM更新
      await new Promise(resolve => setTimeout(resolve, 200))

      // 使用PPTist原生的导出配置
      const config = {
        quality,
        width: 1600, // 使用PPTist原生的1600宽度
        fontEmbedCSS: '' // 忽略Web字体，与PPTist原生一致
      }

      // 生成图片（完全复用PPTist原生逻辑）
      const dataUrl = await toJpeg(thumbnail, config)

      // 转换为File对象
      const response = await fetch(dataUrl)
      const blob = await response.blob()

      const file = new File([blob], `slide_${String(i + 1).padStart(3, '0')}.jpg`, {
        type: 'image/jpeg'
      })

      files.push(file)
      
      // eslint-disable-next-line no-console
      console.log(`✅ PPTist原生方法生成第 ${i + 1} 页成功: ${(blob.size / 1024).toFixed(1)}KB`)

    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`❌ PPTist原生方法生成第 ${i + 1} 页失败:`, error)
      throw error
    }
  }

  return files
}

/**
 * 程序化触发PPTist导出图片对话框
 */
export const triggerPPTistExportDialog = (): Promise<boolean> => {
  return new Promise((resolve) => {
    // eslint-disable-next-line no-console
    console.log('🎭 尝试程序化触发PPTist导出图片对话框...')
    
    // 查找导出图片按钮
    const exportButton = document.querySelector('[title="导出图片"]') || 
                        document.querySelector('.export-image-btn') ||
                        document.querySelector('[data-action="export-image"]')
    
    if (exportButton) {
      // eslint-disable-next-line no-console
      console.log('✅ 找到导出图片按钮，正在触发...')
      
      // 模拟点击
      ;(exportButton as HTMLElement).click()
      
      // 等待对话框出现
      setTimeout(() => {
        const dialog = document.querySelector('.export-img-dialog')
        if (dialog) {
          // eslint-disable-next-line no-console
          console.log('✅ 导出对话框已打开')
          resolve(true)
        } 
        else {
          // eslint-disable-next-line no-console
          console.log('❌ 导出对话框未能打开')
          resolve(false)
        }
      }, 1000)
    } 
    else {
      // eslint-disable-next-line no-console
      console.log('❌ 未找到导出图片按钮')
      resolve(false)
    }
  })
}

/**
 * 智能PPTist原生导出：自动尝试开启对话框或使用已开启的对话框
 */
export const smartPPTistNativeExport = async (): Promise<File[]> => {
  // eslint-disable-next-line no-console
  console.log('🤖 智能PPTist原生导出启动...')

  // 首先检查是否已经有导出对话框打开
  let dialog = document.querySelector('.export-img-dialog')
  
  if (!dialog) {
    // eslint-disable-next-line no-console
    console.log('📭 导出对话框未打开，尝试程序化打开...')
    
    const opened = await triggerPPTistExportDialog()
    if (!opened) {
      throw new Error(`
❌ 无法自动打开导出对话框，请手动操作：

1. 在PPTist界面点击"导出图片"按钮
2. 等待导出对话框完全加载显示所有缩略图
3. 保持对话框打开状态
4. 然后再执行视频导出功能

这样可以确保使用PPTist原生的高质量图片生成功能！`)
    }
    
    // 重新获取对话框
    dialog = document.querySelector('.export-img-dialog')
  }

  if (dialog) {
    // eslint-disable-next-line no-console
    console.log('✅ 导出对话框已就绪，开始使用PPTist原生导出...')
    
    // 再等待一下确保所有缩略图都加载完成
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    return await generateImagesWithPPTistOriginal()
  }
  
  throw new Error('无法获取导出对话框')
}
