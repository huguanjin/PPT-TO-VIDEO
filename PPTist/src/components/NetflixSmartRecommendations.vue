<!--
Netflix智能推荐子组件 - 用于配置推荐功能
-->
<template>
  <div class="smart-recommendations">
    <div class="recommendations-header">
      <h4>🧠 智能推荐</h4>
      <el-tooltip content="基于您的使用习惯和项目特点推荐最优配置">
        <span class="help-icon">ℹ️</span>
      </el-tooltip>
    </div>

    <div class="recommendations-content">
      <!-- 推荐配置卡片 -->
      <div
        v-for="recommendation in recommendations"
        :key="recommendation.id"
        class="recommendation-card"
        :class="`recommendation-${recommendation.priority}`"
      >
        <div class="recommendation-header">
          <span class="recommendation-title">{{ recommendation.title }}</span>
          <span class="recommendation-score">{{ recommendation.score }}%</span>
        </div>
        
        <div class="recommendation-description">
          {{ recommendation.description }}
        </div>
        
        <div class="recommendation-benefits">
          <div
            v-for="benefit in recommendation.benefits"
            :key="benefit"
            class="benefit-tag"
          >
            {{ benefit }}
          </div>
        </div>
        
        <div class="recommendation-actions">
          <button
            class="apply-btn"
            @click="applyRecommendation(recommendation)"
          >
            应用推荐
          </button>
          <button
            class="preview-btn"
            @click="previewRecommendation(recommendation)"
          >
            预览效果
          </button>
        </div>
      </div>

      <!-- 无推荐时的提示 -->
      <div v-if="recommendations.length === 0" class="no-recommendations">
        <span class="empty-icon">🤖</span>
        <p>暂无智能推荐</p>
        <button class="generate-btn" @click="generateRecommendations">
          生成推荐
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// 推荐接口定义
interface SmartRecommendation {
  id: string
  title: string
  description: string
  score: number
  priority: 'high' | 'medium' | 'low'
  benefits: string[]
  config: Record<string, any>
}

// Props
interface Props {
  currentConfig: Record<string, any>
  userPreferences: Record<string, any>
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  recommendationApplied: [recommendation: SmartRecommendation]
  recommendationPreviewed: [recommendation: SmartRecommendation]
}>()

// 推荐列表
const recommendations = ref<SmartRecommendation[]>([])

// 生成智能推荐
const generateRecommendations = () => {
  // 模拟智能推荐逻辑
  recommendations.value = [
    {
      id: 'perf-opt-1',
      title: '🚀 性能优化推荐',
      description: '基于您的硬件配置，建议使用高性能模式以提升处理速度',
      score: 92,
      priority: 'high',
      benefits: ['处理速度提升40%', '内存使用优化', '批处理优化'],
      config: {
        whisper_model: 'medium',
        batch_size: 8,
        performance_mode: true
      }
    },
    {
      id: 'quality-opt-1',
      title: '🎯 质量优化推荐',
      description: '为了获得更好的字幕质量，建议调整同步精度和语音识别参数',
      score: 88,
      priority: 'high',
      benefits: ['字幕精度提升', '同步准确性', '语音识别优化'],
      config: {
        whisper_model: 'large',
        sync_accuracy: 'high',
        subtitle_style: 'netflix_v2'
      }
    },
    {
      id: 'balanced-opt-1',
      title: '⚖️ 平衡模式推荐',
      description: '在性能和质量之间找到最佳平衡点',
      score: 85,
      priority: 'medium',
      benefits: ['性能质量平衡', '资源使用合理', '通用适配'],
      config: {
        whisper_model: 'small',
        batch_size: 4,
        performance_mode: false,
        sync_accuracy: 'medium'
      }
    }
  ]
}

// 应用推荐
const applyRecommendation = (recommendation: SmartRecommendation) => {
  emit('recommendationApplied', recommendation)
}

// 预览推荐
const previewRecommendation = (recommendation: SmartRecommendation) => {
  emit('recommendationPreviewed', recommendation)
}

// 初始化时生成推荐
generateRecommendations()
</script>

<style scoped>
.smart-recommendations {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: white;
  margin-bottom: 20px;
}

.recommendations-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.recommendations-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.help-icon {
  font-size: 16px;
  opacity: 0.8;
  cursor: help;
}

.recommendations-content {
  display: grid;
  gap: 16px;
}

.recommendation-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.recommendation-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.recommendation-high {
  border-left: 4px solid #4CAF50;
}

.recommendation-medium {
  border-left: 4px solid #FF9800;
}

.recommendation-low {
  border-left: 4px solid #9E9E9E;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.recommendation-title {
  font-weight: 600;
  font-size: 16px;
}

.recommendation-score {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.recommendation-description {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 12px;
  opacity: 0.9;
}

.recommendation-benefits {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.benefit-tag {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  white-space: nowrap;
}

.recommendation-actions {
  display: flex;
  gap: 8px;
}

.apply-btn, .preview-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apply-btn {
  background: #4CAF50;
  color: white;
}

.apply-btn:hover {
  background: #45a049;
}

.preview-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.preview-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.no-recommendations {
  text-align: center;
  padding: 32px;
  opacity: 0.8;
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.generate-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 16px;
  transition: all 0.2s ease;
}

.generate-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>