/**
 * AI服务相关类型定义
 */

/**
 * OpenAI配置
 */
export interface OpenAIConfig {
  apiKey: string
  baseUrl?: string
  model?: string
  temperature?: number
  maxTokens?: number
  enabled: boolean
}

/**
 * Anthropic配置
 */
export interface AnthropicConfig {
  apiKey: string
  baseUrl?: string
  model?: string
  temperature?: number
  maxTokens?: number
  enabled: boolean
}

/**
 * 自定义API配置
 */
export interface CustomAPIConfig {
  apiKey: string
  baseUrl: string
  model: string
  temperature?: number
  maxTokens?: number
  headers?: Record<string, string>
  enabled: boolean
}

/**
 * 完整AI配置
 */
export interface AIConfig {
  openai: OpenAIConfig
  anthropic: AnthropicConfig
  custom: CustomAPIConfig
  defaultProvider: 'openai' | 'anthropic' | 'custom'
  timeout?: number
}

/**
 * AI连接测试请求
 */
export interface AITestRequest {
  provider: 'openai' | 'anthropic' | 'custom'
  config: OpenAIConfig | AnthropicConfig | CustomAPIConfig
  testPrompt?: string
}

/**
 * AI连接测试结果
 */
export interface AITestResult {
  success: boolean
  response?: string
  latency?: number
  error?: string
  details?: {
    model?: string
    tokensUsed?: number
    cost?: number
  }
}

/**
 * AI提供商状态
 */
export interface AIProviderStatus {
  openai: {
    available: boolean
    models: string[]
    lastChecked?: string
  }
  anthropic: {
    available: boolean
    models: string[]
    lastChecked?: string
  }
  custom: {
    available: boolean
    endpoint?: string
    lastChecked?: string
  }
}

/**
 * AI使用统计
 */
export interface AIUsageStats {
  totalRequests: number
  successfulRequests: number
  failedRequests: number
  totalTokens: number
  estimatedCost: number
  lastUsed?: string
}
