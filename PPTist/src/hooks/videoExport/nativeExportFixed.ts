/**
 * PPTist原生导出功能调用方案
 * 解决图片缩放到左上角1/4区域的问题
 */

import { toJpeg } from 'html-to-image'

interface ExportImageConfig {
  quality: number
  width: number
  fontEmbedCSS?: string
}

/**
 * 直接调用PPTist原生导出逻辑
 */
export const captureWithNativeLogic = async (projectName: string): Promise<File[]> => {
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
  
  const files: File[] = []
  
  for (let i = 0; i < thumbnails.length; i++) {
    const thumbnail = thumbnails[i] as HTMLElement
    
    try {
      // 使用PPTist原生的导出配置
      const config: ExportImageConfig = {
        quality: 1,
        width: 1600,
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
      
    } 
    catch (error) {
      throw new Error(`第 ${i + 1} 页导出失败: ${error}`)
    }
  }
  
  // 直接发送到后端保存
  await uploadToBackend(projectName, files)
  
  return files
}

/**
 * 上传图片到后端工作流目录
 */
async function uploadToBackend(projectName: string, files: File[]): Promise<void> {
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
    
  } 
  catch (error) {
    throw new Error(`上传图片到后端失败: ${error}`)
  }
}

/**
 * 检查是否在正确的导出环境中
 */
export const validateExportEnvironment = (): boolean => {
  const dialog = document.querySelector('.export-img-dialog')
  if (!dialog) {
    return false
  }
  
  const thumbnails = dialog.querySelectorAll('.thumbnail')
  if (thumbnails.length === 0) {
    return false
  }
  
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
    // 验证环境
    if (!validateExportEnvironment()) {
      return {
        success: false,
        files: [],
        message: '导出环境验证失败'
      }
    }
    
    // 执行原生导出
    const files = await captureWithNativeLogic(projectName)
    
    return {
      success: true,
      files,
      message: `成功导出 ${files.length} 个图片文件`
    }
    
  } 
  catch (error) {
    return {
      success: false,
      files: [],
      message: error instanceof Error ? error.message : '导出失败'
    }
  }
}
