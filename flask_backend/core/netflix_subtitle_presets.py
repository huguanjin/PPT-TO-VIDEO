"""
Netflix级别字幕配置预设
提供电影级别的专业字幕显示效果和配置
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetflixSubtitleStyle:
    """Netflix字幕样式配置"""
    
    # 字体配置
    font_family: str = "Arial"
    font_size: int = 16
    font_weight: str = "normal"  # normal, bold
    font_style: str = "normal"   # normal, italic
    
    # 颜色配置
    text_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    background_color: str = "#000000"
    shadow_color: str = "#000000"
    
    # 轮廓和阴影
    outline_width: float = 2.0
    shadow_offset_x: float = 1.0
    shadow_offset_y: float = 1.0
    shadow_blur: float = 0.0
    
    # 背景设置
    background_opacity: float = 0.75
    background_padding: int = 4
    background_margin: int = 0
    
    # 位置设置
    horizontal_alignment: str = "center"  # left, center, right
    vertical_alignment: str = "bottom"    # top, middle, bottom
    margin_left: int = 0
    margin_right: int = 0
    margin_top: int = 0
    margin_bottom: int = 50
    
    # 行间距和字符间距
    line_spacing: float = 1.2
    character_spacing: float = 0.0


@dataclass
class NetflixDisplayConfig:
    """Netflix显示配置"""
    
    # 字幕长度控制
    max_characters_per_line: int = 40
    max_lines_per_subtitle: int = 2
    target_reading_speed_wpm: int = 180  # 每分钟字数
    
    # 时间控制
    min_duration_ms: int = 1000  # 最小显示时间
    max_duration_ms: int = 6000  # 最大显示时间
    subtitle_gap_ms: int = 167   # 字幕间隙（Netflix标准）
    
    # 分割规则
    prefer_punctuation_breaks: bool = True
    avoid_orphan_words: bool = True
    balance_line_lengths: bool = True
    
    # 质量控制
    reading_speed_tolerance: float = 0.2  # 阅读速度容差
    enforce_netflix_standards: bool = True


@dataclass
class NetflixAccessibilityConfig:
    """Netflix无障碍配置"""
    
    # 视觉辅助
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    color_coding_enabled: bool = False
    
    # 音频描述
    audio_description_support: bool = False
    speaker_identification: bool = False
    
    # 多语言支持
    support_rtl_languages: bool = True  # 从右到左语言
    unicode_support: bool = True
    emoji_support: bool = True


class NetflixSubtitlePresets:
    """Netflix级别字幕配置预设管理器"""
    
    # Netflix官方推荐的字幕配置预设
    NETFLIX_PRESETS = {
        "netflix_standard": {
            "name": "Netflix 标准",
            "description": "Netflix平台标准字幕配置，适用于大多数内容",
            "category": "netflix",
            "style": NetflixSubtitleStyle(
                font_family="Arial",
                font_size=16,
                font_weight="normal",
                text_color="#FFFFFF",
                outline_color="#000000",
                outline_width=2.0,
                background_color="#000000",
                background_opacity=0.75,
                margin_bottom=50,
                line_spacing=1.2
            ),
            "display": NetflixDisplayConfig(
                max_characters_per_line=40,
                max_lines_per_subtitle=2,
                target_reading_speed_wpm=180,
                min_duration_ms=1000,
                max_duration_ms=6000,
                subtitle_gap_ms=167
            ),
            "accessibility": NetflixAccessibilityConfig()
        },
        
        "netflix_cinema": {
            "name": "Netflix 电影级",
            "description": "电影级字幕配置，更短的行长度和更精确的时间控制",
            "category": "netflix",
            "style": NetflixSubtitleStyle(
                font_family="Arial",
                font_size=18,
                font_weight="normal",
                text_color="#FFFFFF",
                outline_color="#000000",
                outline_width=2.5,
                background_color="#000000",
                background_opacity=0.8,
                margin_bottom=60,
                line_spacing=1.3
            ),
            "display": NetflixDisplayConfig(
                max_characters_per_line=35,
                max_lines_per_subtitle=2,
                target_reading_speed_wpm=160,
                min_duration_ms=1200,
                max_duration_ms=5000,
                subtitle_gap_ms=200
            ),
            "accessibility": NetflixAccessibilityConfig(
                high_contrast_mode=False,
                color_coding_enabled=True
            )
        },
        
        "netflix_documentary": {
            "name": "Netflix 纪录片",
            "description": "纪录片专用配置，支持更长的字幕和复杂内容",
            "category": "netflix",
            "style": NetflixSubtitleStyle(
                font_family="Arial",
                font_size=15,
                font_weight="normal",
                text_color="#FFFFFF",
                outline_color="#000000",
                outline_width=1.8,
                background_color="#000000",
                background_opacity=0.7,
                margin_bottom=45,
                line_spacing=1.15
            ),
            "display": NetflixDisplayConfig(
                max_characters_per_line=45,
                max_lines_per_subtitle=3,
                target_reading_speed_wpm=200,
                min_duration_ms=800,
                max_duration_ms=8000,
                subtitle_gap_ms=150
            ),
            "accessibility": NetflixAccessibilityConfig(
                speaker_identification=True,
                audio_description_support=True
            )
        },
        
        "netflix_kids": {
            "name": "Netflix 儿童",
            "description": "儿童内容专用配置，更大字体和更简单的语言",
            "category": "netflix",
            "style": NetflixSubtitleStyle(
                font_family="Arial",
                font_size=20,
                font_weight="bold",
                text_color="#FFFFFF",
                outline_color="#000000",
                outline_width=3.0,
                background_color="#000000",
                background_opacity=0.85,
                margin_bottom=40,
                line_spacing=1.4
            ),
            "display": NetflixDisplayConfig(
                max_characters_per_line=30,
                max_lines_per_subtitle=2,
                target_reading_speed_wpm=120,
                min_duration_ms=1500,
                max_duration_ms=4000,
                subtitle_gap_ms=300
            ),
            "accessibility": NetflixAccessibilityConfig(
                large_text_mode=True,
                color_coding_enabled=True
            )
        },
        
        "netflix_accessibility": {
            "name": "Netflix 无障碍",
            "description": "无障碍优化配置，高对比度和辅助功能",
            "category": "netflix",
            "style": NetflixSubtitleStyle(
                font_family="Arial",
                font_size=18,
                font_weight="bold",
                text_color="#FFFF00",  # 黄色文字
                outline_color="#000000",
                outline_width=3.5,
                background_color="#000000",
                background_opacity=0.9,
                margin_bottom=55,
                line_spacing=1.5
            ),
            "display": NetflixDisplayConfig(
                max_characters_per_line=35,
                max_lines_per_subtitle=2,
                target_reading_speed_wpm=150,
                min_duration_ms=1500,
                max_duration_ms=7000,
                subtitle_gap_ms=250
            ),
            "accessibility": NetflixAccessibilityConfig(
                high_contrast_mode=True,
                large_text_mode=True,
                color_coding_enabled=True,
                speaker_identification=True
            )
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Optional[Dict[str, Any]]:
        """获取指定的Netflix预设配置"""
        return cls.NETFLIX_PRESETS.get(preset_name)
    
    @classmethod
    def list_presets(cls) -> List[Dict[str, str]]:
        """获取所有Netflix预设列表"""
        return [
            {
                "id": preset_id,
                "name": preset_config["name"],
                "description": preset_config["description"],
                "category": preset_config["category"]
            }
            for preset_id, preset_config in cls.NETFLIX_PRESETS.items()
        ]
    
    @classmethod
    def get_preset_config(cls, preset_name: str) -> Dict[str, Any]:
        """获取预设的完整配置对象"""
        preset = cls.get_preset(preset_name)
        if not preset:
            raise ValueError(f"未找到预设: {preset_name}")
        
        # 转换dataclass为字典
        config = {
            "netflix_preset": preset_name,
            "style": asdict(preset["style"]),
            "display": asdict(preset["display"]),
            "accessibility": asdict(preset["accessibility"]),
            "metadata": {
                "name": preset["name"],
                "description": preset["description"],
                "category": preset["category"]
            }
        }
        
        return config
    
    @classmethod
    def validate_netflix_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证Netflix配置是否符合标准"""
        errors = []
        warnings = []
        
        # 获取配置值
        style = config.get("style", {})
        display = config.get("display", {})
        
        # Netflix标准验证
        max_chars = display.get("max_characters_per_line", 0)
        if max_chars > 40:
            warnings.append("Netflix建议每行不超过40个字符")
        elif max_chars > 50:
            errors.append("每行字符数不应超过50个")
        
        max_lines = display.get("max_lines_per_subtitle", 0)
        if max_lines > 2:
            warnings.append("Netflix标准建议最多2行字幕")
        elif max_lines > 3:
            errors.append("字幕行数不应超过3行")
        
        reading_speed = display.get("target_reading_speed_wpm", 0)
        if reading_speed > 200:
            warnings.append("阅读速度过快，可能影响观看体验")
        elif reading_speed < 120:
            warnings.append("阅读速度过慢，可能影响内容流畅性")
        
        # 时间控制验证
        min_duration = display.get("min_duration_ms", 0)
        if min_duration < 1000:
            errors.append("最小显示时间不应少于1秒")
        
        subtitle_gap = display.get("subtitle_gap_ms", 0)
        if subtitle_gap < 167:
            warnings.append("Netflix建议字幕间隙至少167ms")
        
        # 样式验证
        font_size = style.get("font_size", 0)
        if font_size < 12:
            warnings.append("字体过小可能影响可读性")
        elif font_size > 24:
            warnings.append("字体过大可能影响布局")
        
        outline_width = style.get("outline_width", 0)
        if outline_width < 1.5:
            warnings.append("轮廓宽度建议至少1.5px以确保可读性")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "netflix_compliant": len(errors) == 0 and len(warnings) <= 2
        }
    
    @classmethod
    def optimize_for_content_type(cls, content_type: str, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """根据内容类型优化配置"""
        optimized_config = base_config.copy()
        
        if content_type == "action":
            # 动作片：更短的字幕，更快的切换
            optimized_config["display"]["max_characters_per_line"] = 30
            optimized_config["display"]["max_duration_ms"] = 4000
            optimized_config["display"]["target_reading_speed_wpm"] = 200
            
        elif content_type == "drama":
            # 剧情片：平衡的配置
            optimized_config["display"]["max_characters_per_line"] = 40
            optimized_config["display"]["target_reading_speed_wpm"] = 180
            
        elif content_type == "comedy":
            # 喜剧：更长的显示时间以配合笑点
            optimized_config["display"]["min_duration_ms"] = 1200
            optimized_config["display"]["subtitle_gap_ms"] = 200
            
        elif content_type == "documentary":
            # 纪录片：支持更多信息
            optimized_config["display"]["max_characters_per_line"] = 45
            optimized_config["display"]["max_lines_per_subtitle"] = 3
            optimized_config["display"]["target_reading_speed_wpm"] = 200
            
        elif content_type == "educational":
            # 教育内容：慢节奏，更清晰
            optimized_config["display"]["target_reading_speed_wpm"] = 150
            optimized_config["display"]["min_duration_ms"] = 1500
            optimized_config["style"]["font_size"] = 18
            
        return optimized_config
    
    @classmethod
    def create_custom_netflix_preset(cls, name: str, description: str, 
                                   style_overrides: Optional[Dict] = None,
                                   display_overrides: Optional[Dict] = None,
                                   accessibility_overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """创建自定义Netflix预设"""
        
        # 基于标准预设创建
        base_preset = cls.get_preset("netflix_standard")
        
        if base_preset is None:
            raise ValueError("无法获取Netflix标准预设配置")
        
        # 应用覆盖配置
        if style_overrides:
            for key, value in style_overrides.items():
                if hasattr(base_preset["style"], key):
                    setattr(base_preset["style"], key, value)
        
        if display_overrides:
            for key, value in display_overrides.items():
                if hasattr(base_preset["display"], key):
                    setattr(base_preset["display"], key, value)
        
        if accessibility_overrides:
            for key, value in accessibility_overrides.items():
                if hasattr(base_preset["accessibility"], key):
                    setattr(base_preset["accessibility"], key, value)
        
        # 创建新预设
        custom_preset = {
            "name": name,
            "description": description,
            "category": "netflix_custom",
            "style": base_preset["style"],
            "display": base_preset["display"],
            "accessibility": base_preset["accessibility"]
        }
        
        return custom_preset


class NetflixConfigIntegrator:
    """Netflix配置集成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def integrate_with_existing_config(self, existing_config: Dict[str, Any], 
                                     netflix_preset: str) -> Dict[str, Any]:
        """将Netflix预设集成到现有配置中"""
        
        # 获取Netflix预设配置
        netflix_config = NetflixSubtitlePresets.get_preset_config(netflix_preset)
        
        # 创建集成配置
        integrated_config = existing_config.copy()
        
        # 映射Netflix配置到现有配置结构
        if "smart_subtitle_processing" not in integrated_config:
            integrated_config["smart_subtitle_processing"] = {}
        
        subtitle_config = integrated_config["smart_subtitle_processing"]
        
        # 基础配置映射
        display_config = netflix_config["display"]
        style_config = netflix_config["style"]
        
        subtitle_config.update({
            # Netflix显示配置
            "max_length": display_config["max_characters_per_line"],
            "max_lines": display_config["max_lines_per_subtitle"],
            "reading_speed_wpm": display_config["target_reading_speed_wpm"],
            "min_duration_ms": display_config["min_duration_ms"],
            "max_duration_ms": display_config["max_duration_ms"],
            "subtitle_gap_ms": display_config["subtitle_gap_ms"],
            
            # Netflix样式配置
            "netflix_style": {
                "font_family": style_config["font_family"],
                "font_size": style_config["font_size"],
                "font_weight": style_config["font_weight"],
                "text_color": style_config["text_color"],
                "outline_color": style_config["outline_color"],
                "outline_width": style_config["outline_width"],
                "background_color": style_config["background_color"],
                "background_opacity": style_config["background_opacity"],
                "line_spacing": style_config["line_spacing"]
            },
            
            # Netflix质量控制
            "netflix_standards": {
                "enforce_standards": display_config["enforce_netflix_standards"],
                "balance_lines": display_config["balance_line_lengths"],
                "avoid_orphans": display_config["avoid_orphan_words"],
                "prefer_punctuation": display_config["prefer_punctuation_breaks"]
            },
            
            # 元数据
            "netflix_preset": netflix_preset,
            "netflix_metadata": netflix_config["metadata"]
        })
        
        return integrated_config
    
    def export_to_srt_style(self, netflix_config: Dict[str, Any]) -> str:
        """导出为SRT样式配置"""
        style = netflix_config["style"]
        
        srt_style = f"""{{\\an2}}{{\\fs{style['font_size']}}}{{\\c&H{style['text_color'][1:]}}}{{\\3c&H{style['outline_color'][1:]}}}{{\\bord{style['outline_width']}}}"""
        
        return srt_style
    
    def export_to_ass_style(self, netflix_config: Dict[str, Any]) -> str:
        """导出为ASS样式配置"""
        style = netflix_config["style"]
        
        ass_style = f"""Style: Netflix,{style['font_family']},{style['font_size']},&H{style['text_color'][1:]},&H{style['outline_color'][1:]},&H{style['shadow_color'][1:]},&H{style['background_color'][1:]},0,0,0,0,100,100,0,0,1,{style['outline_width']},0,2,10,10,{style['margin_bottom']},1"""
        
        return ass_style
