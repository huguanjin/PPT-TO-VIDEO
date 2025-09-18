/**
 * Netflix V2 Phase 6 国际化系统初始化
 * 应用启动时初始化i18n系统
 */

import { createI18n } from './i18n'

// 全局i18n实例
let globalI18n: any = null

/**
 * 初始化国际化系统
 */
export async function initializeI18n() {
  try {
    globalI18n = await createI18n()
    
    // 设置全局属性
    if (typeof window !== 'undefined') {
      (window as any).__NETFLIX_I18N__ = globalI18n
    }
    
    return globalI18n
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to initialize i18n:', error)
    throw error
  }
}

/**
 * 获取全局i18n实例
 */
export function getGlobalI18n() {
  return globalI18n
}

/**
 * Vue应用插件安装函数
 */
export function installI18n(app: any) {
  if (!globalI18n) {
    throw new Error('i18n not initialized. Call initializeI18n() first.')
  }
  
  // 提供全局属性
  app.config.globalProperties.$t = globalI18n.t.bind(globalI18n)
  app.config.globalProperties.$i18n = globalI18n
  
  // 提供依赖注入
  app.provide('i18n', globalI18n)
}

/**
 * 语言变更监听器类型
 */
export type LanguageChangeListener = (locale: string) => void

// 语言变更监听器列表
const languageChangeListeners: LanguageChangeListener[] = []

/**
 * 添加语言变更监听器
 */
export function addLanguageChangeListener(listener: LanguageChangeListener) {
  languageChangeListeners.push(listener)
  
  // 返回移除函数
  return () => {
    const index = languageChangeListeners.indexOf(listener)
    if (index > -1) {
      languageChangeListeners.splice(index, 1)
    }
  }
}

/**
 * 触发语言变更事件
 */
export function triggerLanguageChange(locale: string) {
  languageChangeListeners.forEach(listener => {
    try {
      listener(locale)
    }
    catch (error) {
      // eslint-disable-next-line no-console
      console.error('Language change listener error:', error)
    }
  })
}

// 监听全局语言变更事件
if (typeof window !== 'undefined') {
  window.addEventListener('localeChanged', (event: any) => {
    triggerLanguageChange(event.detail.locale)
  })
}