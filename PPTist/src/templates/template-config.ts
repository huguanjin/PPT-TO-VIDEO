/**
 * Netflix V2 Phase 6.3 自定义模板系统
 * 模板配置和类型定义
 */

export interface TemplateMetadata {
  id: string
  name: string
  description: string
  version: string
  author: string
  category: TemplateCategory
  tags: string[]
  thumbnail: string
  createdAt: Date
  updatedAt: Date
  downloads: number
  rating: number
  compatibility: string[]
  size: number // bytes
}

export interface TemplateConfig {
  // 基础设置
  name: string
  description: string
  
  // 视频设置
  video: {
    resolution: string
    fps: number
    format: string
    quality: 'low' | 'medium' | 'high' | 'ultra'
    codec: string
  }
  
  // 音频设置
  audio: {
    sampleRate: number
    bitrate: number
    channels: number
    format: string
    enhancementEnabled: boolean
  }
  
  // 字幕设置
  subtitle: {
    style: SubtitleStyle
    position: SubtitlePosition
    timing: SubtitleTiming
    multiline: boolean
    effects: SubtitleEffect[]
  }
  
  // 处理设置
  processing: {
    threads: number
    memoryLimit: string
    gpuAcceleration: boolean
    batchSize: number
    priority: 'low' | 'normal' | 'high'
  }
  
  // 输出设置
  output: {
    directory: string
    naming: string
    compression: boolean
    backup: boolean
    metadata: boolean
  }
  
  // 高级设置
  advanced: {
    customScript?: string
    hooks: ProcessingHooks
    plugins: string[]
    debugging: boolean
  }
}

export interface SubtitleStyle {
  fontFamily: string
  fontSize: number
  fontWeight: 'normal' | 'bold'
  color: string
  backgroundColor: string
  borderColor: string
  borderWidth: number
  shadowColor: string
  shadowOffset: { x: number; y: number }
  opacity: number
}

export interface SubtitlePosition {
  alignment: 'left' | 'center' | 'right'
  verticalAlignment: 'top' | 'middle' | 'bottom'
  margin: { top: number; right: number; bottom: number; left: number }
  maxWidth: number
}

export interface SubtitleTiming {
  offsetMs: number
  durationMultiplier: number
  minimumDuration: number
  maximumDuration: number
  fadeInMs: number
  fadeOutMs: number
}

export interface SubtitleEffect {
  type: 'fade' | 'slide' | 'zoom' | 'bounce' | 'typewriter'
  duration: number
  easing: string
  parameters: Record<string, any>
}

export interface ProcessingHooks {
  preProcess?: string
  postProcess?: string
  onError?: string
  onProgress?: string
  onComplete?: string
}

export type TemplateCategory = 
  | 'business'
  | 'education'
  | 'entertainment'
  | 'marketing'
  | 'tutorial'
  | 'presentation'
  | 'documentary'
  | 'social'
  | 'news'
  | 'gaming'
  | 'medical'
  | 'legal'
  | 'finance'
  | 'technology'
  | 'other'

export interface Template {
  metadata: TemplateMetadata
  config: TemplateConfig
  preview?: TemplatePreview
  validation?: TemplateValidation
}

export interface TemplatePreview {
  screenshots: string[]
  video?: string
  audio?: string
  description: string
  features: string[]
  requirements: string[]
}

export interface TemplateValidation {
  isValid: boolean
  errors: string[]
  warnings: string[]
  compatibility: {
    version: string
    features: string[]
    missing: string[]
  }
}

export interface TemplateMarketplace {
  featured: Template[]
  popular: Template[]
  recent: Template[]
  categories: Record<TemplateCategory, Template[]>
  userTemplates: Template[]
}

/**
 * 默认模板配置
 */
export const DEFAULT_TEMPLATE_CONFIG: TemplateConfig = {
  name: '标准模板',
  description: '通用的标准配置模板',
  
  video: {
    resolution: '1920x1080',
    fps: 30,
    format: 'mp4',
    quality: 'high',
    codec: 'h264'
  },
  
  audio: {
    sampleRate: 44100,
    bitrate: 128000,
    channels: 2,
    format: 'aac',
    enhancementEnabled: true
  },
  
  subtitle: {
    style: {
      fontFamily: 'Arial',
      fontSize: 24,
      fontWeight: 'normal',
      color: '#FFFFFF',
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      borderColor: '#000000',
      borderWidth: 1,
      shadowColor: '#000000',
      shadowOffset: { x: 1, y: 1 },
      opacity: 1.0
    },
    position: {
      alignment: 'center',
      verticalAlignment: 'bottom',
      margin: { top: 20, right: 20, bottom: 50, left: 20 },
      maxWidth: 80
    },
    timing: {
      offsetMs: 0,
      durationMultiplier: 1.0,
      minimumDuration: 500,
      maximumDuration: 8000,
      fadeInMs: 200,
      fadeOutMs: 200
    },
    multiline: true,
    effects: []
  },
  
  processing: {
    threads: 4,
    memoryLimit: '4GB',
    gpuAcceleration: false,
    batchSize: 10,
    priority: 'normal'
  },
  
  output: {
    directory: './output',
    naming: '{title}_{timestamp}',
    compression: true,
    backup: false,
    metadata: true
  },
  
  advanced: {
    hooks: {},
    plugins: [],
    debugging: false
  }
}

/**
 * 预定义模板
 */
export const PREDEFINED_TEMPLATES: Template[] = [
  {
    metadata: {
      id: 'business-presentation',
      name: '商务演示模板',
      description: '适合商务演示和会议的专业模板',
      version: '1.0.0',
      author: 'Netflix V2 Team',
      category: 'business',
      tags: ['商务', '演示', '会议', '专业'],
      thumbnail: '/templates/business-presentation.jpg',
      createdAt: new Date('2025-09-18'),
      updatedAt: new Date('2025-09-18'),
      downloads: 1250,
      rating: 4.8,
      compatibility: ['2.0.0+'],
      size: 1024 * 50 // 50KB
    },
    config: {
      ...DEFAULT_TEMPLATE_CONFIG,
      name: '商务演示模板',
      description: '专业的商务演示配置，适合企业会议和产品展示',
      video: {
        ...DEFAULT_TEMPLATE_CONFIG.video,
        quality: 'ultra'
      },
      subtitle: {
        ...DEFAULT_TEMPLATE_CONFIG.subtitle,
        style: {
          ...DEFAULT_TEMPLATE_CONFIG.subtitle.style,
          fontFamily: 'Microsoft YaHei',
          fontSize: 28,
          fontWeight: 'bold',
          color: '#2C3E50',
          backgroundColor: 'rgba(255, 255, 255, 0.9)'
        }
      }
    }
  },
  
  {
    metadata: {
      id: 'education-tutorial',
      name: '教育教程模板',
      description: '专为在线教育和培训课程设计',
      version: '1.0.0',
      author: 'Netflix V2 Team',
      category: 'education',
      tags: ['教育', '教程', '培训', '课程'],
      thumbnail: '/templates/education-tutorial.jpg',
      createdAt: new Date('2025-09-18'),
      updatedAt: new Date('2025-09-18'),
      downloads: 890,
      rating: 4.7,
      compatibility: ['2.0.0+'],
      size: 1024 * 45
    },
    config: {
      ...DEFAULT_TEMPLATE_CONFIG,
      name: '教育教程模板',
      description: '优化的教育内容配置，支持多语言字幕和清晰画质',
      subtitle: {
        ...DEFAULT_TEMPLATE_CONFIG.subtitle,
        style: {
          ...DEFAULT_TEMPLATE_CONFIG.subtitle.style,
          fontSize: 22,
          color: '#34495E',
          backgroundColor: 'rgba(255, 255, 255, 0.8)'
        },
        timing: {
          ...DEFAULT_TEMPLATE_CONFIG.subtitle.timing,
          minimumDuration: 800,
          maximumDuration: 6000
        },
        effects: [
          {
            type: 'fade',
            duration: 300,
            easing: 'ease-in-out',
            parameters: {}
          }
        ]
      }
    }
  },
  
  {
    metadata: {
      id: 'social-media',
      name: '社交媒体模板',
      description: '针对社交平台优化的短视频模板',
      version: '1.0.0',
      author: 'Netflix V2 Team',
      category: 'social',
      tags: ['社交', '短视频', '移动端', '快速'],
      thumbnail: '/templates/social-media.jpg',
      createdAt: new Date('2025-09-18'),
      updatedAt: new Date('2025-09-18'),
      downloads: 2100,
      rating: 4.6,
      compatibility: ['2.0.0+'],
      size: 1024 * 35
    },
    config: {
      ...DEFAULT_TEMPLATE_CONFIG,
      name: '社交媒体模板',
      description: '快速生成适合社交平台的短视频内容',
      video: {
        ...DEFAULT_TEMPLATE_CONFIG.video,
        resolution: '1080x1920', // 竖屏
        fps: 60,
        quality: 'high'
      },
      subtitle: {
        ...DEFAULT_TEMPLATE_CONFIG.subtitle,
        style: {
          ...DEFAULT_TEMPLATE_CONFIG.subtitle.style,
          fontSize: 32,
          fontWeight: 'bold',
          color: '#FFFFFF',
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          borderWidth: 2
        },
        position: {
          ...DEFAULT_TEMPLATE_CONFIG.subtitle.position,
          verticalAlignment: 'middle',
          maxWidth: 90
        }
      },
      processing: {
        ...DEFAULT_TEMPLATE_CONFIG.processing,
        priority: 'high',
        batchSize: 5
      }
    }
  }
]

/**
 * 模板验证规则
 */
export interface TemplateValidationRule {
  field: string
  type: 'required' | 'range' | 'format' | 'custom'
  message: string
  validator?: (value: any) => boolean
  min?: number
  max?: number
  pattern?: RegExp
}

export const TEMPLATE_VALIDATION_RULES: TemplateValidationRule[] = [
  {
    field: 'name',
    type: 'required',
    message: '模板名称不能为空'
  },
  {
    field: 'video.fps',
    type: 'range',
    message: '帧率必须在15-120之间',
    min: 15,
    max: 120
  },
  {
    field: 'audio.sampleRate',
    type: 'custom',
    message: '采样率必须是标准值',
    validator: (value) => [22050, 44100, 48000, 96000].includes(value)
  },
  {
    field: 'subtitle.style.fontSize',
    type: 'range',
    message: '字体大小必须在12-72之间',
    min: 12,
    max: 72
  },
  {
    field: 'processing.threads',
    type: 'range',
    message: '线程数必须在1-32之间',
    min: 1,
    max: 32
  }
]

/**
 * 模板配置工具类
 */
export class TemplateConfigUtils {
  static validateTemplate(template: Template): TemplateValidation {
    const errors: string[] = []
    const warnings: string[] = []
    
    // 运行验证规则
    for (const rule of TEMPLATE_VALIDATION_RULES) {
      const value = this.getNestedValue(template.config, rule.field)
      
      if (!this.validateField(value, rule)) {
        errors.push(rule.message)
      }
    }
    
    // 检查兼容性
    const compatibility = this.checkCompatibility(template)
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      compatibility
    }
  }
  
  static mergeConfigs(base: TemplateConfig, override: Partial<TemplateConfig>): TemplateConfig {
    return {
      ...base,
      ...override,
      video: { ...base.video, ...override.video },
      audio: { ...base.audio, ...override.audio },
      subtitle: {
        ...base.subtitle,
        ...override.subtitle,
        style: { ...base.subtitle.style, ...override.subtitle?.style },
        position: { ...base.subtitle.position, ...override.subtitle?.position },
        timing: { ...base.subtitle.timing, ...override.subtitle?.timing }
      },
      processing: { ...base.processing, ...override.processing },
      output: { ...base.output, ...override.output },
      advanced: {
        ...base.advanced,
        ...override.advanced,
        hooks: { ...base.advanced.hooks, ...override.advanced?.hooks }
      }
    }
  }
  
  private static getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj)
  }
  
  private static validateField(value: any, rule: TemplateValidationRule): boolean {
    switch (rule.type) {
      case 'required':
        return value !== null && value !== undefined && value !== ''
      case 'range':
        return value >= (rule.min || 0) && value <= (rule.max || Infinity)
      case 'format':
        return rule.pattern ? rule.pattern.test(value) : true
      case 'custom':
        return rule.validator ? rule.validator(value) : true
      default:
        return true
    }
  }
  
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  private static checkCompatibility(template: Template) {
    return {
      version: '2.0.0',
      features: ['ai-optimization', 'multi-language', 'custom-templates'],
      missing: []
    }
  }
}