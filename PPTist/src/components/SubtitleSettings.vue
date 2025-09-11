<template>
  <div class="config-section">
    <h2>字幕设置</h2>
    <div class="form-grid">
      <div class="form-item checkbox-item">
        <label>
          <input type="checkbox" v-model="config.subtitle.enabled" />
          启用字幕
        </label>
      </div>
      
      <!-- Netflix级增强字幕功能 -->
      <div class="form-item checkbox-item">
        <label>
          <input type="checkbox" v-model="config.subtitle.use_enhanced_mode" />
          启用Netflix级增强字幕
        </label>
        <small class="help-text">使用精确时间对齐和智能间隙填充算法</small>
      </div>
      
      <template v-if="config.subtitle.use_enhanced_mode">
        <div class="enhanced-config">
          <div class="enhanced-title">增强字幕配置</div>
          
          <div class="form-item checkbox-item">
            <label>
              <input type="checkbox" v-model="config.subtitle.enable_precise_alignment" />
              精确时间对齐
            </label>
            <small class="help-text">字符级精确匹配，提升时间轴准确性</small>
          </div>
          
          <div class="form-item checkbox-item">
            <label>
              <input type="checkbox" v-model="config.subtitle.enable_gap_filling" />
              智能间隙填充
            </label>
            <small class="help-text">消除不自然的停顿，优化观看体验</small>
          </div>
          
          <div class="form-item checkbox-item">
            <label>
              <input type="checkbox" v-model="config.subtitle.auto_punctuation_removal" />
              自动标点优化
            </label>
            <small class="help-text">自动调整标点符号以提升阅读体验</small>
          </div>
          
          <div class="form-item">
            <label>每行字符数限制</label>
            <input type="number" v-model="config.subtitle.max_chars_per_line" min="20" max="60" />
            <small class="help-text">控制字幕行长度，建议40-50字符</small>
          </div>
        </div>
      </template>
      
      <div class="form-item">
        <label>字体</label>
        <select v-model="config.subtitle.font_family">
          <option value="SimHei">黑体</option>
          <option value="SimSun">宋体</option>
          <option value="Microsoft YaHei">微软雅黑</option>
          <option value="Arial">Arial</option>
        </select>
      </div>
      <div class="form-item">
        <label>字号</label>
        <input type="number" v-model="config.subtitle.font_size" min="12" max="72" />
      </div>
      <div class="form-item">
        <label>字体颜色</label>
        <input type="color" v-model="config.subtitle.font_color" />
      </div>
      <div class="form-item">
        <label>背景颜色</label>
        <input type="color" v-model="config.subtitle.background_color" />
      </div>
      <div class="form-item">
        <label>位置</label>
        <select v-model="config.subtitle.position">
          <option value="bottom">底部</option>
          <option value="center">居中</option>
          <option value="top">顶部</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from 'vue'

interface SubtitleConfig {
  enabled: boolean
  font_family: string
  font_size: number
  font_color: string
  background_color: string
  position: string
  use_enhanced_mode: boolean
  enable_precise_alignment: boolean
  enable_gap_filling: boolean
  max_chars_per_line: number
  auto_punctuation_removal: boolean
}

interface Props {
  config: {
    subtitle: SubtitleConfig
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

.checkbox-item {
  grid-column: span 2;
  
  label {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    cursor: pointer;
    
    input[type="checkbox"] {
      margin-top: 2px;
    }
  }
}

.help-text {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  margin-left: 24px;
  line-height: 1.4;
  font-style: italic;
}

.enhanced-config {
  grid-column: span 2;
  border: 2px solid #e3f2fd;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
  background: linear-gradient(45deg, #f8f9ff, #fff);
  
  .enhanced-title {
    color: #1976d2;
    font-weight: 600;
    margin-bottom: 15px;
    font-size: 14px;
  }
  
  .form-item {
    margin-bottom: 15px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .checkbox-item {
    grid-column: span 1;
  }
  
  .enhanced-config {
    grid-column: span 1;
  }
}
</style>
