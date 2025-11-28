/**
 * 用户认证状态管理
 * 管理登录状态、用户信息、Token
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { API_FALLBACK_URL } from '@/config/api'

// 认证 API 使用 Flask 后端地址（5000端口）
const AUTH_API_BASE = API_FALLBACK_URL

/**
 * 用户信息类型
 */
export interface UserInfo {
  id: string
  username: string
  role: 'admin' | 'user'
  created_at?: string
  last_login?: string
}

/**
 * 登录响应类型
 */
export interface LoginResponse {
  success: boolean
  message?: string
  data?: {
    token: string
    user: UserInfo
  }
}

// localStorage 存储键名
const STORAGE_KEYS = {
  TOKEN: 'auth_token',
  USER_INFO: 'user_info',
} as const

export const useAuthStore = defineStore('auth', () => {
  // ==================== State ====================
  
  /** 访问令牌 */
  const token = ref<string | null>(localStorage.getItem(STORAGE_KEYS.TOKEN))
  
  /** 用户信息 - 从 localStorage 初始化 */
  const storedUserInfo = localStorage.getItem(STORAGE_KEYS.USER_INFO)
  let initialUserInfo: UserInfo | null = null
  if (storedUserInfo) {
    try {
      initialUserInfo = JSON.parse(storedUserInfo)
    }
    catch {
      initialUserInfo = null
    }
  }
  const userInfo = ref<UserInfo | null>(initialUserInfo)
  
  /** 登录加载状态 */
  const isLoading = ref(false)
  
  /** 错误信息 */
  const errorMessage = ref<string | null>(null)

  // ==================== Getters ====================
  
  /** 是否已登录 */
  const isLoggedIn = computed(() => !!token.value)
  
  /** 是否是管理员 */
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  
  /** 用户名 */
  const username = computed(() => userInfo.value?.username || '')
  
  /** 用户ID */
  const userId = computed(() => userInfo.value?.id || 'anonymous')

  // ==================== Actions ====================
  
  /**
   * 设置认证信息
   */
  function setAuth(authToken: string, user: UserInfo) {
    token.value = authToken
    userInfo.value = user
    
    // 持久化存储
    localStorage.setItem(STORAGE_KEYS.TOKEN, authToken)
    localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(user))
    
    errorMessage.value = null
  }
  
  /**
   * 清除认证信息
   */
  function clearAuth() {
    token.value = null
    userInfo.value = null
    
    // 清除存储
    localStorage.removeItem(STORAGE_KEYS.TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER_INFO)
  }
  
  /**
   * 用户登录
   */
  async function login(username: string, password: string): Promise<boolean> {
    isLoading.value = true
    errorMessage.value = null
    
    try {
      const response = await fetch(`${AUTH_API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })
      
      const result: LoginResponse = await response.json()
      
      if (result.success && result.data) {
        setAuth(result.data.token, result.data.user)
        return true
      }
      
      errorMessage.value = result.message || '登录失败'
      return false
    }
    catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '网络错误，请稍后重试'
      return false
    }
    finally {
      isLoading.value = false
    }
  }
  
  /**
   * 用户登出
   */
  async function logout(): Promise<void> {
    try {
      // 调用后端登出接口
      if (token.value) {
        await fetch(`${AUTH_API_BASE}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token.value}`,
          },
        })
      }
    }
    catch {
      // 忽略登出错误
    }
    finally {
      clearAuth()
    }
  }
  
  /**
   * 刷新用户信息
   */
  async function refreshUserInfo(): Promise<boolean> {
    if (!token.value) {
      return false
    }
    
    try {
      const response = await fetch(`${AUTH_API_BASE}/api/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${token.value}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          userInfo.value = result.data
          localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(result.data))
          return true
        }
      }
      
      // Token 无效，清除认证
      if (response.status === 401) {
        clearAuth()
      }
      
      return false
    }
    catch {
      return false
    }
  }
  
  /**
   * 修改密码
   */
  async function changePassword(oldPassword: string, newPassword: string): Promise<{ success: boolean, message: string }> {
    if (!token.value) {
      return { success: false, message: '请先登录' }
    }
    
    try {
      const response = await fetch(`${AUTH_API_BASE}/api/auth/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token.value}`,
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        }),
      })
      
      const result = await response.json()
      return {
        success: result.success,
        message: result.message || (result.success ? '密码修改成功' : '密码修改失败'),
      }
    }
    catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : '网络错误',
      }
    }
  }
  
  /**
   * 检查 Token 是否有效
   */
  async function checkTokenValidity(): Promise<boolean> {
    if (!token.value) {
      return false
    }
    
    return await refreshUserInfo()
  }
  
  /**
   * 初始化认证状态（应用启动时调用）
   */
  async function initAuth(): Promise<void> {
    // 如果有存储的 Token，验证其有效性
    if (token.value) {
      const isValid = await checkTokenValidity()
      if (!isValid) {
        // Token 无效，清除认证但不阻止应用启动
        // eslint-disable-next-line no-console
        console.log('🔐 存储的 Token 已失效，已清除')
      }
    }
  }

  return {
    // State
    token,
    userInfo,
    isLoading,
    errorMessage,
    
    // Getters
    isLoggedIn,
    isAdmin,
    username,
    userId,
    
    // Actions
    setAuth,
    clearAuth,
    login,
    logout,
    refreshUserInfo,
    changePassword,
    checkTokenValidity,
    initAuth,
  }
})
