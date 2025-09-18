/**
 * Netflix V2 国际化系统核心功能
 * 提供多语言支持、动态切换、本地化等功能
 */

import { 
  DEFAULT_LOCALE, 
  FALLBACK_LOCALE, 
  LOCALE_STORAGE_KEY,
  SUPPORTED_LOCALES,
  type SupportedLocale 
} from './config'

// 翻译消息类型
export interface TranslationMessages {
  [key: string]: string | TranslationMessages
}

// i18n实例接口
export interface I18nInstance {
  locale: SupportedLocale
  fallbackLocale: SupportedLocale
  messages: Record<SupportedLocale, TranslationMessages>
  t: (key: string, params?: Record<string, any>) => string
  setLocale: (locale: SupportedLocale) => Promise<void>
  getLocale: () => SupportedLocale
  loadLocaleMessages: (locale: SupportedLocale) => Promise<TranslationMessages>
}

// 全局i18n实例
let i18nInstance: I18nInstance | null = null

/**
 * 从嵌套对象中获取值
 */
function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : undefined
  }, obj)
}

/**
 * 替换字符串中的参数
 */
function interpolate(template: string, params: Record<string, any> = {}): string {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    return params[key] !== undefined ? String(params[key]) : match
  })
}

/**
 * 检测浏览器语言
 */
function detectBrowserLocale(): SupportedLocale {
  const browserLang = navigator.language || navigator.languages?.[0] || DEFAULT_LOCALE
  
  // 精确匹配
  const exactMatch = SUPPORTED_LOCALES.find(lang => lang.code === browserLang)
  if (exactMatch) return exactMatch.code
  
  // 语言代码匹配 (如 zh-CN -> zh)
  const langCode = browserLang.split('-')[0]
  const langMatch = SUPPORTED_LOCALES.find(lang => lang.code.startsWith(langCode))
  if (langMatch) return langMatch.code
  
  return DEFAULT_LOCALE
}

/**
 * 从本地存储获取语言设置
 */
function getStoredLocale(): SupportedLocale | null {
  try {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (stored && SUPPORTED_LOCALES.some(lang => lang.code === stored)) {
      return stored as SupportedLocale
    }
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('Failed to read locale from localStorage:', error)
  }
  return null
}

/**
 * 保存语言设置到本地存储
 */
function setStoredLocale(locale: SupportedLocale): void {
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('Failed to save locale to localStorage:', error)
  }
}

/**
 * 加载语言包
 */
async function loadLocaleMessages(locale: SupportedLocale): Promise<TranslationMessages> {
  try {
    // 动态导入语言包
    const messages = await import(`./locales/${locale}.json`)
    return messages.default || messages
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.error(`Failed to load locale messages for ${locale}:`, error)
    
    // 如果加载失败且不是fallback语言，尝试加载fallback
    if (locale !== FALLBACK_LOCALE) {
      return loadLocaleMessages(FALLBACK_LOCALE)
    }
    
    // 返回空对象作为最后的fallback
    return {}
  }
}

/**
 * 创建i18n实例
 */
export async function createI18n(): Promise<I18nInstance> {
  // 确定初始语言
  const initialLocale = getStoredLocale() || detectBrowserLocale()
  
  // 加载初始语言包
  const initialMessages = await loadLocaleMessages(initialLocale)
  
  // 创建实例
  const instance: I18nInstance = {
    locale: initialLocale,
    fallbackLocale: FALLBACK_LOCALE,
    messages: {
      [initialLocale]: initialMessages
    } as Record<SupportedLocale, TranslationMessages>,
    
    // 翻译函数
    t(key: string, params: Record<string, any> = {}): string {
      // 尝试从当前语言获取翻译
      let value = getNestedValue(this.messages[this.locale], key)
      
      // 如果没有找到且当前语言不是fallback语言，尝试fallback
      if (value === undefined && this.locale !== this.fallbackLocale) {
        value = getNestedValue(this.messages[this.fallbackLocale], key)
      }
      
      // 如果仍然没有找到，返回key本身
      if (value === undefined) {
        // eslint-disable-next-line no-console
        console.warn(`Translation key not found: ${key}`)
        return key
      }
      
      // 如果值不是字符串，返回key
      if (typeof value !== 'string') {
        // eslint-disable-next-line no-console
        console.warn(`Translation value is not a string: ${key}`)
        return key
      }
      
      // 处理参数插值
      return interpolate(value, params)
    },
    
    // 设置语言
    async setLocale(locale: SupportedLocale): Promise<void> {
      if (this.locale === locale) return
      
      // 加载新语言包
      if (!this.messages[locale]) {
        this.messages[locale] = await loadLocaleMessages(locale)
      }
      
      // 更新当前语言
      this.locale = locale
      
      // 保存到本地存储
      setStoredLocale(locale)
      
      // 触发语言变更事件
      window.dispatchEvent(new CustomEvent('localeChanged', { 
        detail: { locale, instance: this } 
      }))
    },
    
    // 获取当前语言
    getLocale(): SupportedLocale {
      return this.locale
    },
    
    // 加载语言包
    loadLocaleMessages
  }
  
  // 设置全局实例
  i18nInstance = instance
  
  return instance
}

/**
 * 获取全局i18n实例
 */
export function useI18n(): I18nInstance {
  if (!i18nInstance) {
    throw new Error('i18n instance not initialized. Call createI18n() first.')
  }
  return i18nInstance
}

/**
 * 语言切换Hook
 */
export function useLanguageSwitch() {
  const i18n = useI18n()
  
  return {
    currentLocale: i18n.locale,
    supportedLocales: SUPPORTED_LOCALES,
    
    // 切换语言
    async switchLanguage(locale: SupportedLocale): Promise<void> {
      try {
        await i18n.setLocale(locale)
        return Promise.resolve()
      }
      catch (error) {
        // eslint-disable-next-line no-console
        console.error('Failed to switch language:', error)
        return Promise.reject(error)
      }
    },
    
    // 获取语言显示名称
    getLanguageName(locale: SupportedLocale): string {
      const lang = SUPPORTED_LOCALES.find(lang => lang.code === locale)
      return lang?.name || locale
    },
    
    // 获取语言旗帜图标
    getLanguageFlag(locale: SupportedLocale): string {
      const lang = SUPPORTED_LOCALES.find(lang => lang.code === locale)
      return lang?.flag || '🌐'
    }
  }
}

/**
 * 翻译Hook
 */
export function useTranslation() {
  const i18n = useI18n()
  
  return {
    t: i18n.t.bind(i18n),
    locale: i18n.locale,
    setLocale: i18n.setLocale.bind(i18n),
    getLocale: i18n.getLocale.bind(i18n)
  }
}

/**
 * 格式化数字
 */
export function formatNumber(
  value: number, 
  locale?: SupportedLocale, 
  options?: Intl.NumberFormatOptions
): string {
  const currentLocale = locale || i18nInstance?.locale || DEFAULT_LOCALE
  try {
    return new Intl.NumberFormat(currentLocale, options).format(value)
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('Number formatting failed:', error)
    return String(value)
  }
}

/**
 * 格式化日期
 */
export function formatDate(
  value: Date | string | number,
  locale?: SupportedLocale,
  options?: Intl.DateTimeFormatOptions
): string {
  const currentLocale = locale || i18nInstance?.locale || DEFAULT_LOCALE
  try {
    const date = typeof value === 'string' || typeof value === 'number' ? new Date(value) : value
    return new Intl.DateTimeFormat(currentLocale, options).format(date)
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('Date formatting failed:', error)
    return String(value)
  }
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(
  value: number,
  unit: Intl.RelativeTimeFormatUnit = 'second',
  locale?: SupportedLocale
): string {
  const currentLocale = locale || i18nInstance?.locale || DEFAULT_LOCALE
  try {
    return new Intl.RelativeTimeFormat(currentLocale, { numeric: 'auto' }).format(value, unit)
  }
  catch (error) {
    // eslint-disable-next-line no-console
    console.warn('Relative time formatting failed:', error)
    return String(value)
  }
}