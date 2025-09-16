"""
下载API接口
处理文件下载
"""
import os
from pathlib import Path
from flask import Blueprint, send_file, current_app, jsonify
from app.utils.logger import get_logger

bp = Blueprint('download', __name__)
logger = get_logger(__name__)

@bp.route('/<project_name>/<filename>', methods=['GET'])
def download_project_file(project_name, filename):
    """下载项目文件"""
    try:
        # 构建文件路径
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'output'))
        file_path = output_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.error(f"请求的文件不存在: {file_path}")
            return jsonify({
                'success': False,
                'message': f'文件 {filename} 不存在'
            }), 404
        
        logger.info(f"开始下载文件: {file_path}")
        
        # 发送文件
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"下载文件时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': f'下载失败: {str(e)}'
        }), 500