"""
AI配置测试API
用于测试各种AI服务的连接状态
"""

from flask import Blueprint, request, jsonify
import requests
import json
import time
from typing import Dict, Any
import logging

# 创建蓝图
ai_test_bp = Blueprint('ai_test', __name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """测试OpenAI API连接"""
    try:
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 使用最小的测试请求
        test_data = {
            'model': config['model'],
            'messages': [{'role': 'user', 'content': 'test'}],
            'max_tokens': 1,
            'temperature': 0
        }
        
        # 构建完整的API URL
        base_url = config['base_url'].rstrip('/')
        if not base_url.endswith('/v1'):
            base_url += '/v1'
        
        url = f"{base_url}/chat/completions"
        
        response = requests.post(
            url,
            headers=headers,
            json=test_data,
            timeout=config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': f'OpenAI API连接成功！模型: {config["model"]}',
                'details': {
                    'status_code': response.status_code,
                    'model': config['model'],
                    'endpoint': url
                }
            }
        else:
            error_msg = f'HTTP {response.status_code}'
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f': {error_data["error"].get("message", "未知错误")}'
            except:
                error_msg += f': {response.text[:200]}'
            
            return {
                'success': False,
                'message': f'OpenAI API连接失败 - {error_msg}',
                'details': {
                    'status_code': response.status_code,
                    'error': error_msg
                }
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'OpenAI API连接超时，请检查网络或增加超时时间',
            'details': {'error': 'timeout'}
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': '无法连接到OpenAI API，请检查API地址和网络连接',
            'details': {'error': 'connection_error'}
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'OpenAI API测试失败: {str(e)}',
            'details': {'error': str(e)}
        }

def test_anthropic_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """测试Anthropic Claude API连接"""
    try:
        headers = {
            'x-api-key': config['api_key'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        # 使用最小的测试请求
        test_data = {
            'model': config['model'],
            'messages': [{'role': 'user', 'content': 'test'}],
            'max_tokens': 1
        }
        
        # 构建完整的API URL
        base_url = config['base_url'].rstrip('/')
        url = f"{base_url}/v1/messages"
        
        response = requests.post(
            url,
            headers=headers,
            json=test_data,
            timeout=config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': f'Anthropic API连接成功！模型: {config["model"]}',
                'details': {
                    'status_code': response.status_code,
                    'model': config['model'],
                    'endpoint': url
                }
            }
        else:
            error_msg = f'HTTP {response.status_code}'
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f': {error_data["error"].get("message", "未知错误")}'
            except:
                error_msg += f': {response.text[:200]}'
            
            return {
                'success': False,
                'message': f'Anthropic API连接失败 - {error_msg}',
                'details': {
                    'status_code': response.status_code,
                    'error': error_msg
                }
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Anthropic API连接超时，请检查网络或增加超时时间',
            'details': {'error': 'timeout'}
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': '无法连接到Anthropic API，请检查API地址和网络连接',
            'details': {'error': 'connection_error'}
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Anthropic API测试失败: {str(e)}',
            'details': {'error': str(e)}
        }

def test_custom_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """测试自定义API连接"""
    try:
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 使用最小的测试请求
        test_data = {
            'model': config['model'],
            'messages': [{'role': 'user', 'content': 'test'}],
            'max_tokens': 1,
            'temperature': 0
        }
        
        # 构建完整的API URL
        base_url = config['base_url'].rstrip('/')
        
        # 尝试多种常见的端点路径
        possible_endpoints = [
            f"{base_url}/chat/completions",
            f"{base_url}/v1/chat/completions",
            f"{base_url}/api/chat/completions",
            f"{base_url}/completions"
        ]
        
        last_error = None
        for url in possible_endpoints:
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=test_data,
                    timeout=config.get('timeout', 30)
                )
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'message': f'自定义API连接成功！模型: {config["model"]}，端点: {url}',
                        'details': {
                            'status_code': response.status_code,
                            'model': config['model'],
                            'endpoint': url
                        }
                    }
                elif response.status_code in [400, 401, 403, 404]:
                    # 这些状态码表示端点存在但请求有问题，继续尝试其他端点
                    last_error = {
                        'status_code': response.status_code,
                        'url': url,
                        'response': response.text[:200]
                    }
                    continue
            except requests.exceptions.ConnectionError:
                # 连接错误，尝试下一个端点
                continue
        
        # 如果所有端点都失败了
        if last_error:
            return {
                'success': False,
                'message': f'自定义API连接失败 - HTTP {last_error["status_code"]}',
                'details': last_error
            }
        else:
            return {
                'success': False,
                'message': '无法连接到自定义API，请检查API地址和网络连接',
                'details': {'error': 'connection_error', 'tried_endpoints': possible_endpoints}
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': '自定义API连接超时，请检查网络或增加超时时间',
            'details': {'error': 'timeout'}
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'自定义API测试失败: {str(e)}',
            'details': {'error': str(e)}
        }

@ai_test_bp.route('/test', methods=['POST'])
def test_ai_connection():
    """测试AI服务连接"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        service = data.get('service')
        config = data.get('config')
        
        if not service or not config:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: service 和 config'
            }), 400
        
        # 验证必填字段
        required_fields = ['api_key', 'base_url', 'model']
        for field in required_fields:
            if not config.get(field):
                return jsonify({
                    'success': False,
                    'message': f'配置字段 {field} 不能为空'
                }), 400
        
        logger.info(f"开始测试 {service} API连接")
        start_time = time.time()
        
        # 根据服务类型调用对应的测试函数
        if service == 'openai':
            result = test_openai_connection(config)
        elif service == 'anthropic':
            result = test_anthropic_connection(config)
        elif service == 'custom':
            result = test_custom_connection(config)
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的服务类型: {service}'
            }), 400
        
        # 添加测试耗时
        result['details'] = result.get('details', {})
        result['details']['test_duration'] = round(time.time() - start_time, 2)
        
        logger.info(f"{service} API测试完成，结果: {result['success']}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI连接测试异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'测试过程中发生异常: {str(e)}',
            'details': {'error': str(e)}
        }), 500

@ai_test_bp.route('/models/<service>', methods=['GET'])
def get_available_models(service):
    """获取指定服务的可用模型列表"""
    models = {
        'openai': [
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k',
            'gpt-4',
            'gpt-4-32k',
            'gpt-4-turbo-preview',
            'gpt-4-vision-preview'
        ],
        'anthropic': [
            'claude-3-haiku-20240307',
            'claude-3-sonnet-20240229',
            'claude-3-opus-20240229',
            'claude-2.1',
            'claude-2.0'
        ],
        'custom': [
            # 自定义服务的常见模型
            'gpt-3.5-turbo',
            'gpt-4',
            'claude-3-sonnet',
            'llama-2-70b',
            'llama-2-13b',
            'llama-2-7b'
        ]
    }
    
    if service not in models:
        return jsonify({
            'success': False,
            'message': f'不支持的服务类型: {service}'
        }), 400
    
    return jsonify({
        'success': True,
        'models': models[service]
    })
