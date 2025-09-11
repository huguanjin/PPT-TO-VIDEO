<template>
  <div class="section">
    <div class="section-header">
      <h3>音频文件上传</h3>
      <p>支持 WAV, MP3, FLAC, AAC, OGG, M4A 格式，最大 100MB</p>
    </div>
    
    <div class="upload-area" @drop="handleDrop" @dragover.prevent @dragenter.prevent>
      <input 
        ref="fileInput" 
        type="file" 
        :accept="acceptedFormats" 
        @change="handleFileSelect"
        style="display: none"
      >
      
      <div v-if="!uploadedFile" class="upload-placeholder" @click="$refs.fileInput.click()">
        <i class="upload-icon">📁</i>
        <p>点击选择音频文件或拖拽文件到此处</p>
        <p class="upload-hint">支持的格式: {{ supportedFormats.join(', ').toUpperCase() }}</p>
      </div>
      
      <div v-else class="file-info">
        <div class="file-details">
          <h4>{{ uploadedFile.name }}</h4>
          <div class="file-meta">
            <span class="file-size">{{ formatFileSize(uploadedFile.size) }}</span>
            <span class="file-type">{{ getFileExtension(uploadedFile.name).toUpperCase() }}</span>
          </div>
          <div class="file-actions">
            <button class="btn-secondary" @click="removeFile">
              <i>🗑️</i> 移除文件
            </button>
            <button class="btn-primary" @click="uploadFile" :disabled="uploading">
              <i>⬆️</i> {{ uploading ? '上传中...' : '开始上传' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading || uploadProgress > 0" class="upload-progress">
      <div class="progress-header">
        <span>上传进度</span>
        <span>{{ uploadProgress }}%</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <div v-if="uploadError" class="error-message">
        上传失败: {{ uploadError }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'AudioUpload',
  props: {
    supportedFormats: {
      type: Array,
      default: () => ['wav', 'mp3', 'flac', 'aac', 'ogg', 'm4a']
    }
  },
  emits: ['file-uploaded', 'file-removed'],
  setup(props, { emit }) {
    const uploadedFile = ref(null)
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const uploadError = ref('')

    const acceptedFormats = computed(() => {
      return props.supportedFormats.map(format => `.${format}`).join(',')
    })

    const handleFileSelect = (event) => {
      const files = event.target.files
      if (files && files.length > 0) {
        selectFile(files[0])
      }
    }

    const handleDrop = (event) => {
      event.preventDefault()
      const files = event.dataTransfer.files
      if (files && files.length > 0) {
        selectFile(files[0])
      }
    }

    const selectFile = (file) => {
      // 检查文件大小 (100MB)
      if (file.size > 100 * 1024 * 1024) {
        uploadError.value = '文件大小超过100MB限制'
        return
      }

      // 检查文件格式
      const extension = getFileExtension(file.name).toLowerCase()
      if (!props.supportedFormats.includes(extension)) {
        uploadError.value = `不支持的文件格式: ${extension}`
        return
      }

      uploadedFile.value = file
      uploadError.value = ''
      uploadProgress.value = 0
    }

    const removeFile = () => {
      uploadedFile.value = null
      uploadProgress.value = 0
      uploadError.value = ''
      emit('file-removed')
    }

    const uploadFile = () => {
      if (!uploadedFile.value) return

      uploading.value = true
      uploadError.value = ''
      uploadProgress.value = 0

      try {
        const formData = new FormData()
        formData.append('audio_file', uploadedFile.value)

        const xhr = new XMLHttpRequest()
        
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            uploadProgress.value = Math.round((event.loaded / event.total) * 100)
          }
        })

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText)
            emit('file-uploaded', {
              file: uploadedFile.value,
              response: response
            })
          }
          else {
            uploadError.value = `上传失败: HTTP ${xhr.status}`
          }
          uploading.value = false
        })

        xhr.addEventListener('error', () => {
          uploadError.value = '网络错误，上传失败'
          uploading.value = false
        })

        xhr.open('POST', '/api/audio/upload')
        xhr.send(formData)
      }
      catch (error) {
        uploadError.value = `上传失败: ${error.message}`
        uploading.value = false
      }
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const getFileExtension = (filename) => {
      return filename.split('.').pop() || ''
    }

    return {
      uploadedFile,
      uploading,
      uploadProgress,
      uploadError,
      acceptedFormats,
      handleFileSelect,
      handleDrop,
      removeFile,
      uploadFile,
      formatFileSize,
      getFileExtension
    }
  }
}
</script>

<style scoped>
.section {
  margin-bottom: 2rem;
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-header h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.section-header p {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.upload-area {
  border: 2px dashed #bdc3c7;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.upload-area:hover {
  border-color: #3498db;
  background: #ecf0f1;
}

.upload-placeholder {
  cursor: pointer;
  padding: 2rem;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  display: block;
}

.upload-hint {
  color: #7f8c8d;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.file-info {
  text-align: left;
}

.file-details h4 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

.file-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.file-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.btn-secondary {
  background: #ecf0f1;
  color: #7f8c8d;
}

.btn-secondary:hover {
  background: #d5dbdb;
}

.upload-progress {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #2c3e50;
}

.progress-bar {
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s ease;
}

.error-message {
  color: #e74c3c;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}
</style>
