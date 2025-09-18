<template>
  <div class="template-editor">
    <div class="template-header">
      <div class="header-actions">
        <Button @click="goBack" type="default">
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          返回
        </Button>
        
        <div class="header-title">
          <h2 v-if="isNewTemplate">创建新模板</h2>
          <h2 v-else>编辑模板: {{ template?.metadata.name }}</h2>
        </div>
        
        <div class="header-buttons">
          <Button @click="previewTemplate" type="default">
            <template #icon>
              <EyeOutlined />
            </template>
            预览
          </Button>
          
          <Button @click="validateTemplate" type="default">
            <template #icon>
              <CheckCircleOutlined />
            </template>
            验证
          </Button>
          
          <Button @click="saveTemplate" type="primary" :loading="saving">
            <template #icon>
              <SaveOutlined />
            </template>
            保存
          </Button>
        </div>
      </div>
    </div>

    <div class="template-content">
      <!-- 左侧配置面板 -->
      <div class="config-panel">
        <Tabs v-model:activeKey="activeTab" type="card">
          <!-- 基础信息 -->
          <TabPane key="basic" tab="基础信息">
            <Form :model="formData" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <FormItem label="模板名称" required>
                <Input v-model:value="formData.name" placeholder="请输入模板名称" />
              </FormItem>
              
              <FormItem label="描述">
                <TextArea 
                  v-model:value="formData.description" 
                  placeholder="请输入模板描述"
                  :rows="3"
                />
              </FormItem>
              
              <FormItem label="分类">
                <Select v-model:value="formData.category" placeholder="选择分类">
                  <SelectOption v-for="cat in categories" :key="cat.value" :value="cat.value">
                    {{ cat.label }}
                  </SelectOption>
                </Select>
              </FormItem>
              
              <FormItem label="标签">
                <Select
                  v-model:value="formData.tags"
                  mode="tags"
                  placeholder="添加标签"
                  :token-separators="[',']"
                />
              </FormItem>
            </Form>
          </TabPane>

          <!-- 视频设置 -->
          <TabPane key="video" tab="视频设置">
            <Form :model="formData.video" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <FormItem label="分辨率">
                <Select v-model:value="formData.video.resolution" placeholder="选择分辨率">
                  <SelectOption value="1920x1080">1920x1080 (1080p)</SelectOption>
                  <SelectOption value="1280x720">1280x720 (720p)</SelectOption>
                  <SelectOption value="1080x1920">1080x1920 (竖屏)</SelectOption>
                  <SelectOption value="3840x2160">3840x2160 (4K)</SelectOption>
                </Select>
              </FormItem>
              
              <FormItem label="帧率">
                <InputNumber 
                  v-model:value="formData.video.fps" 
                  :min="15" 
                  :max="120" 
                  :step="1"
                  style="width: 100%"
                />
              </FormItem>
              
              <FormItem label="质量">
                <Radio.Group v-model:value="formData.video.quality">
                  <Radio value="low">低质量</Radio>
                  <Radio value="medium">中质量</Radio>
                  <Radio value="high">高质量</Radio>
                  <Radio value="ultra">超高质量</Radio>
                </Radio.Group>
              </FormItem>
              
              <FormItem label="编码器">
                <Select v-model:value="formData.video.codec" placeholder="选择编码器">
                  <SelectOption value="h264">H.264</SelectOption>
                  <SelectOption value="h265">H.265 (HEVC)</SelectOption>
                  <SelectOption value="vp9">VP9</SelectOption>
                  <SelectOption value="av1">AV1</SelectOption>
                </Select>
              </FormItem>
            </Form>
          </TabPane>

          <!-- 音频设置 -->
          <TabPane key="audio" tab="音频设置">
            <Form :model="formData.audio" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <FormItem label="采样率">
                <Select v-model:value="formData.audio.sampleRate" placeholder="选择采样率">
                  <SelectOption :value="22050">22050 Hz</SelectOption>
                  <SelectOption :value="44100">44100 Hz</SelectOption>
                  <SelectOption :value="48000">48000 Hz</SelectOption>
                  <SelectOption :value="96000">96000 Hz</SelectOption>
                </Select>
              </FormItem>
              
              <FormItem label="比特率">
                <InputNumber 
                  v-model:value="formData.audio.bitrate" 
                  :min="64000" 
                  :max="320000" 
                  :step="1000"
                  style="width: 100%"
                />
              </FormItem>
              
              <FormItem label="声道数">
                <Radio.Group v-model:value="formData.audio.channels">
                  <Radio :value="1">单声道</Radio>
                  <Radio :value="2">立体声</Radio>
                  <Radio :value="6">5.1环绕声</Radio>
                </Radio.Group>
              </FormItem>
              
              <FormItem label="音频增强">
                <Switch v-model:checked="formData.audio.enhancementEnabled" />
              </FormItem>
            </Form>
          </TabPane>

          <!-- 字幕设置 -->
          <TabPane key="subtitle" tab="字幕设置">
            <Collapse v-model:activeKey="subtitleTabs">
              <!-- 字幕样式 -->
              <CollapsePanel key="style" header="字幕样式">
                <Form :model="formData.subtitle.style" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
                  <FormItem label="字体">
                    <Select v-model:value="formData.subtitle.style.fontFamily" placeholder="选择字体">
                      <SelectOption value="Arial">Arial</SelectOption>
                      <SelectOption value="Microsoft YaHei">微软雅黑</SelectOption>
                      <SelectOption value="SimHei">黑体</SelectOption>
                      <SelectOption value="SimSun">宋体</SelectOption>
                    </Select>
                  </FormItem>
                  
                  <FormItem label="字体大小">
                    <InputNumber 
                      v-model:value="formData.subtitle.style.fontSize" 
                      :min="12" 
                      :max="72" 
                      style="width: 100%"
                    />
                  </FormItem>
                  
                  <FormItem label="字体颜色">
                    <ColorPicker v-model:value="formData.subtitle.style.color" />
                  </FormItem>
                  
                  <FormItem label="背景颜色">
                    <ColorPicker v-model:value="formData.subtitle.style.backgroundColor" />
                  </FormItem>
                  
                  <FormItem label="边框颜色">
                    <ColorPicker v-model:value="formData.subtitle.style.borderColor" />
                  </FormItem>
                  
                  <FormItem label="边框宽度">
                    <InputNumber 
                      v-model:value="formData.subtitle.style.borderWidth" 
                      :min="0" 
                      :max="10" 
                      style="width: 100%"
                    />
                  </FormItem>
                </Form>
              </CollapsePanel>

              <!-- 字幕位置 -->
              <CollapsePanel key="position" header="字幕位置">
                <Form :model="formData.subtitle.position" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
                  <FormItem label="水平对齐">
                    <Radio.Group v-model:value="formData.subtitle.position.alignment">
                      <Radio value="left">左对齐</Radio>
                      <Radio value="center">居中</Radio>
                      <Radio value="right">右对齐</Radio>
                    </Radio.Group>
                  </FormItem>
                  
                  <FormItem label="垂直对齐">
                    <Radio.Group v-model:value="formData.subtitle.position.verticalAlignment">
                      <Radio value="top">顶部</Radio>
                      <Radio value="middle">中间</Radio>
                      <Radio value="bottom">底部</Radio>
                    </Radio.Group>
                  </FormItem>
                  
                  <FormItem label="边距设置">
                    <div class="margin-controls">
                      <div class="margin-row">
                        <span>上:</span>
                        <InputNumber v-model:value="formData.subtitle.position.margin.top" :min="0" />
                      </div>
                      <div class="margin-row">
                        <span>下:</span>
                        <InputNumber v-model:value="formData.subtitle.position.margin.bottom" :min="0" />
                      </div>
                      <div class="margin-row">
                        <span>左:</span>
                        <InputNumber v-model:value="formData.subtitle.position.margin.left" :min="0" />
                      </div>
                      <div class="margin-row">
                        <span>右:</span>
                        <InputNumber v-model:value="formData.subtitle.position.margin.right" :min="0" />
                      </div>
                    </div>
                  </FormItem>
                </Form>
              </CollapsePanel>

              <!-- 字幕时间设置 -->
              <CollapsePanel key="timing" header="时间设置">
                <Form :model="formData.subtitle.timing" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
                  <FormItem label="时间偏移(ms)">
                    <InputNumber 
                      v-model:value="formData.subtitle.timing.offsetMs" 
                      style="width: 100%"
                    />
                  </FormItem>
                  
                  <FormItem label="持续时间倍数">
                    <InputNumber 
                      v-model:value="formData.subtitle.timing.durationMultiplier" 
                      :min="0.1" 
                      :max="5" 
                      :step="0.1"
                      style="width: 100%"
                    />
                  </FormItem>
                  
                  <FormItem label="最小持续时间(ms)">
                    <InputNumber 
                      v-model:value="formData.subtitle.timing.minimumDuration" 
                      :min="100" 
                      style="width: 100%"
                    />
                  </FormItem>
                  
                  <FormItem label="最大持续时间(ms)">
                    <InputNumber 
                      v-model:value="formData.subtitle.timing.maximumDuration" 
                      :min="1000" 
                      style="width: 100%"
                    />
                  </FormItem>
                </Form>
              </CollapsePanel>
            </Collapse>
          </TabPane>

          <!-- 处理设置 -->
          <TabPane key="processing" tab="处理设置">
            <Form :model="formData.processing" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <FormItem label="线程数">
                <InputNumber 
                  v-model:value="formData.processing.threads" 
                  :min="1" 
                  :max="32" 
                  style="width: 100%"
                />
              </FormItem>
              
              <FormItem label="内存限制">
                <Select v-model:value="formData.processing.memoryLimit" placeholder="选择内存限制">
                  <SelectOption value="2GB">2GB</SelectOption>
                  <SelectOption value="4GB">4GB</SelectOption>
                  <SelectOption value="8GB">8GB</SelectOption>
                  <SelectOption value="16GB">16GB</SelectOption>
                </Select>
              </FormItem>
              
              <FormItem label="GPU加速">
                <Switch v-model:checked="formData.processing.gpuAcceleration" />
              </FormItem>
              
              <FormItem label="批处理大小">
                <InputNumber 
                  v-model:value="formData.processing.batchSize" 
                  :min="1" 
                  :max="100" 
                  style="width: 100%"
                />
              </FormItem>
              
              <FormItem label="处理优先级">
                <Radio.Group v-model:value="formData.processing.priority">
                  <Radio value="low">低</Radio>
                  <Radio value="normal">正常</Radio>
                  <Radio value="high">高</Radio>
                </Radio.Group>
              </FormItem>
            </Form>
          </TabPane>

          <!-- 输出设置 -->
          <TabPane key="output" tab="输出设置">
            <Form :model="formData.output" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <FormItem label="输出目录">
                <Input v-model:value="formData.output.directory" placeholder="输出目录路径" />
              </FormItem>
              
              <FormItem label="文件命名">
                <Input v-model:value="formData.output.naming" placeholder="文件命名模板" />
                <div class="naming-hint">
                  可用变量: {title}, {timestamp}, {date}, {index}
                </div>
              </FormItem>
              
              <FormItem label="压缩输出">
                <Switch v-model:checked="formData.output.compression" />
              </FormItem>
              
              <FormItem label="创建备份">
                <Switch v-model:checked="formData.output.backup" />
              </FormItem>
              
              <FormItem label="包含元数据">
                <Switch v-model:checked="formData.output.metadata" />
              </FormItem>
            </Form>
          </TabPane>
        </Tabs>
      </div>

      <!-- 右侧预览面板 -->
      <div class="preview-panel">
        <div class="preview-header">
          <h3>模板预览</h3>
          <Button @click="refreshPreview" type="text" size="small">
            <template #icon>
              <ReloadOutlined />
            </template>
            刷新
          </Button>
        </div>
        
        <div class="preview-content">
          <div class="preview-video">
            <div class="video-placeholder">
              <PlayCircleOutlined class="play-icon" />
              <p>视频预览</p>
              <p class="resolution">{{ formData.video.resolution }}</p>
            </div>
          </div>
          
          <div class="preview-subtitle">
            <div 
              class="subtitle-sample"
              :style="subtitlePreviewStyle"
            >
              这是字幕预览样例
            </div>
          </div>
          
          <div class="preview-info">
            <Descriptions title="配置摘要" :column="1" size="small">
              <DescriptionsItem label="分辨率">{{ formData.video.resolution }}</DescriptionsItem>
              <DescriptionsItem label="帧率">{{ formData.video.fps }} FPS</DescriptionsItem>
              <DescriptionsItem label="质量">{{ getQualityLabel(formData.video.quality) }}</DescriptionsItem>
              <DescriptionsItem label="字体大小">{{ formData.subtitle.style.fontSize }}px</DescriptionsItem>
              <DescriptionsItem label="处理线程">{{ formData.processing.threads }}</DescriptionsItem>
            </Descriptions>
          </div>
        </div>
      </div>
    </div>

    <!-- 验证结果模态框 -->
    <Modal
      v-model:open="validationModalVisible"
      title="模板验证结果"
      :footer="null"
      width="600px"
    >
      <div v-if="validationResult">
        <div v-if="validationResult.isValid" class="validation-success">
          <CheckCircleOutlined class="success-icon" />
          <h3>验证通过</h3>
          <p>模板配置有效，可以正常使用。</p>
        </div>
        
        <div v-else class="validation-error">
          <ExclamationCircleOutlined class="error-icon" />
          <h3>验证失败</h3>
          <div class="error-list">
            <Alert
              v-for="error in validationResult.errors"
              :key="error"
              :message="error"
              type="error"
              show-icon
              style="margin-bottom: 8px"
            />
          </div>
        </div>
        
        <div v-if="validationResult.warnings.length > 0" class="validation-warnings">
          <h4>警告</h4>
          <div class="warning-list">
            <Alert
              v-for="warning in validationResult.warnings"
              :key="warning"
              :message="warning"
              type="warning"
              show-icon
              style="margin-bottom: 8px"
            />
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Button, 
  Form, 
  FormItem, 
  Input, 
  TextArea, 
  Select, 
  SelectOption,
  InputNumber, 
  Radio, 
  Switch, 
  Tabs, 
  TabPane, 
  Collapse, 
  CollapsePanel,
  Modal,
  Alert,
  Descriptions,
  DescriptionsItem,
  ColorPicker,
  message
} from 'ant-design-vue'
import { 
  ArrowLeftOutlined, 
  EyeOutlined, 
  CheckCircleOutlined, 
  SaveOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'

import { templateManager } from '../templates/template-manager'
import type { Template, TemplateConfig, TemplateValidation, TemplateCategory } from '../templates/template-config'
import { DEFAULT_TEMPLATE_CONFIG } from '../templates/template-config'

// Router
const router = useRouter()
const route = useRoute()

// State
const activeTab = ref('basic')
const subtitleTabs = ref(['style', 'position', 'timing'])
const saving = ref(false)
const validationModalVisible = ref(false)
const validationResult = ref<TemplateValidation | null>(null)

// Template data
const templateId = ref<string | null>(null)
const template = ref<Template | null>(null)
const isNewTemplate = computed(() => !templateId.value)

// Form data
const formData = reactive<TemplateConfig & { category: TemplateCategory; tags: string[] }>({
  ...DEFAULT_TEMPLATE_CONFIG,
  category: 'other',
  tags: []
})

// Categories
const categories = [
  { label: '商务', value: 'business' },
  { label: '教育', value: 'education' },
  { label: '娱乐', value: 'entertainment' },
  { label: '营销', value: 'marketing' },
  { label: '教程', value: 'tutorial' },
  { label: '演示', value: 'presentation' },
  { label: '纪录片', value: 'documentary' },
  { label: '社交', value: 'social' },
  { label: '新闻', value: 'news' },
  { label: '游戏', value: 'gaming' },
  { label: '医疗', value: 'medical' },
  { label: '法律', value: 'legal' },
  { label: '金融', value: 'finance' },
  { label: '技术', value: 'technology' },
  { label: '其他', value: 'other' }
]

// Computed
const subtitlePreviewStyle = computed(() => ({
  fontFamily: formData.subtitle.style.fontFamily,
  fontSize: `${formData.subtitle.style.fontSize}px`,
  fontWeight: formData.subtitle.style.fontWeight,
  color: formData.subtitle.style.color,
  backgroundColor: formData.subtitle.style.backgroundColor,
  borderColor: formData.subtitle.style.borderColor,
  borderWidth: `${formData.subtitle.style.borderWidth}px`,
  borderStyle: 'solid',
  textAlign: formData.subtitle.position.alignment,
  padding: '8px 12px',
  borderRadius: '4px',
  display: 'inline-block'
}))

// Methods
const goBack = () => {
  router.push('/templates')
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

const previewTemplate = () => {
  // 实现预览功能
  message.info('预览功能开发中...')
}

const validateTemplate = () => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const tempTemplate: Template = {
    metadata: {
      id: 'temp',
      name: formData.name,
      description: formData.description,
      version: '1.0.0',
      author: 'User',
      category: formData.category,
      tags: formData.tags,
      thumbnail: '',
      createdAt: new Date(),
      updatedAt: new Date(),
      downloads: 0,
      rating: 0,
      compatibility: ['2.0.0+'],
      size: 0
    },
    config: {
      name: formData.name,
      description: formData.description,
      video: formData.video,
      audio: formData.audio,
      subtitle: formData.subtitle,
      processing: formData.processing,
      output: formData.output,
      advanced: formData.advanced
    }
  }
  
  validationResult.value = templateManager.validateTemplate('temp') || {
    isValid: false,
    errors: ['验证失败'],
    warnings: [],
    compatibility: { version: '2.0.0', features: [], missing: [] }
  }
  
  validationModalVisible.value = true
}

const saveTemplate = () => {
  saving.value = true
  
  try {
    const config: TemplateConfig = {
      name: formData.name,
      description: formData.description,
      video: formData.video,
      audio: formData.audio,
      subtitle: formData.subtitle,
      processing: formData.processing,
      output: formData.output,
      advanced: formData.advanced
    }
    
    if (isNewTemplate.value) {
      // 创建新模板
      const newId = templateManager.createTemplate(config, {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        tags: formData.tags
      })
      
      message.success('模板创建成功')
      router.push(`/templates/edit/${newId}`)
    }
    else {
      // 更新现有模板
      templateManager.updateTemplate(templateId.value!, {
        config,
        metadata: {
          ...template.value!.metadata,
          name: formData.name,
          description: formData.description,
          category: formData.category,
          tags: formData.tags,
          updatedAt: new Date()
        }
      })
      
      message.success('模板保存成功')
    }
  }
  catch (error) {
    message.error(`保存失败: ${error instanceof Error ? error.message : '未知错误'}`)
  }
  finally {
    saving.value = false
  }
}

const refreshPreview = () => {
  // 刷新预览
  message.info('预览已刷新')
}

// 加载模板数据
const loadTemplate = () => {
  const id = route.params.id as string
  if (id && id !== 'new') {
    templateId.value = id
    template.value = templateManager.getTemplate(id) || null
    
    if (template.value) {
      // 填充表单数据
      Object.assign(formData, template.value.config)
      formData.category = template.value.metadata.category
      formData.tags = template.value.metadata.tags
    }
  }
}

// Lifecycle
onMounted(() => {
  loadTemplate()
})

// Watch route changes
watch(() => route.params.id, () => {
  loadTemplate()
})
</script>

<style scoped>
.template-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.template-header {
  background: white;
  border-bottom: 1px solid #e8e8e8;
  padding: 16px 24px;
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title h2 {
  margin: 0;
  color: #262626;
  font-size: 20px;
  font-weight: 500;
}

.header-buttons {
  display: flex;
  gap: 12px;
}

.template-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.config-panel {
  flex: 1;
  background: white;
  border-right: 1px solid #e8e8e8;
  overflow-y: auto;
}

.config-panel .ant-tabs {
  height: 100%;
}

.config-panel .ant-tabs-content {
  height: calc(100% - 46px);
  overflow-y: auto;
  padding: 24px;
}

.preview-panel {
  width: 400px;
  background: white;
  overflow-y: auto;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.preview-header h3 {
  margin: 0;
  color: #262626;
  font-size: 16px;
  font-weight: 500;
}

.preview-content {
  padding: 24px;
}

.preview-video {
  margin-bottom: 24px;
}

.video-placeholder {
  aspect-ratio: 16/9;
  background: #fafafa;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
  position: relative;
}

.play-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.resolution {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.preview-subtitle {
  margin-bottom: 24px;
  text-align: center;
}

.subtitle-sample {
  max-width: 100%;
  word-wrap: break-word;
}

.margin-controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.margin-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.margin-row span {
  min-width: 24px;
  color: #666;
}

.naming-hint {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.validation-success,
.validation-error {
  text-align: center;
  padding: 24px;
}

.success-icon {
  font-size: 48px;
  color: #52c41a;
  margin-bottom: 16px;
}

.error-icon {
  font-size: 48px;
  color: #ff4d4f;
  margin-bottom: 16px;
}

.validation-success h3,
.validation-error h3 {
  margin-bottom: 8px;
  color: #262626;
}

.error-list,
.warning-list {
  text-align: left;
  margin-top: 16px;
}

.validation-warnings {
  margin-top: 24px;
}

.validation-warnings h4 {
  color: #262626;
  margin-bottom: 12px;
}

@media (max-width: 1200px) {
  .preview-panel {
    width: 350px;
  }
}

@media (max-width: 768px) {
  .template-content {
    flex-direction: column;
  }
  
  .preview-panel {
    width: 100%;
    max-height: 400px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-buttons {
    justify-content: center;
  }
}
</style>