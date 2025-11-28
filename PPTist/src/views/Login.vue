<template>
  <div class="login-container">
    <div class="login-card">
      <!-- Logo 和标题 -->
      <div class="login-header">
        <div class="logo">
          <IconPowerpoint theme="filled" size="48" fill="#5b9bd5" />
        </div>
        <h1 class="title">PPT-TO-VIDEO</h1>
        <p class="subtitle">PPT 转视频工具</p>
      </div>
      
      <!-- 登录表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-item">
          <label class="form-label">用户名</label>
          <div class="input-wrapper">
            <IconUser class="input-icon" />
            <input 
              v-model="username" 
              type="text" 
              class="form-input"
              placeholder="请输入用户名"
              :disabled="isLoading"
              autocomplete="username"
            />
          </div>
        </div>
        
        <div class="form-item">
          <label class="form-label">密码</label>
          <div class="input-wrapper">
            <IconLock class="input-icon" />
            <input 
              v-model="password" 
              :type="showPassword ? 'text' : 'password'" 
              class="form-input"
              placeholder="请输入密码"
              :disabled="isLoading"
              autocomplete="current-password"
            />
            <button 
              type="button" 
              class="password-toggle"
              @click="showPassword = !showPassword"
            >
              <IconPreviewOpen v-if="showPassword" />
              <IconPreviewClose v-else />
            </button>
          </div>
        </div>
        
        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
          <IconCloseOne theme="filled" />
          <span>{{ errorMessage }}</span>
        </div>
        
        <!-- 登录按钮 -->
        <button 
          type="submit" 
          class="login-button"
          :disabled="isLoading || !username || !password"
        >
          <IconLoading v-if="isLoading" class="loading-icon" />
          <span>{{ isLoading ? '登录中...' : '登 录' }}</span>
        </button>
      </form>
      
      <!-- 匿名访问选项 -->
      <div class="anonymous-section">
        <div class="divider">
          <span>或</span>
        </div>
        <button 
          type="button" 
          class="anonymous-button"
          @click="handleAnonymousAccess"
          :disabled="isLoading"
        >
          <IconPeoples />
          <span>以访客身份继续</span>
        </button>
        <p class="anonymous-tip">访客模式下部分功能可能受限</p>
      </div>
      
      <!-- 页脚 -->
      <div class="login-footer">
        <p>© 2025 PPT-TO-VIDEO. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/store/auth'
import { 
  Powerpoint as IconPowerpoint,
  User as IconUser,
  Lock as IconLock,
  PreviewOpen as IconPreviewOpen,
  PreviewCloseOne as IconPreviewClose,
  CloseOne as IconCloseOne,
  Loading as IconLoading,
  Peoples as IconPeoples,
} from '@icon-park/vue-next'

const emit = defineEmits<{
  (e: 'success'): void
  (e: 'anonymous'): void
}>()

const authStore = useAuthStore()
const { isLoading, errorMessage } = storeToRefs(authStore)

// 表单数据
const username = ref('')
const password = ref('')
const showPassword = ref(false)

// 登录处理
async function handleLogin() {
  if (!username.value || !password.value) {
    return
  }
  
  const success = await authStore.login(username.value, password.value)
  if (success) {
    // eslint-disable-next-line no-console
    console.log('🔐 [Login] 登录成功，准备发送 success 事件')
    // 先发送事件，再让响应式系统更新UI
    emit('success')
  }
}

// 匿名访问
function handleAnonymousAccess() {
  authStore.clearAuth()
  emit('anonymous')
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  padding: 40px;
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
  
  .logo {
    width: 80px;
    height: 80px;
    margin: 0 auto 16px;
    background: linear-gradient(135deg, #5b9bd5 0%, #2d6da8 100%);
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(91, 155, 213, 0.4);
    
    :deep(svg) {
      fill: #fff !important;
    }
  }
  
  .title {
    font-size: 28px;
    font-weight: 700;
    color: #333;
    margin: 0 0 8px;
    letter-spacing: 1px;
  }
  
  .subtitle {
    font-size: 14px;
    color: #888;
    margin: 0;
  }
}

.login-form {
  .form-item {
    margin-bottom: 20px;
  }
  
  .form-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: #333;
    margin-bottom: 8px;
  }
  
  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }
  
  .input-icon {
    position: absolute;
    left: 14px;
    color: #aaa;
    font-size: 18px;
    pointer-events: none;
  }
  
  .form-input {
    width: 100%;
    height: 48px;
    padding: 0 44px;
    border: 2px solid #e8e8e8;
    border-radius: 10px;
    font-size: 15px;
    color: #333;
    background: #fafafa;
    transition: all 0.2s;
    
    &:focus {
      outline: none;
      border-color: #667eea;
      background: #fff;
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
    }
    
    &::placeholder {
      color: #bbb;
    }
    
    &:disabled {
      background: #f5f5f5;
      cursor: not-allowed;
    }
  }
  
  .password-toggle {
    position: absolute;
    right: 14px;
    padding: 4px;
    background: none;
    border: none;
    color: #aaa;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      color: #666;
    }
  }
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  color: #ff4d4f;
  font-size: 14px;
  margin-bottom: 20px;
  
  :deep(svg) {
    flex-shrink: 0;
  }
}

.login-button {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .loading-icon {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.anonymous-section {
  margin-top: 24px;
  
  .divider {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    
    &::before,
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: #e8e8e8;
    }
    
    span {
      padding: 0 16px;
      color: #999;
      font-size: 13px;
    }
  }
  
  .anonymous-button {
    width: 100%;
    height: 44px;
    background: #f5f5f5;
    border: 2px solid #e8e8e8;
    border-radius: 10px;
    color: #666;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.2s;
    
    &:hover:not(:disabled) {
      background: #f0f0f0;
      border-color: #d9d9d9;
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .anonymous-tip {
    text-align: center;
    font-size: 12px;
    color: #999;
    margin: 12px 0 0;
  }
}

.login-footer {
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  
  p {
    text-align: center;
    font-size: 12px;
    color: #bbb;
    margin: 0;
  }
}
</style>
