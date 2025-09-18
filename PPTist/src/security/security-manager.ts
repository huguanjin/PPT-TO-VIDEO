/**
 * 安全强化系统
 * 提供API安全验证、文件上传安全检查、XSS防护等安全措施
 */

export interface SecurityConfig {
  enableCSRF: boolean
  enableXSSProtection: boolean
  enableFileValidation: boolean
  enableRateLimiting: boolean
  enableInputSanitization: boolean
  maxFileSize: number // MB
  allowedFileTypes: string[]
  maxRequestsPerMinute: number
  sessionTimeout: number // 分钟
  enableSecurityHeaders: boolean
}

export interface SecurityViolation {
  type: 'xss' | 'csrf' | 'file_upload' | 'rate_limit' | 'invalid_input' | 'suspicious_activity'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  details: Record<string, any>
  timestamp: number
  userAgent: string
  ip: string
  userId?: string
  blocked: boolean
}

export interface FileValidationResult {
  valid: boolean
  reason?: string
  threat?: 'malware' | 'script' | 'executable' | 'oversized' | 'invalid_type'
  fileInfo: {
    name: string
    size: number
    type: string
    lastModified: number
  }
}

export interface RateLimitStatus {
  remaining: number
  resetTime: number
  limited: boolean
}

/**
 * 安全管理器
 */
export class SecurityManager {
  private static instance: SecurityManager
  private config: SecurityConfig
  private violations: SecurityViolation[] = []
  private rateLimitStore = new Map<string, { count: number; resetTime: number }>()
  private csrfTokens = new Set<string>()
  private blockedIPs = new Set<string>()
  private sessionTokens = new Map<string, { userId: string; expires: number }>()

  constructor(config?: Partial<SecurityConfig>) {
    this.config = {
      enableCSRF: true,
      enableXSSProtection: true,
      enableFileValidation: true,
      enableRateLimiting: true,
      enableInputSanitization: true,
      maxFileSize: 10, // 10MB
      allowedFileTypes: [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'application/json',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation' // PPTX
      ],
      maxRequestsPerMinute: 60,
      sessionTimeout: 30, // 30分钟
      enableSecurityHeaders: true,
      ...config
    }

    this.initializeSecurityHeaders()
    this.startCleanupTimer()
  }

  static getInstance(config?: Partial<SecurityConfig>): SecurityManager {
    if (!SecurityManager.instance) {
      SecurityManager.instance = new SecurityManager(config)
    }
    return SecurityManager.instance
  }

  /**
   * 初始化安全头
   */
  private initializeSecurityHeaders(): void {
    if (!this.config.enableSecurityHeaders || typeof document === 'undefined') {
      return
    }

    // 设置内容安全策略
    const cspMeta = document.createElement('meta')
    cspMeta.httpEquiv = 'Content-Security-Policy'
    cspMeta.content = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self'",
      "connect-src 'self'",
      "frame-ancestors 'none'"
    ].join('; ')
    document.head.appendChild(cspMeta)

    // 设置其他安全头
    const headers = [
      { name: 'X-Content-Type-Options', value: 'nosniff' },
      { name: 'X-Frame-Options', value: 'DENY' },
      { name: 'X-XSS-Protection', value: '1; mode=block' },
      { name: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' }
    ]

    headers.forEach(header => {
      const meta = document.createElement('meta')
      meta.httpEquiv = header.name
      meta.content = header.value
      document.head.appendChild(meta)
    })
  }

  /**
   * 启动清理定时器
   */
  private startCleanupTimer(): void {
    setInterval(() => {
      this.cleanupExpiredData()
    }, 60000) // 每分钟清理一次
  }

  /**
   * 清理过期数据
   */
  private cleanupExpiredData(): void {
    const now = Date.now()

    // 清理过期的会话令牌
    for (const [token, session] of this.sessionTokens.entries()) {
      if (now > session.expires) {
        this.sessionTokens.delete(token)
      }
    }

    // 清理过期的限流记录
    for (const [key, data] of this.rateLimitStore.entries()) {
      if (now > data.resetTime) {
        this.rateLimitStore.delete(key)
      }
    }

    // 保持违规记录在合理范围内
    if (this.violations.length > 1000) {
      this.violations = this.violations.slice(-1000)
    }
  }

  /**
   * 生成CSRF令牌
   */
  generateCSRFToken(): string {
    if (!this.config.enableCSRF) {
      return ''
    }

    const token = this.generateSecureToken()
    this.csrfTokens.add(token)

    // 限制令牌数量
    if (this.csrfTokens.size > 100) {
      const tokensArray = Array.from(this.csrfTokens)
      this.csrfTokens.clear()
      tokensArray.slice(-50).forEach(t => this.csrfTokens.add(t))
    }

    return token
  }

  /**
   * 验证CSRF令牌
   */
  validateCSRFToken(token: string): boolean {
    if (!this.config.enableCSRF) {
      return true
    }

    const valid = this.csrfTokens.has(token)
    
    if (!valid) {
      this.recordViolation({
        type: 'csrf',
        severity: 'high',
        message: 'Invalid CSRF token',
        details: { token },
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        ip: 'unknown',
        blocked: true
      })
    }

    // 一次性使用后删除令牌
    this.csrfTokens.delete(token)
    return valid
  }

  /**
   * XSS防护 - 清理输入
   */
  sanitizeInput(input: string): string {
    if (!this.config.enableXSSProtection) {
      return input
    }

    // 检测可能的XSS攻击
    const xssPatterns = [
      /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi,
      /<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi,
      /<embed\b[^>]*>/gi,
      /<link\b[^>]*>/gi,
      /<meta\b[^>]*>/gi
    ]

    let suspicious = false
    xssPatterns.forEach(pattern => {
      if (pattern.test(input)) {
        suspicious = true
      }
    })

    if (suspicious) {
      this.recordViolation({
        type: 'xss',
        severity: 'high',
        message: 'Potential XSS attack detected',
        details: { input: input.substring(0, 200) },
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        ip: 'unknown',
        blocked: true
      })
    }

    // 清理HTML标签和危险字符
    const sanitized = input
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;')

    return sanitized
  }

  /**
   * 验证文件上传安全性
   */
  async validateFileUpload(file: File): Promise<FileValidationResult> {
    const result: FileValidationResult = {
      valid: false,
      fileInfo: {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
      }
    }

    if (!this.config.enableFileValidation) {
      result.valid = true
      return result
    }

    // 检查文件大小
    const maxSizeBytes = this.config.maxFileSize * 1024 * 1024
    if (file.size > maxSizeBytes) {
      result.reason = `文件大小超出限制 (${this.config.maxFileSize}MB)`
      result.threat = 'oversized'
      this.recordViolation({
        type: 'file_upload',
        severity: 'medium',
        message: 'File size exceeded',
        details: { filename: file.name, size: file.size, limit: maxSizeBytes },
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        ip: 'unknown',
        blocked: true
      })
      return result
    }

    // 检查文件类型
    if (!this.config.allowedFileTypes.includes(file.type)) {
      result.reason = `不允许的文件类型: ${file.type}`
      result.threat = 'invalid_type'
      this.recordViolation({
        type: 'file_upload',
        severity: 'medium',
        message: 'Invalid file type',
        details: { filename: file.name, type: file.type },
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        ip: 'unknown',
        blocked: true
      })
      return result
    }

    // 检查文件名安全性
    const dangerousPatterns = [
      /\.(exe|bat|cmd|scr|pif|com|vbs|js|jar|app|deb|rpm)$/i,
      /\.\./,
      /[<>:"|?*]/,
      /^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/i
    ]

    const isDangerous = dangerousPatterns.some(pattern => pattern.test(file.name))
    if (isDangerous) {
      result.reason = '危险的文件名'
      result.threat = 'executable'
      this.recordViolation({
        type: 'file_upload',
        severity: 'high',
        message: 'Dangerous filename detected',
        details: { filename: file.name },
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        ip: 'unknown',
        blocked: true
      })
      return result
    }

    // 检查文件内容（简单的魔数检查）
    try {
      const buffer = await this.readFileHeader(file)
      const isValidFile = this.validateFileContent(buffer, file.type)
      
      if (!isValidFile) {
        result.reason = '文件内容与类型不匹配'
        result.threat = 'malware'
        this.recordViolation({
          type: 'file_upload',
          severity: 'high',
          message: 'File content mismatch',
          details: { filename: file.name, declaredType: file.type },
          timestamp: Date.now(),
          userAgent: navigator.userAgent,
          ip: 'unknown',
          blocked: true
        })
        return result
      }
    }
    catch (error) {
      result.reason = '文件读取失败'
      result.threat = 'malware'
      return result
    }

    result.valid = true
    return result
  }

  /**
   * 读取文件头部
   */
  private async readFileHeader(file: File): Promise<ArrayBuffer> {
    const slice = file.slice(0, 16) // 读取前16字节
    return await slice.arrayBuffer()
  }

  /**
   * 验证文件内容
   */
  private validateFileContent(buffer: ArrayBuffer, declaredType: string): boolean {
    const bytes = new Uint8Array(buffer)
    const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('')

    // 常见文件类型的魔数
    const magicNumbers: Record<string, string[]> = {
      'image/jpeg': ['ffd8ff'],
      'image/png': ['89504e47'],
      'image/gif': ['474946383761', '474946383961'],
      'image/webp': ['52494646'],
      'application/pdf': ['255044462d'],
      'application/zip': ['504b0304', '504b0506', '504b0708'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['504b0304']
    }

    const expectedMagic = magicNumbers[declaredType]
    if (!expectedMagic) {
      return true // 未知类型，跳过验证
    }

    return expectedMagic.some(magic => hex.startsWith(magic))
  }

  /**
   * 限流检查
   */
  checkRateLimit(identifier: string): RateLimitStatus {
    if (!this.config.enableRateLimiting) {
      return { remaining: Infinity, resetTime: 0, limited: false }
    }

    const now = Date.now()
    const windowMs = 60 * 1000 // 1分钟窗口
    const resetTime = now + windowMs

    let record = this.rateLimitStore.get(identifier)
    
    if (!record || now > record.resetTime) {
      record = { count: 0, resetTime }
      this.rateLimitStore.set(identifier, record)
    }

    record.count++
    const remaining = Math.max(0, this.config.maxRequestsPerMinute - record.count)
    const limited = record.count > this.config.maxRequestsPerMinute

    if (limited) {
      this.recordViolation({
        type: 'rate_limit',
        severity: 'medium',
        message: 'Rate limit exceeded',
        details: { identifier, count: record.count, limit: this.config.maxRequestsPerMinute },
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        ip: 'unknown',
        blocked: true
      })
    }

    return { remaining, resetTime: record.resetTime, limited }
  }

  /**
   * 生成安全令牌
   */
  private generateSecureToken(): string {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  /**
   * 创建会话
   */
  createSession(userId: string): string {
    const token = this.generateSecureToken()
    const expires = Date.now() + (this.config.sessionTimeout * 60 * 1000)
    
    this.sessionTokens.set(token, { userId, expires })
    return token
  }

  /**
   * 验证会话
   */
  validateSession(token: string): { valid: boolean; userId?: string } {
    const session = this.sessionTokens.get(token)
    
    if (!session || Date.now() > session.expires) {
      if (session) {
        this.sessionTokens.delete(token)
      }
      return { valid: false }
    }

    // 延长会话
    session.expires = Date.now() + (this.config.sessionTimeout * 60 * 1000)
    return { valid: true, userId: session.userId }
  }

  /**
   * 销毁会话
   */
  destroySession(token: string): void {
    this.sessionTokens.delete(token)
  }

  /**
   * 记录安全违规
   */
  private recordViolation(violation: SecurityViolation): void {
    this.violations.push(violation)

    // 检查是否需要阻止IP
    const recentViolations = this.violations.filter(
      v => v.ip === violation.ip && 
      Date.now() - v.timestamp < 5 * 60 * 1000 // 5分钟内
    )

    if (recentViolations.length >= 5) {
      this.blockedIPs.add(violation.ip)
    }

    // 触发安全事件（可以集成到日志系统）
    if (typeof window !== 'undefined' && (window as any).securityEventHandler) {
      (window as any).securityEventHandler(violation)
    }
  }

  /**
   * 检查IP是否被阻止
   */
  isIPBlocked(ip: string): boolean {
    return this.blockedIPs.has(ip)
  }

  /**
   * 解除IP阻止
   */
  unblockIP(ip: string): void {
    this.blockedIPs.delete(ip)
  }

  /**
   * 输入验证
   */
  validateInput(input: any, rules: {
    required?: boolean
    type?: 'string' | 'number' | 'email' | 'url'
    minLength?: number
    maxLength?: number
    pattern?: RegExp
    whitelist?: string[]
  }): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (rules.required && (input === null || input === undefined || input === '')) {
      errors.push('字段是必需的')
    }

    if (input !== null && input !== undefined && input !== '') {
      if (rules.type) {
        switch (rules.type) {
          case 'string':
            if (typeof input !== 'string') {
              errors.push('必须是字符串类型')
            }
            break
          case 'number':
            if (typeof input !== 'number' || isNaN(input)) {
              errors.push('必须是有效数字')
            }
            break
          case 'email':
            if (typeof input === 'string' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)) {
              errors.push('必须是有效的邮箱地址')
            }
            break
          case 'url':
            if (typeof input === 'string') {
              try {
                new URL(input)
              }
              catch {
                errors.push('必须是有效的URL')
              }
            }
            break
          default:
            // 未知类型，跳过验证
            break
        }
      }

      if (typeof input === 'string') {
        if (rules.minLength && input.length < rules.minLength) {
          errors.push(`最少需要${rules.minLength}个字符`)
        }
        if (rules.maxLength && input.length > rules.maxLength) {
          errors.push(`最多允许${rules.maxLength}个字符`)
        }
        if (rules.pattern && !rules.pattern.test(input)) {
          errors.push('格式不正确')
        }
        if (rules.whitelist && !rules.whitelist.includes(input)) {
          errors.push('不在允许的值列表中')
        }
      }
    }

    if (errors.length > 0) {
      this.recordViolation({
        type: 'invalid_input',
        severity: 'low',
        message: 'Input validation failed',
        details: { input: JSON.stringify(input), errors },
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        ip: 'unknown',
        blocked: false
      })
    }

    return { valid: errors.length === 0, errors }
  }

  /**
   * 检测可疑活动
   */
  detectSuspiciousActivity(activity: {
    type: string
    frequency: number
    timeWindow: number
    threshold: number
    userId?: string
  }): boolean {
    const { type, frequency, timeWindow, threshold, userId } = activity
    const now = Date.now()
    
    // 检查最近时间窗口内的同类活动
    const recentActivities = this.violations.filter(v => 
      v.details?.activityType === type &&
      (userId ? v.userId === userId : true) &&
      now - v.timestamp < timeWindow
    )

    if (recentActivities.length >= threshold) {
      this.recordViolation({
        type: 'suspicious_activity',
        severity: 'high',
        message: `Suspicious activity detected: ${type}`,
        details: { 
          activityType: type, 
          frequency, 
          threshold, 
          timeWindow,
          recentCount: recentActivities.length 
        },
        timestamp: now,
        userAgent: navigator.userAgent,
        ip: 'unknown',
        userId,
        blocked: true
      })
      return true
    }

    return false
  }

  /**
   * 获取安全违规记录
   */
  getViolations(filters?: {
    type?: SecurityViolation['type']
    severity?: SecurityViolation['severity']
    timeRange?: { start: number; end: number }
    limit?: number
  }): SecurityViolation[] {
    let violations = [...this.violations]

    if (filters) {
      if (filters.type) {
        violations = violations.filter(v => v.type === filters.type)
      }
      if (filters.severity) {
        violations = violations.filter(v => v.severity === filters.severity)
      }
      if (filters.timeRange) {
        violations = violations.filter(v => 
          v.timestamp >= filters.timeRange!.start &&
          v.timestamp <= filters.timeRange!.end
        )
      }
      if (filters.limit) {
        violations = violations.slice(-filters.limit)
      }
    }

    return violations
  }

  /**
   * 生成安全报告
   */
  generateSecurityReport(): {
    summary: {
      totalViolations: number
      blockedAttacks: number
      uniqueThreats: number
      riskLevel: 'low' | 'medium' | 'high' | 'critical'
    }
    breakdown: Record<string, number>
    recommendations: string[]
    } {
    const now = Date.now()
    const last24h = now - 24 * 60 * 60 * 1000
    const recentViolations = this.violations.filter(v => v.timestamp >= last24h)

    // 统计违规类型
    const breakdown: Record<string, number> = {}
    recentViolations.forEach(v => {
      breakdown[v.type] = (breakdown[v.type] || 0) + 1
    })

    const blockedAttacks = recentViolations.filter(v => v.blocked).length
    const uniqueThreats = new Set(recentViolations.map(v => v.type)).size

    // 计算风险级别
    let riskLevel: 'low' | 'medium' | 'high' | 'critical' = 'low'
    const criticalViolations = recentViolations.filter(v => v.severity === 'critical').length
    const highViolations = recentViolations.filter(v => v.severity === 'high').length

    if (criticalViolations > 0) {
      riskLevel = 'critical'
    }
    else if (highViolations > 5) {
      riskLevel = 'high'
    }
    else if (recentViolations.length > 10) {
      riskLevel = 'medium'
    }

    // 生成建议
    const recommendations: string[] = []
    if (breakdown.xss > 0) {
      recommendations.push('检测到XSS攻击尝试，建议加强输入验证')
    }
    if (breakdown.file_upload > 0) {
      recommendations.push('文件上传存在安全风险，建议审查文件类型限制')
    }
    if (breakdown.rate_limit > 0) {
      recommendations.push('检测到频繁请求，建议调整限流策略')
    }
    if (this.blockedIPs.size > 0) {
      recommendations.push(`当前有${this.blockedIPs.size}个IP被阻止，建议定期审查`)
    }

    return {
      summary: {
        totalViolations: recentViolations.length,
        blockedAttacks,
        uniqueThreats,
        riskLevel
      },
      breakdown,
      recommendations
    }
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }

  /**
   * 导出安全数据
   */
  exportSecurityData(): string {
    return JSON.stringify({
      violations: this.violations,
      blockedIPs: Array.from(this.blockedIPs),
      config: this.config,
      exportTime: new Date().toISOString()
    }, null, 2)
  }
}

// 创建默认实例
export const securityManager = SecurityManager.getInstance()

// 安全装饰器
export function SecureEndpoint(options?: {
  requireCSRF?: boolean
  rateLimit?: number
  validateInput?: boolean
}) {
  return function(target: any, propertyName: string, descriptor: PropertyDescriptor): PropertyDescriptor {
    const method = descriptor.value

    descriptor.value = async function(...args: any[]) {
      const opts = options || {}

      // CSRF检查
      if (opts.requireCSRF) {
        // 这里应该从请求头或参数中获取CSRF令牌
        const token = args[0]?.csrfToken
        if (!securityManager.validateCSRFToken(token)) {
          throw new Error('Invalid CSRF token')
        }
      }

      // 限流检查
      if (opts.rateLimit) {
        const identifier = args[0]?.userId || 'anonymous'
        const rateStatus = securityManager.checkRateLimit(identifier)
        if (rateStatus.limited) {
          throw new Error('Rate limit exceeded')
        }
      }

      // 输入验证
      if (opts.validateInput && args[0]) {
        // 基本的输入清理
        if (typeof args[0] === 'object') {
          for (const key in args[0]) {
            if (typeof args[0][key] === 'string') {
              args[0][key] = securityManager.sanitizeInput(args[0][key])
            }
          }
        }
      }

      return await method.apply(this, args)
    }

    return descriptor
  }
}