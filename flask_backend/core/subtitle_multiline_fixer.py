"""
字幕多行显示问题修复模块
针对VideoLingo融合后的字幕生成优化
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SubtitleMultilineFixer:
    """字幕多行显示问题修复器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config_data" / "subtitle_multiline_fix_config.json"
        self.config = self._load_fix_config()
        
    def _load_fix_config(self) -> Dict[str, Any]:
        """加载修复配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return config_data.get("subtitle_multiline_fix_config", {})
        except Exception as e:
            logger.warning(f"加载修复配置失败，使用默认配置: {e}")
            return self._get_default_fix_config()
    
    def _get_default_fix_config(self) -> Dict[str, Any]:
        """获取默认修复配置"""
        return {
            "character_weight_adjustments": {
                "chinese": 2.0,
                "english": 1.0,
                "punctuation": 0.6,
                "space": 0.3
            },
            "line_control_rules": {
                "max_lines_strict": 2,
                "max_chars_per_line_chinese": 30,
                "enforce_line_limit": True
            }
        }
    
    def calculate_enhanced_char_weight(self, text: str) -> float:
        """
        计算增强的字符权重
        基于VideoLingo优化，解决多行显示问题
        """
        import unicodedata
        
        total_weight = 0.0
        char_weights = self.config.get("character_weight_adjustments", {})
        
        for char in text:
            # 获取字符的Unicode分类
            category = unicodedata.category(char)
            
            # 应用优化的权重规则
            if '\u4e00' <= char <= '\u9fff':  # 中文汉字范围
                weight = char_weights.get("chinese", 2.0)
            elif '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff':  # 日文
                weight = char_weights.get("japanese", 2.0)
            elif '\uac00' <= char <= '\ud7af':  # 韩文
                weight = char_weights.get("korean", 1.8)
            elif category.startswith('P'):  # 标点符号
                weight = char_weights.get("punctuation", 0.6)
            elif char == ' ':  # 空格
                weight = char_weights.get("space", 0.3)
            elif category.startswith('N'):  # 数字
                weight = char_weights.get("number", 0.8)
            else:  # 英文和其他字符
                weight = char_weights.get("english", 1.0)
            
            total_weight += weight
        
        return total_weight
    
    def validate_line_limits(self, text: str) -> Tuple[bool, str]:
        """
        验证字幕是否符合行数限制
        返回: (是否有效, 修正后的文本)
        """
        lines = text.split('\n')
        line_rules = self.config.get("line_control_rules", {})
        max_lines = line_rules.get("max_lines_strict", 2)
        
        if len(lines) <= max_lines:
            return True, text
        
        # 如果超过行数限制，尝试修正
        if line_rules.get("enforce_line_limit", True):
            # 强制合并到指定行数
            corrected_text = self._force_merge_lines(lines, max_lines)
            logger.warning(f"字幕超过{max_lines}行，已自动修正: {text[:50]}...")
            return False, corrected_text
        
        return False, text
    
    def _force_merge_lines(self, lines: List[str], max_lines: int) -> str:
        """强制将多行合并到指定行数"""
        if len(lines) <= max_lines:
            return '\n'.join(lines)
        
        # 简单策略：将多余的行合并到前面的行
        result_lines = []
        chars_per_line_limit = self.config.get("line_control_rules", {}).get("max_chars_per_line_chinese", 30)
        
        current_line = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 尝试合并到当前行
            test_line = current_line + (' ' if current_line else '') + line
            if self.calculate_enhanced_char_weight(test_line) <= chars_per_line_limit:
                current_line = test_line
            else:
                # 当前行已满，开始新行
                if current_line:
                    result_lines.append(current_line)
                current_line = line
                
                # 如果已经达到最大行数，强制合并剩余内容
                if len(result_lines) >= max_lines - 1:
                    break
        
        # 添加最后一行
        if current_line:
            result_lines.append(current_line)
        
        return '\n'.join(result_lines[:max_lines])
    
    def optimize_subtitle_text(self, text: str, max_weight_per_line: float = 30.0) -> str:
        """
        优化字幕文本，确保不会产生多行显示问题
        """
        # 1. 验证行数限制
        is_valid, corrected_text = self.validate_line_limits(text)
        
        # 2. 检查每行的字符权重
        lines = corrected_text.split('\n')
        optimized_lines = []
        
        for line in lines:
            line_weight = self.calculate_enhanced_char_weight(line)
            
            if line_weight <= max_weight_per_line:
                optimized_lines.append(line)
            else:
                # 行太长，需要智能分割
                split_lines = self._smart_split_line(line, max_weight_per_line)
                optimized_lines.extend(split_lines)
        
        # 3. 最终验证行数
        final_text = '\n'.join(optimized_lines)
        final_valid, final_corrected = self.validate_line_limits(final_text)
        
        return final_corrected
    
    def _smart_split_line(self, line: str, max_weight: float) -> List[str]:
        """智能分割过长的行"""
        if self.calculate_enhanced_char_weight(line) <= max_weight:
            return [line]
        
        # 查找最佳分割点
        best_split = len(line) // 2
        line_rules = self.config.get("line_control_rules", {})
        
        # 优先在标点符号处分割
        punctuation = "，。！？；："
        for i in range(len(line) // 2, len(line)):
            if line[i] in punctuation:
                if self.calculate_enhanced_char_weight(line[:i+1]) <= max_weight:
                    best_split = i + 1
                    break
        
        # 分割并递归处理
        first_part = line[:best_split].strip()
        second_part = line[best_split:].strip()
        
        result = []
        if first_part:
            result.extend(self._smart_split_line(first_part, max_weight))
        if second_part:
            result.extend(self._smart_split_line(second_part, max_weight))
        
        return result
    
    def get_resolution_adaptive_font_size(self, resolution: Tuple[int, int], base_font_size: int = 24) -> int:
        """
        根据分辨率自适应调整字体大小
        """
        width, height = resolution
        font_config = self.config.get("resolution_adaptive_font", {})
        
        if not font_config.get("enabled", True):
            return base_font_size
        
        # 计算缩放比例
        base_width, base_height = font_config.get("base_resolution", [1920, 1080])
        scale_factor = min(width / base_width, height / base_height)
        
        # 应用缩放
        adaptive_size = int(base_font_size * scale_factor)
        
        # 限制在合理范围内
        min_size = font_config.get("min_font_size", 16)
        max_size = font_config.get("max_font_size", 60)
        
        return max(min_size, min(adaptive_size, max_size))
    
    def apply_fix_to_subtitle_config(self, original_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将修复配置应用到原始字幕配置中
        """
        fixed_config = original_config.copy()
        
        # 更新字符权重
        char_weights = self.config.get("character_weight_adjustments", {})
        if "smart_processing" in fixed_config:
            if "character_weights" in fixed_config["smart_processing"]:
                fixed_config["smart_processing"]["character_weights"].update(char_weights)
        
        # 更新行控制规则
        line_rules = self.config.get("line_control_rules", {})
        fixed_config.update({
            "max_chars_per_line": line_rules.get("max_chars_per_line_chinese", 30),
            "max_lines": line_rules.get("max_lines_strict", 2),
            "enforce_line_limit": line_rules.get("enforce_line_limit", True)
        })
        
        return fixed_config


def apply_multiline_fix(subtitle_text: str, resolution: Tuple[int, int] = (1920, 1080)) -> str:
    """
    便捷函数：应用多行显示修复
    """
    fixer = SubtitleMultilineFixer()
    return fixer.optimize_subtitle_text(subtitle_text)


def get_fixed_font_size(resolution: Tuple[int, int], base_size: int = 24) -> int:
    """
    便捷函数：获取修复后的字体大小
    """
    fixer = SubtitleMultilineFixer()
    return fixer.get_resolution_adaptive_font_size(resolution, base_size)


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "这是一行很长的测试字幕，可能会导致多行显示问题，需要进行智能处理和优化。",
        "This is a very long subtitle line that might cause multiline display issues.",
        "短字幕测试",
        "多行\n字幕\n测试\n需要\n修复"
    ]
    
    fixer = SubtitleMultilineFixer()
    
    for i, test_text in enumerate(test_cases):
        print(f"\n测试案例 {i+1}: {test_text}")
        optimized = fixer.optimize_subtitle_text(test_text)
        print(f"优化后: {optimized}")
        print(f"字符权重: {fixer.calculate_enhanced_char_weight(optimized)}")
