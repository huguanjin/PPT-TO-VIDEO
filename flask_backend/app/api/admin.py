"""
管理员 API
提供用户管理功能（仅管理员可用）
"""

from flask import Blueprint, request, jsonify, g

from app.auth import admin_required
from app.models.user import get_user_service

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """
    获取用户列表
    
    Query Parameters:
        - page: 页码，默认1
        - per_page: 每页数量，默认20
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 限制每页数量
        per_page = min(per_page, 100)
        skip = (page - 1) * per_page
        
        user_service = get_user_service()
        users = user_service.list_users(skip=skip, limit=per_page)
        total = user_service.count_users()
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """
    创建用户
    
    Request Body:
        {
            "username": "newuser",
            "password": "password123",
            "role": "user"  // 可选，默认 "user"
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
        role = data.get('role', 'user')
        
        # 验证输入
        if not username:
            return jsonify({
                'success': False,
                'message': '用户名不能为空'
            }), 400
        
        if len(username) < 3 or len(username) > 32:
            return jsonify({
                'success': False,
                'message': '用户名长度应在3-32个字符之间'
            }), 400
        
        if not password or len(password) < 6:
            return jsonify({
                'success': False,
                'message': '密码长度至少6位'
            }), 400
        
        if role not in ['admin', 'user']:
            return jsonify({
                'success': False,
                'message': '角色必须是 admin 或 user'
            }), 400
        
        # 创建用户
        user_service = get_user_service()
        user = user_service.create_user(username, password, role)
        
        if user:
            return jsonify({
                'success': True,
                'message': '用户创建成功',
                'data': user.to_dict()
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建用户失败: {str(e)}'
        }), 500


@bp.route('/users/<user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """
    获取指定用户信息
    """
    try:
        user_service = get_user_service()
        user = user_service.get_by_id(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'data': user.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户失败: {str(e)}'
        }), 500


@bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    删除用户
    
    注意: 不能删除 admin 用户
    """
    try:
        # 不能删除自己
        if user_id == g.user_id:
            return jsonify({
                'success': False,
                'message': '不能删除自己的账户'
            }), 400
        
        user_service = get_user_service()
        
        # 检查用户是否存在
        user = user_service.get_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 不能删除 admin
        if user.username == 'admin':
            return jsonify({
                'success': False,
                'message': '不能删除管理员账户'
            }), 400
        
        # 删除用户
        success = user_service.delete_user(user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '用户删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        }), 500


@bp.route('/users/<user_id>/password', methods=['PUT'])
@admin_required
def reset_user_password(user_id):
    """
    重置用户密码（管理员功能）
    
    Request Body:
        {
            "new_password": "new_password123"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
        
        new_password = data.get('new_password', '')
        
        if not new_password or len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': '新密码长度至少6位'
            }), 400
        
        user_service = get_user_service()
        
        # 检查用户是否存在
        user = user_service.get_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 更新密码
        success = user_service.update_password(user_id, new_password)
        
        if success:
            return jsonify({
                'success': True,
                'message': '密码重置成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '密码重置失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'密码重置失败: {str(e)}'
        }), 500
