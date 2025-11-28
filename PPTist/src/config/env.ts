/**
 * 环境配置管理
 */

import type { RequestConfig } from '../api/types/common'

/**
 * 环境类型
 */
export type Environment = 'development' | 'production' | 'test'

/**
 * 环境配置接口
 */
export interface EnvironmentConfig {
  API_BASE_URL: string
  API_FALLBACK_URL?: string
  TIMEOUT: number
  RETRY_TIMES: number
  RETRY_DELAY: number
  DEBUG_MODE: boolean
  API_LOGGING: boolean
}

/**
 * 环境配置映射
 */
const ENV_CONFIGS: Record<Environment, EnvironmentConfig> = {
  development: {
    API_BASE_URL: 'http://localhost:5000',
    API_FALLBACK_URL: 'http://localhost:5000',
    TIMEOUT: 30000,
    RETRY_TIMES: 3,
    RETRY_DELAY: 1000,
    DEBUG_MODE: true,
    API_LOGGING: true
  },
  production: {
    API_BASE_URL: 'https://api.pptist.com',
    API_FALLBACK_URL: undefined,
    TIMEOUT: 10000,
    RETRY_TIMES: 2,
    RETRY_DELAY: 500,
    DEBUG_MODE: false,
    API_LOGGING: false
  },
  test: {
    API_BASE_URL: 'http://localhost:5000',
    API_FALLBACK_URL: 'http://localhost:5000',
    TIMEOUT: 5000,
    RETRY_TIMES: 1,
    RETRY_DELAY: 100,
    DEBUG_MODE: true,
    API_LOGGING: true
  }
}

/**
 * 获取当前环境
 */
export function getCurrentEnvironment(): Environment {
  const env = import.meta.env.MODE as Environment
  return env in ENV_CONFIGS ? env : 'development'
}

/**
 * 获取环境配置
 */
export function getEnvironmentConfig(env?: Environment): EnvironmentConfig {
  const currentEnv = env || getCurrentEnvironment()
  return ENV_CONFIGS[currentEnv]
}

/**
 * 从环境变量和默认配置合并生成最终配置
 */
export function createRequestConfig(env?: Environment): RequestConfig {
  const envConfig = getEnvironmentConfig(env)
  
  // 优先使用环境变量，然后使用默认配置
  const baseURL = import.meta.env.VITE_API_BASE_URL || envConfig.API_BASE_URL
  const timeout = Number(import.meta.env.VITE_API_TIMEOUT) || envConfig.TIMEOUT
  const retryTimes = Number(import.meta.env.VITE_API_RETRY_TIMES) || envConfig.RETRY_TIMES
  const retryDelay = Number(import.meta.env.VITE_API_RETRY_DELAY) || envConfig.RETRY_DELAY
  
  return {
    baseURL,
    timeout,
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Version': import.meta.env.VITE_APP_VERSION || '1.0.0',
      'X-Environment': getCurrentEnvironment()
    },
    retry: {
      times: retryTimes,
      delay: retryDelay
    }
  }
}

/**
 * 获取备用API配置（用于降级）
 */
export function getFallbackRequestConfig(env?: Environment): RequestConfig | null {
  const envConfig = getEnvironmentConfig(env)
  
  if (!envConfig.API_FALLBACK_URL) {
    return null
  }
  
  const fallbackURL = import.meta.env.VITE_API_FALLBACK_URL || envConfig.API_FALLBACK_URL
  
  return {
    baseURL: fallbackURL,
    timeout: envConfig.TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Version': import.meta.env.VITE_APP_VERSION || '1.0.0',
      'X-Environment': getCurrentEnvironment(),
      'X-Fallback': 'true'
    },
    retry: {
      times: 1, // 备用服务器重试次数减少
      delay: envConfig.RETRY_DELAY
    }
  }
}

/**
 * 检查是否启用调试模式
 */
export function isDebugMode(): boolean {
  const envConfig = getEnvironmentConfig()
  return import.meta.env.DEV || envConfig.DEBUG_MODE
}

/**
 * 检查是否启用API日志
 */
export function isApiLoggingEnabled(): boolean {
  const envConfig = getEnvironmentConfig()
  return envConfig.API_LOGGING
}

/**
 * 获取API端点前缀配置
 */
export function getApiEndpoints() {
  return {
    AI: import.meta.env.VITE_AI_API_PREFIX || '/api/ai',
    TTS: import.meta.env.VITE_TTS_API_PREFIX || '/api/tts',
    WORKFLOW: import.meta.env.VITE_WORKFLOW_API_PREFIX || '/api/workflow',
    CONFIG: import.meta.env.VITE_CONFIG_API_PREFIX || '/api/config',
    PPTIST: import.meta.env.VITE_PPTIST_API_PREFIX || '/api/pptist',
    // ⚠️ SUBTITLE: 智能字幕API已移除，如需使用请配置环境变量指向其他服务
    SUBTITLE: import.meta.env.VITE_SUBTITLE_API_PREFIX || ''
  }
}

/**
 * 配置验证函数
 */
export function validateConfig(config: RequestConfig): boolean {
  try {
    // 验证基础URL格式
    new URL(config.baseURL)
    
    // 验证超时时间
    if (config.timeout && (config.timeout < 1000 || config.timeout > 60000)) {
      return false
    }
    
    // 验证重试配置
    if (config.retry) {
      if (config.retry.times < 0 || config.retry.times > 10) {
        return false
      }
      if (config.retry.delay < 0 || config.retry.delay > 10000) {
        return false
      }
    }
    
    return true
  }
  catch (error) {
    return false
  }
}
