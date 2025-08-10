"""
步骤1: PPT解析器
解析PPT文件，提取每页内容和备注信息
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import asyncio
import logging

from pptx import Presentation
from pptx.slide import Slide
from PIL import Image
import io

from utils.logger import get_logger
from utils.file_manager import FileManager

class PPTParser:
    """PPT解析器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
    async def parse_ppt(self, ppt_file_path: str, progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """
        解析PPT文件
        
        Args:
            ppt_file_path: PPT文件路径
            progress_callback: 进度回调函数
            
        Returns:
            解析结果字典
        """
        try:
            self.logger.info(f"开始解析PPT文件: {ppt_file_path}")
            
            # 确保必要的目录存在
            self.file_manager.create_directory_structure()
            
            # 打开PPT文件
            presentation = Presentation(ppt_file_path)
            total_slides = len(presentation.slides)
            
            self.logger.info(f"PPT总页数: {total_slides}")
            
            slides_data = {
                "total_slides": total_slides,
                "parsing_completed": False,
                "parsing_timestamp": datetime.now().isoformat(),
                "source_file": ppt_file_path,
                "slides": []
            }
            
            # 解析每一页幻灯片
            for i, slide in enumerate(presentation.slides):
                if progress_callback:
                    progress = int((i / total_slides) * 100)
                    progress_callback(progress)
                
                slide_info = await self._parse_slide(slide, i + 1)
                slides_data["slides"].append(slide_info)
                
                self.logger.info(f"解析完成第 {i + 1} 页")
                
                # 模拟异步处理
                await asyncio.sleep(0.1)
            
            slides_data["parsing_completed"] = True
            
            # 保存解析结果
            self.file_manager.save_slides_metadata(slides_data)
            
            # 保存讲话稿数据到统一的JSON文件
            scripts_data = self._generate_scripts_metadata(slides_data)
            self.file_manager.save_scripts_metadata(scripts_data)
            
            if progress_callback:
                progress_callback(100)
                
            self.logger.info("PPT解析完成")
            return slides_data
            
        except Exception as e:
            self.logger.error(f"PPT解析失败: {e}", exc_info=True)
            raise
    
    async def _parse_slide(self, slide: Slide, slide_number: int) -> Dict[str, Any]:
        """
        解析单页幻灯片
        
        Args:
            slide: 幻灯片对象
            slide_number: 幻灯片编号
            
        Returns:
            幻灯片信息字典
        """
        # 提取幻灯片标题
        title = self._extract_title(slide)
        
        # 提取备注信息
        notes = self._extract_notes(slide)
        
        # 生成幻灯片图片
        image_file = await self._save_slide_image(slide, slide_number)
        
        slide_info = {
            "slide_id": f"{slide_number:03d}",
            "slide_number": slide_number,
            "title": title,
            "image_file": image_file,
            "notes": notes,
            "notes_word_count": len(notes) if notes else 0,
            "extracted_at": datetime.now().isoformat()
        }
        
        return slide_info
    
    def _extract_title(self, slide: Slide) -> str:
        """提取幻灯片标题"""
        try:
            if hasattr(slide, 'shapes'):
                for shape in slide.shapes:
                    if hasattr(shape, 'text') and shape.text.strip():
                        # 通常第一个有文字的形状是标题
                        return shape.text.strip()
            return f"幻灯片标题"
        except Exception as e:
            self.logger.warning(f"提取标题失败: {e}")
            return "无标题"
    
    def _extract_notes(self, slide: Slide) -> Optional[str]:
        """提取幻灯片备注"""
        try:
            if hasattr(slide, 'notes_slide') and slide.notes_slide:
                notes_slide = slide.notes_slide
                if hasattr(notes_slide, 'notes_text_frame') and notes_slide.notes_text_frame:
                    notes_text = notes_slide.notes_text_frame.text.strip()
                    return notes_text if notes_text else None
            return None
        except Exception as e:
            self.logger.warning(f"提取备注失败: {e}")
            return None
    
    async def _save_slide_image(self, slide: Slide, slide_number: int) -> str:
        """
        保存幻灯片为图片
        注意: python-pptx不直接支持导出图片，这里创建占位符图片
        实际实现可能需要其他库如comtypes(Windows)或LibreOffice
        """
        image_filename = f"slide_{slide_number:03d}.png"
        image_path = self.file_manager.slides_dir / image_filename
        
        try:
            # 确保目录存在
            image_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建一个占位符图片，包含页面信息
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (1920, 1080), color='white')
            draw = ImageDraw.Draw(img)
            
            # 添加页面信息文本
            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                # 如果找不到字体，使用默认字体
                font = ImageFont.load_default()
            
            text = f"第 {slide_number} 页\nPPT Slide {slide_number}"
            
            # 计算文本位置（居中）
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (1920 - text_width) // 2
            y = (1080 - text_height) // 2
            
            # 绘制文本
            draw.text((x, y), text, fill='black', font=font)
            
            # 保存图片
            img.save(image_path)
            
            self.logger.info(f"保存幻灯片图片: {image_path}")
            
        except Exception as e:
            self.logger.error(f"保存幻灯片图片失败: {e}")
            # 即使图片生成失败，也不影响其他功能
            # 创建一个简单的空白图片
            try:
                img = Image.new('RGB', (1920, 1080), color='lightgray')
                img.save(image_path)
                self.logger.warning(f"使用简单占位符图片: {image_path}")
            except:
                pass
        
        return image_filename
    
    def _generate_scripts_metadata(self, slides_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成讲话稿元数据
        
        Args:
            slides_data: 幻灯片数据
            
        Returns:
            讲话稿元数据字典
        """
        scripts_data = {
            "total_scripts": slides_data["total_slides"],
            "extraction_completed": True,
            "extraction_timestamp": datetime.now().isoformat(),
            "total_word_count": sum(slide.get("notes_word_count", 0) for slide in slides_data["slides"]),
            "scripts": []
        }
        
        for slide in slides_data["slides"]:
            script_info = {
                "script_id": slide["slide_id"],
                "slide_number": slide["slide_number"],
                "slide_title": slide["title"],
                "script_content": slide["notes"] or "",
                "word_count": slide["notes_word_count"],
                "estimated_duration_seconds": self._estimate_speech_duration(slide["notes"]),
                "extracted_at": slide["extracted_at"]
            }
            scripts_data["scripts"].append(script_info)
        
        return scripts_data
    
    def _estimate_speech_duration(self, text: str) -> float:
        """
        估算语音时长（基于字数和平均语速）
        
        Args:
            text: 文本内容
            
        Returns:
            估算的语音时长（秒）
        """
        if not text:
            return 0.0
        
        # 中文平均语速约为 3-4 字/秒，这里使用3.5字/秒
        chars_per_second = 3.5
        char_count = len(text.replace(" ", "").replace("\n", ""))
        
        return round(char_count / chars_per_second, 2)
    
    async def get_slide_count(self, ppt_file_path: str) -> int:
        """获取PPT页数"""
        try:
            presentation = Presentation(ppt_file_path)
            return len(presentation.slides)
        except Exception as e:
            self.logger.error(f"获取PPT页数失败: {e}")
            return 0
