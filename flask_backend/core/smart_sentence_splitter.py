"""
智能断句算法优化系统
任务3.1: 智能断句算法优化
基于NLP、上下文感知、语义理解的新一代断句系统
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

# 尝试导入可选依赖
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    jieba = None
    JIEBA_AVAILABLE = False

logger = logging.getLogger(__name__)

class LanguageType(Enum):
    """支持的语言类型"""
    CHINESE = "zh"
    ENGLISH = "en"
    MIXED = "mixed"
    AUTO = "auto"

class SplittingStrategy(Enum):
    """断句策略"""
    SEMANTIC = "semantic"          # 语义优先
    LENGTH_BALANCED = "length"     # 长度平衡
    PUNCTUATION = "punctuation"    # 标点符号
    HYBRID = "hybrid"              # 混合策略
    AI_ENHANCED = "ai_enhanced"    # AI增强

@dataclass
class SentenceSegment:
    """句子片段"""
    text: str
    start_pos: int
    end_pos: int
    confidence: float
    segment_type: str
    language: LanguageType
    semantic_weight: float = 1.0
    readability_score: float = 1.0

@dataclass
class SplittingContext:
    """断句上下文"""
    target_length: int = 40
    max_length: int = 60
    min_length: int = 10
    strategy: SplittingStrategy = SplittingStrategy.HYBRID
    language: LanguageType = LanguageType.AUTO
    preserve_semantics: bool = True
    optimize_readability: bool = True
    subtitle_context: bool = True

class AdvancedSentenceSplitter:
    """高级智能断句器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_language_models()
        self._init_patterns()
        
    def _init_language_models(self):
        """初始化语言模型"""
        self.spacy_models = {}
        self.jieba_initialized = False
        
        if SPACY_AVAILABLE:
            try:
                # 加载中文模型
                try:
                    self.spacy_models['zh'] = spacy.load("zh_core_web_sm")
                    self.logger.info("SpaCy中文模型加载成功")
                except OSError:
                    self.logger.warning("SpaCy中文模型未找到，将使用备用方案")
                
                # 加载英文模型
                try:
                    self.spacy_models['en'] = spacy.load("en_core_web_sm")
                    self.logger.info("SpaCy英文模型加载成功")
                except OSError:
                    self.logger.warning("SpaCy英文模型未找到，将使用备用方案")
                    
            except Exception as e:
                self.logger.warning(f"SpaCy模型初始化失败: {e}")
        
        if JIEBA_AVAILABLE:
            try:
                jieba.initialize()
                self.jieba_initialized = True
                self.logger.info("Jieba分词器初始化成功")
            except Exception as e:
                self.logger.warning(f"Jieba初始化失败: {e}")
    
    def _init_patterns(self):
        """初始化分割模式"""
        # 中文标点符号
        self.chinese_punctuation = "。！？；：，、"
        
        # 英文标点符号
        self.english_punctuation = ".!?;:,"
        
        # 句子边界标记
        self.sentence_boundaries = {
            'zh': ['。', '！', '？', '；'],
            'en': ['.', '!', '?', ';'],
            'mixed': ['。', '！', '？', '；', '.', '!', '?', ';']
        }
        
        # 弱分割点（逗号等）
        self.weak_boundaries = {
            'zh': ['，', '、', '：'],
            'en': [',', ':'],
            'mixed': ['，', '、', '：', ',', ':']
        }
        
        # 语义连接词
        self.semantic_connectors = {
            'zh': ['但是', '然而', '而且', '因为', '所以', '由于', '如果', '虽然', '尽管'],
            'en': ['but', 'however', 'and', 'because', 'so', 'due to', 'if', 'although', 'despite'],
            'mixed': []
        }
        
        # 初始化混合连接词
        self.semantic_connectors['mixed'] = (
            self.semantic_connectors['zh'] + self.semantic_connectors['en']
        )
    
    def detect_language(self, text: str) -> LanguageType:
        """检测文本语言"""
        if not text:
            return LanguageType.AUTO
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return LanguageType.AUTO
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if chinese_ratio > 0.3 and english_ratio > 0.1:
            return LanguageType.MIXED
        elif chinese_ratio > english_ratio:
            return LanguageType.CHINESE
        elif english_ratio > 0.5:
            return LanguageType.ENGLISH
        else:
            return LanguageType.MIXED
    
    async def split_intelligent(self, 
                               text: str, 
                               context: Optional[SplittingContext] = None) -> List[SentenceSegment]:
        """
        智能断句主入口
        
        Args:
            text: 待分割文本
            context: 分割上下文配置
            
        Returns:
            分割后的句子片段列表
        """
        if not text or not text.strip():
            return []
        
        # 使用默认上下文
        if context is None:
            context = SplittingContext()
        
        # 检测语言
        if context.language == LanguageType.AUTO:
            context.language = self.detect_language(text)
        
        self.logger.info(f"开始智能断句: 文本长度{len(text)}, 语言{context.language.value}, 策略{context.strategy.value}")
        
        # 根据策略选择分割方法
        if context.strategy == SplittingStrategy.SEMANTIC:
            return await self._semantic_split(text, context)
        elif context.strategy == SplittingStrategy.LENGTH_BALANCED:
            return await self._length_balanced_split(text, context)
        elif context.strategy == SplittingStrategy.PUNCTUATION:
            return await self._punctuation_split(text, context)
        elif context.strategy == SplittingStrategy.AI_ENHANCED:
            return await self._ai_enhanced_split(text, context)
        else:  # HYBRID
            return await self._hybrid_split(text, context)
    
    async def _semantic_split(self, text: str, context: SplittingContext) -> List[SentenceSegment]:
        """基于语义的智能分割"""
        segments = []
        
        # 使用SpaCy进行语义分析
        if context.language.value in self.spacy_models:
            doc = self.spacy_models[context.language.value](text)
            
            current_segment = ""
            current_start = 0
            
            for sent in doc.sents:
                sentence_text = sent.text.strip()
                
                if not sentence_text:
                    continue
                
                # 检查是否可以合并到当前片段
                test_segment = (current_segment + " " + sentence_text).strip()
                
                if len(test_segment) <= context.target_length or not current_segment:
                    current_segment = test_segment
                else:
                    # 保存当前片段
                    if current_segment:
                        segments.append(SentenceSegment(
                            text=current_segment,
                            start_pos=current_start,
                            end_pos=current_start + len(current_segment),
                            confidence=0.9,
                            segment_type="semantic",
                            language=context.language,
                            semantic_weight=self._calculate_semantic_weight(current_segment)
                        ))
                    
                    current_segment = sentence_text
                    current_start = current_start + len(current_segment) if segments else 0
            
            # 添加最后的片段
            if current_segment:
                segments.append(SentenceSegment(
                    text=current_segment,
                    start_pos=current_start,
                    end_pos=current_start + len(current_segment),
                    confidence=0.9,
                    segment_type="semantic",
                    language=context.language,
                    semantic_weight=self._calculate_semantic_weight(current_segment)
                ))
        
        else:
            # 回退到规则分割
            segments = await self._rule_based_split(text, context)
        
        return self._optimize_segments(segments, context)
    
    async def _length_balanced_split(self, text: str, context: SplittingContext) -> List[SentenceSegment]:
        """基于长度平衡的分割"""
        segments = []
        words = self._tokenize_text(text, context.language)
        
        current_segment = ""
        current_words = []
        start_pos = 0
        
        for word in words:
            test_segment = (current_segment + " " + word).strip()
            
            if len(test_segment) <= context.target_length:
                current_segment = test_segment
                current_words.append(word)
            else:
                # 保存当前片段
                if current_segment:
                    segments.append(SentenceSegment(
                        text=current_segment,
                        start_pos=start_pos,
                        end_pos=start_pos + len(current_segment),
                        confidence=0.8,
                        segment_type="length_balanced",
                        language=context.language,
                        readability_score=self._calculate_readability(current_segment)
                    ))
                    start_pos += len(current_segment)
                
                current_segment = word
                current_words = [word]
        
        # 添加最后的片段
        if current_segment:
            segments.append(SentenceSegment(
                text=current_segment,
                start_pos=start_pos,
                end_pos=start_pos + len(current_segment),
                confidence=0.8,
                segment_type="length_balanced",
                language=context.language,
                readability_score=self._calculate_readability(current_segment)
            ))
        
        return segments
    
    async def _punctuation_split(self, text: str, context: SplittingContext) -> List[SentenceSegment]:
        """基于标点符号的分割"""
        segments = []
        language_key = context.language.value if context.language.value in self.sentence_boundaries else 'mixed'
        
        # 强分割点（句号等）
        strong_boundaries = self.sentence_boundaries[language_key]
        weak_boundaries = self.weak_boundaries[language_key]
        
        # 按强分割点分割
        sentences = self._split_by_boundaries(text, strong_boundaries)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            if len(sentence) <= context.target_length:
                segments.append(SentenceSegment(
                    text=sentence.strip(),
                    start_pos=0,  # 简化位置计算
                    end_pos=len(sentence),
                    confidence=0.7,
                    segment_type="punctuation",
                    language=context.language
                ))
            else:
                # 使用弱分割点进一步分割
                sub_segments = self._split_by_boundaries(sentence, weak_boundaries)
                
                current_segment = ""
                for sub_seg in sub_segments:
                    test_segment = (current_segment + sub_seg).strip()
                    
                    if len(test_segment) <= context.target_length:
                        current_segment = test_segment
                    else:
                        if current_segment:
                            segments.append(SentenceSegment(
                                text=current_segment,
                                start_pos=0,
                                end_pos=len(current_segment),
                                confidence=0.7,
                                segment_type="punctuation",
                                language=context.language
                            ))
                        current_segment = sub_seg.strip()
                
                if current_segment:
                    segments.append(SentenceSegment(
                        text=current_segment,
                        start_pos=0,
                        end_pos=len(current_segment),
                        confidence=0.7,
                        segment_type="punctuation",
                        language=context.language
                    ))
        
        return segments
    
    async def _ai_enhanced_split(self, text: str, context: SplittingContext) -> List[SentenceSegment]:
        """AI增强分割（预留接口）"""
        # 这里可以集成更高级的AI模型，如GPT、BERT等
        # 目前使用混合策略作为替代
        self.logger.info("AI增强分割暂时使用混合策略替代")
        return await self._hybrid_split(text, context)
    
    async def _hybrid_split(self, text: str, context: SplittingContext) -> List[SentenceSegment]:
        """混合策略分割"""
        # 先尝试语义分割
        semantic_segments = await self._semantic_split(text, context)
        
        # 如果语义分割失败或结果不理想，使用标点分割
        if not semantic_segments or self._evaluate_segments(semantic_segments, context) < 0.6:
            punctuation_segments = await self._punctuation_split(text, context)
            
            # 如果标点分割也不理想，使用长度平衡
            if not punctuation_segments or self._evaluate_segments(punctuation_segments, context) < 0.5:
                return await self._length_balanced_split(text, context)
            
            return punctuation_segments
        
        return semantic_segments
    
    async def _rule_based_split(self, text: str, context: SplittingContext) -> List[SentenceSegment]:
        """基于规则的分割（备用方案）"""
        segments = []
        language_key = context.language.value if context.language.value in self.sentence_boundaries else 'mixed'
        
        # 使用标点符号分割
        pattern = '[' + ''.join(self.sentence_boundaries[language_key]) + ']'
        sentences = re.split(f'({pattern})', text)
        
        current_segment = ""
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i].strip()
                punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                
                if sentence:
                    full_sentence = sentence + punct
                    
                    if len(current_segment + full_sentence) <= context.target_length:
                        current_segment += full_sentence
                    else:
                        if current_segment:
                            segments.append(SentenceSegment(
                                text=current_segment,
                                start_pos=0,
                                end_pos=len(current_segment),
                                confidence=0.6,
                                segment_type="rule_based",
                                language=context.language
                            ))
                        current_segment = full_sentence
        
        if current_segment:
            segments.append(SentenceSegment(
                text=current_segment,
                start_pos=0,
                end_pos=len(current_segment),
                confidence=0.6,
                segment_type="rule_based",
                language=context.language
            ))
        
        return segments
    
    def _tokenize_text(self, text: str, language: LanguageType) -> List[str]:
        """文本分词"""
        if language == LanguageType.CHINESE and self.jieba_initialized:
            return list(jieba.cut(text))
        elif language.value in self.spacy_models:
            doc = self.spacy_models[language.value](text)
            return [token.text for token in doc]
        else:
            # 简单分词
            return re.findall(r'\S+', text)
    
    def _split_by_boundaries(self, text: str, boundaries: List[str]) -> List[str]:
        """按边界符分割文本"""
        if not boundaries:
            return [text]
        
        pattern = '[' + ''.join(re.escape(b) for b in boundaries) + ']'
        parts = re.split(f'({pattern})', text)
        
        # 重新组合句子和标点
        sentences = []
        for i in range(0, len(parts), 2):
            if i < len(parts):
                sentence = parts[i]
                punct = parts[i + 1] if i + 1 < len(parts) else ""
                if sentence.strip():
                    sentences.append(sentence + punct)
        
        return sentences
    
    def _calculate_semantic_weight(self, text: str) -> float:
        """计算语义权重"""
        # 简化的语义权重计算
        weight = 1.0
        
        # 检查是否包含语义连接词
        for lang_connectors in self.semantic_connectors.values():
            for connector in lang_connectors:
                if connector in text:
                    weight += 0.1
        
        # 基于标点符号密度调整
        punct_count = sum(text.count(p) for p in "。！？；：，、.!?;:,")
        if len(text) > 0:
            punct_density = punct_count / len(text)
            weight += punct_density * 0.5
        
        return min(weight, 2.0)
    
    def _calculate_readability(self, text: str) -> float:
        """计算可读性评分"""
        if not text:
            return 0.0
        
        # 简化的可读性计算
        char_count = len(text)
        word_count = len(self._tokenize_text(text, LanguageType.AUTO))
        
        if word_count == 0:
            return 0.0
        
        avg_word_length = char_count / word_count
        
        # 理想的字符长度范围
        if 20 <= char_count <= 50:
            length_score = 1.0
        elif char_count < 20:
            length_score = char_count / 20
        else:
            length_score = max(0.3, 50 / char_count)
        
        # 词汇复杂度（简化）
        complexity_score = min(1.0, 5.0 / avg_word_length) if avg_word_length > 0 else 1.0
        
        return (length_score + complexity_score) / 2
    
    def _evaluate_segments(self, segments: List[SentenceSegment], context: SplittingContext) -> float:
        """评估分割质量"""
        if not segments:
            return 0.0
        
        scores = []
        
        for segment in segments:
            # 长度评分
            length_score = 1.0
            if segment.end_pos - segment.start_pos > context.max_length:
                length_score = 0.3
            elif segment.end_pos - segment.start_pos < context.min_length:
                length_score = 0.6
            
            # 置信度评分
            confidence_score = segment.confidence
            
            # 综合评分
            total_score = (length_score + confidence_score) / 2
            scores.append(total_score)
        
        return sum(scores) / len(scores)
    
    def _optimize_segments(self, segments: List[SentenceSegment], 
                          context: SplittingContext) -> List[SentenceSegment]:
        """优化分割结果"""
        if not segments:
            return segments
        
        optimized = []
        i = 0
        
        while i < len(segments):
            current = segments[i]
            
            # 检查是否可以与下一个片段合并
            if (i + 1 < len(segments) and 
                len(current.text + " " + segments[i + 1].text) <= context.target_length and
                context.preserve_semantics):
                
                # 合并片段
                next_segment = segments[i + 1]
                merged = SentenceSegment(
                    text=current.text + " " + next_segment.text,
                    start_pos=current.start_pos,
                    end_pos=next_segment.end_pos,
                    confidence=min(current.confidence, next_segment.confidence),
                    segment_type="optimized",
                    language=current.language,
                    semantic_weight=(current.semantic_weight + next_segment.semantic_weight) / 2
                )
                optimized.append(merged)
                i += 2
            else:
                optimized.append(current)
                i += 1
        
        return optimized

class SmartSentenceSplitterManager:
    """智能断句管理器"""
    
    def __init__(self):
        self.splitter = AdvancedSentenceSplitter()
        self.cache = {}
        self.performance_stats = {
            "total_splits": 0,
            "total_processing_time": 0.0,
            "average_confidence": 0.0,
            "strategy_usage": {}
        }
    
    async def split_text_smart(self, 
                              text: str,
                              target_length: int = 40,
                              strategy: str = "hybrid",
                              language: str = "auto") -> Dict[str, Any]:
        """
        智能分割文本的主接口
        
        Args:
            text: 待分割文本
            target_length: 目标长度
            strategy: 分割策略
            language: 语言类型
            
        Returns:
            分割结果
        """
        start_time = datetime.now()
        
        # 检查缓存
        cache_key = f"{hash(text)}_{target_length}_{strategy}_{language}"
        if cache_key in self.cache:
            self.logger.debug("使用缓存结果")
            return self.cache[cache_key]
        
        # 构建上下文
        context = SplittingContext(
            target_length=target_length,
            max_length=int(target_length * 1.5),
            min_length=max(5, int(target_length * 0.3)),
            strategy=SplittingStrategy(strategy),
            language=LanguageType(language)
        )
        
        # 执行分割
        segments = await self.splitter.split_intelligent(text, context)
        
        # 计算统计信息
        processing_time = (datetime.now() - start_time).total_seconds()
        avg_confidence = sum(s.confidence for s in segments) / len(segments) if segments else 0
        
        # 更新性能统计
        self.performance_stats["total_splits"] += 1
        self.performance_stats["total_processing_time"] += processing_time
        self.performance_stats["average_confidence"] = (
            (self.performance_stats["average_confidence"] * (self.performance_stats["total_splits"] - 1) + avg_confidence) /
            self.performance_stats["total_splits"]
        )
        
        if strategy not in self.performance_stats["strategy_usage"]:
            self.performance_stats["strategy_usage"][strategy] = 0
        self.performance_stats["strategy_usage"][strategy] += 1
        
        # 构建结果
        result = {
            "success": True,
            "segments": [
                {
                    "text": seg.text,
                    "length": len(seg.text),
                    "confidence": seg.confidence,
                    "type": seg.segment_type,
                    "language": seg.language.value,
                    "semantic_weight": seg.semantic_weight,
                    "readability_score": seg.readability_score
                }
                for seg in segments
            ],
            "statistics": {
                "total_segments": len(segments),
                "processing_time": processing_time,
                "average_confidence": avg_confidence,
                "average_length": sum(len(s.text) for s in segments) / len(segments) if segments else 0,
                "strategy_used": strategy,
                "language_detected": segments[0].language.value if segments else "unknown"
            },
            "metadata": {
                "original_text": text,
                "original_length": len(text),
                "target_length": target_length,
                "timestamp": start_time.isoformat()
            }
        }
        
        # 缓存结果
        self.cache[cache_key] = result
        
        # 限制缓存大小
        if len(self.cache) > 100:
            oldest_key = min(self.cache.keys())
            del self.cache[oldest_key]
        
        return result
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        avg_time = (
            self.performance_stats["total_processing_time"] / 
            self.performance_stats["total_splits"]
        ) if self.performance_stats["total_splits"] > 0 else 0
        
        return {
            "total_splits": self.performance_stats["total_splits"],
            "average_processing_time": avg_time,
            "average_confidence": self.performance_stats["average_confidence"],
            "strategy_usage": self.performance_stats["strategy_usage"],
            "cache_size": len(self.cache),
            "model_availability": {
                "spacy": SPACY_AVAILABLE,
                "jieba": JIEBA_AVAILABLE
            }
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.logger.info("智能断句缓存已清空")

# 全局实例
smart_splitter_manager = SmartSentenceSplitterManager()
