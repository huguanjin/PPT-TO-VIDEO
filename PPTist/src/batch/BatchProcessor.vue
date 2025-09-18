<template>
  <div class="batch-processor">
    <!-- 头部控制栏 -->
    <div class="header-controls">
      <div class="title-section">
        <h2>{{ $t('batch.title') }}</h2>
        <div class="status-indicator" :class="statusClass">
          <Icon :name="statusIcon" />
          <span>{{ statusText }}</span>
        </div>
      </div>
      
      <div class="action-buttons">
        <a-button 
          type="primary" 
          @click="showCreateWorkflow = true"
          :disabled="!engineStatus.isRunning"
        >
          <Icon name="plus" />
          {{ $t('batch.createWorkflow') }}
        </a-button>
        
        <a-button 
          @click="refreshData"
          :loading="refreshing"
        >
          <Icon name="refresh" />
          {{ $t('common.refresh') }}
        </a-button>
        
        <a-button 
          :type="engineStatus.isRunning ? 'danger' : 'primary'"
          @click="toggleEngine"
          :loading="engineToggling"
        >
          <Icon :name="engineStatus.isRunning ? 'pause' : 'play'" />
          {{ engineStatus.isRunning ? $t('batch.stopEngine') : $t('batch.startEngine') }}
        </a-button>
      </div>
    </div>

    <!-- 统计面板 -->
    <div class="statistics-panel">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ engineStatus.workflowCount }}</div>
              <div class="stat-label">{{ $t('batch.totalWorkflows') }}</div>
            </div>
            <Icon name="workflow" class="stat-icon" />
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ engineStatus.runningExecutions }}</div>
              <div class="stat-label">{{ $t('batch.runningExecutions') }}</div>
            </div>
            <Icon name="play-circle" class="stat-icon running" />
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ queueStats.pendingTasks }}</div>
              <div class="stat-label">{{ $t('batch.pendingTasks') }}</div>
            </div>
            <Icon name="clock" class="stat-icon pending" />
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ Math.round(queueStats.healthScore) }}%</div>
              <div class="stat-label">{{ $t('batch.healthScore') }}</div>
            </div>
            <Icon name="heart" :class="['stat-icon', healthClass]" />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <a-tabs v-model:activeKey="activeTab" @change="onTabChange">
        <!-- 工作流列表 -->
        <a-tab-pane key="workflows" :tab="$t('batch.workflows')">
          <WorkflowList 
            :workflows="workflows"
            :loading="workflowsLoading"
            @execute="executeWorkflow"
            @edit="editWorkflow"
            @delete="deleteWorkflow"
            @duplicate="duplicateWorkflow"
          />
        </a-tab-pane>
        
        <!-- 执行历史 -->
        <a-tab-pane key="executions" :tab="$t('batch.executions')">
          <ExecutionList 
            :executions="executions"
            :loading="executionsLoading"
            @view="viewExecution"
            @cancel="cancelExecution"
            @retry="retryExecution"
          />
        </a-tab-pane>
        
        <!-- 任务队列 -->
        <a-tab-pane key="tasks" :tab="$t('batch.taskQueue')">
          <TaskQueue 
            :tasks="tasks"
            :statistics="queueStats"
            :loading="tasksLoading"
            @cancel="cancelTask"
            @retry="retryTask"
          />
        </a-tab-pane>
        
        <!-- 监控面板 -->
        <a-tab-pane key="monitoring" :tab="$t('batch.monitoring')">
          <MonitoringPanel 
            :engine-status="engineStatus"
            :queue-stats="queueStats"
            :performance-data="performanceData"
          />
        </a-tab-pane>
      </a-tabs>
    </div>

    <!-- 创建工作流对话框 -->
    <WorkflowCreateModal
      v-model:visible="showCreateWorkflow"
      @created="onWorkflowCreated"
    />
    
    <!-- 编辑工作流对话框 -->
    <WorkflowEditModal
      v-model:visible="showEditWorkflow"
      :workflow="editingWorkflow"
      @updated="onWorkflowUpdated"
    />
    
    <!-- 执行详情对话框 -->
    <ExecutionDetailModal
      v-model:visible="showExecutionDetail"
      :execution="viewingExecution"
    />
    
    <!-- 执行参数对话框 -->
    <ExecutionParametersModal
      v-model:visible="showExecutionParams"
      :workflow="executingWorkflow"
      @execute="onExecuteWorkflow"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import Icon from '@/components/Icon.vue'
import WorkflowList from './WorkflowList.vue'
import ExecutionList from './ExecutionList.vue'
import TaskQueue from './TaskQueue.vue'
import MonitoringPanel from './MonitoringPanel.vue'
import WorkflowCreateModal from './WorkflowCreateModal.vue'
import WorkflowEditModal from './WorkflowEditModal.vue'
import ExecutionDetailModal from './ExecutionDetailModal.vue'
import ExecutionParametersModal from './ExecutionParametersModal.vue'

const { t } = useI18n()

// 响应式数据
const activeTab = ref('workflows')
const refreshing = ref(false)
const engineToggling = ref(false)

// 加载状态
const workflowsLoading = ref(false)
const executionsLoading = ref(false)
const tasksLoading = ref(false)

// 模态框状态
const showCreateWorkflow = ref(false)
const showEditWorkflow = ref(false)
const showExecutionDetail = ref(false)
const showExecutionParams = ref(false)

// 数据状态
const workflows = ref([])
const executions = ref([])
const tasks = ref([])
const editingWorkflow = ref(null)
const viewingExecution = ref(null)
const executingWorkflow = ref(null)

// 引擎状态
const engineStatus = reactive({
  isRunning: false,
  workflowCount: 0,
  executionCount: 0,
  runningExecutions: 0,
  taskQueueStatus: null
})

// 队列统计
const queueStats = reactive({
  totalTasks: 0,
  pendingTasks: 0,
  runningTasks: 0,
  completedTasks: 0,
  failedTasks: 0,
  averageExecutionTime: 0,
  throughput: 0,
  healthScore: 100
})

// 性能数据
const performanceData = ref({
  cpuUsage: [],
  memoryUsage: [],
  taskThroughput: []
})

// 定时器
let statusTimer: NodeJS.Timeout | null = null
let metricsTimer: NodeJS.Timeout | null = null

// 计算属性
const statusClass = computed(() => {
  if (!engineStatus.isRunning) return 'status-stopped'
  if (engineStatus.runningExecutions > 0) return 'status-running'
  return 'status-idle'
})

const statusIcon = computed(() => {
  if (!engineStatus.isRunning) return 'stop-circle'
  if (engineStatus.runningExecutions > 0) return 'play-circle'
  return 'pause-circle'
})

const statusText = computed(() => {
  if (!engineStatus.isRunning) return t('batch.status.stopped')
  if (engineStatus.runningExecutions > 0) return t('batch.status.running')
  return t('batch.status.idle')
})

const healthClass = computed(() => {
  const score = queueStats.healthScore
  if (score >= 80) return 'healthy'
  if (score >= 60) return 'warning'
  return 'critical'
})

// 方法
const refreshData = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      loadWorkflows(),
      loadExecutions(),
      loadTasks(),
      loadEngineStatus()
    ])
  } catch (error) {
    message.error(t('batch.errors.refreshFailed'))
    console.error('Refresh data failed:', error)
  } finally {
    refreshing.value = false
  }
}

const loadWorkflows = async () => {
  workflowsLoading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    workflows.value = [
      {
        id: 'workflow_1',
        name: 'PPT转视频工作流',
        description: '将PPT文件转换为视频',
        status: 'draft',
        version: '1.0.0',
        createdAt: new Date(),
        steps: 4
      },
      {
        id: 'workflow_2', 
        name: '批量处理工作流',
        description: '批量处理多个文件',
        status: 'scheduled',
        version: '1.1.0',
        createdAt: new Date(),
        steps: 6
      }
    ]
  } finally {
    workflowsLoading.value = false
  }
}

const loadExecutions = async () => {
  executionsLoading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 300))
    executions.value = [
      {
        id: 'exec_1',
        workflowId: 'workflow_1',
        workflowName: 'PPT转视频工作流',
        status: 'running',
        startTime: new Date(),
        progress: 65,
        completedSteps: 2,
        totalSteps: 4
      },
      {
        id: 'exec_2',
        workflowId: 'workflow_2',
        workflowName: '批量处理工作流',
        status: 'completed',
        startTime: new Date(Date.now() - 300000),
        endTime: new Date(),
        duration: 280000,
        completedSteps: 6,
        totalSteps: 6
      }
    ]
  } finally {
    executionsLoading.value = false
  }
}

const loadTasks = async () => {
  tasksLoading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 200))
    tasks.value = [
      {
        id: 'task_1',
        name: 'PPT内容提取',
        status: 'running',
        priority: 2,
        progress: 80,
        startTime: new Date(),
        executionId: 'exec_1'
      },
      {
        id: 'task_2',
        name: '语音合成',
        status: 'pending',
        priority: 2,
        progress: 0,
        executionId: 'exec_1'
      }
    ]
  } finally {
    tasksLoading.value = false
  }
}

const loadEngineStatus = async () => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 100))
    
    Object.assign(engineStatus, {
      isRunning: true,
      workflowCount: workflows.value.length,
      executionCount: executions.value.length,
      runningExecutions: executions.value.filter(e => e.status === 'running').length
    })
    
    Object.assign(queueStats, {
      totalTasks: 50,
      pendingTasks: 8,
      runningTasks: 2,
      completedTasks: 35,
      failedTasks: 5,
      averageExecutionTime: 12000,
      throughput: 4.2,
      healthScore: 85
    })
  } catch (error) {
    console.error('Load engine status failed:', error)
  }
}

const toggleEngine = async () => {
  engineToggling.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    engineStatus.isRunning = !engineStatus.isRunning
    
    if (engineStatus.isRunning) {
      message.success(t('batch.messages.engineStarted'))
    } else {
      message.success(t('batch.messages.engineStopped'))
    }
  } catch (error) {
    message.error(t('batch.errors.engineToggleFailed'))
    console.error('Toggle engine failed:', error)
  } finally {
    engineToggling.value = false
  }
}

const executeWorkflow = (workflow: any) => {
  executingWorkflow.value = workflow
  showExecutionParams.value = true
}

const editWorkflow = (workflow: any) => {
  editingWorkflow.value = workflow
  showEditWorkflow.value = true
}

const deleteWorkflow = async (workflowId: string) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    workflows.value = workflows.value.filter(w => w.id !== workflowId)
    message.success(t('batch.messages.workflowDeleted'))
  } catch (error) {
    message.error(t('batch.errors.deleteFailed'))
    console.error('Delete workflow failed:', error)
  }
}

const duplicateWorkflow = async (workflow: any) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 300))
    
    const newWorkflow = {
      ...workflow,
      id: `workflow_${Date.now()}`,
      name: `${workflow.name} (副本)`,
      createdAt: new Date()
    }
    
    workflows.value.push(newWorkflow)
    message.success(t('batch.messages.workflowDuplicated'))
  } catch (error) {
    message.error(t('batch.errors.duplicateFailed'))
    console.error('Duplicate workflow failed:', error)
  }
}

const viewExecution = (execution: any) => {
  viewingExecution.value = execution
  showExecutionDetail.value = true
}

const cancelExecution = async (executionId: string) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 300))
    
    const execution = executions.value.find(e => e.id === executionId)
    if (execution) {
      execution.status = 'cancelled'
      execution.endTime = new Date()
    }
    
    message.success(t('batch.messages.executionCancelled'))
  } catch (error) {
    message.error(t('batch.errors.cancelFailed'))
    console.error('Cancel execution failed:', error)
  }
}

const retryExecution = async (executionId: string) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const execution = executions.value.find(e => e.id === executionId)
    if (execution) {
      execution.status = 'running'
      execution.startTime = new Date()
      execution.progress = 0
      execution.completedSteps = 0
      delete execution.endTime
    }
    
    message.success(t('batch.messages.executionRetried'))
  } catch (error) {
    message.error(t('batch.errors.retryFailed'))
    console.error('Retry execution failed:', error)
  }
}

const cancelTask = async (taskId: string) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 200))
    
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.status = 'cancelled'
    }
    
    message.success(t('batch.messages.taskCancelled'))
  } catch (error) {
    message.error(t('batch.errors.taskCancelFailed'))
    console.error('Cancel task failed:', error)
  }
}

const retryTask = async (taskId: string) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 300))
    
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.status = 'pending'
      task.progress = 0
    }
    
    message.success(t('batch.messages.taskRetried'))
  } catch (error) {
    message.error(t('batch.errors.taskRetryFailed'))
    console.error('Retry task failed:', error)
  }
}

const onTabChange = (key: string) => {
  // 切换标签时刷新对应数据
  switch (key) {
    case 'workflows':
      loadWorkflows()
      break
    case 'executions':
      loadExecutions()
      break
    case 'tasks':
      loadTasks()
      break
  }
}

const onWorkflowCreated = (workflow: any) => {
  workflows.value.push(workflow)
  message.success(t('batch.messages.workflowCreated'))
}

const onWorkflowUpdated = (workflow: any) => {
  const index = workflows.value.findIndex(w => w.id === workflow.id)
  if (index !== -1) {
    workflows.value[index] = workflow
  }
  message.success(t('batch.messages.workflowUpdated'))
}

const onExecuteWorkflow = async (params: any) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const newExecution = {
      id: `exec_${Date.now()}`,
      workflowId: executingWorkflow.value.id,
      workflowName: executingWorkflow.value.name,
      status: 'running',
      startTime: new Date(),
      progress: 0,
      completedSteps: 0,
      totalSteps: executingWorkflow.value.steps,
      parameters: params
    }
    
    executions.value.unshift(newExecution)
    
    // 切换到执行历史标签
    activeTab.value = 'executions'
    
    message.success(t('batch.messages.workflowExecuted'))
  } catch (error) {
    message.error(t('batch.errors.executeFailed'))
    console.error('Execute workflow failed:', error)
  }
}

// 启动定时更新
const startTimers = () => {
  // 每5秒更新状态
  statusTimer = setInterval(loadEngineStatus, 5000)
  
  // 每30秒收集性能数据
  metricsTimer = setInterval(() => {
    const now = new Date()
    
    // 模拟性能数据
    performanceData.value.cpuUsage.push({
      time: now,
      value: Math.random() * 100
    })
    
    performanceData.value.memoryUsage.push({
      time: now,
      value: Math.random() * 100
    })
    
    performanceData.value.taskThroughput.push({
      time: now,
      value: Math.random() * 10
    })
    
    // 保留最近50个数据点
    if (performanceData.value.cpuUsage.length > 50) {
      performanceData.value.cpuUsage.shift()
      performanceData.value.memoryUsage.shift()
      performanceData.value.taskThroughput.shift()
    }
  }, 30000)
}

const stopTimers = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  if (metricsTimer) {
    clearInterval(metricsTimer)
    metricsTimer = null
  }
}

// 生命周期钩子
onMounted(() => {
  refreshData()
  startTimers()
})

onUnmounted(() => {
  stopTimers()
})
</script>

<style scoped>
.batch-processor {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-section h2 {
  margin: 0;
  color: #1f2937;
  font-weight: 600;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-indicator.status-running {
  background: #dcfce7;
  color: #166534;
}

.status-indicator.status-idle {
  background: #fef3c7;
  color: #92400e;
}

.status-indicator.status-stopped {
  background: #fee2e2;
  color: #dc2626;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.statistics-panel {
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card .ant-card-body {
  padding: 20px;
}

.stat-content {
  position: relative;
  z-index: 2;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.stat-icon {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 32px;
  color: #e5e7eb;
  z-index: 1;
}

.stat-icon.running {
  color: #10b981;
}

.stat-icon.pending {
  color: #f59e0b;
}

.stat-icon.healthy {
  color: #10b981;
}

.stat-icon.warning {
  color: #f59e0b;
}

.stat-icon.critical {
  color: #ef4444;
}

.main-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.main-content :deep(.ant-tabs-content-holder) {
  padding: 24px;
}

.main-content :deep(.ant-tabs-tab) {
  padding: 12px 20px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-processor {
    padding: 16px;
  }
  
  .header-controls {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .title-section {
    justify-content: center;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .statistics-panel :deep(.ant-col) {
    margin-bottom: 16px;
  }
}

@media (max-width: 480px) {
  .action-buttons {
    flex-direction: column;
  }
  
  .statistics-panel :deep(.ant-row) {
    flex-direction: column;
  }
  
  .statistics-panel :deep(.ant-col) {
    width: 100% !important;
    flex: none;
  }
}
</style>