"""
Netflix字幕功能API集成示例 - Phase 1与现有系统的集成接口
为Phase 2做准备，展示如何将Netflix V2组件集成到现有API中
"""
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict
import logging

# Phase 1 Netflix核心组件
try:
    from .netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from .netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2
    from .netflix_semantic_splitter_v2 import NetflixSemanticSplitterV2, SemanticSplitConfig
    from .netflix_quality_validator_v2 import NetflixQualityValidatorV2, ValidationLevel
except ImportError:
    from netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2
    from netflix_semantic_splitter_v2 import NetflixSemanticSplitterV2, SemanticSplitConfig
    from netflix_quality_validator_v2 import NetflixQualityValidatorV2, ValidationLevel

logger = logging.getLogger(__name__)


class NetflixSubtitleProcessor:
    """
    Netflix字幕处理器 - Phase 1功能的统一API接口
    提供简洁的API接口供外部系统调用
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Netflix字幕处理器
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        
        # 初始化核心组件
        self._init_components()
        
        logger.info("Netflix字幕处理器初始化完成")
    
    def _init_components(self):
        """初始化所有核心组件"""
        try:
            # 字符权重计算器
            char_config = NetflixCharacterConfig()
            if "character_config" in self.config:
                char_config = NetflixCharacterConfig(**self.config["character_config"])
            self.char_calculator = NetflixCharWeightCalculatorV2(char_config)
            
            # 样式预设管理器
            self.style_manager = NetflixStylePresetsV2()
            
            # 语义分割器
            self.semantic_splitter = NetflixSemanticSplitterV2(self.char_calculator)
            
            # 质量验证器
            self.quality_validator = NetflixQualityValidatorV2(
                char_calculator=self.char_calculator,
                style_manager=self.style_manager
            )
            
            logger.info("所有Netflix核心组件初始化成功")
            
        except Exception as e:
            logger.error(f"Netflix核心组件初始化失败: {e}")
            raise
    
    def process_subtitle(self, text: str, style_preset: str = "videolingo_netflix") -> Dict[str, Any]:
        """
        处理单条字幕文本 - 主要API接口
        
        Args:
            text: 字幕文本
            style_preset: 样式预设名称
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理字幕: {text[:30]}...")
            
            # 1. 字符权重分析
            char_analysis = self.char_calculator.analyze_text_composition(text)
            
            # 2. 智能分割
            split_result = self.semantic_splitter.smart_split(text)
            
            # 3. 样式配置
            if style_preset == "videolingo_netflix":
                style_config = self.style_manager.get_videolingo_netflix_style()
            else:
                # 获取其他预设
                all_presets = self.style_manager.get_all_presets()
                style_config = all_presets.get(style_preset, 
                                             self.style_manager.get_videolingo_netflix_style())
            
            # 4. 质量验证
            validation_report = self.quality_validator.comprehensive_validate(
                text, split_result.segments
            )
            
            # 5. 生成样式字符串
            ass_style = self.style_manager.generate_ass_style(style_preset)
            webvtt_style = self.style_manager.generate_webvtt_style(style_preset)
            
            # 构造返回结果
            result = {
                "status": "success",
                "original_text": text,
                "character_analysis": char_analysis,
                "split_result": {
                    "segments": split_result.segments,
                    "segment_count": len(split_result.segments),
                    "optimization_rounds": split_result.optimization_rounds,
                    "quality_score": split_result.quality_score,
                    "netflix_compliant": split_result.netflix_compliant,
                    "split_method": "semantic_optimization"
                },
                "style_config": asdict(style_config),
                "style_strings": {
                    "ass": ass_style,
                    "webvtt": webvtt_style
                },
                "validation": {
                    "total_score": validation_report.total_score,
                    "netflix_compliant": validation_report.netflix_compliant,
                    "issues_count": len(validation_report.issues),
                    "issues": [asdict(issue) for issue in validation_report.issues],
                    "suggestions": validation_report.suggestions
                },
                "processing_metadata": {
                    "processor_version": "2.0",
                    "netflix_standard": True,
                    "videolingo_compatible": True
                }
            }
            
            logger.info(f"字幕处理完成，质量评分: {validation_report.total_score}")
            return result
            
        except Exception as e:
            logger.error(f"字幕处理失败: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "original_text": text
            }
    
    def batch_process_subtitles(self, subtitles: List[str], 
                               style_preset: str = "videolingo_netflix") -> List[Dict[str, Any]]:
        """
        批量处理字幕文本
        
        Args:
            subtitles: 字幕文本列表
            style_preset: 样式预设名称
            
        Returns:
            处理结果列表
        """
        results = []
        total_count = len(subtitles)
        
        logger.info(f"开始批量处理{total_count}条字幕")
        
        for i, subtitle in enumerate(subtitles, 1):
            logger.info(f"处理进度: {i}/{total_count}")
            result = self.process_subtitle(subtitle, style_preset)
            result["batch_index"] = i
            results.append(result)
        
        logger.info(f"批量处理完成，共{total_count}条字幕")
        return results
    
    def validate_netflix_compliance(self, text: str) -> Dict[str, Any]:
        """
        快速Netflix标准兼容性检查
        
        Args:
            text: 字幕文本
            
        Returns:
            兼容性检查结果
        """
        try:
            # 字符权重检查
            is_compliant = self.char_calculator.is_netflix_compliant(text)
            effective_chars = self.char_calculator.get_effective_chinese_chars(text)
            
            # 如果不兼容，尝试分割
            split_needed = False
            suggested_segments = []
            
            if not is_compliant:
                split_result = self.semantic_splitter.smart_split(text)
                split_needed = True
                suggested_segments = split_result.segments
            
            return {
                "original_text": text,
                "netflix_compliant": is_compliant,
                "effective_chars": effective_chars,
                "max_allowed_chars": 36,
                "split_needed": split_needed,
                "suggested_segments": suggested_segments,
                "segment_count": len(suggested_segments) if split_needed else 1
            }
            
        except Exception as e:
            logger.error(f"Netflix兼容性检查失败: {e}")
            return {
                "error": str(e),
                "netflix_compliant": False
            }
    
    def get_available_styles(self) -> Dict[str, Any]:
        """
        获取可用的样式预设
        
        Returns:
            样式预设信息
        """
        try:
            all_presets = self.style_manager.get_all_presets()
            
            result = {
                "available_presets": list(all_presets.keys()),
                "default_preset": "videolingo_netflix",
                "preset_details": {}
            }
            
            # 获取每个预设的详细信息
            for preset_name in all_presets:
                preset_config = all_presets[preset_name]
                result["preset_details"][preset_name] = {
                    "font_color": preset_config.font_color,
                    "font_size": preset_config.font_size,
                    "max_chars_per_line": preset_config.max_chars_per_line,
                    "description": f"Netflix {preset_name.replace('netflix_', '').replace('_', ' ').title()} Style"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"获取样式预设失败: {e}")
            return {"error": str(e)}
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理器统计信息
        
        Returns:
            统计信息
        """
        return {
            "processor_version": "2.0",
            "netflix_standard_version": "Phase 1",
            "videolingo_integration": True,
            "supported_features": [
                "36字符精确控制",
                "Netflix黄色样式",
                "智能语义分割",
                "多轮优化算法",
                "质量验证系统",
                "ASS/WebVTT样式生成"
            ],
            "character_weight_formula": "VideoLingo 1.75x中文权重",
            "max_effective_chars": 36,
            "default_style": "Netflix黄色(&H00FFFF)",
            "validation_rules": 11
        }


# 工厂函数 - 简化外部调用
def create_netflix_processor(config: Optional[Dict[str, Any]] = None) -> NetflixSubtitleProcessor:
    """
    创建Netflix字幕处理器实例
    
    Args:
        config: 可选的配置参数
        
    Returns:
        Netflix字幕处理器实例
    """
    return NetflixSubtitleProcessor(config)


# API兼容性包装函数 - 为现有系统提供兼容接口
def netflix_subtitle_api(text: str, style: str = "videolingo_netflix", 
                        config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Netflix字幕处理API - 兼容性包装函数
    为现有系统提供简单的函数调用接口
    
    Args:
        text: 字幕文本
        style: 样式预设名称
        config: 可选配置
        
    Returns:
        处理结果
    """
    processor = create_netflix_processor(config)
    return processor.process_subtitle(text, style)


def netflix_compliance_check(text: str) -> bool:
    """
    快速Netflix兼容性检查 - 简化版API
    
    Args:
        text: 字幕文本
        
    Returns:
        是否兼容Netflix标准
    """
    processor = create_netflix_processor()
    result = processor.validate_netflix_compliance(text)
    return result.get("netflix_compliant", False)


# 示例用法
if __name__ == "__main__":
    # 创建处理器
    processor = create_netflix_processor()
    
    # 测试字幕
    test_subtitle = "这是一个Netflix字幕处理示例，展示Phase 1技术基础建设的成果！"
    
    # 处理字幕
    result = processor.process_subtitle(test_subtitle)
    
    # 输出结果
    print("🎬 Netflix字幕处理API示例")
    print("=" * 50)
    print(f"原文: {result['original_text']}")
    print(f"分割段数: {result['split_result']['segment_count']}")
    print(f"质量评分: {result['validation']['total_score']}")
    print(f"Netflix兼容: {result['validation']['netflix_compliant']}")
    
    for i, segment in enumerate(result['split_result']['segments'], 1):
        print(f"第{i}段: {segment}")
    
    print("\n✅ API集成示例完成！")