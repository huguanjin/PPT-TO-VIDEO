/**
 * 工作流相关的TypeScript类型定义
 */

/**
 * 工作流项目信息
 */
export interface WorkflowProject {
  id: string
  name: string
  description?: string
  status: 'created' | 'processing' | 'completed' | 'error' | 'cancelled'
  created_at: string
  updated_at: string
  progress: number
  total_steps: number
  current_step: number
  current_step_name?: string
  error_message?: string
  metadata?: Record<string, any>
}

/**
 * 工作流步骤定义
 */
export interface WorkflowStep {
  id: string
  name: string
  description?: string
  status: 'pending' | 'running' | 'completed' | 'error' | 'skipped'
  progress: number
  start_time?: string
  end_time?: string
  error_message?: string
  input_data?: any
  output_data?: any
  logs?: string[]
}

/**
 * 工作流执行请求
 */
export interface WorkflowExecuteRequest {
  project_id: string
  steps?: string[]
  options?: WorkflowOptions
  force_restart?: boolean
}

/**
 * 工作流执行选项
 */
export interface WorkflowOptions {
  skip_completed?: boolean
  auto_retry?: boolean
  max_retries?: number
  retry_delay?: number
  parallel_steps?: boolean
  timeout?: number
  notification?: {
    on_complete?: boolean
    on_error?: boolean
    webhook_url?: string
  }
}

/**
 * 工作流状态
 */
export interface WorkflowStatus {
  project_id: string
  status: WorkflowProject['status']
  progress: number
  current_step: string | null
  steps: WorkflowStep[]
  start_time?: string
  end_time?: string
  total_duration?: number
  estimated_remaining?: number
}

/**
 * 工作流调试信息
 */
export interface WorkflowDebugInfo {
  project_id: string
  step_id?: string
  logs: DebugLog[]
  performance: PerformanceMetrics
  system_info: SystemInfo
}

/**
 * 调试日志
 */
export interface DebugLog {
  timestamp: string
  level: 'debug' | 'info' | 'warning' | 'error'
  message: string
  component?: string
  step_id?: string
  data?: any
}

/**
 * 性能指标
 */
export interface PerformanceMetrics {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_io?: {
    bytes_sent: number
    bytes_received: number
  }
  step_timings: Record<string, number>
  bottlenecks?: string[]
}

/**
 * 系统信息
 */
export interface SystemInfo {
  platform: string
  python_version: string
  memory_total: number
  cpu_count: number
  disk_space: number
  gpu_available: boolean
  gpu_info?: {
    name: string
    memory: number
    compute_capability: string
  }
}

/**
 * 导出配置
 */
export interface ExportConfig {
  format: 'mp4' | 'avi' | 'mov' | 'wmv'
  quality: 'low' | 'medium' | 'high' | 'ultra'
  resolution: '720p' | '1080p' | '1440p' | '4k'
  fps: number
  bitrate?: number
  audio_bitrate?: number
  codec?: string
  audio_codec?: string
  subtitle_embedded?: boolean
  chapter_markers?: boolean
}

/**
 * 导出任务
 */
export interface ExportTask {
  id: string
  project_id: string
  config: ExportConfig
  status: 'pending' | 'preparing' | 'exporting' | 'completed' | 'error' | 'cancelled'
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  file_path?: string
  file_size?: number
  error_message?: string
  estimated_time?: number
  remaining_time?: number
}

/**
 * 项目文件信息
 */
export interface ProjectFile {
  name: string
  path: string
  size: number
  type: 'ppt' | 'audio' | 'video' | 'subtitle' | 'config' | 'log' | 'other'
  created_at: string
  modified_at: string
  checksum?: string
}

/**
 * 项目统计信息
 */
export interface ProjectStats {
  total_files: number
  total_size: number
  slide_count: number
  audio_duration: number
  video_duration: number
  subtitle_count: number
  processing_time: number
  export_count: number
  last_export?: string
}

/**
 * 批量操作请求
 */
export interface BatchOperationRequest {
  project_ids: string[]
  operation: 'export' | 'delete' | 'restart' | 'cancel'
  options?: any
}

/**
 * 批量操作结果
 */
export interface BatchOperationResult {
  total: number
  success: number
  failed: number
  results: Array<{
    project_id: string
    success: boolean
    error?: string
    data?: any
  }>
}

/**
 * 工作流模板
 */
export interface WorkflowTemplate {
  id: string
  name: string
  description?: string
  steps: WorkflowStepTemplate[]
  default_options: WorkflowOptions
  category: string
  tags: string[]
  created_at: string
  usage_count: number
}

/**
 * 工作流步骤模板
 */
export interface WorkflowStepTemplate {
  id: string
  name: string
  description?: string
  type: string
  config: Record<string, any>
  dependencies: string[]
  optional: boolean
  retry_config?: {
    max_retries: number
    retry_delay: number
    backoff_factor: number
  }
}

/**
 * 工作流事件
 */
export interface WorkflowEvent {
  id: string
  project_id: string
  event_type: 'step_started' | 'step_completed' | 'step_failed' | 'project_completed' | 'project_failed'
  timestamp: string
  data: any
  step_id?: string
}

/**
 * 实时更新数据
 */
export interface WorkflowUpdate {
  type: 'progress' | 'status' | 'log' | 'error'
  project_id: string
  step_id?: string
  data: any
  timestamp: string
}
