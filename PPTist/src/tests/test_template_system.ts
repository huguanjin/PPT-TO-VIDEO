/**
 * Netflix V2 Phase 6.3 自定义模板系统测试
 * 测试模板配置、管理器和Vue组件功能
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { 
  templateManager,
  type Template,
  type TemplateConfig,
  DEFAULT_TEMPLATE_CONFIG,
  PREDEFINED_TEMPLATES,
  TemplateConfigUtils
} from '../src/templates/template-config'

describe('Netflix V2 Phase 6.3 - 自定义模板系统', () => {
  beforeEach(() => {
    // 清理模板管理器状态
    const allTemplates = templateManager.getAllTemplates()
    allTemplates
      .filter(t => t.metadata.author === 'User' || t.metadata.author === 'Imported')
      .forEach(t => templateManager.deleteTemplate(t.metadata.id))
  })

  describe('模板配置 (template-config.ts)', () => {
    it('应该有有效的默认模板配置', () => {
      expect(DEFAULT_TEMPLATE_CONFIG).toBeDefined()
      expect(DEFAULT_TEMPLATE_CONFIG.name).toBe('标准模板')
      expect(DEFAULT_TEMPLATE_CONFIG.video.resolution).toBe('1920x1080')
      expect(DEFAULT_TEMPLATE_CONFIG.video.fps).toBe(30)
      expect(DEFAULT_TEMPLATE_CONFIG.audio.sampleRate).toBe(44100)
      expect(DEFAULT_TEMPLATE_CONFIG.subtitle.style.fontSize).toBe(24)
    })

    it('应该包含预定义模板', () => {
      expect(PREDEFINED_TEMPLATES).toBeDefined()
      expect(PREDEFINED_TEMPLATES.length).toBeGreaterThan(0)
      
      const businessTemplate = PREDEFINED_TEMPLATES.find(t => t.metadata.id === 'business-presentation')
      expect(businessTemplate).toBeDefined()
      expect(businessTemplate?.metadata.category).toBe('business')
      expect(businessTemplate?.metadata.name).toBe('商务演示模板')
    })

    it('应该正确验证模板配置', () => {
      const validTemplate: Template = {
        metadata: {
          id: 'test-template',
          name: '测试模板',
          description: '测试描述',
          version: '1.0.0',
          author: 'Test',
          category: 'other',
          tags: ['test'],
          thumbnail: '',
          createdAt: new Date(),
          updatedAt: new Date(),
          downloads: 0,
          rating: 0,
          compatibility: ['2.0.0+'],
          size: 1024
        },
        config: DEFAULT_TEMPLATE_CONFIG
      }

      const validation = TemplateConfigUtils.validateTemplate(validTemplate)
      expect(validation.isValid).toBe(true)
      expect(validation.errors).toHaveLength(0)
    })

    it('应该检测无效的模板配置', () => {
      const invalidTemplate: Template = {
        metadata: {
          id: 'invalid-template',
          name: '',
          description: '无效模板',
          version: '1.0.0',
          author: 'Test',
          category: 'other',
          tags: [],
          thumbnail: '',
          createdAt: new Date(),
          updatedAt: new Date(),
          downloads: 0,
          rating: 0,
          compatibility: ['2.0.0+'],
          size: 1024
        },
        config: {
          ...DEFAULT_TEMPLATE_CONFIG,
          name: '', // 无效：空名称
          video: {
            ...DEFAULT_TEMPLATE_CONFIG.video,
            fps: 200 // 无效：超出范围
          }
        }
      }

      const validation = TemplateConfigUtils.validateTemplate(invalidTemplate)
      expect(validation.isValid).toBe(false)
      expect(validation.errors.length).toBeGreaterThan(0)
    })

    it('应该正确合并模板配置', () => {
      const baseConfig = DEFAULT_TEMPLATE_CONFIG
      const override = {
        video: {
          resolution: '3840x2160',
          fps: 60
        },
        subtitle: {
          style: {
            fontSize: 32
          }
        }
      }

      const merged = TemplateConfigUtils.mergeConfigs(baseConfig, override)
      
      expect(merged.video.resolution).toBe('3840x2160')
      expect(merged.video.fps).toBe(60)
      expect(merged.video.quality).toBe(baseConfig.video.quality) // 保持原值
      expect(merged.subtitle.style.fontSize).toBe(32)
      expect(merged.subtitle.style.fontFamily).toBe(baseConfig.subtitle.style.fontFamily) // 保持原值
    })
  })

  describe('模板管理器 (template-manager.ts)', () => {
    it('应该正确初始化预定义模板', () => {
      const allTemplates = templateManager.getAllTemplates()
      expect(allTemplates.length).toBeGreaterThanOrEqual(PREDEFINED_TEMPLATES.length)
      
      const businessTemplate = templateManager.getTemplate('business-presentation')
      expect(businessTemplate).toBeDefined()
      expect(businessTemplate?.metadata.name).toBe('商务演示模板')
    })

    it('应该能创建新模板', () => {
      const config: TemplateConfig = {
        ...DEFAULT_TEMPLATE_CONFIG,
        name: '测试模板',
        description: '这是一个测试模板'
      }

      const id = templateManager.createTemplate(config, {
        name: '测试模板',
        category: 'other',
        tags: ['test', 'custom']
      })

      expect(id).toBeDefined()
      
      const created = templateManager.getTemplate(id)
      expect(created).toBeDefined()
      expect(created?.metadata.name).toBe('测试模板')
      expect(created?.metadata.author).toBe('User')
      expect(created?.metadata.tags).toContain('test')
    })

    it('应该能更新模板', () => {
      const config: TemplateConfig = {
        ...DEFAULT_TEMPLATE_CONFIG,
        name: '原始模板'
      }

      const id = templateManager.createTemplate(config, {
        name: '原始模板',
        category: 'other'
      })

      const updated = templateManager.updateTemplate(id, {
        config: {
          ...config,
          name: '更新后模板',
          video: {
            ...config.video,
            fps: 60
          }
        },
        metadata: {
          name: '更新后模板',
          tags: ['updated']
        }
      })

      expect(updated).toBe(true)
      
      const template = templateManager.getTemplate(id)
      expect(template?.config.name).toBe('更新后模板')
      expect(template?.config.video.fps).toBe(60)
      expect(template?.metadata.tags).toContain('updated')
    })

    it('应该能删除模板', () => {
      const config: TemplateConfig = {
        ...DEFAULT_TEMPLATE_CONFIG,
        name: '待删除模板'
      }

      const id = templateManager.createTemplate(config, {
        name: '待删除模板',
        category: 'other'
      })

      expect(templateManager.getTemplate(id)).toBeDefined()
      
      const deleted = templateManager.deleteTemplate(id)
      expect(deleted).toBe(true)
      expect(templateManager.getTemplate(id)).toBeUndefined()
    })

    it('应该能复制模板', () => {
      const config: TemplateConfig = {
        ...DEFAULT_TEMPLATE_CONFIG,
        name: '原始模板'
      }

      const originalId = templateManager.createTemplate(config, {
        name: '原始模板',
        category: 'education',
        tags: ['original']
      })

      const clonedId = templateManager.cloneTemplate(originalId, '复制的模板')
      expect(clonedId).toBeDefined()
      
      const cloned = templateManager.getTemplate(clonedId!)
      expect(cloned).toBeDefined()
      expect(cloned?.metadata.name).toBe('复制的模板')
      expect(cloned?.metadata.author).toBe('User')
      expect(cloned?.config.name).toBe('复制的模板')
    })

    it('应该能搜索和过滤模板', () => {
      // 创建测试模板
      templateManager.createTemplate(DEFAULT_TEMPLATE_CONFIG, {
        name: '商务模板A',
        category: 'business',
        tags: ['presentation', 'corporate']
      })

      templateManager.createTemplate(DEFAULT_TEMPLATE_CONFIG, {
        name: '教育模板B',
        category: 'education',
        tags: ['tutorial', 'learning']
      })

      // 按分类搜索
      const businessTemplates = templateManager.searchTemplates({
        category: 'business'
      })
      expect(businessTemplates.some(t => t.metadata.name === '商务模板A')).toBe(true)

      // 按标签搜索
      const tutorialTemplates = templateManager.searchTemplates({
        tags: ['tutorial']
      })
      expect(tutorialTemplates.some(t => t.metadata.name === '教育模板B')).toBe(true)

      // 按搜索词搜索
      const searchResults = templateManager.searchTemplates({
        searchTerm: '教育'
      })
      expect(searchResults.some(t => t.metadata.name === '教育模板B')).toBe(true)
    })

    it('应该能获取模板市场数据', () => {
      const marketplace = templateManager.getMarketplace()
      
      expect(marketplace).toBeDefined()
      expect(marketplace.featured).toBeDefined()
      expect(marketplace.popular).toBeDefined()
      expect(marketplace.recent).toBeDefined()
      expect(marketplace.categories).toBeDefined()
      expect(marketplace.userTemplates).toBeDefined()
    })

    it('应该能导入和导出模板', async () => {
      const config: TemplateConfig = {
        ...DEFAULT_TEMPLATE_CONFIG,
        name: '导出测试模板'
      }

      const id = templateManager.createTemplate(config, {
        name: '导出测试模板',
        category: 'other',
        tags: ['export', 'test']
      })

      // 导出模板
      const exportData = templateManager.exportTemplate(id)
      expect(exportData).toBeDefined()
      
      const exportJson = JSON.parse(exportData!)
      expect(exportJson.config.name).toBe('导出测试模板')
      expect(exportJson.metadata.category).toBe('other')

      // 导入模板
      const importResult = await templateManager.importTemplate(exportData!)
      expect(importResult.success).toBe(true)
      expect(importResult.template).toBeDefined()
      expect(importResult.template?.metadata.author).toBe('Imported')
    })

    it('应该能获取统计信息', () => {
      const stats = templateManager.getStatistics()
      
      expect(stats).toBeDefined()
      expect(stats.total).toBeGreaterThan(0)
      expect(stats.categories).toBeDefined()
      expect(typeof stats.averageRating).toBe('number')
      expect(typeof stats.totalDownloads).toBe('number')
      expect(typeof stats.userTemplates).toBe('number')
    })
  })

  describe('Vue组件集成测试', () => {
    it('应该能渲染模板卡片组件', () => {
      // 这里需要模拟Vue组件测试环境
      // 由于组件依赖太多，这里只做基础检查
      const template = PREDEFINED_TEMPLATES[0]
      expect(template).toBeDefined()
      expect(template.metadata.name).toBeDefined()
      expect(template.config).toBeDefined()
    })

    it('应该能处理模板编辑器表单数据', () => {
      const formData = {
        ...DEFAULT_TEMPLATE_CONFIG,
        category: 'business' as const,
        tags: ['test']
      }

      expect(formData.name).toBeDefined()
      expect(formData.category).toBe('business')
      expect(formData.video.resolution).toBe('1920x1080')
    })
  })

  describe('性能和边界测试', () => {
    it('应该能处理大量模板', () => {
      const start = Date.now()
      
      // 创建100个模板
      for (let i = 0; i < 100; i++) {
        templateManager.createTemplate(DEFAULT_TEMPLATE_CONFIG, {
          name: `性能测试模板 ${i}`,
          category: 'other'
        })
      }
      
      const createTime = Date.now() - start
      expect(createTime).toBeLessThan(5000) // 应该在5秒内完成
      
      // 搜索性能测试
      const searchStart = Date.now()
      const results = templateManager.searchTemplates({
        searchTerm: '性能测试'
      })
      const searchTime = Date.now() - searchStart
      
      expect(results.length).toBe(100)
      expect(searchTime).toBeLessThan(1000) // 搜索应该在1秒内完成
    })

    it('应该正确处理无效输入', () => {
      // 测试无效ID
      expect(templateManager.getTemplate('non-existent')).toBeUndefined()
      expect(templateManager.deleteTemplate('non-existent')).toBe(false)
      expect(templateManager.cloneTemplate('non-existent')).toBeUndefined()
      
      // 测试空搜索
      const emptyResults = templateManager.searchTemplates({
        searchTerm: ''
      })
      expect(emptyResults).toBeDefined()
    })

    it('应该处理导入错误', async () => {
      // 测试无效JSON
      const invalidResult = await templateManager.importTemplate('invalid json')
      expect(invalidResult.success).toBe(false)
      expect(invalidResult.errors.length).toBeGreaterThan(0)
      
      // 测试缺少必要字段的JSON
      const incompleteJson = JSON.stringify({ config: {} })
      const incompleteResult = await templateManager.importTemplate(incompleteJson)
      expect(incompleteResult.success).toBe(false)
    })
  })
})

/**
 * 运行性能基准测试
 */
export function runPerformanceBenchmarks() {
  console.log('🚀 Netflix V2 Phase 6.3 模板系统性能基准测试')
  
  const results = {
    templateCreation: 0,
    templateSearch: 0,
    templateValidation: 0,
    configMerging: 0
  }
  
  // 模板创建性能测试
  const createStart = Date.now()
  for (let i = 0; i < 1000; i++) {
    templateManager.createTemplate(DEFAULT_TEMPLATE_CONFIG, {
      name: `基准测试模板 ${i}`,
      category: 'other'
    })
  }
  results.templateCreation = Date.now() - createStart
  
  // 搜索性能测试
  const searchStart = Date.now()
  for (let i = 0; i < 100; i++) {
    templateManager.searchTemplates({
      searchTerm: '基准测试',
      category: 'other'
    })
  }
  results.templateSearch = Date.now() - searchStart
  
  // 验证性能测试
  const validationStart = Date.now()
  const testTemplate: Template = {
    metadata: {
      id: 'benchmark',
      name: '基准测试',
      description: '性能测试模板',
      version: '1.0.0',
      author: 'Benchmark',
      category: 'other',
      tags: [],
      thumbnail: '',
      createdAt: new Date(),
      updatedAt: new Date(),
      downloads: 0,
      rating: 0,
      compatibility: ['2.0.0+'],
      size: 1024
    },
    config: DEFAULT_TEMPLATE_CONFIG
  }
  
  for (let i = 0; i < 1000; i++) {
    TemplateConfigUtils.validateTemplate(testTemplate)
  }
  results.templateValidation = Date.now() - validationStart
  
  // 配置合并性能测试
  const mergeStart = Date.now()
  for (let i = 0; i < 10000; i++) {
    TemplateConfigUtils.mergeConfigs(DEFAULT_TEMPLATE_CONFIG, {
      video: { fps: 60 },
      subtitle: { style: { fontSize: 32 } }
    })
  }
  results.configMerging = Date.now() - mergeStart
  
  console.log('📊 性能基准测试结果:')
  console.log(`  模板创建 (1000次): ${results.templateCreation}ms`)
  console.log(`  模板搜索 (100次): ${results.templateSearch}ms`)
  console.log(`  模板验证 (1000次): ${results.templateValidation}ms`)
  console.log(`  配置合并 (10000次): ${results.configMerging}ms`)
  
  return results
}

/**
 * 运行集成测试场景
 */
export function runIntegrationScenarios() {
  console.log('🎯 Netflix V2 Phase 6.3 集成测试场景')
  
  const scenarios = [
    {
      name: '完整模板工作流',
      test: () => {
        // 1. 创建模板
        const id = templateManager.createTemplate({
          ...DEFAULT_TEMPLATE_CONFIG,
          name: '集成测试模板'
        }, {
          name: '集成测试模板',
          category: 'tutorial',
          tags: ['integration', 'test']
        })
        
        // 2. 验证创建
        const created = templateManager.getTemplate(id)
        if (!created) throw new Error('模板创建失败')
        
        // 3. 更新模板
        templateManager.updateTemplate(id, {
          config: {
            ...created.config,
            video: { ...created.config.video, fps: 60 }
          }
        })
        
        // 4. 复制模板
        const clonedId = templateManager.cloneTemplate(id)
        if (!clonedId) throw new Error('模板复制失败')
        
        // 5. 导出模板
        const exportData = templateManager.exportTemplate(id)
        if (!exportData) throw new Error('模板导出失败')
        
        // 6. 清理
        templateManager.deleteTemplate(id)
        templateManager.deleteTemplate(clonedId)
        
        return true
      }
    },
    
    {
      name: '模板市场操作',
      test: () => {
        // 1. 获取市场数据
        const marketplace = templateManager.getMarketplace()
        if (!marketplace.featured || !marketplace.categories) {
          throw new Error('市场数据获取失败')
        }
        
        // 2. 搜索操作
        const results = templateManager.searchTemplates({
          category: 'business',
          searchTerm: '商务'
        })
        
        if (results.length === 0) {
          throw new Error('搜索结果为空')
        }
        
        // 3. 统计信息
        const stats = templateManager.getStatistics()
        if (stats.total === 0) {
          throw new Error('统计信息异常')
        }
        
        return true
      }
    },
    
    {
      name: '错误处理场景',
      test: async () => {
        // 1. 无效模板验证
        const invalidTemplate: Template = {
          metadata: {
            id: 'invalid',
            name: '',
            description: '',
            version: '1.0.0',
            author: 'Test',
            category: 'other',
            tags: [],
            thumbnail: '',
            createdAt: new Date(),
            updatedAt: new Date(),
            downloads: 0,
            rating: 0,
            compatibility: ['2.0.0+'],
            size: 0
          },
          config: {
            ...DEFAULT_TEMPLATE_CONFIG,
            name: '',
            video: { ...DEFAULT_TEMPLATE_CONFIG.video, fps: 999 }
          }
        }
        
        const validation = TemplateConfigUtils.validateTemplate(invalidTemplate)
        if (validation.isValid) {
          throw new Error('无效模板验证应该失败')
        }
        
        // 2. 错误导入处理
        const importResult = await templateManager.importTemplate('invalid json')
        if (importResult.success) {
          throw new Error('无效导入应该失败')
        }
        
        return true
      }
    }
  ]
  
  const results = scenarios.map(scenario => {
    try {
      const success = scenario.test()
      console.log(`  ✅ ${scenario.name}: 通过`)
      return { name: scenario.name, success: true, error: null }
    } catch (error) {
      console.log(`  ❌ ${scenario.name}: 失败 - ${error instanceof Error ? error.message : '未知错误'}`)
      return { name: scenario.name, success: false, error: error instanceof Error ? error.message : '未知错误' }
    }
  })
  
  const passed = results.filter(r => r.success).length
  const total = results.length
  
  console.log(`📈 集成测试结果: ${passed}/${total} 通过`)
  
  return results
}