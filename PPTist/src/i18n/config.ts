/**
 * Netflix V2 国际化系统配置
 * 支持多语言动态切换和本地化
 */

// 支持的语言列表
export const SUPPORTED_LOCALES = [
  { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
  { code: 'en-US', name: 'English', flag: '🇺🇸' },
  { code: 'ja-JP', name: '日本語', flag: '🇯🇵' },
  { code: 'ko-KR', name: '한국어', flag: '🇰🇷' },
  { code: 'es-ES', name: 'Español', flag: '🇪🇸' },
  { code: 'fr-FR', name: 'Français', flag: '🇫🇷' }
] as const

export type SupportedLocale = typeof SUPPORTED_LOCALES[number]['code']

// 默认语言配置
export const DEFAULT_LOCALE: SupportedLocale = 'zh-CN'
export const FALLBACK_LOCALE: SupportedLocale = 'en-US'

// 本地存储键名
export const LOCALE_STORAGE_KEY = 'netflix-v2-locale'

// RTL语言列表 (Right-to-Left)
export const RTL_LOCALES: SupportedLocale[] = []

// 语言检测配置
export const LANGUAGE_DETECTION = {
  // 检测顺序：localStorage > navigator.language > 默认语言
  order: ['localStorage', 'navigator', 'default'],
  // 是否启用子标签检测 (如 zh-CN -> zh)
  checkForSimilarInSupportedLocales: true
}

// 翻译加载配置
export const TRANSLATION_CONFIG = {
  // 是否启用懒加载
  lazy: true,
  // 翻译文件格式
  format: 'json',
  // 翻译文件路径模板
  pathTemplate: '/locales/{locale}.json'
}

// 数字和日期格式化配置
export const FORMATTING_CONFIG = {
  // 数字格式化
  number: {
    'zh-CN': { style: 'decimal', minimumFractionDigits: 0 },
    'en-US': { style: 'decimal', minimumFractionDigits: 0 },
    'ja-JP': { style: 'decimal', minimumFractionDigits: 0 },
    'ko-KR': { style: 'decimal', minimumFractionDigits: 0 },
    'es-ES': { style: 'decimal', minimumFractionDigits: 0 },
    'fr-FR': { style: 'decimal', minimumFractionDigits: 0 }
  },
  // 日期格式化
  datetime: {
    'zh-CN': { year: 'numeric', month: 'long', day: 'numeric' },
    'en-US': { year: 'numeric', month: 'long', day: 'numeric' },
    'ja-JP': { year: 'numeric', month: 'long', day: 'numeric' },
    'ko-KR': { year: 'numeric', month: 'long', day: 'numeric' },
    'es-ES': { year: 'numeric', month: 'long', day: 'numeric' },
    'fr-FR': { year: 'numeric', month: 'long', day: 'numeric' }
  }
}

// 特殊字符和符号配置
export const LOCALE_SYMBOLS = {
  'zh-CN': { percent: '%', currency: '¥' },
  'en-US': { percent: '%', currency: '$' },
  'ja-JP': { percent: '%', currency: '¥' },
  'ko-KR': { percent: '%', currency: '₩' },
  'es-ES': { percent: '%', currency: '€' },
  'fr-FR': { percent: '%', currency: '€' }
}

// 语言切换动画配置
export const LANGUAGE_SWITCH_CONFIG = {
  // 切换动画持续时间(ms)
  animationDuration: 300,
  // 是否显示切换loading
  showLoading: true,
  // 是否显示切换成功提示
  showSuccessMessage: true
}