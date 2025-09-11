/**
 * TTS服务API类 - 统一管理TTS相关的API调用
 */

import type { BaseApi } from '../base'
import { smartApiCall } from '../index'
import type { 
  TTSConfig,
  TTSEngine,
  TTSVoice,
  TTSTestRequest,
  TTSTestResult,
  TTSEngineStatus,
  TTSUsageStats,
  TTSTask,
  EdgeTTSConfig,
  FishTTSConfig,
  OpenAITTSConfig,
  CustomTTSConfig
} from '../types/tts'

/**
 * TTS服务类
 */
export class TTSService {
  private api: BaseApi

  constructor(api: BaseApi) {
    this.api = api
  }

  /**
   * 获取TTS配置
   */
  async getConfig(): Promise<TTSConfig> {
    const response = await smartApiCall(api => 
      api.get<TTSConfig>('/api/tts/config')
    )
    return response.data!
  }

  /**
   * 更新TTS配置
   */
  async updateConfig(config: TTSConfig): Promise<void> {
    await smartApiCall(api => 
      api.put('/api/tts/config', config)
    )
  }

  /**
   * 部分更新TTS配置
   */
  async updatePartialConfig(updates: Partial<TTSConfig>): Promise<void> {
    await smartApiCall(api => 
      api.patch('/api/tts/config', updates)
    )
  }

  /**
   * 获取指定引擎的语音列表
   */
  async getVoices(engine: TTSEngine): Promise<TTSVoice[]> {
    const response = await smartApiCall(api => 
      api.get<TTSVoice[]>(`/api/tts/voices/${engine}`)
    )
    return response.data!
  }

  /**
   * 获取Edge TTS语音列表
   */
  getEdgeVoices(): Promise<TTSVoice[]> {
    return this.getVoices('edge')
  }

  /**
   * 获取Fish TTS语音列表
   */
  getFishVoices(): Promise<TTSVoice[]> {
    return this.getVoices('fish')
  }

  /**
   * 获取OpenAI TTS语音列表
   */
  getOpenAIVoices(): Promise<TTSVoice[]> {
    return this.getVoices('openai')
  }

  /**
   * 测试TTS引擎
   */
  async testEngine(request: TTSTestRequest): Promise<TTSTestResult> {
    const response = await smartApiCall(api => 
      api.post<TTSTestResult>('/api/tts/test', request)
    )
    return response.data!
  }

  /**
   * 测试Edge TTS
   */
  testEdgeTTS(config: EdgeTTSConfig, text: string): Promise<TTSTestResult> {
    return this.testEngine({
      engine: 'edge',
      config,
      text
    })
  }

  /**
   * 测试Fish TTS
   */
  testFishTTS(config: FishTTSConfig, text: string): Promise<TTSTestResult> {
    return this.testEngine({
      engine: 'fish',
      config,
      text
    })
  }

  /**
   * 测试OpenAI TTS
   */
  testOpenAITTS(config: OpenAITTSConfig, text: string): Promise<TTSTestResult> {
    return this.testEngine({
      engine: 'openai',
      config,
      text
    })
  }

  /**
   * 测试自定义TTS
   */
  testCustomTTS(config: CustomTTSConfig, text: string): Promise<TTSTestResult> {
    return this.testEngine({
      engine: 'custom',
      config,
      text
    })
  }

  /**
   * 生成语音
   */
  async generateSpeech(
    engine: TTSEngine,
    voice: string,
    text: string,
    options?: {
      format?: string
      quality?: string
      speed?: number
      pitch?: number
      volume?: number
    }
  ): Promise<TTSTestResult> {
    const response = await smartApiCall(api => 
      api.post<TTSTestResult>('/api/tts/generate', {
        engine,
        voice,
        text,
        options
      })
    )
    return response.data!
  }

  /**
   * 批量生成语音
   */
  async generateBatchSpeech(
    requests: Array<{
      id: string
      engine: TTSEngine
      voice: string
      text: string
      options?: any
    }>
  ): Promise<TTSTask[]> {
    const response = await smartApiCall(api => 
      api.post<TTSTask[]>('/api/tts/batch', { requests })
    )
    return response.data!
  }

  /**
   * 获取TTS任务状态
   */
  async getTaskStatus(taskId: string): Promise<TTSTask> {
    const response = await smartApiCall(api => 
      api.get<TTSTask>(`/api/tts/task/${taskId}`)
    )
    return response.data!
  }

  /**
   * 获取所有TTS任务
   */
  async getTasks(status?: string): Promise<TTSTask[]> {
    const params = status ? { status } : undefined
    const response = await smartApiCall(api => 
      api.get<TTSTask[]>('/api/tts/tasks', params)
    )
    return response.data!
  }

  /**
   * 取消TTS任务
   */
  async cancelTask(taskId: string): Promise<void> {
    await smartApiCall(api => 
      api.post(`/api/tts/task/${taskId}/cancel`)
    )
  }

  /**
   * 获取TTS引擎状态
   */
  async getEngineStatus(): Promise<TTSEngineStatus> {
    const response = await smartApiCall(api => 
      api.get<TTSEngineStatus>('/api/tts/status')
    )
    return response.data!
  }

  /**
   * 获取TTS使用统计
   */
  async getUsageStats(): Promise<TTSUsageStats> {
    const response = await smartApiCall(api => 
      api.get<TTSUsageStats>('/api/tts/usage')
    )
    return response.data!
  }

  /**
   * 重置TTS使用统计
   */
  async resetUsageStats(): Promise<void> {
    await smartApiCall(api => 
      api.post('/api/tts/usage/reset')
    )
  }

  /**
   * 预览语音
   */
  async previewVoice(engine: TTSEngine, voice: string): Promise<string> {
    const response = await smartApiCall(api => 
      api.get<{ previewUrl: string }>(`/api/tts/preview/${engine}/${voice}`)
    )
    return response.data!.previewUrl
  }

  /**
   * 获取支持的输出格式
   */
  async getSupportedFormats(engine: TTSEngine): Promise<string[]> {
    const response = await smartApiCall(api => 
      api.get<string[]>(`/api/tts/formats/${engine}`)
    )
    return response.data!
  }

  /**
   * 验证TTS引擎配置
   */
  async validateConfig(
    engine: TTSEngine,
    config: EdgeTTSConfig | FishTTSConfig | OpenAITTSConfig | CustomTTSConfig
  ): Promise<boolean> {
    try {
      const response = await smartApiCall(api => 
        api.post<{ valid: boolean }>('/api/tts/validate', {
          engine,
          config
        })
      )
      return response.data!.valid
    }
    catch {
      return false
    }
  }

  /**
   * 检查TTS服务健康状态
   */
  async healthCheck(): Promise<boolean> {
    try {
      await smartApiCall(api => 
        api.get('/api/tts/health')
      )
      return true
    }
    catch {
      return false
    }
  }

  /**
   * 获取推荐的TTS配置
   */
  async getRecommendedConfig(): Promise<Partial<TTSConfig>> {
    const response = await smartApiCall(api => 
      api.get<Partial<TTSConfig>>('/api/tts/recommended-config')
    )
    return response.data!
  }

  /**
   * 批量测试所有引擎
   */
  async testAllEngines(text: string = 'Hello, this is a test.'): Promise<Record<TTSEngine, TTSTestResult>> {
    const config = await this.getConfig()
    const results: Record<string, TTSTestResult> = {}
    
    // 测试Edge TTS
    if (config.edge.enabled) {
      try {
        results.edge = await this.testEdgeTTS(config.edge, text)
      }
      catch (error: any) {
        results.edge = {
          success: false,
          error: error.message
        }
      }
    }
    
    // 测试Fish TTS
    if (config.fish.enabled && config.fish.apiKey) {
      try {
        results.fish = await this.testFishTTS(config.fish, text)
      }
      catch (error: any) {
        results.fish = {
          success: false,
          error: error.message
        }
      }
    }
    
    // 测试OpenAI TTS
    if (config.openai.enabled && config.openai.apiKey) {
      try {
        results.openai = await this.testOpenAITTS(config.openai, text)
      }
      catch (error: any) {
        results.openai = {
          success: false,
          error: error.message
        }
      }
    }
    
    // 测试自定义TTS
    if (config.custom.enabled && config.custom.endpoint) {
      try {
        results.custom = await this.testCustomTTS(config.custom, text)
      }
      catch (error: any) {
        results.custom = {
          success: false,
          error: error.message
        }
      }
    }
    
    return results as Record<TTSEngine, TTSTestResult>
  }
}

/**
 * 创建TTS服务实例
 */
export function createTTSService(api: BaseApi): TTSService {
  return new TTSService(api)
}
