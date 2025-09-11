<template>
  <div class="config-page">
    <div class="config-section">
      <h3>视频配置</h3>
      <div class="form-group">
        <label>分辨率:</label>
        <select v-model="config.video.resolution">
          <option value="1280x720">1280x720</option>
          <option value="1920x1080">1920x1080</option>
        </select>
      </div>
      <div class="form-group">
        <label>帧率:</label>
        <select v-model="config.video.fps">
          <option value="24">24 fps</option>
          <option value="30">30 fps</option>
          <option value="60">60 fps</option>
        </select>
      </div>
    </div>

    <div class="config-section">
      <h3>语音合成</h3>
      <div class="form-group">
        <label>引擎:</label>
        <select v-model="config.tts.engine">
          <option value="edge">Edge TTS</option>
          <option value="openai">OpenAI TTS</option>
          <option value="fish">Fish TTS</option>
        </select>
      </div>
      <div class="form-group">
        <label>语音角色:</label>
        <select v-model="config.tts.voice">
          <option value="zh-CN-XiaoxiaoNeural">晓晓 (女)</option>
          <option value="zh-CN-YunxiNeural">云希 (男)</option>
        </select>
      </div>
    </div>

    <div class="config-actions">
      <button @click="handleClose" class="btn-secondary">取消</button>
      <button @click="handleSave" class="btn-primary">保存配置</button>
      <button @click="handleSaveAndExport" class="btn-success">保存并导出</button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive, onMounted } from 'vue'
import message from '@/utils/message'
import { API_BASE_URL } from '@/config/api'

// 事件定义
const emit = defineEmits<{
  close: []
  export: []
}>()

// 配置数据
const config = reactive({
  video: {
    resolution: '1920x1080',
    fps: 30,
    bitrate: '2M'
  },
  tts: {
    engine: 'edge',
    voice: 'zh-CN-XiaoxiaoNeural',
    rate: '+0%',
    pitch: '+0Hz'
  },
  subtitle: {
    enabled: true,
    font_size: 24,
    font_color: 'white'
  }
})

// 加载配置
const loadConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`)
    if (response.ok) {
      const data = await response.json()
      Object.assign(config, data)
    }
  } 
  catch (error) {
    // 忽略错误，避免控制台输出
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    })
    
    if (response.ok) {
      message.success('配置保存成功')
      return true
    }
    
    throw new Error('保存失败')
  } 
  catch (error) {
    message.error('配置保存失败')
    return false
  }
}

// 事件处理
const handleClose = () => {
  emit('close')
}

const handleSave = async () => {
  await saveConfig()
  emit('close')
}

const handleSaveAndExport = async () => {
  const success = await saveConfig()
  if (success) {
    emit('export')
  }
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.config-page {
  .config-section {
    margin-bottom: 24px;
    
    h3 {
      margin: 0 0 16px 0;
      font-size: 16px;
      color: #333;
    }
    
    .form-group {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      
      label {
        width: 80px;
        font-size: 14px;
        color: #666;
      }
      
      select {
        flex: 1;
        padding: 8px 12px;
        border: 1px solid #d9d9d9;
        border-radius: 4px;
        font-size: 14px;
      }
    }
  }
  
  .config-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
    
    button {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
      
      &.btn-secondary {
        background: #f5f5f5;
        color: #666;
        
        &:hover {
          background: #e8e8e8;
        }
      }
      
      &.btn-primary {
        background: #1677ff;
        color: white;
        
        &:hover {
          background: #1454d4;
        }
      }
      
      &.btn-success {
        background: #52c41a;
        color: white;
        
        &:hover {
          background: #389e0d;
        }
      }
    }
  }
}
</style>
