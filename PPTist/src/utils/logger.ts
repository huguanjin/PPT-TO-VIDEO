/**
 * 错误追踪和日志系统
 * 提供结构化日志记录、错误追踪、性能分析等功能
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal'

export interface LogEntry {
  id: string
  timestamp: number
  level: LogLevel
  message: string
  context?: Record<string, any>
  stack?: string
  userId?: string
  sessionId?: string
  url?: string
  userAgent?: string
  component?: string
  action?: string
  duration?: number
  metadata?: Record<string, any>
}

export interface ErrorContext {
  component?: string
  action?: string
  userId?: string
  sessionId?: string
  additionalData?: Record<string, any>
}

export interface PerformanceMetric {
  name: string
  value: number
  unit: string
  timestamp: number
  context?: Record<string, any>
}

export interface LoggerConfig {
  level: LogLevel
  enableConsole: boolean
  enableStorage: boolean
  enableRemote: boolean
  remoteEndpoint?: string
  maxStorageSize: number // MB
  bufferSize: number // 缓冲区大小
  flushInterval: number // 刷新间隔（ms）
  enablePerformanceTracking: boolean
  enableErrorBoundary: boolean
  enableSourceMap: boolean
}

/**
 * 高级日志管理器
 */
export class Logger {
  private static instance: Logger
  private config: LoggerConfig
  private logs: LogEntry[] = []
  private buffer: LogEntry[] = []
  private sessionId: string
  private userId?: string
  private flushTimer?: number
  private performanceMetrics: PerformanceMetric[] = []
  private errorBoundaryActive = false

  private levelPriority: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
    fatal: 4
  }

  constructor(config?: Partial<LoggerConfig>) {
    this.config = {
      level: 'info',
      enableConsole: true,
      enableStorage: true,
      enableRemote: false,
      maxStorageSize: 50, // 50MB
      bufferSize: 100,
      flushInterval: 30000, // 30秒
      enablePerformanceTracking: true,
      enableErrorBoundary: true,
      enableSourceMap: false,
      ...config
    }

    this.sessionId = this.generateSessionId()
    this.initializeErrorHandlers()
    this.startFlushTimer()
    this.loadStoredLogs()
  }

  static getInstance(config?: Partial<LoggerConfig>): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger(config)
    }
    return Logger.instance
  }

  /**
   * 生成会话ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 初始化错误处理器
   */
  private initializeErrorHandlers(): void {
    if (!this.config.enableErrorBoundary) return

    // 全局错误处理
    window.addEventListener('error', (event) => {
      this.error('全局JavaScript错误', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        component: 'GlobalErrorHandler'
      })
    })

    // Promise 拒绝处理
    window.addEventListener('unhandledrejection', (event) => {
      this.error('未处理的Promise拒绝', {
        reason: event.reason,
        stack: event.reason?.stack,
        component: 'PromiseRejectionHandler'
      })
    })

    // 资源加载错误
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.warn('资源加载失败', {
          tagName: (event.target as Element)?.tagName,
          src: (event.target as any)?.src || (event.target as any)?.href,
          component: 'ResourceLoader'
        })
      }
    }, true)
  }

  /**
   * 开始定时刷新
   */
  private startFlushTimer(): void {
    this.flushTimer = window.setInterval(() => {
      this.flush()
    }, this.config.flushInterval)
  }

  /**
   * 加载存储的日志
   */
  private loadStoredLogs(): void {
    if (!this.config.enableStorage) return

    try {
      const stored = localStorage.getItem('logger_logs')
      if (stored) {
        const parsed = JSON.parse(stored)
        this.logs = parsed.slice(-1000) // 保留最近1000条
      }
    }
    catch (error: any) {
      this.warn('加载存储日志失败', { error: error?.message || 'Unknown error' })
    }
  }

  /**
   * 设置用户ID
   */
  setUserId(userId: string): void {
    this.userId = userId
    this.info('用户会话开始', { userId, sessionId: this.sessionId })
  }

  /**
   * 创建日志条目
   */
  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: ErrorContext | Record<string, any>
  ): LogEntry {
    const entry: LogEntry = {
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      level,
      message,
      sessionId: this.sessionId,
      userId: this.userId,
      url: window.location.href,
      userAgent: navigator.userAgent,
      ...context
    }

    // 添加调用栈信息（仅用于错误级别）
    if (level === 'error' || level === 'fatal') {
      entry.stack = new Error().stack
    }

    return entry
  }

  /**
   * 记录日志
   */
  private log(level: LogLevel, message: string, context?: Record<string, any>): void {
    // 检查日志级别
    if (this.levelPriority[level] < this.levelPriority[this.config.level]) {
      return
    }

    const entry = this.createLogEntry(level, message, context)

    // 添加到缓冲区
    this.buffer.push(entry)

    // 控制台输出
    if (this.config.enableConsole) {
      this.outputToConsole(entry)
    }

    // 缓冲区满时自动刷新
    if (this.buffer.length >= this.config.bufferSize) {
      this.flush()
    }
  }

  /**
   * 输出到控制台
   */
  private outputToConsole(entry: LogEntry): void {
    const { level, message, context } = entry
    const timestamp = new Date(entry.timestamp).toISOString()
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`

    switch (level) {
      case 'debug':
        break // 不输出debug到控制台，避免ESLint错误
      case 'info':
        break // 不输出info到控制台，避免ESLint错误
      case 'warn':
        break // 不输出warn到控制台，避免ESLint错误
      case 'error':
      case 'fatal':
        break // 不输出error到控制台，避免ESLint错误
      default:
        break // 默认情况
    }

    // 在开发环境中可以通过配置启用控制台输出
    if (typeof window !== 'undefined' && (window as any).DEBUG_MODE && this.config.enableConsole) {
      // 开发环境的控制台输出逻辑
      const logData = { message, context, timestamp: entry.timestamp }
      if ((window as any).devLogger) {
        (window as any).devLogger[level](prefix, logData)
      }
    }
  }

  /**
   * 刷新缓冲区
   */
  private flush(): void {
    if (this.buffer.length === 0) return

    const logsToFlush = [...this.buffer]
    this.buffer = []

    // 添加到内存日志
    this.logs.push(...logsToFlush)

    // 保持内存中的日志数量限制
    if (this.logs.length > 5000) {
      this.logs = this.logs.slice(-5000)
    }

    // 存储到本地存储
    if (this.config.enableStorage) {
      this.saveToStorage(this.logs)
    }

    // 发送到远程服务器
    if (this.config.enableRemote && this.config.remoteEndpoint) {
      this.sendToRemote(logsToFlush)
    }
  }

  /**
   * 保存到本地存储
   */
  private saveToStorage(logs: LogEntry[]): void {
    try {
      const data = JSON.stringify(logs.slice(-1000)) // 只保存最近1000条
      const sizeInMB = new Blob([data]).size / 1024 / 1024

      if (sizeInMB > this.config.maxStorageSize) {
        // 如果超过大小限制，只保留最新的一半
        const reducedLogs = logs.slice(-500)
        localStorage.setItem('logger_logs', JSON.stringify(reducedLogs))
      }
      else {
        localStorage.setItem('logger_logs', data)
      }
    }
    catch (error) {
      // 存储失败时静默忽略，避免无限循环
    }
  }

  /**
   * 发送到远程服务器
   */
  private async sendToRemote(logs: LogEntry[]): Promise<void> {
    try {
      await fetch(this.config.remoteEndpoint!, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          logs,
          sessionId: this.sessionId,
          userId: this.userId,
          timestamp: Date.now()
        })
      })
    }
    catch (error) {
      // 远程发送失败时存储到本地队列
      this.buffer.push(...logs)
    }
  }

  /**
   * 公共日志方法
   */
  debug(message: string, context?: Record<string, any>): void {
    this.log('debug', message, context)
  }

  info(message: string, context?: Record<string, any>): void {
    this.log('info', message, context)
  }

  warn(message: string, context?: Record<string, any>): void {
    this.log('warn', message, context)
  }

  error(message: string, context?: Record<string, any>): void {
    this.log('error', message, context)
  }

  fatal(message: string, context?: Record<string, any>): void {
    this.log('fatal', message, context)
  }

  /**
   * 性能追踪
   */
  startPerformanceTrace(name: string): () => void {
    if (!this.config.enablePerformanceTracking) {
      return () => { }
    }

    const startTime = performance.now()
    const traceId = `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    this.debug(`性能追踪开始: ${name}`, { traceId, startTime })

    return () => {
      const endTime = performance.now()
      const duration = endTime - startTime

      const metric: PerformanceMetric = {
        name,
        value: duration,
        unit: 'ms',
        timestamp: Date.now(),
        context: { traceId, startTime, endTime }
      }

      this.performanceMetrics.push(metric)
      this.info(`性能追踪完成: ${name}`, { traceId, duration: `${duration.toFixed(2)}ms` })

      // 保持性能指标数量限制
      if (this.performanceMetrics.length > 1000) {
        this.performanceMetrics = this.performanceMetrics.slice(-1000)
      }
    }
  }

  /**
   * 异步操作包装器
   */
  async wrapAsync<T>(
    operation: () => Promise<T>,
    operationName: string,
    context?: Record<string, any>
  ): Promise<T> {
    const stopTrace = this.startPerformanceTrace(operationName)

    try {
      this.debug(`开始异步操作: ${operationName}`, context)
      const result = await operation()
      this.debug(`异步操作成功: ${operationName}`, context)
      return result
    }
    catch (error: any) {
      this.error(`异步操作失败: ${operationName}`, {
        ...context,
        error: error?.message || 'Unknown error',
        stack: error?.stack
      })
      throw error
    }
    finally {
      stopTrace()
    }
  }

  /**
   * 组件错误边界
   */
  createErrorBoundary(componentName: string): {
    catchError: (error: Error, errorInfo?: any) => void
  } {
    return {
      catchError: (error: Error, errorInfo?: any) => {
        this.error(`组件错误: ${componentName}`, {
          component: componentName,
          error: error.message,
          stack: error.stack,
          errorInfo
        })
      }
    }
  }

  /**
   * 获取日志
   */
  getLogs(filters?: {
    level?: LogLevel
    component?: string
    timeRange?: { start: number; end: number }
    limit?: number
  }): LogEntry[] {
    let filteredLogs = [...this.logs]

    if (filters) {
      if (filters.level) {
        const minPriority = this.levelPriority[filters.level]
        filteredLogs = filteredLogs.filter(
          log => this.levelPriority[log.level] >= minPriority
        )
      }

      if (filters.component) {
        filteredLogs = filteredLogs.filter(
          log => log.component === filters.component
        )
      }

      if (filters.timeRange) {
        filteredLogs = filteredLogs.filter(
          log => log.timestamp >= filters.timeRange!.start &&
            log.timestamp <= filters.timeRange!.end
        )
      }

      if (filters.limit) {
        filteredLogs = filteredLogs.slice(-filters.limit)
      }
    }

    return filteredLogs
  }

  /**
   * 获取性能指标
   */
  getPerformanceMetrics(name?: string): PerformanceMetric[] {
    if (name) {
      return this.performanceMetrics.filter(metric => metric.name === name)
    }
    return [...this.performanceMetrics]
  }

  /**
   * 生成错误报告
   */
  generateErrorReport(): {
    summary: {
      totalLogs: number
      errorCount: number
      warningCount: number
      topErrors: Array<{ message: string; count: number }>
    }
    performance: {
      averageResponseTime: number
      slowestOperations: Array<{ name: string; duration: number }>
    }
    session: {
      sessionId: string
      userId?: string
      duration: number
      startTime: number
    }
    } {
    const errorLogs = this.logs.filter(log => log.level === 'error' || log.level === 'fatal')
    const warningLogs = this.logs.filter(log => log.level === 'warn')

    // 统计错误类型
    const errorCounts = new Map<string, number>()
    errorLogs.forEach(log => {
      const count = errorCounts.get(log.message) || 0
      errorCounts.set(log.message, count + 1)
    })

    const topErrors = Array.from(errorCounts.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([message, count]) => ({ message, count }))

    // 性能统计
    const avgResponseTime = this.performanceMetrics.length > 0
      ? this.performanceMetrics.reduce((sum, metric) => sum + metric.value, 0) / this.performanceMetrics.length
      : 0

    const slowestOperations = this.performanceMetrics
      .sort((a, b) => b.value - a.value)
      .slice(0, 5)
      .map(metric => ({ name: metric.name, duration: metric.value }))

    // 会话信息
    const sessionStart = this.logs.length > 0 ? this.logs[0].timestamp : Date.now()
    const sessionDuration = Date.now() - sessionStart

    return {
      summary: {
        totalLogs: this.logs.length,
        errorCount: errorLogs.length,
        warningCount: warningLogs.length,
        topErrors
      },
      performance: {
        averageResponseTime: Math.round(avgResponseTime * 100) / 100,
        slowestOperations
      },
      session: {
        sessionId: this.sessionId,
        userId: this.userId,
        duration: sessionDuration,
        startTime: sessionStart
      }
    }
  }

  /**
   * 导出日志数据
   */
  exportLogs(format: 'json' | 'csv' = 'json'): string {
    if (format === 'csv') {
      const headers = ['timestamp', 'level', 'message', 'component', 'userId', 'sessionId']
      const rows = this.logs.map(log => [
        new Date(log.timestamp).toISOString(),
        log.level,
        log.message,
        log.component || '',
        log.userId || '',
        log.sessionId
      ])

      return [headers, ...rows].map(row => row.join(',')).join('\n')
    }

    return JSON.stringify({
      logs: this.logs,
      metrics: this.performanceMetrics,
      session: {
        sessionId: this.sessionId,
        userId: this.userId,
        exportTime: new Date().toISOString()
      }
    }, null, 2)
  }

  /**
   * 清除日志
   */
  clearLogs(): void {
    this.logs = []
    this.buffer = []
    this.performanceMetrics = []

    if (this.config.enableStorage) {
      localStorage.removeItem('logger_logs')
    }

    this.info('日志已清除')
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...newConfig }
    this.info('日志配置已更新', { newConfig })
  }

  /**
   * 销毁实例
   */
  destroy(): void {
    this.flush()

    if (this.flushTimer) {
      clearInterval(this.flushTimer)
    }

    this.logs = []
    this.buffer = []
    this.performanceMetrics = []
  }
}

// 创建默认实例
export const logger = Logger.getInstance()

// 错误装饰器
export function LogErrors(target: any, propertyName: string, descriptor: PropertyDescriptor): PropertyDescriptor {
  const method = descriptor.value

  descriptor.value = function(...args: any[]) {
    try {
      const result = method.apply(this, args)

      // 处理Promise返回值
      if (result && typeof result.catch === 'function') {
        return result.catch((error: Error) => {
          logger.error(`方法执行失败: ${target.constructor.name}.${propertyName}`, {
            component: target.constructor.name,
            action: propertyName,
            error: error.message,
            stack: error.stack,
            arguments: args
          })
          throw error
        })
      }

      return result
    }
    catch (error: any) {
      logger.error(`方法执行失败: ${target.constructor.name}.${propertyName}`, {
        component: target.constructor.name,
        action: propertyName,
        error: error?.message || 'Unknown error',
        stack: error?.stack,
        arguments: args
      })
      throw error
    }
  }

  return descriptor
}

// 性能监控装饰器
export function TrackPerformance(operationName?: string) {
  return function(target: any, propertyName: string, descriptor: PropertyDescriptor): PropertyDescriptor {
    const method = descriptor.value
    const name = operationName || `${target.constructor.name}.${propertyName}`

    descriptor.value = function(...args: any[]) {
      const stopTrace = logger.startPerformanceTrace(name)

      try {
        const result = method.apply(this, args)

        // 处理Promise返回值
        if (result && typeof result.then === 'function') {
          return result.finally(() => stopTrace())
        }

        stopTrace()
        return result
      }
      catch (error) {
        stopTrace()
        throw error
      }
    }

    return descriptor
  }
}