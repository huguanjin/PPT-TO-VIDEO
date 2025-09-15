"""
对齐质量验证系统
Phase 3: 智能对齐系统的质量控制组件
实现时间精度检测、一致性验证、异常值识别等质量控制机制
"""
import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass
import logging
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

from .audio_feature_extractor import AudioFeatures
from .speech_boundary_detector import SpeechBoundary, SpeechSegment
from .dtw_aligner import SubtitleEntry, AlignmentResult
from .timestamp_optimizer import OptimizationResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """验证配置"""
    # 精度验证
    target_precision: float = 0.1          # 目标精度(秒)
    precision_tolerance: float = 0.05      # 精度容忍度
    
    # 一致性验证
    max_interval_variance: float = 2.0     # 最大间隔方差
    min_consistency_score: float = 0.7     # 最小一致性分数
    
    # 异常值检测
    outlier_threshold: float = 2.5         # 异常值阈值(标准差倍数)
    max_outlier_ratio: float = 0.1         # 最大异常值比例
    
    # 边界验证
    boundary_tolerance: float = 0.2        # 边界容忍度(秒)
    min_boundary_confidence: float = 0.6   # 最小边界置信度
    
    # 音频对齐验证
    audio_sync_threshold: float = 0.15     # 音频同步阈值
    energy_correlation_min: float = 0.5    # 最小能量相关性
    
    # 质量评分权重
    precision_weight: float = 0.3          # 精度权重
    consistency_weight: float = 0.25       # 一致性权重
    boundary_weight: float = 0.2           # 边界权重
    audio_sync_weight: float = 0.15        # 音频同步权重
    confidence_weight: float = 0.1         # 置信度权重


@dataclass
class ValidationMetrics:
    """验证指标"""
    # 精度指标
    mean_precision_error: float            # 平均精度误差
    precision_score: float                 # 精度分数
    
    # 一致性指标
    interval_variance: float               # 间隔方差
    consistency_score: float               # 一致性分数
    
    # 异常值指标
    outlier_count: int                     # 异常值数量
    outlier_ratio: float                   # 异常值比例
    outlier_indices: List[int]             # 异常值索引
    
    # 边界验证指标
    boundary_alignment_score: float        # 边界对齐分数
    boundary_coverage: float               # 边界覆盖度
    
    # 音频同步指标
    audio_sync_score: float                # 音频同步分数
    energy_correlation: float              # 能量相关性
    
    # 总体质量
    overall_quality_score: float           # 总体质量分数
    validation_passed: bool                # 是否通过验证
    
    # 详细信息
    detailed_scores: Dict[str, float]      # 详细分数
    recommendations: List[str]             # 改进建议


class AlignmentValidator:
    """对齐质量验证器"""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        初始化对齐质量验证器
        
        Args:
            config: 验证配置
        """
        self.config = config or ValidationConfig()
        
        # 统计信息
        self.stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'average_quality': 0.0,
            'common_issues': {}
        }
        
        logger.info("对齐质量验证器初始化完成")
    
    def validate_alignment(self, 
                         aligned_subtitles: List[SubtitleEntry],
                         original_subtitles: Optional[List[SubtitleEntry]] = None,
                         audio_features: Optional[AudioFeatures] = None,
                         boundaries: Optional[List[SpeechBoundary]] = None,
                         alignment_result: Optional[AlignmentResult] = None) -> ValidationMetrics:
        """
        验证对齐质量的主接口
        
        Args:
            aligned_subtitles: 对齐后的字幕
            original_subtitles: 原始字幕(可选)
            audio_features: 音频特征(可选)
            boundaries: 语音边界(可选)
            alignment_result: 对齐结果(可选)
            
        Returns:
            验证指标
        """
        logger.info(f"开始对齐质量验证，字幕数量: {len(aligned_subtitles)}")
        
        # 精度验证
        precision_error, precision_score = self._validate_precision(
            aligned_subtitles, original_subtitles
        )
        
        # 一致性验证
        interval_variance, consistency_score = self._validate_consistency(aligned_subtitles)
        
        # 异常值检测
        outlier_count, outlier_ratio, outlier_indices = self._detect_outliers(aligned_subtitles)
        
        # 边界验证
        boundary_score, boundary_coverage = self._validate_boundaries(
            aligned_subtitles, boundaries
        )
        
        # 音频同步验证
        audio_sync_score, energy_correlation = self._validate_audio_sync(
            aligned_subtitles, audio_features
        )
        
        # 计算总体质量分数
        detailed_scores = {
            'precision': precision_score,
            'consistency': consistency_score,
            'boundary_alignment': boundary_score,
            'audio_sync': audio_sync_score,
            'outlier_penalty': max(0, 1 - outlier_ratio * 2)  # 异常值惩罚
        }
        
        overall_quality = self._calculate_overall_quality(detailed_scores)
        
        # 生成改进建议
        recommendations = self._generate_recommendations(
            precision_error, consistency_score, outlier_ratio, 
            boundary_score, audio_sync_score
        )
        
        # 判断是否通过验证
        validation_passed = self._check_validation_passed(
            precision_score, consistency_score, outlier_ratio,
            boundary_score, audio_sync_score
        )
        
        # 创建验证指标
        metrics = ValidationMetrics(
            mean_precision_error=precision_error,
            precision_score=precision_score,
            interval_variance=interval_variance,
            consistency_score=consistency_score,
            outlier_count=outlier_count,
            outlier_ratio=outlier_ratio,
            outlier_indices=outlier_indices,
            boundary_alignment_score=boundary_score,
            boundary_coverage=boundary_coverage,
            audio_sync_score=audio_sync_score,
            energy_correlation=energy_correlation,
            overall_quality_score=overall_quality,
            validation_passed=validation_passed,
            detailed_scores=detailed_scores,
            recommendations=recommendations
        )
        
        # 更新统计
        self._update_stats(metrics)
        
        logger.info(f"对齐质量验证完成，总体质量: {overall_quality:.3f}")
        return metrics
    
    def _validate_precision(self, aligned_subtitles: List[SubtitleEntry],
                          original_subtitles: Optional[List[SubtitleEntry]] = None) -> Tuple[float, float]:
        """
        验证时间精度
        
        Args:
            aligned_subtitles: 对齐后的字幕
            original_subtitles: 原始字幕
            
        Returns:
            (平均精度误差, 精度分数)
        """
        if not original_subtitles or len(aligned_subtitles) != len(original_subtitles):
            # 如果没有原始字幕，使用相对精度评估
            return self._estimate_relative_precision(aligned_subtitles)
        
        # 计算时间戳偏差
        deviations = []
        for aligned, original in zip(aligned_subtitles, original_subtitles):
            deviation = abs(aligned.start_time - original.start_time)
            deviations.append(deviation)
        
        mean_error = float(np.mean(deviations))
        
        # 计算精度分数 (误差越小分数越高)
        precision_score = max(0.0, 1.0 - mean_error / self.config.target_precision)
        
        return mean_error, precision_score
    
    def _estimate_relative_precision(self, subtitles: List[SubtitleEntry]) -> Tuple[float, float]:
        """估算相对精度"""
        if len(subtitles) < 2:
            return 0.0, 1.0
        
        # 基于时间间隔的一致性来估算精度
        intervals = []
        for i in range(1, len(subtitles)):
            interval = subtitles[i].start_time - subtitles[i-1].start_time
            intervals.append(interval)
        
        if not intervals:
            return 0.0, 1.0
        
        # 计算间隔的标准差作为精度误差的估计
        interval_std = float(np.std(intervals))
        estimated_error = interval_std / 2  # 经验估计
        
        precision_score = max(0.0, 1.0 - estimated_error / self.config.target_precision)
        
        return estimated_error, precision_score
    
    def _validate_consistency(self, subtitles: List[SubtitleEntry]) -> Tuple[float, float]:
        """
        验证时间一致性
        
        Args:
            subtitles: 字幕列表
            
        Returns:
            (间隔方差, 一致性分数)
        """
        if len(subtitles) < 2:
            return 0.0, 1.0
        
        # 计算时间间隔
        intervals = []
        for i in range(1, len(subtitles)):
            interval = subtitles[i].start_time - subtitles[i-1].start_time
            intervals.append(interval)
        
        if not intervals:
            return 0.0, 1.0
        
        # 计算间隔方差
        interval_variance = np.var(intervals)
        
        # 计算一致性分数
        # 使用变异系数 (CV = std/mean) 来评估一致性
        if np.mean(intervals) > 0:
            cv = float(np.std(intervals) / np.mean(intervals))
            consistency_score = max(0.0, 1.0 - cv)
        else:
            consistency_score = 0.5
        
        return float(interval_variance), consistency_score
    
    def _detect_outliers(self, subtitles: List[SubtitleEntry]) -> Tuple[int, float, List[int]]:
        """
        检测异常值
        
        Args:
            subtitles: 字幕列表
            
        Returns:
            (异常值数量, 异常值比例, 异常值索引列表)
        """
        if len(subtitles) < 3:
            return 0, 0.0, []
        
        # 提取时间戳
        timestamps = [s.start_time for s in subtitles]
        
        # 计算时间间隔
        intervals = np.diff(timestamps)
        
        if len(intervals) < 2:
            return 0, 0.0, []
        
        # 使用Z-score检测异常值
        try:
            # 转换为标准Python列表进行计算
            intervals_list = [float(x) for x in intervals]
            
            # 计算均值和标准差
            mean_val = sum(intervals_list) / len(intervals_list)
            variance = sum((x - mean_val) ** 2 for x in intervals_list) / len(intervals_list)
            std_dev = variance ** 0.5
            
            # 计算Z-scores
            z_scores = [abs((x - mean_val) / std_dev) if std_dev > 0 else 0 for x in intervals_list]
            
            # 找到异常值
            outlier_indices = [i for i, z in enumerate(z_scores) if z > self.config.outlier_threshold]
            outlier_count = len(outlier_indices)
            outlier_ratio = outlier_count / len(intervals) if len(intervals) > 0 else 0
            
        except Exception:
            # 如果计算失败，返回空结果
            return 0, 0.0, []
        
        return outlier_count, float(outlier_ratio), outlier_indices
    
    def _validate_boundaries(self, subtitles: List[SubtitleEntry],
                           boundaries: Optional[List[SpeechBoundary]] = None) -> Tuple[float, float]:
        """
        验证边界对齐
        
        Args:
            subtitles: 字幕列表
            boundaries: 语音边界
            
        Returns:
            (边界对齐分数, 边界覆盖度)
        """
        if not boundaries:
            return 0.5, 0.5  # 无边界信息，返回中性分数
        
        subtitle_times = [s.start_time for s in subtitles]
        boundary_times = [b.time for b in boundaries]
        boundary_confidences = [b.confidence for b in boundaries]
        
        # 计算每个字幕时间戳与最近边界的距离
        alignment_scores = []
        covered_boundaries = 0
        
        for subtitle_time in subtitle_times:
            # 找到最近的边界
            distances = [abs(subtitle_time - bt) for bt in boundary_times]
            
            if distances:
                min_distance = min(distances)
                closest_idx = distances.index(min_distance)
                closest_confidence = boundary_confidences[closest_idx]
                
                # 如果距离在容忍范围内，计算对齐分数
                if min_distance <= self.config.boundary_tolerance:
                    # 距离越近，置信度越高，分数越高
                    distance_factor = 1 - min_distance / self.config.boundary_tolerance
                    score = distance_factor * closest_confidence
                    alignment_scores.append(score)
                    covered_boundaries += 1
                else:
                    alignment_scores.append(0)
            else:
                alignment_scores.append(0)
        
        # 计算平均对齐分数
        boundary_score = float(np.mean(alignment_scores)) if alignment_scores else 0.0
        
        # 计算边界覆盖度
        boundary_coverage = float(covered_boundaries / len(subtitle_times)) if subtitle_times else 0.0
        
        return boundary_score, boundary_coverage
    
    def _validate_audio_sync(self, subtitles: List[SubtitleEntry],
                           audio_features: Optional[AudioFeatures] = None) -> Tuple[float, float]:
        """
        验证音频同步
        
        Args:
            subtitles: 字幕列表
            audio_features: 音频特征
            
        Returns:
            (音频同步分数, 能量相关性)
        """
        if not audio_features:
            return 0.5, 0.5  # 无音频特征，返回中性分数
        
        subtitle_times = [s.start_time for s in subtitles]
        
        # 提取字幕时间点对应的音频能量
        subtitle_energies = []
        for time in subtitle_times:
            # 找到最近的时间帧 - 避免numpy类型问题
            try:
                # 转换为标准Python类型进行计算
                time_diffs = [abs(float(t) - float(time)) for t in audio_features.time_frames]
                frame_idx = time_diffs.index(min(time_diffs))
                if frame_idx < len(audio_features.rms_energy):
                    energy = audio_features.rms_energy[frame_idx]
                    subtitle_energies.append(energy)
            except Exception:
                # 如果计算失败，跳过这个时间点
                continue
        
        if len(subtitle_energies) < 2:
            return 0.5, 0.5
        
        # 计算能量相关性
        # 字幕开始时间应该对应相对较高的音频能量
        # 计算能量百分位 - 手动计算避免scipy类型问题
        energy_percentiles = []
        for energy in subtitle_energies:
            try:
                # 手动计算百分位
                rms_list = [float(x) for x in audio_features.rms_energy]
                energy_val = float(energy)
                
                # 计算有多少值小于当前能量值
                count_below = sum(1 for x in rms_list if x < energy_val)
                percentile = (count_below / len(rms_list)) * 100
                energy_percentiles.append(percentile)
            except Exception:
                energy_percentiles.append(50.0)  # 默认中位数
        
        # 期望字幕开始点的能量百分位较高
        expected_percentile = 70  # 期望在70%分位以上
        sync_scores = []
        for percentile in energy_percentiles:
            if percentile >= expected_percentile:
                score = 1.0
            elif percentile >= 50:
                score = (percentile - 50) / (expected_percentile - 50)
            else:
                score = 0.0
            sync_scores.append(score)
        
        # 计算均值 - 避免numpy类型问题
        audio_sync_score = sum(sync_scores) / len(sync_scores) if sync_scores else 0.5
        
        # 计算能量相关性
        if len(subtitle_energies) > 2:
            # 计算字幕间隔与能量变化的相关性 - 使用标准Python
            subtitle_intervals = [subtitle_times[i+1] - subtitle_times[i] for i in range(len(subtitle_times)-1)]
            energy_changes = [abs(subtitle_energies[i+1] - subtitle_energies[i]) for i in range(len(subtitle_energies)-1)]
            
            if len(subtitle_intervals) > 1 and len(energy_changes) > 1:
                try:
                    # 转换为标准Python列表
                    intervals_list = [float(x) for x in subtitle_intervals]
                    changes_list = [float(x) for x in energy_changes]
                    
                    # 手动计算皮尔逊相关系数
                    if len(intervals_list) > 1 and len(changes_list) > 1:
                        mean_x = sum(intervals_list) / len(intervals_list)
                        mean_y = sum(changes_list) / len(changes_list)
                        
                        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(intervals_list, changes_list))
                        sum_sq_x = sum((x - mean_x) ** 2 for x in intervals_list)
                        sum_sq_y = sum((y - mean_y) ** 2 for y in changes_list)
                        
                        denominator = (sum_sq_x * sum_sq_y) ** 0.5
                        
                        if denominator > 0:
                            correlation = numerator / denominator
                            energy_correlation = abs(correlation)
                        else:
                            energy_correlation = 0.0
                    else:
                        energy_correlation = 0.0
                except Exception:
                    energy_correlation = 0.0
            else:
                energy_correlation = 0.0
        else:
            energy_correlation = 0.0
        
        return float(audio_sync_score), energy_correlation
    
    def _calculate_overall_quality(self, detailed_scores: Dict[str, float]) -> float:
        """计算总体质量分数"""
        weighted_score = (
            detailed_scores['precision'] * self.config.precision_weight +
            detailed_scores['consistency'] * self.config.consistency_weight +
            detailed_scores['boundary_alignment'] * self.config.boundary_weight +
            detailed_scores['audio_sync'] * self.config.audio_sync_weight +
            detailed_scores['outlier_penalty'] * self.config.confidence_weight
        )
        
        return weighted_score
    
    def _generate_recommendations(self, precision_error: float,
                                consistency_score: float,
                                outlier_ratio: float,
                                boundary_score: float,
                                audio_sync_score: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 精度建议
        if precision_error > self.config.target_precision:
            recommendations.append(
                f"时间精度不足 ({precision_error:.3f}s > {self.config.target_precision}s)，"
                "建议调整DTW参数或增加音频特征权重"
            )
        
        # 一致性建议
        if consistency_score < self.config.min_consistency_score:
            recommendations.append(
                f"时间一致性较低 ({consistency_score:.3f})，"
                "建议启用时间轴平滑处理或调整间距优化参数"
            )
        
        # 异常值建议
        if outlier_ratio > self.config.max_outlier_ratio:
            recommendations.append(
                f"异常值比例过高 ({outlier_ratio:.1%})，"
                "建议检查输入数据质量或调整异常值检测阈值"
            )
        
        # 边界对齐建议
        if boundary_score < 0.6:
            recommendations.append(
                f"边界对齐质量较低 ({boundary_score:.3f})，"
                "建议调整边界检测参数或增加边界对齐权重"
            )
        
        # 音频同步建议
        if audio_sync_score < 0.6:
            recommendations.append(
                f"音频同步质量较低 ({audio_sync_score:.3f})，"
                "建议检查音频质量或调整音频对齐算法参数"
            )
        
        if not recommendations:
            recommendations.append("对齐质量良好，无需特殊调整")
        
        return recommendations
    
    def _check_validation_passed(self, precision_score: float,
                               consistency_score: float,
                               outlier_ratio: float,
                               boundary_score: float,
                               audio_sync_score: float) -> bool:
        """检查是否通过验证"""
        # 所有关键指标都需要达到最低标准
        checks = [
            precision_score >= 0.7,
            consistency_score >= self.config.min_consistency_score,
            outlier_ratio <= self.config.max_outlier_ratio,
            boundary_score >= 0.5,
            audio_sync_score >= 0.5
        ]
        
        # 至少需要80%的检查通过
        passed_ratio = sum(checks) / len(checks)
        return passed_ratio >= 0.8
    
    def _update_stats(self, metrics: ValidationMetrics):
        """更新统计信息"""
        self.stats['total_validations'] += 1
        
        if metrics.validation_passed:
            self.stats['passed_validations'] += 1
        
        # 更新平均质量
        total = self.stats['total_validations']
        prev_avg = self.stats['average_quality']
        current_quality = metrics.overall_quality_score
        self.stats['average_quality'] = (prev_avg * (total - 1) + current_quality) / total
        
        # 更新常见问题统计
        for recommendation in metrics.recommendations:
            issue_type = recommendation.split('，')[0]  # 提取问题类型
            self.stats['common_issues'][issue_type] = self.stats['common_issues'].get(issue_type, 0) + 1
    
    def validate_optimization_result(self, optimization_result: OptimizationResult,
                                   original_subtitles: List[SubtitleEntry]) -> ValidationMetrics:
        """
        验证优化结果
        
        Args:
            optimization_result: 优化结果
            original_subtitles: 原始字幕
            
        Returns:
            验证指标
        """
        # 创建优化后的字幕对象
        optimized_subtitles = []
        for i, (subtitle, new_time) in enumerate(zip(original_subtitles, optimization_result.optimized_timestamps)):
            optimized_subtitle = SubtitleEntry(
                text=subtitle.text,
                start_time=new_time,
                end_time=subtitle.end_time + optimization_result.adjustments[i],
                confidence=optimization_result.confidence_scores[i],
                metadata={'optimized': True}
            )
            optimized_subtitles.append(optimized_subtitle)
        
        return self.validate_alignment(optimized_subtitles, original_subtitles)
    
    def batch_validate(self, alignment_batches: List[List[SubtitleEntry]],
                      progress_callback: Optional[Callable[[float], None]] = None) -> List[ValidationMetrics]:
        """
        批量验证对齐结果
        
        Args:
            alignment_batches: 对齐结果批次
            progress_callback: 进度回调
            
        Returns:
            验证指标列表
        """
        results = []
        total_batches = len(alignment_batches)
        
        for i, batch in enumerate(alignment_batches):
            metrics = self.validate_alignment(batch)
            results.append(metrics)
            
            if progress_callback:
                progress = (i + 1) / total_batches
                progress_callback(progress)
        
        return results
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        pass_rate = (self.stats['passed_validations'] / 
                    self.stats['total_validations']) if self.stats['total_validations'] > 0 else 0
        
        return {
            **self.stats,
            'pass_rate': pass_rate,
            'config': {
                'target_precision': self.config.target_precision,
                'min_consistency_score': self.config.min_consistency_score,
                'max_outlier_ratio': self.config.max_outlier_ratio
            }
        }


# 便捷函数
def validate_subtitle_alignment(aligned_subtitles: List[SubtitleEntry],
                              original_subtitles: Optional[List[SubtitleEntry]] = None,
                              audio_features: Optional[AudioFeatures] = None,
                              boundaries: Optional[List[SpeechBoundary]] = None,
                              config: Optional[ValidationConfig] = None) -> ValidationMetrics:
    """
    验证字幕对齐质量的便捷函数
    
    Args:
        aligned_subtitles: 对齐后的字幕
        original_subtitles: 原始字幕
        audio_features: 音频特征
        boundaries: 语音边界
        config: 验证配置
        
    Returns:
        验证指标
    """
    validator = AlignmentValidator(config)
    return validator.validate_alignment(
        aligned_subtitles, original_subtitles, 
        audio_features, boundaries
    )


if __name__ == "__main__":
    # 测试对齐质量验证器
    print("🎯 对齐质量验证器测试")
    print("=" * 60)
    
    # 创建配置
    config = ValidationConfig()
    
    print(f"验证配置:")
    print(f"  目标精度: {config.target_precision}s")
    print(f"  最小一致性分数: {config.min_consistency_score}")
    print(f"  异常值阈值: {config.outlier_threshold}")
    print(f"  最大异常值比例: {config.max_outlier_ratio}")
    
    # 创建验证器
    validator = AlignmentValidator(config)
    
    print(f"\n验证器信息:")
    print(f"  精度权重: {config.precision_weight}")
    print(f"  一致性权重: {config.consistency_weight}")
    print(f"  边界权重: {config.boundary_weight}")
    print(f"  音频同步权重: {config.audio_sync_weight}")
    
    # 创建测试字幕
    test_subtitles = [
        SubtitleEntry("第一句", 1.0, 3.0),
        SubtitleEntry("第二句", 3.1, 5.0),
        SubtitleEntry("第三句", 5.2, 7.0),
        SubtitleEntry("第四句", 7.1, 9.0),
    ]
    
    print(f"\n测试数据:")
    for i, sub in enumerate(test_subtitles):
        print(f"  字幕{i+1}: {sub.text} ({sub.start_time}s-{sub.end_time}s)")
    
    # 执行验证
    metrics = validator.validate_alignment(test_subtitles)
    
    print(f"\n验证结果:")
    print(f"  总体质量分数: {metrics.overall_quality_score:.3f}")
    print(f"  验证通过: {metrics.validation_passed}")
    print(f"  精度分数: {metrics.precision_score:.3f}")
    print(f"  一致性分数: {metrics.consistency_score:.3f}")
    print(f"  异常值比例: {metrics.outlier_ratio:.1%}")
    
    if metrics.recommendations:
        print(f"\n改进建议:")
        for i, rec in enumerate(metrics.recommendations):
            print(f"  {i+1}. {rec}")
    
    print(f"\n✅ 对齐质量验证器测试完成!")