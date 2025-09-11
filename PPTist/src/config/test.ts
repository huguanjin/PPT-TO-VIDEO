/**
 * 前端配置测试脚本
 */

/* eslint-disable no-console */

import { API_BASE_URL, API_ENDPOINTS, getApiUrl, checkApiHealth } from '@/config/api'

export const testApiConfig = async () => {
  console.log('🔧 测试API配置...')
  
  // 显示配置信息
  console.log('配置信息:')
  console.log('  API基础URL:', API_BASE_URL)
  console.log('  环境模式:', import.meta.env.MODE)
  console.log('  环境变量:', {
    VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    VITE_API_HOST: import.meta.env.VITE_API_HOST,
    VITE_API_PORT: import.meta.env.VITE_API_PORT,
  })
  
  // 测试URL构建
  console.log('\nAPI端点测试:')
  console.log('  健康检查URL:', getApiUrl(API_ENDPOINTS.HEALTH))
  console.log('  PPT保存URL:', getApiUrl(API_ENDPOINTS.PPT_SAVE))
  console.log('  工作流启动URL:', getApiUrl(API_ENDPOINTS.WORKFLOW_START))
  
  // 测试API连通性
  console.log('\n🔗 测试API连通性...')
  const isHealthy = await checkApiHealth()
  
  if (isHealthy) {
    console.log('✅ API服务连接成功')
    return true
  }
  
  console.log('❌ API服务连接失败')
  console.log('请检查:')
  console.log('  1. 后端API服务是否启动')
  console.log('  2. 端口配置是否正确')
  console.log('  3. 网络连接是否正常')
  return false
}

// 在开发模式下自动运行测试
if (import.meta.env.DEV) {
  // 延迟执行，确保DOM加载完成
  setTimeout(async () => {
    await testApiConfig()
  }, 1000)
}
