"""
图片生成 API
支持 OpenAI DALL-E、Flux、Nano Banana 等兼容 OpenAI 格式的图片生成模型
"""
import os
import sys
import json
import base64
import uuid
import httpx
import asyncio
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, g, send_file
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from app.auth.decorators import login_required, get_current_user_id
from app.services.storage_service import StorageService
from app.models.user_config import get_user_config_service

# 配置日志
logger = logging.getLogger(__name__)

bp = Blueprint('image_generator', __name__)


def get_system_image_config():
    """获取系统级图片生成配置（作为默认值）"""
    try:
        config_path = Path(__file__).parent.parent.parent / 'config_data' / 'app_config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('image_generation', {})
    except Exception as e:
        logger.error(f"加载系统图片生成配置失败: {e}")
    return {}


def get_user_image_config(user_id: str) -> dict:
    """获取用户的图片生成配置，如果没有则返回系统默认配置"""
    # 获取系统配置作为基础
    system_config = get_system_image_config()
    
    try:
        # 获取用户配置
        config_service = get_user_config_service()
        user_config = config_service.get_by_user_id(user_id)
        
        if user_config and user_config.image_generation:
            # 合并配置，用户配置优先
            merged_config = system_config.copy()
            merged_config.update(user_config.image_generation)
            return merged_config
    except Exception as e:
        logger.error(f"获取用户图片生成配置失败: {e}")
    
    return system_config


def get_user_images_dir(user_id: str) -> Path:
    """获取用户图片存储目录"""
    storage_service = StorageService()
    work_dir = storage_service.get_user_work_dir(user_id)
    images_dir = work_dir / 'generated_images'
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


# 预定义的模型配置 - 只保留 Nano Banana 系列
MODEL_CONFIGS = {
    # Nano Banana 系列 (基于 Gemini)
    'nano-banana': {
        'sizes': ['1:1', '4:3', '3:4', '16:9', '9:16', '2:3', '3:2'],
        'qualities': ['high', 'medium', 'low'],
        'supports_reference': True,
        'description': 'Gemini 2.5 Flash Image: 速度快，最多上传3张参考图片，适合快速生成、轻量级任务'
    },
    'nano-banana-2': {
        'sizes': ['1:1', '4:3', '3:4', '16:9', '9:16', '2:3', '3:2'],
        'qualities': ['high', 'medium', 'low'],
        'supports_reference': True,
        'description': 'Gemini 3 Pro Image Preview: 专业级质量，最多上传14张参考图片，支持最高4K分辨率'
    }
}

# 尺寸标签映射
SIZE_LABELS = {
    '1:1': '1:1 (正方形)',
    '4:3': '4:3 (横向)',
    '3:4': '3:4 (纵向)',
    '16:9': '16:9 (宽屏)',
    '9:16': '9:16 (竖屏)',
    '2:3': '2:3 (人像)',
    '3:2': '3:2 (风景)'
}


@bp.route('/config', methods=['GET', 'POST', 'OPTIONS'])
@login_required
def handle_config():
    """获取或保存当前用户的图片生成配置"""
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
    # GET: 获取配置
    if request.method == 'GET':
        try:
            user_id = get_current_user_id()
            config = get_user_image_config(user_id)
            
            # 返回自定义模型列表
            custom_models = config.get('custom_models', ['nano-banana', 'nano-banana-2'])
            
            return jsonify({
                'success': True,
                'data': {
                    'api_base_url': config.get('api_base_url', ''),
                    'api_key': config.get('api_key', ''),  # 前端需要显示
                    'has_api_key': bool(config.get('api_key')),
                    'default_model': config.get('default_model', 'nano-banana'),
                    'custom_models': custom_models,
                    'model_configs': MODEL_CONFIGS,
                    'size_labels': SIZE_LABELS
                }
            })
        except Exception as e:
            logger.error(f"获取图片生成配置失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # POST: 保存配置
    if request.method == 'POST':
        try:
            user_id = get_current_user_id()
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '无效的请求数据'}), 400
            
            # 支持嵌套的 image_generation 结构
            if 'image_generation' in data:
                config_data = data['image_generation']
            else:
                config_data = data
            
            # 允许保存的配置字段
            allowed_fields = ['api_base_url', 'api_key', 'default_model', 'custom_models']
            config_to_save = {k: v for k, v in config_data.items() if k in allowed_fields}
            
            # 保存到用户配置
            config_service = get_user_config_service()
            config_service.update_section(user_id, 'image_generation', config_to_save)
            
            return jsonify({
                'success': True,
                'message': '配置保存成功'
            })
        except Exception as e:
            logger.error(f"保存图片生成配置失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/generate', methods=['POST'])
@login_required
def generate_image():
    """
    生成图片
    
    请求体:
    {
        "prompt": "图片描述",
        "model": "dall-e-3",
        "size": "1024x1024",
        "quality": "standard",
        "n": 1,
        "reference_images": ["base64..."]  // 可选，参考图片
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({'success': False, 'error': '请输入图片描述'}), 400
        
        model = data.get('model', 'dall-e-3')
        size = data.get('size', '1024x1024')
        quality = data.get('quality', 'standard')
        n = data.get('n', 1)
        reference_images = data.get('reference_images', [])
        
        # 获取用户配置
        config = get_user_image_config(user_id)
        api_base_url = config.get('api_base_url', 'https://api.openai.com/v1')
        api_key = config.get('api_key', '')
        
        if not api_key:
            return jsonify({'success': False, 'error': '请先配置图片生成 API 密钥'}), 400
        
        # 构建请求
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        # 根据是否有参考图片选择不同的 API endpoint
        if reference_images and model in ['dall-e-2', 'gpt-image-1', 'nano-banana', 'nano-banana-2', 'nano-banana-hd', 'flux-kontext-pro', 'flux-kontext-max']:
            # 使用图片编辑 API
            result = _generate_with_reference(api_base_url, headers, prompt, model, size, quality, reference_images, user_id)
        else:
            # 使用标准图片生成 API
            result = _generate_standard(api_base_url, headers, prompt, model, size, quality, n, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"图片生成失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _generate_standard(api_base_url: str, headers: dict, prompt: str, model: str, size: str, quality: str, n: int, user_id: str) -> dict:
    """标准图片生成"""
    url = f"{api_base_url.rstrip('/')}/images/generations"
    
    payload = {
        'prompt': prompt,
        'model': model,
        'size': size,
        'n': n
    }
    
    # 某些模型支持 quality 参数
    if model in ['dall-e-3', 'gpt-image-1'] or 'banana' in model or 'kontext' in model:
        payload['quality'] = quality
    
    logger.info(f"请求图片生成 API: {url}, model={model}, size={size}")
    
    # 使用同步请求
    response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
    
    if response.status_code != 200:
        error_msg = response.text
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', error_msg)
        except:
            pass
        return {'success': False, 'error': f'API 请求失败: {error_msg}'}
    
    result = response.json()
    images = []
    
    for idx, item in enumerate(result.get('data', [])):
        image_info = _save_generated_image(item, user_id, prompt, model)
        if image_info:
            images.append(image_info)
    
    return {
        'success': True,
        'data': {
            'images': images,
            'prompt': prompt,
            'model': model,
            'revised_prompt': result.get('data', [{}])[0].get('revised_prompt', prompt)
        }
    }


def _generate_with_reference(api_base_url: str, headers: dict, prompt: str, model: str, size: str, quality: str, reference_images: list, user_id: str) -> dict:
    """带参考图片的图片生成（图片编辑）"""
    url = f"{api_base_url.rstrip('/')}/images/edits"
    
    # 构建 multipart/form-data 请求
    files = []
    data = {
        'prompt': prompt,
        'model': model,
        'size': size
    }
    
    if quality:
        data['quality'] = quality
    
    # 处理参考图片
    for idx, img_base64 in enumerate(reference_images):
        # 移除 base64 前缀
        if ',' in img_base64:
            img_base64 = img_base64.split(',')[1]
        
        img_bytes = base64.b64decode(img_base64)
        files.append(('image[]', (f'image_{idx}.png', img_bytes, 'image/png')))
    
    logger.info(f"请求图片编辑 API: {url}, model={model}, size={size}, 参考图片数: {len(reference_images)}")
    
    # 使用 multipart/form-data
    del headers['Content-Type']  # httpx 会自动设置
    
    response = httpx.post(url, data=data, files=files, headers=headers, timeout=120.0)
    
    if response.status_code != 200:
        error_msg = response.text
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', error_msg)
        except:
            pass
        return {'success': False, 'error': f'API 请求失败: {error_msg}'}
    
    result = response.json()
    images = []
    
    for idx, item in enumerate(result.get('data', [])):
        image_info = _save_generated_image(item, user_id, prompt, model)
        if image_info:
            images.append(image_info)
    
    return {
        'success': True,
        'data': {
            'images': images,
            'prompt': prompt,
            'model': model,
            'revised_prompt': result.get('data', [{}])[0].get('revised_prompt', prompt)
        }
    }


def _save_generated_image(item: dict, user_id: str, prompt: str, model: str) -> dict:
    """保存生成的图片到用户目录"""
    try:
        images_dir = get_user_images_dir(user_id)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_id = str(uuid.uuid4())[:8]
        filename = f"generated_{timestamp}_{image_id}.png"
        filepath = images_dir / filename
        
        # 保存图片
        if item.get('b64_json'):
            # base64 格式
            img_data = base64.b64decode(item['b64_json'])
            with open(filepath, 'wb') as f:
                f.write(img_data)
        elif item.get('url'):
            # URL 格式，下载图片
            response = httpx.get(item['url'], timeout=60.0)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
            else:
                logger.error(f"下载图片失败: {item['url']}")
                return None
        else:
            logger.error("图片数据格式不正确")
            return None
        
        # 保存元数据
        metadata = {
            'filename': filename,
            'prompt': prompt,
            'model': model,
            'revised_prompt': item.get('revised_prompt', prompt),
            'created_at': datetime.now().isoformat(),
            'url': item.get('url', ''),
            'user_id': user_id
        }
        
        metadata_path = images_dir / f"{filename}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            'filename': filename,
            'url': f'/api/image-generator/image/{filename}',
            'revised_prompt': item.get('revised_prompt', prompt),
            'created_at': metadata['created_at']
        }
        
    except Exception as e:
        logger.error(f"保存图片失败: {e}")
        return None


@bp.route('/image/<filename>', methods=['GET'])
@login_required
def get_image(filename: str):
    """获取生成的图片"""
    try:
        user_id = get_current_user_id()
        images_dir = get_user_images_dir(user_id)
        filepath = images_dir / filename
        
        if not filepath.exists():
            return jsonify({'success': False, 'error': '图片不存在'}), 404
        
        return send_file(filepath, mimetype='image/png')
        
    except Exception as e:
        logger.error(f"获取图片失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/list', methods=['GET'])
@login_required
def list_images():
    """获取用户生成的图片列表"""
    try:
        user_id = get_current_user_id()
        images_dir = get_user_images_dir(user_id)
        
        images = []
        if images_dir.exists():
            for metadata_file in images_dir.glob('*.json'):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # 检查图片文件是否存在
                    img_path = images_dir / metadata['filename']
                    if img_path.exists():
                        images.append({
                            'filename': metadata['filename'],
                            'url': f'/api/image-generator/image/{metadata["filename"]}',
                            'prompt': metadata.get('prompt', ''),
                            'model': metadata.get('model', ''),
                            'created_at': metadata.get('created_at', '')
                        })
                except Exception as e:
                    logger.warning(f"读取图片元数据失败: {metadata_file}, {e}")
        
        # 按创建时间倒序排列
        images.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'images': images,
                'total': len(images)
            }
        })
        
    except Exception as e:
        logger.error(f"获取图片列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/delete/<filename>', methods=['DELETE'])
@login_required
def delete_image(filename: str):
    """删除生成的图片"""
    try:
        user_id = get_current_user_id()
        images_dir = get_user_images_dir(user_id)
        
        # 删除图片文件
        filepath = images_dir / filename
        if filepath.exists():
            filepath.unlink()
        
        # 删除元数据文件
        metadata_path = images_dir / f"{filename}.json"
        if metadata_path.exists():
            metadata_path.unlink()
        
        return jsonify({'success': True, 'message': '图片已删除'})
        
    except Exception as e:
        logger.error(f"删除图片失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
