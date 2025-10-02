<template>
  <div class="editor-header">
    <div class="left">
      <Popover trigger="click" placement="bottom-start" v-model:value="mainMenuVisible">
        <template #content>
          <PopoverMenuItem @click="openAIPPTDialog(); mainMenuVisible = false">AI 生成 PPT</PopoverMenuItem>
          <PopoverMenuItem @click="showProjectManager = true; mainMenuVisible = false">项目管理</PopoverMenuItem>
          <FileInput accept="application/vnd.openxmlformats-officedocument.presentationml.presentation"  @change="files => {
            importPPTXFile(files)
            mainMenuVisible = false
          }">
            <PopoverMenuItem>导入 PPTX 文件（测试）</PopoverMenuItem>
          </FileInput>
          <FileInput accept=".json"  @change="files => {
            importJSON(files)
            mainMenuVisible = false
          }">
            <PopoverMenuItem>导入 JSON 文件（测试）</PopoverMenuItem>
          </FileInput>
          <FileInput accept=".pptist"  @change="files => {
            importSpecificFile(files)
            mainMenuVisible = false
          }">
            <PopoverMenuItem>导入 pptist 文件</PopoverMenuItem>
          </FileInput>
          <PopoverMenuItem @click="setDialogForExport('pptx')">导出文件</PopoverMenuItem>
          <PopoverMenuItem @click="resetSlides(); mainMenuVisible = false">重置幻灯片</PopoverMenuItem>
          <PopoverMenuItem @click="openMarkupPanel(); mainMenuVisible = false">幻灯片类型标注</PopoverMenuItem>
          <PopoverMenuItem @click="goLink('https://github.com/pipipi-pikachu/PPTist/issues')">意见反馈</PopoverMenuItem>
          <PopoverMenuItem @click="goLink('https://github.com/pipipi-pikachu/PPTist/blob/master/doc/Q&A.md')">常见问题</PopoverMenuItem>
          <PopoverMenuItem @click="mainMenuVisible = false; hotkeyDrawerVisible = true">快捷操作</PopoverMenuItem>
          <!-- 开发模式测试入口 -->
          <PopoverMenuItem v-if="isDevelopment" @click="showUnifiedConfigTest = true; mainMenuVisible = false">
            <span style="color: #ff6b35;">🧪 API测试页面</span>
          </PopoverMenuItem>
          <PopoverMenuItem v-if="isDevelopment" @click="showConfigCenter = true; mainMenuVisible = false">
            <span style="color: #27ae60;">⚙️ 配置中心</span>
          </PopoverMenuItem>
        </template>
        <div class="menu-item"><IconHamburgerButton class="icon" /></div>
      </Popover>

      <div class="title">
        <Input 
          class="title-input" 
          ref="titleInputRef"
          v-model:value="titleValue" 
          @blur="handleUpdateTitle()" 
          v-if="editingTitle" 
        ></Input>
        <div 
          class="title-text"
          @click="startEditTitle()"
          :title="title"
          v-else
        >{{ title }}</div>
      </div>
    </div>

    <div class="right">
      <SaveButton />
      
      <!-- 自动保存开关 -->
      <div class="auto-save-toggle" v-tooltip="autoSaveConfig.enabled ? '自动保存：开启' : '自动保存：关闭'">
        <div class="toggle-label">自动保存</div>
        <div 
          class="toggle-switch" 
          :class="{ 'active': autoSaveConfig.enabled }"
          @click="toggleAutoSave"
        >
          <div class="toggle-slider"></div>
        </div>
      </div>
      
      <VideoExportButton />
      <div class="menu-item unified-config-btn" v-tooltip="'项目配置'" @click="showUnifiedConfig = true">
        <IconFormat class="icon" />
        <span class="text">配置</span>
      </div>
      <div class="group-menu-item">
        <div class="menu-item" v-tooltip="'幻灯片放映（F5）'" @click="enterScreening()">
          <IconPpt class="icon" />
        </div>
        <Popover trigger="click" center>
          <template #content>
            <PopoverMenuItem @click="enterScreeningFromStart()">从头开始</PopoverMenuItem>
            <PopoverMenuItem @click="enterScreening()">从当前页开始</PopoverMenuItem>
          </template>
          <div class="arrow-btn"><IconDown class="arrow" /></div>
        </Popover>
      </div>
      <div class="menu-item" v-tooltip="'AI生成PPT'" @click="openAIPPTDialog(); mainMenuVisible = false">
        <span class="text ai">AI</span>
      </div>
      <div class="menu-item" v-tooltip="'导出'" @click="setDialogForExport('pptx')">
        <IconDownload class="icon" />
      </div>
      <a class="github-link" v-tooltip="'速擎智能API'" href="https://github.com/huguanjin/PPT-TO-VIDEO" target="_blank">
        <div class="menu-item"><IconGithub class="icon" /></div>
      </a>
    </div>

    <Drawer
      :width="320"
      v-model:visible="hotkeyDrawerVisible"
      placement="right"
    >
      <HotkeyDoc />
      <template v-slot:title>快捷操作</template>
    </Drawer>

    <!-- 批量导出进度显示 -->
    <div v-if="batchExporting" class="batch-export-progress-overlay">
      <div class="progress-content">
        <div class="progress-title">{{ exportStatus }}</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: exportProgress + '%' }"></div>
        </div>
        <div class="progress-text">{{ exportProgress }}%</div>
      </div>
    </div>

    <FullscreenSpin :loading="exporting" tip="正在导入..." />

    <!-- 统一配置模态框 -->
    <div v-if="showUnifiedConfig" class="unified-config-modal" @click="showUnifiedConfig = false">
      <div class="modal-content" @click.stop>
        <UnifiedConfig @close="showUnifiedConfig = false" />
      </div>
    </div>

    <!-- 项目管理模态框 -->
    <div v-if="showProjectManager" class="project-manager-modal" @click="showProjectManager = false">
      <div class="modal-content" @click.stop>
        <EnhancedProjectManager @close="showProjectManager = false" />
      </div>
    </div>

    <!-- API测试页面模态框 -->
    <div v-if="showUnifiedConfigTest" class="unified-config-test-modal" @click="showUnifiedConfigTest = false">
      <div class="modal-content large" @click.stop>
        <UnifiedConfigTest @close="showUnifiedConfigTest = false" />
      </div>
    </div>

    <!-- 配置中心模态框 -->
    <div v-if="showConfigCenter" class="config-center-modal" @click="showConfigCenter = false">
      <div class="modal-content large" @click.stop>
        <ConfigCenter @close="showConfigCenter = false" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { nextTick, ref, useTemplateRef } from 'vue'
import { storeToRefs } from 'pinia'
import { useMainStore, useSlidesStore } from '@/store'
import useScreening from '@/hooks/useScreening'
import useImport from '@/hooks/useImport'
import useSlideHandler from '@/hooks/useSlideHandler'
import { useProjectManager } from '@/hooks/useProjectManager'
import { useBatchExport } from '@/views/Screen/hooks/useBatchExport'
import type { DialogForExportTypes } from '@/types/export'

import HotkeyDoc from './HotkeyDoc.vue'
import FileInput from '@/components/FileInput.vue'
import FullscreenSpin from '@/components/FullscreenSpin.vue'
import Drawer from '@/components/Drawer.vue'
import Input from '@/components/Input.vue'
import Popover from '@/components/Popover.vue'
import PopoverMenuItem from '@/components/PopoverMenuItem.vue'
import VideoExportButton from '@/components/VideoExportButton.vue'
import SaveButton from '@/components/SaveButton.vue'
import EnhancedProjectManager from '@/components/EnhancedProjectManager.vue'
import UnifiedConfig from '@/views/UnifiedConfigSimple.vue'
import UnifiedConfigTest from '@/views/UnifiedConfigTest.vue'
import ConfigCenter from '@/views/ConfigCenter.vue'

const mainStore = useMainStore()
const slidesStore = useSlidesStore()
const { title } = storeToRefs(slidesStore)
const { enterScreening, enterScreeningFromStart } = useScreening()
const { importSpecificFile, importPPTXFile, importJSON, exporting } = useImport()
const { resetSlides } = useSlideHandler()

// 项目管理
const { autoSaveConfig, toggleAutoSave } = useProjectManager()

// 批量导出
const { exporting: batchExporting, exportProgress, exportStatus } = useBatchExport()

const mainMenuVisible = ref(false)
const hotkeyDrawerVisible = ref(false)
const editingTitle = ref(false)
const showUnifiedConfig = ref(false)
const showProjectManager = ref(false)
const showUnifiedConfigTest = ref(false)
const showConfigCenter = ref(false)
const titleValue = ref('')
const titleInputRef = useTemplateRef<InstanceType<typeof Input>>('titleInputRef')

// 开发模式检测
const isDevelopment = import.meta.env.DEV

const startEditTitle = () => {
  titleValue.value = title.value
  editingTitle.value = true
  nextTick(() => titleInputRef.value?.focus())
}

const handleUpdateTitle = () => {
  slidesStore.setTitle(titleValue.value)
  editingTitle.value = false
}

const goLink = (url: string) => {
  window.open(url)
  mainMenuVisible.value = false
}

const setDialogForExport = (type: DialogForExportTypes) => {
  mainStore.setDialogForExport(type)
  mainMenuVisible.value = false
}

const openMarkupPanel = () => {
  mainStore.setMarkupPanelState(true)
}

const openAIPPTDialog = () => {
  mainStore.setAIPPTDialogState(true)
}
</script>

<style lang="scss" scoped>
.editor-header {
  background-color: #fff;
  user-select: none;
  border-bottom: 1px solid $borderColor;
  display: flex;
  justify-content: space-between;
  padding: 0 5px;
}
.left, .right {
  display: flex;
  justify-content: center;
  align-items: center;
}
.menu-item {
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 14px;
  padding: 0 10px;
  border-radius: $borderRadius;
  cursor: pointer;

  .icon {
    font-size: 18px;
    color: #666;
  }
  .text {
    width: 18px;
    text-align: center;
    font-size: 17px;
  }
  .ai {
    background: linear-gradient(270deg, #d897fd, #33bcfc);
    background-clip: text;
    color: transparent;
    font-weight: 700;
  }

  &:hover {
    background-color: #f1f1f1;
  }

  // 视频配置按钮特殊样式
  &.video-config-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 6px;
    padding: 0 12px;
    margin: 0 4px;
    
    .icon {
      color: white;
      margin-right: 6px;
    }
    
    .text {
      color: white;
      width: auto;
      font-size: 13px;
      font-weight: 500;
    }
    
    &:hover {
      background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
  }
  
  // 批量导出按钮特殊样式
  &.batch-export-btn {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    border-radius: 6px;
    padding: 0 12px;
    margin: 0 4px;
    
    .icon {
      color: white;
      margin-right: 4px;
      font-size: 16px;
    }
    
    .text {
      color: white;
      width: auto;
      font-size: 13px;
      font-weight: 500;
    }
    
    &:hover:not(.disabled) {
      background: linear-gradient(135deg, #e082ea 0%, #e3465b 100%);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
    }
    
    &.disabled {
      opacity: 0.6;
      cursor: not-allowed;
      
      &:hover {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        transform: none;
        box-shadow: none;
      }
    }
  }
  
  // 字幕设置按钮特殊样式
  &.subtitle-config-btn {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: white;
    border-radius: 6px;
    padding: 0 12px;
    margin: 0 4px;
    
    .icon {
      color: white;
      margin-right: 6px;
    }
    
    .text {
      color: white;
      width: auto;
      font-size: 13px;
      font-weight: 500;
    }
    
    &:hover {
      background: linear-gradient(135deg, #0f8c82 0%, #32d971 100%);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3);
    }
  }
  
  // 统一配置按钮特殊样式
  &.unified-config-btn {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
    border-radius: 8px;
    padding: 0 14px;
    margin: 0 4px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(255, 107, 107, 0.2);
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      transition: left 0.6s;
    }
    
    &:hover::before {
      left: 100%;
    }
    
    .icon {
      color: white;
      margin-right: 6px;
      font-size: 14px;
    }
    
    .text {
      color: white;
      width: auto;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.5px;
    }
    
    &:hover {
      background: linear-gradient(135deg, #ff5252 0%, #d63031 100%);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(255, 107, 107, 0.4);
    }
    
    &:active {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
    }
  }
}
.group-menu-item {
  height: 30px;
  display: flex;
  margin: 0 8px;
  padding: 0 2px;
  border-radius: $borderRadius;

  &:hover {
    background-color: #f1f1f1;
  }

  .menu-item {
    padding: 0 3px;
  }
  .arrow-btn {
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
  }
}
.title {
  height: 30px;
  margin-left: 2px;
  font-size: 13px;

  .title-input {
    width: 200px;
    height: 100%;
    padding-left: 0;
    padding-right: 0;

    ::v-deep(input) {
      height: 28px;
      line-height: 28px;
    }
  }
  .title-text {
    min-width: 20px;
    max-width: 400px;
    line-height: 30px;
    padding: 0 6px;
    border-radius: $borderRadius;
    cursor: pointer;

    @include ellipsis-oneline();

    &:hover {
      background-color: #f1f1f1;
    }
  }
}
.github-link {
  display: inline-block;
  height: 30px;
}

// 自动保存开关样式
.auto-save-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 8px;
  padding: 0 8px;
  border-radius: $borderRadius;
  cursor: pointer;
  height: 30px;
  
  &:hover {
    background-color: #f1f1f1;
  }
  
  .toggle-label {
    font-size: 13px;
    color: #666;
    white-space: nowrap;
  }
  
  .toggle-switch {
    position: relative;
    width: 36px;
    height: 18px;
    background-color: #ccc;
    border-radius: 9px;
    transition: background-color 0.3s ease;
    
    &.active {
      background-color: #4CAF50;
    }
    
    .toggle-slider {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 14px;
      height: 14px;
      background-color: white;
      border-radius: 50%;
      transition: transform 0.3s ease;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }
    
    &.active .toggle-slider {
      transform: translateX(18px);
    }
  }
}

// 批量导出进度显示
.batch-export-progress-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;

  .progress-content {
    background: white;
    border-radius: 12px;
    padding: 30px 40px;
    min-width: 400px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);

    .progress-title {
      font-size: 18px;
      font-weight: 600;
      color: #333;
      margin-bottom: 20px;
      text-align: center;
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: #f0f0f0;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 12px;

      .progress-fill {
        height: 100%;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        transition: width 0.3s ease;
      }
    }

    .progress-text {
      font-size: 16px;
      color: #666;
      text-align: center;
      font-weight: 500;
    }
  }
}

.video-config-modal,
.subtitle-settings-modal,
.unified-config-modal,
.unified-config-test-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;

  .modal-content {
    width: 90%;
    max-width: 1200px;
    max-height: 90%;
    background: white;
    border-radius: 12px;
    overflow: auto;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    
    &.large {
      max-width: 1400px;
      width: 95%;
      max-height: 95%;
    }
  }
}

.project-manager-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;

  .modal-content {
    width: 90%;
    max-width: 1000px;
    height: 80%;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }
}

.config-center-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;

  .modal-content {
    width: 95%;
    max-width: 1400px;
    height: 90%;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }
}
</style>