"""
自适应字体大小计算模块
解决字幕文字过大问题，实现基于分辨率和内容的智能字体大小调整
"""
import re
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AdaptiveFontSizeCalculator:
    """自适应字体大小计算器"""
    
    def __init__(self):
        # 基础配置
        self.base_resolution = (1920, 1080)  # 基准分辨率
        self.base_font_size = 16  # 基准字体大小
        
        # 分辨率对应的字体配置
        self.resolution_configs = {
            (1280, 720): {"base_font": 14, "min_font": 12, "max_font": 18},
            (1920, 1080): {"base_font": 16, "min_font": 14, "max_font": 20},
            (2560, 1440): {"base_font": 20, "min_font": 16, "max_font": 26},
            (3840, 2160): {"base_font": 24, "min_font": 20, "max_font": 32}
        }
    
    def calculate_adaptive_font_size(
        self, 
        text: str, 
        line_count: int, 
        resolution: Tuple[int, int] = (1920, 1080),
        video_duration: Optional[float] = None
    ) -> int:
        """
        计算自适应字体大小
        
        Args:
            text: 字幕文本内容
            line_count: 行数
            resolution: 视频分辨率
            video_duration: 视频时长（秒）
            
        Returns:
            优化后的字体大小
        """
        try:
            # 1. 获取基础字体配置
            font_config = self._get_resolution_config(resolution)
            base_font = font_config["base_font"]
            min_font = font_config["min_font"]
            max_font = font_config["max_font"]
            
            # 2. 分辨率调整因子
            resolution_factor = self._calculate_resolution_factor(resolution)
            
            # 3. 内容长度调整因子
            length_factor = self._calculate_length_factor(text)
            
            # 4. 行数调整因子
            line_factor = self._calculate_line_factor(line_count)
            
            # 5. 字符密度调整因子
            density_factor = self._calculate_density_factor(text, line_count)
            
            # 6. 视频时长调整因子（可选）
            duration_factor = self._calculate_duration_factor(video_duration, text) if video_duration else 1.0
            
            # 7. 综合计算
            final_size = int(
                base_font * 
                resolution_factor * 
                length_factor * 
                line_factor * 
                density_factor * 
                duration_factor
            )
            
            # 8. 限制在合理范围内
            final_size = max(min_font, min(final_size, max_font))
            
            logger.info(f"字体大小计算: {text[:20]}... -> {final_size} "
                       f"(分辨率:{resolution}, 行数:{line_count}, 长度:{len(text)})")
            
            return final_size
            
        except Exception as e:
            logger.error(f"字体大小计算失败: {e}")
            return self._get_resolution_config(resolution)["base_font"]
    
    def _get_resolution_config(self, resolution: Tuple[int, int]) -> Dict[str, int]:
        """获取分辨率对应的字体配置"""
        # 寻找最接近的分辨率配置
        target_pixels = resolution[0] * resolution[1]
        
        best_match = None
        min_diff = float('inf')
        
        for res, config in self.resolution_configs.items():
            pixels = res[0] * res[1]
            diff = abs(pixels - target_pixels)
            if diff < min_diff:
                min_diff = diff
                best_match = config
        
        return best_match or self.resolution_configs[(1920, 1080)]
    
    def _calculate_resolution_factor(self, resolution: Tuple[int, int]) -> float:
        """计算分辨率调整因子"""
        base_pixels = self.base_resolution[0] * self.base_resolution[1]
        current_pixels = resolution[0] * resolution[1]
        
        # 使用平方根来避免字体变化过于剧烈
        factor = (current_pixels / base_pixels) ** 0.5
        
        # 限制调整幅度
        return max(0.7, min(factor, 1.5))
    
    def _calculate_length_factor(self, text: str) -> float:
        """计算内容长度调整因子"""
        text_length = len(text.strip())
        
        if text_length <= 15:
            return 1.1  # 短文本稍微大一点
        elif text_length <= 25:
            return 1.0  # 正常大小
        elif text_length <= 35:
            return 0.95  # 稍微小一点
        else:
            return 0.9  # 长文本明显小一点
    
    def _calculate_line_factor(self, line_count: int) -> float:
        """计算行数调整因子"""
        if line_count <= 1:
            return 1.0
        elif line_count == 2:
            return 0.95  # 两行稍微小一点
        else:
            return 0.9  # 多行更小
    
    def _calculate_density_factor(self, text: str, line_count: int) -> float:
        """计算字符密度调整因子"""
        if line_count == 0:
            return 1.0
        
        avg_chars_per_line = len(text) / line_count
        
        if avg_chars_per_line <= 20:
            return 1.0
        elif avg_chars_per_line <= 26:
            return 0.98
        else:
            return 0.95
    
    def _calculate_duration_factor(self, duration: float, text: str) -> float:
        """计算视频时长调整因子"""
        # 计算阅读速度（字符/秒）
        reading_speed = len(text) / duration if duration > 0 else 0
        
        if reading_speed <= 2.0:
            return 1.05  # 慢速阅读，字体可以大一点
        elif reading_speed <= 4.0:
            return 1.0  # 正常速度
        else:
            return 0.95  # 快速阅读，字体小一点
    
    def get_optimal_subtitle_config(
        self, 
        text: str, 
        resolution: Tuple[int, int] = (1920, 1080),
        video_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        获取最优字幕配置
        
        Returns:
            包含字体大小、行数、字符限制等的配置字典
        """
        # 智能断行
        optimal_lines = self._calculate_optimal_lines(text)
        
        # 计算字体大小
        font_size = self.calculate_adaptive_font_size(
            text, optimal_lines, resolution, video_duration
        )
        
        # 获取分辨率配置
        res_config = self._get_resolution_config(resolution)
        
        return {
            "font_size": font_size,
            "max_lines": min(optimal_lines, 2),  # 最多2行
            "max_chars_per_line": self._calculate_max_chars_per_line(resolution),
            "line_spacing": 1.2 if optimal_lines > 1 else 1.0,
            "margin_bottom": self._calculate_margin_bottom(resolution),
            "resolution_config": res_config
        }
    
    def _calculate_optimal_lines(self, text: str) -> int:
        """计算最优行数"""
        text_length = len(text.strip())
        
        if text_length <= 26:
            return 1
        elif text_length <= 52:
            return 2
        else:
            return 2  # 强制最多2行
    
    def _calculate_max_chars_per_line(self, resolution: Tuple[int, int]) -> int:
        """计算每行最大字符数"""
        # 基于分辨率调整
        if resolution[0] <= 1280:
            return 24  # 720p
        elif resolution[0] <= 1920:
            return 26  # 1080p
        elif resolution[0] <= 2560:
            return 28  # 1440p
        else:
            return 30  # 4K
    
    def _calculate_margin_bottom(self, resolution: Tuple[int, int]) -> int:
        """计算底部边距"""
        height = resolution[1]
        return int(height * 0.08)  # 高度的8%作为底部边距


# 全局实例
adaptive_font_calculator = AdaptiveFontSizeCalculator()


def get_adaptive_subtitle_config(
    text: str, 
    resolution: Tuple[int, int] = (1920, 1080),
    video_duration: Optional[float] = None
) -> Dict[str, Any]:
    """
    获取自适应字幕配置的便捷函数
    
    Args:
        text: 字幕文本
        resolution: 视频分辨率
        video_duration: 视频时长
        
    Returns:
        优化后的字幕配置
    """
    return adaptive_font_calculator.get_optimal_subtitle_config(
        text, resolution, video_duration
    )


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        {
            "text": "欢迎使用PPT转视频工具",
            "resolution": (1920, 1080),
            "duration": 3.0
        },
        {
            "text": "请访问我们的官方网站：https://www.example.com 获取更多信息",
            "resolution": (1920, 1080),
            "duration": 5.0
        },
        {
            "text": "这是一个很长的字幕文本示例，用来测试自适应字体大小计算算法的效果",
            "resolution": (1280, 720),
            "duration": 7.0
        }
    ]
    
    calculator = AdaptiveFontSizeCalculator()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"文本: {case['text']}")
        print(f"分辨率: {case['resolution']}")
        print(f"时长: {case['duration']}秒")
        
        config = calculator.get_optimal_subtitle_config(
            case['text'], case['resolution'], case['duration']
        )
        
        print(f"推荐配置: {config}")