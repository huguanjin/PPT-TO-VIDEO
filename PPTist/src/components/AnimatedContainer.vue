<template>
  <div class="animated-container">
    <!-- 加载动画 -->
    <Transition name="fade-scale" mode="out-in">
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <p class="loading-text">{{ loadingText }}</p>
      </div>
    </Transition>

    <!-- 成功/错误消息动画 -->
    <TransitionGroup name="slide-notification" tag="div" class="notifications">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification"
        :class="[`notification-${notification.type}`]"
      >
        <div class="notification-icon">
          <IconCheckOne v-if="notification.type === 'success'" />
          <IconCloseOne v-if="notification.type === 'error'" />
          <IconInfo v-if="notification.type === 'info'" />
          <IconWarning v-if="notification.type === 'warning'" />
        </div>
        <div class="notification-content">
          <h4 class="notification-title">{{ notification.title }}</h4>
          <p class="notification-message">{{ notification.message }}</p>
        </div>
        <button 
          class="notification-close"
          @click="removeNotification(notification.id)"
        >
          <IconClose />
        </button>
      </div>
    </TransitionGroup>

    <!-- 进度条动画 -->
    <div v-if="showProgress" class="progress-container">
      <div class="progress-info">
        <span class="progress-label">{{ progressLabel }}</span>
        <span class="progress-percent">{{ Math.round(progress) }}%</span>
      </div>
      <div class="progress-bar">
        <div 
          class="progress-fill"
          :style="{ width: `${progress}%` }"
        ></div>
      </div>
      <div v-if="progressSteps.length > 0" class="progress-steps">
        <div
          v-for="(step, index) in progressSteps"
          :key="index"
          class="progress-step"
          :class="{
            'step-completed': index < currentStep,
            'step-active': index === currentStep,
            'step-pending': index > currentStep
          }"
        >
          <div class="step-indicator">
            <IconCheckOne v-if="index < currentStep" />
            <span v-else>{{ index + 1 }}</span>
          </div>
          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>
    </div>

    <!-- 骨架屏动画 -->
    <div v-if="showSkeleton" class="skeleton-container">
      <div class="skeleton-item">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-content">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line skeleton-subtitle"></div>
          <div class="skeleton-line skeleton-text"></div>
        </div>
      </div>
      <div class="skeleton-item">
        <div class="skeleton-content">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line skeleton-text"></div>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <Transition :name="transitionName" mode="out-in">
      <div v-if="!loading && !showSkeleton" :key="contentKey">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Notification {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  title: string
  message: string
  duration?: number
}

interface ProgressStep {
  label: string
  description?: string
}

interface Props {
  loading?: boolean
  loadingText?: string
  showProgress?: boolean
  progress?: number
  progressLabel?: string
  progressSteps?: ProgressStep[]
  currentStep?: number
  showSkeleton?: boolean
  transitionName?: string
  contentKey?: string | number
}

withDefaults(defineProps<Props>(), {
  loading: false,
  loadingText: '加载中...',
  showProgress: false,
  progress: 0,
  progressLabel: '处理中',
  progressSteps: () => [],
  currentStep: 0,
  showSkeleton: false,
  transitionName: 'fade-slide',
  contentKey: 'default'
})

defineEmits<{
  'notification-click': [notification: Notification]
}>()

// 通知系统
const notifications = ref<Notification[]>([])
let notificationId = 0

// 方法
const addNotification = (notification: Omit<Notification, 'id'>) => {
  const id = `notification-${++notificationId}`
  const fullNotification: Notification = {
    id,
    duration: 5000,
    ...notification
  }
  
  notifications.value.push(fullNotification)
  
  // 自动移除
  if (fullNotification.duration && fullNotification.duration > 0) {
    setTimeout(() => {
      removeNotification(id)
    }, fullNotification.duration)
  }
  
  return id
}

const removeNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

const clearNotifications = () => {
  notifications.value = []
}

// 快捷方法
const success = (title: string, message: string = '', duration?: number) => {
  return addNotification({ type: 'success', title, message, duration })
}

const error = (title: string, message: string = '', duration?: number) => {
  return addNotification({ type: 'error', title, message, duration })
}

const info = (title: string, message: string = '', duration?: number) => {
  return addNotification({ type: 'info', title, message, duration })
}

const warning = (title: string, message: string = '', duration?: number) => {
  return addNotification({ type: 'warning', title, message, duration })
}

// 暴露给父组件
defineExpose({
  addNotification,
  removeNotification,
  clearNotifications,
  success,
  error,
  info,
  warning
})
</script>

<style lang="scss" scoped>
.animated-container {
  position: relative;
  width: 100%;
  height: 100%;
}

// 加载动画
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;

  .loading-spinner {
    position: relative;
    width: 60px;
    height: 60px;
    margin-bottom: 16px;

    .spinner-ring {
      position: absolute;
      width: 100%;
      height: 100%;
      border: 3px solid transparent;
      border-top: 3px solid #3b82f6;
      border-radius: 50%;
      animation: spin 1s linear infinite;

      &:nth-child(2) {
        width: 80%;
        height: 80%;
        top: 10%;
        left: 10%;
        border-top-color: #8b5cf6;
        animation-duration: 1.5s;
        animation-direction: reverse;
      }

      &:nth-child(3) {
        width: 60%;
        height: 60%;
        top: 20%;
        left: 20%;
        border-top-color: #06d6a0;
        animation-duration: 2s;
      }
    }
  }

  .loading-text {
    font-size: 14px;
    color: #6b7280;
    margin: 0;
  }
}

// 通知动画
.notifications {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1001;
  max-width: 400px;
}

.notification {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #3b82f6;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 300px;

  &.notification-success {
    border-left-color: #10b981;
    
    .notification-icon {
      color: #10b981;
    }
  }

  &.notification-error {
    border-left-color: #ef4444;
    
    .notification-icon {
      color: #ef4444;
    }
  }

  &.notification-warning {
    border-left-color: #f59e0b;
    
    .notification-icon {
      color: #f59e0b;
    }
  }

  &.notification-info {
    border-left-color: #3b82f6;
    
    .notification-icon {
      color: #3b82f6;
    }
  }

  .notification-icon {
    font-size: 20px;
    margin-top: 2px;
  }

  .notification-content {
    flex: 1;

    .notification-title {
      font-size: 14px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 4px 0;
    }

    .notification-message {
      font-size: 13px;
      color: #6b7280;
      margin: 0;
      line-height: 1.4;
    }
  }

  .notification-close {
    background: none;
    border: none;
    cursor: pointer;
    color: #9ca3af;
    font-size: 16px;
    padding: 2px;
    border-radius: 2px;
    transition: all 0.2s;

    &:hover {
      color: #6b7280;
      background: #f3f4f6;
    }
  }
}

// 进度条
.progress-container {
  margin: 20px 0;

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .progress-label {
      font-size: 14px;
      color: #374151;
      font-weight: 500;
    }

    .progress-percent {
      font-size: 12px;
      color: #6b7280;
      font-weight: 600;
    }
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #3b82f6, #8b5cf6);
      border-radius: 4px;
      transition: width 0.3s ease;
      position: relative;

      &::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        background: linear-gradient(
          90deg,
          transparent,
          rgba(255, 255, 255, 0.2),
          transparent
        );
        animation: shimmer 2s infinite;
      }
    }
  }

  .progress-steps {
    margin-top: 20px;
    display: flex;
    gap: 24px;
    overflow-x: auto;
    padding-bottom: 8px;

    .progress-step {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: fit-content;
      
      .step-indicator {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.3s;
      }

      .step-label {
        font-size: 13px;
        font-weight: 500;
        white-space: nowrap;
      }

      &.step-completed {
        .step-indicator {
          background: #10b981;
          color: white;
        }
        .step-label {
          color: #10b981;
        }
      }

      &.step-active {
        .step-indicator {
          background: #3b82f6;
          color: white;
          animation: pulse 2s infinite;
        }
        .step-label {
          color: #3b82f6;
        }
      }

      &.step-pending {
        .step-indicator {
          background: #e5e7eb;
          color: #9ca3af;
        }
        .step-label {
          color: #9ca3af;
        }
      }
    }
  }
}

// 骨架屏
.skeleton-container {
  .skeleton-item {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;

    .skeleton-avatar {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite;
    }

    .skeleton-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;

      .skeleton-line {
        height: 16px;
        border-radius: 4px;
        background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s infinite;

        &.skeleton-title {
          height: 20px;
          width: 60%;
        }

        &.skeleton-subtitle {
          width: 40%;
        }

        &.skeleton-text {
          width: 80%;
        }
      }
    }
  }
}

// 过渡动画
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}

.fade-scale-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.slide-notification-enter-active {
  transition: all 0.3s ease;
}

.slide-notification-leave-active {
  transition: all 0.3s ease;
}

.slide-notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.slide-notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.slide-notification-move {
  transition: transform 0.3s ease;
}

// 关键帧动画
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes skeleton-loading {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

// 响应式调整
@media (max-width: 768px) {
  .notifications {
    left: 16px;
    right: 16px;
    top: 16px;
    max-width: none;
  }

  .notification {
    min-width: unset;
  }

  .progress-steps {
    gap: 16px;
    
    .progress-step {
      flex-direction: column;
      text-align: center;
      gap: 4px;
      
      .step-indicator {
        width: 28px;
        height: 28px;
        font-size: 12px;
      }
      
      .step-label {
        font-size: 11px;
      }
    }
  }
}
</style>
