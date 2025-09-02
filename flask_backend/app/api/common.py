"""
通用API接口
健康检查、系统信息等
"""
from flask import Blueprint, jsonify, current_app
from datetime import datetime
import sys
from pathlib import Path

bp = Blueprint('common', __name__)

@bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'PPT转视频工具 Flask API',
        'version': '1.0.0'
    })

@bp.route('/info', methods=['GET'])
def system_info():
    """系统信息"""
    return jsonify({
        'success': True,
        'data': {
            'service_name': 'PPT转视频工具',
            'version': '1.0.0',
            'python_version': sys.version,
            'debug_mode': current_app.debug,
            'base_dir': str(current_app.config.get('BASE_DIR', '')),
            'endpoints': {
                'health': '/health',
                'info': '/info',
                'pptist_import': '/api/pptist/import',
                'workflow_start': '/api/workflow/start',
                'project_list': '/api/project/list'
            }
        }
    })

@bp.route('/docs', methods=['GET'])
def api_docs():
    """API文档"""
    return jsonify({
        'success': True,
        'data': {
            'title': 'PPT转视频工具 API 文档',
            'description': '提供PPT转视频的完整工作流API服务',
            'version': '1.0.0',
            'api_groups': {
                'pptist': {
                    'description': 'PPTist导入相关接口',
                    'endpoints': [
                        'POST /api/pptist/import - 导入PPTist数据',
                        'GET /api/pptist/status/<task_id> - 获取导入状态',
                        'GET /api/pptist/projects - 获取项目列表'
                    ]
                },
                'workflow': {
                    'description': '工作流处理接口',
                    'endpoints': [
                        'POST /api/workflow/start - 启动视频生成工作流',
                        'GET /api/workflow/status/<task_id> - 获取处理状态',
                        'GET /api/workflow/result/<task_id> - 获取处理结果'
                    ]
                },
                'project': {
                    'description': '项目管理接口',
                    'endpoints': [
                        'GET /api/project/list - 获取项目列表',
                        'GET /api/project/<project_name> - 获取项目详情',
                        'DELETE /api/project/<project_name> - 删除项目'
                    ]
                }
            }
        }
    })
