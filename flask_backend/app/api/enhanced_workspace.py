"""
增强的工作空间持久化API
实现PPTist项目的完整保存、加载和更新功能
"""
import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from utils.logger import get_logger  # type: ignore
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

# 创建蓝图
bp = Blueprint('enhanced_workspace', __name__)
logger = get_logger(__name__)

# 工作空间根目录
WORKSPACE_ROOT = Path("flask_backend/output")

@bp.route('/save', methods=['POST'])
def save_workspace():
    """
    保存PPTist工作空间
    使用JSON格式作为主要持久化文件
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少项目数据'
            }), 400
        
        project_name = data.get('project_name', f"pptist_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # 确保工作空间目录存在
        WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
        
        # 创建项目元数据
        project_metadata = {
            "project_name": project_name,
            "title": data.get('title', project_name),
            "source": "pptist_workspace",
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "format_version": "1.0",
            "pptist_data": data,  # 完整的PPTist JSON数据
            "workspace_info": {
                "slides_count": len(data.get('slides', [])),
                "canvas_size": {
                    "width": data.get('width', 1000),
                    "height": data.get('height', 562.5)
                },
                "theme": data.get('theme', {}),
                "has_animations": False,  # 可以扩展检查动画
                "total_elements": sum(len(slide.get('elements', [])) for slide in data.get('slides', []))
            }
        }
        
        # 保存工作空间文件
        workspace_file = WORKSPACE_ROOT / "workspace.json"
        with open(workspace_file, 'w', encoding='utf-8') as f:
            json.dump(project_metadata, f, ensure_ascii=False, indent=2)
        
        # 同时保存项目元数据文件（用于后端工作流）
        project_metadata_file = WORKSPACE_ROOT / "project_metadata.json"
        backend_metadata = {
            "project_name": project_name,
            "source": "pptist_frontend",
            "created_at": datetime.now().isoformat(),
            "import_info": {
                "title": data.get('title', project_name),
                "description": "从PPTist前端保存",
                "imported_at": datetime.now().isoformat(),
                "total_slides": len(data.get('slides', []))
            },
            "processing_ready": True
        }
        
        with open(project_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(backend_metadata, f, ensure_ascii=False, indent=2)
        
        # 保存兼容格式（用于后端工作流）
        ppt_data_file = WORKSPACE_ROOT / "ppt_data.json"
        compatible_data = {
            "project_name": data.get('title', project_name),
            "slides": [],
            "created_at": datetime.now().isoformat()
        }
        
        # 转换为后端兼容格式
        for i, slide in enumerate(data.get('slides', [])):
            compatible_slide = {
                "id": slide.get('id', f"slide_{i+1}"),
                "slide_number": i + 1,
                "elements": slide.get('elements', []),
                "background": slide.get('background', {"type": "solid", "color": "#fff"}),
                "remark": slide.get('remark', '')
            }
            compatible_data["slides"].append(compatible_slide)
        
        with open(ppt_data_file, 'w', encoding='utf-8') as f:
            json.dump(compatible_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"工作空间已保存: {project_name}")
        
        return jsonify({
            'success': True,
            'message': '工作空间保存成功',
            'data': {
                'project_name': project_name,
                'workspace_file': str(workspace_file),
                'slides_count': len(data.get('slides', [])),
                'last_modified': project_metadata['last_modified']
            }
        })
        
    except Exception as e:
        logger.error(f"保存工作空间失败: {e}")
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500

@bp.route('/load', methods=['GET'])
def load_workspace():
    """
    加载PPTist工作空间
    优先返回完整的PPTist JSON格式数据
    """
    try:
        workspace_file = WORKSPACE_ROOT / "workspace.json"
        
        if not workspace_file.exists():
            return jsonify({
                'success': False,
                'message': '工作空间文件不存在'
            }), 404
        
        # 读取工作空间文件
        with open(workspace_file, 'r', encoding='utf-8') as f:
            workspace_data = json.load(f)
        
        # 提取PPTist数据
        pptist_data = workspace_data.get('pptist_data', {})
        
        if not pptist_data:
            # 如果没有完整的PPTist数据，尝试从兼容文件构建
            ppt_data_file = WORKSPACE_ROOT / "ppt_data.json"
            if ppt_data_file.exists():
                with open(ppt_data_file, 'r', encoding='utf-8') as f:
                    ppt_data = json.load(f)
                
                # 构建基本的PPTist格式
                pptist_data = {
                    "title": ppt_data.get('project_name', '未命名演示文稿'),
                    "width": 1000,
                    "height": 562.5,
                    "theme": {
                        "themeColors": ["#d14836"],
                        "fontColor": "#333333",
                        "backgroundColor": "#ffffff"
                    },
                    "slides": ppt_data.get('slides', [])
                }
        
        logger.info(f"工作空间已加载: {workspace_data.get('project_name', 'unknown')}")
        
        return jsonify({
            'success': True,
            'message': '工作空间加载成功',
            'data': {
                'workspace_info': {
                    'project_name': workspace_data.get('project_name'),
                    'title': workspace_data.get('title'),
                    'created_at': workspace_data.get('created_at'),
                    'last_modified': workspace_data.get('last_modified'),
                    'slides_count': workspace_data.get('workspace_info', {}).get('slides_count', 0)
                },
                'pptist_data': pptist_data
            }
        })
        
    except Exception as e:
        logger.error(f"加载工作空间失败: {e}")
        return jsonify({
            'success': False,
            'message': f'加载失败: {str(e)}'
        }), 500

@bp.route('/update', methods=['PUT'])
def update_workspace():
    """
    更新PPTist工作空间
    增量更新，保持历史记录
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少更新数据'
            }), 400
        
        workspace_file = WORKSPACE_ROOT / "workspace.json"
        
        # 如果工作空间不存在，创建新的
        if not workspace_file.exists():
            return save_workspace()
        
        # 读取现有工作空间
        with open(workspace_file, 'r', encoding='utf-8') as f:
            workspace_data = json.load(f)
        
        # 创建备份
        backup_file = WORKSPACE_ROOT / f"workspace_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(workspace_file, backup_file)
        
        # 更新数据
        workspace_data['last_modified'] = datetime.now().isoformat()
        workspace_data['pptist_data'] = data
        workspace_data['workspace_info']['slides_count'] = len(data.get('slides', []))
        workspace_data['workspace_info']['total_elements'] = sum(
            len(slide.get('elements', [])) for slide in data.get('slides', [])
        )
        
        # 保存更新后的工作空间
        with open(workspace_file, 'w', encoding='utf-8') as f:
            json.dump(workspace_data, f, ensure_ascii=False, indent=2)
        
        # 同步更新兼容文件
        ppt_data_file = WORKSPACE_ROOT / "ppt_data.json"
        compatible_data = {
            "project_name": data.get('title', workspace_data.get('title', '未命名演示文稿')),
            "slides": [],
            "created_at": workspace_data.get('created_at'),
            "last_modified": datetime.now().isoformat()
        }
        
        for i, slide in enumerate(data.get('slides', [])):
            compatible_slide = {
                "id": slide.get('id', f"slide_{i+1}"),
                "slide_number": i + 1,
                "elements": slide.get('elements', []),
                "background": slide.get('background', {"type": "solid", "color": "#fff"}),
                "remark": slide.get('remark', '')
            }
            compatible_data["slides"].append(compatible_slide)
        
        with open(ppt_data_file, 'w', encoding='utf-8') as f:
            json.dump(compatible_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"工作空间已更新: {workspace_data.get('project_name')}")
        
        return jsonify({
            'success': True,
            'message': '工作空间更新成功',
            'data': {
                'project_name': workspace_data.get('project_name'),
                'backup_file': str(backup_file),
                'slides_count': len(data.get('slides', [])),
                'last_modified': workspace_data['last_modified']
            }
        })
        
    except Exception as e:
        logger.error(f"更新工作空间失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500

@bp.route('/export/<format>', methods=['GET'])
def export_workspace(format):
    """
    导出工作空间为指定格式
    支持: json, backup
    注意: .pptist格式由前端PPTist直接处理，无需后端支持
    """
    try:
        workspace_file = WORKSPACE_ROOT / "workspace.json"
        
        if not workspace_file.exists():
            return jsonify({
                'success': False,
                'message': '工作空间文件不存在'
            }), 404
        
        with open(workspace_file, 'r', encoding='utf-8') as f:
            workspace_data = json.load(f)
        
        pptist_data = workspace_data.get('pptist_data', {})
        project_name = workspace_data.get('project_name', 'workspace')
        
        if format == 'json':
            # 导出纯JSON格式
            filename = f"{project_name}.json"
            temp_file = WORKSPACE_ROOT / filename
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(pptist_data, f, ensure_ascii=False, indent=2)
            
            return send_file(
                str(temp_file),
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
            
        elif format == 'backup':
            # 导出完整的工作空间备份
            filename = f"{project_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            temp_file = WORKSPACE_ROOT / filename
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, ensure_ascii=False, indent=2)
            
            return send_file(
                str(temp_file),
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
        
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的导出格式: {format}'
            }), 400
        
    except Exception as e:
        logger.error(f"导出工作空间失败: {e}")
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}'
        }), 500

@bp.route('/status', methods=['GET'])
def workspace_status():
    """
    获取工作空间状态信息
    """
    try:
        workspace_file = WORKSPACE_ROOT / "workspace.json"
        ppt_data_file = WORKSPACE_ROOT / "ppt_data.json"
        
        status = {
            'workspace_exists': workspace_file.exists(),
            'ppt_data_exists': ppt_data_file.exists(),
            'workspace_size': 0,
            'last_modified': None,
            'slides_count': 0,
            'project_name': None
        }
        
        if workspace_file.exists():
            file_stat = workspace_file.stat()
            status['workspace_size'] = file_stat.st_size
            status['last_modified'] = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            with open(workspace_file, 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)
                status['project_name'] = workspace_data.get('project_name')
                status['slides_count'] = workspace_data.get('workspace_info', {}).get('slides_count', 0)
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"获取工作空间状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500

@bp.route('/cleanup', methods=['POST'])
def cleanup_workspace():
    """
    清理工作空间
    移除临时文件，保留主要数据
    """
    try:
        data = request.get_json() or {}
        keep_backups = data.get('keep_backups', True)
        
        cleaned_files = []
        
        # 清理临时文件
        for pattern in ['*.tmp', 'temp_*', '*.cache']:
            for file in WORKSPACE_ROOT.glob(pattern):
                file.unlink()
                cleaned_files.append(file.name)
        
        # 清理旧备份（如果不保留）
        if not keep_backups:
            for backup_file in WORKSPACE_ROOT.glob('workspace_backup_*.json'):
                backup_file.unlink()
                cleaned_files.append(backup_file.name)
        
        return jsonify({
            'success': True,
            'message': '工作空间清理完成',
            'data': {
                'cleaned_files': cleaned_files,
                'cleanup_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"清理工作空间失败: {e}")
        return jsonify({
            'success': False,
            'message': f'清理失败: {str(e)}'
        }), 500
