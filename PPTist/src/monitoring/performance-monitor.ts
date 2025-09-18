/**
 * 性能监控系统
 * 实时监控系统性能指标，包括内存使用、CPU占用率、任务队列状态等
 */

export interface PerformanceMetrics {
  timestamp: number
  memory: {
    used: number // MB
    total: number // MB
    percentage: number
  }
  cpu: {
    usage: number // 百分比
    cores: number
  }
  network: {
    bytesReceived: number
    bytesSent: number
    latency: number // ms
  }
  tasks: {
    queued: number
    running: number
    completed: number
    failed: number
  }
  browser: {
    tabsCount: number
    storageUsed: number // MB
    cacheSize: number // MB
  }
}

export interface PerformanceAlert {
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  metric: keyof PerformanceMetrics
  value: number
  threshold: number
  timestamp: number
  suggestion?: string
}

export interface MonitoringConfig {
  interval: number // 监控间隔（ms）
  historySize: number // 保留历史数据量
  thresholds: {
    memory: number // 内存使用率阈值（%）
    cpu: number // CPU使用率阈值（%）
    queueSize: number // 任务队列大小阈值
    latency: number // 网络延迟阈值（ms）
  }
  enableAlerts: boolean
}

/**
 * 性能监控器类
 */
export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private metrics: PerformanceMetrics[] = []
  private alerts: PerformanceAlert[] = []
  private config: MonitoringConfig
  private intervalId: number | null = null
  private observers: Set<(metrics: PerformanceMetrics) => void> = new Set()
  private alertObservers: Set<(alert: PerformanceAlert) => void> = new Set()

  constructor(config?: Partial<MonitoringConfig>) {
    this.config = {
      interval: 5000, // 5秒
      historySize: 720, // 1小时的数据（5秒间隔）
      thresholds: {
        memory: 80,
        cpu: 85,
        queueSize: 100,
        latency: 1000
      },
      enableAlerts: true,
      ...config
    }
  }

  static getInstance(config?: Partial<MonitoringConfig>): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor(config)
    }
    return PerformanceMonitor.instance
  }

  /**
   * 开始监控
   */
  start(): void {
    if (this.intervalId) {
      return
    }

    this.intervalId = window.setInterval(async () => {
      const metrics = await this.collectMetrics()
      this.addMetrics(metrics)
      this.checkThresholds(metrics)
      this.notifyObservers(metrics)
    }, this.config.interval)

    // 性能监控已启动
  }

  /**
   * 停止监控
   */
  stop(): void {
    if (this.intervalId) {
      window.clearInterval(this.intervalId)
      this.intervalId = null
      // 性能监控已停止
    }
  }

  /**
   * 收集性能指标
   */
  private async collectMetrics(): Promise<PerformanceMetrics> {
    const memory = this.getMemoryMetrics()
    const cpu = this.getCPUMetrics()
    const network = await this.getNetworkMetrics()
    const tasks = this.getTaskMetrics()
    const browser = await this.getBrowserMetrics()

    return {
      timestamp: Date.now(),
      memory,
      cpu,
      network,
      tasks,
      browser
    }
  }

  /**
   * 获取内存指标
   */
  private getMemoryMetrics(): PerformanceMetrics['memory'] {
    if ('memory' in performance) {
      const memInfo = (performance as any).memory
      const used = memInfo.usedJSHeapSize / 1024 / 1024 // 转换为MB
      const total = memInfo.totalJSHeapSize / 1024 / 1024
      
      return {
        used: Math.round(used),
        total: Math.round(total),
        percentage: Math.round((used / total) * 100)
      }
    }

    // 降级方案：估算内存使用
    const estimatedUsed = this.estimateMemoryUsage()
    const estimatedTotal = 512 // 默认512MB

    return {
      used: estimatedUsed,
      total: estimatedTotal,
      percentage: Math.round((estimatedUsed / estimatedTotal) * 100)
    }
  }

  /**
   * 获取CPU指标
   */
  private getCPUMetrics(): PerformanceMetrics['cpu'] {
    const cores = navigator.hardwareConcurrency || 4
    const usage = this.estimateCPUUsage()

    return {
      usage: Math.round(usage),
      cores
    }
  }

  /**
   * 获取网络指标
   */
  private async getNetworkMetrics(): Promise<PerformanceMetrics['network']> {
    const connection = (navigator as any).connection
    const latency = await this.measureNetworkLatency()

    return {
      bytesReceived: connection?.downlink ? connection.downlink * 1024 * 1024 : 0,
      bytesSent: 0, // 浏览器API无法直接获取
      latency
    }
  }

  /**
   * 获取任务指标
   */
  private getTaskMetrics(): PerformanceMetrics['tasks'] {
    // 从全局任务管理器获取统计信息
    const taskManager = (window as any).taskManager
    
    if (taskManager && taskManager.getStats) {
      return taskManager.getStats()
    }

    return {
      queued: 0,
      running: 0,
      completed: 0,
      failed: 0
    }
  }

  /**
   * 获取浏览器指标
   */
  private async getBrowserMetrics(): Promise<PerformanceMetrics['browser']> {
    const storageUsed = await this.getStorageUsage()
    const cacheSize = await this.getCacheSize()

    return {
      tabsCount: 1, // 浏览器API无法获取其他标签页数量
      storageUsed,
      cacheSize
    }
  }

  /**
   * 估算内存使用量
   */
  private estimateMemoryUsage(): number {
    // 基于DOM节点数量和其他因素估算
    const domNodes = document.querySelectorAll('*').length
    const estimatedBase = Math.max(50, domNodes * 0.1) // 每个DOM节点约0.1MB

    return Math.round(estimatedBase)
  }

  /**
   * 估算CPU使用率
   */
  private estimateCPUUsage(): number {
    const startTime = performance.now()
    const iterations = 100000

    // 执行计算密集型任务
    let result = 0
    for (let i = 0; i < iterations; i++) {
      result += Math.sin(i) * Math.cos(i)
    }

    const duration = performance.now() - startTime
    
    // 基于执行时间估算CPU使用率
    const baselineTime = 50 // 基准时间（ms）
    const usage = Math.min(100, (duration / baselineTime) * 100)

    // 避免编译器优化
    if (result === 0) {
      return 0
    }

    return usage
  }

  /**
   * 测量网络延迟
   */
  private async measureNetworkLatency(): Promise<number> {
    try {
      const startTime = performance.now()
      await fetch('/favicon.ico', { method: 'HEAD', cache: 'no-cache' })
      return Math.round(performance.now() - startTime)
    }
    catch {
      return 999 // 网络错误时返回高延迟
    }
  }

  /**
   * 获取存储使用量
   */
  private async getStorageUsage(): Promise<number> {
    try {
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate()
        return Math.round((estimate.usage || 0) / 1024 / 1024) // 转换为MB
      }
    }
    catch {
      // 降级方案
    }

    // 估算localStorage使用量
    let totalSize = 0
    for (const key in localStorage) {
      if (Object.prototype.hasOwnProperty.call(localStorage, key)) {
        totalSize += localStorage[key].length
      }
    }

    return Math.round(totalSize / 1024 / 1024) // 转换为MB
  }

  /**
   * 获取缓存大小
   */
  private async getCacheSize(): Promise<number> {
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys()
        let totalSize = 0

        for (const cacheName of cacheNames) {
          const cache = await caches.open(cacheName)
          const requests = await cache.keys()
          
          for (const request of requests) {
            const response = await cache.match(request)
            if (response) {
              const blob = await response.blob()
              totalSize += blob.size
            }
          }
        }

        return Math.round(totalSize / 1024 / 1024) // 转换为MB
      }
    }
    catch {
      // 缓存API不可用
    }

    return 0
  }

  /**
   * 添加指标数据
   */
  private addMetrics(metrics: PerformanceMetrics): void {
    this.metrics.push(metrics)

    // 保持历史数据在限制范围内
    if (this.metrics.length > this.config.historySize) {
      this.metrics = this.metrics.slice(-this.config.historySize)
    }
  }

  /**
   * 检查阈值并生成警报
   */
  private checkThresholds(metrics: PerformanceMetrics): void {
    if (!this.config.enableAlerts) {
      return
    }

    const alerts: PerformanceAlert[] = []

    // 内存使用率检查
    if (metrics.memory.percentage > this.config.thresholds.memory) {
      alerts.push({
        level: metrics.memory.percentage > 95 ? 'critical' : 'warning',
        message: `内存使用率过高: ${metrics.memory.percentage}%`,
        metric: 'memory',
        value: metrics.memory.percentage,
        threshold: this.config.thresholds.memory,
        timestamp: metrics.timestamp,
        suggestion: '建议清理缓存或关闭不必要的功能'
      })
    }

    // CPU使用率检查
    if (metrics.cpu.usage > this.config.thresholds.cpu) {
      alerts.push({
        level: metrics.cpu.usage > 95 ? 'critical' : 'warning',
        message: `CPU使用率过高: ${metrics.cpu.usage}%`,
        metric: 'cpu',
        value: metrics.cpu.usage,
        threshold: this.config.thresholds.cpu,
        timestamp: metrics.timestamp,
        suggestion: '建议减少并发任务或等待当前任务完成'
      })
    }

    // 任务队列检查
    if (metrics.tasks.queued > this.config.thresholds.queueSize) {
      alerts.push({
        level: 'warning',
        message: `任务队列积压: ${metrics.tasks.queued}个任务`,
        metric: 'tasks',
        value: metrics.tasks.queued,
        threshold: this.config.thresholds.queueSize,
        timestamp: metrics.timestamp,
        suggestion: '建议检查任务处理速度或增加处理线程'
      })
    }

    // 网络延迟检查
    if (metrics.network.latency > this.config.thresholds.latency) {
      alerts.push({
        level: 'warning',
        message: `网络延迟过高: ${metrics.network.latency}ms`,
        metric: 'network',
        value: metrics.network.latency,
        threshold: this.config.thresholds.latency,
        timestamp: metrics.timestamp,
        suggestion: '建议检查网络连接或使用离线模式'
      })
    }

    // 添加新警报
    alerts.forEach(alert => {
      this.addAlert(alert)
    })
  }

  /**
   * 添加警报
   */
  private addAlert(alert: PerformanceAlert): void {
    this.alerts.push(alert)

    // 保持警报历史在合理范围内
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-100)
    }

    // 通知警报观察者
    this.alertObservers.forEach(observer => {
      try {
        observer(alert)
      }
      catch (error) {
        // 忽略警报观察者错误
      }
    })
  }

  /**
   * 通知观察者
   */
  private notifyObservers(metrics: PerformanceMetrics): void {
    this.observers.forEach(observer => {
      try {
        observer(metrics)
      }
      catch (error) {
        // 忽略性能监控观察者错误
      }
    })
  }

  /**
   * 订阅性能指标更新
   */
  subscribe(observer: (metrics: PerformanceMetrics) => void): () => void {
    this.observers.add(observer)
    return () => this.observers.delete(observer)
  }

  /**
   * 订阅警报
   */
  subscribeToAlerts(observer: (alert: PerformanceAlert) => void): () => void {
    this.alertObservers.add(observer)
    return () => this.alertObservers.delete(observer)
  }

  /**
   * 获取历史指标
   */
  getMetrics(timeRange?: { start: number; end: number }): PerformanceMetrics[] {
    if (!timeRange) {
      return [...this.metrics]
    }

    return this.metrics.filter(metric => 
      metric.timestamp >= timeRange.start && metric.timestamp <= timeRange.end
    )
  }

  /**
   * 获取最新指标
   */
  getLatestMetrics(): PerformanceMetrics | null {
    return this.metrics.length > 0 ? this.metrics[this.metrics.length - 1] : null
  }

  /**
   * 获取警报历史
   */
  getAlerts(level?: PerformanceAlert['level']): PerformanceAlert[] {
    if (!level) {
      return [...this.alerts]
    }

    return this.alerts.filter(alert => alert.level === level)
  }

  /**
   * 清除历史数据
   */
  clearHistory(): void {
    this.metrics = []
    this.alerts = []
  }

  /**
   * 生成性能报告
   */
  generateReport(): {
    summary: {
      averageMemoryUsage: number
      averageCPUUsage: number
      totalTasks: number
      alertCount: number
    }
    trends: {
      memoryTrend: 'increasing' | 'decreasing' | 'stable'
      cpuTrend: 'increasing' | 'decreasing' | 'stable'
    }
    recommendations: string[]
    } {
    if (this.metrics.length === 0) {
      return {
        summary: {
          averageMemoryUsage: 0,
          averageCPUUsage: 0,
          totalTasks: 0,
          alertCount: 0
        },
        trends: {
          memoryTrend: 'stable',
          cpuTrend: 'stable'
        },
        recommendations: ['暂无数据，请等待更多监控数据收集']
      }
    }

    const recentMetrics = this.metrics.slice(-20) // 最近20个数据点
    
    const avgMemory = recentMetrics.reduce((sum, m) => sum + m.memory.percentage, 0) / recentMetrics.length
    const avgCPU = recentMetrics.reduce((sum, m) => sum + m.cpu.usage, 0) / recentMetrics.length
    const totalTasks = recentMetrics.reduce((sum, m) => sum + m.tasks.completed + m.tasks.failed, 0)

    // 趋势分析
    const memoryTrend = this.analyzeTrend(recentMetrics.map(m => m.memory.percentage))
    const cpuTrend = this.analyzeTrend(recentMetrics.map(m => m.cpu.usage))

    // 生成建议
    const recommendations = this.generateRecommendations(avgMemory, avgCPU, this.alerts)

    return {
      summary: {
        averageMemoryUsage: Math.round(avgMemory),
        averageCPUUsage: Math.round(avgCPU),
        totalTasks,
        alertCount: this.alerts.length
      },
      trends: {
        memoryTrend,
        cpuTrend
      },
      recommendations
    }
  }

  /**
   * 分析数据趋势
   */
  private analyzeTrend(values: number[]): 'increasing' | 'decreasing' | 'stable' {
    if (values.length < 2) {
      return 'stable'
    }

    const first = values.slice(0, Math.floor(values.length / 2))
    const second = values.slice(Math.floor(values.length / 2))

    const firstAvg = first.reduce((sum, v) => sum + v, 0) / first.length
    const secondAvg = second.reduce((sum, v) => sum + v, 0) / second.length

    const change = (secondAvg - firstAvg) / firstAvg
    
    if (change > 0.1) return 'increasing'
    if (change < -0.1) return 'decreasing'
    return 'stable'
  }

  /**
   * 生成优化建议
   */
  private generateRecommendations(avgMemory: number, avgCPU: number, alerts: PerformanceAlert[]): string[] {
    const recommendations: string[] = []

    if (avgMemory > 80) {
      recommendations.push('内存使用率较高，建议定期清理缓存和临时文件')
    }

    if (avgCPU > 80) {
      recommendations.push('CPU使用率较高，建议减少并发任务数量')
    }

    if (alerts.filter(a => a.level === 'critical').length > 0) {
      recommendations.push('检测到严重性能问题，建议立即检查系统状态')
    }

    if (alerts.filter(a => a.metric === 'network').length > 5) {
      recommendations.push('网络连接不稳定，建议启用离线模式或检查网络设置')
    }

    if (recommendations.length === 0) {
      recommendations.push('系统运行良好，继续保持当前配置')
    }

    return recommendations
  }

  /**
   * 导出监控数据
   */
  exportData(): string {
    const data = {
      metrics: this.metrics,
      alerts: this.alerts,
      config: this.config,
      exportTime: new Date().toISOString()
    }

    return JSON.stringify(data, null, 2)
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<MonitoringConfig>): void {
    this.config = { ...this.config, ...newConfig }
    
    // 如果更改了监控间隔，重启监控
    if (newConfig.interval && this.intervalId) {
      this.stop()
      this.start()
    }
  }
}

// 创建默认实例
export const performanceMonitor = PerformanceMonitor.getInstance()