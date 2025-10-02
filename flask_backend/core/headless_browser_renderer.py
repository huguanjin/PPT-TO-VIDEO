#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无头浏览器渲染器 - 高质量图片导出
集成到PPT转视频工作流，实现与前端完全一致的渲染质量

作者: PPT-TO-VIDEO Team
日期: 2025-09-30
"""
import asyncio
import base64
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from PIL import Image

try:
    # PIL 10.0.0+ 使用 Resampling.LANCZOS
    from PIL.Image import Resampling
    LANCZOS_FILTER = Resampling.LANCZOS
except ImportError:
    # 旧版本 PIL 使用 Image.LANCZOS
    LANCZOS_FILTER = Image.LANCZOS  # type: ignore


@dataclass
class RenderConfig:
    """渲染配置"""
    width: int = 1600
    height: int = 900
    quality: int = 95  # JPEG质量 (0-100)
    format: str = 'jpeg'  # jpeg 或 png
    device_scale_factor: int = 1  # 设备缩放因子，1=标准，2=Retina
    wait_for_fonts: bool = True  # 是否等待字体加载
    timeout: int = 30000  # 超时时间（毫秒）


@dataclass
class RenderResult:
    """渲染结果"""
    success: bool
    output_path: str
    file_size: int
    error_message: Optional[str] = None
    render_time: float = 0.0


class HeadlessBrowserRenderer:
    """
    无头浏览器渲染器
    
    使用Playwright + Chromium实现高质量幻灯片渲染
    渲染质量与前端浏览器完全一致
    """
    
    def __init__(self, config: Optional[RenderConfig] = None):
        """
        初始化渲染器
        
        Args:
            config: 渲染配置，如果为None则使用默认配置
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright未安装，请运行: pip install playwright && playwright install chromium"
            )
        
        self.config = config or RenderConfig()
        self.browser: Optional['Browser'] = None
        self.playwright = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def initialize(self):
        """初始化浏览器"""
        if self._initialized:
            return
        
        try:
            self.logger.info("🚀 启动无头浏览器...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',  # 允许跨域资源
                ]
            )
            self._initialized = True
            self.logger.info("✅ 无头浏览器初始化成功")
        except Exception as e:
            self.logger.error(f"❌ 无头浏览器初始化失败: {e}")
            raise
    
    async def render_from_html(
        self, 
        html_content: str, 
        output_path: str,
        config: Optional[RenderConfig] = None
    ) -> RenderResult:
        """
        从HTML内容渲染图片
        
        Args:
            html_content: 完整的HTML内容
            output_path: 输出文件路径
            config: 渲染配置（可选，使用默认配置）
        
        Returns:
            RenderResult: 渲染结果
        """
        import time
        start_time = time.time()
        
        if not self._initialized:
            await self.initialize()
        
        if self.browser is None:
            raise RuntimeError("浏览器未初始化")
        
        render_config = config or self.config
        
        try:
            # 如果需要高DPI支持，使用context
            if render_config.device_scale_factor > 1:
                context = await self.browser.new_context(
                    viewport={
                        'width': render_config.width,
                        'height': render_config.height
                    },
                    device_scale_factor=render_config.device_scale_factor
                )
                page = await context.new_page()
            else:
                page = await self.browser.new_page()
                await page.set_viewport_size({
                    'width': render_config.width,
                    'height': render_config.height
                })
            
            # 加载HTML内容
            await page.set_content(html_content, timeout=render_config.timeout)
            
            # 等待渲染完成
            await page.wait_for_load_state('networkidle', timeout=render_config.timeout)
            
            # 等待字体加载
            if render_config.wait_for_fonts:
                await page.evaluate('() => document.fonts.ready')
            
            # 额外等待确保完全渲染
            await page.wait_for_timeout(200)
            
            # 截图
            screenshot_options = {
                'path': output_path,
                'type': render_config.format,
                'full_page': False,
                'omit_background': False
            }
            
            if render_config.format == 'jpeg':
                screenshot_options['quality'] = render_config.quality
            
            await page.screenshot(**screenshot_options)
            
            await page.close()
            
            # 获取文件信息
            file_size = Path(output_path).stat().st_size
            render_time = time.time() - start_time
            
            self.logger.info(
                f"✅ 渲染成功: {output_path} "
                f"({file_size/1024:.1f} KB, {render_time:.2f}s)"
            )
            
            return RenderResult(
                success=True,
                output_path=output_path,
                file_size=file_size,
                render_time=render_time
            )
            
        except Exception as e:
            render_time = time.time() - start_time
            self.logger.error(f"❌ 渲染失败: {e}")
            return RenderResult(
                success=False,
                output_path=output_path,
                file_size=0,
                error_message=str(e),
                render_time=render_time
            )
    
    async def render_pptist_slide(
        self,
        slide_data: Dict[str, Any],
        output_path: str,
        config: Optional[RenderConfig] = None
    ) -> RenderResult:
        """
        渲染PPTist幻灯片数据
        
        Args:
            slide_data: PPTist幻灯片数据
            output_path: 输出文件路径
            config: 渲染配置
        
        Returns:
            RenderResult: 渲染结果
        """
        # 构建HTML
        html_content = self._build_pptist_html(slide_data)
        
        # 渲染
        return await self.render_from_html(html_content, output_path, config)
    
    async def render_base64_image(
        self,
        base64_data: str,
        output_path: str,
        config: Optional[RenderConfig] = None
    ) -> RenderResult:
        """
        从base64图片数据重新渲染高质量图片
        
        这个方法可以接收前端导出的base64图片，
        然后在无头浏览器中重新渲染以获得更高质量
        
        Args:
            base64_data: base64编码的图片数据
            output_path: 输出文件路径
            config: 渲染配置
        
        Returns:
            RenderResult: 渲染结果
        """
        import time
        start_time = time.time()
        
        render_config = config or self.config
        
        try:
            # 解码base64数据
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(base64_data)
            
            # 使用PIL重新保存为高质量图片
            with Image.open(io.BytesIO(image_bytes)) as img:
                # 转换颜色模式
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整尺寸（如果需要）
                if img.size != (render_config.width, render_config.height):
                    self.logger.info(
                        f"调整图片尺寸: {img.size} -> "
                        f"({render_config.width}, {render_config.height})"
                    )
                    img = img.resize(
                        (render_config.width, render_config.height),
                        LANCZOS_FILTER
                    )
                
                # 保存为高质量图片
                if render_config.format == 'jpeg':
                    img.save(
                        output_path,
                        'JPEG',
                        quality=render_config.quality,
                        optimize=True,
                        progressive=True
                    )
                else:
                    img.save(output_path, 'PNG', optimize=True)
            
            file_size = Path(output_path).stat().st_size
            render_time = time.time() - start_time
            
            self.logger.info(
                f"✅ 高质量重新保存成功: {output_path} "
                f"({file_size/1024:.1f} KB, {render_time:.2f}s)"
            )
            
            return RenderResult(
                success=True,
                output_path=output_path,
                file_size=file_size,
                render_time=render_time
            )
            
        except Exception as e:
            render_time = time.time() - start_time
            self.logger.error(f"❌ 重新保存失败: {e}")
            return RenderResult(
                success=False,
                output_path=output_path,
                file_size=0,
                error_message=str(e),
                render_time=render_time
            )
    
    def _build_pptist_html(self, slide_data: Dict[str, Any]) -> str:
        """
        构建PPTist风格的HTML
        
        Args:
            slide_data: 幻灯片数据
        
        Returns:
            完整的HTML字符串
        """
        # 提取背景信息
        background = slide_data.get('background', {})
        bg_style = self._build_background_style(background)
        
        # 提取元素
        elements = slide_data.get('elements', [])
        elements_html = ''.join([
            self._build_element_html(elem) for elem in elements
        ])
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        {self._get_pptist_css()}
    </style>
</head>
<body>
    <div class="thumbnail-slide" style="{bg_style}">
        <div class="elements">
            {elements_html}
        </div>
    </div>
</body>
</html>
        """
    
    def _build_background_style(self, background: Dict[str, Any]) -> str:
        """构建背景样式"""
        bg_type = background.get('type', 'solid')
        
        if bg_type == 'solid':
            color = background.get('color', '#ffffff')
            return f"background-color: {color};"
        elif bg_type == 'gradient':
            gradient = background.get('gradient', {})
            # 简化的渐变处理
            return "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        elif bg_type == 'image':
            image_url = background.get('image', {}).get('src', '')
            return f"background-image: url('{image_url}'); background-size: cover;"
        
        return "background-color: #ffffff;"
    
    def _build_element_html(self, element: Dict[str, Any]) -> str:
        """构建元素HTML"""
        elem_type = element.get('type')
        
        if elem_type == 'text':
            return self._build_text_element(element)
        elif elem_type == 'image':
            return self._build_image_element(element)
        elif elem_type == 'shape':
            return self._build_shape_element(element)
        
        return ""
    
    def _build_text_element(self, element: Dict[str, Any]) -> str:
        """构建文本元素"""
        content = element.get('content', '')
        left = element.get('left', 0)
        top = element.get('top', 0)
        width = element.get('width', 200)
        height = element.get('height', 50)
        
        # 提取样式
        font_size = element.get('fontSize', 16)
        color = element.get('color', '#000000')
        
        return f"""
        <div class="element text-element" style="
            position: absolute;
            left: {left}px;
            top: {top}px;
            width: {width}px;
            height: {height}px;
            font-size: {font_size}px;
            color: {color};
        ">
            {content}
        </div>
        """
    
    def _build_image_element(self, element: Dict[str, Any]) -> str:
        """构建图片元素"""
        src = element.get('src', '')
        left = element.get('left', 0)
        top = element.get('top', 0)
        width = element.get('width', 200)
        height = element.get('height', 200)
        
        return f"""
        <img class="element image-element" 
            src="{src}"
            style="
                position: absolute;
                left: {left}px;
                top: {top}px;
                width: {width}px;
                height: {height}px;
            "
        />
        """
    
    def _build_shape_element(self, element: Dict[str, Any]) -> str:
        """构建形状元素（简化版）"""
        # TODO: 完整的SVG形状支持
        return ""
    
    def _get_pptist_css(self) -> str:
        """获取PPTist CSS样式"""
        return """
            * { 
                margin: 0; 
                padding: 0; 
                box-sizing: border-box; 
            }
            body {
                width: 1600px;
                height: 900px;
                overflow: hidden;
            }
            .thumbnail-slide {
                width: 1600px;
                height: 900px;
                position: relative;
                background-color: #fff;
            }
            .elements {
                width: 100%;
                height: 100%;
                position: relative;
            }
            .element {
                position: absolute;
            }
            .text-element {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
                             'Microsoft YaHei', 'PingFang SC', sans-serif;
                line-height: 1.5;
            }
            .image-element {
                object-fit: contain;
            }
        """
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self._initialized = False
        self.logger.info("✅ 无头浏览器资源清理完成")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.cleanup()
