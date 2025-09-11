/**
 * 工作流服务API类 - 统一管理工作流相关的API调用
 */

import type { BaseApi } from '../base'
import { smartApiCall } from '../index'
import type {
  WorkflowProject,
  WorkflowStep,
  WorkflowExecuteRequest,
  WorkflowOptions,
  WorkflowStatus,
  WorkflowDebugInfo,
  ExportConfig,
  ExportTask,
  ProjectFile,
  ProjectStats,
  BatchOperationRequest,
  BatchOperationResult,
  WorkflowTemplate,
  WorkflowEvent,
  WorkflowUpdate
} from '../types/workflow'

/**
 * 工作流服务类
 */
export class WorkflowService {
  private api: BaseApi

  constructor(api: BaseApi) {
    this.api = api
  }

  /**
   * 获取所有项目
   */
  async getProjects(
    status?: string,
    limit?: number,
    offset?: number
  ): Promise<{ projects: WorkflowProject[]; total: number }> {
    const params: any = {}
    if (status) params.status = status
    if (limit) params.limit = limit
    if (offset) params.offset = offset
    
    const response = await smartApiCall(api => 
      api.get<{ projects: WorkflowProject[]; total: number }>('/api/workflow/projects', params)
    )
    return response.data!
  }

  /**
   * 获取单个项目
   */
  async getProject(projectId: string): Promise<WorkflowProject> {
    const response = await smartApiCall(api => 
      api.get<WorkflowProject>(`/api/workflow/projects/${projectId}`)
    )
    return response.data!
  }

  /**
   * 创建新项目
   */
  async createProject(
    name: string,
    description?: string,
    metadata?: Record<string, any>
  ): Promise<WorkflowProject> {
    const response = await smartApiCall(api => 
      api.post<WorkflowProject>('/api/workflow/projects', {
        name,
        description,
        metadata
      })
    )
    return response.data!
  }

  /**
   * 更新项目
   */
  async updateProject(
    projectId: string,
    updates: Partial<Pick<WorkflowProject, 'name' | 'description' | 'metadata'>>
  ): Promise<WorkflowProject> {
    const response = await smartApiCall(api => 
      api.put<WorkflowProject>(`/api/workflow/projects/${projectId}`, updates)
    )
    return response.data!
  }

  /**
   * 删除项目
   */
  async deleteProject(projectId: string, force?: boolean): Promise<void> {
    if (force) {
      await smartApiCall(api => 
        api.delete(`/api/workflow/projects/${projectId}?force=true`)
      )
    }
    else {
      await smartApiCall(api => 
        api.delete(`/api/workflow/projects/${projectId}`)
      )
    }
  }

  /**
   * 执行工作流
   */
  async executeWorkflow(request: WorkflowExecuteRequest): Promise<WorkflowStatus> {
    const response = await smartApiCall(api => 
      api.post<WorkflowStatus>('/api/workflow/execute', request)
    )
    return response.data!
  }

  /**
   * 获取工作流状态
   */
  async getWorkflowStatus(projectId: string): Promise<WorkflowStatus> {
    const response = await smartApiCall(api => 
      api.get<WorkflowStatus>(`/api/workflow/status/${projectId}`)
    )
    return response.data!
  }

  /**
   * 停止工作流
   */
  async stopWorkflow(projectId: string): Promise<void> {
    await smartApiCall(api => 
      api.post(`/api/workflow/stop/${projectId}`)
    )
  }

  /**
   * 重启工作流
   */
  async restartWorkflow(
    projectId: string,
    fromStep?: string,
    options?: WorkflowOptions
  ): Promise<WorkflowStatus> {
    const response = await smartApiCall(api => 
      api.post<WorkflowStatus>(`/api/workflow/restart/${projectId}`, {
        from_step: fromStep,
        options
      })
    )
    return response.data!
  }

  /**
   * 获取工作流步骤
   */
  async getWorkflowSteps(projectId: string): Promise<WorkflowStep[]> {
    const response = await smartApiCall(api => 
      api.get<WorkflowStep[]>(`/api/workflow/steps/${projectId}`)
    )
    return response.data!
  }

  /**
   * 获取单个步骤详情
   */
  async getWorkflowStep(projectId: string, stepId: string): Promise<WorkflowStep> {
    const response = await smartApiCall(api => 
      api.get<WorkflowStep>(`/api/workflow/steps/${projectId}/${stepId}`)
    )
    return response.data!
  }

  /**
   * 重新执行指定步骤
   */
  async retryStep(projectId: string, stepId: string): Promise<WorkflowStep> {
    const response = await smartApiCall(api => 
      api.post<WorkflowStep>(`/api/workflow/retry/${projectId}/${stepId}`)
    )
    return response.data!
  }

  /**
   * 跳过指定步骤
   */
  async skipStep(projectId: string, stepId: string): Promise<WorkflowStep> {
    const response = await smartApiCall(api => 
      api.post<WorkflowStep>(`/api/workflow/skip/${projectId}/${stepId}`)
    )
    return response.data!
  }

  /**
   * 获取调试信息
   */
  async getDebugInfo(projectId: string, stepId?: string): Promise<WorkflowDebugInfo> {
    const params = stepId ? { step_id: stepId } : undefined
    const response = await smartApiCall(api => 
      api.get<WorkflowDebugInfo>(`/api/workflow/debug/${projectId}`, params)
    )
    return response.data!
  }

  /**
   * 导出项目
   */
  async exportProject(
    projectId: string,
    config: ExportConfig
  ): Promise<ExportTask> {
    const response = await smartApiCall(api => 
      api.post<ExportTask>(`/api/workflow/export/${projectId}`, config)
    )
    return response.data!
  }

  /**
   * 获取导出任务列表
   */
  async getExportTasks(projectId?: string): Promise<ExportTask[]> {
    const params = projectId ? { project_id: projectId } : undefined
    const response = await smartApiCall(api => 
      api.get<ExportTask[]>('/api/workflow/exports', params)
    )
    return response.data!
  }

  /**
   * 获取导出任务状态
   */
  async getExportTask(taskId: string): Promise<ExportTask> {
    const response = await smartApiCall(api => 
      api.get<ExportTask>(`/api/workflow/exports/${taskId}`)
    )
    return response.data!
  }

  /**
   * 取消导出任务
   */
  async cancelExportTask(taskId: string): Promise<void> {
    await smartApiCall(api => 
      api.post(`/api/workflow/exports/${taskId}/cancel`)
    )
  }

  /**
   * 下载导出文件
   */
  async downloadExportFile(taskId: string): Promise<string> {
    const response = await smartApiCall(api => 
      api.get<{ download_url: string }>(`/api/workflow/exports/${taskId}/download`)
    )
    return response.data!.download_url
  }

  /**
   * 获取项目文件列表
   */
  async getProjectFiles(projectId: string): Promise<ProjectFile[]> {
    const response = await smartApiCall(api => 
      api.get<ProjectFile[]>(`/api/workflow/files/${projectId}`)
    )
    return response.data!
  }

  /**
   * 上传项目文件
   */
  async uploadProjectFile(
    projectId: string,
    file: File,
    type?: string
  ): Promise<ProjectFile> {
    const formData = new FormData()
    formData.append('file', file)
    if (type) formData.append('type', type)

    const response = await smartApiCall(api => 
      api.post<ProjectFile>(`/api/workflow/files/${projectId}`, formData)
    )
    return response.data!
  }

  /**
   * 删除项目文件
   */
  async deleteProjectFile(projectId: string, filename: string): Promise<void> {
    await smartApiCall(api => 
      api.delete(`/api/workflow/files/${projectId}/${filename}`)
    )
  }

  /**
   * 获取项目统计信息
   */
  async getProjectStats(projectId: string): Promise<ProjectStats> {
    const response = await smartApiCall(api => 
      api.get<ProjectStats>(`/api/workflow/stats/${projectId}`)
    )
    return response.data!
  }

  /**
   * 批量操作项目
   */
  async batchOperation(request: BatchOperationRequest): Promise<BatchOperationResult> {
    const response = await smartApiCall(api => 
      api.post<BatchOperationResult>('/api/workflow/batch', request)
    )
    return response.data!
  }

  /**
   * 获取工作流模板
   */
  async getWorkflowTemplates(): Promise<WorkflowTemplate[]> {
    const response = await smartApiCall(api => 
      api.get<WorkflowTemplate[]>('/api/workflow/templates')
    )
    return response.data!
  }

  /**
   * 从模板创建项目
   */
  async createProjectFromTemplate(
    templateId: string,
    name: string,
    options?: Record<string, any>
  ): Promise<WorkflowProject> {
    const response = await smartApiCall(api => 
      api.post<WorkflowProject>('/api/workflow/templates/create', {
        template_id: templateId,
        name,
        options
      })
    )
    return response.data!
  }

  /**
   * 获取工作流事件
   */
  async getWorkflowEvents(
    projectId: string,
    eventType?: string,
    limit?: number
  ): Promise<WorkflowEvent[]> {
    const params: any = {}
    if (eventType) params.event_type = eventType
    if (limit) params.limit = limit
    
    const response = await smartApiCall(api => 
      api.get<WorkflowEvent[]>(`/api/workflow/events/${projectId}`, params)
    )
    return response.data!
  }

  /**
   * 清理项目文件
   */
  async cleanupProject(
    projectId: string,
    options?: {
      keep_logs?: boolean
      keep_outputs?: boolean
      keep_source?: boolean
    }
  ): Promise<{ cleaned_files: number; freed_space: number }> {
    const response = await smartApiCall(api => 
      api.post<{ cleaned_files: number; freed_space: number }>(
        `/api/workflow/cleanup/${projectId}`,
        options
      )
    )
    return response.data!
  }

  /**
   * 检查工作流服务健康状态
   */
  async healthCheck(): Promise<boolean> {
    try {
      await smartApiCall(api => 
        api.get('/api/workflow/health')
      )
      return true
    }
    catch {
      return false
    }
  }

  /**
   * 获取系统信息
   */
  async getSystemInfo(): Promise<any> {
    const response = await smartApiCall(api => 
      api.get('/api/workflow/system-info')
    )
    return response.data!
  }

  /**
   * 获取实时进度更新（WebSocket连接）
   */
  createProgressSubscription(
    projectId: string,
    onUpdate: (update: WorkflowUpdate) => void,
    onError?: (error: Error) => void
  ): () => void {
    // WebSocket implementation placeholder
    // 实际实现需要WebSocket连接
    
    // 模拟订阅，实际实现需要WebSocket
    const interval = setInterval(() => {
      // 可以在这里轮询状态更新
      // 实际应该通过WebSocket接收更新
    }, 1000)
    
    // 防止未使用参数警告
    void onUpdate
    void onError
    
    return () => {
      clearInterval(interval)
      // WebSocket cleanup logic would go here
    }
  }
}

/**
 * 创建工作流服务实例
 */
export function createWorkflowService(api: BaseApi): WorkflowService {
  return new WorkflowService(api)
}
