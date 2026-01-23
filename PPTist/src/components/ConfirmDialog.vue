<template>
  <div v-if="visible" class="confirm-overlay" @click.self="handleCancel">
    <div class="confirm-dialog">
      <div class="confirm-header">
        <span class="confirm-icon">{{ icon }}</span>
        <h3 class="confirm-title">{{ title }}</h3>
      </div>
      
      <div class="confirm-content">
        <p class="confirm-message">{{ message }}</p>
      </div>
      
      <div class="confirm-actions">
        <button 
          class="confirm-btn confirm-btn-cancel"
          @click="handleCancel"
        >
          {{ cancelText }}
        </button>
        <button 
          class="confirm-btn confirm-btn-confirm"
          @click="handleConfirm"
          :class="{ 'confirm-btn-danger': type === 'danger' }"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

interface Props {
  visible: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'default' | 'danger' | 'warning'
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认操作',
  confirmText: '确定',
  cancelText: '取消',
  type: 'default'
})

const emit = defineEmits<{
  confirm: []
  cancel: []
  'update:visible': [value: boolean]
}>()

const icon = computed(() => {
  const icons = {
    default: '❓',
    danger: '⚠️',
    warning: '⚠️'
  }
  return icons[props.type]
})

const handleConfirm = () => {
  emit('update:visible', false)
  emit('confirm')
}

const handleCancel = () => {
  emit('update:visible', false)
  emit('cancel')
}
</script>

<style lang="scss" scoped>
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.2s ease-out;
}

.confirm-dialog {
  background: #fff;
  border-radius: 8px;
  min-width: 400px;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  animation: scaleIn 0.2s ease-out;
}

.confirm-header {
  padding: 20px 20px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #e0e0e0;
  
  .confirm-icon {
    font-size: 24px;
  }
  
  .confirm-title {
    margin: 0;
    font-size: 16px;
    font-weight: 500;
    color: #333;
  }
}

.confirm-content {
  padding: 16px 20px;
  
  .confirm-message {
    margin: 0;
    font-size: 14px;
    line-height: 1.5;
    color: #666;
  }
}

.confirm-actions {
  padding: 16px 20px 20px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #f0f0f0;
}

.confirm-btn {
  padding: 8px 16px;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-1px);
  }
}

.confirm-btn-cancel {
  background: #fff;
  color: #666;
  
  &:hover {
    background: #f5f5f5;
    border-color: #b0b0b0;
  }
}

.confirm-btn-confirm {
  background: #0066cc;
  color: #fff;
  border-color: #0066cc;
  
  &:hover {
    background: #0052a3;
    border-color: #0052a3;
  }
}

.confirm-btn-danger {
  background: #dc3545 !important;
  border-color: #dc3545 !important;
  
  &:hover {
    background: #c82333 !important;
    border-color: #c82333 !important;
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { 
    opacity: 0;
    transform: scale(0.9);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}
</style>
