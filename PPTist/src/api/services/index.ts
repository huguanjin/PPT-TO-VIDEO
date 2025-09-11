/**
 * API服务聚合 - 提供简化的服务访问接口
 */

import { getPrimaryApi } from '../index'
import { createAIService } from './aiService'
import { createTTSService } from './ttsService'
import { createWorkflowService } from './workflowService'

/**
 * 业务服务聚合类
 */
class ApiServices {
  private _ai?: ReturnType<typeof createAIService>
  private _tts?: ReturnType<typeof createTTSService>
  private _workflow?: ReturnType<typeof createWorkflowService>

  /**
   * AI服务
   */
  get ai() {
    if (!this._ai) {
      this._ai = createAIService(getPrimaryApi())
    }
    return this._ai
  }

  /**
   * TTS服务
   */
  get tts() {
    if (!this._tts) {
      this._tts = createTTSService(getPrimaryApi())
    }
    return this._tts
  }

  /**
   * 工作流服务
   */
  get workflow() {
    if (!this._workflow) {
      this._workflow = createWorkflowService(getPrimaryApi())
    }
    return this._workflow
  }

  /**
   * 重置所有服务实例
   */
  reset() {
    this._ai = undefined
    this._tts = undefined
    this._workflow = undefined
  }
}

// 创建单例实例
export const services = new ApiServices()

// 向后兼容的导出
export const aiService = services.ai
export const ttsService = services.tts
export const workflowService = services.workflow
