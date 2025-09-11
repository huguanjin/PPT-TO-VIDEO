/**
 * 任务3.3: 实时预览功能 - 前端Vue组件
 * 
 * 实现实时字幕预览、WYSIWYG编辑和即时质量反馈的完整前端界面
 * 与后端实时预览API无缝集成
 */

<template>
  <div class="real-time-preview-container">
    <!-- 标题栏 -->
    <div class="preview-header">
      <h2 class="preview-title">
        🎬 实时字幕预览
        <span v-if="sessionId" class="session-indicator">会话: {{ sessionId.slice(-8) }}</span>
      </h2>
      
      <div class="preview-controls">
        <button 
          @click="startPreviewSession" 
          :disabled="isSessionActive || isLoading"
          class="btn btn-primary"
        >
          <span v-if="isLoading">🔄 启动中...</span>
          <span v-else>🎬 启动预览</span>
        </button>
        
        <button 
          @click="stopPreviewSession" 
          :disabled="!isSessionActive || isLoading"
          class="btn btn-secondary"
        >
          ⏹️ 停止预览
        </button>
        
        <button 
          @click="exportSubtitles" 
          :disabled="!isSessionActive || previewItems.length === 0"
          class="btn btn-success"
        >
          💾 导出字幕
        </button>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-section" v-if="isSessionActive">
      <div class="input-header">
        <label for="text-input" class="input-label">📝 输入文本内容</label>
        <div class="input-stats">
          <span>字符数: {{ inputText.length }}</span>
          <span>预计时长: {{ estimatedDuration }}s</span>
        </div>
      </div>
      
      <textarea
        id="text-input"
        v-model="inputText"
        @input="onTextInput"
        placeholder="请输入需要生成字幕的文本内容..."
        class="text-input"
        rows="6"
      ></textarea>
      
      <div class="input-options">
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            v-model="realTimeUpdate"
          />
          <span>实时更新预览</span>
        </label>
        
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            v-model="enableQualityCheck"
          />
          <span>启用质量检查</span>
        </label>
        
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            v-model="highlightIssues"
          />
          <span>高亮显示问题</span>
        </label>
      </div>
    </div>

    <!-- 预览区域 -->
    <div class="preview-section" v-if="isSessionActive">
      <!-- 质量摘要 -->
      <div class="quality-summary" v-if="qualitySummary && enableQualityCheck">
        <div class="quality-header">
          <h3>📊 质量评估报告</h3>
          <div class="quality-score">
            总体评分: 
            <span :class="getScoreClass(qualitySummary.overall_score)">
              {{ (qualitySummary.overall_score * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
        
        <div class="quality-details">
          <div class="quality-stats">
            <div class="stat-item">
              <span class="stat-label">字幕数量:</span>
              <span class="stat-value">{{ qualitySummary.total_items || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">通过率:</span>
              <span class="stat-value">{{ ((qualitySummary.pass_rate || 0) * 100).toFixed(1) }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">问题数量:</span>
              <span class="stat-value">{{ qualitySummary.total_issues || 0 }}</span>
            </div>
          </div>
          
          <!-- 质量分布 -->
          <div class="quality-distribution" v-if="qualitySummary.quality_distribution">
            <div class="distribution-bar">
              <div 
                class="bar-segment high" 
                :style="{ width: getDistributionWidth('high') }"
                :title="`优质: ${qualitySummary.quality_distribution.high}`"
              ></div>
              <div 
                class="bar-segment medium" 
                :style="{ width: getDistributionWidth('medium') }"
                :title="`一般: ${qualitySummary.quality_distribution.medium}`"
              ></div>
              <div 
                class="bar-segment low" 
                :style="{ width: getDistributionWidth('low') }"
                :title="`待改进: ${qualitySummary.quality_distribution.low}`"
              ></div>
            </div>
          </div>
          
          <!-- 改进建议 -->
          <div class="recommendations" v-if="qualitySummary.recommendations && qualitySummary.recommendations.length > 0">
            <h4>💡 改进建议:</h4>
            <ul class="recommendation-list">
              <li v-for="(rec, index) in qualitySummary.recommendations" :key="index">
                {{ rec }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 字幕预览列表 -->
      <div class="subtitle-preview-list">
        <div class="preview-header">
          <h3>🎭 字幕预览</h3>
          <div class="preview-info">
            <span>共 {{ totalCount }} 项</span>
            <span v-if="processingStatus">状态: {{ processingStatus }}</span>
          </div>
        </div>
        
        <div class="subtitle-items" v-if="previewItems.length > 0">
          <div 
            v-for="(item, index) in previewItems" 
            :key="item.id"
            class="subtitle-item"
            :class="{
              'has-issues': item.issues && item.issues.length > 0 && highlightIssues,
              'high-quality': item.quality_score >= 0.8,
              'medium-quality': item.quality_score >= 0.6 && item.quality_score < 0.8,
              'low-quality': item.quality_score < 0.6
            }"
          >
            <!-- 字幕序号和时间 -->
            <div class="subtitle-header">
              <span class="subtitle-index">#{index + 1}</span>
              <span class="subtitle-timing">
                {{ formatTime(item.start_time) }} → {{ formatTime(item.end_time) }}
              </span>
              <span class="subtitle-duration">
                ({{ (item.end_time - item.start_time).toFixed(1) }}s)
              </span>
              <div class="subtitle-quality">
                <span class="quality-score" :class="getScoreClass(item.quality_score)">
                  {{ (item.quality_score * 100).toFixed(0) }}%
                </span>
              </div>
            </div>
            
            <!-- 字幕内容 -->
            <div class="subtitle-content">
              <div 
                v-if="editingItemId !== item.id"
                class="subtitle-text"
                @dblclick="startEditing(item.id)"
                :style="item.style"
              >
                {{ item.text }}
              </div>
              
              <div v-else class="subtitle-editor">
                <textarea 
                  v-model="editingText"
                  @blur="saveEdit"
                  @keydown.enter.ctrl="saveEdit"
                  @keydown.esc="cancelEdit"
                  class="edit-textarea"
                  rows="2"
                ></textarea>
                <div class="edit-buttons">
                  <button @click="saveEdit" class="btn btn-sm btn-success">✓ 保存</button>
                  <button @click="cancelEdit" class="btn btn-sm btn-secondary">✗ 取消</button>
                </div>
              </div>
            </div>
            
            <!-- 问题显示 -->
            <div v-if="item.issues && item.issues.length > 0 && highlightIssues" class="subtitle-issues">
              <span class="issues-label">⚠️ 问题:</span>
              <div class="issues-list">
                <span 
                  v-for="issue in item.issues" 
                  :key="issue"
                  class="issue-tag"
                >
                  {{ issue }}
                </span>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="subtitle-actions">
              <button 
                @click="startEditing(item.id)"
                class="action-btn edit-btn"
                title="编辑"
              >
                ✏️
              </button>
              
              <button 
                @click="showSplitDialog(item.id)"
                class="action-btn split-btn"
                title="分割"
              >
                ✂️
              </button>
              
              <button 
                @click="toggleSelectForMerge(item.id)"
                class="action-btn merge-btn"
                :class="{ 'selected': selectedForMerge.includes(item.id) }"
                title="选择合并"
              >
                🔗
              </button>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-preview">
          <div class="empty-icon">📝</div>
          <div class="empty-text">
            <p>暂无字幕预览</p>
            <p>请在上方输入文本开始生成字幕</p>
          </div>
        </div>
      </div>

      <!-- 操作面板 -->
      <div class="action-panel" v-if="selectedForMerge.length > 1">
        <div class="merge-info">
          已选择 {{ selectedForMerge.length }} 项进行合并
        </div>
        <div class="merge-actions">
          <button @click="mergeSelectedItems" class="btn btn-warning">
            🔗 合并选中项
          </button>
          <button @click="clearSelection" class="btn btn-secondary">
            ✗ 清除选择
          </button>
        </div>
      </div>
      
      <!-- 撤销操作 -->
      <div class="undo-panel">
        <button 
          @click="undoLastEdit"
          :disabled="!canUndo"
          class="btn btn-info"
        >
          ↶ 撤销操作
        </button>
      </div>
    </div>

    <!-- 分割对话框 -->
    <div v-if="showSplitDialogFlag" class="modal-overlay" @click="closeSplitDialog">
      <div class="modal-content" @click.stop>
        <h3>✂️ 分割字幕</h3>
        <div class="split-content">
          <div class="original-text">
            <label>原文本:</label>
            <div class="text-display">{{ splitDialogText }}</div>
          </div>
          
          <div class="split-position">
            <label>分割位置:</label>
            <input 
              type="range" 
              v-model="splitPosition" 
              :min="1" 
              :max="splitDialogText.length - 1"
              class="split-slider"
            />
            <span class="position-indicator">{{ splitPosition }}</span>
          </div>
          
          <div class="split-preview">
            <div class="split-part">
              <label>前半部分:</label>
              <div class="text-preview">{{ splitDialogText.substring(0, splitPosition) }}</div>
            </div>
            <div class="split-part">
              <label>后半部分:</label>
              <div class="text-preview">{{ splitDialogText.substring(splitPosition) }}</div>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button @click="confirmSplit" class="btn btn-primary">✓ 确认分割</button>
          <button @click="closeSplitDialog" class="btn btn-secondary">✗ 取消</button>
        </div>
      </div>
    </div>

    <!-- 导出对话框 -->
    <div v-if="showExportDialog" class="modal-overlay" @click="closeExportDialog">
      <div class="modal-content" @click.stop>
        <h3>💾 导出字幕</h3>
        <div class="export-options">
          <div class="format-selection">
            <label>选择格式:</label>
            <div class="format-buttons">
              <button 
                v-for="format in exportFormats" 
                :key="format.value"
                @click="selectedExportFormat = format.value"
                class="format-btn"
                :class="{ 'selected': selectedExportFormat === format.value }"
              >
                {{ format.label }}
              </button>
            </div>
          </div>
          
          <div class="export-preview" v-if="exportPreview">
            <label>预览:</label>
            <pre class="export-content">{{ exportPreview }}</pre>
          </div>
        </div>
        
        <div class="modal-actions">
          <button @click="confirmExport" class="btn btn-success">💾 下载文件</button>
          <button @click="closeExportDialog" class="btn btn-secondary">✗ 取消</button>
        </div>
      </div>
    </div>

    <!-- 加载指示器 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <div class="loading-text">{{ loadingMessage }}</div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message" class="message-toast" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'

export default {
  name: 'RealTimePreviewComponent',
  setup() {
    // 响应式数据
    const sessionId = ref('')
    const isSessionActive = ref(false)
    const isLoading = ref(false)
    const loadingMessage = ref('')
    
    // 文本输入
    const inputText = ref('')
    const realTimeUpdate = ref(true)
    const enableQualityCheck = ref(true)
    const highlightIssues = ref(true)
    
    // 预览数据
    const previewItems = ref([])
    const totalCount = ref(0)
    const processingStatus = ref('')
    const qualitySummary = ref(null)
    
    // 编辑状态
    const editingItemId = ref('')
    const editingText = ref('')
    const selectedForMerge = ref([])
    const canUndo = ref(false)
    
    // 分割对话框
    const showSplitDialogFlag = ref(false)
    const splitDialogItemId = ref('')
    const splitDialogText = ref('')
    const splitPosition = ref(0)
    
    // 导出对话框
    const showExportDialog = ref(false)
    const selectedExportFormat = ref('srt')
    const exportPreview = ref('')
    const exportFormats = [
      { value: 'srt', label: 'SRT' },
      { value: 'vtt', label: 'VTT' },
      { value: 'json', label: 'JSON' }
    ]
    
    // 消息提示
    const message = ref('')
    const messageType = ref('info')
    
    // 计算属性
    const estimatedDuration = computed(() => {
      return (inputText.value.length * 0.1).toFixed(1)
    })
    
    // 输入防抖
    let inputDebounceTimer = null
    
    // 方法
    const showMessage = (msg, type = 'info') => {
      message.value = msg
      messageType.value = type
      setTimeout(() => {
        message.value = ''
      }, 3000)
    }
    
    const startPreviewSession = async () => {
      try {
        isLoading.value = true
        loadingMessage.value = '正在启动预览会话...'
        
        const response = await fetch('/api/real-time-preview/start-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: `session_${Date.now()}`,
            config: {
              enable_real_time: realTimeUpdate.value,
              enable_quality_check: enableQualityCheck.value,
              highlight_issues: highlightIssues.value,
              preview_window_size: 10
            },
            initial_text: inputText.value
          })
        })
        
        const result = await response.json()
        
        if (result.status === 'success') {
          sessionId.value = result.session_id
          isSessionActive.value = true
          
          // 如果有初始预览结果
          if (result.initial_preview) {
            updatePreviewData(result.initial_preview)
          }
          
          showMessage('预览会话启动成功！', 'success')
        } else {
          showMessage(`启动失败: ${result.error}`, 'error')
        }
        
      } catch (error) {
        console.error('启动预览会话失败:', error)
        showMessage('启动预览会话失败', 'error')
      } finally {
        isLoading.value = false
      }
    }
    
    const stopPreviewSession = async () => {
      try {
        isLoading.value = true
        loadingMessage.value = '正在停止预览会话...'
        
        const response = await fetch('/api/real-time-preview/close-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId.value
          })
        })
        
        const result = await response.json()
        
        // 重置状态
        isSessionActive.value = false
        sessionId.value = ''
        previewItems.value = []
        totalCount.value = 0
        qualitySummary.value = null
        
        showMessage('预览会话已停止', 'info')
        
      } catch (error) {
        console.error('停止预览会话失败:', error)
        showMessage('停止预览会话失败', 'error')
      } finally {
        isLoading.value = false
      }
    }
    
    const onTextInput = () => {
      if (!realTimeUpdate.value || !isSessionActive.value) return
      
      // 防抖处理
      if (inputDebounceTimer) {
        clearTimeout(inputDebounceTimer)
      }
      
      inputDebounceTimer = setTimeout(async () => {
        await updatePreview()
      }, 500)
    }
    
    const updatePreview = async () => {
      if (!isSessionActive.value || !inputText.value.trim()) return
      
      try {
        const response = await fetch('/api/real-time-preview/update-preview', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId.value,
            text: inputText.value
          })
        })
        
        const result = await response.json()
        
        if (result.status === 'success') {
          updatePreviewData(result.preview_update)
        }
        
      } catch (error) {
        console.error('更新预览失败:', error)
      }
    }
    
    const updatePreviewData = (previewUpdate) => {
      previewItems.value = previewUpdate.items || []
      totalCount.value = previewUpdate.total_count || 0
      processingStatus.value = previewUpdate.processing_status || ''
      qualitySummary.value = previewUpdate.quality_summary || null
    }
    
    const startEditing = (itemId) => {
      const item = previewItems.value.find(i => i.id === itemId)
      if (item) {
        editingItemId.value = itemId
        editingText.value = item.text
      }
    }
    
    const saveEdit = async () => {
      if (!editingItemId.value || !editingText.value.trim()) return
      
      try {
        const response = await fetch('/api/real-time-preview/edit-subtitle', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId.value,
            item_id: editingItemId.value,
            new_text: editingText.value,
            auto_adjust_timing: true
          })
        })
        
        const result = await response.json()
        
        if (result.status === 'success') {
          // 更新本地数据
          const itemIndex = previewItems.value.findIndex(i => i.id === editingItemId.value)
          if (itemIndex !== -1) {
            previewItems.value[itemIndex] = result.edit_result.updated_item
          }
          
          showMessage('字幕编辑成功', 'success')
          canUndo.value = true
        } else {
          showMessage(`编辑失败: ${result.error}`, 'error')
        }
        
      } catch (error) {
        console.error('保存编辑失败:', error)
        showMessage('保存编辑失败', 'error')
      } finally {
        cancelEdit()
      }
    }
    
    const cancelEdit = () => {
      editingItemId.value = ''
      editingText.value = ''
    }
    
    const showSplitDialog = (itemId) => {
      const item = previewItems.value.find(i => i.id === itemId)
      if (item) {
        splitDialogItemId.value = itemId
        splitDialogText.value = item.text
        splitPosition.value = Math.floor(item.text.length / 2)
        showSplitDialogFlag.value = true
      }
    }
    
    const closeSplitDialog = () => {
      showSplitDialogFlag.value = false
      splitDialogItemId.value = ''
      splitDialogText.value = ''
    }
    
    const confirmSplit = async () => {
      try {
        const response = await fetch('/api/real-time-preview/split-subtitle', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId.value,
            item_id: splitDialogItemId.value,
            split_position: splitPosition.value
          })
        })
        
        const result = await response.json()
        
        if (result.status === 'success') {
          // 刷新预览
          await updatePreview()
          showMessage('字幕分割成功', 'success')
          canUndo.value = true
        } else {
          showMessage(`分割失败: ${result.error}`, 'error')
        }
        
      } catch (error) {
        console.error('分割字幕失败:', error)
        showMessage('分割字幕失败', 'error')
      } finally {
        closeSplitDialog()
      }
    }
    
    const toggleSelectForMerge = (itemId) => {
      const index = selectedForMerge.value.indexOf(itemId)
      if (index === -1) {
        selectedForMerge.value.push(itemId)
      } else {
        selectedForMerge.value.splice(index, 1)
      }
    }
    
    const mergeSelectedItems = async () => {
      if (selectedForMerge.value.length < 2) return
      
      try {
        const response = await fetch('/api/real-time-preview/merge-subtitles', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId.value,
            item_ids: selectedForMerge.value
          })
        })
        
        const result = await response.json()
        
        if (result.status === 'success') {
          // 刷新预览
          await updatePreview()
          showMessage(`成功合并 ${selectedForMerge.value.length} 个字幕`, 'success')
          selectedForMerge.value = []
          canUndo.value = true
        } else {
          showMessage(`合并失败: ${result.error}`, 'error')
        }
        
      } catch (error) {
        console.error('合并字幕失败:', error)
        showMessage('合并字幕失败', 'error')
      }
    }
    
    const clearSelection = () => {
      selectedForMerge.value = []
    }
    
    const undoLastEdit = async () => {
      try {
        const response = await fetch('/api/real-time-preview/undo-edit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId.value
          })
        })
        
        const result = await response.json()
        
        if (result.status === 'success') {
          // 刷新预览
          await updatePreview()
          showMessage('撤销操作成功', 'success')
        } else {
          showMessage(`撤销失败: ${result.error}`, 'error')
          if (result.error.includes('没有可撤销')) {
            canUndo.value = false
          }
        }
        
      } catch (error) {
        console.error('撤销操作失败:', error)
        showMessage('撤销操作失败', 'error')
      }
    }
    
    const exportSubtitles = () => {
      showExportDialog.value = true
      generateExportPreview()
    }
    
    const generateExportPreview = () => {
      if (selectedExportFormat.value === 'srt') {
        exportPreview.value = generateSRTPreview()
      } else if (selectedExportFormat.value === 'vtt') {
        exportPreview.value = generateVTTPreview()
      } else if (selectedExportFormat.value === 'json') {
        exportPreview.value = generateJSONPreview()
      }
    }
    
    const generateSRTPreview = () => {
      let content = ''
      previewItems.value.slice(0, 3).forEach((item, index) => {
        content += `${index + 1}\n`
        content += `${formatTime(item.start_time).replace('.', ',')} --> ${formatTime(item.end_time).replace('.', ',')}\n`
        content += `${item.text}\n\n`
      })
      if (previewItems.value.length > 3) {
        content += '...\n'
      }
      return content
    }
    
    const generateVTTPreview = () => {
      let content = 'WEBVTT\n\n'
      previewItems.value.slice(0, 3).forEach((item) => {
        content += `${formatTime(item.start_time)} --> ${formatTime(item.end_time)}\n`
        content += `${item.text}\n\n`
      })
      if (previewItems.value.length > 3) {
        content += '...\n'
      }
      return content
    }
    
    const generateJSONPreview = () => {
      const data = {
        subtitles: previewItems.value.slice(0, 3).map(item => ({
          id: item.id,
          text: item.text,
          start_time: item.start_time,
          end_time: item.end_time,
          quality_score: item.quality_score
        })),
        total_count: previewItems.value.length
      }
      return JSON.stringify(data, null, 2)
    }
    
    const confirmExport = async () => {
      try {
        const response = await fetch('/api/real-time-preview/export-subtitles', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId.value,
            format: selectedExportFormat.value
          })
        })
        
        const result = await response.json()
        
        if (result.status === 'success') {
          // 创建下载链接
          const blob = new Blob([result.content], { type: 'text/plain' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = result.filename
          a.click()
          URL.revokeObjectURL(url)
          
          showMessage('字幕文件导出成功', 'success')
        } else {
          showMessage(`导出失败: ${result.error}`, 'error')
        }
        
      } catch (error) {
        console.error('导出字幕失败:', error)
        showMessage('导出字幕失败', 'error')
      } finally {
        closeExportDialog()
      }
    }
    
    const closeExportDialog = () => {
      showExportDialog.value = false
      exportPreview.value = ''
    }
    
    // 辅助函数
    const formatTime = (seconds) => {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = Math.floor(seconds % 60)
      const millis = Math.floor((seconds - Math.floor(seconds)) * 1000)
      
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`
    }
    
    const getScoreClass = (score) => {
      if (score >= 0.8) return 'score-high'
      if (score >= 0.6) return 'score-medium'
      return 'score-low'
    }
    
    const getDistributionWidth = (type) => {
      if (!qualitySummary.value?.quality_distribution) return '0%'
      
      const dist = qualitySummary.value.quality_distribution
      const total = dist.high + dist.medium + dist.low
      
      if (total === 0) return '0%'
      
      return `${(dist[type] / total * 100).toFixed(1)}%`
    }
    
    // 监听导出格式变化
    watch(selectedExportFormat, () => {
      if (showExportDialog.value) {
        generateExportPreview()
      }
    })
    
    // 生命周期
    onMounted(() => {
      // 可以在这里添加初始化逻辑
    })
    
    onUnmounted(() => {
      // 清理定时器
      if (inputDebounceTimer) {
        clearTimeout(inputDebounceTimer)
      }
      
      // 如果会话还活跃，尝试关闭
      if (isSessionActive.value) {
        stopPreviewSession()
      }
    })
    
    return {
      // 数据
      sessionId,
      isSessionActive,
      isLoading,
      loadingMessage,
      inputText,
      realTimeUpdate,
      enableQualityCheck,
      highlightIssues,
      previewItems,
      totalCount,
      processingStatus,
      qualitySummary,
      editingItemId,
      editingText,
      selectedForMerge,
      canUndo,
      showSplitDialogFlag,
      splitDialogText,
      splitPosition,
      showExportDialog,
      selectedExportFormat,
      exportPreview,
      exportFormats,
      message,
      messageType,
      
      // 计算属性
      estimatedDuration,
      
      // 方法
      startPreviewSession,
      stopPreviewSession,
      onTextInput,
      updatePreview,
      startEditing,
      saveEdit,
      cancelEdit,
      showSplitDialog,
      closeSplitDialog,
      confirmSplit,
      toggleSelectForMerge,
      mergeSelectedItems,
      clearSelection,
      undoLastEdit,
      exportSubtitles,
      confirmExport,
      closeExportDialog,
      formatTime,
      getScoreClass,
      getDistributionWidth
    }
  }
}
</script>

<style scoped>
.real-time-preview-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 标题栏样式 */
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e1e5e9;
}

.preview-title {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
}

.session-indicator {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: normal;
  margin-left: 10px;
}

.preview-controls {
  display: flex;
  gap: 10px;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-warning {
  background: #f39c12;
  color: white;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

/* 输入区域 */
.input-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.input-label {
  font-weight: 600;
  color: #2c3e50;
}

.input-stats {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #7f8c8d;
}

.text-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  font-size: 16px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: #3498db;
}

.input-options {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

/* 预览区域 */
.preview-section {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

/* 质量摘要 */
.quality-summary {
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.quality-header h3 {
  margin: 0;
  color: #2c3e50;
}

.quality-score {
  font-size: 18px;
  font-weight: 600;
}

.score-high {
  color: #27ae60;
}

.score-medium {
  color: #f39c12;
}

.score-low {
  color: #e74c3c;
}

.quality-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  background: white;
  border-radius: 6px;
  min-width: 80px;
}

.stat-label {
  font-size: 12px;
  color: #7f8c8d;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

/* 质量分布条 */
.quality-distribution {
  margin-bottom: 15px;
}

.distribution-bar {
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
}

.bar-segment {
  height: 100%;
  transition: width 0.3s;
}

.bar-segment.high {
  background: #27ae60;
}

.bar-segment.medium {
  background: #f39c12;
}

.bar-segment.low {
  background: #e74c3c;
}

/* 建议列表 */
.recommendations h4 {
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.recommendation-list {
  margin: 0;
  padding-left: 20px;
}

.recommendation-list li {
  margin-bottom: 5px;
  color: #5d6d7e;
}

/* 字幕预览列表 */
.subtitle-preview-list {
  padding: 20px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #dee2e6;
}

.preview-header h3 {
  margin: 0;
  color: #2c3e50;
}

.preview-info {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #7f8c8d;
}

/* 字幕项 */
.subtitle-items {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.subtitle-item {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 15px;
  transition: all 0.2s;
}

.subtitle-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.subtitle-item.has-issues {
  border-color: #e74c3c;
  background: rgba(231, 76, 60, 0.05);
}

.subtitle-item.high-quality {
  border-left: 4px solid #27ae60;
}

.subtitle-item.medium-quality {
  border-left: 4px solid #f39c12;
}

.subtitle-item.low-quality {
  border-left: 4px solid #e74c3c;
}

.subtitle-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 14px;
  color: #7f8c8d;
}

.subtitle-index {
  font-weight: 600;
  color: #3498db;
}

.subtitle-timing {
  font-family: monospace;
}

.subtitle-duration {
  color: #95a5a6;
}

.subtitle-quality {
  margin-left: auto;
}

.subtitle-content {
  margin-bottom: 10px;
}

.subtitle-text {
  font-size: 16px;
  line-height: 1.5;
  color: #2c3e50;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.subtitle-text:hover {
  background: #f8f9fa;
}

.subtitle-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.edit-textarea {
  width: 100%;
  padding: 8px;
  border: 2px solid #3498db;
  border-radius: 4px;
  font-size: 16px;
  resize: vertical;
}

.edit-buttons {
  display: flex;
  gap: 10px;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

/* 问题显示 */
.subtitle-issues {
  margin-bottom: 10px;
  padding: 8px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 4px;
}

.issues-label {
  font-weight: 600;
  color: #e74c3c;
}

.issues-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}

.issue-tag {
  background: #e74c3c;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

/* 操作按钮 */
.subtitle-actions {
  display: flex;
  gap: 5px;
}

.action-btn {
  padding: 4px 8px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f8f9fa;
}

.action-btn.selected {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

/* 空预览 */
.empty-preview {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.empty-text p {
  margin: 5px 0;
}

/* 操作面板 */
.action-panel {
  padding: 15px 20px;
  background: #fff3cd;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.merge-info {
  font-weight: 500;
  color: #856404;
}

.merge-actions {
  display: flex;
  gap: 10px;
}

.undo-panel {
  padding: 15px 20px;
  border-top: 1px solid #dee2e6;
  background: #f8f9fa;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 分割对话框 */
.split-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.original-text,
.split-position,
.split-part {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.text-display,
.text-preview {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  min-height: 40px;
}

.split-slider {
  width: 100%;
}

.position-indicator {
  text-align: center;
  font-weight: 600;
  color: #3498db;
}

.split-preview {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

/* 导出对话框 */
.export-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.format-selection label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
}

.format-buttons {
  display: flex;
  gap: 10px;
}

.format-btn {
  padding: 8px 16px;
  border: 2px solid #dee2e6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.format-btn:hover {
  background: #f8f9fa;
}

.format-btn.selected {
  border-color: #3498db;
  background: #3498db;
  color: white;
}

.export-preview label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
}

.export-content {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
}

/* 加载指示器 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.loading-spinner {
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #2c3e50;
  font-weight: 500;
}

/* 消息提示 */
.message-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 6px;
  color: white;
  font-weight: 500;
  z-index: 3000;
  animation: slideIn 0.3s ease-out;
}

.message-toast.success {
  background: #27ae60;
}

.message-toast.error {
  background: #e74c3c;
}

.message-toast.info {
  background: #3498db;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .real-time-preview-container {
    padding: 10px;
  }
  
  .preview-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .preview-controls {
    width: 100%;
    justify-content: center;
  }
  
  .input-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .quality-stats {
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .split-preview {
    grid-template-columns: 1fr;
  }
  
  .subtitle-header {
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .action-panel {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>
