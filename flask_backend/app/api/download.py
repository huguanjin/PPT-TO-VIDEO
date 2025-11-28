"""
下载API接口
处理文件下载
"""
import os
from pathlib import Path
from flask import Blueprint, send_file, current_app, jsonify
from app.utils.logger import get_logger
from app.auth.decorators import optional_login, get_current_user_id
from app.services.storage_service import StorageService

bp = Blueprint('download', __name__)
logger = get_logger(__name__)

@bp.route('/<project_name>/<filename>', methods=['GET'])
@optional_login
def download_project_file(project_name, filename):
    """下载项目文件"""
    try:
        # 获取当前用户的工作目录
        user_id = get_current_user_id()
        storage_service = StorageService()
        output_dir = storage_service.get_user_work_dir(user_id)
        
        # 对于final_video.mp4，需要查找final目录中的最新文件
        if filename == 'final_video.mp4':
            final_dir = output_dir / 'final'
            if final_dir.exists():
                # 查找最新的final_video_*.mp4文件
                video_files = list(final_dir.glob('final_video_*.mp4'))
                if video_files:
                    # 按文件名排序（时间戳），获取最新的
                    latest_video = sorted(video_files, key=lambda x: x.name)[-1]
                    file_path = latest_video
                    logger.info(f"找到最新视频文件: {file_path}")
                else:
                    logger.error(f"final目录中没有找到视频文件: {final_dir}")
                    return jsonify({
                        'success': False,
                        'message': f'没有找到视频文件'
                    }), 404
            else:
                logger.error(f"final目录不存在: {final_dir}")
                return jsonify({
                    'success': False,
                    'message': f'final目录不存在'
                }), 404
        else:
            # 其他文件直接在output目录查找
            file_path = output_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.error(f"请求的文件不存在: {file_path}")
            return jsonify({
                'success': False,
                'message': f'文件 {filename} 不存在'
            }), 404
        
        logger.info(f"开始下载文件: {file_path}")
        
        # 确定下载文件名
        download_name = filename
        if filename == 'final_video.mp4' and 'final_video_' in file_path.name:
            # 对于final_video.mp4，可以选择保持原名或使用实际文件名
            # 这里保持原名便于前端处理
            download_name = filename
        
        # 发送文件
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        logger.error(f"下载文件时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'下载失败: {str(e)}'
        }), 500