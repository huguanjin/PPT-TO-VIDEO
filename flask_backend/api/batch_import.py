#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask后端API - 接收前端批量导出的高质量图片
位置:flask_backend/api/batch_import.py
"""
import base64
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from flask import Blueprint, request, jsonify, g
import logging
import sys

# 添加项目根目录到Python路径
flask_backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(flask_backend_root))

# 导入工作流相关类
from core.workflow_persistence import StepStatus

# 🔧 导入用户认证和存储服务
from app.auth.decorators import get_current_user_id, optional_login
from app.services.storage_service import StorageService

# 创建Blueprint
batch_import_bp = Blueprint('batch_import', __name__)
logger = logging.getLogger(__name__)


@batch_import_bp.route('/api/import-slides-batch', methods=['POST', 'OPTIONS'])
@optional_login
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
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
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
        
        # 🔧 多用户支持：使用用户专属工作目录
        user_id = get_current_user_id()
        storage_service = StorageService()
        output_base = storage_service.get_user_work_dir(user_id)
        slides_dir = output_base / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)
        
        # 🔧 调试日志：打印详细信息
        print(f"🔧🔧🔧 [DEBUG] user_id = {user_id}")
        print(f"🔧🔧🔧 [DEBUG] output_base = {output_base}")
        print(f"🔧🔧🔧 [DEBUG] slides_dir = {slides_dir}")
        print(f"🔧🔧🔧 [DEBUG] g.user_id = {getattr(g, 'user_id', 'NOT SET')}")
        print(f"🔧🔧🔧 [DEBUG] g.username = {getattr(g, 'username', 'NOT SET')}")
        
        logger.info(f"🔧 用户ID: {user_id}, 输出目录: {output_base}")
        
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
        
        # 🔧 NEW: 自动启动工作流
        workflow_id = None
        auto_start_workflow = data.get('auto_start_workflow', True)  # 默认自动启动
        
        # 🔧 从 ppt_data.json 读取原始项目名称（用于 MongoDB tasks 表）
        ppt_project_name = project_name  # 默认使用前端传来的项目名
        ppt_data_path = output_base / "ppt_data.json"
        if ppt_data_path.exists():
            try:
                with open(ppt_data_path, 'r', encoding='utf-8') as f:
                    ppt_data = json.load(f)
                    ppt_project_name = ppt_data.get('project_name', project_name)
                    logger.info(f"📝 从 ppt_data.json 读取项目名称: {ppt_project_name}")
            except Exception as e:
                logger.warning(f"⚠️ 读取 ppt_data.json 失败，使用默认名称: {e}")
        
        if auto_start_workflow:
            try:
                # 🔧 传入用户目录 output_base 和原始项目名称给工作流执行器
                workflow_id = _start_workflow_sync(project_name, slides_metadata, output_base, ppt_project_name)
                logger.info(f"🚀 工作流已启动: {workflow_id}")
            except Exception as e:
                logger.error(f"❌ 启动工作流失败: {e}")
                # 不影响导入成功,继续返回
        
        response_data = {
            "success": True,
            "message": f"成功导入 {len(saved_files)}/{total_slides} 张幻灯片",
            "project_name": project_name,
            "output_dir": str(slides_dir),
            "saved_files": saved_files,
            "failed_files": failed_files,
            "metadata_path": str(metadata_path),
            # 🔧 添加工作流信息
            "workflow_id": workflow_id,  # 前端需要这个ID来查询进度
            "workflow_started": workflow_id is not None,
            "workflow_ready": workflow_id is not None,  # 🔧 兼容前端检查的字段名
            "workflow_status_url": f"/api/workflow/status/{workflow_id}" if workflow_id else None
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
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    if status != 200:
        response.status_code = status
    
    return response


async def _start_workflow_async(project_name: str, slides_metadata: Dict[str, Any], output_base: Path = None, ppt_project_name: str = None) -> str:
    """
    异步启动工作流
    
    Args:
        project_name: 项目名称（用于 task_id）
        slides_metadata: 幻灯片元数据
        output_base: 用户输出目录
        ppt_project_name: PPT原始项目名称（用于 MongoDB tasks 表显示）
    
    Returns:
        workflow_id: 工作流任务ID
    """
    # 如果未提供 ppt_project_name，使用 project_name
    if ppt_project_name is None:
        ppt_project_name = project_name
    try:
        from core.enhanced_workflow_executor import EnhancedWorkflowExecutor
        from app.api.workflow import update_task_status
        
        # 生成任务ID
        task_id = f"workflow_{project_name}_{int(time.time())}"
        
        # 初始化任务状态
        update_task_status(
            task_id=task_id,
            status='pending',
            message='工作流准备启动',
            progress=0,
            project_name=ppt_project_name,  # 🔧 使用PPT原始项目名称
            current_step=0,
            total_steps=5,
            steps=[
                {'name': '准备阶段', 'status': 'pending', 'message': '初始化工作流'},
                {'name': 'TTS音频生成', 'status': 'pending', 'message': '等待开始'},
                {'name': '字幕文件生成', 'status': 'pending', 'message': '等待开始'},
                {'name': '视频片段合成', 'status': 'pending', 'message': '等待开始'},
                {'name': '最终视频合并', 'status': 'pending', 'message': '等待开始'}
            ]
        )
        
        # 🔧 多用户支持：使用传入的用户目录或默认目录
        if output_base is None:
            # 回退到默认目录（兼容旧调用）
            output_base = Path(__file__).parent.parent / "output"
            logger.warning("⚠️ 未指定用户目录，使用默认output目录")
        
        executor = EnhancedWorkflowExecutor(project_dir=output_base)
        logger.info(f"🔧 工作流执行器使用目录: {output_base}")
        
        # 定义进度回调 - 接收WorkflowExecution对象
        async def progress_callback(execution):
            """工作流进度回调 - 匹配EnhancedWorkflowExecutor的签名"""
            try:
                # 从execution对象提取信息
                current_step_name = execution.current_step or 'step01_data_preparation'
                
                # 步骤映射
                step_mapping = {
                    'step01_data_preparation': (0, '准备阶段'),
                    'step02_tts_generation': (1, 'TTS音频生成'),
                    'step03_subtitle_generation': (2, '字幕文件生成'),
                    'step04_video_generation': (3, '视频片段合成'),
                    'step05_final_merge': (4, '最终视频合并')
                }
                
                current_step_index, step_display_name = step_mapping.get(
                    current_step_name, (0, '处理中')
                )
                
                # 获取当前步骤进度
                step_progress = 0.0
                step_message = '处理中'
                if execution.steps and current_step_name in execution.steps:
                    step_info = execution.steps[current_step_name]
                    step_progress = step_info.progress
                    # WorkflowStepResult 没有 message 属性，使用 status 判断
                    if step_info.status == StepStatus.RUNNING:
                        step_message = f'进行中 ({int(step_info.progress)}%)'
                    elif step_info.status == StepStatus.COMPLETED:
                        step_message = '已完成'
                    elif step_info.status == StepStatus.FAILED:
                        step_message = step_info.error_message or '执行失败'
                    else:
                        step_message = '等待开始'
                
                # 计算总进度 (基于步骤数 + 当前步骤内进度)
                total_progress = int((current_step_index / 5) * 100 + (step_progress / 5))
                
                # 构建步骤列表
                steps = [
                    {'name': '准备阶段', 'status': 'pending', 'message': '等待开始'},
                    {'name': 'TTS音频生成', 'status': 'pending', 'message': '等待开始'},
                    {'name': '字幕文件生成', 'status': 'pending', 'message': '等待开始'},
                    {'name': '视频片段合成', 'status': 'pending', 'message': '等待开始'},
                    {'name': '最终视频合并', 'status': 'pending', 'message': '等待开始'}
                ]
                
                # 更新步骤状态
                for i in range(5):
                    if i < current_step_index:
                        steps[i]['status'] = 'completed'
                        steps[i]['message'] = '已完成'
                    elif i == current_step_index:
                        steps[i]['status'] = 'running'
                        steps[i]['message'] = step_message
                
                update_task_status(
                    task_id=task_id,
                    status='running',
                    message=step_message,
                    progress=total_progress,
                    project_name=ppt_project_name,  # 🔧 使用PPT原始项目名称
                    current_step=current_step_index,
                    total_steps=5,
                    steps=steps
                )
                
            except Exception as e:
                logger.error(f"进度回调错误: {e}")
        
        # 在后台线程中启动工作流
        import threading
        
        def run_workflow():
            """在新线程中运行工作流"""
            try:
                # 启动工作流
                result = asyncio.run(executor.start_workflow(
                    project_name=project_name,
                    config={
                        'slides_metadata': slides_metadata,
                        'use_existing_slides': True  # 使用已有的图片
                    },
                    progress_callback=progress_callback
                ))
                
                # 工作流完成 - 处理WorkflowExecution对象
                # 🔧 修复：使用正确的 workflow_status 属性判断成功/失败
                workflow_status = getattr(result, 'workflow_status', None)
                success = (workflow_status is not None and 
                          workflow_status.value == 'completed')
                
                logger.info(f"工作流执行结果: workflow_status={workflow_status}, success={success}")
                
                if success:
                    # 🔧 修复：将 WorkflowStepResult 对象转换为可序列化的字典
                    raw_steps = getattr(result, 'steps', {})
                    serializable_steps = {}
                    if isinstance(raw_steps, dict):
                        for step_name, step_result in raw_steps.items():
                            if hasattr(step_result, '__dict__'):
                                # 转换 WorkflowStepResult 为字典
                                step_dict = {}
                                for attr in ['step_name', 'status', 'start_time', 'end_time', 
                                           'progress', 'output_files', 'error_message', 'execution_time']:
                                    val = getattr(step_result, attr, None)
                                    # 处理枚举值
                                    if hasattr(val, 'value'):
                                        val = val.value
                                    step_dict[attr] = val
                                serializable_steps[step_name] = step_dict
                            else:
                                serializable_steps[step_name] = step_result
                    
                    result_data = {
                        'video_file': getattr(result, 'video_file', ''),
                        'duration': getattr(result, 'duration', 0),
                        'steps': serializable_steps
                    }
                    update_task_status(
                        task_id=task_id,
                        status='completed',
                        message='视频生成完成',
                        progress=100,
                        result=result_data,
                        project_name=ppt_project_name,  # 🔧 使用PPT原始项目名称
                        current_step=5,
                        total_steps=5,
                        steps=[
                            {'name': '准备阶段', 'status': 'completed', 'message': '已完成'},
                            {'name': 'TTS音频生成', 'status': 'completed', 'message': '已完成'},
                            {'name': '字幕文件生成', 'status': 'completed', 'message': '已完成'},
                            {'name': '视频片段合成', 'status': 'completed', 'message': '已完成'},
                            {'name': '最终视频合并', 'status': 'completed', 'message': '已完成'}
                        ]
                    )
                else:
                    # 🔧 修复：获取正确的错误信息
                    error_msg = getattr(result, 'error_message', None) or '工作流执行失败'
                    update_task_status(
                        task_id=task_id,
                        status='failed',
                        message=error_msg,
                        progress=0,
                        project_name=ppt_project_name  # 🔧 使用PPT原始项目名称
                    )
                    
            except Exception as e:
                logger.error(f"工作流执行错误: {e}")
                import traceback
                traceback.print_exc()
                
                update_task_status(
                    task_id=task_id,
                    status='failed',
                    message=f'工作流执行异常: {str(e)}',
                    progress=0,
                    project_name=ppt_project_name  # 🔧 使用PPT原始项目名称
                )
        
        # 启动后台线程
        thread = threading.Thread(target=run_workflow, daemon=True)
        thread.start()
        
        logger.info(f"✅ 工作流线程已启动: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"启动工作流失败: {e}")
        raise


def _start_workflow_sync(project_name: str, slides_metadata: Dict[str, Any], output_base: Path = None, ppt_project_name: str = None) -> str:
    """
    同步启动工作流 (用于Flask路由)
    
    Args:
        project_name: 项目名称（用于 task_id）
        slides_metadata: 幻灯片元数据
        output_base: 用户工作目录
        ppt_project_name: PPT原始项目名称（用于 MongoDB tasks 表显示）
    
    Returns:
        workflow_id: 工作流任务ID
    """
    # 直接调用异步函数并在新事件循环中运行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_start_workflow_async(project_name, slides_metadata, output_base, ppt_project_name))
    finally:
        loop.close()



# 用于测试的路由
@batch_import_bp.route('/api/test-import', methods=['GET'])
def test_import():
    """测试接口是否正常工作"""
    return _cors_response(jsonify({
        "status": "ok",
        "message": "批量导入API正常运行",
        "timestamp": datetime.now().isoformat()
    }))

