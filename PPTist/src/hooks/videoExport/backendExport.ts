/**
 * 后端导出相关函数
 * 包含与后端API的交互逻辑
 */
import axios from 'axios'
import { API_BASE_URL } from '@/config/api'
import { 
  readFileInChunks, 
  handleUploadError, 
  retryWithDelay,
  showProgressMessage
} from './exportUtils'

// 配置axios实例
const api = axios.create({
  timeout: 60000, // 60秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 项目数据接口
 */
export interface ProjectData {
  project_name: string
  slides: Array<{
    slide_number: number
    title: string
    content: string
  }>
}

/**
 * 上传文件到后端
 */
export const uploadFileToBackend = async (
  file: File,
  endpoint: string,
  onProgress?: (progress: number) => void
): Promise<any> => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await api.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })

    return response.data
  }
  catch (error) {
    handleUploadError(error, '文件上传')
    throw error
  }
}

/**
 * 分块上传大文件
 */
export const uploadLargeFile = async (
  file: File,
  baseUrl: string, // 改为baseUrl参数
  chunkSize: number = 1024 * 1024, // 1MB per chunk
  onProgress?: (progress: number) => void
): Promise<any> => {
  try {
    // 读取文件分块
    const chunks = await readFileInChunks(file, chunkSize)
    const totalChunks = chunks.length
    
    // eslint-disable-next-line no-console
    console.log(`开始分块上传，总共 ${totalChunks} 个分块`)

    // 1. 初始化分块上传
    const initFormData = new FormData()
    initFormData.append('filename', file.name)
    initFormData.append('file_size', file.size.toString())
    initFormData.append('total_chunks', totalChunks.toString())
    
    const initResponse = await api.post(`${baseUrl}/api/upload/init`, initFormData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const uploadId = initResponse.data.upload_id
    
    // eslint-disable-next-line no-console
    console.log(`分块上传初始化成功，upload_id: ${uploadId}`)

    // 2. 发送每个分块
    for (let i = 0; i < totalChunks; i++) {
      const chunk = chunks[i]
      
      const chunkFormData = new FormData()
      chunkFormData.append('upload_id', uploadId)
      chunkFormData.append('chunk_index', i.toString())
      chunkFormData.append('chunk', new Blob([chunk.buffer as ArrayBuffer]), `chunk_${i}`)

      await retryWithDelay(async () => {
        const response = await api.post(`${baseUrl}/api/upload/chunk`, chunkFormData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        if (onProgress) {
          const progress = Math.round(((i + 1) * 100) / totalChunks)
          onProgress(progress)
        }

        return response.data
      }, 3, 1000)

      // eslint-disable-next-line no-console
      console.log(`分块 ${i + 1}/${totalChunks} 上传成功`)
    }

    // 3. 完成分块上传
    const completeFormData = new FormData()
    completeFormData.append('upload_id', uploadId)
    
    const completeResponse = await api.post(`${baseUrl}/api/upload/complete`, completeFormData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    return completeResponse.data
  }
  catch (error) {
    handleUploadError(error, '分块上传')
    throw error
  }
}

/**
 * 上传项目数据和图片
 */
export const exportToBackendWithChunkedUpload = async (
  projectData: ProjectData,
  imageFiles: File[],
  baseUrl: string = API_BASE_URL
): Promise<string> => {
  try {
    showProgressMessage('开始导出项目...', 'info')

    // 1. 使用 PPTist JSON项目导入API发送项目元数据
    // eslint-disable-next-line no-console
    console.log('📤 发送项目元数据...')
    
    // 直接发送JSON数据，不使用FormData
    const requestData = {
      project_data: projectData,
      project_name: projectData.project_name || `pptist_${Date.now()}`
    }
    
    const metadataResponse = await api.post(`${baseUrl}/api/pptist/import`, requestData)
    
    const projectName = metadataResponse.data.data?.project_name || requestData.project_name
    showProgressMessage(`项目创建成功，名称: ${projectName}`, 'success')

    // 2. 分别上传每个图片文件
    // eslint-disable-next-line no-console
    console.log(`🖼️ 开始上传 ${imageFiles.length} 个图片文件...`)
    
    for (let i = 0; i < imageFiles.length; i++) {
      const file = imageFiles[i]
      
      showProgressMessage(`正在上传第 ${i + 1}/${imageFiles.length} 张图片...`, 'info')
      
      // 对大文件使用分块上传
      if (file.size > 5 * 1024 * 1024) { // 5MB以上使用分块上传
        const uploadResult = await uploadLargeFile(
          file,
          baseUrl, // 传递baseUrl参数但函数内部会使用统一的分块上传API
          1024 * 1024, // 1MB chunks
          (progress) => {
            // eslint-disable-next-line no-console
            console.log(`图片 ${i + 1} 上传进度: ${progress}%`)
          }
        )
        
        // 分块上传完成后，需要使用项目相关的API来关联图片
        if (uploadResult.success) {
          const moveFormData = new FormData()
          moveFormData.append('slide_index', i.toString())
          moveFormData.append('upload_id', uploadResult.upload_id)
          
          await api.post(`${baseUrl}/api/project/${projectName}/upload-images-chunked`, moveFormData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
        }
      }
      else {
        // 小文件直接上传 - 使用正确的后端API
        const imageFormData = new FormData()
        imageFormData.append('image', file)
        imageFormData.append('slide_index', i.toString())
        
        await api.post(`${baseUrl}/api/project/${projectName}/upload-image`, imageFormData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              // eslint-disable-next-line no-console
              console.log(`图片 ${i + 1} 上传进度: ${progress}%`)
            }
          }
        })
      }
      
      // eslint-disable-next-line no-console
      console.log(`✅ 图片 ${i + 1}/${imageFiles.length} 上传成功`)
    }

    showProgressMessage('所有图片上传完成！', 'success')

    // 3. 触发视频生成 - 使用工作流执行API
    // eslint-disable-next-line no-console
    console.log('🎬 开始生成视频...')
    showProgressMessage('开始生成视频，请稍候...', 'info')
    
    const videoResponse = await api.post(`${baseUrl}/api/workflow/execute`, {
      project_name: projectName
    }, {
      timeout: 300000 // 5分钟超时
    })

    if (videoResponse.data.success) {
      const workflowId = videoResponse.data.workflow_id
      showProgressMessage('工作流启动成功！', 'success')
      // 返回工作流ID作为字符串，保持兼容性
      return workflowId
    }
    
    throw new Error(videoResponse.data.message || '工作流启动失败')
  }
  catch (error) {
    handleUploadError(error, '导出到后端')
    throw error
  }
}

/**
 * 改进的分块上传方法，支持多种回退策略
 */
export const exportToBackendWithChunkedUploadImproved = async (
  projectData: ProjectData,
  imageFiles: File[],
  baseUrl: string = API_BASE_URL
): Promise<string> => {
  try {
    showProgressMessage('开始导出项目...', 'info')

    // 1. 使用 PPTist JSON项目导入API发送项目元数据
    // eslint-disable-next-line no-console
    console.log('📤 发送项目元数据...')
    
    // 直接发送JSON数据，不使用FormData
    const requestData = {
      project_data: projectData,
      project_name: projectData.project_name || `pptist_${Date.now()}`
    }
    
    const metadataResponse = await api.post(`${baseUrl}/api/pptist/import`, requestData)
    
    const projectName = metadataResponse.data.data?.project_name || requestData.project_name
    showProgressMessage(`项目创建成功，名称: ${projectName}`, 'success')

    // 2. 批量上传图片（多种策略）
    // eslint-disable-next-line no-console
    console.log(`🖼️ 开始上传 ${imageFiles.length} 个图片文件...`)
    
    // 策略：单个文件上传（因为后端不支持批量上传）
    for (let i = 0; i < imageFiles.length; i++) {
      const file = imageFiles[i]
      
      showProgressMessage(`正在上传第 ${i + 1}/${imageFiles.length} 张图片...`, 'info')
      
      try {
        // 对大文件使用分块上传
        if (file.size > 10 * 1024 * 1024) { // 10MB以上使用分块上传
          const uploadResult = await uploadLargeFile(
            file,
            baseUrl, // 传递baseUrl参数但函数内部会使用统一的分块上传API
            2 * 1024 * 1024, // 2MB chunks
            (progress) => {
              // eslint-disable-next-line no-console
              console.log(`图片 ${i + 1} 分块上传进度: ${progress}%`)
            }
          )
          
          // 分块上传完成后，需要使用项目相关的API来关联图片
          if (uploadResult.success) {
            const moveFormData = new FormData()
            moveFormData.append('slide_index', i.toString())
            moveFormData.append('upload_id', uploadResult.upload_id)
            
            await api.post(`${baseUrl}/api/project/${projectName}/upload-images-chunked`, moveFormData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            })
          }
        }
        else {
          // 小文件直接上传 - 使用正确的后端API
          const imageFormData = new FormData()
          imageFormData.append('image', file)
          imageFormData.append('slide_index', i.toString())
          
          await api.post(`${baseUrl}/api/project/${projectName}/upload-image`, imageFormData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                // eslint-disable-next-line no-console
                console.log(`图片 ${i + 1} 上传进度: ${progress}%`)
              }
            }
          })
        }
        
        // eslint-disable-next-line no-console
        console.log(`✅ 图片 ${i + 1}/${imageFiles.length} 上传成功`)
      }
      catch (uploadError) {
        // eslint-disable-next-line no-console
        console.error(`图片 ${i + 1} 上传失败:`, uploadError)
        throw uploadError
      }
    }
    
    showProgressMessage('所有图片上传完成！', 'success')

    // 3. 触发视频生成 - 使用工作流执行API
    // eslint-disable-next-line no-console
    console.log('🎬 准备生成视频...')
    showProgressMessage('项目数据上传完成，准备启动工作流...', 'info')
    
    try {
      const videoResponse = await api.post(`${baseUrl}/api/workflow/execute`, {
        project_name: projectName
      }, {
        timeout: 300000 // 5分钟超时
      })

      if (videoResponse.data.success) {
        const workflowId = videoResponse.data.data?.workflow_id || videoResponse.data.workflow_id
        showProgressMessage('工作流启动成功！', 'success')
        // eslint-disable-next-line no-console
        console.log('✅ 工作流启动成功，完整响应:', videoResponse.data)
        // eslint-disable-next-line no-console
        console.log('✅ 解析的工作流ID:', workflowId)
        // eslint-disable-next-line no-console
        console.log('✅ 返回值:', workflowId || projectName)
        return workflowId || projectName
      }
      
      throw new Error(videoResponse.data.message || '工作流启动失败')
    }
    catch (workflowError) {
      // eslint-disable-next-line no-console
      console.warn('⚠️ 工作流启动失败，但文件上传成功:', workflowError)
      showProgressMessage('文件上传成功，但工作流启动失败。请手动检查后端服务。', 'warning')
      
      // 返回项目名称，表示至少上传成功了
      return projectName
    }
  }
  catch (error) {
    handleUploadError(error, '导出到后端')
    throw error
  }
}

/**
 * 检查后端服务状态
 */
export const checkBackendStatus = async (baseUrl: string = API_BASE_URL): Promise<boolean> => {
  try {
    const response = await api.get(`${baseUrl}/api/config`, {
      timeout: 5000
    })
    return response.status === 200
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('后端服务检查失败:', error)
    return false
  }
}

/**
 * 获取项目列表
 */
export const getProjectList = async (baseUrl: string = API_BASE_URL): Promise<any[]> => {
  try {
    const response = await api.get(`${baseUrl}/api/projects`)
    return response.data.projects || []
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('获取项目列表失败:', error)
    return []
  }
}

/**
 * 删除项目 - 暂时不支持，后端未实现此API
 */
export const deleteProject = (
  projectName: string, 
  baseUrl: string = API_BASE_URL
): Promise<boolean> => {
  try {
    // TODO: 后端需要实现项目删除API
    // const response = await api.delete(`${baseUrl}/api/projects/${projectName}`)
    // return response.data.success === true
    
    // eslint-disable-next-line no-console
    console.warn('删除项目功能暂未实现，项目:', projectName, '基础URL:', baseUrl)
    return Promise.resolve(false)
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('删除项目失败:', error)
    return Promise.resolve(false)
  }
}
