"""
图片生成器 - 从JSON数据生成幻灯片图片
这是一个简化的占位符实现，未来可以集成更强大的渲染引擎
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

class ImageGenerator:
    """从JSON数据生成幻灯片图片的简单实现"""
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        
    async def generate_images_from_json(self, project_path: Path, project_data: Dict[str, Any]) -> List[Path]:
        """
        从JSON数据生成幻灯片图片
        
        Args:
            project_path: 项目目录路径
            project_data: PPTist项目数据
            
        Returns:
            生成的图片文件路径列表
        """
        try:
            logger.info(f"🖼️ 开始从JSON数据生成图片，项目路径: {project_path}")
            
            slides = project_data.get('slides', [])
            logger.info(f"📊 需要生成 {len(slides)} 张幻灯片图片")
            
            # 创建图片输出目录
            images_dir = project_path / "slides"
            images_dir.mkdir(exist_ok=True)
            
            generated_images = []
            
            for i, slide in enumerate(slides):
                try:
                    slide_id = slide.get('id', f'slide_{i+1}')
                    logger.info(f"🎯 生成第 {i+1} 张图片: {slide_id}")
                    
                    # 创建简单的占位符图片
                    image = self._create_placeholder_image(slide, i+1)
                    
                    # 保存图片
                    image_path = images_dir / f"slide_{str(i+1).zfill(3)}.jpg"
                    image.save(image_path, "JPEG", quality=85)
                    
                    generated_images.append(image_path)
                    logger.info(f"✅ 图片已保存: {image_path}")
                    
                except Exception as e:
                    logger.error(f"❌ 生成第 {i+1} 张图片失败: {e}")
                    continue
            
            logger.info(f"🎉 图片生成完成，共生成 {len(generated_images)} 张图片")
            return generated_images
            
        except Exception as e:
            logger.error(f"❌ 图片生成失败: {e}")
            raise Exception(f"图片生成失败: {e}")
    
    def _create_placeholder_image(self, slide: Dict[str, Any], slide_number: int) -> Image.Image:
        """
        创建简单的占位符图片
        这是一个简化实现，未来可以替换为完整的PPT渲染引擎
        """
        # 创建白色背景图片
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)
        
        try:
            # 尝试加载中文字体，优先选择Windows系统字体
            font_large = None
            font_medium = None
            font_small = None
            
            # Windows中文字体列表
            chinese_fonts = [
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                "C:/Windows/Fonts/simkai.ttf",  # 楷体
                "arial.ttf",  # 备选英文字体
            ]
            
            # 尝试加载字体
            for font_path in chinese_fonts:
                try:
                    font_large = ImageFont.truetype(font_path, 72)
                    font_medium = ImageFont.truetype(font_path, 36)
                    font_small = ImageFont.truetype(font_path, 24)
                    logger.info(f"✅ 成功加载字体: {font_path}")
                    break
                except Exception as font_error:
                    logger.debug(f"尝试加载字体失败: {font_path} - {font_error}")
                    continue
            
            # 如果所有字体都失败，使用默认字体
            if not font_large:
                logger.warning("⚠️ 无法加载中文字体，使用默认字体")
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # 绘制背景（如果有背景色）
            background = slide.get('background', {})
            if background.get('type') == 'solid':
                bg_color = background.get('color', '#ffffff')
                if bg_color.startswith('#'):
                    try:
                        # 转换十六进制颜色
                        rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
                        image = Image.new('RGB', (self.width, self.height), color=rgb)
                        draw = ImageDraw.Draw(image)
                    except:
                        pass
            
            # 绘制页码
            page_text = f"第 {slide_number} 页"
            draw.text((50, 50), page_text, fill='black', font=font_medium)
            
            # 绘制幻灯片ID
            slide_id = slide.get('id', 'unknown')
            draw.text((50, 100), f"ID: {slide_id}", fill='gray', font=font_small)
            
            # 简单解析和绘制文本元素
            elements = slide.get('elements', [])
            
            for element in elements:
                if element.get('type') == 'text':
                    content = element.get('content', '')
                    # 简单提取文本内容（去除HTML标签）
                    import re
                    clean_text = re.sub(r'<[^>]+>', '', content)
                    
                    if clean_text.strip():
                        # 计算文本位置和大小
                        x = element.get('left', 50)
                        y = element.get('top', 200)
                        width = element.get('width', 500)
                        height = element.get('height', 100)
                        
                        # 根据content中的font-size选择合适的字体
                        font_to_use = font_medium
                        if 'font-size: 112px' in content:
                            font_to_use = font_large
                        elif 'font-size: 24px' in content or 'font-size: 20px' in content:
                            font_to_use = font_small
                        
                        # 确定文本颜色
                        text_color = 'black'
                        if 'color: #' in content:
                            # 尝试提取颜色
                            color_match = re.search(r'color: (#[0-9a-fA-F]{6})', content)
                            if color_match:
                                try:
                                    hex_color = color_match.group(1)
                                    text_color = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
                                except:
                                    text_color = 'black'
                        
                        # 处理文本换行
                        lines = clean_text.split('\n')
                        line_height = 40
                        
                        for i, line in enumerate(lines):
                            if line.strip():
                                line_y = y + (i * line_height)
                                # 确保文本在画布范围内
                                if line_y < self.height - 50:
                                    draw.text((x, line_y), line[:50], fill=text_color, font=font_to_use)
                
                elif element.get('type') == 'shape':
                    # 绘制简单的形状占位符
                    x = element.get('left', 0)
                    y = element.get('top', 0)
                    width = element.get('width', 100)
                    height = element.get('height', 100)
                    fill_color = element.get('fill', '#5b9bd5')
                    
                    try:
                        if fill_color.startswith('#'):
                            rgb_color = tuple(int(fill_color[i:i+2], 16) for i in (1, 3, 5))
                            # 绘制矩形占位符
                            draw.rectangle([x, y, x + min(width, 200), y + min(height, 200)], 
                                         fill=rgb_color, outline='gray')
                    except:
                        # 如果颜色解析失败，绘制灰色矩形
                        draw.rectangle([x, y, x + min(width, 200), y + min(height, 200)], 
                                     fill='lightgray', outline='gray')
            
            # 绘制slide的remark内容（PPT备注）
            remark = slide.get('remark', '')
            if remark:
                # 提取remark中的文本
                import re
                clean_remark = re.sub(r'<[^>]+>', '', remark).strip()
                if clean_remark:
                    # 在底部绘制备注内容
                    draw.text((50, self.height - 150), f"备注: {clean_remark}", 
                             fill='blue', font=font_small)
            
            # 绘制元素数量信息
            info_text = f"包含 {len(elements)} 个元素"
            draw.text((50, self.height - 100), info_text, fill='gray', font=font_small)
            
            # 绘制生成时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((50, self.height - 50), f"生成时间: {timestamp}", fill='gray', font=font_small)
            
        except Exception as e:
            logger.warning(f"⚠️ 绘制幻灯片内容时出错: {e}，使用基础占位符")
            # 如果绘制失败，至少绘制基本信息
            draw.text((100, 100), f"幻灯片 {slide_number}", fill='black')
            draw.text((100, 200), "（图片生成占位符）", fill='gray')
        
        return image

# 用于测试的主函数
async def main():
    """测试函数"""
    # 创建测试数据
    test_data = {
        "slides": [
            {
                "id": "test-slide-1",
                "elements": [
                    {
                        "type": "text",
                        "content": "<p>这是第一张幻灯片</p>",
                        "left": 100,
                        "top": 300
                    }
                ],
                "background": {"type": "solid", "color": "#ffffff"}
            },
            {
                "id": "test-slide-2", 
                "elements": [
                    {
                        "type": "text",
                        "content": "<p>这是第二张幻灯片</p>",
                        "left": 100,
                        "top": 300
                    }
                ],
                "background": {"type": "solid", "color": "#f0f0f0"}
            }
        ]
    }
    
    # 测试图片生成
    generator = ImageGenerator()
    test_path = Path("test_output")
    test_path.mkdir(exist_ok=True)
    
    images = await generator.generate_images_from_json(test_path, test_data)
    print(f"✅ 测试完成，生成了 {len(images)} 张图片")

if __name__ == "__main__":
    asyncio.run(main())
