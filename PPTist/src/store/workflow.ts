import { defineStore } from 'pinia'

export interface WorkflowProgressState {
  showProgress: boolean
  workflowId: string
}

export const useWorkflowStore = defineStore('workflow', {
  state: (): WorkflowProgressState => ({
    showProgress: false,
    workflowId: ''
  }),

  actions: {
    showWorkflowProgress(workflowId: string) {
      this.workflowId = workflowId
      this.showProgress = true
      // eslint-disable-next-line no-console
      console.log('🎬 [WorkflowStore] 显示工作流进度:', workflowId)
    },

    hideWorkflowProgress() {
      this.showProgress = false
      this.workflowId = ''
      // eslint-disable-next-line no-console
      console.log('🛑 [WorkflowStore] 隐藏工作流进度')
    }
  }
})
