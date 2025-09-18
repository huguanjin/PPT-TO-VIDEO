/**
 * Netflix V2 Phase 6.2 硬件性能分析器
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
 * 基准测试配置
 */
interface BenchmarkTest {
  name: string
  description: string
  testFunction: () => Promise<number>
  weight: number
  timeout: number
}

/**
 * 硬件性能分析器类
 */
export class HardwareAnalyzer {
  private benchmarkTests: BenchmarkTest[] = []
  private detectionCache: Map<string, HardwareDetectionResult> = new Map()
  private isAnalyzing = false

  constructor() {
    this.initializeBenchmarkTests()
  }

  /**
   * 初始化基准测试
   */
  private initializeBenchmarkTests(): void {
    this.benchmarkTests = [
      {
        name: 'cpu_performance',
        description: 'CPU性能测试',
        testFunction: this.testCPUPerformance.bind(this),
        weight: 0.4,
        timeout: 5000
      },
      {
        name: 'memory_bandwidth',
        description: '内存带宽测试',
        testFunction: this.testMemoryBandwidth.bind(this),
        weight: 0.2,
        timeout: 3000
      },
      {
        name: 'gpu_compute',
        description: 'GPU计算测试',
        testFunction: this.testGPUCompute.bind(this),
        weight: 0.3,
        timeout: 5000
      },
      {
        name: 'storage_io',
        description: '存储IO测试',
        testFunction: this.testStorageIO.bind(this),
        weight: 0.1,
        timeout: 2000
      }
    ]
  }

  /**
   * 分析硬件性能
   */
  async analyzeHardware(): Promise<HardwareDetectionResult> {
    if (this.isAnalyzing) {
      throw new Error('硬件分析正在进行中')
    }

    this.isAnalyzing = true
    const startTime = performance.now()

    try {
      // 检查缓存
      const cacheKey = await this.generateHardwareFingerprint()
      const cached = this.detectionCache.get(cacheKey)
      if (cached && (Date.now() - cached.detectionTime) < 3600000) { // 1小时缓存
        return cached
      }

      // 获取硬件信息
      const profile = await this.detectHardwareProfile()
      
      // 运行基准测试
      const benchmarkScores = await this.runBenchmarkTests()
      
      // 计算性能评级
      const performanceRating = this.calculatePerformanceRating(benchmarkScores)
      
      // 生成推荐设置
      const recommendedSettings = this.generateRecommendedSettings(profile, benchmarkScores)
      
      // 计算置信度
      const confidence = this.calculateConfidence(profile, benchmarkScores)
      
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
  private async detectHardwareProfile(): Promise<HardwareProfile> {
    const profile: HardwareProfile = {
      cpu: await this.detectCPU(),
      memory: await this.detectMemory(),
      gpu: await this.detectGPU(),
      storage: await this.detectStorage()
    }

    return profile
  }

  /**
   * 检测CPU信息
   */
  private async detectCPU(): Promise<HardwareProfile['cpu']> {
    try {
      // 使用Navigator API获取CPU信息
      const cores = navigator.hardwareConcurrency || 4
      
      // 通过性能测试估算频率
      const frequency = await this.estimateCPUFrequency()
      
      return {
        cores,
        threads: cores, // 简化假设
        architecture: this.detectArchitecture(),
        frequency,
        cache: {
          l1: 32, // 默认值
          l2: 256,
          l3: 8
        }
      }
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.warn('CPU检测失败，使用默认值:', error)
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
      // 使用Device Memory API（如果可用）
      const deviceMemory = (navigator as any).deviceMemory
      const total = deviceMemory ? deviceMemory : this.estimateMemorySize()
      
      return {
        total,
        available: total * 0.7, // 估算可用内存
        speed: 3200, // 默认DDR4速度
        type: 'DDR4'
      }
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.warn('内存检测失败，使用默认值:', error)
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
      const gl = canvas.getContext('webgl') as WebGLRenderingContext | null
      
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

      // 估算GPU内存
      const memory = this.estimateGPUMemory(renderer)
      
      return {
        available: true,
        model: renderer,
        memory,
        computeCapability: this.estimateComputeCapability(renderer)
      }
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.warn('GPU检测失败:', error)
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
  private async detectStorage(): Promise<HardwareProfile['storage']> {
    try {
      // 通过IO测试估算存储类型和速度
      const ioSpeed = await this.measureStorageSpeed()
      
      return {
        type: ioSpeed > 200 ? 'SSD' : 'HDD',
        speed: ioSpeed,
        available: await this.estimateStorageSpace()
      }
    }
    catch (error) {
      // 存储检测失败，使用默认值
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
  private async runBenchmarkTests(): Promise<Record<string, number>> {
    const scores: Record<string, number> = {}
    
    for (const test of this.benchmarkTests) {
      try {
        const score = await Promise.race([
          test.testFunction(),
          new Promise<number>((_, reject) => 
            setTimeout(() => reject(new Error('测试超时')), test.timeout)
          )
        ])
        
        scores[test.name] = score
      }
      catch (error) {
        // 基准测试失败，使用默认分数0
        scores[test.name] = 0
      }
    }
    
    return scores
  }

  /**
   * CPU性能测试
   */
  private async testCPUPerformance(): Promise<number> {
    const startTime = performance.now()
    const iterations = 1000000
    
    // 计算密集型任务
    let result = 0
    for (let i = 0; i < iterations; i++) {
      result += Math.sqrt(i) * Math.sin(i)
    }
    
    const duration = performance.now() - startTime
    
    // 避免编译器优化掉计算结果
    if (result === 0) {
      return 0
    }
    
    // 使用Promise来确保异步
    return await Promise.resolve(Math.round(iterations / (duration / 1000)))
  }

  /**
   * 内存带宽测试
   */
  private async testMemoryBandwidth(): Promise<number> {
    const arraySize = 1024 * 1024 // 1MB
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
    
    // 使用sum避免编译器优化并使用Promise确保异步
    const bandwidthMBs = Math.round((arraySize * 4) / (duration / 1000) / 1024 / 1024)
    return await Promise.resolve(sum > 0 ? bandwidthMBs : 0)
  }

  /**
   * GPU计算测试
   */
  private async testGPUCompute(): Promise<number> {
    try {
      const canvas = document.createElement('canvas')
      const gl = canvas.getContext('webgl')
      
      if (!gl) return 0
      
      canvas.width = 512
      canvas.height = 512
      
      const startTime = performance.now()
      
      // 简单的GPU计算测试
      for (let i = 0; i < 100; i++) {
        gl.clear(gl.COLOR_BUFFER_BIT)
        gl.drawArrays(gl.TRIANGLES, 0, 3)
      }
      
      await new Promise(resolve => requestAnimationFrame(resolve))
      
      const duration = performance.now() - startTime
      
      // 返回FPS
      return Math.round(100 / (duration / 1000))
    }
    catch (error) {
      return 0
    }
  }

  /**
   * 存储IO测试
   */
  private async testStorageIO(): Promise<number> {
    const testData = new Uint8Array(1024 * 1024) // 1MB
    crypto.getRandomValues(testData)
    
    const startTime = performance.now()
    
    // 模拟存储写入
    const blob = new Blob([testData])
    const url = URL.createObjectURL(blob)
    
    try {
      await fetch(url)
      const duration = performance.now() - startTime
      
      // 返回速度 MB/s
      return Math.round(1 / (duration / 1000))
    }
    finally {
      URL.revokeObjectURL(url)
    }
  }

  /**
   * 辅助方法
   */
  private async estimateCPUFrequency(): Promise<number> {
    // 通过计算性能估算CPU频率
    const iterations = 100000
    const startTime = performance.now()
    
    for (let i = 0; i < iterations; i++) {
      Math.sin(i)
    }
    
    const duration = performance.now() - startTime
    const opsPerSecond = iterations / (duration / 1000)
    
    // 简化的频率估算 - 使用Promise来确保异步
    return await Promise.resolve(Math.max(1.0, Math.min(5.0, opsPerSecond / 50000)))
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
      // 基于网络连接类型估算设备等级
      switch (connection.effectiveType) {
        case '4g': return 8
        case '3g': return 4
        case '2g': return 2
        default: return 6
      }
    }
    return 8 // 默认8GB
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
    
    return 4 // 默认4GB
  }

  private estimateComputeCapability(renderer: string): number {
    const lowerRenderer = renderer.toLowerCase()
    
    if (lowerRenderer.includes('rtx 40')) return 8.9
    if (lowerRenderer.includes('rtx 30')) return 8.6
    if (lowerRenderer.includes('rtx 20')) return 7.5
    if (lowerRenderer.includes('gtx 16')) return 7.5
    if (lowerRenderer.includes('gtx 10')) return 6.1
    
    return 5.0 // 默认值
  }

  private async measureStorageSpeed(): Promise<number> {
    // 简化的存储速度测试
    const testSize = 1024 * 100 // 100KB
    const testData = new Uint8Array(testSize)
    crypto.getRandomValues(testData)
    
    const startTime = performance.now()
    
    // 使用localStorage模拟存储操作，使用Promise确保异步
    try {
      const base64Data = btoa(String.fromCharCode(...testData))
      localStorage.setItem('speed_test', base64Data)
      localStorage.removeItem('speed_test')
      
      const duration = performance.now() - startTime
      
      // 返回速度 MB/s
      return await Promise.resolve(Math.round((testSize / 1024 / 1024) / (duration / 1000)))
    }
    catch (error) {
      return await Promise.resolve(100) // 默认速度
    }
  }

  private async estimateStorageSpace(): Promise<number> {
    try {
      // 使用Storage API估算可用空间
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate()
        const totalGB = estimate.quota ? estimate.quota / 1024 / 1024 / 1024 : 100
        return Math.round(totalGB)
      }
    }
    catch (error) {
      // 忽略错误，使用默认值
    }
    
    return 100 // 默认100GB
  }

  private calculatePerformanceRating(scores: Record<string, number>): 'low' | 'medium' | 'high' | 'ultra' {
    // 计算综合得分
    let totalScore = 0
    let totalWeight = 0
    
    this.benchmarkTests.forEach(test => {
      const score = scores[test.name] || 0
      totalScore += score * test.weight
      totalWeight += test.weight
    })
    
    const averageScore = totalScore / totalWeight
    
    if (averageScore >= 1000) return 'ultra'
    if (averageScore >= 500) return 'high'
    if (averageScore >= 200) return 'medium'
    return 'low'
  }

  private generateRecommendedSettings(
    profile: HardwareProfile,
    scores: Record<string, number>
  ): Record<string, any> {
    const settings: Record<string, any> = {}
    
    // 基于CPU性能调整线程数
    const cpuScore = scores['CPU性能'] || 100
    settings.processingThreads = Math.min(profile.cpu.threads, Math.max(1, Math.floor(cpuScore / 100)))
    
    // 基于内存大小调整缓存
    settings.maxCacheSize = `${Math.floor(profile.memory.total * 0.3)}GB`
    
    // 基于GPU性能决定是否启用GPU加速
    const gpuScore = scores['GPU计算'] || 0
    settings.enableGPU = profile.gpu.available && profile.gpu.memory >= 4 && gpuScore > 50
    
    // 基于存储类型调整IO缓冲
    settings.ioBufferSize = profile.storage.type === 'SSD' ? '256KB' : '64KB'
    
    return settings
  }

  private calculateConfidence(
    profile: HardwareProfile,
    scores: Record<string, number>
  ): number {
    // 基于检测到的信息计算置信度
    let confidence = 0.5 // 基础置信度
    
    // 如果有详细的硬件信息，增加置信度
    if (profile.cpu.cores > 0) confidence += 0.1
    if (profile.memory.total > 0) confidence += 0.1
    if (profile.gpu.available) confidence += 0.1
    
    // 如果基准测试成功，增加置信度
    const successfulTests = Object.values(scores).filter(score => score > 0).length
    confidence += (successfulTests / this.benchmarkTests.length) * 0.3
    
    return Math.min(1.0, confidence)
  }

  private async generateHardwareFingerprint(): Promise<string> {
    const userAgent = navigator.userAgent
    const cores = navigator.hardwareConcurrency || 4
    const memory = (navigator as any).deviceMemory || 4
    const platform = navigator.platform
    
    const fingerprint = `${userAgent}_${cores}_${memory}_${platform}`
    
    // 生成哈希
    const encoder = new TextEncoder()
    const data = encoder.encode(fingerprint)
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  }
}