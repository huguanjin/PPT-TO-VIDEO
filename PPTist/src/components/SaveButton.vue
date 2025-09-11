<template>
  <div class="save-controls">
    <!-- 保存按钮 -->
    <div 
      class="save-button" 
      :class="{ saving: isSaving }"
      @click="handleSave"
      v-tooltip="saveButtonTooltip"
    >
      <IconLoader class="icon loading" v-if="isSaving" />
      <IconSave class="icon" v-else />
      <span class="text">{{ isSaving ? '保存中...' : '保存' }}</span>
    </div>

    <!-- 自动保存状态 -->
    <div class="auto-save-status" v-if="showAutoSaveStatus">
      <div class="status-indicator" :class="{ active: isAutoSaveEnabled }"></div>
      <span class="status-text">{{ autoSaveStatusText }}</span>
    </div>

    <!-- 保存设置弹窗 -->
    <Popover 
      trigger="click" 
      placement="bottom-end" 
      v-model:value="showSettings"
    >
      <template #content>
        <div class="save-settings">
          <div class="setting-item">
            <label>
              <input 
                type="checkbox" 
                v-model="autoSaveConfig.enabled"
                @change="updateAutoSaveConfig"
              />
              启用自动保存
            </label>
          </div>
          
          <div class="setting-item" v-if="autoSaveConfig.enabled">
            <label>自动保存间隔（分钟）：</label>
            <input 
              type="number" 
              min="1" 
              max="60"
              v-model.number="autoSaveConfig.interval"
              @change="updateAutoSaveConfig"
              class="interval-input"
            />
          </div>
          
          <div class="setting-item">
            <button @click="handleManualSave" class="manual-save-btn">
              立即保存
            </button>
          </div>
        </div>
      </template>
      
      <div class="settings-trigger" v-tooltip="'保存设置'">
        <IconSettings class="icon" />
      </div>
    </Popover>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useWorkspaceManager } from '@/hooks/useWorkspaceManager'
import Popover from '@/components/Popover.vue'
import message from '@/utils/message'

const workspace = useWorkspaceManager()

const isSaving = ref(false)
const showSettings = ref(false)
const showAutoSaveStatus = ref(true)

// 自动保存配置
const autoSaveConfig = ref({
  enabled: true,
  interval: 3 // 3秒自动保存
})

// 保存项目
const saveProject = async (showMessage = false) => {
  try {
    const success = await workspace.saveWorkspace()
    if (success && showMessage) {
      message.success('工作空间保存成功')
    }
    return success
  }
  catch (error) {
    if (showMessage) {
      message.error('保存失败: ' + (error instanceof Error ? error.message : '未知错误'))
    }
    return false
  }
}

// 保存按钮提示文本
const saveButtonTooltip = computed(() => {
  if (isSaving.value) return '正在保存工作空间...'
  if (workspace.hasUnsavedChanges.value) return '保存更改 (Ctrl+S)'
  return '保存工作空间 (Ctrl+S)'
})

// 自动保存状态文本
const autoSaveStatusText = computed(() => {
  return workspace.workspaceStatus.value
})

// 自动保存是否启用
const isAutoSaveEnabled = computed(() => autoSaveConfig.value.enabled)

// 手动保存
const handleSave = async () => {
  if (isSaving.value) return
  
  try {
    isSaving.value = true
    await saveProject(true) // 显示保存消息
  }
  finally {
    isSaving.value = false
  }
}

// 立即保存
const handleManualSave = async () => {
  showSettings.value = false
  await handleSave()
}

// 更新自动保存配置
const updateAutoSaveConfig = () => {
  // 工作空间管理器自动处理自动保存
}
</script>

<style lang="scss" scoped>
.save-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.save-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  
  .icon {
    font-size: 16px;
    
    &.loading {
      animation: spin 1s linear infinite;
    }
  }
  
  &:hover {
    background: linear-gradient(135deg, #218838 0%, #1e9d5b 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
  }
  
  &.saving {
    background: linear-gradient(135deg, #6c757d 0%, #868e96 100%);
    cursor: not-allowed;
    
    &:hover {
      transform: none;
      box-shadow: none;
    }
  }
}

.auto-save-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #dc3545;
    transition: background-color 0.3s ease;
    
    &.active {
      background: #28a745;
      animation: pulse 2s infinite;
    }
  }
}

.settings-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  
  .icon {
    font-size: 16px;
    color: #666;
  }
  
  &:hover {
    background: rgba(0, 0, 0, 0.1);
  }
}

.save-settings {
  padding: 12px;
  min-width: 200px;
  
  .setting-item {
    margin-bottom: 12px;
    
    label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      cursor: pointer;
    }
    
    .interval-input {
      width: 60px;
      padding: 4px 6px;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-left: 8px;
    }
    
    .manual-save-btn {
      width: 100%;
      padding: 8px 12px;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      
      &:hover {
        background: #0056b3;
      }
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
