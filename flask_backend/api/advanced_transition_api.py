"""
任务4.1: 高级视频效果系统 - Flask API接口

为转场效果引擎提供RESTful API服务
支持实时预览、批量处理和效果管理
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import uuid
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

# 导入核心模块
from task4_1_advanced_transition_engine import (
    AdvancedTransitionEngine,
    TransitionConfig, 
    TransitionType,
    EasingType,
    VideoClip,
    TransitionResult
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 全局变量
transition_engine = None
executor = ThreadPoolExecutor(max_workers=4)
active_sessions = {}

def get_transition_engine():
    """获取转场引擎实例"""
    global transition_engine
    if transition_engine is None:
        transition_engine = AdvancedTransitionEngine()
    return transition_engine

def run_async_task(coro):
    """在新线程中运行异步任务"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    future = executor.submit(run_in_thread)
    return future

@app.route('/api/transitions/list', methods=['GET'])
def list_transitions():
    """列出所有可用的转场效果"""
    try:
        engine = get_transition_engine()
        transitions = engine.list_available_transitions()
        
        return jsonify({
            "success": True,
            "data": {
                "transitions": transitions,
                "total": len(transitions)
            }
        })
    
    except Exception as e:
        logger.error(f"列出转场效果失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/presets', methods=['GET'])
def get_presets():
    """获取转场效果预设"""
    try:
        engine = get_transition_engine()
        presets = {}
        
        for name, config in engine.presets.items():
            presets[name] = {
                "transition_type": config.transition_type.value,
                "duration": config.duration,
                "easing": config.easing.value,
                "intensity": config.intensity,
                "blur_amount": config.blur_amount,
                "audio_fade": config.audio_fade
            }
        
        return jsonify({
            "success": True,
            "data": {
                "presets": presets,
                "total": len(presets)
            }
        })
    
    except Exception as e:
        logger.error(f"获取预设失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/config/validate', methods=['POST'])
def validate_config():
    """验证转场配置"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['transition_type', 'duration']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"缺少必需字段: {field}"
                }), 400
        
        # 验证转场类型
        try:
            transition_type = TransitionType(data['transition_type'])
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"无效的转场类型: {data['transition_type']}"
            }), 400
        
        # 验证时长
        duration = data['duration']
        if not isinstance(duration, (int, float)) or duration <= 0:
            return jsonify({
                "success": False,
                "error": "时长必须为正数"
            }), 400
        
        # 验证缓动类型
        easing = data.get('easing', 'ease_in_out')
        try:
            easing_type = EasingType(easing)
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"无效的缓动类型: {easing}"
            }), 400
        
        # 验证强度
        intensity = data.get('intensity', 1.0)
        if not isinstance(intensity, (int, float)) or intensity < 0 or intensity > 2:
            return jsonify({
                "success": False,
                "error": "强度必须在0.0-2.0之间"
            }), 400
        
        # 创建配置对象进行进一步验证
        config = TransitionConfig(
            transition_type=transition_type,
            duration=duration,
            easing=easing_type,
            intensity=intensity,
            blur_amount=data.get('blur_amount', 0.0),
            audio_fade=data.get('audio_fade', True)
        )
        
        return jsonify({
            "success": True,
            "data": {
                "valid": True,
                "config": {
                    "transition_type": config.transition_type.value,
                    "duration": config.duration,
                    "easing": config.easing.value,
                    "intensity": config.intensity,
                    "blur_amount": config.blur_amount,
                    "audio_fade": config.audio_fade
                }
            }
        })
    
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/apply', methods=['POST'])
def apply_transition():
    """应用转场效果"""
    try:
        data = request.get_json()
        
        # 验证输入
        required_fields = ['clip_a', 'clip_b', 'config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"缺少必需字段: {field}"
                }), 400
        
        # 创建视频片段对象
        clip_a_data = data['clip_a']
        clip_b_data = data['clip_b']
        
        clip_a = VideoClip(
            id=clip_a_data.get('id', str(uuid.uuid4())),
            path=clip_a_data['path'],
            start_time=clip_a_data.get('start_time', 0.0),
            end_time=clip_a_data.get('end_time', 5.0),
            width=clip_a_data.get('width', 1920),
            height=clip_a_data.get('height', 1080),
            fps=clip_a_data.get('fps', 30.0)
        )
        
        clip_b = VideoClip(
            id=clip_b_data.get('id', str(uuid.uuid4())),
            path=clip_b_data['path'],
            start_time=clip_b_data.get('start_time', 0.0),
            end_time=clip_b_data.get('end_time', 5.0),
            width=clip_b_data.get('width', 1920),
            height=clip_b_data.get('height', 1080),
            fps=clip_b_data.get('fps', 30.0)
        )
        
        # 创建转场配置
        config_data = data['config']
        config = TransitionConfig(
            transition_type=TransitionType(config_data['transition_type']),
            duration=config_data['duration'],
            easing=EasingType(config_data.get('easing', 'ease_in_out')),
            intensity=config_data.get('intensity', 1.0),
            blur_amount=config_data.get('blur_amount', 0.0),
            audio_fade=config_data.get('audio_fade', True)
        )
        
        # 生成输出路径
        output_path = data.get('output_path')
        if not output_path:
            temp_dir = Path(tempfile.gettempdir()) / "video_transitions"
            temp_dir.mkdir(exist_ok=True)
            output_path = str(temp_dir / f"transition_{uuid.uuid4().hex[:8]}.mp4")
        
        # 创建会话ID
        session_id = str(uuid.uuid4())
        
        # 进度回调函数
        progress_data = {"progress": 0.0, "status": "开始处理"}
        
        def progress_callback(progress: float):
            progress_data["progress"] = progress
            progress_data["status"] = f"处理中... {progress*100:.1f}%"
            active_sessions[session_id] = progress_data.copy()
        
        # 启动异步任务
        engine = get_transition_engine()
        
        def process_transition():
            # 在新事件循环中运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    engine.apply_transition(clip_a, clip_b, config, output_path, progress_callback)
                )
                return result
            finally:
                loop.close()
        
        # 如果是同步请求，直接处理
        if data.get('async', True):
            # 异步处理
            future = executor.submit(process_transition)
            active_sessions[session_id] = {
                "progress": 0.0,
                "status": "排队中",
                "future": future
            }
            
            return jsonify({
                "success": True,
                "data": {
                    "session_id": session_id,
                    "status": "started",
                    "message": "转场效果处理已开始"
                }
            })
        else:
            # 同步处理
            result = process_transition()
            
            if result.success:
                return jsonify({
                    "success": True,
                    "data": {
                        "result": {
                            "output_path": result.output_path,
                            "duration": result.duration,
                            "file_size": result.file_size,
                            "quality_metrics": result.quality_metrics,
                            "processing_time": result.processing_time
                        }
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result.error_message
                }), 500
    
    except Exception as e:
        logger.error(f"应用转场效果失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/status/<session_id>', methods=['GET'])
def get_transition_status(session_id):
    """获取转场处理状态"""
    try:
        if session_id not in active_sessions:
            return jsonify({
                "success": False,
                "error": "会话不存在"
            }), 404
        
        session_data = active_sessions[session_id]
        
        # 检查是否完成
        if 'future' in session_data:
            future = session_data['future']
            
            if future.done():
                try:
                    result = future.result()
                    
                    # 清理会话
                    del active_sessions[session_id]
                    
                    if result.success:
                        return jsonify({
                            "success": True,
                            "data": {
                                "status": "completed",
                                "progress": 1.0,
                                "result": {
                                    "output_path": result.output_path,
                                    "duration": result.duration,
                                    "file_size": result.file_size,
                                    "quality_metrics": result.quality_metrics,
                                    "processing_time": result.processing_time
                                }
                            }
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "error": result.error_message
                        }), 500
                
                except Exception as e:
                    # 清理会话
                    del active_sessions[session_id]
                    return jsonify({
                        "success": False,
                        "error": f"处理失败: {str(e)}"
                    }), 500
        
        # 返回当前状态
        return jsonify({
            "success": True,
            "data": {
                "status": "processing",
                "progress": session_data.get("progress", 0.0),
                "message": session_data.get("status", "处理中")
            }
        })
    
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/batch', methods=['POST'])
def apply_batch_transitions():
    """批量应用转场效果"""
    try:
        data = request.get_json()
        
        # 验证输入
        required_fields = ['clips', 'configs']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"缺少必需字段: {field}"
                }), 400
        
        clips_data = data['clips']
        configs_data = data['configs']
        
        if len(clips_data) < 2:
            return jsonify({
                "success": False,
                "error": "至少需要2个视频片段"
            }), 400
        
        # 创建视频片段列表
        clips = []
        for clip_data in clips_data:
            clip = VideoClip(
                id=clip_data.get('id', str(uuid.uuid4())),
                path=clip_data['path'],
                start_time=clip_data.get('start_time', 0.0),
                end_time=clip_data.get('end_time', 5.0),
                width=clip_data.get('width', 1920),
                height=clip_data.get('height', 1080),
                fps=clip_data.get('fps', 30.0)
            )
            clips.append(clip)
        
        # 创建转场配置列表
        configs = []
        for config_data in configs_data:
            config = TransitionConfig(
                transition_type=TransitionType(config_data['transition_type']),
                duration=config_data['duration'],
                easing=EasingType(config_data.get('easing', 'ease_in_out')),
                intensity=config_data.get('intensity', 1.0),
                blur_amount=config_data.get('blur_amount', 0.0),
                audio_fade=config_data.get('audio_fade', True)
            )
            configs.append(config)
        
        # 生成输出目录
        output_dir = data.get('output_dir')
        if not output_dir:
            temp_dir = Path(tempfile.gettempdir()) / "video_transitions"
            temp_dir.mkdir(exist_ok=True)
            output_dir = str(temp_dir / f"batch_{uuid.uuid4().hex[:8]}")
            Path(output_dir).mkdir(exist_ok=True)
        
        # 创建会话
        session_id = str(uuid.uuid4())
        
        # 进度回调
        batch_progress = {"current": 0, "total": len(clips) - 1, "progress": 0.0}
        
        def batch_progress_callback(current: int, total: int):
            batch_progress["current"] = current
            batch_progress["total"] = total
            batch_progress["progress"] = current / total if total > 0 else 0.0
            
            active_sessions[session_id] = {
                "progress": batch_progress["progress"],
                "status": f"处理转场 {current}/{total}",
                "batch_info": batch_progress.copy()
            }
        
        # 启动批量处理
        engine = get_transition_engine()
        
        def process_batch():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    engine.batch_apply_transitions(clips, configs, output_dir, batch_progress_callback)
                )
                return results
            finally:
                loop.close()
        
        # 异步处理
        future = executor.submit(process_batch)
        active_sessions[session_id] = {
            "progress": 0.0,
            "status": "批量处理开始",
            "future": future,
            "batch_info": batch_progress.copy()
        }
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "status": "started",
                "total_transitions": len(clips) - 1,
                "output_dir": output_dir
            }
        })
    
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/preview', methods=['POST'])
def preview_transition():
    """预览转场效果"""
    try:
        data = request.get_json()
        
        # 验证输入
        required_fields = ['config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"缺少必需字段: {field}"
                }), 400
        
        config_data = data['config']
        
        # 创建转场配置
        config = TransitionConfig(
            transition_type=TransitionType(config_data['transition_type']),
            duration=config_data['duration'],
            easing=EasingType(config_data.get('easing', 'ease_in_out')),
            intensity=config_data.get('intensity', 1.0),
            blur_amount=config_data.get('blur_amount', 0.0),
            audio_fade=config_data.get('audio_fade', True)
        )
        
        # 生成预览信息
        engine = get_transition_engine()
        
        # 创建示例视频片段
        clip_a = VideoClip(
            id="preview_a",
            path="preview_a.mp4",
            start_time=0.0,
            end_time=5.0,
            width=1920,
            height=1080,
            fps=30.0
        )
        
        clip_b = VideoClip(
            id="preview_b", 
            path="preview_b.mp4",
            start_time=0.0,
            end_time=5.0,
            width=1920,
            height=1080,
            fps=30.0
        )
        
        # 生成滤镜链预览
        filter_complex = await_sync(engine._generate_filter_complex(clip_a, clip_b, config))
        
        # 获取转场描述
        transitions = engine.list_available_transitions()
        transition_info = next(
            (t for t in transitions if t['type'] == config.transition_type.value), 
            None
        )
        
        return jsonify({
            "success": True,
            "data": {
                "config": {
                    "transition_type": config.transition_type.value,
                    "duration": config.duration,
                    "easing": config.easing.value,
                    "intensity": config.intensity,
                    "blur_amount": config.blur_amount
                },
                "preview_info": {
                    "description": transition_info['description'] if transition_info else "",
                    "category": transition_info['category'] if transition_info else "",
                    "complexity": transition_info['complexity'] if transition_info else "",
                    "estimated_processing_time": config.duration * 2 + 5,  # 估算处理时间
                    "filter_preview": filter_complex[:200] + "..." if len(filter_complex) > 200 else filter_complex
                }
            }
        })
    
    except Exception as e:
        logger.error(f"预览失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def await_sync(coro):
    """同步等待协程"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/api/transitions/download/<path:file_path>', methods=['GET'])
def download_result(file_path):
    """下载处理结果"""
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return jsonify({
                "success": False,
                "error": "文件不存在"
            }), 404
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=file_path.name
        )
    
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/cleanup', methods=['POST'])
def cleanup_sessions():
    """清理过期会话"""
    try:
        cleaned_count = 0
        
        # 清理已完成的会话
        sessions_to_remove = []
        for session_id, session_data in active_sessions.items():
            if 'future' in session_data and session_data['future'].done():
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del active_sessions[session_id]
            cleaned_count += 1
        
        return jsonify({
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count,
                "active_sessions": len(active_sessions)
            }
        })
    
    except Exception as e:
        logger.error(f"清理失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/transitions/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        engine = get_transition_engine()
        
        return jsonify({
            "success": True,
            "data": {
                "status": "healthy",
                "engine_ready": engine is not None,
                "active_sessions": len(active_sessions),
                "available_transitions": len(engine.list_available_transitions()),
                "presets": len(engine.presets),
                "timestamp": datetime.now().isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "API端点不存在"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500

if __name__ == '__main__':
    print("🎬 任务4.1: 高级视频效果系统 - Flask API服务启动")
    print("=" * 60)
    print("API端点:")
    print("  GET  /api/transitions/list        - 列出转场效果")
    print("  GET  /api/transitions/presets     - 获取预设配置")
    print("  POST /api/transitions/apply       - 应用转场效果")
    print("  POST /api/transitions/batch       - 批量处理")
    print("  POST /api/transitions/preview     - 预览效果")
    print("  GET  /api/transitions/health      - 健康检查")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8002, debug=True)
