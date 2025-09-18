/**
 * 企业级任务队列管理器
 * Netflix V2 Phase 6.4 Enterprise Task Queue Manager
 */

import type {
  BatchTask,
  TaskStatus,
  TaskPriority,
  ResourceRequirements,
  TaskError,
  TaskProgress,
  ResourcePool,
  ResourceNode,
  SchedulingPolicy,
  TaskResult
} from './batch-types';

import { DEFAULT_BATCH_CONFIG } from './batch-types';

// 队列统计信息接口
export interface QueueStatistics {
  totalTasks: number;
  pendingTasks: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  
  // 性能指标
  averageWaitTime: number;
  averageExecutionTime: number;
  throughput: number; // 任务/分钟
  
  // 资源使用率
  resourceUtilization: Record<string, number>;
  
  // 队列健康度
  healthScore: number;
}

// 调度事件接口
export interface SchedulingEvent {
  type: 'task-scheduled' | 'task-started' | 'task-completed' | 'task-failed' | 'resource-allocated' | 'resource-released';
  taskId: string;
  timestamp: Date;
  details: Record<string, any>;
}

/**
 * 任务队列管理器
 * 负责任务的排队、调度、执行和监控
 */
export class TaskQueue extends EventEmitter {
  private tasks: Map<string, BatchTask> = new Map();
  private runningTasks: Map<string, BatchTask> = new Map();
  private completedTasks: Map<string, TaskResult> = new Map();
  private failedTasks: Map<string, TaskResult> = new Map();
  
  private resourcePools: Map<string, ResourcePool> = new Map();
  private taskAssignments: Map<string, string> = new Map(); // taskId -> nodeId
  
  private isRunning = false;
  private maxConcurrentTasks: number;
  private schedulingPolicy: SchedulingPolicy;
  
  // 性能监控
  private statistics: QueueStatistics;
  private metricsHistory: SchedulingEvent[] = [];
  
  // 定时器
  private schedulerTimer?: NodeJS.Timeout;
  private metricsTimer?: NodeJS.Timeout;
  
  constructor(config: {
    maxConcurrentTasks?: number;
    schedulingPolicy?: SchedulingPolicy;
    resourcePools?: ResourcePool[];
  } = {}) {
    super();
    
    this.maxConcurrentTasks = config.maxConcurrentTasks || DEFAULT_BATCH_CONFIG.globalConfig.maxConcurrentTasks;
    this.schedulingPolicy = config.schedulingPolicy || {
      algorithm: 'priority',
      loadBalancing: { strategy: 'weighted' },
      priority: { enabled: true, weights: {}, preemption: false }
    };
    
    // 初始化资源池
    if (config.resourcePools) {
      config.resourcePools.forEach(pool => {
        this.resourcePools.set(pool.id, pool);
      });
    }
    
    // 初始化统计信息
    this.statistics = {
      totalTasks: 0,
      pendingTasks: 0,
      runningTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      averageWaitTime: 0,
      averageExecutionTime: 0,
      throughput: 0,
      resourceUtilization: {},
      healthScore: 100
    };
    
    this.initializeScheduler();
  }
  
  /**
   * 初始化调度器
   */
  private initializeScheduler(): void {
    // 调度器定时器 - 每秒检查一次
    this.schedulerTimer = setInterval(() => {
      this.scheduleNextTasks();
    }, 1000);
    
    // 性能监控定时器 - 每分钟更新一次统计信息
    this.metricsTimer = setInterval(() => {
      this.updateStatistics();
    }, 60000);
  }
  
  /**
   * 添加任务到队列
   */
  async addTask(task: BatchTask): Promise<void> {
    // 验证任务
    await this.validateTask(task);
    
    // 设置任务状态
    task.status = TaskStatus.PENDING;
    task.createdAt = new Date();
    task.updatedAt = new Date();
    
    // 添加到队列
    this.tasks.set(task.id, task);
    
    // 更新统计信息
    this.statistics.totalTasks++;
    this.statistics.pendingTasks++;
    
    // 发出事件
    this.emit('task-added', task);
    
    // 记录日志
    this.logEvent({
      type: 'task-scheduled',
      taskId: task.id,
      timestamp: new Date(),
      details: { priority: task.priority, type: task.type }
    });
    
    console.log(`任务 ${task.name} (${task.id}) 已添加到队列`);\n  }
  
  /**
   * 添加多个任务
   */
  async addTasks(tasks: BatchTask[]): Promise<void> {
    for (const task of tasks) {
      await this.addTask(task);
    }
  }
  
  /**
   * 移除任务
   */
  async removeTask(taskId: string): Promise<boolean> {
    const task = this.tasks.get(taskId);
    if (!task) {
      return false;
    }
    
    // 如果任务正在运行，先取消
    if (task.status === TaskStatus.RUNNING) {
      await this.cancelTask(taskId);
    }
    
    // 从队列中移除
    this.tasks.delete(taskId);
    this.runningTasks.delete(taskId);
    
    // 更新统计信息
    if (task.status === TaskStatus.PENDING) {
      this.statistics.pendingTasks--;
    }
    
    this.emit('task-removed', task);
    
    console.log(`任务 ${task.name} (${taskId}) 已从队列中移除`);
    return true;
  }
  
  /**
   * 取消任务
   */
  async cancelTask(taskId: string): Promise<boolean> {
    const task = this.tasks.get(taskId) || this.runningTasks.get(taskId);
    if (!task) {
      return false;
    }
    
    // 更新任务状态
    task.status = TaskStatus.CANCELLED;
    task.updatedAt = new Date();
    
    // 释放资源
    await this.releaseTaskResources(taskId);
    
    // 移除运行中的任务
    this.runningTasks.delete(taskId);
    
    // 更新统计信息
    this.statistics.runningTasks--;
    
    this.emit('task-cancelled', task);
    
    console.log(`任务 ${task.name} (${taskId}) 已取消`);
    return true;
  }
  
  /**
   * 暂停任务
   */
  async pauseTask(taskId: string): Promise<boolean> {
    const task = this.runningTasks.get(taskId);
    if (!task || task.status !== TaskStatus.RUNNING) {
      return false;
    }
    
    task.status = TaskStatus.PAUSED;
    task.updatedAt = new Date();
    
    this.emit('task-paused', task);
    
    console.log(`任务 ${task.name} (${taskId}) 已暂停`);
    return true;
  }
  
  /**
   * 恢复任务
   */
  async resumeTask(taskId: string): Promise<boolean> {
    const task = this.runningTasks.get(taskId);
    if (!task || task.status !== TaskStatus.PAUSED) {
      return false;
    }
    
    task.status = TaskStatus.RUNNING;
    task.updatedAt = new Date();
    
    this.emit('task-resumed', task);
    
    console.log(`任务 ${task.name} (${taskId}) 已恢复`);
    return true;
  }
  
  /**
   * 调度下一批任务
   */
  private async scheduleNextTasks(): Promise<void> {
    if (!this.isRunning || this.runningTasks.size >= this.maxConcurrentTasks) {
      return;
    }
    
    // 获取可执行的任务
    const eligibleTasks = this.getEligibleTasks();
    
    // 根据调度策略排序
    const sortedTasks = this.sortTasksByPriority(eligibleTasks);
    
    // 调度任务
    for (const task of sortedTasks) {
      if (this.runningTasks.size >= this.maxConcurrentTasks) {
        break;
      }
      
      // 检查资源可用性
      const availableNode = await this.findAvailableNode(task.resourceRequirements);
      if (!availableNode) {
        continue;
      }
      
      // 分配资源并启动任务
      await this.allocateResourcesAndStartTask(task, availableNode);
    }
  }
  
  /**
   * 获取可执行的任务
   */
  private getEligibleTasks(): BatchTask[] {
    const eligibleTasks: BatchTask[] = [];
    
    for (const task of this.tasks.values()) {
      if (task.status === TaskStatus.PENDING && this.checkTaskDependencies(task)) {
        eligibleTasks.push(task);
      }
    }
    
    return eligibleTasks;
  }
  
  /**
   * 检查任务依赖
   */
  private checkTaskDependencies(task: BatchTask): boolean {
    for (const depId of task.dependencies) {
      const depResult = this.completedTasks.get(depId);
      if (!depResult || depResult.status !== TaskStatus.COMPLETED) {
        return false;
      }
    }
    return true;
  }
  
  /**
   * 按优先级排序任务
   */
  private sortTasksByPriority(tasks: BatchTask[]): BatchTask[] {
    return tasks.sort((a, b) => {
      // 首先按优先级排序
      if (a.priority !== b.priority) {
        return b.priority - a.priority; // 高优先级在前
      }
      
      // 然后按创建时间排序
      return a.createdAt.getTime() - b.createdAt.getTime();
    });
  }
  
  /**
   * 查找可用节点
   */
  private async findAvailableNode(requirements: ResourceRequirements): Promise<ResourceNode | null> {
    for (const pool of this.resourcePools.values()) {
      for (const node of pool.nodes) {
        if (node.status === 'online' && this.checkNodeCapacity(node, requirements)) {
          return node;
        }
      }
    }
    return null;
  }
  
  /**
   * 检查节点容量
   */
  private checkNodeCapacity(node: ResourceNode, requirements: ResourceRequirements): boolean {
    const capacity = node.capacity;
    
    return (
      capacity.available >= requirements.cpu &&
      capacity.available >= requirements.memory &&
      capacity.available >= requirements.storage
    );
  }
  
  /**
   * 分配资源并启动任务
   */
  private async allocateResourcesAndStartTask(task: BatchTask, node: ResourceNode): Promise<void> {
    try {
      // 分配资源
      await this.allocateResources(task, node);
      
      // 更新任务状态
      task.status = TaskStatus.RUNNING;
      task.startedAt = new Date();
      task.updatedAt = new Date();
      task.executorId = node.id;
      
      // 从待处理队列移到运行队列
      this.tasks.delete(task.id);
      this.runningTasks.set(task.id, task);
      
      // 更新统计信息
      this.statistics.pendingTasks--;
      this.statistics.runningTasks++;
      
      // 记录任务分配
      this.taskAssignments.set(task.id, node.id);
      
      // 发出事件
      this.emit('task-started', task);
      
      // 记录日志
      this.logEvent({
        type: 'task-started',
        taskId: task.id,
        timestamp: new Date(),
        details: { nodeId: node.id, resources: task.resourceRequirements }
      });
      
      // 启动任务执行
      this.executeTask(task);
      
      console.log(`任务 ${task.name} (${task.id}) 已在节点 ${node.name} 上启动`);
      
    } catch (error) {
      console.error(`启动任务 ${task.id} 失败:`, error);
      await this.handleTaskFailure(task, {
        code: 'TASK_START_FAILED',
        message: error instanceof Error ? error.message : '未知错误',
        timestamp: new Date(),
        severity: 'high',
        recoverable: true
      });
    }
  }
  
  /**
   * 分配资源
   */
  private async allocateResources(task: BatchTask, node: ResourceNode): Promise<void> {
    const requirements = task.resourceRequirements;
    
    // 更新节点容量
    node.capacity.allocated += requirements.cpu;
    node.capacity.available -= requirements.cpu;
    
    // 记录资源分配事件
    this.logEvent({
      type: 'resource-allocated',
      taskId: task.id,
      timestamp: new Date(),
      details: { nodeId: node.id, resources: requirements }
    });
  }
  
  /**
   * 释放任务资源
   */
  private async releaseTaskResources(taskId: string): Promise<void> {
    const nodeId = this.taskAssignments.get(taskId);
    if (!nodeId) {
      return;
    }
    
    const task = this.runningTasks.get(taskId) || this.tasks.get(taskId);
    if (!task) {
      return;
    }
    
    // 查找节点
    let node: ResourceNode | undefined;
    for (const pool of this.resourcePools.values()) {
      node = pool.nodes.find(n => n.id === nodeId);
      if (node) break;
    }
    
    if (node) {
      const requirements = task.resourceRequirements;
      
      // 释放资源
      node.capacity.allocated -= requirements.cpu;
      node.capacity.available += requirements.cpu;
      
      // 记录资源释放事件
      this.logEvent({
        type: 'resource-released',
        taskId: taskId,
        timestamp: new Date(),
        details: { nodeId: node.id, resources: requirements }
      });
    }
    
    // 移除任务分配记录
    this.taskAssignments.delete(taskId);
  }
  
  /**
   * 执行任务
   */
  private async executeTask(task: BatchTask): Promise<void> {
    try {
      // 模拟任务执行（实际实现中这里会调用具体的执行器）
      const result = await this.runTaskLogic(task);
      
      // 任务成功完成
      await this.handleTaskCompletion(task, result);
      
    } catch (error) {
      // 任务执行失败
      await this.handleTaskFailure(task, {
        code: 'TASK_EXECUTION_FAILED',
        message: error instanceof Error ? error.message : '任务执行失败',
        timestamp: new Date(),
        severity: 'medium',
        recoverable: true
      });
    }
  }
  
  /**
   * 运行任务逻辑（模拟）
   */
  private async runTaskLogic(task: BatchTask): Promise<any> {
    return new Promise((resolve, reject) => {
      // 模拟任务执行时间
      const executionTime = Math.random() * 10000 + 5000; // 5-15秒
      
      setTimeout(() => {
        // 模拟90%的成功率
        if (Math.random() < 0.9) {
          resolve({
            status: 'success',
            output: `任务 ${task.name} 执行完成`,
            timestamp: new Date()
          });
        } else {
          reject(new Error('模拟任务执行失败'));
        }
      }, executionTime);
    });
  }
  
  /**
   * 处理任务完成
   */
  private async handleTaskCompletion(task: BatchTask, result: any): Promise<void> {
    // 更新任务状态
    task.status = TaskStatus.COMPLETED;
    task.completedAt = new Date();
    task.updatedAt = new Date();
    task.outputData = result;
    
    // 创建任务结果
    const taskResult: TaskResult = {
      taskId: task.id,
      status: TaskStatus.COMPLETED,
      startTime: task.startedAt!,
      endTime: task.completedAt,
      duration: task.completedAt.getTime() - task.startedAt!.getTime(),
      output: result,
      metrics: {
        memoryUsage: Math.random() * 512,
        cpuUsage: Math.random() * 100,
        diskIO: Math.random() * 1024,
        networkIO: Math.random() * 256,
        custom: {}
      }
    };
    
    // 添加到完成列表
    this.completedTasks.set(task.id, taskResult);
    
    // 从运行队列移除
    this.runningTasks.delete(task.id);
    
    // 释放资源
    await this.releaseTaskResources(task.id);
    
    // 更新统计信息
    this.statistics.runningTasks--;
    this.statistics.completedTasks++;
    
    // 发出事件
    this.emit('task-completed', task, taskResult);
    
    // 记录日志
    this.logEvent({
      type: 'task-completed',
      taskId: task.id,
      timestamp: new Date(),
      details: { duration: taskResult.duration, output: result }
    });
    
    console.log(`任务 ${task.name} (${task.id}) 执行完成，耗时 ${taskResult.duration}ms`);
  }
  
  /**
   * 处理任务失败
   */
  private async handleTaskFailure(task: BatchTask, error: TaskError): Promise<void> {
    // 检查是否需要重试
    if (this.shouldRetryTask(task, error)) {
      await this.retryTask(task, error);
      return;
    }
    
    // 更新任务状态
    task.status = TaskStatus.FAILED;
    task.completedAt = new Date();
    task.updatedAt = new Date();
    task.error = error;
    
    // 创建任务结果
    const taskResult: TaskResult = {
      taskId: task.id,
      status: TaskStatus.FAILED,
      startTime: task.startedAt || task.createdAt,
      endTime: task.completedAt,
      duration: task.completedAt.getTime() - (task.startedAt || task.createdAt).getTime(),
      error: error,
      metrics: {
        memoryUsage: 0,
        cpuUsage: 0,
        diskIO: 0,
        networkIO: 0,
        custom: {}
      }
    };
    
    // 添加到失败列表
    this.failedTasks.set(task.id, taskResult);
    
    // 从运行队列移除
    this.runningTasks.delete(task.id);
    
    // 释放资源
    await this.releaseTaskResources(task.id);
    
    // 更新统计信息
    this.statistics.runningTasks--;
    this.statistics.failedTasks++;
    
    // 发出事件
    this.emit('task-failed', task, error);
    
    // 记录日志
    this.logEvent({
      type: 'task-failed',
      taskId: task.id,
      timestamp: new Date(),
      details: { error: error.message, code: error.code }
    });
    
    console.error(`任务 ${task.name} (${task.id}) 执行失败: ${error.message}`);
  }
  
  /**
   * 检查是否应该重试任务
   */
  private shouldRetryTask(task: BatchTask, error: TaskError): boolean {
    const retryConfig = task.retryConfig;
    
    // 检查重试次数
    const currentRetries = task.metadata.retryCount || 0;
    if (currentRetries >= retryConfig.maxRetries) {
      return false;
    }
    
    // 检查错误是否可重试
    if (retryConfig.nonRetryableErrors.includes(error.code)) {
      return false;
    }
    
    // 检查是否是可重试错误
    if (retryConfig.retryableErrors.length > 0 && !retryConfig.retryableErrors.includes(error.code)) {
      return false;
    }
    
    // 自定义重试逻辑
    if (retryConfig.customRetryLogic) {
      return retryConfig.customRetryLogic(error, currentRetries);
    }
    
    return error.recoverable;
  }
  
  /**
   * 重试任务
   */
  private async retryTask(task: BatchTask, error: TaskError): Promise<void> {
    const retryConfig = task.retryConfig;
    const currentRetries = task.metadata.retryCount || 0;
    
    // 更新重试计数
    task.metadata.retryCount = currentRetries + 1;
    
    // 计算延迟时间
    let delay = retryConfig.retryDelay;
    
    switch (retryConfig.strategy) {
      case 'linear':
        delay = retryConfig.retryDelay * (currentRetries + 1);
        break;
      case 'exponential':
        delay = retryConfig.retryDelay * Math.pow(retryConfig.backoffMultiplier, currentRetries);
        break;
      case 'fixed':
      default:
        delay = retryConfig.retryDelay;
        break;
    }
    
    // 限制最大延迟
    delay = Math.min(delay, retryConfig.maxRetryDelay);
    
    // 更新任务状态
    task.status = TaskStatus.RETRYING;
    task.updatedAt = new Date();
    
    console.log(`任务 ${task.name} (${task.id}) 将在 ${delay}ms 后重试（第${currentRetries + 1}次重试）`);
    
    // 延迟后重新添加到队列
    setTimeout(() => {
      task.status = TaskStatus.PENDING;
      task.updatedAt = new Date();
      
      // 重新添加到待处理队列
      this.runningTasks.delete(task.id);
      this.tasks.set(task.id, task);
      
      // 更新统计信息
      this.statistics.runningTasks--;
      this.statistics.pendingTasks++;
      
      this.emit('task-retrying', task);
    }, delay);
  }
  
  /**
   * 验证任务
   */
  private async validateTask(task: BatchTask): Promise<void> {
    if (!task.id || !task.name || !task.type) {
      throw new Error('任务缺少必需字段');
    }
    
    if (this.tasks.has(task.id) || this.runningTasks.has(task.id)) {
      throw new Error(`任务ID ${task.id} 已存在`);
    }
    
    // 验证资源需求
    if (!task.resourceRequirements || task.resourceRequirements.cpu <= 0) {
      throw new Error('无效的资源需求');
    }
    
    // 验证依赖关系
    for (const depId of task.dependencies) {
      if (!this.completedTasks.has(depId) && !this.tasks.has(depId) && !this.runningTasks.has(depId)) {
        throw new Error(`依赖任务 ${depId} 不存在`);
      }
    }
  }
  
  /**
   * 更新统计信息
   */
  private updateStatistics(): void {
    // 计算平均等待时间和执行时间
    let totalWaitTime = 0;
    let totalExecutionTime = 0;
    let completedCount = 0;
    
    for (const result of this.completedTasks.values()) {
      if (result.duration) {
        totalExecutionTime += result.duration;
        completedCount++;
      }
    }
    
    if (completedCount > 0) {
      this.statistics.averageExecutionTime = totalExecutionTime / completedCount;
    }
    
    // 计算吞吐量（最近一分钟完成的任务数）
    const oneMinuteAgo = new Date(Date.now() - 60000);
    const recentCompletions = this.metricsHistory.filter(
      event => event.type === 'task-completed' && event.timestamp > oneMinuteAgo
    ).length;
    
    this.statistics.throughput = recentCompletions;
    
    // 计算资源利用率
    for (const pool of this.resourcePools.values()) {
      let totalCapacity = 0;
      let totalAllocated = 0;
      
      for (const node of pool.nodes) {
        totalCapacity += node.capacity.total;
        totalAllocated += node.capacity.allocated;
      }
      
      if (totalCapacity > 0) {
        this.statistics.resourceUtilization[pool.id] = (totalAllocated / totalCapacity) * 100;
      }
    }
    
    // 计算健康度
    this.statistics.healthScore = this.calculateHealthScore();
    
    // 发出统计更新事件
    this.emit('statistics-updated', this.statistics);
  }
  
  /**
   * 计算队列健康度
   */
  private calculateHealthScore(): number {
    let score = 100;
    
    // 失败率影响
    const totalTasks = this.statistics.completedTasks + this.statistics.failedTasks;
    if (totalTasks > 0) {
      const failureRate = this.statistics.failedTasks / totalTasks;
      score -= failureRate * 50; // 失败率每10%扣5分
    }
    
    // 资源利用率影响
    const avgUtilization = Object.values(this.statistics.resourceUtilization).reduce((a, b) => a + b, 0) / 
                          Object.keys(this.statistics.resourceUtilization).length;
    
    if (avgUtilization > 90) {
      score -= 20; // 资源使用率过高
    } else if (avgUtilization < 20) {
      score -= 10; // 资源使用率过低
    }
    
    // 待处理任务积压影响
    if (this.statistics.pendingTasks > 50) {
      score -= 15; // 任务积压
    }
    
    return Math.max(0, Math.min(100, score));
  }
  
  /**
   * 记录事件
   */
  private logEvent(event: SchedulingEvent): void {
    this.metricsHistory.push(event);
    
    // 保留最近1000个事件
    if (this.metricsHistory.length > 1000) {
      this.metricsHistory = this.metricsHistory.slice(-1000);
    }
  }
  
  /**
   * 启动队列
   */
  start(): void {
    this.isRunning = true;
    console.log('任务队列已启动');
    this.emit('queue-started');
  }
  
  /**
   * 停止队列
   */
  async stop(): Promise<void> {
    this.isRunning = false;
    
    // 停止定时器
    if (this.schedulerTimer) {
      clearInterval(this.schedulerTimer);
    }
    if (this.metricsTimer) {
      clearInterval(this.metricsTimer);
    }
    
    // 等待运行中的任务完成或超时
    const timeout = 30000; // 30秒超时
    const startTime = Date.now();
    
    while (this.runningTasks.size > 0 && Date.now() - startTime < timeout) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // 强制取消剩余的运行任务
    for (const taskId of this.runningTasks.keys()) {
      await this.cancelTask(taskId);
    }
    
    console.log('任务队列已停止');
    this.emit('queue-stopped');
  }
  
  /**
   * 获取队列状态
   */
  getStatus(): {
    isRunning: boolean;
    statistics: QueueStatistics;
    runningTasks: BatchTask[];
    pendingTasks: BatchTask[];
  } {
    return {
      isRunning: this.isRunning,
      statistics: this.statistics,
      runningTasks: Array.from(this.runningTasks.values()),
      pendingTasks: Array.from(this.tasks.values())
    };
  }
  
  /**
   * 获取任务详情
   */
  getTask(taskId: string): BatchTask | TaskResult | null {
    return this.tasks.get(taskId) || 
           this.runningTasks.get(taskId) || 
           this.completedTasks.get(taskId) || 
           this.failedTasks.get(taskId) || 
           null;
  }
  
  /**
   * 获取任务历史
   */
  getTaskHistory(limit = 100): SchedulingEvent[] {
    return this.metricsHistory.slice(-limit);
  }
  
  /**
   * 清理已完成的任务
   */
  cleanupCompletedTasks(maxAge = 86400000): number { // 默认24小时
    const cutoffTime = new Date(Date.now() - maxAge);
    let cleanedCount = 0;
    
    for (const [taskId, result] of this.completedTasks.entries()) {
      if (result.endTime && result.endTime < cutoffTime) {
        this.completedTasks.delete(taskId);
        cleanedCount++;
      }
    }
    
    for (const [taskId, result] of this.failedTasks.entries()) {
      if (result.endTime && result.endTime < cutoffTime) {
        this.failedTasks.delete(taskId);
        cleanedCount++;
      }
    }
    
    console.log(`清理了 ${cleanedCount} 个历史任务`);
    return cleanedCount;
  }
}