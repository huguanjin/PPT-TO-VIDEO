/**
 * PPT编辑器自动保存配置
 */
export interface AutoSaveConfig {
  enabled: boolean
  interval: number // 自动保存间隔（分钟）
  maxBackups: number // 最大备份数量
  showNotification: boolean // 是否显示保存通知
}

export const defaultAutoSaveConfig: AutoSaveConfig = {
  enabled: true,
  interval: 5, // 默认5分钟
  maxBackups: 10,
  showNotification: true
}

// 从localStorage获取配置
export const getAutoSaveConfig = (): AutoSaveConfig => {
  try {
    const stored = localStorage.getItem('ppt-auto-save-config')
    if (stored) {
      return { ...defaultAutoSaveConfig, ...JSON.parse(stored) }
    }
  }
  catch (error) {
    // 忽略加载错误，使用默认配置
  }
  return defaultAutoSaveConfig
}

// 保存配置到localStorage
export const saveAutoSaveConfig = (config: AutoSaveConfig): void => {
  try {
    localStorage.setItem('ppt-auto-save-config', JSON.stringify(config))
  }
  catch (error) {
    // 忽略保存错误
  }
}

export default {
  getAutoSaveConfig,
  saveAutoSaveConfig,
  defaultAutoSaveConfig
}
