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
import time
import platform

try:
    import cv2
except ImportError:
    cv2 = None

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
    
    def merge_videos(self, 
                    scripts_data: Dict[str, Any],
                    audio_data: Dict[str, Any], 
                    video_data: Dict[str, Any],
                    subtitles_data: Optional[Dict[str, Any]] = None,
                    config: Optional[Dict[str, Any]] = None,
                    progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        视频合并适配器方法 - 兼容UI调用接口
        
        Args:
            scripts_data: 脚本数据字典（暂不使用）
            audio_data: 音频数据字典
            video_data: 视频数据字典
            subtitles_data: 字幕数据字典（可选）
            config: 输出配置
            progress_callback: 进度回调函数
            
        Returns:
            合并结果字典
        """
        # 适配进度回调函数格式
        adapted_progress_callback = None
        if progress_callback:
            def adapted_callback(progress: int):
                # 将int进度转换为字符串描述和float进度
                step_name = f"处理进度 {progress}%"
                progress_float = progress / 100.0
                progress_callback(step_name, progress_float)
            adapted_progress_callback = adapted_callback
        
        # 调用实际的合并方法
        return self.merge_final_video(
            video_data=video_data,
            audio_data=audio_data,
            subtitle_data=subtitles_data,
            config=config,
            progress_callback=adapted_progress_callback
        )
    
    def _prepare_merge_parameters(self, 
                                 video_data: Dict[str, Any], 
                                 audio_data: Dict[str, Any],
                                 subtitle_data: Optional[Dict[str, Any]] = None,
                                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备FFmpeg合并参数"""
        
        # 获取视频文件列表
        video_files = []
        for video_info in video_data.get("video_clips", []):
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
        
        # 检查配置是否启用字幕
        output_config = config or {}
        include_subtitles = output_config.get("include_subtitles", True)  # 默认包含字幕
        
        if include_subtitles and subtitle_data:
            # 检查多种可能的字幕文件字段
            subtitle_filename = (
                subtitle_data.get("merged_subtitle_file") or
                subtitle_data.get("combined_subtitle_info", {}).get("combined_subtitle_file") or
                subtitle_data.get("combined_subtitle_file")
            )
            
            if subtitle_filename:
                subtitle_path = self.file_manager.subtitles_dir / subtitle_filename
                if subtitle_path.exists():
                    subtitle_file = str(subtitle_path)
                    self.logger.info(f"找到字幕文件: {subtitle_file}")
                else:
                    self.logger.warning(f"字幕文件不存在: {subtitle_path}")
            else:
                self.logger.warning("未找到字幕文件名配置")
        elif not include_subtitles:
            self.logger.info("配置中禁用了字幕，跳过字幕处理")
        else:
            self.logger.info("未提供字幕数据，跳过字幕处理")
        
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
                if not success:
                    # 字幕添加失败，使用无字幕版本作为备用
                    self.logger.warning("字幕添加失败，使用无字幕版本")
                    try:
                        shutil.move(av_merge_path, final_output_path)
                        success = True
                    except Exception as e:
                        self.logger.error(f"移动无字幕视频失败: {e}")
                        return {"success": False, "error": f"视频处理失败: {e}"}
            else:
                # 没有字幕，直接移动文件
                try:
                    shutil.move(av_merge_path, final_output_path)
                    success = True
                except Exception as e:
                    self.logger.error(f"移动视频文件失败: {e}")
                    return {"success": False, "error": f"视频处理失败: {e}"}
            
            # 验证最终输出
            output_path = Path(final_output_path)
            if not output_path.exists() or output_path.stat().st_size < 10000:
                return {"success": False, "error": "最终视频文件无效或过小"}
            
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
                    # 使用绝对路径，并确保路径格式正确
                    abs_path = os.path.abspath(video_file)
                    # 在Windows上，需要使用正斜杠或转义反斜杠
                    abs_path = abs_path.replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")
            
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
                timeout=300  # 5分钟超时
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
                    # 使用绝对路径，并确保路径格式正确
                    abs_path = os.path.abspath(audio_file)
                    # 在Windows上，需要使用正斜杠或转义反斜杠
                    abs_path = abs_path.replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")
            
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
                timeout=180  # 3分钟超时
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
            
            self.logger.info(f"音视频合并返回码: {result.returncode}")
            
            if result.returncode == 0:
                # 等待文件系统同步
                import time
                time.sleep(1)
                
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    self.logger.info(f"音视频合并成功，文件大小: {file_size} bytes")
                    return str(output_path)
                else:
                    self.logger.error(f"音视频合并返回成功但输出文件不存在: {output_path}")
                    self.logger.error(f"FFmpeg stderr: {result.stderr}")
                    return None
            else:
                self.logger.error(f"音视频合并失败，返回码: {result.returncode}")
                self.logger.error(f"FFmpeg stderr: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"音视频合并异常: {str(e)}")
            return None
    
    def _add_subtitles(self, video_path: str, subtitle_path: str, output_path: str) -> bool:
        """
        添加字幕到视频 - 借鉴 testfile 的稳定实现
        """
        try:
            video_path_obj = Path(video_path)
            subtitle_path_obj = Path(subtitle_path)
            output_path_obj = Path(output_path)
            
            # 检查输入文件
            if not video_path_obj.exists():
                self.logger.error(f"输入视频文件不存在: {video_path}")
                return False
            
            if not subtitle_path_obj.exists():
                self.logger.warning(f"字幕文件不存在: {subtitle_path}")
                # 没有字幕时，直接复制视频
                return self._copy_video_without_subtitles(video_path_obj, output_path_obj)
            
            # 获取视频分辨率
            video_info = self._get_video_resolution(video_path_obj)
            if video_info:
                target_width, target_height = video_info['width'], video_info['height']
                self.logger.info(f"检测到视频分辨率: {target_width}x{target_height}")
            else:
                target_width, target_height = 1920, 1080
                self.logger.warning("无法检测视频分辨率，使用默认: 1920x1080")
            
            # 获取平台适配的字体
            font_name = self._get_platform_font()
            
            # 构造字幕滤镜 - 使用简单可靠的方式
            # 尝试使用相对路径避免Windows路径问题
            try:
                subtitle_path_rel = subtitle_path_obj.relative_to(self.project_dir)
                subtitle_path_fixed = str(subtitle_path_rel).replace('\\', '/')
            except ValueError:
                # 如果无法获取相对路径，使用绝对路径
                subtitle_path_fixed = str(subtitle_path_obj).replace('\\', '/')
            
            vf_filter = (
                f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
                f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,"
                f"subtitles={subtitle_path_fixed}:force_style='"
                f"FontSize=20,FontName={font_name},"
                f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,OutlineWidth=1,"
                f"ShadowColour=&H80000000,BorderStyle=1'"
            )
            
            # 构造 FFmpeg 命令 - 借鉴 testfile 方式
            # 由于设置了cwd，需要使用相对路径
            try:
                video_path_rel = video_path_obj.relative_to(self.project_dir)
                output_path_rel = output_path_obj.relative_to(self.project_dir)
            except ValueError:
                # 如果无法获取相对路径，使用绝对路径
                video_path_rel = video_path_obj
                output_path_rel = output_path_obj
            
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path_rel),
                '-vf', vf_filter,  # 保持字符串类型，不编码
                '-c:a', 'copy',
                str(output_path_rel)
            ]
            
            self.logger.info(f"开始字幕合并，输出: {output_path_obj.name}")
            
            # 使用 testfile 的进程管理方式
            start_time = time.time()
            
            self.logger.info(f"执行FFmpeg命令: {' '.join(ffmpeg_cmd)}")
            
            try:
                # 直接使用 subprocess.run，更简单可靠
                result = subprocess.run(
                    ffmpeg_cmd,
                    cwd=str(self.project_dir),  # 重要：在项目目录中执行
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                elapsed_time = time.time() - start_time
                
                # 简化的成功判断：借鉴 testfile - 只检查返回码
                if result.returncode == 0:
                    # 验证输出文件
                    if output_path_obj.exists() and output_path_obj.stat().st_size > 10000:
                        self.logger.info(f"字幕添加成功！耗时: {elapsed_time:.2f}秒, 大小: {output_path_obj.stat().st_size} bytes")
                        return True
                    else:
                        self.logger.error("FFmpeg返回成功但输出文件无效")
                        return False
                else:
                    # 记录错误但不失败，因为可能是字幕格式问题
                    self.logger.warning(f"FFmpeg执行警告，返回码: {result.returncode}")
                    self.logger.warning(f"FFmpeg stdout: {result.stdout}")
                    self.logger.warning(f"FFmpeg stderr: {result.stderr}")
                    
                    # 检查是否有输出文件生成
                    if output_path_obj.exists() and output_path_obj.stat().st_size > 10000:
                        self.logger.info(f"尽管有警告，字幕添加仍然成功！耗时: {elapsed_time:.2f}秒")
                        return True
                    
                    return False
                    
            except subprocess.TimeoutExpired:
                self.logger.error("FFmpeg执行超时")
                return False
            except Exception as e:
                self.logger.error(f"进程执行异常: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"字幕添加方法异常: {e}")
            return False
    
    def _copy_video_without_subtitles(self, source_path: Path, dest_path: Path) -> bool:
        """复制视频文件作为备用方案"""
        try:
            shutil.copy2(source_path, dest_path)
            self.logger.info(f"已复制视频文件（无字幕）: {dest_path}")
            return True
        except Exception as e:
            self.logger.error(f"复制视频文件失败: {e}")
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
    
    def _get_video_resolution(self, video_path: Path) -> Optional[Dict[str, int]]:
        """获取视频分辨率 - 借鉴 testfile 方式"""
        try:
            # 方法1: 使用 ffprobe
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                '-show_streams', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        width = stream.get('width')
                        height = stream.get('height')
                        if width and height:
                            return {'width': int(width), 'height': int(height)}
        except Exception as e:
            self.logger.debug(f"ffprobe方式获取分辨率失败: {e}")
        
        try:
            # 方法2: 使用 opencv (如果可用)
            import cv2
            video = cv2.VideoCapture(str(video_path))
            if video.isOpened():
                width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                video.release()
                if width > 0 and height > 0:
                    return {'width': width, 'height': height}
        except Exception as e:
            self.logger.debug(f"opencv方式获取分辨率失败: {e}")
        
        return None
    
    def _get_platform_font(self) -> str:
        """获取平台适配的字体名称 - 借鉴 testfile 方式"""
        system = platform.system()
        
        if system == 'Linux':
            return 'NotoSansCJK-Regular'
        elif system == 'Darwin':  # macOS
            return 'Arial Unicode MS'
        else:  # Windows
            return 'Microsoft YaHei'

# 为了向后兼容，创建一个别名
FinalMerger = FFmpegFinalMerger
