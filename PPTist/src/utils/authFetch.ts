/**
 * 带认证的 Fetch 工具
 * 自动附带 Token 到请求头
 */

/**
 * 获取认证头
 */
export const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {}
  const token = localStorage.getItem('auth_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

/**
 * 获取带 Content-Type 的认证头
 */
export const getAuthJsonHeaders = (): Record<string, string> => {
  return {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  }
}

/**
 * 带认证的 fetch 封装
 */
export const authFetch = (url: string, options: RequestInit = {}): Promise<Response> => {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  }
  
  return fetch(url, {
    ...options,
    headers,
  })
}

/**
 * 带认证的 JSON fetch
 */
export const authJsonFetch = (url: string, options: RequestInit = {}): Promise<Response> => {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...options.headers,
  }
  
  return fetch(url, {
    ...options,
    headers,
  })
}
