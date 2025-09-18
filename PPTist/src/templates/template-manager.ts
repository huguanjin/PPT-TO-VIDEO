/**
 * Netflix V2 Phase 6.3 模板管理器
 * 负责模板的CRUD操作、验证、导入导出等核心功能
 */

import { 
  type Template, 
  type TemplateConfig, 
  type TemplateMetadata, 
  type TemplateValidation,
  type TemplateMarketplace,
  type TemplateCategory,
  PREDEFINED_TEMPLATES,
  TemplateConfigUtils
} from './template-config'

export interface TemplateManagerOptions {
  storageKey?: string
  autoSave?: boolean
  validateOnSave?: boolean
  enableCache?: boolean
  maxCacheSize?: number
}

export interface TemplateFilter {
  category?: TemplateCategory
  tags?: string[]
  author?: string
  minRating?: number
  maxSize?: number
  compatibility?: string
  searchTerm?: string
}

export interface TemplateSortOptions {
  field: 'name' | 'createdAt' | 'updatedAt' | 'rating' | 'downloads'
  order: 'asc' | 'desc'
}

export interface TemplateImportResult {
  success: boolean
  template?: Template
  errors: string[]
  warnings: string[]
}

export interface TemplateExportOptions {
  includePreview?: boolean
  includeMetadata?: boolean
  format?: 'json' | 'zip'
  compression?: boolean
}

export class TemplateManager {
  private templates: Map<string, Template> = new Map()
  private options: TemplateManagerOptions
  private cache: Map<string, any> = new Map()
  
  constructor(options: TemplateManagerOptions = {}) {
    this.options = {
      storageKey: 'netflix-v2-templates',
      autoSave: true,
      validateOnSave: true,
      enableCache: true,
      maxCacheSize: 100,
      ...options
    }
    
    this.initializeTemplates()
  }
  
  /**
   * 初始化预定义模板
   */
  private initializeTemplates(): void {
    // 加载预定义模板
    for (const template of PREDEFINED_TEMPLATES) {
      this.templates.set(template.metadata.id, template)
    }
    
    // 从本地存储加载用户模板
    this.loadFromStorage()
  }
  
  /**
   * 获取所有模板
   */
  getAllTemplates(): Template[] {
    return Array.from(this.templates.values())
  }
  
  /**
   * 根据ID获取模板
   */
  getTemplate(id: string): Template | undefined {
    return this.templates.get(id)
  }
  
  /**
   * 创建新模板
   */
  createTemplate(config: TemplateConfig, metadata: Partial<TemplateMetadata>): string {
    const id = this.generateId()
    const template: Template = {
      metadata: {
        id,
        name: metadata.name || config.name,
        description: metadata.description || config.description,
        version: metadata.version || '1.0.0',
        author: metadata.author || 'User',
        category: metadata.category || 'other',
        tags: metadata.tags || [],
        thumbnail: metadata.thumbnail || '',
        createdAt: new Date(),
        updatedAt: new Date(),
        downloads: 0,
        rating: 0,
        compatibility: ['2.0.0+'],
        size: this.calculateSize(config)
      },
      config,
      validation: this.options.validateOnSave ? TemplateConfigUtils.validateTemplate({ metadata: {} as TemplateMetadata, config }) : undefined
    }
    
    this.templates.set(id, template)
    
    if (this.options.autoSave) {
      this.saveToStorage()
    }
    
    return id
  }
  
  /**
   * 更新模板
   */
  updateTemplate(id: string, updates: Partial<Template>): boolean {
    const existing = this.templates.get(id)
    if (!existing) {
      return false
    }
    
    const updated: Template = {
      ...existing,
      ...updates,
      metadata: {
        ...existing.metadata,
        ...updates.metadata,
        updatedAt: new Date()
      }
    }
    
    if (this.options.validateOnSave && updates.config) {
      updated.validation = TemplateConfigUtils.validateTemplate(updated)
      if (!updated.validation.isValid) {
        throw new Error(`模板验证失败: ${updated.validation.errors.join(', ')}`)
      }
    }
    
    this.templates.set(id, updated)
    
    if (this.options.autoSave) {
      this.saveToStorage()
    }
    
    return true
  }
  
  /**
   * 删除模板
   */
  deleteTemplate(id: string): boolean {
    const deleted = this.templates.delete(id)
    
    if (deleted && this.options.autoSave) {
      this.saveToStorage()
    }
    
    return deleted
  }
  
  /**
   * 复制模板
   */
  cloneTemplate(id: string, newName?: string): string | undefined {
    const original = this.templates.get(id)
    if (!original) {
      return undefined
    }
    
    const clonedConfig = JSON.parse(JSON.stringify(original.config))
    if (newName) {
      clonedConfig.name = newName
    }
    
    return this.createTemplate(clonedConfig, {
      ...original.metadata,
      name: newName || `${original.metadata.name} (副本)`,
      author: 'User'
    })
  }
  
  /**
   * 搜索和过滤模板
   */
  searchTemplates(filter?: TemplateFilter, sort?: TemplateSortOptions): Template[] {
    let results = this.getAllTemplates()
    
    // 应用过滤条件
    if (filter) {
      results = results.filter(template => {
        if (filter.category && template.metadata.category !== filter.category) {
          return false
        }
        
        if (filter.tags && filter.tags.length > 0) {
          const hasMatchingTag = filter.tags.some(tag => 
            template.metadata.tags.includes(tag)
          )
          if (!hasMatchingTag) {
            return false
          }
        }
        
        if (filter.author && template.metadata.author !== filter.author) {
          return false
        }
        
        if (filter.minRating && template.metadata.rating < filter.minRating) {
          return false
        }
        
        if (filter.maxSize && template.metadata.size > filter.maxSize) {
          return false
        }
        
        if (filter.searchTerm) {
          const searchLower = filter.searchTerm.toLowerCase()
          const matchesName = template.metadata.name.toLowerCase().includes(searchLower)
          const matchesDesc = template.metadata.description.toLowerCase().includes(searchLower)
          const matchesTags = template.metadata.tags.some(tag => 
            tag.toLowerCase().includes(searchLower)
          )
          
          if (!matchesName && !matchesDesc && !matchesTags) {
            return false
          }
        }
        
        return true
      })
    }
    
    // 应用排序
    if (sort) {
      results.sort((a, b) => {
        let valueA: any
        let valueB: any
        
        switch (sort.field) {
          case 'name':
            valueA = a.metadata.name
            valueB = b.metadata.name
            break
          case 'createdAt':
            valueA = a.metadata.createdAt
            valueB = b.metadata.createdAt
            break
          case 'updatedAt':
            valueA = a.metadata.updatedAt
            valueB = b.metadata.updatedAt
            break
          case 'rating':
            valueA = a.metadata.rating
            valueB = b.metadata.rating
            break
          case 'downloads':
            valueA = a.metadata.downloads
            valueB = b.metadata.downloads
            break
          default:
            return 0
        }
        
        if (typeof valueA === 'string') {
          valueA = valueA.toLowerCase()
          valueB = valueB.toLowerCase()
        }
        
        const comparison = valueA < valueB ? -1 : valueA > valueB ? 1 : 0
        return sort.order === 'desc' ? -comparison : comparison
      })
    }
    
    return results
  }
  
  /**
   * 获取模板市场数据
   */
  getMarketplace(): TemplateMarketplace {
    const allTemplates = this.getAllTemplates()
    
    // 按分类分组
    const categories: Record<TemplateCategory, Template[]> = {
      business: [],
      education: [],
      entertainment: [],
      marketing: [],
      tutorial: [],
      presentation: [],
      documentary: [],
      social: [],
      news: [],
      gaming: [],
      medical: [],
      legal: [],
      finance: [],
      technology: [],
      other: []
    }
    
    for (const template of allTemplates) {
      categories[template.metadata.category].push(template)
    }
    
    return {
      featured: allTemplates
        .filter(t => t.metadata.rating >= 4.5)
        .sort((a, b) => b.metadata.rating - a.metadata.rating)
        .slice(0, 6),
      popular: allTemplates
        .sort((a, b) => b.metadata.downloads - a.metadata.downloads)
        .slice(0, 10),
      recent: allTemplates
        .sort((a, b) => b.metadata.updatedAt.getTime() - a.metadata.updatedAt.getTime())
        .slice(0, 8),
      categories,
      userTemplates: allTemplates.filter(t => t.metadata.author === 'User')
    }
  }
  
  /**
   * 导入模板
   */
  async importTemplate(data: string | File): Promise<TemplateImportResult> {
    try {
      let templateData: any
      
      if (typeof data === 'string') {
        templateData = JSON.parse(data)
      }
      else {
        // 处理文件上传
        const text = await this.readFile(data)
        templateData = JSON.parse(text)
      }
      
      // 验证模板格式
      if (!this.isValidTemplateFormat(templateData)) {
        return {
          success: false,
          errors: ['无效的模板格式'],
          warnings: []
        }
      }
      
      // 创建模板
      const template: Template = {
        metadata: {
          ...templateData.metadata,
          id: this.generateId(), // 生成新ID避免冲突
          createdAt: new Date(),
          updatedAt: new Date(),
          downloads: 0,
          author: 'Imported'
        },
        config: templateData.config,
        preview: templateData.preview
      }
      
      // 验证模板
      const validation = TemplateConfigUtils.validateTemplate(template)
      template.validation = validation
      
      if (!validation.isValid) {
        return {
          success: false,
          errors: validation.errors,
          warnings: validation.warnings
        }
      }
      
      // 添加到模板库
      this.templates.set(template.metadata.id, template)
      
      if (this.options.autoSave) {
        this.saveToStorage()
      }
      
      return {
        success: true,
        template,
        errors: [],
        warnings: validation.warnings
      }
    }
    catch (error) {
      return {
        success: false,
        errors: [`导入失败: ${error instanceof Error ? error.message : '未知错误'}`],
        warnings: []
      }
    }
  }
  
  /**
   * 导出模板
   */
  exportTemplate(id: string, options: TemplateExportOptions = {}): string | undefined {
    const template = this.templates.get(id)
    if (!template) {
      return undefined
    }
    
    const exportData: any = {
      metadata: options.includeMetadata !== false ? template.metadata : undefined,
      config: template.config
    }
    
    if (options.includePreview && template.preview) {
      exportData.preview = template.preview
    }
    
    return JSON.stringify(exportData, null, 2)
  }
  
  /**
   * 验证模板
   */
  validateTemplate(id: string): TemplateValidation | undefined {
    const template = this.templates.get(id)
    if (!template) {
      return undefined
    }
    
    return TemplateConfigUtils.validateTemplate(template)
  }
  
  /**
   * 合并模板配置
   */
  mergeTemplateConfigs(baseId: string, overrideConfig: Partial<TemplateConfig>): TemplateConfig | undefined {
    const baseTemplate = this.templates.get(baseId)
    if (!baseTemplate) {
      return undefined
    }
    
    return TemplateConfigUtils.mergeConfigs(baseTemplate.config, overrideConfig)
  }
  
  /**
   * 获取模板统计信息
   */
  getStatistics() {
    const templates = this.getAllTemplates()
    const categories: Record<string, number> = {}
    
    for (const template of templates) {
      categories[template.metadata.category] = (categories[template.metadata.category] || 0) + 1
    }
    
    return {
      total: templates.length,
      categories,
      averageRating: templates.reduce((sum, t) => sum + t.metadata.rating, 0) / templates.length,
      totalDownloads: templates.reduce((sum, t) => sum + t.metadata.downloads, 0),
      userTemplates: templates.filter(t => t.metadata.author === 'User').length,
      recentlyUpdated: templates.filter(t => {
        const dayAgo = new Date()
        dayAgo.setDate(dayAgo.getDate() - 1)
        return t.metadata.updatedAt > dayAgo
      }).length
    }
  }
  
  /**
   * 保存到本地存储
   */
  private saveToStorage(): void {
    if (!this.options.storageKey) return
    
    try {
      const userTemplates = this.getAllTemplates().filter(t => t.metadata.author === 'User' || t.metadata.author === 'Imported')
      localStorage.setItem(this.options.storageKey, JSON.stringify(userTemplates))
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('Failed to save templates to storage:', error)
    }
  }
  
  /**
   * 从本地存储加载
   */
  private loadFromStorage(): void {
    if (!this.options.storageKey) return
    
    try {
      const stored = localStorage.getItem(this.options.storageKey)
      if (stored) {
        const userTemplates: Template[] = JSON.parse(stored)
        for (const template of userTemplates) {
          this.templates.set(template.metadata.id, template)
        }
      }
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('Failed to load templates from storage:', error)
    }
  }
  
  /**
   * 生成唯一ID
   */
  private generateId(): string {
    return `template-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
  
  /**
   * 计算模板大小
   */
  private calculateSize(config: TemplateConfig): number {
    return JSON.stringify(config).length
  }
  
  /**
   * 读取文件内容
   */
  private readFile(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(reader.error)
      reader.readAsText(file)
    })
  }
  
  /**
   * 验证模板格式
   */
  private isValidTemplateFormat(data: any): boolean {
    return (
      data &&
      typeof data === 'object' &&
      data.metadata &&
      data.config &&
      typeof data.metadata.name === 'string' &&
      typeof data.config === 'object'
    )
  }
  
  /**
   * 清理缓存
   */
  private cleanupCache(): void {
    if (this.cache.size > (this.options.maxCacheSize || 100)) {
      const keys = Array.from(this.cache.keys())
      const keysToDelete = keys.slice(0, keys.length - (this.options.maxCacheSize || 100))
      for (const key of keysToDelete) {
        this.cache.delete(key)
      }
    }
  }
}

/**
 * 全局模板管理器实例
 */
export const templateManager = new TemplateManager()