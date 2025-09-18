/**
 * 企业级任务队列管理器
 * Netflix V2 Phase 6.4 Enterprise Task Queue Manager
 */

import { DEFAULT_BATCH_CONFIG } from './batch-types';

// 重新定义必要的枚举和接口，避免type-only导入问题
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused',
  RETRYING = 'retrying'
}

export enum TaskPriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  URGENT = 3,
  CRITICAL = 4
}

export interface SimpleTask {
  id: string;
  name: string;
  description?: string;
  type: string;
  status: TaskStatus;
  priority: TaskPriority;
  
  inputData: Record<string, any>;
  outputData?: Record<string, any>;
  
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  updatedAt: Date;
  
  resourceRequirements: {
    cpu: number;
    memory: number;
    storage: number;
  };
  
  progress: {
    current: number;
    total: number;
    percentage: number;
  };
  
  error?: {
    code: string;
    message: string;
    timestamp: Date;
    severity: 'low' | 'medium' | 'high' | 'critical';
    recoverable: boolean;
  };
  
  dependencies: string[];
  
  retryConfig: {
    maxRetries: number;
    retryDelay: number;
    backoffMultiplier: number;
    maxRetryDelay: number;
    strategy: 'fixed' | 'linear' | 'exponential';
    retryableErrors: string[];
    nonRetryableErrors: string[];
  };
  
  tags: string[];
  metadata: Record<string, any>;
  
  executorId?: string;
  nodeId?: string;
}

export interface QueueStatistics {
  totalTasks: number;
  pendingTasks: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  
  averageWaitTime: number;
  averageExecutionTime: number;
  throughput: number;
  
  resourceUtilization: Record<string, number>;
  healthScore: number;
}

export interface TaskResult {
  taskId: string;
  status: TaskStatus;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  output?: any;
  error?: any;
  metrics: {
    memoryUsage: number;
    cpuUsage: number;
    diskIO: number;
    networkIO: number;
  };
}

export interface SchedulingEvent {
  type: 'task-scheduled' | 'task-started' | 'task-completed' | 'task-failed' | 'resource-allocated' | 'resource-released';
  taskId: string;
  timestamp: Date;
  details: Record<string, any>;
}

// 简单的事件发射器
class SimpleEventEmitter {
  private listeners: Map<string, Function[]> = new Map();
  
  on(event: string, listener: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(listener);
  }
  
  emit(event: string, ...args: any[]): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(listener => listener(...args));
    }
  }
  
  off(event: string, listener: Function): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      const index = eventListeners.indexOf(listener);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }
}

/**
 * 任务队列管理器
 */
export class TaskQueue extends SimpleEventEmitter {
  private tasks: Map<string, SimpleTask> = new Map();
  private runningTasks: Map<string, SimpleTask> = new Map();
  private completedTasks: Map<string, TaskResult> = new Map();
  private failedTasks: Map<string, TaskResult> = new Map();
  
  private isRunning = false;
  private maxConcurrentTasks: number;
  
  private statistics: QueueStatistics;
  private metricsHistory: SchedulingEvent[] = [];
  
  private schedulerTimer?: any;
  private metricsTimer?: any;
  
  constructor(config: {
    maxConcurrentTasks?: number;
  } = {}) {
    super();
    
    this.maxConcurrentTasks = config.maxConcurrentTasks || 10;
    
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
  
  private initializeScheduler(): void {
    this.schedulerTimer = setInterval(() => {
      this.scheduleNextTasks();
    }, 1000);
    
    this.metricsTimer = setInterval(() => {
      this.updateStatistics();
    }, 60000);
  }
  
  async addTask(task: SimpleTask): Promise<void> {
    await this.validateTask(task);
    
    task.status = TaskStatus.PENDING;
    task.createdAt = new Date();
    task.updatedAt = new Date();
    
    this.tasks.set(task.id, task);
    
    this.statistics.totalTasks++;
    this.statistics.pendingTasks++;
    
    this.emit('task-added', task);
    
    this.logEvent({
      type: 'task-scheduled',
      taskId: task.id,
      timestamp: new Date(),
      details: { priority: task.priority, type: task.type }
    });
    
    console.log(`任务 ${task.name} (${task.id}) 已添加到队列`);
  }
  
  async addTasks(tasks: SimpleTask[]): Promise<void> {
    for (const task of tasks) {
      await this.addTask(task);
    }
  }
  
  async removeTask(taskId: string): Promise<boolean> {
    const task = this.tasks.get(taskId);
    if (!task) {
      return false;
    }
    
    if (task.status === TaskStatus.RUNNING) {
      await this.cancelTask(taskId);
    }
    
    this.tasks.delete(taskId);
    this.runningTasks.delete(taskId);
    
    if (task.status === TaskStatus.PENDING) {
      this.statistics.pendingTasks--;
    }
    
    this.emit('task-removed', task);
    
    console.log(`任务 ${task.name} (${taskId}) 已从队列中移除`);
    return true;
  }
  
  async cancelTask(taskId: string): Promise<boolean> {
    const task = this.tasks.get(taskId) || this.runningTasks.get(taskId);
    if (!task) {
      return false;
    }
    
    task.status = TaskStatus.CANCELLED;
    task.updatedAt = new Date();
    
    this.runningTasks.delete(taskId);
    this.statistics.runningTasks--;
    
    this.emit('task-cancelled', task);
    
    console.log(`任务 ${task.name} (${taskId}) 已取消`);
    return true;
  }
  
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
  
  private async scheduleNextTasks(): Promise<void> {
    if (!this.isRunning || this.runningTasks.size >= this.maxConcurrentTasks) {
      return;
    }
    
    const eligibleTasks = this.getEligibleTasks();
    const sortedTasks = this.sortTasksByPriority(eligibleTasks);
    
    for (const task of sortedTasks) {
      if (this.runningTasks.size >= this.maxConcurrentTasks) {
        break;
      }
      
      await this.startTask(task);
    }
  }
  
  private getEligibleTasks(): SimpleTask[] {
    const eligibleTasks: SimpleTask[] = [];
    
    for (const task of this.tasks.values()) {
      if (task.status === TaskStatus.PENDING && this.checkTaskDependencies(task)) {
        eligibleTasks.push(task);
      }
    }
    
    return eligibleTasks;
  }
  
  private checkTaskDependencies(task: SimpleTask): boolean {
    for (const depId of task.dependencies) {
      const depResult = this.completedTasks.get(depId);
      if (!depResult || depResult.status !== TaskStatus.COMPLETED) {
        return false;
      }
    }
    return true;
  }
  
  private sortTasksByPriority(tasks: SimpleTask[]): SimpleTask[] {
    return tasks.sort((a, b) => {
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }
      return a.createdAt.getTime() - b.createdAt.getTime();
    });
  }
  
  private async startTask(task: SimpleTask): Promise<void> {
    try {
      task.status = TaskStatus.RUNNING;
      task.startedAt = new Date();
      task.updatedAt = new Date();
      
      this.tasks.delete(task.id);
      this.runningTasks.set(task.id, task);
      
      this.statistics.pendingTasks--;
      this.statistics.runningTasks++;
      
      this.emit('task-started', task);
      
      this.logEvent({
        type: 'task-started',
        taskId: task.id,
        timestamp: new Date(),
        details: { resources: task.resourceRequirements }
      });
      
      this.executeTask(task);
      
      console.log(`任务 ${task.name} (${task.id}) 已启动`);
      
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
  
  private async executeTask(task: SimpleTask): Promise<void> {
    try {
      const result = await this.runTaskLogic(task);
      await this.handleTaskCompletion(task, result);
    } catch (error) {
      await this.handleTaskFailure(task, {
        code: 'TASK_EXECUTION_FAILED',
        message: error instanceof Error ? error.message : '任务执行失败',
        timestamp: new Date(),
        severity: 'medium',
        recoverable: true
      });
    }
  }
  
  private async runTaskLogic(task: SimpleTask): Promise<any> {
    return new Promise((resolve, reject) => {
      const executionTime = Math.random() * 10000 + 5000;
      
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        task.progress.current += 10;
        task.progress.percentage = Math.min(100, (task.progress.current / task.progress.total) * 100);
        this.emit('task-progress', task);
      }, 1000);
      
      setTimeout(() => {
        clearInterval(progressInterval);
        
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
  
  private async handleTaskCompletion(task: SimpleTask, result: any): Promise<void> {
    task.status = TaskStatus.COMPLETED;
    task.completedAt = new Date();
    task.updatedAt = new Date();
    task.outputData = result;
    task.progress.current = task.progress.total;
    task.progress.percentage = 100;
    
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
        networkIO: Math.random() * 256
      }
    };
    
    this.completedTasks.set(task.id, taskResult);
    this.runningTasks.delete(task.id);
    
    this.statistics.runningTasks--;
    this.statistics.completedTasks++;
    
    this.emit('task-completed', task, taskResult);
    
    this.logEvent({
      type: 'task-completed',
      taskId: task.id,
      timestamp: new Date(),
      details: { duration: taskResult.duration, output: result }
    });
    
    console.log(`任务 ${task.name} (${task.id}) 执行完成，耗时 ${taskResult.duration}ms`);
  }
  
  private async handleTaskFailure(task: SimpleTask, error: any): Promise<void> {
    if (this.shouldRetryTask(task, error)) {
      await this.retryTask(task, error);
      return;
    }
    
    task.status = TaskStatus.FAILED;
    task.completedAt = new Date();
    task.updatedAt = new Date();
    task.error = error;
    
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
        networkIO: 0
      }
    };
    
    this.failedTasks.set(task.id, taskResult);
    this.runningTasks.delete(task.id);
    
    this.statistics.runningTasks--;
    this.statistics.failedTasks++;
    
    this.emit('task-failed', task, error);
    
    this.logEvent({
      type: 'task-failed',
      taskId: task.id,
      timestamp: new Date(),
      details: { error: error.message, code: error.code }
    });
    
    console.error(`任务 ${task.name} (${task.id}) 执行失败: ${error.message}`);
  }
  
  private shouldRetryTask(task: SimpleTask, error: any): boolean {
    const retryConfig = task.retryConfig;
    const currentRetries = task.metadata.retryCount || 0;
    
    if (currentRetries >= retryConfig.maxRetries) {
      return false;
    }
    
    if (retryConfig.nonRetryableErrors.includes(error.code)) {
      return false;
    }
    
    if (retryConfig.retryableErrors.length > 0 && !retryConfig.retryableErrors.includes(error.code)) {
      return false;
    }
    
    return error.recoverable;
  }
  
  private async retryTask(task: SimpleTask, error: any): Promise<void> {
    const retryConfig = task.retryConfig;
    const currentRetries = task.metadata.retryCount || 0;
    
    task.metadata.retryCount = currentRetries + 1;
    
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
    
    delay = Math.min(delay, retryConfig.maxRetryDelay);
    
    task.status = TaskStatus.RETRYING;
    task.updatedAt = new Date();
    
    console.log(`任务 ${task.name} (${task.id}) 将在 ${delay}ms 后重试（第${currentRetries + 1}次重试）`);
    
    setTimeout(() => {
      task.status = TaskStatus.PENDING;
      task.updatedAt = new Date();
      
      this.runningTasks.delete(task.id);
      this.tasks.set(task.id, task);
      
      this.statistics.runningTasks--;
      this.statistics.pendingTasks++;
      
      this.emit('task-retrying', task);
    }, delay);
  }
  
  private async validateTask(task: SimpleTask): Promise<void> {
    if (!task.id || !task.name || !task.type) {
      throw new Error('任务缺少必需字段');
    }
    
    if (this.tasks.has(task.id) || this.runningTasks.has(task.id)) {
      throw new Error(`任务ID ${task.id} 已存在`);
    }
    
    if (!task.resourceRequirements || task.resourceRequirements.cpu <= 0) {
      throw new Error('无效的资源需求');
    }
  }
  
  private updateStatistics(): void {
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
    
    const oneMinuteAgo = new Date(Date.now() - 60000);
    const recentCompletions = this.metricsHistory.filter(
      event => event.type === 'task-completed' && event.timestamp > oneMinuteAgo
    ).length;
    
    this.statistics.throughput = recentCompletions;
    this.statistics.healthScore = this.calculateHealthScore();
    
    this.emit('statistics-updated', this.statistics);
  }
  
  private calculateHealthScore(): number {
    let score = 100;
    
    const totalTasks = this.statistics.completedTasks + this.statistics.failedTasks;
    if (totalTasks > 0) {
      const failureRate = this.statistics.failedTasks / totalTasks;
      score -= failureRate * 50;
    }
    
    if (this.statistics.pendingTasks > 50) {
      score -= 15;
    }
    
    return Math.max(0, Math.min(100, score));
  }
  
  private logEvent(event: SchedulingEvent): void {
    this.metricsHistory.push(event);
    
    if (this.metricsHistory.length > 1000) {
      this.metricsHistory = this.metricsHistory.slice(-1000);
    }
  }
  
  start(): void {
    this.isRunning = true;
    console.log('任务队列已启动');
    this.emit('queue-started');
  }
  
  async stop(): Promise<void> {
    this.isRunning = false;
    
    if (this.schedulerTimer) {
      clearInterval(this.schedulerTimer);
    }
    if (this.metricsTimer) {
      clearInterval(this.metricsTimer);
    }
    
    const timeout = 30000;
    const startTime = Date.now();
    
    while (this.runningTasks.size > 0 && Date.now() - startTime < timeout) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    for (const taskId of this.runningTasks.keys()) {
      await this.cancelTask(taskId);
    }
    
    console.log('任务队列已停止');
    this.emit('queue-stopped');
  }
  
  getStatus(): {
    isRunning: boolean;
    statistics: QueueStatistics;
    runningTasks: SimpleTask[];
    pendingTasks: SimpleTask[];
  } {
    return {
      isRunning: this.isRunning,
      statistics: this.statistics,
      runningTasks: Array.from(this.runningTasks.values()),
      pendingTasks: Array.from(this.tasks.values())
    };
  }
  
  getTask(taskId: string): SimpleTask | TaskResult | null {
    return this.tasks.get(taskId) || 
           this.runningTasks.get(taskId) || 
           this.completedTasks.get(taskId) || 
           this.failedTasks.get(taskId) || 
           null;
  }
  
  getTaskHistory(limit = 100): SchedulingEvent[] {
    return this.metricsHistory.slice(-limit);
  }
  
  cleanupCompletedTasks(maxAge = 86400000): number {
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
  
  // 工具方法：创建示例任务
  createSampleTask(name: string, type: string = 'processing'): SimpleTask {
    return {
      id: `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      type,
      status: TaskStatus.PENDING,
      priority: TaskPriority.NORMAL,
      inputData: {},
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
      dependencies: [],
      retryConfig: {
        maxRetries: 3,
        retryDelay: 1000,
        backoffMultiplier: 2,
        maxRetryDelay: 30000,
        strategy: 'exponential',
        retryableErrors: ['NETWORK_ERROR', 'TIMEOUT_ERROR'],
        nonRetryableErrors: ['AUTHENTICATION_ERROR', 'INVALID_INPUT']
      },
      tags: [],
      metadata: {}
    };
  }
}