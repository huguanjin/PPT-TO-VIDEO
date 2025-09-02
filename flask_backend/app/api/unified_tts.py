#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一 TTS 配置管理 API
同时支持 Edge TTS 和 Fish TTS 的配置管理
"""

from flask import Blueprint, jsonify, request
import json
from pathlib import Path
import logging

# 创建蓝图
bp = Blueprint('unified_tts', __name__, url_prefix='/api/tts')

# 配置日志
logger = logging.getLogger(__name__)

def load_edge_tts_config():
    """加载Edge TTS配置"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config_data" / "edge_tts_voices.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载Edge TTS配置失败: {e}")
    return None

def load_fish_tts_config():
    """加载Fish TTS配置"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config_data" / "fish_tts_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载Fish TTS配置失败: {e}")
    return None

def load_app_config():
    """加载应用配置"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config_data" / "app_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载应用配置失败: {e}")
    return None

@bp.route('/engines', methods=['GET'])
def get_tts_engines():
    """获取所有可用的TTS引擎"""
    try:
        engines = []
        
        # Edge TTS
        edge_config = load_edge_tts_config()
        if edge_config:
            edge_voices = edge_config.get('edge_tts_voices', {})
            total_edge_voices = sum(len(region_data.get('voices', [])) for region_data in edge_voices.values())
            
            engines.append({
                'id': 'edge_tts',
                'name': 'Edge TTS',
                'display_name': 'Microsoft Edge TTS',
                'description': '微软Edge文字转语音服务，免费使用',
                'voice_count': total_edge_voices,
                'languages': list(edge_voices.keys()),
                'available': True,
                'cost': 'free',
                'quality': 'high'
            })
        
        # Fish TTS
        fish_config = load_fish_tts_config()
        if fish_config:
            fish_characters = fish_config.get('fish_tts_characters', {})
            total_fish_characters = sum(len(gender_data.get('characters', [])) for gender_data in fish_characters.values())
            api_key_configured = bool(fish_config.get('api_key'))
            
            engines.append({
                'id': 'fish_tts',
                'name': 'Fish TTS',
                'display_name': 'Fish Audio TTS',
                'description': '智能语音合成服务，提供名人声音克隆',
                'voice_count': total_fish_characters,
                'languages': ['zh-CN'],
                'available': api_key_configured,
                'cost': 'paid',
                'quality': 'very_high',
                'requires_api_key': True
            })
        
        # 获取当前设置
        app_config = load_app_config()
        current_engine = 'edge_tts'
        if app_config and app_config.get('tts'):
            current_engine = app_config['tts'].get('preferred_engine', 'edge_tts')
        
        return jsonify({
            'success': True,
            'data': {
                'engines': engines,
                'current_engine': current_engine,
                'total_engines': len(engines)
            }
        })
        
    except Exception as e:
        logger.error(f"获取TTS引擎失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取TTS引擎失败: {str(e)}'
        }), 500

@bp.route('/voices/<engine_id>', methods=['GET'])
def get_voices_by_engine(engine_id):
    """根据引擎ID获取配音角色"""
    try:
        if engine_id == 'edge_tts':
            config = load_edge_tts_config()
            if not config:
                return jsonify({
                    'success': False,
                    'message': 'Edge TTS配置未找到'
                }), 404
            
            # 提取Edge TTS语音
            all_voices = []
            edge_tts_voices = config.get('edge_tts_voices', {})
            
            for region_code, region_data in edge_tts_voices.items():
                region_name = region_data.get('name', region_code)
                voices = region_data.get('voices', [])
                
                for voice in voices:
                    voice_info = {
                        'id': voice['name'],
                        'name': voice['name'],
                        'display_name': voice['display_name'],
                        'gender': voice['gender'],
                        'description': voice['description'],
                        'region': region_name,
                        'region_code': region_code,
                        'type': 'voice'
                    }
                    all_voices.append(voice_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'engine_id': engine_id,
                    'engine_name': 'Edge TTS',
                    'voices': all_voices,
                    'default_voice': config.get('default_voice', 'zh-CN-XiaoxiaoNeural'),
                    'total_count': len(all_voices)
                }
            })
            
        elif engine_id == 'fish_tts':
            config = load_fish_tts_config()
            if not config:
                return jsonify({
                    'success': False,
                    'message': 'Fish TTS配置未找到'
                }), 404
            
            # 提取Fish TTS角色
            all_characters = []
            fish_characters = config.get('fish_tts_characters', {})
            
            for gender_type, gender_data in fish_characters.items():
                gender_name = gender_data.get('name', gender_type)
                characters = gender_data.get('characters', [])
                
                for character in characters:
                    character_info = {
                        'id': character['character_id'],
                        'name': character['name'],
                        'display_name': character['display_name'],
                        'gender': gender_type.replace('_voices', '').replace('male', '男性').replace('female', '女性'),
                        'description': character['description'],
                        'style': character['style'],
                        'recommended_use': character['recommended_use'],
                        'gender_type': gender_type,
                        'type': 'character'
                    }
                    all_characters.append(character_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'engine_id': engine_id,
                    'engine_name': 'Fish TTS',
                    'voices': all_characters,
                    'default_voice': config.get('default_character', '雷军'),
                    'total_count': len(all_characters),
                    'api_key_configured': bool(config.get('api_key'))
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的TTS引擎: {engine_id}'
            }), 400
            
    except Exception as e:
        logger.error(f"获取{engine_id}配音角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取{engine_id}配音角色失败: {str(e)}'
        }), 500

@bp.route('/config', methods=['GET'])
def get_current_config():
    """获取当前TTS配置"""
    try:
        app_config = load_app_config()
        if not app_config or 'tts' not in app_config:
            return jsonify({
                'success': False,
                'message': 'TTS配置未找到'
            }), 404
        
        tts_config = app_config['tts']
        
        return jsonify({
            'success': True,
            'data': {
                'current_engine': tts_config.get('preferred_engine', 'edge_tts'),
                'edge_config': {
                    'voice': tts_config.get('edge_voice', 'zh-CN-XiaoxiaoNeural'),
                    'rate': tts_config.get('edge_rate', 'medium'),
                    'pitch': tts_config.get('edge_pitch', 'medium')
                },
                'fish_config': {
                    'character': tts_config.get('fish_character_name', '雷军'),
                    'character_id': tts_config.get('fish_character_id', ''),
                    'api_key_configured': bool(tts_config.get('fish_api_key'))
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取TTS配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取TTS配置失败: {str(e)}'
        }), 500

@bp.route('/config', methods=['POST'])
def update_tts_config():
    """更新TTS配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少配置数据'
            }), 400
        
        # 加载当前应用配置
        app_config = load_app_config()
        if not app_config:
            app_config = {}
        
        if 'tts' not in app_config:
            app_config['tts'] = {}
        
        # 更新TTS配置
        tts_config = app_config['tts']
        
        # 更新引擎选择
        if 'preferred_engine' in data:
            tts_config['preferred_engine'] = data['preferred_engine']
        
        # 更新Edge TTS配置
        if 'edge_config' in data:
            edge_config = data['edge_config']
            if 'voice' in edge_config:
                tts_config['edge_voice'] = edge_config['voice']
            if 'rate' in edge_config:
                tts_config['edge_rate'] = edge_config['rate']
            if 'pitch' in edge_config:
                tts_config['edge_pitch'] = edge_config['pitch']
        
        # 更新Fish TTS配置
        if 'fish_config' in data:
            fish_config = data['fish_config']
            if 'character' in fish_config:
                tts_config['fish_character_name'] = fish_config['character']
            if 'character_id' in fish_config:
                tts_config['fish_character_id'] = fish_config['character_id']
        
        # 保存配置
        app_config['_updated_at'] = request.json.get('_updated_at', '')
        
        config_path = Path(__file__).parent.parent.parent / "config_data" / "app_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(app_config, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'TTS配置更新成功',
            'data': {
                'updated_config': tts_config
            }
        })
        
    except Exception as e:
        logger.error(f"更新TTS配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新TTS配置失败: {str(e)}'
        }), 500

@bp.route('/test', methods=['POST'])
def test_tts():
    """测试TTS配音"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少测试数据'
            }), 400
        
        engine_id = data.get('engine_id')
        voice_id = data.get('voice_id')
        test_text = data.get('text', '这是一个TTS配音测试。')
        
        if not engine_id or not voice_id:
            return jsonify({
                'success': False,
                'message': '缺少引擎ID或语音ID'
            }), 400
        
        # 这里可以调用实际的TTS测试功能
        # 暂时返回成功响应
        return jsonify({
            'success': True,
            'message': 'TTS测试功能开发中',
            'data': {
                'engine_id': engine_id,
                'voice_id': voice_id,
                'text': test_text,
                'estimated_duration': len(test_text) * 0.15  # 估算时长
            }
        })
        
    except Exception as e:
        logger.error(f"TTS测试失败: {e}")
        return jsonify({
            'success': False,
            'message': f'TTS测试失败: {str(e)}'
        }), 500

# 错误处理
@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'TTS API接口不存在'
    }), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'TTS服务器内部错误'
    }), 500
