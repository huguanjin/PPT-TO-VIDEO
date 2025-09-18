"""
Netflix质量指标监控系统
实时监控字幕分割质量、性能和合规性
"""

import time
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging
from collections import defaultdict, deque
from difflib import SequenceMatcher
import threading

class NetflixQualityMetrics:
    """Netflix质量指标监控器"""
    
    def __init__(self, config_loader=None):
        """
        初始化质量监控器
        
        Args:
            config_loader: Netflix配置加载器实例
        """
        self.logger = logging.getLogger(__name__)
        self.config = config_loader
        
        # 基础指标
        self.metrics = {
            'total_splits': 0,
            'successful_ai_splits': 0,
            'fallback_splits': 0,
            'nlp_only_splits': 0,
            'failed_splits': 0,
            'average_similarity': 0.0,
            'netflix_compliance_rate': 0.0,
            'average_processing_time': 0.0,
            'error_count': 0
        }
        
        # 详细统计
        self.detailed_stats = {
            'similarity_scores': deque(maxlen=1000),
            'processing_times': deque(maxlen=1000),
            'split_methods': defaultdict(int),
            'error_types': defaultdict(int),
            'daily_counts': defaultdict(int),
            'compliance_details': {
                'length_violations': 0,
                'balance_violations': 0,
                'content_violations': 0
            }
        }
        
        # 时间窗口统计（最近1小时、24小时、7天）
        self.time_windows = {
            '1h': deque(maxlen=3600),    # 假设每秒一次记录
            '24h': deque(maxlen=86400),  # 假设每秒一次记录
            '7d': deque(maxlen=604800)   # 假设每秒一次记录
        }
        
        # 质量阈值（从配置加载）
        self.thresholds = self._load_thresholds()
        
        # 线程锁保证线程安全
        self._lock = threading.Lock()
        
        # 报告生成相关
        self.last_report_time = datetime.now()
        self.report_data = []
    
    def _load_thresholds(self) -> Dict[str, float]:
        """从配置加载质量阈值"""
        if self.config:
            quality_config = self.config.quality_metrics
            return {
                'similarity_warning': quality_config.get('similarity_warning_threshold', 0.85),
                'compliance_target': quality_config.get('compliance_target', 0.9),
                'low_similarity_rate': quality_config.get('alert_thresholds', {}).get('low_similarity_rate', 0.1),
                'high_fallback_rate': quality_config.get('alert_thresholds', {}).get('high_fallback_rate', 0.3),
                'slow_response_rate': quality_config.get('alert_thresholds', {}).get('slow_response_rate', 0.2)
            }
        else:
            return {
                'similarity_warning': 0.85,
                'compliance_target': 0.9,
                'low_similarity_rate': 0.1,
                'high_fallback_rate': 0.3,
                'slow_response_rate': 0.2
            }
    
    def record_split_result(self, 
                          original: str, 
                          result: List[str], 
                          method: str, 
                          processing_time: float = 0.0,
                          error: Optional[str] = None):
        """
        记录分割结果
        
        Args:
            original: 原始文本
            result: 分割结果
            method: 分割方法 ('ai', 'nlp_fallback', 'simple_fallback', 'failed')
            processing_time: 处理时间（秒）
            error: 错误信息（如果有）
        """
        with self._lock:
            current_time = datetime.now()
            
            # 更新基础计数
            self.metrics['total_splits'] += 1
            
            if method == 'ai':
                self.metrics['successful_ai_splits'] += 1
            elif method in ['nlp_fallback', 'simple_fallback']:
                if method == 'nlp_fallback':
                    self.metrics['nlp_only_splits'] += 1
                else:
                    self.metrics['fallback_splits'] += 1
            elif method == 'failed':
                self.metrics['failed_splits'] += 1
            
            # 记录错误
            if error:
                self.metrics['error_count'] += 1
                self.detailed_stats['error_types'][error] += 1
            
            # 记录分割方法
            self.detailed_stats['split_methods'][method] += 1
            
            # 记录处理时间
            if processing_time > 0:
                self.detailed_stats['processing_times'].append(processing_time)
                # 更新平均处理时间
                times = list(self.detailed_stats['processing_times'])
                self.metrics['average_processing_time'] = sum(times) / len(times)
            
            # 计算相似度（仅当有结果时）
            if result and method != 'failed':
                similarity = self._calculate_similarity(original, result)
                self.detailed_stats['similarity_scores'].append(similarity)
                
                # 更新平均相似度
                scores = list(self.detailed_stats['similarity_scores'])
                self.metrics['average_similarity'] = sum(scores) / len(scores)
                
                # 检查Netflix合规性
                compliance = self._check_netflix_compliance(result)
                self._update_compliance_stats(compliance)
            
            # 记录到时间窗口
            record = {
                'timestamp': current_time,
                'method': method,
                'similarity': similarity if 'similarity' in locals() else 0.0,
                'processing_time': processing_time,
                'compliant': compliance if 'compliance' in locals() else False,
                'error': error is not None
            }
            
            for window in self.time_windows.values():
                window.append(record)
            
            # 每日统计
            date_key = current_time.strftime('%Y-%m-%d')
            self.detailed_stats['daily_counts'][date_key] += 1
            
            # 检查是否需要生成报告
            self._check_report_schedule()
    
    def _calculate_similarity(self, original: str, result: List[str]) -> float:
        """计算分割结果与原文的相似度"""
        if not result:
            return 0.0
        
        reconstructed = ''.join(result).replace(' ', '')
        original_clean = original.replace(' ', '')
        
        return SequenceMatcher(None, original_clean, reconstructed).ratio()
    
    def _check_netflix_compliance(self, result: List[str]) -> Dict[str, Any]:
        """检查Netflix标准合规性"""
        compliance = {
            'is_compliant': True,
            'violations': [],
            'length_ok': True,
            'balance_ok': True,
            'content_ok': True
        }
        
        if not result:
            compliance['is_compliant'] = False
            compliance['violations'].append('empty_result')
            return compliance
        
        # 获取长度限制
        max_chars = self.config.netflix_standards.get('max_chars_per_line', 20) if self.config else 20
        min_chars = self.config.netflix_standards.get('min_chars_per_line', 3) if self.config else 3
        balance_ratio = self.config.netflix_standards.get('length_balance_ratio', 2.5) if self.config else 2.5
        
        # 检查单行长度
        for i, line in enumerate(result):
            line_length = len(line.strip())
            if line_length > max_chars:
                compliance['is_compliant'] = False
                compliance['length_ok'] = False
                compliance['violations'].append(f'line_{i+1}_too_long')
            elif line_length < min_chars and line_length > 0:  # 只检查非空行
                compliance['is_compliant'] = False
                compliance['length_ok'] = False
                compliance['violations'].append(f'line_{i+1}_too_short')
        
        # 检查长度均衡性
        if len(result) > 1:
            lengths = [len(line.strip()) for line in result]
            max_length = max(lengths)
            min_length = min(lengths)
            if min_length > 0 and max_length / min_length > balance_ratio:
                compliance['is_compliant'] = False
                compliance['balance_ok'] = False
                compliance['violations'].append('unbalanced_lengths')
        
        return compliance
    
    def _update_compliance_stats(self, compliance: Dict[str, Any]):
        """更新合规性统计"""
        if compliance['is_compliant']:
            # 计算合规率
            total = self.metrics['total_splits']
            current_compliant = self.metrics['netflix_compliance_rate'] * (total - 1)
            self.metrics['netflix_compliance_rate'] = (current_compliant + 1) / total
        else:
            # 记录违规详情
            if not compliance['length_ok']:
                self.detailed_stats['compliance_details']['length_violations'] += 1
            if not compliance['balance_ok']:
                self.detailed_stats['compliance_details']['balance_violations'] += 1
            if not compliance['content_ok']:
                self.detailed_stats['compliance_details']['content_violations'] += 1
            
            # 更新合规率
            total = self.metrics['total_splits']
            current_compliant = self.metrics['netflix_compliance_rate'] * (total - 1)
            self.metrics['netflix_compliance_rate'] = current_compliant / total
    
    def get_quality_report(self, time_window: str = 'all') -> Dict[str, Any]:
        """
        获取质量报告
        
        Args:
            time_window: 时间窗口 ('1h', '24h', '7d', 'all')
        """
        with self._lock:
            if time_window == 'all':
                return self._generate_full_report()
            else:
                return self._generate_window_report(time_window)
    
    def _generate_full_report(self) -> Dict[str, Any]:
        """生成完整报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.metrics.copy(),
            'performance': {
                'ai_success_rate': self.metrics['successful_ai_splits'] / max(self.metrics['total_splits'], 1),
                'fallback_rate': (self.metrics['fallback_splits'] + self.metrics['nlp_only_splits']) / max(self.metrics['total_splits'], 1),
                'error_rate': self.metrics['error_count'] / max(self.metrics['total_splits'], 1),
                'average_processing_time_ms': self.metrics['average_processing_time'] * 1000
            },
            'quality': {
                'average_similarity': self.metrics['average_similarity'],
                'compliance_rate': self.metrics['netflix_compliance_rate'],
                'similarity_distribution': self._get_similarity_distribution(),
                'compliance_violations': self.detailed_stats['compliance_details'].copy()
            },
            'trends': {
                'daily_counts': dict(self.detailed_stats['daily_counts']),
                'method_distribution': dict(self.detailed_stats['split_methods']),
                'error_types': dict(self.detailed_stats['error_types'])
            },
            'alerts': self._generate_alerts()
        }
        
        return report
    
    def _generate_window_report(self, window: str) -> Dict[str, Any]:
        """生成时间窗口报告"""
        if window not in self.time_windows:
            return {}
        
        records = list(self.time_windows[window])
        if not records:
            return {'message': f'No data in {window} window'}
        
        # 计算窗口统计
        total_count = len(records)
        ai_count = sum(1 for r in records if r['method'] == 'ai')
        error_count = sum(1 for r in records if r['error'])
        similarities = [r['similarity'] for r in records if r['similarity'] > 0]
        compliant_count = sum(1 for r in records if r['compliant'])
        
        return {
            'window': window,
            'timestamp': datetime.now().isoformat(),
            'total_operations': total_count,
            'ai_success_rate': ai_count / total_count if total_count > 0 else 0,
            'error_rate': error_count / total_count if total_count > 0 else 0,
            'average_similarity': sum(similarities) / len(similarities) if similarities else 0,
            'compliance_rate': compliant_count / total_count if total_count > 0 else 0,
            'processing_times': {
                'average': sum(r['processing_time'] for r in records) / total_count if total_count > 0 else 0,
                'max': max((r['processing_time'] for r in records), default=0),
                'min': min((r['processing_time'] for r in records), default=0)
            }
        }
    
    def _get_similarity_distribution(self) -> Dict[str, int]:
        """获取相似度分布"""
        scores = list(self.detailed_stats['similarity_scores'])
        if not scores:
            return {}
        
        distribution = {
            '0.9-1.0': 0,
            '0.8-0.9': 0,
            '0.7-0.8': 0,
            '0.6-0.7': 0,
            '0.0-0.6': 0
        }
        
        for score in scores:
            if score >= 0.9:
                distribution['0.9-1.0'] += 1
            elif score >= 0.8:
                distribution['0.8-0.9'] += 1
            elif score >= 0.7:
                distribution['0.7-0.8'] += 1
            elif score >= 0.6:
                distribution['0.6-0.7'] += 1
            else:
                distribution['0.0-0.6'] += 1
        
        return distribution
    
    def _generate_alerts(self) -> List[Dict[str, str]]:
        """生成质量警告"""
        alerts = []
        
        # 低相似度警告
        if self.metrics['average_similarity'] < self.thresholds['similarity_warning']:
            alerts.append({
                'level': 'warning',
                'type': 'low_similarity',
                'message': f"平均相似度 {self.metrics['average_similarity']:.3f} 低于阈值 {self.thresholds['similarity_warning']}"
            })
        
        # 高回退率警告
        total = self.metrics['total_splits']
        if total > 0:
            fallback_rate = (self.metrics['fallback_splits'] + self.metrics['nlp_only_splits']) / total
            if fallback_rate > self.thresholds['high_fallback_rate']:
                alerts.append({
                    'level': 'warning',
                    'type': 'high_fallback_rate',
                    'message': f"回退率 {fallback_rate:.3f} 超过阈值 {self.thresholds['high_fallback_rate']}"
                })
        
        # 低合规率警告
        if self.metrics['netflix_compliance_rate'] < self.thresholds['compliance_target']:
            alerts.append({
                'level': 'error',
                'type': 'low_compliance',
                'message': f"合规率 {self.metrics['netflix_compliance_rate']:.3f} 低于目标 {self.thresholds['compliance_target']}"
            })
        
        # 处理时间警告
        if self.metrics['average_processing_time'] > 1.0:  # 超过1秒
            alerts.append({
                'level': 'warning',
                'type': 'slow_processing',
                'message': f"平均处理时间 {self.metrics['average_processing_time']:.3f}s 过长"
            })
        
        return alerts
    
    def _check_report_schedule(self):
        """检查是否需要生成定期报告"""
        if not self.config:
            return
        
        frequency = self.config.quality_metrics.get('report_frequency', 'daily')
        now = datetime.now()
        
        if frequency == 'daily' and (now - self.last_report_time).days >= 1:
            self._generate_scheduled_report()
            self.last_report_time = now
        elif frequency == 'hourly' and (now - self.last_report_time).seconds >= 3600:
            self._generate_scheduled_report()
            self.last_report_time = now
    
    def _generate_scheduled_report(self):
        """生成定期报告"""
        report = self.get_quality_report()
        self.report_data.append(report)
        
        # 保存到文件
        if self.config and self.config.logging.get('enable_detailed_metrics', True):
            self._save_report_to_file(report)
    
    def _save_report_to_file(self, report: Dict[str, Any]):
        """保存报告到文件"""
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"netflix_quality_report_{timestamp}.json"
            filepath = logs_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"质量报告已保存: {filepath}")
        except Exception as e:
            self.logger.error(f"保存质量报告失败: {e}")
    
    def reset_metrics(self):
        """重置所有指标"""
        with self._lock:
            self.metrics = {
                'total_splits': 0,
                'successful_ai_splits': 0,
                'fallback_splits': 0,
                'nlp_only_splits': 0,
                'failed_splits': 0,
                'average_similarity': 0.0,
                'netflix_compliance_rate': 0.0,
                'average_processing_time': 0.0,
                'error_count': 0
            }
            
            self.detailed_stats = {
                'similarity_scores': deque(maxlen=1000),
                'processing_times': deque(maxlen=1000),
                'split_methods': defaultdict(int),
                'error_types': defaultdict(int),
                'daily_counts': defaultdict(int),
                'compliance_details': {
                    'length_violations': 0,
                    'balance_violations': 0,
                    'content_violations': 0
                }
            }
            
            for window in self.time_windows.values():
                window.clear()
    
    def export_metrics(self, filepath: str):
        """导出指标到文件"""
        with self._lock:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'metrics': self.metrics,
                'detailed_stats': {
                    'similarity_scores': list(self.detailed_stats['similarity_scores']),
                    'processing_times': list(self.detailed_stats['processing_times']),
                    'split_methods': dict(self.detailed_stats['split_methods']),
                    'error_types': dict(self.detailed_stats['error_types']),
                    'daily_counts': dict(self.detailed_stats['daily_counts']),
                    'compliance_details': self.detailed_stats['compliance_details']
                },
                'thresholds': self.thresholds
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"指标已导出到: {filepath}")
    
    def __repr__(self) -> str:
        return f"NetflixQualityMetrics(total_splits={self.metrics['total_splits']}, compliance_rate={self.metrics['netflix_compliance_rate']:.3f})"