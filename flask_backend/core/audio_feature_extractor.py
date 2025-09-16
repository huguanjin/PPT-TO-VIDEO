"""
音频特征提取系统
Phase 3: 智能对齐系统的核心组件
实现专业级音频分析、VAD检测、特征提取等功能
"""
import numpy as np
import librosa
import soundfile as sf
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path
import warnings

# 尝试导入webrtcvad，如果不可用则使用备用实现
try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    webrtcvad = None
    WEBRTCVAD_AVAILABLE = False

# 忽略音频处理相关的警告
warnings.filterwarnings('ignore', category=UserWarning, module='librosa')
warnings.filterwarnings('ignore', category=FutureWarning, module='librosa')

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """音频处理配置"""
    # 基础参数
    sample_rate: int = 16000  # 标准化采样率
    frame_length: int = 1024  # 帧长度
    hop_length: int = 512     # 跳跃长度
    
    # VAD参数
    vad_mode: int = 3         # VAD敏感度 (0-3, 3最敏感)
    vad_frame_duration: int = 30  # VAD帧时长(ms)
    
    # 特征提取参数
    n_mfcc: int = 13          # MFCC特征数量
    n_fft: int = 2048         # FFT窗口大小
    
    # 边界检测参数
    silence_threshold: float = 0.01  # 静音阈值
    min_silence_duration: float = 0.1  # 最小静音时长(秒)
    min_speech_duration: float = 0.3   # 最小语音时长(秒)
    
    # 预处理参数
    normalize_audio: bool = True      # 是否归一化音频
    remove_silence: bool = False      # 是否移除静音段
    high_pass_filter: bool = True     # 是否应用高通滤波器


@dataclass
class AudioFeatures:
    """音频特征数据结构"""
    # 基础信息
    duration: float
    sample_rate: int
    frame_count: int
    
    # 时域特征
    rms_energy: np.ndarray        # RMS能量
    zero_crossing_rate: np.ndarray # 过零率
    
    # 频域特征
    mfcc: np.ndarray              # MFCC特征
    spectral_centroid: np.ndarray # 频谱质心
    spectral_rolloff: np.ndarray  # 频谱滚降
    spectral_bandwidth: np.ndarray # 频谱带宽
    
    # VAD结果
    vad_segments: List[Tuple[float, float]]  # 语音段 (开始时间, 结束时间)
    voice_activity: np.ndarray               # 帧级语音活动
    
    # 边界信息
    speech_boundaries: List[float]  # 语音边界时间点
    silence_segments: List[Tuple[float, float]]  # 静音段
    
    # 时间信息
    time_frames: np.ndarray        # 时间帧对应时间戳


class AudioFeatureExtractor:
    """音频特征提取器"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """
        初始化音频特征提取器
        
        Args:
            config: 音频处理配置
        """
        self.config = config or AudioConfig()
        
        # 初始化VAD检测器
        if WEBRTCVAD_AVAILABLE and webrtcvad is not None:
            try:
                self.vad = webrtcvad.Vad(self.config.vad_mode)  # type: ignore
                self.vad_available = True
                logger.info(f"VAD检测器初始化成功 - 模式: {self.config.vad_mode}")
            except Exception as e:
                logger.warning(f"VAD检测器初始化失败: {e}，将使用基于能量的检测")
                self.vad = None
                self.vad_available = False
        else:
            logger.warning("webrtcvad包不可用，使用基于能量的语音检测")
            self.vad = None
            self.vad_available = False
        
        logger.info(f"音频特征提取器初始化完成 - 采样率: {self.config.sample_rate}Hz")
    
    def load_audio(self, audio_path: Union[str, Path]) -> Tuple[np.ndarray, int]:
        """
        加载音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            (音频数据, 原始采样率)
        """
        try:
            audio_path = Path(audio_path)
            
            if not audio_path.exists():
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            # 使用librosa加载音频
            audio_data, original_sr_float = librosa.load(
                str(audio_path),
                sr=self.config.sample_rate,  # 重采样到目标采样率
                mono=True  # 转换为单声道
            )
            
            # 确保采样率是整数
            original_sr = int(original_sr_float)
            
            logger.info(f"音频加载成功: {audio_path.name}, 时长: {len(audio_data)/self.config.sample_rate:.2f}秒")
            
            return audio_data, original_sr
            
        except Exception as e:
            logger.error(f"音频加载失败: {e}")
            raise
    
    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        音频预处理
        
        Args:
            audio_data: 原始音频数据
            
        Returns:
            处理后的音频数据
        """
        processed_audio = audio_data.copy()
        
        # 归一化
        if self.config.normalize_audio:
            max_val = np.max(np.abs(processed_audio))
            if max_val > 0:
                processed_audio = processed_audio / max_val
        
        # 高通滤波器 (移除低频噪声)
        if self.config.high_pass_filter:
            # 简单的高通滤波器实现
            try:
                # 使用简单的一阶高通滤波器
                alpha = 0.95  # 高通滤波器系数
                filtered_audio = np.zeros_like(processed_audio)
                filtered_audio[0] = processed_audio[0]
                for i in range(1, len(processed_audio)):
                    filtered_audio[i] = alpha * (filtered_audio[i-1] + processed_audio[i] - processed_audio[i-1])
                processed_audio = filtered_audio
                logger.debug("应用简单高通滤波器")
            except Exception as e:
                logger.warning(f"高通滤波失败: {e}")
        
        logger.debug(f"音频预处理完成 - 长度: {len(processed_audio)}")
        return processed_audio
    
    def extract_basic_features(self, audio_data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        提取基础音频特征
        
        Args:
            audio_data: 音频数据
            
        Returns:
            基础特征字典
        """
        features = {}
        
        # RMS能量
        features['rms_energy'] = librosa.feature.rms(
            y=audio_data,
            frame_length=self.config.frame_length,
            hop_length=self.config.hop_length
        )[0]
        
        # 过零率
        features['zero_crossing_rate'] = librosa.feature.zero_crossing_rate(
            y=audio_data,
            frame_length=self.config.frame_length,
            hop_length=self.config.hop_length
        )[0]
        
        # MFCC特征
        features['mfcc'] = librosa.feature.mfcc(
            y=audio_data,
            sr=self.config.sample_rate,
            n_mfcc=self.config.n_mfcc,
            n_fft=self.config.n_fft,
            hop_length=self.config.hop_length
        )
        
        # 频谱特征
        features['spectral_centroid'] = librosa.feature.spectral_centroid(
            y=audio_data,
            sr=self.config.sample_rate,
            hop_length=self.config.hop_length
        )[0]
        
        features['spectral_rolloff'] = librosa.feature.spectral_rolloff(
            y=audio_data,
            sr=self.config.sample_rate,
            hop_length=self.config.hop_length
        )[0]
        
        features['spectral_bandwidth'] = librosa.feature.spectral_bandwidth(
            y=audio_data,
            sr=self.config.sample_rate,
            hop_length=self.config.hop_length
        )[0]
        
        logger.debug(f"基础特征提取完成 - MFCC形状: {features['mfcc'].shape}")
        return features
    
    def detect_voice_activity(self, audio_data: np.ndarray) -> Tuple[np.ndarray, List[Tuple[float, float]]]:
        """
        语音活动检测(VAD)
        
        Args:
            audio_data: 音频数据
            
        Returns:
            (帧级语音活动, 语音段列表)
        """
        if self.vad_available:
            return self._webrtc_vad(audio_data)
        else:
            return self._energy_based_vad(audio_data)
    
    def _webrtc_vad(self, audio_data: np.ndarray) -> Tuple[np.ndarray, List[Tuple[float, float]]]:
        """基于WebRTC的VAD检测"""
        # 转换为16bit PCM格式
        audio_16bit = (audio_data * 32767).astype(np.int16)
        
        # VAD帧长度(样本数)
        frame_samples = int(self.config.vad_frame_duration * self.config.sample_rate / 1000)
        
        # 确保帧长度是正确的
        if frame_samples not in [160, 320, 480]:  # 10ms, 20ms, 30ms at 16kHz
            frame_samples = 320  # 默认20ms
        
        voice_activity = []
        segments = []
        current_segment_start = None
        
        # 分帧处理
        for i in range(0, len(audio_16bit) - frame_samples + 1, frame_samples):
            frame = audio_16bit[i:i + frame_samples]
            
            # 确保帧长度正确
            if len(frame) == frame_samples:
                try:
                    if self.vad is not None:
                        is_speech = self.vad.is_speech(frame.tobytes(), self.config.sample_rate)
                    else:
                        # 使用简单的能量检测作为备份
                        frame_energy = float(np.mean(frame.astype(float) ** 2))
                        is_speech = frame_energy > 0.01  # 简单阈值
                    voice_activity.append(is_speech)
                    
                    # 检测语音段
                    time_pos = i / self.config.sample_rate
                    if is_speech and current_segment_start is None:
                        current_segment_start = time_pos
                    elif not is_speech and current_segment_start is not None:
                        segments.append((current_segment_start, time_pos))
                        current_segment_start = None
                        
                except Exception as e:
                    logger.warning(f"VAD处理帧失败: {e}")
                    voice_activity.append(False)
        
        # 处理最后一个段
        if current_segment_start is not None:
            segments.append((current_segment_start, len(audio_data) / self.config.sample_rate))
        
        return np.array(voice_activity), segments
    
    def _energy_based_vad(self, audio_data: np.ndarray) -> Tuple[np.ndarray, List[Tuple[float, float]]]:
        """基于能量的VAD检测"""
        # 计算RMS能量
        frame_length = self.config.frame_length
        hop_length = self.config.hop_length
        
        rms_energy = librosa.feature.rms(
            y=audio_data,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        # 动态阈值计算
        energy_mean = np.mean(rms_energy)
        energy_std = np.std(rms_energy)
        threshold = energy_mean + 0.5 * energy_std
        
        # 语音活动检测
        voice_activity = rms_energy > threshold
        
        # 生成语音段
        segments = []
        in_speech = False
        segment_start = 0
        
        for i, is_voice in enumerate(voice_activity):
            time_pos = i * hop_length / self.config.sample_rate
            
            if is_voice and not in_speech:
                segment_start = time_pos
                in_speech = True
            elif not is_voice and in_speech:
                segments.append((segment_start, time_pos))
                in_speech = False
        
        # 处理最后一个段
        if in_speech:
            segments.append((segment_start, len(audio_data) / self.config.sample_rate))
        
        return voice_activity, segments
    
    def detect_speech_boundaries(self, audio_data: np.ndarray, voice_activity: np.ndarray) -> List[float]:
        """
        检测语音边界
        
        Args:
            audio_data: 音频数据
            voice_activity: 语音活动检测结果
            
        Returns:
            语音边界时间点列表
        """
        boundaries = []
        hop_length = self.config.hop_length
        
        # 检测语音活动的变化点
        voice_changes = np.diff(voice_activity.astype(int))
        
        # 找到开始和结束点
        start_points = np.where(voice_changes == 1)[0]  # 静音到语音
        end_points = np.where(voice_changes == -1)[0]   # 语音到静音
        
        # 转换为时间戳
        for point in start_points:
            time_pos = point * hop_length / self.config.sample_rate
            boundaries.append(time_pos)
        
        for point in end_points:
            time_pos = (point + 1) * hop_length / self.config.sample_rate
            boundaries.append(time_pos)
        
        # 排序并去重
        boundaries = sorted(list(set(boundaries)))
        
        logger.debug(f"检测到 {len(boundaries)} 个语音边界点")
        return boundaries
    
    def detect_silence_segments(self, audio_data: np.ndarray, voice_activity: np.ndarray) -> List[Tuple[float, float]]:
        """
        检测静音段
        
        Args:
            audio_data: 音频数据
            voice_activity: 语音活动检测结果
            
        Returns:
            静音段列表 (开始时间, 结束时间)
        """
        silence_segments = []
        hop_length = self.config.hop_length
        
        # 找到静音区域
        silence_activity = ~voice_activity
        
        # 找到连续的静音段
        in_silence = False
        segment_start = 0
        
        for i, is_silence in enumerate(silence_activity):
            time_pos = i * hop_length / self.config.sample_rate
            
            if is_silence and not in_silence:
                segment_start = time_pos
                in_silence = True
            elif not is_silence and in_silence:
                duration = time_pos - segment_start
                if duration >= self.config.min_silence_duration:
                    silence_segments.append((segment_start, time_pos))
                in_silence = False
        
        # 处理最后一个段
        if in_silence:
            time_pos = len(audio_data) / self.config.sample_rate
            duration = time_pos - segment_start
            if duration >= self.config.min_silence_duration:
                silence_segments.append((segment_start, time_pos))
        
        logger.debug(f"检测到 {len(silence_segments)} 个静音段")
        return silence_segments
    
    def extract_features(self, audio_path: Union[str, Path]) -> AudioFeatures:
        """
        提取完整的音频特征
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频特征对象
        """
        logger.info(f"开始提取音频特征: {audio_path}")
        
        # 加载音频
        audio_data, original_sr = self.load_audio(audio_path)
        
        # 预处理
        processed_audio = self.preprocess_audio(audio_data)
        
        # 提取基础特征
        basic_features = self.extract_basic_features(processed_audio)
        
        # VAD检测
        voice_activity, vad_segments = self.detect_voice_activity(processed_audio)
        
        # 边界检测
        speech_boundaries = self.detect_speech_boundaries(processed_audio, voice_activity)
        silence_segments = self.detect_silence_segments(processed_audio, voice_activity)
        
        # 生成时间帧
        frame_count = basic_features['rms_energy'].shape[0]
        time_frames = librosa.frames_to_time(
            np.arange(frame_count),
            sr=self.config.sample_rate,
            hop_length=self.config.hop_length
        )
        
        # 构建特征对象
        features = AudioFeatures(
            duration=len(processed_audio) / self.config.sample_rate,
            sample_rate=self.config.sample_rate,
            frame_count=frame_count,
            rms_energy=basic_features['rms_energy'],
            zero_crossing_rate=basic_features['zero_crossing_rate'],
            mfcc=basic_features['mfcc'],
            spectral_centroid=basic_features['spectral_centroid'],
            spectral_rolloff=basic_features['spectral_rolloff'],
            spectral_bandwidth=basic_features['spectral_bandwidth'],
            vad_segments=vad_segments,
            voice_activity=voice_activity,
            speech_boundaries=speech_boundaries,
            silence_segments=silence_segments,
            time_frames=time_frames
        )
        
        logger.info(f"音频特征提取完成 - 时长: {features.duration:.2f}秒, "
                   f"语音段: {len(features.vad_segments)}个, "
                   f"边界点: {len(features.speech_boundaries)}个")
        
        return features
    
    def get_feature_summary(self, features: AudioFeatures) -> Dict[str, Any]:
        """
        获取特征摘要信息
        
        Args:
            features: 音频特征对象
            
        Returns:
            特征摘要字典
        """
        # 计算语音活动率
        voice_ratio = np.sum(features.voice_activity) / len(features.voice_activity) if len(features.voice_activity) > 0 else 0
        
        # 计算平均特征值
        avg_energy = np.mean(features.rms_energy)
        avg_zcr = np.mean(features.zero_crossing_rate)
        avg_spectral_centroid = np.mean(features.spectral_centroid)
        
        # 计算语音段统计
        speech_durations = [end - start for start, end in features.vad_segments]
        avg_speech_duration = np.mean(speech_durations) if speech_durations else 0
        
        # 计算静音段统计
        silence_durations = [end - start for start, end in features.silence_segments]
        avg_silence_duration = np.mean(silence_durations) if silence_durations else 0
        
        summary = {
            'basic_info': {
                'duration': features.duration,
                'sample_rate': features.sample_rate,
                'frame_count': features.frame_count
            },
            'voice_activity': {
                'voice_ratio': voice_ratio,
                'speech_segments': len(features.vad_segments),
                'silence_segments': len(features.silence_segments),
                'avg_speech_duration': avg_speech_duration,
                'avg_silence_duration': avg_silence_duration
            },
            'audio_features': {
                'avg_rms_energy': avg_energy,
                'avg_zero_crossing_rate': avg_zcr,
                'avg_spectral_centroid': avg_spectral_centroid,
                'mfcc_shape': features.mfcc.shape
            },
            'boundaries': {
                'speech_boundaries': len(features.speech_boundaries),
                'boundary_density': len(features.speech_boundaries) / features.duration if features.duration > 0 else 0
            }
        }
        
        return summary


# 便捷函数
def extract_audio_features(audio_path: Union[str, Path], config: Optional[AudioConfig] = None) -> AudioFeatures:
    """
    提取音频特征的便捷函数
    
    Args:
        audio_path: 音频文件路径
        config: 音频配置
        
    Returns:
        音频特征对象
    """
    extractor = AudioFeatureExtractor(config)
    return extractor.extract_features(audio_path)


def analyze_audio_file(audio_path: Union[str, Path], config: Optional[AudioConfig] = None) -> Dict[str, Any]:
    """
    分析音频文件的便捷函数
    
    Args:
        audio_path: 音频文件路径
        config: 音频配置
        
    Returns:
        音频分析结果
    """
    extractor = AudioFeatureExtractor(config)
    features = extractor.extract_features(audio_path)
    summary = extractor.get_feature_summary(features)
    
    return {
        'features': features,
        'summary': summary
    }


if __name__ == "__main__":
    # 测试音频特征提取器
    print("🎵 音频特征提取器测试")
    print("=" * 60)
    
    # 创建默认配置
    config = AudioConfig()
    print(f"配置信息:")
    print(f"  采样率: {config.sample_rate}Hz")
    print(f"  VAD模式: {config.vad_mode}")
    print(f"  MFCC特征数: {config.n_mfcc}")
    
    # 创建提取器
    extractor = AudioFeatureExtractor(config)
    
    print(f"\n提取器信息:")
    print(f"  VAD可用: {extractor.vad_available}")
    print(f"  配置: {extractor.config}")
    
    # 如果有音频文件，可以测试提取功能
    # 这里只是演示如何使用
    print(f"\n使用示例:")
    print(f"  features = extractor.extract_features('audio.wav')")
    print(f"  summary = extractor.get_feature_summary(features)")
    print(f"  print(f'音频时长: {{features.duration:.2f}}秒')")
    print(f"  print(f'语音段数: {{len(features.vad_segments)}}个')")