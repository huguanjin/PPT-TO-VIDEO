<template>
  <div class="image-creator-container">
    <!-- 左侧控制面板 -->
    <div class="control-panel">
      <div class="panel-header">
        <span class="title">AI 绘图</span>
        <button class="settings-btn" @click="showSettings = true" title="API 设置">⚙️</button>
      </div>

      <!-- 模型选择 -->
      <div class="form-group">
        <label>选择模型</label>
        <select v-model="form.model" @change="onModelChange">
          <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>

      <!-- 宽高比 -->
      <div class="form-group">
        <label>宽高比</label>
        <select v-model="form.size">
          <option v-for="s in availableSizes" :key="s" :value="s">{{ sizeLabels[s] || s }}</option>
        </select>
      </div>

      <!-- 提示词输入 -->
      <div class="form-group prompt-group">
        <textarea v-model="form.prompt" placeholder="描述你想要生成的图像..." rows="3" maxlength="3000"></textarea>
        <div class="char-count">{{ form.prompt.length }} / 3000</div>
      </div>

      <!-- 参考图片区域 -->
      <div class="reference-section">
        <label>参考图片（可选）<span class="ref-count">（最多 {{ maxReferenceImages }} 张，已 {{ referenceImages.length }} 张）</span></label>
        <div class="reference-images">
          <div v-for="(img, idx) in referenceImages" :key="idx" class="ref-image-item">
            <img :src="img" alt="参考图片" />
            <button class="remove-btn" @click="removeReferenceImage(idx)">×</button>
          </div>
          <div v-if="referenceImages.length < maxReferenceImages" class="add-image-btn" @click="triggerFileInput">
            <span class="plus-icon">+</span>
          </div>
        </div>
        <input ref="fileInput" type="file" accept="image/*" style="display: none" @change="onFileSelect" />
      </div>

      <!-- 生成按钮 -->
      <button class="generate-btn" @click="handleGenerate" :disabled="!form.prompt.trim() || isGenerating">
        {{ isGenerating ? '生成中...' : '🎨 生成图片' }}
      </button>
    </div>

    <!-- 右侧结果面板 -->
    <div class="result-panel">
      <div class="result-header">
        <span>生成结果</span>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      <div class="result-content">
        <div v-if="isGenerating" class="generating-status">
          <div class="loading-dots"><span></span><span></span><span></span></div>
          <p>正在生成图像，请稍候...</p>
        </div>
        <div v-else-if="generatedImage" class="generated-result">
          <div class="result-image-wrapper">
            <img :src="generatedImage" alt="生成的图片" />
            <div class="image-toolbar">
              <button @click="downloadImage">💾 下载</button>
              <button @click="insertToSlide">📥 插入幻灯片</button>
              <button @click="copyImage">📋 复制</button>
            </div>
          </div>
          <p v-if="revisedPrompt" class="revised-prompt">优化后的提示词: {{ revisedPrompt }}</p>
        </div>
        <div v-else-if="history.length" class="history-section">
          <h4>生成历史</h4>
          <div class="history-grid">
            <div v-for="item in history" :key="item.id" class="history-item">
              <img :src="item.image_url" alt="历史图片" @click="previewHistoryItem(item)" />
              <div class="history-item-actions">
                <button @click="useHistoryPrompt(item)">复用</button>
                <button class="delete-btn" @click="confirmDeleteHistory(item)">删除</button>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state"><p>输入提示词并点击生成按钮创建图像</p></div>
        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="delete-confirm-overlay" @click.self="showDeleteConfirm = false">
      <div class="delete-confirm-dialog">
        <p>确定要删除这条记录吗？</p>
        <div class="dialog-actions">
          <button class="cancel-btn" @click="showDeleteConfirm = false">取消</button>
          <button class="confirm-btn" @click="doDeleteHistory">确定删除</button>
        </div>
      </div>
    </div>

    <!-- 设置模态框 -->
    <div v-if="showSettings" class="settings-overlay" @click.self="showSettings = false">
      <div class="settings-modal">
        <div class="settings-modal-header">
          <span>API 设置</span>
          <button class="close-btn" @click="showSettings = false">✕</button>
        </div>
        <div class="settings-modal-body">
          <div class="form-group">
            <label>API Base URL</label>
            <input v-model="apiSettings.api_base_url" type="text" placeholder="https://api.openai.com/v1" />
          </div>
          <div class="form-group">
            <label>API Key</label>
            <input v-model="apiSettings.api_key" type="password" placeholder="sk-..." />
          </div>
          <div class="form-group">
            <label>自定义模型列表 <span class="hint">（每行一个模型名称）</span></label>
            <textarea 
              v-model="customModelsText" 
              placeholder="nano-banana&#10;nano-banana-2&#10;dall-e-3"
              rows="5"
              class="models-textarea"
            ></textarea>
          </div>
        </div>
        <div class="settings-modal-footer">
          <button class="cancel-btn" @click="showSettings = false">取消</button>
          <button class="save-btn" @click="saveSettings" :disabled="isSavingSettings">
            {{ isSavingSettings ? '保存中...' : '保存配置' }}
          </button>
          <span class="save-tip" v-if="saveMessage">{{ saveMessage }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject } from 'vue'
import axios from 'axios'
import message from '@/utils/message'
import { API_BASE_URL } from '@/config/api'

const emit = defineEmits<{ (e: 'close'): void; (e: 'insert', url: string): void }>()
const addImageElement = inject<((url: string) => void) | undefined>('addImageElement', undefined)

const showSettings = ref(false)
const apiSettings = ref({ api_base_url: '', api_key: '' })
const customModelsText = ref('nano-banana\nnano-banana-2')
const isSavingSettings = ref(false)
const saveMessage = ref('')
const form = ref({ model: 'nano-banana', size: '1:1', prompt: '', quality: 'high' })

// 从自定义文本解析模型列表
const models = computed(() => {
  return customModelsText.value
    .split('\n')
    .map(s => s.trim())
    .filter(s => s.length > 0)
})

const sizeLabels: Record<string, string> = {
  '1:1': '1:1 (正方形)', '4:3': '4:3 (横向)', '3:4': '3:4 (纵向)',
  '16:9': '16:9 (宽屏)', '9:16': '9:16 (竖屏)', '2:3': '2:3 (人像)', '3:2': '3:2 (风景)'
}
const availableSizes = ['1:1', '4:3', '3:4', '16:9', '9:16', '2:3', '3:2']
const referenceImages = ref<string[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const maxReferenceImages = computed(() => form.value.model.includes('nano-banana-2') ? 14 : 3)
const isGenerating = ref(false)
const generatedImage = ref('')
const revisedPrompt = ref('')
const errorMessage = ref('')
const history = ref<any[]>([])
const showDeleteConfirm = ref(false)
const deleteTarget = ref<any>(null)

// 创建 API 客户端
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  withCredentials: true
})

const onModelChange = () => {
  if (referenceImages.value.length > maxReferenceImages.value) {
    referenceImages.value = referenceImages.value.slice(0, maxReferenceImages.value)
    message.warning(`参考图片已裁剪至 ${maxReferenceImages.value} 张`)
  }
}

const triggerFileInput = () => fileInput.value?.click()

const onFileSelect = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    if (referenceImages.value.length < maxReferenceImages.value) {
      referenceImages.value.push(ev.target?.result as string)
    }
  }
  reader.readAsDataURL(file)
  if (fileInput.value) fileInput.value.value = ''
}

const removeReferenceImage = (idx: number) => referenceImages.value.splice(idx, 1)

const handleGenerate = async () => {
  if (!form.value.prompt.trim()) return
  isGenerating.value = true
  errorMessage.value = ''
  generatedImage.value = ''
  revisedPrompt.value = ''
  try {
    const res = await api.post('/api/image/generate', {
      prompt: form.value.prompt,
      model: form.value.model,
      size: form.value.size,
      quality: form.value.quality,
      reference_images: referenceImages.value
    })
    if (res.data.success && res.data.data?.image_url) {
      generatedImage.value = res.data.data.image_url
      revisedPrompt.value = res.data.data.revised_prompt || ''
      loadHistory()
    }
    else {
      errorMessage.value = res.data.error || '生成失败'
    }
  }
  catch (err: any) {
    errorMessage.value = err.response?.data?.error || err.message || '生成失败'
  }
  finally {
    isGenerating.value = false
  }
}

const downloadImage = () => {
  if (!generatedImage.value) return
  const a = document.createElement('a')
  a.href = generatedImage.value
  a.download = `generated_${Date.now()}.png`
  a.click()
}

const insertToSlide = () => {
  if (!generatedImage.value) return
  if (addImageElement) {
    addImageElement(generatedImage.value)
    message.success('已插入幻灯片')
    emit('close')
  }
  else {
    emit('insert', generatedImage.value)
  }
}

const copyImage = async () => {
  if (!generatedImage.value) return
  try {
    const res = await fetch(generatedImage.value)
    const blob = await res.blob()
    await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })])
    message.success('已复制到剪贴板')
  }
  catch {
    message.error('复制失败')
  }
}

const loadHistory = async () => {
  try {
    const res = await api.get('/api/image/history', { params: { limit: 20 } })
    if (res.data.success) history.value = res.data.data || []
  }
  catch {
    // ignore
  }
}

const previewHistoryItem = (item: any) => {
  generatedImage.value = item.image_url
}

const useHistoryPrompt = (item: any) => {
  form.value.prompt = item.prompt
  if (item.model && models.value.includes(item.model)) {
    form.value.model = item.model
    onModelChange()
  }
  if (item.size) form.value.size = item.size
  message.success('已复用提示词')
}

const confirmDeleteHistory = (item: any) => {
  deleteTarget.value = item
  showDeleteConfirm.value = true
}

const doDeleteHistory = async () => {
  if (!deleteTarget.value) return
  try {
    await api.delete(`/api/image/history/${deleteTarget.value.id}`)
    history.value = history.value.filter(h => h.id !== deleteTarget.value.id)
    message.success('删除成功')
  }
  catch {
    message.error('删除失败')
  }
  showDeleteConfirm.value = false
  deleteTarget.value = null
}

const loadConfig = async () => {
  try {
    const res = await api.get('/api/image/config')
    if (res.data.success && res.data.data) {
      const cfg = res.data.data
      apiSettings.value.api_base_url = cfg.api_base_url || ''
      apiSettings.value.api_key = cfg.api_key || ''
      // 加载自定义模型列表
      if (cfg.custom_models && Array.isArray(cfg.custom_models) && cfg.custom_models.length > 0) {
        customModelsText.value = cfg.custom_models.join('\n')
      }
      // 设置默认模型
      if (cfg.default_model && models.value.includes(cfg.default_model)) {
        form.value.model = cfg.default_model
      }
      else if (models.value.length > 0) {
        form.value.model = models.value[0]
      }
      if (cfg.default_size) form.value.size = cfg.default_size
    }
  }
  catch {
    // ignore
  }
}

const saveSettings = async () => {
  isSavingSettings.value = true
  saveMessage.value = ''
  try {
    const customModels = customModelsText.value
      .split('\n')
      .map(s => s.trim())
      .filter(s => s.length > 0)
    await api.post('/api/image/config', { 
      image_generation: {
        ...apiSettings.value,
        custom_models: customModels
      }
    })
    saveMessage.value = '✓ 已保存'
    // 保存后更新当前模型（如果当前模型不在列表中）
    if (!customModels.includes(form.value.model) && customModels.length > 0) {
      form.value.model = customModels[0]
    }
    setTimeout(() => {
      saveMessage.value = ''
    }, 2000)
  }
  catch {
    saveMessage.value = '保存失败'
  }
  isSavingSettings.value = false
}

onMounted(() => {
  loadConfig()
  loadHistory()
})
</script>

<style lang="scss" scoped>
.image-creator-container {
  display: flex; width: 100%; height: 100%; max-height: 70vh; background: #1a1a1a; border-radius: 8px; overflow: hidden;
}
.control-panel {
  width: 300px; flex-shrink: 0; background: #1e1e1e; border-right: 1px solid #333; padding: 16px; overflow-y: auto; color: #e0e0e0;
  .panel-header {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #333;
    .title { font-size: 14px; font-weight: 500; color: #4ade80; }
    .settings-btn { background: transparent; border: none; font-size: 16px; cursor: pointer; opacity: 0.7; &:hover { opacity: 1; } }
  }
}
.form-group {
  margin-bottom: 12px;
  label { display: block; margin-bottom: 6px; font-size: 12px; color: #999; }
  select, input {
    width: 100%; padding: 8px 10px; border: 1px solid #444; border-radius: 4px; font-size: 13px; background: #2a2a2a; color: #e0e0e0;
    &:focus { outline: none; border-color: #4ade80; }
    option { background: #2a2a2a; color: #e0e0e0; }
  }
  &.prompt-group {
    textarea {
      width: 100%; padding: 10px; border: 1px solid #444; border-radius: 4px; font-size: 13px; background: #2a2a2a; color: #e0e0e0; resize: vertical; min-height: 60px; max-height: 120px;
      &::placeholder { color: #666; }
      &:focus { outline: none; border-color: #4ade80; }
    }
    .char-count { text-align: right; font-size: 11px; color: #666; margin-top: 2px; }
  }
}
.reference-section {
  margin-bottom: 12px;
  label { display: block; margin-bottom: 6px; font-size: 12px; color: #999; line-height: 1.4; .ref-count { color: #4ade80; } }
  .reference-images { display: flex; gap: 6px; flex-wrap: wrap; }
  .ref-image-item {
    position: relative; width: 60px; height: 60px; border-radius: 4px; overflow: hidden; border: 1px solid #444;
    img { width: 100%; height: 100%; object-fit: cover; }
    .remove-btn {
      position: absolute; top: 2px; right: 2px; width: 16px; height: 16px; border: none; background: rgba(255, 0, 0, 0.8);
      color: #fff; border-radius: 50%; cursor: pointer; font-size: 10px; line-height: 1; display: flex; align-items: center; justify-content: center;
    }
  }
  .add-image-btn {
    width: 60px; height: 60px; border: 2px dashed #444; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s;
    .plus-icon { font-size: 24px; color: #666; }
    &:hover { border-color: #4ade80; .plus-icon { color: #4ade80; } }
  }
}
.generate-btn {
  width: 100%; padding: 10px; border: none; border-radius: 4px; background: #4ade80; color: #1a1a1a; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; margin-bottom: 12px;
  &:hover:not(:disabled) { background: #22c55e; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
.model-description {
  background: #252525; border-radius: 4px; padding: 10px; font-size: 11px; color: #999; line-height: 1.5;
  h4 { margin: 0 0 6px; font-size: 12px; color: #e0e0e0; }
  ul { margin: 0; padding-left: 14px; li { margin-bottom: 2px; strong { color: #4ade80; } } }
}
.result-panel {
  flex: 1; display: flex; flex-direction: column; background: #1a1a1a; min-width: 0;
  .result-header {
    display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid #333; flex-shrink: 0;
    span { font-size: 13px; color: #e0e0e0; }
    .close-btn { width: 24px; height: 24px; border: none; background: transparent; font-size: 16px; cursor: pointer; color: #999; border-radius: 4px; &:hover { background: #333; color: #fff; } }
  }
  .result-content { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }
}
.generating-status {
  text-align: center; color: #999;
  .loading-dots {
    display: flex; gap: 6px; justify-content: center; margin-bottom: 12px;
    span {
      width: 8px; height: 8px; background: #4ade80; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;
      &:nth-child(1) { animation-delay: -0.32s; }
      &:nth-child(2) { animation-delay: -0.16s; }
    }
  }
  @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
}
.generated-result {
  width: 100%;
  .result-image-wrapper {
    background: #252525; border-radius: 6px; padding: 10px; margin-bottom: 10px;
    img { width: 100%; max-width: 400px; border-radius: 4px; display: block; margin: 0 auto; }
    .image-toolbar {
      display: flex; justify-content: center; gap: 10px; margin-top: 10px;
      button {
        padding: 6px 12px; border: 1px solid #444; background: #2a2a2a; color: #e0e0e0; border-radius: 4px; cursor: pointer; font-size: 12px;
        &:hover { background: #333; border-color: #4ade80; }
      }
    }
  }
  .revised-prompt { background: #252525; padding: 8px 10px; border-radius: 4px; font-size: 12px; color: #999; }
}
.history-section {
  width: 100%;
  h4 { margin: 0 0 10px; font-size: 13px; color: #999; }
  .history-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; }
  .history-item {
    background: #252525; border-radius: 4px; overflow: hidden;
    img { width: 100%; height: 80px; object-fit: cover; cursor: pointer; }
    .history-item-actions {
      display: flex; border-top: 1px solid #333;
      button {
        flex: 1; padding: 4px; border: none; background: transparent; color: #999; cursor: pointer; font-size: 11px;
        &:hover { background: #333; color: #fff; }
        &.delete-btn:hover { color: #ff4d4f; }
        &:not(:last-child) { border-right: 1px solid #333; }
      }
    }
  }
}
.empty-state { text-align: center; color: #666; font-size: 13px; padding-top: 40px; }
.error-message {
  margin-top: 12px; padding: 10px 12px; background: rgba(255, 77, 79, 0.1); border: 1px solid rgba(255, 77, 79, 0.3);
  border-radius: 6px; color: #ff4d4f; font-size: 13px; text-align: center;
}
.delete-confirm-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.delete-confirm-dialog {
  background: #2a2a2a; padding: 24px; border-radius: 8px; text-align: center; min-width: 280px; border: 1px solid #444;
  p { margin: 0 0 20px; font-size: 15px; color: #e0e0e0; }
  .dialog-actions {
    display: flex; gap: 12px; justify-content: center;
    button { padding: 8px 24px; border-radius: 4px; font-size: 14px; cursor: pointer; transition: all 0.2s; }
    .cancel-btn { border: 1px solid #444; background: transparent; color: #999; &:hover { border-color: #666; color: #fff; } }
    .confirm-btn { border: none; background: #ff4d4f; color: #fff; &:hover { background: #ff7875; } }
  }
}

// 设置模态框
.settings-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); 
  display: flex; align-items: center; justify-content: center; z-index: 1001;
}
.settings-modal {
  background: #2a2a2a; border-radius: 8px; min-width: 380px; max-width: 90vw; border: 1px solid #444;
  .settings-modal-header {
    display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #444;
    span { font-size: 16px; font-weight: 500; color: #e0e0e0; }
    .close-btn { width: 28px; height: 28px; border: none; background: transparent; font-size: 18px; cursor: pointer; color: #999; border-radius: 4px;
      &:hover { background: #333; color: #fff; }
    }
  }
  .settings-modal-body {
    padding: 20px;
    .form-group {
      margin-bottom: 16px;
      label { display: block; margin-bottom: 8px; font-size: 13px; color: #999;
        .hint { font-size: 11px; color: #666; }
      }
      input, .models-textarea {
        width: 100%; padding: 10px 12px; border: 1px solid #444; border-radius: 6px; font-size: 14px; background: #1e1e1e; color: #e0e0e0;
        &:focus { outline: none; border-color: #4ade80; }
        &::placeholder { color: #666; }
      }
      .models-textarea { resize: vertical; min-height: 100px; font-family: monospace; font-size: 13px; }
    }
  }
  .settings-modal-footer {
    display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-top: 1px solid #444; justify-content: flex-end;
    .cancel-btn { padding: 8px 20px; border: 1px solid #444; background: transparent; color: #999; border-radius: 4px; cursor: pointer;
      &:hover { border-color: #666; color: #fff; }
    }
    .save-btn { padding: 8px 20px; border: none; border-radius: 4px; background: #4ade80; color: #1a1a1a; font-weight: 500; cursor: pointer;
      &:hover:not(:disabled) { background: #22c55e; }
      &:disabled { opacity: 0.6; cursor: not-allowed; }
    }
    .save-tip { font-size: 12px; color: #4ade80; }
  }
}
</style>
