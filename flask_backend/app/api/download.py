"""
下载API接口
处理文件下载
"""
import os
from pathlib import Path
from flask import Blueprint, send_file, current_app, jsonify
from utils.logger import get_logger

bp = Blueprint('download', __name__)
logger = get_logger(__name__)

@bp.route('/<project_name>/<filename>', methods=['GET'])
def download_project_file(project_name, filename):
    """下载项目文件"""
    try:
        # 构建文件路径
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'output'))
        
        # 特殊处理 final_video.mp4 请求
        if filename == 'final_video.mp4':
            # 在final目录中查找最新的final_video_*.mp4文件
            final_dir = output_dir / 'final'
            if final_dir.exists():
                video_files = list(final_dir.glob('final_video_*.mp4'))
                if video_files:
                    # 选择最新的文件
                    latest_video = max(video_files, key=lambda f: f.stat().st_mtime)
                    file_path = latest_video
                    logger.info(f"找到最新的最终视频文件: {file_path}")
                else:
                    logger.warning(f"在final目录中未找到final_video_*.mp4文件")
                    return jsonify({
                        'success': False,
                        'message': f'文件 {filename} 不存在'
                    }), 404
            else:
                logger.warning(f"final目录不存在: {final_dir}")
                return jsonify({
                    'success': False,
                    'message': f'文件 {filename} 不存在'
                }), 404
        else:
            # 单机版本：直接在output目录中查找文件
            file_path = output_dir / filename
            
            # 如果不存在，尝试final子目录（最终视频文件通常在这里）
            if not file_path.exists() and filename.startswith('final_video_'):
                file_path = output_dir / 'final' / filename
                logger.info(f"尝试从final目录查找文件: {file_path}")
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return jsonify({
                'success': False,
                'message': f'文件 {filename} 不存在'
            }), 404
        
        # 确定MIME类型
        if filename.endswith('.mp4'):
            mimetype = 'video/mp4'
        elif filename.endswith('.wav'):
            mimetype = 'audio/wav'
        elif filename.endswith('.srt'):
            mimetype = 'text/plain'
        else:
            mimetype = 'application/octet-stream'
        
        logger.info(f"下载文件: {file_path}")
        
        # 返回文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/task/<task_id>', methods=['GET'])
def download_task_result(task_id):
    """根据任务ID下载结果文件"""
    try:
        from app.api.workflow import task_statuses
        
        # 检查任务是否存在
        if task_id not in task_statuses:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        task_status = task_statuses[task_id]
        
        # 检查任务是否完成
        if task_status['status'] != 'completed':
            return jsonify({
                'success': False,
                'message': '任务尚未完成'
            }), 400
        
        # 获取项目名称和文件名
        project_name = task_status.get('project_name', '')
        result = task_status.get('result', {})
        video_file = result.get('video_file', '')
        
        if not project_name or not video_file:
            return jsonify({
                'success': False,
                'message': '无法获取下载文件信息'
            }), 400
        
        # 重定向到项目文件下载
        return download_project_file(project_name, video_file)
        
    except Exception as e:
        logger.error(f"下载任务结果失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
