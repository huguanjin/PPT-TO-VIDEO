<template>
  <div class="template-marketplace">
    <!-- 页面头部 -->
    <div class="marketplace-header">
      <div class="header-content">
        <div class="title-section">
          <h1>模板市场</h1>
          <p>发现和分享优质的视频生成模板</p>
        </div>
        
        <div class="header-actions">
          <Button type="primary" @click="createTemplate">
            <template #icon>
              <PlusOutlined />
            </template>
            创建模板
          </Button>
          
          <Button @click="importTemplate">
            <template #icon>
              <ImportOutlined />
            </template>
            导入模板
          </Button>
        </div>
      </div>
    </div>

    <!-- 搜索和过滤 -->
    <div class="search-section">
      <div class="search-controls">
        <Input.Search
          v-model:value="searchTerm"
          placeholder="搜索模板..."
          style="width: 300px"
          @search="handleSearch"
        />
        
        <Select
          v-model:value="selectedCategory"
          placeholder="选择分类"
          style="width: 150px"
          @change="handleCategoryChange"
        >
          <SelectOption value="">全部分类</SelectOption>
          <SelectOption v-for="cat in categories" :key="cat.value" :value="cat.value">
            {{ cat.label }}
          </SelectOption>
        </Select>
        
        <Select
          v-model:value="sortBy"
          placeholder="排序方式"
          style="width: 150px"
          @change="handleSortChange"
        >
          <SelectOption value="rating">评分</SelectOption>
          <SelectOption value="downloads">下载量</SelectOption>
          <SelectOption value="updatedAt">更新时间</SelectOption>
          <SelectOption value="name">名称</SelectOption>
        </Select>
        
        <Button @click="clearFilters">清除筛选</Button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="marketplace-content">
      <Tabs v-model:activeKey="activeTab" size="large">
        <!-- 推荐模板 -->
        <TabPane key="featured" tab="推荐">
          <div class="section-header">
            <h2>精选模板</h2>
            <p>编辑推荐的高质量模板</p>
          </div>
          
          <div class="template-grid">
            <TemplateCard
              v-for="template in marketplace.featured"
              :key="template.metadata.id"
              :template="template"
              @use="useTemplate"
              @preview="previewTemplate"
              @edit="editTemplate"
              @download="downloadTemplate"
              @clone="cloneTemplate"
            />
          </div>
        </TabPane>

        <!-- 热门模板 -->
        <TabPane key="popular" tab="热门">
          <div class="section-header">
            <h2>热门模板</h2>
            <p>下载量最高的模板</p>
          </div>
          
          <div class="template-grid">
            <TemplateCard
              v-for="template in marketplace.popular"
              :key="template.metadata.id"
              :template="template"
              @use="useTemplate"
              @preview="previewTemplate"
              @edit="editTemplate"
              @download="downloadTemplate"
              @clone="cloneTemplate"
            />
          </div>
        </TabPane>

        <!-- 最新模板 -->
        <TabPane key="recent" tab="最新">
          <div class="section-header">
            <h2>最新模板</h2>
            <p>最近更新的模板</p>
          </div>
          
          <div class="template-grid">
            <TemplateCard
              v-for="template in marketplace.recent"
              :key="template.metadata.id"
              :template="template"
              @use="useTemplate"
              @preview="previewTemplate"
              @edit="editTemplate"
              @download="downloadTemplate"
              @clone="cloneTemplate"
            />
          </div>
        </TabPane>

        <!-- 我的模板 -->
        <TabPane key="mine" tab="我的模板">
          <div class="section-header">
            <h2>我的模板</h2>
            <p>您创建和导入的模板</p>
          </div>
          
          <div class="template-grid">
            <TemplateCard
              v-for="template in marketplace.userTemplates"
              :key="template.metadata.id"
              :template="template"
              :show-management="true"
              @use="useTemplate"
              @preview="previewTemplate"
              @edit="editTemplate"
              @delete="deleteTemplate"
              @export="exportTemplate"
              @clone="cloneTemplate"
            />
          </div>
          
          <Empty v-if="marketplace.userTemplates.length === 0" description="暂无自定义模板">
            <Button type="primary" @click="createTemplate">创建第一个模板</Button>
          </Empty>
        </TabPane>

        <!-- 分类浏览 -->
        <TabPane key="categories" tab="分类">
          <div class="categories-section">
            <div class="category-grid">
              <div
                v-for="category in categoriesWithCount"
                :key="category.value"
                class="category-card"
                @click="browseCategory(category.value)"
              >
                <div class="category-icon">
                  <component :is="getCategoryIcon(category.value)" />
                </div>
                <h3>{{ category.label }}</h3>
                <p>{{ category.count }} 个模板</p>
              </div>
            </div>
          </div>
        </TabPane>
      </Tabs>
    </div>

    <!-- 模板导入对话框 -->
    <Modal
      v-model:open="importModalVisible"
      title="导入模板"
      :footer="null"
      width="600px"
    >
      <div class="import-section">
        <Tabs v-model:activeKey="importTab">
          <TabPane key="file" tab="文件导入">
            <Upload.Dragger
              :before-upload="handleFileImport"
              :show-upload-list="false"
              accept=".json"
            >
              <p class="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p class="ant-upload-hint">支持 JSON 格式的模板文件</p>
            </Upload.Dragger>
          </TabPane>
          
          <TabPane key="url" tab="URL导入">
            <Form :model="importForm" layout="vertical">
              <FormItem label="模板URL">
                <Input v-model:value="importForm.url" placeholder="输入模板文件URL" />
              </FormItem>
              
              <FormItem>
                <Button type="primary" @click="importFromUrl" :loading="importing">
                  导入
                </Button>
              </FormItem>
            </Form>
          </TabPane>
          
          <TabPane key="text" tab="文本导入">
            <Form :model="importForm" layout="vertical">
              <FormItem label="模板JSON">
                <TextArea
                  v-model:value="importForm.json"
                  placeholder="粘贴模板JSON内容"
                  :rows="10"
                />
              </FormItem>
              
              <FormItem>
                <Button type="primary" @click="importFromText" :loading="importing">
                  导入
                </Button>
              </FormItem>
            </Form>
          </TabPane>
        </Tabs>
      </div>
    </Modal>

    <!-- 统计信息 -->
    <div class="statistics-section">
      <Row :gutter="24">
        <Col :span="6">
          <Statistic title="总模板数" :value="statistics.total" />
        </Col>
        <Col :span="6">
          <Statistic title="总下载量" :value="statistics.totalDownloads" />
        </Col>
        <Col :span="6">
          <Statistic title="平均评分" :value="statistics.averageRating" :precision="1" />
        </Col>
        <Col :span="6">
          <Statistic title="用户模板" :value="statistics.userTemplates" />
        </Col>
      </Row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Button,
  Input,
  Select,
  SelectOption,
  Tabs,
  TabPane,
  Modal,
  Upload,
  Form,
  FormItem,
  TextArea,
  Empty,
  Row,
  Col,
  Statistic,
  message
} from 'ant-design-vue'
import {
  PlusOutlined,
  ImportOutlined,
  InboxOutlined,
  ShopOutlined,
  BookOutlined,
  PlayCircleOutlined,
  CameraOutlined,
  GlobalOutlined,
  TrophyOutlined,
  BulbOutlined,
  HeartOutlined,
  ToolOutlined
} from '@ant-design/icons-vue'

import { templateManager } from '../templates/template-manager'
import type { Template, TemplateCategory, TemplateMarketplace, TemplateFilter } from '../templates/template-config'
import TemplateCard from './TemplateCard.vue'

// Router
const router = useRouter()

// State
const activeTab = ref('featured')
const importTab = ref('file')
const importModalVisible = ref(false)
const importing = ref(false)

// Search and filter
const searchTerm = ref('')
const selectedCategory = ref<TemplateCategory | ''>('')
const sortBy = ref('rating')

// Import form
const importForm = reactive({
  url: '',
  json: ''
})

// Data
const marketplace = ref<TemplateMarketplace>({
  featured: [],
  popular: [],
  recent: [],
  categories: {} as Record<TemplateCategory, Template[]>,
  userTemplates: []
})

const statistics = ref({
  total: 0,
  categories: {} as Record<string, number>,
  averageRating: 0,
  totalDownloads: 0,
  userTemplates: 0,
  recentlyUpdated: 0
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
const categoriesWithCount = computed(() => {
  return categories.map(cat => ({
    ...cat,
    count: marketplace.value.categories[cat.value as TemplateCategory]?.length || 0
  }))
})

// Methods
const loadMarketplace = () => {
  marketplace.value = templateManager.getMarketplace()
  statistics.value = templateManager.getStatistics()
}

const createTemplate = () => {
  router.push('/templates/edit/new')
}

const importTemplate = () => {
  importModalVisible.value = true
}

const useTemplate = (template: Template) => {
  // 应用模板到当前项目
  message.success(`已应用模板: ${template.metadata.name}`)
  router.push('/workspace')
}

const previewTemplate = (template: Template) => {
  // 预览模板
  message.info(`预览模板: ${template.metadata.name}`)
}

const editTemplate = (template: Template) => {
  router.push(`/templates/edit/${template.metadata.id}`)
}

const deleteTemplate = (template: Template) => {
  Modal.confirm({
    title: '删除模板',
    content: `确定要删除模板 "${template.metadata.name}" 吗？此操作不可恢复。`,
    onOk: () => {
      templateManager.deleteTemplate(template.metadata.id)
      loadMarketplace()
      message.success('模板已删除')
    }
  })
}

const downloadTemplate = (template: Template) => {
  const exportData = templateManager.exportTemplate(template.metadata.id)
  if (exportData) {
    const blob = new Blob([exportData], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${template.metadata.name}.json`
    a.click()
    URL.revokeObjectURL(url)
    message.success('模板已下载')
  }
}

const exportTemplate = (template: Template) => {
  downloadTemplate(template)
}

const cloneTemplate = (template: Template) => {
  const newId = templateManager.cloneTemplate(template.metadata.id)
  if (newId) {
    message.success('模板已复制')
    loadMarketplace()
    router.push(`/templates/edit/${newId}`)
  }
}

const handleSearch = () => {
  // 实现搜索功能
  const filter: TemplateFilter = {
    searchTerm: searchTerm.value,
    category: selectedCategory.value || undefined
  }
  
  const results = templateManager.searchTemplates(filter, {
    field: sortBy.value as any,
    order: 'desc'
  })
  
  // 更新显示结果
  message.info(`找到 ${results.length} 个匹配的模板`)
}

const handleCategoryChange = () => {
  handleSearch()
}

const handleSortChange = () => {
  handleSearch()
}

const clearFilters = () => {
  searchTerm.value = ''
  selectedCategory.value = ''
  sortBy.value = 'rating'
  loadMarketplace()
}

const browseCategory = (category: TemplateCategory) => {
  selectedCategory.value = category
  activeTab.value = 'featured'
  handleSearch()
}

const handleFileImport = (file: File) => {
  importing.value = true
  
  templateManager.importTemplate(file)
    .then(result => {
      if (result.success) {
        message.success('模板导入成功')
        loadMarketplace()
        importModalVisible.value = false
      } else {
        message.error(`导入失败: ${result.errors.join(', ')}`)
      }
    })
    .catch(error => {
      message.error(`导入失败: ${error.message}`)
    })
    .finally(() => {
      importing.value = false
    })
  
  return false // 阻止自动上传
}

const importFromUrl = async () => {
  if (!importForm.url) {
    message.error('请输入URL')
    return
  }
  
  importing.value = true
  
  try {
    const response = await fetch(importForm.url)
    const json = await response.text()
    
    const result = await templateManager.importTemplate(json)
    if (result.success) {
      message.success('模板导入成功')
      loadMarketplace()
      importModalVisible.value = false
      importForm.url = ''
    } else {
      message.error(`导入失败: ${result.errors.join(', ')}`)
    }
  } catch (error) {
    message.error(`导入失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    importing.value = false
  }
}

const importFromText = async () => {
  if (!importForm.json) {
    message.error('请输入JSON内容')
    return
  }
  
  importing.value = true
  
  try {
    const result = await templateManager.importTemplate(importForm.json)
    if (result.success) {
      message.success('模板导入成功')
      loadMarketplace()
      importModalVisible.value = false
      importForm.json = ''
    } else {
      message.error(`导入失败: ${result.errors.join(', ')}`)
    }
  } catch (error) {
    message.error(`导入失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    importing.value = false
  }
}

const getCategoryIcon = (category: string) => {
  const iconMap: Record<string, any> = {
    business: ShopOutlined,
    education: BookOutlined,
    entertainment: PlayCircleOutlined,
    marketing: TrophyOutlined,
    tutorial: BulbOutlined,
    presentation: CameraOutlined,
    documentary: BookOutlined,
    social: HeartOutlined,
    news: GlobalOutlined,
    gaming: PlayCircleOutlined,
    medical: HeartOutlined,
    legal: BookOutlined,
    finance: ShopOutlined,
    technology: ToolOutlined,
    other: ToolOutlined
  }
  
  return iconMap[category] || ToolOutlined
}

// Lifecycle
onMounted(() => {
  loadMarketplace()
})
</script>

<style scoped>
.template-marketplace {
  background: #f5f5f5;
  min-height: 100vh;
}

.marketplace-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 48px 24px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h1 {
  font-size: 36px;
  font-weight: bold;
  margin: 0 0 8px 0;
  color: white;
}

.title-section p {
  font-size: 18px;
  margin: 0;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 16px;
}

.search-section {
  background: white;
  padding: 24px;
  border-bottom: 1px solid #e8e8e8;
}

.search-controls {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 16px;
  align-items: center;
}

.marketplace-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  background: white;
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #262626;
}

.section-header p {
  color: #8c8c8c;
  margin: 0;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
}

.categories-section {
  padding: 24px 0;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 24px;
}

.category-card {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.1);
  transform: translateY(-2px);
}

.category-icon {
  font-size: 48px;
  color: #1890ff;
  margin-bottom: 16px;
}

.category-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #262626;
}

.category-card p {
  color: #8c8c8c;
  margin: 0;
}

.import-section {
  padding: 24px 0;
}

.statistics-section {
  background: white;
  padding: 24px;
  margin-top: 24px;
  border-radius: 8px;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 24px;
    text-align: center;
  }
  
  .search-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .template-grid {
    grid-template-columns: 1fr;
  }
  
  .category-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
  
  .title-section h1 {
    font-size: 28px;
  }
  
  .title-section p {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .marketplace-header {
    padding: 32px 16px;
  }
  
  .search-section,
  .marketplace-content,
  .statistics-section {
    padding: 16px;
  }
  
  .category-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>