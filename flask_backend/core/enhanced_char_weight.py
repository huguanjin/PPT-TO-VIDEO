"""
字符权重计算优化模块
基于VideoLingo项目的calc_len函数改进
提供更精确的多语言字符显示权重计算
"""

import unicodedata
from typing import Dict, Set, Any
import logging

logger = logging.getLogger(__name__)


class EnhancedCharacterWeightCalculator:
    """
    增强的字符权重计算器
    基于VideoLingo算法优化，支持更多字符类型和语言
    """
    
    # Unicode字符分类到权重的映射
    CATEGORY_WEIGHTS = {
        # 中日韩字符 (东亚字符)
        'Lo': 1.75,    # Letter, other (中日韩汉字等)
        'Lm': 1.75,    # Letter, modifier (中日韩修饰符)
        
        # 标点符号
        'Po': 1.0,     # Punctuation, other
        'Ps': 1.0,     # Punctuation, open (括号等)
        'Pe': 1.0,     # Punctuation, close
        'Pc': 1.0,     # Punctuation, connector (下划线等)
        'Pd': 1.0,     # Punctuation, dash
        'Pi': 1.0,     # Punctuation, initial quote
        'Pf': 1.0,     # Punctuation, final quote
        
        # 数字
        'Nd': 1.0,     # Number, decimal digit
        'Nl': 1.0,     # Number, letter
        'No': 1.0,     # Number, other
        
        # 拉丁字母
        'Lu': 1.0,     # Letter, uppercase
        'Ll': 1.0,     # Letter, lowercase
        'Lt': 1.0,     # Letter, titlecase
        
        # 符号
        'Sm': 1.0,     # Symbol, math
        'Sc': 1.0,     # Symbol, currency
        'Sk': 1.0,     # Symbol, modifier
        'So': 1.2,     # Symbol, other (包括emoji等)
        
        # 分隔符
        'Zs': 1.0,     # Separator, space
        'Zl': 1.0,     # Separator, line
        'Zp': 1.0,     # Separator, paragraph
        
        # 控制字符
        'Cc': 0.0,     # Other, control
        'Cf': 0.0,     # Other, format
        'Cs': 0.0,     # Other, surrogate
        'Co': 0.0,     # Other, private use
        'Cn': 0.0,     # Other, not assigned
        
        # 标记字符 (结合字符)
        'Mn': 0.5,     # Mark, nonspacing (重音符号等)
        'Mc': 1.0,     # Mark, spacing combining
        'Me': 1.0,     # Mark, enclosing
    }
    
    # 特定Unicode范围的权重覆盖
    UNICODE_RANGE_WEIGHTS = {
        # 中日韩统一汉字
        (0x4E00, 0x9FFF): 1.75,    # CJK Unified Ideographs
        (0x3400, 0x4DBF): 1.75,    # CJK Extension A
        (0x20000, 0x2A6DF): 1.75,  # CJK Extension B
        (0x2A700, 0x2B73F): 1.75,  # CJK Extension C
        (0x2B740, 0x2B81F): 1.75,  # CJK Extension D
        (0x2B820, 0x2CEAF): 1.75,  # CJK Extension E
        
        # 日文假名
        (0x3040, 0x309F): 1.75,    # 平假名
        (0x30A0, 0x30FF): 1.75,    # 片假名
        (0x31F0, 0x31FF): 1.75,    # 片假名语音扩展
        
        # 韩文
        (0xAC00, 0xD7A3): 1.5,     # 韩文音节
        (0x1100, 0x11FF): 1.5,     # 韩文字母
        (0x3130, 0x318F): 1.5,     # 韩文兼容字母
        (0xA960, 0xA97F): 1.5,     # 韩文字母扩展A
        (0xD7B0, 0xD7FF): 1.5,     # 韩文字母扩展B
        
        # 全角符号
        (0xFF01, 0xFF5E): 1.75,    # 全角ASCII
        (0xFF61, 0xFFDC): 1.5,     # 半角片假名
        (0xFFE0, 0xFFE6): 1.75,    # 全角符号
        
        # 阿拉伯文
        (0x0600, 0x06FF): 1.3,     # 阿拉伯文
        (0x0750, 0x077F): 1.3,     # 阿拉伯文补充
        
        # 泰文
        (0x0E00, 0x0E7F): 1.2,     # 泰文
        
        # 天城文 (印地语等)
        (0x0900, 0x097F): 1.2,     # 天城文
        
        # 西里尔文 (俄文等)
        (0x0400, 0x04FF): 1.1,     # 西里尔文
        
        # 希腊文
        (0x0370, 0x03FF): 1.1,     # 希腊文
        
        # Emoji和符号
        (0x1F600, 0x1F64F): 1.8,   # 表情符号
        (0x1F300, 0x1F5FF): 1.8,   # 杂项符号和象形文字
        (0x1F680, 0x1F6FF): 1.8,   # 交通和地图符号
        (0x1F700, 0x1F77F): 1.8,   # 炼金术符号
        (0x2600, 0x26FF): 1.5,     # 杂项符号
        (0x2700, 0x27BF): 1.5,     # 装饰符号
        
        # 数学符号
        (0x2200, 0x22FF): 1.3,     # 数学运算符
        (0x2190, 0x21FF): 1.3,     # 箭头
        (0x2100, 0x214F): 1.3,     # 字母式符号
    }
    
    @classmethod
    def get_char_weight(cls, char: str) -> float:
        """
        获取单个字符的显示权重
        基于Unicode分类和特定范围的优化算法
        
        Args:
            char: 单个字符
            
        Returns:
            字符的显示权重
        """
        if not char:
            return 0.0
        
        # 处理多字节字符（如组合emoji）
        if len(char) > 1:
            # 对于组合字符，取最大权重并稍微增加
            max_weight = max(cls.get_char_weight(c) for c in char)
            return min(max_weight * 1.2, 2.0)  # 限制最大权重
        
        code = ord(char)
        
        # 首先检查特定Unicode范围
        for (start, end), weight in cls.UNICODE_RANGE_WEIGHTS.items():
            if start <= code <= end:
                return weight
        
        # 然后使用Unicode分类
        try:
            category = unicodedata.category(char)
            if category in cls.CATEGORY_WEIGHTS:
                return cls.CATEGORY_WEIGHTS[category]
        except Exception as e:
            logger.debug(f"Unicode分类检查失败: {char} -> {e}")
        
        # 默认返回1.0
        return 1.0
    
    @classmethod
    def calc_text_weight(cls, text: str) -> float:
        """
        计算文本总权重
        支持组合字符和emoji的精确计算
        
        Args:
            text: 输入文本
            
        Returns:
            文本的总显示权重
        """
        if not text:
            return 0.0
        
        total_weight = 0.0
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # 检查是否是emoji组合或其他多字节Unicode序列
            if i + 1 < len(text):
                # 检查变异选择器、肤色修饰符等
                next_char = text[i + 1]
                if (0xFE00 <= ord(next_char) <= 0xFE0F or  # 变异选择器
                    0x1F3FB <= ord(next_char) <= 0x1F3FF or  # 肤色修饰符
                    next_char == '\u200D'):  # 零宽连接符
                    # 寻找完整的emoji序列
                    j = i + 1
                    while j < len(text):
                        if (ord(text[j]) in range(0xFE00, 0xFE10) or
                            ord(text[j]) in range(0x1F3FB, 0x1F400) or
                            text[j] == '\u200D'):
                            j += 1
                        else:
                            break
                    
                    # 计算整个序列的权重
                    sequence = text[i:j]
                    total_weight += cls.get_char_weight(sequence)
                    i = j
                    continue
            
            # 单个字符
            total_weight += cls.get_char_weight(char)
            i += 1
        
        return total_weight
    
    @classmethod
    def get_char_info(cls, char: str) -> Dict[str, Any]:
        """
        获取字符的详细信息（用于调试和分析）
        
        Args:
            char: 单个字符
            
        Returns:
            包含字符信息的字典
        """
        if not char:
            return {'char': '', 'weight': 0.0, 'info': 'Empty'}
        
        try:
            code = ord(char) if len(char) == 1 else ord(char[0])
            category = unicodedata.category(char)
            name = unicodedata.name(char, 'UNKNOWN')
            weight = cls.get_char_weight(char)
            
            # 检查属于哪个Unicode范围
            range_info = "General"
            for (start, end), range_weight in cls.UNICODE_RANGE_WEIGHTS.items():
                if start <= code <= end:
                    range_info = f"Range({start:04X}-{end:04X})"
                    break
            
            return {
                'char': char,
                'code': f'U+{code:04X}',
                'category': category,
                'name': name,
                'weight': weight,
                'range': range_info,
                'length': len(char)
            }
        except Exception as e:
            return {
                'char': char,
                'weight': cls.get_char_weight(char),
                'error': str(e)
            }


# 保持向后兼容的别名
CharacterWeightCalculatorV2 = EnhancedCharacterWeightCalculator
