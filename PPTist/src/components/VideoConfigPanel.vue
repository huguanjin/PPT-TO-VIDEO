<template>
  <div class="settings-section">
    <div class="section-header">
      <h3>
        <VideoTwo class="section-icon" />
        视频导出设置
      </h3>
      <p class="section-desc">配置视频的分辨率、帧率和质量参数</p>
    </div>
    
    <div class="settings-grid">
      <div class="setting-card">
        <label class="setting-label">输出分辨率</label>
        <select class="setting-select" v-model="resolution">
          <option value="1920x1080">1920×1080 (Full HD)</option>
          <option value="1280x720">1280×720 (HD)</option>
          <option value="3840x2160">3840×2160 (4K)</option>
        </select>
      </div>
      
      <div class="setting-card">
        <label class="setting-label">帧率 (FPS)</label>
        <select class="setting-select" v-model="fps">
          <option value="24">24 FPS (电影级)</option>
          <option value="30">30 FPS (标准)</option>
          <option value="60">60 FPS (高流畅)</option>
        </select>
      </div>
      
      <div class="setting-card">
        <label class="setting-label">视频质量</label>
        <select class="setting-select" v-model="quality">
          <option value="high">高质量</option>
          <option value="medium">中等质量</option>
          <option value="low">经济模式</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { VideoTwo } from '@icon-park/vue-next'

interface VideoConfig {
  resolution: string
  fps: number
  quality: string
}

interface Props {
  config: VideoConfig
}

interface Emits {
  (e: 'update:config', config: VideoConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const resolution = computed({
  get: () => props.config.resolution,
  set: (value) => emit('update:config', { ...props.config, resolution: value })
})

const fps = computed({
  get: () => props.config.fps,
  set: (value) => emit('update:config', { ...props.config, fps: value })
})

const quality = computed({
  get: () => props.config.quality,
  set: (value) => emit('update:config', { ...props.config, quality: value })
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
