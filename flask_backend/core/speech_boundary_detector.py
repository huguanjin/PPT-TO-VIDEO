"""
语音边界检测系统
Phase 3: 智能对齐系统的语音分析组件
实现精确的语音边界识别、停顿检测和语音分段功能
"""
import numpy as np
import librosa
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
import logging
from .audio_feature_extractor import AudioFeatureExtractor, AudioConfig, AudioFeatures

logger = logging.getLogger(__name__)


@dataclass
class BoundaryConfig:
    """边界检测配置"""
    # 基础参数
    min_pause_duration: float = 0.15      # 最小停顿时长(秒)
    max_pause_duration: float = 2.0       # 最大停顿时长(秒)
    
    # 能量阈值
    energy_percentile: float = 25         # 能量阈值百分位
    energy_ratio_threshold: float = 0.3   # 能量比率阈值
    
    # 频谱阈值
    spectral_threshold: float = 0.1       # 频谱能量阈值
    
    # 平滑参数
    smoothing_window: int = 5             # 平滑窗口大小
    median_filter_size: int = 3           # 中值滤波器大小
    
    # 后处理参数
    merge_close_boundaries: bool = True   # 合并相近边界
    min_boundary_distance: float = 0.2   # 最小边界间距(秒)
    
    # 质量控制
    confidence_threshold: float = 0.6     # 置信度阈值
    min_segment_duration: float = 0.3     # 最小段长度(秒)


@dataclass
class SpeechBoundary:
    """语音边界信息"""
    time: float                    # 边界时间(秒)
    confidence: float              # 置信度(0-1)
    boundary_type: str            # 边界类型: 'pause', 'energy_drop', 'spectral_change'
    strength: float               # 边界强度
    context: Dict[str, Any]       # 上下文信息


@dataclass
class SpeechSegment:
    """语音段信息"""
    start_time: float             # 开始时间
    end_time: float              # 结束时间
    duration: float              # 持续时间
    avg_energy: float            # 平均能量
    avg_pitch: float             # 平均基频(如果可用)
    confidence: float            # 段质量置信度
    features: Dict[str, Any]     # 段特征


class SpeechBoundaryDetector:
    """语音边界检测器"""
    
    def __init__(self, boundary_config: Optional[BoundaryConfig] = None, 
                 audio_config: Optional[AudioConfig] = None):
        """
        初始化语音边界检测器
        
        Args:
            boundary_config: 边界检测配置
            audio_config: 音频处理配置
        """
        self.boundary_config = boundary_config or BoundaryConfig()
        self.audio_config = audio_config or AudioConfig()
        
        # 初始化音频特征提取器
        self.feature_extractor = AudioFeatureExtractor(self.audio_config)
        
        logger.info(f"语音边界检测器初始化完成")
    
    def detect_energy_boundaries(self, features: AudioFeatures) -> List[SpeechBoundary]:
        """
        基于能量的边界检测
        
        Args:
            features: 音频特征
            
        Returns:
            能量边界列表
        """
        boundaries = []
        
        # 获取RMS能量和时间帧
        rms_energy = features.rms_energy
        time_frames = features.time_frames
        
        # 计算能量阈值
        energy_threshold = np.percentile(rms_energy, self.boundary_config.energy_percentile)
        
        # 平滑能量曲线
        smoothed_energy = self._smooth_signal(rms_energy, self.boundary_config.smoothing_window)
        
        # 检测能量下降点
        energy_diff = np.diff(smoothed_energy)
        
        # 找到显著的能量下降
        for i, diff in enumerate(energy_diff):
            if i + 1 < len(time_frames):
                current_energy = smoothed_energy[i + 1]
                prev_energy = smoothed_energy[i]
                
                # 检查是否是显著下降
                if (current_energy < energy_threshold and 
                    prev_energy > current_energy * (1 + self.boundary_config.energy_ratio_threshold)):
                    
                    time = time_frames[i + 1]
                    confidence = min(1.0, abs(diff) / float(np.std(energy_diff)))
                    strength = abs(diff)
                    
                    boundary = SpeechBoundary(
                        time=time,
                        confidence=confidence,
                        boundary_type='energy_drop',
                        strength=strength,
                        context={
                            'current_energy': current_energy,
                            'prev_energy': prev_energy,
                            'energy_diff': diff
                        }
                    )
                    boundaries.append(boundary)
        
        logger.debug(f"检测到 {len(boundaries)} 个能量边界")
        return boundaries
    
    def detect_pause_boundaries(self, features: AudioFeatures) -> List[SpeechBoundary]:
        """
        基于停顿的边界检测
        
        Args:
            features: 音频特征
            
        Returns:
            停顿边界列表
        """
        boundaries = []
        
        # 使用静音段作为停顿边界
        for start_time, end_time in features.silence_segments:
            duration = end_time - start_time
            
            # 检查停顿时长
            if (self.boundary_config.min_pause_duration <= duration <= 
                self.boundary_config.max_pause_duration):
                
                # 在停顿中间添加边界
                boundary_time = (start_time + end_time) / 2
                
                # 计算置信度 (基于停顿时长)
                ideal_duration = 0.5  # 理想停顿时长
                confidence = 1.0 - abs(duration - ideal_duration) / ideal_duration
                confidence = max(0.1, min(1.0, confidence))
                
                boundary = SpeechBoundary(
                    time=boundary_time,
                    confidence=confidence,
                    boundary_type='pause',
                    strength=duration,
                    context={
                        'pause_start': start_time,
                        'pause_end': end_time,
                        'pause_duration': duration
                    }
                )
                boundaries.append(boundary)
        
        logger.debug(f"检测到 {len(boundaries)} 个停顿边界")
        return boundaries
    
    def detect_spectral_boundaries(self, features: AudioFeatures) -> List[SpeechBoundary]:
        """
        基于频谱变化的边界检测
        
        Args:
            features: 音频特征
            
        Returns:
            频谱边界列表
        """
        boundaries = []
        
        # 使用频谱质心作为频谱特征
        spectral_centroid = features.spectral_centroid
        time_frames = features.time_frames
        
        # 计算频谱变化率
        spectral_diff = np.abs(np.diff(spectral_centroid))
        
        # 平滑频谱变化
        smoothed_diff = self._smooth_signal(spectral_diff, self.boundary_config.smoothing_window)
        
        # 计算阈值
        threshold = np.percentile(smoothed_diff, 75)  # 使用75分位数作为阈值
        
        # 检测显著变化点
        for i, diff in enumerate(smoothed_diff):
            if diff > threshold and i + 1 < len(time_frames):
                time = time_frames[i + 1]
                confidence = min(1.0, diff / float(np.max(smoothed_diff)))
                
                boundary = SpeechBoundary(
                    time=time,
                    confidence=confidence,
                    boundary_type='spectral_change',
                    strength=diff,
                    context={
                        'spectral_diff': diff,
                        'threshold': threshold
                    }
                )
                boundaries.append(boundary)
        
        logger.debug(f"检测到 {len(boundaries)} 个频谱边界")
        return boundaries
    
    def _smooth_signal(self, signal: np.ndarray, window_size: int) -> np.ndarray:
        """
        信号平滑处理
        
        Args:
            signal: 输入信号
            window_size: 窗口大小
            
        Returns:
            平滑后的信号
        """
        if window_size <= 1:
            return signal
        
        # 使用简单的移动平均
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(signal, kernel, mode='same')
        
        return smoothed
    
    def merge_boundaries(self, boundaries: List[SpeechBoundary]) -> List[SpeechBoundary]:
        """
        合并相近的边界点
        
        Args:
            boundaries: 原始边界列表
            
        Returns:
            合并后的边界列表
        """
        if not boundaries or not self.boundary_config.merge_close_boundaries:
            return boundaries
        
        # 按时间排序
        sorted_boundaries = sorted(boundaries, key=lambda b: b.time)
        merged = []
        
        current_group = [sorted_boundaries[0]]
        
        for boundary in sorted_boundaries[1:]:
            # 检查是否与当前组相近
            if (boundary.time - current_group[-1].time <= 
                self.boundary_config.min_boundary_distance):
                current_group.append(boundary)
            else:
                # 合并当前组
                merged_boundary = self._merge_boundary_group(current_group)
                merged.append(merged_boundary)
                current_group = [boundary]
        
        # 处理最后一组
        if current_group:
            merged_boundary = self._merge_boundary_group(current_group)
            merged.append(merged_boundary)
        
        logger.debug(f"边界合并: {len(boundaries)} -> {len(merged)}")
        return merged
    
    def _merge_boundary_group(self, group: List[SpeechBoundary]) -> SpeechBoundary:
        """
        合并一组边界点
        
        Args:
            group: 边界组
            
        Returns:
            合并后的边界
        """
        if len(group) == 1:
            return group[0]
        
        # 计算加权平均时间
        total_weight = sum(b.confidence * b.strength for b in group)
        if total_weight > 0:
            avg_time = sum(b.time * b.confidence * b.strength for b in group) / total_weight
        else:
            avg_time = sum(b.time for b in group) / len(group)
        
        # 计算合并后的置信度和强度
        avg_confidence = sum(b.confidence for b in group) / len(group)
        total_strength = sum(b.strength for b in group)
        
        # 确定主要类型
        type_counts = {}
        for b in group:
            type_counts[b.boundary_type] = type_counts.get(b.boundary_type, 0) + 1
        main_type = max(type_counts.keys(), key=lambda t: type_counts[t])
        
        return SpeechBoundary(
            time=avg_time,
            confidence=avg_confidence,
            boundary_type=main_type,
            strength=total_strength,
            context={
                'merged_from': len(group),
                'original_types': list(type_counts.keys())
            }
        )
    
    def filter_boundaries(self, boundaries: List[SpeechBoundary]) -> List[SpeechBoundary]:
        """
        过滤低质量边界
        
        Args:
            boundaries: 原始边界列表
            
        Returns:
            过滤后的边界列表
        """
        filtered = []
        
        for boundary in boundaries:
            # 置信度过滤
            if boundary.confidence >= self.boundary_config.confidence_threshold:
                filtered.append(boundary)
        
        logger.debug(f"边界过滤: {len(boundaries)} -> {len(filtered)}")
        return filtered
    
    def detect_boundaries(self, audio_path: str) -> List[SpeechBoundary]:
        """
        检测语音边界的主要接口
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            检测到的边界列表
        """
        logger.info(f"开始检测语音边界: {audio_path}")
        
        # 提取音频特征
        features = self.feature_extractor.extract_features(audio_path)
        
        # 检测各种类型的边界
        energy_boundaries = self.detect_energy_boundaries(features)
        pause_boundaries = self.detect_pause_boundaries(features)
        spectral_boundaries = self.detect_spectral_boundaries(features)
        
        # 合并所有边界
        all_boundaries = energy_boundaries + pause_boundaries + spectral_boundaries
        
        # 合并相近边界
        merged_boundaries = self.merge_boundaries(all_boundaries)
        
        # 过滤低质量边界
        final_boundaries = self.filter_boundaries(merged_boundaries)
        
        logger.info(f"边界检测完成: {len(final_boundaries)} 个高质量边界")
        return final_boundaries
    
    def create_speech_segments(self, boundaries: List[SpeechBoundary], 
                             features: AudioFeatures) -> List[SpeechSegment]:
        """
        基于边界创建语音段
        
        Args:
            boundaries: 边界列表
            features: 音频特征
            
        Returns:
            语音段列表
        """
        segments = []
        
        # 按时间排序边界
        sorted_boundaries = sorted(boundaries, key=lambda b: b.time)
        
        # 添加开始和结束边界
        boundary_times = [0.0] + [b.time for b in sorted_boundaries] + [features.duration]
        
        # 创建段
        for i in range(len(boundary_times) - 1):
            start_time = boundary_times[i]
            end_time = boundary_times[i + 1]
            duration = end_time - start_time
            
            # 检查段长度
            if duration >= self.boundary_config.min_segment_duration:
                # 计算段特征
                avg_energy = self._calculate_segment_energy(features, start_time, end_time)
                confidence = self._calculate_segment_confidence(features, start_time, end_time)
                
                segment = SpeechSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    avg_energy=avg_energy,
                    avg_pitch=0.0,  # 暂未实现基频检测
                    confidence=confidence,
                    features={}
                )
                segments.append(segment)
        
        logger.debug(f"创建了 {len(segments)} 个语音段")
        return segments
    
    def _calculate_segment_energy(self, features: AudioFeatures, 
                                start_time: float, end_time: float) -> float:
        """计算段平均能量"""
        # 找到时间范围内的帧
        time_mask = (features.time_frames >= start_time) & (features.time_frames <= end_time)
        
        if np.any(time_mask):
            return float(np.mean(features.rms_energy[time_mask]))
        else:
            return 0.0
    
    def _calculate_segment_confidence(self, features: AudioFeatures, 
                                    start_time: float, end_time: float) -> float:
        """计算段置信度"""
        # 简单的置信度计算：基于能量一致性
        time_mask = (features.time_frames >= start_time) & (features.time_frames <= end_time)
        
        if np.any(time_mask):
            energy_in_segment = features.rms_energy[time_mask]
            if len(energy_in_segment) > 1:
                energy_std = float(np.std(energy_in_segment))
                energy_mean = float(np.mean(energy_in_segment))
                # 变异系数越小，置信度越高
                cv = energy_std / energy_mean if energy_mean > 0 else 1.0
                confidence = max(0.1, 1.0 - cv)
                return confidence
        
        return 0.5
    
    def get_boundary_analysis(self, boundaries: List[SpeechBoundary]) -> Dict[str, Any]:
        """
        获取边界分析结果
        
        Args:
            boundaries: 边界列表
            
        Returns:
            分析结果字典
        """
        if not boundaries:
            return {
                'total_boundaries': 0,
                'boundary_types': {},
                'avg_confidence': 0,
                'quality_score': 0
            }
        
        # 统计边界类型
        type_counts = {}
        for boundary in boundaries:
            type_counts[boundary.boundary_type] = type_counts.get(boundary.boundary_type, 0) + 1
        
        # 计算统计信息
        confidences = [b.confidence for b in boundaries]
        strengths = [b.strength for b in boundaries]
        
        # 计算质量分数
        avg_confidence = float(np.mean(confidences))
        confidence_std = float(np.std(confidences))
        quality_score = avg_confidence * (1 - confidence_std)  # 高置信度 + 低方差 = 高质量
        
        analysis = {
            'total_boundaries': len(boundaries),
            'boundary_types': type_counts,
            'confidence_stats': {
                'mean': avg_confidence,
                'std': confidence_std,
                'min': float(np.min(confidences)),
                'max': float(np.max(confidences))
            },
            'strength_stats': {
                'mean': float(np.mean(strengths)),
                'std': float(np.std(strengths)),
                'min': float(np.min(strengths)),
                'max': float(np.max(strengths))
            },
            'quality_score': quality_score
        }
        
        return analysis


# 便捷函数
def detect_speech_boundaries(audio_path: str, 
                           boundary_config: Optional[BoundaryConfig] = None,
                           audio_config: Optional[AudioConfig] = None) -> List[SpeechBoundary]:
    """
    检测语音边界的便捷函数
    
    Args:
        audio_path: 音频文件路径
        boundary_config: 边界检测配置
        audio_config: 音频处理配置
        
    Returns:
        边界列表
    """
    detector = SpeechBoundaryDetector(boundary_config, audio_config)
    return detector.detect_boundaries(audio_path)


def analyze_speech_segments(audio_path: str,
                           boundary_config: Optional[BoundaryConfig] = None,
                           audio_config: Optional[AudioConfig] = None) -> Dict[str, Any]:
    """
    分析语音段的便捷函数
    
    Args:
        audio_path: 音频文件路径
        boundary_config: 边界检测配置
        audio_config: 音频处理配置
        
    Returns:
        分析结果
    """
    detector = SpeechBoundaryDetector(boundary_config, audio_config)
    
    # 检测边界
    boundaries = detector.detect_boundaries(audio_path)
    
    # 提取特征
    features = detector.feature_extractor.extract_features(audio_path)
    
    # 创建语音段
    segments = detector.create_speech_segments(boundaries, features)
    
    # 分析结果
    boundary_analysis = detector.get_boundary_analysis(boundaries)
    
    return {
        'boundaries': boundaries,
        'segments': segments,
        'boundary_analysis': boundary_analysis,
        'features': features
    }


if __name__ == "__main__":
    # 测试语音边界检测器
    print("🎯 语音边界检测器测试")
    print("=" * 60)
    
    # 创建配置
    boundary_config = BoundaryConfig()
    audio_config = AudioConfig()
    
    print(f"边界检测配置:")
    print(f"  最小停顿时长: {boundary_config.min_pause_duration}秒")
    print(f"  置信度阈值: {boundary_config.confidence_threshold}")
    print(f"  合并相近边界: {boundary_config.merge_close_boundaries}")
    
    # 创建检测器
    detector = SpeechBoundaryDetector(boundary_config, audio_config)
    
    print(f"\n检测器信息:")
    print(f"  音频配置: {detector.audio_config.sample_rate}Hz")
    print(f"  VAD可用: {detector.feature_extractor.vad_available}")
    
    print(f"\n使用示例:")
    print(f"  boundaries = detector.detect_boundaries('audio.wav')")
    print(f"  segments = detector.create_speech_segments(boundaries, features)")
    print(f"  analysis = detector.get_boundary_analysis(boundaries)")
    print(f"  print(f'检测到{{len(boundaries)}}个边界点')")