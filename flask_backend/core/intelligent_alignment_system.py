"""
智能对齐系统集成模块
Phase 3: 智能对齐系统的核心集成层
整合音频特征提取、语音边界检测和DTW对齐功能
"""
import os
import json
import time
from typing import List, Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict, field
import logging
import asyncio
from pathlib import Path

from .audio_feature_extractor import (
    AudioFeatureExtractor, AudioConfig, AudioFeatures, 
    extract_audio_features
)
from .speech_boundary_detector import (
    SpeechBoundaryDetector, BoundaryConfig, SpeechBoundary, SpeechSegment,
    detect_speech_boundaries
)
from .dtw_aligner import (
    DTWAligner, DTWConfig, SubtitleEntry, AlignmentResult,
    align_audio_subtitles
)

logger = logging.getLogger(__name__)


@dataclass
class IntelligentAlignmentConfig:
    """智能对齐系统配置"""
    # 子模块配置 - 使用lambda函数延迟实例化
    audio_config: AudioConfig = field(default_factory=lambda: AudioConfig())
    boundary_config: BoundaryConfig = field(default_factory=lambda: BoundaryConfig())
    dtw_config: DTWConfig = field(default_factory=lambda: DTWConfig())
    
    # 系统级参数
    precision_target: float = 0.1       # 目标精度(秒)，100ms
    min_confidence: float = 0.7         # 最小置信度
    enable_iterative: bool = True       # 启用迭代优化
    max_iterations: int = 3             # 最大迭代次数
    
    # 质量控制
    quality_threshold: float = 0.8      # 质量阈值
    enable_validation: bool = True      # 启用结果验证
    
    # 性能配置
    enable_caching: bool = True         # 启用结果缓存
    parallel_processing: bool = True    # 并行处理
    max_workers: int = 4                # 最大工作线程
    
    # 输出配置
    save_intermediate: bool = False     # 保存中间结果
    output_format: str = 'srt'          # 输出格式: srt, vtt, json


@dataclass
class AlignmentQualityMetrics:
    """对齐质量指标"""
    precision_score: float              # 精度分数
    boundary_accuracy: float            # 边界准确性
    dtw_alignment_score: float          # DTW对齐分数
    overall_confidence: float           # 总体置信度
    timing_variance: float              # 时间方差
    consistency_score: float            # 一致性分数
    
    @property
    def overall_quality(self) -> float:
        """计算总体质量分数"""
        scores = [
            self.precision_score,
            self.boundary_accuracy,
            self.dtw_alignment_score,
            self.overall_confidence,
            1.0 - min(1.0, self.timing_variance),  # 方差越小越好
            self.consistency_score
        ]
        return sum(scores) / len(scores)


@dataclass
class AlignmentReport:
    """对齐报告"""
    input_audio_path: str               # 输入音频路径
    input_subtitles_count: int          # 输入字幕数量
    output_subtitles_count: int         # 输出字幕数量
    processing_time: float              # 处理时间
    quality_metrics: AlignmentQualityMetrics  # 质量指标
    alignment_adjustments: int          # 调整次数
    boundaries_detected: int            # 检测到的边界数
    successful_alignments: int          # 成功对齐数
    warnings: List[str]                 # 警告信息
    metadata: Dict[str, Any]            # 元数据


class IntelligentAlignmentSystem:
    """智能对齐系统"""
    
    def __init__(self, config: Optional[IntelligentAlignmentConfig] = None):
        """
        初始化智能对齐系统
        
        Args:
            config: 系统配置
        """
        self.config = config or IntelligentAlignmentConfig()
        
        # 初始化子模块
        self.audio_extractor = AudioFeatureExtractor(self.config.audio_config)
        self.boundary_detector = SpeechBoundaryDetector(
            self.config.boundary_config, 
            self.config.audio_config
        )
        self.dtw_aligner = DTWAligner(self.config.dtw_config)
        
        # 缓存系统
        self.cache = {} if self.config.enable_caching else None
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'successful_alignments': 0,
            'average_quality': 0.0,
            'average_processing_time': 0.0
        }
        
        logger.info(f"智能对齐系统初始化完成")
    
    def align_subtitles(self, audio_path: str, 
                       subtitles: List[SubtitleEntry],
                       progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[List[SubtitleEntry], AlignmentReport]:
        """
        执行智能字幕对齐
        
        Args:
            audio_path: 音频文件路径
            subtitles: 输入字幕列表
            progress_callback: 进度回调函数
            
        Returns:
            (对齐后的字幕, 对齐报告)
        """
        start_time = time.time()
        
        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
            logger.info(f"进度 {progress:.1%}: {message}")
        
        update_progress(0.0, "开始智能对齐处理")
        
        # 检查缓存
        cache_key = self._generate_cache_key(audio_path, subtitles)
        if self.cache and cache_key in self.cache:
            logger.info("使用缓存结果")
            return self.cache[cache_key]
        
        warnings = []
        
        try:
            # 第一步：提取音频特征
            update_progress(0.1, "提取音频特征")
            audio_features = self.audio_extractor.extract_features(audio_path)
            
            if not audio_features:
                raise ValueError("音频特征提取失败")
            
            # 第二步：检测语音边界
            update_progress(0.3, "检测语音边界")
            boundaries = self.boundary_detector.detect_boundaries(audio_path)
            
            if not boundaries:
                warnings.append("未检测到明显的语音边界")
            
            # 第三步：DTW对齐
            update_progress(0.5, "执行DTW对齐")
            aligned_subtitles = self.dtw_aligner.align_audio_text(audio_features, subtitles)
            
            # 第四步：质量评估和优化
            update_progress(0.7, "质量评估和优化")
            quality_metrics = self._calculate_quality_metrics(
                audio_features, boundaries, aligned_subtitles, subtitles
            )
            
            # 迭代优化
            if (self.config.enable_iterative and 
                quality_metrics.overall_quality < self.config.quality_threshold):
                
                update_progress(0.8, "执行迭代优化")
                aligned_subtitles, quality_metrics = self._iterative_optimization(
                    audio_features, boundaries, aligned_subtitles, subtitles
                )
            
            # 第五步：结果验证
            update_progress(0.9, "验证对齐结果")
            if self.config.enable_validation:
                aligned_subtitles = self._validate_and_correct(aligned_subtitles)
            
            # 生成报告
            processing_time = time.time() - start_time
            report = AlignmentReport(
                input_audio_path=audio_path,
                input_subtitles_count=len(subtitles),
                output_subtitles_count=len(aligned_subtitles),
                processing_time=processing_time,
                quality_metrics=quality_metrics,
                alignment_adjustments=getattr(self, '_alignment_adjustments', 0),
                boundaries_detected=len(boundaries),
                successful_alignments=sum(1 for s in aligned_subtitles 
                                        if s.metadata.get('aligned', False)),
                warnings=warnings,
                metadata={
                    'audio_duration': audio_features.duration,
                    'audio_sample_rate': self.config.audio_config.sample_rate,
                    'dtw_config': asdict(self.config.dtw_config)
                }
            )
            
            # 更新统计
            self._update_stats(report)
            
            # 缓存结果
            if self.cache:
                self.cache[cache_key] = (aligned_subtitles, report)
            
            update_progress(1.0, "对齐处理完成")
            logger.info(f"智能对齐完成，质量分数: {quality_metrics.overall_quality:.3f}")
            
            return aligned_subtitles, report
            
        except Exception as e:
            logger.error(f"智能对齐失败: {e}")
            # 返回原始字幕和错误报告
            error_report = AlignmentReport(
                input_audio_path=audio_path,
                input_subtitles_count=len(subtitles),
                output_subtitles_count=len(subtitles),
                processing_time=time.time() - start_time,
                quality_metrics=AlignmentQualityMetrics(0, 0, 0, 0, 1, 0),
                alignment_adjustments=0,
                boundaries_detected=0,
                successful_alignments=0,
                warnings=[f"对齐失败: {str(e)}"],
                metadata={'error': True}
            )
            return subtitles, error_report
    
    def _generate_cache_key(self, audio_path: str, 
                           subtitles: List[SubtitleEntry]) -> str:
        """生成缓存键"""
        import hashlib
        
        # 音频文件信息
        audio_stat = os.stat(audio_path)
        audio_info = f"{audio_path}_{audio_stat.st_mtime}_{audio_stat.st_size}"
        
        # 字幕内容哈希
        subtitle_text = "".join([s.text for s in subtitles])
        subtitle_hash = hashlib.md5(subtitle_text.encode()).hexdigest()
        
        # 配置哈希
        config_str = json.dumps(asdict(self.config), sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        return f"{audio_info}_{subtitle_hash}_{config_hash}"
    
    def _calculate_quality_metrics(self, audio_features: AudioFeatures,
                                 boundaries: List[SpeechBoundary],
                                 aligned_subtitles: List[SubtitleEntry],
                                 original_subtitles: List[SubtitleEntry]) -> AlignmentQualityMetrics:
        """计算对齐质量指标"""
        
        # 精度分数：基于时间戳变化
        timing_changes = []
        for orig, aligned in zip(original_subtitles, aligned_subtitles):
            change = abs(aligned.start_time - orig.start_time)
            timing_changes.append(change)
        
        avg_change = sum(timing_changes) / len(timing_changes) if timing_changes else 0
        precision_score = max(0, 1 - avg_change / self.config.precision_target)
        
        # 边界准确性：边界检测质量
        if boundaries:
            boundary_confidences = [b.confidence for b in boundaries]
            boundary_accuracy = sum(boundary_confidences) / len(boundary_confidences)
        else:
            boundary_accuracy = 0.5
        
        # DTW对齐分数：基于对齐置信度
        dtw_confidences = [s.confidence for s in aligned_subtitles if s.confidence > 0]
        dtw_alignment_score = sum(dtw_confidences) / len(dtw_confidences) if dtw_confidences else 0
        
        # 总体置信度
        alignment_confidences = [s.metadata.get('alignment_confidence', 0.5) 
                               for s in aligned_subtitles]
        overall_confidence = sum(alignment_confidences) / len(alignment_confidences) if alignment_confidences else 0
        
        # 时间方差
        if len(timing_changes) > 1:
            import numpy as np
            timing_variance = float(np.var(timing_changes))
        else:
            timing_variance = 0.0
        
        # 一致性分数：相邻字幕时间间隔的一致性
        intervals = []
        for i in range(1, len(aligned_subtitles)):
            interval = aligned_subtitles[i].start_time - aligned_subtitles[i-1].start_time
            intervals.append(interval)
        
        if len(intervals) > 1:
            import numpy as np
            interval_std = float(np.std(intervals))
            interval_mean = float(np.mean(intervals))
            consistency_score = max(0.0, 1.0 - interval_std / interval_mean) if interval_mean > 0 else 0.0
        else:
            consistency_score = 1.0
        
        return AlignmentQualityMetrics(
            precision_score=precision_score,
            boundary_accuracy=boundary_accuracy,
            dtw_alignment_score=dtw_alignment_score,
            overall_confidence=overall_confidence,
            timing_variance=timing_variance,
            consistency_score=consistency_score
        )
    
    def _iterative_optimization(self, audio_features: AudioFeatures,
                              boundaries: List[SpeechBoundary],
                              aligned_subtitles: List[SubtitleEntry],
                              original_subtitles: List[SubtitleEntry]) -> Tuple[List[SubtitleEntry], AlignmentQualityMetrics]:
        """迭代优化对齐结果"""
        
        best_subtitles = aligned_subtitles
        best_quality = self._calculate_quality_metrics(
            audio_features, boundaries, aligned_subtitles, original_subtitles
        )
        
        self._alignment_adjustments = 0
        
        for iteration in range(self.config.max_iterations):
            logger.debug(f"迭代优化第 {iteration + 1} 轮")
            
            # 调整DTW参数
            adjusted_config = DTWConfig(
                radius=self.config.dtw_config.radius + iteration,
                distance_metric=self.config.dtw_config.distance_metric,
                normalize_features=True,
                apply_smoothing=True
            )
            
            # 重新对齐
            temp_aligner = DTWAligner(adjusted_config)
            temp_subtitles = temp_aligner.align_audio_text(audio_features, original_subtitles)
            
            # 评估质量
            temp_quality = self._calculate_quality_metrics(
                audio_features, boundaries, temp_subtitles, original_subtitles
            )
            
            # 更新最佳结果
            if temp_quality.overall_quality > best_quality.overall_quality:
                best_subtitles = temp_subtitles
                best_quality = temp_quality
                self._alignment_adjustments += 1
                logger.debug(f"优化改进，质量提升至: {best_quality.overall_quality:.3f}")
            
            # 达到目标质量则提前结束
            if best_quality.overall_quality >= self.config.quality_threshold:
                break
        
        return best_subtitles, best_quality
    
    def _validate_and_correct(self, aligned_subtitles: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """验证和修正对齐结果"""
        
        corrected = []
        
        for i, subtitle in enumerate(aligned_subtitles):
            corrected_subtitle = SubtitleEntry(
                text=subtitle.text,
                start_time=subtitle.start_time,
                end_time=subtitle.end_time,
                confidence=subtitle.confidence,
                metadata=subtitle.metadata.copy()
            )
            
            # 检查时间顺序
            if i > 0 and corrected_subtitle.start_time < corrected[i-1].start_time:
                # 修正时间顺序
                corrected_subtitle.start_time = corrected[i-1].start_time + 0.1
                corrected_subtitle.metadata['time_order_corrected'] = True
                logger.debug(f"修正字幕 {i} 的时间顺序")
            
            # 检查结束时间
            if corrected_subtitle.end_time <= corrected_subtitle.start_time:
                corrected_subtitle.end_time = corrected_subtitle.start_time + 1.0
                corrected_subtitle.metadata['end_time_corrected'] = True
            
            # 检查置信度
            if corrected_subtitle.confidence < self.config.min_confidence:
                corrected_subtitle.metadata['low_confidence'] = True
            
            corrected.append(corrected_subtitle)
        
        return corrected
    
    def _update_stats(self, report: AlignmentReport):
        """更新统计信息"""
        self.stats['total_processed'] += 1
        self.stats['successful_alignments'] += report.successful_alignments
        
        # 更新平均质量
        current_quality = report.quality_metrics.overall_quality
        total = self.stats['total_processed']
        prev_avg = self.stats['average_quality']
        self.stats['average_quality'] = (prev_avg * (total - 1) + current_quality) / total
        
        # 更新平均处理时间
        prev_time_avg = self.stats['average_processing_time']
        self.stats['average_processing_time'] = (prev_time_avg * (total - 1) + report.processing_time) / total
    
    def export_alignment_result(self, aligned_subtitles: List[SubtitleEntry],
                              output_path: str, 
                              format: Optional[str] = None) -> str:
        """
        导出对齐结果
        
        Args:
            aligned_subtitles: 对齐后的字幕
            output_path: 输出路径
            format: 输出格式
            
        Returns:
            实际输出文件路径
        """
        export_format = format or self.config.output_format
        
        if export_format.lower() == 'srt':
            return self._export_srt(aligned_subtitles, output_path)
        elif export_format.lower() == 'vtt':
            return self._export_vtt(aligned_subtitles, output_path)
        elif export_format.lower() == 'json':
            return self._export_json(aligned_subtitles, output_path)
        else:
            raise ValueError(f"不支持的输出格式: {export_format}")
    
    def _export_srt(self, subtitles: List[SubtitleEntry], output_path: str) -> str:
        """导出SRT格式"""
        srt_path = Path(output_path).with_suffix('.srt')
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(subtitles, 1):
                start_time = self._format_srt_time(subtitle.start_time)
                end_time = self._format_srt_time(subtitle.end_time)
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle.text}\n\n")
        
        return str(srt_path)
    
    def _export_vtt(self, subtitles: List[SubtitleEntry], output_path: str) -> str:
        """导出VTT格式"""
        vtt_path = Path(output_path).with_suffix('.vtt')
        
        with open(vtt_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for subtitle in subtitles:
                start_time = self._format_vtt_time(subtitle.start_time)
                end_time = self._format_vtt_time(subtitle.end_time)
                
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle.text}\n\n")
        
        return str(vtt_path)
    
    def _export_json(self, subtitles: List[SubtitleEntry], output_path: str) -> str:
        """导出JSON格式"""
        json_path = Path(output_path).with_suffix('.json')
        
        subtitle_data = []
        for subtitle in subtitles:
            subtitle_data.append({
                'text': subtitle.text,
                'start_time': subtitle.start_time,
                'end_time': subtitle.end_time,
                'confidence': subtitle.confidence,
                'metadata': subtitle.metadata
            })
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
        
        return str(json_path)
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化SRT时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """格式化VTT时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            **self.stats,
            'cache_size': len(self.cache) if self.cache else 0,
            'config': asdict(self.config)
        }
    
    def clear_cache(self):
        """清空缓存"""
        if self.cache:
            self.cache.clear()
            logger.info("缓存已清空")


# 便捷函数
def intelligent_align_subtitles(audio_path: str,
                              subtitles: List[SubtitleEntry],
                              config: Optional[IntelligentAlignmentConfig] = None,
                              progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[List[SubtitleEntry], AlignmentReport]:
    """
    智能字幕对齐便捷函数
    
    Args:
        audio_path: 音频文件路径
        subtitles: 字幕列表
        config: 配置
        progress_callback: 进度回调
        
    Returns:
        (对齐后的字幕, 对齐报告)
    """
    system = IntelligentAlignmentSystem(config)
    return system.align_subtitles(audio_path, subtitles, progress_callback)


if __name__ == "__main__":
    # 测试智能对齐系统
    print("🎯 智能对齐系统测试")
    print("=" * 60)
    
    # 创建配置
    config = IntelligentAlignmentConfig()
    
    print(f"系统配置:")
    print(f"  精度目标: {config.precision_target}秒")
    print(f"  最小置信度: {config.min_confidence}")
    print(f"  启用迭代优化: {config.enable_iterative}")
    print(f"  质量阈值: {config.quality_threshold}")
    
    # 创建系统
    system = IntelligentAlignmentSystem(config)
    
    print(f"\n系统信息:")
    print(f"  音频特征提取器: 已初始化")
    print(f"  语音边界检测器: 已初始化")
    print(f"  DTW对齐器: 已初始化")
    print(f"  缓存系统: {'启用' if system.cache else '禁用'}")
    
    print(f"\n使用示例:")
    print(f"  aligned_subs, report = system.align_subtitles(audio_path, subtitles)")
    print(f"  print(f'质量分数: {{report.quality_metrics.overall_quality:.3f}}')")
    print(f"  system.export_alignment_result(aligned_subs, 'output.srt')")
    print(f"  stats = system.get_system_stats()")