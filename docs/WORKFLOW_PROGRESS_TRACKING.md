# 工作流进度实时追踪功能说明

## 📋 功能概述

新增了完整的工作流任务进度追踪系统,支持:
1. **自动弹出进度弹窗** - PPTist导出图片后自动启动工作流并显示进度
2. **持久化任务状态** - 后端将任务状态保存到`output/task_status/task_statuses.json`
3. **历史任务查看** - 浮动面板查看所有历史任务,可随时查看任务进度
4. **实时进度更新** - 前端每2-3秒轮询后端获取最新状态

## 🏗️ 架构设计

### 后端 (Flask)

#### 1. 任务状态持久化
**文件**: `flask_backend/app/api/workflow.py`

```python
# 全局任务状态字典
task_statuses = {}

def save_task_statuses():
    """保存到 output/task_status/task_statuses.json"""
    status_file = Path('output/task_status/task_statuses.json')
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(task_statuses, f, ensure_ascii=False, indent=2)

def update_task_status(task_id, status, message, progress, ...):
    """更新任务状态并持久化"""
    task_statuses[task_id] = {
        'status': status,  # pending/running/completed/failed
        'progress': progress,  # 0-100
        'project_name': project_name,
        'current_step': current_step,
        'total_steps': total_steps,
        'steps': [...]  # 各步骤详情
    }
    save_task_statuses()
```

#### 2. 批量导入自动启动工作流
**文件**: `flask_backend/api/batch_import.py`

```python
@batch_import_bp.route('/api/import-slides-batch', methods=['POST'])
def import_slides_batch():
    # ... 保存图片 ...
    
    # 🔧 NEW: 自动启动工作流
    workflow_id = _start_workflow_sync(project_name, slides_metadata)
    
    return jsonify({
        "success": True,
        "workflow_id": workflow_id,  # ✅ 返回任务ID
        "workflow_status_url": f"/api/workflow/status/{workflow_id}"
    })

def _start_workflow_sync(project_name, slides_metadata):
    # 生成任务ID
    task_id = f"workflow_{project_name}_{timestamp}"
    
    # 初始化任务状态
    update_task_status(task_id, 'pending', ...)
    
    # 后台线程启动工作流
    def run_workflow():
        executor = EnhancedWorkflowExecutor(...)
        result = asyncio.run(executor.start_workflow(...))
        update_task_status(task_id, 'completed', ...)
    
    thread = threading.Thread(target=run_workflow, daemon=True)
    thread.start()
    
    return task_id
```

#### 3. API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/workflow/status/<task_id>` | GET | 获取单个任务状态 |
| `/api/workflow/list` | GET | 获取所有任务列表 |
| `/api/workflow/cleanup` | POST | 清理已完成/失败任务 |
| `/api/import-slides-batch` | POST | 批量导入图片并自动启动工作流 |

### 前端 (Vue 3 + TypeScript)

#### 1. WorkflowProgress.vue (进度弹窗)
**位置**: `PPTist/src/components/WorkflowProgress.vue`

```vue
<template>
  <div class="workflow-progress-overlay">
    <div class="workflow-progress-modal">
      <h2>视频生成进度</h2>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: status.progress + '%' }"></div>
      </div>
      <div class="steps">
        <div v-for="step in status.steps" :key="step.name">
          {{ step.name }}: {{ step.status }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 每2秒轮询状态
const checkStatus = async () => {
  const response = await fetch(`/api/workflow/status/${props.workflowId}`)
  const data = await response.json()
  status.progress = data.workflow.progress
  status.steps = data.workflow.steps
}
</script>
```

#### 2. WorkflowHistoryPanel.vue (历史任务面板)
**位置**: `PPTist/src/components/WorkflowHistoryPanel.vue`

**特性**:
- 🎯 固定在屏幕右侧,可折叠/展开
- 🔄 展开时每3秒自动刷新任务列表
- 📊 显示所有任务的状态、进度、时间
- 🗑️ 支持一键清理已完成任务
- 👆 点击任务卡片可查看详细进度

```vue
<template>
  <div class="workflow-history-panel" :class="{ collapsed: isCollapsed }">
    <!-- 折叠按钮 -->
    <div class="toggle-button" @click="togglePanel">
      <span>{{ isCollapsed ? '📋' : '❌' }}</span>
    </div>
    
    <!-- 任务列表 -->
    <div v-if="!isCollapsed" class="task-list">
      <div 
        v-for="task in tasks" 
        @click="viewTaskProgress(task.task_id)"
      >
        {{ task.project_name }} - {{ task.progress }}%
      </div>
    </div>
  </div>
</template>
```

#### 3. 自动弹出逻辑
**文件**: `PPTist/src/views/Screen/BaseView.vue`

```typescript
// 批量导出完成后
const result = await fetch('/api/import-slides-batch', {
  method: 'POST',
  body: JSON.stringify({ images, projectName, auto_start_workflow: true })
})

if (result.workflow_id) {
  // 🔧 触发自定义事件,通知VideoExportButton
  const event = new CustomEvent('batchExportComplete', {
    detail: {
      success: true,
      workflow_id: result.workflow_id
    }
  })
  window.dispatchEvent(event)
}
```

**文件**: `PPTist/src/components/VideoExportButton.vue`

```typescript
// 监听批量导出完成事件
const handleExportComplete = (event: CustomEvent) => {
  const { workflow_id } = event.detail
  
  // 🎉 自动显示进度弹窗
  workflowStore.showWorkflowProgress(workflow_id)
}

window.addEventListener('batchExportComplete', handleExportComplete)
```

## 📊 数据流程

```
[前端 PPTist 导出图片]
        ↓
[POST /api/import-slides-batch]
  - 保存图片到 output/slides/
  - 保存元数据到 slides_metadata.json
  - 🔧 自动启动工作流
  - 返回 workflow_id
        ↓
[前端接收 workflow_id]
        ↓
[触发 batchExportComplete 事件]
        ↓
[VideoExportButton 监听到事件]
        ↓
[workflowStore.showWorkflowProgress(workflow_id)]
        ↓
[WorkflowProgress.vue 弹窗显示]
        ↓
[每2秒轮询 GET /api/workflow/status/{workflow_id}]
        ↓
[实时更新进度条和步骤状态]
```

## 🚀 使用方法

### 用户操作流程

1. **启动视频导出**
   - 点击编辑器中的"🎬 视频导出"按钮
   - 或使用 VideoExportButton 组件

2. **自动进入批量导出**
   - 系统自动切换到 Screen 模式
   - 逐张导出高质量图片 (2000x1125)

3. **自动启动工作流**
   - 图片导出完成后,后端自动启动工作流
   - 前端自动弹出进度弹窗

4. **实时查看进度**
   - 进度弹窗显示:
     - 当前步骤名称
     - 总进度百分比
     - 各步骤详细状态
   - 可点击关闭按钮收起弹窗

5. **查看历史任务**
   - 点击右侧"📋"按钮展开历史面板
   - 查看所有任务状态和进度
   - 点击任务卡片重新打开进度弹窗

6. **下载视频**
   - 工作流完成后,进度弹窗显示"下载视频"按钮
   - 点击下载最终生成的MP4文件

### 开发者接口

#### 手动启动工作流并显示进度

```typescript
import { useWorkflowStore } from '@/store'

const workflowStore = useWorkflowStore()

// 启动工作流
const response = await fetch('/api/workflow/execute', {
  method: 'POST',
  body: JSON.stringify({ project_name: 'my_project' })
})

const { workflow_id } = await response.json()

// 显示进度弹窗
workflowStore.showWorkflowProgress(workflow_id)
```

#### 查询任务状态

```typescript
const response = await fetch('/api/workflow/status/workflow_xxx_123456')
const { workflow } = await response.json()

console.log(workflow.status)    // 'running'
console.log(workflow.progress)  // 45
console.log(workflow.steps)     // [{ name, status, message }, ...]
```

#### 获取任务列表

```typescript
const response = await fetch('/api/workflow/list')
const { workflows } = await response.json()

Object.keys(workflows).forEach(taskId => {
  const task = workflows[taskId]
  console.log(`${task.project_name}: ${task.progress}%`)
})
```

## 🔧 配置选项

### 后端配置

**禁用自动启动工作流** (在批量导入时):

```python
# 前端请求体中添加:
{
  "projectName": "...",
  "images": [...],
  "auto_start_workflow": false  # 设置为false禁用
}
```

**修改任务保存位置**:

```python
# flask_backend/app/api/workflow.py
def save_task_statuses():
    status_file = Path('output/task_status/task_statuses.json')  # 修改此路径
```

### 前端配置

**修改轮询间隔**:

```typescript
// WorkflowProgress.vue
timer = setInterval(checkStatus, 2000)  // 改为其他毫秒数

// WorkflowHistoryPanel.vue
refreshTimer = setInterval(refreshTasks, 3000)  // 改为其他毫秒数
```

**调整历史面板位置**:

```scss
// WorkflowHistoryPanel.vue
.workflow-history-panel {
  position: fixed;
  right: 20px;   // 修改水平位置
  top: 100px;    // 修改垂直位置
}
```

## 📁 文件清单

### 后端文件

- ✅ `flask_backend/api/batch_import.py` - 批量导入+自动启动工作流
- ✅ `flask_backend/app/api/workflow.py` - 任务状态管理API
- ✅ `output/task_status/task_statuses.json` - 任务状态持久化文件

### 前端文件

- ✅ `PPTist/src/components/WorkflowProgress.vue` - 进度弹窗组件
- ✅ `PPTist/src/components/WorkflowHistoryPanel.vue` - 历史任务面板 (新增)
- ✅ `PPTist/src/views/Screen/BaseView.vue` - 批量导出触发逻辑
- ✅ `PPTist/src/components/VideoExportButton.vue` - 导出按钮+事件监听
- ✅ `PPTist/src/store/workflow.ts` - 工作流状态管理
- ✅ `PPTist/src/App.vue` - 全局组件注册

## 🐛 常见问题

### Q1: 工作流启动后没有弹出进度窗口?

**原因**: 批量导入API没有返回`workflow_id`

**解决**:
1. 检查后端日志,确认工作流是否启动成功
2. 查看浏览器控制台,检查`batchExportComplete`事件是否触发
3. 确认`batch_import.py`中`auto_start_workflow`参数为`true`

```bash
# 后端日志应该显示:
🚀 工作流已启动: workflow_xxx_1234567890
✅ 工作流线程已启动: workflow_xxx_1234567890
```

### Q2: 进度一直显示0%不更新?

**原因**: 工作流执行器没有正确调用`progress_callback`

**解决**:
1. 检查`EnhancedWorkflowExecutor`是否正确接收并调用回调函数
2. 查看`update_task_status`是否正确保存状态
3. 确认前端轮询间隔设置正确(默认2秒)

### Q3: 服务器重启后历史任务丢失?

**原因**: 任务状态保存在内存和文件中,但文件加载可能失败

**解决**:
```python
# flask_backend/app/api/workflow.py
# 确保启动时加载:
load_task_statuses()  # 在文件末尾执行
```

### Q4: 历史面板显示空白?

**原因**: API返回格式不匹配或权限问题

**解决**:
1. 测试API: `curl http://localhost:5000/api/workflow/list`
2. 检查`output/task_status/task_statuses.json`文件权限
3. 查看浏览器Network标签,确认API调用成功

## 📈 性能优化建议

1. **限制历史任务数量**
   ```python
   # 自动清理7天前的任务
   def cleanup_old_tasks():
       cutoff_date = datetime.now() - timedelta(days=7)
       task_statuses = {
           k: v for k, v in task_statuses.items()
           if datetime.fromisoformat(v['updated_at']) > cutoff_date
       }
   ```

2. **减少轮询频率**
   - 任务完成后停止轮询
   - 使用WebSocket替代轮询(高级)

3. **懒加载历史任务**
   - 只在展开面板时加载
   - 分页加载大量任务

## 🎉 功能亮点

✨ **无缝集成**: 用户无需额外操作,导出即启动  
📊 **实时反馈**: 2秒内看到最新进度  
💾 **数据持久**: 服务器重启不丢失任务状态  
🎨 **美观易用**: 现代化UI设计,支持折叠/展开  
🔧 **灵活配置**: 可禁用自动启动,手动控制工作流  

---

**版本**: v1.0  
**最后更新**: 2025-10-22  
**作者**: GitHub Copilot  
