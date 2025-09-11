// 项目管理组合式函数
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useSlidesStore } from '@/store'
import message from '@/utils/message'
import { apiRequest, API_ENDPOINTS } from '@/config/api'

interface ProjectInfo {
  project_name: string
  id: string
  title: string
  created_at: string
  updated_at: string
  isDefault: boolean
  // 添加缺失的属性
  project_id?: string
  description?: string
  slides_count?: number
  workflow_count?: number
  last_workflow_status?: string
}

export function useProjectManager() {
  const slidesStore = useSlidesStore()
  const { title, slides, theme, viewportSize, viewportRatio } = storeToRefs(slidesStore)

  const currentProject = ref<ProjectInfo | null>(null)
  const projects = ref<ProjectInfo[]>([])
  const isLoading = ref(false)
  const isAutoSaving = ref(false)
  const isRestoring = ref(false)
  const lastSaveTime = ref<number | null>(null)
  
  const autoSaveConfig = ref({
    enabled: false,
    interval: 120000,
    onSlideChange: true,
    onContentChange: true
  })

  const hasUnsavedChanges = computed(() => {
    if (!currentProject.value || !lastSaveTime.value) return false
    
    // 检查是否有修改
    const currentTime = Date.now()
    const timeSinceLastSave = currentTime - lastSaveTime.value
    
    // 如果最近没有保存过，认为有未保存的更改
    return timeSinceLastSave > 5000 // 5秒内的修改认为是未保存的
  })

  const isProjectActive = computed(() => currentProject.value !== null)

  // 初始化项目
  const initializeProject = async (projectName = 'default_project') => {
    try {
      isRestoring.value = true
      
      // 尝试从localStorage获取当前项目ID
      const savedProjectId = localStorage.getItem('currentProjectId')
      // 验证savedProjectId是否是有效的项目名称（不是 'true', 'false', null 等）
      const isValidProjectId = savedProjectId && 
                              savedProjectId !== 'true' && 
                              savedProjectId !== 'false' && 
                              savedProjectId !== 'null' && 
                              savedProjectId !== 'undefined'
      const targetProject = isValidProjectId ? savedProjectId : projectName
      
      // eslint-disable-next-line no-console
      console.log('🔄 正在初始化项目:', targetProject)
      
      // 尝试加载项目
      const loaded = await loadProject(targetProject)
      
      if (loaded) {
        // eslint-disable-next-line no-console
        console.log('✅ 项目恢复成功:', targetProject)
        return true
      }
      
      // eslint-disable-next-line no-console
      console.log('📝 项目不存在，将创建新项目:', targetProject)
      return false
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('❌ 项目初始化失败:', error)
      return false
    }
    finally {
      isRestoring.value = false
    }
  }

  // 创建项目
  const createProject = async (projectName?: string, projectData?: any) => {
    try {
      isLoading.value = true
      
      const name = projectName || `project_${Date.now()}`
      
      const payload = {
        project_name: name,
        title: projectData?.title || title.value || '未命名演示文稿',
        slides_data: projectData?.slides_data || {
          slides: slides.value,
          theme: theme.value,
          viewportSize: viewportSize.value,
          viewportRatio: viewportRatio.value
        }
      }

      const response = await apiRequest(API_ENDPOINTS.PROJECT.CREATE, {
        method: 'POST',
        body: JSON.stringify(payload)
      })

      if (response.success) {
        currentProject.value = {
          project_name: name,
          id: name,
          title: payload.title,
          created_at: response.data.created_at,
          updated_at: response.data.updated_at,
          isDefault: name === 'default_project'
        }
        
        // 记录当前项目ID
        localStorage.setItem('currentProjectId', name)
        lastSaveTime.value = Date.now()
        
        message.success('项目创建成功')
        return response.data
      }

      throw new Error(response.message || '创建项目失败')
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('创建项目失败:', error)
      message.error('创建项目失败')
      throw error
    }
    finally {
      isLoading.value = false
    }
  }

  // 保存项目
  const saveProject = async (projectName?: string, showMessage = true) => {
    try {
      isAutoSaving.value = true
      
      const targetProject = projectName || currentProject.value?.project_name || 'default_project'
      
      const payload = {
        project_name: targetProject,
        title: title.value || '未命名演示文稿',
        slides_data: {
          slides: slides.value,
          theme: theme.value,
          viewportSize: viewportSize.value,
          viewportRatio: viewportRatio.value
        }
      }

      const response = await apiRequest(API_ENDPOINTS.PROJECT.UPDATE(targetProject), {
        method: 'PUT',
        body: JSON.stringify(payload)
      })

      if (response.success) {
        // 更新当前项目信息
        currentProject.value = {
          project_name: targetProject,
          id: targetProject,
          title: payload.title,
          created_at: response.data.created_at,
          updated_at: response.data.updated_at,
          isDefault: targetProject === 'default_project'
        }
        
        // 记录当前项目ID
        localStorage.setItem('currentProjectId', targetProject)
        lastSaveTime.value = Date.now()
        
        if (showMessage) {
          message.success('项目保存成功')
        }
        
        // eslint-disable-next-line no-console
        console.log('✅ 项目保存成功:', targetProject)
        return response.data
      }

      throw new Error(response.message || '保存项目失败')
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('保存项目失败:', error)
      if (showMessage) {
        message.error('保存项目失败')
      }
      throw error
    }
    finally {
      isAutoSaving.value = false
    }
  }

  // 加载项目
  const loadProject = async (projectName?: string) => {
    try {
      isLoading.value = true
      
      const targetProject = projectName || currentProject.value?.project_name || 'default_project'
      
      const response = await apiRequest(API_ENDPOINTS.PROJECT.GET(targetProject), {
        method: 'GET'
      })
      
      if (response.success && response.data) {
        const projectData = response.data
        
        // 更新当前项目信息
        currentProject.value = {
          project_name: targetProject,
          id: targetProject,
          title: projectData.title || projectData.import_info?.title || '未命名演示文稿',
          created_at: projectData.created_at,
          updated_at: projectData.updated_at,
          isDefault: targetProject === 'default_project'
        }
        
        // 恢复slides数据到store
        if (projectData.slides_data && typeof projectData.slides_data === 'object') {
          const slidesData = projectData.slides_data
          
          // 更新slides store
          if (slidesData.slides && Array.isArray(slidesData.slides)) {
            // 过滤掉任何undefined或null元素，确保数据安全
            const validSlides = slidesData.slides.filter((slide: any) => slide && typeof slide === 'object' && slide.id)
            if (validSlides.length > 0) {
              slidesStore.setSlides(validSlides)
            }
            else {
              // 如果没有有效的slides，不要设置空数组，让默认数据继续存在
              // eslint-disable-next-line no-console
              console.warn('⚠️ 项目中没有有效的slides数据，保持当前数据')
              return true // 仍然算作成功，避免覆盖默认数据
            }
          }
          else {
            // 如果slides_data存在但slides数组无效，也不要覆盖默认数据
            // eslint-disable-next-line no-console
            console.warn('⚠️ slides_data存在但slides数组无效，保持当前数据')
            return true
          }
          
          // 只有当slides成功设置后，才设置其他属性
          if (slidesData.theme) {
            slidesStore.setTheme(slidesData.theme)
          }
          
          if (slidesData.viewportSize) {
            slidesStore.setViewportSize(slidesData.viewportSize)
          }
          
          if (slidesData.viewportRatio) {
            slidesStore.setViewportRatio(slidesData.viewportRatio)
          }
          
          // 更新标题
          if (currentProject.value.title) {
            slidesStore.setTitle(currentProject.value.title)
          }
        }
        else {
          // 项目存在但没有slides_data，这是正常情况（项目刚创建时）
          // eslint-disable-next-line no-console
          console.log('📋 项目存在但暂无PPT数据，保持默认数据')
          
          // 仍然更新项目信息，但不改变slides
          if (currentProject.value.title) {
            slidesStore.setTitle(currentProject.value.title)
          }
        }
        
        // 记录当前项目ID
        localStorage.setItem('currentProjectId', targetProject)
        lastSaveTime.value = new Date(projectData.updated_at || projectData.created_at).getTime()
        
        // eslint-disable-next-line no-console
        console.log('✅ 项目加载成功:', targetProject, projectData)
        return true
      }
      
      throw new Error(response.message || '加载项目失败')
    } 
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('加载项目失败:', error)
      
      // 如果是default_project不存在，这是正常的，不需要报错
      if (projectName === 'default_project' || (!projectName && currentProject.value?.project_name === 'default_project')) {
        // eslint-disable-next-line no-console
        console.log('🔄 默认项目不存在，这是首次使用，将在保存时创建')
        return false
      }
      
      throw error
    } 
    finally {
      isLoading.value = false
    }
  }
  
  const loadProjects = async () => {}
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const deleteProject = async (projectId?: string) => {
    // TODO: 实现项目删除功能
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const duplicateProject = async (projectId?: string, newName?: string) => {
    // TODO: 实现项目复制功能
  }
  
  // 添加缺失的函数
  const startWorkflow = () => {
    // TODO: 实现工作流启动功能
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const showWorkflowHistory = (projectId?: string) => {
    // TODO: 实现工作流历史显示功能
  }
  const formatTime = (timestamp: number | Date) => {
    if (typeof timestamp === 'number') {
      return new Date(timestamp).toLocaleString()
    }
    return timestamp.toLocaleString()
  }
  
  // 自动保存相关功能
  const startAutoSave = () => {
    autoSaveConfig.value.enabled = true
  }
  
  const stopAutoSave = () => {
    autoSaveConfig.value.enabled = false
  }
  
  const toggleAutoSave = () => {
    autoSaveConfig.value.enabled = !autoSaveConfig.value.enabled
  }
  
  // 设置恢复状态
  const setRestoringState = (state: boolean) => {
    isRestoring.value = state
  }

  // 监听slides变化进行自动保存
  watch(
    [slides, theme, viewportSize, viewportRatio],
    async () => {
      if (autoSaveConfig.value.enabled && currentProject.value && !isLoading.value && !isAutoSaving.value) {
        try {
          await saveProject(undefined, false) // 自动保存不显示消息
        }
        catch (error) {
          // eslint-disable-next-line no-console
          console.error('自动保存失败:', error)
        }
      }
    },
    { deep: true, immediate: false }
  )

  return {
    currentProject,
    projects,
    isAutoSaving,
    isLoading,
    isRestoring,
    lastSaveTime,
    autoSaveConfig,
    hasUnsavedChanges,
    isProjectActive,
    initializeProject,
    createProject,
    loadProject,
    saveProject,
    loadProjects,
    deleteProject,
    duplicateProject,
    startAutoSave,
    stopAutoSave,
    toggleAutoSave,
    setRestoringState,
    startWorkflow,
    showWorkflowHistory,
    formatTime
  }
}
