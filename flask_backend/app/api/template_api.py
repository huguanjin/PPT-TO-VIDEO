"""
PPTist模板数据API
提供模板JSON文件和封面图片的访问接口
"""
import os
import logging
from flask import Blueprint, jsonify, send_file, abort
from flask_cors import cross_origin

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

template_api = Blueprint('template_api', __name__)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'flask_backend', 'data')
IMG_DIR = os.path.join(BASE_DIR, 'flask_backend', 'static', 'img')

@template_api.route('/data/<filename>', methods=['GET'])
@cross_origin()
def get_template_data(filename):
    """
    获取模板JSON数据
    支持的文件：template_1.json, template_2.json, template_3.json, template_4.json, slides.json
    """
    try:
        # 确保文件名安全
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = os.path.join(DATA_DIR, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"模板文件不存在: {file_path}")
            abort(404)
        
        # 返回JSON文件
        return send_file(file_path, mimetype='application/json')
        
    except Exception as e:
        logger.error(f"获取模板数据失败: {str(e)}")
        return jsonify({'error': f'获取模板数据失败: {str(e)}'}), 500

@template_api.route('/img/<filename>', methods=['GET'])
@cross_origin()
def get_template_image(filename):
    """
    获取模板封面图片
    支持的文件：template_1.jpg, template_2.jpg, template_3.jpg, template_4.jpg
    """
    try:
        # 确保是图片文件
        if not any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            abort(404)
        
        file_path = os.path.join(IMG_DIR, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"图片文件不存在: {file_path}")
            # 如果图片不存在，返回一个默认图片或者404
            abort(404)
        
        # 根据文件扩展名设置MIME类型
        if filename.endswith('.png'):
            mimetype = 'image/png'
        elif filename.endswith('.webp'):
            mimetype = 'image/webp'
        else:
            mimetype = 'image/jpeg'
        
        return send_file(file_path, mimetype=mimetype)
        
    except Exception as e:
        logger.error(f"获取模板图片失败: {str(e)}")
        return jsonify({'error': f'获取模板图片失败: {str(e)}'}), 500

@template_api.route('/templates/list', methods=['GET'])
@cross_origin()
def list_templates():
    """
    获取可用模板列表
    """
    try:
        templates = []
        
        # 检查数据目录中的模板文件
        if os.path.exists(DATA_DIR):
            for filename in os.listdir(DATA_DIR):
                if filename.startswith('template_') and filename.endswith('.json'):
                    template_id = filename.replace('.json', '')
                    template_name = f"模板 {template_id.split('_')[1]}"
                    
                    templates.append({
                        'id': template_id,
                        'name': template_name,
                        'data_url': f'/data/{filename}',
                        'cover_url': f'/img/{template_id}.jpg',
                        'available': True
                    })
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        return jsonify({'error': f'获取模板列表失败: {str(e)}'}), 500

@template_api.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    模板API健康检查
    """
    try:
        data_exists = os.path.exists(DATA_DIR)
        img_exists = os.path.exists(IMG_DIR)
        
        template_files = []
        if data_exists:
            template_files = [f for f in os.listdir(DATA_DIR) if f.startswith('template_') and f.endswith('.json')]
        
        return jsonify({
            'status': 'healthy',
            'data_directory': data_exists,
            'img_directory': img_exists,
            'template_count': len(template_files),
            'templates': template_files
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({'error': f'健康检查失败: {str(e)}'}), 500