/**
 * API性能监控工具 - 实时监控API调用性能和状态
 */
import type { BaseApi } from './base'

interface PerformanceMetric {
  url: string
  method: string
  duration: number
  status: number
  timestamp: number
  success: boolean
  retryCount: number
}

interface ApiStats {
  totalRequests: number
  successRequests: number
  failedRequests: number
  avgResponseTime: number
  minResponseTime: number
  maxResponseTime: number
  totalRetries: number
  lastRequest?: PerformanceMetric
}

class ApiPerformanceMonitor {
  private metrics: PerformanceMetric[] = []
  private maxMetrics = 1000 // 最多保存1000条记录
  private listeners: Array<(metric: PerformanceMetric) => void> = []

  /**
   * 记录API调用性能指标
   */
  recordMetric(metric: PerformanceMetric) {
    this.metrics.push(metric)
    
    // 保持最大记录数限制
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.shift()
    }
    
    // 通知监听器
    this.listeners.forEach(listener => listener(metric))
  }

  /**
   * 获取整体统计信息
   */
  getStats(): ApiStats {
    if (this.metrics.length === 0) {
      return {
        totalRequests: 0,
        successRequests: 0,
        failedRequests: 0,
        avgResponseTime: 0,
        minResponseTime: 0,
        maxResponseTime: 0,
        totalRetries: 0
      }
    }

    const successMetrics = this.metrics.filter(m => m.success)
    const failedMetrics = this.metrics.filter(m => !m.success)
    const responseTimes = this.metrics.map(m => m.duration)
    
    return {
      totalRequests: this.metrics.length,
      successRequests: successMetrics.length,
      failedRequests: failedMetrics.length,
      avgResponseTime: Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length),
      minResponseTime: Math.min(...responseTimes),
      maxResponseTime: Math.max(...responseTimes),
      totalRetries: this.metrics.reduce((sum, m) => sum + m.retryCount, 0),
      lastRequest: this.metrics[this.metrics.length - 1]
    }
  }

  /**
   * 获取指定时间范围内的统计
   */
  getStatsInTimeRange(minutes: number): ApiStats {
    const cutoff = Date.now() - (minutes * 60 * 1000)
    const recentMetrics = this.metrics.filter(m => m.timestamp >= cutoff)
    
    if (recentMetrics.length === 0) {
      return this.getStats() // 返回全部统计
    }

    const successMetrics = recentMetrics.filter(m => m.success)
    const responseTimes = recentMetrics.map(m => m.duration)
    
    return {
      totalRequests: recentMetrics.length,
      successRequests: successMetrics.length,
      failedRequests: recentMetrics.length - successMetrics.length,
      avgResponseTime: Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length),
      minResponseTime: Math.min(...responseTimes),
      maxResponseTime: Math.max(...responseTimes),
      totalRetries: recentMetrics.reduce((sum, m) => sum + m.retryCount, 0),
      lastRequest: recentMetrics[recentMetrics.length - 1]
    }
  }

  /**
   * 获取按URL分组的统计
   */
  getStatsByUrl(): Record<string, ApiStats> {
    const urlGroups: Record<string, PerformanceMetric[]> = {}
    
    // 按URL分组
    this.metrics.forEach(metric => {
      const key = `${metric.method} ${metric.url}`
      if (!urlGroups[key]) {
        urlGroups[key] = []
      }
      urlGroups[key].push(metric)
    })
    
    // 计算每个URL的统计
    const result: Record<string, ApiStats> = {}
    Object.entries(urlGroups).forEach(([key, metrics]) => {
      const successMetrics = metrics.filter(m => m.success)
      const responseTimes = metrics.map(m => m.duration)
      
      result[key] = {
        totalRequests: metrics.length,
        successRequests: successMetrics.length,
        failedRequests: metrics.length - successMetrics.length,
        avgResponseTime: Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length),
        minResponseTime: Math.min(...responseTimes),
        maxResponseTime: Math.max(...responseTimes),
        totalRetries: metrics.reduce((sum, m) => sum + m.retryCount, 0),
        lastRequest: metrics[metrics.length - 1]
      }
    })
    
    return result
  }

  /**
   * 获取原始指标数据
   */
  getMetrics(): PerformanceMetric[] {
    return [...this.metrics]
  }

  /**
   * 清空所有指标
   */
  clear() {
    this.metrics = []
  }

  /**
   * 添加性能监听器
   */
  addListener(listener: (metric: PerformanceMetric) => void) {
    this.listeners.push(listener)
  }

  /**
   * 移除性能监听器
   */
  removeListener(listener: (metric: PerformanceMetric) => void) {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  /**
   * 获取性能报告
   */
  generateReport(): string {
    const stats = this.getStats()
    const urlStats = this.getStatsByUrl()
    
    let report = '=== API 性能监控报告 ===\n\n'
    
    // 整体统计
    report += '整体统计:\n'
    report += `- 总请求数: ${stats.totalRequests}\n`
    report += `- 成功请求: ${stats.successRequests} (${Math.round(stats.successRequests / stats.totalRequests * 100)}%)\n`
    report += `- 失败请求: ${stats.failedRequests} (${Math.round(stats.failedRequests / stats.totalRequests * 100)}%)\n`
    report += `- 平均响应时间: ${stats.avgResponseTime}ms\n`
    report += `- 最快响应: ${stats.minResponseTime}ms\n`
    report += `- 最慢响应: ${stats.maxResponseTime}ms\n`
    report += `- 总重试次数: ${stats.totalRetries}\n\n`
    
    // 按URL统计
    report += '按端点统计:\n'
    Object.entries(urlStats)
      .sort(([, a], [, b]) => b.totalRequests - a.totalRequests)
      .forEach(([url, stat]) => {
        report += `\n${url}:\n`
        report += `  - 请求数: ${stat.totalRequests}\n`
        report += `  - 成功率: ${Math.round(stat.successRequests / stat.totalRequests * 100)}%\n`
        report += `  - 平均响应: ${stat.avgResponseTime}ms\n`
        report += `  - 重试次数: ${stat.totalRetries}\n`
      })
    
    return report
  }
}

// 创建全局性能监控实例
export const apiPerformanceMonitor = new ApiPerformanceMonitor()

/**
 * API性能拦截器 - 自动记录所有API调用的性能指标
 */
export function createPerformanceInterceptor() {
  return {
    onRequest: (config: RequestInit): RequestInit => {
      // 在请求配置中添加开始时间（使用headers传递）
      return {
        ...config,
        headers: {
          ...config.headers,
          'X-Start-Time': Date.now().toString(),
          'X-Retry-Count': '0'
        }
      }
    },
    
    onResponse: (response: Response): Response => {
      const startTime = response.headers.get('X-Start-Time')
      const retryCount = response.headers.get('X-Retry-Count')
      
      if (startTime) {
        const duration = Date.now() - parseInt(startTime)
        
        apiPerformanceMonitor.recordMetric({
          url: response.url || 'unknown',
          method: 'GET', // Response对象无法获取原始method
          duration,
          status: response.status,
          timestamp: Date.now(),
          success: response.ok,
          retryCount: parseInt(retryCount || '0')
        })
      }
      
      return response
    },
    
    onError: (error: Error): Error => {
      // 记录错误的性能指标
      apiPerformanceMonitor.recordMetric({
        url: 'unknown',
        method: 'unknown',
        duration: 0,
        status: 0,
        timestamp: Date.now(),
        success: false,
        retryCount: 0
      })
      
      return error
    }
  }
}

/**
 * 自动为API实例添加性能监控
 */
export function enablePerformanceMonitoring(api: BaseApi) {
  const interceptor = createPerformanceInterceptor()
  
  api.addRequestInterceptor(interceptor.onRequest)
  api.addResponseInterceptor(interceptor.onResponse)
  api.addErrorInterceptor(interceptor.onError)
}

export type { PerformanceMetric, ApiStats }
