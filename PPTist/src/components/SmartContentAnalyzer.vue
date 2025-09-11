<!--
任务4.2: 智能内容分析系统 - Vue.js前端组件
智能内容分析界面，支持内容分析、布局推荐、配色建议

功能特性:
1. 内容结构分析展示
2. 关键概念提取展示
3. 布局推荐可视化
4. 配色方案预览
5. 分析结果导出
6. 实时分析进度

Author: Assistant
Date: 2025-09-09
Version: 1.0.0
-->

<template>
  <div class="smart-content-analyzer">
    <!-- 页面标题 -->
    <div class="analyzer-header">
      <h2 class="title">
        <i class="icon brain"></i>
        智能内容分析系统
      </h2>
      <p class="subtitle">基于AI的PPT内容结构分析和优化建议</p>
    </div>

    <!-- 分析控制面板 -->
    <div class="analysis-control">
      <div class="upload-section">
        <h3>PPT数据输入</h3>
        <div class="upload-area" @click="selectFile" :class="{ 'has-file': hasFile }">
          <div v-if="!hasFile" class="upload-placeholder">
            <i class="icon upload"></i>
            <p>点击选择PPT文件或拖拽PPT数据</p>
            <small>支持.pptx文件或JSON数据</small>
          </div>
          <div v-else class="file-info">
            <i class="icon file"></i>
            <div class="file-details">
              <p class="file-name">{{ fileName }}</p>
              <p class="file-size">{{ fileSize }}</p>
            </div>
            <button @click.stop="removeFile" class="remove-btn">
              <i class="icon close"></i>
            </button>
          </div>
        </div>
        <input 
          ref="fileInput" 
          type="file" 
          @change="handleFileSelect" 
          accept=".pptx,.json"
          style="display: none"
        >
      </div>

      <div class="analysis-options">
        <h3>分析选项</h3>
        <div class="options-grid">
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="analysisConfig.enableStructureAnalysis"
            >
            <span class="checkmark"></span>
            <div class="option-content">
              <span class="option-title">结构分析</span>
              <span class="option-desc">分析内容层次和逻辑关系</span>
            </div>
          </label>

          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="analysisConfig.enableLayoutRecommendation"
            >
            <span class="checkmark"></span>
            <div class="option-content">
              <span class="option-title">布局推荐</span>
              <span class="option-desc">自动推荐最佳布局方案</span>
            </div>
          </label>

          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="analysisConfig.enableColorRecommendation"
            >
            <span class="checkmark"></span>
            <div class="option-content">
              <span class="option-title">配色建议</span>
              <span class="option-desc">基于内容特征推荐配色</span>
            </div>
          </label>

          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="analysisConfig.enableKeywordExtraction"
            >
            <span class="checkmark"></span>
            <div class="option-content">
              <span class="option-title">关键词提取</span>
              <span class="option-desc">提取核心概念和关键词</span>
            </div>
          </label>
        </div>
      </div>

      <div class="action-buttons">
        <button 
          @click="startAnalysis" 
          :disabled="!canStartAnalysis"
          class="btn btn-primary"
        >
          <i class="icon" :class="isAnalyzing ? 'loading' : 'play'"></i>
          {{ isAnalyzing ? '分析中...' : '开始分析' }}
        </button>

        <button 
          @click="resetAnalysis" 
          :disabled="isAnalyzing"
          class="btn btn-secondary"
        >
          <i class="icon reset"></i>
          重置
        </button>
      </div>
    </div>

    <!-- 分析进度 -->
    <div v-if="isAnalyzing" class="analysis-progress">
      <div class="progress-header">
        <h3>分析进度</h3>
        <span class="progress-text">{{ Math.round(analysisProgress) }}%</span>
      </div>
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: analysisProgress + '%' }"
        ></div>
      </div>
      <p class="progress-status">{{ progressStatus }}</p>
    </div>

    <!-- 分析结果展示 -->
    <div v-if="analysisResults" class="analysis-results">
      
      <!-- 结果概览 -->
      <div class="results-summary">
        <h3>分析概览</h3>
        <div class="summary-grid">
          <div class="summary-item">
            <div class="summary-value">{{ analysisResults.summary?.content_elements_count || 0 }}</div>
            <div class="summary-label">内容元素</div>
          </div>
          <div class="summary-item">
            <div class="summary-value">{{ analysisResults.summary?.key_concepts?.length || 0 }}</div>
            <div class="summary-label">关键概念</div>
          </div>
          <div class="summary-item">
            <div class="summary-value">{{ analysisResults.layout_recommendations?.length || 0 }}</div>
            <div class="summary-label">布局建议</div>
          </div>
          <div class="summary-item">
            <div class="summary-value">{{ analysisResults.color_recommendations?.length || 0 }}</div>
            <div class="summary-label">配色方案</div>
          </div>
        </div>
      </div>

      <!-- 内容结构分析 -->
      <div v-if="analysisResults.structure" class="structure-analysis">
        <h3>内容结构分析</h3>
        
        <div class="structure-section">
          <h4>幻灯片层次</h4>
          <div class="hierarchy-chart">
            <div 
              v-for="(level, slideIndex) in analysisResults.structure.slide_hierarchy" 
              :key="slideIndex"
              class="hierarchy-item"
              :class="`level-${level}`"
            >
              <span class="slide-number">幻灯片 {{ parseInt(slideIndex) + 1 }}</span>
              <span class="level-indicator">层次 {{ level }}</span>
            </div>
          </div>
        </div>

        <div class="structure-section">
          <h4>关键概念</h4>
          <div class="concepts-cloud">
            <span 
              v-for="(concept, index) in analysisResults.structure.key_concepts" 
              :key="concept"
              class="concept-tag"
              :class="`priority-${Math.min(3, Math.floor(index / 3) + 1)}`"
            >
              {{ concept }}
            </span>
          </div>
        </div>

        <div class="structure-section">
          <h4>逻辑关系</h4>
          <div class="logical-flow">
            <div 
              v-for="(relation, index) in analysisResults.structure.logical_flow" 
              :key="index"
              class="relation-item"
              :class="`relation-${relation}`"
            >
              {{ getRelationLabel(relation) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 布局推荐 -->
      <div v-if="analysisResults.layout_recommendations?.length" class="layout-recommendations">
        <h3>布局推荐</h3>
        <div class="recommendations-grid">
          <div 
            v-for="recommendation in analysisResults.layout_recommendations" 
            :key="`layout-${recommendation.slide_index}`"
            class="recommendation-card"
          >
            <div class="card-header">
              <h4>幻灯片 {{ recommendation.slide_index + 1 }}</h4>
              <div class="confidence-badge" :class="getConfidenceClass(recommendation.confidence)">
                {{ Math.round(recommendation.confidence * 100) }}%
              </div>
            </div>
            
            <div class="layout-preview">
              <div class="layout-icon" :class="`layout-${recommendation.recommended_layout}`">
                <i class="icon" :class="getLayoutIcon(recommendation.recommended_layout)"></i>
              </div>
              <div class="layout-name">{{ getLayoutName(recommendation.recommended_layout) }}</div>
            </div>
            
            <div class="recommendation-details">
              <p class="reasoning">{{ recommendation.reasoning }}</p>
              <div v-if="recommendation.adjustments?.length" class="adjustments">
                <h5>调整建议:</h5>
                <ul>
                  <li v-for="adjustment in recommendation.adjustments" :key="adjustment">
                    {{ adjustment }}
                  </li>
                </ul>
              </div>
            </div>
            
            <div class="card-actions">
              <button @click="applyLayoutRecommendation(recommendation)" class="btn btn-sm btn-primary">
                应用布局
              </button>
              <button @click="previewLayout(recommendation)" class="btn btn-sm btn-secondary">
                预览效果
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 配色推荐 -->
      <div v-if="analysisResults.color_recommendations?.length" class="color-recommendations">
        <h3>配色推荐</h3>
        <div class="color-schemes">
          <div 
            v-for="(scheme, index) in analysisResults.color_recommendations" 
            :key="`color-${index}`"
            class="color-scheme-card"
          >
            <div class="scheme-header">
              <h4>{{ getThemeName(scheme.theme) }}</h4>
              <div class="confidence-badge" :class="getConfidenceClass(scheme.confidence)">
                {{ Math.round(scheme.confidence * 100) }}%
              </div>
            </div>
            
            <div class="color-palette">
              <div class="color-item primary" :style="{ backgroundColor: scheme.primary_color }">
                <span class="color-label">主色</span>
                <span class="color-value">{{ scheme.primary_color }}</span>
              </div>
              
              <div class="color-item secondary" :style="{ backgroundColor: scheme.secondary_color }">
                <span class="color-label">辅助色</span>
                <span class="color-value">{{ scheme.secondary_color }}</span>
              </div>
              
              <div class="color-item accent" :style="{ backgroundColor: scheme.accent_color }">
                <span class="color-label">强调色</span>
                <span class="color-value">{{ scheme.accent_color }}</span>
              </div>
              
              <div class="color-item background" :style="{ backgroundColor: scheme.background_color }">
                <span class="color-label">背景色</span>
                <span class="color-value">{{ scheme.background_color }}</span>
              </div>
              
              <div class="color-item text" :style="{ backgroundColor: scheme.text_color }">
                <span class="color-label">文字色</span>
                <span class="color-value">{{ scheme.text_color }}</span>
              </div>
            </div>
            
            <div class="scheme-details">
              <p class="reasoning">{{ scheme.reasoning }}</p>
            </div>
            
            <div class="scheme-preview">
              <div class="preview-sample" :style="getPreviewStyle(scheme)">
                <h5 :style="{ color: scheme.text_color }">示例标题</h5>
                <p :style="{ color: scheme.text_color }">这是使用推荐配色方案的示例文本内容。</p>
                <button 
                  class="preview-btn" 
                  :style="{ 
                    backgroundColor: scheme.accent_color, 
                    color: scheme.background_color 
                  }"
                >
                  示例按钮
                </button>
              </div>
            </div>
            
            <div class="card-actions">
              <button @click="applyColorScheme(scheme)" class="btn btn-sm btn-primary">
                应用配色
              </button>
              <button @click="exportColorScheme(scheme)" class="btn btn-sm btn-secondary">
                导出配色
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 结果导出 -->
      <div class="results-export">
        <h3>导出分析结果</h3>
        <div class="export-options">
          <button @click="exportAsJSON" class="btn btn-secondary">
            <i class="icon download"></i>
            导出为JSON
          </button>
          <button @click="exportAsReport" class="btn btn-secondary">
            <i class="icon file-text"></i>
            生成分析报告
          </button>
          <button @click="exportRecommendations" class="btn btn-secondary">
            <i class="icon star"></i>
            导出推荐方案
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!isAnalyzing && !analysisResults" class="empty-state">
      <div class="empty-icon">
        <i class="icon brain"></i>
      </div>
      <h3>开始智能内容分析</h3>
      <p>上传PPT文件或输入数据，让AI为您分析内容结构并提供优化建议</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SmartContentAnalyzer',
  
  data() {
    return {
      // 文件相关
      hasFile: false,
      fileName: '',
      fileSize: '',
      fileData: null,
      
      // 分析配置
      analysisConfig: {
        enableStructureAnalysis: true,
        enableLayoutRecommendation: true,
        enableColorRecommendation: true,
        enableKeywordExtraction: true
      },
      
      // 分析状态
      isAnalyzing: false,
      analysisProgress: 0,
      progressStatus: '',
      taskId: null,
      
      // 分析结果
      analysisResults: null,
      
      // 轮询定时器
      progressTimer: null
    }
  },
  
  computed: {
    canStartAnalysis() {
      return this.hasFile && !this.isAnalyzing && 
             Object.values(this.analysisConfig).some(v => v)
    }
  },
  
  methods: {
    // 文件处理
    selectFile() {
      this.$refs.fileInput.click()
    },
    
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (!file) return
      
      this.fileName = file.name
      this.fileSize = this.formatFileSize(file.size)
      this.hasFile = true
      
      // 处理文件数据
      this.processFile(file)
    },
    
    async processFile(file) {
      try {
        if (file.name.endsWith('.json')) {
          // JSON文件直接读取
          const text = await this.readFileAsText(file)
          this.fileData = JSON.parse(text)
        }
        else if (file.name.endsWith('.pptx')) {
          // PPTX文件需要转换（这里简化处理）
          this.fileData = {
            slides: [
              {
                elements: [
                  { text: '示例标题', style: { fontSize: 24 } },
                  { text: '示例内容：这是一个演示用的PPT内容分析', style: { fontSize: 14 } }
                ]
              }
            ]
          }
        }
      }
      catch (error) {
        // console.error('文件处理失败:', error)
        this.$message.error('文件格式不支持或内容有误')
        this.removeFile()
      }
    },
    
    readFileAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = e => resolve(e.target.result)
        reader.onerror = reject
        reader.readAsText(file)
      })
    },
    
    removeFile() {
      this.hasFile = false
      this.fileName = ''
      this.fileSize = ''
      this.fileData = null
      this.$refs.fileInput.value = ''
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    // 分析控制
    async startAnalysis() {
      if (!this.canStartAnalysis) return
      
      this.isAnalyzing = true
      this.analysisProgress = 0
      this.progressStatus = '准备分析...'
      this.analysisResults = null
      
      try {
        // 启动分析任务
        const response = await axios.post('/api/content/analyze', {
          ppt_data: this.fileData
        })
        
        if (response.data.success) {
          this.taskId = response.data.task_id
          this.progressStatus = '分析任务已启动'
          
          // 开始轮询进度
          this.startProgressPolling()
        }
        else {
          throw new Error(response.data.error || '启动分析失败')
        }
        
      }
      catch (error) {
        // console.error('启动分析失败:', error)
        this.$message.error('分析启动失败: ' + error.message)
        this.isAnalyzing = false
      }
    },
    
    startProgressPolling() {
      this.progressTimer = setInterval(async () => {
        try {
          await this.checkProgress()
        }
        catch (error) {
          // console.error('检查进度失败:', error)
          this.stopProgressPolling()
          this.isAnalyzing = false
          this.$message.error('检查分析进度失败')
        }
      }, 1000)
    },
    
    stopProgressPolling() {
      if (this.progressTimer) {
        clearInterval(this.progressTimer)
        this.progressTimer = null
      }
    },
    
    async checkProgress() {
      const response = await axios.get(`/api/content/structure/${this.taskId}`)
      
      if (response.data.success) {
        if (response.data.status === 'processing') {
          this.analysisProgress = response.data.progress || 0
          this.progressStatus = '正在分析内容结构...'
          
        }
        else if (response.data.status === 'completed') {
          this.analysisProgress = 100
          this.progressStatus = '分析完成'
          this.stopProgressPolling()
          
          // 获取完整结果
          await this.loadAnalysisResults()
          
        }
        else if (response.data.status === 'failed') {
          this.stopProgressPolling()
          this.isAnalyzing = false
          this.$message.error('分析失败: ' + response.data.error)
        }
      }
    },
    
    async loadAnalysisResults() {
      try {
        // 获取结构分析结果
        const structureRes = await axios.get(`/api/content/structure/${this.taskId}`)
        
        // 获取布局推荐
        const layoutRes = await axios.post('/api/content/layout-recommendations', {
          task_id: this.taskId
        })
        
        // 获取配色推荐
        const colorRes = await axios.post('/api/content/color-recommendations', {
          task_id: this.taskId
        })
        
        // 获取分析摘要
        const summaryRes = await axios.get(`/api/content/summary/${this.taskId}`)
        
        this.analysisResults = {
          structure: structureRes.data.data,
          layout_recommendations: layoutRes.data.data?.recommendations || [],
          color_recommendations: colorRes.data.data?.recommendations || [],
          summary: summaryRes.data.data?.summary || {}
        }
        
        this.isAnalyzing = false
        this.$message.success('内容分析完成')
        
      }
      catch (error) {
        // console.error('加载分析结果失败:', error)
        this.$message.error('获取分析结果失败')
        this.isAnalyzing = false
      }
    },
    
    resetAnalysis() {
      this.isAnalyzing = false
      this.analysisProgress = 0
      this.progressStatus = ''
      this.analysisResults = null
      this.taskId = null
      this.stopProgressPolling()
    },
    
    // 辅助方法
    getRelationLabel(relation) {
      const labels = {
        sequence: '顺序关系',
        hierarchy: '层次关系',
        comparison: '对比关系',
        causation: '因果关系',
        elaboration: '阐述关系',
        summary: '总结关系'
      }
      return labels[relation] || relation
    },
    
    getConfidenceClass(confidence) {
      if (confidence >= 0.8) return 'high'
      if (confidence >= 0.6) return 'medium'
      return 'low'
    },
    
    getLayoutIcon(layout) {
      const icons = {
        centered: 'align-center',
        left_aligned: 'align-left',
        right_aligned: 'align-right',
        grid_layout: 'grid',
        hierarchical: 'sitemap',
        flow_layout: 'flow'
      }
      return icons[layout] || 'layout'
    },
    
    getLayoutName(layout) {
      const names = {
        centered: '居中布局',
        left_aligned: '左对齐布局',
        right_aligned: '右对齐布局',
        grid_layout: '网格布局',
        hierarchical: '层次布局',
        flow_layout: '流式布局'
      }
      return names[layout] || layout
    },
    
    getThemeName(theme) {
      const names = {
        professional: '商务专业',
        creative: '创意活泼',
        academic: '学术严谨',
        tech: '科技现代',
        warm: '温暖亲和',
        cool: '冷静理性'
      }
      return names[theme] || theme
    },
    
    getPreviewStyle(scheme) {
      return {
        backgroundColor: scheme.background_color,
        color: scheme.text_color,
        padding: '16px',
        borderRadius: '8px',
        border: `2px solid ${scheme.secondary_color}`
      }
    },
    
    // 推荐应用
    applyLayoutRecommendation(recommendation) {
      this.$emit('apply-layout', recommendation)
      this.$message.success(`已应用${this.getLayoutName(recommendation.recommended_layout)}`)
    },
    
    previewLayout(recommendation) {
      this.$emit('preview-layout', recommendation)
    },
    
    applyColorScheme(scheme) {
      this.$emit('apply-colors', scheme)
      this.$message.success(`已应用${this.getThemeName(scheme.theme)}配色`)
    },
    
    exportColorScheme(scheme) {
      const css = this.generateCSSFromScheme(scheme)
      this.downloadFile(`${scheme.theme}-colors.css`, css)
    },
    
    generateCSSFromScheme(scheme) {
      return `
/* ${this.getThemeName(scheme.theme)}配色方案 */
:root {
  --primary-color: ${scheme.primary_color};
  --secondary-color: ${scheme.secondary_color};
  --accent-color: ${scheme.accent_color};
  --background-color: ${scheme.background_color};
  --text-color: ${scheme.text_color};
}
      `.trim()
    },
    
    // 结果导出
    exportAsJSON() {
      const data = JSON.stringify(this.analysisResults, null, 2)
      this.downloadFile('content-analysis-results.json', data)
    },
    
    exportAsReport() {
      const report = this.generateAnalysisReport()
      this.downloadFile('content-analysis-report.md', report)
    },
    
    exportRecommendations() {
      const recommendations = {
        layout_recommendations: this.analysisResults.layout_recommendations,
        color_recommendations: this.analysisResults.color_recommendations
      }
      const data = JSON.stringify(recommendations, null, 2)
      this.downloadFile('recommendations.json', data)
    },
    
    generateAnalysisReport() {
      const results = this.analysisResults
      return `
# PPT内容分析报告

## 分析概览
- 内容元素数量: ${results.summary?.content_elements_count || 0}
- 关键概念数量: ${results.summary?.key_concepts?.length || 0}
- 布局建议数量: ${results.layout_recommendations?.length || 0}
- 配色方案数量: ${results.color_recommendations?.length || 0}

## 关键概念
${results.structure?.key_concepts?.map(concept => `- ${concept}`).join('\n') || '无'}

## 布局推荐
${results.layout_recommendations?.map(rec => 
    `### 幻灯片 ${rec.slide_index + 1}
- 推荐布局: ${this.getLayoutName(rec.recommended_layout)}
- 置信度: ${Math.round(rec.confidence * 100)}%
- 理由: ${rec.reasoning}
`).join('\n') || '无布局推荐'}

## 配色建议
${results.color_recommendations?.map(scheme => 
    `### ${this.getThemeName(scheme.theme)}
- 主色调: ${scheme.primary_color}
- 辅助色: ${scheme.secondary_color}
- 强调色: ${scheme.accent_color}
- 理由: ${scheme.reasoning}
`).join('\n') || '无配色建议'}
      `.trim()
    },
    
    downloadFile(filename, content) {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  },
  
  beforeUnmount() {
    this.stopProgressPolling()
  }
}
</script>

<style scoped>
/* 这里会引用外部CSS文件 */
@import './SmartContentAnalyzer.css';
</style>
