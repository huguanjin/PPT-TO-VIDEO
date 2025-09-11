/**
 * TTS服务相关类型定义
 */

/**
 * TTS引擎类型
 */
export type TTSEngine = 'edge' | 'fish' | 'openai' | 'custom'

/**
 * TTS语音信息
 */
export interface TTSVoice {
  id: string
  name: string
  language: string
  gender: 'male' | 'female' | 'neutral'
  age?: 'adult' | 'child' | 'senior'
  style?: string[]
  preview?: string
}

/**
 * Edge TTS配置
 */
export interface EdgeTTSConfig {
  enabled: boolean
  voice: string
  rate: number
  pitch: number
  volume: number
  style?: string
  role?: string
}

/**
 * Fish TTS配置
 */
export interface FishTTSConfig {
  enabled: boolean
  apiKey: string
  baseUrl?: string
  voice: string
  speed: number
  volume: number
  emotion?: string
  customVoiceId?: string
}

/**
 * OpenAI TTS配置
 */
export interface OpenAITTSConfig {
  enabled: boolean
  apiKey: string
  baseUrl?: string
  model: 'tts-1' | 'tts-1-hd'
  voice: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer'
  speed: number
  format: 'mp3' | 'opus' | 'aac' | 'flac'
}

/**
 * 自定义TTS配置
 */
export interface CustomTTSConfig {
  enabled: boolean
  name: string
  endpoint: string
  apiKey?: string
  headers?: Record<string, string>
  requestFormat: 'json' | 'form'
  responseFormat: 'audio' | 'url'
  voiceParameter: string
  textParameter: string
}

/**
 * 完整TTS配置
 */
export interface TTSConfig {
  edge: EdgeTTSConfig
  fish: FishTTSConfig
  openai: OpenAITTSConfig
  custom: CustomTTSConfig
  defaultEngine: TTSEngine
  outputFormat: 'mp3' | 'wav' | 'ogg'
  outputQuality: 'low' | 'medium' | 'high'
}

/**
 * TTS测试请求
 */
export interface TTSTestRequest {
  engine: TTSEngine
  config: EdgeTTSConfig | FishTTSConfig | OpenAITTSConfig | CustomTTSConfig
  text: string
  outputFormat?: string
}

/**
 * TTS测试结果
 */
export interface TTSTestResult {
  success: boolean
  audioUrl?: string
  audioBlob?: Blob
  duration?: number
  size?: number
  format?: string
  error?: string
  latency?: number
}

/**
 * TTS引擎状态
 */
export interface TTSEngineStatus {
  edge: {
    available: boolean
    voiceCount: number
    lastChecked?: string
  }
  fish: {
    available: boolean
    connected: boolean
    balance?: number
    lastChecked?: string
  }
  openai: {
    available: boolean
    connected: boolean
    models: string[]
    lastChecked?: string
  }
  custom: {
    available: boolean
    connected: boolean
    endpoint?: string
    lastChecked?: string
  }
}

/**
 * TTS使用统计
 */
export interface TTSUsageStats {
  totalGenerations: number
  totalDuration: number
  totalSize: number
  engineUsage: Record<TTSEngine, {
    generations: number
    duration: number
    size: number
  }>
  lastUsed?: string
}

/**
 * 语音合成任务
 */
export interface TTSTask {
  id: string
  text: string
  engine: TTSEngine
  voice: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  result?: TTSTestResult
  error?: string
  createdAt: string
  completedAt?: string
}
