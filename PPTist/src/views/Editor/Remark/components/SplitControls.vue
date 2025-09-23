<template>
  <div class="split-mode-controls">
    <!-- 分割模式切换 -->
    <div class="control-group">
      <label class="switch-label">
        <input 
          type="checkbox" 
          v-model="localSplitEnabled"
          @change="handleSplitToggle"
          class="switch-input"
        />
        <span class="switch-slider"></span>
      </label>
      <span class="control-text">换行分割</span>
    </div>

    <!-- 分割操作按钮 -->
    <div v-if="localSplitEnabled" class="split-actions">
      <button 
        type="button"
        class="action-btn"
        @click="handleSplitByLines"
        title="按现有换行分割"
      >
        <IconSplit />
      </button>
      <button 
        type="button"
        class="action-btn"
        @click="handleSplitBySentences" 
        title="按句号自动分割"
      >
        <IconSentence />
      </button>
      <button 
        type="button"
        class="action-btn"
        @click="handleMergeLines"
        title="合并所有行"
      >
        <IconMerge />
      </button>
    </div>

    <!-- 统计信息 -->
    <div class="split-stats">
      <span class="stat-item">
        <IconText />
        {{ characterCount }}字
      </span>
      <span v-if="segmentCount > 1" class="stat-item">
        <IconSegment />
        {{ segmentCount }}段
      </span>
      <span v-if="estimatedDuration" class="stat-item">
        <IconTime />
        ~{{ estimatedDuration }}s
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

// 图标组件（简化版）
const IconSplit = () => '⫮'
const IconSentence = () => '。'
const IconMerge = () => '⫯'
const IconText = () => '📝'
const IconSegment = () => '📋'
const IconTime = () => '⏱'

// Props
interface Props {
  splitEnabled: boolean
  characterCount: number
  segmentCount: number
  estimatedDuration?: number
}

const props = defineProps<Props>()

// Emits
interface Emits {
  'update:splitEnabled': [value: boolean]
  'splitByLines': []
  'splitBySentences': []
  'mergeLines': []
}

const emit = defineEmits<Emits>()

// 本地状态
const localSplitEnabled = ref(props.splitEnabled)

// 监听props变化
watch(() => props.splitEnabled, (newValue) => {
  localSplitEnabled.value = newValue
})

// 事件处理
const handleSplitToggle = () => {
  emit('update:splitEnabled', localSplitEnabled.value)
}

const handleSplitByLines = () => {
  emit('splitByLines')
}

const handleSplitBySentences = () => {
  emit('splitBySentences')
}

const handleMergeLines = () => {
  emit('mergeLines')
}
</script>

<style lang="scss" scoped>
.split-mode-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;

  .control-group {
    display: flex;
    align-items: center;
    gap: 6px;

    .switch-label {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
      cursor: pointer;

      .switch-input {
        opacity: 0;
        width: 0;
        height: 0;

        &:checked + .switch-slider {
          background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);

          &:before {
            transform: translateX(20px);
            background: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          }
        }

        &:focus + .switch-slider {
          box-shadow: 0 0 8px rgba(76, 175, 80, 0.6);
        }
      }

      .switch-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: #ccc;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        border-radius: 12px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);

        &:before {
          position: absolute;
          content: "";
          height: 18px;
          width: 18px;
          left: 3px;
          bottom: 3px;
          background: white;
          transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
          border-radius: 50%;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        &:hover {
          box-shadow: 0 0 12px rgba(76, 175, 80, 0.4);
        }
      }
    }

    .control-text {
      color: rgba(255, 255, 255, 0.9);
      font-size: 13px;
      font-weight: 500;
      user-select: none;
    }
  }

  .split-actions {
    display: flex;
    gap: 4px;

    .action-btn {
      width: 28px;
      height: 28px;
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.9);
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      backdrop-filter: blur(4px);

      &:hover {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.5);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      }

      &:active {
        transform: translateY(0);
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
      }
    }
  }

  .split-stats {
    display: flex;
    gap: 8px;
    margin-left: auto;

    .stat-item {
      display: flex;
      align-items: center;
      gap: 4px;
      color: rgba(255, 255, 255, 0.8);
      font-size: 12px;
      font-weight: 500;
      background: rgba(255, 255, 255, 0.1);
      padding: 4px 8px;
      border-radius: 12px;
      backdrop-filter: blur(4px);
      border: 1px solid rgba(255, 255, 255, 0.2);
    }
  }
}

// 响应式适配
@media (max-width: 1200px) {
  .split-mode-controls {
    order: 3;
    flex-basis: 100%;
    justify-content: center;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.2);

    .split-stats {
      margin-left: 0;
    }
  }
}

@media (max-height: 900px) {
  .split-mode-controls {
    gap: 8px;

    .split-actions {
      gap: 4px;

      .action-btn {
        width: 24px;
        height: 24px;
      }
    }
  }
}

@media (max-height: 700px) {
  .split-actions .action-btn {
    width: 22px;
    height: 22px;
  }
}
</style>