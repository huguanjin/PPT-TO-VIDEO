"""
任务 3.2: 多语言支持增强系统
基于智能断句算法的跨语言字幕处理优化
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime
import json
import os

# 智能断句系统类定义
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class LanguageType(Enum):
    CHINESE = "chinese"
    ENGLISH = "english"
    MIXED = "mixed"

class SplittingStrategy(Enum):
    SIMPLE = "simple"
    SEMANTIC = "semantic"
    BALANCED = "balanced"

@dataclass
class SentenceSegment:
    text: str
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 0.8
    semantic_weight: float = 1.0
    readability_score: float = 0.8
    language: LanguageType = LanguageType.MIXED
    break_reason: str = "default"

@dataclass
class SplittingContext:
    target_length: int = 35
    max_length: int = 40
    min_length: int = 10
    language: LanguageType = LanguageType.MIXED
    strategy: SplittingStrategy = SplittingStrategy.BALANCED
    preserve_syntax: bool = True
    semantic_threshold: float = 0.7

class AdvancedSentenceSplitter:
    """高级句子分割器实现"""
    
    def __init__(self):
        self.chinese_punctuation = "。！？；：，、"
        self.english_punctuation = ".!?;:,"
        self.sentence_terminators = "。！？.!?"
        
    async def split_intelligent(self, text: str, context: Optional[SplittingContext] = None) -> List[SentenceSegment]:
        """智能分割文本为句子段落"""
        if context is None:
            context = SplittingContext()
        
        segments = []
        
        # 根据语言类型选择分割策略
        if context.language == LanguageType.CHINESE:
            sentences = self._split_chinese(text, context)
        elif context.language == LanguageType.ENGLISH:
            sentences = self._split_english(text, context)
        else:
            sentences = self._split_mixed(text, context)
        
        # 创建句子段落对象
        current_pos = 0
        for sentence in sentences:
            if sentence.strip():
                start_pos = text.find(sentence, current_pos)
                end_pos = start_pos + len(sentence)
                
                segment = SentenceSegment(
                    text=sentence.strip(),
                    start_pos=start_pos,
                    end_pos=end_pos,
                    confidence=self._calculate_confidence(sentence, context),
                    semantic_weight=self._calculate_semantic_weight(sentence),
                    readability_score=self._calculate_readability(sentence, context),
                    language=context.language,
                    break_reason=self._get_break_reason(sentence)
                )
                segments.append(segment)
                current_pos = end_pos
        
        # 应用长度优化
        segments = self._optimize_segments_length(segments, context)
        
        return segments
    
    def _split_chinese(self, text: str, context: SplittingContext) -> List[str]:
        """中文文本分割"""
        # 基于中文标点符号分割
        sentences = re.split(f'[{self.chinese_punctuation}]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_english(self, text: str, context: SplittingContext) -> List[str]:
        """英文文本分割"""
        # 基于英文标点符号和语法分割
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_mixed(self, text: str, context: SplittingContext) -> List[str]:
        """混合语言文本分割"""
        # 综合中英文标点符号分割
        pattern = f'[{self.sentence_terminators}]+\\s*'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_confidence(self, sentence: str, context: SplittingContext) -> float:
        """计算分割置信度"""
        base_confidence = 0.8
        
        # 长度因子
        length_factor = 1.0
        if len(sentence) < context.min_length:
            length_factor = 0.6
        elif len(sentence) > context.max_length:
            length_factor = 0.7
        
        # 标点符号因子
        punct_factor = 1.0
        if any(p in sentence for p in self.sentence_terminators):
            punct_factor = 1.1
        
        return min(base_confidence * length_factor * punct_factor, 1.0)
    
    def _calculate_semantic_weight(self, sentence: str) -> float:
        """计算语义权重"""
        # 基于句子特征计算语义权重
        weight = 1.0
        
        # 长度因子
        if len(sentence) > 20:
            weight += 0.1
        
        # 复杂度因子（逗号数量）
        comma_count = sentence.count(',') + sentence.count('，')
        weight += comma_count * 0.05
        
        return min(weight, 2.0)
    
    def _calculate_readability(self, sentence: str, context: SplittingContext) -> float:
        """计算可读性评分"""
        # 基于长度和复杂度计算可读性
        target_length = context.target_length
        actual_length = len(sentence)
        
        # 长度适宜性
        if actual_length <= target_length:
            length_score = 1.0
        else:
            length_score = max(0.3, target_length / actual_length)
        
        # 复杂度评分
        complexity_score = 1.0 - min(0.5, sentence.count(',') * 0.1)
        
        return (length_score + complexity_score) / 2
    
    def _get_break_reason(self, sentence: str) -> str:
        """获取断句原因"""
        if any(p in sentence for p in "。！？"):
            return "chinese_punctuation"
        elif any(p in sentence for p in ".!?"):
            return "english_punctuation"
        elif len(sentence) > 40:
            return "length_limit"
        else:
            return "semantic_break"
    
    def _optimize_segments_length(self, segments: List[SentenceSegment], context: SplittingContext) -> List[SentenceSegment]:
        """优化片段长度"""
        optimized = []
        
        for segment in segments:
            if len(segment.text) > context.max_length:
                # 分割过长的段落
                sub_segments = self._split_long_segment(segment, context)
                optimized.extend(sub_segments)
            elif len(segment.text) < context.min_length and optimized:
                # 合并过短的段落
                last_segment = optimized[-1]
                if len(last_segment.text + segment.text) <= context.max_length:
                    merged = SentenceSegment(
                        text=last_segment.text + " " + segment.text,
                        start_pos=last_segment.start_pos,
                        end_pos=segment.end_pos,
                        confidence=(last_segment.confidence + segment.confidence) / 2,
                        semantic_weight=max(last_segment.semantic_weight, segment.semantic_weight),
                        readability_score=(last_segment.readability_score + segment.readability_score) / 2,
                        language=context.language,
                        break_reason="merge_short"
                    )
                    optimized[-1] = merged
                else:
                    optimized.append(segment)
            else:
                optimized.append(segment)
        
        return optimized
    
    def _split_long_segment(self, segment: SentenceSegment, context: SplittingContext) -> List[SentenceSegment]:
        """分割过长的段落"""
        text = segment.text
        target_length = context.target_length
        
        # 尝试在逗号处分割
        parts = []
        if '，' in text or ',' in text:
            split_chars = ['，', ',']
            for char in split_chars:
                if char in text:
                    parts = text.split(char)
                    break
        
        if not parts or len(parts) == 1:
            # 如果没有逗号，按长度强制分割
            parts = [text[i:i+target_length] for i in range(0, len(text), target_length)]
        
        segments = []
        current_pos = segment.start_pos
        
        for i, part in enumerate(parts):
            if part.strip():
                part_segment = SentenceSegment(
                    text=part.strip(),
                    start_pos=current_pos,
                    end_pos=current_pos + len(part),
                    confidence=segment.confidence * 0.9,  # 分割后置信度略降
                    semantic_weight=segment.semantic_weight,
                    readability_score=segment.readability_score,
                    language=segment.language,
                    break_reason="split_long"
                )
                segments.append(part_segment)
                current_pos += len(part)
        
        return segments

logger = logging.getLogger(__name__)

class SupportedLanguage(Enum):
    """支持的语言类型扩展"""
    # 主要语言
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW" 
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    RUSSIAN = "ru"
    ARABIC = "ar"
    
    # 东南亚语言
    THAI = "th"
    VIETNAMESE = "vi"
    INDONESIAN = "id"
    MALAY = "ms"
    
    # 欧洲语言
    ITALIAN = "it"
    PORTUGUESE = "pt"
    DUTCH = "nl"
    POLISH = "pl"
    
    # 印度语言
    HINDI = "hi"
    BENGALI = "bn"
    
    # 特殊标识
    AUTO_DETECT = "auto"
    MIXED_LANGUAGE = "mixed"
    UNKNOWN = "unknown"

@dataclass
class LanguageConfig:
    """语言特定配置"""
    language_code: str
    language_name: str
    rtl: bool = False  # 是否从右到左
    sentence_terminators: List[str] = field(default_factory=lambda: [".", "!", "?"])
    paragraph_separators: List[str] = field(default_factory=lambda: ["\n", "\r\n"])
    word_separators: List[str] = field(default_factory=lambda: [" ", "\t"])
    max_subtitle_length: int = 40
    target_subtitle_length: int = 35
    voice_mapping: Dict[str, str] = field(default_factory=dict)
    tts_engine_preference: List[str] = field(default_factory=lambda: ["edge", "azure"])
    
    # 分词特性
    needs_word_segmentation: bool = False  # 中日韩等需要分词
    has_capitalization: bool = True  # 是否有大小写
    has_spaces: bool = True  # 是否有空格分词
    
    # 语义特性
    sov_order: bool = False  # 主谓宾语序
    agglutinative: bool = False  # 黏着语特性
    tonal: bool = False  # 声调语言

@dataclass
class MultilingualSubtitle:
    """多语言字幕段"""
    text: str
    start_time: float
    end_time: float
    language: SupportedLanguage
    confidence: float
    
    # 同步信息
    sync_group_id: Optional[str] = None
    cross_lang_refs: List[str] = field(default_factory=list)
    
    # 质量信息
    translation_quality: Optional[float] = None
    readability_score: Optional[float] = None
    
    # 元数据
    source_text: Optional[str] = None
    translation_engine: Optional[str] = None

@dataclass
class CrossLanguageSync:
    """跨语言同步配置"""
    primary_language: SupportedLanguage
    secondary_languages: List[SupportedLanguage]
    sync_tolerance: float = 0.5  # 同步容忍度(秒)
    
    # 同步策略
    time_based_sync: bool = True
    content_based_sync: bool = True
    semantic_sync: bool = False
    
    # 质量控制
    min_confidence: float = 0.7
    max_time_drift: float = 2.0

class AdvancedLanguageDetector:
    """高级语言检测器"""
    
    def __init__(self):
        self.language_patterns = self._init_language_patterns()
        self.confidence_threshold = 0.8
        
    def _init_language_patterns(self) -> Dict[SupportedLanguage, Dict[str, Any]]:
        """初始化语言识别模式"""
        return {
            SupportedLanguage.CHINESE_SIMPLIFIED: {
                "char_ranges": [(0x4e00, 0x9fff)],  # CJK统一汉字
                "common_chars": "的在是了有和人这个我们",
                "punctuation": "。！？，、；：""''（）【】",
                "numbers": "一二三四五六七八九十百千万",
                "indicators": ["中国", "我们", "这个", "是的"]
            },
            SupportedLanguage.CHINESE_TRADITIONAL: {
                "char_ranges": [(0x4e00, 0x9fff)],
                "common_chars": "的在是了有和人這個我們",
                "punctuation": "。！？，、；：""''（）【】",
                "indicators": ["這個", "我們", "台灣", "繁體"]
            },
            SupportedLanguage.ENGLISH: {
                "char_ranges": [(0x0041, 0x005a), (0x0061, 0x007a)],
                "common_words": ["the", "and", "is", "in", "to", "of", "a", "that"],
                "punctuation": ".,!?;:\"'()[]{}",
                "indicators": ["this", "that", "with", "from"]
            },
            SupportedLanguage.JAPANESE: {
                "char_ranges": [
                    (0x3040, 0x309f),  # 平假名
                    (0x30a0, 0x30ff),  # 片假名
                    (0x4e00, 0x9fff)   # 汉字
                ],
                "common_chars": "のはでをにがとてもあります",
                "indicators": ["です", "ます", "である", "ございます"]
            },
            SupportedLanguage.KOREAN: {
                "char_ranges": [(0xac00, 0xd7af)],  # 韩文音节
                "common_chars": "이의는을를에서로와",
                "indicators": ["입니다", "습니다", "것이다"]
            },
            SupportedLanguage.ARABIC: {
                "char_ranges": [(0x0600, 0x06ff)],  # 阿拉伯文
                "rtl": True,
                "indicators": ["في", "من", "إلى", "على"]
            },
            SupportedLanguage.RUSSIAN: {
                "char_ranges": [(0x0400, 0x04ff)],  # 西里尔字母
                "common_chars": "аеиоуыэюяйлнрстм",
                "indicators": ["это", "что", "как", "если"]
            }
        }
    
    def detect_language(self, text: str) -> Tuple[SupportedLanguage, float]:
        """检测文本语言及置信度"""
        if not text.strip():
            return SupportedLanguage.UNKNOWN, 0.0
        
        scores = {}
        text_clean = re.sub(r'\s+', '', text.lower())
        
        for lang, patterns in self.language_patterns.items():
            score = self._calculate_language_score(text_clean, patterns)
            scores[lang] = score
        
        # 找到最高分
        best_lang = max(scores, key=lambda x: scores.get(x, 0))  # type: ignore
        confidence = scores[best_lang]
        
        # 检查混合语言
        top_langs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        if len([score for _, score in top_langs if score > 0.3]) > 1:
            return SupportedLanguage.MIXED_LANGUAGE, confidence
        
        return best_lang if confidence > self.confidence_threshold else SupportedLanguage.UNKNOWN, confidence
    
    def _calculate_language_score(self, text: str, patterns: Dict[str, Any]) -> float:
        """计算语言匹配分数"""
        score = 0.0
        total_chars = len(text)
        
        if total_chars == 0:
            return 0.0
        
        # 字符范围匹配
        if "char_ranges" in patterns:
            char_matches = 0
            for char in text:
                char_code = ord(char)
                for start, end in patterns["char_ranges"]:
                    if start <= char_code <= end:
                        char_matches += 1
                        break
            score += (char_matches / total_chars) * 0.6
        
        # 常见字符/词汇匹配
        if "common_chars" in patterns:
            common_matches = sum(1 for char in text if char in patterns["common_chars"])
            score += (common_matches / total_chars) * 0.3
        
        if "common_words" in patterns:
            words = text.split()
            if words:
                word_matches = sum(1 for word in words if word in patterns["common_words"])
                score += (word_matches / len(words)) * 0.3
        
        # 标识符匹配
        if "indicators" in patterns:
            for indicator in patterns["indicators"]:
                if indicator in text:
                    score += 0.1
        
        return min(score, 1.0)
    
    def detect_multiple_languages(self, text: str) -> List[Tuple[SupportedLanguage, float, int, int]]:
        """检测文本中的多种语言及位置"""
        results = []
        sentences = re.split(r'[.!?。！？]\s*', text)
        
        current_pos = 0
        for sentence in sentences:
            if sentence.strip():
                lang, confidence = self.detect_language(sentence)
                start_pos = text.find(sentence, current_pos)
                end_pos = start_pos + len(sentence)
                results.append((lang, confidence, start_pos, end_pos))
                current_pos = end_pos
        
        return results

class MultilingualSplittingEngine:
    """多语言智能断句引擎"""
    
    def __init__(self):
        self.base_splitter = AdvancedSentenceSplitter()
        self.language_detector = AdvancedLanguageDetector()
        self.language_configs = self._init_language_configs()
        
    def _init_language_configs(self) -> Dict[SupportedLanguage, LanguageConfig]:
        """初始化语言配置"""
        configs = {}
        
        # 中文简体配置
        configs[SupportedLanguage.CHINESE_SIMPLIFIED] = LanguageConfig(  # type: ignore
            language_code="zh-CN",
            language_name="简体中文",
            sentence_terminators=["。", "！", "？", "；"],
            max_subtitle_length=20,  # 中文字符较密集
            target_subtitle_length=18,
            needs_word_segmentation=True,
            has_spaces=False,
            tonal=True,
            voice_mapping={
                "female": "zh-CN-XiaoxiaoNeural",
                "male": "zh-CN-YunxiNeural"
            }
        )
        
        # 中文繁体配置
        configs[SupportedLanguage.CHINESE_TRADITIONAL] = LanguageConfig(  # type: ignore
            language_code="zh-TW",
            language_name="繁體中文",
            sentence_terminators=["。", "！", "？", "；"],
            max_subtitle_length=20,
            target_subtitle_length=18,
            needs_word_segmentation=True,
            has_spaces=False,
            tonal=True,
            voice_mapping={
                "female": "zh-TW-HsiaoyuNeural",
                "male": "zh-TW-YunJheNeural"
            }
        )
        
        # 英文配置
        configs[SupportedLanguage.ENGLISH] = LanguageConfig(  # type: ignore
            language_code="en",
            language_name="English",
            sentence_terminators=[".", "!", "?"],
            max_subtitle_length=40,
            target_subtitle_length=35,
            voice_mapping={
                "female": "en-US-JennyNeural",
                "male": "en-US-GuyNeural"
            }
        )
        
        # 日文配置
        configs[SupportedLanguage.JAPANESE] = LanguageConfig(  # type: ignore
            language_code="ja",
            language_name="日本語",
            sentence_terminators=["。", "！", "？"],
            max_subtitle_length=25,
            target_subtitle_length=22,
            needs_word_segmentation=True,
            has_spaces=False,
            sov_order=True,
            agglutinative=True,
            voice_mapping={
                "female": "ja-JP-NanamiNeural",
                "male": "ja-JP-KeitaNeural"
            }
        )
        
        # 韩文配置
        configs[SupportedLanguage.KOREAN] = LanguageConfig(  # type: ignore
            language_code="ko",
            language_name="한국어",
            sentence_terminators=[".", "!", "?", "。"],
            max_subtitle_length=25,
            target_subtitle_length=22,
            needs_word_segmentation=True,
            sov_order=True,
            agglutinative=True,
            voice_mapping={
                "female": "ko-KR-SunHiNeural",
                "male": "ko-KR-InJoonNeural"
            }
        )
        
        # 阿拉伯文配置
        configs[SupportedLanguage.ARABIC] = LanguageConfig(  # type: ignore
            language_code="ar",
            language_name="العربية",
            rtl=True,
            sentence_terminators=[".", "!", "?", "。"],
            max_subtitle_length=35,
            target_subtitle_length=30,
            voice_mapping={
                "female": "ar-SA-ZariyahNeural",
                "male": "ar-SA-HamedNeural"
            }
        )
        
        return configs
    
    async def split_multilingual_text(
        self, 
        text: str, 
        target_language: Optional[SupportedLanguage] = None,
        context: Optional[SplittingContext] = None
    ) -> List[SentenceSegment]:
        """多语言文本智能分割"""
        
        # 1. 语言检测
        detected_lang, confidence = self.language_detector.detect_language(text)
        working_lang = target_language or detected_lang
        
        # 2. 获取语言配置
        lang_config = self.language_configs.get(
            working_lang, 
            self.language_configs[SupportedLanguage.ENGLISH]
        )
        
        # 3. 调整分割上下文
        if context is None:
            context = SplittingContext()
        
        # 应用语言特定配置
        context.target_length = lang_config.target_subtitle_length
        context.max_length = lang_config.max_subtitle_length
        
        # 根据语言特性调整策略
        if working_lang in [SupportedLanguage.CHINESE_SIMPLIFIED, SupportedLanguage.CHINESE_TRADITIONAL]:
            context.language = LanguageType.CHINESE
        elif working_lang == SupportedLanguage.ENGLISH:
            context.language = LanguageType.ENGLISH
        else:
            context.language = LanguageType.MIXED
        
        # 4. 执行智能分割
        segments = await self.base_splitter.split_intelligent(text, context)
        
        # 5. 后处理：应用语言特定优化
        optimized_segments = await self._apply_language_specific_optimization(
            segments, working_lang, lang_config
        )
        
        return optimized_segments
    
    async def _apply_language_specific_optimization(
        self,
        segments: List[SentenceSegment],
        language: SupportedLanguage,
        config: LanguageConfig
    ) -> List[SentenceSegment]:
        """应用语言特定优化"""
        
        optimized = []
        
        for segment in segments:
            # 更新语言信息
            if language == SupportedLanguage.CHINESE_SIMPLIFIED:
                segment.language = LanguageType.CHINESE
            elif language == SupportedLanguage.ENGLISH:
                segment.language = LanguageType.ENGLISH
            else:
                segment.language = LanguageType.MIXED
            
            # RTL语言处理
            if config.rtl:
                segment.text = self._process_rtl_text(segment.text)
            
            # 声调语言优化
            if config.tonal:
                segment.semantic_weight *= 1.1  # 声调语言更注重语义
            
            # SOV语序语言优化
            if config.sov_order:
                segment.readability_score = self._adjust_sov_readability(segment.text, segment.readability_score)
            
            optimized.append(segment)
        
        return optimized
    
    def _process_rtl_text(self, text: str) -> str:
        """处理从右到左文本"""
        # 对于RTL语言，可能需要特殊的文本处理
        # 这里简单返回原文本，实际实现可能需要更复杂的处理
        return text
    
    def _adjust_sov_readability(self, text: str, current_score: float) -> float:
        """调整SOV语序语言的可读性评分"""
        # SOV语言的可读性评估可能需要不同的标准
        # 这里进行简单调整
        return min(current_score * 1.05, 1.0)

class CrossLanguageSubtitleManager:
    """跨语言字幕管理器"""
    
    def __init__(self):
        self.multilingual_engine = MultilingualSplittingEngine()
        self.sync_configs: Dict[str, CrossLanguageSync] = {}
        self.subtitle_groups: Dict[str, List[MultilingualSubtitle]] = {}
        
    async def create_multilingual_subtitles(
        self,
        texts: List[str],
        primary_language: SupportedLanguage,
        secondary_languages: Optional[List[SupportedLanguage]] = None,
        sync_config: Optional[CrossLanguageSync] = None
    ) -> Dict[SupportedLanguage, List[MultilingualSubtitle]]:
        """创建多语言字幕"""
        
        results = {}
        secondary_languages = secondary_languages or []
        
        # 1. 处理主语言
        primary_subtitles = await self._process_language_subtitles(
            texts, primary_language, is_primary=True
        )
        results[primary_language] = primary_subtitles
        
        # 2. 处理次要语言
        for lang in secondary_languages:
            secondary_subtitles = await self._process_language_subtitles(
                texts, lang, is_primary=False
            )
            results[lang] = secondary_subtitles
        
        # 3. 跨语言同步
        if sync_config:
            results = await self._synchronize_multilingual_subtitles(
                results, sync_config
            )
        
        return results
    
    async def _process_language_subtitles(
        self,
        texts: List[str],
        language: SupportedLanguage,
        is_primary: bool = True
    ) -> List[MultilingualSubtitle]:
        """处理特定语言的字幕"""
        
        subtitles = []
        current_time = 0.0
        
        for i, text in enumerate(texts):
            # 使用多语言分割引擎
            segments = await self.multilingual_engine.split_multilingual_text(
                text, target_language=language
            )
            
            for segment in segments:
                # 估算时长（基于字符数和语言特性）
                duration = self._estimate_duration(segment.text, language)
                
                subtitle = MultilingualSubtitle(
                    text=segment.text,
                    start_time=current_time,
                    end_time=current_time + duration,
                    language=language,
                    confidence=segment.confidence,
                    sync_group_id=f"group_{i}",
                    readability_score=segment.readability_score
                )
                
                subtitles.append(subtitle)
                current_time += duration
        
        return subtitles
    
    def _estimate_duration(self, text: str, language: SupportedLanguage) -> float:
        """估算字幕显示时长"""
        
        # 语言特定的阅读速度（字符/秒）
        reading_speeds = {
            SupportedLanguage.CHINESE_SIMPLIFIED: 6.0,
            SupportedLanguage.CHINESE_TRADITIONAL: 6.0,
            SupportedLanguage.ENGLISH: 12.0,
            SupportedLanguage.JAPANESE: 8.0,
            SupportedLanguage.KOREAN: 8.0,
            SupportedLanguage.ARABIC: 10.0,
        }
        
        speed = reading_speeds.get(language, 10.0)
        min_duration = 1.0  # 最小显示时间
        max_duration = 6.0  # 最大显示时间
        
        estimated = len(text) / speed
        return max(min_duration, min(estimated, max_duration))
    
    async def _synchronize_multilingual_subtitles(
        self,
        multilingual_subtitles: Dict[SupportedLanguage, List[MultilingualSubtitle]],
        sync_config: CrossLanguageSync
    ) -> Dict[SupportedLanguage, List[MultilingualSubtitle]]:
        """同步多语言字幕"""
        
        primary_subs = multilingual_subtitles.get(sync_config.primary_language, [])
        if not primary_subs:
            return multilingual_subtitles
        
        # 以主语言为基准同步其他语言
        for lang, subtitles in multilingual_subtitles.items():
            if lang == sync_config.primary_language:
                continue
                
            synchronized = await self._sync_to_primary(
                subtitles, primary_subs, sync_config
            )
            multilingual_subtitles[lang] = synchronized
        
        return multilingual_subtitles
    
    async def _sync_to_primary(
        self,
        secondary_subs: List[MultilingualSubtitle],
        primary_subs: List[MultilingualSubtitle],
        sync_config: CrossLanguageSync
    ) -> List[MultilingualSubtitle]:
        """将次要语言同步到主语言"""
        
        synchronized = []
        
        for i, primary_sub in enumerate(primary_subs):
            if i < len(secondary_subs):
                secondary_sub = secondary_subs[i]
                
                # 时间同步
                if sync_config.time_based_sync:
                    secondary_sub.start_time = primary_sub.start_time
                    secondary_sub.end_time = primary_sub.end_time
                
                # 内容同步
                if sync_config.content_based_sync:
                    secondary_sub.sync_group_id = primary_sub.sync_group_id
                    if primary_sub.sync_group_id:
                        secondary_sub.cross_lang_refs.append(primary_sub.sync_group_id)
                
                synchronized.append(secondary_sub)
        
        return synchronized

class MultilingualConfigManager:
    """多语言配置管理器"""
    
    def __init__(self, config_dir: str = "config_data"):
        self.config_dir = config_dir
        self.multilingual_engine = MultilingualSplittingEngine()
        self.subtitle_manager = CrossLanguageSubtitleManager()
        
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """获取支持的语言列表"""
        languages = []
        
        for lang in SupportedLanguage:
            if lang in [SupportedLanguage.AUTO_DETECT, SupportedLanguage.MIXED_LANGUAGE, SupportedLanguage.UNKNOWN]:
                continue
                
            config = self.multilingual_engine.language_configs.get(lang)
            if config:
                languages.append({
                    "code": lang.value,
                    "name": config.language_name,
                    "rtl": config.rtl,
                    "max_length": config.max_subtitle_length,
                    "voices": config.voice_mapping
                })
        
        return languages
    
    def get_language_config(self, language: Union[str, SupportedLanguage]) -> Optional[LanguageConfig]:
        """获取语言配置"""
        if isinstance(language, str):
            try:
                language = SupportedLanguage(language)
            except ValueError:
                return None
                
        return self.multilingual_engine.language_configs.get(language)
    
    async def optimize_config_for_language(
        self,
        base_config: Dict[str, Any],
        target_language: SupportedLanguage
    ) -> Dict[str, Any]:
        """为特定语言优化配置"""
        
        lang_config = self.get_language_config(target_language)
        if not lang_config:
            return base_config
        
        optimized = base_config.copy()
        
        # 调整字幕长度
        if "subtitle" in optimized:
            optimized["subtitle"]["max_length"] = lang_config.max_subtitle_length
            optimized["subtitle"]["target_length"] = lang_config.target_subtitle_length
        
        # 调整TTS设置
        if "tts" in optimized and "voice" in optimized["tts"]:
            if "female" in lang_config.voice_mapping:
                optimized["tts"]["voice"] = lang_config.voice_mapping["female"]
        
        # 调整分割策略
        if "splitting" in optimized:
            if lang_config.needs_word_segmentation:
                optimized["splitting"]["strategy"] = "semantic"
            if lang_config.sov_order:
                optimized["splitting"]["preserve_syntax"] = True
        
        return optimized
    
    def save_multilingual_config(
        self,
        config: Dict[str, Any],
        filename: str = "multilingual_config.json"
    ) -> bool:
        """保存多语言配置"""
        try:
            config_path = os.path.join(self.config_dir, filename)
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"保存多语言配置失败: {e}")
            return False
    
    def load_multilingual_config(
        self,
        filename: str = "multilingual_config.json"
    ) -> Optional[Dict[str, Any]]:
        """加载多语言配置"""
        try:
            config_path = os.path.join(self.config_dir, filename)
            
            if not os.path.exists(config_path):
                return None
                
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"加载多语言配置失败: {e}")
            return None

# 导出主要类
__all__ = [
    'SupportedLanguage',
    'LanguageConfig', 
    'MultilingualSubtitle',
    'CrossLanguageSync',
    'AdvancedLanguageDetector',
    'MultilingualSplittingEngine',
    'CrossLanguageSubtitleManager',
    'MultilingualConfigManager'
]
