import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  
  // 获取API配置，支持环境变量和默认值
  const getApiConfig = () => {
    const apiHost = env.VITE_API_HOST || 'localhost'
    const apiPort = env.VITE_API_PORT || '8002'
    const apiBaseUrl = env.VITE_API_BASE_URL || `http://${apiHost}:${apiPort}`
    
    return {
      host: apiHost,
      port: parseInt(apiPort),
      baseUrl: apiBaseUrl
    }
  }

  const apiConfig = getApiConfig()

  // 开发模式下显示API配置信息
  if (mode === 'development') {
    // eslint-disable-next-line no-console
    console.log(`🔧 API配置: ${apiConfig.baseUrl} (模式: ${mode})`)
  }

  return {
    base: '',
    plugins: [
      vue(),
    ],
    
    // 定义全局常量
    define: {
      __API_BASE_URL__: JSON.stringify(apiConfig.baseUrl),
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
    },

    server: {
      host: '127.0.0.1',
      port: 5173,
      open: true, // 自动打开浏览器
      
      // 动态代理配置
      proxy: {
        '/api': {
          target: apiConfig.baseUrl,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, '/api'),
          configure: (proxy, options) => {
            // 代理错误处理
            proxy.on('error', (err) => {
              // eslint-disable-next-line no-console
              console.error('🚫 代理错误:', err.message)
            })
            
            proxy.on('proxyReq', (proxyReq, req) => {
              // eslint-disable-next-line no-console
              console.log(`📤 代理请求: ${req.method} ${req.url} -> ${options.target}${req.url}`)
            })
          }
        },
        
        // 添加临时文件代理（音频预览文件）
        '/temp': {
          target: apiConfig.baseUrl,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/temp/, '/temp'),
          configure: (proxy, options) => {
            proxy.on('error', (err) => {
              // eslint-disable-next-line no-console
              console.error('🚫 音频文件代理错误:', err.message)
            })
            
            proxy.on('proxyReq', (proxyReq, req) => {
              // eslint-disable-next-line no-console
              console.log(`🎵 音频文件代理: ${req.method} ${req.url} -> ${options.target}${req.url}`)
            })
          }
        },
        
        // WebSocket代理（如果需要）
        '/ws': {
          target: apiConfig.baseUrl.replace('http', 'ws'),
          ws: true,
          changeOrigin: true,
        }
      }
    },

    // 构建配置
    build: {
      // 生产环境移除console
      terserOptions: {
        compress: {
          drop_console: mode === 'production',
          drop_debugger: mode === 'production',
        },
      },
    },

    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `
            @import '@/assets/styles/variable.scss';
            @import '@/assets/styles/mixin.scss';
          `
        },
      },
    },

    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    }
  }
})
