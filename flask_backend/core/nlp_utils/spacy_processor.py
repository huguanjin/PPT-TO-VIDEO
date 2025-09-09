"""
Spacy语法分析处理器
基于VideoLingo项目的spacy_utils模块移植
提供高级语法分析和智能分割功能
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union, TYPE_CHECKING
import warnings

# 可选导入spacy，支持降级
try:
    import spacy
    from spacy.tokens import Doc, Token, Span
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

# 仅在类型检查时导入spacy类型
if TYPE_CHECKING:
    from spacy.tokens import Doc, Token, Span
else:
    if not SPACY_AVAILABLE:
        Doc = Token = Span = Any

warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


class SpacyProcessor:
    """Spacy语法分析处理器"""
    
    # 支持的语言和对应的模型
    LANGUAGE_MODELS = {
        'zh': 'zh_core_web_sm',     # 中文
        'en': 'en_core_web_sm',     # 英文
        'ja': 'ja_core_news_sm',    # 日文
        'ko': None,                 # 韩文（暂不支持spacy模型）
        'auto': 'zh_core_web_sm'    # 默认中文
    }
    
    # 重要的分割词性标签
    IMPORTANT_POS = {'VERB', 'AUX', 'SCONJ', 'CCONJ', 'ADV'}
    
    # 重要的依赖关系标签
    IMPORTANT_DEP = {'ROOT', 'ccomp', 'xcomp', 'advcl', 'acl'}
    
    def __init__(self, language: str = 'auto', model_name: Optional[str] = None):
        """
        初始化Spacy处理器
        
        Args:
            language: 语言代码
            model_name: 自定义模型名称
        """
        self.language = language
        self.model_name = model_name or self.LANGUAGE_MODELS.get(language, 'zh_core_web_sm')
        self.nlp = None
        self.is_available = SPACY_AVAILABLE
        
        if SPACY_AVAILABLE:
            self._init_nlp()
        else:
            logger.warning("Spacy不可用，将使用基础分析功能")
    
    def _init_nlp(self):
        """初始化NLP模型"""
        if not self.model_name:
            logger.warning(f"语言 {self.language} 暂不支持spacy模型")
            return
            
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"成功加载Spacy模型: {self.model_name}")
        except OSError:
            logger.warning(f"Spacy模型 {self.model_name} 未安装，尝试自动下载...")
            try:
                spacy.cli.download(self.model_name)
                self.nlp = spacy.load(self.model_name)
                logger.info(f"成功下载并加载Spacy模型: {self.model_name}")
            except Exception as e:
                logger.error(f"无法下载Spacy模型 {self.model_name}: {e}")
                self.nlp = None
                self.is_available = False
    
    def is_model_available(self) -> bool:
        """检查模型是否可用"""
        return self.is_available and self.nlp is not None
    
    def analyze_text(self, text: str) -> Optional['Doc']:
        """
        分析文本并返回Doc对象
        
        Args:
            text: 输入文本
            
        Returns:
            Spacy Doc对象，如果分析失败返回None
        """
        if not self.is_model_available():
            return None
            
        try:
            doc = self.nlp(text)
            return doc
        except Exception as e:
            logger.warning(f"Spacy文本分析失败: {e}")
            return None
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        提取句子边界
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        doc = self.analyze_text(text)
        if doc is None:
            # 降级到基于标点的分割
            return self._fallback_sentence_split(text)
        
        try:
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            return sentences if sentences else [text]
        except Exception as e:
            logger.warning(f"Spacy句子分割失败: {e}")
            return self._fallback_sentence_split(text)
    
    def find_split_points(self, text: str) -> List[Tuple[int, float, str]]:
        """
        找到文本中的潜在分割点
        
        Args:
            text: 输入文本
            
        Returns:
            分割点列表，每个元素为(位置, 权重, 原因)
        """
        doc = self.analyze_text(text)
        if doc is None:
            return self._fallback_split_points(text)
        
        split_points = []
        
        try:
            for token in doc:
                position = token.idx + len(token.text)
                weight = 0.0
                reasons = []
                
                # 句子边界
                if token.is_sent_end:
                    weight += 10.0
                    reasons.append("句末")
                
                # 重要词性
                if token.pos_ in self.IMPORTANT_POS:
                    weight += 5.0
                    reasons.append(f"词性:{token.pos_}")
                
                # 重要依赖关系
                if token.dep_ in self.IMPORTANT_DEP:
                    weight += 3.0
                    reasons.append(f"依赖:{token.dep_}")
                
                # 标点符号
                if token.is_punct:
                    punct_weight = self._get_punctuation_weight(token.text)
                    weight += punct_weight
                    if punct_weight > 0:
                        reasons.append(f"标点:{token.text}")
                
                # 连词
                if token.pos_ in {'CCONJ', 'SCONJ'}:
                    weight += 2.0
                    reasons.append("连词")
                
                if weight > 0:
                    reason = "|".join(reasons)
                    split_points.append((position, weight, reason))
            
            return split_points
            
        except Exception as e:
            logger.warning(f"Spacy分割点分析失败: {e}")
            return self._fallback_split_points(text)
    
    def get_token_info(self, text: str) -> List[Dict[str, Any]]:
        """
        获取详细的token信息
        
        Args:
            text: 输入文本
            
        Returns:
            token信息列表
        """
        doc = self.analyze_text(text)
        if doc is None:
            return self._fallback_token_info(text)
        
        try:
            token_info = []
            for token in doc:
                info = {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos_': token.pos_,
                    'tag_': token.tag_,
                    'dep_': token.dep_,
                    'shape_': token.shape_,
                    'is_alpha': token.is_alpha,
                    'is_stop': token.is_stop,
                    'is_punct': token.is_punct,
                    'is_sent_start': token.is_sent_start,
                    'is_sent_end': token.is_sent_end,
                    'idx': token.idx,
                    'length': len(token.text)
                }
                token_info.append(info)
            
            return token_info
            
        except Exception as e:
            logger.warning(f"Spacy token信息提取失败: {e}")
            return self._fallback_token_info(text)
    
    def analyze_sentence_structure(self, text: str, language: str = 'auto') -> Dict[str, Any]:
        """
        分析句子语法结构
        
        Args:
            text: 输入文本
            language: 语言代码（兼容性参数，当前版本使用实例设置的语言）
            
        Returns:
            结构分析结果
        """
        doc = self.analyze_text(text)
        if doc is None:
            return self._fallback_structure_analysis(text)
        
        try:
            # 提取句子
            sentences = list(doc.sents)
            
            # 提取根词
            root_tokens = [token for token in doc if token.dep_ == 'ROOT']
            
            # 提取动词短语
            verb_phrases = [token for token in doc if token.pos_ in ['VERB', 'AUX']]
            
            # 提取名词短语
            noun_phrases = list(doc.noun_chunks)
            
            # 提取实体
            entities = list(doc.ents)
            
            return {
                'sentences': [sent.text for sent in sentences],
                'root_tokens': [{'text': token.text, 'idx': token.idx} for token in root_tokens],
                'verb_phrases': [{'text': token.text, 'idx': token.idx} for token in verb_phrases],
                'noun_phrases': [{'text': chunk.text, 'start': chunk.start_char, 'end': chunk.end_char} for chunk in noun_phrases],
                'entities': [{'text': ent.text, 'label': ent.label_, 'start': ent.start_char, 'end': ent.end_char} for ent in entities],
                'token_count': len(doc),
                'sentence_count': len(sentences)
            }
            
        except Exception as e:
            logger.warning(f"Spacy结构分析失败: {e}")
            return self._fallback_structure_analysis(text)
    
    def _get_punctuation_weight(self, punct: str) -> float:
        """获取标点符号的权重"""
        weights = {
            '。': 10.0, '.': 10.0,
            '！': 9.0, '!': 9.0,
            '？': 9.0, '?': 9.0,
            '；': 8.0, ';': 8.0,
            '：': 7.0, ':': 7.0,
            '，': 6.0, ',': 6.0,
            '、': 5.0,
            ' ': 1.0,
            '-': 2.0,
            '/': 1.0,
        }
        return weights.get(punct, 0.0)
    
    def _fallback_sentence_split(self, text: str) -> List[str]:
        """基于标点的降级句子分割"""
        if self.language in ['zh', 'ja']:
            pattern = r'[。！？；]+'
        else:
            pattern = r'[.!?;]+'
        
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _fallback_split_points(self, text: str) -> List[Tuple[int, float, str]]:
        """降级分割点分析"""
        split_points = []
        
        for i, char in enumerate(text):
            weight = self._get_punctuation_weight(char)
            if weight > 0:
                split_points.append((i + 1, weight, f"标点:{char}"))
        
        return split_points
    
    def _fallback_token_info(self, text: str) -> List[Dict[str, Any]]:
        """降级token信息"""
        if self.language in ['zh', 'ja', 'ko']:
            # 字符级token
            tokens = list(text)
        else:
            # 单词级token
            tokens = text.split()
        
        token_info = []
        idx = 0
        for token in tokens:
            info = {
                'text': token,
                'lemma': token.lower(),
                'pos_': 'UNKNOWN',
                'tag_': 'UNKNOWN',
                'dep_': 'UNKNOWN',
                'shape_': 'UNKNOWN',
                'is_alpha': token.isalpha(),
                'is_stop': False,
                'is_punct': not token.isalnum(),
                'is_sent_start': idx == 0,
                'is_sent_end': idx == len(tokens) - 1,
                'idx': idx,
                'length': len(token)
            }
            token_info.append(info)
            idx += len(token)
            if self.language not in ['zh', 'ja', 'ko']:
                idx += 1  # 空格
        
        return token_info
    
    def _fallback_structure_analysis(self, text: str) -> Dict[str, Any]:
        """降级结构分析"""
        sentences = self._fallback_sentence_split(text)
        
        return {
            'sentences': sentences,
            'root_tokens': [],
            'verb_phrases': [],
            'noun_phrases': [],
            'entities': [],
            'token_count': len(text),
            'sentence_count': len(sentences)
        }


def test_spacy_processor():
    """测试Spacy处理器"""
    print("=== Spacy语法分析处理器测试 ===\n")
    
    # 测试不同语言
    test_cases = [
        {
            'language': 'zh',
            'text': '这是一个复杂的中文句子，包含多个从句和复合结构，需要进行精确的语法分析。',
            'description': '中文语法分析'
        },
        {
            'language': 'en', 
            'text': 'This is a complex English sentence with multiple clauses and compound structures that requires precise grammatical analysis.',
            'description': '英文语法分析'
        }
    ]
    
    for case in test_cases:
        print(f"测试: {case['description']}")
        print(f"文本: {case['text']}")
        
        processor = SpacyProcessor(case['language'])
        print(f"模型可用: {processor.is_model_available()}")
        
        if processor.is_model_available():
            # 句子分割
            sentences = processor.extract_sentences(case['text'])
            print(f"句子分割: {sentences}")
            
            # 分割点分析
            split_points = processor.find_split_points(case['text'])
            print(f"分割点 (前5个): {split_points[:5]}")
            
            # 结构分析
            structure = processor.analyze_sentence_structure(case['text'])
            print(f"句子数量: {structure['sentence_count']}")
            print(f"根词: {structure['root_tokens']}")
            print(f"动词短语: {structure['verb_phrases']}")
        else:
            print("使用降级分析...")
            sentences = processor.extract_sentences(case['text'])
            print(f"降级句子分割: {sentences}")
        
        print("-" * 60)
    
    def smart_split_with_grammar(self, 
                               text: str, 
                               max_length: int = 75,
                               language: str = 'auto') -> List[str]:
        """
        基于语法的智能分割
        
        Args:
            text: 要分割的文本
            max_length: 最大长度
            language: 语言代码（兼容性参数，实际使用实例的language）
            
        Returns:
            分割后的文本列表
        """
        if not text or not text.strip():
            return []
        
        # 如果文本不长，直接返回
        if len(text) <= max_length:
            return [text.strip()]
        
        # 进行语法分析
        analysis = self.analyze_sentence_structure(text)
        
        if not analysis['success']:
            return self._simple_split(text, max_length)
        
        # 基于分析结果进行智能分割
        if analysis['method'] == 'spacy' and analysis.get('split_candidates'):
            return self._grammar_based_split(text, analysis, max_length)
        else:
            return self._rule_based_split(text, analysis, max_length)
    
    def _grammar_based_split(self, 
                           text: str, 
                           analysis: Dict[str, Any], 
                           max_length: int) -> List[str]:
        """
        基于语法分析的分割
        """
        # 按置信度排序分割候选点
        candidates = sorted(analysis.get('split_candidates', []), 
                          key=lambda x: x.get('confidence', 0), reverse=True)
        
        segments = []
        current_start = 0
        
        for candidate in candidates:
            split_pos = candidate.get('position', 0)
            
            # 检查分割是否合适
            if split_pos - current_start >= max_length * 0.5:  # 最小长度检查
                segment = text[current_start:split_pos].strip()
                if segment and len(segment) <= max_length:
                    segments.append(segment)
                    current_start = split_pos
        
        # 添加剩余部分
        if current_start < len(text):
            remaining = text[current_start:].strip()
            if remaining:
                if len(remaining) <= max_length:
                    segments.append(remaining)
                else:
                    # 剩余部分仍然过长，递归分割
                    segments.extend(self._simple_split(remaining, max_length))
        
        return segments if segments else [text.strip()]
    
    def _rule_based_split(self, 
                        text: str, 
                        analysis: Dict[str, Any], 
                        max_length: int) -> List[str]:
        """
        基于规则的分割
        """
        # 使用句子边界进行分割
        sentences = analysis.get('sentences', [text])
        
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            if len(current_segment + sentence) <= max_length:
                current_segment += sentence
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                
                if len(sentence) <= max_length:
                    current_segment = sentence
                else:
                    # 单个句子过长，需要进一步分割
                    sub_segments = self._simple_split(sentence, max_length)
                    segments.extend(sub_segments[:-1])
                    current_segment = sub_segments[-1] if sub_segments else ""
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments if segments else [text.strip()]
    
    def _simple_split(self, text: str, max_length: int) -> List[str]:
        """
        简单分割（备用方案）
        """
        if len(text) <= max_length:
            return [text.strip()]
        
        segments = []
        current_pos = 0
        
        while current_pos < len(text):
            end_pos = min(current_pos + max_length, len(text))
            
            # 尝试在单词边界分割
            if end_pos < len(text):
                # 寻找最近的空格或标点
                for i in range(end_pos, current_pos, -1):
                    if text[i] in [' ', '，', '。', ',', '.', '!', '?', '！', '？']:
                        end_pos = i + 1
                        break
            
            segment = text[current_pos:end_pos].strip()
            if segment:
                segments.append(segment)
            
            current_pos = end_pos
        
        return segments


if __name__ == "__main__":
    test_spacy_processor()
