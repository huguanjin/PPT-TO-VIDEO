/**
 * 企业级资源管理器
 * Netflix V2 Phase 6.4 Enterprise Resource Manager
 */

export enum ResourceType {
  CPU = 'cpu',
  MEMORY = 'memory',
  STORAGE = 'storage',
  NETWORK = 'network',
  GPU = 'gpu'
}

export interface ResourceRequirements {
  cpu: number
  memory: number
  storage: number
  network?: number
  gpu?: number
}

export interface ResourceNode {
  id: string
  name: string
  type: string
  status: 'online' | 'offline' | 'maintenance' | 'error'
  
  capacity: {
    total: number
    available: number
    allocated: number
    reserved: number
  }
  
  labels: Record<string, string>
  
  health: {
    score: number
    checks: Array<{
      name: string
      status: 'pass' | 'fail' | 'warn'
      message?: string
      timestamp: Date
    }>
    metrics: {
      cpuUsage: number
      memoryUsage: number
      diskUsage: number
      networkLatency: number
      temperature?: number
    }
  }
  
  lastHeartbeat: Date
}

export interface ResourcePool {
  id: string
  name: string
  type: ResourceType
  
  capacity: {
    total: number
    available: number
    allocated: number
    reserved: number
  }
  
  usage: {
    current: number
    peak: number
    average: number
    history: Array<{
      timestamp: Date
      value: number
    }>
  }
  
  nodes: ResourceNode[]
  
  schedulingPolicy: {
    algorithm: 'round-robin' | 'least-loaded' | 'priority' | 'affinity'
    loadBalancing: {
      strategy: 'weighted' | 'random' | 'consistent-hashing'
      weights?: Record<string, number>
    }
  }
  
  monitoring: {
    enabled: boolean
    interval: number
    metrics: string[]
    alerts: Array<{
      id: string
      name: string
      condition: {
        metric: string
        operator: '>' | '<' | '>=' | '<=' | '==' | '!='
        threshold: number
        duration: number
      }
      severity: 'info' | 'warning' | 'critical'
    }>
  }
}

export interface ResourceAllocation {
  id: string
  taskId: string
  nodeId: string
  poolId: string
  
  resources: ResourceRequirements
  
  allocatedAt: Date
  scheduledReleaseAt?: Date
  actualReleaseAt?: Date
  
  status: 'allocated' | 'released' | 'expired'
  
  metadata: Record<string, any>
}

/**
 * 资源管理器
 */
export class ResourceManager {
  private pools: Map<string, ResourcePool> = new Map()
  private nodes: Map<string, ResourceNode> = new Map()
  private allocations: Map<string, ResourceAllocation> = new Map()
  
  private isRunning = false
  private monitoringTimer?: any
  private heartbeatTimer?: any
  
  constructor() {
    this.initializeDefaultPools()
  }
  
  /**
   * 初始化默认资源池
   */
  private initializeDefaultPools(): void {
    // CPU池
    const cpuPool: ResourcePool = {
      id: 'cpu_pool',
      name: 'CPU资源池',
      type: ResourceType.CPU,
      capacity: { total: 0, available: 0, allocated: 0, reserved: 0 },
      usage: { current: 0, peak: 0, average: 0, history: [] },
      nodes: [],
      schedulingPolicy: {
        algorithm: 'least-loaded',
        loadBalancing: { strategy: 'weighted' }
      },
      monitoring: {
        enabled: true,
        interval: 30000,
        metrics: ['cpuUsage', 'loadAverage'],
        alerts: [
          {
            id: 'cpu_high',
            name: 'CPU使用率过高',
            condition: {
              metric: 'cpuUsage',
              operator: '>',
              threshold: 90,
              duration: 300000
            },
            severity: 'warning'
          }
        ]
      }
    }
    
    // 内存池
    const memoryPool: ResourcePool = {
      id: 'memory_pool',
      name: '内存资源池',
      type: ResourceType.MEMORY,
      capacity: { total: 0, available: 0, allocated: 0, reserved: 0 },
      usage: { current: 0, peak: 0, average: 0, history: [] },
      nodes: [],
      schedulingPolicy: {
        algorithm: 'least-loaded',
        loadBalancing: { strategy: 'weighted' }
      },
      monitoring: {
        enabled: true,
        interval: 30000,
        metrics: ['memoryUsage'],
        alerts: [
          {
            id: 'memory_high',
            name: '内存使用率过高',
            condition: {
              metric: 'memoryUsage',
              operator: '>',
              threshold: 85,
              duration: 300000
            },
            severity: 'critical'
          }
        ]
      }
    }
    
    this.pools.set(cpuPool.id, cpuPool)
    this.pools.set(memoryPool.id, memoryPool)
    
    // 添加默认节点
    this.addDefaultNodes()
  }
  
  /**
   * 添加默认节点
   */
  private addDefaultNodes(): void {
    const nodes = [
      {
        id: 'node_1',
        name: '工作节点-1',
        type: 'worker',
        poolIds: ['cpu_pool', 'memory_pool'],
        capacity: { cpu: 8, memory: 16384, storage: 100000 }
      },
      {
        id: 'node_2',
        name: '工作节点-2',
        type: 'worker',
        poolIds: ['cpu_pool', 'memory_pool'],
        capacity: { cpu: 4, memory: 8192, storage: 50000 }
      },
      {
        id: 'node_3',
        name: '高性能节点',
        type: 'high-performance',
        poolIds: ['cpu_pool', 'memory_pool'],
        capacity: { cpu: 16, memory: 32768, storage: 200000 }
      }
    ]
    
    nodes.forEach(nodeConfig => {
      const node: ResourceNode = {
        id: nodeConfig.id,
        name: nodeConfig.name,
        type: nodeConfig.type,
        status: 'online',
        capacity: {
          total: nodeConfig.capacity.cpu,
          available: nodeConfig.capacity.cpu,
          allocated: 0,
          reserved: 0
        },
        labels: {
          type: nodeConfig.type,
          region: 'local'
        },
        health: {
          score: 100,
          checks: [
            {
              name: 'cpu_check',
              status: 'pass',
              message: 'CPU健康',
              timestamp: new Date()
            },
            {
              name: 'memory_check',
              status: 'pass',
              message: '内存健康',
              timestamp: new Date()
            }
          ],
          metrics: {
            cpuUsage: Math.random() * 20,
            memoryUsage: Math.random() * 30,
            diskUsage: Math.random() * 50,
            networkLatency: Math.random() * 10,
            temperature: 45 + Math.random() * 15
          }
        },
        lastHeartbeat: new Date()
      }
      
      this.addNode(node, nodeConfig.poolIds)
    })
  }
  
  /**
   * 添加节点
   */
  addNode(node: ResourceNode, poolIds: string[]): void {
    this.nodes.set(node.id, node)
    
    // 将节点添加到指定的资源池
    poolIds.forEach(poolId => {
      const pool = this.pools.get(poolId)
      if (pool) {
        pool.nodes.push(node)
        pool.capacity.total += node.capacity.total
        pool.capacity.available += node.capacity.available
      }
    })
    
    // 使用日志记录节点添加事件
    // console.log(`节点 ${node.name} (${node.id}) 已添加到资源池`)
  }
  
  /**
   * 移除节点
   */
  removeNode(nodeId: string): boolean {
    const node = this.nodes.get(nodeId)
    if (!node) {
      return false
    }
    
    // 从所有资源池中移除
    this.pools.forEach(pool => {
      const index = pool.nodes.findIndex(n => n.id === nodeId)
      if (index !== -1) {
        pool.nodes.splice(index, 1)
        pool.capacity.total -= node.capacity.total
        pool.capacity.available -= node.capacity.available
      }
    })
    
    // 释放该节点上的所有分配
    this.releaseNodeAllocations(nodeId)
    
    this.nodes.delete(nodeId)
    
    // 使用日志记录节点移除事件
    // console.log(`节点 ${node.name} (${nodeId}) 已从资源池中移除`)
    return true
  }
  
  /**
   * 分配资源
   */
  allocateResources(taskId: string, requirements: ResourceRequirements): ResourceAllocation | null {
    // 查找可用节点
    const availableNode = this.findAvailableNode(requirements)
    if (!availableNode) {
      // 使用日志记录警告信息
      // console.warn(`无法为任务 ${taskId} 找到满足要求的节点`)
      return null
    }
    
    // 创建分配记录
    const allocation: ResourceAllocation = {
      id: `alloc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      taskId,
      nodeId: availableNode.id,
      poolId: this.getNodePoolId(availableNode.id),
      resources: requirements,
      allocatedAt: new Date(),
      status: 'allocated',
      metadata: {}
    }
    
    // 更新节点容量
    availableNode.capacity.allocated += requirements.cpu
    availableNode.capacity.available -= requirements.cpu
    
    // 更新资源池容量
    const pool = this.getNodePool(availableNode.id)
    if (pool) {
      pool.capacity.allocated += requirements.cpu
      pool.capacity.available -= requirements.cpu
      pool.usage.current += requirements.cpu
      
      // 更新峰值使用量
      if (pool.usage.current > pool.usage.peak) {
        pool.usage.peak = pool.usage.current
      }
    }
    
    // 保存分配记录
    this.allocations.set(allocation.id, allocation)
    
    // 使用日志记录分配成功事件
    // console.log(`为任务 ${taskId} 在节点 ${availableNode.name} 上分配了资源`)
    return allocation
  }
  
  /**
   * 释放资源
   */
  releaseResources(allocationId: string): boolean {
    const allocation = this.allocations.get(allocationId)
    if (!allocation || allocation.status !== 'allocated') {
      return false
    }
    
    const node = this.nodes.get(allocation.nodeId)
    if (!node) {
      return false
    }
    
    // 更新节点容量
    node.capacity.allocated -= allocation.resources.cpu
    node.capacity.available += allocation.resources.cpu
    
    // 更新资源池容量
    const pool = this.getNodePool(node.id)
    if (pool) {
      pool.capacity.allocated -= allocation.resources.cpu
      pool.capacity.available += allocation.resources.cpu
      pool.usage.current -= allocation.resources.cpu
    }
    
    // 更新分配状态
    allocation.status = 'released'
    allocation.actualReleaseAt = new Date()
    
    // 使用日志记录释放成功事件
    // console.log(`已释放任务 ${allocation.taskId} 在节点 ${node.name} 上的资源`)
    return true
  }
  
  /**
   * 查找可用节点
   */
  private findAvailableNode(requirements: ResourceRequirements): ResourceNode | null {
    const eligibleNodes: ResourceNode[] = []
    
    // 查找满足资源要求的节点
    this.nodes.forEach(node => {
      if (
        node.status === 'online' &&
        node.capacity.available >= requirements.cpu &&
        node.health.score >= 80
      ) {
        eligibleNodes.push(node)
      }
    })
    
    if (eligibleNodes.length === 0) {
      return null
    }
    
    // 根据调度策略选择节点
    return this.selectNodeByPolicy(eligibleNodes, requirements)
  }
  
  /**
   * 根据调度策略选择节点
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  private selectNodeByPolicy(nodes: ResourceNode[], _requirements: ResourceRequirements): ResourceNode {
    // 默认使用最少负载策略
    // TODO: 未来可能会基于 requirements 参数进行更智能的节点选择
    return nodes.reduce((bestNode, currentNode) => {
      const bestLoad = bestNode.capacity.allocated / bestNode.capacity.total
      const currentLoad = currentNode.capacity.allocated / currentNode.capacity.total
      
      return currentLoad < bestLoad ? currentNode : bestNode
    })
  }
  
  /**
   * 获取节点所属的资源池
   */
  private getNodePool(nodeId: string): ResourcePool | null {
    for (const pool of this.pools.values()) {
      if (pool.nodes.some(node => node.id === nodeId)) {
        return pool
      }
    }
    return null
  }
  
  /**
   * 获取节点所属的资源池ID
   */
  private getNodePoolId(nodeId: string): string {
    for (const [poolId, pool] of this.pools.entries()) {
      if (pool.nodes.some(node => node.id === nodeId)) {
        return poolId
      }
    }
    return ''
  }
  
  /**
   * 释放节点上的所有分配
   */
  private releaseNodeAllocations(nodeId: string): void {
    this.allocations.forEach(allocation => {
      if (allocation.nodeId === nodeId && allocation.status === 'allocated') {
        this.releaseResources(allocation.id)
      }
    })
  }
  
  /**
   * 更新节点健康状态
   */
  updateNodeHealth(nodeId: string, healthData: Partial<ResourceNode['health']>): void {
    const node = this.nodes.get(nodeId)
    if (!node) {
      return
    }
    
    // 更新健康数据
    if (healthData.metrics) {
      Object.assign(node.health.metrics, healthData.metrics)
    }
    
    if (healthData.checks) {
      node.health.checks = healthData.checks
    }
    
    // 计算健康分数
    node.health.score = this.calculateHealthScore(node)
    
    // 更新心跳时间
    node.lastHeartbeat = new Date()
    
    // 检查节点状态
    this.checkNodeStatus(node)
  }
  
  /**
   * 计算节点健康分数
   */
  private calculateHealthScore(node: ResourceNode): number {
    let score = 100
    
    // CPU使用率影响
    if (node.health.metrics.cpuUsage > 90) {
      score -= 20
    }
    else if (node.health.metrics.cpuUsage > 75) {
      score -= 10
    }
    
    // 内存使用率影响
    if (node.health.metrics.memoryUsage > 85) {
      score -= 25
    }
    else if (node.health.metrics.memoryUsage > 70) {
      score -= 10
    }
    
    // 磁盘使用率影响
    if (node.health.metrics.diskUsage > 90) {
      score -= 15
    }
    
    // 网络延迟影响
    if (node.health.metrics.networkLatency > 100) {
      score -= 10
    }
    
    // 温度影响
    if (node.health.metrics.temperature && node.health.metrics.temperature > 80) {
      score -= 15
    }
    
    // 健康检查影响
    const failedChecks = node.health.checks.filter(check => check.status === 'fail').length
    score -= failedChecks * 20
    
    const warnChecks = node.health.checks.filter(check => check.status === 'warn').length
    score -= warnChecks * 5
    
    return Math.max(0, Math.min(100, score))
  }
  
  /**
   * 检查节点状态
   */
  private checkNodeStatus(node: ResourceNode): void {
    const timeSinceHeartbeat = Date.now() - node.lastHeartbeat.getTime()
    
    // 超过5分钟没有心跳，标记为离线
    if (timeSinceHeartbeat > 300000) {
      node.status = 'offline'
      return
    }
    
    // 健康分数过低，标记为错误
    if (node.health.score < 50) {
      node.status = 'error'
      return
    }
    
    // 否则标记为在线
    node.status = 'online'
  }
  
  /**
   * 收集资源使用统计
   */
  private collectUsageStatistics(): void {
    this.pools.forEach(pool => {
      const now = new Date()
      
      // 添加当前使用量到历史记录
      pool.usage.history.push({
        timestamp: now,
        value: pool.usage.current
      })
      
      // 保留最近100个数据点
      if (pool.usage.history.length > 100) {
        pool.usage.history.shift()
      }
      
      // 计算平均使用量
      if (pool.usage.history.length > 0) {
        const sum = pool.usage.history.reduce((total, point) => total + point.value, 0)
        pool.usage.average = sum / pool.usage.history.length
      }
    })
  }
  
  /**
   * 检查告警条件
   */
  private checkAlerts(): void {
    this.pools.forEach(pool => {
      if (!pool.monitoring.enabled) {
        return
      }
      
      pool.monitoring.alerts.forEach(alert => {
        const { metric, operator, threshold } = alert.condition
        
        // 检查每个节点
        pool.nodes.forEach(node => {
          const metricValue = this.getNodeMetricValue(node, metric)
          
          if (this.evaluateCondition(metricValue, operator, threshold)) {
            this.triggerAlert()
          }
        })
      })
    })
  }
  
  /**
   * 获取节点指标值
   */
  private getNodeMetricValue(node: ResourceNode, metric: string): number {
    switch (metric) {
      case 'cpuUsage':
        return node.health.metrics.cpuUsage
      case 'memoryUsage':
        return node.health.metrics.memoryUsage
      case 'diskUsage':
        return node.health.metrics.diskUsage
      case 'networkLatency':
        return node.health.metrics.networkLatency
      case 'temperature':
        return node.health.metrics.temperature || 0
      default:
        return 0
    }
  }
  
  /**
   * 评估告警条件
   */
  private evaluateCondition(value: number, operator: string, threshold: number): boolean {
    switch (operator) {
      case '>':
        return value > threshold
      case '<':
        return value < threshold
      case '>=':
        return value >= threshold
      case '<=':
        return value <= threshold
      case '==':
        return value === threshold
      case '!=':
        return value !== threshold
      default:
        return false
    }
  }
  
  /**
   * 触发告警
   */
  private triggerAlert(): void {
    // TODO: 实现告警触发逻辑
    // 使用日志记录告警信息
  }
  
  /**
   * 启动资源管理器
   */
  start(): void {
    this.isRunning = true
    
    // 启动监控定时器
    this.monitoringTimer = setInterval(() => {
      this.collectUsageStatistics()
      this.checkAlerts()
    }, 30000)
    
    // 启动心跳检查定时器
    this.heartbeatTimer = setInterval(() => {
      this.nodes.forEach(node => {
        this.checkNodeStatus(node)
      })
    }, 60000)
    
    // 使用日志记录启动事件
    // console.log('资源管理器已启动')
  }
  
  /**
   * 停止资源管理器
   */
  stop(): void {
    this.isRunning = false
    
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer)
      this.monitoringTimer = undefined
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = undefined
    }
    
    // 使用日志记录停止事件
    // console.log('资源管理器已停止')
  }
  
  /**
   * 获取资源池列表
   */
  getResourcePools(): ResourcePool[] {
    return Array.from(this.pools.values())
  }
  
  /**
   * 获取节点列表
   */
  getNodes(): ResourceNode[] {
    return Array.from(this.nodes.values())
  }
  
  /**
   * 获取分配列表
   */
  getAllocations(): ResourceAllocation[] {
    return Array.from(this.allocations.values())
  }
  
  /**
   * 获取资源使用统计
   */
  getResourceStatistics(): {
    totalCapacity: number
    totalAllocated: number
    totalAvailable: number
    utilizationRate: number
    nodeCount: number
    onlineNodes: number
    poolStats: Array<{
      poolId: string
      name: string
      type: string
      utilization: number
      nodeCount: number
    }>
    } {
    let totalCapacity = 0
    let totalAllocated = 0
    let totalAvailable = 0
    
    const poolStats = Array.from(this.pools.values()).map(pool => {
      totalCapacity += pool.capacity.total
      totalAllocated += pool.capacity.allocated
      totalAvailable += pool.capacity.available
      
      const utilization = pool.capacity.total > 0 
        ? (pool.capacity.allocated / pool.capacity.total) * 100 
        : 0
      
      return {
        poolId: pool.id,
        name: pool.name,
        type: pool.type,
        utilization,
        nodeCount: pool.nodes.length
      }
    })
    
    const nodeCount = this.nodes.size
    const onlineNodes = Array.from(this.nodes.values()).filter(node => node.status === 'online').length
    
    return {
      totalCapacity,
      totalAllocated,
      totalAvailable,
      utilizationRate: totalCapacity > 0 ? (totalAllocated / totalCapacity) * 100 : 0,
      nodeCount,
      onlineNodes,
      poolStats
    }
  }
  
  /**
   * 清理过期分配
   */
  cleanupExpiredAllocations(): number {
    let cleanedCount = 0
    const now = Date.now()
    
    this.allocations.forEach((allocation, allocationId) => {
      // 清理24小时前释放的分配记录
      if (
        allocation.status === 'released' &&
        allocation.actualReleaseAt &&
        now - allocation.actualReleaseAt.getTime() > 86400000
      ) {
        this.allocations.delete(allocationId)
        cleanedCount++
      }
    })
    
    // 使用日志记录清理事件
    // console.log(`清理了 ${cleanedCount} 个过期分配记录`)
    return cleanedCount
  }
}