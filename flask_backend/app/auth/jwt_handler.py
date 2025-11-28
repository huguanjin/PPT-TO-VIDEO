"""
JWT Token 处理器
实现 Token 的生成、验证和解析
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import request

logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ppt-to-video-jwt-secret-key-2025')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 默认1小时


def create_access_token(user_id: str, username: str, role: str, 
                        expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        expires_delta: 过期时间增量，默认使用配置值
        
    Returns:
        JWT Token 字符串
    """
    if expires_delta is None:
        expires_delta = timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
    
    now = datetime.utcnow()
    expire = now + expires_delta
    
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'iat': now,  # issued at
        'exp': expire  # expiration
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证 Token
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        解码后的 payload，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token 无效: {e}")
        return None


def get_token_from_header() -> Optional[str]:
    """
    从请求头获取 Token
    
    支持格式:
    - Authorization: Bearer <token>
    - X-Access-Token: <token>
    
    Returns:
        Token 字符串，未找到返回 None
    """
    # 尝试从 Authorization header 获取
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    
    # 尝试从 X-Access-Token header 获取
    token = request.headers.get('X-Access-Token')
    if token:
        return token
    
    # 尝试从查询参数获取（用于某些特殊场景，如文件下载）
    token = request.args.get('token')
    if token:
        return token
    
    return None


def verify_token_and_get_payload() -> Optional[Dict[str, Any]]:
    """
    从请求中获取并验证 Token
    
    Returns:
        验证成功返回 payload，失败返回 None
    """
    token = get_token_from_header()
    if not token:
        return None
    
    return decode_token(token)
