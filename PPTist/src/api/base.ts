/**
 * API基础类 - 统一HTTP请求处理
 * 提供统一的请求配置、错误处理、重试机制和拦截器
 */

import type { ApiResponse, RequestConfig, RetryConfig } from '@/api/types/common'

/**
 * HTTP请求方法枚举
 */
export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH'
}

/**
 * 请求状态枚举
 */
export enum RequestStatus {
  IDLE = 'idle',
  PENDING = 'pending',
  SUCCESS = 'success',
  ERROR = 'error'
}

/**
 * API错误类
 */
export class ApiError extends Error {
  public readonly code: number
  public readonly status: string
  public readonly originalError?: Error

  constructor(message: string, code: number = 500, status: string = 'error', originalError?: Error) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.originalError = originalError
  }
}

/**
 * 请求拦截器类型
 */
export type RequestInterceptor = (config: RequestInit) => RequestInit | Promise<RequestInit>

/**
 * 响应拦截器类型
 */
export type ResponseInterceptor = (response: Response) => Response | Promise<Response>

/**
 * 错误拦截器类型
 */
export type ErrorInterceptor = (error: Error) => Error | Promise<Error>

/**
 * API基础类
 */
export class BaseApi {
  private readonly baseURL: string
  private readonly timeout: number
  private readonly retryConfig: RetryConfig
  private readonly defaultHeaders: Record<string, string>
  
  // 拦截器存储
  private requestInterceptors: RequestInterceptor[] = []
  private responseInterceptors: ResponseInterceptor[] = []
  private errorInterceptors: ErrorInterceptor[] = []

  constructor(config: RequestConfig) {
    this.baseURL = config.baseURL
    this.timeout = config.timeout || 30000
    this.retryConfig = config.retry || { times: 3, delay: 1000 }
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers
    }
  }

  /**
   * 添加请求拦截器
   */
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor)
  }

  /**
   * 添加响应拦截器
   */
  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor)
  }

  /**
   * 添加错误拦截器
   */
  addErrorInterceptor(interceptor: ErrorInterceptor): void {
    this.errorInterceptors.push(interceptor)
  }

  /**
   * 构建完整URL
   */
  private buildURL(endpoint: string): string {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseURL}${endpoint}`
    return url
  }

  /**
   * 应用请求拦截器
   */
  private async applyRequestInterceptors(config: RequestInit): Promise<RequestInit> {
    let processedConfig = config
    
    for (const interceptor of this.requestInterceptors) {
      processedConfig = await interceptor(processedConfig)
    }
    
    return processedConfig
  }

  /**
   * 应用响应拦截器
   */
  private async applyResponseInterceptors(response: Response): Promise<Response> {
    let processedResponse = response
    
    for (const interceptor of this.responseInterceptors) {
      processedResponse = await interceptor(processedResponse)
    }
    
    return processedResponse
  }

  /**
   * 应用错误拦截器
   */
  private async applyErrorInterceptors(error: Error): Promise<Error> {
    let processedError = error
    
    for (const interceptor of this.errorInterceptors) {
      processedError = await interceptor(processedError)
    }
    
    return processedError
  }

  /**
   * 超时控制
   */
  private createTimeoutSignal(timeout: number): AbortSignal {
    const controller = new AbortController()
    setTimeout(() => controller.abort(), timeout)
    return controller.signal
  }

  /**
   * 延迟函数（用于重试）
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 执行HTTP请求（带重试机制）
   */
  private async executeRequest<T>(
    url: string, 
    config: RequestInit, 
    attempt: number = 1
  ): Promise<ApiResponse<T>> {
    try {
      // 创建超时信号
      const timeoutSignal = this.createTimeoutSignal(this.timeout)
      const finalConfig = {
        ...config,
        signal: timeoutSignal
      }

      // 应用请求拦截器
      const interceptedConfig = await this.applyRequestInterceptors(finalConfig)

      // 发送请求
      const response = await fetch(url, interceptedConfig)

      // 应用响应拦截器
      const interceptedResponse = await this.applyResponseInterceptors(response)

      // 检查响应状态
      if (!interceptedResponse.ok) {
        throw new ApiError(
          `HTTP ${interceptedResponse.status}: ${interceptedResponse.statusText}`,
          interceptedResponse.status,
          'http_error'
        )
      }

      // 解析响应数据
      const data = await interceptedResponse.json()

      // 检查业务逻辑错误
      if (data.success === false) {
        throw new ApiError(
          data.message || '请求失败',
          data.code || 400,
          'business_error'
        )
      }

      return {
        success: true,
        data: data.data || data,
        message: data.message || 'success',
        code: interceptedResponse.status
      }

    }
    catch (error) {
      // 应用错误拦截器
      const processedError = await this.applyErrorInterceptors(error as Error)

      // 重试逻辑
      if (attempt < this.retryConfig.times) {
        // console.warn(`请求失败，第 ${attempt} 次重试...`, processedError.message)
        await this.delay(this.retryConfig.delay * attempt)
        return this.executeRequest<T>(url, config, attempt + 1)
      }

      // 最终错误处理
      if (processedError instanceof ApiError) {
        throw processedError
      }

      throw new ApiError(
        processedError.message || '网络请求失败',
        500,
        'network_error',
        processedError
      )
    }
  }

  /**
   * GET请求
   */
  get<T = any>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint)
    const searchParams = params ? new URLSearchParams(params).toString() : ''
    const finalURL = searchParams ? `${url}?${searchParams}` : url

    const config: RequestInit = {
      method: HttpMethod.GET,
      headers: this.defaultHeaders
    }

    return this.executeRequest<T>(finalURL, config)
  }

  /**
   * POST请求
   */
  post<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint)

    const config: RequestInit = {
      method: HttpMethod.POST,
      headers: this.defaultHeaders,
      body: data ? JSON.stringify(data) : undefined
    }

    return this.executeRequest<T>(url, config)
  }

  /**
   * PUT请求
   */
  put<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint)

    const config: RequestInit = {
      method: HttpMethod.PUT,
      headers: this.defaultHeaders,
      body: data ? JSON.stringify(data) : undefined
    }

    return this.executeRequest<T>(url, config)
  }

  /**
   * DELETE请求
   */
  delete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint)

    const config: RequestInit = {
      method: HttpMethod.DELETE,
      headers: this.defaultHeaders
    }

    return this.executeRequest<T>(url, config)
  }

  /**
   * PATCH请求
   */
  patch<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint)

    const config: RequestInit = {
      method: HttpMethod.PATCH,
      headers: this.defaultHeaders,
      body: data ? JSON.stringify(data) : undefined
    }

    return this.executeRequest<T>(url, config)
  }

  /**
   * 文件上传请求
   */
  upload<T = any>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint)

    const config: RequestInit = {
      method: HttpMethod.POST,
      headers: {
        // 不设置Content-Type，让浏览器自动设置boundary
        ...Object.fromEntries(
          Object.entries(this.defaultHeaders).filter(([key]) => 
            key.toLowerCase() !== 'content-type'
          )
        )
      },
      body: formData
    }

    return this.executeRequest<T>(url, config)
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.get('/health')
      return response.success
    }
    catch (error) {
      return false
    }
  }
}

/**
 * 创建API实例的工厂函数
 */
export function createApiInstance(config: RequestConfig): BaseApi {
  return new BaseApi(config)
}

export default BaseApi
