/**
 * API服务主入口 - 统一导出所有API服务
 */

import { type BaseApi, createApiInstance } from './base'
import { defaultInterceptors } from './interceptors'
import { createRequestConfig, getFallbackRequestConfig } from '../config/env'

// 导入业务服务
import { createAIService, type AIService } from './services/aiService'
import { createTTSService, type TTSService } from './services/ttsService'
import { createWorkflowService, type WorkflowService } from './services/workflowService'

/**
 * 主API实例
 */
let primaryApiInstance: BaseApi | null = null

/**
 * 备用API实例
 */
let fallbackApiInstance: BaseApi | null = null

/**
 * 业务服务实例
 */
let aiServiceInstance: AIService | null = null
let ttsServiceInstance: TTSService | null = null
let workflowServiceInstance: WorkflowService | null = null

/**
 * 获取主API实例
 */
export function getPrimaryApi(): BaseApi {
  if (!primaryApiInstance) {
    const config = createRequestConfig()
    primaryApiInstance = createApiInstance(config)
    
    // 添加默认拦截器
    defaultInterceptors.request.forEach(interceptor => {
      primaryApiInstance!.addRequestInterceptor(interceptor)
    })
    
    defaultInterceptors.response.forEach(interceptor => {
      primaryApiInstance!.addResponseInterceptor(interceptor)
    })
    
    defaultInterceptors.error.forEach(interceptor => {
      primaryApiInstance!.addErrorInterceptor(interceptor)
    })
  }
  
  return primaryApiInstance
}

/**
 * 获取备用API实例
 */
export function getFallbackApi(): BaseApi | null {
  if (!fallbackApiInstance) {
    const config = getFallbackRequestConfig()
    if (!config) {
      return null
    }
    
    fallbackApiInstance = createApiInstance(config)
    
    // 添加基础拦截器（减少日志）
    defaultInterceptors.error.forEach(interceptor => {
      fallbackApiInstance!.addErrorInterceptor(interceptor)
    })
  }
  
  return fallbackApiInstance
}

/**
 * 智能API调用 - 自动降级到备用服务
 */
export async function smartApiCall<T>(
  apiCall: (api: BaseApi) => Promise<T>
): Promise<T> {
  try {
    // 首先尝试主API
    const primaryApi = getPrimaryApi()
    return await apiCall(primaryApi)
  }
  catch (primaryError) {
    // 主API失败，尝试备用API
    const fallbackApi = getFallbackApi()
    if (fallbackApi) {
      try {
        return await apiCall(fallbackApi)
      }
      catch (fallbackError) {
        // 两个API都失败，抛出原始错误
        throw primaryError
      }
    }
    
    // 没有备用API，直接抛出错误
    throw primaryError
  }
}

/**
 * 重置API实例（用于配置更新）
 */
export function resetApiInstances(): void {
  primaryApiInstance = null
  fallbackApiInstance = null
  // 重置业务服务实例
  aiServiceInstance = null
  ttsServiceInstance = null
  workflowServiceInstance = null
}

/**
 * 获取AI服务实例
 */
export function getAIService(): AIService {
  if (!aiServiceInstance) {
    const api = getPrimaryApi()
    aiServiceInstance = createAIService(api)
  }
  return aiServiceInstance
}

/**
 * 获取TTS服务实例
 */
export function getTTSService(): TTSService {
  if (!ttsServiceInstance) {
    const api = getPrimaryApi()
    ttsServiceInstance = createTTSService(api)
  }
  return ttsServiceInstance
}

/**
 * 获取工作流服务实例
 */
export function getWorkflowService(): WorkflowService {
  if (!workflowServiceInstance) {
    const api = getPrimaryApi()
    workflowServiceInstance = createWorkflowService(api)
  }
  return workflowServiceInstance
}

/**
 * 检查API健康状态
 */
export async function checkApiHealth(): Promise<{
  primary: boolean
  fallback: boolean
}> {
  const result = {
    primary: false,
    fallback: false
  }
  
  try {
    const primaryApi = getPrimaryApi()
    result.primary = await primaryApi.healthCheck()
  }
  catch {
    result.primary = false
  }
  
  try {
    const fallbackApi = getFallbackApi()
    if (fallbackApi) {
      result.fallback = await fallbackApi.healthCheck()
    }
  }
  catch {
    result.fallback = false
  }
  
  return result
}

// 导出默认API实例
export const api = getPrimaryApi()

// 导出业务服务实例
export const aiService = getAIService()
export const ttsService = getTTSService()
export const workflowService = getWorkflowService()

// 导出API相关类型和工具
export type { ApiResponse, RequestConfig } from '@/api/types/common'
export { ApiError, HttpMethod, RequestStatus } from './base'
