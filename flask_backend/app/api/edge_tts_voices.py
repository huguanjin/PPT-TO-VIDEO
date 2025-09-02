#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Edge TTS 配音角色 API
提供配音角色列表和配置选项
"""

from flask import Blueprint, jsonify, request
import json
from pathlib import Path
import logging

# 创建蓝图
bp = Blueprint('edge_tts_voices', __name__, url_prefix='/api/edge-tts')

# 配置日志
logger = logging.getLogger(__name__)

def load_edge_tts_voices():
    """加载Edge TTS配音角色配置"""
    try:
        # 修复路径：相对于flask_backend目录
        config_path = Path(__file__).parent.parent.parent / "config_data" / "edge_tts_voices.json"
        
        if not config_path.exists():
            logger.error(f"Edge TTS配音角色配置文件不存在: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"加载Edge TTS配音角色配置失败: {e}")
        return None

@bp.route('/voices', methods=['GET'])
def get_voices():
    """获取所有可用的配音角色"""
    try:
        config = load_edge_tts_voices()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载配音角色配置失败'
            }), 500
        
        # 提取所有语言区域的配音角色
        all_voices = []
        edge_tts_voices = config.get('edge_tts_voices', {})
        
        for region_code, region_data in edge_tts_voices.items():
            region_name = region_data.get('name', region_code)
            voices = region_data.get('voices', [])
            
            for voice in voices:
                voice_info = {
                    'name': voice['name'],
                    'display_name': voice['display_name'],
                    'gender': voice['gender'],
                    'description': voice['description'],
                    'region': region_name,
                    'region_code': region_code
                }
                all_voices.append(voice_info)
        
        return jsonify({
            'success': True,
            'data': {
                'voices': all_voices,
                'default_voice': config.get('default_voice', 'zh-CN-XiaoxiaoNeural'),
                'total_count': len(all_voices)
            }
        })
        
    except Exception as e:
        logger.error(f"获取配音角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取配音角色失败: {str(e)}'
        }), 500

@bp.route('/voices/grouped', methods=['GET'])
def get_voices_grouped():
    """获取按语言区域分组的配音角色"""
    try:
        config = load_edge_tts_voices()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载配音角色配置失败'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'grouped_voices': config.get('edge_tts_voices', {}),
                'default_voice': config.get('default_voice', 'zh-CN-XiaoxiaoNeural')
            }
        })
        
    except Exception as e:
        logger.error(f"获取分组配音角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取分组配音角色失败: {str(e)}'
        }), 500

@bp.route('/voice-settings', methods=['GET'])
def get_voice_settings():
    """获取语音设置选项（速率、音调等）"""
    try:
        config = load_edge_tts_voices()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载配音角色配置失败'
            }), 500
        
        return jsonify({
            'success': True,
            'data': config.get('voice_settings', {})
        })
        
    except Exception as e:
        logger.error(f"获取语音设置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取语音设置失败: {str(e)}'
        }), 500

@bp.route('/voice/<voice_name>', methods=['GET'])
def get_voice_info(voice_name):
    """获取特定配音角色的详细信息"""
    try:
        config = load_edge_tts_voices()
        if not config:
            return jsonify({
                'success': False,
                'message': '加载配音角色配置失败'
            }), 500
        
        # 查找指定的配音角色
        edge_tts_voices = config.get('edge_tts_voices', {})
        
        for region_code, region_data in edge_tts_voices.items():
            voices = region_data.get('voices', [])
            
            for voice in voices:
                if voice['name'] == voice_name:
                    voice_info = {
                        'name': voice['name'],
                        'display_name': voice['display_name'],
                        'gender': voice['gender'],
                        'description': voice['description'],
                        'region': region_data.get('name', region_code),
                        'region_code': region_code
                    }
                    return jsonify({
                        'success': True,
                        'data': voice_info
                    })
        
        return jsonify({
            'success': False,
            'message': f'未找到配音角色: {voice_name}'
        }), 404
        
    except Exception as e:
        logger.error(f"获取配音角色信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取配音角色信息失败: {str(e)}'
        }), 500

@bp.route('/test-voice', methods=['POST'])
def test_voice():
    """测试指定配音角色"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        voice_name = data.get('voice_name')
        test_text = data.get('text', '这是一个语音测试。')
        rate = data.get('rate', 'medium')
        pitch = data.get('pitch', 'medium')
        
        if not voice_name:
            return jsonify({
                'success': False,
                'message': '缺少配音角色名称'
            }), 400
        
        # 这里可以调用实际的TTS测试功能
        # 暂时返回成功响应
        return jsonify({
            'success': True,
            'message': '语音测试功能开发中',
            'data': {
                'voice_name': voice_name,
                'text': test_text,
                'rate': rate,
                'pitch': pitch
            }
        })
        
    except Exception as e:
        logger.error(f"测试配音角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'测试配音角色失败: {str(e)}'
        }), 500

# 错误处理
@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500
