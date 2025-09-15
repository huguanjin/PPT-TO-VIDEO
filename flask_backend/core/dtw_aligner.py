"""
DTW对齐算法核心模块
Phase 3: 智能对齐系统的动态时间规整组件
实现高精度音频-字幕时间戳对齐功能
"""
import numpy as np
from typing import List, Tuple, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
import logging

try:
    from fastdtw import fastdtw
except ImportError:
    print("Warning: fastdtw not installed. Install with: pip install fastdtw")
    def fastdtw(x, y, dist=None):
        """Fallback DTW implementation"""
        # 简单的DTW fallback实现
        print("Using fallback DTW implementation")
        return 0.0, []

from scipy.spatial.distance import euclidean, cosine
from sklearn.preprocessing import StandardScaler
from .audio_feature_extractor import AudioFeatures, AudioConfig
from .speech_boundary_detector import SpeechBoundary, SpeechSegment, BoundaryConfig

logger = logging.getLogger(__name__)


@dataclass
class DTWConfig:
    """DTW对齐配置"""
    # 基础参数
    radius: int = 5                    # DTW搜索半径
    distance_metric: str = 'euclidean' # 距离度量: 'euclidean', 'cosine', 'manhattan'
    
    # 特征权重
    mfcc_weight: float = 0.4          # MFCC特征权重
    energy_weight: float = 0.3        # 能量特征权重
    spectral_weight: float = 0.2      # 频谱特征权重
    rhythm_weight: float = 0.1        # 韵律特征权重
    
    # 对齐约束
    max_warp_ratio: float = 2.0       # 最大时间扭曲比例
    min_alignment_score: float = 0.5  # 最小对齐分数
    
    # 预处理
    normalize_features: bool = True    # 标准化特征
    apply_smoothing: bool = True      # 应用平滑
    smoothing_window: int = 3         # 平滑窗口
    
    # 后处理
    interpolate_gaps: bool = True     # 插值填补间隙
    remove_outliers: bool = True      # 移除异常值
    outlier_threshold: float = 2.0    # 异常值阈值(标准差倍数)


@dataclass
class AlignmentResult:
    """对齐结果"""
    audio_timestamps: List[float]     # 音频时间戳
    text_positions: List[int]         # 文本位置
    alignment_path: List[Tuple[int, int]]  # 对齐路径
    alignment_score: float            # 对齐分数
    confidence: float                 # 置信度
    metadata: Dict[str, Any]          # 元数据


@dataclass
class SubtitleEntry:
    """字幕条目"""
    text: str                         # 字幕文本
    start_time: float                 # 开始时间
    end_time: float                   # 结束时间
    confidence: float = 1.0           # 置信度
    metadata: Dict[str, Any] = field(default_factory=dict)   # 元数据


class DTWAligner:
    """DTW对齐器"""
    
    def __init__(self, dtw_config: Optional[DTWConfig] = None):
        """
        初始化DTW对齐器
        
        Args:
            dtw_config: DTW配置
        """
        self.config = dtw_config or DTWConfig()
        
        # 距离函数映射
        self.distance_functions = {
            'euclidean': euclidean,
            'cosine': cosine,
            'manhattan': lambda x, y: np.sum(np.abs(x - y))
        }
        
        # 特征缩放器
        self.scaler = StandardScaler() if self.config.normalize_features else None
        
        logger.info(f"DTW对齐器初始化完成，搜索半径: {self.config.radius}")
    
    def extract_alignment_features(self, audio_features: AudioFeatures) -> np.ndarray:
        """
        提取用于对齐的音频特征
        
        Args:
            audio_features: 音频特征对象
            
        Returns:
            对齐特征矩阵 (n_frames, n_features)
        """
        features_list = []
        
        # MFCC特征
        if hasattr(audio_features, 'mfcc') and audio_features.mfcc is not None:
            mfcc_features = audio_features.mfcc.T  # 转置为 (n_frames, n_mfcc)
            if self.config.mfcc_weight > 0:
                features_list.append(mfcc_features * self.config.mfcc_weight)
        
        # 能量特征
        if hasattr(audio_features, 'rms_energy') and audio_features.rms_energy is not None:
            energy_features = audio_features.rms_energy.reshape(-1, 1)
            if self.config.energy_weight > 0:
                features_list.append(energy_features * self.config.energy_weight)
        
        # 频谱特征
        spectral_features = []
        if hasattr(audio_features, 'spectral_centroid') and audio_features.spectral_centroid is not None:
            spectral_features.append(audio_features.spectral_centroid)
        if hasattr(audio_features, 'spectral_bandwidth') and audio_features.spectral_bandwidth is not None:
            spectral_features.append(audio_features.spectral_bandwidth)
        if hasattr(audio_features, 'spectral_rolloff') and audio_features.spectral_rolloff is not None:
            spectral_features.append(audio_features.spectral_rolloff)
        
        if spectral_features and self.config.spectral_weight > 0:
            spectral_matrix = np.column_stack(spectral_features)
            features_list.append(spectral_matrix * self.config.spectral_weight)
        
        # 韵律特征 (简化版本)
        if hasattr(audio_features, 'zero_crossing_rate') and audio_features.zero_crossing_rate is not None:
            rhythm_features = audio_features.zero_crossing_rate.reshape(-1, 1)
            if self.config.rhythm_weight > 0:
                features_list.append(rhythm_features * self.config.rhythm_weight)
        
        # 合并所有特征
        if features_list:
            combined_features = np.column_stack(features_list)
        else:
            # 如果没有特征，使用能量作为基本特征
            combined_features = audio_features.rms_energy.reshape(-1, 1)
        
        # 标准化
        if self.config.normalize_features and self.scaler is not None:
            combined_features = self.scaler.fit_transform(combined_features)
        
        # 平滑处理
        if self.config.apply_smoothing:
            combined_features = self._smooth_features(combined_features)
        
        logger.debug(f"提取对齐特征: {combined_features.shape}")
        return combined_features
    
    def _smooth_features(self, features: np.ndarray) -> np.ndarray:
        """
        特征平滑处理
        
        Args:
            features: 特征矩阵
            
        Returns:
            平滑后的特征矩阵
        """
        window_size = self.config.smoothing_window
        if window_size <= 1:
            return features
        
        # 对每个特征维度应用移动平均
        smoothed = np.zeros_like(features)
        for i in range(features.shape[1]):
            smoothed[:, i] = np.convolve(
                features[:, i], 
                np.ones(window_size) / window_size, 
                mode='same'
            )
        
        return smoothed
    
    def create_text_sequence(self, subtitles: List[SubtitleEntry], 
                           total_duration: float) -> np.ndarray:
        """
        创建文本序列用于对齐
        
        Args:
            subtitles: 字幕列表
            total_duration: 总时长
            
        Returns:
            文本序列特征
        """
        # 创建时间网格
        time_resolution = 0.01  # 10ms分辨率
        n_frames = int(total_duration / time_resolution) + 1
        time_grid = np.linspace(0, total_duration, n_frames)
        
        # 创建文本密度序列
        text_density = np.zeros(n_frames)
        
        for subtitle in subtitles:
            start_idx = int(subtitle.start_time / time_resolution)
            end_idx = int(subtitle.end_time / time_resolution)
            
            # 限制索引范围
            start_idx = max(0, min(start_idx, n_frames - 1))
            end_idx = max(0, min(end_idx, n_frames - 1))
            
            if start_idx < end_idx:
                # 根据文本长度设置密度
                text_length = len(subtitle.text)
                density_value = text_length / max(1, (end_idx - start_idx))
                text_density[start_idx:end_idx] = density_value
        
        # 平滑文本密度
        if self.config.apply_smoothing:
            text_density = np.convolve(
                text_density, 
                np.ones(self.config.smoothing_window) / self.config.smoothing_window,
                mode='same'
            )
        
        # 转换为二维特征
        text_features = text_density.reshape(-1, 1)
        
        logger.debug(f"创建文本序列: {text_features.shape}")
        return text_features
    
    def align_sequences(self, audio_features: np.ndarray, 
                       text_features: np.ndarray) -> AlignmentResult:
        """
        对齐音频和文本序列
        
        Args:
            audio_features: 音频特征序列
            text_features: 文本特征序列
            
        Returns:
            对齐结果
        """
        logger.info(f"开始DTW对齐: 音频帧{audio_features.shape[0]}, 文本帧{text_features.shape[0]}")
        
        # 选择距离函数
        distance_func = self.distance_functions.get(
            self.config.distance_metric, 
            euclidean
        )
        
        # 执行DTW对齐
        try:
            # 使用正确的fastdtw参数
            distance, path = fastdtw(
                audio_features, 
                text_features,
                dist=distance_func
            )
            
            # 计算对齐分数 (距离越小，分数越高)
            max_possible_distance = np.sqrt(np.sum(np.var(audio_features, axis=0)) + 
                                          np.sum(np.var(text_features, axis=0)))
            alignment_score = max(0, 1 - distance / max_possible_distance)
            
            # 提取对齐路径
            audio_indices = [p[0] for p in path]
            text_indices = [p[1] for p in path]
            
            # 计算置信度
            confidence = self._calculate_alignment_confidence(
                audio_features, text_features, path, distance
            )
            
            # 创建结果
            result = AlignmentResult(
                audio_timestamps=[],  # 需要转换为实际时间戳
                text_positions=text_indices,
                alignment_path=path,
                alignment_score=alignment_score,
                confidence=confidence,
                metadata={
                    'dtw_distance': distance,
                    'path_length': len(path),
                    'compression_ratio': len(path) / max(len(audio_features), len(text_features))
                }
            )
            
            logger.info(f"DTW对齐完成: 分数={alignment_score:.3f}, 置信度={confidence:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"DTW对齐失败: {e}")
            # 返回线性对齐作为后备
            return self._fallback_linear_alignment(audio_features, text_features)
    
    def _calculate_alignment_confidence(self, audio_features: np.ndarray,
                                      text_features: np.ndarray,
                                      path: List[Tuple[int, int]],
                                      distance: float) -> float:
        """
        计算对齐置信度
        
        Args:
            audio_features: 音频特征
            text_features: 文本特征
            path: 对齐路径
            distance: DTW距离
            
        Returns:
            置信度分数
        """
        # 基于距离的置信度
        distance_confidence = 1.0 / (1.0 + distance)
        
        # 基于路径平滑性的置信度
        if len(path) > 1:
            # 计算路径斜率变化
            slopes = []
            for i in range(1, len(path)):
                dx = path[i][0] - path[i-1][0]
                dy = path[i][1] - path[i-1][1]
                if dx > 0:
                    slope = dy / dx
                    slopes.append(slope)
            
            if slopes:
                slope_std = float(np.std(slopes))
                smoothness_confidence = 1.0 / (1.0 + slope_std)
            else:
                smoothness_confidence = 0.5
        else:
            smoothness_confidence = 0.5
        
        # 基于时间扭曲程度的置信度
        ideal_length = max(len(audio_features), len(text_features))
        actual_length = len(path)
        warp_ratio = actual_length / ideal_length
        
        if warp_ratio <= self.config.max_warp_ratio:
            warp_confidence = 1.0 - abs(warp_ratio - 1.0) / self.config.max_warp_ratio
        else:
            warp_confidence = 0.1
        
        # 综合置信度
        total_confidence = (distance_confidence * 0.4 + 
                          smoothness_confidence * 0.3 + 
                          warp_confidence * 0.3)
        
        return min(1.0, max(0.0, float(total_confidence)))
    
    def _fallback_linear_alignment(self, audio_features: np.ndarray,
                                 text_features: np.ndarray) -> AlignmentResult:
        """
        线性对齐作为后备方案
        
        Args:
            audio_features: 音频特征
            text_features: 文本特征
            
        Returns:
            线性对齐结果
        """
        logger.warning("使用线性对齐作为后备方案")
        
        # 创建线性映射
        audio_len = len(audio_features)
        text_len = len(text_features)
        
        if audio_len == 0 or text_len == 0:
            return AlignmentResult([], [], [], 0.0, 0.0, {})
        
        # 线性插值
        path = []
        for i in range(max(audio_len, text_len)):
            audio_idx = int(i * audio_len / max(audio_len, text_len))
            text_idx = int(i * text_len / max(audio_len, text_len))
            path.append((audio_idx, text_idx))
        
        return AlignmentResult(
            audio_timestamps=[],
            text_positions=[p[1] for p in path],
            alignment_path=path,
            alignment_score=0.5,  # 中等分数
            confidence=0.3,       # 低置信度
            metadata={'fallback': True}
        )
    
    def convert_to_timestamps(self, alignment_result: AlignmentResult,
                            audio_time_frames: np.ndarray,
                            subtitles: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """
        将对齐结果转换为时间戳
        
        Args:
            alignment_result: 对齐结果
            audio_time_frames: 音频时间帧
            subtitles: 原始字幕
            
        Returns:
            对齐后的字幕
        """
        aligned_subtitles = []
        
        if not alignment_result.alignment_path:
            return subtitles
        
        # 创建时间映射
        time_mapping = {}
        for audio_idx, text_idx in alignment_result.alignment_path:
            if audio_idx < len(audio_time_frames):
                time_mapping[text_idx] = audio_time_frames[audio_idx]
        
        # 更新字幕时间戳
        for i, subtitle in enumerate(subtitles):
            new_subtitle = SubtitleEntry(
                text=subtitle.text,
                start_time=subtitle.start_time,
                end_time=subtitle.end_time,
                confidence=subtitle.confidence,
                metadata=subtitle.metadata.copy()
            )
            
            # 查找对应的音频时间
            if i in time_mapping:
                new_subtitle.start_time = time_mapping[i]
                new_subtitle.metadata['aligned'] = True
                new_subtitle.metadata['alignment_confidence'] = alignment_result.confidence
            
            aligned_subtitles.append(new_subtitle)
        
        # 后处理
        if self.config.interpolate_gaps:
            aligned_subtitles = self._interpolate_missing_timestamps(aligned_subtitles)
        
        if self.config.remove_outliers:
            aligned_subtitles = self._remove_timestamp_outliers(aligned_subtitles)
        
        return aligned_subtitles
    
    def _interpolate_missing_timestamps(self, subtitles: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """插值填补缺失的时间戳"""
        if len(subtitles) < 2:
            return subtitles
        
        result = []
        
        for i, subtitle in enumerate(subtitles):
            if subtitle.metadata.get('aligned', False):
                result.append(subtitle)
            else:
                # 查找前后已对齐的点进行插值
                prev_time = None
                next_time = None
                prev_idx = None
                next_idx = None
                
                # 找前一个对齐点
                for j in range(i - 1, -1, -1):
                    if subtitles[j].metadata.get('aligned', False):
                        prev_time = subtitles[j].start_time
                        prev_idx = j
                        break
                
                # 找后一个对齐点
                for j in range(i + 1, len(subtitles)):
                    if subtitles[j].metadata.get('aligned', False):
                        next_time = subtitles[j].start_time
                        next_idx = j
                        break
                
                # 插值计算
                if prev_time is not None and next_time is not None and prev_idx is not None and next_idx is not None:
                    ratio = (i - prev_idx) / (next_idx - prev_idx) if next_idx != prev_idx else 0.5
                    interpolated_time = prev_time + ratio * (next_time - prev_time)
                    
                    new_subtitle = SubtitleEntry(
                        text=subtitle.text,
                        start_time=interpolated_time,
                        end_time=subtitle.end_time,
                        confidence=subtitle.confidence * 0.8,  # 降低置信度
                        metadata={**subtitle.metadata, 'interpolated': True}
                    )
                    result.append(new_subtitle)
                else:
                    result.append(subtitle)
        
        return result
    
    def _remove_timestamp_outliers(self, subtitles: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """移除时间戳异常值"""
        if len(subtitles) < 3:
            return subtitles
        
        # 计算时间差异
        time_diffs = []
        for i in range(1, len(subtitles)):
            diff = subtitles[i].start_time - subtitles[i-1].start_time
            time_diffs.append(diff)
        
        if not time_diffs:
            return subtitles
        
        # 计算异常值阈值
        mean_diff = float(np.mean(time_diffs))
        std_diff = float(np.std(time_diffs))
        threshold = self.config.outlier_threshold * std_diff
        
        result = [subtitles[0]]  # 保留第一个
        
        for i in range(1, len(subtitles)):
            current_diff = subtitles[i].start_time - subtitles[i-1].start_time
            
            if abs(current_diff - mean_diff) <= threshold:
                result.append(subtitles[i])
            else:
                # 异常值，使用预测值
                predicted_time = float(result[-1].start_time + mean_diff)
                corrected_subtitle = SubtitleEntry(
                    text=subtitles[i].text,
                    start_time=predicted_time,
                    end_time=subtitles[i].end_time,
                    confidence=subtitles[i].confidence * 0.6,  # 大幅降低置信度
                    metadata={**subtitles[i].metadata, 'outlier_corrected': True}
                )
                result.append(corrected_subtitle)
        
        return result
    
    def align_audio_text(self, audio_features: AudioFeatures,
                        subtitles: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """
        音频文本对齐的主接口
        
        Args:
            audio_features: 音频特征
            subtitles: 字幕列表
            
        Returns:
            对齐后的字幕
        """
        logger.info(f"开始音频文本对齐，字幕数量: {len(subtitles)}")
        
        # 提取对齐特征
        audio_align_features = self.extract_alignment_features(audio_features)
        
        # 创建文本序列
        text_align_features = self.create_text_sequence(subtitles, audio_features.duration)
        
        # 执行DTW对齐
        alignment_result = self.align_sequences(audio_align_features, text_align_features)
        
        # 检查对齐质量
        if alignment_result.alignment_score < self.config.min_alignment_score:
            logger.warning(f"对齐质量较低: {alignment_result.alignment_score:.3f}")
        
        # 转换为时间戳
        aligned_subtitles = self.convert_to_timestamps(
            alignment_result, audio_features.time_frames, subtitles
        )
        
        logger.info(f"音频文本对齐完成，对齐分数: {alignment_result.alignment_score:.3f}")
        return aligned_subtitles


# 便捷函数
def align_audio_subtitles(audio_features: AudioFeatures,
                         subtitles: List[SubtitleEntry],
                         dtw_config: Optional[DTWConfig] = None) -> List[SubtitleEntry]:
    """
    音频字幕对齐的便捷函数
    
    Args:
        audio_features: 音频特征
        subtitles: 字幕列表
        dtw_config: DTW配置
        
    Returns:
        对齐后的字幕
    """
    aligner = DTWAligner(dtw_config)
    return aligner.align_audio_text(audio_features, subtitles)


if __name__ == "__main__":
    # 测试DTW对齐器
    print("🎯 DTW对齐器测试")
    print("=" * 60)
    
    # 创建配置
    dtw_config = DTWConfig()
    
    print(f"DTW配置:")
    print(f"  搜索半径: {dtw_config.radius}")
    print(f"  距离度量: {dtw_config.distance_metric}")
    print(f"  最大扭曲比例: {dtw_config.max_warp_ratio}")
    print(f"  特征权重:")
    print(f"    MFCC: {dtw_config.mfcc_weight}")
    print(f"    能量: {dtw_config.energy_weight}")
    print(f"    频谱: {dtw_config.spectral_weight}")
    print(f"    韵律: {dtw_config.rhythm_weight}")
    
    # 创建对齐器
    aligner = DTWAligner(dtw_config)
    
    print(f"\n对齐器信息:")
    print(f"  距离函数: {list(aligner.distance_functions.keys())}")
    print(f"  特征标准化: {aligner.config.normalize_features}")
    print(f"  特征平滑: {aligner.config.apply_smoothing}")
    
    print(f"\n使用示例:")
    print(f"  aligned_subtitles = aligner.align_audio_text(audio_features, subtitles)")
    print(f"  print(f'对齐完成，分数: {{alignment_result.alignment_score:.3f}}')")
    print(f"  print(f'置信度: {{alignment_result.confidence:.3f}}')")