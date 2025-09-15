"""
简化版性能基准测试器 - 测试基础功能
不依赖复杂的音频处理模块，专注于性能监控和分析功能
"""
import os
import time
import psutil
import threading
import gc
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, asdict
import logging
import numpy as np
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class SimpleBenchmarkConfig:
    """简化基准测试配置"""
    test_iterations: int = 5              # 测试迭代次数
    target_speed_ratio: float = 3.0       # 目标速度比
    max_memory_mb: float = 500.0          # 最大内存使用(MB)
    monitoring_interval: float = 0.1      # 监控间隔(秒)


@dataclass
class SimplePerformanceMetrics:
    """简化性能指标"""
    iteration: int                        # 迭代次数
    processing_time: float                # 处理时间(秒)
    memory_peak: float                    # 内存峰值(MB)
    memory_final: float                   # 最终内存(MB)
    cpu_usage: float                      # CPU使用率(%)
    error_occurred: bool = False          # 是否出错
    error_message: str = ""               # 错误信息


class SimplePerformanceBenchmark:
    """简化性能基准测试器"""
    
    def __init__(self, config: Optional[SimpleBenchmarkConfig] = None):
        """初始化简化性能基准测试器"""
        self.config = config or SimpleBenchmarkConfig()
        
        # 性能监控
        self.process = psutil.Process()
        self.monitoring_active = False
        self.monitoring_data = []
        
        # 测试结果存储
        self.results_dir = "simple_benchmark_results"
        Path(self.results_dir).mkdir(exist_ok=True)
        
        print(f"✅ 简化性能基准测试器初始化完成")
        print(f"   配置: {self.config.test_iterations}次迭代")
        print(f"   内存限制: {self.config.max_memory_mb}MB")
        print(f"   监控间隔: {self.config.monitoring_interval}s")
    
    def start_monitoring(self):
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
                    
                    time.sleep(self.config.monitoring_interval)
                except Exception as e:
                    print(f"监控错误: {e}")
                    break
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        print("🔍 性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1.0)
        print("⏹️ 性能监控已停止")
    
    def simulate_workload(self, duration: float = 2.0, memory_usage: int = 100):
        """模拟工作负载"""
        print(f"   模拟工作负载: {duration}s, 内存使用: {memory_usage}MB")
        
        start_time = time.time()
        
        # 分配内存模拟内存使用
        data = []
        for i in range(memory_usage):
            # 每次分配约1MB数据
            data.append(np.random.rand(128, 1024))  # 约1MB float64数据
        
        # CPU密集型计算
        total = 0
        while time.time() - start_time < duration:
            # 模拟计算工作
            result = np.sum(np.random.rand(1000, 1000))
            total += result
            
            # 短暂休眠避免100% CPU占用
            time.sleep(0.01)
        
        # 清理部分数据
        del data[::2]  # 删除一半数据
        
        return total
    
    def run_single_test(self, iteration: int) -> SimplePerformanceMetrics:
        """运行单次测试"""
        print(f"   执行第 {iteration} 次测试...")
        
        # 记录初始内存
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        
        # 开始监控
        self.start_monitoring()
        
        try:
            # 执行模拟工作负载
            workload_duration = 1.0 + iteration * 0.5  # 递增工作负载
            memory_usage = 50 + iteration * 10         # 递增内存使用
            result = self.simulate_workload(workload_duration, memory_usage)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 停止监控
            self.stop_monitoring()
            
            # 计算性能指标
            final_memory = self.process.memory_info().rss / 1024 / 1024
            
            if self.monitoring_data:
                memory_peak = max([data['memory'] for data in self.monitoring_data])
                avg_cpu = np.mean([data['cpu'] for data in self.monitoring_data])
            else:
                memory_peak = final_memory
                avg_cpu = 0.0
            
            metrics = SimplePerformanceMetrics(
                iteration=iteration,
                processing_time=processing_time,
                memory_peak=memory_peak,
                memory_final=final_memory,
                cpu_usage=float(avg_cpu),
                error_occurred=False
            )
            
            print(f"   ✅ 完成: {processing_time:.2f}s, {memory_peak:.1f}MB, {avg_cpu:.1f}% CPU")
            return metrics
            
        except Exception as e:
            self.stop_monitoring()
            
            processing_time = time.time() - start_time
            final_memory = self.process.memory_info().rss / 1024 / 1024
            
            print(f"   ❌ 失败: {e}")
            
            return SimplePerformanceMetrics(
                iteration=iteration,
                processing_time=processing_time,
                memory_peak=final_memory,
                memory_final=final_memory,
                cpu_usage=0.0,
                error_occurred=True,
                error_message=str(e)
            )
    
    def run_benchmark(self) -> Dict[str, Any]:
        """运行完整基准测试"""
        print(f"\n🎯 开始性能基准测试")
        print(f"   测试配置: {self.config.test_iterations} 次迭代")
        
        metrics_list = []
        
        for i in range(1, self.config.test_iterations + 1):
            print(f"\n第 {i}/{self.config.test_iterations} 轮测试:")
            
            # 运行单次测试
            metrics = self.run_single_test(i)
            metrics_list.append(metrics)
            
            # 强制垃圾回收
            gc.collect()
            
            # 短暂休眠
            time.sleep(0.5)
        
        # 分析结果
        print(f"\n📊 分析测试结果...")
        analysis = self.analyze_results(metrics_list)
        
        # 保存结果
        self.save_results(metrics_list, analysis)
        
        print(f"\n✅ 基准测试完成!")
        return {
            'metrics_list': metrics_list,
            'analysis': analysis
        }
    
    def analyze_results(self, metrics_list: List[SimplePerformanceMetrics]) -> Dict[str, Any]:
        """分析测试结果"""
        successful_metrics = [m for m in metrics_list if not m.error_occurred]
        
        if not successful_metrics:
            return {'error': 'No successful tests'}
        
        # 计算统计信息
        processing_times = [m.processing_time for m in successful_metrics]
        memory_peaks = [m.memory_peak for m in successful_metrics]
        cpu_usages = [m.cpu_usage for m in successful_metrics]
        
        analysis = {
            'total_tests': len(metrics_list),
            'successful_tests': len(successful_metrics),
            'success_rate': len(successful_metrics) / len(metrics_list),
            
            # 处理时间统计
            'avg_processing_time': np.mean(processing_times),
            'max_processing_time': np.max(processing_times),
            'min_processing_time': np.min(processing_times),
            
            # 内存统计
            'avg_memory_peak': np.mean(memory_peaks),
            'max_memory_peak': np.max(memory_peaks),
            'min_memory_peak': np.min(memory_peaks),
            
            # CPU统计
            'avg_cpu_usage': np.mean(cpu_usages),
            'max_cpu_usage': np.max(cpu_usages),
            
            # 性能指标
            'memory_within_limit': all(m < self.config.max_memory_mb for m in memory_peaks),
            'performance_stable': (np.max(processing_times) - np.min(processing_times)) < 2.0,
        }
        
        # 识别问题
        issues = []
        if analysis['max_memory_peak'] > self.config.max_memory_mb:
            issues.append(f"内存使用超限: {analysis['max_memory_peak']:.1f}MB > {self.config.max_memory_mb}MB")
        
        if analysis['avg_cpu_usage'] > 80:
            issues.append(f"CPU使用率过高: {analysis['avg_cpu_usage']:.1f}%")
        
        if not analysis['performance_stable']:
            issues.append("性能不稳定，处理时间波动较大")
        
        analysis['issues'] = issues
        
        # 生成建议
        recommendations = []
        if issues:
            if any("内存" in issue for issue in issues):
                recommendations.append("考虑实现内存优化策略，如分批处理或内存池")
            if any("CPU" in issue for issue in issues):
                recommendations.append("考虑优化算法或使用并行处理")
            if any("不稳定" in issue for issue in issues):
                recommendations.append("检查资源竞争和垃圾回收策略")
        else:
            recommendations.append("性能表现良好，继续保持")
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def save_results(self, metrics_list: List[SimplePerformanceMetrics], 
                    analysis: Dict[str, Any]):
        """保存测试结果"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # 转换numpy类型为Python原生类型
        def convert_numpy_types(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            return obj
        
        # 保存详细结果
        result_data = {
            'config': asdict(self.config),
            'metrics': [asdict(m) for m in metrics_list],
            'analysis': convert_numpy_types(analysis),
            'timestamp': timestamp
        }
        
        json_path = os.path.join(self.results_dir, f'benchmark_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"   📁 结果已保存: {json_path}")
    
    def test_memory_leak(self, iterations: int = 5) -> Dict[str, Any]:
        """测试内存泄漏"""
        print(f"\n🔍 内存泄漏测试 ({iterations} 次迭代)")
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        memory_samples = [initial_memory]
        
        print(f"   初始内存: {initial_memory:.1f}MB")
        
        for i in range(iterations):
            print(f"   迭代 {i+1}/{iterations}:")
            
            # 模拟工作负载
            self.simulate_workload(1.0, 50)
            
            # 记录内存
            current_memory = self.process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            print(f"     内存: {current_memory:.1f}MB")
            
            # 垃圾回收
            gc.collect()
            
            time.sleep(0.5)
        
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        # 分析内存趋势
        if len(memory_samples) > 3:
            x = np.arange(len(memory_samples))
            slope, intercept = np.polyfit(x, memory_samples, 1)
            growth_rate = slope
        else:
            growth_rate = memory_growth / iterations
        
        result = {
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'memory_growth': memory_growth,
            'growth_rate_per_iteration': growth_rate,
            'memory_samples': memory_samples,
            'iterations': iterations,
            'has_leak': growth_rate > 5.0,  # 每次迭代增长超过5MB认为有泄漏
            'leak_severity': 'high' if growth_rate > 10.0 else 'medium' if growth_rate > 5.0 else 'low'
        }
        
        print(f"   内存增长: {memory_growth:.1f}MB")
        print(f"   增长率: {growth_rate:.2f}MB/次")
        print(f"   有泄漏: {'是' if result['has_leak'] else '否'}")
        
        return result


def main():
    """主测试函数"""
    print("🎯 简化性能基准测试器")
    print("=" * 50)
    
    # 创建配置
    config = SimpleBenchmarkConfig(
        test_iterations=3,     # 小规模测试
        max_memory_mb=300.0,   # 较小的内存限制
        monitoring_interval=0.05  # 更频繁的监控
    )
    
    # 创建测试器
    benchmark = SimplePerformanceBenchmark(config)
    
    # 运行基准测试
    print(f"\n📈 运行基准测试...")
    result = benchmark.run_benchmark()
    
    # 显示摘要
    analysis = result['analysis']
    print(f"\n📊 测试摘要:")
    print(f"   成功率: {analysis['success_rate']:.1%}")
    print(f"   平均处理时间: {analysis['avg_processing_time']:.2f}s")
    print(f"   平均内存峰值: {analysis['avg_memory_peak']:.1f}MB")
    print(f"   平均CPU使用: {analysis['avg_cpu_usage']:.1f}%")
    
    if analysis['issues']:
        print(f"\n⚠️ 发现问题:")
        for issue in analysis['issues']:
            print(f"   - {issue}")
    
    if analysis['recommendations']:
        print(f"\n💡 优化建议:")
        for rec in analysis['recommendations']:
            print(f"   - {rec}")
    
    # 测试内存泄漏
    leak_result = benchmark.test_memory_leak(iterations=3)
    
    print(f"\n✅ 测试完成!")
    print(f"   结果目录: {benchmark.results_dir}")


if __name__ == "__main__":
    main()