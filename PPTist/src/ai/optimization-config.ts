/**
 * Netflix V2 Phase 6.2 AI驱动配置优化系统
 * 核心配置文件
 */

export interface HardwareProfile {
  cpu: {
    cores: number
    threads: number
    architecture: string
    frequency: number // GHz
    cache: {
      l1: number // KB
      l2: number // KB
      l3: number // MB
    }
  }
  memory: {
    total: number // GB
    available: number // GB
    speed: number // MHz
    type: string // DDR4/DDR5
  }
  gpu: {
    available: boolean
    model: string
    memory: number // GB
    computeCapability: number
  }
  storage: {
    type: string // SSD/HDD
    speed: number // MB/s
    available: number // GB
  }
}

export interface UsagePattern {
  sessionDuration: number // minutes
  averageFileSize: number // MB
  processingFrequency: number // times per day
  peakUsageHours: number[]
  preferredQuality: 'low' | 'medium' | 'high' | 'ultra'
  commonFormats: string[]
  errorPatterns: string[]
  resourceBottlenecks: string[]
}

export interface OptimizationRecommendation {
  category: 'performance' | 'quality' | 'resource' | 'workflow'
  priority: 'low' | 'medium' | 'high' | 'critical'
  impact: number // 1-100
  confidence: number // 0-1
  title: string
  description: string
  implementation: {
    configKey: string
    oldValue: any
    newValue: any | ((profile: HardwareProfile) => any)
    reason: string
  }
  expectedImprovement: {
    performance: number // percentage
    quality: number // percentage
    resourceUsage: number // percentage
  }
}

export interface AIOptimizationConfig {
  // 硬件分析配置
  hardwareAnalysis: {
    enabled: boolean
    profilingInterval: number // seconds
    benchmarkTests: string[]
    adaptiveThresholds: {
      cpuUsage: number
      memoryUsage: number
      gpuUsage: number
    }
  }

  // 使用模式学习
  usagePatternLearning: {
    enabled: boolean
    learningWindow: number // days
    minDataPoints: number
    confidenceThreshold: number
    adaptationRate: number
  }

  // 推荐引擎
  recommendationEngine: {
    enabled: boolean
    maxRecommendations: number
    autoApply: {
      enabled: boolean
      safetyThreshold: number
      backupConfigs: boolean
    }
    weightFactors: {
      performance: number
      quality: number
      stability: number
      resourceEfficiency: number
    }
  }

  // 预测模型
  predictionModel: {
    enabled: boolean
    modelType: 'linear' | 'polynomial' | 'neural' | 'ensemble'
    features: string[]
    updateFrequency: number // hours
    validationSplit: number
  }

  // 智能调度
  intelligentScheduling: {
    enabled: boolean
    priorityLevels: number
    resourceAwareScheduling: boolean
    batchOptimization: boolean
    predictivePreloading: boolean
  }
}

export const DEFAULT_AI_OPTIMIZATION_CONFIG: AIOptimizationConfig = {
  hardwareAnalysis: {
    enabled: true,
    profilingInterval: 30,
    benchmarkTests: [
      'cpu_stress',
      'memory_bandwidth',
      'gpu_compute',
      'storage_io'
    ],
    adaptiveThresholds: {
      cpuUsage: 0.8,
      memoryUsage: 0.9,
      gpuUsage: 0.85
    }
  },

  usagePatternLearning: {
    enabled: true,
    learningWindow: 7,
    minDataPoints: 10,
    confidenceThreshold: 0.7,
    adaptationRate: 0.1
  },

  recommendationEngine: {
    enabled: true,
    maxRecommendations: 10,
    autoApply: {
      enabled: false,
      safetyThreshold: 0.9,
      backupConfigs: true
    },
    weightFactors: {
      performance: 0.4,
      quality: 0.3,
      stability: 0.2,
      resourceEfficiency: 0.1
    }
  },

  predictionModel: {
    enabled: true,
    modelType: 'ensemble',
    features: [
      'hardware_profile',
      'usage_pattern',
      'historical_performance',
      'resource_utilization',
      'error_frequency'
    ],
    updateFrequency: 6,
    validationSplit: 0.2
  },

  intelligentScheduling: {
    enabled: true,
    priorityLevels: 5,
    resourceAwareScheduling: true,
    batchOptimization: true,
    predictivePreloading: true
  }
}

/**
 * 优化策略定义
 */
export interface OptimizationStrategy {
  name: string
  description: string
  conditions: (profile: HardwareProfile, pattern: UsagePattern) => boolean
  optimizations: OptimizationRecommendation[]
  expectedGain: number // percentage
  riskLevel: 'low' | 'medium' | 'high'
}

/**
 * 预定义优化策略
 */
export const OPTIMIZATION_STRATEGIES: OptimizationStrategy[] = [
  {
    name: 'high_performance_cpu',
    description: '高性能CPU优化策略',
    conditions: (profile) => profile.cpu.cores >= 8 && profile.cpu.frequency >= 3.0,
    optimizations: [
      {
        category: 'performance',
        priority: 'high',
        impact: 25,
        confidence: 0.9,
        title: '启用多线程处理',
        description: '利用多核CPU优势，提升处理速度',
        implementation: {
          configKey: 'processing.threads',
          oldValue: 4,
          newValue: (profile: HardwareProfile) => Math.min(profile.cpu.threads, 16),
          reason: '检测到高性能CPU，增加处理线程数'
        },
        expectedImprovement: {
          performance: 25,
          quality: 0,
          resourceUsage: 10
        }
      }
    ],
    expectedGain: 25,
    riskLevel: 'low'
  },

  {
    name: 'memory_optimization',
    description: '内存优化策略',
    conditions: (profile) => profile.memory.total >= 16,
    optimizations: [
      {
        category: 'resource',
        priority: 'medium',
        impact: 20,
        confidence: 0.85,
        title: '增加内存缓存',
        description: '利用充足内存提升缓存性能',
        implementation: {
          configKey: 'cache.maxMemory',
          oldValue: '2GB',
          newValue: (profile: HardwareProfile) => `${Math.floor(profile.memory.total * 0.3)}GB`,
          reason: '检测到充足内存，增加缓存大小'
        },
        expectedImprovement: {
          performance: 20,
          quality: 5,
          resourceUsage: -15
        }
      }
    ],
    expectedGain: 20,
    riskLevel: 'low'
  },

  {
    name: 'gpu_acceleration',
    description: 'GPU加速优化策略',
    conditions: (profile) => profile.gpu.available && profile.gpu.memory >= 4,
    optimizations: [
      {
        category: 'performance',
        priority: 'high',
        impact: 40,
        confidence: 0.8,
        title: '启用GPU加速',
        description: '使用GPU加速视频处理和渲染',
        implementation: {
          configKey: 'rendering.useGPU',
          oldValue: false,
          newValue: true,
          reason: '检测到兼容GPU，启用硬件加速'
        },
        expectedImprovement: {
          performance: 40,
          quality: 10,
          resourceUsage: 5
        }
      }
    ],
    expectedGain: 40,
    riskLevel: 'medium'
  },

  {
    name: 'storage_optimization',
    description: '存储优化策略',
    conditions: (profile) => profile.storage.type === 'SSD' && profile.storage.speed >= 500,
    optimizations: [
      {
        category: 'performance',
        priority: 'medium',
        impact: 15,
        confidence: 0.9,
        title: '优化IO缓冲',
        description: '针对SSD存储优化读写缓冲区',
        implementation: {
          configKey: 'io.bufferSize',
          oldValue: '64KB',
          newValue: '256KB',
          reason: '检测到高速SSD，增加IO缓冲区大小'
        },
        expectedImprovement: {
          performance: 15,
          quality: 0,
          resourceUsage: 5
        }
      }
    ],
    expectedGain: 15,
    riskLevel: 'low'
  }
]

/**
 * 机器学习模型配置
 */
export interface MLModelConfig {
  modelId: string
  version: string
  type: 'regression' | 'classification' | 'clustering'
  features: string[]
  hyperparameters: Record<string, any>
  performance: {
    accuracy: number
    precision: number
    recall: number
    f1Score: number
  }
  lastTrained: Date
  trainingData: {
    samples: number
    features: number
    validationScore: number
  }
}

/**
 * 默认机器学习模型配置
 */
export const DEFAULT_ML_MODELS: MLModelConfig[] = [
  {
    modelId: 'performance_predictor',
    version: '1.0.0',
    type: 'regression',
    features: [
      'cpu_cores',
      'memory_total',
      'gpu_memory',
      'file_size',
      'complexity_score'
    ],
    hyperparameters: {
      learningRate: 0.001,
      epochs: 100,
      batchSize: 32,
      hiddenLayers: [128, 64, 32]
    },
    performance: {
      accuracy: 0.92,
      precision: 0.89,
      recall: 0.91,
      f1Score: 0.90
    },
    lastTrained: new Date(),
    trainingData: {
      samples: 10000,
      features: 15,
      validationScore: 0.88
    }
  },

  {
    modelId: 'resource_optimizer',
    version: '1.0.0',
    type: 'classification',
    features: [
      'current_usage',
      'peak_usage',
      'usage_pattern',
      'resource_type'
    ],
    hyperparameters: {
      maxDepth: 10,
      nEstimators: 100,
      minSamplesSplit: 2
    },
    performance: {
      accuracy: 0.87,
      precision: 0.85,
      recall: 0.88,
      f1Score: 0.86
    },
    lastTrained: new Date(),
    trainingData: {
      samples: 5000,
      features: 8,
      validationScore: 0.84
    }
  }
]