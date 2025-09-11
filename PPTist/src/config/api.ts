/**
 * API配置文件 - 统一管理后端API地址
 * 适配VideoLingo技术融合主入口
 */

// 从环境变量获取API基础URL，默认指向VideoLingo技术融合主入口
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8004'

// 备用API地址（传统Flask应用）
export const API_FALLBACK_URL: string = import.meta.env.VITE_API_FALLBACK_URL || 'http://localhost:5000'

// 后端服务配置
export const API_CONFIG = {
  // Flask后端基础URL
  BASE_URL: API_BASE_URL,
  
  // API超时时间（毫秒）
  TIMEOUT: 30000,
  
  // 重试配置
  RETRY: {
    times: 3,
    delay: 1000
  },
  
  // 开发模式配置
  DEBUG: import.meta.env.DEV,
  
  // 请求头配置
  headers: {
    'Content-Type': 'application/json',
  }
} as const

// API端点配置
export const API_ENDPOINTS = {
  // 健康检查
  HEALTH: '/health',
  INFO: '/info',
  DOCS: '/docs',
  
  // PPTist相关API
  PPTIST: {
    IMPORT: '/api/pptist/import',
    STATUS: (taskId: string) => `/api/pptist/status/${taskId}`,
    PROJECTS: '/api/pptist/projects',
    PROJECT: (projectName: string) => `/api/pptist/project/${projectName}`,
    UPLOAD_IMAGES: '/api/pptist/upload-native-images'
  },
  
  // 项目管理API (Flask统一接口)
  PROJECT: {
    LIST: '/api/project/list',
    GET: (projectName: string) => `/api/project/${projectName}`,
    CREATE: '/api/project/create', 
    UPDATE: (projectName: string) => `/api/project/${projectName}`,
    DELETE: (projectName: string) => `/api/project/${projectName}`,
    DUPLICATE: (projectName: string) => `/api/project/${projectName}/duplicate`,
    DOWNLOAD: (projectName: string) => `/api/project/${projectName}/download`
  },
  
  // 工作流API
  WORKFLOW: {
    START: '/api/workflow/start',
    STATUS: (taskId: string) => `/api/workflow/status/${taskId}`,
    RESULT: (taskId: string) => `/api/workflow/result/${taskId}`,
    DOWNLOAD: (taskId: string) => `/api/workflow/download/${taskId}`,
    CANCEL: (taskId: string) => `/api/workflow/cancel/${taskId}`,
    CONFIG: '/api/workflow/config'
  },

  // 智能字幕API
  SMART_SUBTITLE: {
    CONFIG: '/api/smart-subtitle/config',
    TEST_SPLIT: '/api/smart-subtitle/test-split',
    AI_CONFIG: '/api/smart-subtitle/ai-config',
    STATUS: '/api/smart-subtitle/status',
    WEIGHT_CALC: '/api/smart-subtitle/weight-calculator'
  },

  // AI配置API
  AI_CONFIG: {
    GET: '/api/ai-config',
    UPDATE: '/api/ai-config',
    VALIDATE: '/api/ai-config/validate',
    SERVICES: '/api/ai-config/services',
    SERVICE_MODELS: (service: string) => `/api/ai-config/services/${service}/models`,
    ADD_MODEL: (service: string) => `/api/ai-config/services/${service}/models`,
    TEST: '/api/ai-config/test',
    RESET: '/api/ai-config/reset'
  },

  // 统一配置API (阶段一：API端点标准化)
  UNIFIED_CONFIG: {
    GET: '/api/config/unified',
    SAVE: '/api/config/unified',
    UPDATE_SECTION: '/api/config/unified/section',
    SCHEMA: '/api/config/schema',
    VALIDATE: '/api/config/validate'
  },

  // 兼容旧的端点配置（逐步废弃）
  TTS_PREVIEW: '/api/tts/preview',
  TTS_CONFIG: '/api/config/tts',
  PPT_SAVE: '/api/ppt/save',
  PPT_LOAD: '/api/ppt/load',
  PPT_LIST: '/api/ppt/list',
  PPT_DELETE: '/api/ppt/delete',
  PPT_AUTO_SAVE: '/api/ppt/auto-save',
  WORKFLOW_START: '/api/workflow/start',
  WORKFLOW_STATUS: '/api/workflow/status',
  CONFIG_GET: '/api/config',
  CONFIG_UPDATE: '/api/config',
  IMPORT_PPT: '/api/import',
  EXPORT_VIDEO: '/api/export'
} as const

// 构建完整API URL
export const buildApiUrl = (endpoint: string): string => {
  const baseUrl = API_CONFIG.BASE_URL.replace(/\/$/, '') // 移除末尾的斜杠
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${baseUrl}${cleanEndpoint}`
}

// API请求配置
export const getRequestConfig = (options: RequestInit = {}): RequestInit => {
  return {
    headers: {
      ...API_CONFIG.headers,
      ...options.headers,
    },
    ...options,
  }
}

// API响应类型定义
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error?: string
}

// 统一的API请求错误类
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * 统一的API请求函数
 */
export async function apiRequest<T = any>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = buildApiUrl(endpoint)
  const config = getRequestConfig(options)
  
  if (API_CONFIG.DEBUG) {
    // eslint-disable-next-line no-console
    console.log(`🚀 API请求: ${config.method || 'GET'} ${url}`)
  }
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)
    
    const response = await fetch(url, {
      ...config,
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData.error
      )
    }
    
    const data = await response.json()
    
    if (API_CONFIG.DEBUG) {
      // eslint-disable-next-line no-console
      console.log(`✅ API响应:`, data)
    }
    
    return data
  }
  catch (error) {
    if (API_CONFIG.DEBUG) {
      // eslint-disable-next-line no-console
      console.error(`❌ API请求失败 ${endpoint}:`, error)
    }
    
    if (error instanceof ApiError) {
      throw error
    }
    
    throw new ApiError(
      error instanceof Error ? error.message : '网络请求失败',
      0,
      'NETWORK_ERROR'
    )
  }
}

/**
 * 带重试的API请求
 */
export async function apiRequestWithRetry<T = any>(
  endpoint: string,
  options: RequestInit = {},
  retryTimes = API_CONFIG.RETRY.times
): Promise<ApiResponse<T>> {
  let lastError: ApiError | null = null
  
  for (let i = 0; i <= retryTimes; i++) {
    try {
      return await apiRequest<T>(endpoint, options)
    }
    catch (error) {
      lastError = error instanceof ApiError ? error : new ApiError('Unknown error')
      
      if (i < retryTimes) {
        if (API_CONFIG.DEBUG) {
          // eslint-disable-next-line no-console
          console.log(`🔄 API请求重试 ${i + 1}/${retryTimes}: ${endpoint}`)
        }
        await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY.delay))
      }
    }
  }
  
  throw lastError
}

// 开发模式下的调试信息
if (import.meta.env.DEV) {
  // eslint-disable-next-line no-console
  console.log('🔧 API配置信息:')
  // eslint-disable-next-line no-console
  console.log('  基础URL:', API_BASE_URL)
  // eslint-disable-next-line no-console
  console.log('  Flask后端:', API_CONFIG.BASE_URL)
  // eslint-disable-next-line no-console
  console.log('  模式:', import.meta.env.MODE)
}

/**
 * 获取完整的API URL
 */
export const getApiUrl = (endpoint: string): string => {
  // 如果endpoint已经是完整URL，直接返回
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint
  }
  
  // 确保endpoint以/开头
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  
  return `${API_BASE_URL}${path}`
}

/**
 * 检查API服务是否可用
 */
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(getApiUrl(API_ENDPOINTS.HEALTH), {
      method: 'GET',
      headers: API_CONFIG.headers,
    })
    return response.ok
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('🚫 API健康检查失败:', error)
    return false
  }
}
