#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fish TTS 配音角色 API
提供Fish TTS配音角色列表和配置选项
"""

from flask import Blueprint, jsonify, request
import json
from pathlib import Path
import logging

# 创建蓝图
bp = Blueprint('fish_tts_voices', __name__, url_prefix='/api/fish-tts')

# 配置日志
logger = logging.getLogger(__name__)

def load_fish_tts_config():
    """加载Fish TTS配音角色配置"""
    try:
        # 配置文件路径
        config_path = Path(__file__).parent.parent.parent / "config_data" / "fish_tts_config.json"
        
        if not config_path.exists():
            logger.error(f"Fish TTS配置文件不存在: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"加载Fish TTS配置失败: {e}")
        return None

@bp.route('/characters', methods=['GET'])
def get_characters():
    """获取所有可用的Fish TTS配音角色"""
    try:
        config = load_fish_tts_config()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载Fish TTS配置失败'
            }), 500
        
        # 提取所有配音角色
        all_characters = []
        fish_characters = config.get('fish_tts_characters', {})
        
        for gender_type, gender_data in fish_characters.items():
            gender_name = gender_data.get('name', gender_type)
            characters = gender_data.get('characters', [])
            
            for character in characters:
                character_info = {
                    'name': character['name'],
                    'character_id': character['character_id'],
                    'display_name': character['display_name'],
                    'description': character['description'],
                    'style': character['style'],
                    'recommended_use': character['recommended_use'],
                    'gender_type': gender_type,
                    'gender_name': gender_name
                }
                all_characters.append(character_info)
        
        return jsonify({
            'success': True,
            'data': {
                'characters': all_characters,
                'default_character': config.get('default_character', '雷军'),
                'total_count': len(all_characters),
                'api_key_configured': bool(config.get('api_key'))
            }
        })
        
    except Exception as e:
        logger.error(f"获取Fish TTS角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取Fish TTS角色失败: {str(e)}'
        }), 500

@bp.route('/characters/grouped', methods=['GET'])
def get_characters_grouped():
    """获取按性别分组的Fish TTS配音角色"""
    try:
        config = load_fish_tts_config()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载Fish TTS配置失败'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'grouped_characters': config.get('fish_tts_characters', {}),
                'default_character': config.get('default_character', '雷军'),
                'api_key_configured': bool(config.get('api_key'))
            }
        })
        
    except Exception as e:
        logger.error(f"获取分组Fish TTS角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取分组Fish TTS角色失败: {str(e)}'
        }), 500

@bp.route('/voice-settings', methods=['GET'])
def get_voice_settings():
    """获取Fish TTS语音设置选项"""
    try:
        config = load_fish_tts_config()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载Fish TTS配置失败'
            }), 500
        
        voice_settings = config.get('voice_settings', {})
        api_settings = config.get('api_settings', {})
        
        return jsonify({
            'success': True,
            'data': {
                'voice_settings': voice_settings,
                'api_settings': api_settings
            }
        })
        
    except Exception as e:
        logger.error(f"获取Fish TTS设置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取Fish TTS设置失败: {str(e)}'
        }), 500

@bp.route('/character/<character_name>', methods=['GET'])
def get_character_info(character_name):
    """获取特定Fish TTS配音角色的详细信息"""
    try:
        config = load_fish_tts_config()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载Fish TTS配置失败'
            }), 500
        
        # 查找指定的配音角色
        fish_characters = config.get('fish_tts_characters', {})
        
        for gender_type, gender_data in fish_characters.items():
            characters = gender_data.get('characters', [])
            
            for character in characters:
                if character['name'] == character_name:
                    character_info = {
                        'name': character['name'],
                        'character_id': character['character_id'],
                        'display_name': character['display_name'],
                        'description': character['description'],
                        'style': character['style'],
                        'recommended_use': character['recommended_use'],
                        'gender_type': gender_type,
                        'gender_name': gender_data.get('name', gender_type)
                    }
                    return jsonify({
                        'success': True,
                        'data': character_info
                    })
        
        return jsonify({
            'success': False,
            'message': f'未找到Fish TTS角色: {character_name}'
        }), 404
        
    except Exception as e:
        logger.error(f"获取Fish TTS角色信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取Fish TTS角色信息失败: {str(e)}'
        }), 500

@bp.route('/test-character', methods=['POST'])
def test_character():
    """测试指定Fish TTS配音角色"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        character_name = data.get('character_name')
        test_text = data.get('text', '这是Fish TTS配音测试。')
        format_type = data.get('format', 'mp3')
        latency = data.get('latency', 'normal')
        
        if not character_name:
            return jsonify({
                'success': False,
                'message': '缺少配音角色名称'
            }), 400
        
        # 获取角色ID
        config = load_fish_tts_config()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载Fish TTS配置失败'
            }), 500
        
        character_id = None
        fish_characters = config.get('fish_tts_characters', {})
        
        for gender_type, gender_data in fish_characters.items():
            characters = gender_data.get('characters', [])
            
            for character in characters:
                if character['name'] == character_name:
                    character_id = character['character_id']
                    break
            
            if character_id:
                break
        
        if not character_id:
            return jsonify({
                'success': False,
                'message': f'未找到角色: {character_name}'
            }), 400
        
        # 这里可以调用实际的Fish TTS测试功能
        # 暂时返回成功响应
        return jsonify({
            'success': True,
            'message': 'Fish TTS测试功能开发中',
            'data': {
                'character_name': character_name,
                'character_id': character_id,
                'text': test_text,
                'format': format_type,
                'latency': latency
            }
        })
        
    except Exception as e:
        logger.error(f"测试Fish TTS角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'测试Fish TTS角色失败: {str(e)}'
        }), 500

@bp.route('/api-status', methods=['GET'])
def get_api_status():
    """检查Fish TTS API状态"""
    try:
        config = load_fish_tts_config()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载Fish TTS配置失败'
            }), 500
        
        api_key = config.get('api_key')
        api_settings = config.get('api_settings', {})
        
        status_info = {
            'api_key_configured': bool(api_key),
            'api_key_length': len(api_key) if api_key else 0,
            'base_url': api_settings.get('base_url', ''),
            'timeout': api_settings.get('timeout', 30),
            'max_retries': api_settings.get('max_retries', 3)
        }
        
        return jsonify({
            'success': True,
            'data': status_info
        })
        
    except Exception as e:
        logger.error(f"获取Fish TTS API状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取Fish TTS API状态失败: {str(e)}'
        }), 500

# 错误处理
@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Fish TTS API接口不存在'
    }), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Fish TTS服务器内部错误'
    }), 500
