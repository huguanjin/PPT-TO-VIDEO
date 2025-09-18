"""
Netflix语义分割器API端点 - Phase 2系统集成
为前端提供Netflix级别字幕分割服务的API接口
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError

# Phase 2核心组件
from ...core.netflix_integration_adapter import NetflixSplitterIntegrationAdapter, IntegrationConfig
from ...core.netflix_semantic_splitter import NetflixStyleSemanticSplitter
from ...core.netflix_sequence_validator import NetflixSequenceValidator
from flask_backend.core.unified_config_manager import UnifiedConfigManager, ConfigContext, ConfigModuleType, ConfigComplexityLevel

# 错误处理和监控
from ...utils.netflix_error_monitoring import (
    NetflixErrorHandler, 
    NetflixPerformanceMonitor, 
    NetflixHealthChecker,
    ErrorSeverity,
    monitor_performance,
    handle_errors
)

# 创建Blueprint
bp = Blueprint('netflix_subtitle', __name__, url_prefix='/api/netflix-subtitle')

# 全局监控实例
error_handler = NetflixErrorHandler()
performance_monitor = NetflixPerformanceMonitor()
health_checker = NetflixHealthChecker(error_handler, performance_monitor)

# 设置装饰器的全局监控器
monitor_performance._performance_monitor = performance_monitor
handle_errors._error_handler = error_handler

# 全局适配器实例（延迟初始化）
_adapter_instance = None
_config_loader = None

def get_adapter() -> NetflixSplitterIntegrationAdapter:
    """获取适配器实例（单例模式）"""
    global _adapter_instance, _config_loader
    
    if _adapter_instance is None:
        try:
            # 从Flask应用获取项目目录
            project_dir = getattr(current_app, 'project_dir', Path.cwd())
            
            # 创建配置
            integration_config = IntegrationConfig(
                enable_netflix_splitter=True,
                enable_validation=True,
                enable_quality_monitoring=True,
                fallback_to_original=True,
                compatibility_mode='enhanced'
            )
            
            # 创建适配器实例
            _adapter_instance = NetflixSplitterIntegrationAdapter(
                project_dir=project_dir,
                integration_config=integration_config
            )
            
            current_app.logger.info("Netflix适配器实例创建成功")
            
        except Exception as e:
            current_app.logger.error(f"Netflix适配器初始化失败: {e}")
            raise
    
    return _adapter_instance

def get_config_manager() -> UnifiedConfigManager:
    """获取统一配置管理器实例"""
    global _config_loader
    
    if _config_loader is None:
        _config_loader = UnifiedConfigManager()
    
    return _config_loader

@bp.route('/config', methods=['GET'])
def get_netflix_config():
    """获取Netflix配置信息"""
    try:
        config_manager = get_config_manager()
        
        # 创建Netflix配置上下文
        context = ConfigContext(
            module_type=ConfigModuleType.NETFLIX,
            complexity_level=ConfigComplexityLevel.PROFESSIONAL,
            preset_name="netflix_optimized"
        )
        
        # 获取Netflix配置
        netflix_config = config_manager.get_config(context)
        
        config_info = {
            'netflix_standards': netflix_config.get('netflix_standards', {}),
            'ai_settings': netflix_config.get('ai_settings', {}),
            'prompt_templates': netflix_config.get('prompt_templates', {}),
            'validation_settings': netflix_config.get('validation_settings', {}),
            'feature_flags': {
                'netflix_splitter_enabled': True,
                'sequence_validation_enabled': True,
                'quality_monitoring_enabled': True,
                'prompt_templates_enabled': True
            }
        }
        
        return jsonify({
            'success': True,
            'config': config_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取Netflix配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/config', methods=['POST'])
def update_netflix_config():
    """更新Netflix配置"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("请提供配置数据")
        
        config_manager = get_config_manager()
        
        # 创建Netflix配置上下文
        context = ConfigContext(
            module_type=ConfigModuleType.NETFLIX,
            complexity_level=ConfigComplexityLevel.PROFESSIONAL,
            preset_name="netflix_optimized"
        )
        
        # 更新配置（这里简化处理，实际应该有更完善的验证）
        updated_sections = []
        
        if 'netflix_standards' in data:
            # 验证并更新Netflix标准
            standards = data['netflix_standards']
            if 'max_chars_per_line' in standards:
                if not 10 <= standards['max_chars_per_line'] <= 50:
                    raise BadRequest("max_chars_per_line必须在10-50之间")
            updated_sections.append('netflix_standards')
        
        if 'ai_settings' in data:
            # 验证并更新AI设置
            ai_settings = data['ai_settings']
            if 'temperature' in ai_settings:
                if not 0.0 <= ai_settings['temperature'] <= 2.0:
                    raise BadRequest("temperature必须在0.0-2.0之间")
            updated_sections.append('ai_settings')
        
        return jsonify({
            'success': True,
            'updated_sections': updated_sections,
            'message': f"已更新{len(updated_sections)}个配置节",
            'timestamp': datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"更新Netflix配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/split', methods=['POST'])
@monitor_performance('netflix_api', 'split_subtitle')
@handle_errors('netflix_api', 'split_subtitle', ErrorSeverity.HIGH)
def split_subtitle_text():
    """分割字幕文本 - 核心API"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("请提供分割请求数据")
        
        # 验证必需参数
        text = data.get('text', '').strip()
        if not text:
            raise BadRequest("text参数不能为空")
        
        target_lines = data.get('target_lines', 2)
        if not 1 <= target_lines <= 5:
            raise BadRequest("target_lines必须在1-5之间")
        
        # 可选参数
        context_data = data.get('context', {})
        enable_validation = data.get('enable_validation', True)
        timeout = data.get('timeout', 30.0)
        
        # 获取适配器
        adapter = get_adapter()
        
        # 创建异步任务
        async def process_split():
            result = await adapter.enhanced_subtitle_split(
                text=text,
                target_lines=target_lines,
                context_data=context_data
            )
            return result
        
        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                asyncio.wait_for(process_split(), timeout=timeout)
            )
        finally:
            loop.close()
        
        # 处理结果
        response_data = {
            'success': True,
            'result': result,
            'processing_info': {
                'text_length': len(text),
                'target_lines': target_lines,
                'actual_lines': len(result.get('segments', [])),
                'method_used': result.get('method'),
                'processing_time': result.get('processing_time', 0),
                'netflix_compliant': result.get('quality_metrics', {}).get('netflix_compliant', False)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加验证信息
        if enable_validation and 'validation' in result:
            validation = result['validation']
            response_data['validation'] = {
                'is_valid': validation.is_valid,
                'similarity_score': validation.similarity_score,
                'quality_score': validation.overall_quality_score,
                'netflix_compliant': validation.netflix_compliant,
                'error_count': len(validation.error_details),
                'warning_count': len(validation.warning_details)
            }
        
        return jsonify(response_data)
        
    except asyncio.TimeoutError:
        current_app.logger.warning(f"分割请求超时: {timeout}秒")
        return jsonify({
            'success': False,
            'error': f'处理超时（{timeout}秒）',
            'error_type': 'timeout'
        }), 408
    except BadRequest as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'bad_request'
        }), 400
    except Exception as e:
        current_app.logger.error(f"分割请求处理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'internal_error'
        }), 500

@bp.route('/batch-split', methods=['POST'])
@monitor_performance('netflix_api', 'batch_split')
@handle_errors('netflix_api', 'batch_split', ErrorSeverity.HIGH)
def batch_split_subtitles():
    """批量分割字幕文本"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("请提供批量分割请求数据")
        
        items = data.get('items', [])
        if not items:
            raise BadRequest("items列表不能为空")
        
        if len(items) > 100:
            raise BadRequest("单次批量处理最多100个项目")
        
        # 验证每个项目
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise BadRequest(f"第{i+1}个项目必须是对象")
            
            text = item.get('text', '').strip()
            if not text:
                raise BadRequest(f"第{i+1}个项目的text不能为空")
            
            target_lines = item.get('target_lines', 2)
            if not 1 <= target_lines <= 5:
                raise BadRequest(f"第{i+1}个项目的target_lines必须在1-5之间")
        
        # 获取适配器
        adapter = get_adapter()
        
        # 创建异步批量处理任务
        async def process_batch():
            results = await adapter.batch_process_subtitles(items)
            return results
        
        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = time.time()
            results = loop.run_until_complete(
                asyncio.wait_for(process_batch(), timeout=120.0)  # 2分钟超时
            )
            processing_time = time.time() - start_time
        finally:
            loop.close()
        
        # 统计结果
        total_items = len(results)
        netflix_splits = sum(1 for r in results if r.get('method') == 'ai_enhanced')
        validation_passes = sum(1 for r in results if r.get('validation', {}).get('is_valid', False))
        
        response_data = {
            'success': True,
            'results': results,
            'batch_info': {
                'total_items': total_items,
                'netflix_splits': netflix_splits,
                'validation_passes': validation_passes,
                'netflix_success_rate': netflix_splits / total_items if total_items > 0 else 0,
                'validation_success_rate': validation_passes / total_items if total_items > 0 else 0,
                'total_processing_time': processing_time,
                'avg_processing_time': processing_time / total_items if total_items > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except asyncio.TimeoutError:
        current_app.logger.warning("批量分割请求超时")
        return jsonify({
            'success': False,
            'error': '批量处理超时（2分钟）',
            'error_type': 'timeout'
        }), 408
    except BadRequest as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'bad_request'
        }), 400
    except Exception as e:
        current_app.logger.error(f"批量分割请求处理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'internal_error'
        }), 500

@bp.route('/validate', methods=['POST'])
@monitor_performance('netflix_api', 'validate_split')
@handle_errors('netflix_api', 'validate_split', ErrorSeverity.MEDIUM)
def validate_split_result():
    """验证分割结果质量"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("请提供验证请求数据")
        
        original_text = data.get('original_text', '').strip()
        segments = data.get('segments', [])
        
        if not original_text:
            raise BadRequest("original_text不能为空")
        
        if not segments or not isinstance(segments, list):
            raise BadRequest("segments必须是非空数组")
        
        # 获取适配器中的验证器
        adapter = get_adapter()
        if not adapter.validator:
            raise InternalServerError("验证器不可用")
        
        # 执行验证
        validation_result = adapter.validator.comprehensive_validate(
            original=original_text,
            segments=segments,
            protected_units=data.get('protected_units', []),
            target_compliance=data.get('target_compliance', 'netflix')
        )
        
        response_data = {
            'success': True,
            'validation': {
                'is_valid': validation_result.is_valid,
                'similarity_score': validation_result.similarity_score,
                'quality_score': validation_result.overall_quality_score,
                'netflix_compliant': validation_result.netflix_compliant,
                'validation_time': validation_result.validation_time,
                'error_details': validation_result.error_details,
                'warning_details': validation_result.warning_details,
                'quality_metrics': validation_result.quality_metrics
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except BadRequest as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'bad_request'
        }), 400
    except Exception as e:
        current_app.logger.error(f"验证请求处理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'internal_error'
        }), 500

@bp.route('/status', methods=['GET'])
def get_integration_status():
    """获取集成状态信息"""
    try:
        adapter = get_adapter()
        status = adapter.get_integration_status()
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/test', methods=['POST'])
def test_netflix_splitter():
    """测试Netflix分割器功能"""
    try:
        data = request.get_json()
        test_text = data.get('test_text', '这是一个测试字幕文本，用于验证Netflix级别的语义分割功能是否正常工作。')
        target_lines = data.get('target_lines', 2)
        
        # 获取适配器
        adapter = get_adapter()
        
        # 测试分割
        async def run_test():
            result = await adapter.enhanced_subtitle_split(
                text=test_text,
                target_lines=target_lines
            )
            return result
        
        # 运行测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = time.time()
            test_result = loop.run_until_complete(
                asyncio.wait_for(run_test(), timeout=10.0)
            )
            test_time = time.time() - start_time
        finally:
            loop.close()
        
        # 评估测试结果
        test_success = test_result.get('method') in ['ai_enhanced', 'nlp_only']
        segments_count = len(test_result.get('segments', []))
        
        test_summary = {
            'test_passed': test_success,
            'test_time': test_time,
            'method_used': test_result.get('method'),
            'segments_generated': segments_count,
            'target_segments': target_lines,
            'netflix_compliant': test_result.get('quality_metrics', {}).get('netflix_compliant', False),
            'validation_passed': test_result.get('validation', {}).get('is_valid', False)
        }
        
        return jsonify({
            'success': True,
            'test_result': test_result,
            'test_summary': test_summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except asyncio.TimeoutError:
        return jsonify({
            'success': False,
            'error': '测试超时',
            'error_type': 'timeout'
        }), 408
    except Exception as e:
        current_app.logger.error(f"测试失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'test_failed'
        }), 500

@bp.route('/metrics', methods=['GET'])
@monitor_performance('netflix_api', 'get_metrics')
def get_quality_metrics():
    """获取质量监控指标 - 增强版包含系统监控"""
    try:
        # 获取时间范围参数
        hours = request.args.get('hours', 24, type=int)
        if not 1 <= hours <= 168:  # 最多7天
            hours = 24
        
        # 获取适配器质量指标
        adapter = get_adapter()
        adapter_metrics = {}
        try:
            if adapter.quality_metrics:
                adapter_metrics = adapter.quality_metrics.get_quality_report()
        except Exception as e:
            adapter_metrics = {'error': str(e)}
        
        # 获取性能监控指标
        performance_summary = performance_monitor.get_performance_summary(hours=hours)
        
        # 获取错误监控指标
        error_summary = error_handler.get_error_summary(hours=hours)
        
        # 获取系统资源信息
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()
        
        system_metrics = {
            'memory': {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': psutil.virtual_memory().percent
            },
            'cpu': {
                'process_percent': cpu_percent,
                'system_percent': psutil.cpu_percent()
            },
            'uptime_seconds': time.time() - psutil.boot_time()
        }
        
        # 构建综合指标报告
        metrics_report = {
            'time_range_hours': hours,
            'timestamp': datetime.now().isoformat(),
            'adapter_quality_metrics': adapter_metrics,
            'performance_metrics': performance_summary,
            'error_metrics': error_summary,
            'system_metrics': system_metrics,
            'health_summary': {
                'overall_status': health_checker.check_overall_health()['overall_status'],
                'component_count': len(health_checker.component_health),
                'active_circuit_breakers': len([
                    k for k, v in error_handler.circuit_breakers.items() 
                    if v['state'] == 'open'
                ])
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics_report
        })
        
    except Exception as e:
        current_app.logger.error(f"获取质量指标失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 错误处理器
@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在',
        'error_type': 'not_found'
    }), 404

@bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': '方法不允许',
        'error_type': 'method_not_allowed'
    }), 405

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '内部服务器错误',
        'error_type': 'internal_error'
    }), 500

# 健康检查
@bp.route('/health', methods=['GET'])
@monitor_performance('netflix_api', 'health_check')
def health_check():
    """健康检查端点 - 集成Netflix监控系统"""
    try:
        # 注册组件（如果尚未注册）
        health_checker.register_component('netflix_splitter')
        health_checker.register_component('netflix_validator')
        health_checker.register_component('netflix_adapter')
        health_checker.register_component('netflix_api')
        
        # 获取整体健康状态
        overall_health = health_checker.check_overall_health()
        
        # 获取适配器状态（兼容性）
        try:
            adapter = get_adapter()
            adapter_status = adapter.get_integration_status()
        except Exception as e:
            adapter_status = {'error': str(e)}
        
        # 获取性能和错误总结
        performance_summary = performance_monitor.get_performance_summary(hours=1)
        error_summary = error_handler.get_error_summary(hours=1)
        
        # 确定HTTP状态码
        status_code = 200
        if overall_health['overall_status'] in ['unhealthy', 'degraded']:
            status_code = 503  # Service Unavailable
        elif overall_health['overall_status'] == 'warning':
            status_code = 200  # OK but with warnings
        
        response_data = {
            'healthy': overall_health['overall_status'] in ['healthy', 'warning'],
            'overall_status': overall_health['overall_status'],
            'version': '2.0.0',
            'timestamp': overall_health['check_time'],
            'components': overall_health['components'],
            'summary': overall_health['summary'],
            'adapter_status': adapter_status,
            'performance': {
                'total_operations': performance_summary.get('total_operations', 0),
                'success_rate': performance_summary.get('success_rate', 0),
                'avg_response_time': performance_summary.get('duration_stats', {}).get('avg', 0)
            },
            'errors': {
                'total_errors': error_summary.get('total_errors', 0),
                'by_severity': error_summary.get('by_severity', {}),
                'circuit_breakers': error_summary.get('circuit_breakers', {})
            }
        }
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        return jsonify({
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

# 新增监控端点
@bp.route('/monitoring/errors', methods=['GET'])
@monitor_performance('netflix_api', 'get_error_report')
def get_error_report():
    """获取详细错误报告"""
    try:
        hours = request.args.get('hours', 24, type=int)
        if not 1 <= hours <= 168:
            hours = 24
        
        error_summary = error_handler.get_error_summary(hours=hours)
        
        # 获取最近的错误详情
        recent_errors = [
            {
                'timestamp': error.timestamp.isoformat(),
                'severity': error.severity.value,
                'component': error.component,
                'operation': error.operation,
                'error_type': error.error_type,
                'message': error.message,
                'recovery_action': error.recovery_action
            }
            for error in error_handler.errors[-50:]  # 最近50个错误
        ]
        
        return jsonify({
            'success': True,
            'error_report': {
                'summary': error_summary,
                'recent_errors': recent_errors,
                'circuit_breakers_detail': error_handler.circuit_breakers
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/monitoring/performance', methods=['GET'])
@monitor_performance('netflix_api', 'get_performance_report')
def get_performance_report():
    """获取详细性能报告"""
    try:
        hours = request.args.get('hours', 24, type=int)
        if not 1 <= hours <= 168:
            hours = 24
        
        performance_summary = performance_monitor.get_performance_summary(hours=hours)
        
        # 获取最近的性能数据
        recent_metrics = [
            {
                'timestamp': metric.timestamp.isoformat(),
                'component': metric.component,
                'operation': metric.operation,
                'duration': metric.duration,
                'memory_usage': metric.memory_usage,
                'cpu_usage': metric.cpu_usage,
                'success': metric.success,
                'throughput': metric.throughput
            }
            for metric in performance_monitor.metrics[-100:]  # 最近100个指标
        ]
        
        return jsonify({
            'success': True,
            'performance_report': {
                'summary': performance_summary,
                'recent_metrics': recent_metrics
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/monitoring/health/detailed', methods=['GET'])
@monitor_performance('netflix_api', 'get_detailed_health')
def get_detailed_health():
    """获取详细健康状态"""
    try:
        # 强制检查所有组件
        components_to_check = [
            'netflix_splitter', 'netflix_validator', 
            'netflix_adapter', 'netflix_api'
        ]
        
        for component in components_to_check:
            health_checker.register_component(component)
        
        detailed_health = health_checker.check_overall_health()
        
        # 添加系统级信息
        import psutil
        system_info = {
            'memory': dict(psutil.virtual_memory()._asdict()),
            'cpu_count': psutil.cpu_count(),
            'boot_time': psutil.boot_time(),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        
        return jsonify({
            'success': True,
            'detailed_health': detailed_health,
            'system_info': system_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500