/**
 * 统一配置API客户端 - 阶段一：API端点标准化
 * 提供标准化的配置管理接口
 */

import { apiRequest, API_ENDPOINTS } from '@/config/api'

// 类型定义
export interface VideoConfig {
  resolution: string
  fps: number
  bitrate: string
  background_color: string
  include_subtitles: boolean
}

export interface SubtitleConfig {
  enabled: boolean
  font_family: string
  font_size: number
  font_color: string
  background_color: string
  position: string
  enhanced_settings: {
    use_enhanced_mode: boolean
    enable_precise_alignment: boolean
    enable_gap_filling: boolean
    max_chars_per_line: number
    auto_punctuation_removal: boolean
  }
}

export interface TTSEngineConfig {
  voice?: string
  rate?: string
  pitch?: string
  api_key?: string
  character?: string
  character_id?: string
  character_name?: string
  region?: string
}

export interface TTSConfig {
  preferred_engine: 'edge_tts' | 'fish_tts' | 'azure_tts'
  engines: {
    edge_tts: TTSEngineConfig
    fish_tts: TTSEngineConfig
    azure_tts: TTSEngineConfig
  }
  common: {
    sample_rate: number
    max_retries: number
    timeout: number
  }
}

export interface AIServiceConfig {
  api_key: string
  base_url: string
  model: string
  timeout: number
  max_retries: number
  support_json?: boolean
}

export interface AIConfig {
  default_service: 'openai' | 'anthropic' | 'custom'
  services: {
    openai: AIServiceConfig
    anthropic: AIServiceConfig
    custom: AIServiceConfig
  }
  processing: {
    source_language: string
    target_language: string
    max_workers: number
  }
}

export interface AdvancedConfig {
  output_path: string
  naming_rule: 'timestamp' | 'title' | 'custom'
  auto_clean_temp: boolean
  enable_progress: boolean
  max_concurrency: number
  memory_limit: number
}

export interface UnifiedConfig {
  video: VideoConfig
  subtitle: SubtitleConfig
  tts: TTSConfig
  ai: AIConfig
  advanced: AdvancedConfig
}

export interface ConfigMetadata {
  last_updated?: string
  version?: string
  source?: string
  preset_key?: string
}

export interface ConfigValidationResult {
  valid: boolean
  errors: string[]
  message: string
}

export interface ConfigSchema {
  version: string
  description: string
  sections: {
    [key: string]: {
      description: string
      required_fields?: string[]
      optional_fields?: string[]
      field_types?: {
        [field: string]: string
      }
    }
  }
}

// 阶段二：实时验证和测试相关类型定义

export interface ValidationResponse {
  success: boolean
  data: {
    is_valid: boolean
    errors: ValidationError[]
    warnings: ValidationWarning[]
    suggestions: ValidationSuggestion[]
    performance_score: number
    validation_time: number
    timestamp: string
  }
}

export interface ValidationError {
  field: string
  message: string
  severity: 'error' | 'warning' | 'info'
  code?: string
}

export interface ValidationWarning {
  field: string
  message: string
  suggestion?: string
}

export interface ValidationSuggestion {
  type: string
  message: string
  field?: string
  suggested_value?: any
}

export interface ConflictResponse {
  success: boolean
  data: {
    has_conflicts: boolean
    conflicts: Conflict[]
    severity: 'low' | 'medium' | 'high' | 'critical'
    impact_description: string
  }
}

export interface Conflict {
  type: string
  fields: string[]
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  suggested_resolution?: string
}

export interface PerformanceResponse {
  success: boolean
  data: {
    performance_suggestions: string[]
    estimated_processing_time: string
    resource_usage: string
    analysis_time: number
    timestamp: string
  }
}

export interface ValidationHistoryResponse {
  success: boolean
  data: {
    history: ValidationHistoryItem[]
    total_validations: number
  }
}

export interface ValidationHistoryItem {
  is_valid: boolean
  error_count: number
  warning_count: number
  suggestion_count: number
  performance_score: number
  validation_time: number
  timestamp: string
}

export interface RecoveryResponse {
  success: boolean
  data: {
    suggestions: RecoverySuggestion[]
    error_type: string
    context: any
    timestamp: string
  }
}

export interface RecoverySuggestion {
  type: string
  description: string
  action: string
  priority: 'low' | 'medium' | 'high'
}

export interface ApplyRecoveryResponse {
  success: boolean
  data: {
    action_applied: string
    success: boolean
    message: string
    new_config?: UnifiedConfig
  }
}

/**
 * 统一配置API客户端类
 */
export class UnifiedConfigAPI {
  /**
   * 获取完整配置
   */
  static async getUnifiedConfig(): Promise<{
    config: UnifiedConfig
    metadata: ConfigMetadata
  }> {
    const response = await apiRequest<{
      config: UnifiedConfig
      metadata: ConfigMetadata
    }>(API_ENDPOINTS.UNIFIED_CONFIG.GET)
    
    if (response.success && response.data) {
      return response.data
    }
    
    throw new Error(response.message || '获取配置失败')
  }

  /**
   * 保存完整配置
   */
  static async saveUnifiedConfig(
    config: UnifiedConfig,
    metadata?: {
      name?: string
      description?: string
      tags?: string[]
    }
  ): Promise<string> {
    const response = await apiRequest<{ config_id: string }>(
      API_ENDPOINTS.UNIFIED_CONFIG.SAVE,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config,
          ...metadata
        })
      }
    )
    
    if (response.success && response.data) {
      return response.data.config_id
    }
    
    throw new Error(response.message || '保存配置失败')
  }

  /**
   * 更新配置段落
   */
  static async updateConfigSection(
    section: keyof UnifiedConfig,
    sectionConfig: any
  ): Promise<{
    config_id?: string
    section: string
    message: string
  }> {
    const response = await apiRequest<{
      config_id?: string
      section: string
      message: string
    }>(API_ENDPOINTS.UNIFIED_CONFIG.UPDATE_SECTION, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        section,
        config: sectionConfig
      })
    })
    
    if (response.success && response.data) {
      return response.data
    }
    
    throw new Error(response.message || '更新配置段落失败')
  }

  /**
   * 获取配置结构定义
   */
  static async getConfigSchema(): Promise<ConfigSchema> {
    const response = await apiRequest<{ schema: ConfigSchema }>(
      API_ENDPOINTS.UNIFIED_CONFIG.SCHEMA
    )
    
    if (response.success && response.data) {
      return response.data.schema
    }
    
    throw new Error(response.message || '获取配置结构定义失败')
  }

  /**
   * 验证配置
   */
  static async validateConfig(config: UnifiedConfig): Promise<ConfigValidationResult> {
    const response = await apiRequest<ConfigValidationResult>(
      API_ENDPOINTS.UNIFIED_CONFIG.VALIDATE,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config
        })
      }
    )
    
    if (response.success && response.data) {
      return response.data
    }
    
    throw new Error(response.message || '验证配置失败')
  }

  // 阶段二：实时验证和测试API

  /**
   * 实时验证配置
   */
  static async validateRealtime(config: UnifiedConfig): Promise<ValidationResponse> {
    const response = await apiRequest<ValidationResponse['data']>(
      '/api/validation/validate/realtime',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config })
      }
    )
    
    if (response.success && response.data) {
      return { success: true, data: response.data }
    }
    
    throw new Error(response.message || '实时验证失败')
  }

  /**
   * 检测配置冲突
   */
  static async detectConflicts(config: UnifiedConfig): Promise<ConflictResponse> {
    const response = await apiRequest<ConflictResponse['data']>(
      '/api/validation/conflicts/detect',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config })
      }
    )
    
    if (response.success && response.data) {
      return { success: true, data: response.data }
    }
    
    throw new Error(response.message || '冲突检测失败')
  }

  /**
   * 性能分析
   */
  static async analyzePerformance(config: UnifiedConfig): Promise<PerformanceResponse> {
    const response = await apiRequest<PerformanceResponse['data']>(
      '/api/validation/performance/analyze',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config })
      }
    )
    
    if (response.success && response.data) {
      return { success: true, data: response.data }
    }
    
    throw new Error(response.message || '性能分析失败')
  }

  /**
   * 获取验证历史
   */
  static async getValidationHistory(limit?: number): Promise<ValidationHistoryResponse> {
    const params = limit ? `?limit=${limit}` : ''
    const response = await apiRequest<ValidationHistoryResponse['data']>(
      `/api/validation/validation/history${params}`
    )
    
    if (response.success && response.data) {
      return { success: true, data: response.data }
    }
    
    throw new Error(response.message || '获取验证历史失败')
  }

  /**
   * 获取错误恢复建议
   */
  static async getRecoverySuggestions(errorType: string, context: any): Promise<RecoveryResponse> {
    const response = await apiRequest<RecoveryResponse['data']>(
      '/api/validation/recovery/suggest',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ error_type: errorType, context })
      }
    )
    
    if (response.success && response.data) {
      return { success: true, data: response.data }
    }
    
    throw new Error(response.message || '获取恢复建议失败')
  }

  /**
   * 应用恢复操作
   */
  static async applyRecovery(action: string, context: any): Promise<ApplyRecoveryResponse> {
    const response = await apiRequest<ApplyRecoveryResponse['data']>(
      '/api/validation/recovery/apply',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action, context })
      }
    )
    
    if (response.success && response.data) {
      return { success: true, data: response.data }
    }
    
    throw new Error(response.message || '应用恢复操作失败')
  }

  /**
   * 获取默认配置
   */
  static getDefaultConfig(): UnifiedConfig {
    return {
      video: {
        resolution: '1920x1080',
        fps: 30,
        bitrate: '2000k',
        background_color: '#ffffff',
        include_subtitles: true
      },
      subtitle: {
        enabled: true,
        font_family: '微软雅黑',
        font_size: 24,
        font_color: '#ffffff',
        background_color: '#000000',
        position: 'bottom',
        enhanced_settings: {
          use_enhanced_mode: false,
          enable_precise_alignment: false,
          enable_gap_filling: false,
          max_chars_per_line: 40,
          auto_punctuation_removal: false
        }
      },
      tts: {
        preferred_engine: 'edge_tts',
        engines: {
          edge_tts: {
            voice: 'zh-CN-XiaoxiaoNeural',
            rate: '+0%',
            pitch: '+0Hz'
          },
          fish_tts: {
            api_key: '',
            character: 'default',
            character_id: '',
            character_name: 'Default'
          },
          azure_tts: {
            api_key: '',
            region: '',
            voice: 'zh-CN-XiaoxiaoNeural'
          }
        },
        common: {
          sample_rate: 44100,
          max_retries: 3,
          timeout: 30
        }
      },
      ai: {
        default_service: 'openai',
        services: {
          openai: {
            api_key: '',
            base_url: 'https://api.openai.com',
            model: 'gpt-3.5-turbo',
            timeout: 300,
            max_retries: 3,
            support_json: true
          },
          anthropic: {
            api_key: '',
            base_url: 'https://api.anthropic.com',
            model: 'claude-3-sonnet-20240229',
            timeout: 300,
            max_retries: 3
          },
          custom: {
            api_key: '',
            base_url: '',
            model: '',
            timeout: 300,
            max_retries: 3,
            support_json: true
          }
        },
        processing: {
          source_language: '中文',
          target_language: '中文',
          max_workers: 4
        }
      },
      advanced: {
        output_path: '',
        naming_rule: 'timestamp',
        auto_clean_temp: true,
        enable_progress: true,
        max_concurrency: 4,
        memory_limit: 2048
      }
    }
  }

  /**
   * 合并配置 - 深度合并两个配置对象
   */
  static mergeConfigs(baseConfig: UnifiedConfig, updateConfig: Partial<UnifiedConfig>): UnifiedConfig {
    const merged = JSON.parse(JSON.stringify(baseConfig)) // 深拷贝
    
    Object.keys(updateConfig).forEach(key => {
      const configKey = key as keyof UnifiedConfig
      if (updateConfig[configKey]) {
        if (typeof updateConfig[configKey] === 'object' && !Array.isArray(updateConfig[configKey])) {
          merged[configKey] = {
            ...merged[configKey],
            ...updateConfig[configKey]
          }
        }
        else {
          merged[configKey] = updateConfig[configKey] as any
        }
      }
    })
    
    return merged
  }

  /**
   * 比较配置差异
   */
  static compareConfigs(config1: UnifiedConfig, config2: UnifiedConfig): {
    identical: boolean
    differences: string[]
  } {
    const differences: string[] = []
    
    const compare = (obj1: any, obj2: any, path: string = '') => {
      Object.keys(obj1).forEach(key => {
        const currentPath = path ? `${path}.${key}` : key
        
        if (!(key in obj2)) {
          differences.push(`缺少字段: ${currentPath}`)
        }
        else if (typeof obj1[key] !== typeof obj2[key]) {
          differences.push(`类型不匹配: ${currentPath}`)
        }
        else if (typeof obj1[key] === 'object' && obj1[key] !== null) {
          compare(obj1[key], obj2[key], currentPath)
        }
        else if (obj1[key] !== obj2[key]) {
          differences.push(`值不同: ${currentPath} (${obj1[key]} != ${obj2[key]})`)
        }
      })
    }
    
    compare(config1, config2)
    
    return {
      identical: differences.length === 0,
      differences
    }
  }
}

/**
 * 配置工具函数
 */
export const ConfigUtils = {
  /**
   * 设置嵌套对象的值
   */
  setNestedValue(obj: any, path: string, value: any): void {
    const keys = path.split('.')
    let current = obj
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i]
      if (!(key in current) || typeof current[key] !== 'object') {
        current[key] = {}
      }
      current = current[key]
    }
    
    current[keys[keys.length - 1]] = value
  },

  /**
   * 获取嵌套对象的值
   */
  getNestedValue(obj: any, path: string): any {
    const keys = path.split('.')
    let current = obj
    
    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key]
      }
      else {
        return undefined
      }
    }
    
    return current
  },

  /**
   * 验证配置字段
   */
  validateField(value: any, type: string): boolean {
    switch (type) {
      case 'string':
        return typeof value === 'string'
      case 'integer':
        return typeof value === 'number' && Number.isInteger(value)
      case 'number':
        return typeof value === 'number'
      case 'boolean':
        return typeof value === 'boolean'
      case 'object':
        return typeof value === 'object' && value !== null
      case 'array':
        return Array.isArray(value)
      default:
        return true
    }
  }
}

export default UnifiedConfigAPI
