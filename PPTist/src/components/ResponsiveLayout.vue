<template>
  <div class="responsive-layout" :class="layoutClasses">
    <!-- 移动端导航栏 -->
    <div v-if="isMobile" class="mobile-header">
      <button class="mobile-menu-btn" @click="toggleMobileMenu">
        <IconHamburgerButton class="menu-icon" />
      </button>
      <h1 class="mobile-title">{{ currentPageTitle }}</h1>
      <button v-if="showBackButton" class="mobile-back-btn" @click="goBack">
        <IconArrowLeft class="back-icon" />
      </button>
    </div>

    <!-- 侧边栏 -->
    <div 
      class="layout-sidebar" 
      :class="{ 'sidebar-open': sidebarOpen, 'sidebar-mobile': isMobile }"
    >
      <div class="sidebar-content">
        <slot name="sidebar" :isMobile="isMobile" :sidebarOpen="sidebarOpen" />
      </div>
      
      <!-- 移动端遮罩 -->
      <div 
        v-if="isMobile && sidebarOpen" 
        class="mobile-overlay"
        @click="closeMobileMenu"
      ></div>
    </div>

    <!-- 主内容区 -->
    <div class="layout-main" :class="{ 'main-shifted': sidebarOpen && !isMobile }">
      <div class="main-content">
        <!-- 桌面端标题栏 -->
        <div v-if="!isMobile" class="desktop-header">
          <div class="header-left">
            <button 
              class="sidebar-toggle" 
              @click="toggleSidebar"
              v-tooltip="sidebarOpen ? '收起侧边栏' : '展开侧边栏'"
            >
              <IconMenuFold v-if="sidebarOpen" class="toggle-icon" />
              <IconMenuUnfold v-else class="toggle-icon" />
            </button>
            <h1 class="page-title">{{ currentPageTitle }}</h1>
          </div>
          <div class="header-right">
            <slot name="header-actions" />
          </div>
        </div>

        <!-- 主要内容 -->
        <div class="content-body">
          <slot name="content" :isMobile="isMobile" :isTablet="isTablet" />
        </div>
      </div>
    </div>

    <!-- 浮动操作按钮 (移动端) -->
    <div v-if="isMobile && showFloatingActions" class="floating-actions">
      <slot name="floating-actions" />
    </div>

    <!-- 底部导航 (移动端) -->
    <div v-if="isMobile && showBottomNav" class="bottom-navigation">
      <slot name="bottom-nav" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  currentPageTitle?: string
  showBackButton?: boolean
  showFloatingActions?: boolean
  showBottomNav?: boolean
  sidebarDefaultOpen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  currentPageTitle: '配置管理',
  showBackButton: false,
  showFloatingActions: true,
  showBottomNav: false,
  sidebarDefaultOpen: true
})

const emit = defineEmits<{
  'sidebar-toggle': [open: boolean]
  'go-back': []
}>()

// 响应式状态
const windowWidth = ref(window.innerWidth)
const sidebarOpen = ref(props.sidebarDefaultOpen)

// 计算属性
const isMobile = computed(() => windowWidth.value < 768)
const isTablet = computed(() => windowWidth.value >= 768 && windowWidth.value < 1024)
const isDesktop = computed(() => windowWidth.value >= 1024)

const layoutClasses = computed(() => ({
  'layout-mobile': isMobile.value,
  'layout-tablet': isTablet.value,
  'layout-desktop': isDesktop.value,
  'sidebar-open': sidebarOpen.value
}))

// 方法
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
  emit('sidebar-toggle', sidebarOpen.value)
}

const toggleMobileMenu = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeMobileMenu = () => {
  if (isMobile.value) {
    sidebarOpen.value = false
  }
}

const goBack = () => {
  emit('go-back')
}

// 窗口大小监听
const handleResize = () => {
  windowWidth.value = window.innerWidth
  
  // 在不同屏幕尺寸间切换时自动调整侧边栏状态
  if (isMobile.value) {
    sidebarOpen.value = false
  }
  else if (isDesktop.value && !sidebarOpen.value) {
    sidebarOpen.value = props.sidebarDefaultOpen
  }
}

// 生命周期
onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize() // 初始化时调用一次
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// 暴露给父组件的方法
defineExpose({
  toggleSidebar,
  closeMobileMenu,
  isMobile,
  isTablet,
  isDesktop
})
</script>

<style lang="scss" scoped>
.responsive-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  position: relative;

  // 移动端头部
  .mobile-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 56px;
    background: #ffffff;
    border-bottom: 1px solid #e5e5e5;
    display: flex;
    align-items: center;
    padding: 0 16px;
    z-index: 1000;
    
    .mobile-menu-btn {
      background: none;
      border: none;
      padding: 8px;
      cursor: pointer;
      border-radius: 4px;
      transition: background-color 0.2s;
      
      &:hover {
        background: #f5f5f5;
      }
      
      .menu-icon {
        font-size: 20px;
        color: #333;
      }
    }
    
    .mobile-title {
      flex: 1;
      margin: 0 16px;
      font-size: 18px;
      font-weight: 600;
      color: #333;
      text-align: center;
    }
    
    .mobile-back-btn {
      background: none;
      border: none;
      padding: 8px;
      cursor: pointer;
      border-radius: 4px;
      
      .back-icon {
        font-size: 20px;
        color: #666;
      }
    }
  }

  // 侧边栏
  .layout-sidebar {
    width: 280px;
    background: #f8f9fa;
    border-right: 1px solid #e5e5e5;
    transform: translateX(0);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 999;
    
    &.sidebar-mobile {
      position: fixed;
      top: 56px;
      left: 0;
      bottom: 0;
      width: 280px;
      transform: translateX(-100%);
      box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
      
      &.sidebar-open {
        transform: translateX(0);
      }
    }
    
    .sidebar-content {
      height: 100%;
      overflow-y: auto;
      padding: 16px;
    }
    
    .mobile-overlay {
      position: fixed;
      top: 56px;
      left: 280px;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.3);
      z-index: -1;
    }
  }

  // 主内容区
  .layout-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &.main-shifted {
      margin-left: 0;
    }
    
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .desktop-header {
      height: 60px;
      background: #ffffff;
      border-bottom: 1px solid #e5e5e5;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .sidebar-toggle {
          background: none;
          border: none;
          padding: 8px;
          cursor: pointer;
          border-radius: 4px;
          transition: background-color 0.2s;
          
          &:hover {
            background: #f5f5f5;
          }
          
          .toggle-icon {
            font-size: 18px;
            color: #666;
          }
        }
        
        .page-title {
          margin: 0;
          font-size: 20px;
          font-weight: 600;
          color: #333;
        }
      }
      
      .header-right {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }
    
    .content-body {
      flex: 1;
      overflow: auto;
      padding: 24px;
    }
  }

  // 浮动操作按钮
  .floating-actions {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1000;
  }

  // 底部导航
  .bottom-navigation {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: #ffffff;
    border-top: 1px solid #e5e5e5;
    z-index: 1000;
  }

  // 移动端布局调整
  &.layout-mobile {
    .layout-main {
      margin-top: 56px;
      
      .content-body {
        padding: 16px;
      }
    }
    
    &.sidebar-open {
      .layout-sidebar {
        transform: translateX(0);
      }
    }
  }

  // 平板布局调整
  &.layout-tablet {
    .layout-sidebar {
      width: 240px;
    }
    
    .content-body {
      padding: 20px;
    }
  }

  // 桌面布局调整
  &.layout-desktop {
    .layout-sidebar {
      position: relative;
      width: 280px;
    }
  }
}

// 响应式断点
@media (max-width: 767px) {
  .responsive-layout {
    .layout-sidebar {
      width: 280px;
    }
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .responsive-layout {
    .layout-sidebar {
      width: 240px;
    }
  }
}

@media (min-width: 1024px) {
  .responsive-layout {
    .layout-sidebar {
      width: 300px;
    }
  }
}

// 暗色模式支持
@media (prefers-color-scheme: dark) {
  .responsive-layout {
    .mobile-header,
    .desktop-header,
    .layout-sidebar,
    .bottom-navigation {
      background: #1f2937;
      border-color: #374151;
      color: #f9fafb;
    }
    
    .mobile-title,
    .page-title {
      color: #f9fafb;
    }
    
    .mobile-menu-btn:hover,
    .sidebar-toggle:hover {
      background: #374151;
    }
  }
}
</style>
