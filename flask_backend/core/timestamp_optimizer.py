"""
时间戳优化器核心模块
Phase 3: 智能对齐系统的时间戳精细化调整组件
实现基于音频内容的微调、相邻字幕间距优化、时间轴平滑处理等功能
"""
import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass
import logging
from scipy import signal
from scipy.ndimage import gaussian_filter1d
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

from .audio_feature_extractor import AudioFeatures, AudioConfig
from .speech_boundary_detector import SpeechBoundary, SpeechSegment
from .dtw_aligner import SubtitleEntry, AlignmentResult

logger = logging.getLogger(__name__)


@dataclass
class OptimizerConfig:
    """时间戳优化器配置"""
    # 微调参数
    fine_tune_window: float = 0.2       # 微调窗口大小(秒)
    min_adjustment: float = 0.01        # 最小调整步长(秒)
    max_adjustment: float = 0.5         # 最大调整幅度(秒)
    
    # 间距优化
    min_subtitle_gap: float = 0.1       # 最小字幕间距(秒)
    max_subtitle_gap: float = 3.0       # 最大字幕间距(秒)
    ideal_gap_ratio: float = 0.15       # 理想间距比例
    
    # 平滑处理
    enable_smoothing: bool = True       # 启用时间轴平滑
    smoothing_sigma: float = 1.0        # 高斯平滑参数
    smoothing_window: int = 5           # 平滑窗口大小
    
    # 聚类优化
    enable_clustering: bool = True      # 启用时间戳聚类
    cluster_eps: float = 0.1           # DBSCAN聚类距离
    cluster_min_samples: int = 2       # 聚类最小样本数
    
    # 音频对齐
    audio_alignment_weight: float = 0.6 # 音频对齐权重
    boundary_alignment_weight: float = 0.4  # 边界对齐权重
    
    # 质量控制
    confidence_threshold: float = 0.7   # 置信度阈值
    max_iterations: int = 5             # 最大优化迭代次数
    convergence_threshold: float = 0.01 # 收敛阈值


@dataclass
class OptimizationResult:
    """优化结果"""
    original_timestamps: List[float]    # 原始时间戳
    optimized_timestamps: List[float]   # 优化后时间戳
    adjustments: List[float]            # 调整量
    quality_scores: List[float]         # 质量分数
    confidence_scores: List[float]      # 置信度分数
    optimization_steps: int             # 优化步数
    convergence_achieved: bool          # 是否收敛
    metadata: Dict[str, Any]            # 元数据


class TimestampOptimizer:
    """时间戳优化器"""
    
    def __init__(self, config: Optional[OptimizerConfig] = None):
        """
        初始化时间戳优化器
        
        Args:
            config: 优化器配置
        """
        self.config = config or OptimizerConfig()
        
        # 统计信息
        self.stats = {
            'total_optimizations': 0,
            'average_improvement': 0.0,
            'convergence_rate': 0.0
        }
        
        logger.info("时间戳优化器初始化完成")
    
    def optimize_timestamps(self, subtitles: List[SubtitleEntry],
                          audio_features: Optional[AudioFeatures] = None,
                          boundaries: Optional[List[SpeechBoundary]] = None) -> Tuple[List[SubtitleEntry], OptimizationResult]:
        """
        优化字幕时间戳的主接口
        
        Args:
            subtitles: 输入字幕列表
            audio_features: 音频特征(可选)
            boundaries: 语音边界(可选)
            
        Returns:
            (优化后的字幕, 优化结果)
        """
        logger.info(f"开始时间戳优化，字幕数量: {len(subtitles)}")
        
        if not subtitles:
            return subtitles, OptimizationResult([], [], [], [], [], 0, True, {})
        
        # 提取原始时间戳
        original_timestamps = [s.start_time for s in subtitles]
        current_timestamps = original_timestamps.copy()
        
        optimization_steps = 0
        convergence_achieved = False
        
        for iteration in range(self.config.max_iterations):
            prev_timestamps = current_timestamps.copy()
            
            # 第一步：音频对齐优化
            if audio_features is not None:
                current_timestamps = self._audio_alignment_optimization(
                    current_timestamps, audio_features, subtitles
                )
            
            # 第二步：边界对齐优化  
            if boundaries is not None:
                current_timestamps = self._boundary_alignment_optimization(
                    current_timestamps, boundaries, subtitles
                )
            
            # 第三步：间距优化
            current_timestamps = self._gap_optimization(current_timestamps, subtitles)
            
            # 第四步：聚类优化
            if self.config.enable_clustering:
                current_timestamps = self._clustering_optimization(current_timestamps)
            
            # 第五步：平滑处理
            if self.config.enable_smoothing:
                current_timestamps = self._smoothing_optimization(current_timestamps)
            
            optimization_steps += 1
            
            # 检查收敛
            max_change = max(abs(curr - prev) for curr, prev in zip(current_timestamps, prev_timestamps))
            if max_change < self.config.convergence_threshold:
                convergence_achieved = True
                break
            
            logger.debug(f"优化迭代 {iteration + 1}: 最大变化 {max_change:.4f}s")
        
        # 计算调整量和质量分数
        adjustments = [curr - orig for curr, orig in zip(current_timestamps, original_timestamps)]
        quality_scores = self._calculate_quality_scores(current_timestamps, subtitles, audio_features)
        confidence_scores = self._calculate_confidence_scores(current_timestamps, subtitles, boundaries)
        
        # 创建优化后的字幕
        optimized_subtitles = []
        for i, subtitle in enumerate(subtitles):
            optimized_subtitle = SubtitleEntry(
                text=subtitle.text,
                start_time=current_timestamps[i],
                end_time=subtitle.end_time + adjustments[i],  # 同样调整结束时间
                confidence=confidence_scores[i],
                metadata={
                    **subtitle.metadata,
                    'optimized': True,
                    'adjustment': adjustments[i],
                    'quality_score': quality_scores[i],
                    'optimization_steps': optimization_steps
                }
            )
            optimized_subtitles.append(optimized_subtitle)
        
        # 创建优化结果
        result = OptimizationResult(
            original_timestamps=original_timestamps,
            optimized_timestamps=current_timestamps,
            adjustments=adjustments,
            quality_scores=quality_scores,
            confidence_scores=confidence_scores,
            optimization_steps=optimization_steps,
            convergence_achieved=convergence_achieved,
            metadata={
                'avg_adjustment': np.mean(np.abs(adjustments)),
                'max_adjustment': np.max(np.abs(adjustments)),
                'improvement_score': np.mean(quality_scores)
            }
        )
        
        # 更新统计
        self._update_stats(result)
        
        logger.info(f"时间戳优化完成，步数: {optimization_steps}, 收敛: {convergence_achieved}")
        return optimized_subtitles, result
    
    def _audio_alignment_optimization(self, timestamps: List[float],
                                    audio_features: AudioFeatures,
                                    subtitles: List[SubtitleEntry]) -> List[float]:
        """
        基于音频特征的对齐优化
        
        Args:
            timestamps: 当前时间戳
            audio_features: 音频特征
            subtitles: 字幕列表
            
        Returns:
            优化后的时间戳
        """
        optimized = timestamps.copy()
        
        for i, (timestamp, subtitle) in enumerate(zip(timestamps, subtitles)):
            # 在微调窗口内寻找最佳对齐点
            window_start = max(0, timestamp - self.config.fine_tune_window / 2)
            window_end = min(audio_features.duration, timestamp + self.config.fine_tune_window / 2)
            
            # 找到时间窗口对应的帧索引
            frame_indices = np.where(
                (audio_features.time_frames >= window_start) & 
                (audio_features.time_frames <= window_end)
            )[0]
            
            if len(frame_indices) == 0:
                continue
            
            # 寻找能量变化最大的点作为对齐候选
            window_energy = audio_features.rms_energy[frame_indices]
            window_times = audio_features.time_frames[frame_indices]
            
            # 计算能量梯度
            energy_gradient = np.gradient(window_energy)
            
            # 寻找梯度最大的点(能量上升最快)
            best_idx = np.argmax(np.abs(energy_gradient))
            best_time = window_times[best_idx]
            
            # 应用权重和约束
            adjustment = (best_time - timestamp) * self.config.audio_alignment_weight
            adjustment = np.clip(adjustment, -self.config.max_adjustment, self.config.max_adjustment)
            
            optimized[i] = timestamp + adjustment
        
        return optimized
    
    def _boundary_alignment_optimization(self, timestamps: List[float],
                                       boundaries: List[SpeechBoundary],
                                       subtitles: List[SubtitleEntry]) -> List[float]:
        """
        基于语音边界的对齐优化
        
        Args:
            timestamps: 当前时间戳
            boundaries: 语音边界
            subtitles: 字幕列表
            
        Returns:
            优化后的时间戳
        """
        optimized = timestamps.copy()
        boundary_times = [b.time for b in boundaries]
        boundary_confidences = [b.confidence for b in boundaries]
        
        for i, timestamp in enumerate(timestamps):
            # 寻找最近的高置信度边界
            distances = [abs(bt - timestamp) for bt in boundary_times]
            
            if not distances:
                continue
            
            # 找到距离最近且置信度较高的边界
            min_distance = min(distances)
            if min_distance <= self.config.fine_tune_window:
                closest_idx = distances.index(min_distance)
                boundary_confidence = boundary_confidences[closest_idx]
                
                # 只有当边界置信度足够高时才进行调整
                if boundary_confidence >= self.config.confidence_threshold:
                    best_boundary_time = boundary_times[closest_idx]
                    
                    # 计算调整量
                    adjustment = (best_boundary_time - timestamp) * self.config.boundary_alignment_weight
                    adjustment *= boundary_confidence  # 根据置信度加权
                    adjustment = np.clip(adjustment, -self.config.max_adjustment, self.config.max_adjustment)
                    
                    optimized[i] = timestamp + adjustment
        
        return optimized
    
    def _gap_optimization(self, timestamps: List[float], 
                         subtitles: List[SubtitleEntry]) -> List[float]:
        """
        字幕间距优化
        
        Args:
            timestamps: 当前时间戳
            subtitles: 字幕列表
            
        Returns:
            优化后的时间戳
        """
        if len(timestamps) < 2:
            return timestamps
        
        optimized = timestamps.copy()
        
        for i in range(1, len(timestamps)):
            current_gap = timestamps[i] - timestamps[i-1]
            
            # 计算理想间距(基于字幕长度)
            prev_text_length = len(subtitles[i-1].text)
            curr_text_length = len(subtitles[i].text)
            ideal_gap = (prev_text_length + curr_text_length) * self.config.ideal_gap_ratio
            ideal_gap = np.clip(ideal_gap, self.config.min_subtitle_gap, self.config.max_subtitle_gap)
            
            # 如果当前间距偏离理想间距太多，进行调整
            if current_gap < self.config.min_subtitle_gap:
                # 间距太小，向后推
                adjustment = self.config.min_subtitle_gap - current_gap
                optimized[i] = timestamps[i] + adjustment
            elif current_gap > self.config.max_subtitle_gap:
                # 间距太大，向前拉
                adjustment = current_gap - ideal_gap
                optimized[i] = timestamps[i] - adjustment * 0.5  # 温和调整
            
        return optimized
    
    def _clustering_optimization(self, timestamps: List[float]) -> List[float]:
        """
        基于聚类的时间戳优化
        
        Args:
            timestamps: 当前时间戳
            
        Returns:
            优化后的时间戳
        """
        if len(timestamps) < 3:
            return timestamps
        
        # 转换为二维数组用于聚类
        timestamp_array = np.array(timestamps).reshape(-1, 1)
        
        # 使用DBSCAN进行聚类
        clustering = DBSCAN(
            eps=self.config.cluster_eps,
            min_samples=self.config.cluster_min_samples
        ).fit(timestamp_array)
        
        labels = clustering.labels_
        optimized = timestamps.copy()
        
        # 对每个簇进行优化
        for cluster_id in set(labels):
            if cluster_id == -1:  # 噪声点
                continue
            
            cluster_indices = np.where(labels == cluster_id)[0]
            if len(cluster_indices) < 2:
                continue
            
            cluster_timestamps = [timestamps[i] for i in cluster_indices]
            
            # 计算簇内时间戳的平滑版本
            cluster_center = np.mean(cluster_timestamps)
            
            # 对簇内时间戳进行微调，使其更加均匀分布
            for idx in cluster_indices:
                relative_pos = (timestamps[idx] - cluster_timestamps[0]) / (cluster_timestamps[-1] - cluster_timestamps[0]) if len(cluster_timestamps) > 1 else 0
                smoothed_time = cluster_timestamps[0] + relative_pos * (cluster_timestamps[-1] - cluster_timestamps[0])
                
                # 温和调整
                adjustment = (smoothed_time - timestamps[idx]) * 0.3
                optimized[idx] = timestamps[idx] + adjustment
        
        return optimized
    
    def _smoothing_optimization(self, timestamps: List[float]) -> List[float]:
        """
        时间轴平滑优化
        
        Args:
            timestamps: 当前时间戳
            
        Returns:
            优化后的时间戳
        """
        if len(timestamps) < 3:
            return timestamps
        
        # 使用高斯滤波进行平滑
        timestamp_array = np.array(timestamps)
        
        # 计算时间间隔
        intervals = np.diff(timestamp_array)
        
        # 对间隔进行平滑
        if len(intervals) > 1:
            smoothed_intervals = gaussian_filter1d(
                intervals, 
                sigma=self.config.smoothing_sigma
            )
            
            # 重构时间戳
            smoothed_timestamps = [timestamps[0]]
            for i, interval in enumerate(smoothed_intervals):
                smoothed_timestamps.append(smoothed_timestamps[-1] + interval)
            
            # 混合原始和平滑后的结果
            blend_factor = 0.3  # 平滑强度
            optimized = []
            for orig, smooth in zip(timestamps, smoothed_timestamps):
                optimized.append(orig * (1 - blend_factor) + smooth * blend_factor)
            
            return optimized
        
        return timestamps
    
    def _calculate_quality_scores(self, timestamps: List[float],
                                subtitles: List[SubtitleEntry],
                                audio_features: Optional[AudioFeatures] = None) -> List[float]:
        """计算时间戳质量分数"""
        scores = []
        
        for i, (timestamp, subtitle) in enumerate(zip(timestamps, subtitles)):
            score = 1.0
            
            # 基于间距的质量分数
            if i > 0:
                gap = timestamp - timestamps[i-1]
                if gap < self.config.min_subtitle_gap:
                    score *= 0.5  # 间距太小
                elif gap > self.config.max_subtitle_gap:
                    score *= 0.7  # 间距太大
            
            # 基于音频特征的质量分数
            if audio_features is not None:
                # 查找最近的时间帧
                frame_idx = np.argmin(np.abs(audio_features.time_frames - timestamp))
                if frame_idx < len(audio_features.rms_energy):
                    energy = audio_features.rms_energy[frame_idx]
                    # 归一化能量分数
                    energy_score = min(1.0, energy / np.mean(audio_features.rms_energy))
                    score *= (0.7 + 0.3 * energy_score)
            
            scores.append(score)
        
        return scores
    
    def _calculate_confidence_scores(self, timestamps: List[float],
                                   subtitles: List[SubtitleEntry],
                                   boundaries: Optional[List[SpeechBoundary]] = None) -> List[float]:
        """计算时间戳置信度分数"""
        scores = []
        
        for i, timestamp in enumerate(timestamps):
            confidence = 0.5  # 基础置信度
            
            # 基于边界的置信度
            if boundaries is not None:
                min_distance = float('inf')
                best_boundary_confidence = 0
                
                for boundary in boundaries:
                    distance = abs(boundary.time - timestamp)
                    if distance < min_distance:
                        min_distance = distance
                        best_boundary_confidence = boundary.confidence
                
                # 距离越近，置信度越高
                if min_distance <= self.config.fine_tune_window:
                    distance_factor = 1 - min_distance / self.config.fine_tune_window
                    confidence = max(confidence, best_boundary_confidence * distance_factor)
            
            # 基于原始置信度
            if hasattr(subtitles[i], 'confidence'):
                original_confidence = subtitles[i].confidence
                confidence = max(confidence, original_confidence * 0.8)
            
            scores.append(min(1.0, confidence))
        
        return scores
    
    def _update_stats(self, result: OptimizationResult):
        """更新统计信息"""
        self.stats['total_optimizations'] += 1
        
        # 计算改进程度
        improvement = result.metadata.get('improvement_score', 0)
        total = self.stats['total_optimizations']
        prev_avg = self.stats['average_improvement']
        self.stats['average_improvement'] = (prev_avg * (total - 1) + improvement) / total
        
        # 更新收敛率
        if result.convergence_achieved:
            prev_convergence = self.stats['convergence_rate']
            self.stats['convergence_rate'] = (prev_convergence * (total - 1) + 1) / total
        else:
            self.stats['convergence_rate'] = (self.stats['convergence_rate'] * (total - 1)) / total
    
    def fine_tune_single_timestamp(self, timestamp: float,
                                 audio_features: AudioFeatures,
                                 window_size: Optional[float] = None) -> Tuple[float, float]:
        """
        精细调整单个时间戳
        
        Args:
            timestamp: 原始时间戳
            audio_features: 音频特征
            window_size: 调整窗口大小
            
        Returns:
            (优化后的时间戳, 置信度)
        """
        window = window_size or self.config.fine_tune_window
        
        # 定义搜索窗口
        window_start = max(0, timestamp - window / 2)
        window_end = min(audio_features.duration, timestamp + window / 2)
        
        # 获取窗口内的特征
        frame_mask = (audio_features.time_frames >= window_start) & (audio_features.time_frames <= window_end)
        window_frames = audio_features.time_frames[frame_mask]
        window_energy = audio_features.rms_energy[frame_mask]
        
        if len(window_frames) == 0:
            return timestamp, 0.5
        
        # 寻找最佳对齐点：能量上升最快的点
        energy_gradient = np.gradient(window_energy)
        best_idx = np.argmax(np.abs(energy_gradient))
        best_timestamp = window_frames[best_idx]
        
        # 计算置信度
        gradient_strength = np.abs(energy_gradient[best_idx])
        max_gradient = np.max(np.abs(energy_gradient))
        confidence = gradient_strength / max_gradient if max_gradient > 0 else 0.5
        
        return best_timestamp, confidence
    
    def batch_optimize_timestamps(self, timestamp_batches: List[List[float]],
                                audio_features_list: List[AudioFeatures],
                                progress_callback: Optional[Callable[[float], None]] = None) -> List[List[float]]:
        """
        批量优化时间戳
        
        Args:
            timestamp_batches: 时间戳批次列表
            audio_features_list: 对应的音频特征列表
            progress_callback: 进度回调函数
            
        Returns:
            优化后的时间戳批次列表
        """
        optimized_batches = []
        total_batches = len(timestamp_batches)
        
        for i, (timestamps, audio_features) in enumerate(zip(timestamp_batches, audio_features_list)):
            # 创建临时字幕对象
            temp_subtitles = [
                SubtitleEntry(f"Temp {j}", ts, ts + 1.0) 
                for j, ts in enumerate(timestamps)
            ]
            
            # 优化时间戳
            optimized_subtitles, _ = self.optimize_timestamps(temp_subtitles, audio_features)
            optimized_timestamps = [s.start_time for s in optimized_subtitles]
            optimized_batches.append(optimized_timestamps)
            
            # 更新进度
            if progress_callback:
                progress = (i + 1) / total_batches
                progress_callback(progress)
        
        return optimized_batches
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            **self.stats,
            'config': {
                'fine_tune_window': self.config.fine_tune_window,
                'max_adjustment': self.config.max_adjustment,
                'enable_smoothing': self.config.enable_smoothing,
                'enable_clustering': self.config.enable_clustering
            }
        }


# 便捷函数
def optimize_subtitle_timestamps(subtitles: List[SubtitleEntry],
                               audio_features: Optional[AudioFeatures] = None,
                               boundaries: Optional[List[SpeechBoundary]] = None,
                               config: Optional[OptimizerConfig] = None) -> Tuple[List[SubtitleEntry], OptimizationResult]:
    """
    优化字幕时间戳的便捷函数
    
    Args:
        subtitles: 字幕列表
        audio_features: 音频特征
        boundaries: 语音边界
        config: 优化器配置
        
    Returns:
        (优化后的字幕, 优化结果)
    """
    optimizer = TimestampOptimizer(config)
    return optimizer.optimize_timestamps(subtitles, audio_features, boundaries)


if __name__ == "__main__":
    # 测试时间戳优化器
    print("🎯 时间戳优化器测试")
    print("=" * 60)
    
    # 创建配置
    config = OptimizerConfig()
    
    print(f"优化器配置:")
    print(f"  微调窗口: {config.fine_tune_window}秒")
    print(f"  最大调整幅度: {config.max_adjustment}秒")
    print(f"  最小字幕间距: {config.min_subtitle_gap}秒")
    print(f"  启用平滑: {config.enable_smoothing}")
    print(f"  启用聚类: {config.enable_clustering}")
    
    # 创建优化器
    optimizer = TimestampOptimizer(config)
    
    print(f"\n优化器信息:")
    print(f"  最大迭代次数: {config.max_iterations}")
    print(f"  收敛阈值: {config.convergence_threshold}")
    print(f"  置信度阈值: {config.confidence_threshold}")
    
    # 创建测试字幕
    test_subtitles = [
        SubtitleEntry("第一句", 1.0, 3.0),
        SubtitleEntry("第二句", 2.8, 4.5),  # 间距过小
        SubtitleEntry("第三句", 7.0, 9.0),  # 间距过大
    ]
    
    print(f"\n测试数据:")
    for i, sub in enumerate(test_subtitles):
        print(f"  字幕{i+1}: {sub.text} ({sub.start_time}s-{sub.end_time}s)")
    
    print(f"\n使用示例:")
    print(f"  optimized_subs, result = optimizer.optimize_timestamps(subtitles, audio_features, boundaries)")
    print(f"  print(f'优化步数: {{result.optimization_steps}}')")
    print(f"  print(f'收敛状态: {{result.convergence_achieved}}')")
    print(f"  print(f'平均调整: {{np.mean(np.abs(result.adjustments)):.3f}}s')")