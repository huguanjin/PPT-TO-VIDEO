/**
 * ⚠️⚠️⚠️ 智能字幕服务 - 已废弃 (2025-10-17) ⚠️⚠️⚠️
 * 
 * 后端smart_subtitle_api已移除,项目已简化为单行字幕模式。
 * 此文件保留用于类型定义和向后兼容,但所有API调用将失败。
 * 
 * 迁移建议:
 * - 使用基础字幕生成功能(无AI优化)
 * - 或配置VITE_SUBTITLE_API_PREFIX环境变量指向自定义服务
 * 
 * 提供AI字幕分割、配置管理等功能
 */
import { apiRequest, API_ENDPOINTS } from '@/config/api'

// 废弃警告 - 用于运行时提示
function logDeprecationWarning(method: string) {
  console.warn(`⚠️ [DEPRECATED] SmartSubtitleService.${method}() 已废弃 - smart_subtitle API已在后端移除 (2025-10-17)`)
  console.warn('   迁移建议: 使用基础字幕生成或配置 VITE_SUBTITLE_API_PREFIX')
}

// 智能字幕配置接口
export interface SmartSubtitleConfig {
  enabled: boolean
  max_length: number
  target_multiplier: number
  smart_split: boolean
  use_ai_splitting: boolean
  character_weights: {
    chinese: number
    japanese: number
    korean: number
    english: number
    punctuation: number
    space: number
    number: number
  }
  punctuation_priority: Record<string, number>
  semantic_splitting: {
    enabled: boolean
    look_ahead_chars: number
    min_priority_threshold: number
  }
  ai_config: {
    service_type: string
    api_key: string
    model: string
    base_url: string
    timeout: number
    max_retries: number
  }
}

// AI配置接口
export interface AIConfig {
  service_type: 'openai' | 'anthropic' | 'custom'
  api_key: string
  model: string
  base_url?: string
  timeout?: number
  max_retries?: number
  support_json?: boolean
}

// 分割测试结果接口
export interface SplitTestResult {
  original_text: string
  split_result: string[]
  lines_detail: Array<{
    text: string
    length: number
    weight: number
    is_valid: boolean
  }>
  metrics: {
    original_weight: number
    split_count: number
    total_weight: number
    max_line_weight: number
    min_line_weight: number
    avg_line_weight: number
    weight_distribution: 'balanced' | 'moderate' | 'unbalanced'
    processing_method: 'ai' | 'rule'
    processed_at: string
  }
  processing_method: string
}

// 文本权重计算结果接口
export interface TextWeightResult {
  text: string
  total_weight: number
  character_count: number
  average_weight: number
  char_details: Array<{
    char: string
    position: number
    weight: number
    unicode: number
    category: string
  }>
}

// 功能状态接口
export interface SmartSubtitleStatus {
  config_status: {
    netflix_config_exists: boolean
    tts_config_exists: boolean
    smart_config_valid: boolean
    config_errors: string[]
    ai_splitting_available: boolean
    smart_processing_enabled: boolean
    config_dir: string
    last_checked: string | null
  }
  modules_status: {
    subtitle_utils: boolean
    ai_subtitle_splitter: boolean
    subtitle_config_loader: boolean
  }
  features: {
    smart_splitting: boolean
    character_weights: boolean
    semantic_splitting: boolean
    ai_splitting: boolean
    config_management: boolean
  }
}

class SmartSubtitleService {
  /**
   * 获取智能字幕配置
   * @deprecated API已移除
   */
  async getConfig(): Promise<SmartSubtitleConfig> {
    logDeprecationWarning('getConfig')
    const response = await apiRequest<{ config: SmartSubtitleConfig }>(
      API_ENDPOINTS.SMART_SUBTITLE.CONFIG
    )
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取配置失败')
    }
    
    return response.data.config
  }

  /**
   * 更新智能字幕配置
   * @deprecated API已移除
   */
  async updateConfig(config: Partial<SmartSubtitleConfig>): Promise<void> {
    logDeprecationWarning('updateConfig')
    const response = await apiRequest(API_ENDPOINTS.SMART_SUBTITLE.CONFIG, {
      method: 'POST',
      body: JSON.stringify(config)
    })
    
    if (!response.success) {
      throw new Error(response.error || '配置更新失败')
    }
  }

  /**
   * 测试字幕分割功能
   * @deprecated API已移除
   */
  async testSplit(text: string, config?: Partial<SmartSubtitleConfig>): Promise<SplitTestResult> {
    logDeprecationWarning('testSplit')
    const response = await apiRequest<{ result: SplitTestResult }>(
      API_ENDPOINTS.SMART_SUBTITLE.TEST_SPLIT,
      {
        method: 'POST',
        body: JSON.stringify({ text, config: config || {} })
      }
    )
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '分割测试失败')
    }
    
    return response.data.result
  }

  /**
   * 计算文本显示权重
   * @deprecated API已移除
   */
  async calculateTextWeight(text: string): Promise<TextWeightResult> {
    logDeprecationWarning('calculateTextWeight')
    const response = await apiRequest<TextWeightResult>(
      API_ENDPOINTS.SMART_SUBTITLE.WEIGHT_CALC,
      {
        method: 'POST',
        body: JSON.stringify({ text })
      }
    )
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '权重计算失败')
    }
    
    return response.data
  }

  /**
   * 获取功能状态
   * @deprecated API已移除
   */
  async getStatus(): Promise<SmartSubtitleStatus> {
    logDeprecationWarning('getStatus')
    const response = await apiRequest<SmartSubtitleStatus>(
      API_ENDPOINTS.SMART_SUBTITLE.STATUS
    )
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取状态失败')
    }
    
    return response.data
  }

  /**
   * 获取AI配置
   */
  async getAIConfig(): Promise<{
    ai_config: AIConfig
    ai_enabled: boolean
    ai_available: boolean
    validation?: {
      is_valid: boolean
      issues: string[]
    }
    display_info?: Record<string, string>
  }> {
    const response = await apiRequest<{
      enabled: boolean
      ai_config: AIConfig
      validation: {
        is_valid: boolean
        issues: string[]
      }
      display_info: Record<string, string>
    }>(API_ENDPOINTS.AI_CONFIG.GET)
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取AI配置失败')
    }
    
    return {
      ai_config: response.data.ai_config,
      ai_enabled: response.data.enabled,
      ai_available: response.data.validation.is_valid,
      validation: response.data.validation,
      display_info: response.data.display_info
    }
  }

  /**
   * 更新AI配置
   */
  async updateAIConfig(config: { enabled: boolean; ai_config?: AIConfig }): Promise<void> {
    const response = await apiRequest(API_ENDPOINTS.AI_CONFIG.UPDATE, {
      method: 'POST',
      body: JSON.stringify(config)
    })
    
    if (!response.success) {
      throw new Error(response.error || 'AI配置更新失败')
    }
  }

  /**
   * 验证API密钥是否有效
   */
  async validateAPIKey(config: AIConfig): Promise<boolean> {
    try {
      const response = await apiRequest<{
        is_valid: boolean
        test_result?: string
      }>(API_ENDPOINTS.AI_CONFIG.VALIDATE, {
        method: 'POST',
        body: JSON.stringify({ ai_config: config })
      })
      
      return response.success && response.data?.is_valid === true
    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('API密钥验证失败:', error)
      return false
    }
  }

  /**
   * 获取可用的AI服务列表
   */
  async getAvailableServices(): Promise<Record<string, {
    name: string
    description: string
    default_base_url: string
    models: Array<{
      value: string
      label: string
      description: string
    }>
    supports_json: boolean
    note?: string
  }>> {
    const response = await apiRequest<Record<string, any>>(
      API_ENDPOINTS.AI_CONFIG.SERVICES
    )
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取AI服务列表失败')
    }
    
    return response.data
  }

  /**
   * 测试AI分割功能
   */
  async testAISplit(text: string, aiConfig: AIConfig, maxWeight: number = 75): Promise<{
    original_text: string
    split_result: string[]
    lines_count: number
    test_params: {
      max_weight: number
      service_type: string
      model: string
    }
  }> {
    const response = await apiRequest<{
      original_text: string
      split_result: string[]
      lines_count: number
      test_params: {
        max_weight: number
        service_type: string
        model: string
      }
    }>(API_ENDPOINTS.AI_CONFIG.TEST, {
      method: 'POST',
      body: JSON.stringify({
        text,
        ai_config: aiConfig,
        max_weight: maxWeight
      })
    })
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'AI分割测试失败')
    }
    
    return response.data
  }

  /**
   * 获取推荐的配置参数
   */
  getRecommendedConfig(): Partial<SmartSubtitleConfig> {
    return {
      enabled: true,
      max_length: 75,
      target_multiplier: 1.2,
      smart_split: true,
      use_ai_splitting: false, // 默认不启用AI，需要用户手动配置
      character_weights: {
        chinese: 1.75,
        japanese: 1.75,
        korean: 1.5,
        english: 1.0,
        punctuation: 0.8,
        space: 0.5,
        number: 0.8
      },
      semantic_splitting: {
        enabled: true,
        look_ahead_chars: 10,
        min_priority_threshold: 6
      }
    }
  }

  /**
   * 检查配置是否有效
   */
  validateConfig(config: Partial<SmartSubtitleConfig>): { isValid: boolean; errors: string[] } {
    const errors: string[] = []

    if (config.max_length !== undefined && (config.max_length <= 0 || config.max_length > 200)) {
      errors.push('最大长度必须在1-200之间')
    }

    if (config.target_multiplier !== undefined && (config.target_multiplier <= 1 || config.target_multiplier > 3)) {
      errors.push('目标倍数必须在1-3之间')
    }

    if (config.use_ai_splitting && (!config.ai_config || !config.ai_config.api_key)) {
      errors.push('启用AI分割时必须提供API密钥')
    }

    return {
      isValid: errors.length === 0,
      errors
    }
  }
}

// 导出服务实例
export const smartSubtitleService = new SmartSubtitleService()

// 导出便捷函数
export const {
  getConfig: getSmartSubtitleConfig,
  updateConfig: updateSmartSubtitleConfig,
  testSplit: testSmartSubtitleSplit,
  calculateTextWeight,
  getStatus: getSmartSubtitleStatus,
  getAIConfig,
  updateAIConfig,
  validateAPIKey,
  getRecommendedConfig,
  validateConfig: validateSmartSubtitleConfig,
  getAvailableServices,
  testAISplit
} = smartSubtitleService

export default smartSubtitleService
