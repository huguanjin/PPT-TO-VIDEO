"""
Netflix字幕系统错误处理和监控模块
提供生产级的错误处理、性能监控、健康检查功能
"""

import logging
import time
import traceback
import threading
import psutil
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

class ErrorSeverity(Enum):
    """错误严重级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SystemStatus(Enum):
    """系统状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class ErrorInfo:
    """错误信息类"""
    timestamp: datetime
    severity: ErrorSeverity
    component: str
    operation: str
    error_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    recovery_action: Optional[str] = None

@dataclass
class PerformanceMetrics:
    """性能指标类"""
    timestamp: datetime
    component: str
    operation: str
    duration: float
    memory_usage: float
    cpu_usage: float
    success: bool
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthStatus:
    """健康状态类"""
    component: str
    status: SystemStatus
    last_check: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)

class NetflixErrorHandler:
    """Netflix字幕系统错误处理器"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "logs/netflix_error_handler.log"
        self.logger = self._setup_logger()
        self.errors: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # 错误阈值配置
        self.thresholds = {
            'max_errors_per_hour': 100,
            'circuit_breaker_failure_threshold': 5,
            'circuit_breaker_timeout': 60,  # 秒
            'memory_threshold': 1024,  # MB
            'cpu_threshold': 80,  # %
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('netflix_error_handler')
        logger.setLevel(logging.DEBUG)
        
        # 确保日志目录存在
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 避免重复添加处理器
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def handle_error(self, 
                    component: str,
                    operation: str,
                    error: Exception,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    user_context: Optional[Dict[str, Any]] = None,
                    recovery_action: Optional[str] = None) -> ErrorInfo:
        """处理错误"""
        
        error_info = ErrorInfo(
            timestamp=datetime.now(),
            severity=severity,
            component=component,
            operation=operation,
            error_type=type(error).__name__,
            message=str(error),
            stack_trace=traceback.format_exc(),
            user_context=user_context,
            recovery_action=recovery_action,
            details={
                'error_class': error.__class__.__module__ + '.' + error.__class__.__name__,
                'args': error.args if hasattr(error, 'args') else None
            }
        )
        
        with self._lock:
            self.errors.append(error_info)
            
            # 更新错误计数
            error_key = f"{component}.{operation}.{error_info.error_type}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # 检查熔断器
            self._check_circuit_breaker(component, operation)
        
        # 记录日志
        log_message = f"[{severity.value.upper()}] {component}.{operation}: {error_info.message}"
        if user_context:
            log_message += f" | Context: {user_context}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return error_info
    
    def _check_circuit_breaker(self, component: str, operation: str):
        """检查和更新熔断器状态"""
        key = f"{component}.{operation}"
        
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = {
                'failure_count': 0,
                'last_failure': None,
                'state': 'closed'  # closed, open, half-open
            }
        
        breaker = self.circuit_breakers[key]
        breaker['failure_count'] += 1
        breaker['last_failure'] = datetime.now()
        
        # 检查是否需要打开熔断器
        if breaker['failure_count'] >= self.thresholds['circuit_breaker_failure_threshold']:
            if breaker['state'] == 'closed':
                breaker['state'] = 'open'
                self.logger.warning(f"熔断器打开: {key} (失败次数: {breaker['failure_count']})")
    
    def is_circuit_breaker_open(self, component: str, operation: str) -> bool:
        """检查熔断器是否打开"""
        key = f"{component}.{operation}"
        
        if key not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[key]
        
        if breaker['state'] == 'closed':
            return False
        elif breaker['state'] == 'open':
            # 检查是否可以尝试半开状态
            if breaker['last_failure']:
                time_since_failure = (datetime.now() - breaker['last_failure']).total_seconds()
                if time_since_failure >= self.thresholds['circuit_breaker_timeout']:
                    breaker['state'] = 'half-open'
                    self.logger.info(f"熔断器进入半开状态: {key}")
                    return False
            return True
        else:  # half-open
            return False
    
    def record_success(self, component: str, operation: str):
        """记录成功操作（用于重置熔断器）"""
        key = f"{component}.{operation}"
        
        if key in self.circuit_breakers:
            breaker = self.circuit_breakers[key]
            if breaker['state'] in ['open', 'half-open']:
                breaker['state'] = 'closed'
                breaker['failure_count'] = 0
                self.logger.info(f"熔断器重置为关闭状态: {key}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误总结"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [e for e in self.errors if e.timestamp >= cutoff_time]
        
        # 按组件分组
        by_component = {}
        by_severity = {}
        by_error_type = {}
        
        for error in recent_errors:
            # 按组件
            if error.component not in by_component:
                by_component[error.component] = []
            by_component[error.component].append(error)
            
            # 按严重程度
            severity_key = error.severity.value
            if severity_key not in by_severity:
                by_severity[severity_key] = 0
            by_severity[severity_key] += 1
            
            # 按错误类型
            if error.error_type not in by_error_type:
                by_error_type[error.error_type] = 0
            by_error_type[error.error_type] += 1
        
        return {
            'total_errors': len(recent_errors),
            'time_range_hours': hours,
            'by_component': {k: len(v) for k, v in by_component.items()},
            'by_severity': by_severity,
            'by_error_type': by_error_type,
            'circuit_breakers': {k: v['state'] for k, v in self.circuit_breakers.items()},
            'most_frequent_errors': sorted(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }

class NetflixPerformanceMonitor:
    """Netflix字幕系统性能监控器"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "logs/netflix_performance.log"
        self.logger = self._setup_logger()
        self.metrics: List[PerformanceMetrics] = []
        self._lock = threading.RLock()
        
        # 性能阈值
        self.thresholds = {
            'max_response_time': 5.0,  # 秒
            'max_memory_usage': 1024,  # MB
            'max_cpu_usage': 80,  # %
            'min_throughput': 1.0,  # 操作/秒
            'max_error_rate': 0.05,  # 5%
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('netflix_performance_monitor')
        logger.setLevel(logging.INFO)
        
        # 确保日志目录存在
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        if not logger.handlers:
            logger.addHandler(file_handler)
        
        return logger
    
    def record_performance(self, 
                          component: str,
                          operation: str,
                          duration: float,
                          success: bool = True,
                          throughput: Optional[float] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetrics:
        """记录性能指标"""
        
        # 获取系统资源使用情况
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage = memory_info.rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            duration=duration,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            success=success,
            throughput=throughput,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics.append(metrics)
        
        # 检查性能阈值
        warnings = []
        if duration > self.thresholds['max_response_time']:
            warnings.append(f"响应时间过长: {duration:.2f}s")
        
        if memory_usage > self.thresholds['max_memory_usage']:
            warnings.append(f"内存使用过高: {memory_usage:.1f}MB")
        
        if cpu_usage > self.thresholds['max_cpu_usage']:
            warnings.append(f"CPU使用过高: {cpu_usage:.1f}%")
        
        if throughput and throughput < self.thresholds['min_throughput']:
            warnings.append(f"吞吐量过低: {throughput:.2f} ops/s")
        
        # 记录性能日志
        log_message = (f"{component}.{operation}: "
                      f"duration={duration:.3f}s, "
                      f"memory={memory_usage:.1f}MB, "
                      f"cpu={cpu_usage:.1f}%, "
                      f"success={success}")
        
        if throughput:
            log_message += f", throughput={throughput:.2f} ops/s"
        
        if warnings:
            log_message += f" | WARNINGS: {'; '.join(warnings)}"
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return metrics
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能总结"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {'total_operations': 0, 'time_range_hours': hours}
        
        # 计算统计信息
        total_ops = len(recent_metrics)
        successful_ops = sum(1 for m in recent_metrics if m.success)
        success_rate = successful_ops / total_ops if total_ops > 0 else 0
        
        durations = [m.duration for m in recent_metrics]
        memory_usages = [m.memory_usage for m in recent_metrics]
        cpu_usages = [m.cpu_usage for m in recent_metrics if m.cpu_usage > 0]
        
        # 按组件分组
        by_component = {}
        for metric in recent_metrics:
            if metric.component not in by_component:
                by_component[metric.component] = []
            by_component[metric.component].append(metric)
        
        component_stats = {}
        for component, metrics_list in by_component.items():
            component_durations = [m.duration for m in metrics_list]
            component_stats[component] = {
                'total_operations': len(metrics_list),
                'success_rate': sum(1 for m in metrics_list if m.success) / len(metrics_list),
                'avg_duration': sum(component_durations) / len(component_durations),
                'max_duration': max(component_durations),
                'min_duration': min(component_durations)
            }
        
        return {
            'total_operations': total_ops,
            'success_rate': success_rate,
            'time_range_hours': hours,
            'duration_stats': {
                'avg': sum(durations) / len(durations),
                'max': max(durations),
                'min': min(durations),
                'p95': sorted(durations)[int(len(durations) * 0.95)] if durations else 0
            },
            'memory_stats': {
                'avg': sum(memory_usages) / len(memory_usages),
                'max': max(memory_usages),
                'min': min(memory_usages)
            },
            'cpu_stats': {
                'avg': sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0,
                'max': max(cpu_usages) if cpu_usages else 0
            },
            'by_component': component_stats
        }

class NetflixHealthChecker:
    """Netflix字幕系统健康检查器"""
    
    def __init__(self, 
                 error_handler: NetflixErrorHandler,
                 performance_monitor: NetflixPerformanceMonitor):
        self.error_handler = error_handler
        self.performance_monitor = performance_monitor
        self.component_health: Dict[str, HealthStatus] = {}
        self._lock = threading.RLock()
        
        # 健康检查阈值
        self.health_thresholds = {
            'error_rate_warning': 0.05,  # 5%
            'error_rate_critical': 0.20,  # 20%
            'response_time_warning': 2.0,  # 秒
            'response_time_critical': 5.0,  # 秒
            'memory_warning': 800,  # MB
            'memory_critical': 1200,  # MB
            'cpu_warning': 70,  # %
            'cpu_critical': 90,  # %
        }
    
    def register_component(self, component: str, check_function: Optional[Callable] = None):
        """注册需要健康检查的组件"""
        with self._lock:
            self.component_health[component] = HealthStatus(
                component=component,
                status=SystemStatus.HEALTHY,
                last_check=datetime.now(),
                details={'check_function': check_function}
            )
    
    def check_component_health(self, component: str) -> HealthStatus:
        """检查特定组件的健康状态"""
        if component not in self.component_health:
            self.register_component(component)
        
        health_status = self.component_health[component]
        
        # 获取组件的性能指标（最近1小时）
        recent_metrics = [
            m for m in self.performance_monitor.metrics
            if m.component == component and 
            m.timestamp >= datetime.now() - timedelta(hours=1)
        ]
        
        # 获取组件的错误信息（最近1小时）
        recent_errors = [
            e for e in self.error_handler.errors
            if e.component == component and 
            e.timestamp >= datetime.now() - timedelta(hours=1)
        ]
        
        # 计算健康指标
        if recent_metrics:
            total_ops = len(recent_metrics)
            successful_ops = sum(1 for m in recent_metrics if m.success)
            error_rate = 1 - (successful_ops / total_ops)
            
            avg_response_time = sum(m.duration for m in recent_metrics) / total_ops
            avg_memory = sum(m.memory_usage for m in recent_metrics) / total_ops
            avg_cpu = sum(m.cpu_usage for m in recent_metrics if m.cpu_usage > 0)
            avg_cpu = avg_cpu / len([m for m in recent_metrics if m.cpu_usage > 0]) if avg_cpu else 0
        else:
            error_rate = 0
            avg_response_time = 0
            avg_memory = 0
            avg_cpu = 0
        
        # 确定健康状态
        status = SystemStatus.HEALTHY
        issues = []
        
        # 检查错误率
        if error_rate >= self.health_thresholds['error_rate_critical']:
            status = SystemStatus.UNHEALTHY
            issues.append(f"错误率过高: {error_rate:.1%}")
        elif error_rate >= self.health_thresholds['error_rate_warning']:
            if status == SystemStatus.HEALTHY:
                status = SystemStatus.WARNING
            issues.append(f"错误率偏高: {error_rate:.1%}")
        
        # 检查响应时间
        if avg_response_time >= self.health_thresholds['response_time_critical']:
            status = SystemStatus.UNHEALTHY
            issues.append(f"响应时间过长: {avg_response_time:.2f}s")
        elif avg_response_time >= self.health_thresholds['response_time_warning']:
            if status == SystemStatus.HEALTHY:
                status = SystemStatus.WARNING
            issues.append(f"响应时间偏长: {avg_response_time:.2f}s")
        
        # 检查内存使用
        if avg_memory >= self.health_thresholds['memory_critical']:
            status = SystemStatus.UNHEALTHY
            issues.append(f"内存使用过高: {avg_memory:.1f}MB")
        elif avg_memory >= self.health_thresholds['memory_warning']:
            if status == SystemStatus.HEALTHY:
                status = SystemStatus.WARNING
            issues.append(f"内存使用偏高: {avg_memory:.1f}MB")
        
        # 检查CPU使用
        if avg_cpu >= self.health_thresholds['cpu_critical']:
            status = SystemStatus.UNHEALTHY
            issues.append(f"CPU使用过高: {avg_cpu:.1f}%")
        elif avg_cpu >= self.health_thresholds['cpu_warning']:
            if status == SystemStatus.HEALTHY:
                status = SystemStatus.WARNING
            issues.append(f"CPU使用偏高: {avg_cpu:.1f}%")
        
        # 检查熔断器状态
        open_breakers = [
            k for k, v in self.error_handler.circuit_breakers.items()
            if k.startswith(component) and v['state'] == 'open'
        ]
        if open_breakers:
            status = SystemStatus.DEGRADED
            issues.append(f"熔断器打开: {', '.join(open_breakers)}")
        
        # 更新健康状态
        with self._lock:
            health_status.status = status
            health_status.last_check = datetime.now()
            health_status.details = {
                'issues': issues,
                'recent_operations': len(recent_metrics),
                'recent_errors': len(recent_errors),
                'check_function': health_status.details.get('check_function')
            }
            health_status.metrics = {
                'error_rate': error_rate,
                'avg_response_time': avg_response_time,
                'avg_memory_usage': avg_memory,
                'avg_cpu_usage': avg_cpu
            }
        
        return health_status
    
    def check_overall_health(self) -> Dict[str, Any]:
        """检查整体系统健康状态"""
        component_statuses = {}
        
        # 检查所有已注册的组件
        for component in self.component_health.keys():
            component_statuses[component] = self.check_component_health(component)
        
        # 确定整体状态
        all_statuses = [status.status for status in component_statuses.values()]
        
        if SystemStatus.UNHEALTHY in all_statuses:
            overall_status = SystemStatus.UNHEALTHY
        elif SystemStatus.DEGRADED in all_statuses:
            overall_status = SystemStatus.DEGRADED
        elif SystemStatus.WARNING in all_statuses:
            overall_status = SystemStatus.WARNING
        else:
            overall_status = SystemStatus.HEALTHY
        
        return {
            'overall_status': overall_status.value,
            'check_time': datetime.now().isoformat(),
            'components': {
                name: {
                    'status': status.status.value,
                    'last_check': status.last_check.isoformat(),
                    'issues': status.details.get('issues', []),
                    'metrics': status.metrics
                }
                for name, status in component_statuses.items()
            },
            'summary': {
                'total_components': len(component_statuses),
                'healthy': sum(1 for s in all_statuses if s == SystemStatus.HEALTHY),
                'warning': sum(1 for s in all_statuses if s == SystemStatus.WARNING),
                'degraded': sum(1 for s in all_statuses if s == SystemStatus.DEGRADED),
                'unhealthy': sum(1 for s in all_statuses if s == SystemStatus.UNHEALTHY)
            }
        }

# 性能装饰器
def monitor_performance(component: str, operation: str = None):
    """性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从全局获取监控器实例（需要在应用启动时设置）
            monitor = getattr(wrapper, '_performance_monitor', None)
            if not monitor:
                # 如果没有监控器，直接执行函数
                return func(*args, **kwargs)
            
            op_name = operation or func.__name__
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_performance(
                    component=component,
                    operation=op_name,
                    duration=duration,
                    success=success
                )
        
        return wrapper
    return decorator

# 错误处理装饰器
def handle_errors(component: str, operation: str = None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """错误处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从全局获取错误处理器实例
            error_handler = getattr(wrapper, '_error_handler', None)
            
            op_name = operation or func.__name__
            
            try:
                # 检查熔断器
                if error_handler and error_handler.is_circuit_breaker_open(component, op_name):
                    raise Exception(f"熔断器打开: {component}.{op_name}")
                
                result = func(*args, **kwargs)
                
                # 记录成功
                if error_handler:
                    error_handler.record_success(component, op_name)
                
                return result
                
            except Exception as e:
                if error_handler:
                    error_handler.handle_error(
                        component=component,
                        operation=op_name,
                        error=e,
                        severity=severity
                    )
                raise
        
        return wrapper
    return decorator