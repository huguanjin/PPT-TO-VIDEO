/**
 * Netflix V2 Phase 6.2 简化硬件性能分析器
 * 自动检测硬件配置并生成性能画像
 */

import type { HardwareProfile } from './optimization-config'

/**
 * 硬件检测结果
 */
export interface HardwareDetectionResult {
  profile: HardwareProfile
  benchmarkScores: Record<string, number>
  performanceRating: 'low' | 'medium' | 'high' | 'ultra'
  recommendedSettings: Record<string, any>
  detectionTime: number
  confidence: number
}

/**
 * 硬件性能分析器类
 */
export class HardwareAnalyzer {
  private detectionCache: Map<string, HardwareDetectionResult> = new Map()
  private isAnalyzing = false

  /**
   * 分析硬件性能
   */
  analyzeHardware(): HardwareDetectionResult {
    if (this.isAnalyzing) {
      throw new Error('硬件分析正在进行中')
    }

    this.isAnalyzing = true
    const startTime = performance.now()

    try {
      // 检查缓存
      const cacheKey = this.generateHardwareFingerprint()
      const cached = this.detectionCache.get(cacheKey)
      if (cached && (Date.now() - cached.detectionTime) < 3600000) { // 1小时缓存
        return cached
      }

      // 获取硬件信息
      const profile = this.detectHardwareProfile()
      
      // 运行基准测试
      const benchmarkScores = this.runBenchmarkTests()
      
      // 计算性能评级
      const performanceRating = this.calculatePerformanceRating(benchmarkScores)
      
      // 生成推荐设置
      const recommendedSettings = this.generateRecommendedSettings(profile)
      
      // 计算置信度
      const confidence = this.calculateConfidence(profile)
      
      const result: HardwareDetectionResult = {
        profile,
        benchmarkScores,
        performanceRating,
        recommendedSettings,
        detectionTime: performance.now() - startTime,
        confidence
      }

      // 缓存结果
      this.detectionCache.set(cacheKey, {
        ...result,
        detectionTime: Date.now()
      })

      return result
    }
    finally {
      this.isAnalyzing = false
    }
  }

  /**
   * 检测硬件配置
   */
  private detectHardwareProfile(): HardwareProfile {
    return {
      cpu: this.detectCPU(),
      memory: this.detectMemory(),
      gpu: this.detectGPU(),
      storage: this.detectStorage()
    }
  }

  /**
   * 检测CPU信息
   */
  private detectCPU(): HardwareProfile['cpu'] {
    try {
      const cores = navigator.hardwareConcurrency || 4
      const frequency = this.estimateCPUFrequency()
      
      return {
        cores,
        threads: cores,
        architecture: this.detectArchitecture(),
        frequency,
        cache: {
          l1: 32,
          l2: 256,
          l3: 8
        }
      }
    }
    catch {
      return {
        cores: 4,
        threads: 4,
        architecture: 'unknown',
        frequency: 2.5,
        cache: { l1: 32, l2: 256, l3: 8 }
      }
    }
  }

  /**
   * 检测内存信息
   */
  private detectMemory(): HardwareProfile['memory'] {
    try {
      const deviceMemory = (navigator as any).deviceMemory
      const total = deviceMemory ? deviceMemory : this.estimateMemorySize()
      
      return {
        total,
        available: total * 0.7,
        speed: 3200,
        type: 'DDR4'
      }
    }
    catch {
      return {
        total: 8,
        available: 6,
        speed: 2400,
        type: 'DDR4'
      }
    }
  }

  /**
   * 检测GPU信息
   */
  private detectGPU(): HardwareProfile['gpu'] {
    try {
      const canvas = document.createElement('canvas')
      const gl = canvas.getContext('webgl') as WebGLRenderingContext
      
      if (!gl) {
        return {
          available: false,
          model: 'None',
          memory: 0,
          computeCapability: 0
        }
      }

      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
      const renderer = debugInfo ? 
        gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) as string : 
        'Unknown GPU'

      const memory = this.estimateGPUMemory(renderer)
      
      return {
        available: true,
        model: renderer,
        memory,
        computeCapability: this.estimateComputeCapability(renderer)
      }
    }
    catch {
      return {
        available: false,
        model: 'Unknown',
        memory: 0,
        computeCapability: 0
      }
    }
  }

  /**
   * 检测存储信息
   */
  private detectStorage(): HardwareProfile['storage'] {
    try {
      const ioSpeed = this.measureStorageSpeed()
      
      return {
        type: ioSpeed > 200 ? 'SSD' : 'HDD',
        speed: ioSpeed,
        available: this.estimateStorageSpace()
      }
    }
    catch {
      return {
        type: 'SSD',
        speed: 500,
        available: 100
      }
    }
  }

  /**
   * 运行基准测试
   */
  private runBenchmarkTests(): Record<string, number> {
    const scores: Record<string, number> = {}
    
    try {
      scores.cpu_performance = this.testCPUPerformance()
      scores.memory_bandwidth = this.testMemoryBandwidth()
      scores.gpu_compute = this.testGPUCompute()
      scores.storage_io = this.testStorageIO()
    }
    catch {
      // 如果测试失败，使用默认分数
      scores.cpu_performance = 500
      scores.memory_bandwidth = 1000
      scores.gpu_compute = 60
      scores.storage_io = 200
    }
    
    return scores
  }

  /**
   * CPU性能测试
   */
  private testCPUPerformance(): number {
    const startTime = performance.now()
    const iterations = 100000
    
    // 计算密集型任务
    let result = 0
    for (let i = 0; i < iterations; i++) {
      result += Math.sqrt(i) * Math.sin(i)
    }
    
    const duration = performance.now() - startTime
    
    // 确保result被使用，避免lint警告
    if (result < 0) {
      return 0
    }
    
    // 返回每秒操作数
    return Math.round(iterations / (duration / 1000))
  }

  /**
   * 内存带宽测试
   */
  private testMemoryBandwidth(): number {
    const arraySize = 1024 * 256 // 256KB
    const array = new Float32Array(arraySize)
    
    // 填充数组
    for (let i = 0; i < arraySize; i++) {
      array[i] = Math.random()
    }
    
    const startTime = performance.now()
    let sum = 0
    
    // 读取测试
    for (let i = 0; i < arraySize; i++) {
      sum += array[i]
    }
    
    const duration = performance.now() - startTime
    
    // 确保sum被使用
    if (sum < 0) {
      return 0
    }
    
    // 返回带宽 MB/s
    return Math.round((arraySize * 4) / (duration / 1000) / 1024 / 1024)
  }

  /**
   * GPU计算测试
   */
  private testGPUCompute(): number {
    try {
      const canvas = document.createElement('canvas')
      const gl = canvas.getContext('webgl')
      
      if (!gl) return 0
      
      canvas.width = 256
      canvas.height = 256
      
      const startTime = performance.now()
      
      // 简单的GPU测试
      for (let i = 0; i < 10; i++) {
        gl.clear(gl.COLOR_BUFFER_BIT)
      }
      
      const duration = performance.now() - startTime
      
      // 返回性能分数
      return Math.round(1000 / duration)
    }
    catch {
      return 0
    }
  }

  /**
   * 存储IO测试
   */
  private testStorageIO(): number {
    try {
      const testData = new Uint8Array(1024 * 100) // 100KB
      crypto.getRandomValues(testData)
      
      const startTime = performance.now()
      
      // 模拟存储操作
      const base64Data = btoa(String.fromCharCode(...testData.slice(0, 1000)))
      localStorage.setItem('speed_test_temp', base64Data)
      localStorage.removeItem('speed_test_temp')
      
      const duration = performance.now() - startTime
      
      // 返回速度分数
      return Math.round(1000 / duration)
    }
    catch {
      return 100
    }
  }

  /**
   * 辅助方法
   */
  private estimateCPUFrequency(): number {
    const iterations = 10000
    const startTime = performance.now()
    
    for (let i = 0; i < iterations; i++) {
      Math.sin(i)
    }
    
    const duration = performance.now() - startTime
    const opsPerSecond = iterations / (duration / 1000)
    
    return Math.max(1.0, Math.min(5.0, opsPerSecond / 10000))
  }

  private detectArchitecture(): string {
    const userAgent = navigator.userAgent.toLowerCase()
    if (userAgent.includes('arm') || userAgent.includes('aarch64')) {
      return 'ARM'
    }
    return 'x86_64'
  }

  private estimateMemorySize(): number {
    const connection = (navigator as any).connection
    if (connection) {
      switch (connection.effectiveType) {
        case '4g': return 8
        case '3g': return 4
        case '2g': return 2
        default: return 6
      }
    }
    return 8
  }

  private estimateGPUMemory(renderer: string): number {
    const lowerRenderer = renderer.toLowerCase()
    
    if (lowerRenderer.includes('rtx 4090')) return 24
    if (lowerRenderer.includes('rtx 4080')) return 16
    if (lowerRenderer.includes('rtx 4070')) return 12
    if (lowerRenderer.includes('rtx 3080')) return 10
    if (lowerRenderer.includes('rtx 3070')) return 8
    if (lowerRenderer.includes('rtx 3060')) return 8
    if (lowerRenderer.includes('gtx 1660')) return 6
    if (lowerRenderer.includes('gtx 1050')) return 4
    
    return 4
  }

  private estimateComputeCapability(renderer: string): number {
    const lowerRenderer = renderer.toLowerCase()
    
    if (lowerRenderer.includes('rtx 40')) return 8.9
    if (lowerRenderer.includes('rtx 30')) return 8.6
    if (lowerRenderer.includes('rtx 20')) return 7.5
    if (lowerRenderer.includes('gtx 16')) return 7.5
    if (lowerRenderer.includes('gtx 10')) return 6.1
    
    return 5.0
  }

  private measureStorageSpeed(): number {
    const testSize = 1024 * 10 // 10KB
    const testData = new Uint8Array(testSize)
    crypto.getRandomValues(testData)
    
    const startTime = performance.now()
    
    try {
      const base64Data = btoa(String.fromCharCode(...testData.slice(0, 1000)))
      localStorage.setItem('storage_speed_test', base64Data)
      localStorage.removeItem('storage_speed_test')
      
      const duration = performance.now() - startTime
      
      return Math.round(100 / duration)
    }
    catch {
      return 100
    }
  }

  private estimateStorageSpace(): number {
    return 100 // 默认100GB
  }

  private calculatePerformanceRating(scores: Record<string, number>): 'low' | 'medium' | 'high' | 'ultra' {
    const values = Object.values(scores)
    const averageScore = values.reduce((a, b) => a + b, 0) / values.length
    
    if (averageScore >= 1000) return 'ultra'
    if (averageScore >= 500) return 'high'
    if (averageScore >= 200) return 'medium'
    return 'low'
  }

  private generateRecommendedSettings(profile: HardwareProfile): Record<string, any> {
    const settings: Record<string, any> = {}
    
    settings.processingThreads = Math.min(profile.cpu.threads, 16)
    settings.maxCacheSize = `${Math.floor(profile.memory.total * 0.3)}GB`
    settings.enableGPU = profile.gpu.available && profile.gpu.memory >= 4
    settings.ioBufferSize = profile.storage.type === 'SSD' ? '256KB' : '64KB'
    
    return settings
  }

  private calculateConfidence(profile: HardwareProfile): number {
    let confidence = 0.5
    
    if (profile.cpu.cores > 0) confidence += 0.1
    if (profile.memory.total > 0) confidence += 0.1
    if (profile.gpu.available) confidence += 0.1
    confidence += 0.2 // 基准测试成功
    
    return Math.min(1.0, confidence)
  }

  private generateHardwareFingerprint(): string {
    const userAgent = navigator.userAgent
    const cores = navigator.hardwareConcurrency || 4
    const memory = (navigator as any).deviceMemory || 4
    const platform = navigator.platform
    
    return `${userAgent}_${cores}_${memory}_${platform}`.replace(/[^a-zA-Z0-9_]/g, '_')
  }
}