/**
 * PPT自动保存功能组合式函数
 */
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'
import { pptStorageAPI, type PPTProject } from '@/api/pptStorage'
import { getAutoSaveConfig, saveAutoSaveConfig, type AutoSaveConfig } from '@/config/autoSaveConfig'
import message from '@/utils/message'

export const useAutoSave = () => {
  const slidesStore = useSlidesStore()
  const { title, theme, slides, viewportSize, viewportRatio } = storeToRefs(slidesStore)
  
  const config = ref<AutoSaveConfig>(getAutoSaveConfig())
  const isAutoSaving = ref(false)
  const lastSaveTime = ref<Date | null>(null)
  const saveTimer = ref<number | null>(null)
  const currentProjectId = ref<string>('')

  // 计算当前项目数据
  const currentProjectData = computed((): Partial<PPTProject> => ({
    id: currentProjectId.value || `auto-${Date.now()}`,
    name: title.value,
    slides: slides.value.map(slide => ({
      id: slide.id,
      elements: slide.elements,
      background: slide.background ? {
        type: slide.background.type === 'image' ? 'image' : 
          slide.background.type === 'gradient' ? 'gradient' : 'solid',
        value: JSON.stringify(slide.background)
      } : undefined,
      width: viewportSize.value * viewportRatio.value,
      height: viewportSize.value
    })),
    theme: {
      backgroundColor: theme.value.backgroundColor,
      themeColor: theme.value.themeColors[0],
      fontColor: theme.value.fontColor,
      fontName: theme.value.fontName
    },
    viewport: {
      width: viewportSize.value * viewportRatio.value,
      height: viewportSize.value
    },
    updatedAt: new Date().toISOString(),
    metadata: {
      slideCount: slides.value.length,
      author: 'PPTist用户',
      lastSavedBy: 'AutoSave',
      fileSize: JSON.stringify(slides.value).length
    }
  }))

  // 手动保存
  const saveProject = async (): Promise<boolean> => {
    try {
      if (!currentProjectData.value.id) {
        currentProjectId.value = `project-${Date.now()}`
      }

      const projectToSave = {
        ...currentProjectData.value,
        id: currentProjectId.value,
        createdAt: currentProjectData.value.createdAt || new Date().toISOString()
      }

      await pptStorageAPI.saveProject(projectToSave)
      lastSaveTime.value = new Date()
      
      if (config.value.showNotification) {
        message.success('项目保存成功')
      }
      
      return true
    }
    catch (error) {
      message.error('保存项目失败，请重试')
      return false
    }
  }

  // 自动保存
  const autoSave = async (): Promise<void> => {
    if (!config.value.enabled || isAutoSaving.value) {
      return
    }

    try {
      isAutoSaving.value = true
      
      if (!currentProjectData.value.id) {
        currentProjectId.value = `auto-${Date.now()}`
      }

      const success = await pptStorageAPI.autoSave(currentProjectData.value)
      
      if (success) {
        lastSaveTime.value = new Date()
        if (config.value.showNotification) {
          message.success('自动保存成功')
        }
      }
    }
    catch (error) {
      // 自动保存失败时静默处理
    }
    finally {
      isAutoSaving.value = false
    }
  }

  // 启动自动保存定时器
  const startAutoSave = (): void => {
    if (saveTimer.value) {
      clearInterval(saveTimer.value)
    }

    if (config.value.enabled && config.value.interval > 0) {
      saveTimer.value = window.setInterval(() => {
        autoSave()
      }, config.value.interval * 60 * 1000) // 转换为毫秒
    }
  }

  // 停止自动保存定时器
  const stopAutoSave = (): void => {
    if (saveTimer.value) {
      clearInterval(saveTimer.value)
      saveTimer.value = null
    }
  }

  // 更新配置
  const updateConfig = (newConfig: Partial<AutoSaveConfig>): void => {
    config.value = { ...config.value, ...newConfig }
    saveAutoSaveConfig(config.value)
    
    // 重启定时器
    stopAutoSave()
    startAutoSave()
  }

  // 加载项目
  const loadProject = async (projectId: string): Promise<boolean> => {
    try {
      const response = await pptStorageAPI.loadProject(projectId)
      
      if (response.success && response.data) {
        const project = response.data
        currentProjectId.value = project.id
        
        // 更新store数据
        slidesStore.setTitle(project.name)
        if (project.slides && project.slides.length > 0) {
          // 这里需要根据PPTist的具体API来更新slides
          // slidesStore.setSlides(project.slides)
        }
        
        lastSaveTime.value = new Date(project.updatedAt)
        message.success('项目加载成功')
        return true
      }
      
      message.error('加载项目失败')
      return false
    }
    catch (error) {
      message.error('加载项目失败，请重试')
      return false
    }
  }

  // 获取项目列表
  const getProjectList = async () => {
    try {
      return await pptStorageAPI.getProjects()
    }
    catch (error) {
      message.error('获取项目列表失败')
      return []
    }
  }

  // 删除项目
  const deleteProject = async (projectId: string): Promise<boolean> => {
    try {
      await pptStorageAPI.deleteProject(projectId)
      message.success('项目删除成功')
      return true
    }
    catch (error) {
      message.error('删除项目失败')
      return false
    }
  }

  // 获取上次保存时间的友好显示
  const lastSaveTimeText = computed(() => {
    if (!lastSaveTime.value) return '尚未保存'
    
    const now = new Date()
    const diff = now.getTime() - lastSaveTime.value.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return '刚刚保存'
    if (minutes < 60) return `${minutes}分钟前保存`
    
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}小时前保存`
    
    const days = Math.floor(hours / 24)
    return `${days}天前保存`
  })

  // 生命周期钩子
  onMounted(() => {
    startAutoSave()
  })

  onUnmounted(() => {
    stopAutoSave()
  })

  return {
    // 状态
    config,
    isAutoSaving,
    lastSaveTime,
    lastSaveTimeText,
    currentProjectId,
    currentProjectData,
    
    // 方法
    saveProject,
    autoSave,
    loadProject,
    getProjectList,
    deleteProject,
    updateConfig,
    startAutoSave,
    stopAutoSave
  }
}
