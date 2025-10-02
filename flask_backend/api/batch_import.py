#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask后端API - 接收前端批量导出的高质量图片
位置：flask_backend/api/batch_import.py
"""
import base64
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from flask import Blueprint, request, jsonify
import logging

# 创建Blueprint
batch_import_bp = Blueprint('batch_import', __name__)
logger = logging.getLogger(__name__)


@batch_import_bp.route('/api/import-slides-batch', methods=['POST', 'OPTIONS'])
def import_slides_batch():
    """
    接收前端批量导出的幻灯片图片
    
    请求格式:
    {
        "projectName": "项目名称",
        "totalSlides": 24,
        "exportedCount": 24,
        "timestamp": 1696000000000,
        "images": [
            {
                "slideIndex": 0,
                "filename": "slide_001.jpg",
                "dataURL": "data:image/jpeg;base64,...",
                "size": 1234567
            },
            ...
        ]
    }
    
    返回格式:
    {
        "success": true,
        "message": "成功导入24张幻灯片",
        "project_name": "项目名称",
        "output_dir": "/path/to/output",
        "saved_files": ["slide_001.jpg", ...]
    }
    """
    # 处理OPTIONS预检请求（CORS）
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200
    
    try:
        # 获取JSON数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "没有接收到数据"
            }), 400
        
        project_name = data.get('projectName', 'untitled_project')
        images = data.get('images', [])
        total_slides = data.get('totalSlides', 0)
        
        if not images:
            return jsonify({
                "success": False,
                "error": "没有图片数据"
            }), 400
        
        logger.info(f"📥 开始接收批量导出: {project_name}, {len(images)} 张图片")
        
        # 创建输出目录
        output_base = Path(__file__).parent.parent / "output"
        slides_dir = output_base / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存所有图片
        saved_files = []
        failed_files = []
        
        for img_data in images:
            try:
                filename = img_data.get('filename', f"slide_{img_data.get('slideIndex', 0) + 1:03d}.jpg")
                data_url = img_data.get('dataURL', '')
                
                if not data_url or not data_url.startswith('data:image'):
                    logger.warning(f"⚠️ 无效的dataURL: {filename}")
                    failed_files.append(filename)
                    continue
                
                # 解析base64数据
                # 格式: data:image/jpeg;base64,<base64数据>
                header, base64_data = data_url.split(',', 1)
                image_bytes = base64.b64decode(base64_data)
                
                # 保存文件
                file_path = slides_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                
                file_size = len(image_bytes) / 1024  # KB
                logger.info(f"✅ 已保存: {filename} ({file_size:.1f} KB)")
                saved_files.append(filename)
                
            except Exception as e:
                logger.error(f"❌ 保存失败 {filename}: {e}")
                failed_files.append(filename)
        
        # 保存增强的元数据（匹配工作流期望的格式）
        slides_metadata = {
            "project_name": project_name,
            "total_slides": total_slides,
            "export_method": "pptist_batch_export_v1.4",
            "exported_at": datetime.now().isoformat(),
            "slides": []
        }
        
        # 为每个slide生成标准格式的元数据
        for i, filename in enumerate(saved_files, 1):
            img_data = images[i-1]  # 获取对应的图片数据
            
            # 从图片数据中提取可能的文本和时长
            slide_text = img_data.get('text', '')  # 如果前端提供了文本
            slide_duration = img_data.get('duration', max(3.0, len(slide_text) * 0.1))
            
            slide_metadata = {
                "slide_id": i,
                "filename": filename,
                "image_path": f"slides/{filename}",
                "text": slide_text,  # 备注文本（如果前端提供）
                "duration": slide_duration,
                "width": 2000,  # 预期尺寸（实际可能略有不同）
                "height": 1125,
                "exported_at": datetime.now().isoformat()
            }
            slides_metadata["slides"].append(slide_metadata)
        
        # 保存到 output/slides_metadata.json（工作流期望的位置）
        metadata_path = slides_dir / "slides_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(slides_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ 元数据已保存: {metadata_path}")
        logger.info(f"✅ 批量导入完成: {len(saved_files)}/{total_slides}")
        
        response_data = {
            "success": True,
            "message": f"成功导入 {len(saved_files)}/{total_slides} 张幻灯片",
            "project_name": project_name,
            "output_dir": str(slides_dir),
            "saved_files": saved_files,
            "failed_files": failed_files,
            "metadata_path": str(metadata_path),
            # 🔧 添加工作流启动信息
            "workflow_ready": True,
            "next_step": {
                "description": "图片已就绪，可以启动工作流",
                "api_endpoint": "/api/workflow/execute",
                "method": "POST",
                "body": {
                    "project_name": project_name
                },
                "note": "工作流将自动使用 slides_metadata.json 中的图片和文本数据"
            }
        }
        
        return _cors_response(jsonify(response_data))
        
    except Exception as e:
        logger.error(f"❌ 批量导入失败: {e}")
        import traceback
        traceback.print_exc()
        
        return _cors_response(jsonify({
            "success": False,
            "error": str(e)
        }), 500)


def _cors_response(response=None, status=200):
    """添加CORS头"""
    if response is None:
        response = jsonify({"status": "ok"})
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    if status != 200:
        response.status_code = status
    
    return response


# 用于测试的路由
@batch_import_bp.route('/api/test-import', methods=['GET'])
def test_import():
    """测试接口是否正常工作"""
    return _cors_response(jsonify({
        "status": "ok",
        "message": "批量导入API正常运行",
        "timestamp": datetime.now().isoformat()
    }))
