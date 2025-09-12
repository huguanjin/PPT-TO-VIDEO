#!/usr/bin/env python3
"""
智能语速匹配字幕时长优化系统
专门处理字幕显示时长与语速的精确匹配，确保最佳观看体验
"""

import asyncio
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
from enum import Enum

# 设置日志
logger = logging.getLogger(__name__)


class SpeechRateCategory(Enum):
    """语速分类"""
    VERY_SLOW = "very_slow"      # < 120 WPM
    SLOW = "slow"                # 120-160 WPM  
    NORMAL = "normal"            # 160-200 WPM
    FAST = "fast"                # 200-250 WPM
    VERY_FAST = "very_fast"      # > 250 WPM


class ContentType(Enum):
    """内容类型"""
    PRESENTATION = "presentation"  # PPT演示
    LECTURE = "lecture"           # 讲座
    CONVERSATION = "conversation"  # 对话
    NARRATION = "narration"       # 叙述
    TECHNICAL = "technical"       # 技术内容


@dataclass
class SpeechAnalysisResult:
    """语速分析结果"""
    words_per_minute: float
    syllables_per_minute: float
    character_per_minute: float
    speech_rate_category: SpeechRateCategory
    content_type: ContentType
    pause_ratio: float            # 停顿比例
    speech_clarity: float         # 语音清晰度 (0-1)
    emotional_intensity: float    # 情感强度 (0-1)
    
    def __post_init__(self):
        """计算衍生属性"""
        self.optimal_display_wpm = self._calculate_optimal_display_speed()
        self.complexity_factor = self._calculate_complexity_factor()
    
    def _calculate_optimal_display_speed(self) -> float:
        """计算最佳显示速度"""
        base_speed = self.words_per_minute
        
        # 根据内容类型调整
        content_adjustments = {
            ContentType.TECHNICAL: 0.7,      # 技术内容需要更慢
            ContentType.LECTURE: 0.8,        # 讲座稍慢
            ContentType.PRESENTATION: 0.9,   # 演示正常
            ContentType.CONVERSATION: 1.1,   # 对话可以快一些
            ContentType.NARRATION: 1.0       # 叙述正常
        }
        
        adjustment = content_adjustments.get(self.content_type, 1.0)
        
        # 考虑停顿和清晰度
        clarity_factor = 0.8 + (self.speech_clarity * 0.4)  # 0.8-1.2
        pause_factor = 1.0 + (self.pause_ratio * 0.3)       # 停顿多的内容可以稍快
        
        optimal_speed = base_speed * adjustment * clarity_factor * pause_factor
        
        # 限制在合理范围内
        return max(60, min(optimal_speed, 300))
    
    def _calculate_complexity_factor(self) -> float:
        """计算内容复杂度因子"""
        # 基础复杂度基于语速
        base_complexity = {
            SpeechRateCategory.VERY_SLOW: 0.9,
            SpeechRateCategory.SLOW: 0.8,
            SpeechRateCategory.NORMAL: 0.7,
            SpeechRateCategory.FAST: 0.6,
            SpeechRateCategory.VERY_FAST: 0.5
        }
        
        complexity = base_complexity.get(self.speech_rate_category, 0.7)
        
        # 技术内容增加复杂度
        if self.content_type == ContentType.TECHNICAL:
            complexity += 0.2
        elif self.content_type == ContentType.LECTURE:
            complexity += 0.1
            
        # 情感强度影响复杂度
        complexity += self.emotional_intensity * 0.1
        
        return min(complexity, 1.0)


@dataclass
class SubtitleTimingRule:
    """字幕时长规则"""
    min_duration_ms: int = 800           # 最小显示时长
    max_duration_ms: int = 6000         # 最大显示时长
    optimal_chars_per_second: float = 15.0  # 最佳字符/秒
    min_gap_ms: int = 83                # 最小间隙 (Netflix: 2帧@24fps)
    max_gap_ms: int = 500              # 最大间隙
    
    # 语言特定参数
    chinese_reading_speed: float = 4.0   # 中文阅读速度 (字符/秒)
    english_reading_speed: float = 12.0  # 英文阅读速度 (字符/秒)
    
    # 内容类型调整
    content_speed_multipliers: Dict[ContentType, float] = None
    
    def __post_init__(self):
        if self.content_speed_multipliers is None:
            self.content_speed_multipliers = {
                ContentType.TECHNICAL: 0.7,
                ContentType.LECTURE: 0.8,
                ContentType.PRESENTATION: 1.0,
                ContentType.CONVERSATION: 1.2,
                ContentType.NARRATION: 1.0
            }


@dataclass
class SubtitleSegment:
    """字幕片段"""
    text: str
    start_time: float                    # 开始时间 (秒)
    end_time: float                      # 结束时间 (秒)
    original_duration: float             # 原始时长
    character_count: int
    chinese_char_count: int
    english_word_count: int
    
    # 优化相关
    content_type: Optional[ContentType] = None
    complexity_score: float = 0.0
    recommended_duration: float = 0.0
    quality_score: float = 0.0
    
    @property
    def duration(self) -> float:
        """当前时长"""
        return self.end_time - self.start_time
    
    @property
    def reading_speed_cps(self) -> float:
        """字符每秒阅读速度"""
        return self.character_count / self.duration if self.duration > 0 else 0
    
    def __post_init__(self):
        """自动计算字符数"""
        if not hasattr(self, 'character_count') or self.character_count == 0:
            self.character_count = len(self.text)
        
        if not hasattr(self, 'chinese_char_count') or self.chinese_char_count == 0:
            self.chinese_char_count = sum(1 for c in self.text if '\u4e00' <= c <= '\u9fff')
        
        if not hasattr(self, 'english_word_count') or self.english_word_count == 0:
            english_chars = sum(1 for c in self.text if c.isalpha() and not ('\u4e00' <= c <= '\u9fff'))
            self.english_word_count = max(1, english_chars // 5)  # 估算英文单词数


class IntelligentSubtitleTimingOptimizer:
    """智能字幕时长优化器 - 语速匹配系统核心"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化优化器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 加载配置
        self.config = self._load_config(config_path)
        self.timing_rules = SubtitleTimingRule()
        
        # 优化统计
        self.optimization_stats = {
            "total_segments": 0,
            "optimized_segments": 0,
            "average_improvement": 0.0,
            "processing_time": 0.0
        }
        
        self.logger.info("智能字幕时长优化器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "optimization_aggressive_level": 0.7,  # 优化激进程度 (0-1)
            "preserve_original_gaps": True,        # 保持原始间隙
            "enable_content_type_detection": True, # 启用内容类型检测
            "enable_quality_scoring": True,        # 启用质量评分
            "min_improvement_threshold": 0.1,      # 最小改进阈值
            "max_duration_extension_ratio": 1.5,   # 最大时长扩展比例
            "min_duration_compression_ratio": 0.7  # 最小时长压缩比例
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"配置加载失败，使用默认配置: {e}")
        
        return default_config
    
    async def analyze_speech_patterns(self, audio_path: str, transcript: str) -> SpeechAnalysisResult:
        """分析语音模式"""
        self.logger.info(f"开始分析语音模式: {audio_path}")
        
        try:
            # 模拟语音分析（实际项目中会调用真实的语音分析API）
            duration = await self._estimate_audio_duration(audio_path)
            
            # 字符和单词统计
            char_count = len(transcript)
            chinese_chars = sum(1 for c in transcript if '\u4e00' <= c <= '\u9fff')
            english_words = len([w for w in transcript.split() if any(c.isalpha() and not ('\u4e00' <= c <= '\u9fff') for c in w)])
            
            # 计算语速
            chars_per_minute = (char_count / duration) * 60 if duration > 0 else 0
            words_per_minute = (english_words / duration) * 60 if duration > 0 else 0
            syllables_per_minute = chars_per_minute * 1.2  # 估算音节数
            
            # 分类语速
            speech_category = self._categorize_speech_rate(chars_per_minute)
            
            # 检测内容类型
            content_type = await self._detect_content_type(transcript)
            
            # 模拟其他分析结果
            pause_ratio = min(0.3, max(0.05, 0.15 + np.random.normal(0, 0.05)))
            speech_clarity = min(1.0, max(0.3, 0.8 + np.random.normal(0, 0.1)))
            emotional_intensity = min(1.0, max(0.0, 0.4 + np.random.normal(0, 0.2)))
            
            result = SpeechAnalysisResult(
                words_per_minute=words_per_minute,
                syllables_per_minute=syllables_per_minute,
                character_per_minute=chars_per_minute,
                speech_rate_category=speech_category,
                content_type=content_type,
                pause_ratio=pause_ratio,
                speech_clarity=speech_clarity,
                emotional_intensity=emotional_intensity
            )
            
            self.logger.info(f"语音分析完成: {chars_per_minute:.1f} CPM, {speech_category.value}, {content_type.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"语音分析失败: {e}")
            # 返回默认结果
            return SpeechAnalysisResult(
                words_per_minute=180,
                syllables_per_minute=200,
                character_per_minute=240,
                speech_rate_category=SpeechRateCategory.NORMAL,
                content_type=ContentType.PRESENTATION,
                pause_ratio=0.15,
                speech_clarity=0.8,
                emotional_intensity=0.5
            )
    
    def _categorize_speech_rate(self, chars_per_minute: float) -> SpeechRateCategory:
        """分类语速"""
        if chars_per_minute < 180:
            return SpeechRateCategory.VERY_SLOW
        elif chars_per_minute < 240:
            return SpeechRateCategory.SLOW
        elif chars_per_minute < 300:
            return SpeechRateCategory.NORMAL
        elif chars_per_minute < 400:
            return SpeechRateCategory.FAST
        else:
            return SpeechRateCategory.VERY_FAST
    
    async def _detect_content_type(self, transcript: str) -> ContentType:
        """检测内容类型"""
        transcript_lower = transcript.lower()
        
        # 技术内容关键词
        technical_keywords = ['api', 'algorithm', 'function', 'method', 'class', 'variable', 
                            'database', 'server', 'client', '算法', '函数', '方法', '数据库']
        
        # 演示内容关键词
        presentation_keywords = ['slide', 'chart', 'graph', '幻灯片', '图表', '显示', '展示',
                               'first', 'second', 'next', '第一', '第二', '接下来']
        
        # 讲座关键词
        lecture_keywords = ['lesson', 'chapter', 'study', 'learn', '课程', '学习', '章节',
                          'understand', '理解', '掌握']
        
        # 对话关键词
        conversation_keywords = ['我们', '你们', 'we', 'you', 'question', 'answer', '问题', '回答']
        
        # 计算匹配度
        technical_score = sum(1 for keyword in technical_keywords if keyword in transcript_lower)
        presentation_score = sum(1 for keyword in presentation_keywords if keyword in transcript_lower)
        lecture_score = sum(1 for keyword in lecture_keywords if keyword in transcript_lower)
        conversation_score = sum(1 for keyword in conversation_keywords if keyword in transcript_lower)
        
        # 选择最高分的类型
        scores = {
            ContentType.TECHNICAL: technical_score,
            ContentType.PRESENTATION: presentation_score,
            ContentType.LECTURE: lecture_score,
            ContentType.CONVERSATION: conversation_score,
            ContentType.NARRATION: 0  # 默认值
        }
        
        max_type = max(scores.items(), key=lambda x: x[1])
        return max_type[0] if max_type[1] > 0 else ContentType.NARRATION
    
    async def _estimate_audio_duration(self, audio_path: str) -> float:
        """估算音频时长"""
        try:
            # 简单的时长估算（实际项目中应使用ffprobe或librosa）
            import os
            file_size = os.path.getsize(audio_path)
            # 假设平均比特率计算时长（这是一个粗略估算）
            estimated_duration = max(10.0, file_size / (128 * 1024 / 8))  # 假设128kbps
            return min(estimated_duration, 3600)  # 限制在1小时内
        except Exception:
            return 60.0  # 默认1分钟
    
    def optimize_subtitle_timing(self, segments: List[SubtitleSegment], 
                               speech_analysis: SpeechAnalysisResult) -> List[SubtitleSegment]:
        """优化字幕时长"""
        self.logger.info(f"开始优化 {len(segments)} 个字幕片段的时长")
        start_time = time.time()
        
        optimized_segments = []
        total_improvement = 0.0
        optimized_count = 0
        
        for i, segment in enumerate(segments):
            try:
                # 计算推荐时长
                recommended_duration = self._calculate_recommended_duration(segment, speech_analysis)
                
                # 计算质量分数
                quality_score = self._calculate_quality_score(segment, speech_analysis)
                
                # 判断是否需要优化
                improvement_needed = abs(segment.duration - recommended_duration) / segment.duration
                
                if improvement_needed > self.config["min_improvement_threshold"]:
                    # 需要优化
                    optimized_segment = self._apply_timing_optimization(
                        segment, recommended_duration, quality_score, i, len(segments)
                    )
                    optimized_segments.append(optimized_segment)
                    
                    total_improvement += improvement_needed
                    optimized_count += 1
                    
                    self.logger.debug(f"片段 {i+1} 优化: {segment.duration:.2f}s -> {optimized_segment.duration:.2f}s")
                else:
                    # 无需优化，保持原样
                    segment.recommended_duration = recommended_duration
                    segment.quality_score = quality_score
                    optimized_segments.append(segment)
            
            except Exception as e:
                self.logger.warning(f"片段 {i+1} 优化失败: {e}")
                optimized_segments.append(segment)
        
        # 全局时间轴调整
        optimized_segments = self._adjust_global_timeline(optimized_segments)
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self._update_optimization_stats(len(segments), optimized_count, 
                                      total_improvement, processing_time)
        
        self.logger.info(f"时长优化完成: {optimized_count}/{len(segments)} 个片段被优化, "
                        f"平均改进: {(total_improvement/max(optimized_count, 1))*100:.1f}%, "
                        f"处理耗时: {processing_time:.3f}s")
        
        return optimized_segments
    
    def _calculate_recommended_duration(self, segment: SubtitleSegment, 
                                     speech_analysis: SpeechAnalysisResult) -> float:
        """计算推荐时长"""
        # 基于字符数的基础时长
        chinese_chars = segment.chinese_char_count
        english_chars = segment.character_count - chinese_chars
        
        # 语言特定的阅读时间
        chinese_reading_time = chinese_chars / self.timing_rules.chinese_reading_speed
        english_reading_time = english_chars / self.timing_rules.english_reading_speed
        
        base_duration = chinese_reading_time + english_reading_time
        
        # 应用内容类型调整 (🎯 修复：确保技术内容时长更长)
        content_multiplier = self.timing_rules.content_speed_multipliers.get(
            speech_analysis.content_type, 1.0
        )
        
        # 🎯 强化复杂度调整
        complexity_adjustment = 1.0 + (speech_analysis.complexity_factor * 0.5)  # 增加影响力
        
        # 🎯 修复语速调整 - 确保正确的反比关系
        speech_rate_adjustment = {
            SpeechRateCategory.VERY_SLOW: 1.6,   # 更慢语速需要更长时间
            SpeechRateCategory.SLOW: 1.3,
            SpeechRateCategory.NORMAL: 1.0,
            SpeechRateCategory.FAST: 0.7,        # 快语速需要更短时间
            SpeechRateCategory.VERY_FAST: 0.5    # 极快语速大幅缩短
        }
        
        speech_multiplier = speech_rate_adjustment.get(speech_analysis.speech_rate_category, 1.0)
        
        # 计算最终推荐时长
        recommended = base_duration * content_multiplier * complexity_adjustment * speech_multiplier
        
        # 🎯 动态调整最大时长限制以支持复杂内容
        min_duration = self.timing_rules.min_duration_ms / 1000.0
        max_duration = self.timing_rules.max_duration_ms / 1000.0
        
        # 对于复杂内容类型，允许更长的显示时间
        if speech_analysis.content_type in [ContentType.TECHNICAL, ContentType.LECTURE]:
            max_duration *= 1.3  # 技术和讲座内容可以延长30%
        
        return max(min_duration, min(recommended, max_duration))
    
    def _calculate_quality_score(self, segment: SubtitleSegment, 
                               speech_analysis: SpeechAnalysisResult) -> float:
        """计算质量分数 (0-1)"""
        quality = 1.0
        
        # 时长合理性检查
        recommended_duration = self._calculate_recommended_duration(segment, speech_analysis)
        duration_ratio = segment.duration / recommended_duration
        
        if duration_ratio < 0.7 or duration_ratio > 1.5:
            quality -= 0.3  # 时长偏差大
        elif duration_ratio < 0.85 or duration_ratio > 1.15:
            quality -= 0.1  # 时长稍有偏差
        
        # 阅读速度检查
        reading_speed = segment.reading_speed_cps
        optimal_speed = self.timing_rules.optimal_chars_per_second
        
        if reading_speed > optimal_speed * 1.5 or reading_speed < optimal_speed * 0.5:
            quality -= 0.2  # 阅读速度不合理
        
        # 文本长度检查
        if segment.character_count < 5:
            quality -= 0.1  # 过短
        elif segment.character_count > 80:
            quality -= 0.15  # 过长
        
        # 🎯 优化语言混合度检查
        if segment.chinese_char_count > 0 and (segment.character_count - segment.chinese_char_count) > 0:
            # 中英文混合，需要额外考虑
            mixed_ratio = min(segment.chinese_char_count, segment.character_count - segment.chinese_char_count) / segment.character_count
            if mixed_ratio > 0.1:  # 降低混合度阈值
                quality += 0.15  # 增加混合内容的质量加分
                
        # 🎯 额外的质量提升机制
        # 合理时长范围内的内容给予质量加分
        if 1.5 <= segment.duration <= 5.0:
            quality += 0.1
        
        # 字符密度合理的内容给予加分
        char_density = segment.character_count / segment.duration if segment.duration > 0 else 0
        if 10 <= char_density <= 25:  # 合理的字符密度范围
            quality += 0.1
        
        return max(0.0, min(1.0, quality))
    
    def _apply_timing_optimization(self, segment: SubtitleSegment, recommended_duration: float,
                                 quality_score: float, segment_index: int, total_segments: int) -> SubtitleSegment:
        """应用时长优化"""
        # 计算优化后的结束时间
        duration_diff = recommended_duration - segment.duration
        
        # 应用激进程度限制
        aggressive_level = self.config["optimization_aggressive_level"]
        actual_adjustment = duration_diff * aggressive_level
        
        # 应用压缩/扩展比例限制
        max_extension = segment.duration * self.config["max_duration_extension_ratio"]
        min_compression = segment.duration * self.config["min_duration_compression_ratio"]
        
        new_duration = segment.duration + actual_adjustment
        new_duration = max(min_compression, min(new_duration, max_extension))
        
        # 创建优化后的片段
        optimized_segment = SubtitleSegment(
            text=segment.text,
            start_time=segment.start_time,
            end_time=segment.start_time + new_duration,
            original_duration=segment.duration,
            character_count=segment.character_count,
            chinese_char_count=segment.chinese_char_count,
            english_word_count=segment.english_word_count,
            content_type=segment.content_type,
            complexity_score=segment.complexity_score,
            recommended_duration=recommended_duration,
            quality_score=quality_score
        )
        
        return optimized_segment
    
    def _adjust_global_timeline(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """全局时间轴调整"""
        if not segments:
            return segments
        
        adjusted_segments = []
        current_time = segments[0].start_time
        
        for i, segment in enumerate(segments):
            # 调整开始时间
            if i > 0:
                # 确保最小间隙
                min_gap = self.timing_rules.min_gap_ms / 1000.0
                current_time = max(current_time + min_gap, segment.start_time)
            
            # 创建调整后的片段
            adjusted_segment = SubtitleSegment(
                text=segment.text,
                start_time=current_time,
                end_time=current_time + segment.duration,
                original_duration=segment.original_duration,
                character_count=segment.character_count,
                chinese_char_count=segment.chinese_char_count,
                english_word_count=segment.english_word_count,
                content_type=segment.content_type,
                complexity_score=getattr(segment, 'complexity_score', 0.0),
                recommended_duration=getattr(segment, 'recommended_duration', segment.duration),
                quality_score=getattr(segment, 'quality_score', 1.0)
            )
            
            adjusted_segments.append(adjusted_segment)
            current_time = adjusted_segment.end_time
        
        return adjusted_segments
    
    def _update_optimization_stats(self, total: int, optimized: int, 
                                 improvement: float, processing_time: float) -> None:
        """更新优化统计"""
        self.optimization_stats.update({
            "total_segments": total,
            "optimized_segments": optimized,
            "average_improvement": improvement / max(optimized, 1),
            "processing_time": processing_time
        })
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        stats = self.optimization_stats.copy()
        stats["optimization_rate"] = (stats["optimized_segments"] / max(stats["total_segments"], 1)) * 100
        stats["average_improvement_percent"] = stats["average_improvement"] * 100
        
        return {
            "statistics": stats,
            "configuration": self.config,
            "timing_rules": {
                "min_duration_ms": self.timing_rules.min_duration_ms,
                "max_duration_ms": self.timing_rules.max_duration_ms,
                "optimal_cps": self.timing_rules.optimal_chars_per_second,
                "chinese_reading_speed": self.timing_rules.chinese_reading_speed,
                "english_reading_speed": self.timing_rules.english_reading_speed
            }
        }


# 测试和示例代码
async def test_subtitle_timing_optimization():
    """测试字幕时长优化功能"""
    print("🚀 字幕时长优化系统测试")
    print("=" * 60)
    
    # 创建优化器
    optimizer = IntelligentSubtitleTimingOptimizer()
    
    # 模拟语音分析结果
    speech_analysis = SpeechAnalysisResult(
        words_per_minute=180,
        syllables_per_minute=220,
        character_per_minute=280,
        speech_rate_category=SpeechRateCategory.NORMAL,
        content_type=ContentType.PRESENTATION,
        pause_ratio=0.15,
        speech_clarity=0.85,
        emotional_intensity=0.6
    )
    
    # 测试字幕片段
    test_segments = [
        SubtitleSegment(
            text="这是第一个字幕片段，内容相对较短。",
            start_time=0.0,
            end_time=2.5,
            original_duration=2.5,
            character_count=0,  # 将自动计算
            chinese_char_count=0,
            english_word_count=0
        ),
        SubtitleSegment(
            text="This is a mixed content subtitle with 中英文混合内容，需要进行时长优化处理。",
            start_time=3.0,
            end_time=6.5,
            original_duration=3.5,
            character_count=0,
            chinese_char_count=0,
            english_word_count=0
        ),
        SubtitleSegment(
            text="技术性内容包含API调用、数据库操作和算法实现等复杂概念。",
            start_time=7.0,
            end_time=9.0,
            original_duration=2.0,
            character_count=0,
            chinese_char_count=0,
            english_word_count=0
        )
    ]
    
    print(f"🧪 测试语音分析结果:")
    print(f"  语速分类: {speech_analysis.speech_rate_category.value}")
    print(f"  内容类型: {speech_analysis.content_type.value}")
    print(f"  最佳显示速度: {speech_analysis.optimal_display_wpm:.1f} WPM")
    print(f"  复杂度因子: {speech_analysis.complexity_factor:.2f}")
    print()
    
    print(f"📝 原始字幕片段:")
    for i, segment in enumerate(test_segments):
        print(f"  片段{i+1}: '{segment.text[:30]}...' "
              f"({segment.duration:.2f}s, {segment.character_count}字符)")
    print()
    
    # 执行优化
    optimized_segments = optimizer.optimize_subtitle_timing(test_segments, speech_analysis)
    
    print(f"✨ 优化后的字幕片段:")
    for i, segment in enumerate(optimized_segments):
        original = test_segments[i]
        improvement = abs(segment.duration - original.duration) / original.duration * 100
        print(f"  片段{i+1}: {original.duration:.2f}s -> {segment.duration:.2f}s "
              f"(改进: {improvement:.1f}%, 质量: {segment.quality_score:.2f})")
    print()
    
    # 显示优化报告
    report = optimizer.get_optimization_report()
    print(f"📊 优化报告:")
    print(f"  优化率: {report['statistics']['optimization_rate']:.1f}%")
    print(f"  平均改进: {report['statistics']['average_improvement_percent']:.1f}%")
    print(f"  处理时间: {report['statistics']['processing_time']:.3f}秒")
    
    print("\n✅ 字幕时长优化测试完成!")
    return optimized_segments, report


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_subtitle_timing_optimization())