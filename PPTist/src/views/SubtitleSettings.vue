<!--
字幕设置页面
整合智能字幕配置功能
-->
<template>
  <div class="subtitle-settings">
    <div class="settings-header">
      <h2>📝 字幕设置</h2>
      <p>配置视频字幕生成的各项参数</p>
      <button class="close-btn" @click="emit('close')" title="关闭">✕</button>
    </div>

    <!-- 基础字幕设置 -->
    <div class="settings-section">
      <h3>🎬 基础设置</h3>
      
      <div class="setting-group">
        <label>字幕显示时长 (秒)：</label>
        <input 
          type="number" 
          v-model.number="basicSettings.duration"
          :min="1" 
          :max="10"
          :step="0.1"
        />
      </div>

      <div class="setting-group">
        <label>字幕字体大小：</label>
        <select v-model="basicSettings.fontSize">
          <option value="small">小</option>
          <option value="medium">中</option>
          <option value="large">大</option>
        </select>
      </div>

      <div class="setting-group">
        <label>字幕位置：</label>
        <select v-model="basicSettings.position">
          <option value="bottom">底部</option>
          <option value="center">中间</option>
          <option value="top">顶部</option>
        </select>
      </div>

      <div class="setting-group">
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            v-model="basicSettings.showBackground"
          />
          显示字幕背景
        </label>
      </div>
    </div>

    <!-- 智能字幕配置 -->
    <div class="settings-section">
      <SmartSubtitleConfig 
        v-model="smartSubtitleConfig"
        @change="onSmartConfigChange"
      />
    </div>

    <!-- 预览区域 -->
    <div class="settings-section">
      <h3>👀 预览</h3>
      
      <div class="preview-container">
        <div 
          class="subtitle-preview"
          :class="{
            'small-font': basicSettings.fontSize === 'small',
            'medium-font': basicSettings.fontSize === 'medium',
            'large-font': basicSettings.fontSize === 'large',
            'position-top': basicSettings.position === 'top',
            'position-center': basicSettings.position === 'center',
            'position-bottom': basicSettings.position === 'bottom',
            'with-background': basicSettings.showBackground
          }"
        >
          {{ previewText }}
        </div>
      </div>
    </div>

    <!-- 保存按钮 -->
    <div class="settings-actions">
      <button 
        class="save-btn"
        @click="saveAllSettings"
        :disabled="isSaving"
      >
        {{ isSaving ? '保存中...' : '保存设置' }}
      </button>
      
      <button 
        class="reset-btn"
        @click="resetToDefaults"
      >
        恢复默认
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import SmartSubtitleConfig from '@/components/SmartSubtitleConfig.vue'
import type { SmartSubtitleConfig as ISmartSubtitleConfig } from '@/services/smartSubtitle'

// Emits
const emit = defineEmits<{
  'close': []
}>()

// 基础设置接口
interface BasicSubtitleSettings {
  duration: number
  fontSize: 'small' | 'medium' | 'large'
  position: 'top' | 'center' | 'bottom'
  showBackground: boolean
}

// 响应式数据
const basicSettings = reactive<BasicSubtitleSettings>({
  duration: 3.0,
  fontSize: 'medium',
  position: 'bottom',
  showBackground: true
})

const smartSubtitleConfig = ref<Partial<ISmartSubtitleConfig>>({})
const isSaving = ref(false)

// 预览文本
const previewText = computed(() => {
  if (smartSubtitleConfig.value.enabled) {
    return '这是智能分割的字幕预览文本，支持AI语义理解。'
  }
  return '这是标准字幕的预览文本。'
})

// 组件挂载
onMounted(() => {
  loadSettings()
})

// 加载设置
function loadSettings() {
  // 从localStorage加载基础设置
  const savedBasicSettings = localStorage.getItem('subtitleBasicSettings')
  if (savedBasicSettings) {
    try {
      Object.assign(basicSettings, JSON.parse(savedBasicSettings))
    } 
    catch (error) {
      // 使用默认设置
    }
  }
}

// 智能配置变化处理
function onSmartConfigChange(config: Partial<ISmartSubtitleConfig>) {
  smartSubtitleConfig.value = config
}

// 保存所有设置
function saveAllSettings() {
  isSaving.value = true
  
  try {
    // 保存基础设置到localStorage
    localStorage.setItem('subtitleBasicSettings', JSON.stringify(basicSettings))
    
    // 智能配置会通过SmartSubtitleConfig组件自动保存到后端
    showMessage('设置保存成功')
    
  } 
  catch (error) {
    showMessage('设置保存失败', 'error')
  } 
  finally {
    isSaving.value = false
  }
}

// 恢复默认设置
function resetToDefaults() {
  // 重置基础设置
  basicSettings.duration = 3.0
  basicSettings.fontSize = 'medium'
  basicSettings.position = 'bottom'
  basicSettings.showBackground = true
  
  // 清除智能配置（组件会处理）
  smartSubtitleConfig.value = {
    enabled: false
  }
  
  showMessage('已恢复默认设置')
}

// 简单的消息提示
function showMessage(message: string, type: 'success' | 'error' | 'warning' = 'success') {
  const messageEl = document.createElement('div')
  messageEl.textContent = message
  messageEl.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 4px;
    color: white;
    z-index: 9999;
    font-size: 14px;
    background-color: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#ffc107'};
  `
  document.body.appendChild(messageEl)
  
  setTimeout(() => {
    if (messageEl.parentNode) {
      messageEl.parentNode.removeChild(messageEl)
    }
  }, 3000)
}
</script>

<style scoped>
.subtitle-settings {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.settings-header {
  text-align: center;
  margin-bottom: 30px;
  position: relative;
}

.settings-header h2 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 24px;
}

.settings-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.close-btn {
  position: absolute;
  top: 0;
  right: 0;
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f5f5;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #666;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #e0e0e0;
  color: #333;
}

.settings-section {
  margin-bottom: 40px;
  padding: 25px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.settings-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.setting-group {
  margin-bottom: 20px;
}

.setting-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 8px;
}

.setting-group input,
.setting-group select {
  width: 200px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.preview-container {
  position: relative;
  width: 100%;
  height: 200px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  overflow: hidden;
}

.subtitle-preview {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  color: white;
  text-align: center;
  white-space: nowrap;
  transition: all 0.3s ease;
}

/* 字体大小 */
.subtitle-preview.small-font {
  font-size: 14px;
}

.subtitle-preview.medium-font {
  font-size: 18px;
}

.subtitle-preview.large-font {
  font-size: 22px;
}

/* 位置 */
.subtitle-preview.position-top {
  top: 20px;
}

.subtitle-preview.position-center {
  top: 50%;
  transform: translate(-50%, -50%);
}

.subtitle-preview.position-bottom {
  bottom: 20px;
}

/* 背景 */
.subtitle-preview.with-background {
  background: rgba(0, 0, 0, 0.7);
  border-radius: 4px;
}

.settings-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.save-btn,
.reset-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-btn {
  background: #007bff;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #0056b3;
}

.save-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.reset-btn {
  background: #6c757d;
  color: white;
}

.reset-btn:hover {
  background: #545b62;
}
</style>
