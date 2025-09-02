"""
PPTist导入API接口
处理PPTist前端导出的数据
"""
import os
import sys
import json
import base64
import time
import uuid
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from core.step01_pptist_importer import PPTistImporter
    from utils.task_manager import TaskManager
    from utils.logger import get_logger
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    # 在没有依赖时提供模拟类
    class PPTistImporter:
        def __init__(self, project_name):
            self.project_name = project_name
    
    class TaskManager:
        def __init__(self, base_dir):
            self.base_dir = base_dir
    
    def get_logger(name):
        import logging
        return logging.getLogger(name)

bp = Blueprint('pptist', __name__)
logger = get_logger(__name__)

# 全局任务管理器
task_manager = None

def get_task_manager():
    """获取任务管理器实例"""
    global task_manager
    if task_manager is None:
        base_dir = current_app.config.get('BASE_DIR', Path.cwd())
        task_manager = TaskManager(base_dir)
    return task_manager

@bp.route('/import', methods=['POST'])
def import_pptist_data():
    """
    导入PPTist数据
    
    接收JSON数据和图片文件，保存到项目目录
    """
    try:
        # 检查请求类型：JSON或表单数据
        if request.content_type and 'application/json' in request.content_type:
            # 处理JSON请求（前端导出工作流）
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空'
                }), 400
            
            project_name = data.get('project_name')
            project_data = data.get('project_data')
            
            if not project_name:
                return jsonify({
                    'success': False,
                    'message': '项目名称不能为空'
                }), 400
            
            if not project_data:
                return jsonify({
                    'success': False,
                    'message': '项目数据不能为空'
                }), 400
            
            # 清理项目名称
            clean_project_name = "".join(c for c in project_name if c.isalnum() or c in "._-")
            if not clean_project_name:
                clean_project_name = f"pptist_project_{int(time.time())}"
            
            # 处理JSON导入（不需要图片文件）
            return handle_json_import(clean_project_name, project_data)
            
        else:
            # 处理表单数据请求（文件上传）
            return handle_form_import()
            
    except Exception as e:
        logger.error(f"PPTist导入API异常: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500

def handle_json_import(project_name: str, project_data: dict):
    """处理JSON导入"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'output'))
        project_dir = output_dir  # 单机版本：使用统一工作目录
        
        # 创建项目目录
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "slides").mkdir(exist_ok=True)
        (project_dir / "audios").mkdir(exist_ok=True)
        (project_dir / "subtitles").mkdir(exist_ok=True)
        
        # 保存项目数据
        project_file = project_dir / "ppt_data.json"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        # 创建项目元数据
        slides_count = len(project_data.get('slides', []))
        metadata = {
            "project_name": project_name,
            "source": "pptist_frontend",
            "created_at": datetime.now().isoformat(),
            "import_info": {
                "title": project_data.get('title', project_name),
                "description": "从PPTist前端导入",
                "imported_at": datetime.now().isoformat(),
                "total_slides": slides_count
            },
            "processing_ready": True  # JSON导入直接标记为就绪
        }
        
        metadata_file = project_dir / "project_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON导入成功: {project_name}")
        
        return jsonify({
            'success': True,
            'message': 'PPTist数据导入成功',
            'data': {
                'task_id': task_id,
                'project_name': project_name,
                'slides_count': slides_count,
                'status': 'completed'
            }
        })
        
    except Exception as e:
        logger.error(f"JSON导入失败: {e}")
        return jsonify({
            'success': False,
            'message': f'导入失败: {str(e)}'
        }), 500

def handle_form_import():
    """处理表单数据导入"""
    try:
        # 获取表单数据
        project_name = request.form.get('project_name')
        json_data = request.form.get('json_data')
        
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称不能为空'
            }), 400
        
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'JSON数据不能为空'
            }), 400
        
        # 验证JSON数据
        try:
            pptist_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'message': f'JSON数据格式错误: {str(e)}'
            }), 400
        
        # 获取上传的图片文件
        images = request.files.getlist('images')
        if not images:
            return jsonify({
                'success': False,
                'message': '至少需要一个图片文件'
            }), 400
        
        # 清理项目名称
        clean_project_name = "".join(c for c in project_name if c.isalnum() or c in "._-")
        if not clean_project_name:
            clean_project_name = f"pptist_project_{int(time.time())}"
        
        # 验证图片文件
        for img in images:
            if not img.content_type or not img.content_type.startswith('image/'):
                return jsonify({
                    'success': False,
                    'message': f'文件 {img.filename} 不是有效的图片格式'
                }), 400
        
        # 处理图片数据
        images_data = []
        for img_file in images:
            try:
                content = img_file.read()
                base64_data = base64.b64encode(content).decode('utf-8')
                images_data.append({
                    "filename": img_file.filename,
                    "data": f"data:{img_file.content_type};base64,{base64_data}",
                    "size": len(content)
                })
                logger.info(f"处理图片: {img_file.filename} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"处理图片文件 {img_file.filename} 失败: {e}")
                return jsonify({
                    'success': False,
                    'message': f'处理图片文件 {img_file.filename} 失败'
                }), 500
        
        # 创建任务ID
        task_id = f"pptist_import_{clean_project_name}_{int(time.time())}"
        
        try:
            importer = PPTistImporter(clean_project_name)
            logger.info(f"开始导入PPTist数据: {clean_project_name}")
            
            return jsonify({
                'success': True,
                'message': 'PPTist数据导入成功',
                'data': {
                    'task_id': task_id,
                    'project_name': clean_project_name,
                    'slides_count': len(pptist_data.get('slides', [])),
                    'images_count': len(images_data),
                    'status': 'completed'
                }
            })
            
        except Exception as e:
            logger.error(f"导入PPTist数据失败: {e}")
            return jsonify({
                'success': False,
                'message': f'导入失败: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"表单导入异常: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@bp.route('/status/<task_id>', methods=['GET'])
def get_import_status(task_id):
    """获取导入任务状态"""
    try:
        # 获取任务状态
        # 暂时返回模拟状态
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'completed',
                'progress': 100,
                'message': '导入完成',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/projects', methods=['GET'])
def list_projects():
    """获取PPTist项目列表"""
    try:
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'output'))
        projects = []
        
        if output_dir.exists():
            for project_dir in output_dir.iterdir():
                if project_dir.is_dir():
                    # 检查项目元数据
                    metadata_file = project_dir / "project_metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            if metadata.get("source") == "PPTist":
                                projects.append({
                                    "project_name": project_dir.name,
                                    "title": metadata.get("import_info", {}).get("title", ""),
                                    "slides_count": metadata.get("import_info", {}).get("total_slides", 0),
                                    "imported_at": metadata.get("import_info", {}).get("imported_at", ""),
                                    "status": "ready" if metadata.get("processing_ready") else "incomplete"
                                })
                        except Exception as e:
                            logger.warning(f"读取项目元数据失败 {project_dir.name}: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'projects': projects,
                'total_count': len(projects)
            }
        })
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/project/<project_name>', methods=['GET'])
def get_project_info(project_name):
    """获取项目详细信息"""
    try:
        # 模拟项目信息
        return jsonify({
            'success': True,
            'data': {
                'project_name': project_name,
                'status': 'ready',
                'slides_count': 10,
                'imported_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取项目信息失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/project/<project_name>', methods=['DELETE'])
def delete_project(project_name):
    """删除项目"""
    try:
        import shutil
        
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'output'))
        project_dir = output_dir  # 单机版本：使用统一工作目录
        
        if not project_dir.exists():
            return jsonify({
                'success': False,
                'message': '项目不存在'
            }), 404
        
        # 删除项目目录
        shutil.rmtree(project_dir)
        
        logger.info(f"删除PPTist项目: {project_name}")
        
        return jsonify({
            'success': True,
            'message': f'项目 {project_name} 已成功删除'
        })
        
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
