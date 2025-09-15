"""
音频测试套件
Phase 3: 智能对齐系统的综合测试组件
创建多种类型的测试音频和字幕，验证系统在真实场景下的性能表现
"""
import os
import json
import time
import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import tempfile
import wave
import warnings
warnings.filterwarnings('ignore')

from .audio_feature_extractor import AudioFeatureExtractor, AudioConfig, extract_audio_features
from .speech_boundary_detector import SpeechBoundaryDetector, BoundaryConfig, detect_speech_boundaries
from .dtw_aligner import DTWAligner, DTWConfig, SubtitleEntry, align_audio_subtitles
from .timestamp_optimizer import TimestampOptimizer, OptimizerConfig, optimize_subtitle_timestamps
from .alignment_validator import AlignmentValidator, ValidationConfig, validate_subtitle_alignment
from .intelligent_alignment_system import IntelligentAlignmentSystem, IntelligentAlignmentConfig

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """测试用例"""
    name: str                           # 测试用例名称
    description: str                    # 描述
    audio_type: str                     # 音频类型: 'synthetic', 'real', 'mixed'
    difficulty: str                     # 难度: 'easy', 'medium', 'hard'
    expected_precision: float           # 期望精度
    expected_quality: float             # 期望质量分数
    test_data: Dict[str, Any]          # 测试数据
    metadata: Dict[str, Any]           # 元数据


@dataclass
class TestResult:
    """测试结果"""
    test_case_name: str                 # 测试用例名称
    success: bool                       # 测试是否成功
    processing_time: float              # 处理时间
    precision_achieved: float           # 实际精度
    quality_score: float                # 质量分数
    performance_metrics: Dict[str, float]  # 性能指标
    validation_passed: bool             # 验证是否通过
    error_message: Optional[str]        # 错误信息
    detailed_metrics: Dict[str, Any]    # 详细指标


class AudioTestSuite:
    """音频测试套件"""
    
    def __init__(self, test_data_dir: Optional[str] = None):
        """
        初始化音频测试套件
        
        Args:
            test_data_dir: 测试数据目录
        """
        self.test_data_dir = test_data_dir or "test_data"
        self.results_dir = "test_results"
        
        # 确保目录存在
        Path(self.test_data_dir).mkdir(exist_ok=True)
        Path(self.results_dir).mkdir(exist_ok=True)
        
        # 初始化测试用例
        self.test_cases = []
        self._create_test_cases()
        
        # 测试统计
        self.test_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'average_quality': 0.0,
            'average_processing_time': 0.0
        }
        
        logger.info(f"音频测试套件初始化完成，测试用例: {len(self.test_cases)}")
    
    def _create_test_cases(self):
        """创建测试用例"""
        
        # 简单测试用例
        self.test_cases.append(TestCase(
            name="simple_clean_speech",
            description="清晰语音，均匀间隔，理想条件",
            audio_type="synthetic",
            difficulty="easy",
            expected_precision=0.05,
            expected_quality=0.9,
            test_data={
                "subtitle_count": 5,
                "duration": 10.0,
                "noise_level": 0.0,
                "speech_rate": "normal",
                "language": "zh-CN"
            },
            metadata={"category": "baseline"}
        ))
        
        # 中等难度测试用例
        self.test_cases.append(TestCase(
            name="noisy_speech",
            description="有噪声的语音，测试噪声环境下的对齐",
            audio_type="synthetic",
            difficulty="medium",
            expected_precision=0.1,
            expected_quality=0.7,
            test_data={
                "subtitle_count": 8,
                "duration": 15.0,
                "noise_level": 0.2,
                "speech_rate": "normal",
                "language": "zh-CN"
            },
            metadata={"category": "noise_robustness"}
        ))
        
        # 快速语音测试
        self.test_cases.append(TestCase(
            name="fast_speech",
            description="快速语音，测试高语速下的对齐精度",
            audio_type="synthetic",
            difficulty="medium",
            expected_precision=0.08,
            expected_quality=0.75,
            test_data={
                "subtitle_count": 12,
                "duration": 15.0,
                "noise_level": 0.1,
                "speech_rate": "fast",
                "language": "zh-CN"
            },
            metadata={"category": "speech_rate"}
        ))
        
        # 不均匀间隔测试
        self.test_cases.append(TestCase(
            name="irregular_timing",
            description="不规则时间间隔，测试复杂时序对齐",
            audio_type="synthetic",
            difficulty="hard",
            expected_precision=0.15,
            expected_quality=0.6,
            test_data={
                "subtitle_count": 10,
                "duration": 20.0,
                "noise_level": 0.15,
                "speech_rate": "variable",
                "irregular_gaps": True,
                "language": "zh-CN"
            },
            metadata={"category": "timing_complexity"}
        ))
        
        # 长音频测试
        self.test_cases.append(TestCase(
            name="long_audio",
            description="长音频文件，测试系统的扩展性",
            audio_type="synthetic",
            difficulty="medium",
            expected_precision=0.12,
            expected_quality=0.7,
            test_data={
                "subtitle_count": 30,
                "duration": 60.0,
                "noise_level": 0.1,
                "speech_rate": "normal",
                "language": "zh-CN"
            },
            metadata={"category": "scalability"}
        ))
        
        # 多语言测试 (如果支持)
        self.test_cases.append(TestCase(
            name="multilingual_test",
            description="多语言混合，测试语言无关性",
            audio_type="synthetic",
            difficulty="hard",
            expected_precision=0.2,
            expected_quality=0.65,
            test_data={
                "subtitle_count": 6,
                "duration": 12.0,
                "noise_level": 0.1,
                "speech_rate": "normal",
                "languages": ["zh-CN", "en-US"]
            },
            metadata={"category": "multilingual"}
        ))
    
    def generate_synthetic_audio(self, test_case: TestCase) -> Tuple[str, List[SubtitleEntry]]:
        """
        生成合成音频和对应字幕
        
        Args:
            test_case: 测试用例
            
        Returns:
            (音频文件路径, 字幕列表)
        """
        data = test_case.test_data
        
        # 生成基础参数
        sample_rate = 16000
        duration = data['duration']
        subtitle_count = data['subtitle_count']
        noise_level = data.get('noise_level', 0.0)
        
        # 创建音频信号
        total_samples = int(sample_rate * duration)
        audio_signal = np.zeros(total_samples)
        
        # 生成字幕时间戳
        subtitles = self._generate_subtitle_timestamps(test_case)
        
        # 为每个字幕段生成语音信号
        for i, subtitle in enumerate(subtitles):
            start_sample = int(subtitle.start_time * sample_rate)
            end_sample = int(subtitle.end_time * sample_rate)
            
            if end_sample <= total_samples:
                # 生成语音信号（使用正弦波模拟）
                segment_length = end_sample - start_sample
                
                # 基频随字幕变化
                base_freq = 200 + (i % 5) * 50  # 200-400Hz范围
                
                # 生成语音段
                t = np.linspace(0, segment_length / sample_rate, segment_length)
                
                # 基础音调
                speech_signal = np.sin(2 * np.pi * base_freq * t)
                
                # 添加谐波使其更像语音
                speech_signal += 0.3 * np.sin(2 * np.pi * base_freq * 2 * t)
                speech_signal += 0.1 * np.sin(2 * np.pi * base_freq * 3 * t)
                
                # 添加包络
                envelope = np.exp(-t * 0.5) * (1 - np.exp(-t * 10))
                speech_signal *= envelope
                
                # 添加语音变化
                modulation = 1 + 0.2 * np.sin(2 * np.pi * 10 * t)  # 10Hz调制
                speech_signal *= modulation
                
                # 归一化
                if np.max(np.abs(speech_signal)) > 0:
                    speech_signal = speech_signal / np.max(np.abs(speech_signal)) * 0.7
                
                # 添加到主信号
                audio_signal[start_sample:end_sample] = speech_signal
        
        # 添加噪声
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, total_samples)
            audio_signal += noise
        
        # 归一化最终信号
        if np.max(np.abs(audio_signal)) > 0:
            audio_signal = audio_signal / np.max(np.abs(audio_signal)) * 0.8
        
        # 保存音频文件
        audio_path = os.path.join(self.test_data_dir, f"{test_case.name}.wav")
        self._save_wav_file(audio_signal, sample_rate, audio_path)
        
        return audio_path, subtitles
    
    def _generate_subtitle_timestamps(self, test_case: TestCase) -> List[SubtitleEntry]:
        """生成字幕时间戳"""
        data = test_case.test_data
        subtitle_count = data['subtitle_count']
        duration = data['duration']
        
        subtitles = []
        
        if data.get('irregular_gaps', False):
            # 不规则间隔
            timestamps = []
            current_time = 1.0
            
            for i in range(subtitle_count):
                # 随机间隔 0.5-3.0秒
                gap = np.random.uniform(0.5, 3.0)
                subtitle_duration = np.random.uniform(1.0, 2.5)
                
                start_time = current_time
                end_time = min(current_time + subtitle_duration, duration - 0.5)
                
                if end_time > start_time:
                    subtitle = SubtitleEntry(
                        text=f"测试字幕 {i+1}",
                        start_time=start_time,
                        end_time=end_time,
                        confidence=1.0
                    )
                    subtitles.append(subtitle)
                
                current_time = end_time + gap
                if current_time >= duration - 1.0:
                    break
        else:
            # 规则间隔
            avg_duration = duration / subtitle_count * 0.7  # 70%用于语音
            avg_gap = duration / subtitle_count * 0.3       # 30%用于间隔
            
            current_time = 0.5
            for i in range(subtitle_count):
                start_time = current_time
                end_time = start_time + avg_duration
                
                if end_time >= duration:
                    break
                
                subtitle = SubtitleEntry(
                    text=f"测试字幕 {i+1}",
                    start_time=start_time,
                    end_time=end_time,
                    confidence=1.0
                )
                subtitles.append(subtitle)
                
                current_time = end_time + avg_gap
        
        return subtitles
    
    def _save_wav_file(self, audio_data: np.ndarray, sample_rate: int, file_path: str):
        """保存WAV文件"""
        # 转换为16位整数
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(file_path, 'w') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
    
    def run_single_test(self, test_case: TestCase,
                       progress_callback: Optional[Callable[[str], None]] = None) -> TestResult:
        """
        运行单个测试用例
        
        Args:
            test_case: 测试用例
            progress_callback: 进度回调
            
        Returns:
            测试结果
        """
        if progress_callback:
            progress_callback(f"开始测试: {test_case.name}")
        
        start_time = time.time()
        
        try:
            # 生成测试数据
            if progress_callback:
                progress_callback("生成测试音频和字幕")
            
            audio_path, original_subtitles = self.generate_synthetic_audio(test_case)
            
            # 创建扰动的字幕作为输入 (模拟不准确的时间戳)
            disturbed_subtitles = self._create_disturbed_subtitles(original_subtitles, test_case)
            
            # 创建智能对齐系统
            if progress_callback:
                progress_callback("初始化智能对齐系统")
            
            config = IntelligentAlignmentConfig()
            system = IntelligentAlignmentSystem(config)
            
            # 执行对齐
            if progress_callback:
                progress_callback("执行智能对齐")
            
            aligned_subtitles, alignment_report = system.align_subtitles(
                audio_path, disturbed_subtitles
            )
            
            processing_time = time.time() - start_time
            
            # 验证结果
            if progress_callback:
                progress_callback("验证对齐结果")
            
            validator = AlignmentValidator()
            validation_metrics = validator.validate_alignment(
                aligned_subtitles, original_subtitles
            )
            
            # 计算性能指标
            performance_metrics = self._calculate_performance_metrics(
                original_subtitles, aligned_subtitles, processing_time
            )
            
            # 创建测试结果
            result = TestResult(
                test_case_name=test_case.name,
                success=True,
                processing_time=processing_time,
                precision_achieved=performance_metrics['precision'],
                quality_score=validation_metrics.overall_quality_score,
                performance_metrics=performance_metrics,
                validation_passed=validation_metrics.validation_passed,
                error_message=None,
                detailed_metrics={
                    'alignment_report': asdict(alignment_report),
                    'validation_metrics': asdict(validation_metrics)
                }
            )
            
            if progress_callback:
                progress_callback(f"测试完成: {test_case.name}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"测试 {test_case.name} 失败: {error_msg}")
            
            result = TestResult(
                test_case_name=test_case.name,
                success=False,
                processing_time=processing_time,
                precision_achieved=0.0,
                quality_score=0.0,
                performance_metrics={},
                validation_passed=False,
                error_message=error_msg,
                detailed_metrics={}
            )
            
            if progress_callback:
                progress_callback(f"测试失败: {test_case.name} - {error_msg}")
            
            return result
    
    def _create_disturbed_subtitles(self, original_subtitles: List[SubtitleEntry], 
                                  test_case: TestCase) -> List[SubtitleEntry]:
        """创建扰动的字幕时间戳"""
        disturbed = []
        
        # 根据难度等级设置扰动程度
        if test_case.difficulty == "easy":
            noise_level = 0.05  # ±50ms
        elif test_case.difficulty == "medium":
            noise_level = 0.15  # ±150ms
        else:  # hard
            noise_level = 0.3   # ±300ms
        
        for subtitle in original_subtitles:
            # 添加随机时间偏移
            offset = np.random.normal(0, noise_level)
            
            disturbed_subtitle = SubtitleEntry(
                text=subtitle.text,
                start_time=max(0, subtitle.start_time + offset),
                end_time=max(subtitle.start_time + 0.5, subtitle.end_time + offset),
                confidence=subtitle.confidence,
                metadata={'original_time': subtitle.start_time, 'disturbed': True}
            )
            disturbed.append(disturbed_subtitle)
        
        return disturbed
    
    def _calculate_performance_metrics(self, original_subtitles: List[SubtitleEntry],
                                     aligned_subtitles: List[SubtitleEntry],
                                     processing_time: float) -> Dict[str, float]:
        """计算性能指标"""
        if not original_subtitles or not aligned_subtitles:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'speed': 0.0}
        
        # 计算时间戳精度
        time_errors = []
        for orig, aligned in zip(original_subtitles, aligned_subtitles):
            error = abs(aligned.start_time - orig.start_time)
            time_errors.append(error)
        
        precision = 1.0 / (1.0 + np.mean(time_errors)) if time_errors else 0.0
        
        # 计算处理速度 (音频时长/处理时间)
        if original_subtitles:
            audio_duration = max(s.end_time for s in original_subtitles)
            speed = audio_duration / processing_time if processing_time > 0 else 0
        else:
            speed = 0
        
        return {
            'precision': precision,
            'mean_error': np.mean(time_errors) if time_errors else 0,
            'max_error': np.max(time_errors) if time_errors else 0,
            'std_error': np.std(time_errors) if time_errors else 0,
            'speed_ratio': speed,
            'processing_time': processing_time
        }
    
    def run_all_tests(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> List[TestResult]:
        """
        运行所有测试用例
        
        Args:
            progress_callback: 进度回调 (progress, message)
            
        Returns:
            测试结果列表
        """
        logger.info(f"开始运行 {len(self.test_cases)} 个测试用例")
        
        results = []
        total_tests = len(self.test_cases)
        
        for i, test_case in enumerate(self.test_cases):
            if progress_callback:
                progress = i / total_tests
                progress_callback(progress, f"运行测试: {test_case.name}")
            
            def single_progress(msg):
                if progress_callback:
                    progress_callback(i / total_tests, msg)
            
            result = self.run_single_test(test_case, single_progress)
            results.append(result)
            
            # 更新统计
            self._update_test_stats(result)
        
        if progress_callback:
            progress_callback(1.0, "所有测试完成")
        
        # 保存测试报告
        self._save_test_report(results)
        
        logger.info(f"测试套件完成，通过率: {self.test_stats['passed_tests']}/{self.test_stats['total_tests']}")
        return results
    
    def _update_test_stats(self, result: TestResult):
        """更新测试统计"""
        self.test_stats['total_tests'] += 1
        
        if result.success and result.validation_passed:
            self.test_stats['passed_tests'] += 1
        else:
            self.test_stats['failed_tests'] += 1
        
        # 更新平均质量
        total = self.test_stats['total_tests']
        prev_avg_quality = self.test_stats['average_quality']
        self.test_stats['average_quality'] = (
            prev_avg_quality * (total - 1) + result.quality_score
        ) / total
        
        # 更新平均处理时间
        prev_avg_time = self.test_stats['average_processing_time']
        self.test_stats['average_processing_time'] = (
            prev_avg_time * (total - 1) + result.processing_time
        ) / total
    
    def _save_test_report(self, results: List[TestResult]):
        """保存测试报告"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'statistics': self.test_stats,
            'test_results': [asdict(result) for result in results],
            'summary': self._generate_test_summary(results)
        }
        
        report_path = os.path.join(self.results_dir, 'test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试报告已保存: {report_path}")
    
    def _generate_test_summary(self, results: List[TestResult]) -> Dict[str, Any]:
        """生成测试摘要"""
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {'error': 'No successful tests'}
        
        # 按难度分组统计
        difficulty_stats = {}
        for test_case in self.test_cases:
            difficulty = test_case.difficulty
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {'total': 0, 'passed': 0}
            
            difficulty_stats[difficulty]['total'] += 1
            
            # 查找对应结果
            result = next((r for r in results if r.test_case_name == test_case.name), None)
            if result and result.success and result.validation_passed:
                difficulty_stats[difficulty]['passed'] += 1
        
        return {
            'total_tests': len(results),
            'passed_tests': len([r for r in results if r.success and r.validation_passed]),
            'average_quality': np.mean([r.quality_score for r in successful_results]),
            'average_precision': np.mean([r.precision_achieved for r in successful_results]),
            'average_processing_time': np.mean([r.processing_time for r in results]),
            'difficulty_breakdown': difficulty_stats,
            'performance_range': {
                'best_quality': max([r.quality_score for r in successful_results]),
                'worst_quality': min([r.quality_score for r in successful_results]),
                'fastest_processing': min([r.processing_time for r in results]),
                'slowest_processing': max([r.processing_time for r in results])
            }
        }
    
    def get_test_stats(self) -> Dict[str, Any]:
        """获取测试统计信息"""
        return {
            **self.test_stats,
            'test_cases': len(self.test_cases),
            'pass_rate': (self.test_stats['passed_tests'] / 
                         self.test_stats['total_tests']) if self.test_stats['total_tests'] > 0 else 0
        }


# 便捷函数
def run_audio_test_suite(test_data_dir: Optional[str] = None,
                        progress_callback: Optional[Callable[[float, str], None]] = None) -> List[TestResult]:
    """
    运行音频测试套件的便捷函数
    
    Args:
        test_data_dir: 测试数据目录
        progress_callback: 进度回调
        
    Returns:
        测试结果列表
    """
    suite = AudioTestSuite(test_data_dir)
    return suite.run_all_tests(progress_callback)


if __name__ == "__main__":
    # 测试音频测试套件
    print("🎯 音频测试套件")
    print("=" * 60)
    
    # 创建测试套件
    suite = AudioTestSuite("temp_test_data")
    
    print(f"测试套件信息:")
    print(f"  测试用例数量: {len(suite.test_cases)}")
    print(f"  测试数据目录: {suite.test_data_dir}")
    print(f"  结果目录: {suite.results_dir}")
    
    print(f"\n测试用例列表:")
    for i, case in enumerate(suite.test_cases):
        print(f"  {i+1}. {case.name} ({case.difficulty}) - {case.description}")
    
    # 运行单个简单测试
    simple_case = suite.test_cases[0]  # simple_clean_speech
    print(f"\n运行单个测试: {simple_case.name}")
    
    def progress_callback(msg):
        print(f"  进度: {msg}")
    
    result = suite.run_single_test(simple_case, progress_callback)
    
    print(f"\n测试结果:")
    print(f"  成功: {result.success}")
    print(f"  处理时间: {result.processing_time:.3f}s")
    print(f"  质量分数: {result.quality_score:.3f}")
    print(f"  验证通过: {result.validation_passed}")
    
    if result.error_message:
        print(f"  错误信息: {result.error_message}")
    
    stats = suite.get_test_stats()
    print(f"\n测试统计:")
    print(f"  总测试数: {stats['total_tests']}")
    print(f"  通过数: {stats['passed_tests']}")
    print(f"  通过率: {stats['pass_rate']:.1%}")
    
    print(f"\n✅ 音频测试套件准备完成!")
    print(f"使用示例:")
    print(f"  results = suite.run_all_tests()")
    print(f"  print(f'通过率: {{stats['pass_rate']:.1%}}')")