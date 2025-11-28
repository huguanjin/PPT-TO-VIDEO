"""
用户配置 API
提供用户配置的读取和更新接口
"""

from flask import Blueprint, request, jsonify, g

from app.auth import login_required, admin_required, optional_login
from app.services.config_service import get_config_service

bp = Blueprint('user_config', __name__, url_prefix='/api/user-config')


@bp.route('', methods=['GET'])
@optional_login
def get_config():
    """
    获取当前用户的完整配置
    
    Response:
        {
            "success": true,
            "data": {
                "ai": {...},
                "tts": {...},
                "video": {...},
                "subtitle": {...},
                "smart_subtitle": {...},
                "netflix_v2": {...},
                "advanced_features": {...}
            }
        }
    """
    try:
        user_id = g.user.get('user_id', 'anonymous')
        
        config_service = get_config_service()
        config = config_service.get_user_config(user_id)
        
        return jsonify({
            'success': True,
            'data': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500


@bp.route('/<section>', methods=['GET'])
@optional_login
def get_config_section(section):
    """
    获取配置的某个部分
    
    Path Parameters:
        section: ai | tts | video | subtitle | smart_subtitle | netflix_v2 | advanced_features
        
    Response:
        {
            "success": true,
            "data": {...}
        }
    """
    try:
        user_id = g.user.get('user_id', 'anonymous')
        
        valid_sections = ['ai', 'tts', 'video', 'subtitle', 'smart_subtitle', 
                         'netflix_v2', 'advanced_features']
        
        if section not in valid_sections:
            return jsonify({
                'success': False,
                'message': f'无效的配置部分: {section}，有效值: {valid_sections}'
            }), 400
        
        config_service = get_config_service()
        config = config_service.get_user_config_section(user_id, section)
        
        return jsonify({
            'success': True,
            'data': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500


@bp.route('', methods=['PUT'])
@login_required
def update_config():
    """
    更新用户配置（整体更新）
    
    Request Body:
        {
            "ai": {...},
            "tts": {...},
            ...
        }
        
    Response:
        {
            "success": true,
            "message": "配置已更新"
        }
    """
    try:
        user_id = g.user.get('user_id')
        data = request.get_json() or {}
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        config_service = get_config_service()
        
        if config_service.update_user_config(user_id, data):
            return jsonify({
                'success': True,
                'message': '配置已更新'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新配置失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新配置失败: {str(e)}'
        }), 500


@bp.route('/<section>', methods=['PUT'])
@login_required
def update_config_section(section):
    """
    更新配置的某个部分（深度合并）
    
    Path Parameters:
        section: ai | tts | video | subtitle | smart_subtitle | netflix_v2 | advanced_features
        
    Request Body:
        {
            "key1": "value1",
            "key2": "value2"
        }
        
    Response:
        {
            "success": true,
            "message": "配置已更新"
        }
    """
    try:
        user_id = g.user.get('user_id')
        data = request.get_json() or {}
        
        valid_sections = ['ai', 'tts', 'video', 'subtitle', 'smart_subtitle', 
                         'netflix_v2', 'advanced_features']
        
        if section not in valid_sections:
            return jsonify({
                'success': False,
                'message': f'无效的配置部分: {section}'
            }), 400
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        config_service = get_config_service()
        
        if config_service.update_user_config_section(user_id, section, data):
            return jsonify({
                'success': True,
                'message': f'{section} 配置已更新'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新配置失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新配置失败: {str(e)}'
        }), 500


@bp.route('/reset', methods=['POST'])
@login_required
def reset_config():
    """
    重置用户配置为默认值
    
    Response:
        {
            "success": true,
            "message": "配置已重置为默认值"
        }
    """
    try:
        user_id = g.user.get('user_id')
        
        config_service = get_config_service()
        
        if config_service.reset_user_config(user_id):
            return jsonify({
                'success': True,
                'message': '配置已重置为默认值'
            })
        else:
            return jsonify({
                'success': False,
                'message': '重置配置失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'重置配置失败: {str(e)}'
        }), 500


# ============================================================
# 系统配置管理 API（仅管理员）
# ============================================================

@bp.route('/system/settings', methods=['GET'])
@admin_required
def get_system_settings():
    """
    获取系统设置（仅管理员）
    
    Response:
        {
            "success": true,
            "data": {
                "allow_registration": false,
                "max_video_duration": 3600,
                "max_slides_count": 100,
                "maintenance_mode": false
            }
        }
    """
    try:
        config_service = get_config_service()
        settings = config_service.get_system_settings()
        
        return jsonify({
            'success': True,
            'data': settings
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统设置失败: {str(e)}'
        }), 500


@bp.route('/system/settings', methods=['PUT'])
@admin_required
def update_system_settings():
    """
    更新系统设置（仅管理员）
    
    Request Body:
        {
            "allow_registration": true,
            "max_video_duration": 7200
        }
    """
    try:
        user_id = g.user.get('user_id')
        data = request.get_json() or {}
        
        config_service = get_config_service()
        
        if config_service.update_system_settings(data, user_id):
            return jsonify({
                'success': True,
                'message': '系统设置已更新'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新系统设置失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新系统设置失败: {str(e)}'
        }), 500


@bp.route('/system/default', methods=['GET'])
@admin_required
def get_default_config():
    """
    获取默认用户配置模板（仅管理员）
    """
    try:
        config_service = get_config_service()
        config = config_service.get_default_user_config()
        
        return jsonify({
            'success': True,
            'data': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取默认配置失败: {str(e)}'
        }), 500


@bp.route('/system/default', methods=['PUT'])
@admin_required
def update_default_config():
    """
    更新默认用户配置模板（仅管理员）
    
    注意：这会影响所有新用户的默认配置
    """
    try:
        user_id = g.user.get('user_id')
        data = request.get_json() or {}
        
        config_service = get_config_service()
        
        if config_service.update_default_user_config(data, user_id):
            return jsonify({
                'success': True,
                'message': '默认配置模板已更新'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新默认配置失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新默认配置失败: {str(e)}'
        }), 500
