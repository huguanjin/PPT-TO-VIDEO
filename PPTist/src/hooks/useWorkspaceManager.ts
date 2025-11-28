/**
 * 工作空间管理器
 * 支持单一工作区模式和智能归档功能
 */

import { ref, computed } from 'vue'
import { useSlidesStore } from '@/store'

export interface ArchiveItem {
  name: string
  project_name: string
  archived_at: string
  slide_count: number
  has_video: boolean
  folder_name: string
  size_mb: number
}

export interface WorkspaceData {
  title?: string
  slides?: string
  last_modified?: string
}

// API基础URL - 使用环境变量
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
const API_BASE = `${API_BASE_URL}/api/workspace`

// 获取认证头
const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const token = localStorage.getItem('auth_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

// API请求封装 - 带认证
const api = {
  async get(url: string) {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    return response.json()
  },

  async post(url: string, data?: any) {
    const response = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    return response.json()
  },

  async delete(url: string, data?: any) {
    const response = await fetch(`${API_BASE}${url}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    return response.json()
  }
}

export const useWorkspaceManager = () => {
  const slidesStore = useSlidesStore()
  
  // 响应式状态
  const isLoading = ref(false)
  const archives = ref<ArchiveItem[]>([])
  const lastSaved = ref<Date | null>(null)
  const hasUnsavedChanges = ref(false)
  
  // 计算属性
  const currentTitle = computed(() => slidesStore.title)
  const workspaceStatus = computed(() => {
    if (isLoading.value) return '处理中...'
    if (hasUnsavedChanges.value) return '未保存'
    if (lastSaved.value) {
      const diff = Date.now() - lastSaved.value.getTime()
      if (diff < 60000) return '刚刚保存'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前保存`
      return `${Math.floor(diff / 3600000)}小时前保存`
    }
    return '已保存'
  })
  
  // 初始化工作空间
  const initializeWorkspace = async (): Promise<boolean> => {
    try {
      isLoading.value = true
      
      // eslint-disable-next-line no-console
      console.log('🔄 [Workspace] 正在初始化工作空间...')
      
      // 检查当前工作区是否有内容
      // eslint-disable-next-line no-console
      console.log('🔄 [Workspace] 调用 api.get(/check)...')
      const checkResult = await api.get('/check')
      // eslint-disable-next-line no-console
      console.log('🔄 [Workspace] /check 返回:', checkResult)
      const hasContent = checkResult.exists
      
      // eslint-disable-next-line no-console
      console.log('✅ [Workspace] 检查完成, hasContent:', hasContent)
      
      if (hasContent) {
        // 加载现有内容
        // eslint-disable-next-line no-console
        console.log('🔄 [Workspace] 调用 loadWorkspaceContent()...')
        await loadWorkspaceContent()
        // eslint-disable-next-line no-console
        console.log('✅ [Workspace] 已加载现有工作空间内容')
      }
      else {
        // 创建默认内容
        await createDefaultContent()
        // eslint-disable-next-line no-console
        console.log('✅ [Workspace] 已创建默认工作空间内容')
      }
      
      // 加载归档列表
      await loadArchiveList()
      // eslint-disable-next-line no-console
      console.log('✅ [Workspace] 归档列表加载完成')
      
      // 设置自动保存
      setupAutoSave()
      
      // eslint-disable-next-line no-console
      console.log('✅ [Workspace] 初始化完成')
      
      return true
      
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('❌ [Workspace] 初始化失败:', error)
      return false
    }
    finally {
      isLoading.value = false
    }
  }
  
  // 加载工作空间内容
  const loadWorkspaceContent = async (): Promise<void> => {
    try {
      // eslint-disable-next-line no-console
      console.log('🔄 [Workspace] loadWorkspaceContent - 调用 api.get(/load)...')
      const response = await api.get('/load')
      // eslint-disable-next-line no-console
      console.log('🔄 [Workspace] loadWorkspaceContent - /load 返回:', response)
      
      if (response.success) {
        const { slides, title, last_modified } = response
        
        if (slides) {
          try {
            const slidesData = typeof slides === 'string' ? JSON.parse(slides) : slides
            if (slidesData && slidesData.length > 0) {
              slidesStore.setSlides(slidesData)
            }
            else {
              // 创建默认slide
              const defaultSlide = {
                id: 'slide_' + Date.now(),
                elements: [],
                remark: ''
              }
              slidesStore.setSlides([defaultSlide])
            }
          }
          catch (e) {
            // 解析slides数据失败，创建默认slide
            const defaultSlide = {
              id: 'slide_' + Date.now(),
              elements: [],
              remark: ''
            }
            slidesStore.setSlides([defaultSlide])
          }
        }
        else {
          // 没有slides数据，创建默认slide
          const defaultSlide = {
            id: 'slide_' + Date.now(),
            elements: [],
            remark: ''
          }
          slidesStore.setSlides([defaultSlide])
        }
        
        if (title) {
          slidesStore.setTitle(title)
        }
        
        if (last_modified) {
          lastSaved.value = new Date(last_modified)
        }
        
        hasUnsavedChanges.value = false
      }
      
    }
    catch (error) {
      // 加载工作空间内容失败
    }
  }
  
  // 创建默认内容
  const createDefaultContent = async (): Promise<void> => {
    const defaultTitle = '我的演示文稿'
    slidesStore.setTitle(defaultTitle)
    
    // 确保有默认slide
    if (!slidesStore.slides || slidesStore.slides.length === 0) {
      // 创建一个默认的空白slide
      const defaultSlide = {
        id: 'slide_' + Date.now(),
        elements: [],
        remark: ''
      }
      slidesStore.setSlides([defaultSlide])
      slidesStore.updateSlideIndex(0)
    }
    
    await saveWorkspace()
  }
  
  // 保存工作空间
  const saveWorkspace = async (): Promise<boolean> => {
    try {
      const slides = slidesStore.slides || []
      const title = slidesStore.title || '我的演示文稿'
      
      const response = await api.post('/save', {
        slides: JSON.stringify(slides),
        title: title
      })
      
      if (response.success) {
        lastSaved.value = new Date()
        hasUnsavedChanges.value = false
        return true
      }
      
      return false
      
    }
    catch (error) {
      return false
    }
  }
  
  // 归档当前项目
  const archiveProject = async (archiveName?: string): Promise<boolean> => {
    try {
      isLoading.value = true
      
      const name = archiveName || slidesStore.title || '未命名项目'
      
      if (name === '未命名项目' || !name.trim()) {
        throw new Error('请先为演示文稿设置名称后再归档')
      }
      
      // 先保存当前工作
      await saveWorkspace()
      
      // 执行归档
      const response = await api.post('/archive', {
        archive_name: name.trim()
      })
      
      if (response.success) {
        // 创建新的默认内容
        await createDefaultContent()
        await loadArchiveList()
        
        return true
      }
      
      throw new Error(response.message || '归档失败')
      
    }
    finally {
      isLoading.value = false
    }
  }
  
  // 加载归档列表
  const loadArchiveList = async (): Promise<void> => {
    try {
      const response = await api.get('/archives')
      if (response.success) {
        archives.value = response.archives || []
      }
    }
    catch (error) {
      // 忽略错误
    }
  }
  
  // 恢复归档
  const restoreArchive = async (folderName: string): Promise<boolean> => {
    try {
      isLoading.value = true
      
      const response = await api.post('/restore', {
        folder_name: folderName
      })
      
      if (response.success) {
        await loadWorkspaceContent()
        return true
      }
      
      throw new Error(response.message || '恢复失败')
      
    }
    finally {
      isLoading.value = false
    }
  }
  
  // 删除归档
  const deleteArchive = async (folderName: string): Promise<boolean> => {
    try {
      isLoading.value = true
      
      const response = await api.delete('/delete', {
        folder_name: folderName
      })
      
      if (response.success) {
        await loadArchiveList()
        return true
      }
      
      throw new Error(response.message || '删除失败')
      
    }
    finally {
      isLoading.value = false
    }
  }
  
  // 设置自动保存
  const setupAutoSave = (): void => {
    let autoSaveTimer: number | null = null
    
    // 监听store变化
    slidesStore.$subscribe(() => {
      hasUnsavedChanges.value = true
      
      // 清除之前的定时器
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer)
      }
      
      // 设置新的自动保存定时器（5秒后保存）
      autoSaveTimer = setTimeout(() => {
        saveWorkspace()
      }, 5000)
    })
    
    // 页面卸载前保存
    window.addEventListener('beforeunload', (event) => {
      if (hasUnsavedChanges.value) {
        event.preventDefault()
        event.returnValue = '您有未保存的更改，确定要离开吗？'
        saveWorkspace() // 尝试快速保存
      }
    })
  }
  
  // 标记有未保存的更改
  const markUnsaved = (): void => {
    hasUnsavedChanges.value = true
  }
  
  // 格式化时间
  const formatTime = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    
    return date.toLocaleDateString()
  }
  
  return {
    // 状态
    isLoading: computed(() => isLoading.value),
    currentTitle,
    archives: computed(() => archives.value),
    workspaceStatus,
    hasUnsavedChanges: computed(() => hasUnsavedChanges.value),
    
    // 方法
    initializeWorkspace,
    saveWorkspace,
    archiveProject,
    restoreArchive,
    deleteArchive,
    loadArchiveList,
    markUnsaved,
    formatTime
  }
}
