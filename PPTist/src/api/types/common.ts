/**
 * 通用API类型定义
 */

/**
 * 统一API响应格式
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  code?: number
}

/**
 * HTTP请求配置
 */
export interface RequestConfig {
  baseURL: string
  timeout?: number
  headers?: Record<string, string>
  retry?: RetryConfig
}

/**
 * 重试配置
 */
export interface RetryConfig {
  times: number
  delay: number
}

/**
 * 请求状态
 */
export type RequestStatus = 'idle' | 'pending' | 'success' | 'error'

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page?: number
  pageSize?: number
  total?: number
}

/**
 * 分页响应数据
 */
export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

/**
 * 排序参数
 */
export interface SortParams {
  field: string
  order: 'asc' | 'desc'
}

/**
 * 过滤参数
 */
export interface FilterParams {
  [key: string]: any
}

/**
 * 搜索参数
 */
export interface SearchParams extends PaginationParams {
  keyword?: string
  filters?: FilterParams
  sort?: SortParams[]
}

/**
 * 文件上传响应
 */
export interface UploadResponse {
  url: string
  filename: string
  size: number
  type: string
}

/**
 * 错误响应
 */
export interface ErrorResponse {
  error: {
    code: number
    message: string
    details?: any
  }
}

/**
 * 健康检查响应
 */
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  services?: Record<string, 'up' | 'down'>
}

/**
 * 版本信息响应
 */
export interface VersionResponse {
  version: string
  buildTime: string
  commit?: string
  environment: string
}
