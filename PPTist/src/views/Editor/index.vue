<template>
  <div class="pptist-editor">
    <!-- 工作空间状态栏 -->
    <div class="workspace-bar" v-if="workspace.currentTitle.value">
      <div class="workspace-info">
        <i class="icon-document">📄</i>
        <span class="title">{{ workspace.currentTitle.value }}</span>
        <span class="status">{{ workspace.workspaceStatus.value }}</span>
      </div>
      <div class="workspace-actions">
        <button 
          class="history-btn"
          @click="showArchiveManager"
          title="查看归档"
        >
          <i class="icon-history">📚</i>
          历史项目
        </button>
      </div>
    </div>

    <EditorHeader class="layout-header" />
    <div class="layout-content">
      <Thumbnails class="layout-content-left" />
      <div class="layout-content-center">
        <CanvasTool class="center-top" />
        <Canvas class="center-body" :style="{ height: `calc(100% - ${remarkHeight + 40}px)` }" />
        <Remark
          class="center-bottom" 
          v-model:height="remarkHeight" 
          :style="{ height: `${remarkHeight}px` }"
        />
      </div>
      <Toolbar class="layout-content-right" />
    </div>
  </div>

  <SelectPanel v-if="showSelectPanel" />
  <SearchPanel v-if="showSearchPanel" />
  <NotesPanel v-if="showNotesPanel" />
  <MarkupPanel v-if="showMarkupPanel" />

  <!-- 归档管理弹窗 -->
  <Modal v-model:visible="showArchiveList" :width="800">
    <ArchiveManager
      :archives="workspace.archives.value"
      :loading="workspace.isLoading.value"
      @restore="handleRestoreArchive"
      @delete="handleDeleteArchive"
      @refresh="() => workspace.loadArchiveList()"
      @close="showArchiveList = false"
    />
  </Modal>

  <Modal
    :visible="!!dialogForExport" 
    :width="680"
    @closed="closeExportDialog()"
  >
    <ExportDialog />
  </Modal>

  <Modal
    :visible="showAIPPTDialog" 
    :width="720"
    :closeOnClickMask="false"
    :closeOnEsc="false"
    closeButton
    @closed="closeAIPPTDialog()"
  >
    <AIPPTDialog />
  </Modal>

  <!-- 通知管理器 -->
  <NotificationManager ref="notificationManager" />

  <!-- 确认对话框 -->
  <ConfirmDialog
    v-model:visible="showDeleteConfirm"
    title="删除归档"
    :message="`确定要删除归档 '${deleteTarget}' 吗？此操作不可撤销。`"
    :variant="'danger'"
    @confirm="confirmDeleteArchive"
    @cancel="cancelDeleteArchive"
  />
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useMainStore } from '@/store'
import useGlobalHotkey from '@/hooks/useGlobalHotkey'
import usePasteEvent from '@/hooks/usePasteEvent'
import { useWorkspaceManager } from '@/hooks/useWorkspaceManager'

import EditorHeader from './EditorHeader/index.vue'
import Canvas from './Canvas/index.vue'
import CanvasTool from './CanvasTool/index.vue'
import Thumbnails from './Thumbnails/index.vue'
import Toolbar from './Toolbar/index.vue'
import Remark from './Remark/index.vue'
import ExportDialog from './ExportDialog/index.vue'
import SelectPanel from './SelectPanel.vue'
import SearchPanel from './SearchPanel.vue'
import NotesPanel from './NotesPanel.vue'
import MarkupPanel from './MarkupPanel.vue'
import AIPPTDialog from './AIPPTDialog.vue'
import Modal from '@/components/Modal.vue'
import ArchiveManager from '../../components/ArchiveManager.vue'
import NotificationManager from '../../components/NotificationManager.vue'
import ConfirmDialog from '../../components/ConfirmDialog.vue'

const mainStore = useMainStore()
const { dialogForExport, showSelectPanel, showSearchPanel, showNotesPanel, showMarkupPanel, showAIPPTDialog } = storeToRefs(mainStore)
const closeExportDialog = () => mainStore.setDialogForExport('')
const closeAIPPTDialog = () => mainStore.setAIPPTDialogState(false)

const remarkHeight = ref(240) // 增加默认高度到240px，提供更好的编辑体验

// 工作空间管理
const workspace = useWorkspaceManager()
const showArchiveList = ref(false)

// 通知和确认对话框
const notificationManager = ref<InstanceType<typeof NotificationManager> | null>(null)
const showDeleteConfirm = ref(false)
const deleteTarget = ref<string>('')

// 显示归档管理器
const showArchiveManager = async () => {
  try {
    await workspace.loadArchiveList()
    showArchiveList.value = true
  }
  catch (error: any) {
    notificationManager.value?.error(`获取归档列表失败: ${error.message || '未知错误'}`)
  }
}

// 恢复归档
const handleRestoreArchive = async (folderName: string) => {
  try {
    const success = await workspace.restoreArchive(folderName)
    if (success) {
      showArchiveList.value = false
      notificationManager.value?.success('归档恢复成功！')
    }
  } 
  catch (error: any) {
    notificationManager.value?.error(`恢复失败: ${error.message || '未知错误'}`)
  }
}

// 删除归档
const handleDeleteArchive = (folderName: string) => {
  deleteTarget.value = folderName
  showDeleteConfirm.value = true
}

// 确认删除归档
const confirmDeleteArchive = async () => {
  showDeleteConfirm.value = false
  try {
    const success = await workspace.deleteArchive(deleteTarget.value)
    if (success) {
      notificationManager.value?.success('归档删除成功！')
    }
  }
  catch (error: any) {
    notificationManager.value?.error(`删除失败: ${error.message || '未知错误'}`)
  }
  deleteTarget.value = ''
}

// 取消删除
const cancelDeleteArchive = () => {
  showDeleteConfirm.value = false
  deleteTarget.value = ''
}

// 初始化
onMounted(async () => {
  // 初始化工作空间
  try {
    await workspace.initializeWorkspace()
    notificationManager.value?.info('工作空间已加载', 3000)
  }
  catch (error: any) {
    notificationManager.value?.error(`工作空间初始化失败: ${error.message || '未知错误'}`)
  }
})

useGlobalHotkey()
usePasteEvent()

// 工作空间管理器已在onMounted中初始化
</script>

<style lang="scss" scoped>
.pptist-editor {
  height: 100%;
}

.workspace-bar {
  height: 36px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 13px;
  
  .workspace-info {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .icon-document {
      font-size: 14px;
    }
    
    .title {
      font-weight: 500;
      color: #333;
    }
    
    .status {
      color: #666;
      font-size: 12px;
    }
  }
  
  .workspace-actions {
    display: flex;
    gap: 8px;
    
    button {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 4px 8px;
      border: 1px solid #d0d0d0;
      background: #fff;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
      
      &:hover {
        background: #f0f0f0;
        border-color: #b0b0b0;
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      i {
        font-size: 12px;
      }
    }
    
    .history-btn {
      color: #666;
    }
  }
}

.layout-header {
  height: 40px;
}

.layout-content {
  height: calc(100% - 40px - 36px); // 减去workspace-bar的高度
  display: flex;
}

.layout-content-left {
  width: 160px;
  height: 100%;
  flex-shrink: 0;
}

.layout-content-center {
  width: calc(100% - 160px - 260px);

  .center-top {
    height: 40px;
  }
}

.layout-content-right {
  width: 260px;
  height: 100%;
}
</style>