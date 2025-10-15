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
from core.step02_tts_generator import TTSGenerator
from core.step03_video_generator import VideoGenerator
from core.step04_subtitle_generator import SubtitleGenerator
from core.step05_final_merger import FFmpegFinalMerger
from app.utils.logger import get_logger
from app.utils.file_manager import FileManager

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
                # 从PPTist slide中正确提取remark文本
                import re
                import json as json_lib
                
                # PPTist数据结构：remark在content字段的JSON字符串中
                raw_remark = ""
                content_str = slide.get("content", "")
                if content_str:
                    try:
                        # 解析content中的JSON
                        content_data = json_lib.loads(content_str)
                        raw_remark = content_data.get("remark", "")
                        self.logger.debug(f"第{i}页原始remark: {raw_remark[:100]}...")
                    except (json_lib.JSONDecodeError, ValueError) as e:
                        self.logger.warning(f"第{i}页content解析失败: {e}")
                        raw_remark = ""
                
                # 处理PPTist的多个<p>标签格式，保留手动分行
                if raw_remark:
                    # 1. 将连续的</p><p>标签对转换为换行符（这是PPTist的手动分行格式）
                    clean_remark = re.sub(r'</p>\s*<p[^>]*>', '\n', raw_remark, flags=re.IGNORECASE)
                    # 2. 将各种形式的<br>标签转换为换行符
                    clean_remark = re.sub(r'<br\s*/?>', '\n', clean_remark, flags=re.IGNORECASE)
                    # 3. 去除所有剩余的HTML标签
                    clean_remark = re.sub(r'<[^>]+>', '', clean_remark)
                    # 4. 清理多余的空白字符，但保留换行符
                    clean_remark = re.sub(r'[ \t]+', ' ', clean_remark)  # 将多个空格/制表符合并为单个空格
                    clean_remark = re.sub(r' *\n *', '\n', clean_remark)  # 清理换行符前后的空格
                    clean_remark = clean_remark.strip()  # 去除首尾空白
                    self.logger.debug(f"第{i}页处理后文本: {clean_remark}")
                else:
                    clean_remark = ""
                    self.logger.debug(f"第{i}页无remark内容")
                
                standard_slide = {
                    "slide_id": i,
                    "text": clean_remark,  # 使用text字段作为主要文本内容
                    "duration": max(3.0, len(clean_remark) * 0.1),
                    "background": slide.get("background", {}),
                    "elements": slide.get("elements", [])
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
                    "script_id": slide["slide_id"],
                    "slide_id": slide["slide_id"],
                    "text": slide.get("text", ""),  # 使用text字段匹配字幕生成器
                    "duration": slide.get("duration", 3.0)
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
        
        # 详细的错误检查
        if not slides_data:
            self.logger.error("无法加载slides_metadata.json文件")
            raise Exception("缺少幻灯片元数据，请先执行数据准备步骤")
        
        if not audio_data:
            self.logger.error("无法加载audio_metadata.json文件")
            raise Exception("缺少音频元数据，请先执行音频生成步骤")
        
        self.logger.info(f"成功加载: slides={len(slides_data.get('slides', []))}张, audio={len(audio_data.get('audio_files', []))}个文件")
        
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

