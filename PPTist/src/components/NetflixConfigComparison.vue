<!--
Netflix配置比较子组件 - 用于配置对比功能
-->
<template>
  <div class="config-comparison">
    <div class="comparison-header">
      <h4>📊 配置比较</h4>
      <div class="comparison-controls">
        <el-button
          size="small"
          @click="addToComparison"
          :disabled="!selectedConfig || comparisonConfigs.length >= 3"
        >
          添加到比较
        </el-button>
        <el-button
          size="small"
          type="danger"
          @click="clearComparison"
          :disabled="comparisonConfigs.length === 0"
        >
          清空比较
        </el-button>
      </div>
    </div>

    <div v-if="comparisonConfigs.length === 0" class="empty-comparison">
      <div class="empty-state">
        <span class="empty-icon">📊</span>
        <p class="empty-text">暂无配置进行比较</p>
        <button class="add-config-btn" @click="addToComparison">添加配置</button>
      </div>
    </div>

    <div v-else class="comparison-table-container">
      <table class="comparison-table">
        <thead>
          <tr>
            <th class="param-column">参数</th>
            <th v-for="config in comparisonConfigs" :key="config.name">
              {{ config.name }}
              <button
                class="remove-config-btn"
                @click="removeFromComparison(config)"
                title="移除配置"
              >
                ❌
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="param in comparisonParams" :key="param.key">
            <td class="param-name">{{ param.label }}</td>
            <td v-for="config in comparisonConfigs" :key="config.name">
              <span class="comparison-cell">
                {{ getConfigValue(config, param.key) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// 定义配置接口
interface NetflixConfig {
  name: string
  description?: string
  recommended?: boolean
  performance: number
  quality: number
  memoryUsage: number
  params: Record<string, any>
}

// Props
interface Props {
  selectedConfig: NetflixConfig | null
  availableConfigs: NetflixConfig[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  configAdded: [config: NetflixConfig]
  configRemoved: [config: NetflixConfig]
  comparisonCleared: []
}>()

// 比较配置列表
const comparisonConfigs = ref<NetflixConfig[]>([])

// 比较参数定义
const comparisonParams = computed(() => [
  { key: 'whisper_model', label: 'Whisper模型' },
  { key: 'batch_size', label: '批处理大小' },
  { key: 'performance_mode', label: '性能模式' },
  { key: 'subtitle_style', label: '字幕样式' },
  { key: 'sync_accuracy', label: '同步精度' }
])

// 添加到比较
const addToComparison = () => {
  if (props.selectedConfig && !comparisonConfigs.value.find(c => c.name === props.selectedConfig!.name)) {
    comparisonConfigs.value.push(props.selectedConfig)
    emit('configAdded', props.selectedConfig)
  }
}

// 从比较中移除
const removeFromComparison = (config: NetflixConfig) => {
  const index = comparisonConfigs.value.findIndex(c => c.name === config.name)
  if (index > -1) {
    comparisonConfigs.value.splice(index, 1)
    emit('configRemoved', config)
  }
}

// 清空比较
const clearComparison = () => {
  comparisonConfigs.value = []
  emit('comparisonCleared')
}

// 获取配置值
const getConfigValue = (config: NetflixConfig, key: string): string => {
  const value = config.params[key]
  if (value === undefined || value === null) return '未设置'
  if (typeof value === 'boolean') return value ? '是' : '否'
  return String(value)
}
</script>

<style scoped>
.config-comparison {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.comparison-header h4 {
  margin: 0;
  color: #333;
}

.comparison-controls {
  display: flex;
  gap: 8px;
}

.empty-comparison {
  text-align: center;
  padding: 32px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.6;
}

.empty-text {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.add-config-btn {
  background: #2196F3;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.add-config-btn:hover {
  background: #1976D2;
  transform: translateY(-1px);
}

.comparison-table-container {
  overflow-x: auto;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.comparison-table th,
.comparison-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.comparison-table th {
  background: #f5f5f5;
  font-weight: 600;
  position: relative;
}

.param-column {
  min-width: 120px;
  background: #e8f5e8 !important;
}

.param-name {
  font-weight: 500;
  background: #f9f9f9;
}

.comparison-cell {
  display: inline-block;
  padding: 4px 8px;
  background: #e3f2fd;
  border-radius: 4px;
  font-size: 14px;
}

.remove-config-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: none;
  border: none;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 2px;
  opacity: 0.7;
  transition: all 0.2s ease;
}

.remove-config-btn:hover {
  opacity: 1;
  background: rgba(255, 0, 0, 0.1);
}
</style>