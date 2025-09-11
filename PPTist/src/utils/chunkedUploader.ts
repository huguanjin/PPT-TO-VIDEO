/**
 * 分片上传工具
 * 解决大文件上传限制问题
 */

import { API_BASE_URL } from '@/config/api'

export interface ChunkUploadOptions {
  file: File
  chunkSize?: number
  onProgress?: (progress: number) => void
  onChunkProgress?: (chunkIndex: number, total: number) => void
}

export interface UploadResult {
  success: boolean
  uploadId: string
  filename: string
  fileSize: number
}

export class ChunkedUploader {
  private baseUrl: string
  private chunkSize: number

  constructor(baseUrl: string = API_BASE_URL, chunkSize: number = 1024 * 512) { // 512KB per chunk
    this.baseUrl = baseUrl
    this.chunkSize = chunkSize
  }

  /**
   * 计算文件MD5校验和
   */
  private calculateMD5(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          const buffer = e.target?.result as ArrayBuffer
          const hashBuffer = await crypto.subtle.digest('MD5', buffer)
          const hashArray = Array.from(new Uint8Array(hashBuffer))
          const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
          resolve(hashHex)
        }
        catch (error) {
          // 如果MD5不支持，使用简单的哈希
          resolve(`${file.name}_${file.size}_${file.lastModified}`)
        }
      }
      reader.onerror = reject
      reader.readAsArrayBuffer(file)
    })
  }

  /**
   * 初始化分片上传
   */
  private async initUpload(file: File): Promise<string> {
    const totalChunks = Math.ceil(file.size / this.chunkSize)
    const checksum = await this.calculateMD5(file)

    const formData = new FormData()
    formData.append('filename', file.name)
    formData.append('total_size', file.size.toString())
    formData.append('total_chunks', totalChunks.toString())
    formData.append('checksum', checksum)

    const response = await fetch(`${this.baseUrl}/api/upload/init`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`初始化上传失败: ${response.statusText}`)
    }

    const result = await response.json()
    if (!result.success) {
      throw new Error(`初始化上传失败: ${result.message || '未知错误'}`)
    }

    return result.upload_id
  }

  /**
   * 上传单个分片
   */
  private async uploadChunk(
    uploadId: string, 
    chunkIndex: number, 
    chunk: Blob
  ): Promise<any> {
    const formData = new FormData()
    formData.append('upload_id', uploadId)
    formData.append('chunk_index', chunkIndex.toString())
    formData.append('chunk', chunk, `chunk_${chunkIndex}`)

    const response = await fetch(`${this.baseUrl}/api/upload/chunk`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`上传分片 ${chunkIndex} 失败: ${response.statusText}`)
    }

    const result = await response.json()
    if (!result.success) {
      throw new Error(`上传分片 ${chunkIndex} 失败: ${result.message || '未知错误'}`)
    }

    return result
  }

  /**
   * 完成分片上传，并将图片保存到项目slides目录
   */
  private async completeUpload(
    uploadId: string, 
    projectName: string, 
    imageIndex: number, 
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _slidesMetadata?: any // 暂时不使用，但保留参数兼容性
  ): Promise<any> {
    const formData = new FormData()
    formData.append('upload_id', uploadId)
    formData.append('slide_index', (imageIndex - 1).toString()) // 后端使用0-based index

    // 使用新的项目图片上传端点
    const response = await fetch(`${this.baseUrl}/api/project/${projectName}/upload-images-chunked`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`完成图片上传失败: ${response.statusText}`)
    }

    const result = await response.json()
    if (!result.success) {
      throw new Error(`完成图片上传失败: ${result.message || '未知错误'}`)
    }

    return result
  }

  /**
   * 执行分片上传
   */
  async upload(options: ChunkUploadOptions): Promise<UploadResult> {
    const { file, onProgress, onChunkProgress } = options
    
    // 1. 初始化上传
    const uploadId = await this.initUpload(file)
    
    // 2. 分片上传
    const totalChunks = Math.ceil(file.size / this.chunkSize)
    
    for (let i = 0; i < totalChunks; i++) {
      const start = i * this.chunkSize
      const end = Math.min(start + this.chunkSize, file.size)
      const chunk = file.slice(start, end)
      
      const result = await this.uploadChunk(uploadId, i, chunk)
      
      // 回调进度
      if (onChunkProgress) {
        onChunkProgress(i + 1, totalChunks)
      }
      if (onProgress) {
        onProgress(result.progress || ((i + 1) / totalChunks * 100))
      }
    }
    
    return {
      success: true,
      uploadId,
      filename: file.name,
      fileSize: file.size
    }
  }

  /**
   * 上传图片到项目（完整流程）
   */
  async uploadImageToProject(
    file: File, 
    projectName: string, 
    imageIndex: number, 
    slidesMetadata: any,
    onProgress?: (progress: number) => void
  ): Promise<any> {
    // 1. 分片上传文件
    const uploadResult = await this.upload({
      file,
      onProgress: (progress) => {
        // 上传进度占80%
        if (onProgress) onProgress(progress * 0.8)
      }
    })
    
    if (onProgress) onProgress(80)
    
    // 2. 完成上传并导入项目
    const result = await this.completeUpload(
      uploadResult.uploadId,
      projectName,
      imageIndex,
      slidesMetadata
    )
    
    if (onProgress) onProgress(100)
    
    return result
  }
}

// 导出默认实例
export const chunkedUploader = new ChunkedUploader()
