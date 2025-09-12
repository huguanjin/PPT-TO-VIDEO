#!/usr/bin/env python3
"""
自定义AI模型管理API
提供模型注册、配置管理、句子分析等功能的HTTP接口
"""

from flask import Blueprint, request, jsonify
import asyncio
import logging
import traceback
from typing import Dict, Any, List
from pathlib import Path
import sys

# 添加路径
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

try:
    from core.custom_ai_models import (
        CustomAIModelManager, 
        ModelConfig, 
        ModelProvider,
        AIAnalysisRequest,
        analyze_sentence_with_ai
    )
    from utils.config_manager import ConfigManager
    CUSTOM_AI_AVAILABLE = True
except ImportError as e:
    CUSTOM_AI_AVAILABLE = False
    print(f"Warning: Custom AI models not available: {e}")

custom_ai_api = Blueprint('custom_ai_api', __name__)
logger = logging.getLogger(__name__)

# 全局AI管理器（如果可用）
ai_manager = None
if CUSTOM_AI_AVAILABLE:
    ai_manager = CustomAIModelManager()


@custom_ai_api.route('/api/custom-ai/status', methods=['GET'])
def get_custom_ai_status():
    """获取自定义AI系统状态"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'available': False,
                'message': '自定义AI模块不可用'
            })
        
        available_models = ai_manager.get_available_models()
        stats = ai_manager.get_stats()
        
        return jsonify({
            'success': True,
            'available': True,
            'data': {
                'total_models': len(available_models),
                'active_models': sum(1 for model in available_models.values() if model['is_active']),
                'stats': stats,
                'available_models': available_models
            }
        })
        
    except Exception as e:
        logger.error(f"获取自定义AI状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500


@custom_ai_api.route('/api/custom-ai/templates', methods=['GET'])
def get_model_templates():
    """获取模型配置模板"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '自定义AI模块不可用'
            })
        
        templates = ai_manager.get_model_templates()
        
        return jsonify({
            'success': True,
            'data': {
                'templates': templates,
                'providers': [provider.value for provider in ModelProvider]
            }
        })
        
    except Exception as e:
        logger.error(f"获取模型模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取模板失败: {str(e)}'
        }), 500


@custom_ai_api.route('/api/custom-ai/models', methods=['POST'])
def register_custom_model():
    """注册自定义AI模型"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '自定义AI模块不可用'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供模型配置数据'
            }), 400
        
        # 验证必要字段
        required_fields = ['model_name', 'name', 'provider', 'model_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        # 创建模型配置
        config = ModelConfig(
            name=data['name'],
            provider=ModelProvider(data['provider']),
            model_id=data['model_id'],
            api_key=data.get('api_key'),
            base_url=data.get('base_url'),
            max_tokens=data.get('max_tokens', 4000),
            temperature=data.get('temperature', 0.7),
            timeout=data.get('timeout', 300),
            support_json=data.get('support_json', True),
            custom_headers=data.get('custom_headers'),
            local_model_path=data.get('local_model_path'),
            context_length=data.get('context_length', 4096),
            enable_streaming=data.get('enable_streaming', False),
            enable_function_calling=data.get('enable_function_calling', False)
        )
        
        # 注册模型
        success = ai_manager.register_model(data['model_name'], config)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'成功注册模型: {data["model_name"]}',
                'data': {
                    'model_name': data['model_name'],
                    'config': data
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'注册模型失败: {data["model_name"]}'
            }), 500
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'配置参数错误: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"注册自定义模型失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500


@custom_ai_api.route('/api/custom-ai/analyze', methods=['POST'])
def analyze_with_custom_ai():
    """使用自定义AI模型进行文本分析"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '自定义AI模块不可用'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供分析数据'
            }), 400
        
        # 验证必要字段
        if 'text' not in data:
            return jsonify({
                'success': False,
                'message': '缺少待分析文本'
            }), 400
        
        # 获取参数
        text = data['text']
        model_name = data.get('model_name', 'default')
        task_type = data.get('task_type', 'sentence_analysis')
        context = data.get('context')
        language = data.get('language', 'zh')
        
        # 运行异步分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                analyze_sentence_with_ai(
                    text=text,
                    model_name=model_name,
                    task_type=task_type,
                    context=context,
                    language=language
                )
            )
        finally:
            loop.close()
        
        if result.success:
            return jsonify({
                'success': True,
                'data': {
                    'result': result.result,
                    'confidence': result.confidence,
                    'processing_time': result.processing_time,
                    'model_used': result.model_used,
                    'metadata': result.metadata
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result.error_message,
                'data': {
                    'processing_time': result.processing_time,
                    'model_used': result.model_used
                }
            }), 500
        
    except Exception as e:
        logger.error(f"AI分析失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'分析失败: {str(e)}'
        }), 500


@custom_ai_api.route('/api/custom-ai/batch-analyze', methods=['POST'])
def batch_analyze_with_custom_ai():
    """批量文本分析"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '自定义AI模块不可用'
            }), 400
        
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({
                'success': False,
                'message': '请提供待分析文本列表'
            }), 400
        
        texts = data['texts']
        if not isinstance(texts, list) or not texts:
            return jsonify({
                'success': False,
                'message': '文本列表格式错误'
            }), 400
        
        # 限制批处理数量
        if len(texts) > 50:
            return jsonify({
                'success': False,
                'message': '单次批处理不能超过50个文本'
            }), 400
        
        model_name = data.get('model_name', 'default')
        task_type = data.get('task_type', 'sentence_analysis')
        language = data.get('language', 'zh')
        
        results = []
        total_processing_time = 0
        
        # 逐个处理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for i, text in enumerate(texts):
                try:
                    result = loop.run_until_complete(
                        analyze_sentence_with_ai(
                            text=text,
                            model_name=model_name,
                            task_type=task_type,
                            language=language
                        )
                    )
                    
                    total_processing_time += result.processing_time
                    
                    results.append({
                        'index': i,
                        'text': text,
                        'success': result.success,
                        'result': result.result if result.success else None,
                        'error': result.error_message if not result.success else None,
                        'confidence': result.confidence,
                        'processing_time': result.processing_time
                    })
                    
                except Exception as e:
                    results.append({
                        'index': i,
                        'text': text,
                        'success': False,
                        'result': None,
                        'error': str(e),
                        'confidence': 0.0,
                        'processing_time': 0.0
                    })
        finally:
            loop.close()
        
        # 计算统计信息
        successful_count = sum(1 for r in results if r['success'])
        average_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'summary': {
                    'total_texts': len(texts),
                    'successful': successful_count,
                    'failed': len(texts) - successful_count,
                    'success_rate': successful_count / len(texts) if texts else 0,
                    'average_confidence': average_confidence,
                    'total_processing_time': total_processing_time,
                    'model_used': model_name
                }
            }
        })
        
    except Exception as e:
        logger.error(f"批量AI分析失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'批量分析失败: {str(e)}'
        }), 500


@custom_ai_api.route('/api/custom-ai/models/<model_name>/test', methods=['POST'])
def test_custom_model(model_name: str):
    """测试自定义模型连接"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '自定义AI模块不可用'
            }), 400
        
        # 使用简单的测试文本
        test_text = "这是一个测试句子，用于验证模型是否正常工作。"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                analyze_sentence_with_ai(
                    text=test_text,
                    model_name=model_name,
                    task_type="sentence_analysis"
                )
            )
        finally:
            loop.close()
        
        if result.success:
            return jsonify({
                'success': True,
                'message': f'模型 {model_name} 测试通过',
                'data': {
                    'test_text': test_text,
                    'processing_time': result.processing_time,
                    'confidence': result.confidence,
                    'model_response': result.result
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'模型 {model_name} 测试失败: {result.error_message}',
                'data': {
                    'test_text': test_text,
                    'processing_time': result.processing_time
                }
            }), 500
        
    except Exception as e:
        logger.error(f"测试模型失败 {model_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500


@custom_ai_api.route('/api/custom-ai/models', methods=['GET'])
def list_custom_models():
    """获取已注册的自定义模型列表"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '自定义AI模块不可用'
            }), 400
        
        models = ai_manager.get_available_models()
        stats = ai_manager.get_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'models': models,
                'total_models': len(models),
                'active_models': sum(1 for model in models.values() if model['is_active']),
                'system_stats': stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取列表失败: {str(e)}'
        }), 500


@custom_ai_api.route('/api/custom-ai/models/<model_name>', methods=['DELETE'])
def unregister_custom_model(model_name: str):
    """注销自定义模型"""
    try:
        if not CUSTOM_AI_AVAILABLE:
            return jsonify({
                'success': False,
                'message': '自定义AI模块不可用'
            }), 400
        
        # 检查模型是否存在
        models = ai_manager.get_available_models()
        if model_name not in models:
            return jsonify({
                'success': False,
                'message': f'模型 {model_name} 不存在'
            }), 404
        
        # 移除模型（简单实现：从内存中删除）
        if model_name in ai_manager.models:
            del ai_manager.models[model_name]
        if model_name in ai_manager.active_clients:
            del ai_manager.active_clients[model_name]
        
        return jsonify({
            'success': True,
            'message': f'成功注销模型: {model_name}'
        })
        
    except Exception as e:
        logger.error(f"注销模型失败 {model_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'注销失败: {str(e)}'
        }), 500


# 预设示例配置
@custom_ai_api.route('/api/custom-ai/examples', methods=['GET'])
def get_example_configs():
    """获取示例配置"""
    examples = {
        "ollama_local": {
            "model_name": "ollama_chatglm",
            "name": "本地Ollama ChatGLM",
            "provider": "ollama",
            "model_id": "chatglm3:6b",
            "base_url": "http://localhost:11434",
            "api_key": None,
            "temperature": 0.7,
            "max_tokens": 2048,
            "support_json": True,
            "description": "使用Ollama部署的本地ChatGLM模型"
        },
        "xinference_local": {
            "model_name": "xinference_qwen",
            "name": "XInference通义千问",
            "provider": "xinference",
            "model_id": "qwen-chat",
            "base_url": "http://localhost:9997/v1",
            "api_key": "dummy-key",
            "temperature": 0.7,
            "max_tokens": 4000,
            "support_json": True,
            "description": "使用XInference部署的通义千问模型"
        },
        "custom_openai_compatible": {
            "model_name": "custom_gpt",
            "name": "自定义OpenAI兼容API",
            "provider": "custom_api",
            "model_id": "gpt-3.5-turbo",
            "base_url": "https://your-api-endpoint.com/v1",
            "api_key": "your-api-key",
            "temperature": 0.7,
            "max_tokens": 4000,
            "support_json": True,
            "description": "自定义的OpenAI兼容API服务"
        },
        "chatglm_api": {
            "model_name": "chatglm_official",
            "name": "智谱AI ChatGLM",
            "provider": "chatglm",
            "model_id": "glm-4",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "your-chatglm-api-key",
            "temperature": 0.7,
            "max_tokens": 4000,
            "support_json": True,
            "description": "智谱AI官方ChatGLM API"
        }
    }
    
    return jsonify({
        'success': True,
        'data': {
            'examples': examples,
            'usage_instructions': {
                'step1': '选择合适的示例配置',
                'step2': '修改API密钥和端点地址', 
                'step3': '调用注册API进行模型注册',
                'step4': '使用测试API验证模型可用性',
                'step5': '开始使用分析API进行文本处理'
            }
        }
    })


if __name__ == "__main__":
    # 测试API
    pass