"""
增强的工作流执行器 - 支持断点续传和智能跳过
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

# 确保可以导入本地模块
flask_backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(flask_backend_dir))

from core.workflow_persistence import (
    WorkflowPersistenceManager, WorkflowExecution, 
    StepStatus, WorkflowStatus
)
from core.step01_ppt_parser import PPTParser
from core.step01_pptist_importer import PPTistImporter
from core.step02_tts_generator import TTSGenerator
from core.step03_video_generator import VideoGenerator
from core.step04_subtitle_generator import SubtitleGenerator
from core.step05_final_merger import FFmpegFinalMerger
from utils.logger import get_logger
from utils.file_manager import FileManager

class EnhancedWorkflowExecutor:
    """增强的工作流执行器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        self.persistence_manager = WorkflowPersistenceManager(self.project_dir)
        
        # 步骤执行器映射
        self.step_executors = {
            "step01_data_preparation": self._execute_data_preparation,
            "step01b_ai_content_optimization": self._execute_ai_content_optimization,  # 新增AI内容优化步骤
            "step02_tts_generation": self._execute_tts_generation,
            "step03_video_generation": self._execute_video_generation,
            "step04_subtitle_generation": self._execute_subtitle_generation,
            "step05_final_merge": self._execute_final_merge
        }
    
    async def start_workflow(self, project_name: str, config: Optional[Dict[str, Any]] = None,
                           force_restart: bool = False,
                           progress_callback: Optional[Callable] = None) -> WorkflowExecution:
        """启动工作流（支持断点续传）"""
        
        # 检查是否有未完成的执行记录
        if not force_restart:
            latest_execution = self.persistence_manager.get_latest_execution(project_name)
            if latest_execution and self.persistence_manager.can_resume_workflow(latest_execution):
                self.logger.info(f"发现未完成的工作流，从断点继续执行: {latest_execution.execution_id}")
                return await self._resume_workflow(latest_execution, progress_callback)
        
        # 创建新的执行记录
        execution = self.persistence_manager.create_new_execution(project_name, config)
        execution.workflow_status = WorkflowStatus.RUNNING
        self.persistence_manager.save_execution(execution)
        
        return await self._execute_workflow(execution, progress_callback)
    
    async def resume_workflow(self, execution_id: str, 
                            progress_callback: Optional[Callable] = None) -> Optional[WorkflowExecution]:
        """恢复指定的工作流执行"""
        execution = self.persistence_manager.load_execution(execution_id)
        if not execution:
            self.logger.error(f"未找到执行记录: {execution_id}")
            return None
        
        if not self.persistence_manager.can_resume_workflow(execution):
            self.logger.error(f"工作流不能恢复: {execution.workflow_status.value}")
            return None
        
        return await self._resume_workflow(execution, progress_callback)
    
    async def _resume_workflow(self, execution: WorkflowExecution, 
                             progress_callback: Optional[Callable] = None) -> WorkflowExecution:
        """恢复工作流执行"""
        execution.workflow_status = WorkflowStatus.RUNNING
        self.persistence_manager.save_execution(execution)
        
        return await self._execute_workflow(execution, progress_callback)
    
    async def _execute_workflow(self, execution: WorkflowExecution,
                              progress_callback: Optional[Callable] = None) -> WorkflowExecution:
        """执行工作流"""
        try:
            self.logger.info(f"开始执行工作流: {execution.execution_id}")
            
            while True:
                # 获取下一个待执行步骤
                next_step = self.persistence_manager.get_next_pending_step(execution)
                if not next_step:
                    break
                
                # 确保next_step不为None
                if next_step is None:
                    break
                
                # 检查是否可以跳过
                can_skip, skip_reason = self.persistence_manager.check_step_can_skip(next_step, execution)
                
                if can_skip:
                    self.logger.info(f"跳过步骤 {next_step}: {skip_reason}")
                    self.persistence_manager.update_step_status(
                        execution, next_step, StepStatus.SKIPPED, 100.0
                    )
                    
                    if progress_callback:
                        await progress_callback(execution)
                    continue
                
                # 执行步骤
                self.logger.info(f"执行步骤: {next_step}")
                self.persistence_manager.update_step_status(
                    execution, next_step, StepStatus.RUNNING, 0.0
                )
                
                if progress_callback:
                    await progress_callback(execution)
                
                try:
                    # 创建步骤特定的进度回调
                    def step_progress_callback(progress: float):
                        # next_step在此处已确保不为None
                        if next_step is not None:
                            self.persistence_manager.update_step_status(
                                execution, next_step, StepStatus.RUNNING, progress
                            )
                        if progress_callback:
                            asyncio.create_task(progress_callback(execution))
                    
                    # 执行步骤
                    step_executor = self.step_executors.get(next_step)
                    if not step_executor:
                        raise Exception(f"未找到步骤执行器: {next_step}")
                    
                    output_files = await step_executor(execution, step_progress_callback)
                    
                    # 标记步骤完成
                    self.persistence_manager.update_step_status(
                        execution, next_step, StepStatus.COMPLETED, 100.0,
                        output_files=output_files
                    )
                    
                    self.logger.info(f"步骤 {next_step} 执行完成")
                    
                except Exception as e:
                    error_message = f"步骤 {next_step} 执行失败: {str(e)}"
                    self.logger.error(error_message, exc_info=True)
                    
                    self.persistence_manager.update_step_status(
                        execution, next_step, StepStatus.FAILED, 0.0, error_message
                    )
                    
                    # 标记整个工作流失败
                    self.persistence_manager.mark_workflow_failed(execution, error_message)
                    
                    if progress_callback:
                        await progress_callback(execution)
                    
                    return execution
                
                if progress_callback:
                    await progress_callback(execution)
            
            # 所有步骤完成
            self.persistence_manager.mark_workflow_completed(execution)
            self.logger.info(f"工作流执行完成: {execution.execution_id}")
            
            if progress_callback:
                await progress_callback(execution)
            
            return execution
            
        except Exception as e:
            error_message = f"工作流执行失败: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            self.persistence_manager.mark_workflow_failed(execution, error_message)
            
            if progress_callback:
                await progress_callback(execution)
            
            return execution
    
    async def _execute_data_preparation(self, execution: WorkflowExecution, 
                                      progress_callback: Callable) -> List[str]:
        """执行数据准备步骤"""
        # 优先检查slides_metadata.json，如果不存在则检查ppt_data.json
        slides_metadata_path = self.project_dir / "slides" / "slides_metadata.json"
        ppt_data_path = self.project_dir / "ppt_data.json"
        
        slides_data = None
        
        if slides_metadata_path.exists():
            # 使用slides_metadata.json
            self.logger.info("使用slides_metadata.json文件")
            import json
            with open(slides_metadata_path, 'r', encoding='utf-8') as f:
                slides_data = json.load(f)
        elif ppt_data_path.exists():
            # 使用ppt_data.json
            self.logger.info("使用ppt_data.json文件")
            import json
            with open(ppt_data_path, 'r', encoding='utf-8') as f:
                ppt_data = json.load(f)
            
            # 将PPTist格式转换为标准格式
            self.logger.info("将ppt_data.json转换为标准slides_metadata.json格式")
            slides_data = {
                "slides": [],
                "total_slides": len(ppt_data.get("slides", [])),
                "generated_at": datetime.now().isoformat()
            }
            
            for i, slide in enumerate(ppt_data.get("slides", []), 1):
                # 从PPTist content JSON中提取remark文本
                import json
                import re
                content_str = slide.get("content", "{}")
                try:
                    content_json = json.loads(content_str)
                    raw_remark = content_json.get("remark", "")
                    # 使用正则表达式去除HTML标签，提取纯文本
                    clean_remark = re.sub(r'<[^>]+>', '', raw_remark) if raw_remark else ""
                except:
                    clean_remark = ""
                
                standard_slide = {
                    "slide_number": i,
                    "title": f"幻灯片 {i}",
                    "image_file": slide.get("image", f"slide_{i:03d}.jpg"),  # 转换image字段为image_file
                    "notes": clean_remark,  # 使用提取的文本内容
                    "remark": clean_remark  # 使用提取的文本内容
                }
                slides_data["slides"].append(standard_slide)
            
            # 保存转换后的标准格式数据
            self.file_manager.save_slides_metadata(slides_data)
        else:
            raise Exception("找不到slides_metadata.json或ppt_data.json文件")
        
        progress_callback(20.0)
        
        progress_callback(60.0)
        
        # 转换为scripts格式并保存
        scripts_data = {
            "scripts": [
                {
                    "slide_number": slide["slide_number"],
                    "script_content": slide.get("notes", slide.get("remark", "")),
                    "word_count": len(slide.get("notes", slide.get("remark", ""))),
                    "estimated_duration": max(3.0, len(slide.get("notes", slide.get("remark", ""))) * 0.1)
                }
                for slide in slides_data.get("slides", [])
            ],
            "total_scripts": len(slides_data.get("slides", [])),
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存scripts_metadata.json
        self.file_manager.save_scripts_metadata(scripts_data)
        
        progress_callback(100.0)
        
        return ["scripts/scripts_metadata.json"]
    
    async def _execute_ai_content_optimization(self, execution: WorkflowExecution,
                                             progress_callback: Callable) -> List[str]:
        """执行AI内容优化步骤（可选）"""
        try:
            # 检查是否启用AI内容优化 - 默认启用
            config = execution.config or {}
            ai_optimization_enabled = config.get("ai_content_optimization", {}).get("enabled", True)  # 默认启用
            
            if not ai_optimization_enabled:
                self.logger.info("AI内容优化已被配置为禁用，跳过该步骤")
                progress_callback(100.0)
                return ["scripts/scripts_metadata.json"]  # 返回原始文件
            
            # 读取原始scripts数据
            scripts_data = self.file_manager.load_scripts_metadata()
            if not scripts_data:
                raise Exception("scripts_metadata.json文件不存在")
            
            progress_callback(20.0)
            
            # 加载AI配置
            ai_config = None
            try:
                from core.subtitle_config_loader import SmartSubtitleConfigLoader
                # 修正配置目录路径 - 配置文件在flask_backend/config_data目录
                config_dir = Path(__file__).parent.parent / "config_data"
                config_loader = SmartSubtitleConfigLoader(config_dir)
                if hasattr(config_loader, 'load_ai_config'):
                    ai_config = config_loader.load_ai_config()  # type: ignore
                else:
                    self.logger.warning("SmartSubtitleConfigLoader不支持load_ai_config方法")
                    ai_config = None
                
                if not ai_config or not ai_config.get("api_key"):
                    self.logger.warning("AI配置不可用，跳过AI内容优化")
                    progress_callback(100.0)
                    return ["scripts/scripts_metadata.json"]
                
            except Exception as e:
                self.logger.warning(f"加载AI配置失败: {e}")
                progress_callback(100.0)
                return ["scripts/scripts_metadata.json"]
            
            # 检查是否为测试环境，如果API密钥是测试密钥则跳过AI调用
            if ai_config and ai_config.get("api_key", "").startswith("test-"):
                self.logger.info("检测到测试API密钥，跳过AI内容优化")
                progress_callback(100.0)
                return ["scripts/scripts_metadata.json"]
            
            progress_callback(40.0)
            
            # 创建AI内容优化器
            from core.ai_content_optimizer import AIContentOptimizer
            optimizer = AIContentOptimizer(self.project_dir, ai_config)
            
            progress_callback(60.0)
            
            # 执行AI内容优化 - 添加超时保护
            try:
                self.logger.info("开始执行AI内容优化")
                
                # 设置超时时间为5分钟
                optimized_data = await asyncio.wait_for(
                    optimizer.optimize_scripts_content(scripts_data),
                    timeout=300  # 5分钟超时
                )
                
                # 保存优化后的scripts数据
                optimized_filename = "scripts_optimized_metadata.json"
                self.file_manager.save_scripts_metadata(optimized_data, filename=optimized_filename)
                
                progress_callback(100.0)
                
                self.logger.info("AI内容优化完成")
                return [f"scripts/{optimized_filename}"]
                
            except asyncio.TimeoutError:
                self.logger.warning("AI内容优化超时，使用原始数据")
                progress_callback(100.0)
                return ["scripts/scripts_metadata.json"]
            
        except Exception as e:
            self.logger.error(f"AI内容优化失败: {e}")
            # 失败时返回原始文件
            return ["scripts/scripts_metadata.json"]
    
    async def _execute_tts_generation(self, execution: WorkflowExecution,
                                    progress_callback: Callable) -> List[str]:
        """执行TTS生成步骤"""
        # 读取scripts数据
        scripts_data = self.file_manager.load_scripts_metadata()
        if not scripts_data:
            raise Exception("scripts_metadata.json文件不存在")
        
        # 创建TTS生成器
        tts_generator = TTSGenerator(self.project_dir)
        
        # 执行TTS生成
        result = await tts_generator.generate_audio(
            scripts_data=scripts_data,
            progress_callback=lambda p: progress_callback(p)
        )
        
        if not result.get("generation_completed"):
            raise Exception("TTS生成失败")
        
        # 返回输出文件列表
        output_files = ["audio/audio_metadata.json"]
        audio_files = result.get("audio_files", [])
        output_files.extend([f["audio_file"] for f in audio_files])
        
        return output_files
    
    async def _execute_video_generation(self, execution: WorkflowExecution,
                                      progress_callback: Callable) -> List[str]:
        """执行视频生成步骤"""
        # 读取需要的数据
        slides_data = self.file_manager.load_slides_metadata()
        audio_data = self.file_manager.load_audio_metadata()
        
        if not slides_data or not audio_data:
            raise Exception("缺少必要的输入数据")
        
        # 创建视频生成器
        video_generator = VideoGenerator(self.project_dir)
        
        # 执行视频生成
        result = await video_generator.generate_video_clips(
            slides_data=slides_data,
            audio_data=audio_data,
            progress_callback=lambda p: progress_callback(p)
        )
        
        if not result.get("generation_completed"):
            raise Exception("视频生成失败")
        
        # 返回输出文件列表
        output_files = ["video_clips/video_metadata.json"]
        video_clips = result.get("video_clips", [])
        output_files.extend([f["video_file"] for f in video_clips])
        
        return output_files
    
    async def _execute_subtitle_generation(self, execution: WorkflowExecution,
                                         progress_callback: Callable) -> List[str]:
        """执行字幕生成步骤"""
        # 读取需要的数据
        scripts_data = self.file_manager.load_scripts_metadata()
        audio_data = self.file_manager.load_audio_metadata()
        
        if not scripts_data or not audio_data:
            raise Exception("缺少必要的输入数据")
        
        # 从配置中获取高级功能设置
        config = execution.config or {}
        advanced_features = config.get("advanced_features", {})
        
        # 创建字幕生成器，支持增强模式和帧同步
        use_enhanced = advanced_features.get("enhanced_subtitles", False)
        enable_frame_sync = advanced_features.get("frame_sync_optimization", True)
        
        subtitle_generator = SubtitleGenerator(
            self.project_dir, 
            use_enhanced=use_enhanced,
            enable_frame_sync=enable_frame_sync
        )
        
        self.logger.info(f"字幕生成配置: 增强模式={use_enhanced}, 帧同步={enable_frame_sync}")
        
        # 执行字幕生成
        result = await subtitle_generator.generate_subtitles(
            scripts_data=scripts_data,
            audio_data=audio_data,
            progress_callback=lambda p: progress_callback(p)
        )
        
        if not result.get("subtitle_generation_completed"):
            raise Exception("字幕生成失败")
        
        # 记录帧同步报告
        if result.get("frame_sync_applied"):
            sync_report = result.get("frame_sync_report", {})
            sync_stats = sync_report.get("sync_statistics", {})
            self.logger.info(f"🎨 视频帧同步已应用: 同步率{sync_stats.get('sync_accuracy', 0):.1f}%, "
                           f"帧对齐{sync_stats.get('frame_aligned_segments', 0)}/{sync_stats.get('total_segments', 0)}")
        
        # 返回输出文件列表
        output_files = []
        subtitle_files = result.get("subtitle_files", [])
        output_files.extend(subtitle_files)
        
        return output_files
    
    async def _execute_final_merge(self, execution: WorkflowExecution,
                                 progress_callback: Callable) -> List[str]:
        """执行最终合并步骤"""
        # 读取需要的数据
        video_data = self.file_manager.load_video_metadata()
        audio_data = self.file_manager.load_audio_metadata()
        
        if not video_data or not audio_data:
            raise Exception("缺少必要的输入数据")
        
        # 尝试读取字幕数据
        subtitle_data = None
        try:
            subtitle_data = self.file_manager.load_subtitles_metadata()
            if subtitle_data:
                self.logger.info("找到字幕数据，将包含在最终视频中")
            else:
                self.logger.info("未找到字幕数据")
        except Exception as e:
            self.logger.warning(f"读取字幕数据失败: {e}")
        
        # 创建最终合并器
        final_merger = FFmpegFinalMerger(self.project_dir)
        
        # 执行最终合并 - 移除await，因为merge_final_video不是async方法
        result = final_merger.merge_final_video(
            video_data=video_data,
            audio_data=audio_data,
            subtitle_data=subtitle_data,  # 传递字幕数据
            progress_callback=lambda p: progress_callback(p)
        )
        
        if not result.get("success"):
            raise Exception(f"最终合并失败: {result.get('error', '未知错误')}")
        
        return [result.get("output_file", "final/final_video.mp4")]
    
    def get_execution_history(self, project_name: str) -> List[WorkflowExecution]:
        """获取项目的执行历史"""
        return self.persistence_manager.list_project_executions(project_name)
    
    def delete_execution(self, execution_id: str) -> bool:
        """删除执行记录"""
        execution_file = self.persistence_manager.workflow_dir / f"{execution_id}.json"
        if execution_file.exists():
            execution_file.unlink()
            return True
        return False
