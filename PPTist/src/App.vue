<template>
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
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useScreenStore, useMainStore, useSnapshotStore, useSlidesStore, useWorkflowStore } from '@/store'
import { useWorkspaceManager } from '@/hooks/useWorkspaceManager'
import { LOCALSTORAGE_KEY_DISCARDED_DB } from '@/configs/storage'
import { deleteDiscardedDB } from '@/utils/database'
import { isPC } from '@/utils/common'
import { API_BASE_URL } from '@/config/api'
import api from '@/services'

import Editor from './views/Editor/index.vue'
import Screen from './views/Screen/index.vue'
import Mobile from './views/Mobile/index.vue'
import FullscreenSpin from '@/components/FullscreenSpin.vue'
import WorkflowProgress from '@/components/WorkflowProgress.vue'

const _isPC = isPC()
const appReady = ref(false)

const mainStore = useMainStore()
const slidesStore = useSlidesStore()
const snapshotStore = useSnapshotStore()
const workflowStore = useWorkflowStore()
const workspace = useWorkspaceManager()
const { databaseId } = storeToRefs(mainStore)
const { screening } = storeToRefs(useScreenStore())

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

onMounted(async () => {
  try {
    await deleteDiscardedDB()
    snapshotStore.initSnapshotDatabase()
    
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
    
    // 初始化工作空间管理器
    const workspaceInitialized = await workspace.initializeWorkspace()
    
    if (!workspaceInitialized) {
      // eslint-disable-next-line no-console
      console.warn('工作空间初始化失败，使用默认设置')
      // 加载默认数据
      const defaultSlides = await api.getFileData('slides')
      slidesStore.setSlides(defaultSlides)
    }
    
    appReady.value = true
    // eslint-disable-next-line no-console
    console.log('应用初始化完成')
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('应用初始化失败:', error)
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
