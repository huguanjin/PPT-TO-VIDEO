"""
工作流API接口
处理视频生成工作流
"""
import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app

# 添加项目根目录到Python路径
# 添加flask_backend目录到Python路径
flask_backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(flask_backend_root))

try:
    from core.step02_tts_generator import TTSGenerator  # type: ignore
    from core.step03_video_generator import VideoGenerator  # type: ignore
    from core.step04_subtitle_generator import SubtitleGenerator  # type: ignore
    from core.step05_final_merger import FFmpegFinalMerger  # type: ignore
    from core.enhanced_workflow_executor import EnhancedWorkflowExecutor, WorkflowExecution  # type: ignore
    from core.workflow_persistence import StepStatus  # type: ignore
    from app.utils.task_manager import TaskManager  # type: ignore
    from app.utils.logger import get_logger  # type: ignore
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    # 提供模拟类
    class TTSGenerator:
        def __init__(self, project_name):
            self.project_name = project_name
    
    class VideoGenerator:
        def __init__(self, project_name):
            self.project_name = project_name
    
    class SubtitleGenerator:
        def __init__(self, project_name):
            self.project_name = project_name
    
    class EnhancedWorkflowExecutor:
        def __init__(self, project_dir):
            self.project_dir = project_dir
        
        async def start_workflow(self, project_name, config=None, progress_callback=None):
            """Fallback implementation that raises an error"""
            raise ImportError("Enhanced workflow executor not available - core modules failed to import")
    
    class WorkflowExecution:
        def __init__(self, project_name):
            self.project_name = project_name
    
    class FFmpegFinalMerger:
        def __init__(self, project_name):
            self.project_name = project_name
    
    class TaskManager:
        def __init__(self, base_dir):
            self.base_dir = base_dir
    
    def get_logger(name):
        import logging
        return logging.getLogger(name)

bp = Blueprint('workflow', __name__)
logger = get_logger(__name__)

@bp.route('/start', methods=['POST'])
def start_workflow():
    """
    启动视频生成工作流
    
    接收项目配置，启动完整的视频生成流程
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        project_name = data.get('project_name')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称不能为空'
            }), 400
        
        # 工作流配置
        workflow_config = data.get('config', {})
        
        # 创建任务ID
        task_id = f"workflow_{project_name}_{int(time.time())}"
        
        # 这里应该启动后台任务处理工作流
        # 暂时返回任务已启动的响应
        logger.info(f"启动视频生成工作流: {project_name}")
        
        return jsonify({
            'success': True,
            'message': '视频生成工作流已启动',
            'data': {
                'task_id': task_id,
                'project_name': project_name,
                'status': 'processing',
                'workflow_steps': [
                    'TTS音频生成',
                    '字幕生成',
                    '视频合成',
                    '最终合并'
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"启动工作流失败: {e}")
        return jsonify({
            'success': False,
            'message': f'启动工作流失败: {str(e)}'
        }), 500

@bp.route('/status/<task_id>', methods=['GET'])
def get_workflow_status(task_id):
    """获取工作流处理状态"""
    try:
        # 从任务状态管理器获取真实状态
        if task_id in task_statuses:
            task_status = task_statuses[task_id]
            
            # 构造符合前端期望的工作流状态格式
            workflow_data = {
                'workflow_id': task_id,
                'status': task_status['status'],
                'progress': task_status['progress'],
                'project_name': task_status.get('project_name', ''),
                'current_step': task_status.get('current_step', 1),
                'total_steps': task_status.get('total_steps', 5),
                'steps': task_status.get('steps', []),
                'final_video': task_status.get('result', {}).get('video_file', '') if task_status.get('result') else '',
                'error': task_status.get('message', '') if task_status['status'] == 'failed' else ''
            }
            
            return jsonify({
                'success': True,
                'workflow': workflow_data  # 前端期待的字段名
            })
        else:
            # 任务不存在，可能是服务器重启导致的，返回未找到状态
            logger.warning(f"任务 {task_id} 不存在，可能是服务器重启导致的")
            return jsonify({
                'success': True,
                'workflow': {
                    'workflow_id': task_id,
                    'status': 'failed',  # 改为failed状态，让前端停止轮询
                    'progress': 0,
                    'project_name': '',
                    'current_step': 0,
                    'total_steps': 5,
                    'steps': [],
                    'final_video': '',
                    'error': '任务不存在或服务器已重启，请重新启动工作流'
                }
            })
        
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/result/<task_id>', methods=['GET'])
def get_workflow_result(task_id):
    """获取工作流处理结果"""
    try:
        # 模拟结果返回
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'completed',
                'progress': 100,
                'result': {
                    'video_file': '/output/project_name/final_video.mp4',
                    'duration': '5:30',
                    'file_size': '25.6MB',
                    'resolution': '1920x1080',
                    'completed_at': datetime.now().isoformat()
                },
                'download_url': f'/api/workflow/download/{task_id}'
            }
        })
        
    except Exception as e:
        logger.error(f"获取工作流结果失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/cleanup', methods=['POST'])
def cleanup_workflows():
    """清理已完成或失败的工作流"""
    try:
        global task_statuses
        
        # 获取要清理的状态类型
        data = request.get_json() or {}
        cleanup_types = data.get('types', ['completed', 'failed'])
        
        original_count = len(task_statuses)
        
        # 清理指定状态的任务
        task_statuses = {
            task_id: status for task_id, status in task_statuses.items()
            if status.get('status') not in cleanup_types
        }
        
        # 保存更新后的状态
        save_task_statuses()
        
        cleaned_count = original_count - len(task_statuses)
        
        logger.info(f"清理了 {cleaned_count} 个任务状态")
        
        return jsonify({
            'success': True,
            'message': f'成功清理了 {cleaned_count} 个任务',
            'data': {
                'cleaned_count': cleaned_count,
                'remaining_count': len(task_statuses)
            }
        })
        
    except Exception as e:
        logger.error(f"清理工作流失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/list', methods=['GET'])
def list_workflows():
    """列出所有工作流状态"""
    try:
        # 确保加载最新状态
        load_task_statuses()
        
        return jsonify({
            'success': True,
            'data': {
                'workflows': task_statuses,
                'total_count': len(task_statuses)
            }
        })
        
    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/download/<task_id>', methods=['GET'])
def download_result(task_id):
    """下载生成的视频文件"""
    try:
        from flask import send_file
        
        # 这里应该根据task_id找到对应的视频文件
        # 暂时返回错误
        return jsonify({
            'success': False,
            'message': '文件下载功能暂未实现'
        }), 501
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/download/<project_name>/<filename>', methods=['GET'])
def download_project_file(project_name, filename):
    """下载项目文件"""
    try:
        from flask import send_file, current_app
        
        # 构建文件路径 - 单机版本：直接使用output目录
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'output'))
        file_path = output_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return jsonify({
                'success': False,
                'message': f'文件 {filename} 不存在'
            }), 404
        
        # 返回文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4' if filename.endswith('.mp4') else 'application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/config', methods=['GET'])
def get_workflow_config():
    """获取工作流配置选项"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'tts_engines': [
                    {'id': 'edge', 'name': 'Edge TTS', 'description': '微软Edge TTS引擎'},
                    {'id': 'openai', 'name': 'OpenAI TTS', 'description': 'OpenAI TTS引擎'},
                    {'id': 'azure', 'name': 'Azure TTS', 'description': 'Azure认知服务TTS'}
                ],
                'video_quality': [
                    {'id': 'hd', 'name': '高清 (1920x1080)', 'bitrate': '5000k'},
                    {'id': 'sd', 'name': '标清 (1280x720)', 'bitrate': '3000k'},
                    {'id': 'ld', 'name': '流畅 (854x480)', 'bitrate': '1500k'}
                ],
                'subtitle_styles': [
                    {'id': 'default', 'name': '默认样式'},
                    {'id': 'netflix', 'name': 'Netflix样式'},
                    {'id': 'youtube', 'name': 'YouTube样式'}
                ],
                'advanced_features': [
                    {
                        'id': 'enhanced_subtitles',
                        'name': '增强字幕生成',
                        'description': 'Netflix级字幕处理算法',
                        'default': False
                    },
                    {
                        'id': 'frame_sync_optimization',
                        'name': '🎨 视频帧同步优化',
                        'description': '毫秒级精确帧同步，提升字幕与视频的同步精度',
                        'default': True
                    },
                    {
                        'id': 'intelligent_timing',
                        'name': '智能时长优化',
                        'description': '基于语速和内容的智能字幕时长调整',
                        'default': True
                    }
                ],
                'sync_precision_levels': [
                    {'id': 'basic', 'name': '基础同步 (±100ms)', 'description': '适合一般场景'},
                    {'id': 'standard', 'name': '标准同步 (±33ms)', 'description': '适合大多数专业场景'},
                    {'id': 'high', 'name': '高精度同步 (±16ms)', 'description': '推荐，适合高质量制作'},
                    {'id': 'perfect', 'name': '帧完美同步 (±1帧)', 'description': '最高精度，适合电影级制作'}
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"获取工作流配置失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/cancel/<task_id>', methods=['POST'])
def cancel_workflow(task_id):
    """取消工作流任务"""
    try:
        # 这里应该实现任务取消逻辑
        logger.info(f"取消工作流任务: {task_id}")
        
        return jsonify({
            'success': True,
            'message': f'任务 {task_id} 已取消'
        })
        
    except Exception as e:
        logger.error(f"取消工作流任务失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/execute', methods=['POST'])
def execute_workflow():
    """执行工作流（兼容前端调用）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        project_name = data.get('project_name')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称不能为空'
            }), 400
        
        # 生成任务ID
        task_id = f"workflow_{int(time.time() * 1000)}"
        
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'output'))
        # 🔧 修复：使用项目根目录而不是output目录，确保配置文件路径正确
        # 项目根目录 = output目录的父级的父级 (flask_backend/output -> flask_backend -> 项目根)
        project_dir = output_dir.parent.parent
        logger.info(f"🔧 项目根目录设置为: {project_dir}")
        logger.info(f"🔧 输出目录: {output_dir}")
        
        if not project_dir.exists():
            return jsonify({
                'success': False,
                'message': f'项目根目录不存在: {project_dir}'
            }), 404
        
        # 检查项目数据文件 - 在output目录下
        ppt_data_file = output_dir / "ppt_data.json"
        if not ppt_data_file.exists():
            return jsonify({
                'success': False,
                'message': f'项目 {project_name} 缺少PPT数据文件: {ppt_data_file}'
            }), 400
        
        # 检查图片文件 - 在output目录下
        slides_dir = output_dir / "slides"
        if not slides_dir.exists() or not any(slides_dir.glob("*.jpg")):
            return jsonify({
                'success': False,
                'message': f'项目 {project_name} 缺少幻灯片图片文件: {slides_dir}'
            }), 400
        
        logger.info(f"启动工作流执行: {project_name}, 任务ID: {task_id}")
        
        # 启动后台任务处理工作流
        import threading
        def run_workflow():
            try:
                execute_workflow_task(project_name, task_id, project_dir, output_dir)
            except Exception as e:
                logger.error(f"工作流执行失败: {e}")
                # 更新任务状态为失败
                update_task_status(task_id, 'failed', str(e), 0, None, project_name)
        
        # 在后台线程中执行工作流
        thread = threading.Thread(target=run_workflow)
        thread.daemon = True
        thread.start()
        
        # 立即返回成功响应
        return jsonify({
            'success': True,
            'message': '工作流已启动',
            'data': {
                'task_id': task_id,
                'workflow_id': task_id,
                'project_name': project_name,
                'status': 'started'
            }
        })
        
    except Exception as e:
        logger.error(f"执行工作流失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def execute_workflow_task(project_name: str, task_id: str, project_dir: Path, output_dir: Path):
    """实际执行工作流任务 - 使用增强的工作流执行器"""
    try:
        logger.info(f"开始执行工作流任务: {project_name}")
        
        # 初始化步骤状态
        steps = [
            {'name': '数据准备', 'status': 'waiting', 'progress': 0.0, 'message': '等待开始'},
            {'name': 'AI内容优化', 'status': 'waiting', 'progress': 0.0, 'message': '等待开始'},
            {'name': 'TTS音频生成', 'status': 'waiting', 'progress': 0.0, 'message': '等待开始'},
            {'name': '视频合成', 'status': 'waiting', 'progress': 0.0, 'message': '等待开始'},
            {'name': '字幕生成', 'status': 'waiting', 'progress': 0.0, 'message': '等待开始'},
            {'name': '最终合并', 'status': 'waiting', 'progress': 0.0, 'message': '等待开始'}
        ]
        
        update_task_status(task_id, 'running', '开始处理工作流', 0, None, 
                          project_name, 1, 6, steps)
        
        # 创建增强的工作流执行器
        # 🔧 使用output目录作为工作目录，因为数据文件都在那里
        executor = EnhancedWorkflowExecutor(output_dir)
        
        # 定义进度回调函数
        async def progress_callback(execution):
            """进度回调函数"""
            current_step = execution.current_step
            if current_step:
                step_names = ['step01_data_preparation', 'step01b_ai_content_optimization', 'step02_tts_generation', 'step03_video_generation', 'step04_subtitle_generation', 'step05_final_merge']
                display_names = ['数据准备', 'AI内容优化', 'TTS音频生成', '视频合成', '字幕生成', '最终合并']
                
                # 更新所有步骤的状态，不仅仅是当前步骤
                for i, step_name in enumerate(step_names):
                    if i < len(display_names) and i < len(steps):
                        display_name = display_names[i]
                        step_result = execution.steps.get(step_name)
                        
                        if step_result:
                            # 根据步骤状态确定显示状态
                            if step_result.status == StepStatus.COMPLETED:
                                progress = 100.0
                                status = 'completed'
                                message = f'{display_name}已完成'
                            elif step_result.status == StepStatus.SKIPPED:
                                progress = 100.0
                                status = 'completed'  # 跳过的步骤也显示为完成
                                message = f'{display_name}已跳过'
                            elif step_result.status == StepStatus.RUNNING:
                                # step_result.progress可能是0-1或0-100范围，需要标准化为0-100
                                if step_result.progress <= 1.0:
                                    progress = step_result.progress * 100  # 0-1范围转换为0-100
                                else:
                                    progress = step_result.progress  # 已经是0-100范围
                                progress = min(100.0, max(0.0, progress))  # 确保在有效范围内
                                status = 'running'
                                message = step_result.error_message if step_result.error_message else f'{display_name}进行中...'
                            elif step_result.status == StepStatus.FAILED:
                                progress = 0.0
                                status = 'failed'
                                message = step_result.error_message or f'{display_name}失败'
                            else:  # PENDING
                                progress = 0.0
                                status = 'waiting'
                                message = '等待开始'
                        else:
                            progress = 0.0
                            status = 'waiting'
                            message = '等待开始'
                        
                        # 更新步骤状态
                        steps[i] = {
                            'name': display_name, 
                            'status': status,
                            'progress': progress / 100.0,  # 前端期望0-1范围
                            'message': message
                        }
                    
                # 计算整体进度和当前步骤索引
                overall_progress = int(execution.total_progress)
                current_step_index = 1  # 默认第一步
                
                # 找到当前步骤的索引用于显示
                for i, step_name in enumerate(step_names):
                    if step_name == current_step:
                        current_step_index = i + 1
                        break
                
                # 获取当前步骤的消息
                current_message = "工作流进行中..."
                if current_step and current_step in execution.steps:
                    step_result = execution.steps[current_step]
                    if step_result and step_result.error_message:
                        current_message = step_result.error_message
                    else:
                        step_index = next((i for i, name in enumerate(step_names) if name == current_step), -1)
                        if step_index >= 0 and step_index < len(display_names):
                            current_message = f'{display_names[step_index]}进行中...'
                
                update_task_status(task_id, 'running', current_message, overall_progress, None, 
                                  project_name, current_step_index, len(step_names), steps)
        
        # 运行增强的工作流
        import asyncio
        
        # 创建新的事件循环（如果当前线程没有）
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 执行完整工作流
        result_execution = loop.run_until_complete(
            executor.start_workflow(project_name, config={}, progress_callback=progress_callback)
        )
        
        if result_execution.workflow_status.value != 'completed':
            error_msg = result_execution.error_message or "工作流执行失败"
            raise Exception(f"工作流执行失败: {error_msg}")
        
        logger.info("增强工作流执行完成")
        
        # 获取最终结果
        final_video_file = project_dir / "final_video.mp4"
        subtitle_file = project_dir / "subtitles" / "combined_subtitle.srt"
        
        # 获取视频文件的相对路径
        if final_video_file.exists():
            try:
                relative_path = final_video_file.relative_to(project_dir)
                video_file_name = str(relative_path).replace('\\', '/')
            except ValueError:
                video_file_name = final_video_file.name
        else:
            video_file_name = "final_video.mp4"
        
        # 构建最终结果
        final_result = {
            'video_file': video_file_name,
            'subtitle_file': subtitle_file.name if subtitle_file.exists() else '',
            'duration': 0,  # 从执行结果中获取或计算
            'slides_count': 0  # 从执行结果中获取或计算
        }
        
        # 标记所有步骤为完成
        for i in range(len(steps)):
            steps[i]['status'] = 'completed'
            steps[i]['progress'] = 1.0
        
        update_task_status(task_id, 'completed', '视频生成完成', 100, final_result, 
                          project_name, 6, 6, steps)
        
        logger.info(f"工作流执行完成: {project_name}")
        
    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        # 更新失败状态
        steps = steps if 'steps' in locals() else []
        update_task_status(task_id, 'failed', str(e), 0, None, 
                          project_name, 1, 6, steps)


def format_time(seconds):
    """格式化时间为SRT格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def convert_slides_to_scripts(ppt_data, project_name):
    """将PPT数据转换为脚本数据格式"""
    scripts_data = {
        "project_name": project_name,
        "generated_at": datetime.now().isoformat(),
        "scripts": []
    }
    
    for slide in ppt_data.get('slides', []):
        slide_number = slide.get('id', 1)
        # 优先使用notes，其次使用remark
        text = slide.get('notes', slide.get('remark', ''))
        
        if text:
            script_info = {
                "slide_number": slide_number,
                "text": text,
                "word_count": len(text),
                "estimated_duration": max(3.0, len(text) * 0.1)
            }
            scripts_data["scripts"].append(script_info)
    
    scripts_data["total_scripts"] = len(scripts_data["scripts"])
    return scripts_data


# 任务状态管理
task_statuses = {}

def save_task_statuses():
    """保存任务状态到文件"""
    try:
        status_file = Path('output/task_status/task_statuses.json')
        status_file.parent.mkdir(exist_ok=True)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(task_statuses, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存任务状态失败: {e}")

def load_task_statuses():
    """从文件加载任务状态"""
    try:
        global task_statuses
        status_file = Path('output/task_status/task_statuses.json')
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                task_statuses = json.load(f)
        else:
            task_statuses = {}
    except Exception as e:
        logger.error(f"加载任务状态失败: {e}")
        task_statuses = {}

def update_task_status(task_id, status, message, progress, result=None, project_name='', current_step=1, total_steps=5, steps=None):
    """更新任务状态"""
    task_statuses[task_id] = {
        'status': status,
        'message': message,
        'progress': progress,
        'result': result,
        'project_name': project_name,
        'current_step': current_step,
        'total_steps': total_steps,
        'steps': steps or [],
        'updated_at': datetime.now().isoformat()
    }
    save_task_statuses()

# 启动时加载任务状态
load_task_statuses()

