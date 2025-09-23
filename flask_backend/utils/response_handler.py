"""
API响应处理工具
提供统一的API响应格式
"""
from typing import Any, Dict, Optional
from flask import jsonify, Response

def success_response(data: Any = None, message: str = "Success") -> Response:
    """成功响应"""
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response)

def error_response(message: str, status_code: int = 400, error_code: Optional[str] = None) -> tuple[Response, int]:
    """错误响应"""
    response = {
        'success': False,
        'message': message
    }
    
    if error_code:
        response['error_code'] = error_code
    
    return jsonify(response), status_code

def paginated_response(data: list, page: int = 1, per_page: int = 10, 
                      total: Optional[int] = None, message: str = "Success") -> Response:
    """分页响应"""
    if total is None:
        total = len(data)
    
    return jsonify({
        'success': True,
        'message': message,
        'data': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })