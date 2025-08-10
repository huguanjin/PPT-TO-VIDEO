"""
步骤3: PPT视频片段生成器
基于PPT图片和音频时长生成视频片段
"""
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging

from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

from utils.logger import get_logger
from utils.file_manager import FileManager

class VideoGenerator:
    """视频片段生成器"""
    
    def __init__(self, project_dir: Path, resolution: str = "1920x1080", fps: int = 24):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # 解析分辨率
        self.width, self.height = map(int, resolution.split('x'))
        self.fps = fps
        
        # 视频配置
        self.video_config = {
            "resolution": resolution,
            "width": self.width,
            "height": self.height,
            "fps": fps,
            "codec": "mp4v"  # 使用mp4v编码器，兼容性更好
        }
    
    async def generate_video_clips(self, slides_data: Dict[str, Any], audio_data: Dict[str, Any], 
                                 progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """
        生成所有PPT页面的视频片段
        
        Args:
            slides_data: 幻灯片数据
            audio_data: 音频数据
            progress_callback: 进度回调函数
            
        Returns:
            视频数据字典
        """
        try:
            self.logger.info("开始生成视频片段")
            
            # 确保视频目录存在
            self.file_manager.video_clips_dir.mkdir(parents=True, exist_ok=True)
            
            slides = slides_data.get("slides", [])
            audio_files = audio_data.get("audio_files", [])
            total_slides = len(slides)
            
            # 创建音频文件映射
            audio_map = {audio["slide_number"]: audio for audio in audio_files}
            
            video_data = {
                "total_video_clips": total_slides,
                "generation_completed": False,
                "generation_timestamp": datetime.now().isoformat(),
                "video_config": self.video_config.copy(),
                "video_clips": [],
                "total_duration_seconds": 0.0
            }
            
            for i, slide in enumerate(slides):
                if progress_callback:
                    progress = int((i / total_slides) * 100)
                    progress_callback(progress)
                
                slide_number = slide["slide_number"]
                self.logger.info(f"生成第 {slide_number} 页视频片段")
                
                # 获取对应的音频信息
                audio_info = audio_map.get(slide_number)
                if not audio_info:
                    self.logger.warning(f"未找到第 {slide_number} 页的音频信息，使用默认时长")
                    duration = 3.0
                else:
                    duration = audio_info["duration_seconds"]
                
                # 生成单个视频片段
                video_info = await self._generate_single_video_clip(slide, duration)
                video_data["video_clips"].append(video_info)
                
                # 模拟处理延迟
                await asyncio.sleep(0.3)
            
            # 计算总时长
            video_data["total_duration_seconds"] = sum(clip["duration_seconds"] for clip in video_data["video_clips"])
            video_data["generation_completed"] = True
            
            # 保存视频元数据
            self.file_manager.save_video_metadata(video_data)
            
            if progress_callback:
                progress_callback(100)
            
            self.logger.info(f"视频片段生成完成，总时长: {video_data['total_duration_seconds']:.2f} 秒")
            return video_data
            
        except Exception as e:
            self.logger.error(f"视频片段生成失败: {e}", exc_info=True)
            raise
    
    async def _generate_single_video_clip(self, slide: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """
        生成单个PPT页面的视频片段
        
        Args:
            slide: 幻灯片数据
            duration: 视频时长（秒）
            
        Returns:
            视频信息字典
        """
        slide_number = slide["slide_number"]
        slide_title = slide["title"]
        
        # 视频文件路径
        video_filename = f"clip_{slide_number:03d}.mp4"
        video_path = self.file_manager.video_clips_dir / video_filename
        
        # 幻灯片图片路径
        slide_image_path = self.file_manager.slides_dir / slide["image_file"]
        
        try:
            # 生成视频片段
            await self._create_video_from_image(slide_image_path, video_path, duration, slide_title, slide_number)
            
            # 获取视频文件信息
            file_size = video_path.stat().st_size
            
            self.logger.info(f"视频片段生成成功: {video_path}, 时长: {duration:.2f}秒")
            
            video_info = {
                "clip_id": f"{slide_number:03d}",
                "slide_number": slide_number,
                "video_file": video_filename,
                "duration_seconds": duration,
                "file_size_bytes": file_size,
                "resolution": f"{self.width}x{self.height}",
                "fps": self.fps,
                "generation_timestamp": datetime.now().isoformat(),
                "slide_title": slide_title,
                "source_image": slide["image_file"]
            }
            
            return video_info
            
        except Exception as e:
            self.logger.error(f"生成视频片段失败 {video_filename}: {e}")
            raise
    
    async def _create_video_from_image(self, image_path: Path, output_path: Path, 
                                     duration: float, title: str, slide_number: int):
        """
        从图片创建视频片段
        
        Args:
            image_path: 输入图片路径
            output_path: 输出视频路径
            duration: 视频时长
            title: 幻灯片标题
            slide_number: 幻灯片编号
        """
        try:
            # 计算总帧数
            total_frames = int(duration * self.fps)
            
            # 初始化视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                str(output_path), 
                fourcc, 
                self.fps, 
                (self.width, self.height)
            )
            
            if not video_writer.isOpened():
                raise Exception("无法创建视频写入器")
            
            # 加载或创建幻灯片图片
            if image_path.exists():
                # 加载真实的幻灯片图片
                image = cv2.imread(str(image_path))
                if image is None:
                    # 如果图片加载失败，创建占位符
                    image = self._create_placeholder_image(title, slide_number)
                else:
                    # 调整图片尺寸
                    image = cv2.resize(image, (self.width, self.height))
            else:
                # 创建占位符图片
                image = self._create_placeholder_image(title, slide_number)
            
            # 写入所有帧（静态图片）
            for frame_num in range(total_frames):
                # 可以在这里添加动画效果，现在保持静态
                frame = image.copy()
                
                # 可选：添加进度指示器
                if total_frames > self.fps:  # 只有视频长度超过1秒才显示进度
                    progress = frame_num / total_frames
                    self._add_progress_bar(frame, progress)
                
                video_writer.write(frame)
            
            # 释放资源
            video_writer.release()
            
            self.logger.info(f"视频创建完成: {output_path}, 帧数: {total_frames}")
            
        except Exception as e:
            self.logger.error(f"创建视频失败: {e}")
            raise
    
    def _create_placeholder_image(self, title: str, slide_number: int) -> np.ndarray:
        """
        创建占位符图片
        
        Args:
            title: 幻灯片标题
            slide_number: 幻灯片编号
            
        Returns:
            OpenCV格式的图片数组
        """
        # 创建白色背景
        image = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        
        # 添加边框
        cv2.rectangle(image, (50, 50), (self.width-50, self.height-50), (200, 200, 200), 3)
        
        # 添加页面编号
        page_text = f"第 {slide_number} 页"
        cv2.putText(image, page_text, (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (100, 100, 100), 3)
        
        # 添加标题（处理中文显示问题）
        title_y = 250
        if title and len(title) < 50:  # 避免标题过长
            # 简单处理：对于中文标题，使用英文替代显示
            display_title = f"Title: {title}" if any('\u4e00' <= char <= '\u9fff' for char in title) else title
            cv2.putText(image, display_title[:30], (100, title_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 50), 2)
        
        # 添加logo或水印
        logo_text = "PPT-to-Video"
        cv2.putText(image, logo_text, (100, self.height - 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (150, 150, 150), 2)
        
        return image
    
    def _add_progress_bar(self, frame: np.ndarray, progress: float):
        """
        在帧上添加进度条
        
        Args:
            frame: 视频帧
            progress: 进度（0-1）
        """
        # 进度条参数
        bar_height = 8
        bar_width = self.width - 200
        bar_x = 100
        bar_y = self.height - 50
        
        # 绘制进度条背景
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (200, 200, 200), -1)
        
        # 绘制进度
        progress_width = int(bar_width * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (100, 200, 100), -1)
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的视频格式
        
        Returns:
            支持的格式列表
        """
        return ["mp4", "avi", "mov", "mkv"]
    
    def estimate_file_size(self, duration: float, quality: str = "medium") -> int:
        """
        估算视频文件大小
        
        Args:
            duration: 视频时长（秒）
            quality: 质量等级
            
        Returns:
            估算的文件大小（字节）
        """
        # 简单的文件大小估算（基于分辨率、帧率和时长）
        pixels_per_frame = self.width * self.height
        
        # 不同质量的压缩比
        compression_ratios = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.8
        }
        
        ratio = compression_ratios.get(quality, 0.3)
        bytes_per_frame = pixels_per_frame * 3 * ratio  # RGB 3通道
        total_frames = duration * self.fps
        
        return int(total_frames * bytes_per_frame)
