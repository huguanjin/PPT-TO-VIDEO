<template>
  <!-- 登录页面 -->
  <Login 
    v-if="showLogin" 
    @success="handleLoginSuccess"
    @anonymous="handleAnonymousAccess"
  />
  
  <!-- 主应用 -->
  <template v-else>
    <template v-if="appReady">
      <Screen v-if="screening" />
      <Editor v-else-if="_isPC" />
      <Mobile v-else />
    </template>
    <FullscreenSpin tip="数据初始化中，请稍等 ..." v-else  loading :mask="false" />
    
    <!-- 全局工作流进度对话框 - 不受Screen/Editor切换影响 -->
    <WorkflowProgress 
      v-if="workflowStore.showProgress && workflowStore.workflowId"
      :workflowId="workflowStore.workflowId"
      @close="workflowStore.hideWorkflowProgress()"
      @download="handleDownload"
    />
    
    <!-- 用户信息悬浮按钮 -->
    <UserFloatButton v-if="appReady" />
  </template>
</template>

<script lang="ts" setup>
import { onMounted, ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useScreenStore, useMainStore, useSnapshotStore, useSlidesStore, useWorkflowStore, useAuthStore } from '@/store'
import { useWorkspaceManager } from '@/hooks/useWorkspaceManager'
import { LOCALSTORAGE_KEY_DISCARDED_DB } from '@/configs/storage'
import { deleteDiscardedDB } from '@/utils/database'
import { isPC } from '@/utils/common'
import { API_BASE_URL } from '@/config/api'
import api from '@/services'

import Editor from './views/Editor/index.vue'
import Screen from './views/Screen/index.vue'
import Mobile from './views/Mobile/index.vue'
import Login from './views/Login.vue'
import FullscreenSpin from '@/components/FullscreenSpin.vue'
import WorkflowProgress from '@/components/WorkflowProgress.vue'
import UserFloatButton from '@/components/UserFloatButton.vue'

const _isPC = isPC()
const appReady = ref(false)

// 认证相关
const authStore = useAuthStore()
const { isLoggedIn } = storeToRefs(authStore)

// 是否跳过登录（匿名访问模式）
const skipLogin = ref(localStorage.getItem('skip_login') === 'true')

// 是否显示登录页面
const showLogin = computed(() => !isLoggedIn.value && !skipLogin.value)

const mainStore = useMainStore()
const slidesStore = useSlidesStore()
const snapshotStore = useSnapshotStore()
const workflowStore = useWorkflowStore()
const workspace = useWorkspaceManager()
const { databaseId } = storeToRefs(mainStore)
const { screening } = storeToRefs(useScreenStore())

// 登录成功处理
async function handleLoginSuccess() {
  skipLogin.value = false
  localStorage.removeItem('skip_login')
  // eslint-disable-next-line no-console
  console.log('🔐 登录成功:', authStore.username)
  // 重置 appReady 以确保重新初始化
  appReady.value = false
  await initApp()
}

// 匿名访问处理
async function handleAnonymousAccess() {
  skipLogin.value = true
  localStorage.setItem('skip_login', 'true')
  // eslint-disable-next-line no-console
  console.log('👤 以访客身份访问')
  // 重置 appReady 以确保重新初始化
  appReady.value = false
  await initApp()
}

// 处理视频下载
const handleDownload = (projectName: string) => {
  const downloadUrl = `${API_BASE_URL}/api/download/${projectName}/final_video.mp4`
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `${projectName}_final_video.mp4`
  link.click()
  // eslint-disable-next-line no-console
  console.log('📥 [App] 下载视频:', downloadUrl)
}

if (import.meta.env.MODE !== 'development') {
  window.onbeforeunload = () => false
}

// 应用初始化函数
async function initApp() {
  // eslint-disable-next-line no-console
  console.log('🚀 [App] initApp 被调用, appReady =', appReady.value)
  
  if (appReady.value) {
    // eslint-disable-next-line no-console
    console.log('⚠️ [App] appReady 已为 true，跳过初始化')
    return
  }
  
  try {
    // eslint-disable-next-line no-console
    console.log('🚀 [App] 开始初始化应用...')
    
    await deleteDiscardedDB()
    // eslint-disable-next-line no-console
    console.log('✅ [App] 已清理废弃数据库')
    
    // 为调试暴露stores和工作空间管理器
    ;(window as any).__SLIDES_STORE_DEBUG__ = slidesStore
    ;(window as any).__WORKSPACE_MANAGER_DEBUG__ = {
      currentTitle: workspace.currentTitle,
      archives: workspace.archives,
      workspaceStatus: workspace.workspaceStatus,
      isLoading: workspace.isLoading,
      hasUnsavedChanges: workspace.hasUnsavedChanges,
      saveWorkspace: workspace.saveWorkspace,
      archiveProject: workspace.archiveProject,
      initializeWorkspace: workspace.initializeWorkspace
    }
    
    // 初始化工作空间管理器（先加载 slides 数据）
    // eslint-disable-next-line no-console
    console.log('🔄 [App] 准备调用 workspace.initializeWorkspace()...')
    const workspaceInitialized = await workspace.initializeWorkspace()
    // eslint-disable-next-line no-console
    console.log('✅ [App] 工作空间初始化:', workspaceInitialized ? '成功' : '失败')
    
    if (!workspaceInitialized) {
      // eslint-disable-next-line no-console
      console.warn('工作空间初始化失败，使用默认设置')
      // 加载默认数据
      const defaultSlides = await api.getFileData('slides')
      slidesStore.setSlides(defaultSlides)
    }
    
    // 在 slides 加载完成后初始化快照数据库
    await snapshotStore.initSnapshotDatabase()
    // eslint-disable-next-line no-console
    console.log('✅ [App] 快照数据库初始化完成')
    
    appReady.value = true
    // eslint-disable-next-line no-console
    console.log('✅ [App] 应用初始化完成')
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('❌ [App] 应用初始化失败:', error)
    // 初始化失败时也要确保应用能启动，提供最基本的slide
    slidesStore.setSlides([{
      id: 'fallback-slide',
      elements: [],
      background: {
        type: 'solid',
        color: '#ffffff'
      }
    }])
    appReady.value = true
  }
}

onMounted(async () => {
  // 初始化认证状态
  await authStore.initAuth()
  
  // 如果已登录或选择了匿名访问，直接初始化应用
  if (isLoggedIn.value || skipLogin.value) {
    await initApp()
  }
  // 否则显示登录页面，等待用户操作
})

// 监听登录状态变化 - 当用户登录成功后自动初始化应用
watch(isLoggedIn, async (newValue, oldValue) => {
  // eslint-disable-next-line no-console
  console.log('🔄 [App] isLoggedIn 变化:', oldValue, '->', newValue)
  
  // 从未登录变为已登录
  if (newValue && !oldValue) {
    // eslint-disable-next-line no-console
    console.log('🔐 [App] 检测到登录成功，开始初始化应用')
    skipLogin.value = false
    localStorage.removeItem('skip_login')
    appReady.value = false
    await initApp()
  }
})

// 应用注销时向 localStorage 中记录下本次 indexedDB 的数据库ID，用于之后清除数据库
window.addEventListener('beforeunload', () => {
  const discardedDB = localStorage.getItem(LOCALSTORAGE_KEY_DISCARDED_DB)
  const discardedDBList: string[] = discardedDB ? JSON.parse(discardedDB) : []

  discardedDBList.push(databaseId.value)

  const newDiscardedDB = JSON.stringify(discardedDBList)
  localStorage.setItem(LOCALSTORAGE_KEY_DISCARDED_DB, newDiscardedDB)
})
</script>

<style lang="scss">
#app {
  height: 100%;
}
</style>
