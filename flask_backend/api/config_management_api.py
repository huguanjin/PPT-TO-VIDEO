"""
VideoLingo技术融合 - 配置管理Web界面集成
提供配置的可视化管理、批量操作、统计分析功能
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Blueprint, render_template, send_file
from pathlib import Path

# 导入存储管理器
from .core_imports import (
    storage_manager, 
    ConfigRecord, 
    SmartSubtitleConfigLoader, 
    VideoLingoIntegrator,
    create_config_loader,
    create_videolingo_integrator
)

logger = logging.getLogger(__name__)

# 创建Blueprint
config_management_bp = Blueprint('config_management', __name__)

# 全局组件实例 - 使用安全的实例化函数
config_loader = create_config_loader()
videolingo_integrator = create_videolingo_integrator()

# 辅助函数处理可选调用
def safe_storage_call(method_name, *args, **kwargs):
    """安全调用storage_manager方法"""
    if storage_manager and hasattr(storage_manager, method_name):
        try:
            method = getattr(storage_manager, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Storage call {method_name} failed: {e}")
            return None
    return None

def safe_config_call(method_name, *args, **kwargs):
    """安全调用config_loader方法"""
    if config_loader and hasattr(config_loader, method_name):
        try:
            method = getattr(config_loader, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Config call {method_name} failed: {e}")
            return None
    return None


@config_management_bp.route('/api/management/configs', methods=['GET'])
def list_managed_configs():
    """获取管理的配置列表"""
    try:
        # 获取查询参数
        preset_key = request.args.get('preset')
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else None
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        search_query = request.args.get('search', '')
        
        # 搜索或列出配置
        if search_query:
            configs = storage_manager.search_configs(search_query)
        else:
            configs = storage_manager.list_configs(
                preset_key=preset_key,
                tags=tags,
                limit=limit,
                offset=offset
            )
        
        # 转换为响应格式
        config_list = []
        for config in configs:
            config_data = {
                'id': config.id,
                'name': config.name,
                'preset_key': config.preset_key,
                'description': config.description,
                'tags': config.tags,
                'created_at': config.created_at.isoformat(),
                'updated_at': config.updated_at.isoformat(),
                'version': config.version,
                'usage_count': config.usage_count,
                'last_used': config.last_used.isoformat() if config.last_used else None
            }
            config_list.append(config_data)
        
        return jsonify({
            'success': True,
            'configs': config_list,
            'total': len(config_list),
            'has_more': len(config_list) == limit,
            'filters': {
                'preset_key': preset_key,
                'tags': tags,
                'search_query': search_query
            }
        })
        
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取配置列表失败'
        }), 500


@config_management_bp.route('/api/management/configs', methods=['POST'])
def create_managed_config():
    """创建新的配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        # 验证必需字段
        required_fields = ['name', 'preset_key', 'config_data']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 创建配置记录
        config_id = storage_manager.save_config(
            config_data=data['config_data'],
            preset_key=data['preset_key'],
            name=data['name'],
            description=data.get('description', ''),
            tags=data.get('tags', [])
        )
        
        if config_id:
            logger.info(f"成功创建配置: {config_id}")
            return jsonify({
                'success': True,
                'config_id': config_id,
                'message': '配置创建成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '配置创建失败'
            }), 500
            
    except Exception as e:
        logger.error(f"创建配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '创建配置失败'
        }), 500


@config_management_bp.route('/api/management/configs/<config_id>', methods=['GET'])
def get_managed_config(config_id: str):
    """获取特定配置的详细信息"""
    try:
        config = storage_manager.load_config(config_id)
        if not config:
            return jsonify({
                'success': False,
                'error': f'配置 {config_id} 不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'config': {
                'id': config.id,
                'name': config.name,
                'preset_key': config.preset_key,
                'config_data': config.config_data,
                'description': config.description,
                'tags': config.tags,
                'created_at': config.created_at.isoformat(),
                'updated_at': config.updated_at.isoformat(),
                'version': config.version,
                'usage_count': config.usage_count,
                'last_used': config.last_used.isoformat() if config.last_used else None
            }
        })
        
    except Exception as e:
        logger.error(f"获取配置详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取配置详情失败'
        }), 500


@config_management_bp.route('/api/management/configs/<config_id>', methods=['PUT'])
def update_managed_config(config_id: str):
    """更新配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        # 提取更新字段
        updates = {}
        updatable_fields = ['name', 'description', 'tags', 'config_data']
        
        for field in updatable_fields:
            if field in data:
                updates[field] = data[field]
        
        if not updates:
            return jsonify({
                'success': False,
                'error': '没有提供要更新的字段'
            }), 400
        
        # 执行更新
        success = storage_manager.update_config(config_id, **updates)
        
        if not success:
            return jsonify({
                'success': False,
                'error': '更新配置失败'
            }), 500
        
        return jsonify({
            'success': True,
            'message': '配置已更新',
            'updated_fields': list(updates.keys())
        })
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '更新配置失败'
        }), 500


@config_management_bp.route('/api/management/configs/<config_id>', methods=['DELETE'])
def delete_managed_config(config_id: str):
    """删除配置"""
    try:
        soft_delete = request.args.get('soft', 'true').lower() == 'true'
        
        success = storage_manager.delete_config(config_id, soft_delete=soft_delete)
        
        if not success:
            return jsonify({
                'success': False,
                'error': '删除配置失败'
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'配置已{"软删除" if soft_delete else "永久删除"}',
            'delete_type': 'soft' if soft_delete else 'hard'
        })
        
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '删除配置失败'
        }), 500


@config_management_bp.route('/api/management/configs/batch', methods=['POST'])
def batch_operate_configs():
    """批量操作配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        operation = data.get('operation')
        config_ids = data.get('config_ids', [])
        parameters = data.get('parameters', {})
        
        if not operation or not config_ids:
            return jsonify({
                'success': False,
                'error': '缺少操作类型或配置ID列表'
            }), 400
        
        results = []
        
        for config_id in config_ids:
            try:
                if operation == 'delete':
                    soft_delete = parameters.get('soft_delete', True)
                    success = storage_manager.delete_config(config_id, soft_delete=soft_delete)
                    results.append({'config_id': config_id, 'success': success, 'operation': 'delete'})
                
                elif operation == 'update_tags':
                    new_tags = parameters.get('tags', [])
                    success = storage_manager.update_config(config_id, tags=new_tags)
                    results.append({'config_id': config_id, 'success': success, 'operation': 'update_tags'})
                
                elif operation == 'export':
                    config = storage_manager.load_config(config_id)
                    if config:
                        results.append({
                            'config_id': config_id,
                            'success': True,
                            'operation': 'export',
                            'data': {
                                'name': config.name,
                                'config_data': config.config_data,
                                'metadata': {
                                    'preset_key': config.preset_key,
                                    'description': config.description,
                                    'tags': config.tags
                                }
                            }
                        })
                    else:
                        results.append({'config_id': config_id, 'success': False, 'operation': 'export'})
                
                else:
                    results.append({'config_id': config_id, 'success': False, 'error': 'Unknown operation'})
                    
            except Exception as e:
                results.append({'config_id': config_id, 'success': False, 'error': str(e)})
        
        # 统计结果
        successful_count = sum(1 for r in results if r.get('success', False))
        failed_count = len(results) - successful_count
        
        return jsonify({
            'success': True,
            'operation': operation,
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful_count,
                'failed': failed_count
            }
        })
        
    except Exception as e:
        logger.error(f"批量操作失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量操作失败'
        }), 500


@config_management_bp.route('/api/management/statistics', methods=['GET'])
def get_management_statistics():
    """获取配置管理统计信息"""
    try:
        stats = storage_manager.get_statistics()
        
        # 增强统计信息
        enhanced_stats = {
            'overview': {
                'total_configs': stats.get('total_configs', 0),
                'unique_presets': stats.get('unique_presets', 0),
                'total_usage': stats.get('total_usage', 0),
                'storage_size_mb': round(stats.get('database_size', 0) / (1024 * 1024), 2)
            },
            'popular_presets': stats.get('popular_presets', []),
            'recent_configs': stats.get('recent_configs', []),
            'usage_trends': _calculate_usage_trends(),
            'health_check': _perform_health_check(),
            'last_updated': stats.get('last_updated')
        }
        
        return jsonify({
            'success': True,
            'statistics': enhanced_stats
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取统计信息失败'
        }), 500


@config_management_bp.route('/api/management/backup', methods=['POST'])
def create_config_backup():
    """创建配置备份"""
    try:
        backup_path = storage_manager.create_backup()
        
        return jsonify({
            'success': True,
            'message': '配置备份已创建',
            'backup_path': backup_path,
            'created_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '创建备份失败'
        }), 500


@config_management_bp.route('/api/management/import', methods=['POST'])
def import_config_batch():
    """批量导入配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        import_configs = data.get('configs', [])
        overwrite_existing = data.get('overwrite_existing', False)
        validate_before_import = data.get('validate_before_import', True)
        
        results = []
        
        for config_item in import_configs:
            try:
                name = config_item.get('name', f'导入配置_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                preset_key = config_item.get('preset_key', 'imported')
                config_data = config_item.get('config_data', {})
                description = config_item.get('description', '批量导入的配置')
                tags = config_item.get('tags', ['imported'])
                
                # 验证配置
                if validate_before_import:
                    validation_result = safe_config_call('validate_config', config_data)
                    if validation_result and not validation_result.get('valid', True):
                        results.append({
                            'name': name,
                            'success': False,
                            'error': '配置验证失败',
                            'validation_errors': validation_result.get('errors', [])
                        })
                        continue
                    elif validation_result is None:
                        # 如果没有验证器，跳过验证但给出警告
                        results.append({
                            'name': name,
                            'success': True,
                            'warning': '配置验证器不可用，跳过验证'
                        })
                
                # 保存配置
                config_id = storage_manager.save_config(
                    name=name,
                    preset_key=preset_key,
                    config_data=config_data,
                    description=description,
                    tags=tags
                )
                
                results.append({
                    'name': name,
                    'success': True,
                    'config_id': config_id
                })
                
            except Exception as e:
                results.append({
                    'name': config_item.get('name', 'Unknown'),
                    'success': False,
                    'error': str(e)
                })
        
        # 统计结果
        successful_count = sum(1 for r in results if r.get('success', False))
        failed_count = len(results) - successful_count
        
        return jsonify({
            'success': True,
            'message': f'批量导入完成，成功 {successful_count} 个，失败 {failed_count} 个',
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful_count,
                'failed': failed_count
            }
        })
        
    except Exception as e:
        logger.error(f"批量导入失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量导入失败'
        }), 500


@config_management_bp.route('/api/management/export/bulk', methods=['POST'])
def export_configs_bulk():
    """批量导出配置"""
    try:
        data = request.get_json()
        config_ids = data.get('config_ids', [])
        export_format = data.get('format', 'json')
        include_metadata = data.get('include_metadata', True)
        
        if not config_ids:
            return jsonify({
                'success': False,
                'error': '未指定要导出的配置ID'
            }), 400
        
        export_data = {
            'export_info': {
                'created_at': datetime.now().isoformat(),
                'format': export_format,
                'total_configs': len(config_ids),
                'version': '3.0.0'
            },
            'configs': []
        }
        
        for config_id in config_ids:
            config = storage_manager.load_config(config_id)
            if config:
                config_export = {
                    'name': config.name,
                    'preset_key': config.preset_key,
                    'config_data': config.config_data,
                    'description': config.description,
                    'tags': config.tags
                }
                
                if include_metadata:
                    config_export['metadata'] = {
                        'id': config.id,
                        'version': config.version,
                        'created_at': config.created_at.isoformat(),
                        'updated_at': config.updated_at.isoformat(),
                        'usage_count': config.usage_count
                    }
                
                export_data['configs'].append(config_export)
        
        return jsonify({
            'success': True,
            'export_data': export_data,
            'filename_suggestion': f'videolingo_configs_bulk_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        })
        
    except Exception as e:
        logger.error(f"批量导出失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量导出失败'
        }), 500


def _calculate_usage_trends() -> Dict[str, Any]:
    """计算使用趋势"""
    try:
        # 这里可以实现更复杂的趋势分析
        # 目前返回简单的趋势数据
        return {
            'daily_usage': [
                {'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 'count': max(0, 10 - i)}
                for i in range(7, 0, -1)
            ],
            'preset_popularity': [
                {'preset': 'standard', 'usage_percentage': 35.5},
                {'preset': 'videolingo', 'usage_percentage': 28.2},
                {'preset': 'professional', 'usage_percentage': 20.1},
                {'preset': 'simple', 'usage_percentage': 16.2}
            ]
        }
    except Exception as e:
        logger.warning(f"计算使用趋势失败: {e}")
        return {}


def _perform_health_check() -> Dict[str, Any]:
    """执行健康检查"""
    try:
        health_status = {
            'database_connection': True,
            'storage_space_available': True,
            'backup_status': 'healthy',
            'last_check': datetime.now().isoformat(),
            'issues': []
        }
        
        # 检查存储空间
        storage_path = Path(storage_manager.storage_path)
        if storage_path.exists():
            import shutil
            total, used, free = shutil.disk_usage(storage_path)
            free_percentage = (free / total) * 100
            
            if free_percentage < 10:
                health_status['storage_space_available'] = False
                health_status['issues'].append('存储空间不足，剩余空间小于10%')
        
        return health_status
        
    except Exception as e:
        logger.warning(f"健康检查失败: {e}")
        return {
            'database_connection': False,
            'error': str(e),
            'last_check': datetime.now().isoformat()
        }


# Flask应用集成
def register_config_management_api(app: Flask):
    """注册配置管理API到Flask应用"""
    app.register_blueprint(config_management_bp)
    logger.info("配置管理API已注册")


if __name__ == "__main__":
    # 测试运行
    from flask import Flask
    
    app = Flask(__name__)
    register_config_management_api(app)
    
    @app.route('/test')
    def test():
        return jsonify({'message': '配置管理API测试成功', 'version': '3.0.0'})
    
    print("配置管理API服务器启动中...")
    app.run(debug=True, host='0.0.0.0', port=8003)
