/**
 * AI服务API类 - 统一管理AI相关的API调用
 */

import type { BaseApi } from '../base'
import { smartApiCall } from '../index'
import type { 
  AIConfig, 
  AITestRequest, 
  AITestResult, 
  AIProviderStatus,
  AIUsageStats,
  OpenAIConfig,
  AnthropicConfig,
  CustomAPIConfig
} from '../types/ai'

/**
 * AI服务类
 */
export class AIService {
  private api: BaseApi

  constructor(api: BaseApi) {
    this.api = api
  }

  /**
   * 获取AI配置
   */
  async getConfig(): Promise<AIConfig> {
    const response = await smartApiCall(api => 
      api.get<AIConfig>('/api/ai-config')
    )
    return response.data!
  }

  /**
   * 更新AI配置
   */
  async updateConfig(config: AIConfig): Promise<void> {
    await smartApiCall(api => 
      api.put('/api/ai-config', config)
    )
  }

  /**
   * 部分更新AI配置
   */
  async updatePartialConfig(updates: Partial<AIConfig>): Promise<void> {
    await smartApiCall(api => 
      api.patch('/api/ai-config', updates)
    )
  }

  /**
   * 测试AI服务连接
   */
  async testConnection(request: AITestRequest): Promise<AITestResult> {
    const response = await smartApiCall(api => 
      api.post<AITestResult>('/api/ai/test', request)
    )
    return response.data!
  }

  /**
   * 测试OpenAI连接
   */
  async testOpenAI(config: OpenAIConfig, testPrompt?: string): Promise<AITestResult> {
    return await this.testConnection({
      provider: 'openai',
      config,
      testPrompt: testPrompt || 'Hello, this is a test.'
    })
  }

  /**
   * 测试Anthropic连接
   */
  async testAnthropic(config: AnthropicConfig, testPrompt?: string): Promise<AITestResult> {
    return await this.testConnection({
      provider: 'anthropic',
      config,
      testPrompt: testPrompt || 'Hello, this is a test.'
    })
  }

  /**
   * 测试自定义API连接
   */
  async testCustomAPI(config: CustomAPIConfig, testPrompt?: string): Promise<AITestResult> {
    return await this.testConnection({
      provider: 'custom',
      config,
      testPrompt: testPrompt || 'Hello, this is a test.'
    })
  }

  /**
   * 获取AI提供商状态
   */
  async getProviderStatus(): Promise<AIProviderStatus> {
    const response = await smartApiCall(api => 
      api.get<AIProviderStatus>('/api/ai/status')
    )
    return response.data!
  }

  /**
   * 获取可用的AI模型列表
   */
  async getAvailableModels(provider: 'openai' | 'anthropic' | 'custom'): Promise<string[]> {
    const response = await smartApiCall(api => 
      api.get<string[]>(`/api/ai/models/${provider}`)
    )
    return response.data!
  }

  /**
   * 获取AI使用统计
   */
  async getUsageStats(): Promise<AIUsageStats> {
    const response = await smartApiCall(api => 
      api.get<AIUsageStats>('/api/ai/usage')
    )
    return response.data!
  }

  /**
   * 重置AI使用统计
   */
  async resetUsageStats(): Promise<void> {
    await smartApiCall(api => 
      api.post('/api/ai/usage/reset')
    )
  }

  /**
   * 验证API密钥
   */
  async validateApiKey(provider: 'openai' | 'anthropic' | 'custom', apiKey: string): Promise<boolean> {
    try {
      const response = await smartApiCall(api => 
        api.post<{ valid: boolean }>('/api/ai/validate-key', {
          provider,
          apiKey
        })
      )
      return response.data!.valid
    }
    catch {
      return false
    }
  }

  /**
   * 获取推荐的AI配置
   */
  async getRecommendedConfig(): Promise<Partial<AIConfig>> {
    const response = await smartApiCall(api => 
      api.get<Partial<AIConfig>>('/api/ai/recommended-config')
    )
    return response.data!
  }

  /**
   * 检查AI服务健康状态
   */
  async healthCheck(): Promise<boolean> {
    try {
      await smartApiCall(api => 
        api.get('/api/ai/health')
      )
      return true
    }
    catch {
      return false
    }
  }

  /**
   * 获取AI提供商定价信息
   */
  async getPricingInfo(provider: 'openai' | 'anthropic' | 'custom'): Promise<any> {
    const response = await smartApiCall(api => 
      api.get(`/api/ai/pricing/${provider}`)
    )
    return response.data!
  }

  /**
   * 批量测试所有配置的提供商
   */
  async testAllProviders(): Promise<Record<string, AITestResult>> {
    const config = await this.getConfig()
    const results: Record<string, AITestResult> = {}
    
    // 测试OpenAI
    if (config.openai.enabled && config.openai.apiKey) {
      try {
        results.openai = await this.testOpenAI(config.openai)
      }
      catch (error: any) {
        results.openai = {
          success: false,
          error: error.message
        }
      }
    }
    
    // 测试Anthropic
    if (config.anthropic.enabled && config.anthropic.apiKey) {
      try {
        results.anthropic = await this.testAnthropic(config.anthropic)
      }
      catch (error: any) {
        results.anthropic = {
          success: false,
          error: error.message
        }
      }
    }
    
    // 测试自定义API
    if (config.custom.enabled && config.custom.apiKey && config.custom.baseUrl) {
      try {
        results.custom = await this.testCustomAPI(config.custom)
      }
      catch (error: any) {
        results.custom = {
          success: false,
          error: error.message
        }
      }
    }
    
    return results
  }
}

/**
 * 创建AI服务实例
 */
export function createAIService(api: BaseApi): AIService {
  return new AIService(api)
}
