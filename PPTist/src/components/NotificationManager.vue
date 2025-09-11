<template>
  <div v-if="notifications.length > 0" class="notification-container">
    <div 
      v-for="notification in notifications" 
      :key="notification.id"
      :class="['notification', `notification-${notification.type}`]"
    >
      <div class="notification-content">
        <span class="notification-icon">{{ getIcon(notification.type) }}</span>
        <span class="notification-message">{{ notification.message }}</span>
      </div>
      <button 
        class="notification-close"
        @click="removeNotification(notification.id)"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onUnmounted } from 'vue'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

const notifications = ref<Notification[]>([])
const timers = new Map<string, number>()

const getIcon = (type: string): string => {
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  }
  return icons[type as keyof typeof icons] || 'ℹ️'
}

const addNotification = (notification: Omit<Notification, 'id'>): string => {
  const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  const newNotification: Notification = {
    id,
    duration: 3000,
    ...notification
  }
  
  notifications.value.push(newNotification)
  
  // 自动移除通知
  if (newNotification.duration && newNotification.duration > 0) {
    const timer = setTimeout(() => {
      removeNotification(id)
    }, newNotification.duration)
    timers.set(id, timer)
  }
  
  return id
}

const removeNotification = (id: string): void => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
  
  const timer = timers.get(id)
  if (timer) {
    clearTimeout(timer)
    timers.delete(id)
  }
}

// 清理定时器
onUnmounted(() => {
  timers.forEach(timer => clearTimeout(timer))
  timers.clear()
})

// 导出方法供外部使用
defineExpose({
  addNotification,
  removeNotification,
  success: (message: string, duration?: number) => addNotification({ type: 'success', message, duration }),
  error: (message: string, duration?: number) => addNotification({ type: 'error', message, duration }),
  warning: (message: string, duration?: number) => addNotification({ type: 'warning', message, duration }),
  info: (message: string, duration?: number) => addNotification({ type: 'info', message, duration }),
})
</script>

<style lang="scss" scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification {
  min-width: 300px;
  max-width: 400px;
  padding: 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  animation: slideIn 0.3s ease-out;
}

.notification-success {
  background: #f0f9f0;
  border: 1px solid #4caf50;
  color: #2e7d2e;
}

.notification-error {
  background: #fff5f5;
  border: 1px solid #f44336;
  color: #c62828;
}

.notification-warning {
  background: #fffbf0;
  border: 1px solid #ff9800;
  color: #ef6c00;
}

.notification-info {
  background: #f0f8ff;
  border: 1px solid #2196f3;
  color: #1565c0;
}

.notification-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.notification-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.notification-message {
  font-size: 14px;
  line-height: 1.4;
}

.notification-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    opacity: 1;
  }
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
</style>
