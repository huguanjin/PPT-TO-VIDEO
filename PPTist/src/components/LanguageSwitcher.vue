<!--
语言切换器组件 - Netflix V2 Phase 6 国际化支持
提供优雅的多语言切换界面
-->
<template>
  <div class="language-switcher">
    <!-- 当前语言显示 -->
    <div 
      class="current-language"
      @click="toggleDropdown"
      :class="{ 'dropdown-open': isDropdownOpen }"
    >
      <span class="language-flag">{{ currentFlag }}</span>
      <span class="language-name">{{ currentName }}</span>
      <span class="dropdown-arrow">{{ isDropdownOpen ? '▲' : '▼' }}</span>
    </div>

    <!-- 语言选择下拉菜单 -->
    <transition name="dropdown">
      <div v-if="isDropdownOpen" class="language-dropdown">
        <div class="dropdown-header">
          <span class="dropdown-title">{{ t('language.switch_language') }}</span>
        </div>
        
        <div class="language-options">
          <div
            v-for="locale in supportedLocales"
            :key="locale.code"
            class="language-option"
            :class="{ 
              'active': locale.code === currentLocale,
              'switching': switchingLocale === locale.code
            }"
            @click="handleLanguageSwitch(locale.code)"
          >
            <span class="option-flag">{{ locale.flag }}</span>
            <span class="option-name">{{ locale.name }}</span>
            <span v-if="locale.code === currentLocale" class="current-indicator">✓</span>
            <span v-if="switchingLocale === locale.code" class="switching-indicator">⟳</span>
          </div>
        </div>

        <div class="dropdown-footer">
          <small class="auto-detect-hint">
            {{ t('language.auto_detect') }}: {{ t('language.browser_language') }}
          </small>
        </div>
      </div>
    </transition>

    <!-- 切换状态提示 -->
    <transition name="status">
      <div v-if="switchStatus" class="switch-status" :class="switchStatus.type">
        {{ switchStatus.message }}
      </div>
    </transition>

    <!-- 点击外部关闭下拉菜单 -->
    <div 
      v-if="isDropdownOpen" 
      class="dropdown-overlay"
      @click="closeDropdown"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLanguageSwitch, useTranslation } from '../i18n/i18n'
import type { SupportedLocale } from '../i18n/config'

// 使用i18n hooks
const { t } = useTranslation()
const { 
  currentLocale, 
  supportedLocales, 
  switchLanguage, 
  getLanguageName, 
  getLanguageFlag 
} = useLanguageSwitch()

// 组件状态
const isDropdownOpen = ref(false)
const switchingLocale = ref<SupportedLocale | null>(null)
const switchStatus = ref<{
  type: 'success' | 'error' | 'info'
  message: string
} | null>(null)

// 计算属性
const currentName = computed(() => getLanguageName(currentLocale))
const currentFlag = computed(() => getLanguageFlag(currentLocale))

// 方法
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const showStatus = (type: 'success' | 'error' | 'info', messageKey: string, params?: Record<string, any>) => {
  switchStatus.value = {
    type,
    message: t(messageKey, params)
  }
  
  setTimeout(() => {
    switchStatus.value = null
  }, 3000)
}

const handleLanguageSwitch = async (locale: SupportedLocale) => {
  if (locale === currentLocale || switchingLocale.value) return
  
  switchingLocale.value = locale
  
  try {
    // 显示切换中状态
    showStatus('info', 'language.switching')
    
    // 执行语言切换
    await switchLanguage(locale)
    
    // 显示成功状态
    showStatus('success', 'language.switch_success')
    
    // 关闭下拉菜单
    closeDropdown()
  }
  catch (error) {
    // 显示错误状态
    showStatus('error', 'language.switch_failed')
  }
  finally {
    switchingLocale.value = null
  }
}

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isDropdownOpen.value) {
    closeDropdown()
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.language-switcher {
  position: relative;
  display: inline-block;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.current-language {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  font-size: 14px;
  min-width: 120px;
}

.current-language:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.current-language.dropdown-open {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.4);
}

.language-flag {
  font-size: 16px;
}

.language-name {
  flex: 1;
  text-align: left;
  font-weight: 500;
}

.dropdown-arrow {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.dropdown-open .dropdown-arrow {
  transform: rotate(180deg);
}

.language-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
  min-width: 200px;
}

.dropdown-header {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.dropdown-title {
  display: block;
}

.language-options {
  max-height: 300px;
  overflow-y: auto;
}

.language-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
}

.language-option:last-child {
  border-bottom: none;
}

.language-option:hover {
  background: rgba(102, 126, 234, 0.05);
}

.language-option.active {
  background: rgba(102, 126, 234, 0.1);
  font-weight: 600;
  color: #667eea;
}

.language-option.switching {
  background: rgba(118, 75, 162, 0.1);
  pointer-events: none;
}

.option-flag {
  font-size: 18px;
}

.option-name {
  flex: 1;
  text-align: left;
}

.current-indicator {
  color: #4CAF50;
  font-weight: bold;
}

.switching-indicator {
  color: #764ba2;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dropdown-footer {
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.02);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.auto-detect-hint {
  color: #666;
  font-size: 12px;
}

.switch-status {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  z-index: 1001;
}

.switch-status.success {
  background: #4CAF50;
  color: white;
}

.switch-status.error {
  background: #f44336;
  color: white;
}

.switch-status.info {
  background: #2196F3;
  color: white;
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: transparent;
}

/* 动画效果 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.status-enter-active,
.status-leave-active {
  transition: all 0.2s ease;
}

.status-enter-from,
.status-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .language-dropdown {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 300px;
    margin: 0 20px;
  }
  
  .dropdown-overlay {
    background: rgba(0, 0, 0, 0.3);
  }
}

/* 无障碍访问 */
.language-option:focus {
  outline: 2px solid #667eea;
  outline-offset: -2px;
}

.current-language:focus {
  outline: 2px solid rgba(255, 255, 255, 0.5);
  outline-offset: 2px;
}
</style>