"""
任务管理 API
提供任务的创建、查询、更新、删除等接口
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from app.auth import login_required, admin_required, optional_login
from app.models.task import (
    get_task_service, TaskStatus, StepStatus
)

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@bp.route('', methods=['GET'])
@login_required
def list_tasks():
    """
    获取当前用户的任务列表
    
    Query Parameters:
        status: 可选，按状态筛选 (pending|running|completed|failed|cancelled)
        skip: 跳过数量，默认 0
        limit: 返回数量，默认 20，最大 100
        
    Response:
        {
            "success": true,
            "data": {
                "tasks": [...],
                "total": 10,
                "skip": 0,
                "limit": 20
            }
        }
    """
    try:
        user_id = g.user['user_id']
        
        status = request.args.get('status')
        skip = int(request.args.get('skip', 0))
        limit = min(int(request.args.get('limit', 20)), 100)
        
        task_service = get_task_service()
        tasks = task_service.get_user_tasks(user_id, status=status, skip=skip, limit=limit)
        total = task_service.count_user_tasks(user_id, status=status)
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': [t.to_dict() for t in tasks],
                'total': total,
                'skip': skip,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取任务列表失败: {str(e)}'
        }), 500


@bp.route('/active', methods=['GET'])
@login_required
def get_active_task():
    """
    获取当前用户的活动任务（正在执行的任务）
    
    Response:
        {
            "success": true,
            "data": {
                "task": {...} or null
            }
        }
    """
    try:
        user_id = g.user['user_id']
        
        task_service = get_task_service()
        task = task_service.get_user_active_task(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'task': task.to_dict() if task else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取活动任务失败: {str(e)}'
        }), 500


@bp.route('', methods=['POST'])
@login_required
def create_task():
    """
    创建新任务
    
    Request Body:
        {
            "project_name": "我的演示文稿",
            "work_dir": "output/xxx"  // 可选
        }
        
    Response:
        {
            "success": true,
            "message": "任务创建成功",
            "data": {
                "task": {...}
            }
        }
    """
    try:
        user_id = g.user['user_id']
        data = request.get_json() or {}
        
        project_name = data.get('project_name', '').strip()
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称不能为空'
            }), 400
        
        work_dir = data.get('work_dir')
        
        task_service = get_task_service()
        
        # 检查是否已有活动任务
        active_task = task_service.get_user_active_task(user_id)
        if active_task:
            return jsonify({
                'success': False,
                'message': '您已有一个正在执行的任务，请等待完成或取消后再创建新任务',
                'data': {
                    'active_task': active_task.to_dict()
                }
            }), 409  # Conflict
        
        task = task_service.create_task(user_id, project_name, work_dir)
        
        if task:
            return jsonify({
                'success': True,
                'message': '任务创建成功',
                'data': {
                    'task': task.to_dict()
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '任务创建失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建任务失败: {str(e)}'
        }), 500


@bp.route('/<task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """
    获取任务详情
    
    Response:
        {
            "success": true,
            "data": {
                "task": {...}
            }
        }
    """
    try:
        user_id = g.user['user_id']
        
        task_service = get_task_service()
        task = task_service.get_by_id(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        # 检查权限（只能查看自己的任务，除非是管理员）
        if str(task.user_id) != user_id and g.user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': '无权访问此任务'
            }), 403
        
        return jsonify({
            'success': True,
            'data': {
                'task': task.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取任务详情失败: {str(e)}'
        }), 500


@bp.route('/<task_id>/start', methods=['POST'])
@login_required
def start_task(task_id):
    """
    启动任务
    
    Response:
        {
            "success": true,
            "message": "任务已启动"
        }
    """
    try:
        user_id = g.user['user_id']
        
        task_service = get_task_service()
        task = task_service.get_by_id(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        if str(task.user_id) != user_id:
            return jsonify({
                'success': False,
                'message': '无权操作此任务'
            }), 403
        
        if task.status != TaskStatus.PENDING.value:
            return jsonify({
                'success': False,
                'message': f'任务状态为 {task.status}，无法启动'
            }), 400
        
        if task_service.start_task(task_id):
            return jsonify({
                'success': True,
                'message': '任务已启动'
            })
        else:
            return jsonify({
                'success': False,
                'message': '启动任务失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动任务失败: {str(e)}'
        }), 500


@bp.route('/<task_id>/progress', methods=['PUT'])
@login_required
def update_progress(task_id):
    """
    更新任务步骤进度
    
    Request Body:
        {
            "step_name": "step02_tts_generation",
            "status": "running",  // pending|running|completed|failed|skipped
            "progress": 50,
            "message": "正在生成第3/5个音频..."
        }
        
    Response:
        {
            "success": true,
            "message": "进度已更新"
        }
    """
    try:
        user_id = g.user['user_id']
        data = request.get_json() or {}
        
        step_name = data.get('step_name')
        status = data.get('status')
        progress = data.get('progress', 0)
        message = data.get('message', '')
        
        if not step_name or not status:
            return jsonify({
                'success': False,
                'message': '缺少必要参数 step_name 和 status'
            }), 400
        
        task_service = get_task_service()
        task = task_service.get_by_id(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        if str(task.user_id) != user_id:
            return jsonify({
                'success': False,
                'message': '无权操作此任务'
            }), 403
        
        if task_service.update_step_progress(task_id, step_name, status, progress, message):
            return jsonify({
                'success': True,
                'message': '进度已更新'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新进度失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新进度失败: {str(e)}'
        }), 500


@bp.route('/<task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """
    完成任务
    """
    try:
        user_id = g.user['user_id']
        
        task_service = get_task_service()
        task = task_service.get_by_id(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        if str(task.user_id) != user_id:
            return jsonify({
                'success': False,
                'message': '无权操作此任务'
            }), 403
        
        if task_service.complete_task(task_id):
            return jsonify({
                'success': True,
                'message': '任务已完成'
            })
        else:
            return jsonify({
                'success': False,
                'message': '完成任务失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'完成任务失败: {str(e)}'
        }), 500


@bp.route('/<task_id>/fail', methods=['POST'])
@login_required
def fail_task(task_id):
    """
    标记任务失败
    
    Request Body:
        {
            "error_message": "错误描述"
        }
    """
    try:
        user_id = g.user['user_id']
        data = request.get_json() or {}
        
        error_message = data.get('error_message', '未知错误')
        
        task_service = get_task_service()
        task = task_service.get_by_id(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        if str(task.user_id) != user_id:
            return jsonify({
                'success': False,
                'message': '无权操作此任务'
            }), 403
        
        if task_service.fail_task(task_id, error_message):
            return jsonify({
                'success': True,
                'message': '任务已标记为失败'
            })
        else:
            return jsonify({
                'success': False,
                'message': '操作失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


@bp.route('/<task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    """
    取消任务
    """
    try:
        user_id = g.user['user_id']
        
        task_service = get_task_service()
        task = task_service.get_by_id(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        if str(task.user_id) != user_id:
            return jsonify({
                'success': False,
                'message': '无权操作此任务'
            }), 403
        
        # 只能取消待执行或执行中的任务
        if task.status not in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
            return jsonify({
                'success': False,
                'message': f'任务状态为 {task.status}，无法取消'
            }), 400
        
        if task_service.cancel_task(task_id):
            return jsonify({
                'success': True,
                'message': '任务已取消'
            })
        else:
            return jsonify({
                'success': False,
                'message': '取消任务失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'取消任务失败: {str(e)}'
        }), 500


@bp.route('/<task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """
    删除任务
    注意：只能删除已完成、失败或取消的任务
    """
    try:
        user_id = g.user['user_id']
        
        task_service = get_task_service()
        task = task_service.get_by_id(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        if str(task.user_id) != user_id and g.user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': '无权删除此任务'
            }), 403
        
        # 不能删除正在执行的任务
        if task.status in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
            return jsonify({
                'success': False,
                'message': '无法删除正在执行或等待执行的任务，请先取消任务'
            }), 400
        
        if task_service.delete_task(task_id):
            return jsonify({
                'success': True,
                'message': '任务已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除任务失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除任务失败: {str(e)}'
        }), 500


@bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_tasks():
    """
    清理已完成的任务
    
    Request Body:
        {
            "days_old": 7  // 可选，清理多少天前的任务
        }
        
    Response:
        {
            "success": true,
            "message": "已清理 5 个任务"
        }
    """
    try:
        user_id = g.user['user_id']
        data = request.get_json() or {}
        
        days_old = data.get('days_old')
        
        before_date = None
        if days_old:
            from datetime import timedelta
            before_date = datetime.utcnow() - timedelta(days=int(days_old))
        
        task_service = get_task_service()
        deleted_count = task_service.delete_completed_tasks(user_id, before_date)
        
        return jsonify({
            'success': True,
            'message': f'已清理 {deleted_count} 个任务'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清理任务失败: {str(e)}'
        }), 500


# ============================================================
# 管理员接口
# ============================================================

@bp.route('/admin/all', methods=['GET'])
@admin_required
def admin_list_all_tasks():
    """
    管理员：获取所有用户的任务
    
    Query Parameters:
        user_id: 可选，按用户筛选
        status: 可选，按状态筛选
        skip: 跳过数量
        limit: 返回数量
    """
    try:
        task_service = get_task_service()
        
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        skip = int(request.args.get('skip', 0))
        limit = min(int(request.args.get('limit', 50)), 200)
        
        # 构建查询
        query = {}
        if user_id:
            from bson import ObjectId
            query['user_id'] = ObjectId(user_id)
        if status:
            query['status'] = status
        
        # 直接查询数据库
        db = task_service.db
        cursor = db.tasks.find(query).sort('created_at', -1).skip(skip).limit(limit)
        total = db.tasks.count_documents(query)
        
        tasks = []
        for doc in cursor:
            from app.models.task import Task
            tasks.append(Task.from_dict(doc).to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks,
                'total': total,
                'skip': skip,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取任务列表失败: {str(e)}'
        }), 500
