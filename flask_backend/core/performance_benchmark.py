"""
性能基准测试与优化模块
Phase 3: 智能对齐系统的性能评估组件
测试大文件处理能力、内存使用优化、处理速度基准，并优化瓶颈
"""
import os
import time
import psutil
import threading
import gc
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict, field
import logging
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

try:
    # 尝试相对导入
    from .audio_feature_extractor import AudioFeatureExtractor, AudioConfig
    from .speech_boundary_detector import SpeechBoundaryDetector, BoundaryConfig
    from .dtw_aligner import DTWAligner, DTWConfig, SubtitleEntry
    from .timestamp_optimizer import TimestampOptimizer, OptimizerConfig
    from .alignment_validator import AlignmentValidator, ValidationConfig
    from .intelligent_alignment_system import IntelligentAlignmentSystem, IntelligentAlignmentConfig
    from .audio_test_suite import AudioTestSuite
except ImportError:
    # 如果失败，使用绝对导入
    from audio_feature_extractor import AudioFeatureExtractor, AudioConfig
    from speech_boundary_detector import SpeechBoundaryDetector, BoundaryConfig
    from dtw_aligner import DTWAligner, DTWConfig, SubtitleEntry
    from timestamp_optimizer import TimestampOptimizer, OptimizerConfig
    from alignment_validator import AlignmentValidator, ValidationConfig
    from intelligent_alignment_system import IntelligentAlignmentSystem, IntelligentAlignmentConfig
    from audio_test_suite import AudioTestSuite

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    # 测试规模
    audio_durations: List[float] = field(default_factory=lambda: [10, 30, 60, 120, 300, 600])  # 音频时长列表(秒)
    subtitle_counts: List[int] = field(default_factory=lambda: [5, 15, 30, 60, 150, 300])      # 字幕数量列表
    
    # 性能指标
    target_speed_ratio: float = 5.0          # 目标速度比(音频时长/处理时间)
    max_memory_mb: float = 1000.0            # 最大内存使用(MB)
    target_precision: float = 0.1            # 目标精度(秒)
    
    # 测试选项
    test_memory_leak: bool = True            # 测试内存泄漏
    test_concurrent: bool = True             # 测试并发处理
    test_large_files: bool = True            # 测试大文件
    
    # 优化选项
    enable_profiling: bool = True            # 启用性能分析
    enable_optimization: bool = True         # 启用自动优化


@dataclass
class PerformanceMetrics:
    """性能指标"""
    # 基础指标
    processing_time: float                   # 处理时间(秒)
    memory_peak: float                       # 内存峰值(MB)
    memory_final: float                      # 最终内存(MB)
    cpu_usage: float                         # CPU使用率(%)
    
    # 速度指标
    speed_ratio: float                       # 速度比(音频时长/处理时间)
    throughput: float                        # 吞吐量(字幕/秒)
    
    # 质量指标
    precision: float                         # 精度
    quality_score: float                     # 质量分数
    
    # 效率指标
    memory_efficiency: float                 # 内存效率(MB/分钟音频)
    cpu_efficiency: float                    # CPU效率(CPU%/速度比)
    
    # 详细信息
    audio_duration: float                    # 音频时长
    subtitle_count: int                      # 字幕数量
    error_occurred: bool                     # 是否出错
    error_message: str = ""                  # 错误信息


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    config: BenchmarkConfig                  # 测试配置
    metrics_list: List[PerformanceMetrics]   # 性能指标列表
    summary: Dict[str, float]                # 摘要统计
    bottlenecks: List[str]                   # 性能瓶颈
    recommendations: List[str]               # 优化建议
    timestamp: str                           # 测试时间戳


class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """
        初始化性能基准测试器
        
        Args:
            config: 基准测试配置
        """
        self.config = config or BenchmarkConfig()
        
        # 性能监控
        self.process = psutil.Process()
        self.monitoring_active = False
        self.monitoring_data = []
        
        # 测试结果存储
        self.results_dir = "benchmark_results"
        Path(self.results_dir).mkdir(exist_ok=True)
        
        logger.info("性能基准测试器初始化完成")
    
    def run_benchmark(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> BenchmarkResult:
        """
        运行完整的基准测试
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            基准测试结果
        """
        logger.info("开始性能基准测试")
        
        if progress_callback:
            progress_callback(0.0, "初始化基准测试")
        
        metrics_list = []
        total_tests = len(self.config.audio_durations)
        
        # 创建测试套件
        test_suite = AudioTestSuite()
        
        for i, (duration, subtitle_count) in enumerate(zip(
            self.config.audio_durations, 
            self.config.subtitle_counts
        )):
            if progress_callback:
                progress = i / total_tests
                progress_callback(progress, f"测试 {duration}s 音频, {subtitle_count} 字幕")
            
            # 运行单次性能测试
            metrics = self._run_single_benchmark(
                duration, subtitle_count, test_suite
            )
            metrics_list.append(metrics)
            
            # 强制垃圾回收
            gc.collect()
        
        if progress_callback:
            progress_callback(0.9, "分析测试结果")
        
        # 分析结果
        summary = self._analyze_results(metrics_list)
        bottlenecks = self._identify_bottlenecks(metrics_list)
        recommendations = self._generate_recommendations(metrics_list, bottlenecks)
        
        # 创建基准测试结果
        result = BenchmarkResult(
            config=self.config,
            metrics_list=metrics_list,
            summary=summary,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 保存结果
        self._save_benchmark_result(result)
        
        if progress_callback:
            progress_callback(1.0, "基准测试完成")
        
        logger.info(f"基准测试完成，平均速度比: {summary.get('avg_speed_ratio', 0):.2f}")
        return result
    
    def _run_single_benchmark(self, audio_duration: float, 
                            subtitle_count: int,
                            test_suite: AudioTestSuite) -> PerformanceMetrics:
        """运行单次基准测试"""
        
        # 创建测试数据
        test_case = test_suite.test_cases[0]  # 使用简单测试用例作为模板
        test_case.test_data['duration'] = audio_duration
        test_case.test_data['subtitle_count'] = subtitle_count
        
        # 记录初始内存
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()
        
        # 开始性能监控
        self._start_monitoring()
        
        try:
            # 生成测试音频和字幕
            audio_path, subtitles = test_suite.generate_synthetic_audio(test_case)
            
            # 创建智能对齐系统
            config = IntelligentAlignmentConfig()
            system = IntelligentAlignmentSystem(config)
            
            # 执行对齐处理
            aligned_subtitles, alignment_report = system.align_subtitles(
                audio_path, subtitles
            )
            
            # 记录处理完成时间
            processing_time = time.time() - start_time
            
            # 验证结果质量
            validator = AlignmentValidator()
            validation_metrics = validator.validate_alignment(aligned_subtitles, subtitles)
            
            # 停止监控
            self._stop_monitoring()
            
            # 计算性能指标
            final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_peak = max([data['memory'] for data in self.monitoring_data]) if self.monitoring_data else final_memory
            avg_cpu = np.mean([data['cpu'] for data in self.monitoring_data]) if self.monitoring_data else 0
            
            # 计算派生指标
            speed_ratio = audio_duration / processing_time if processing_time > 0 else 0
            throughput = subtitle_count / processing_time if processing_time > 0 else 0
            memory_efficiency = memory_peak / (audio_duration / 60) if audio_duration > 0 else 0  # MB/分钟
            cpu_efficiency = avg_cpu / speed_ratio if speed_ratio > 0 else 0
            
            metrics = PerformanceMetrics(
                processing_time=processing_time,
                memory_peak=memory_peak,
                memory_final=final_memory,
                cpu_usage=float(avg_cpu),  # 转换numpy类型为float
                speed_ratio=speed_ratio,
                throughput=throughput,
                precision=1.0 - validation_metrics.mean_precision_error,
                quality_score=validation_metrics.overall_quality_score,
                memory_efficiency=memory_efficiency,
                cpu_efficiency=float(cpu_efficiency),  # 转换numpy类型为float
                audio_duration=audio_duration,
                subtitle_count=subtitle_count,
                error_occurred=False
            )
            
            # 清理测试文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return metrics
            
        except Exception as e:
            self._stop_monitoring()
            
            processing_time = time.time() - start_time
            final_memory = self.process.memory_info().rss / 1024 / 1024
            
            logger.error(f"基准测试失败 (时长{audio_duration}s): {e}")
            
            return PerformanceMetrics(
                processing_time=processing_time,
                memory_peak=final_memory,
                memory_final=final_memory,
                cpu_usage=0,
                speed_ratio=0,
                throughput=0,
                precision=0,
                quality_score=0,
                memory_efficiency=0,
                cpu_efficiency=0,
                audio_duration=audio_duration,
                subtitle_count=subtitle_count,
                error_occurred=True,
                error_message=str(e)
            )
    
    def _start_monitoring(self):
        """开始性能监控"""
        self.monitoring_active = True
        self.monitoring_data = []
        
        def monitor():
            while self.monitoring_active:
                try:
                    memory = self.process.memory_info().rss / 1024 / 1024  # MB
                    cpu = self.process.cpu_percent()
                    
                    self.monitoring_data.append({
                        'timestamp': time.time(),
                        'memory': memory,
                        'cpu': cpu
                    })
                    
                    time.sleep(0.1)  # 每100ms采样一次
                except:
                    break
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def _stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1.0)
    
    def _analyze_results(self, metrics_list: List[PerformanceMetrics]) -> Dict[str, Any]:
        """分析测试结果"""
        successful_metrics = [m for m in metrics_list if not m.error_occurred]
        
        if not successful_metrics:
            return {'error': 'No successful tests'}
        
        summary = {
            'total_tests': len(metrics_list),
            'successful_tests': len(successful_metrics),
            'success_rate': len(successful_metrics) / len(metrics_list),
            
            # 速度统计
            'avg_speed_ratio': float(np.mean([m.speed_ratio for m in successful_metrics])),
            'min_speed_ratio': float(np.min([m.speed_ratio for m in successful_metrics])),
            'max_speed_ratio': float(np.max([m.speed_ratio for m in successful_metrics])),
            
            # 内存统计
            'avg_memory_peak': float(np.mean([m.memory_peak for m in successful_metrics])),
            'max_memory_peak': float(np.max([m.memory_peak for m in successful_metrics])),
            'avg_memory_efficiency': float(np.mean([m.memory_efficiency for m in successful_metrics])),
            
            # 质量统计
            'avg_quality_score': float(np.mean([m.quality_score for m in successful_metrics])),
            'avg_precision': float(np.mean([m.precision for m in successful_metrics])),
            
            # CPU统计
            'avg_cpu_usage': float(np.mean([m.cpu_usage for m in successful_metrics])),
            'avg_cpu_efficiency': float(np.mean([m.cpu_efficiency for m in successful_metrics])),
            
            # 吞吐量统计
            'avg_throughput': float(np.mean([m.throughput for m in successful_metrics])),
            'max_throughput': float(np.max([m.throughput for m in successful_metrics])),
        }
        
        return summary
    
    def _identify_bottlenecks(self, metrics_list: List[PerformanceMetrics]) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []
        successful_metrics = [m for m in metrics_list if not m.error_occurred]
        
        if not successful_metrics:
            return ["所有测试都失败了"]
        
        # 速度瓶颈
        avg_speed = np.mean([m.speed_ratio for m in successful_metrics])
        if avg_speed < self.config.target_speed_ratio:
            bottlenecks.append(
                f"处理速度低于目标 ({avg_speed:.2f} < {self.config.target_speed_ratio})"
            )
        
        # 内存瓶颈
        max_memory = np.max([m.memory_peak for m in successful_metrics])
        if max_memory > self.config.max_memory_mb:
            bottlenecks.append(
                f"内存使用超出限制 ({max_memory:.1f}MB > {self.config.max_memory_mb}MB)"
            )
        
        # 精度瓶颈
        avg_precision = np.mean([m.precision for m in successful_metrics])
        if avg_precision < (1.0 - self.config.target_precision):
            bottlenecks.append(
                f"精度不满足要求 (误差 > {self.config.target_precision}s)"
            )
        
        # CPU效率瓶颈
        cpu_usages = [m.cpu_usage for m in successful_metrics]
        if np.max(cpu_usages) > 80:
            bottlenecks.append("CPU使用率过高 (>80%)")
        
        # 扩展性瓶颈
        if len(successful_metrics) > 3:
            # 检查处理时间是否与音频长度成比例
            durations = [m.audio_duration for m in successful_metrics]
            processing_times = [m.processing_time for m in successful_metrics]
            
            # 计算相关性
            correlation = np.corrcoef(durations, processing_times)[0, 1]
            if correlation > 0.9:  # 高度相关说明可能存在线性扩展问题
                growth_rate = np.polyfit(durations, processing_times, 1)[0]
                if growth_rate > 0.5:  # 处理时间增长过快
                    bottlenecks.append("处理时间增长过快，可能存在算法复杂度问题")
        
        return bottlenecks
    
    def _generate_recommendations(self, metrics_list: List[PerformanceMetrics], 
                                bottlenecks: List[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        successful_metrics = [m for m in metrics_list if not m.error_occurred]
        
        if not successful_metrics:
            recommendations.append("需要修复基础错误，确保系统能正常运行")
            return recommendations
        
        # 基于瓶颈的建议
        for bottleneck in bottlenecks:
            if "处理速度" in bottleneck:
                recommendations.append(
                    "建议优化算法实现，考虑使用更高效的DTW实现或减少特征维度"
                )
            elif "内存使用" in bottleneck:
                recommendations.append(
                    "建议实现流式处理，分批处理大文件，或优化内存分配策略"
                )
            elif "精度不满足" in bottleneck:
                recommendations.append(
                    "建议调整DTW参数，增加音频特征权重，或改进边界检测算法"
                )
            elif "CPU使用率" in bottleneck:
                recommendations.append(
                    "建议优化计算密集型操作，考虑并行化处理或使用更高效的数值计算库"
                )
            elif "处理时间增长" in bottleneck:
                recommendations.append(
                    "建议重新设计算法架构，考虑O(n log n)或O(n)复杂度的算法"
                )
        
        # 通用优化建议
        avg_memory_efficiency = np.mean([m.memory_efficiency for m in successful_metrics])
        if avg_memory_efficiency > 100:  # 每分钟音频使用超过100MB
            recommendations.append(
                "内存效率较低，建议实现内存池或对象重用机制"
            )
        
        avg_cpu_efficiency = np.mean([m.cpu_efficiency for m in successful_metrics])
        if avg_cpu_efficiency > 20:  # CPU效率指标过高
            recommendations.append(
                "CPU效率较低，建议优化算法或使用硬件加速"
            )
        
        # 质量相关建议
        avg_quality = np.mean([m.quality_score for m in successful_metrics])
        if avg_quality < 0.8:
            recommendations.append(
                "对齐质量有待改进，建议调优配置参数或改进特征提取"
            )
        
        if not recommendations:
            recommendations.append("性能表现良好，继续保持当前配置")
        
        return recommendations
    
    def _save_benchmark_result(self, result: BenchmarkResult):
        """保存基准测试结果"""
        # 保存JSON格式结果
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        json_path = os.path.join(self.results_dir, f'benchmark_{timestamp}.json')
        
        # 转换为可序列化的格式
        serializable_result = {
            'config': asdict(result.config),
            'metrics_list': [asdict(m) for m in result.metrics_list],
            'summary': result.summary,
            'bottlenecks': result.bottlenecks,
            'recommendations': result.recommendations,
            'timestamp': result.timestamp
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        # 生成性能图表
        self._generate_performance_charts(result, timestamp)
        
        logger.info(f"基准测试结果已保存: {json_path}")
    
    def _generate_performance_charts(self, result: BenchmarkResult, timestamp: str):
        """生成性能图表"""
        try:
            successful_metrics = [m for m in result.metrics_list if not m.error_occurred]
            
            if not successful_metrics:
                return
            
            # 创建图表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            durations = [m.audio_duration for m in successful_metrics]
            
            # 处理速度图
            speed_ratios = [m.speed_ratio for m in successful_metrics]
            ax1.plot(durations, speed_ratios, 'b-o')
            ax1.axhline(y=self.config.target_speed_ratio, color='r', linestyle='--', label='目标')
            ax1.set_xlabel('音频时长 (秒)')
            ax1.set_ylabel('速度比')
            ax1.set_title('处理速度性能')
            ax1.legend()
            ax1.grid(True)
            
            # 内存使用图
            memory_peaks = [m.memory_peak for m in successful_metrics]
            ax2.plot(durations, memory_peaks, 'g-o')
            ax2.axhline(y=self.config.max_memory_mb, color='r', linestyle='--', label='限制')
            ax2.set_xlabel('音频时长 (秒)')
            ax2.set_ylabel('内存峰值 (MB)')
            ax2.set_title('内存使用')
            ax2.legend()
            ax2.grid(True)
            
            # 质量分数图
            quality_scores = [m.quality_score for m in successful_metrics]
            ax3.plot(durations, quality_scores, 'm-o')
            ax3.set_xlabel('音频时长 (秒)')
            ax3.set_ylabel('质量分数')
            ax3.set_title('对齐质量')
            ax3.grid(True)
            
            # CPU使用率图
            cpu_usages = [m.cpu_usage for m in successful_metrics]
            ax4.plot(durations, cpu_usages, 'c-o')
            ax4.set_xlabel('音频时长 (秒)')
            ax4.set_ylabel('CPU使用率 (%)')
            ax4.set_title('CPU使用')
            ax4.grid(True)
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = os.path.join(self.results_dir, f'performance_chart_{timestamp}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"性能图表已保存: {chart_path}")
            
        except Exception as e:
            logger.warning(f"生成性能图表失败: {e}")
    
    def test_memory_leak(self, iterations: int = 10) -> Dict[str, Any]:
        """测试内存泄漏"""
        logger.info(f"开始内存泄漏测试，迭代次数: {iterations}")
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        memory_samples = [initial_memory]
        
        test_suite = AudioTestSuite()
        test_case = test_suite.test_cases[0]  # 使用简单测试用例
        
        for i in range(iterations):
            try:
                # 生成测试数据
                audio_path, subtitles = test_suite.generate_synthetic_audio(test_case)
                
                # 执行对齐
                config = IntelligentAlignmentConfig()
                system = IntelligentAlignmentSystem(config)
                aligned_subtitles, _ = system.align_subtitles(audio_path, subtitles)
                
                # 清理
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                del system, aligned_subtitles, subtitles
                gc.collect()
                
                # 记录内存
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                logger.debug(f"迭代 {i+1}/{iterations}, 内存: {current_memory:.1f}MB")
                
            except Exception as e:
                logger.error(f"内存泄漏测试迭代 {i+1} 失败: {e}")
        
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        # 分析内存趋势
        if len(memory_samples) > 5:
            # 线性回归分析内存增长趋势
            x = np.arange(len(memory_samples))
            slope, intercept = np.polyfit(x, memory_samples, 1)
            growth_rate = slope  # MB per iteration
        else:
            growth_rate = memory_growth / iterations
        
        result = {
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'memory_growth': memory_growth,
            'growth_rate_per_iteration': growth_rate,
            'memory_samples': memory_samples,
            'iterations': iterations,
            'has_leak': growth_rate > 1.0,  # 每次迭代增长超过1MB认为有泄漏
            'leak_severity': 'high' if growth_rate > 5.0 else 'medium' if growth_rate > 1.0 else 'low'
        }
        
        logger.info(f"内存泄漏测试完成，增长: {memory_growth:.1f}MB, 增长率: {growth_rate:.2f}MB/次")
        return result
    
    def optimize_performance(self) -> Dict[str, Any]:
        """执行性能优化"""
        logger.info("开始性能优化")
        
        optimizations = {}
        
        # 1. 垃圾回收优化
        gc.collect()
        optimizations['gc_collected'] = True
        
        # 2. 内存池优化 (示例)
        # 这里可以实现对象池、内存池等优化策略
        
        # 3. 缓存优化
        # 可以实现智能缓存策略
        
        logger.info("性能优化完成")
        return optimizations


# 便捷函数
def run_performance_benchmark(config: Optional[BenchmarkConfig] = None,
                            progress_callback: Optional[Callable[[float, str], None]] = None) -> BenchmarkResult:
    """
    运行性能基准测试的便捷函数
    
    Args:
        config: 基准测试配置
        progress_callback: 进度回调
        
    Returns:
        基准测试结果
    """
    benchmark = PerformanceBenchmark(config)
    return benchmark.run_benchmark(progress_callback)


if __name__ == "__main__":
    # 测试性能基准测试器
    print("🎯 性能基准测试器")
    print("=" * 60)
    
    # 创建配置 (小规模测试)
    config = BenchmarkConfig(
        audio_durations=[5, 10, 20],  # 小规模测试
        subtitle_counts=[3, 5, 10],
        target_speed_ratio=3.0,
        max_memory_mb=500.0
    )
    
    print(f"基准测试配置:")
    print(f"  音频时长: {config.audio_durations}秒")
    print(f"  字幕数量: {config.subtitle_counts}")
    print(f"  目标速度比: {config.target_speed_ratio}")
    print(f"  内存限制: {config.max_memory_mb}MB")
    
    # 创建基准测试器
    benchmark = PerformanceBenchmark(config)
    
    print(f"\n基准测试器信息:")
    print(f"  结果目录: {benchmark.results_dir}")
    print(f"  监控启用: {benchmark.config.enable_profiling}")
    
    # 测试内存泄漏检测
    print(f"\n测试内存泄漏检测 (3次迭代):")
    
    def progress_callback(progress, message):
        print(f"  进度: {message}")
    
    try:
        leak_result = benchmark.test_memory_leak(iterations=3)
        print(f"  初始内存: {leak_result['initial_memory']:.1f}MB")
        print(f"  最终内存: {leak_result['final_memory']:.1f}MB")
        print(f"  内存增长: {leak_result['memory_growth']:.1f}MB")
        print(f"  有内存泄漏: {leak_result['has_leak']}")
    except Exception as e:
        print(f"  内存泄漏测试失败: {e}")
    
    print(f"\n✅ 性能基准测试器准备完成!")
    print(f"使用示例:")
    print(f"  result = benchmark.run_benchmark()")
    print(f"  print(f'平均速度比: {{result.summary['avg_speed_ratio']:.2f}}')")
    print(f"  print(f'瓶颈: {{result.bottlenecks}}')")