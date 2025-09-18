<template>
  <div class="template-preview">
    <Tabs :active-key="activeTab" @change="onTabChange">
      <!-- 配置概览 -->
      <TabPane key="overview" tab="配置概览">
        <div class="overview-section">
          <Row :gutter="24">
            <Col :span="12">
              <Card title="视频设置" size="small">
                <DescriptionsItem label="分辨率">{{ template.config.video.resolution }}</DescriptionsItem>
                <DescriptionsItem label="帧率">{{ template.config.video.fps }} FPS</DescriptionsItem>
                <DescriptionsItem label="质量">{{ getQualityLabel(template.config.video.quality) }}</DescriptionsItem>
                <DescriptionsItem label="编码器">{{ template.config.video.codec.toUpperCase() }}</DescriptionsItem>
                <DescriptionsItem label="格式">{{ template.config.video.format.toUpperCase() }}</DescriptionsItem>
              </Card>
            </Col>
            
            <Col :span="12">
              <Card title="音频设置" size="small">
                <DescriptionsItem label="采样率">{{ template.config.audio.sampleRate }} Hz</DescriptionsItem>
                <DescriptionsItem label="比特率">{{ template.config.audio.bitrate / 1000 }} kbps</DescriptionsItem>
                <DescriptionsItem label="声道">{{ getChannelLabel(template.config.audio.channels) }}</DescriptionsItem>
                <DescriptionsItem label="格式">{{ template.config.audio.format.toUpperCase() }}</DescriptionsItem>
                <DescriptionsItem label="增强">{{ template.config.audio.enhancementEnabled ? '启用' : '禁用' }}</DescriptionsItem>
              </Card>
            </Col>
          </Row>
          
          <Row :gutter="24" style="margin-top: 16px;">
            <Col :span="12">
              <Card title="处理设置" size="small">
                <DescriptionsItem label="线程数">{{ template.config.processing.threads }}</DescriptionsItem>
                <DescriptionsItem label="内存限制">{{ template.config.processing.memoryLimit }}</DescriptionsItem>
                <DescriptionsItem label="GPU加速">{{ template.config.processing.gpuAcceleration ? '启用' : '禁用' }}</DescriptionsItem>
                <DescriptionsItem label="批处理大小">{{ template.config.processing.batchSize }}</DescriptionsItem>
                <DescriptionsItem label="优先级">{{ getPriorityLabel(template.config.processing.priority) }}</DescriptionsItem>
              </Card>
            </Col>
            
            <Col :span="12">
              <Card title="输出设置" size="small">
                <DescriptionsItem label="输出目录">{{ template.config.output.directory }}</DescriptionsItem>
                <DescriptionsItem label="文件命名">{{ template.config.output.naming }}</DescriptionsItem>
                <DescriptionsItem label="压缩">{{ template.config.output.compression ? '启用' : '禁用' }}</DescriptionsItem>
                <DescriptionsItem label="备份">{{ template.config.output.backup ? '启用' : '禁用' }}</DescriptionsItem>
                <DescriptionsItem label="元数据">{{ template.config.output.metadata ? '包含' : '不包含' }}</DescriptionsItem>
              </Card>
            </Col>
          </Row>
        </div>
      </TabPane>

      <!-- 字幕预览 -->
      <TabPane key="subtitle" tab="字幕预览">
        <div class="subtitle-preview-section">
          <div class="preview-container">
            <div class="video-mock" :style="videoMockStyle">
              <div class="video-info">
                <p>视频预览区域</p>
                <p>{{ template.config.video.resolution }}</p>
                <p>{{ template.config.video.fps }} FPS</p>
              </div>
              
              <div class="subtitle-mock" :style="subtitleStyle">
                这是字幕预览样例文本<br/>
                支持多行显示效果
              </div>
            </div>
          </div>
          
          <div class="subtitle-controls">
            <Card title="字幕样式预览" size="small">
              <Row :gutter="16}>
                <Col :span="8">
                  <div class="style-item">
                    <label>字体:</label>
                    <span>{{ template.config.subtitle.style.fontFamily }}</span>
                  </div>
                </Col>
                <Col :span="8">
                  <div class="style-item">
                    <label>大小:</label>
                    <span>{{ template.config.subtitle.style.fontSize }}px</span>
                  </div>
                </Col>
                <Col :span="8">
                  <div class="style-item">
                    <label>颜色:</label>
                    <div class="color-preview" :style="{ backgroundColor: template.config.subtitle.style.color }"></div>
                  </div>
                </Col>
                <Col :span="8">
                  <div class="style-item">
                    <label>背景:</label>
                    <div class="color-preview" :style="{ backgroundColor: template.config.subtitle.style.backgroundColor }"></div>
                  </div>
                </Col>
                <Col :span="8">
                  <div class="style-item">
                    <label>对齐:</label>
                    <span>{{ getAlignmentLabel(template.config.subtitle.position.alignment) }}</span>
                  </div>
                </Col>
                <Col :span="8">
                  <div class="style-item">
                    <label>位置:</label>
                    <span>{{ getVerticalAlignmentLabel(template.config.subtitle.position.verticalAlignment) }}</span>
                  </div>
                </Col>
              </Row>
            </Card>
          </div>
        </div>
      </TabPane>

      <!-- 性能评估 -->
      <TabPane key="performance" tab="性能评估">
        <div class="performance-section">
          <Alert
            message="性能评估"
            description="基于当前配置估算的处理性能和资源消耗"
            type="info"
            show-icon
            style="margin-bottom: 16px"
          />
          
          <Row :gutter="24">
            <Col :span="12">
              <Card title="性能指标">
                <div class="performance-metrics">
                  <div class="metric-item">
                    <div class="metric-label">处理速度</div>
                    <Progress 
                      :percent="performanceMetrics.speed" 
                      :stroke-color="getPerformanceColor(performanceMetrics.speed)"
                    />
                  </div>
                  
                  <div class="metric-item">
                    <div class="metric-label">内存使用</div>
                    <Progress 
                      :percent="performanceMetrics.memory" 
                      :stroke-color="getPerformanceColor(performanceMetrics.memory, true)"
                    />
                  </div>
                  
                  <div class="metric-item">
                    <div class="metric-label">CPU 负载</div>
                    <Progress 
                      :percent="performanceMetrics.cpu" 
                      :stroke-color="getPerformanceColor(performanceMetrics.cpu, true)"
                    />
                  </div>
                  
                  <div class="metric-item">
                    <div class="metric-label">输出质量</div>
                    <Progress 
                      :percent="performanceMetrics.quality" 
                      :stroke-color="getPerformanceColor(performanceMetrics.quality)"
                    />
                  </div>
                </div>
              </Card>
            </Col>
            
            <Col :span="12">
              <Card title="预估时间">
                <Statistic
                  title="1小时视频处理时间"
                  :value="estimatedProcessingTime"
                  suffix="分钟"
                  :value-style="{ color: getTimeColor(estimatedProcessingTime) }"
                />
                
                <Divider />
                
                <div class="time-breakdown">
                  <div class="time-item">
                    <span>音频处理:</span>
                    <span>{{ Math.ceil(estimatedProcessingTime * 0.3) }} 分钟</span>
                  </div>
                  <div class="time-item">
                    <span>视频渲染:</span>
                    <span>{{ Math.ceil(estimatedProcessingTime * 0.5) }} 分钟</span>
                  </div>
                  <div class="time-item">
                    <span>字幕合成:</span>
                    <span>{{ Math.ceil(estimatedProcessingTime * 0.2) }} 分钟</span>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>
          
          <Card title="优化建议" style="margin-top: 16px;">
            <div class="optimization-suggestions">
              <div v-for="suggestion in optimizationSuggestions" :key="suggestion.type" class="suggestion-item">
                <Tag :color="suggestion.level === 'high' ? 'red' : suggestion.level === 'medium' ? 'orange' : 'green'">
                  {{ suggestion.level === 'high' ? '重要' : suggestion.level === 'medium' ? '建议' : '可选' }}
                </Tag>
                <span>{{ suggestion.message }}</span>
              </div>
            </div>
          </Card>
        </div>
      </TabPane>

      <!-- 兼容性检查 -->
      <TabPane key="compatibility" tab="兼容性">
        <div class="compatibility-section">
          <Card title="系统兼容性">
            <Row :gutter="16">
              <Col :span="8">
                <div class="compatibility-item">
                  <CheckCircleOutlined style="color: #52c41a;" />
                  <span>Windows 10+</span>
                </div>
              </Col>
              <Col :span="8">
                <div class="compatibility-item">
                  <CheckCircleOutlined style="color: #52c41a;" />
                  <span>macOS 10.15+</span>
                </div>
              </Col>
              <Col :span="8">
                <div class="compatibility-item">
                  <CheckCircleOutlined style="color: #52c41a;" />
                  <span>Linux</span>
                </div>
              </Col>
            </Row>
          </Card>
          
          <Card title="功能要求" style="margin-top: 16px;">
            <div class="requirements-list">
              <div class="requirement-item">
                <span class="requirement-label">最小内存:</span>
                <span>{{ getMinimumMemory() }}</span>
              </div>
              <div class="requirement-item">
                <span class="requirement-label">推荐 CPU:</span>
                <span>{{ getRecommendedCPU() }}</span>
              </div>
              <div class="requirement-item">
                <span class="requirement-label">GPU 支持:</span>
                <span>{{ template.config.processing.gpuAcceleration ? '需要' : '可选' }}</span>
              </div>
              <div class="requirement-item">
                <span class="requirement-label">存储空间:</span>
                <span>{{ getStorageRequirement() }}</span>
              </div>
            </div>
          </Card>
          
          <Card title="编码器支持" style="margin-top: 16px;">
            <div class="codec-support">
              <Tag 
                v-for="codec in supportedCodecs" 
                :key="codec.name"
                :color="codec.supported ? 'green' : 'red'"
              >
                {{ codec.name }}
              </Tag>
            </div>
          </Card>
        </div>
      </TabPane>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Tabs,
  TabPane,
  Card,
  Row,
  Col,
  DescriptionsItem,
  Alert,
  Progress,
  Statistic,
  Divider,
  Tag
} from 'ant-design-vue'
import { CheckCircleOutlined } from '@ant-design/icons-vue'

import type { Template } from '../templates/template-config'

// Props
interface Props {
  template: Template
}

defineProps<Props>()

// State
const activeTab = ref('overview')

// Computed
const videoMockStyle = computed(() => {
  const [width, height] = props.template.config.video.resolution.split('x').map(Number)
  const aspectRatio = width / height
  
  return {
    aspectRatio: aspectRatio,
    maxWidth: '100%',
    backgroundColor: '#000',
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white'
  }
})

const subtitleStyle = computed(() => {
  const config = props.template.config.subtitle
  
  return {
    position: 'absolute',
    bottom: `${config.position.margin.bottom}px`,
    left: `${config.position.margin.left}px`,
    right: `${config.position.margin.right}px`,
    fontFamily: config.style.fontFamily,
    fontSize: `${Math.max(config.style.fontSize * 0.8, 12)}px`,
    fontWeight: config.style.fontWeight,
    color: config.style.color,
    backgroundColor: config.style.backgroundColor,
    borderColor: config.style.borderColor,
    borderWidth: `${config.style.borderWidth}px`,
    borderStyle: config.style.borderWidth > 0 ? 'solid' : 'none',
    textAlign: config.position.alignment,
    padding: '8px 12px',
    borderRadius: '4px',
    boxShadow: `${config.style.shadowOffset.x}px ${config.style.shadowOffset.y}px 4px ${config.style.shadowColor}`,
    opacity: config.style.opacity,
    lineHeight: '1.4'
  }
})

const performanceMetrics = computed(() => {
  const config = props.template.config
  const [width, height] = config.video.resolution.split('x').map(Number)
  const pixelCount = width * height
  
  // 基于配置计算性能指标 (模拟)
  const speed = Math.max(20, 100 - (pixelCount / 50000) - (config.video.fps / 2))
  const memory = Math.min(95, (pixelCount / 100000) + (config.processing.threads * 5))
  const cpu = Math.min(90, config.processing.threads * 8 + (config.video.fps / 3))
  const quality = getQualityScore(config.video.quality)
  
  return {
    speed: Math.round(speed),
    memory: Math.round(memory),
    cpu: Math.round(cpu),
    quality: Math.round(quality)
  }
})

const estimatedProcessingTime = computed(() => {
  const config = props.template.config
  const [width, height] = config.video.resolution.split('x').map(Number)
  const pixelCount = width * height
  
  // 基于配置估算处理时间 (分钟/小时)
  let baseTime = 30 // 基础30分钟
  
  // 分辨率影响
  if (pixelCount > 2073600) baseTime += 20 // 1080p+
  if (pixelCount > 8294400) baseTime += 40 // 4K+
  
  // 帧率影响
  if (config.video.fps > 30) baseTime += 15
  if (config.video.fps > 60) baseTime += 25
  
  // 质量影响
  if (config.video.quality === 'ultra') baseTime += 30
  if (config.video.quality === 'high') baseTime += 15
  
  // 线程数减少时间
  baseTime = Math.max(10, baseTime - (config.processing.threads - 1) * 3)
  
  return baseTime
})

const optimizationSuggestions = computed(() => {
  const suggestions: Array<{ type: string; level: string; message: string }> = []
  const config = props.template.config
  
  if (config.processing.threads < 4) {
    suggestions.push({
      type: 'threads',
      level: 'medium',
      message: '建议增加线程数到4以上以提高处理速度'
    })
  }
  
  if (!config.processing.gpuAcceleration && config.video.quality === 'ultra') {
    suggestions.push({
      type: 'gpu',
      level: 'high',
      message: '超高质量建议启用GPU加速'
    })
  }
  
  if (config.video.fps > 60 && config.video.quality === 'ultra') {
    suggestions.push({
      type: 'performance',
      level: 'high',
      message: '高帧率+超高质量会显著增加处理时间，考虑降低其中一项'
    })
  }
  
  return suggestions
})

const supportedCodecs = computed(() => [
  { name: 'H.264', supported: true },
  { name: 'H.265', supported: true },
  { name: 'VP9', supported: true },
  { name: 'AV1', supported: false },
  { name: 'AAC', supported: true },
  { name: 'MP3', supported: true }
])

// Methods
const onTabChange = (key: string) => {
  activeTab.value = key
}

const getQualityLabel = (quality: string) => {
  const labels: Record<string, string> = {
    low: '低质量',
    medium: '中质量',
    high: '高质量',
    ultra: '超高质量'
  }
  return labels[quality] || quality
}

const getChannelLabel = (channels: number) => {
  const labels: Record<number, string> = {
    1: '单声道',
    2: '立体声',
    6: '5.1环绕声'
  }
  return labels[channels] || `${channels}声道`
}

const getPriorityLabel = (priority: string) => {
  const labels: Record<string, string> = {
    low: '低',
    normal: '正常',
    high: '高'
  }
  return labels[priority] || priority
}

const getAlignmentLabel = (alignment: string) => {
  const labels: Record<string, string> = {
    left: '左对齐',
    center: '居中',
    right: '右对齐'
  }
  return labels[alignment] || alignment
}

const getVerticalAlignmentLabel = (alignment: string) => {
  const labels: Record<string, string> = {
    top: '顶部',
    middle: '中间',
    bottom: '底部'
  }
  return labels[alignment] || alignment
}

const getQualityScore = (quality: string) => {
  const scores: Record<string, number> = {
    low: 40,
    medium: 65,
    high: 85,
    ultra: 95
  }
  return scores[quality] || 50
}

const getPerformanceColor = (value: number, inverse = false) => {
  if (inverse) {
    if (value > 80) return '#ff4d4f'
    if (value > 60) return '#faad14'
    return '#52c41a'
  }
  
  if (value > 80) return '#52c41a'
  if (value > 60) return '#faad14'
  return '#ff4d4f'
}

const getTimeColor = (time: number) => {
  if (time > 60) return '#ff4d4f'
  if (time > 30) return '#faad14'
  return '#52c41a'
}

const getMinimumMemory = () => {
  const config = props.template.config
  const [width, height] = config.video.resolution.split('x').map(Number)
  
  if (width * height > 8294400) return '16GB' // 4K+
  if (width * height > 2073600) return '8GB'  // 1080p+
  return '4GB'
}

const getRecommendedCPU = () => {
  const config = props.template.config
  
  if (config.video.quality === 'ultra') return '8核 3.0GHz+'
  if (config.video.quality === 'high') return '6核 2.5GHz+'
  return '4核 2.0GHz+'
}

const getStorageRequirement = () => {
  const config = props.template.config
  const [width, height] = config.video.resolution.split('x').map(Number)
  
  let storage = 10 // 基础10GB
  
  if (width * height > 8294400) storage = 50 // 4K
  else if (width * height > 2073600) storage = 25 // 1080p
  
  if (config.video.quality === 'ultra') storage *= 1.5
  
  return `${Math.ceil(storage)}GB+`
}
</script>

<style scoped>
.template-preview {
  max-height: 600px;
  overflow-y: auto;
}

.overview-section .ant-descriptions-item-label {
  font-weight: 500;
  color: #262626;
}

.subtitle-preview-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-container {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: #f5f5f5;
  border-radius: 8px;
}

.video-mock {
  border-radius: 8px;
  overflow: hidden;
  max-width: 500px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.video-info {
  text-align: center;
  font-size: 14px;
  opacity: 0.7;
}

.video-info p {
  margin: 4px 0;
}

.subtitle-controls .style-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.style-item label {
  font-weight: 500;
  min-width: 50px;
}

.color-preview {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
}

.performance-section .metric-item {
  margin-bottom: 16px;
}

.metric-label {
  margin-bottom: 8px;
  font-weight: 500;
  color: #262626;
}

.time-breakdown {
  margin-top: 16px;
}

.time-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #595959;
}

.optimization-suggestions .suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.compatibility-section .compatibility-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.requirements-list .requirement-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.requirement-label {
  font-weight: 500;
  color: #262626;
}

.codec-support {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .preview-container {
    padding: 16px;
  }
  
  .video-mock {
    max-width: 100%;
  }
  
  .subtitle-controls .ant-col {
    margin-bottom: 12px;
  }
}
</style>