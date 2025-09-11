/**
 * 统一Flask后端API服务
 * 与 http://localhost:5000 的统一Flask服务进行通信
 */

import { BaseApi } from '@/api/base'
import type { ApiResponse } from '@/api/types/common'

/**
 * PPT导入结果接口
 */
export interface PPTImportResult {
  success: boolean
  data?: {
    id: string
    title: string
    slides: Array<{
      id: string
      content: string
      notes: string
      image_path?: string
    }>
    metadata: {
      total_slides: number
      created_at: string
      file_size: number
    }
  }
  message?: string
  error?: string
}

/**
 * TTS语音信息接口
 */
export interface TTSVoice {
  id: string
  name: string
  language: string
  gender: string
  engine: string
}

/**
 * 工作流状态接口
 */
export interface WorkflowStatus {
  status: 'idle' | 'running' | 'completed' | 'error'
  current_step?: string
  progress?: number
  message?: string
  timestamp: string
}

/**
 * 视频生成配置接口
 */
export interface VideoGenerationConfig {
  voice_id?: string
  quality?: 'low' | 'medium' | 'high'
  format?: 'mp4' | 'avi' | 'mov'
  resolution?: '720p' | '1080p' | '4k'
  fps?: number
}

/**
 * VideoLingo状态接口
 */
export interface VideoLingoStatus {
  videolingo: {
    available: boolean
    core_path: string
    apis: {
      config: boolean
      management: boolean
    }
  }
  integration: {
    status: string
    endpoints: string[]
  }
}

/**
 * 统一Flask后端API服务类
 */
export class UnifiedFlaskAPI extends BaseApi {
  constructor() {
    super({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
      timeout: 30000,
      retry: { times: 3, delay: 1000 },
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // 添加请求拦截器
    this.addRequestInterceptor((config) => {
      // eslint-disable-next-line no-console
      console.log(`🚀 API请求: ${config.method || 'GET'}`)
      return config
    })

    // 添加响应拦截器
    this.addResponseInterceptor((response) => {
      // eslint-disable-next-line no-console
      console.log(`✅ API响应: ${response.status} ${response.url}`)
      return response
    })

    // 添加错误拦截器
    this.addErrorInterceptor((error) => {
      // eslint-disable-next-line no-console
      console.error(`❌ API错误:`, error)
      return error
    })
  }

  /**
   * 健康检查
   */
  checkHealth(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.get('/health')
  }

  /**
   * VideoLingo健康检查
   */
  checkVideoLingoHealth(): Promise<ApiResponse<any>> {
    return this.get('/api/videolingo/health')
  }

  /**
   * 获取VideoLingo版本信息
   */
  getVideoLingoVersion(): Promise<ApiResponse<any>> {
    return this.get('/api/videolingo/version')
  }

  /**
   * 获取VideoLingo状态
   */
  getVideoLingoStatus(): Promise<ApiResponse<VideoLingoStatus>> {
    return this.get('/api/videolingo/status')
  }

  /**
   * 导入PPT文件
   */
  importPPT(file: File): Promise<ApiResponse<PPTImportResult>> {
    const formData = new FormData()
    formData.append('file', file)
    return this.upload('/api/pptist/import', formData)
  }

  /**
   * 获取幻灯片数据
   */
  getSlides(): Promise<ApiResponse<any>> {
    return this.get('/api/pptist_export/slides')
  }

  /**
   * 生成视频
   */
  generateVideo(config: VideoGenerationConfig): Promise<ApiResponse<any>> {
    return this.post('/api/pptist_export/generate_video', config)
  }

  /**
   * 获取TTS语音列表
   */
  getTTSVoices(): Promise<ApiResponse<TTSVoice[]>> {
    return this.get('/api/tts/voices')
  }

  /**
   * TTS语音合成
   */
  synthesizeAudio(text: string, voice: string): Promise<ApiResponse<any>> {
    return this.post('/api/tts/synthesize', { text, voice })
  }

  /**
   * 批量TTS合成
   */
  batchSynthesize(texts: string[], voice: string): Promise<ApiResponse<any>> {
    return this.post('/api/tts/batch', { texts, voice })
  }

  /**
   * 获取工作流状态
   */
  getWorkflowStatus(): Promise<ApiResponse<WorkflowStatus>> {
    return this.get('/api/workflow/status')
  }

  /**
   * 获取主配置
   */
  getConfig(): Promise<ApiResponse<any>> {
    return this.get('/api/config')
  }

  /**
   * 获取项目列表
   */
  getProjects(): Promise<ApiResponse<any[]>> {
    return this.get('/api/project')
  }

  /**
   * 创建新项目
   */
  createProject(projectData: any): Promise<ApiResponse<any>> {
    return this.post('/api/project/create', projectData)
  }

  /**
   * 获取工作空间状态
   */
  getWorkspaceStatus(): Promise<ApiResponse<any>> {
    return this.get('/api/workspace/status')
  }

  /**
   * 智能字幕相关API
   */
  getSmartSubtitleStatus(): Promise<ApiResponse<any>> {
    return this.get('/api/smart-subtitle/status')
  }

  /**
   * AI配置相关API
   */
  getAIModels(): Promise<ApiResponse<any>> {
    return this.get('/api/ai-config/models')
  }

  /**
   * 增强工作流状态
   */
  getEnhancedWorkflowStatus(): Promise<ApiResponse<any>> {
    return this.get('/api/enhanced_workflow/status')
  }

  /**
   * 增强TTS引擎
   */
  getEnhancedTTSEngines(): Promise<ApiResponse<any>> {
    return this.get('/api/enhanced_tts/engines')
  }

  /**
   * 增强工作空间状态
   */
  getEnhancedWorkspaceStatus(): Promise<ApiResponse<any>> {
    return this.get('/api/enhanced_workspace/status')
  }
}

// 导出单例实例
/**
 * API服务实例
 */
export const unifiedFlaskAPI = new UnifiedFlaskAPI()

/**
 * 默认导出
 */
export default unifiedFlaskAPI
