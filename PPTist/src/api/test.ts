/**
 * API基类功能测试
 */

import { api, checkApiHealth } from './index'

/**
 * 测试API基类基础功能
 */
export async function testApiBase() {
  try {
    // eslint-disable-next-line no-console
    console.log('🧪 开始测试API基类...')
    
    // 1. 测试健康检查
    // eslint-disable-next-line no-console
    console.log('1️⃣ 测试健康检查...')
    const health = await checkApiHealth()
    // eslint-disable-next-line no-console
    console.log('   健康状态:', health)
    
    // 2. 测试GET请求
    // eslint-disable-next-line no-console
    console.log('2️⃣ 测试GET请求...')
    try {
      const response = await api.get('/health')
      // eslint-disable-next-line no-console
      console.log('   GET请求成功:', response)
    }
    catch (error: unknown) {
      // eslint-disable-next-line no-console
      console.log('   GET请求失败 (预期):', error instanceof Error ? error.message : '未知错误')
    }
    
    // 3. 测试POST请求
    // eslint-disable-next-line no-console
    console.log('3️⃣ 测试POST请求...')
    try {
      const response = await api.post('/api/test', { test: true })
      // eslint-disable-next-line no-console
      console.log('   POST请求成功:', response)
    }
    catch (error: unknown) {
      // eslint-disable-next-line no-console
      console.log('   POST请求失败 (预期):', error instanceof Error ? error.message : '未知错误')
    }
    
    // eslint-disable-next-line no-console
    console.log('✅ API基类测试完成')
    return true
    
  }
  catch (error: unknown) {
    // eslint-disable-next-line no-console
    console.error('❌ API基类测试失败:', error)
    return false
  }
}

/**
 * 在开发环境下自动运行测试
 */
if (import.meta.env.DEV && import.meta.env.VITE_API_TEST === 'true') {
  testApiBase()
}
