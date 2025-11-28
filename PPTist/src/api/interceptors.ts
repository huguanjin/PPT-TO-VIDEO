/**
 * API拦截器 - 统一处理请求和响应
 */

import type { RequestInterceptor, ResponseInterceptor, ErrorInterceptor } from './base'

/**
 * 请求日志拦截器
 */
export const requestLoggerInterceptor: RequestInterceptor = (config) => {
  if (import.meta.env.DEV) {
    // console.log('🚀 API Request:', config)
  }
  return config
}

/**
 * 认证拦截器 - 添加认证信息
 */
export const authInterceptor: RequestInterceptor = (config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers = {
      ...config.headers,
      'Authorization': `Bearer ${token}`
    }
  }
  return config
}

/**
 * 请求ID拦截器 - 为每个请求添加唯一标识
 */
export const requestIdInterceptor: RequestInterceptor = (config) => {
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  config.headers = {
    ...config.headers,
    'X-Request-ID': requestId
  }
  return config
}

/**
 * 响应日志拦截器
 */
export const responseLoggerInterceptor: ResponseInterceptor = (response) => {
  if (import.meta.env.DEV) {
    // console.log('📦 API Response:', response)
  }
  return response
}

/**
 * 响应时间拦截器
 */
export const responseTimeInterceptor: ResponseInterceptor = (response) => {
  const startTime = response.headers.get('X-Start-Time')
  if (startTime) {
    const duration = Date.now() - parseInt(startTime)
    if (import.meta.env.DEV) {
      // 可以在这里记录响应时间或发送到监控系统
      // eslint-disable-next-line no-console
      console.debug(`⏱️ Request completed in ${duration}ms`)
    }
  }
  return response
}

/**
 * 错误日志拦截器
 */
export const errorLoggerInterceptor: ErrorInterceptor = (error) => {
  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.error('❌ API Error:', error)
  }
  return error
}

/**
 * 认证错误拦截器 - 处理401未授权错误
 */
export const authErrorInterceptor: ErrorInterceptor = (error) => {
  if (error.message.includes('401')) {
    // 清除本地认证信息
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    
    // 清除匿名访问标记，强制显示登录页
    localStorage.removeItem('skip_login')
    
    // eslint-disable-next-line no-console
    console.warn('🔐 认证已过期，请重新登录')
    
    // 刷新页面以显示登录界面
    // 延迟执行避免中断当前请求处理
    setTimeout(() => {
      window.location.reload()
    }, 100)
  }
  return error
}

/**
 * 网络错误拦截器 - 处理网络连接问题
 */
export const networkErrorInterceptor: ErrorInterceptor = (error) => {
  if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
    // eslint-disable-next-line no-console
    console.warn('网络连接异常，请检查网络设置')
    
    // 可以在这里触发网络状态检查
    // checkNetworkStatus()
  }
  return error
}

/**
 * 服务器错误拦截器 - 处理5xx服务器错误
 */
export const serverErrorInterceptor: ErrorInterceptor = (error) => {
  if (error.message.includes('500') || error.message.includes('503')) {
    // eslint-disable-next-line no-console
    console.warn('服务器暂时不可用，请稍后重试')
    
    // 可以在这里触发服务状态检查
    // checkServerStatus()
  }
  return error
}

/**
 * 默认拦截器配置
 */
export const defaultInterceptors = {
  request: [
    requestLoggerInterceptor,
    authInterceptor,
    requestIdInterceptor
  ],
  response: [
    responseLoggerInterceptor,
    responseTimeInterceptor
  ],
  error: [
    errorLoggerInterceptor,
    authErrorInterceptor,
    networkErrorInterceptor,
    serverErrorInterceptor
  ]
}
