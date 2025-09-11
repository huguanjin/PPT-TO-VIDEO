/**
 * PPT项目数据持久化存储API
 * 提供完整的项目CRUD操作和自动保存功能
 */

import { API_BASE_URL, getApiUrl } from '@/config/api'

// 数据类型定义
export interface PPTSlide {
  id: string
  elements: any[]
  background?: {
    type: 'solid' | 'gradient' | 'image'
    value: string
  }
  width: number
  height: number
}

export interface PPTProject {
  id: string
  name: string
  description?: string
  slides: PPTSlide[]
  theme: {
    backgroundColor: string
    themeColor: string
    fontColor: string
    fontName: string
  }
  viewport: {
    width: number
    height: number
  }
  createdAt: string
  updatedAt: string
  thumbnailUrl?: string
  metadata?: {
    slideCount: number
    author: string
    lastSavedBy: string
    fileSize: number
  }
}

export interface ProjectListItem {
  id: string
  name: string
  description?: string
  thumbnailUrl?: string
  createdAt: string
  updatedAt: string
  slideCount: number
}

export interface APIResponse<T> {
  success: boolean
  data?: T
  message: string
  timestamp: string
}

export interface ProjectStats {
  totalProjects: number
  totalSlides: number
  lastModified: string
  storageUsed: string
}

class PPTStorageAPI {
  private baseURL = `${API_BASE_URL}/api/ppt`

  /**
   * 构造完整的API URL
   */
  private getFullUrl(endpoint: string): string {
    return getApiUrl(`/api/ppt${endpoint}`)
  }

  /**
   * 保存PPT项目
   */
  async saveProject(projectData: Partial<PPTProject>): Promise<APIResponse<any>> {
    const response = await fetch(this.getFullUrl('/save'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(projectData)
    })
    
    if (!response.ok) {
      throw new Error(`保存失败: ${response.statusText}`)
    }
    
    return await response.json()
  }

  /**
   * 加载PPT项目
   */
  async loadProject(projectId: string): Promise<APIResponse<PPTProject>> {
    const response = await fetch(this.getFullUrl(`/load/${projectId}`))
    
    if (response.ok) {
      return await response.json()
    }
    
    throw new Error('加载项目数据失败')
  }

  /**
   * 获取项目列表
   */
  async getProjects(): Promise<ProjectListItem[]> {
    const response = await fetch(this.getFullUrl('/list'))
    
    if (response.ok) {
      const result: APIResponse<ProjectListItem[]> = await response.json()
      return result.data || []
    }
    
    return []
  }

  /**
   * 删除项目
   */
  async deleteProject(projectId: string): Promise<APIResponse<any>> {
    const response = await fetch(this.getFullUrl(`/delete/${projectId}`), {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error(`删除失败: ${response.statusText}`)
    }
    
    return await response.json()
  }

  /**
   * 复制项目
   */
  async duplicateProject(projectId: string, newName?: string): Promise<APIResponse<PPTProject>> {
    const payload: any = { projectId }
    if (newName) {
      payload.newName = newName
    }
    
    const response = await fetch(this.getFullUrl('/duplicate'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) {
      throw new Error(`复制失败: ${response.statusText}`)
    }
    
    return await response.json()
  }

  /**
   * 自动保存（静默保存，不抛出错误）
   */
  async autoSave(projectData: Partial<PPTProject>): Promise<boolean> {
    try {
      const response = await fetch(this.getFullUrl('/auto-save'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(projectData)
      })
      
      return response.ok
    }
    catch (error) {
      return false
    }
  }

  /**
   * 获取项目统计信息
   */
  async getStats(): Promise<ProjectStats | null> {
    try {
      const response = await fetch(this.getFullUrl('/stats'))
      
      if (response.ok) {
        const result: APIResponse<ProjectStats> = await response.json()
        return result.data || null
      }
      
      return null
    }
    catch (error) {
      return null
    }
  }

  /**
   * 上传缩略图
   */
  async uploadThumbnail(projectId: string, thumbnailFile: File): Promise<string | null> {
    try {
      const formData = new FormData()
      formData.append('thumbnail', thumbnailFile)
      
      const response = await fetch(this.getFullUrl(`/thumbnail/${projectId}`), {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const result: APIResponse<{ thumbnailUrl: string }> = await response.json()
        return result.data?.thumbnailUrl || null
      }
      
      return null
    }
    catch (error) {
      return null
    }
  }

  /**
   * 导出项目为JSON文件
   */
  async exportProject(projectId: string): Promise<Blob | null> {
    try {
      const response = await fetch(this.getFullUrl(`/export/${projectId}`))
      
      if (response.ok) {
        return await response.blob()
      }
      
      return null
    }
    catch (error) {
      return null
    }
  }

  /**
   * 从JSON文件导入项目
   */
  async importProject(jsonFile: File, projectName?: string): Promise<APIResponse<PPTProject> | null> {
    try {
      const formData = new FormData()
      formData.append('file', jsonFile)
      if (projectName) {
        formData.append('name', projectName)
      }
      
      const response = await fetch(this.getFullUrl('/import'), {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        return await response.json()
      }
      
      return null
    }
    catch (error) {
      return null
    }
  }

  /**
   * 清理过期的自动保存文件
   */
  async cleanupAutoSaves(olderThanDays: number = 7): Promise<boolean> {
    try {
      const response = await fetch(this.getFullUrl('/cleanup'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ olderThanDays })
      })
      
      return response.ok
    }
    catch (error) {
      return false
    }
  }

  /**
   * 搜索项目
   */
  async searchProjects(query: string): Promise<ProjectListItem[]> {
    try {
      const response = await fetch(this.getFullUrl(`/search?q=${encodeURIComponent(query)}`))
      
      if (response.ok) {
        const result: APIResponse<ProjectListItem[]> = await response.json()
        return result.data || []
      }
      
      return []
    }
    catch (error) {
      return []
    }
  }
}

// 创建单例实例
export const pptStorageAPI = new PPTStorageAPI()

// 自动保存管理器
export class AutoSaveManager {
  private saveTimer: number | null = null
  private readonly saveInterval = 30000 // 30秒自动保存
  private isDirty = false
  private currentProject: Partial<PPTProject> | null = null

  /**
   * 标记数据已修改
   */
  markDirty(projectData: Partial<PPTProject>): void {
    this.isDirty = true
    this.currentProject = projectData
    this.startAutoSave()
  }

  /**
   * 开始自动保存
   */
  private startAutoSave(): void {
    if (this.saveTimer) {
      clearTimeout(this.saveTimer)
    }

    this.saveTimer = window.setTimeout(async () => {
      if (this.isDirty && this.currentProject) {
        const success = await pptStorageAPI.autoSave(this.currentProject)
        if (success) {
          this.isDirty = false
        }
      }
    }, this.saveInterval)
  }

  /**
   * 立即保存
   */
  async saveNow(): Promise<boolean> {
    if (this.currentProject) {
      const success = await pptStorageAPI.autoSave(this.currentProject)
      if (success) {
        this.isDirty = false
        if (this.saveTimer) {
          clearTimeout(this.saveTimer)
          this.saveTimer = null
        }
      }
      return success
    }
    return false
  }

  /**
   * 停止自动保存
   */
  stop(): void {
    if (this.saveTimer) {
      clearTimeout(this.saveTimer)
      this.saveTimer = null
    }
    this.isDirty = false
    this.currentProject = null
  }
}

// 创建自动保存管理器实例
export const autoSaveManager = new AutoSaveManager()

export default pptStorageAPI
