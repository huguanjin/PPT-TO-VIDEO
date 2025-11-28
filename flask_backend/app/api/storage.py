"""
存储管理 API
管理用户工作目录和历史项目
"""
from flask import Blueprint, jsonify, request, g, send_file
from ..auth.decorators import login_required, optional_login
from ..services.storage_service import get_storage_service
import logging

logger = logging.getLogger(__name__)

storage_bp = Blueprint('storage', __name__, url_prefix='/api/storage')


@storage_bp.route('/workspace', methods=['GET'])
@optional_login
def get_workspace_info():
    """
    获取当前用户的工作空间信息
    
    Returns:
        工作空间信息，包括路径、状态、文件统计
    """
    try:
        user_id = getattr(g, 'user_id', 'anonymous')
        storage = get_storage_service()
        
        info = storage.get_work_dir_info(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                **info
            }
        })
    except Exception as e:
        logger.error(f"获取工作空间信息失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@storage_bp.route('/workspace/init', methods=['POST'])
@optional_login
def init_workspace():
    """
    初始化用户工作空间
    
    Body:
        clean: bool - 是否清空现有内容 (默认 True)
        
    Returns:
        初始化后的工作空间路径
    """
    try:
        user_id = getattr(g, 'user_id', 'anonymous')
        data = request.get_json() or {}
        clean = data.get('clean', True)
        
        storage = get_storage_service()
        work_dir = storage.init_work_dir(user_id, clean=clean)
        
        return jsonify({
            'success': True,
            'message': '工作空间初始化成功',
            'data': {
                'user_id': user_id,
                'path': str(work_dir)
            }
        })
    except Exception as e:
        logger.error(f"初始化工作空间失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@storage_bp.route('/workspace/path', methods=['GET'])
@optional_login
def get_workspace_path():
    """
    获取当前用户的工作目录路径
    用于其他模块获取正确的工作目录
    
    Returns:
        工作目录路径
    """
    try:
        user_id = getattr(g, 'user_id', 'anonymous')
        storage = get_storage_service()
        
        work_dir = storage.get_user_work_dir(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'path': str(work_dir),
                'relative_path': f'output/{user_id}'
            }
        })
    except Exception as e:
        logger.error(f"获取工作目录路径失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@storage_bp.route('/history', methods=['GET'])
@optional_login
def list_history():
    """
    获取用户的历史项目列表
    
    Returns:
        历史项目列表
    """
    try:
        user_id = getattr(g, 'user_id', 'anonymous')
        storage = get_storage_service()
        
        projects = storage.list_user_history(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'projects': projects,
                'total': len(projects)
            }
        })
    except Exception as e:
        logger.error(f"获取历史项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@storage_bp.route('/archive', methods=['POST'])
@optional_login
def archive_project():
    """
    归档当前工作目录的项目
    
    Body:
        project_name: str - 项目名称 (可选)
        
    Returns:
        归档后的项目ID
    """
    try:
        user_id = getattr(g, 'user_id', 'anonymous')
        data = request.get_json() or {}
        project_name = data.get('project_name')
        
        storage = get_storage_service()
        
        # 检查是否有内容需要归档
        if not storage.check_work_dir_busy(user_id):
            return jsonify({
                'success': False,
                'message': '工作目录为空，无需归档'
            }), 400
        
        project_id = storage.archive_project(user_id, project_name)
        
        return jsonify({
            'success': True,
            'message': '项目归档成功',
            'data': {
                'project_id': project_id,
                'project_name': project_name or project_id
            }
        })
    except Exception as e:
        logger.error(f"归档项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@storage_bp.route('/history/<project_id>', methods=['DELETE'])
@optional_login
def delete_history_project(project_id: str):
    """
    删除历史项目
    
    Args:
        project_id: 项目ID
        
    Returns:
        删除结果
    """
    try:
        user_id = getattr(g, 'user_id', 'anonymous')
        storage = get_storage_service()
        
        success = storage.delete_project(user_id, project_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '项目删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '项目不存在'
            }), 404
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@storage_bp.route('/history/<project_id>/video', methods=['GET'])
@optional_login
def get_project_video(project_id: str):
    """
    获取历史项目的视频文件
    
    Args:
        project_id: 项目ID
        
    Returns:
        视频文件
    """
    try:
        user_id = getattr(g, 'user_id', 'anonymous')
        storage = get_storage_service()
        
        video_path = storage.get_project_video_path(user_id, project_id)
        
        if video_path and video_path.exists():
            return send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name=f'{project_id}_video.mp4'
            )
        else:
            return jsonify({
                'success': False,
                'message': '视频文件不存在'
            }), 404
    except Exception as e:
        logger.error(f"获取视频失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@storage_bp.route('/migrate', methods=['POST'])
@login_required
def migrate_anonymous():
    """
    将匿名用户的工作目录迁移到当前登录用户
    用于用户登录后继承之前的匿名工作
    
    Returns:
        迁移结果
    """
    try:
        user_id = g.user_id
        storage = get_storage_service()
        
        success = storage.migrate_anonymous_to_user(user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '匿名工作目录已迁移到您的账户'
            })
        else:
            return jsonify({
                'success': True,
                'message': '没有需要迁移的匿名工作'
            })
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
