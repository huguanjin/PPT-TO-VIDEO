"""
步骤5: 最终视频合并器 - 基于FFmpeg
使用FFmpeg合并视频片段、音频文件和字幕，生成最终视频
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import shutil

from utils.file_manager import FileManager
from utils.logger import get_logger

class FFmpegFinalMerger:
    """基于FFmpeg的最终视频合并器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # FFmpeg配置
        self.ffmpeg_config = {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "audio_bitrate": "128k",
            "video_bitrate": "2000k",
            "preset": "medium",
            "crf": "23",
            "pixel_format": "yuv420p",
            "movflags": "+faststart"
        }
        
        # 检查FFmpeg可用性
        self.ffmpeg_available = self._check_ffmpeg_availability()
        if not self.ffmpeg_available:
            self.logger.warning("FFmpeg不可用，将使用MoviePy作为备选方案")
    
    def _check_ffmpeg_availability(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def merge_final_video(self, 
                         video_data: Dict[str, Any], 
                         audio_data: Dict[str, Any],
                         subtitle_data: Optional[Dict[str, Any]] = None,
                         config: Optional[Dict[str, Any]] = None,
                         progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """
        合并最终视频
        
        Args:
            video_data: 视频数据字典
            audio_data: 音频数据字典
            subtitle_data: 字幕数据字典（可选）
            config: 输出配置
            progress_callback: 进度回调函数
            
        Returns:
            合并结果字典
        """
        try:
            self.logger.info("开始使用FFmpeg合并最终视频")
            
            if not self.ffmpeg_available:
                self.logger.error("FFmpeg不可用，无法进行合并")
                return {"success": False, "error": "FFmpeg不可用"}
            
            # 创建输出目录
            self.file_manager.create_directory_structure()
            
            # 准备合并参数
            merge_params = self._prepare_merge_parameters(
                video_data, audio_data, subtitle_data, config
            )
            
            if progress_callback:
                progress_callback(10)
            
            # 执行FFmpeg合并
            result = self._execute_ffmpeg_merge(merge_params, progress_callback)
            
            if result["success"]:
                # 生成合并元数据
                merge_metadata = self._generate_merge_metadata(
                    video_data, audio_data, subtitle_data, result
                )
                
                # 保存元数据
                self.file_manager.save_merge_metadata(merge_metadata)
                
                self.logger.info(f"视频合并完成: {result['output_file']}")
                
                if progress_callback:
                    progress_callback(100)
                
                return {
                    "success": True,
                    "output_file": result["output_file"],
                    "file_size": result["file_size"],
                    "duration": result["duration"],
                    "metadata": merge_metadata
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"视频合并失败: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _prepare_merge_parameters(self, 
                                 video_data: Dict[str, Any], 
                                 audio_data: Dict[str, Any],
                                 subtitle_data: Optional[Dict[str, Any]] = None,
                                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备FFmpeg合并参数"""
        
        # 获取视频文件列表
        video_files = []
        for video_info in video_data.get("video_files", []):
            video_path = self.file_manager.video_clips_dir / video_info["video_file"]
            if video_path.exists():
                video_files.append(str(video_path))
        
        # 获取音频文件列表
        audio_files = []
        for audio_info in audio_data.get("audio_files", []):
            audio_path = self.file_manager.audio_dir / audio_info["audio_file"]
            if audio_path.exists():
                audio_files.append(str(audio_path))
        
        # 获取字幕文件
        subtitle_file = None
        if subtitle_data and subtitle_data.get("merged_subtitle_file"):
            subtitle_path = self.file_manager.subtitles_dir / subtitle_data["merged_subtitle_file"]
            if subtitle_path.exists():
                subtitle_file = str(subtitle_path)
        
        # 输出文件配置
        output_config = config or {}
        output_format = output_config.get("output_format", "MP4 (推荐)")
        
        if "MP4" in output_format:
            output_extension = ".mp4"
        elif "AVI" in output_format:
            output_extension = ".avi"
        elif "MOV" in output_format:
            output_extension = ".mov"
        else:
            output_extension = ".mp4"
        
        output_filename = f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}{output_extension}"
        output_path = self.file_manager.final_dir / output_filename
        
        return {
            "video_files": video_files,
            "audio_files": audio_files,
            "subtitle_file": subtitle_file,
            "output_path": str(output_path),
            "output_config": output_config,
            "total_duration": video_data.get("total_duration_seconds", 0)
        }
    
    def _execute_ffmpeg_merge(self, params: Dict[str, Any], 
                            progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """执行FFmpeg合并操作"""
        
        try:
            # 第一步：合并视频片段
            if progress_callback:
                progress_callback(20)
            
            concat_video_path = self._concatenate_videos(params["video_files"])
            if not concat_video_path:
                return {"success": False, "error": "视频片段合并失败"}
            
            # 第二步：合并音频文件
            if progress_callback:
                progress_callback(40)
            
            concat_audio_path = self._concatenate_audios(params["audio_files"])
            if not concat_audio_path:
                return {"success": False, "error": "音频文件合并失败"}
            
            # 第三步：合并视频和音频
            if progress_callback:
                progress_callback(60)
            
            av_merge_path = self._merge_audio_video(concat_video_path, concat_audio_path)
            if not av_merge_path:
                return {"success": False, "error": "音视频合并失败"}
            
            # 第四步：添加字幕（如果有）
            if progress_callback:
                progress_callback(80)
            
            final_output_path = params["output_path"]
            
            if params["subtitle_file"]:
                success = self._add_subtitles(av_merge_path, params["subtitle_file"], final_output_path)
            else:
                # 没有字幕，直接移动文件
                shutil.move(av_merge_path, final_output_path)
                success = True
            
            if not success:
                return {"success": False, "error": "字幕添加失败"}
            
            # 清理临时文件
            self._cleanup_temp_files([concat_video_path, concat_audio_path, av_merge_path])
            
            # 获取输出文件信息
            output_path = Path(final_output_path)
            file_size = output_path.stat().st_size if output_path.exists() else 0
            duration = params.get("total_duration", 0)
            
            return {
                "success": True,
                "output_file": output_path.name,
                "output_path": str(output_path),
                "file_size": file_size,
                "duration": duration
            }
            
        except Exception as e:
            self.logger.error(f"FFmpeg合并执行失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _concatenate_videos(self, video_files: List[str]) -> Optional[str]:
        """合并视频片段"""
        if not video_files:
            return None
        
        if len(video_files) == 1:
            return video_files[0]
        
        try:
            # 创建FFmpeg concat文件列表
            concat_list_path = self.file_manager.temp_dir / "video_concat_list.txt"
            concat_list_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for video_file in video_files:
                    # 使用相对路径避免路径问题
                    relative_path = os.path.relpath(video_file, concat_list_path.parent)
                    f.write(f"file '{relative_path}'\n")
            
            # 输出路径
            output_path = self.file_manager.temp_dir / "concatenated_video.mp4"
            
            # FFmpeg命令
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list_path),
                '-c', 'copy',
                str(output_path)
            ]
            
            self.logger.info(f"执行视频合并: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=str(concat_list_path.parent)
            )
            
            if result.returncode == 0 and output_path.exists():
                self.logger.info("视频片段合并成功")
                return str(output_path)
            else:
                self.logger.error(f"视频合并失败: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"视频合并异常: {str(e)}")
            return None
    
    def _concatenate_audios(self, audio_files: List[str]) -> Optional[str]:
        """合并音频文件"""
        if not audio_files:
            return None
        
        if len(audio_files) == 1:
            return audio_files[0]
        
        try:
            # 创建FFmpeg concat文件列表
            concat_list_path = self.file_manager.temp_dir / "audio_concat_list.txt"
            
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for audio_file in audio_files:
                    relative_path = os.path.relpath(audio_file, concat_list_path.parent)
                    f.write(f"file '{relative_path}'\n")
            
            # 输出路径
            output_path = self.file_manager.temp_dir / "concatenated_audio.wav"
            
            # FFmpeg命令
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list_path),
                '-c', 'copy',
                str(output_path)
            ]
            
            self.logger.info(f"执行音频合并: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3分钟超时
                cwd=str(concat_list_path.parent)
            )
            
            if result.returncode == 0 and output_path.exists():
                self.logger.info("音频文件合并成功")
                return str(output_path)
            else:
                self.logger.error(f"音频合并失败: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"音频合并异常: {str(e)}")
            return None
    
    def _merge_audio_video(self, video_path: str, audio_path: str) -> Optional[str]:
        """合并音频和视频"""
        try:
            output_path = self.file_manager.temp_dir / "merged_av.mp4"
            
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', self.ffmpeg_config["video_codec"],
                '-c:a', self.ffmpeg_config["audio_codec"],
                '-b:a', self.ffmpeg_config["audio_bitrate"],
                '-b:v', self.ffmpeg_config["video_bitrate"],
                '-preset', self.ffmpeg_config["preset"],
                '-crf', self.ffmpeg_config["crf"],
                '-pix_fmt', self.ffmpeg_config["pixel_format"],
                '-movflags', self.ffmpeg_config["movflags"],
                '-shortest',  # 以较短的流为准
                str(output_path)
            ]
            
            self.logger.info(f"执行音视频合并: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0 and output_path.exists():
                self.logger.info("音视频合并成功")
                return str(output_path)
            else:
                self.logger.error(f"音视频合并失败: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"音视频合并异常: {str(e)}")
            return None
    
    def _add_subtitles(self, video_path: str, subtitle_path: str, output_path: str) -> bool:
        """添加字幕到视频"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', f"subtitles='{subtitle_path}'",
                '-c:a', 'copy',
                output_path
            ]
            
            self.logger.info(f"执行字幕添加: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                self.logger.info("字幕添加成功")
                return True
            else:
                self.logger.error(f"字幕添加失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"字幕添加异常: {str(e)}")
            return False
    
    def _cleanup_temp_files(self, temp_files: List[str]):
        """清理临时文件"""
        for temp_file in temp_files:
            if temp_file and Path(temp_file).exists():
                try:
                    Path(temp_file).unlink()
                    self.logger.debug(f"清理临时文件: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"清理临时文件失败 {temp_file}: {str(e)}")
    
    def _generate_merge_metadata(self, 
                                video_data: Dict[str, Any], 
                                audio_data: Dict[str, Any],
                                subtitle_data: Optional[Dict[str, Any]],
                                merge_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成合并元数据"""
        
        return {
            "merge_completed": True,
            "merge_timestamp": datetime.now().isoformat(),
            "merge_method": "ffmpeg",
            "output_file": merge_result["output_file"],
            "output_path": merge_result["output_path"],
            "file_size_bytes": merge_result["file_size"],
            "duration_seconds": merge_result["duration"],
            "ffmpeg_config": self.ffmpeg_config,
            "input_summary": {
                "video_files_count": len(video_data.get("video_files", [])),
                "audio_files_count": len(audio_data.get("audio_files", [])),
                "has_subtitles": subtitle_data is not None,
                "total_duration": video_data.get("total_duration_seconds", 0)
            },
            "processing_steps": [
                "视频片段合并",
                "音频文件合并", 
                "音视频同步合并",
                "字幕添加" if subtitle_data else "无字幕处理"
            ]
        }
    
    def get_ffmpeg_info(self) -> Dict[str, Any]:
        """获取FFmpeg信息"""
        if not self.ffmpeg_available:
            return {"available": False, "error": "FFmpeg不可用"}
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            version_info = result.stdout.split('\n')[0] if result.stdout else "未知版本"
            
            return {
                "available": True,
                "version": version_info,
                "config": self.ffmpeg_config
            }
            
        except Exception as e:
            return {"available": False, "error": str(e)}

# 为了向后兼容，创建一个别名
FinalMerger = FFmpegFinalMerger
