/**
 * 导出工具函数
 * 包含数据处理、分块上传等通用功能
 */
import message from '@/utils/message'

/**
 * 分块读取文件
 */
export const readFileInChunks = (file: File, chunkSize: number = 1024 * 1024): Promise<Uint8Array[]> => {
  return new Promise((resolve, reject) => {
    const chunks: Uint8Array[] = []
    const reader = new FileReader()
    let offset = 0

    const readNextChunk = () => {
      if (offset >= file.size) {
        resolve(chunks)
        return
      }

      const chunkEnd = Math.min(offset + chunkSize, file.size)
      const chunk = file.slice(offset, chunkEnd)

      reader.onload = (e) => {
        if (e.target?.result instanceof ArrayBuffer) {
          chunks.push(new Uint8Array(e.target.result))
          offset = chunkEnd
          readNextChunk()
        }
        else {
          reject(new Error('读取文件失败'))
        }
      }

      reader.onerror = () => reject(new Error('读取文件失败'))
      reader.readAsArrayBuffer(chunk)
    }

    readNextChunk()
  })
}

/**
 * Base64编码
 */
export const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

/**
 * 创建项目文件夹名称
 */
export const createProjectFolderName = (): string => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hour = String(now.getHours()).padStart(2, '0')
  const minute = String(now.getMinutes()).padStart(2, '0')
  const second = String(now.getSeconds()).padStart(2, '0')
  
  return `pptist_${year}${month}${day}_${hour}${minute}${second}`
}

/**
 * 验证文件类型
 */
export const validateImageFile = (file: File): boolean => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png']
  return allowedTypes.includes(file.type)
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 显示进度消息
 */
export const showProgressMessage = (messageText: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
  message[type](messageText, {
    duration: 2000
  })
}

/**
 * 处理分块上传错误
 */
export const handleUploadError = (error: any, context: string): never => {
  // eslint-disable-next-line no-console
  console.error(`${context}失败:`, error)
  
  let errorMessage = `${context}失败`
  
  if (error.response) {
    const status = error.response.status
    const data = error.response.data
    
    if (status === 413) {
      errorMessage = '文件太大，超出服务器限制'
    }
    else if (status === 422) {
      errorMessage = '文件格式不正确或数据验证失败'
    }
    else if (data && data.detail) {
      errorMessage = `${context}失败: ${data.detail}`
    }
    else {
      errorMessage = `${context}失败: HTTP ${status}`
    }
  }
  else if (error.message) {
    errorMessage = `${context}失败: ${error.message}`
  }
  
  message.error(errorMessage)
  throw new Error(errorMessage)
}

/**
 * 等待指定时间
 */
export const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 重试机制
 */
export const retryWithDelay = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delayMs: number = 1000
): Promise<T> => {
  let lastError: Error
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn()
    }
    catch (error) {
      lastError = error as Error
      
      if (i === maxRetries) {
        break
      }
      
      // eslint-disable-next-line no-console
      console.warn(`重试 ${i + 1}/${maxRetries} 失败:`, error)
      await delay(delayMs * (i + 1)) // 递增延迟
    }
  }
  
  throw lastError!
}

/**
 * 文件压缩选项
 */
export interface ImageCompressionOptions {
  maxWidth?: number
  maxHeight?: number
  quality?: number
  format?: 'jpeg' | 'png' | 'webp'
}

/**
 * 压缩图片文件
 */
export const compressImage = (
  file: File, 
  options: ImageCompressionOptions = {}
): Promise<File> => {
  const {
    maxWidth = 1920,
    maxHeight = 1080,
    quality = 0.9,
    format = 'jpeg'
  } = options

  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      // 计算新的尺寸，保持宽高比
      let { width, height } = img
      
      if (width > maxWidth) {
        height = (height * maxWidth) / width
        width = maxWidth
      }
      
      if (height > maxHeight) {
        width = (width * maxHeight) / height
        height = maxHeight
      }

      canvas.width = width
      canvas.height = height

      // 绘制图片
      ctx!.fillStyle = '#ffffff'
      ctx!.fillRect(0, 0, width, height)
      ctx!.drawImage(img, 0, 0, width, height)

      // 转换为Blob
      canvas.toBlob(
        (blob) => {
          if (blob) {
            const compressedFile = new File([blob], file.name, {
              type: `image/${format}`,
              lastModified: Date.now()
            })
            resolve(compressedFile)
          }
          else {
            reject(new Error('图片压缩失败'))
          }
        },
        `image/${format}`,
        quality
      )
    }

    img.onerror = () => reject(new Error('图片加载失败'))
    img.src = URL.createObjectURL(file)
  })
}
