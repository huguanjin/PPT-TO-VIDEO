"""
认证 API
提供用户登录、登出、个人信息管理等接口
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from app.auth import login_required, create_access_token, get_current_user
from app.models.user import get_user_service
from app.database.init_db import verify_password

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    Request Body:
        {
            "username": "admin",
            "password": "your_password"
        }
        
    Response:
        {
            "success": true,
            "message": "登录成功",
            "data": {
                "token": "jwt_token_here",
                "user": {
                    "id": "...",
                    "username": "admin",
                    "role": "admin"
                }
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 验证用户
        user_service = get_user_service()
        user = user_service.authenticate(username, password)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
        
        # 生成 Token
        token = create_access_token(
            user_id=str(user._id),
            username=user.username,
            role=user.role
        )
        
        # 🔧 新用户初始化：确保工作目录和配置已创建
        from app.services.user_init_service import get_user_init_service
        init_service = get_user_init_service()
        init_result = init_service.ensure_user_initialized(
            user_id=str(user._id),
            username=user.username
        )
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict(),
                'init_status': init_result  # 返回初始化状态供前端了解
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    用户登出
    
    注意: JWT 是无状态的，登出只是前端清除 Token
    如需真正失效，需要实现 Token 黑名单机制
    """
    return jsonify({
        'success': True,
        'message': '登出成功'
    })


@bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    获取当前用户信息
    """
    user = get_current_user()
    
    if not user:
        return jsonify({
            'success': False,
            'message': '用户不存在'
        }), 404
    
    return jsonify({
        'success': True,
        'data': {
            'id': str(user.get('_id')),
            'username': user.get('username'),
            'role': user.get('role'),
            'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
            'last_login': user.get('last_login').isoformat() if user.get('last_login') else None
        }
    })


@bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    """
    修改密码
    
    Request Body:
        {
            "old_password": "current_password",
            "new_password": "new_password"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'message': '旧密码和新密码不能为空'
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': '新密码长度至少6位'
            }), 400
        
        # 验证旧密码
        user = get_current_user()
        if not verify_password(old_password, user.get('password', '')):
            return jsonify({
                'success': False,
                'message': '旧密码错误'
            }), 400
        
        # 更新密码
        user_service = get_user_service()
        success = user_service.update_password(g.user_id, new_password)
        
        if success:
            return jsonify({
                'success': True,
                'message': '密码修改成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '密码修改失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'密码修改失败: {str(e)}'
        }), 500


@bp.route('/verify', methods=['GET'])
@login_required
def verify_token():
    """
    验证 Token 是否有效
    用于前端检查登录状态
    """
    return jsonify({
        'success': True,
        'message': 'Token 有效',
        'data': {
            'user_id': g.user_id,
            'username': g.username,
            'role': g.role
        }
    })
