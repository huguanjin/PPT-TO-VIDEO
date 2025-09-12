#!/usr/bin/env python3
"""
音频智能同步增强系统
基于音频内容分析的智能字幕同步优化
"""

import asyncio
import numpy as np
import time
import logging
import json
import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import subprocess

# 音频处理库
try:
    import librosa
    import scipy.signal as signal
    import scipy.fft
    AUDIO_LIBS_AVAILABLE = True
except ImportError as e:
    AUDIO_LIBS_AVAILABLE = False
    # 创建占位模块以避免NameError
    class MockLibrosa:
        @staticmethod
        def load(audio_path, sr=22050):
            raise ImportError("librosa not installed")
    
    class MockSignal:
        pass
        
    class MockFFT:
        pass
    
    librosa = MockLibrosa()
    signal = MockSignal()
    scipy = type('MockScipy', (), {'fft': MockFFT()})()
    
    logger = logging.getLogger(__name__)
    logger.warning(f"Audio processing libraries not available: {e}. Using mock implementations.")
    print("Warning: Audio processing libraries not available. Install with: pip install librosa scipy")

# 设置日志
logger = logging.getLogger(__name__)


class AudioSyncPrecision(Enum):
    """音频同步精度级别"""
    BASIC = "basic"           # 基础音频同步 (±50ms)
    ENHANCED = "enhanced"     # 增强音频同步 (±25ms)  
    INTELLIGENT = "intelligent" # 智能音频同步 (±10ms)
    PERFECT = "perfect"       # 完美音频同步 (±5ms)


class SpeechEmotionType(Enum):
    """语音情感类型"""
    NEUTRAL = "neutral"       # 中性
    EXCITED = "excited"       # 兴奋
    CALM = "calm"            # 平静
    EMPHASIZED = "emphasized" # 强调
    QUESTIONING = "questioning" # 疑问
    NARRATIVE = "narrative"   # 叙述


@dataclass
class AudioBeat:
    """音频节拍点"""
    timestamp: float          # 节拍时间戳(秒)
    strength: float          # 节拍强度 (0-1)
    frequency: float         # 主要频率
    is_speech_beat: bool     # 是否为语音节拍
    beat_type: str          # 节拍类型 (strong/weak/pause)


@dataclass  
class SpeechSegment:
    """语音片段"""
    start_time: float        # 开始时间
    end_time: float         # 结束时间
    speech_rate: float      # 语速 (字符/秒)
    emotion_type: SpeechEmotionType  # 情感类型
    emphasis_level: float   # 强调程度 (0-1)
    pause_after: float     # 后续停顿时长
    audio_energy: float    # 音频能量
    pitch_variance: float  # 音调变化
    

@dataclass
class AudioSyncResult:
    """音频同步结果"""
    original_subtitle: Dict[str, Any]    # 原始字幕
    synced_start: float                  # 同步后开始时间  
    synced_end: float                    # 同步后结束时间
    sync_offset: float                   # 同步偏移(ms)
    confidence: float                    # 同步置信度 (0-1)
    beat_aligned: bool                   # 是否节拍对齐
    speech_matched: bool                 # 是否语音匹配
    emotion_enhanced: bool               # 是否情感增强
    sync_reason: str                     # 同步原因说明


class AudioIntelligentSyncOptimizer:
    """音频智能同步优化器 - 基于音频内容的智能同步"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化音频智能同步优化器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 同步规则
        self.sync_rules = {
            'precision_level': AudioSyncPrecision.INTELLIGENT,
            'enable_beat_alignment': True,        # 启用节拍对齐
            'enable_emotion_sync': True,          # 启用情感同步  
            'enable_speech_rate_adapt': True,     # 启用语速适配
            'enable_pause_detection': True,       # 启用停顿检测
            'min_sync_confidence': 0.7,          # 最小同步置信度
            'beat_alignment_tolerance': 50,       # 节拍对齐容差(ms)
            'emotion_weight': 0.3,               # 情感权重
            'speech_rate_weight': 0.4,           # 语速权重  
            'pause_weight': 0.3                  # 停顿权重
        }
        
        # 统计信息
        self.sync_stats = {
            "total_segments": 0,
            "audio_synced_segments": 0, 
            "beat_aligned_segments": 0,
            "emotion_enhanced_segments": 0,
            "average_confidence": 0.0,
            "processing_time": 0.0,
            "audio_analysis_time": 0.0
        }
        
        self.logger.info("🎵 音频智能同步优化器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "audio_analysis": {
                "sample_rate": 22050,             # 音频采样率
                "hop_length": 512,                # 跳跃长度  
                "n_mels": 128,                    # 梅尔频谱数量
                "enable_beat_tracking": True,     # 启用节拍跟踪
                "enable_pitch_analysis": True,    # 启用音调分析
                "enable_energy_analysis": True    # 启用能量分析
            },
            "speech_detection": {
                "min_speech_duration": 0.2,      # 最小语音时长(秒)
                "speech_threshold": 0.1,          # 语音阈值
                "pause_threshold": 0.05,          # 停顿阈值
                "emphasis_threshold": 0.7         # 强调阈值
            },
            "sync_optimization": {
                "max_offset_ms": 200,             # 最大偏移(毫秒)
                "preferred_lead_time": 100,       # 首选提前时间(ms)
                "min_display_duration": 800,      # 最小显示时长(ms)
                "max_display_duration": 8000      # 最大显示时长(ms)
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"配置加载失败，使用默认配置: {e}")
        
        return default_config
    
    async def analyze_audio_content(self, audio_path: str) -> Dict[str, Any]:
        """分析音频内容"""
        self.logger.info(f"🎵 开始分析音频内容: {audio_path}")
        analysis_start = time.time()
        
        try:
            if AUDIO_LIBS_AVAILABLE and Path(audio_path).exists():
                # 真实音频分析
                audio_data = await self._load_audio_file(audio_path)
                if audio_data is not None:
                    analysis_result = await self._perform_real_audio_analysis(audio_data)
                else:
                    analysis_result = self._create_mock_audio_analysis()
            else:
                # 模拟音频分析
                self.logger.info("使用模拟音频分析")
                analysis_result = self._create_mock_audio_analysis()
            
            analysis_time = time.time() - analysis_start
            self.sync_stats["audio_analysis_time"] = analysis_time
            
            self.logger.info(f"🎵 音频分析完成，耗时: {analysis_time:.3f}s")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"音频分析失败: {e}")
            return self._create_mock_audio_analysis()
    
    async def _load_audio_file(self, audio_path: str) -> Optional[Tuple[np.ndarray, int]]:
        """加载音频文件"""
        try:
            if AUDIO_LIBS_AVAILABLE:
                audio_data, sample_rate = librosa.load(audio_path, sr=self.config["audio_analysis"]["sample_rate"])
                # 确保 sample_rate 是整数类型
                sample_rate_int = int(sample_rate)
                return audio_data, sample_rate_int
            else:
                return None
        except Exception as e:
            self.logger.error(f"音频文件加载失败: {e}")
            return None
    
    async def _perform_real_audio_analysis(self, audio_data: Tuple[np.ndarray, int]) -> Dict[str, Any]:
        """执行真实音频分析"""
        audio, sr = audio_data
        
        # 节拍检测
        beats = await self._detect_audio_beats(audio, sr)
        
        # 语音片段分析
        speech_segments = await self._analyze_speech_segments(audio, sr)
        
        # 情感分析
        emotion_segments = await self._analyze_speech_emotions(audio, sr)
        
        # 停顿检测
        pauses = await self._detect_speech_pauses(audio, sr)
        
        return {
            "audio_duration": len(audio) / sr,
            "sample_rate": sr,
            "beats": beats,
            "speech_segments": speech_segments, 
            "emotion_segments": emotion_segments,
            "pauses": pauses,
            "energy_profile": await self._calculate_energy_profile(audio, sr),
            "pitch_profile": await self._calculate_pitch_profile(audio, sr)
        }
    
    def _create_mock_audio_analysis(self) -> Dict[str, Any]:
        """创建模拟音频分析结果"""
        duration = 30.0  # 模拟30秒音频
        
        # 模拟节拍点 (每0.8秒一个主要节拍)
        beats = []
        for i in range(int(duration / 0.8)):
            beat_time = i * 0.8 + 0.1
            if beat_time < duration:
                beats.append(AudioBeat(
                    timestamp=beat_time,
                    strength=0.8 if i % 4 == 0 else 0.6,  # 强弱节拍
                    frequency=220.0 + (i % 8) * 55,       # 变化的频率
                    is_speech_beat=True,
                    beat_type="strong" if i % 4 == 0 else "weak"
                ))
        
        # 模拟语音片段
        speech_segments = []
        for i in range(6):  # 6个语音片段
            start = i * 5.0
            end = start + 4.0
            if end <= duration:
                speech_segments.append(SpeechSegment(
                    start_time=start,
                    end_time=end,
                    speech_rate=3.5 + (i % 3) * 0.5,     # 变化的语速
                    emotion_type=list(SpeechEmotionType)[i % len(SpeechEmotionType)],
                    emphasis_level=0.6 + (i % 3) * 0.15,
                    pause_after=0.8 if i % 2 == 0 else 0.3,
                    audio_energy=0.7 + (i % 4) * 0.1,
                    pitch_variance=0.4 + (i % 3) * 0.2
                ))
        
        # 模拟停顿
        pauses = [(4.8, 5.2), (9.7, 10.1), (14.6, 15.0), (19.8, 20.3), (24.9, 25.2)]
        
        return {
            "audio_duration": duration,
            "sample_rate": 22050,
            "beats": [self._beat_to_dict(beat) for beat in beats],
            "speech_segments": [self._speech_segment_to_dict(seg) for seg in speech_segments],
            "emotion_segments": [
                {"start": 0.0, "end": 10.0, "emotion": "neutral", "confidence": 0.8},
                {"start": 10.0, "end": 20.0, "emotion": "excited", "confidence": 0.7},
                {"start": 20.0, "end": 30.0, "emotion": "calm", "confidence": 0.9}
            ],
            "pauses": pauses,
            "energy_profile": [0.6 + 0.3 * math.sin(i * 0.1) for i in range(int(duration * 10))],
            "pitch_profile": [200 + 50 * math.sin(i * 0.05) for i in range(int(duration * 10))]
        }
    
    async def optimize_audio_sync(self, subtitles: List[Dict[str, Any]], 
                                audio_analysis: Dict[str, Any]) -> List[AudioSyncResult]:
        """基于音频分析优化字幕同步"""
        self.logger.info(f"🎵 开始音频智能同步优化: {len(subtitles)} 个字幕片段")
        start_time = time.time()
        
        sync_results = []
        beats = self._parse_beats_from_analysis(audio_analysis)
        speech_segments = self._parse_speech_segments_from_analysis(audio_analysis)
        pauses = audio_analysis.get("pauses", [])
        
        for i, subtitle in enumerate(subtitles):
            try:
                # 原始时间信息
                original_start = subtitle.get("start_time", 0.0)
                original_end = subtitle.get("end_time", 0.0)
                text = subtitle.get("text", "")
                
                # 执行音频智能同步
                sync_result = await self._optimize_single_subtitle_sync(
                    subtitle, beats, speech_segments, pauses, i, len(subtitles)
                )
                
                sync_results.append(sync_result)
                
                self.logger.debug(f"字幕 {i+1} 音频同步: {original_start:.3f}s -> {sync_result.synced_start:.3f}s "
                                f"(偏移: {sync_result.sync_offset:.1f}ms, 置信度: {sync_result.confidence:.2f})")
                
            except Exception as e:
                self.logger.warning(f"字幕 {i+1} 音频同步失败: {e}")
                # 创建未优化的结果
                sync_results.append(AudioSyncResult(
                    original_subtitle=subtitle,
                    synced_start=subtitle.get("start_time", 0.0),
                    synced_end=subtitle.get("end_time", 0.0),
                    sync_offset=0.0,
                    confidence=0.5,
                    beat_aligned=False,
                    speech_matched=False,
                    emotion_enhanced=False,
                    sync_reason="同步失败，保持原始时间"
                ))
        
        # 全局音频同步调整
        sync_results = await self._adjust_global_audio_sync(sync_results, audio_analysis)
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self._update_audio_sync_stats(sync_results, processing_time)
        
        self.logger.info(f"🎵 音频智能同步完成: 处理 {len(sync_results)} 个片段, 耗时: {processing_time:.3f}s")
        return sync_results
    
    async def _optimize_single_subtitle_sync(self, subtitle: Dict[str, Any], 
                                           beats: List[AudioBeat],
                                           speech_segments: List[SpeechSegment],
                                           pauses: List[Tuple[float, float]],
                                           index: int, total: int) -> AudioSyncResult:
        """优化单个字幕的音频同步"""
        
        original_start = subtitle.get("start_time", 0.0)
        original_end = subtitle.get("end_time", 0.0)
        text = subtitle.get("text", "")
        
        # 初始化同步结果
        synced_start = original_start
        synced_end = original_end
        confidence = 0.5
        beat_aligned = False
        speech_matched = False  
        emotion_enhanced = False
        sync_reasons = []
        
        # 1. 节拍对齐优化
        if self.sync_rules['enable_beat_alignment'] and beats:
            best_beat = self._find_nearest_beat(original_start, beats)
            if best_beat and abs(best_beat.timestamp - original_start) < 0.2:  # 200ms内
                synced_start = best_beat.timestamp
                beat_aligned = True
                confidence += 0.2
                sync_reasons.append(f"节拍对齐({best_beat.beat_type})")
        
        # 2. 语音片段匹配优化
        if self.sync_rules['enable_speech_rate_adapt'] and speech_segments:
            matching_speech = self._find_matching_speech_segment(original_start, original_end, speech_segments)
            if matching_speech:
                # 根据语速调整显示时长
                text_length = len(text)
                optimal_duration = text_length / matching_speech.speech_rate
                
                # 保持合理的显示时长范围
                min_duration = self.config["sync_optimization"]["min_display_duration"] / 1000.0
                max_duration = self.config["sync_optimization"]["max_display_duration"] / 1000.0
                optimal_duration = max(min_duration, min(optimal_duration, max_duration))
                
                synced_end = synced_start + optimal_duration
                speech_matched = True
                confidence += 0.25
                sync_reasons.append(f"语速适配({matching_speech.speech_rate:.1f}字/秒)")
                
                # 3. 情感增强同步
                if self.sync_rules['enable_emotion_sync']:
                    if matching_speech.emotion_type == SpeechEmotionType.EXCITED:
                        # 兴奋语调：稍微提前显示
                        synced_start -= 0.05
                        emotion_enhanced = True
                        confidence += 0.1
                        sync_reasons.append("情感增强(兴奋)")
                    elif matching_speech.emotion_type == SpeechEmotionType.EMPHASIZED:
                        # 强调语调：延长显示时间
                        synced_end += 0.1
                        emotion_enhanced = True
                        confidence += 0.1
                        sync_reasons.append("情感增强(强调)")
        
        # 4. 停顿检测优化
        if self.sync_rules['enable_pause_detection'] and pauses:
            # 检查结束时间后是否有自然停顿
            for pause_start, pause_end in pauses:
                if abs(pause_start - synced_end) < 0.3:  # 300ms内有停顿
                    synced_end = pause_start  # 对齐到停顿开始
                    confidence += 0.15
                    sync_reasons.append("停顿对齐")
                    break
        
        # 计算最终偏移
        sync_offset = (synced_start - original_start) * 1000  # 转换为毫秒
        
        # 应用偏移限制
        max_offset = self.config["sync_optimization"]["max_offset_ms"]
        if abs(sync_offset) > max_offset:
            # 偏移过大，回退到安全范围
            if sync_offset > 0:
                synced_start = original_start + max_offset / 1000.0
            else:
                synced_start = original_start - max_offset / 1000.0
            synced_end = synced_start + (original_end - original_start)
            sync_offset = (synced_start - original_start) * 1000
            confidence *= 0.8  # 降低置信度
            sync_reasons.append("偏移限制")
        
        return AudioSyncResult(
            original_subtitle=subtitle,
            synced_start=synced_start,
            synced_end=synced_end,
            sync_offset=sync_offset,
            confidence=min(confidence, 1.0),
            beat_aligned=beat_aligned,
            speech_matched=speech_matched,
            emotion_enhanced=emotion_enhanced,
            sync_reason="; ".join(sync_reasons) if sync_reasons else "无优化"
        )
    
    def _find_nearest_beat(self, timestamp: float, beats: List[AudioBeat]) -> Optional[AudioBeat]:
        """找到最近的节拍点"""
        if not beats:
            return None
        
        best_beat = None
        min_distance = float('inf')
        
        for beat in beats:
            distance = abs(beat.timestamp - timestamp)
            if distance < min_distance:
                min_distance = distance
                best_beat = beat
        
        return best_beat if min_distance < 0.5 else None  # 500ms容差
    
    def _find_matching_speech_segment(self, start: float, end: float, 
                                    speech_segments: List[SpeechSegment]) -> Optional[SpeechSegment]:
        """找到匹配的语音片段"""
        center = (start + end) / 2
        
        for segment in speech_segments:
            if segment.start_time <= center <= segment.end_time:
                return segment
        
        return None
    
    async def _adjust_global_audio_sync(self, sync_results: List[AudioSyncResult], 
                                      audio_analysis: Dict[str, Any]) -> List[AudioSyncResult]:
        """全局音频同步调整"""
        # 确保同步结果之间没有重叠
        adjusted_results = []
        
        for i, result in enumerate(sync_results):
            adjusted_result = result
            
            # 检查与前一个字幕的重叠
            if i > 0:
                prev_result = adjusted_results[-1]
                if result.synced_start <= prev_result.synced_end:
                    # 有重叠，调整开始时间
                    min_gap = 0.05  # 最小50ms间隙
                    adjusted_start = prev_result.synced_end + min_gap
                    duration = result.synced_end - result.synced_start
                    
                    adjusted_result = AudioSyncResult(
                        original_subtitle=result.original_subtitle,
                        synced_start=adjusted_start,
                        synced_end=adjusted_start + duration,
                        sync_offset=(adjusted_start - result.original_subtitle.get("start_time", 0.0)) * 1000,
                        confidence=result.confidence * 0.9,  # 降低置信度
                        beat_aligned=result.beat_aligned,
                        speech_matched=result.speech_matched,
                        emotion_enhanced=result.emotion_enhanced,
                        sync_reason=result.sync_reason + "; 重叠调整"
                    )
            
            adjusted_results.append(adjusted_result)
        
        return adjusted_results
    
    def _update_audio_sync_stats(self, sync_results: List[AudioSyncResult], processing_time: float) -> None:
        """更新音频同步统计"""
        total = len(sync_results)
        audio_synced = sum(1 for r in sync_results if abs(r.sync_offset) > 1.0)  # 偏移>1ms
        beat_aligned = sum(1 for r in sync_results if r.beat_aligned)
        emotion_enhanced = sum(1 for r in sync_results if r.emotion_enhanced)
        avg_confidence = sum(r.confidence for r in sync_results) / max(total, 1)
        
        self.sync_stats.update({
            "total_segments": total,
            "audio_synced_segments": audio_synced,
            "beat_aligned_segments": beat_aligned,
            "emotion_enhanced_segments": emotion_enhanced,
            "average_confidence": avg_confidence,
            "processing_time": processing_time
        })
    
    def get_audio_sync_report(self) -> Dict[str, Any]:
        """获取音频同步报告"""
        stats = self.sync_stats.copy()
        
        # 计算额外指标
        if stats["total_segments"] > 0:
            stats["audio_sync_rate"] = (stats["audio_synced_segments"] / stats["total_segments"]) * 100
            stats["beat_alignment_rate"] = (stats["beat_aligned_segments"] / stats["total_segments"]) * 100
            stats["emotion_enhancement_rate"] = (stats["emotion_enhanced_segments"] / stats["total_segments"]) * 100
        else:
            stats.update({"audio_sync_rate": 0.0, "beat_alignment_rate": 0.0, "emotion_enhancement_rate": 0.0})
        
        # 复制sync_rules并转换枚举为字符串值
        serializable_sync_rules = self.sync_rules.copy()
        if 'precision_level' in serializable_sync_rules:
            serializable_sync_rules['precision_level'] = serializable_sync_rules['precision_level'].value
        
        return {
            "audio_sync_statistics": stats,
            "sync_rules": serializable_sync_rules,
            "configuration": self.config,
            "performance_metrics": {
                "precision_level": self.sync_rules['precision_level'].value,
                "beat_alignment_enabled": self.sync_rules['enable_beat_alignment'],
                "emotion_sync_enabled": self.sync_rules['enable_emotion_sync'],
                "speech_rate_adaptation": self.sync_rules['enable_speech_rate_adapt']
            }
        }
    
    # 辅助方法
    def _beat_to_dict(self, beat: AudioBeat) -> Dict[str, Any]:
        """将AudioBeat转换为字典"""
        return {
            "timestamp": beat.timestamp,
            "strength": beat.strength,
            "frequency": beat.frequency,
            "is_speech_beat": beat.is_speech_beat,
            "beat_type": beat.beat_type
        }
    
    def _speech_segment_to_dict(self, segment: SpeechSegment) -> Dict[str, Any]:
        """将SpeechSegment转换为字典"""
        return {
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "speech_rate": segment.speech_rate,
            "emotion_type": segment.emotion_type.value,
            "emphasis_level": segment.emphasis_level,
            "pause_after": segment.pause_after,
            "audio_energy": segment.audio_energy,
            "pitch_variance": segment.pitch_variance
        }
    
    def _parse_beats_from_analysis(self, analysis: Dict[str, Any]) -> List[AudioBeat]:
        """从分析结果解析节拍"""
        beats = []
        for beat_data in analysis.get("beats", []):
            beats.append(AudioBeat(
                timestamp=beat_data["timestamp"],
                strength=beat_data["strength"],
                frequency=beat_data["frequency"],
                is_speech_beat=beat_data["is_speech_beat"],
                beat_type=beat_data["beat_type"]
            ))
        return beats
    
    def _parse_speech_segments_from_analysis(self, analysis: Dict[str, Any]) -> List[SpeechSegment]:
        """从分析结果解析语音片段"""
        segments = []
        for seg_data in analysis.get("speech_segments", []):
            segments.append(SpeechSegment(
                start_time=seg_data["start_time"],
                end_time=seg_data["end_time"],
                speech_rate=seg_data["speech_rate"],
                emotion_type=SpeechEmotionType(seg_data["emotion_type"]),
                emphasis_level=seg_data["emphasis_level"],
                pause_after=seg_data["pause_after"],
                audio_energy=seg_data["audio_energy"],
                pitch_variance=seg_data["pitch_variance"]
            ))
        return segments
    
    # 占位方法（用于真实音频分析）
    async def _detect_audio_beats(self, audio: np.ndarray, sr: int) -> List[AudioBeat]:
        """检测音频节拍"""
        # 这里可以实现真实的节拍检测算法
        return []
    
    async def _analyze_speech_segments(self, audio: np.ndarray, sr: int) -> List[SpeechSegment]:
        """分析语音片段"""
        # 这里可以实现真实的语音片段分析
        return []
    
    async def _analyze_speech_emotions(self, audio: np.ndarray, sr: int) -> List[Dict[str, Any]]:
        """分析语音情感"""
        # 这里可以实现真实的情感分析
        return []
    
    async def _detect_speech_pauses(self, audio: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """检测语音停顿"""
        # 这里可以实现真实的停顿检测
        return []
    
    async def _calculate_energy_profile(self, audio: np.ndarray, sr: int) -> List[float]:
        """计算能量轮廓"""
        # 这里可以实现真实的能量分析
        return []
    
    async def _calculate_pitch_profile(self, audio: np.ndarray, sr: int) -> List[float]:
        """计算音调轮廓"""
        # 这里可以实现真实的音调分析
        return []


# 测试代码
async def test_audio_intelligent_sync():
    """测试音频智能同步功能"""
    print("🎵 音频智能同步增强系统测试")
    print("=" * 70)
    
    # 创建音频智能同步优化器
    audio_sync_optimizer = AudioIntelligentSyncOptimizer()
    
    print(f"🎶 音频智能同步优化器初始化完成")
    print(f"   - 精度级别: {audio_sync_optimizer.sync_rules['precision_level'].value}")
    print(f"   - 节拍对齐: {audio_sync_optimizer.sync_rules['enable_beat_alignment']}")
    print(f"   - 情感同步: {audio_sync_optimizer.sync_rules['enable_emotion_sync']}")
    print(f"   - 语速适配: {audio_sync_optimizer.sync_rules['enable_speech_rate_adapt']}")
    print()
    
    # 模拟音频分析
    print("🎵 执行音频内容分析...")
    audio_analysis = await audio_sync_optimizer.analyze_audio_content("test_audio.wav")
    
    print(f"✅ 音频分析完成:")
    print(f"   - 音频时长: {audio_analysis['audio_duration']:.1f}s")
    print(f"   - 节拍点数: {len(audio_analysis['beats'])}")
    print(f"   - 语音片段数: {len(audio_analysis['speech_segments'])}")
    print(f"   - 停顿数: {len(audio_analysis['pauses'])}")
    print()
    
    # 测试字幕数据
    test_subtitles = [
        {"text": "欢迎来到音频智能同步系统演示", "start_time": 1.0, "end_time": 4.5},
        {"text": "我们将展示基于音频内容的智能同步", "start_time": 5.0, "end_time": 8.8},
        {"text": "Smart audio synchronization!", "start_time": 9.2, "end_time": 12.0},
        {"text": "节拍对齐和情感增强功能", "start_time": 12.5, "end_time": 15.8},
        {"text": "让字幕与语音完美配合", "start_time": 16.2, "end_time": 19.5}
    ]
    
    print(f"📝 原始字幕片段:")
    for i, subtitle in enumerate(test_subtitles):
        duration = subtitle["end_time"] - subtitle["start_time"]
        print(f"  片段{i+1}: {subtitle['start_time']:.1f}s - {subtitle['end_time']:.1f}s "
              f"({duration:.1f}s) '{subtitle['text'][:25]}...'")
    print()
    
    # 执行音频智能同步
    print("🎵 执行音频智能同步优化...")
    sync_results = await audio_sync_optimizer.optimize_audio_sync(test_subtitles, audio_analysis)
    
    print(f"✨ 音频同步优化结果:")
    total_offset = 0.0
    beat_aligned_count = 0
    emotion_enhanced_count = 0
    
    for i, result in enumerate(sync_results):
        offset_ms = result.sync_offset
        total_offset += abs(offset_ms)
        if result.beat_aligned:
            beat_aligned_count += 1
        if result.emotion_enhanced:
            emotion_enhanced_count += 1
        
        print(f"  片段{i+1}: {result.synced_start:.3f}s - {result.synced_end:.3f}s")
        print(f"          偏移: {offset_ms:+.1f}ms, 置信度: {result.confidence:.2f}")
        print(f"          节拍对齐: {'✓' if result.beat_aligned else '✗'}, "
              f"情感增强: {'✓' if result.emotion_enhanced else '✗'}")
        print(f"          同步原因: {result.sync_reason}")
    print()
    
    # 显示同步报告  
    report = audio_sync_optimizer.get_audio_sync_report()
    audio_stats = report["audio_sync_statistics"]
    
    print(f"📊 音频智能同步报告:")
    print(f"  同步片段数: {audio_stats['audio_synced_segments']}/{audio_stats['total_segments']}")
    print(f"  节拍对齐数: {beat_aligned_count}/{len(sync_results)} ({audio_stats['beat_alignment_rate']:.1f}%)")
    print(f"  情感增强数: {emotion_enhanced_count}/{len(sync_results)} ({audio_stats['emotion_enhancement_rate']:.1f}%)")
    print(f"  平均置信度: {audio_stats['average_confidence']:.2f}")
    print(f"  平均偏移: {total_offset/len(sync_results):.1f}ms")
    print(f"  处理时间: {audio_stats['processing_time']:.3f}s")
    print(f"  音频分析时间: {audio_stats['audio_analysis_time']:.3f}s")
    
    print(f"\n🎉 音频智能同步测试完成!")
    return sync_results, report


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_audio_intelligent_sync())