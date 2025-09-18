"""
Netflix样式预设配置 V2 - VideoLingo Netflix标准
基于VideoLingo-3.0.0的Netflix字幕标准，实现专业级样式配置
集成36个中文字符/行控制 + Netflix黄色样式 + 智能样式适配
"""
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetflixStyleConfigV2:
    """Netflix样式配置 V2 - VideoLingo标准"""
    
    # Netflix黄色字体标准 (基于VideoLingo实现)
    font_color: str = "&H00FFFF"           # Netflix经典黄色 (BGR格式)
    font_color_hex: str = "#FFFF00"        # Netflix黄色 (HEX格式)
    font_color_rgb: tuple = (255, 255, 0)  # Netflix黄色 (RGB格式)
    
    # 字体配置 (Netflix标准)
    font_family: str = "Arial Unicode MS"  # 跨平台Unicode字体
    font_size: int = 17                    # Netflix标准字体大小
    font_weight: str = "normal"            # 字体粗细
    font_style: str = "normal"             # 字体样式
    
    # 描边配置 (Netflix黑色描边标准)
    outline_color: str = "&H000000"        # 黑色描边 (BGR格式)
    outline_color_hex: str = "#000000"     # 黑色描边 (HEX格式)
    outline_width: int = 1                 # 描边宽度 (1px)
    
    # 背景配置 (Netflix半透明背景标准)
    back_color: str = "&H33000000"         # 半透明黑色背景
    back_color_hex: str = "#00000033"      # 半透明黑色背景 (HEX+Alpha)
    background_opacity: float = 0.2       # 背景透明度 (20%)
    background_padding: int = 4            # 背景内边距
    
    # 位置与对齐 (Netflix底部居中标准)
    alignment: int = 2                     # ASS格式对齐: 2=底部居中
    horizontal_alignment: str = "center"   # 水平对齐
    vertical_alignment: str = "bottom"     # 垂直对齐
    margin_v: int = 27                     # 底部边距 (Netflix标准)
    margin_l: int = 0                      # 左边距
    margin_r: int = 0                      # 右边距
    
    # 字符与行控制 (VideoLingo Netflix标准)
    max_chars_per_line: int = 36           # 36个中文字符/行 (VideoLingo标准)
    max_lines: int = 2                     # 最大行数
    line_spacing: float = 1.2              # 行间距
    character_spacing: float = 0.0         # 字符间距
    
    # 显示时间控制
    min_duration_seconds: float = 1.0      # 最小显示时间
    max_duration_seconds: float = 6.0      # 最大显示时间
    reading_speed_cps: float = 17.0        # 每秒字符数 (Netflix标准)
    
    # 高级样式选项
    border_style: int = 4                  # 边框样式: 4=背景框
    shadow_offset_x: float = 0             # 阴影X偏移
    shadow_offset_y: float = 0             # 阴影Y偏移
    shadow_blur: float = 0                 # 阴影模糊度
    
    # 质量控制选项
    single_line_preference: bool = True    # 优先单行显示
    semantic_split_enabled: bool = True    # 启用语义分割
    auto_quality_check: bool = True        # 自动质量检查


@dataclass 
class VideoLingoNetflixConfig:
    """VideoLingo Netflix配置集成"""
    
    # VideoLingo核心配置
    subtitle_length_control: Optional[Dict[str, Any]] = None
    netflix_style_presets: Optional[Dict[str, Any]] = None
    ai_optimization: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.subtitle_length_control is None:
            self.subtitle_length_control = {
                "max_length": 75,                    # VideoLingo内部计算基准
                "target_multiplier": 1.2,            # 翻译长度系数  
                "chinese_char_weight": 1.75,         # 中文字符权重
                "effective_chinese_limit": 36,       # 实际中文字符限制
                "split_optimization_rounds": 3       # 最大分割优化轮数
            }
        
        if self.netflix_style_presets is None:
            self.netflix_style_presets = {
                "chinese_font_size": 17,             # 中文字体大小
                "chinese_font_color": "&H00FFFF",    # Netflix黄色
                "outline_color": "&H000000",         # 黑色描边  
                "outline_width": 1,                  # 描边宽度
                "background_color": "&H33000000",    # 半透明背景
                "alignment_style": "bottom_center",  # 底部居中
                "line_preference": "single_line"     # 单行优先
            }
        
        if self.ai_optimization is None:
            self.ai_optimization = {
                "semantic_splitter": "netflix_grade",  # Netflix级语义分割
                "alignment_algorithm": "dtw_enhanced",  # DTW增强对齐
                "quality_validator": "multi_round",     # 多轮质量验证
                "prompt_templates": "netflix_standard"  # Netflix提示词模板
            }


class NetflixStylePresetsV2:
    """Netflix样式预设管理器 V2 - VideoLingo集成版本"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.logger = logger
        
        # 预定义样式预设
        self._style_presets = self._init_style_presets()
        
        # VideoLingo配置集成
        self.videolingo_config = VideoLingoNetflixConfig()
        
        self.logger.info("Netflix样式预设管理器V2已初始化 - VideoLingo标准集成")
    
    def _init_style_presets(self) -> Dict[str, NetflixStyleConfigV2]:
        """初始化样式预设库"""
        return {
            # Netflix标准样式 (VideoLingo版本)
            "netflix_standard": NetflixStyleConfigV2(),
            
            # Netflix高清样式
            "netflix_hd": NetflixStyleConfigV2(
                font_size=20,
                outline_width=2,
                margin_v=32
            ),
            
            # Netflix大字体样式 (视障用户友好)
            "netflix_large_text": NetflixStyleConfigV2(
                font_size=24,
                outline_width=2,
                background_opacity=0.4,
                margin_v=40
            ),
            
            # Netflix高对比度样式
            "netflix_high_contrast": NetflixStyleConfigV2(
                font_color="&H00FFFFFF",      # 纯白色
                outline_width=3,
                background_opacity=0.8,
                back_color="&H80000000"       # 更深的背景
            ),
            
            # VideoLingo专用样式
            "videolingo_netflix": NetflixStyleConfigV2(
                font_color="&H00FFFF",        # VideoLingo Netflix黄色
                font_size=17,                 # VideoLingo标准字体
                max_chars_per_line=36,        # VideoLingo 36字符限制
                single_line_preference=True,  # VideoLingo单行优先
                semantic_split_enabled=True   # VideoLingo语义分割
            )
        }
    
    def get_style_preset(self, preset_name: str) -> Optional[NetflixStyleConfigV2]:
        """获取指定样式预设"""
        return self._style_presets.get(preset_name)
    
    def get_videolingo_netflix_style(self) -> NetflixStyleConfigV2:
        """获取VideoLingo Netflix标准样式"""
        return self._style_presets["videolingo_netflix"]
    
    def get_all_presets(self) -> Dict[str, NetflixStyleConfigV2]:
        """获取所有样式预设"""
        return self._style_presets.copy()
    
    def add_custom_preset(self, name: str, style_config: NetflixStyleConfigV2) -> bool:
        """添加自定义样式预设"""
        try:
            self._style_presets[name] = style_config
            self.logger.info(f"自定义样式预设 '{name}' 已添加")
            return True
        except Exception as e:
            self.logger.error(f"添加自定义样式预设失败: {e}")
            return False
    
    def generate_srt_style(self, preset_name: str = "videolingo_netflix") -> str:
        """生成SRT格式样式字符串"""
        style = self.get_style_preset(preset_name)
        if not style:
            style = self.get_videolingo_netflix_style()
        
        # SRT格式不直接支持样式，返回样式描述
        return f"Netflix标准字幕样式 - 字体: {style.font_family} {style.font_size}px"
    
    def generate_ass_style(self, preset_name: str = "videolingo_netflix") -> str:
        """生成ASS格式样式字符串 - Netflix标准"""
        style = self.get_style_preset(preset_name)
        if not style:
            style = self.get_videolingo_netflix_style()
        
        # ASS格式样式字符串 (Netflix标准)
        ass_style = (
            f"Style: Netflix,{style.font_family},{style.font_size},"
            f"{style.font_color},{style.outline_color},{style.back_color},"
            f"0,0,0,0,100,100,0,0,{style.outline_width},0,"
            f"{style.alignment},{style.margin_l},{style.margin_r},{style.margin_v},1"
        )
        
        return ass_style
    
    def generate_webvtt_style(self, preset_name: str = "videolingo_netflix") -> str:
        """生成WebVTT格式样式 - Netflix标准"""
        style = self.get_style_preset(preset_name)
        if not style:
            style = self.get_videolingo_netflix_style()
        
        # WebVTT CSS样式
        webvtt_style = f"""
::cue {{
    font-family: {style.font_family};
    font-size: {style.font_size}px;
    color: {style.font_color_hex};
    text-stroke: {style.outline_width}px {style.outline_color_hex};
    background-color: {style.back_color_hex};
    text-align: center;
    line-height: {style.line_spacing};
}}"""
        
        return webvtt_style
    
    def export_config_to_json(self, preset_name: str, file_path: Optional[Path] = None) -> Dict[str, Any]:
        """导出样式配置为JSON格式"""
        style = self.get_style_preset(preset_name)
        if not style:
            style = self.get_videolingo_netflix_style()
        
        config_dict = {
            "netflix_style_config": asdict(style),
            "videolingo_integration": asdict(self.videolingo_config),
            "export_timestamp": str(Path(__file__).stat().st_mtime),
            "version": "2.0",
            "standard": "VideoLingo Netflix"
        }
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, ensure_ascii=False, indent=2)
                self.logger.info(f"样式配置已导出到: {file_path}")
            except Exception as e:
                self.logger.error(f"导出配置失败: {e}")
        
        return config_dict
    
    def validate_style_config(self, style: NetflixStyleConfigV2) -> Dict[str, Any]:
        """验证样式配置是否符合Netflix标准"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "netflix_compliance": True
        }
        
        # 检查字体大小
        if style.font_size < 12 or style.font_size > 30:
            validation_result["warnings"].append(f"字体大小 {style.font_size}px 可能不适合Netflix标准 (推荐12-30px)")
        
        # 检查Netflix黄色
        if style.font_color != "&H00FFFF":
            validation_result["warnings"].append("字体颜色不是Netflix标准黄色 (&H00FFFF)")
            validation_result["netflix_compliance"] = False
        
        # 检查36字符限制
        if style.max_chars_per_line != 36:
            validation_result["warnings"].append(f"每行字符数 {style.max_chars_per_line} 不符合VideoLingo Netflix标准 (36字符)")
            validation_result["netflix_compliance"] = False
        
        # 检查描边设置
        if style.outline_width < 1:
            validation_result["errors"].append("描边宽度过小，可能影响可读性")
            validation_result["valid"] = False
        
        return validation_result


# 工厂函数
def create_netflix_style_manager(config_path: Optional[Path] = None) -> NetflixStylePresetsV2:
    """创建Netflix样式预设管理器"""
    return NetflixStylePresetsV2(config_path)


def get_default_netflix_style() -> NetflixStyleConfigV2:
    """获取默认Netflix样式配置"""
    return NetflixStyleConfigV2()


def get_videolingo_netflix_style() -> NetflixStyleConfigV2:
    """获取VideoLingo Netflix样式配置"""
    manager = create_netflix_style_manager()
    return manager.get_videolingo_netflix_style()


# 测试函数
def test_netflix_style_presets():
    """测试Netflix样式预设功能"""
    manager = create_netflix_style_manager()
    
    print("🎨 Netflix样式预设V2测试结果：")
    print("=" * 60)
    
    # 测试所有预设
    for preset_name, style in manager.get_all_presets().items():
        print(f"\n📋 样式预设: {preset_name}")
        print(f"  字体颜色: {style.font_color} ({style.font_color_hex})")
        print(f"  字体大小: {style.font_size}px")
        print(f"  每行字符: {style.max_chars_per_line}")
        print(f"  描边宽度: {style.outline_width}px")
        
        # 验证配置
        validation = manager.validate_style_config(style)
        compliance = "✅" if validation["netflix_compliance"] else "⚠️"
        print(f"  Netflix兼容: {compliance}")
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"  ⚠️ {warning}")
    
    # 测试样式生成
    print(f"\n🎬 ASS样式字符串:")
    print(manager.generate_ass_style("videolingo_netflix"))
    
    print(f"\n🌐 WebVTT样式:")
    print(manager.generate_webvtt_style("videolingo_netflix"))


if __name__ == "__main__":
    test_netflix_style_presets()