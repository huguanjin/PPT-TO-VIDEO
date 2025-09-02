"""
Step 01: PPT图片导出器 - 基于PPTist原生导出
使用PPTist前端的原生图片导出功能，生成高质量的PPT页面图片
"""
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import subprocess
import time

logger = logging.getLogger(__name__)

@dataclass
class SlideExportResult:
    """单个slide导出结果"""
    slide_index: int
    slide_id: str
    image_path: str
    file_size: int
    export_time: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class PPTExportResult:
    """PPT导出结果"""
    project_name: str
    total_slides: int
    exported_slides: List[SlideExportResult]
    export_format: str
    image_quality: float
    total_time: float
    success_count: int
    failed_count: int

class PPTistImageExporter:
    """基于PPTist的PPT图片导出器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.slides_dir = project_dir / "slides"
        self.temp_dir = project_dir / "temp"
        
        # 创建必要目录
        self.slides_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # PPTist配置
        self.pptist_url = "http://localhost:3000"  # PPTist前端地址
        self.export_config = {
            "format": "png",  # png 或 jpeg
            "quality": 1.0,   # 图片质量 0-1
            "width": 1600,    # 导出宽度
            "ignore_webfont": True  # 忽略在线字体
        }
        
        logger.info(f"PPTist图片导出器初始化: {project_dir}")
    
    def set_export_config(self, format: str = "png", quality: float = 1.0, 
                         width: int = 1600, ignore_webfont: bool = True):
        """设置导出配置"""
        self.export_config.update({
            "format": format,
            "quality": quality,
            "width": width,
            "ignore_webfont": ignore_webfont
        })
        logger.info(f"导出配置已更新: {self.export_config}")
    
    async def export_ppt_via_api(self, ppt_data: Dict[str, Any], 
                                progress_callback: Optional[Callable] = None) -> PPTExportResult:
        """
        通过PPTist API导出PPT为图片
        
        Args:
            ppt_data: PPT数据（来自PPTist解析结果）
            progress_callback: 进度回调函数
            
        Returns:
            PPTExportResult: 导出结果
        """
        start_time = time.time()
        slides = ppt_data.get('slides', [])
        total_slides = len(slides)
        
        logger.info(f"开始导出PPT图片: {total_slides} 个slides")
        
        exported_slides = []
        success_count = 0
        failed_count = 0
        
        for i, slide in enumerate(slides):
            try:
                # 更新进度
                if progress_callback:
                    progress = int((i / total_slides) * 100)
                    progress_callback(progress)
                
                # 导出单个slide
                result = await self._export_single_slide(slide, i)
                exported_slides.append(result)
                
                if result.success:
                    success_count += 1
                    logger.info(f"Slide {i+1} 导出成功: {result.image_path}")
                else:
                    failed_count += 1
                    logger.error(f"Slide {i+1} 导出失败: {result.error_message}")
                
            except Exception as e:
                failed_count += 1
                error_result = SlideExportResult(
                    slide_index=i,
                    slide_id=slide.get('id', f'slide_{i}'),
                    image_path="",
                    file_size=0,
                    export_time=0,
                    success=False,
                    error_message=str(e)
                )
                exported_slides.append(error_result)
                logger.error(f"Slide {i+1} 导出异常: {e}")
        
        # 完成进度
        if progress_callback:
            progress_callback(100)
        
        total_time = time.time() - start_time
        
        result = PPTExportResult(
            project_name=self.project_dir.name,
            total_slides=total_slides,
            exported_slides=exported_slides,
            export_format=self.export_config["format"],
            image_quality=self.export_config["quality"],
            total_time=total_time,
            success_count=success_count,
            failed_count=failed_count
        )
        
        logger.info(f"PPT图片导出完成: {success_count}/{total_slides} 成功, 耗时 {total_time:.2f}s")
        
        return result
    
    async def _export_single_slide(self, slide: Dict[str, Any], index: int) -> SlideExportResult:
        """导出单个slide为图片"""
        slide_start_time = time.time()
        slide_id = slide.get('id', f'slide_{index}')
        
        try:
            # 方案1: 直接调用PPTist导出API（如果有的话）
            # 方案2: 使用无头浏览器控制PPTist前端导出
            # 方案3: 重用PPTist的渲染组件
            
            # 这里先使用方案2 - 无头浏览器自动化
            image_path = await self._export_via_browser_automation(slide, index)
            
            # 检查文件是否成功生成
            if os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                export_time = time.time() - slide_start_time
                
                return SlideExportResult(
                    slide_index=index,
                    slide_id=slide_id,
                    image_path=image_path,
                    file_size=file_size,
                    export_time=export_time,
                    success=True
                )
            else:
                raise FileNotFoundError(f"导出的图片文件不存在: {image_path}")
                
        except Exception as e:
            export_time = time.time() - slide_start_time
            return SlideExportResult(
                slide_index=index,
                slide_id=slide_id,
                image_path="",
                file_size=0,
                export_time=export_time,
                success=False,
                error_message=str(e)
            )
    
    async def _export_via_browser_automation(self, slide: Dict[str, Any], index: int) -> str:
        """
        使用浏览器自动化导出slide
        这需要PPTist前端正在运行，并提供API接口
        """
        # 这是一个示例实现，实际需要根据PPTist的API设计
        import aiohttp
        
        # 构造slide数据
        slide_data = {
            "slide": slide,
            "config": self.export_config
        }
        
        # 调用PPTist导出API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.pptist_url}/api/export/slide",
                json=slide_data
            ) as response:
                if response.status == 200:
                    # 假设API返回图片数据
                    image_data = await response.read()
                    
                    # 保存图片文件
                    filename = f"slide_{index+1:03d}.{self.export_config['format']}"
                    image_path = str(self.slides_dir / filename)
                    
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    return image_path
                else:
                    raise Exception(f"API调用失败: {response.status}")
    
    def export_slides_list(self) -> List[str]:
        """获取已导出的slides文件列表"""
        slide_files = []
        for ext in ['png', 'jpg', 'jpeg']:
            slide_files.extend(list(self.slides_dir.glob(f"*.{ext}")))
        
        # 按文件名排序
        slide_files.sort(key=lambda x: x.name)
        
        return [str(f) for f in slide_files]
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info("临时文件清理完成")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")

# 兼容性函数 - 为现有工作流提供接口
async def export_ppt_to_images(project_dir: Path, ppt_data: Dict[str, Any], 
                             config: Dict[str, Any] = None,
                             progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    将PPT导出为图片文件
    
    Args:
        project_dir: 项目目录
        ppt_data: PPT数据
        config: 导出配置
        progress_callback: 进度回调
        
    Returns:
        Dict: 导出结果
    """
    exporter = PPTistImageExporter(project_dir)
    
    # 应用配置
    if config:
        exporter.set_export_config(
            format=config.get('format', 'png'),
            quality=config.get('quality', 1.0),
            width=config.get('width', 1600),
            ignore_webfont=config.get('ignore_webfont', True)
        )
    
    # 执行导出
    result = await exporter.export_ppt_via_api(ppt_data, progress_callback)
    
    # 转换为兼容格式
    return {
        "success": result.success_count > 0,
        "message": f"成功导出 {result.success_count}/{result.total_slides} 个slides",
        "total_slides": result.total_slides,
        "success_count": result.success_count,
        "failed_count": result.failed_count,
        "slides_dir": str(exporter.slides_dir),
        "slide_files": exporter.export_slides_list(),
        "export_time": result.total_time
    }
