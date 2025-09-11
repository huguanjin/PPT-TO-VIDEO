/**
 * PPTist原生导出功能直接调用方案
 * 
 * 解决方案：
 * 1. 拦截PPTist原生导出的saveAs调用
 * 2. 将图片数据直接发送到后端保存
 * 3. 避免浏览器下载，直接持久化到工作流slides目录
 */

import { toJpeg } from 'html-to-image'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'

interface ExportImageConfig {
  quality: number
  width: number
  fontEmbedCSS?: string
}

/**
 * 直接调用PPTist原生导出逻辑，但保存到后端
 */
export const captureWithNativeLogic = async (projectName: string): Promise<File[]> => {
  // eslint-disable-next-line no-console
  console.log('🎯 使用PPTist原生导出逻辑，直接保存到后端...')
  
  const slidesStore = useSlidesStore()
  const { title } = storeToRefs(slidesStore)
  
  // 查找导出对话框
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    throw new Error('请先打开PPTist的"导出图片"对话框')
  }
  
  const thumbnailsContainer = dialog.querySelector('.thumbnails')
  if (!thumbnailsContainer) {
    throw new Error('导出对话框中没有找到缩略图容器')
  }
  
  const thumbnails = thumbnailsContainer.querySelectorAll('.thumbnail')
  if (thumbnails.length === 0) {
    throw new Error('导出对话框中没有找到缩略图')
  }
  
  // eslint-disable-next-line no-console
  console.log(`📝 找到 ${thumbnails.length} 个缩略图，开始原生导出... 项目: ${title.value}`)
  
  const files: File[] = []
  
  for (let i = 0; i < thumbnails.length; i++) {
    const thumbnail = thumbnails[i] as HTMLElement
    
    try {
      // eslint-disable-next-line no-console
      console.log(`🖼️ 导出第 ${i + 1} 页...`)
      
      // 使用PPTist原生的导出配置
      const config: ExportImageConfig = {
        quality: 1, // 最高质量
        width: 1600, // PPTist原生尺寸
      }
      
      // 忽略在线字体（PPTist默认行为）
      config.fontEmbedCSS = ''
      
      // 清理可能影响导出的属性（PPTist原生逻辑）
      const foreignObjectSpans = thumbnail.querySelectorAll('foreignObject [xmlns]')
      foreignObjectSpans.forEach(spanRef => spanRef.removeAttribute('xmlns'))
      
      // 等待DOM稳定（PPTist原生逻辑）
      await new Promise(resolve => setTimeout(resolve, 200))
      
      // 使用JPEG格式导出（PPTist原生默认）
      const dataUrl = await toJpeg(thumbnail, config)
      
      // 转换为File对象
      const response = await fetch(dataUrl)
      const blob = await response.blob()
      
      const file = new File([blob], `slide_${String(i + 1).padStart(3, '0')}.jpg`, {
        type: 'image/jpeg'
      })
      
      files.push(file)
      
      // eslint-disable-next-line no-console
      console.log(`✅ 第 ${i + 1} 页导出成功: ${(file.size / 1024).toFixed(1)}KB`)
      
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error(`❌ 第 ${i + 1} 页导出失败:`, error)
      throw error
    }
  }
  
  // eslint-disable-next-line no-console
  console.log(`🎉 PPTist原生导出完成，生成 ${files.length} 个文件`)
  
  // 直接发送到后端保存
  await uploadToBackend(projectName, files)
  
  return files
}

/**
 * 直接上传图片到后端工作流目录
 */
async function uploadToBackend(projectName: string, files: File[]): Promise<void> {
  // eslint-disable-next-line no-console
  console.log(`📤 上传 ${files.length} 个图片到后端工作流目录...`)
  
  try {
    const formData = new FormData()
    formData.append('project_name', projectName)
    formData.append('total_files', files.length.toString())
    
    // 添加所有图片文件
    files.forEach((file, index) => {
      formData.append(`image_${index}`, file)
    })
    
    // 发送到后端API
    const response = await fetch('/api/pptist/upload-native-images', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`上传失败: ${response.status} ${response.statusText}`)
    }
    
    const result = await response.json()
    // eslint-disable-next-line no-console
    console.log('✅ 图片上传成功:', result)
    
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('❌ 上传图片到后端失败:', error)
    throw error
  }
}

/**
 * 模拟PPTist的exportImage函数，但不下载
 */
export const simulateNativeExport = async (): Promise<File[]> => {
  // eslint-disable-next-line no-console
  console.log('🎭 模拟PPTist原生导出（不触发下载）...')
  
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    throw new Error('请先打开PPTist的"导出图片"对话框')
  }
  
  const thumbnailsContainer = dialog.querySelector('.thumbnails')
  if (!thumbnailsContainer) {
    throw new Error('找不到缩略图容器')
  }
  
  // 直接使用PPTist的原生导出逻辑，但拦截saveAs
  const originalSaveAs = (window as any).saveAs
  const capturedFiles: File[] = []
  
  // 临时替换saveAs函数来拦截下载
  ;(window as any).saveAs = (data: any, filename: string) => {
    // eslint-disable-next-line no-console
    console.log(`🎯 拦截到PPTist导出: ${filename}`)
    
    if (data instanceof Blob || (typeof data === 'string' && data.startsWith('data:'))) {
      // 转换为File对象
      if (typeof data === 'string') {
        // data URL转换为blob
        fetch(data).then(response => response.blob()).then(blobData => {
          const file = new File([blobData], filename, { type: 'image/jpeg' })
          capturedFiles.push(file)
        })
      }
      else {
        const file = new File([data], filename, { type: 'image/jpeg' })
        capturedFiles.push(file)
      }
    }
  }
  
  try {
    // 触发PPTist原生导出
    const exportButton = dialog.querySelector('.btn.export') as HTMLElement
    if (exportButton) {
      exportButton.click()
      
      // 等待导出完成
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
    
    return capturedFiles
    
  }
  finally {
    // 恢复原始的saveAs函数
    (window as any).saveAs = originalSaveAs
  }
}

/**
 * 检查是否在正确的导出环境中
 */
export const validateExportEnvironment = (): boolean => {
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    // eslint-disable-next-line no-console
    console.warn('⚠️ 请先打开PPTist的"导出图片"对话框')
    return false
  }
  
  const thumbnails = dialog.querySelectorAll('.thumbnail')
  if (thumbnails.length === 0) {
    // eslint-disable-next-line no-console
    console.warn('⚠️ 导出对话框中没有缩略图')
    return false
  }
  
  // eslint-disable-next-line no-console
  console.log(`✅ 导出环境验证通过，找到 ${thumbnails.length} 个缩略图`)
  return true
}

/**
 * 完整的原生导出流程
 */
export const executeNativeExportWorkflow = async (projectName: string): Promise<{
  success: boolean
  files: File[]
  message: string
}> => {
  try {
    // 1. 验证环境
    if (!validateExportEnvironment()) {
      return {
        success: false,
        files: [],
        message: '导出环境验证失败'
      }
    }
    
    // 2. 执行原生导出
    const files = await captureWithNativeLogic(projectName)
    
    return {
      success: true,
      files,
      message: `成功导出 ${files.length} 个图片文件`
    }
    
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('❌ 原生导出流程失败:', error)
    return {
      success: false,
      files: [],
      message: error instanceof Error ? error.message : '导出失败'
    }
  }
}
