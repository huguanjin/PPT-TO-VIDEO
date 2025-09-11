"""
智能字幕处理工具模块
基于开源项目分析，实现字符权重计算和语义分割功能
"""
import re
import unicodedata
from typing import List, Tuple, Dict, Any, Optional, TYPE_CHECKING
import logging
from datetime import datetime

if TYPE_CHECKING:
    from .algorithms.dp_sentence_splitter import DynamicProgrammingSplitter

# 导入增强的字符权重计算器
try:
    from .enhanced_char_weight import EnhancedCharacterWeightCalculator as CharWeightCalc
    ENHANCED_WEIGHT_AVAILABLE = True
except ImportError:
    CharWeightCalc = None
    ENHANCED_WEIGHT_AVAILABLE = False


class CharacterWeightCalculator:
    """字符权重计算器 - 基于VideoLingo算法优化的字符显示宽度权重"""
    
    @classmethod
    def get_char_weight(cls, char: str) -> float:
        """
        获取单个字符的显示权重
        基于VideoLingo项目的calc_len函数优化
        """
        if not char:
            return 0.0
        
        # 处理多字节字符，使用第一个字符的编码
        try:
            code = ord(char[0])
        except (TypeError, IndexError):
            return 1.0
            
        # 中文和日文字符 (CJK统一汉字 + 平假名片假名)
        if (0x4E00 <= code <= 0x9FFF or 0x3040 <= code <= 0x30FF):
            return 1.75
        
        # 韩文字符 (韩文音节 + 韩文字母)
        elif (0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF):
            return 1.5
        
        # 泰文字符
        elif (0x0E00 <= code <= 0x0E7F):
            return 1.0
        
        # 全角符号
        elif (0xFF01 <= code <= 0xFF5E):
            return 1.75
        
        # 其他字符（英文和半角符号）
        else:
            return 1.0
    
    @classmethod
    def calc_text_weight(cls, text: str, use_enhanced: bool = True) -> float:
        """
        计算文本总权重
        基于VideoLingo的字符权重计算优化
        
        Args:
            text: 输入文本
            use_enhanced: 是否使用增强算法（支持更多语言和emoji）
        
        Returns:
            文本的总显示权重
        """
        if not text:
            return 0.0
        
        # 优先使用增强算法
        if use_enhanced and ENHANCED_WEIGHT_AVAILABLE and CharWeightCalc:
            return CharWeightCalc.calc_text_weight(text)
        
        # 降级到基础算法
        return sum(cls.get_char_weight(char) for char in str(text))
    
    @classmethod
    def get_char_weight_enhanced(cls, char: str) -> float:
        """
        获取字符权重（增强版本）
        
        Args:
            char: 单个字符
            
        Returns:
            字符的显示权重
        """
        if ENHANCED_WEIGHT_AVAILABLE and CharWeightCalc:
            return CharWeightCalc.get_char_weight(char)
        else:
            return cls.get_char_weight(char)


class SemanticTextSplitter:
    """语义文本分割器"""
    
    # 标点符号优先级 (分割优先级从高到低)
    PUNCTUATION_PRIORITY = {
        '。': 10, '.': 10,
        '！': 9, '!': 9,
        '？': 9, '?': 9,
        '；': 8, ';': 8,
        '：': 7, ':': 7,
        '，': 6, ',': 6,
        '、': 5,
        ' ': 3,
        '-': 2,
        '/': 1,
    }
    
    def __init__(self, max_weight: float = 75.0, target_multiplier: float = 1.2):
        """
        初始化语义分割器
        
        Args:
            max_weight: 最大字符权重
            target_multiplier: 目标权重倍数
        """
        self.max_weight = max_weight
        self.target_weight = max_weight / target_multiplier
        self.calc = CharacterWeightCalculator()
        
    def find_best_split_point(self, text: str, max_pos: int) -> int:
        """在指定位置前找到最佳分割点"""
        if max_pos <= 0:
            return 0
            
        best_pos = max_pos
        best_priority = -1
        
        # 从后往前查找最高优先级的分割点
        for i in range(max_pos, -1, -1):
            if i < len(text):
                char = text[i]
                priority = self.PUNCTUATION_PRIORITY.get(char, 0)
                
                if priority > best_priority:
                    best_priority = priority
                    best_pos = i + 1 if char in self.PUNCTUATION_PRIORITY else i
                    
                # 如果找到高优先级分割点，提前结束
                if priority >= 8:  # 句号、感叹号、问号等
                    break
                    
        return min(best_pos, len(text))
    
    def split_text_by_weight(self, text: str) -> List[str]:
        """按字符权重分割文本"""
        if not text:
            return []
            
        # 计算总权重
        total_weight = self.calc.calc_text_weight(text)
        
        # 如果总权重小于最大权重，直接返回
        if total_weight <= self.max_weight:
            return [text]
            
        chunks = []
        start = 0
        
        while start < len(text):
            # 计算当前位置到目标权重的位置
            current_weight = 0.0
            target_pos = start
            
            for i in range(start, len(text)):
                char_weight = self.calc.get_char_weight(text[i])
                
                if current_weight + char_weight > self.max_weight:
                    break
                    
                current_weight += char_weight
                target_pos = i + 1
                
                # 如果达到目标权重，寻找最佳分割点
                if current_weight >= self.target_weight:
                    # 在后续几个字符中寻找更好的分割点
                    look_ahead = min(target_pos + 10, len(text))
                    for j in range(target_pos, look_ahead):
                        if j < len(text) and text[j] in self.PUNCTUATION_PRIORITY:
                            char_weight = self.calc.get_char_weight(text[j])
                            if current_weight + char_weight <= self.max_weight:
                                priority = self.PUNCTUATION_PRIORITY[text[j]]
                                if priority >= 6:  # 逗号及以上优先级
                                    target_pos = j + 1
                                    current_weight += char_weight
                                    break
                    break
            
            # 如果没有找到合适的分割点，使用最佳分割点算法
            if target_pos == start:
                target_pos = start + 1
            else:
                # 寻找最佳分割点
                best_pos = self.find_best_split_point(text, target_pos - 1)
                if best_pos > start:
                    target_pos = best_pos
            
            # 提取当前块
            chunk = text[start:target_pos].strip()
            if chunk:
                chunks.append(chunk)
                
            start = target_pos
            
        return chunks


class SmartSubtitleProcessor:
    """智能字幕处理器 - 整合所有功能"""
    
    dp_splitter: Optional['DynamicProgrammingSplitter']
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化智能字幕处理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 默认配置
        self.max_weight = self.config.get('max_length', 75)
        self.target_multiplier = self.config.get('target_multiplier', 1.2)
        self.smart_split = self.config.get('smart_split', True)
        self.use_dp_algorithm = self.config.get('use_dp_algorithm', True)  # 是否使用动态规划算法
        self.use_enhanced_weight = self.config.get('use_enhanced_weight', True)  # 是否使用增强权重计算
        
        # 初始化组件
        self.calc = CharacterWeightCalculator()
        self.splitter = SemanticTextSplitter(
            max_weight=self.max_weight,
            target_multiplier=self.target_multiplier
        )
        
        # 初始化动态规划分割器
        if self.use_dp_algorithm:
            try:
                from .algorithms.dp_sentence_splitter import DynamicProgrammingSplitter
                # 根据字符权重计算token级别的最大长度
                max_token_length = max(int(self.max_weight / 1.5), 30)  # 保守估算
                min_token_length = max(int(max_token_length / 3), 10)
                
                self.dp_splitter = DynamicProgrammingSplitter(
                    max_length=max_token_length,
                    min_length=min_token_length
                )
                
                # 初始化logger
                self.logger = logging.getLogger(__name__)
                
                # 检查是否启用Spacy功能
                self.use_spacy = self.config.get('use_spacy', True)
                if self.use_spacy:
                    # 尝试初始化Spacy处理器进行预检
                    try:
                        from .nlp_utils.spacy_processor import SpacyProcessor
                        test_processor = SpacyProcessor('auto')
                        if test_processor.is_model_available():
                            self.logger.info("Spacy语法分析功能已启用")
                        else:
                            self.logger.warning("Spacy模型不可用，将使用基础分析")
                            self.use_spacy = False
                    except ImportError:
                        self.logger.warning("Spacy处理器不可用，将使用基础分析")
                        self.use_spacy = False
                
                self.logger.info("动态规划分割器初始化成功")
            except ImportError as e:
                self.logger = logging.getLogger(__name__)
                self.logger.warning(f"动态规划分割器导入失败，将使用传统算法: {e}")
                self.dp_splitter = None
                self.use_dp_algorithm = False
                self.use_spacy = False
        else:
            self.dp_splitter = None
            self.use_spacy = False
            self.logger = logging.getLogger(__name__)
    
    def calculate_text_weight(self, text: str) -> float:
        """
        计算文本权重（考虑配置选项）
        
        Args:
            text: 输入文本
            
        Returns:
            文本的显示权重
        """
        return self.calc.calc_text_weight(text, use_enhanced=self.use_enhanced_weight)
        
    def process_subtitle_text(self, text: str) -> List[str]:
        """
        处理字幕文本，返回分割后的行
        
        Args:
            text: 原始文本
            
        Returns:
            分割后的文本行列表
        """
        if not text:
            return []
            
        # 预处理：清理文本
        text = text.strip()
        if not text:
            return []
            
        self.logger.debug(f"处理字幕文本: {text}")
        
        # 计算文本权重
        text_weight = self.calculate_text_weight(text)
        self.logger.debug(f"文本权重: {text_weight}")
        
        # 如果文本权重在合理范围内，直接返回
        if text_weight <= self.max_weight:
            return [text]
        
        # 优先使用动态规划算法（如果可用且启用）
        if self.use_dp_algorithm and self.dp_splitter:
            return self.process_long_text_with_dp(text)
        
        # 使用传统智能分割
        elif self.smart_split:
            chunks = self.splitter.split_text_by_weight(text)
            self.logger.debug(f"传统智能分割结果: {chunks}")
            return chunks
        else:
            # 简单按字符数分割
            max_chars = int(self.max_weight / 1.5)  # 粗略估算
            chunks = []
            for i in range(0, len(text), max_chars):
                chunk = text[i:i + max_chars]
                if chunk:
                    chunks.append(chunk)
            return chunks
    
    def process_long_text_with_dp(self, text: str) -> List[str]:
        """
        使用动态规划算法处理长文本（增强Spacy支持）
        
        Args:
            text: 原始文本
            
        Returns:
            分割后的文本行列表
        """
        try:
            # 确保dp_splitter可用
            if self.dp_splitter is None:
                self.logger.warning("DP分割器不可用，回退到传统方法")
                return self.splitter.split_text_by_weight(text)
            
            # 自动检测语言（简单实现）
            language = self.detect_language(text)
            
            # 使用动态规划分割（启用Spacy增强）
            dp_result = self.dp_splitter.split_text(
                text, 
                language=language, 
                use_spacy=self.use_spacy
            )
            
            # 验证分割结果的权重
            validated_result = []
            for chunk in dp_result:
                chunk_weight = self.calc.calc_text_weight(chunk)
                
                if chunk_weight <= self.max_weight:  # 严格限制在最大权重内
                    validated_result.append(chunk)
                else:
                    # 如果DP分割的结果仍然过长，使用传统方法进一步分割
                    self.logger.debug(f"DP分割结果过长，使用传统方法进一步分割: {chunk} (权重: {chunk_weight})")
                    sub_chunks = self.splitter.split_text_by_weight(chunk)
                    # 递归验证每个子块
                    for sub_chunk in sub_chunks:
                        sub_weight = self.calc.calc_text_weight(sub_chunk)
                        if sub_weight <= self.max_weight:
                            validated_result.append(sub_chunk)
                        else:
                            # 最后的保障：强制按字符数分割
                            max_chars = int(self.max_weight / 1.8)  # 更保守的估算
                            for i in range(0, len(sub_chunk), max_chars):
                                final_chunk = sub_chunk[i:i + max_chars].strip()
                                if final_chunk:
                                    validated_result.append(final_chunk)
            
            # 记录处理结果
            spacy_status = "Spacy增强" if self.use_spacy else "基础分析"
            self.logger.debug(f"动态规划分割结果 ({spacy_status}): {validated_result}")
            return validated_result
            
        except Exception as e:
            self.logger.warning(f"动态规划分割失败，使用备用方案: {e}")
            # 降级到传统算法
            return self.splitter.split_text_by_weight(text)
    
    def detect_language(self, text: str) -> str:
        """
        简单的语言检测
        
        Args:
            text: 文本
            
        Returns:
            语言代码
        """
        # 统计不同语言字符的比例
        chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        japanese_count = sum(1 for char in text if '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')
        korean_count = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        english_count = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        
        total_chars = len(text)
        if total_chars == 0:
            return 'auto'
            
        # 判断主要语言
        if chinese_count / total_chars > 0.3:
            return 'zh'
        elif japanese_count / total_chars > 0.2:
            return 'ja'
        elif korean_count / total_chars > 0.2:
            return 'ko'
        elif english_count / total_chars > 0.5:
            return 'en'
        else:
            return 'auto'
    
    def validate_subtitle_line(self, text: str) -> bool:
        """验证字幕行是否符合要求"""
        if not text:
            return False
            
        weight = self.calc.calc_text_weight(text)
        return weight <= self.max_weight
    
    def get_text_metrics(self, text: str) -> Dict[str, Any]:
        """获取文本度量信息"""
        return {
            'text': text,
            'length': len(text),
            'weight': self.calc.calc_text_weight(text),
            'max_weight': self.max_weight,
            'is_valid': self.validate_subtitle_line(text),
            'processed_at': datetime.now().isoformat()
        }


# 便捷函数
def process_subtitle_text(text: str, config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    便捷函数：处理字幕文本
    
    Args:
        text: 原始文本
        config: 配置参数
        
    Returns:
        分割后的文本行列表
    """
    processor = SmartSubtitleProcessor(config)
    return processor.process_subtitle_text(text)


def calc_text_display_weight(text: str) -> float:
    """
    便捷函数：计算文本显示权重
    
    Args:
        text: 文本
        
    Returns:
        显示权重
    """
    calc = CharacterWeightCalculator()
    return calc.calc_text_weight(text)


if __name__ == "__main__":
    # 测试代码
    test_texts = [
        "这是一个测试字幕文本，包含中文和English混合内容，需要进行智能分割处理。",
        "Hello, this is a test subtitle with mixed content: 你好世界！",
        "短文本",
        "Very long English text that needs to be split according to character weights and semantic meaning.",
    ]
    
    processor = SmartSubtitleProcessor()
    
    for text in test_texts:
        print(f"\n原文: {text}")
        print(f"权重: {calc_text_display_weight(text):.2f}")
        
        chunks = processor.process_subtitle_text(text)
        print(f"分割结果 ({len(chunks)} 行):")
        for i, chunk in enumerate(chunks, 1):
            weight = calc_text_display_weight(chunk)
            print(f"  {i}. {chunk} (权重: {weight:.2f})")
