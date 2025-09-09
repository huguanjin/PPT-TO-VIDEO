"""
动态规划长句分割器
基于VideoLingo项目的split_long_by_root.py算法移植
优化长句分割的语义完整性和显示效果
"""

import re
import string
import warnings
from typing import List, Dict, Any, Optional, Tuple
import logging

warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


class DynamicProgrammingSplitter:
    """
    动态规划长句分割器
    
    基于VideoLingo项目的核心算法，使用动态规划优化分割点选择
    主要特性：
    1. 基于语法依赖关系的智能分割
    2. 考虑词性标注（VERB, AUX, ROOT）
    3. 动态调整分割策略
    4. 超长句子强制均分机制
    """
    
    def __init__(self, 
                 max_length: int = 60,
                 min_length: int = 30,
                 max_search_range: int = 100):
        """
        初始化分割器
        
        Args:
            max_length: 最大句子长度（token数）
            min_length: 最小句子长度（token数）
            max_search_range: 动态规划搜索范围限制
        """
        self.max_length = max_length
        self.min_length = min_length
        self.max_search_range = max_search_range
        
        # 语言特定的连接符配置
        self.language_configs = {
            'zh': {'joiner': '', 'name': 'Chinese'},
            'en': {'joiner': ' ', 'name': 'English'},
            'ja': {'joiner': '', 'name': 'Japanese'},
            'ko': {'joiner': '', 'name': 'Korean'},
            'auto': {'joiner': '', 'name': 'Auto'}  # 默认配置
        }
        
    def get_joiner(self, language: str = 'auto') -> str:
        """获取语言特定的连接符"""
        config = self.language_configs.get(language, self.language_configs['auto'])
        return config['joiner']
    
    def split_long_sentence(self, 
                          tokens: List[str], 
                          token_info: Optional[List[Dict]] = None,
                          language: str = 'auto') -> List[str]:
        """
        使用动态规划分割长句
        
        Args:
            tokens: 分词后的token列表
            token_info: token的语法信息（可选）
            language: 语言代码
            
        Returns:
            分割后的句子列表
        """
        n = len(tokens)
        if n <= self.max_length:
            joiner = self.get_joiner(language)
            return [joiner.join(tokens)]
        
        # 动态规划数组，dp[i]表示从开始到第i个token的最优分割方案
        dp = [float('inf')] * (n + 1)
        dp[0] = 0
        
        # 记录最优分割点
        prev = [0] * (n + 1)
        
        for i in range(1, n + 1):
            # 限制搜索范围避免过长句子
            search_start = max(0, i - self.max_search_range)
            
            for j in range(search_start, i):
                # 确保句子长度至少为min_length
                if i - j >= self.min_length:
                    # 检查分割点是否合适
                    if self._is_good_split_point(tokens, token_info, j, i, language):
                        if dp[j] + 1 < dp[i]:
                            dp[i] = dp[j] + 1
                            prev[i] = j
        
        # 根据最优分割点重建句子
        sentences = []
        i = n
        joiner = self.get_joiner(language)
        
        while i > 0:
            j = prev[i]
            sentence = joiner.join(tokens[j:i]).strip()
            if sentence:  # 只添加非空句子
                sentences.append(sentence)
            i = j
        
        # 反转列表保持原始顺序
        return sentences[::-1] if sentences else [joiner.join(tokens)]
    
    def _is_good_split_point(self, 
                            tokens: List[str], 
                            token_info: Optional[List[Dict]], 
                            start: int, 
                            end: int, 
                            language: str) -> bool:
        """
        判断是否是好的分割点
        增强版本：优先使用Spacy语法信息
        
        Args:
            tokens: token列表
            token_info: token语法信息
            start: 开始位置
            end: 结束位置
            language: 语言代码
            
        Returns:
            是否为好的分割点
        """
        if start == 0:
            return True
            
        if end > len(tokens):
            return False
            
        # 如果有Spacy语法信息，优先使用
        if token_info and end - 1 < len(token_info):
            token = token_info[end - 1]
            
            # 高优先级分割点
            if token.get('is_sent_end', False):
                return True
                
            # 重要的语法结构
            pos = token.get('pos_', '')
            dep = token.get('dep_', '')
            
            # 动词和助动词
            if pos in ['VERB', 'AUX']:
                return True
                
            # 重要的依赖关系
            if dep in ['ROOT', 'ccomp', 'xcomp', 'advcl']:
                return True
                
            # 连词
            if pos in ['CCONJ', 'SCONJ']:
                return True
                
            # 标点符号
            if token.get('is_punct', False):
                punct_text = token.get('text', '')
                if punct_text in '。！？.!?；;：:，,、':
                    return True
        
        # 备用方案：基于标点符号和常见模式
        if end - 1 < len(tokens):
            current_token = tokens[end - 1]
            
            # 句子结束标点（高优先级）
            if current_token in '。！？.!?':
                return True
                
            # 逗号和分号（中优先级）
            if current_token in '，；,:;':
                return True
                
            # 顿号和其他标点（低优先级）
            if current_token in '、':
                return True
        
        # 检查前一个token是否是连词
        if end - 2 >= 0 and end - 2 < len(tokens):
            prev_token = tokens[end - 2]
            if prev_token.lower() in ['and', 'or', 'but', 'so', '和', '或', '但是', '所以', '而且', '然后']:
                return True
        
        return False
    
    def split_extremely_long_sentence(self, 
                                    tokens: List[str], 
                                    target_parts: int = None,
                                    language: str = 'auto') -> List[str]:
        """
        对极长句子进行强制均分
        
        Args:
            tokens: token列表
            target_parts: 目标分割部分数（自动计算如果为None）
            language: 语言代码
            
        Returns:
            分割后的句子列表
        """
        n = len(tokens)
        
        # 自动计算分割部分数
        if target_parts is None:
            target_parts = (n + self.max_length - 1) // self.max_length
        
        part_length = n // target_parts
        
        sentences = []
        joiner = self.get_joiner(language)
        
        for i in range(target_parts):
            start = i * part_length
            end = start + part_length if i < target_parts - 1 else n
            
            sentence = joiner.join(tokens[start:end]).strip()
            if sentence:
                sentences.append(sentence)
        
        return sentences
    
    def split_text(self, 
                   text: str, 
                   language: str = 'auto',
                   use_spacy: bool = True) -> List[str]:
        """
        分割文本的主入口方法
        
        Args:
            text: 要分割的文本
            language: 语言代码
            use_spacy: 是否使用Spacy分析（默认True）
            
        Returns:
            分割后的句子列表
        """
        if not text or not text.strip():
            return []
        
        # 优先使用Spacy分词
        if use_spacy:
            tokens, token_info = self._spacy_tokenize(text, language)
        else:
            tokens = self._simple_tokenize(text, language)
            token_info = None
        
        if len(tokens) <= self.max_length:
            return [text.strip()]
        
        # 尝试动态规划分割
        try:
            split_sentences = self.split_long_sentence(tokens, token_info, language)
            
            # 检查是否仍有过长的句子需要强制分割
            final_sentences = []
            for sentence in split_sentences:
                if use_spacy:
                    sentence_tokens, _ = self._spacy_tokenize(sentence, language)
                else:
                    sentence_tokens = self._simple_tokenize(sentence, language)
                    
                if len(sentence_tokens) > self.max_length:
                    # 对仍然过长的句子进行强制分割
                    extremely_long_parts = self.split_extremely_long_sentence(
                        sentence_tokens, language=language
                    )
                    final_sentences.extend(extremely_long_parts)
                else:
                    final_sentences.append(sentence)
            
            return final_sentences
            
        except Exception as e:
            logger.warning(f"动态规划分割失败，使用备用方案: {e}")
            # 备用方案：简单分割
            return self._fallback_split(text, language)
    
    def _simple_tokenize(self, text: str, language: str) -> List[str]:
        """
        简单分词实现
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            token列表
        """
        if language in ['zh', 'ja', 'ko']:
            # 中日韩语言：字符级分词
            return list(text.strip())
        else:
            # 英语等：基于空格分词
            return text.strip().split()
    
    def _spacy_tokenize(self, text: str, language: str) -> Tuple[List[str], List[Dict]]:
        """
        使用spacy进行分词和语法分析
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            (tokens, token_info)的元组
        """
        try:
            # 尝试导入Spacy处理器
            from ..nlp_utils.spacy_processor import SpacyProcessor
            
            # 初始化处理器
            processor = SpacyProcessor(language)
            
            if processor.is_model_available():
                # 获取详细的token信息
                token_info_list = processor.get_token_info(text)
                
                # 提取tokens
                tokens = [info['text'] for info in token_info_list]
                
                # 转换为兼容格式
                token_info = []
                for info in token_info_list:
                    token_info.append({
                        'text': info['text'],
                        'pos_': info['pos_'],
                        'dep_': info['dep_'],
                        'is_sent_end': info['is_sent_end'],
                        'is_punct': info['is_punct'],
                        'idx': info['idx']
                    })
                
                logger.debug(f"Spacy分词成功: {len(tokens)} tokens")
                return tokens, token_info
            else:
                logger.warning("Spacy模型不可用，使用简单分词")
                return self._simple_tokenize(text, language), None
                
        except ImportError:
            logger.warning("Spacy处理器不可用，使用简单分词")
            return self._simple_tokenize(text, language), None
        except Exception as e:
            logger.warning(f"Spacy分词失败: {e}，使用简单分词")
            return self._simple_tokenize(text, language), None
    
    def _fallback_split(self, text: str, language: str) -> List[str]:
        """
        备用分割方案
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            分割后的句子列表
        """
        # 基于标点符号的简单分割
        if language in ['zh', 'ja', 'ko']:
            # 中日韩语言的分割模式
            pattern = r'[。！？；]+'
        else:
            # 英语的分割模式
            pattern = r'[.!?;]+'
        
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]


def test_dp_splitter():
    """测试动态规划分割器（包含Spacy增强功能）"""
    splitter = DynamicProgrammingSplitter(max_length=25, min_length=8)
    
    # 测试用例
    test_cases = [
        {
            'text': '这是一个非常长的句子，包含了多个语义单元，需要进行智能分割处理，确保语义完整性的同时控制显示长度，这样可以提高字幕的可读性。',
            'language': 'zh',
            'description': '中文长句测试（Spacy增强）'
        },
        {
            'text': 'This is a very long English sentence that contains multiple semantic units and needs to be intelligently split to ensure semantic integrity while controlling display length.',
            'language': 'en', 
            'description': '英文长句测试（Spacy增强）'
        }
    ]
    
    print("=== 动态规划分割器测试（含Spacy增强） ===")
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['description']}")
        print(f"原文: {case['text']}")
        print(f"长度: {len(case['text'])} 字符")
        
        # 测试Spacy增强版本
        print(f"\n[使用Spacy增强]")
        result_spacy = splitter.split_text(case['text'], case['language'], use_spacy=True)
        print(f"分割结果 ({len(result_spacy)} 部分):")
        for j, part in enumerate(result_spacy, 1):
            print(f"  {j}. {part} (长度: {len(part)})")
        
        # 测试传统版本对比
        print(f"\n[传统分词对比]")
        result_simple = splitter.split_text(case['text'], case['language'], use_spacy=False)
        print(f"分割结果 ({len(result_simple)} 部分):")
        for j, part in enumerate(result_simple, 1):
            print(f"  {j}. {part} (长度: {len(part)})")
        
        print("-" * 80)


if __name__ == "__main__":
    test_dp_splitter()
