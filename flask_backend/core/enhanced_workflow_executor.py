"""
增强的工作流执行器 - 支持断点续传和智能跳过
支持工作流前清理和完成后归档
"""
import asyncio
import sys
import shutil
import json
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
from app.utils.logger import get_logger, clear_log_directory, reset_logger_cleared_state
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
        
        # 🔧 历史目录配置
        self.history_dir = flask_backend_dir / "history"
    
    def _cleanup_before_workflow(self) -> Dict[str, Any]:
        """
        工作流执行前清理历史数据
        
        清理内容:
        - audios/ 目录下的所有音频文件  
        - video_clips/ 目录下的所有视频片段
        - subtitles/ 目录下的所有字幕文件
        - final/ 目录下的所有最终视频
        - temp/ 目录下的临时文件
        - workflow_history/ 目录下的历史记录
        - logs/ 目录下的所有日志文件
        - 各种 *_metadata.json 文件（除了 ppt_data.json 和 workspace.json）
        
        保留内容:
        - slides/ 目录（幻灯片图片）
        - ppt_data.json（源PPT数据）
        - workspace.json（工作区配置）
        
        Returns:
            清理结果统计
        """
        self.logger.info("🧹 开始清理历史工作流数据...")
        
        cleanup_stats = {
            "deleted_files": 0,
            "deleted_dirs": 0,
            "freed_space_mb": 0.0,
            "errors": []
        }
        
        # 🔧 清理日志目录 - 确保每次工作流只保留最新日志
        logs_dir = self.project_dir / "logs"
        if logs_dir.exists():
            try:
                clear_log_directory(logs_dir)
                reset_logger_cleared_state()
                self.logger.info("✅ 清理日志目录完成")
            except Exception as e:
                cleanup_stats["errors"].append(f"清理日志目录失败: {e}")
        
        # 需要清理的目录 - 只清理实际使用的目录
        dirs_to_clean = [
            self.project_dir / "audios",       # TTS生成的音频
            self.project_dir / "video_clips",  # 视频片段
            self.project_dir / "subtitles",    # 字幕文件
            self.project_dir / "temp",         # 临时文件
            self.project_dir / "workflow_history",  # 工作流历史
        ]
        
        # 清理目录内容
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                try:
                    for item in dir_path.iterdir():
                        try:
                            if item.is_file():
                                size = item.stat().st_size
                                item.unlink()
                                cleanup_stats["deleted_files"] += 1
                                cleanup_stats["freed_space_mb"] += size / (1024 * 1024)
                            elif item.is_dir():
                                shutil.rmtree(item)
                                cleanup_stats["deleted_dirs"] += 1
                        except Exception as e:
                            cleanup_stats["errors"].append(f"{item}: {e}")
                    self.logger.info(f"✅ 清理目录: {dir_path.name}")
                except Exception as e:
                    cleanup_stats["errors"].append(f"清理目录 {dir_path} 失败: {e}")
        
        # 清理 final/ 目录（删除所有历史视频文件）
        final_dir = self.project_dir / "final"
        if final_dir.exists():
            try:
                for video_file in final_dir.glob("*.mp4"):
                    try:
                        size = video_file.stat().st_size
                        video_file.unlink()
                        cleanup_stats["deleted_files"] += 1
                        cleanup_stats["freed_space_mb"] += size / (1024 * 1024)
                    except Exception as e:
                        cleanup_stats["errors"].append(f"删除视频 {video_file}: {e}")
                self.logger.info(f"✅ 清理 final 目录中的历史视频")
            except Exception as e:
                cleanup_stats["errors"].append(f"清理 final 目录失败: {e}")
        
        # 清理中间元数据文件（保留 ppt_data.json 和 workspace.json）
        metadata_files_to_delete = [
            "audio_metadata.json",
            "video_metadata.json", 
            "subtitles_metadata.json",
            "scripts_metadata.json",
            "merge_metadata.json",
            "slides_metadata.json",  # 这个会重新生成
            "speech_scripts.json",   # TTS前的讲话稿提取结果
        ]
        
        for filename in metadata_files_to_delete:
            file_path = self.project_dir / filename
            if file_path.exists():
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    cleanup_stats["deleted_files"] += 1
                    cleanup_stats["freed_space_mb"] += size / (1024 * 1024)
                    self.logger.info(f"✅ 删除元数据: {filename}")
                except Exception as e:
                    cleanup_stats["errors"].append(f"删除 {filename}: {e}")
        
        # 清理 slides 目录下的 slides_metadata.json
        slides_metadata = self.project_dir / "slides" / "slides_metadata.json"
        if slides_metadata.exists():
            try:
                slides_metadata.unlink()
                cleanup_stats["deleted_files"] += 1
            except Exception as e:
                cleanup_stats["errors"].append(f"删除 slides_metadata.json: {e}")
        
        self.logger.info(f"🧹 清理完成: 删除 {cleanup_stats['deleted_files']} 个文件, "
                        f"{cleanup_stats['deleted_dirs']} 个目录, "
                        f"释放 {cleanup_stats['freed_space_mb']:.2f} MB")
        
        if cleanup_stats["errors"]:
            self.logger.warning(f"⚠️ 清理过程中有 {len(cleanup_stats['errors'])} 个错误")
        
        return cleanup_stats
    
    def _archive_completed_workflow(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """
        工作流完成后归档结果到 history 目录
        
        只归档核心文件:
        - 最终视频文件 (final_video.mp4)
        - ppt_data.json（源数据）
        - 执行元数据 (archive_metadata.json)
        
        归档目录结构:
        history/{user_id}/{project_name}_{timestamp}/
            ├── final_video.mp4
            ├── ppt_data.json
            └── archive_metadata.json
        
        注意: 工作流执行完成后会保留所有中间结果文件便于排查问题，
        只有在重新执行工作流时才会清理上一次的历史记录。
        
        Args:
            execution: 工作流执行记录
            
        Returns:
            归档结果
        """
        self.logger.info("📦 开始归档工作流结果...")
        
        archive_result = {
            "success": False,
            "archive_path": None,
            "archived_files": [],
            "errors": []
        }
        
        try:
            # 从项目目录路径提取用户ID（目录名就是用户ID）
            user_id = self.project_dir.name
            
            # 生成归档目录名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = execution.project_name or "unnamed"
            # 清理项目名中的特殊字符
            safe_project_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
            archive_name = f"{safe_project_name}_{timestamp}"
            
            # 创建归档目录
            archive_dir = self.history_dir / user_id / archive_name
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"📁 归档目录: {archive_dir}")
            
            # 1. 复制最终视频
            final_dir = self.project_dir / "final"
            if final_dir.exists():
                video_files = list(final_dir.glob("*.mp4"))
                if video_files:
                    # 取最新的视频文件
                    latest_video = max(video_files, key=lambda f: f.stat().st_mtime)
                    dest_video = archive_dir / "final_video.mp4"
                    shutil.copy2(latest_video, dest_video)
                    archive_result["archived_files"].append(str(dest_video))
                    self.logger.info(f"✅ 归档视频: {latest_video.name}")
            
            # 2. 复制 ppt_data.json
            ppt_data_path = self.project_dir / "ppt_data.json"
            if ppt_data_path.exists():
                dest_ppt = archive_dir / "ppt_data.json"
                shutil.copy2(ppt_data_path, dest_ppt)
                archive_result["archived_files"].append(str(dest_ppt))
                self.logger.info("✅ 归档 ppt_data.json")
            
            # 注意：不再归档 subtitles/ 和 slides/ 目录
            # 这些文件保留在用户工作目录中便于排查问题
            # 只有重新执行工作流时才会被清理
            
            # 3. 创建归档元数据
            # 解析时间字符串为 datetime 对象用于计算持续时间
            start_dt = None
            end_dt = None
            try:
                if execution.start_time:
                    start_dt = datetime.fromisoformat(execution.start_time)
                if execution.end_time:
                    end_dt = datetime.fromisoformat(execution.end_time)
            except (ValueError, TypeError):
                pass
            
            archive_metadata = {
                "project_name": project_name,
                "user_id": user_id,
                "archived_at": datetime.now().isoformat(),
                "execution_id": execution.execution_id,
                "workflow_status": execution.workflow_status.value if execution.workflow_status else "unknown",
                "started_at": execution.start_time,  # 已经是 ISO 格式字符串
                "completed_at": execution.end_time,  # 已经是 ISO 格式字符串
                "total_duration_seconds": (end_dt - start_dt).total_seconds() 
                    if start_dt and end_dt else None,
                "archived_files": [str(f) for f in archive_result["archived_files"]],
                "source_dir": str(self.project_dir)
            }
            
            metadata_path = archive_dir / "archive_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(archive_metadata, f, indent=2, ensure_ascii=False)
            archive_result["archived_files"].append(str(metadata_path))
            
            archive_result["success"] = True
            archive_result["archive_path"] = str(archive_dir)
            
            self.logger.info(f"📦 归档完成: {len(archive_result['archived_files'])} 个文件 -> {archive_dir}")
            
            # 注意：归档后不再清理用户工作目录
            # 保留所有中间结果文件便于后续排查问题
            # 只有在重新执行工作流时才会清理上一次的历史记录
            
        except Exception as e:
            error_msg = f"归档失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            archive_result["errors"].append(error_msg)
        
        return archive_result
    
    async def start_workflow(self, project_name: str, config: Optional[Dict[str, Any]] = None,
                           force_restart: bool = False,
                           progress_callback: Optional[Callable] = None) -> WorkflowExecution:
        """启动工作流（支持断点续传）"""
        
        # 🔧 新增：每次启动工作流前清理历史数据
        # 这确保每次执行都是全新的，只保留 ppt_data.json 作为起点
        self.logger.info("🚀 准备启动新工作流，先清理历史数据...")
        cleanup_result = self._cleanup_before_workflow()
        self.logger.info(f"🧹 清理完成: {cleanup_result}")
        
        # 不再检查断点续传，每次都是全新执行
        # 因为每个用户只有一个工作目录，每次只能执行一个工作流
        
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
            
            # 🔧 新增：工作流成功完成后归档结果到 history 目录
            self.logger.info("📦 开始归档工作流结果...")
            archive_result = self._archive_completed_workflow(execution)
            if archive_result["success"]:
                self.logger.info(f"✅ 归档成功: {archive_result['archive_path']}")
                # 将归档路径保存到执行记录中
                execution.archive_path = archive_result["archive_path"]
            else:
                self.logger.warning(f"⚠️ 归档失败: {archive_result['errors']}")
            
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
                # 从PPTist slide中提取讲话稿文本
                import re
                
                # PPTist数据结构：
                # - remark: PPT备注内容（HTML格式）- 作为讲话稿来源
                # - script: PPT页面的脚本内容（非讲话稿）
                # 使用remark字段作为讲话稿，按换行符分段
                raw_remark = slide.get("remark", "") or ""
                
                if raw_remark:
                    # 处理PPTist的HTML格式，提取文本并保留分段信息
                    # 1. 将连续的</p><p>标签对转换为换行符（PPTist的手动分行格式）
                    clean_text = re.sub(r'</p>\s*<p[^>]*>', '\n', raw_remark, flags=re.IGNORECASE)
                    # 2. 将各种形式的<br>标签转换为换行符
                    clean_text = re.sub(r'<br\s*/?>', '\n', clean_text, flags=re.IGNORECASE)
                    # 3. 去除所有剩余的HTML标签
                    clean_text = re.sub(r'<[^>]+>', '', clean_text)
                    # 4. HTML实体解码
                    import html
                    clean_text = html.unescape(clean_text)
                    # 5. 清理多余的空白字符，但保留换行符
                    clean_text = re.sub(r'[ \t]+', ' ', clean_text)
                    clean_text = re.sub(r' *\n *', '\n', clean_text)
                    # 6. 移除空行
                    clean_text = re.sub(r'\n+', '\n', clean_text)
                    clean_text = clean_text.strip()
                    
                    self.logger.info(f"第{i}页备注内容: \"{clean_text[:80]}{'...' if len(clean_text) > 80 else ''}\"")
                else:
                    clean_text = ""
                    self.logger.info(f"第{i}页无备注内容")
                
                standard_slide = {
                    "slide_id": i,
                    "text": clean_text,  # 使用text字段存储清理后的备注内容
                    "duration": max(3.0, len(clean_text) * 0.1) if clean_text else 3.0,
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
        
        return ["scripts_metadata.json"]  # 保存在项目根目录
    
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

