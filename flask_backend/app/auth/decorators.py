"""
认证装饰器
提供路由保护功能
"""

from functools import wraps
from flask import request, jsonify, g
from typing import Callable, Optional

from .jwt_handler import decode_token, get_token_from_header
from app.database.mongodb import get_db


def get_current_user() -> Optional[dict]:
    """
    获取当前登录用户
    
    Returns:
        用户信息字典，未登录返回 None
    """
    return getattr(g, 'current_user', None)


def get_current_user_id() -> str:
    """
    获取当前用户ID
    
    Returns:
        用户ID（访客模式已禁用，不再返回 'anonymous'）
    """
    return getattr(g, 'user_id', 'anonymous')


def login_required(f: Callable) -> Callable:
    """
    登录验证装饰器
    需要用户登录才能访问
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取 Token
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                'success': False,
                'message': '未提供认证令牌',
                'error': 'UNAUTHORIZED'
            }), 401
        
        # 解码 Token
        payload = decode_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'message': '令牌无效或已过期',
                'error': 'INVALID_TOKEN'
            }), 401
        
        # 获取用户信息
        user_id = payload.get('user_id')
        db = get_db()
        
        from bson import ObjectId
        try:
            user = db.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            user = None
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'error': 'USER_NOT_FOUND'
            }), 401
        
        # 存储用户信息到请求上下文
        g.current_user = user
        g.user_id = user_id
        g.username = payload.get('username')
        g.role = payload.get('role')
        
        # 兼容格式：g.user 存储 payload 信息（便于 API 使用）
        g.user = {
            'user_id': user_id,
            'username': payload.get('username'),
            'role': payload.get('role')
        }
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f: Callable) -> Callable:
    """
    管理员验证装饰器
    需要管理员权限才能访问
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取 Token
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                'success': False,
                'message': '未提供认证令牌',
                'error': 'UNAUTHORIZED'
            }), 401
        
        # 解码 Token
        payload = decode_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'message': '令牌无效或已过期',
                'error': 'INVALID_TOKEN'
            }), 401
        
        # 检查角色
        role = payload.get('role')
        if role != 'admin':
            return jsonify({
                'success': False,
                'message': '需要管理员权限',
                'error': 'FORBIDDEN'
            }), 403
        
        # 获取用户信息
        user_id = payload.get('user_id')
        db = get_db()
        
        from bson import ObjectId
        try:
            user = db.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            user = None
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'error': 'USER_NOT_FOUND'
            }), 401
        
        # 存储用户信息到请求上下文
        g.current_user = user
        g.user_id = user_id
        g.username = payload.get('username')
        g.role = role
        
        # 兼容格式：g.user 存储 payload 信息
        g.user = {
            'user_id': user_id,
            'username': payload.get('username'),
            'role': role
        }
        
        return f(*args, **kwargs)
    
    return decorated


def optional_login(f: Callable) -> Callable:
    """
    可选登录装饰器（已禁用访客模式）
    现在强制要求登录，不再支持匿名访问
    
    注意：如需恢复访客模式，请将下方 REQUIRE_LOGIN 设置为 False
    """
    # 是否强制要求登录（设置为 False 可恢复访客模式）
    REQUIRE_LOGIN = True
    
    @wraps(f)
    def decorated(*args, **kwargs):
        # 尝试获取 Token
        token = get_token_from_header()
        
        if not token:
            if REQUIRE_LOGIN:
                return jsonify({
                    'success': False,
                    'message': '未提供认证令牌，请先登录',
                    'error': 'UNAUTHORIZED'
                }), 401
            else:
                # 访客模式（已禁用）
                g.current_user = None
                g.user_id = 'anonymous'
                g.username = 'anonymous'
                g.role = 'anonymous'
                g.user = {
                    'user_id': 'anonymous',
                    'username': 'anonymous',
                    'role': 'anonymous'
                }
                return f(*args, **kwargs)
        
        # 解码 Token
        payload = decode_token(token)
        
        if not payload:
            return jsonify({
                'success': False,
                'message': '令牌无效或已过期，请重新登录',
                'error': 'INVALID_TOKEN'
            }), 401
        
        # 获取用户信息
        user_id = payload.get('user_id')
        db = get_db()
        
        from bson import ObjectId
        try:
            user = db.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            user = None
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'error': 'USER_NOT_FOUND'
            }), 401
        
        # 存储用户信息到请求上下文
        g.current_user = user
        g.user_id = user_id
        g.username = payload.get('username')
        g.role = payload.get('role')
        g.user = {
            'user_id': user_id,
            'username': payload.get('username'),
            'role': payload.get('role')
        }
        
        return f(*args, **kwargs)
    
    return decorated
