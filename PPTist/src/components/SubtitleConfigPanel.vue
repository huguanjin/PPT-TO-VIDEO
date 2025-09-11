<template>
  <div class="settings-section">
    <div class="section-header">
      <h3>
        <Text class="section-icon" />
        字幕样式设置
      </h3>
      <p class="section-desc">自定义字幕的外观和动画效果</p>
    </div>
    
    <div class="settings-grid">
      <div class="setting-card">
        <label class="setting-label">字体大小</label>
        <input 
          type="range" 
          min="12" 
          max="48" 
          v-model="fontSize"
          class="setting-slider"
        />
        <span class="slider-value">{{ config.fontSize }}px</span>
      </div>
      
      <div class="setting-card">
        <label class="setting-label">字体颜色</label>
        <input 
          type="color" 
          v-model="color"
          class="setting-color"
        />
      </div>
      
      <div class="setting-card">
        <label class="setting-label">字幕位置</label>
        <select class="setting-select" v-model="position">
          <option value="bottom">底部居中</option>
          <option value="top">顶部居中</option>
          <option value="center">屏幕中心</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Text } from '@icon-park/vue-next'

interface SubtitleConfig {
  fontSize: number
  color: string
  position: string
}

interface Props {
  config: SubtitleConfig
}

interface Emits {
  (e: 'update:config', config: SubtitleConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const fontSize = computed({
  get: () => props.config.fontSize,
  set: (value) => emit('update:config', { ...props.config, fontSize: Number(value) })
})

const color = computed({
  get: () => props.config.color,
  set: (value) => emit('update:config', { ...props.config, color: value })
})

const position = computed({
  get: () => props.config.position,
  set: (value) => emit('update:config', { ...props.config, position: value })
})
</script>

<style lang="scss" scoped>
.settings-section {
  .section-header {
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
      color: white;

      .section-icon {
        margin-right: 8px;
        font-size: 24px;
      }
    }

    .section-desc {
      margin: 0;
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
    }
  }

  .settings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }

  .setting-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;

    .setting-label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      color: white;
      font-size: 14px;
    }

    .setting-slider {
      width: 100%;
      margin-bottom: 8px;
    }

    .slider-value {
      color: rgba(255, 255, 255, 0.8);
      font-size: 14px;
    }

    .setting-color {
      width: 100%;
      height: 40px;
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      cursor: pointer;
    }

    .setting-select {
      width: 100%;
      padding: 12px 16px;
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.05);
      color: white;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        border-color: rgba(52, 152, 219, 0.6);
      }

      &:focus {
        outline: none;
        border-color: rgba(52, 152, 219, 0.8);
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
      }

      option {
        background: #2c3e50;
        color: white;
      }
    }
  }
}
</style>
