"""
提示词管理API
提供RESTful接口来管理和使用AI提示词模板
"""
from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# 添加路径以导入提示词管理器
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

try:
    from core.prompt_manager import PromptManager
except ImportError as e:
    logging.error(f"无法导入PromptManager: {e}")
    PromptManager = None

# 创建蓝图
prompt_api = Blueprint('prompt_api', __name__)
logger = logging.getLogger(__name__)

def get_prompt_manager():
    """获取提示词管理器实例"""
    if PromptManager is None:
        raise ImportError("PromptManager未正确导入")
    return PromptManager()

@prompt_api.route('/api/prompts', methods=['GET'])
def get_available_prompts():
    """获取所有可用的提示词类型"""
    try:
        prompt_manager = get_prompt_manager()
        prompts = prompt_manager.get_available_prompts()
        
        # 构建详细信息
        prompt_details = []
        for prompt_type in prompts:
            prompt_details.append({
                "type": prompt_type,
                "description": prompt_manager.get_prompt_description(prompt_type)
            })
        
        return jsonify({
            "success": True,
            "prompts": prompt_details,
            "total": len(prompts)
        })
        
    except Exception as e:
        logger.error(f"获取提示词列表失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取提示词列表失败: {str(e)}"
        }), 500

@prompt_api.route('/api/prompts/subtitle-split', methods=['POST'])
def generate_subtitle_split_prompt():
    """生成字幕分割提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供JSON数据"
            }), 400
        
        text = data.get('text', '')
        if not text:
            return jsonify({
                "success": False,
                "error": "请提供要分割的文本"
            }), 400
        
        max_weight = data.get('max_weight', 75)
        num_parts = data.get('num_parts', 2)
        
        prompt_manager = get_prompt_manager()
        prompt = prompt_manager.get_subtitle_split_prompt(text, max_weight, num_parts)
        
        return jsonify({
            "success": True,
            "prompt": prompt,
            "parameters": {
                "text": text,
                "max_weight": max_weight,
                "num_parts": num_parts
            }
        })
        
    except Exception as e:
        logger.error(f"生成字幕分割提示词失败: {e}")
        return jsonify({
            "success": False,
            "error": f"生成字幕分割提示词失败: {str(e)}"
        }), 500

@prompt_api.route('/api/prompts/ppt-summary', methods=['POST'])
def generate_ppt_summary_prompt():
    """生成PPT总结提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供JSON数据"
            }), 400
        
        ppt_content = data.get('ppt_content', '')
        if not ppt_content:
            return jsonify({
                "success": False,
                "error": "请提供PPT内容"
            }), 400
        
        existing_terms = data.get('existing_terms', [])
        
        prompt_manager = get_prompt_manager()
        prompt = prompt_manager.get_ppt_summary_prompt(ppt_content, existing_terms)
        
        return jsonify({
            "success": True,
            "prompt": prompt,
            "parameters": {
                "ppt_content_length": len(ppt_content),
                "existing_terms_count": len(existing_terms)
            }
        })
        
    except Exception as e:
        logger.error(f"生成PPT总结提示词失败: {e}")
        return jsonify({
            "success": False,
            "error": f"生成PPT总结提示词失败: {str(e)}"
        }), 500

@prompt_api.route('/api/prompts/tts-optimization', methods=['POST'])
def generate_tts_optimization_prompt():
    """生成TTS优化提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供JSON数据"
            }), 400
        
        text = data.get('text', '')
        if not text:
            return jsonify({
                "success": False,
                "error": "请提供要优化的文本"
            }), 400
        
        target_duration = data.get('target_duration', 10.0)
        style = data.get('style', 'natural')
        
        prompt_manager = get_prompt_manager()
        prompt = prompt_manager.get_tts_optimization_prompt(text, target_duration, style)
        
        return jsonify({
            "success": True,
            "prompt": prompt,
            "parameters": {
                "text_length": len(text),
                "target_duration": target_duration,
                "style": style
            }
        })
        
    except Exception as e:
        logger.error(f"生成TTS优化提示词失败: {e}")
        return jsonify({
            "success": False,
            "error": f"生成TTS优化提示词失败: {str(e)}"
        }), 500

@prompt_api.route('/api/prompts/ppt-narration', methods=['POST'])
def generate_ppt_narration_prompt():
    """生成PPT解说词提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供JSON数据"
            }), 400
        
        slide_content = data.get('slide_content', '')
        if not slide_content:
            return jsonify({
                "success": False,
                "error": "请提供幻灯片内容"
            }), 400
        
        slide_context = data.get('slide_context', '')
        narration_style = data.get('narration_style', 'educational')
        
        prompt_manager = get_prompt_manager()
        prompt = prompt_manager.get_ppt_narration_prompt(slide_content, slide_context, narration_style)
        
        return jsonify({
            "success": True,
            "prompt": prompt,
            "parameters": {
                "slide_content_length": len(slide_content),
                "has_context": bool(slide_context),
                "narration_style": narration_style
            }
        })
        
    except Exception as e:
        logger.error(f"生成PPT解说词提示词失败: {e}")
        return jsonify({
            "success": False,
            "error": f"生成PPT解说词提示词失败: {str(e)}"
        }), 500

@prompt_api.route('/api/prompts/text-cleanup', methods=['POST'])
def generate_text_cleanup_prompt():
    """生成文本清理提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供JSON数据"
            }), 400
        
        text = data.get('text', '')
        if not text:
            return jsonify({
                "success": False,
                "error": "请提供要清理的文本"
            }), 400
        
        prompt_manager = get_prompt_manager()
        prompt = prompt_manager.get_text_cleanup_prompt(text)
        
        return jsonify({
            "success": True,
            "prompt": prompt,
            "parameters": {
                "text_length": len(text),
                "original_text": text[:100] + "..." if len(text) > 100 else text
            }
        })
        
    except Exception as e:
        logger.error(f"生成文本清理提示词失败: {e}")
        return jsonify({
            "success": False,
            "error": f"生成文本清理提示词失败: {str(e)}"
        }), 500

@prompt_api.route('/api/prompts/format-for-api', methods=['POST'])
def format_prompt_for_api():
    """为API调用格式化提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供JSON数据"
            }), 400
        
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({
                "success": False,
                "error": "请提供提示词内容"
            }), 400
        
        system_message = data.get('system_message', '')
        
        prompt_manager = get_prompt_manager()
        formatted = prompt_manager.format_prompt_for_api(prompt, system_message)
        
        return jsonify({
            "success": True,
            "formatted_request": formatted,
            "api_ready": True
        })
        
    except Exception as e:
        logger.error(f"格式化提示词失败: {e}")
        return jsonify({
            "success": False,
            "error": f"格式化提示词失败: {str(e)}"
        }), 500

@prompt_api.route('/api/prompts/config', methods=['GET'])
def get_prompt_config():
    """获取提示词配置信息"""
    try:
        prompt_manager = get_prompt_manager()
        
        config_info = {
            "source_language": prompt_manager.source_language,
            "target_language": prompt_manager.target_language,
            "ai_service": prompt_manager.ai_service,
            "available_prompts": prompt_manager.get_available_prompts()
        }
        
        return jsonify({
            "success": True,
            "config": config_info
        })
        
    except Exception as e:
        logger.error(f"获取提示词配置失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取提示词配置失败: {str(e)}"
        }), 500

@prompt_api.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({
        "success": False,
        "error": "API端点不存在"
    }), 404

@prompt_api.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500
