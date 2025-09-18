/**
 * 企业级批处理系统 - 核心类型定义
 * Netflix V2 Phase 6.4 Enterprise Batch Processing System
 */

// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused',
  RETRYING = 'retrying'
}

// 任务优先级枚举
export enum TaskPriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  URGENT = 3,
  CRITICAL = 4
}

// 资源类型枚举
export enum ResourceType {
  CPU = 'cpu',
  MEMORY = 'memory',
  STORAGE = 'storage',
  NETWORK = 'network',
  GPU = 'gpu'
}

// 工作流状态枚举
export enum WorkflowStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused'
}

// 基础任务接口
export interface BatchTask {
  id: string;
  name: string;
  description?: string;
  type: string;
  status: TaskStatus;
  priority: TaskPriority;
  
  // 任务数据
  inputData: Record<string, any>;
  outputData?: Record<string, any>;
  
  // 时间信息
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  updatedAt: Date;
  
  // 资源需求
  resourceRequirements: ResourceRequirements;
  
  // 进度信息
  progress: TaskProgress;
  
  // 错误信息
  error?: TaskError;
  
  // 依赖关系
  dependencies: string[];
  dependents: string[];
  
  // 重试配置
  retryConfig: RetryConfig;
  
  // 标签和元数据
  tags: string[];
  metadata: Record<string, any>;
  
  // 执行器信息
  executorId?: string;
  nodeId?: string;
}

// 资源需求接口
export interface ResourceRequirements {
  cpu: number; // CPU核心数
  memory: number; // 内存MB
  storage: number; // 存储MB
  network?: number; // 网络带宽Mbps
  gpu?: number; // GPU数量
  
  // 资源限制
  maxCpu?: number;
  maxMemory?: number;
  maxStorage?: number;
  
  // 特殊要求
  nodeSelector?: Record<string, string>;
  affinity?: ResourceAffinity;
}

// 资源亲和性配置
export interface ResourceAffinity {
  nodeAffinity?: NodeAffinity;
  taskAffinity?: TaskAffinity;
  antiAffinity?: AntiAffinity;
}

export interface NodeAffinity {
  requiredDuringScheduling?: NodeSelector[];
  preferredDuringScheduling?: PreferredNodeSelector[];
}

export interface TaskAffinity {
  requiredDuringScheduling?: TaskSelector[];
  preferredDuringScheduling?: PreferredTaskSelector[];
}

export interface AntiAffinity {
  tasks?: string[];
  taskTypes?: string[];
}

export interface NodeSelector {
  matchExpressions: MatchExpression[];
}

export interface PreferredNodeSelector {
  weight: number;
  preference: NodeSelector;
}

export interface TaskSelector {
  matchLabels?: Record<string, string>;
  matchExpressions?: MatchExpression[];
}

export interface PreferredTaskSelector {
  weight: number;
  preference: TaskSelector;
}

export interface MatchExpression {
  key: string;
  operator: 'In' | 'NotIn' | 'Exists' | 'DoesNotExist';
  values?: string[];
}

// 任务进度接口
export interface TaskProgress {
  current: number;
  total: number;
  percentage: number;
  
  // 详细进度信息
  steps: ProgressStep[];
  currentStep?: string;
  
  // 性能指标
  metrics: ProgressMetrics;
  
  // 估算信息
  estimatedTimeRemaining?: number;
  estimatedCompletionTime?: Date;
}

export interface ProgressStep {
  id: string;
  name: string;
  status: TaskStatus;
  progress: number;
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
}

export interface ProgressMetrics {
  throughput?: number; // 处理速度
  latency?: number; // 延迟
  memoryUsage?: number; // 内存使用
  cpuUsage?: number; // CPU使用
  diskIO?: number; // 磁盘IO
  networkIO?: number; // 网络IO
}

// 任务错误接口
export interface TaskError {
  code: string;
  message: string;
  details?: Record<string, any>;
  stackTrace?: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  recoverable: boolean;
}

// 重试配置接口
export interface RetryConfig {
  maxRetries: number;
  retryDelay: number; // 毫秒
  backoffMultiplier: number;
  maxRetryDelay: number; // 毫秒
  
  // 重试条件
  retryableErrors: string[];
  nonRetryableErrors: string[];
  
  // 重试策略
  strategy: 'fixed' | 'linear' | 'exponential' | 'custom';
  
  // 自定义重试逻辑
  customRetryLogic?: (error: TaskError, attempt: number) => boolean;
}

// 工作流定义接口
export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  version: string;
  
  // 工作流状态
  status: WorkflowStatus;
  
  // 任务节点
  tasks: WorkflowTask[];
  
  // 连接关系
  connections: WorkflowConnection[];
  
  // 全局配置
  globalConfig: WorkflowGlobalConfig;
  
  // 调度配置
  schedule?: WorkflowSchedule;
  
  // 变量和参数
  variables: Record<string, any>;
  parameters: WorkflowParameter[];
  
  // 通知配置
  notifications: NotificationConfig[];
  
  // 时间信息
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
}

export interface WorkflowTask {
  id: string;
  name: string;
  type: string;
  
  // 任务配置
  config: Record<string, any>;
  
  // 位置信息（用于可视化）
  position: { x: number; y: number };
  
  // 条件执行
  condition?: WorkflowCondition;
  
  // 循环配置
  loop?: WorkflowLoop;
  
  // 超时配置
  timeout?: number;
}

export interface WorkflowConnection {
  id: string;
  from: string; // 源任务ID
  to: string; // 目标任务ID
  
  // 连接条件
  condition?: WorkflowCondition;
  
  // 数据映射
  dataMapping?: DataMapping[];
}

export interface WorkflowCondition {
  type: 'success' | 'failure' | 'always' | 'custom';
  expression?: string; // JavaScript表达式
}

export interface WorkflowLoop {
  type: 'for' | 'while' | 'foreach';
  
  // For循环
  start?: number;
  end?: number;
  step?: number;
  
  // While循环
  condition?: string;
  
  // ForEach循环
  items?: string; // 变量名或表达式
  itemVariable?: string;
  indexVariable?: string;
  
  // 循环控制
  maxIterations?: number;
  breakOnError?: boolean;
}

export interface DataMapping {
  from: string; // 源数据路径
  to: string; // 目标数据路径
  transform?: string; // 转换表达式
}

export interface WorkflowGlobalConfig {
  // 全局资源限制
  resourceLimits: ResourceRequirements;
  
  // 全局重试配置
  defaultRetryConfig: RetryConfig;
  
  // 全局超时
  globalTimeout?: number;
  
  // 并发控制
  maxConcurrentTasks: number;
  
  // 错误处理策略
  errorHandling: ErrorHandlingStrategy;
  
  // 日志配置
  logging: LoggingConfig;
}

export interface ErrorHandlingStrategy {
  strategy: 'fail-fast' | 'continue-on-error' | 'manual-intervention';
  
  // 自动恢复配置
  autoRecovery?: AutoRecoveryConfig;
  
  // 人工干预配置
  manualIntervention?: ManualInterventionConfig;
}

export interface AutoRecoveryConfig {
  enabled: boolean;
  maxAttempts: number;
  recoveryActions: RecoveryAction[];
}

export interface RecoveryAction {
  type: 'restart-task' | 'skip-task' | 'rollback' | 'custom';
  condition: string;
  action?: string; // 自定义恢复脚本
}

export interface ManualInterventionConfig {
  enabled: boolean;
  notificationChannels: string[];
  escalationRules: EscalationRule[];
}

export interface EscalationRule {
  after: number; // 等待时间（分钟）
  notificationChannels: string[];
  assignees: string[];
}

export interface LoggingConfig {
  level: 'debug' | 'info' | 'warn' | 'error';
  destinations: LogDestination[];
  format: 'json' | 'text' | 'structured';
  retention: number; // 天数
}

export interface LogDestination {
  type: 'file' | 'database' | 'external' | 'console';
  config: Record<string, any>;
}

export interface WorkflowSchedule {
  type: 'once' | 'recurring' | 'cron' | 'event-driven';
  
  // 一次性调度
  scheduledTime?: Date;
  
  // 循环调度
  interval?: number; // 毫秒
  
  // Cron调度
  cronExpression?: string;
  timezone?: string;
  
  // 事件驱动
  trigger?: EventTrigger;
  
  // 调度窗口
  startDate?: Date;
  endDate?: Date;
  
  // 暂停和恢复
  enabled: boolean;
  pausedRanges?: DateRange[];
}

export interface EventTrigger {
  type: 'file-change' | 'api-call' | 'webhook' | 'message-queue';
  config: Record<string, any>;
}

export interface DateRange {
  start: Date;
  end: Date;
  reason?: string;
}

export interface WorkflowParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  defaultValue?: any;
  description?: string;
  validation?: ParameterValidation;
}

export interface ParameterValidation {
  pattern?: string; // 正则表达式
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  enum?: any[];
  customValidator?: string; // JavaScript函数
}

export interface NotificationConfig {
  id: string;
  name: string;
  
  // 触发条件
  triggers: NotificationTrigger[];
  
  // 通知渠道
  channels: NotificationChannel[];
  
  // 通知内容
  template: NotificationTemplate;
  
  // 频率控制
  rateLimit?: RateLimit;
}

export interface NotificationTrigger {
  event: 'workflow-start' | 'workflow-complete' | 'workflow-fail' | 'task-fail' | 'custom';
  condition?: string; // JavaScript表达式
}

export interface NotificationChannel {
  type: 'email' | 'sms' | 'slack' | 'webhook' | 'in-app';
  config: Record<string, any>;
  recipients: string[];
}

export interface NotificationTemplate {
  subject: string;
  body: string;
  format: 'text' | 'html' | 'markdown';
  
  // 模板变量
  variables: Record<string, string>;
}

export interface RateLimit {
  maxNotifications: number;
  timeWindow: number; // 毫秒
  strategy: 'sliding-window' | 'fixed-window';
}

// 资源池配置接口
export interface ResourcePool {
  id: string;
  name: string;
  type: ResourceType;
  
  // 资源容量
  capacity: ResourceCapacity;
  
  // 当前使用情况
  usage: ResourceUsage;
  
  // 节点信息
  nodes: ResourceNode[];
  
  // 调度策略
  schedulingPolicy: SchedulingPolicy;
  
  // 监控配置
  monitoring: ResourceMonitoring;
}

export interface ResourceCapacity {
  total: number;
  available: number;
  allocated: number;
  reserved: number;
}

export interface ResourceUsage {
  current: number;
  peak: number;
  average: number;
  
  // 历史使用率
  history: UsageHistory[];
}

export interface UsageHistory {
  timestamp: Date;
  value: number;
  metadata?: Record<string, any>;
}

export interface ResourceNode {
  id: string;
  name: string;
  type: string;
  
  // 节点状态
  status: 'online' | 'offline' | 'maintenance' | 'error';
  
  // 节点容量
  capacity: ResourceCapacity;
  
  // 节点标签
  labels: Record<string, string>;
  
  // 健康状态
  health: NodeHealth;
  
  // 最后更新时间
  lastHeartbeat: Date;
}

export interface NodeHealth {
  score: number; // 0-100
  checks: HealthCheck[];
  
  // 性能指标
  metrics: NodeMetrics;
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message?: string;
  timestamp: Date;
}

export interface NodeMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkLatency: number;
  temperature?: number;
  loadAverage?: number[];
}

export interface SchedulingPolicy {
  algorithm: 'round-robin' | 'least-loaded' | 'priority' | 'affinity' | 'custom';
  
  // 负载均衡配置
  loadBalancing: LoadBalancingConfig;
  
  // 优先级配置
  priority: PriorityConfig;
  
  // 自定义调度器
  customScheduler?: string;
}

export interface LoadBalancingConfig {
  strategy: 'weighted' | 'random' | 'consistent-hashing';
  weights?: Record<string, number>;
  hashKey?: string;
}

export interface PriorityConfig {
  enabled: boolean;
  weights: Record<TaskPriority, number>;
  preemption: boolean;
}

export interface ResourceMonitoring {
  enabled: boolean;
  interval: number; // 毫秒
  
  // 监控指标
  metrics: MonitoringMetric[];
  
  // 告警配置
  alerts: AlertConfig[];
  
  // 数据保留
  retention: RetentionPolicy;
}

export interface MonitoringMetric {
  name: string;
  type: 'gauge' | 'counter' | 'histogram' | 'summary';
  description?: string;
  
  // 采集配置
  collection: MetricCollection;
  
  // 聚合配置
  aggregation?: MetricAggregation;
}

export interface MetricCollection {
  interval: number;
  source: string;
  query?: string;
}

export interface MetricAggregation {
  functions: string[]; // 'sum', 'avg', 'min', 'max', 'count'
  window: number; // 时间窗口（毫秒）
  groupBy?: string[];
}

export interface AlertConfig {
  id: string;
  name: string;
  
  // 告警条件
  condition: AlertCondition;
  
  // 告警级别
  severity: 'info' | 'warning' | 'critical';
  
  // 通知配置
  notifications: NotificationChannel[];
  
  // 抑制配置
  suppression?: AlertSuppression;
}

export interface AlertCondition {
  metric: string;
  operator: '>' | '<' | '>=' | '<=' | '==' | '!=';
  threshold: number;
  duration: number; // 持续时间（毫秒）
}

export interface AlertSuppression {
  enabled: boolean;
  duration: number; // 抑制时间（毫秒）
  
  // 抑制条件
  conditions?: AlertCondition[];
}

export interface RetentionPolicy {
  rawData: number; // 原始数据保留天数
  aggregatedData: number; // 聚合数据保留天数
  
  // 压缩配置
  compression?: CompressionConfig;
}

export interface CompressionConfig {
  enabled: boolean;
  algorithm: 'gzip' | 'lz4' | 'snappy';
  level?: number;
}

// 批处理结果接口
export interface BatchResult {
  id: string;
  workflowId: string;
  
  // 执行信息
  startTime: Date;
  endTime?: Date;
  duration?: number; // 毫秒
  
  // 结果状态
  status: WorkflowStatus;
  
  // 任务结果
  taskResults: TaskResult[];
  
  // 执行统计
  statistics: ExecutionStatistics;
  
  // 输出数据
  outputs: Record<string, any>;
  
  // 错误信息
  errors: TaskError[];
}

export interface TaskResult {
  taskId: string;
  status: TaskStatus;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  
  // 输出数据
  output?: any;
  
  // 错误信息
  error?: TaskError;
  
  // 性能指标
  metrics: TaskMetrics;
}

export interface TaskMetrics {
  memoryUsage: number;
  cpuUsage: number;
  diskIO: number;
  networkIO: number;
  
  // 自定义指标
  custom: Record<string, number>;
}

export interface ExecutionStatistics {
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  skippedTasks: number;
  
  // 资源使用统计
  resourceUsage: ResourceUsageStats;
  
  // 性能统计
  performance: PerformanceStats;
}

export interface ResourceUsageStats {
  peakMemory: number;
  peakCpu: number;
  totalDiskIO: number;
  totalNetworkIO: number;
  
  // 按时间的使用情况
  timeline: ResourceTimelinePoint[];
}

export interface ResourceTimelinePoint {
  timestamp: Date;
  memory: number;
  cpu: number;
  diskIO: number;
  networkIO: number;
}

export interface PerformanceStats {
  averageTaskDuration: number;
  medianTaskDuration: number;
  taskThroughput: number; // 任务/秒
  
  // 瓶颈分析
  bottlenecks: BottleneckAnalysis[];
}

export interface BottleneckAnalysis {
  type: 'cpu' | 'memory' | 'io' | 'network' | 'dependency';
  severity: number; // 0-1
  description: string;
  suggestion?: string;
}

// 默认配置
export const DEFAULT_BATCH_CONFIG = {
  resourceRequirements: {
    cpu: 1,
    memory: 512,
    storage: 1024
  } as ResourceRequirements,
  
  retryConfig: {
    maxRetries: 3,
    retryDelay: 1000,
    backoffMultiplier: 2,
    maxRetryDelay: 30000,
    strategy: 'exponential',
    retryableErrors: ['NETWORK_ERROR', 'TIMEOUT_ERROR'],
    nonRetryableErrors: ['AUTHENTICATION_ERROR', 'INVALID_INPUT']
  } as RetryConfig,
  
  globalConfig: {
    maxConcurrentTasks: 10,
    globalTimeout: 3600000, // 1小时
    errorHandling: {
      strategy: 'continue-on-error'
    },
    logging: {
      level: 'info',
      destinations: [{ type: 'console', config: {} }],
      format: 'json',
      retention: 30
    }
  } as WorkflowGlobalConfig
}

// 工具函数类型
export interface BatchProcessorUtils {
  createTask(config: Partial<BatchTask>): BatchTask;
  createWorkflow(config: Partial<WorkflowDefinition>): WorkflowDefinition;
  validateTaskDependencies(tasks: BatchTask[]): boolean;
  calculateResourceRequirements(tasks: BatchTask[]): ResourceRequirements;
  optimizeTaskScheduling(tasks: BatchTask[]): BatchTask[];
  generateExecutionPlan(workflow: WorkflowDefinition): ExecutionPlan;
}

export interface ExecutionPlan {
  id: string;
  workflowId: string;
  
  // 执行阶段
  phases: ExecutionPhase[];
  
  // 资源分配
  resourceAllocation: ResourceAllocation[];
  
  // 估算信息
  estimatedDuration: number;
  estimatedResources: ResourceRequirements;
  
  // 风险评估
  risks: RiskAssessment[];
}

export interface ExecutionPhase {
  id: string;
  name: string;
  tasks: string[]; // 任务ID列表
  
  // 并行度
  parallelism: number;
  
  // 阶段依赖
  dependencies: string[];
  
  // 预计时间
  estimatedDuration: number;
}

export interface ResourceAllocation {
  taskId: string;
  nodeId: string;
  resources: ResourceRequirements;
  
  // 分配时间
  scheduledTime: Date;
  estimatedDuration: number;
}

export interface RiskAssessment {
  type: 'resource-constraint' | 'dependency-cycle' | 'single-point-failure' | 'performance-bottleneck';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  impact: string;
  mitigation?: string;
  probability: number; // 0-1
}