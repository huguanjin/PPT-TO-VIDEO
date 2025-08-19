"""
PPTist数据导入模块
接收PPTist导出的JSON数据和图片，转换为标准格式
"""
import json
import os
import base64
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import asyncio
import aiofiles
from datetime import datetime

from utils.logger import get_logger
from utils.file_manager import FileManager

logger = get_logger(__name__)

@dataclass
class PPTistSlideData:
    """PPTist幻灯片数据结构"""
    slide_number: int
    id: str
    title: str
    notes: str  # 讲话稿
    image_file: str
    background: Dict[str, Any]
    elements: List[Dict[str, Any]]

@dataclass 
class PPTistImportResult:
    """导入结果"""
    project_name: str
    output_dir: str
    slides_count: int
    json_file: str
    image_files: List[str]
    success: bool
    message: str

class PPTistImporter:
    """PPTist数据导入器"""
    
    def __init__(self, project_name: str, base_output_dir: Path = None):
        self.project_name = project_name
        if base_output_dir is None:
            base_output_dir = Path("output")
        
        self.output_dir = base_output_dir / project_name
        self.slides_dir = self.output_dir / "slides"
        self.file_manager = FileManager(self.output_dir)
        
    async def import_pptist_data(
        self, 
        json_data: Dict[str, Any], 
        images_data: List[Dict[str, str]],
        progress_callback: Optional[callable] = None
    ) -> PPTistImportResult:
        """
        导入PPTist数据
        
        Args:
            json_data: PPTist导出的JSON数据
            images_data: 图片数据列表 [{"filename": "slide_001.png", "data": "base64..."}]
            progress_callback: 进度回调函数
        """
        try:
            logger.info(f"开始导入PPTist数据到项目: {self.project_name}")
            
            # 创建输出目录
            await self._create_directories()
            if progress_callback:
                progress_callback(10)
            
            # 处理JSON数据
            processed_data = await self._process_json_data(json_data)
            if progress_callback:
                progress_callback(30)
            
            # 保存图片文件
            image_files = await self._save_image_files(images_data)
            if progress_callback:
                progress_callback(70)
            
            # 保存幻灯片元数据
            slides_metadata = await self._generate_slides_metadata(processed_data, image_files)
            if progress_callback:
                progress_callback(85)
            
            # 保存项目元数据
            await self._generate_project_metadata(processed_data, image_files)
            if progress_callback:
                progress_callback(100)
            
            result = PPTistImportResult(
                project_name=self.project_name,
                output_dir=str(self.output_dir),
                slides_count=len(processed_data['slides']),
                json_file=str(self.slides_dir / "slides_metadata.json"),
                image_files=image_files,
                success=True,
                message="PPTist数据导入成功"
            )
            
            logger.info(f"PPTist数据导入完成: {result.slides_count}张幻灯片")
            return result
            
        except Exception as e:
            logger.error(f"PPTist数据导入失败: {e}")
            return PPTistImportResult(
                project_name=self.project_name,
                output_dir=str(self.output_dir),
                slides_count=0,
                json_file="",
                image_files=[],
                success=False,
                message=f"导入失败: {str(e)}"
            )
    
    async def _create_directories(self):
        """创建必要的目录"""
        try:
            self.file_manager.create_directory_structure()
            logger.info(f"创建目录结构: {self.output_dir}")
        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            raise
        
    async def _process_json_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理JSON数据，转换为标准格式"""
        slides_data = []
        
        for i, slide in enumerate(json_data.get("slides", [])):
            slide_info = {
                "slide_id": f"{i+1:03d}",
                "slide_number": slide.get("slide_number", i + 1),
                "title": slide.get("title", f"幻灯片 {i+1}"),
                "image_file": f"slide_{i+1:03d}.png",
                "notes": slide.get("remark", ""),  # 讲话稿
                "notes_word_count": len(slide.get("remark", "")),
                "extracted_at": datetime.now().isoformat(),
                "background": slide.get("background", {}),
                "elements": slide.get("elements", []),
                "content": self._extract_content_from_elements(slide.get("elements", [])),
                "metadata": {
                    "original_id": slide.get("id"),
                    "elements_count": len(slide.get("elements", []))
                }
            }
            slides_data.append(slide_info)
        
        return {
            "project_info": {
                "title": json_data.get("title", "PPTist导入项目"),
                "source": "PPTist",
                "exported_at": json_data.get("exported_at"),
                "imported_at": datetime.now().isoformat(),
                "viewport": {
                    "width": json_data.get("width", 1600),
                    "height": json_data.get("height", 900)
                },
                "theme": json_data.get("theme", {}),
                "total_slides": len(slides_data)
            },
            "slides": slides_data
        }
    
    async def _save_image_files(self, images_data: List[Dict[str, str]]) -> List[str]:
        """保存图片文件"""
        image_files = []
        
        for i, img_data in enumerate(images_data):
            try:
                filename = img_data.get("filename") or f"slide_{i+1:03d}.png"
                base64_data = img_data["data"]
                
                # 处理base64数据
                if "," in base64_data:
                    # 去除data:image/png;base64,前缀
                    base64_data = base64_data.split(",", 1)[1]
                
                # 解码base64数据
                image_bytes = base64.b64decode(base64_data)
                
                # 保存文件
                file_path = self.slides_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                
                image_files.append(str(file_path))
                logger.info(f"保存图片: {filename} ({len(image_bytes)} bytes)")
                
            except Exception as e:
                logger.error(f"保存图片失败 {i+1}: {e}")
                # 创建占位符图片
                placeholder_path = await self._create_placeholder_image(i+1)
                if placeholder_path:
                    image_files.append(placeholder_path)
        
        return image_files
    
    async def _create_placeholder_image(self, slide_number: int) -> Optional[str]:
        """创建占位符图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建1920x1080的图片
            img = Image.new('RGB', (1920, 1080), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # 绘制文本
            text = f"幻灯片 {slide_number}"
            try:
                font = ImageFont.truetype("arial.ttf", 72)
            except:
                font = ImageFont.load_default()
            
            # 计算文本位置（居中）
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (1920 - text_width) // 2
            y = (1080 - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # 保存图片
            filename = f"slide_{slide_number:03d}.png"
            file_path = self.slides_dir / filename
            img.save(file_path, 'PNG')
            
            logger.info(f"创建占位符图片: {filename}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"创建占位符图片失败: {e}")
            return None
    
    def _extract_content_from_elements(self, elements: List[Dict[str, Any]]) -> str:
        """从元素中提取文本内容"""
        texts = []
        for element in elements:
            if element.get("type") == "text":
                content = element.get("content", "")
                if content:
                    # 简单清理HTML标签
                    import re
                    clean_content = re.sub(r'<[^>]+>', '', str(content))
                    if clean_content.strip():
                        texts.append(clean_content.strip())
        
        return "\n".join(texts)
    
    async def _generate_slides_metadata(self, data: Dict[str, Any], image_files: List[str]) -> str:
        """生成幻灯片元数据文件"""
        metadata = {
            "total_slides": data["project_info"]["total_slides"],
            "parsing_completed": True,
            "parsing_timestamp": data["project_info"]["imported_at"],
            "source_file": "PPTist导入",
            "source_type": "PPTist",
            "slides": data["slides"]
        }
        
        # 保存幻灯片元数据
        metadata_file = self.slides_dir / "slides_metadata.json"
        self.file_manager.save_json(metadata, metadata_file)
        
        logger.info(f"生成幻灯片元数据: {metadata_file}")
        return str(metadata_file)
    
    async def _generate_project_metadata(self, data: Dict[str, Any], image_files: List[str]):
        """生成项目元数据文件"""
        metadata = {
            "project_name": self.project_name,
            "source": "PPTist",
            "import_info": data["project_info"],
            "files": {
                "slides_metadata": "slides/slides_metadata.json",
                "image_files": [Path(f).name for f in image_files],
                "slides_directory": "slides/"
            },
            "processing_ready": True,
            "workflow_status": {
                "step1_ppt_parser": "completed",
                "step2_tts_generator": "pending",
                "step3_video_generator": "pending", 
                "step4_subtitle_generator": "pending",
                "step5_final_merger": "pending"
            }
        }
        
        # 保存项目元数据
        self.file_manager.save_project_metadata(metadata)
        logger.info(f"生成项目元数据")

    def get_import_status(self) -> Dict[str, Any]:
        """获取导入状态"""
        if not self.output_dir.exists():
            return {"status": "not_imported", "message": "项目不存在"}
        
        metadata_file = self.output_dir / "project_metadata.json"
        if metadata_file.exists():
            metadata = self.file_manager.load_project_metadata()
            return {
                "status": "imported",
                "project_name": metadata.get("project_name"),
                "slides_count": metadata.get("import_info", {}).get("total_slides", 0),
                "import_time": metadata.get("import_info", {}).get("imported_at"),
                "processing_ready": metadata.get("processing_ready", False)
            }
        
        return {"status": "incomplete", "message": "导入未完成"}
