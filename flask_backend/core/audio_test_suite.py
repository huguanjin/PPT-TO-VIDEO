"""
音频测试套件
为性能基准测试提供测试数据和测试用例
"""
import os
import numpy as np
import tempfile
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import wave
from pathlib import Path

@dataclass
class TestCase:
    """测试用例数据结构"""
    name: str
    test_data: Dict[str, Any]
    expected_results: Dict[str, Any] = None

class AudioTestSuite:
    """音频测试套件"""
    
    def __init__(self):
        """初始化测试套件"""
        self.test_cases = [
            TestCase(
                name="simple_case",
                test_data={
                    "duration": 30.0,
                    "subtitle_count": 10,
                    "sample_rate": 16000,
                    "complexity": "simple"
                }
            ),
            TestCase(
                name="medium_case", 
                test_data={
                    "duration": 60.0,
                    "subtitle_count": 20,
                    "sample_rate": 16000,
                    "complexity": "medium"
                }
            ),
            TestCase(
                name="complex_case",
                test_data={
                    "duration": 120.0,
                    "subtitle_count": 40,
                    "sample_rate": 16000,
                    "complexity": "complex"
                }
            )
        ]
    
    def generate_synthetic_audio(self, test_case: TestCase) -> Tuple[str, List[Dict[str, Any]]]:
        """生成合成音频和对应的字幕"""
        duration = test_case.test_data.get("duration", 30.0)
        subtitle_count = test_case.test_data.get("subtitle_count", 10)
        sample_rate = test_case.test_data.get("sample_rate", 16000)
        
        # 生成合成音频数据
        audio_data = self._generate_audio_signal(duration, sample_rate)
        
        # 保存为临时音频文件
        audio_path = self._save_temp_audio(audio_data, sample_rate)
        
        # 生成对应的字幕
        subtitles = self._generate_subtitles(duration, subtitle_count)
        
        return audio_path, subtitles
    
    def _generate_audio_signal(self, duration: float, sample_rate: int) -> np.ndarray:
        """生成音频信号"""
        # 生成时间轴
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # 生成混合信号（正弦波 + 白噪声）
        # 主要频率在语音范围内 (100-4000 Hz)
        frequencies = [200, 400, 800, 1600]
        signal = np.zeros_like(t)
        
        for freq in frequencies:
            signal += 0.2 * np.sin(2 * np.pi * freq * t)
        
        # 添加白噪声
        noise = 0.1 * np.random.random(len(t))
        signal += noise
        
        # 添加包络（模拟语音的幅度变化）
        envelope = 0.5 * (1 + np.sin(2 * np.pi * 0.5 * t))
        signal *= envelope
        
        # 归一化到16位PCM范围
        signal = signal / np.max(np.abs(signal))
        signal = (signal * 32767).astype(np.int16)
        
        return signal
    
    def _save_temp_audio(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """保存音频到临时文件"""
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_path = temp_file.name
        temp_file.close()
        
        # 写入WAV文件
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_path
    
    def _generate_subtitles(self, duration: float, subtitle_count: int) -> List[Dict[str, Any]]:
        """生成测试字幕"""
        subtitles = []
        
        # 计算每个字幕的平均持续时间
        avg_duration = duration / subtitle_count
        
        for i in range(subtitle_count):
            start_time = i * avg_duration
            end_time = min(start_time + avg_duration, duration)
            
            subtitle = {
                "start_time": start_time,
                "end_time": end_time,
                "text": f"测试字幕内容 {i + 1}，这是一段用于性能测试的文本。",
                "index": i + 1
            }
            subtitles.append(subtitle)
        
        return subtitles
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        # 这个方法可以在测试完成后调用来清理临时音频文件
        # 由于使用了tempfile.NamedTemporaryFile，文件会在适当时候自动清理
        pass