"""
Netflix V2 增强字幕生成器 - Phase 4 工作流集成版本
集成Netflix V2配置管理系统的完整字幕生成解决方案
"""
import os
import re
# import pandas as pd  # 暂时注释掉以避免NumPy版本问题
import pysrt
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple, TYPE_CHECKING
from datetime import datetime
import logging
import dataclasses
import asyncio

# 总是定义备用函数，避免运行时错误
def get_logger_fallback(name, log_dir):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

class FileManagerFallback:
    def __init__(self, project_dir):
        from pathlib import Path
        self.project_dir = Path(project_dir)
        self.subtitles_dir = self.project_dir / "subtitles"
        self.subtitles_dir.mkdir(parents=True, exist_ok=True)

class SubtitleMultilineFixerFallback:
    def optimize_subtitle_text(self, text):
        return text
    def calculate_enhanced_char_weight(self, text):
        return len(text)

# 尝试导入真实的类，失败时使用备用类
try:
    from app.utils.logger import get_logger
except ImportError:
    get_logger = get_logger_fallback

try:
    from app.utils.file_manager import FileManager
except ImportError:
    FileManager = FileManagerFallback

try:
    from .subtitle_multiline_fixer import SubtitleMultilineFixer
except ImportError:
    SubtitleMultilineFixer = SubtitleMultilineFixerFallback

# 🎯 集成Netflix V2配置管理
try:
    from .netflix_v2_config_manager import NetflixV2ConfigManager, NetflixSubtitleConfig
    NETFLIX_V2_CONFIG_AVAILABLE = True
except ImportError:
    # 如果配置管理器不可用，提供占位符
    NETFLIX_V2_CONFIG_AVAILABLE = False
    
    class MockNetflixV2ConfigManager:
        def __init__(self, project_dir): pass
        def load_netflix_config(self, name=None): return None
        def list_available_configs(self): return {"templates": [], "user_configs": [], "global_config": []}
        def validate_config(self, config): return {"is_valid": True, "errors": [], "warnings": []}
        def create_config_from_template(self, template, name, customizations=None): return False
    
    NetflixV2ConfigManager = MockNetflixV2ConfigManager
    NetflixSubtitleConfig = None


class NetflixV2SubtitleGenerator:
    """
    Netflix V2 增强字幕生成器
    
    集成特性:
    - Netflix V2配置管理系统
    - 动态配置加载和验证
    - Netflix标准合规检查
    - 模板驱动的字幕生成
    - 实时配置切换
    """
    
    def __init__(self, project_dir: Path, netflix_config_name: Optional[str] = None):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # 🎯 初始化Netflix V2配置管理器
        self.netflix_config_manager = None
        self.netflix_config = None
        self.current_config_name = netflix_config_name or "default"
        
        self._initialize_netflix_config_system()
        
        # 初始化多行修复器
        self.multiline_fixer = SubtitleMultilineFixer()
        
        # 从Netflix配置加载配置参数
        self._load_subtitle_config_from_netflix()
        
        # 视频分辨率缓存 (用于字体大小自适应)
        self.video_resolution = None
        self.adaptive_font_size = 18  # 默认字体大小
        
        self.logger.info(f"Netflix V2字幕生成器初始化完成，使用配置: {self.current_config_name}")
        
    def _initialize_netflix_config_system(self):
        """初始化Netflix V2配置管理系统"""
        try:
            if NETFLIX_V2_CONFIG_AVAILABLE:
                self.netflix_config_manager = NetflixV2ConfigManager(self.project_dir)
                
                # 加载或创建指定配置
                if self.current_config_name and self.current_config_name != "default":
                    # 尝试加载指定配置
                    try:
                        self.netflix_config = self.netflix_config_manager.load_netflix_config(self.current_config_name)
                        self.logger.info(f"成功加载Netflix配置: {self.current_config_name}")
                    except Exception as e:
                        self.logger.warning(f"无法加载配置 {self.current_config_name}: {e}")
                        self.netflix_config = self.netflix_config_manager.load_netflix_config()  # 加载默认
                        self.current_config_name = "default"
                else:
                    # 使用默认配置
                    self.netflix_config = self.netflix_config_manager.load_netflix_config()
                    self.current_config_name = "default"
                    
                self.logger.info("Netflix V2配置系统初始化成功")
            else:
                self.logger.warning("Netflix V2配置管理系统不可用，使用传统配置")
                self.netflix_config = None
                
        except Exception as e:
            self.logger.error(f"Netflix V2配置系统初始化失败: {e}")
            self.netflix_config = None
    
    def _load_subtitle_config_from_netflix(self):
        """从Netflix配置加载字幕配置参数"""
        if self.netflix_config:
            # 🎯 使用Netflix V2配置
            self.subtitle_config = {
                "max_chars_per_line": self.netflix_config.max_chars_per_line,
                "max_lines": 2 if self.netflix_config.enable_semantic_splitting else 1,
                "min_display_time": self.netflix_config.min_duration,
                "max_display_time": self.netflix_config.max_duration,
                "words_per_second": 3.5,  # 可以添加到Netflix配置中
                "line_break_chars": "，。！？；：",
                "gap_threshold": self.netflix_config.gap_threshold,
                "enable_gap_filling": True,
                "enable_precise_alignment": True,
                "auto_punctuation_removal": True,
                "enable_multiline_fix": True,
                "chinese_weight": self.netflix_config.chinese_weight,
                "english_weight": self.netflix_config.english_weight,
                "punctuation_weight": self.netflix_config.punctuation_weight,
                "netflix_compliance": self.netflix_config.strict_netflix_compliance,
                "style_preset": self.netflix_config.style_preset,
                "font_color": self.netflix_config.font_color,
                "font_size": self.netflix_config.font_size,
                "outline_color": self.netflix_config.outline_color,
                "outline_width": self.netflix_config.outline_width,
            }
            
            self.logger.info(f"已从Netflix配置 '{self.current_config_name}' 加载字幕参数")
        else:
            # 🎯 使用传统配置作为后备
            self.subtitle_config = {
                "max_chars_per_line": 36,
                "max_lines": 2,
                "min_display_time": 1.0,
                "max_display_time": 8.0,
                "words_per_second": 3.5,
                "line_break_chars": "，。！？；：",
                "gap_threshold": 1.0,
                "enable_gap_filling": True,
                "enable_precise_alignment": True,
                "auto_punctuation_removal": True,
                "enable_multiline_fix": True,
                "chinese_weight": 1.75,
                "english_weight": 1.0,
                "punctuation_weight": 0.5,
                "netflix_compliance": False,
                "style_preset": "default",
                "font_color": "&H00FFFF",
                "font_size": 17,
                "outline_color": "&H000000",
                "outline_width": 1,
            }
            
            self.logger.info("使用传统字幕配置参数")
    
    def switch_netflix_config(self, config_name: str) -> bool:
        """
        切换Netflix配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            是否切换成功
        """
        try:
            if not self.netflix_config_manager:
                self.logger.warning("Netflix配置管理器不可用")
                return False
                
            # 加载新配置
            new_config = self.netflix_config_manager.load_netflix_config(config_name)
            
            # 检查配置是否成功加载
            if new_config is None:
                self.logger.error(f"无法加载配置: {config_name}")
                return False
            
            # 验证配置
            validation_result = self.netflix_config_manager.validate_config(new_config)
            if not validation_result.get("is_valid", False):
                self.logger.error(f"配置验证失败: {validation_result.get('errors', [])}")
                return False
            
            # 应用新配置
            self.netflix_config = new_config
            self.current_config_name = config_name
            self._load_subtitle_config_from_netflix()
            
            self.logger.info(f"成功切换到Netflix配置: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"切换Netflix配置失败: {e}")
            return False
    
    def get_available_netflix_configs(self) -> List[str]:
        """获取可用的Netflix配置列表"""
        try:
            if self.netflix_config_manager:
                configs_dict = self.netflix_config_manager.list_available_configs()
                config_names = []
                # 从模板和用户配置中提取名称
                for template in configs_dict.get("templates", []):
                    config_names.append(template.get("name", ""))
                for user_config in configs_dict.get("user_configs", []):
                    config_names.append(user_config.get("name", ""))
                return [name for name in config_names if name]
            else:
                return ["default"]
        except Exception as e:
            self.logger.error(f"获取配置列表失败: {e}")
            return ["default"]
    
    def get_netflix_templates(self) -> List[str]:
        """获取可用的Netflix模板列表"""
        try:
            if self.netflix_config_manager:
                configs_dict = self.netflix_config_manager.list_available_configs()
                template_names = []
                for template in configs_dict.get("templates", []):
                    template_names.append(template.get("name", ""))
                return [name for name in template_names if name]
            else:
                return []
        except Exception as e:
            self.logger.error(f"获取模板列表失败: {e}")
            return []
    
    def create_config_from_template(self, template_name: str, config_name: str) -> bool:
        """从模板创建新配置"""
        try:
            if not self.netflix_config_manager:
                self.logger.warning("Netflix配置管理器不可用")
                return False
                
            success = self.netflix_config_manager.create_config_from_template(template_name, config_name)
            if success:
                self.logger.info(f"成功从模板 '{template_name}' 创建配置 '{config_name}'")
            return success
            
        except Exception as e:
            self.logger.error(f"从模板创建配置失败: {e}")
            return False
    
    def validate_current_netflix_config(self) -> Dict[str, Any]:
        """验证当前Netflix配置"""
        try:
            if self.netflix_config_manager and self.netflix_config:
                validation_result = self.netflix_config_manager.validate_config(self.netflix_config)
                return {
                    "valid": validation_result.get("is_valid", False),
                    "config_name": self.current_config_name,
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", []),
                    "netflix_compliance": self.netflix_config.strict_netflix_compliance if self.netflix_config else False
                }
            else:
                return {
                    "valid": True,
                    "config_name": self.current_config_name,
                    "errors": [],
                    "warnings": ["Netflix配置系统不可用"],
                    "netflix_compliance": False
                }
        except Exception as e:
            return {
                "valid": False,
                "config_name": self.current_config_name,
                "errors": [str(e)],
                "warnings": [],
                "netflix_compliance": False
            }
    
    def _validate_subtitle_compliance(self, text: str) -> Dict[str, Any]:
        """
        验证字幕Netflix合规性
        
        Args:
            text: 字幕文本
            
        Returns:
            验证结果
        """
        validation_result = {
            "compliant": True,
            "issues": [],
            "metrics": {}
        }
        
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # 基本指标
            validation_result["metrics"] = {
                "line_count": len(lines),
                "max_chars_per_line": max([len(line) for line in lines]) if lines else 0,
                "char_weights": []
            }
            
            # Netflix配置验证
            if self.netflix_config and self.netflix_config.strict_netflix_compliance:
                max_lines = 2 if self.netflix_config.enable_semantic_splitting else 1
                max_chars = self.netflix_config.max_chars_per_line
                
                # 验证行数
                if len(lines) > max_lines:
                    validation_result["compliant"] = False
                    validation_result["issues"].append(f"行数超限: {len(lines)} > {max_lines}")
                
                # 验证字符权重
                for i, line in enumerate(lines):
                    char_weight = self._calculate_line_char_weight(line)
                    validation_result["metrics"]["char_weights"].append(char_weight)
                    
                    if char_weight > max_chars:
                        validation_result["compliant"] = False
                        validation_result["issues"].append(f"第{i+1}行字符权重超限: {char_weight:.1f} > {max_chars}")
            
            else:
                # 传统验证
                max_chars_traditional = self.subtitle_config["max_chars_per_line"]
                for i, line in enumerate(lines):
                    if len(line) > max_chars_traditional:
                        validation_result["compliant"] = False
                        validation_result["issues"].append(f"第{i+1}行字符数超限: {len(line)} > {max_chars_traditional}")
            
        except Exception as e:
            validation_result["compliant"] = False
            validation_result["issues"].append(f"验证过程出错: {e}")
        
        return validation_result
    
    def _calculate_line_char_weight(self, line: str) -> float:
        """计算行字符权重（基于Netflix配置）"""
        if not self.netflix_config:
            return len(line)  # 传统字符计数
            
        weight = 0.0
        for char in line:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                weight += self.netflix_config.chinese_weight
            elif char.isalpha():  # 英文字符
                weight += self.netflix_config.english_weight
            else:  # 标点符号和其他
                weight += self.netflix_config.punctuation_weight
        
        return weight
    
    def _optimize_subtitle_with_netflix_config(self, text: str) -> str:
        """使用Netflix配置优化字幕文本"""
        if not self.netflix_config:
            return text
        
        # 应用多行修复器（如果启用）
        if self.subtitle_config.get("enable_multiline_fix", True):
            optimized_text = self.multiline_fixer.optimize_subtitle_text(text)
        else:
            optimized_text = text
        
        # Netflix合规检查和自动修复
        if self.netflix_config.strict_netflix_compliance and self.netflix_config.auto_fix_issues:
            validation_result = self._validate_subtitle_compliance(optimized_text)
            
            if not validation_result["compliant"]:
                # 尝试自动修复
                optimized_text = self._auto_fix_compliance_issues(optimized_text, validation_result["issues"])
                self.logger.info(f"自动修复Netflix合规问题: {validation_result['issues']}")
        
        return optimized_text
    
    def _auto_fix_compliance_issues(self, text: str, issues: List[str]) -> str:
        """自动修复Netflix合规问题"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 如果行数过多，尝试合并
        if len(lines) > 2:
            # 简单策略：合并为两行
            mid_point = len(lines) // 2
            line1 = ''.join(lines[:mid_point])
            line2 = ''.join(lines[mid_point:])
            lines = [line1, line2]
        
        # 如果单行字符权重过大，尝试分割
        max_chars = self.netflix_config.max_chars_per_line if self.netflix_config else self.subtitle_config["max_chars_per_line"]
        
        optimized_lines = []
        for line in lines:
            if self._calculate_line_char_weight(line) > max_chars:
                # 尝试智能分割
                split_lines = self._smart_split_line(line, max_chars)
                optimized_lines.extend(split_lines)
            else:
                optimized_lines.append(line)
        
        # 确保不超过最大行数
        if len(optimized_lines) > 2:
            optimized_lines = optimized_lines[:2]
        
        return '\n'.join(optimized_lines)
    
    def _smart_split_line(self, line: str, max_weight: float) -> List[str]:
        """智能分割行（基于权重）"""
        if self._calculate_line_char_weight(line) <= max_weight:
            return [line]
        
        # 寻找合适的分割点
        split_chars = "，。！？；："
        best_split = len(line) // 2
        
        for i, char in enumerate(line):
            if char in split_chars:
                weight_before = self._calculate_line_char_weight(line[:i+1])
                weight_after = self._calculate_line_char_weight(line[i+1:])
                
                if weight_before <= max_weight and weight_after <= max_weight:
                    return [line[:i+1].strip(), line[i+1:].strip()]
        
        # 如果没有找到好的分割点，强制分割
        return [line[:best_split].strip(), line[best_split:].strip()]
    
    def remove_punctuation(self, text: str) -> str:
        """移除标点符号（用于文本对齐）"""
        # 保留基本的中英文字符和数字
        return re.sub(r'[^\w\u4e00-\u9fff]', '', text)
    
    def _split_text_to_segments(self, text: str) -> List[str]:
        """
        智能文本分段（基于Netflix配置）
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        if not text:
            return []
        
        # 基于Netflix配置决定分段策略
        if self.netflix_config and self.netflix_config.enable_semantic_splitting:
            # 语义分割模式
            segments = self._semantic_text_splitting(text)
        else:
            # 传统分割模式
            segments = self._traditional_text_splitting(text)
        
        # 应用Netflix配置优化
        optimized_segments = []
        for segment in segments:
            optimized_segment = self._optimize_subtitle_with_netflix_config(segment)
            if optimized_segment:
                optimized_segments.append(optimized_segment)
        
        return optimized_segments
    
    def _semantic_text_splitting(self, text: str) -> List[str]:
        """语义分割（Netflix标准）"""
        # 首先按句号等强分隔符分割
        sentences = re.split(r'[。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        segments = []
        max_chars = self.netflix_config.max_chars_per_line if self.netflix_config else self.subtitle_config["max_chars_per_line"]
        
        for sentence in sentences:
            if self._calculate_line_char_weight(sentence) <= max_chars:
                segments.append(sentence)
            else:
                # 进一步分割长句
                sub_segments = self._split_long_sentence(sentence, max_chars)
                segments.extend(sub_segments)
        
        return segments
    
    def _traditional_text_splitting(self, text: str) -> List[str]:
        """传统分割方式"""
        # 按标点符号分割
        segments = re.split(r'[，。！？；：]', text)
        segments = [s.strip() for s in segments if s.strip()]
        
        # 合并过短的片段
        merged_segments = []
        current_segment = ""
        
        for segment in segments:
            if not current_segment:
                current_segment = segment
            elif len(current_segment + segment) <= self.subtitle_config["max_chars_per_line"]:
                current_segment += segment
            else:
                merged_segments.append(current_segment)
                current_segment = segment
        
        if current_segment:
            merged_segments.append(current_segment)
        
        return merged_segments
    
    def _split_long_sentence(self, sentence: str, max_weight: float) -> List[str]:
        """分割长句子"""
        if self._calculate_line_char_weight(sentence) <= max_weight:
            return [sentence]
        
        # 尝试在逗号处分割
        parts = sentence.split('，')
        if len(parts) > 1:
            segments = []
            current = ""
            
            for part in parts:
                test_segment = current + ('，' if current else '') + part
                if self._calculate_line_char_weight(test_segment) <= max_weight:
                    current = test_segment
                else:
                    if current:
                        segments.append(current)
                    current = part
            
            if current:
                segments.append(current)
            
            return segments
        
        # 强制分割
        mid_point = len(sentence) // 2
        return [sentence[:mid_point], sentence[mid_point:]]
    
    # 继承原有的时间戳和生成方法...
    async def generate_enhanced_subtitles(
        self, 
        scripts_data: Dict[str, Any], 
        audio_data: Dict[str, Any],
        word_level_data: Optional[List[Dict]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        生成增强版字幕 - Netflix V2配置集成版本
        
        Args:
            scripts_data: 脚本数据
            audio_data: 音频数据
            word_level_data: 词级别时间数据（可选，用于精确对齐）
            progress_callback: 进度回调
        """
        try:
            self.logger.info(f"开始生成Netflix V2增强字幕，使用配置: {self.current_config_name}")
            
            # 验证当前Netflix配置
            config_validation = self.validate_current_netflix_config()
            if not config_validation["valid"]:
                self.logger.warning(f"Netflix配置验证失败: {config_validation['errors']}")
            
            # 确保字幕目录存在
            self.file_manager.subtitles_dir.mkdir(parents=True, exist_ok=True)
            
            scripts = scripts_data.get("scripts", [])
            all_subtitles = []
            subtitle_index = 1
            total_scripts = len(scripts)
            
            # 统计信息
            stats = {
                "total_segments": 0,
                "netflix_compliant_segments": 0,
                "auto_fixed_segments": 0,
                "config_used": self.current_config_name,
                "netflix_features_enabled": bool(self.netflix_config),
                "validation_results": []
            }
            
            for i, script in enumerate(scripts):
                if progress_callback:
                    progress = int((i / total_scripts) * 80)
                    progress_callback(progress)
                
                slide_number = script["slide_number"]
                script_content = script["script_content"]
                
                self.logger.info(f"生成第 {slide_number} 页字幕 (Netflix V2)")
                
                # 🎯 使用Netflix配置的智能分割
                segments = self._split_text_to_segments(script_content)
                stats["total_segments"] += len(segments)
                
                # 为每个段落生成字幕
                for j, segment in enumerate(segments):
                    # Netflix合规验证
                    validation_result = self._validate_subtitle_compliance(segment)
                    stats["validation_results"].append(validation_result)
                    
                    if validation_result["compliant"]:
                        stats["netflix_compliant_segments"] += 1
                    else:
                        # 如果启用自动修复
                        if self.netflix_config and self.netflix_config.auto_fix_issues:
                            segment = self._auto_fix_compliance_issues(segment, validation_result["issues"])
                            stats["auto_fixed_segments"] += 1
                    
                    # 创建字幕项
                    start_time = i * 5.0 + j * 3.0  # 简化的时间计算
                    end_time = start_time + 3.0
                    
                    subtitle = pysrt.SubRipItem(
                        index=subtitle_index,
                        start=pysrt.SubRipTime(seconds=int(start_time)),
                        end=pysrt.SubRipTime(seconds=int(end_time)),
                        text=segment
                    )
                    
                    all_subtitles.append(subtitle)
                    subtitle_index += 1
            
            # 保存字幕文件
            combined_srt = pysrt.SubRipFile(all_subtitles)
            subtitle_path = self.file_manager.subtitles_dir / f"netflix_v2_subtitle_{self.current_config_name}.srt"
            combined_srt.save(str(subtitle_path), encoding='utf-8')
            
            # 生成兼容性文件
            traditional_path = self.file_manager.subtitles_dir / "combined_subtitle.srt"
            combined_srt.save(str(traditional_path), encoding='utf-8')
            
            # 构建返回数据
            subtitle_data = {
                "subtitle_generation_completed": True,
                "netflix_v2_enhanced": True,
                "total_subtitles": len(all_subtitles),
                "subtitle_file": f"netflix_v2_subtitle_{self.current_config_name}.srt",
                "traditional_subtitle_file": "combined_subtitle.srt",
                "netflix_config_used": self.current_config_name,
                "netflix_compliance_rate": (stats["netflix_compliant_segments"] / max(stats["total_segments"], 1)) * 100,
                "auto_fixes_applied": stats["auto_fixed_segments"],
                "generation_timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "netflix_config_validation": config_validation,
                "config_details": {
                    "max_chars_per_line": self.subtitle_config["max_chars_per_line"],
                    "netflix_compliance": self.subtitle_config.get("netflix_compliance", False),
                    "style_preset": self.subtitle_config.get("style_preset", "default"),
                    "font_color": self.subtitle_config.get("font_color", "&H00FFFF"),
                    "font_size": self.subtitle_config.get("font_size", 17),
                }
            }
            
            if progress_callback:
                progress_callback(100)
            
            self.logger.info(f"Netflix V2增强字幕生成完成: {len(all_subtitles)} 个字幕项")
            self.logger.info(f"Netflix合规率: {subtitle_data['netflix_compliance_rate']:.1f}%")
            self.logger.info(f"自动修复次数: {stats['auto_fixed_segments']}")
            
            return subtitle_data
            
        except Exception as e:
            self.logger.error(f"Netflix V2增强字幕生成失败: {e}", exc_info=True)
            raise
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新字幕配置"""
        self.subtitle_config.update(new_config)
        self.logger.info(f"字幕配置已更新: {new_config}")
    
    def get_current_config_summary(self) -> Dict[str, Any]:
        """获取当前配置摘要"""
        return {
            "config_name": self.current_config_name,
            "netflix_config_available": bool(self.netflix_config),
            "subtitle_config": self.subtitle_config.copy(),
            "available_configs": self.get_available_netflix_configs(),
            "available_templates": self.get_netflix_templates(),
            "validation_status": self.validate_current_netflix_config()
        }