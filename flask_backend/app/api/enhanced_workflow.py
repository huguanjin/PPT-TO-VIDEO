"""
增强的工作流API接口 - 合并FastAPI功能到Flask
处理完整的PPT到视频工作流，包含项目导入、配置管理、执行监控等
"""
import os
import sys
import json
import asyncio
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# 类型检查导入
if TYPE_CHECKING:
    from core.step04_subtitle_generator import SubtitleGenerator as RealSubtitleGenerator

try:
    from core.step01_ppt_parser import PPTParser  # type: ignore
    from core.step02_tts_generator import TTSGenerator  # type: ignore
    from core.step03_video_generator import VideoGenerator  # type: ignore
    from core.step04_subtitle_generator import SubtitleGenerator  # type: ignore
    from core.step05_final_merger import FFmpegFinalMerger  # type: ignore
    from app.utils.task_manager import TaskManager  # type: ignore
    from app.utils.file_manager import FileManager  # type: ignore
    from app.utils.logger import get_logger  # type: ignore
    from config.settings import load_app_config  # type: ignore
    
    # save_app_config 可能不存在，提供安全的导入
    try:
        from config.settings import save_app_config  # type: ignore
    except ImportError:
        def save_app_config(config):
            """备用的配置保存函数"""
            pass
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    # 提供模拟类以避免导入错误
    class PPTParser:
        def __init__(self, project_dir): pass
    class TTSGenerator:
        def __init__(self, project_dir): pass
    class VideoGenerator:
        def __init__(self, project_dir): pass
    class SubtitleGenerator:
        def __init__(self, project_dir, use_enhanced=False, enable_frame_sync=True, 
                     enable_audio_sync=True, enable_ai_content_understanding=False,
                     enable_phase3_alignment=False): pass
        async def generate_subtitles(self, scripts_data=None, audio_data=None, progress_callback=None):
            return {"subtitle_generation_completed": False}
    class FFmpegFinalMerger:
        def __init__(self, project_dir): pass
    class TaskManager:
        def __init__(self, project_dir): pass
    class FileManager:
        def __init__(self, project_dir): pass
    def get_logger(name, log_dir=None):
        import logging
        return logging.getLogger(name)
    def load_app_config():
        return {}
    def save_app_config(config):
        pass

# 创建蓝图
bp = Blueprint('enhanced_workflow', __name__)
logger = get_logger(__name__)

# 全局变量存储工作流状态
workflow_status = {}
project_tasks = {}

class WorkflowConfig:
    """工作流配置类 - 替代Pydantic模型"""
    def __init__(self, data=None):
        data = data or {}
        
        # 视频配置
        video_config = data.get('video', {})
        self.video = {
            'resolution': video_config.get('resolution', '1920x1080'),
            'fps': video_config.get('fps', 24),
            'video_bitrate': video_config.get('video_bitrate', '2000k'),
            'include_subtitles': video_config.get('include_subtitles', True),
            'background_color': video_config.get('background_color', '#FFFFFF')
        }
        
        # TTS配置
        tts_config = data.get('tts', {})
        self.tts = {
            'preferred_engine': tts_config.get('preferred_engine', 'edge_tts'),
            'edge_voice': tts_config.get('edge_voice', 'zh-CN-XiaoxiaoNeural'),
            'edge_rate': tts_config.get('edge_rate', 'medium'),
            'edge_pitch': tts_config.get('edge_pitch', 'medium'),
            'fish_api_key': tts_config.get('fish_api_key', ''),
            'fish_character': tts_config.get('fish_character', '雷军'),
            'fish_character_id': tts_config.get('fish_character_id', ''),
            'fish_character_name': tts_config.get('fish_character_name', ''),
            'openai_api_key': tts_config.get('openai_api_key', ''),
            'openai_voice': tts_config.get('openai_voice', 'alloy'),
            'openai_model': tts_config.get('openai_model', 'tts-1'),
            'azure_api_key': tts_config.get('azure_api_key', ''),
            'azure_region': tts_config.get('azure_region', ''),
            'azure_voice': tts_config.get('azure_voice', 'zh-CN-XiaoxiaoNeural'),
            'sample_rate': tts_config.get('sample_rate', 22050),
            'max_retries': tts_config.get('max_retries', 3),
            'timeout': tts_config.get('timeout', 30.0)
        }
        
        # 字幕配置
        subtitle_config = data.get('subtitle', {})
        self.subtitle = {
            'font_family': subtitle_config.get('font_family', '微软雅黑'),
            'font_size': subtitle_config.get('font_size', 16),  # 优化后的字体大小
            'font_color': subtitle_config.get('font_color', '#FFFFFF'),
            'background_color': subtitle_config.get('background_color', '#000000'),
            'position': subtitle_config.get('position', 'bottom'),
            'enabled': subtitle_config.get('enabled', True),
            # 新增优化配置
            'max_chars_per_line': subtitle_config.get('max_chars_per_line', 26),  # 优化后的字符限制
            'enable_adaptive_font': subtitle_config.get('enable_adaptive_font', True),
            'enable_semantic_split': subtitle_config.get('enable_semantic_split', True),
            'enable_ai_optimization': subtitle_config.get('enable_ai_optimization', False)
        }
        
        # Phase 3智能对齐配置
        phase3_config = data.get('phase3_intelligent_alignment', {})
        self.phase3_alignment = {
            'enabled': phase3_config.get('enabled', False),
            'precision_level': phase3_config.get('precision_level', 'enhanced'),
            'audio_analysis': phase3_config.get('audio_analysis', {
                'sample_rate': 16000,
                'frame_length': 1024,
                'hop_length': 512
            }),
            'alignment_settings': phase3_config.get('alignment_settings', {
                'dtw_step_pattern': 'symmetric2',
                'boundary_detection_threshold': 0.3,
                'min_segment_duration': 0.5
            }),
            'quality_control': phase3_config.get('quality_control', {
                'min_confidence_threshold': 0.7,
                'max_time_deviation': 200,
                'enable_validation': True
            })
        }

@bp.route('/config', methods=['GET'])
def get_enhanced_config():
    """获取增强的工作流配置"""
    try:
        # 读取应用配置
        app_config = load_app_config()
        
        # 优先从app_config.json读取TTS配置（前端主配置文件）
        tts_config = app_config.get("tts", {})
        
        # 如果app_config中没有TTS配置，则从tts_config.json读取（兼容性后备）
        if not tts_config:
            tts_config_path = Path(__file__).parent.parent.parent / "config_data" / "tts_config.json"
            if tts_config_path.exists():
                with open(tts_config_path, 'r', encoding='utf-8') as f:
                    tts_config = json.load(f)
            else:
                tts_config = {}
        
        # 构建完整配置
        config = {
            "video": {
                "resolution": app_config.get("video_resolution", "1920x1080"),
                "fps": app_config.get("video_fps", 24),
                "video_bitrate": app_config.get("video_bitrate", "2000k"),
                "include_subtitles": app_config.get("include_subtitles", True),
                "background_color": app_config.get("background_color", "#FFFFFF")
            },
            "tts": tts_config,
            "subtitle": {
                "font_family": app_config.get("subtitle_font_family", "微软雅黑"),
                "font_size": app_config.get("subtitle_font_size", 16),  # 优化后的字体大小
                "font_color": app_config.get("subtitle_font_color", "#FFFFFF"),
                "background_color": app_config.get("subtitle_background_color", "#000000"),
                "position": app_config.get("subtitle_position", "bottom"),
                "enabled": app_config.get("subtitle_enabled", True),
                # 新增优化配置
                "max_chars_per_line": app_config.get("max_chars_per_line", 26),  # 优化后的字符限制
                "enable_adaptive_font": app_config.get("enable_adaptive_font", True),
                "enable_semantic_split": app_config.get("enable_semantic_split", True),
                "enable_ai_optimization": app_config.get("enable_ai_optimization", False)
            }
        }
        
        return jsonify({"success": True, "config": config})
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({"success": False, "message": f"获取配置失败: {str(e)}"}), 500

@bp.route('/config', methods=['POST'])
def update_enhanced_config():
    """更新增强的工作流配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少配置数据"}), 400
        
        logger.info(f"收到的配置数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 解析配置
        config = WorkflowConfig(data)
        
        # 更新应用配置
        app_config = load_app_config()
        
        # 更新视频配置
        app_config.update({
            "video_resolution": config.video['resolution'],
            "video_fps": config.video['fps'],
            "video_bitrate": config.video['video_bitrate'],
            "include_subtitles": config.video['include_subtitles'],
            "background_color": config.video['background_color'],
            "subtitle_font_family": config.subtitle['font_family'],
            "subtitle_font_size": config.subtitle['font_size'],
            "subtitle_font_color": config.subtitle['font_color'],
            "subtitle_background_color": config.subtitle['background_color'],
            "subtitle_position": config.subtitle['position'],
            "subtitle_enabled": config.subtitle['enabled'],
            # 新增优化配置
            "max_chars_per_line": config.subtitle.get('max_chars_per_line', 26),
            "enable_adaptive_font": config.subtitle.get('enable_adaptive_font', True),
            "enable_semantic_split": config.subtitle.get('enable_semantic_split', True),
            "enable_ai_optimization": config.subtitle.get('enable_ai_optimization', False),
            "subtitle_background_color": config.subtitle['background_color'],
            "subtitle_position": config.subtitle['position'],
            "subtitle_enabled": config.subtitle['enabled']
        })
        
        save_app_config(app_config)
        
        # 注意：不再更新tts_config.json，统一使用app_config.json作为主配置
        # 这避免了配置文件之间的不一致问题
        
        # 如果是Fish TTS，同时更新fish_tts_config.json（仅用于Fish角色配置）
        if config.tts['preferred_engine'] == "fish_tts":
            fish_config_path = Path(__file__).parent.parent.parent / "config_data" / "fish_tts_config.json"
            
            # 读取现有的fish配置
            if fish_config_path.exists():
                with open(fish_config_path, 'r', encoding='utf-8') as f:
                    fish_config = json.load(f)
            else:
                fish_config = {
                    "api_key": "",
                    "character": "雷军",
                    "character_id_dict": {
                        "AD学姐": "7f92f8afb8ec43bf81429cc1c9199cb1",
                        "丁真": "54a5170264694bfc8e9ad98df7bd89c3",
                        "赛马娘": "0eb38bc974e1459facca38b359e13511",
                        "蔡徐坤": "e4642e5edccd4d9ab61a69e82d4f8a14",
                        "雷军": "738d0cc1a3e9430a9de2b544a466a7fc"
                    }
                }
            
            # 更新fish配置
            fish_config["api_key"] = config.tts['fish_api_key']
            fish_config["character"] = config.tts['fish_character']
            
            # 保存更新后的fish配置
            with open(fish_config_path, 'w', encoding='utf-8') as f:
                json.dump(fish_config, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "配置更新成功"})
        
    except Exception as e:
        logger.error(f"配置更新错误: {str(e)}")
        return jsonify({"success": False, "message": f"更新配置失败: {str(e)}"}), 500

@bp.route('/import', methods=['POST'])
def import_project():
    """增强的项目导入功能 - 合并FastAPI的FormData处理"""
    try:
        logger.info("开始处理项目导入请求")
        
        # 获取项目数据
        project_data_str = request.form.get("project_data")
        if not project_data_str:
            logger.error("错误: 缺少project_data参数")
            return jsonify({"success": False, "message": "缺少project_data参数"}), 400
        
        logger.info(f"项目数据长度: {len(project_data_str)}")
        
        # 解析项目数据
        try:
            project_metadata = json.loads(project_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return jsonify({"success": False, "message": f"项目数据JSON格式错误: {e}"}), 400
        
        project_name = project_metadata.get("project_name")
        
        if not project_name:
            # 生成项目名称，但只用于标识，不用于目录
            project_name = f"pptist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"项目名称: {project_name}")
        
        # 单机版本：直接使用当前目录下的output目录作为项目目录
        project_dir = Path("output")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存slides_metadata
        slides_dir = project_dir / "slides"
        slides_dir.mkdir(exist_ok=True)
        
        metadata_path = slides_dir / "slides_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(project_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"元数据已保存到: {metadata_path}")
        
        # 保存图片文件
        image_files = request.files.getlist("images")
        logger.info(f"接收到 {len(image_files)} 个图片文件")
        
        for i, image_file in enumerate(image_files):
            if image_file and image_file.filename:
                logger.info(f"处理图片 {i+1}: {image_file.filename}")
                filename = secure_filename(image_file.filename)
                img_path = slides_dir / filename
                image_file.save(str(img_path))
                logger.info(f"图片已保存到: {img_path}")
            else:
                logger.info(f"跳过无效的图片文件: {type(image_file)}")
        
        # 初始化任务管理器
        task_manager = TaskManager(project_dir)
        
        # 从项目元数据提取slides数据来初始化任务
        slides_data = project_metadata.get("slides", [])
        if slides_data:
            # 安全调用initialize_tasks方法
            if hasattr(task_manager, 'initialize_tasks'):
                task_manager.initialize_tasks(slides_data)  # type: ignore
            task_id = "project_import"
        else:
            # 如果没有slides数据，创建一个简单的导入记录
            task_id = "project_import_simple"
        
        project_tasks[project_name] = task_manager
        
        logger.info(f"项目导入成功: {project_name}")
        return jsonify({
            "success": True,
            "message": f"项目 {project_name} 导入成功",
            "project_name": project_name,
            "task_id": task_id
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"项目导入失败: {e}")
        logger.error(f"详细错误信息: {error_details}")
        return jsonify({"success": False, "message": f"项目导入失败: {str(e)}"}), 500

@bp.route('/execute', methods=['POST'])
def execute_workflow():
    """执行完整工作流 - 合并FastAPI的异步执行功能"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少请求数据"}), 400
        
        project_name = data.get('project_name')
        if not project_name:
            return jsonify({"success": False, "message": "缺少项目名称"}), 400
        
        logger.info(f"开始执行工作流，项目名称: {project_name}")
        
        # 单机版本：直接使用当前目录下的output目录
        project_dir = Path("output")
        
        if not project_dir.exists():
            logger.error(f"错误: 输出目录不存在: {project_dir}")
            return jsonify({"success": False, "message": "输出目录不存在"}), 404
        
        logger.info(f"使用输出目录: {project_dir}")
        
        # 初始化工作流状态
        workflow_id = f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"创建工作流ID: {workflow_id}")
        
        workflow_status[workflow_id] = {
            "status": "running",
            "current_step": 1,
            "total_steps": 5,
            "steps": {
                1: {"name": "解析PPT数据", "status": "running", "progress": 0.0},
                2: {"name": "生成语音", "status": "pending", "progress": 0.0},
                3: {"name": "生成视频", "status": "pending", "progress": 0.0},
                4: {"name": "生成字幕", "status": "pending", "progress": 0.0},
                5: {"name": "合并最终视频", "status": "pending", "progress": 0.0}
            },
            "start_time": datetime.now().isoformat(),
            "project_name": project_name
        }
        
        # 在后台线程执行工作流（Flask版本的后台任务）
        config = WorkflowConfig(data.get('config'))
        thread = threading.Thread(
            target=run_complete_workflow_sync,
            args=(project_name, workflow_id, config)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "workflow_id": workflow_id,
            "message": "工作流开始执行",
            "status_url": f"/api/enhanced_workflow/status/{workflow_id}"
        })
        
    except Exception as e:
        logger.error(f"工作流启动失败: {e}")
        return jsonify({"success": False, "message": f"工作流启动失败: {str(e)}"}), 500

def run_complete_workflow_sync(project_name: str, workflow_id: str, config: WorkflowConfig):
    """运行完整工作流的同步包装器"""
    try:
        # 创建新的事件循环来运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_complete_workflow(project_name, workflow_id, config))
    except Exception as e:
        logger.error(f"工作流执行异常: {str(e)}")
        # 更新失败状态
        if workflow_id in workflow_status:
            workflow_status[workflow_id]["status"] = "failed"
            workflow_status[workflow_id]["error"] = str(e)
            workflow_status[workflow_id]["end_time"] = datetime.now().isoformat()
    finally:
        loop.close()

async def run_complete_workflow(project_name: str, workflow_id: str, config: WorkflowConfig):
    """运行完整工作流 - 从FastAPI移植"""
    try:
        # 单机版本：直接使用当前目录下的output目录
        project_dir = Path("output")
        logger = get_logger(__name__, project_dir / "logs")
        
        # 更新配置（如果提供）
        if config:
            await update_config_internal(config)
        
        def update_step_progress(step: int, status: str, progress: float, message: str = ""):
            workflow_status[workflow_id]["current_step"] = step
            workflow_status[workflow_id]["steps"][step] = {
                "name": workflow_status[workflow_id]["steps"][step]["name"],
                "status": status,
                "progress": progress,
                "message": message
            }
        
        try:
            # 步骤1：解析PPT数据（转换格式）
            update_step_progress(1, "running", 0.0, "正在转换数据格式...")
            
            # 读取slides_metadata.json并转换为scripts_metadata.json
            slides_metadata_path = project_dir / "slides" / "slides_metadata.json"
            if not slides_metadata_path.exists():
                raise Exception("slides_metadata.json文件不存在")
            
            with open(slides_metadata_path, 'r', encoding='utf-8') as f:
                slides_data = json.load(f)
            
            # 转换数据格式
            scripts_data = convert_slides_to_scripts(slides_data)
            
            # 保存scripts_metadata.json
            scripts_dir = project_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            scripts_metadata_path = scripts_dir / "scripts_metadata.json"
            
            with open(scripts_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(scripts_data, f, ensure_ascii=False, indent=2)
            
            update_step_progress(1, "completed", 1.0, "数据格式转换完成")
            
            # 步骤2：生成语音
            update_step_progress(2, "running", 0.0, "正在生成语音...")
            
            tts_generator = TTSGenerator(project_dir)
            
            def tts_progress_callback(progress: int):
                update_step_progress(2, "running", progress / 100.0, f"正在生成语音 {progress}%")
            
            tts_result = await tts_generator.generate_audio(  # type: ignore
                scripts_data=scripts_data,
                progress_callback=tts_progress_callback
            )
            
            # 检查TTS结果
            if not tts_result or not tts_result.get("generation_completed"):
                raise Exception(f"语音生成失败: 生成未完成")
            
            update_step_progress(2, "completed", 1.0, "语音生成完成")
            
            # 步骤3：生成视频
            update_step_progress(3, "running", 0.0, "正在生成视频...")
            
            video_generator = VideoGenerator(project_dir)
            
            def video_progress_callback(progress: int):
                update_step_progress(3, "running", progress / 100.0, f"正在生成视频 {progress}%")
            
            video_result = await video_generator.generate_video_clips(  # type: ignore
                slides_data=slides_data,
                audio_data=tts_result,
                progress_callback=video_progress_callback
            )
            
            if not video_result or not video_result.get("generation_completed"):
                raise Exception(f"视频生成失败: 生成未完成")
            
            update_step_progress(3, "completed", 1.0, "视频生成完成")
            
            # 步骤4：生成字幕
            update_step_progress(4, "running", 0.0, "正在生成字幕...")
            
            # 获取Phase 3配置
            app_config = load_app_config()
            phase3_config = app_config.get('phase3_intelligent_alignment', {})
            enable_phase3_alignment = phase3_config.get('enabled', False)
            
            subtitle_generator = SubtitleGenerator(
                project_dir,
                enable_phase3_alignment=enable_phase3_alignment
            )
            
            def subtitle_progress_callback(progress: int):
                update_step_progress(4, "running", progress / 100.0, f"正在生成字幕 {progress}%")
            
            subtitle_result = await subtitle_generator.generate_subtitles(  # type: ignore
                scripts_data=scripts_data,
                audio_data=tts_result,
                progress_callback=subtitle_progress_callback
            )
            
            if not subtitle_result or not subtitle_result.get("subtitle_generation_completed"):
                raise Exception(f"字幕生成失败: 生成未完成")
            
            update_step_progress(4, "completed", 1.0, "字幕生成完成")
            
            # 步骤5：合并最终视频
            update_step_progress(5, "running", 0.0, "正在合并最终视频...")
            
            final_merger = FFmpegFinalMerger(project_dir)
            
            def merge_progress_callback(progress: int):
                update_step_progress(5, "running", progress / 100.0, f"正在合并视频 {progress}%")
            
            final_result = final_merger.merge_final_video(  # type: ignore
                video_data=video_result,
                audio_data=tts_result,
                subtitle_data=subtitle_result,
                progress_callback=merge_progress_callback
            )
            
            if not final_result.get("success"):
                raise Exception(f"最终视频合并失败: {final_result.get('error', '未知错误')}")
            
            update_step_progress(5, "completed", 1.0, "最终视频合并完成")
            
            # 工作流完成
            workflow_status[workflow_id]["status"] = "completed"
            workflow_status[workflow_id]["end_time"] = datetime.now().isoformat()
            workflow_status[workflow_id]["final_video"] = final_result.get("output_file")
            
            logger.info(f"工作流 {workflow_id} 完成")
            
        except Exception as e:
            # 工作流失败
            current_step = workflow_status[workflow_id]["current_step"]
            update_step_progress(current_step, "failed", 0.0, str(e))
            workflow_status[workflow_id]["status"] = "failed"
            workflow_status[workflow_id]["error"] = str(e)
            workflow_status[workflow_id]["end_time"] = datetime.now().isoformat()
            
            logger.error(f"工作流 {workflow_id} 失败: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"工作流执行异常: {str(e)}")

def convert_slides_to_scripts(slides_data):
    """将slides_metadata转换为scripts_metadata格式"""
    scripts_data = {
        "project_info": slides_data.get("project_info", {}),
        "scripts": []
    }
    
    slides = slides_data.get("slides", [])
    for i, slide in enumerate(slides):
        script = {
            "script_id": f"script_{i+1:03d}",
            "slide_index": i,
            "slide_number": slide.get("slide_number", i + 1),
            "slide_id": slide.get("id", f"slide_{i+1}"),
            "title": slide.get("title", ""),
            "content": slide.get("remark", ""),
            "script_content": slide.get("remark", ""),
            "text": slide.get("remark", ""),
            "duration": slide.get("duration", 3.0),
            "image_file": slide.get("image_file", f"slide_{i+1:03d}.png")
        }
        scripts_data["scripts"].append(script)
    
    return scripts_data

async def update_config_internal(config: WorkflowConfig):
    """内部配置更新函数"""
    try:
        # 更新应用配置
        app_config = load_app_config()
        
        app_config.update({
            "video_resolution": config.video['resolution'],
            "video_fps": config.video['fps'],
            "video_bitrate": config.video['video_bitrate'],
            "include_subtitles": config.video['include_subtitles'],
            "background_color": config.video['background_color'],
            "subtitle_font_family": config.subtitle['font_family'],
            "subtitle_font_size": config.subtitle['font_size'],
            "subtitle_font_color": config.subtitle['font_color'],
            "subtitle_background_color": config.subtitle['background_color'],
            "subtitle_position": config.subtitle['position'],
            "subtitle_enabled": config.subtitle['enabled'],
            # 新增优化配置
            "max_chars_per_line": config.subtitle.get('max_chars_per_line', 26),
            "enable_adaptive_font": config.subtitle.get('enable_adaptive_font', True),
            "enable_semantic_split": config.subtitle.get('enable_semantic_split', True),
            "enable_ai_optimization": config.subtitle.get('enable_ai_optimization', False)
        })
        
        save_app_config(app_config)
        
        # 注意：不再更新tts_config.json，统一使用app_config.json作为主配置
        # 这避免了配置文件之间的不一致问题
            
    except Exception as e:
        raise Exception(f"配置更新失败: {str(e)}")

@bp.route('/status/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """获取工作流状态"""
    try:
        if workflow_id not in workflow_status:
            return jsonify({"success": False, "message": "工作流不存在"}), 404
        
        return jsonify({"success": True, "workflow": workflow_status[workflow_id]})
        
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@bp.route('/projects', methods=['GET'])
def list_projects():
    """列出所有项目 - 单机版本返回当前工作空间信息"""
    try:
        # 使用当前目录下的output目录
        output_dir = Path("output")
        if not output_dir.exists():
            return jsonify({"success": True, "projects": []})
        
        projects = []
        
        # 单机版本：检查output目录本身是否有项目内容
        slides_metadata_path = output_dir / "slides" / "slides_metadata.json"
        ppt_data_path = output_dir / "ppt_data.json"
        workspace_path = output_dir / "workspace.json"
        
        # 检查是否存在项目数据
        project_data = None
        project_name = "current_workspace"
        project_title = "当前工作空间"
        
        if slides_metadata_path.exists():
            with open(slides_metadata_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                project_name = project_data.get("project_name", "current_workspace")
                project_title = project_data.get("project_info", {}).get("title", "当前工作空间")
        elif ppt_data_path.exists():
            with open(ppt_data_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                project_title = project_data.get("title", "当前工作空间")
        elif workspace_path.exists():
            with open(workspace_path, 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)
                project_title = workspace_data.get("title", "当前工作空间")
        
        if project_data or workspace_path.exists():
            # 检查是否有最终视频
            final_dir = output_dir / "final"
            final_videos = []
            if final_dir.exists():
                for video_file in final_dir.glob("*.mp4"):
                    final_videos.append({
                        "filename": video_file.name,
                        "size": video_file.stat().st_size,
                        "created": datetime.fromtimestamp(video_file.stat().st_ctime).isoformat()
                    })
            
            projects.append({
                "name": project_name,
                "title": project_title,
                "created": datetime.fromtimestamp(output_dir.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(output_dir.stat().st_mtime).isoformat(),
                "slide_count": len(project_data.get("slides", [])) if project_data else 0,
                "final_videos": final_videos
            })
        
        return jsonify({"success": True, "projects": projects})
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        return jsonify({"success": False, "message": f"获取项目列表失败: {str(e)}"}), 500

@bp.route('/download/<project_name>/<filename>', methods=['GET'])
def download_video(project_name, filename):
    """下载视频文件"""
    try:
        # 单机版本：直接从当前目录下的output/final目录下载
        video_path = Path("output") / "final" / filename
        if not video_path.exists():
            return jsonify({"success": False, "message": "视频文件不存在"}), 404
        
        return send_file(
            str(video_path),
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return jsonify({"success": False, "message": f"下载失败: {str(e)}"}), 500

