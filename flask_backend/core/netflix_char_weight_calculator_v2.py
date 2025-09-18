"""
Netflix字符权重计算器 V2 - 36字符精确控制版本
基于VideoLingo-3.0.0标准，实现36个中文字符/行的精确控制
集成Phase 1技术基础建设的核心算法
"""
import re
import unicodedata
import math
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetflixCharacterConfig:
    """Netflix字符配置 - VideoLingo标准"""
    
    # VideoLingo核心参数 (基于VideoLingo-3.0.0标准)
    MAX_LENGTH: int = 75                    # VideoLingo内部计算基准
    TARGET_MULTIPLIER: float = 1.2          # 翻译长度系数
    CHINESE_CHAR_WEIGHT: float = 1.75       # 中文字符权重
    EFFECTIVE_CHINESE_LIMIT: int = 36       # 实际中文字符限制 (75÷1.75÷1.2≈36)
    
    # Netflix实际显示限制 (按有效中文字符计算)
    NETFLIX_MAX_EFFECTIVE_CHARS: int = 36   # Netflix标准: 36个中文字符/行
    
    # 精细化权重配置
    fullwidth_weight: float = 1.75          # 全角字符权重
    halfwidth_weight: float = 1.0           # 半角字符权重
    punctuation_weight: float = 0.8         # 标点符号权重
    space_weight: float = 0.3               # 空格权重
    number_weight: float = 0.9              # 数字权重
    
    # Netflix样式配置
    font_size: int = 17                     # Netflix标准字体大小
    line_preference: str = "single_line"    # 优先单行显示
    
    # 分割优化配置
    max_optimization_rounds: int = 3        # 最大分割优化轮数
    semantic_split_enabled: bool = True     # 启用语义分割
    auto_quality_check: bool = True         # 自动质量检查


class NetflixCharWeightCalculatorV2:
    """Netflix字符权重计算器 V2 - 36字符精确控制"""
    
    def __init__(self, config: Optional[NetflixCharacterConfig] = None):
        self.config = config or NetflixCharacterConfig()
        
        # 字符分类缓存
        self._char_cache = {}
        
        # 构建Unicode范围映射
        self._unicode_ranges = self._build_unicode_ranges()
        
        logger.info(f"Netflix字符权重计算器V2已初始化 - 目标限制: {self.config.EFFECTIVE_CHINESE_LIMIT}个中文字符/行")
    
    def _build_unicode_ranges(self) -> Dict[str, List[Tuple[int, int]]]:
        """构建Unicode字符范围映射"""
        return {
            'chinese': [
                (0x4E00, 0x9FFF),    # CJK统一汉字
                (0x3400, 0x4DBF),    # CJK扩展A
                (0x20000, 0x2A6DF),  # CJK扩展B
                (0x2A700, 0x2B73F),  # CJK扩展C
                (0x2B740, 0x2B81F),  # CJK扩展D
                (0x2B820, 0x2CEAF),  # CJK扩展E
                (0x2CEB0, 0x2EBEF),  # CJK扩展F
            ],
            'fullwidth_punctuation': [
                (0xFF01, 0xFF5E),    # 全角ASCII
                (0x3000, 0x303F),    # CJK符号和标点
                (0xFF00, 0xFFEF),    # 半角和全角形式
            ],
            'japanese': [
                (0x3040, 0x309F),    # 平假名
                (0x30A0, 0x30FF),    # 片假名
            ],
            'korean': [
                (0xAC00, 0xD7AF),    # 韩文音节
                (0x1100, 0x11FF),    # 韩文字母
            ]
        }
    
    def _get_char_category(self, char: str) -> str:
        """获取字符分类 - 高性能版本"""
        if char in self._char_cache:
            return self._char_cache[char]
        
        char_code = ord(char)
        category = self._classify_char_by_unicode(char_code)
        
        # 缓存结果
        self._char_cache[char] = category
        return category
    
    def _classify_char_by_unicode(self, char_code: int) -> str:
        """基于Unicode代码点分类字符"""
        # 检查中文字符
        for start, end in self._unicode_ranges['chinese']:
            if start <= char_code <= end:
                return 'chinese'
        
        # 检查全角符号
        for start, end in self._unicode_ranges['fullwidth_punctuation']:
            if start <= char_code <= end:
                return 'fullwidth_punctuation'
        
        # 检查日文字符
        for start, end in self._unicode_ranges['japanese']:
            if start <= char_code <= end:
                return 'japanese'
        
        # 检查韩文字符
        for start, end in self._unicode_ranges['korean']:
            if start <= char_code <= end:
                return 'korean'
        
        # ASCII字符检查
        if 32 <= char_code <= 126:
            if char_code == 32:  # 空格
                return 'space'
            elif 48 <= char_code <= 57:  # 数字
                return 'number'
            elif (33 <= char_code <= 47) or (58 <= char_code <= 64) or (91 <= char_code <= 96) or (123 <= char_code <= 126):
                return 'punctuation'
            else:
                return 'halfwidth'
        
        # 其他情况
        return 'other'
    
    def get_char_weight(self, char: str) -> float:
        """获取单个字符的精确权重"""
        category = self._get_char_category(char)
        
        weight_mapping = {
            'chinese': self.config.CHINESE_CHAR_WEIGHT,
            'japanese': self.config.CHINESE_CHAR_WEIGHT,  # 日文使用相同权重
            'korean': self.config.CHINESE_CHAR_WEIGHT,    # 韩文使用相同权重
            'fullwidth_punctuation': self.config.fullwidth_weight,
            'halfwidth': self.config.halfwidth_weight,
            'number': self.config.number_weight,
            'punctuation': self.config.punctuation_weight,
            'space': self.config.space_weight,
            'other': self.config.halfwidth_weight
        }
        
        return weight_mapping.get(category, 1.0)
    
    def calc_precise_length(self, text: str) -> float:
        """计算文本的精确显示长度 - VideoLingo标准"""
        if not text:
            return 0.0
        
        total_weight = 0.0
        for char in text:
            total_weight += self.get_char_weight(char)
        
        return total_weight
    
    def is_netflix_compliant(self, text: str) -> bool:
        """检查文本是否符合Netflix 36字符标准 - 按有效中文字符计算"""
        effective_chars = self.get_effective_chinese_chars(text)
        return effective_chars <= self.config.NETFLIX_MAX_EFFECTIVE_CHARS
    
    def get_effective_chinese_chars(self, text: str) -> int:
        """计算有效中文字符数 - Netflix标准"""
        total_weight = self.calc_precise_length(text)
        # 按照VideoLingo公式: 有效中文字符 = 总权重 ÷ 权重系数 ÷ 目标系数
        effective_chars = total_weight / self.config.CHINESE_CHAR_WEIGHT / self.config.TARGET_MULTIPLIER
        return int(math.ceil(effective_chars))
    
    def analyze_text_composition(self, text: str) -> Dict[str, Any]:
        """分析文本组成 - 详细统计"""
        if not text:
            return {
                'total_length': 0,
                'total_weight': 0.0,
                'effective_chinese_chars': 0,
                'netflix_compliant': True,
                'composition': {},
                'recommendations': []
            }
        
        # 字符组成统计
        composition = {
            'chinese': 0,
            'fullwidth_punctuation': 0,
            'halfwidth': 0,
            'number': 0,
            'punctuation': 0,
            'space': 0,
            'other': 0
        }
        
        total_weight = 0.0
        for char in text:
            category = self._get_char_category(char)
            composition[category] = composition.get(category, 0) + 1
            total_weight += self.get_char_weight(char)
        
        effective_chinese_chars = self.get_effective_chinese_chars(text)
        netflix_compliant = self.is_netflix_compliant(text)
        
        # 生成建议
        recommendations = []
        if effective_chinese_chars > self.config.NETFLIX_MAX_EFFECTIVE_CHARS:
            recommendations.append(f"建议缩短文本，当前{effective_chinese_chars}字符，超出{self.config.NETFLIX_MAX_EFFECTIVE_CHARS}字符限制")
        
        if total_weight > self.config.MAX_LENGTH:
            recommendations.append(f"VideoLingo显示长度过长({total_weight:.1f})，建议控制在{self.config.MAX_LENGTH}以内")
        
        return {
            'total_length': len(text),
            'total_weight': total_weight,
            'effective_chinese_chars': effective_chinese_chars,
            'netflix_compliant': netflix_compliant,
            'composition': composition,
            'recommendations': recommendations,
            'weight_breakdown': {
                f"{category}({count}字符)": count * self.get_char_weight(text[0] if text else '')
                for category, count in composition.items() if count > 0
            }
        }
    
    def split_to_netflix_lines(self, text: str, prefer_single_line: bool = True) -> List[str]:
        """按Netflix标准分割文本为多行"""
        if not text:
            return []
        
        # 如果文本符合单行标准，直接返回
        if self.is_netflix_compliant(text) and prefer_single_line:
            return [text]
        
        # 简单的断句分割 (基于标点符号)
        sentences = self._split_by_punctuation(text)
        lines = []
        current_line = ""
        
        for sentence in sentences:
            # 尝试添加到当前行
            test_line = current_line + sentence if current_line else sentence
            
            if self.is_netflix_compliant(test_line):
                current_line = test_line
            else:
                # 当前行已满，开始新行
                if current_line:
                    lines.append(current_line.strip())
                current_line = sentence
        
        # 添加最后一行
        if current_line:
            lines.append(current_line.strip())
        
        return lines
    
    def _split_by_punctuation(self, text: str) -> List[str]:
        """基于标点符号分割文本"""
        # Netflix常用断句符号
        punctuation_pattern = r'([，。！？；：])'
        parts = re.split(punctuation_pattern, text)
        
        sentences = []
        for i in range(0, len(parts), 2):
            sentence = parts[i]
            if i + 1 < len(parts):
                sentence += parts[i + 1]  # 添加标点符号
            if sentence.strip():
                sentences.append(sentence)
        
        return sentences
    
    def optimize_for_netflix(self, text: str) -> Dict[str, Any]:
        """针对Netflix标准优化文本"""
        analysis = self.analyze_text_composition(text)
        
        # 如果已经符合标准，直接返回
        if analysis['netflix_compliant']:
            return {
                'original_text': text,
                'optimized_text': text,
                'optimization_applied': False,
                'analysis': analysis,
                'lines': [text]
            }
        
        # 尝试分割优化
        optimized_lines = self.split_to_netflix_lines(text)
        
        return {
            'original_text': text,
            'optimized_text': '\n'.join(optimized_lines),
            'optimization_applied': True,
            'analysis': analysis,
            'lines': optimized_lines,
            'line_count': len(optimized_lines),
            'max_line_weight': max(self.calc_precise_length(line) for line in optimized_lines) if optimized_lines else 0
        }


# 工厂函数
def create_netflix_calculator(config: Optional[NetflixCharacterConfig] = None) -> NetflixCharWeightCalculatorV2:
    """创建Netflix字符权重计算器实例"""
    return NetflixCharWeightCalculatorV2(config)


# 快速测试函数
def test_netflix_char_calculator():
    """测试Netflix字符权重计算器"""
    calculator = create_netflix_calculator()
    
    # 测试案例
    test_cases = [
        "这是一个测试字幕",
        "这是一个测试字幕，包含标点符号！",
        "这是一个包含English和中文的混合字幕测试",
        "这是一个非常长的测试字幕，用来验证是否会超出36个中文字符的限制标准",
        "Test English subtitle with Chinese 中文字符",
    ]
    
    print("🎯 Netflix字符权重计算器V2测试结果：")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {text}")
        analysis = calculator.analyze_text_composition(text)
        optimization = calculator.optimize_for_netflix(text)
        
        print(f"  字符总数: {analysis['total_length']}")
        print(f"  显示权重: {analysis['total_weight']:.2f}")
        print(f"  有效中文字符: {analysis['effective_chinese_chars']}")
        print(f"  Netflix兼容: {'✅' if analysis['netflix_compliant'] else '❌'}")
        
        if optimization['optimization_applied']:
            print(f"  优化后行数: {optimization['line_count']}")
            print(f"  优化后内容: {optimization['optimized_text']}")


if __name__ == "__main__":
    test_netflix_char_calculator()