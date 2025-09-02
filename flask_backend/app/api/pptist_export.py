"""
PPTist原生导出API
提供与PPTist前端交互的API接口，用于高质量图片导出
"""
import json
import base64
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

pptist_export_bp = Blueprint('pptist_export', __name__)

@pptist_export_bp.route('/export/slide', methods=['POST'])
def export_single_slide():
    """
    导出单个slide为图片
    接收PPTist前端发送的slide数据和配置，返回图片文件
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        slide_data = data.get('slide')
        config = data.get('config', {})
        project_name = data.get('project_name', 'default')
        
        if not slide_data:
            return jsonify({
                'success': False,
                'message': '缺少slide数据'
            }), 400
        
        # 这里应该调用PPTist的渲染逻辑
        # 由于PPTist是前端应用，我们需要通过浏览器自动化来实现
        # 或者在前端直接调用导出并上传图片数据
        
        return jsonify({
            'success': True,
            'message': '导出功能需要与PPTist前端配合实现',
            'data': {
                'slide_id': slide_data.get('id'),
                'config': config
            }
        })
        
    except Exception as e:
        logger.error(f"导出slide失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@pptist_export_bp.route('/export/batch', methods=['POST'])
def export_batch_slides():
    """
    批量导出slides为图片
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        slides = data.get('slides', [])
        config = data.get('config', {})
        project_name = data.get('project_name', 'default')
        
        if not slides:
            return jsonify({
                'success': False,
                'message': '缺少slides数据'
            }), 400
        
        # 批量导出逻辑
        results = []
        for i, slide in enumerate(slides):
            results.append({
                'slide_index': i,
                'slide_id': slide.get('id'),
                'status': 'pending',
                'message': '等待前端实现'
            })
        
        return jsonify({
            'success': True,
            'message': f'准备导出 {len(slides)} 个slides',
            'data': {
                'results': results,
                'config': config
            }
        })
        
    except Exception as e:
        logger.error(f"批量导出slides失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@pptist_export_bp.route('/upload/image', methods=['POST'])
def upload_exported_image():
    """
    接收PPTist前端导出的图片数据
    这是一个反向API - 前端导出图片后上传到后端
    """
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': '缺少图片文件'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400
        
        # 获取其他参数
        project_name = request.form.get('project_name', 'default')
        slide_index = request.form.get('slide_index', '0')
        slide_id = request.form.get('slide_id', '')
        
        # 安全的文件名
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"slide_{slide_index}.png"
        
        # 保存路径
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "output" / project_name / "slides"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / filename
        file.save(str(file_path))
        
        # 获取文件信息
        file_size = file_path.stat().st_size
        
        logger.info(f"图片上传成功: {filename}, 大小: {file_size} bytes")
        
        return jsonify({
            'success': True,
            'message': '图片上传成功',
            'data': {
                'filename': filename,
                'file_path': str(file_path),
                'file_size': file_size,
                'slide_index': slide_index,
                'slide_id': slide_id
            }
        })
        
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@pptist_export_bp.route('/upload/base64', methods=['POST'])
def upload_base64_image():
    """
    接收base64格式的图片数据
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        image_data = data.get('image_data')
        project_name = data.get('project_name', 'default')
        slide_index = data.get('slide_index', 0)
        slide_id = data.get('slide_id', '')
        format = data.get('format', 'png')
        
        if not image_data:
            return jsonify({
                'success': False,
                'message': '缺少图片数据'
            }), 400
        
        # 解析base64数据
        if image_data.startswith('data:image/'):
            # 移除data URL前缀
            image_data = image_data.split(',')[1]
        
        # 解码base64
        image_bytes = base64.b64decode(image_data)
        
        # 保存文件
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "output" / project_name / "slides"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"slide_{slide_index+1:03d}.{format}"
        file_path = output_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        file_size = file_path.stat().st_size
        
        logger.info(f"Base64图片保存成功: {filename}, 大小: {file_size} bytes")
        
        return jsonify({
            'success': True,
            'message': 'Base64图片保存成功',
            'data': {
                'filename': filename,
                'file_path': str(file_path),
                'file_size': file_size,
                'slide_index': slide_index,
                'slide_id': slide_id
            }
        })
        
    except Exception as e:
        logger.error(f"Base64图片保存失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@pptist_export_bp.route('/export/status/<project_name>', methods=['GET'])
def get_export_status(project_name):
    """获取项目的导出状态"""
    try:
        project_root = Path(__file__).parent.parent.parent
        slides_dir = project_root / "output" / project_name / "slides"
        
        if not slides_dir.exists():
            return jsonify({
                'success': True,
                'data': {
                    'project_name': project_name,
                    'slides_count': 0,
                    'slides': []
                }
            })
        
        # 查找所有图片文件
        image_files = []
        for ext in ['png', 'jpg', 'jpeg']:
            image_files.extend(list(slides_dir.glob(f"*.{ext}")))
        
        # 按文件名排序
        image_files.sort(key=lambda x: x.name)
        
        slides_info = []
        for file_path in image_files:
            file_stat = file_path.stat()
            slides_info.append({
                'filename': file_path.name,
                'file_size': file_stat.st_size,
                'created_at': file_stat.st_ctime,
                'file_path': str(file_path)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'project_name': project_name,
                'slides_count': len(slides_info),
                'slides': slides_info,
                'slides_dir': str(slides_dir)
            }
        })
        
    except Exception as e:
        logger.error(f"获取导出状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@pptist_export_bp.route('/upload/file', methods=['POST'])
def upload_slide_file():
    """
    接收前端直接捕获的图片文件
    用于新的直接幻灯片捕获功能
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '缺少图片文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400
        
        # 获取其他参数
        project_name = request.form.get('project_name', 'default')
        slide_index = request.form.get('slide_index', '0')
        slide_id = request.form.get('slide_id', '')
        format_type = request.form.get('format', 'jpeg')
        
        # 生成安全的文件名
        slide_num = str(int(slide_index) + 1).zfill(3)
        file_extension = 'jpg' if format_type == 'jpeg' else format_type
        filename = f"slide_{slide_num}.{file_extension}"
        
        # 保存路径
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "output" / project_name / "slides"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / filename
        file.save(str(file_path))
        
        # 获取文件信息
        file_size = file_path.stat().st_size
        
        logger.info(f"直接捕获文件上传成功: {filename}, 大小: {file_size} bytes")
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'filename': filename,
                'file_size': file_size,
                'slide_index': slide_index,
                'slide_id': slide_id,
                'file_path': str(file_path),
                'project_name': project_name
            }
        })
        
    except Exception as e:
        logger.error(f"直接捕获文件上传失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
