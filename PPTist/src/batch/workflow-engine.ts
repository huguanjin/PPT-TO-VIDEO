/**
 * 企业级工作流引擎
 * Netflix V2 Phase 6.4 Enterprise Workflow Engine
 */

import { TaskQueue, SimpleTask, TaskStatus, TaskPriority } from './task-queue-simple'

export enum WorkflowStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused'
}

export interface WorkflowStep {
  id: string
  name: string
  type: string
  config: Record<string, any>
  dependencies: string[]
  position: { x: number; y: number }
  condition?: {
    type: 'success' | 'failure' | 'always' | 'custom'
    expression?: string
  }
  timeout?: number
}

export interface WorkflowDefinition {
  id: string
  name: string
  description?: string
  version: string
  status: WorkflowStatus
  
  steps: WorkflowStep[]
  connections: Array<{
    id: string
    from: string
    to: string
    condition?: {
      type: 'success' | 'failure' | 'always' | 'custom'
      expression?: string
    }
  }>
  
  globalConfig: {
    maxConcurrentTasks: number
    globalTimeout?: number
    errorHandling: {
      strategy: 'fail-fast' | 'continue-on-error' | 'manual-intervention'
    }
  }
  
  variables: Record<string, any>
  parameters: Array<{
    name: string
    type: 'string' | 'number' | 'boolean' | 'object'
    required: boolean
    defaultValue?: any
    description?: string
  }>
  
  schedule?: {
    type: 'once' | 'recurring' | 'cron'
    scheduledTime?: Date
    interval?: number
    cronExpression?: string
    enabled: boolean
  }
  
  createdAt: Date
  updatedAt: Date
  createdBy: string
}

export interface WorkflowExecution {
  id: string
  workflowId: string
  status: WorkflowStatus
  
  startTime: Date
  endTime?: Date
  duration?: number
  
  stepResults: Map<string, {
    status: TaskStatus
    startTime: Date
    endTime?: Date
    duration?: number
    output?: any
    error?: any
  }>
  
  variables: Record<string, any>
  outputs: Record<string, any>
  errors: Array<{
    stepId?: string
    message: string
    timestamp: Date
  }>
  
  statistics: {
    totalSteps: number
    completedSteps: number
    failedSteps: number
    skippedSteps: number
  }
}

/**
 * 工作流引擎
 */
export class WorkflowEngine {
  private taskQueue: TaskQueue
  private workflows: Map<string, WorkflowDefinition> = new Map()
  private executions: Map<string, WorkflowExecution> = new Map()
  private isRunning = false
  
  constructor(taskQueue?: TaskQueue) {
    this.taskQueue = taskQueue || new TaskQueue({ maxConcurrentTasks: 10 })
  }
  
  /**
   * 创建工作流
   */
  async createWorkflow(definition: Partial<WorkflowDefinition>): Promise<WorkflowDefinition> {
    const workflow: WorkflowDefinition = {
      id: definition.id || `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: definition.name || '未命名工作流',
      description: definition.description,
      version: definition.version || '1.0.0',
      status: WorkflowStatus.DRAFT,
      
      steps: definition.steps || [],
      connections: definition.connections || [],
      
      globalConfig: {
        maxConcurrentTasks: 5,
        globalTimeout: 3600000, // 1小时
        errorHandling: {
          strategy: 'continue-on-error'
        },
        ...definition.globalConfig
      },
      
      variables: definition.variables || {},
      parameters: definition.parameters || [],
      schedule: definition.schedule,
      
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: definition.createdBy || 'system'
    }
    
    // 验证工作流
    await this.validateWorkflow(workflow)
    
    this.workflows.set(workflow.id, workflow)
    
    console.log(`工作流 ${workflow.name} (${workflow.id}) 已创建`)
    return workflow
  }
  
  /**
   * 更新工作流
   */
  async updateWorkflow(workflowId: string, updates: Partial<WorkflowDefinition>): Promise<WorkflowDefinition | null> {
    const workflow = this.workflows.get(workflowId)
    if (!workflow) {
      return null
    }
    
    // 合并更新
    Object.assign(workflow, updates, { updatedAt: new Date() })
    
    // 重新验证
    await this.validateWorkflow(workflow)
    
    console.log(`工作流 ${workflow.name} (${workflowId}) 已更新`)
    return workflow
  }
  
  /**
   * 删除工作流
   */
  async deleteWorkflow(workflowId: string): Promise<boolean> {
    const workflow = this.workflows.get(workflowId)
    if (!workflow) {
      return false
    }
    
    // 取消正在运行的执行
    for (const execution of this.executions.values()) {
      if (execution.workflowId === workflowId && execution.status === WorkflowStatus.RUNNING) {
        await this.cancelExecution(execution.id)
      }
    }
    
    this.workflows.delete(workflowId)
    
    console.log(`工作流 ${workflow.name} (${workflowId}) 已删除`)
    return true
  }
  
  /**
   * 执行工作流
   */
  async executeWorkflow(workflowId: string, parameters: Record<string, any> = {}): Promise<string> {
    const workflow = this.workflows.get(workflowId)
    if (!workflow) {
      throw new Error(`工作流 ${workflowId} 不存在`)
    }
    
    // 创建执行实例
    const execution: WorkflowExecution = {
      id: `execution_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      workflowId: workflow.id,
      status: WorkflowStatus.RUNNING,
      
      startTime: new Date(),
      
      stepResults: new Map(),
      variables: { ...workflow.variables, ...parameters },
      outputs: {},
      errors: [],
      
      statistics: {
        totalSteps: workflow.steps.length,
        completedSteps: 0,
        failedSteps: 0,
        skippedSteps: 0
      }
    }
    
    this.executions.set(execution.id, execution)
    
    console.log(`开始执行工作流 ${workflow.name} (执行ID: ${execution.id})`)
    
    // 异步执行工作流
    this.runWorkflowExecution(execution, workflow).catch(error => {
      console.error(`工作流执行失败: ${error.message}`)
      execution.status = WorkflowStatus.FAILED
      execution.endTime = new Date()
      execution.duration = execution.endTime.getTime() - execution.startTime.getTime()
      execution.errors.push({
        message: error.message,
        timestamp: new Date()
      })
    })
    
    return execution.id
  }
  
  /**
   * 运行工作流执行
   */
  private async runWorkflowExecution(execution: WorkflowExecution, workflow: WorkflowDefinition): Promise<void> {
    try {
      // 构建执行图
      const executionGraph = this.buildExecutionGraph(workflow)
      
      // 按拓扑顺序执行步骤
      const executionOrder = this.topologicalSort(executionGraph)
      
      for (const stepId of executionOrder) {
        if (execution.status !== WorkflowStatus.RUNNING) {
          break
        }
        
        const step = workflow.steps.find(s => s.id === stepId)
        if (!step) {
          continue
        }
        
        // 检查依赖是否满足
        if (!this.checkStepDependencies(step, execution)) {
          execution.statistics.skippedSteps++
          continue
        }
        
        // 执行步骤
        await this.executeStep(step, execution, workflow)
      }
      
      // 完成执行
      if (execution.status === WorkflowStatus.RUNNING) {
        execution.status = WorkflowStatus.COMPLETED
        execution.endTime = new Date()
        execution.duration = execution.endTime.getTime() - execution.startTime.getTime()
        
        console.log(`工作流执行完成 (${execution.id})，耗时 ${execution.duration}ms`)
      }
      
    } catch (error) {
      throw error
    }
  }
  
  /**
   * 构建执行图
   */
  private buildExecutionGraph(workflow: WorkflowDefinition): Map<string, string[]> {
    const graph = new Map<string, string[]>()
    
    // 初始化所有步骤
    workflow.steps.forEach(step => {
      graph.set(step.id, [])
    })
    
    // 添加连接关系
    workflow.connections.forEach(connection => {
      const dependencies = graph.get(connection.to) || []
      dependencies.push(connection.from)
      graph.set(connection.to, dependencies)
    })
    
    // 添加显式依赖
    workflow.steps.forEach(step => {
      step.dependencies.forEach(depId => {
        const dependencies = graph.get(step.id) || []
        if (!dependencies.includes(depId)) {
          dependencies.push(depId)
        }
        graph.set(step.id, dependencies)
      })
    })
    
    return graph
  }
  
  /**
   * 拓扑排序
   */
  private topologicalSort(graph: Map<string, string[]>): string[] {
    const visited = new Set<string>()
    const visiting = new Set<string>()
    const result: string[] = []
    
    const visit = (nodeId: string) => {
      if (visiting.has(nodeId)) {
        throw new Error(`检测到循环依赖: ${nodeId}`)
      }
      
      if (visited.has(nodeId)) {
        return
      }
      
      visiting.add(nodeId)
      
      const dependencies = graph.get(nodeId) || []
      dependencies.forEach(depId => {
        visit(depId)
      })
      
      visiting.delete(nodeId)
      visited.add(nodeId)
      result.push(nodeId)
    }
    
    Array.from(graph.keys()).forEach(nodeId => {
      if (!visited.has(nodeId)) {
        visit(nodeId)
      }
    })
    
    return result
  }
  
  /**
   * 检查步骤依赖
   */
  private checkStepDependencies(step: WorkflowStep, execution: WorkflowExecution): boolean {
    for (const depId of step.dependencies) {
      const depResult = execution.stepResults.get(depId)
      if (!depResult || depResult.status !== TaskStatus.COMPLETED) {
        return false
      }
    }
    return true
  }
  
  /**
   * 执行步骤
   */
  private async executeStep(
    step: WorkflowStep, 
    execution: WorkflowExecution, 
    workflow: WorkflowDefinition
  ): Promise<void> {
    console.log(`执行步骤: ${step.name} (${step.id})`)
    
    const stepResult = {
      status: TaskStatus.RUNNING,
      startTime: new Date(),
      output: undefined,
      error: undefined
    }
    
    execution.stepResults.set(step.id, stepResult)
    
    try {
      // 创建对应的任务
      const task = this.createTaskFromStep(step, execution, workflow)
      
      // 添加到任务队列
      await this.taskQueue.addTask(task)
      
      // 等待任务完成
      await this.waitForTaskCompletion(task.id)
      
      // 获取任务结果
      const taskResult = this.taskQueue.getTask(task.id)
      
      if (taskResult && 'status' in taskResult && taskResult.status === TaskStatus.COMPLETED) {
        stepResult.status = TaskStatus.COMPLETED
        stepResult.endTime = new Date()
        stepResult.duration = stepResult.endTime.getTime() - stepResult.startTime.getTime()
        stepResult.output = 'output' in taskResult ? taskResult.output : null
        
        execution.statistics.completedSteps++
        
        console.log(`步骤 ${step.name} 执行完成`)
        
      } else {
        throw new Error(`步骤 ${step.name} 执行失败`)
      }
      
    } catch (error) {
      stepResult.status = TaskStatus.FAILED
      stepResult.endTime = new Date()
      stepResult.duration = stepResult.endTime.getTime() - stepResult.startTime.getTime()
      stepResult.error = error instanceof Error ? error.message : '未知错误'
      
      execution.statistics.failedSteps++
      execution.errors.push({
        stepId: step.id,
        message: stepResult.error,
        timestamp: new Date()
      })
      
      console.error(`步骤 ${step.name} 执行失败: ${stepResult.error}`)
      
      // 根据错误处理策略决定是否继续
      if (workflow.globalConfig.errorHandling.strategy === 'fail-fast') {
        execution.status = WorkflowStatus.FAILED
        throw error
      }
    }
  }
  
  /**
   * 从工作流步骤创建任务
   */
  private createTaskFromStep(
    step: WorkflowStep, 
    execution: WorkflowExecution, 
    workflow: WorkflowDefinition
  ): SimpleTask {
    return {
      id: `task_${execution.id}_${step.id}`,
      name: step.name,
      type: step.type,
      status: TaskStatus.PENDING,
      priority: TaskPriority.NORMAL,
      
      inputData: {
        stepConfig: step.config,
        workflowVariables: execution.variables,
        stepId: step.id,
        executionId: execution.id
      },
      
      createdAt: new Date(),
      updatedAt: new Date(),
      
      resourceRequirements: {
        cpu: 1,
        memory: 512,
        storage: 1024
      },
      
      progress: {
        current: 0,
        total: 100,
        percentage: 0
      },
      
      dependencies: step.dependencies.map(depId => `task_${execution.id}_${depId}`),
      
      retryConfig: {
        maxRetries: 3,
        retryDelay: 1000,
        backoffMultiplier: 2,
        maxRetryDelay: 30000,
        strategy: 'exponential',
        retryableErrors: ['NETWORK_ERROR', 'TIMEOUT_ERROR'],
        nonRetryableErrors: ['AUTHENTICATION_ERROR', 'INVALID_INPUT']
      },
      
      tags: ['workflow', workflow.id, execution.id],
      metadata: {
        workflowId: workflow.id,
        executionId: execution.id,
        stepId: step.id
      }
    }
  }
  
  /**
   * 等待任务完成
   */
  private async waitForTaskCompletion(taskId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const checkTask = () => {
        const task = this.taskQueue.getTask(taskId)
        
        if (task && 'status' in task) {
          if (task.status === TaskStatus.COMPLETED) {
            resolve()
          } else if (task.status === TaskStatus.FAILED || task.status === TaskStatus.CANCELLED) {
            reject(new Error(`任务 ${taskId} 失败或被取消`))
          } else {
            // 继续等待
            setTimeout(checkTask, 1000)
          }
        } else {
          // 任务不存在，可能已被清理
          reject(new Error(`任务 ${taskId} 不存在`))
        }
      }
      
      checkTask()
    })
  }
  
  /**
   * 取消工作流执行
   */
  async cancelExecution(executionId: string): Promise<boolean> {
    const execution = this.executions.get(executionId)
    if (!execution || execution.status !== WorkflowStatus.RUNNING) {
      return false
    }
    
    execution.status = WorkflowStatus.CANCELLED
    execution.endTime = new Date()
    execution.duration = execution.endTime.getTime() - execution.startTime.getTime()
    
    // 取消相关的任务
    for (const stepId of execution.stepResults.keys()) {
      const taskId = `task_${executionId}_${stepId}`
      await this.taskQueue.cancelTask(taskId)
    }
    
    console.log(`工作流执行 ${executionId} 已取消`)
    return true
  }
  
  /**
   * 暂停工作流执行
   */
  async pauseExecution(executionId: string): Promise<boolean> {
    const execution = this.executions.get(executionId)
    if (!execution || execution.status !== WorkflowStatus.RUNNING) {
      return false
    }
    
    execution.status = WorkflowStatus.PAUSED
    
    // 暂停相关的任务
    for (const stepId of execution.stepResults.keys()) {
      const taskId = `task_${executionId}_${stepId}`
      await this.taskQueue.pauseTask(taskId)
    }
    
    console.log(`工作流执行 ${executionId} 已暂停`)
    return true
  }
  
  /**
   * 恢复工作流执行
   */
  async resumeExecution(executionId: string): Promise<boolean> {
    const execution = this.executions.get(executionId)
    if (!execution || execution.status !== WorkflowStatus.PAUSED) {
      return false
    }
    
    execution.status = WorkflowStatus.RUNNING
    
    // 恢复相关的任务
    for (const stepId of execution.stepResults.keys()) {
      const taskId = `task_${executionId}_${stepId}`
      await this.taskQueue.resumeTask(taskId)
    }
    
    console.log(`工作流执行 ${executionId} 已恢复`)
    return true
  }
  
  /**
   * 验证工作流
   */
  private async validateWorkflow(workflow: WorkflowDefinition): Promise<void> {
    // 检查基本字段
    if (!workflow.id || !workflow.name) {
      throw new Error('工作流缺少必需字段')
    }
    
    // 检查步骤ID唯一性
    const stepIds = new Set<string>()
    for (const step of workflow.steps) {
      if (stepIds.has(step.id)) {
        throw new Error(`重复的步骤ID: ${step.id}`)
      }
      stepIds.add(step.id)
    }
    
    // 检查连接有效性
    for (const connection of workflow.connections) {
      if (!stepIds.has(connection.from) || !stepIds.has(connection.to)) {
        throw new Error(`无效的连接: ${connection.from} -> ${connection.to}`)
      }
    }
    
    // 检查循环依赖
    try {
      const graph = this.buildExecutionGraph(workflow)
      this.topologicalSort(graph)
    } catch (error) {
      throw new Error(`工作流验证失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }
  
  /**
   * 启动引擎
   */
  start(): void {
    this.isRunning = true
    this.taskQueue.start()
    console.log('工作流引擎已启动')
  }
  
  /**
   * 停止引擎
   */
  async stop(): Promise<void> {
    this.isRunning = false
    
    // 取消所有正在运行的执行
    for (const execution of this.executions.values()) {
      if (execution.status === WorkflowStatus.RUNNING) {
        await this.cancelExecution(execution.id)
      }
    }
    
    await this.taskQueue.stop()
    console.log('工作流引擎已停止')
  }
  
  /**
   * 获取工作流列表
   */
  getWorkflows(): WorkflowDefinition[] {
    return Array.from(this.workflows.values())
  }
  
  /**
   * 获取工作流详情
   */
  getWorkflow(workflowId: string): WorkflowDefinition | null {
    return this.workflows.get(workflowId) || null
  }
  
  /**
   * 获取执行列表
   */
  getExecutions(workflowId?: string): WorkflowExecution[] {
    const executions = Array.from(this.executions.values())
    
    if (workflowId) {
      return executions.filter(execution => execution.workflowId === workflowId)
    }
    
    return executions
  }
  
  /**
   * 获取执行详情
   */
  getExecution(executionId: string): WorkflowExecution | null {
    return this.executions.get(executionId) || null
  }
  
  /**
   * 获取引擎状态
   */
  getStatus(): {
    isRunning: boolean
    workflowCount: number
    executionCount: number
    runningExecutions: number
    taskQueueStatus: any
  } {
    const runningExecutions = Array.from(this.executions.values())
      .filter(execution => execution.status === WorkflowStatus.RUNNING).length
    
    return {
      isRunning: this.isRunning,
      workflowCount: this.workflows.size,
      executionCount: this.executions.size,
      runningExecutions,
      taskQueueStatus: this.taskQueue.getStatus()
    }
  }
  
  /**
   * 清理历史执行
   */
  cleanupExecutions(maxAge = 86400000): number { // 默认24小时
    const cutoffTime = new Date(Date.now() - maxAge)
    let cleanedCount = 0
    
    for (const [executionId, execution] of this.executions.entries()) {
      if (execution.endTime && execution.endTime < cutoffTime) {
        this.executions.delete(executionId)
        cleanedCount++
      }
    }
    
    console.log(`清理了 ${cleanedCount} 个历史执行`)
    return cleanedCount
  }
  
  /**
   * 创建示例工作流
   */
  createSampleWorkflow(): WorkflowDefinition {
    return {
      id: `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: '示例PPT转视频工作流',
      description: '将PPT文件转换为视频的完整工作流',
      version: '1.0.0',
      status: WorkflowStatus.DRAFT,
      
      steps: [
        {
          id: 'step_ppt_import',
          name: 'PPT导入',
          type: 'ppt-import',
          config: { format: 'pptx' },
          dependencies: [],
          position: { x: 100, y: 100 }
        },
        {
          id: 'step_content_extract',
          name: '内容提取',
          type: 'content-extract',
          config: { extractImages: true, extractText: true },
          dependencies: ['step_ppt_import'],
          position: { x: 300, y: 100 }
        },
        {
          id: 'step_tts_generate',
          name: '语音合成',
          type: 'tts-generate',
          config: { voice: 'default', speed: 1.0 },
          dependencies: ['step_content_extract'],
          position: { x: 500, y: 100 }
        },
        {
          id: 'step_video_generate',
          name: '视频生成',
          type: 'video-generate',
          config: { resolution: '1920x1080', fps: 30 },
          dependencies: ['step_tts_generate'],
          position: { x: 700, y: 100 }
        }
      ],
      
      connections: [
        { id: 'conn_1', from: 'step_ppt_import', to: 'step_content_extract' },
        { id: 'conn_2', from: 'step_content_extract', to: 'step_tts_generate' },
        { id: 'conn_3', from: 'step_tts_generate', to: 'step_video_generate' }
      ],
      
      globalConfig: {
        maxConcurrentTasks: 5,
        globalTimeout: 3600000,
        errorHandling: { strategy: 'continue-on-error' }
      },
      
      variables: {},
      parameters: [
        {
          name: 'inputFile',
          type: 'string',
          required: true,
          description: 'PPT文件路径'
        },
        {
          name: 'outputPath',
          type: 'string',
          required: true,
          description: '输出目录'
        }
      ],
      
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: 'system'
    }
  }
}