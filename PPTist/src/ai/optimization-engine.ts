/**
 * Netflix V2 Phase 6.2 AI配置优化引擎
 * 智能分析和优化系统配置
 */

import type { 
  HardwareProfile, 
  UsagePattern, 
  OptimizationRecommendation, 
  OptimizationStrategy,
  AIOptimizationConfig
} from './optimization-config'
import { HardwareAnalyzer } from './hardware-analyzer-simple'

/**
 * 配置优化结果
 */
export interface OptimizationResult {
  recommendations: OptimizationRecommendation[]
  appliedStrategies: string[]
  expectedPerformanceGain: number
  confidence: number
  timestamp: number
  hardwareProfile: HardwareProfile
  usagePattern?: UsagePattern
}

/**
 * 学习数据点
 */
interface LearningDataPoint {
  hardwareProfile: HardwareProfile
  usagePattern: UsagePattern
  configValues: Record<string, any>
  performanceMetrics: {
    processingTime: number
    resourceUsage: number
    errorRate: number
    userSatisfaction: number
  }
  timestamp: number
}

/**
 * AI配置优化引擎
 */
export class AIOptimizationEngine {
  private config: AIOptimizationConfig
  private hardwareAnalyzer: HardwareAnalyzer
  private learningData: LearningDataPoint[] = []
  private optimizationHistory: OptimizationResult[] = []
  private isOptimizing = false

  constructor(config: AIOptimizationConfig) {
    this.config = config
    this.hardwareAnalyzer = new HardwareAnalyzer()
    this.loadLearningData()
  }

  /**
   * 执行智能配置优化
   */
  optimize(usagePattern?: UsagePattern): OptimizationResult {
    if (this.isOptimizing) {
      throw new Error('优化引擎正在运行中')
    }

    this.isOptimizing = true

    try {
      // 1. 分析硬件性能
      const hardwareResult = this.hardwareAnalyzer.analyzeHardware()
      
      // 2. 分析使用模式
      const pattern = usagePattern || this.predictUsagePattern(hardwareResult.profile)
      
      // 3. 生成优化推荐
      const recommendations = this.generateRecommendations(hardwareResult.profile, pattern)
      
      // 4. 计算应用策略
      const appliedStrategies = this.selectOptimalStrategies(
        hardwareResult.profile, 
        pattern, 
        recommendations
      )
      
      // 5. 评估预期性能提升
      const expectedGain = this.calculateExpectedGain(recommendations)
      
      // 6. 计算置信度
      const confidence = this.calculateOptimizationConfidence(
        hardwareResult.profile, 
        pattern, 
        recommendations
      )

      const result: OptimizationResult = {
        recommendations,
        appliedStrategies,
        expectedPerformanceGain: expectedGain,
        confidence,
        timestamp: Date.now(),
        hardwareProfile: hardwareResult.profile,
        usagePattern: pattern
      }

      // 保存优化历史
      this.optimizationHistory.push(result)
      this.trimOptimizationHistory()

      return result
    }
    finally {
      this.isOptimizing = false
    }
  }

  /**
   * 学习用户使用模式
   */
  learnUsagePattern(dataPoint: LearningDataPoint): void {
    if (!this.config.usagePatternLearning.enabled) {
      return
    }

    this.learningData.push(dataPoint)
    this.trimLearningData()
    this.saveLearningData()
  }

  /**
   * 预测使用模式
   */
  private predictUsagePattern(hardwareProfile: HardwareProfile): UsagePattern {
    if (!this.config.usagePatternLearning.enabled || this.learningData.length === 0) {
      return this.getDefaultUsagePattern()
    }

    // 基于历史数据预测使用模式
    const relevantData = this.findRelevantLearningData(hardwareProfile)
    
    if (relevantData.length === 0) {
      return this.getDefaultUsagePattern()
    }

    // 聚合相关数据
    const avgSessionDuration = relevantData.reduce((sum, dp) => sum + dp.usagePattern.sessionDuration, 0) / relevantData.length
    const avgFileSize = relevantData.reduce((sum, dp) => sum + dp.usagePattern.averageFileSize, 0) / relevantData.length
    const avgFrequency = relevantData.reduce((sum, dp) => sum + dp.usagePattern.processingFrequency, 0) / relevantData.length

    // 获取最常用的质量设置
    const qualityMap = new Map<string, number>()
    relevantData.forEach(dp => {
      const quality = dp.usagePattern.preferredQuality
      qualityMap.set(quality, (qualityMap.get(quality) || 0) + 1)
    })
    
    const mostCommonQuality = Array.from(qualityMap.entries())
      .sort(([, a], [, b]) => b - a)[0]?.[0] as 'low' | 'medium' | 'high' | 'ultra' || 'medium'

    return {
      sessionDuration: Math.round(avgSessionDuration),
      averageFileSize: Math.round(avgFileSize),
      processingFrequency: Math.round(avgFrequency),
      peakUsageHours: [9, 10, 14, 15, 20, 21], // 默认高峰时段
      preferredQuality: mostCommonQuality,
      commonFormats: ['mp4', 'avi', 'mov'],
      errorPatterns: [],
      resourceBottlenecks: []
    }
  }

  /**
   * 生成优化推荐
   */
  private generateRecommendations(
    hardwareProfile: HardwareProfile, 
    usagePattern: UsagePattern
  ): OptimizationRecommendation[] {
    const recommendations: OptimizationRecommendation[] = []

    // 1. 应用预定义策略
    const strategies = this.loadOptimizationStrategies()
    strategies.forEach(strategy => {
      if (strategy.conditions(hardwareProfile, usagePattern)) {
        recommendations.push(...strategy.optimizations)
      }
    })

    // 2. 基于机器学习的推荐
    if (this.config.recommendationEngine.enabled) {
      const mlRecommendations = this.generateMLRecommendations(hardwareProfile, usagePattern)
      recommendations.push(...mlRecommendations)
    }

    // 3. 基于历史数据的推荐
    const historyRecommendations = this.generateHistoryBasedRecommendations(hardwareProfile)
    recommendations.push(...historyRecommendations)

    // 4. 排序和筛选推荐
    return this.rankAndFilterRecommendations(recommendations)
  }

  /**
   * 基于机器学习生成推荐
   */
  private generateMLRecommendations(
    hardwareProfile: HardwareProfile, 
    usagePattern: UsagePattern
  ): OptimizationRecommendation[] {
    const recommendations: OptimizationRecommendation[] = []

    // 简化的ML推荐逻辑
    const cpuScore = hardwareProfile.cpu.cores * hardwareProfile.cpu.frequency
    const memoryScore = hardwareProfile.memory.total
    const gpuScore = hardwareProfile.gpu.available ? hardwareProfile.gpu.memory : 0

    // CPU优化推荐
    if (cpuScore > 20 && usagePattern.preferredQuality === 'high') {
      recommendations.push({
        category: 'performance',
        priority: 'high',
        impact: 30,
        confidence: 0.85,
        title: 'AI推荐：启用高性能CPU处理',
        description: '基于硬件分析和使用模式，推荐启用高性能处理模式',
        implementation: {
          configKey: 'ai.cpu.highPerformanceMode',
          oldValue: false,
          newValue: true,
          reason: 'AI模型预测高性能模式适合当前配置'
        },
        expectedImprovement: {
          performance: 30,
          quality: 10,
          resourceUsage: 5
        }
      })
    }

    // 内存优化推荐
    if (memoryScore >= 16 && usagePattern.averageFileSize > 100) {
      recommendations.push({
        category: 'resource',
        priority: 'medium',
        impact: 25,
        confidence: 0.8,
        title: 'AI推荐：增加预加载缓存',
        description: '基于文件大小分析，推荐增加预加载缓存',
        implementation: {
          configKey: 'ai.cache.preloadSize',
          oldValue: '512MB',
          newValue: '2GB',
          reason: 'AI分析显示大文件处理需要更多缓存'
        },
        expectedImprovement: {
          performance: 25,
          quality: 5,
          resourceUsage: -10
        }
      })
    }

    // GPU优化推荐
    if (gpuScore >= 8 && usagePattern.preferredQuality !== 'low') {
      recommendations.push({
        category: 'performance',
        priority: 'high',
        impact: 40,
        confidence: 0.9,
        title: 'AI推荐：启用GPU加速渲染',
        description: '检测到高性能GPU，推荐启用硬件加速',
        implementation: {
          configKey: 'ai.gpu.acceleratedRendering',
          oldValue: false,
          newValue: true,
          reason: 'AI分析确认GPU性能足够支持加速渲染'
        },
        expectedImprovement: {
          performance: 40,
          quality: 15,
          resourceUsage: 0
        }
      })
    }

    return recommendations
  }

  /**
   * 基于历史数据生成推荐
   */
  private generateHistoryBasedRecommendations(
    hardwareProfile: HardwareProfile
  ): OptimizationRecommendation[] {
    const recommendations: OptimizationRecommendation[] = []

    // 分析历史优化结果
    const successfulOptimizations = this.optimizationHistory.filter(
      result => result.expectedPerformanceGain > 15 && result.confidence > 0.7
    )

    if (successfulOptimizations.length > 0) {
      // 找到最成功的配置模式
      const bestResult = successfulOptimizations.reduce((best, current) => 
        current.expectedPerformanceGain > best.expectedPerformanceGain ? current : best
      )

      // 如果当前硬件与历史成功案例相似，应用相似配置
      if (this.isHardwareSimilar(hardwareProfile, bestResult.hardwareProfile)) {
        recommendations.push({
          category: 'workflow',
          priority: 'medium',
          impact: Math.round(bestResult.expectedPerformanceGain * 0.8),
          confidence: 0.75,
          title: '历史推荐：应用成功配置模式',
          description: '基于历史成功案例，推荐应用类似配置',
          implementation: {
            configKey: 'history.appliedPattern',
            oldValue: 'default',
            newValue: bestResult.appliedStrategies.join(','),
            reason: '历史数据显示此配置模式效果良好'
          },
          expectedImprovement: {
            performance: Math.round(bestResult.expectedPerformanceGain * 0.8),
            quality: 5,
            resourceUsage: -5
          }
        })
      }
    }

    return recommendations
  }

  /**
   * 选择最优策略
   */
  private selectOptimalStrategies(
    hardwareProfile: HardwareProfile,
    usagePattern: UsagePattern,
    recommendations: OptimizationRecommendation[]
  ): string[] {
    const selectedStrategies: string[] = []
    const strategies = this.loadOptimizationStrategies()

    // 按影响力和置信度排序推荐
    const sortedRecommendations = recommendations.sort((a, b) => 
      (b.impact * b.confidence) - (a.impact * a.confidence)
    )

    // 选择最佳策略组合
    for (const strategy of strategies) {
      if (strategy.conditions(hardwareProfile, usagePattern)) {
        const strategyRecommendations = sortedRecommendations.filter(rec =>
          strategy.optimizations.some(opt => opt.title === rec.title)
        )

        if (strategyRecommendations.length > 0) {
          const avgImpact = strategyRecommendations.reduce((sum, rec) => sum + rec.impact, 0) / strategyRecommendations.length
          
          if (avgImpact >= 15) { // 只选择影响力大于15%的策略
            selectedStrategies.push(strategy.name)
          }
        }
      }
    }

    return selectedStrategies
  }

  /**
   * 计算预期性能提升
   */
  private calculateExpectedGain(recommendations: OptimizationRecommendation[]): number {
    if (recommendations.length === 0) return 0

    // 加权平均计算
    const totalWeight = recommendations.reduce((sum, rec) => sum + rec.confidence, 0)
    const weightedGain = recommendations.reduce((sum, rec) => 
      sum + (rec.expectedImprovement.performance * rec.confidence), 0
    )

    return Math.round(weightedGain / totalWeight)
  }

  /**
   * 计算优化置信度
   */
  private calculateOptimizationConfidence(
    hardwareProfile: HardwareProfile,
    usagePattern: UsagePattern,
    recommendations: OptimizationRecommendation[]
  ): number {
    if (recommendations.length === 0) return 0

    let baseConfidence = 0.6

    // 硬件检测置信度调整
    if (hardwareProfile.cpu.cores > 0) baseConfidence += 0.1
    if (hardwareProfile.memory.total > 0) baseConfidence += 0.1
    if (hardwareProfile.gpu.available) baseConfidence += 0.1

    // 推荐质量调整
    const avgRecConfidence = recommendations.reduce((sum, rec) => sum + rec.confidence, 0) / recommendations.length
    baseConfidence = (baseConfidence + avgRecConfidence) / 2

    // 历史数据调整
    if (this.optimizationHistory.length > 5) {
      baseConfidence += 0.1
    }

    return Math.min(1.0, baseConfidence)
  }

  /**
   * 辅助方法
   */
  private getDefaultUsagePattern(): UsagePattern {
    return {
      sessionDuration: 30,
      averageFileSize: 50,
      processingFrequency: 5,
      peakUsageHours: [9, 10, 14, 15, 20, 21],
      preferredQuality: 'medium',
      commonFormats: ['mp4', 'avi', 'mov'],
      errorPatterns: [],
      resourceBottlenecks: []
    }
  }

  private findRelevantLearningData(hardwareProfile: HardwareProfile): LearningDataPoint[] {
    return this.learningData.filter(dp => 
      this.isHardwareSimilar(hardwareProfile, dp.hardwareProfile)
    )
  }

  private isHardwareSimilar(profile1: HardwareProfile, profile2: HardwareProfile): boolean {
    const cpuSimilar = Math.abs(profile1.cpu.cores - profile2.cpu.cores) <= 2
    const memorySimilar = Math.abs(profile1.memory.total - profile2.memory.total) <= 4
    const gpuSimilar = profile1.gpu.available === profile2.gpu.available

    return cpuSimilar && memorySimilar && gpuSimilar
  }

  private loadOptimizationStrategies(): OptimizationStrategy[] {
    // 在实际实现中，这里会从配置文件加载
    // 现在返回一个简化的策略列表
    return [
      {
        name: 'high_performance_cpu',
        description: '高性能CPU优化策略',
        conditions: (profile) => profile.cpu.cores >= 8 && profile.cpu.frequency >= 3.0,
        optimizations: [],
        expectedGain: 25,
        riskLevel: 'low'
      },
      {
        name: 'memory_optimization',
        description: '内存优化策略',
        conditions: (profile) => profile.memory.total >= 16,
        optimizations: [],
        expectedGain: 20,
        riskLevel: 'low'
      }
    ]
  }

  private rankAndFilterRecommendations(recommendations: OptimizationRecommendation[]): OptimizationRecommendation[] {
    // 按优先级和影响力排序
    const sorted = recommendations.sort((a, b) => {
      const priorityWeight = { critical: 4, high: 3, medium: 2, low: 1 }
      const scoreA = priorityWeight[a.priority] * a.impact * a.confidence
      const scoreB = priorityWeight[b.priority] * b.impact * b.confidence
      return scoreB - scoreA
    })

    // 限制推荐数量
    const maxRecommendations = this.config.recommendationEngine.maxRecommendations
    return sorted.slice(0, maxRecommendations)
  }

  private trimLearningData(): void {
    const maxDataPoints = 1000
    if (this.learningData.length > maxDataPoints) {
      this.learningData = this.learningData.slice(-maxDataPoints)
    }
  }

  private trimOptimizationHistory(): void {
    const maxHistory = 100
    if (this.optimizationHistory.length > maxHistory) {
      this.optimizationHistory = this.optimizationHistory.slice(-maxHistory)
    }
  }

  private loadLearningData(): void {
    try {
      const saved = localStorage.getItem('netflix_ai_learning_data')
      if (saved) {
        this.learningData = JSON.parse(saved)
      }
    }
    catch {
      this.learningData = []
    }
  }

  private saveLearningData(): void {
    try {
      localStorage.setItem('netflix_ai_learning_data', JSON.stringify(this.learningData))
    }
    catch {
      // 静默失败
    }
  }
}