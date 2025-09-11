<template>
  <div class="config-section">
    <h2>视频设置</h2>
    <div class="form-grid">
      <div class="form-item">
        <label>视频分辨率</label>
        <select v-model="config.video.resolution">
          <option value="1920x1080">1920x1080 (Full HD)</option>
          <option value="1280x720">1280x720 (HD)</option>
          <option value="3840x2160">3840x2160 (4K)</option>
        </select>
      </div>
      <div class="form-item">
        <label>帧率 (FPS)</label>
        <select v-model="config.video.fps">
          <option :value="24">24 FPS</option>
          <option :value="30">30 FPS</option>
          <option :value="60">60 FPS</option>
        </select>
      </div>
      <div class="form-item">
        <label>视频比特率</label>
        <select v-model="config.video.video_bitrate">
          <option value="1000k">1000k (标清)</option>
          <option value="2000k">2000k (高清)</option>
          <option value="4000k">4000k (超清)</option>
          <option value="8000k">8000k (超高清)</option>
        </select>
      </div>
      <div class="form-item">
        <label>背景色</label>
        <input type="color" v-model="config.video.background_color" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from 'vue'

interface VideoConfig {
  resolution: string
  fps: number
  video_bitrate: string
  background_color: string
  include_subtitles?: boolean
}

interface Props {
  config: {
    video: VideoConfig
  }
}

const props = defineProps<Props>()
const { config } = toRefs(props)
</script>

<style lang="scss" scoped>
.config-section {
  margin-bottom: 40px;

  h2 {
    color: #2c3e50;
    font-size: 1.6em;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #ecf0f1;
  }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;

  label {
    margin-bottom: 8px;
    font-weight: 600;
    color: #34495e;
    font-size: 0.95em;
  }

  input, select {
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 1em;
    transition: all 0.3s ease;

    &:focus {
      outline: none;
      border-color: #5c7cfa;
      box-shadow: 0 0 0 3px rgba(92, 124, 250, 0.1);
    }
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
