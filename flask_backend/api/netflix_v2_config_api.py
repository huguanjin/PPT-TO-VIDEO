"""
Netflix V2配置管理API
为Flask后端提供Netflix V2配置管理的RESTful API接口
支持配置CRUD、模板管理、配置验证等功能
"""
from flask import Blueprint, request, jsonify, current_app, Response
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

# 初始化logger
logger = logging.getLogger(__name__)

# 导入Netflix V2配置管理器
try:
    from ..core.netflix_v2_config_manager import (
        NetflixV2ConfigManager, 
        NetflixSubtitleConfig, 
        ConfigScope, 
        ConfigCategory,
        ConfigMetadata
    )
    CONFIG_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Netflix V2配置管理器导入失败: {e}")
    CONFIG_MANAGER_AVAILABLE = False
    # 创建占位符类
    NetflixV2ConfigManager = None
    NetflixSubtitleConfig = None
    ConfigScope = None
    ConfigCategory = None
    ConfigMetadata = None

# 创建Blueprint
netflix_config_api_v2 = Blueprint('netflix_config_api_v2', __name__, url_prefix='/api/v2/netflix/config')

# 全局配置管理器实例
_config_manager = None


def get_config_manager():
    """获取配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        if not CONFIG_MANAGER_AVAILABLE or NetflixV2ConfigManager is None:
            raise RuntimeError("Netflix V2配置管理器不可用")
        _config_manager = NetflixV2ConfigManager()
    return _config_manager


def create_error_response(message: str, error_code: str = "CONFIG_ERROR", status_code: int = 400) -> tuple:
    """创建错误响应"""
    return jsonify({
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        },
        "data": None
    }), status_code


def create_success_response(data: Any = None, message: str = "操作成功") -> Response:
    """创建成功响应"""
    return jsonify({
        "success": True,
        "error": None,
        "message": message,
        "data": data
    })


@netflix_config_api_v2.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        config_manager = get_config_manager()
        info = config_manager.get_config_info()
        
        return create_success_response({
            "status": "healthy",
            "config_manager_version": info["config_manager_version"],
            "netflix_v2_available": info["netflix_v2_available"],
            "total_templates": info["total_templates"],
            "total_user_configs": info["total_user_configs"]
        }, "Netflix V2配置管理服务正常运行")
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return create_error_response(f"配置管理服务异常: {str(e)}", "HEALTH_CHECK_FAILED", 503)


@netflix_config_api_v2.route('/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        config_manager = get_config_manager()
        info = config_manager.get_config_info()
        return create_success_response(info, "系统信息获取成功")
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return create_error_response(f"无法获取系统信息: {str(e)}")


@netflix_config_api_v2.route('/configs', methods=['GET'])
def list_configs():
    """列出所有可用配置"""
    try:
        config_manager = get_config_manager()
        configs = config_manager.list_available_configs()
        
        return create_success_response(configs, "配置列表获取成功")
        
    except Exception as e:
        logger.error(f"列出配置失败: {e}")
        return create_error_response(f"无法获取配置列表: {str(e)}")


@netflix_config_api_v2.route('/configs/<config_name>', methods=['GET'])
def get_config(config_name: str):
    """获取指定配置"""
    try:
        config_manager = get_config_manager()
        
        # 处理默认配置请求
        config_name_param: Optional[str] = config_name
        if config_name.lower() in ['default', 'global']:
            config_name_param = None
        
        config = config_manager.load_netflix_config(config_name_param)
        
        # 转换为字典格式
        config_dict = {
            "enabled": config.enabled,
            "style_preset": config.style_preset,
            "max_chars_per_line": config.max_chars_per_line,
            "validation_level": config.validation_level,
            "chinese_weight": config.chinese_weight,
            "english_weight": config.english_weight,
            "punctuation_weight": config.punctuation_weight,
            "enable_semantic_splitting": config.enable_semantic_splitting,
            "max_optimization_rounds": config.max_optimization_rounds,
            "quality_threshold": config.quality_threshold,
            "output_formats": config.output_formats,
            "font_color": config.font_color,
            "font_size": config.font_size,
            "outline_color": config.outline_color,
            "outline_width": config.outline_width,
            "background_alpha": config.background_alpha,
            "min_duration": config.min_duration,
            "max_duration": config.max_duration,
            "gap_threshold": config.gap_threshold,
            "enable_quality_validation": config.enable_quality_validation,
            "auto_fix_issues": config.auto_fix_issues,
            "strict_netflix_compliance": config.strict_netflix_compliance
        }
        
        return create_success_response({
            "config_name": config_name or "default",
            "config": config_dict
        }, f"配置'{config_name or 'default'}'获取成功")
        
    except FileNotFoundError:
        return create_error_response(f"配置'{config_name}'不存在", "CONFIG_NOT_FOUND", 404)
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return create_error_response(f"无法获取配置: {str(e)}")


@netflix_config_api_v2.route('/configs/<config_name>', methods=['POST', 'PUT'])
def save_config(config_name: str):
    """保存配置"""
    try:
        config_manager = get_config_manager()
        data = request.get_json()
        
        if not data:
            return create_error_response("请提供配置数据", "MISSING_DATA")
        
        # 提取配置数据
        config_data = data.get('config', {})
        metadata_data = data.get('metadata', {})
        scope_str = data.get('scope', 'user')
        
        # 创建配置对象
        try:
            if NetflixSubtitleConfig is None:
                return create_error_response("Netflix配置类不可用", "CONFIG_CLASS_UNAVAILABLE")
            config = NetflixSubtitleConfig(**config_data)
        except TypeError as e:
            return create_error_response(f"配置数据格式错误: {str(e)}", "INVALID_CONFIG_FORMAT")
        
        # 验证配置
        validation = config_manager.validate_config(config)
        if not validation["valid"]:
            return create_error_response(
                f"配置验证失败: {', '.join(validation['errors'])}", 
                "CONFIG_VALIDATION_FAILED"
            )
        
        # 创建元数据
        if ConfigScope is None:
            return create_error_response("配置范围类不可用", "CONFIG_SCOPE_UNAVAILABLE")
        scope = ConfigScope.USER if scope_str.lower() == 'user' else ConfigScope.TEMPLATE
        metadata = None
        
        if metadata_data:
            try:
                if ConfigMetadata is None or ConfigCategory is None:
                    return create_error_response("配置元数据类不可用", "CONFIG_METADATA_UNAVAILABLE")
                metadata = ConfigMetadata(
                    name=metadata_data.get('name', config_name),
                    description=metadata_data.get('description', f"Netflix配置: {config_name}"),
                    version=metadata_data.get('version', '2.0'),
                    category=ConfigCategory.NETFLIX_SUBTITLE,
                    scope=scope,
                    tags=metadata_data.get('tags', [])
                )
            except Exception as e:
                logger.warning(f"元数据创建失败，使用默认值: {e}")
        
        # 保存配置
        success = config_manager.save_netflix_config(config, config_name, scope, metadata)
        
        if success:
            return create_success_response({
                "config_name": config_name,
                "scope": scope.value,
                "validation": validation
            }, f"配置'{config_name}'保存成功")
        else:
            return create_error_response("配置保存失败", "SAVE_FAILED", 500)
        
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return create_error_response(f"无法保存配置: {str(e)}")


@netflix_config_api_v2.route('/configs/<config_name>/validate', methods=['POST'])
def validate_config(config_name: str):
    """验证配置"""
    try:
        config_manager = get_config_manager()
        data = request.get_json()
        
        if data and 'config' in data:
            # 验证提交的配置数据
            try:
                if NetflixSubtitleConfig is None:
                    return create_error_response("Netflix配置类不可用", "CONFIG_CLASS_UNAVAILABLE")
                config = NetflixSubtitleConfig(**data['config'])
            except TypeError as e:
                return create_error_response(f"配置数据格式错误: {str(e)}", "INVALID_CONFIG_FORMAT")
        else:
            # 验证已保存的配置
            try:
                config = config_manager.load_netflix_config(config_name)
            except FileNotFoundError:
                return create_error_response(f"配置'{config_name}'不存在", "CONFIG_NOT_FOUND", 404)
        
        # 执行验证
        validation = config_manager.validate_config(config)
        
        return create_success_response({
            "config_name": config_name,
            "validation": validation
        }, "配置验证完成")
        
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        return create_error_response(f"无法验证配置: {str(e)}")


@netflix_config_api_v2.route('/templates', methods=['GET'])
def list_templates():
    """列出所有配置模板"""
    try:
        config_manager = get_config_manager()
        configs = config_manager.list_available_configs()
        
        return create_success_response({
            "templates": configs["templates"]
        }, "模板列表获取成功")
        
    except Exception as e:
        logger.error(f"列出模板失败: {e}")
        return create_error_response(f"无法获取模板列表: {str(e)}")


@netflix_config_api_v2.route('/templates/<template_name>/create-config', methods=['POST'])
def create_from_template(template_name: str):
    """从模板创建配置"""
    try:
        config_manager = get_config_manager()
        data = request.get_json()
        
        if not data or 'config_name' not in data:
            return create_error_response("请提供新配置名称", "MISSING_CONFIG_NAME")
        
        new_config_name = data['config_name']
        customizations = data.get('customizations', {})
        
        # 从模板创建配置
        success = config_manager.create_config_from_template(
            template_name, 
            new_config_name, 
            customizations
        )
        
        if success:
            return create_success_response({
                "template_name": template_name,
                "new_config_name": new_config_name,
                "customizations_applied": len(customizations)
            }, f"从模板'{template_name}'创建配置'{new_config_name}'成功")
        else:
            return create_error_response("从模板创建配置失败", "TEMPLATE_CREATE_FAILED", 500)
        
    except Exception as e:
        logger.error(f"从模板创建配置失败: {e}")
        return create_error_response(f"无法从模板创建配置: {str(e)}")


@netflix_config_api_v2.route('/configs/<config_name>/export', methods=['GET'])
def export_config(config_name: str):
    """导出配置"""
    try:
        config_manager = get_config_manager()
        
        # 获取导出路径参数
        export_format = request.args.get('format', 'json')
        if export_format != 'json':
            return create_error_response("目前只支持JSON格式导出", "UNSUPPORTED_FORMAT")
        
        # 加载配置并转换为导出格式
        config = config_manager.load_netflix_config(config_name)
        
        # 准备导出数据
        from datetime import datetime
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "config_manager_version": "2.0",
                "original_config_name": config_name or "default"
            },
            "metadata": {
                "name": f"Exported {config_name or 'default'}",
                "description": f"导出的Netflix配置: {config_name or 'default'}",
                "version": "2.0",
                "category": "netflix_subtitle",
                "scope": "user"
            },
            "config": {
                "enabled": config.enabled,
                "style_preset": config.style_preset,
                "max_chars_per_line": config.max_chars_per_line,
                "validation_level": config.validation_level,
                "chinese_weight": config.chinese_weight,
                "english_weight": config.english_weight,
                "punctuation_weight": config.punctuation_weight,
                "enable_semantic_splitting": config.enable_semantic_splitting,
                "max_optimization_rounds": config.max_optimization_rounds,
                "quality_threshold": config.quality_threshold,
                "output_formats": config.output_formats,
                "font_color": config.font_color,
                "font_size": config.font_size,
                "outline_color": config.outline_color,
                "outline_width": config.outline_width,
                "background_alpha": config.background_alpha,
                "min_duration": config.min_duration,
                "max_duration": config.max_duration,
                "gap_threshold": config.gap_threshold,
                "enable_quality_validation": config.enable_quality_validation,
                "auto_fix_issues": config.auto_fix_issues,
                "strict_netflix_compliance": config.strict_netflix_compliance
            }
        }
        
        return create_success_response({
            "config_name": config_name or "default",
            "export_data": export_data
        }, f"配置'{config_name or 'default'}'导出成功")
        
    except FileNotFoundError:
        return create_error_response(f"配置'{config_name}'不存在", "CONFIG_NOT_FOUND", 404)
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        return create_error_response(f"无法导出配置: {str(e)}")


@netflix_config_api_v2.route('/configs/import', methods=['POST'])
def import_config():
    """导入配置"""
    try:
        config_manager = get_config_manager()
        data = request.get_json()
        
        if not data:
            return create_error_response("请提供导入数据", "MISSING_DATA")
        
        # 提取导入数据
        import_data = data.get('import_data')
        new_config_name = data.get('config_name')
        
        if not import_data:
            return create_error_response("请提供有效的导入数据", "INVALID_IMPORT_DATA")
        
        # 验证导入数据格式
        if 'config' not in import_data:
            return create_error_response("导入数据缺少配置信息", "INVALID_IMPORT_FORMAT")
        
        # 创建配置对象
        try:
            if NetflixSubtitleConfig is None:
                return create_error_response("Netflix配置类不可用", "CONFIG_CLASS_UNAVAILABLE")
            config = NetflixSubtitleConfig(**import_data['config'])
        except TypeError as e:
            return create_error_response(f"导入配置数据格式错误: {str(e)}", "INVALID_CONFIG_FORMAT")
        
        # 确定配置名称
        if not new_config_name:
            export_info = import_data.get("export_info", {})
            metadata = import_data.get("metadata", {})
            new_config_name = (
                export_info.get("original_config_name") or 
                metadata.get("name") or 
                "imported_config"
            )
        
        # 验证配置
        validation = config_manager.validate_config(config)
        if not validation["valid"]:
            return create_error_response(
                f"导入配置验证失败: {', '.join(validation['errors'])}", 
                "IMPORT_VALIDATION_FAILED"
            )
        
        # 创建元数据
        from flask_backend.core.netflix_v2_config_manager import ConfigMetadata, ConfigScope, ConfigCategory
        metadata = ConfigMetadata(
            name=new_config_name,
            description=f"导入的Netflix配置",
            version="2.0",
            category=ConfigCategory.NETFLIX_SUBTITLE,
            scope=ConfigScope.USER,
            tags=["imported"]
        )
        
        # 保存配置
        success = config_manager.save_netflix_config(config, new_config_name, ConfigScope.USER, metadata)
        
        if success:
            return create_success_response({
                "config_name": new_config_name,
                "validation": validation
            }, f"配置'{new_config_name}'导入成功")
        else:
            return create_error_response("配置导入保存失败", "IMPORT_SAVE_FAILED", 500)
        
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        return create_error_response(f"无法导入配置: {str(e)}")


@netflix_config_api_v2.route('/configs/<config_name>', methods=['DELETE'])
def delete_config(config_name: str):
    """删除配置"""
    try:
        config_manager = get_config_manager()
        
        # 不允许删除默认配置
        if config_name.lower() in ['default', 'global']:
            return create_error_response("不能删除默认配置", "CANNOT_DELETE_DEFAULT", 403)
        
        # 查找配置文件
        user_config_file = config_manager.user_configs_dir / f"{config_name}.json"
        template_file = config_manager.templates_dir / f"{config_name}.json"
        
        deleted = False
        file_type = ""
        
        if user_config_file.exists():
            user_config_file.unlink()
            deleted = True
            file_type = "用户配置"
        elif template_file.exists():
            template_file.unlink()
            deleted = True
            file_type = "配置模板"
        
        if deleted:
            return create_success_response({
                "config_name": config_name,
                "file_type": file_type
            }, f"{file_type}'{config_name}'删除成功")
        else:
            return create_error_response(f"配置'{config_name}'不存在", "CONFIG_NOT_FOUND", 404)
        
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        return create_error_response(f"无法删除配置: {str(e)}")


# 错误处理器
@netflix_config_api_v2.errorhandler(404)
def not_found(error):
    return create_error_response("请求的资源不存在", "NOT_FOUND", 404)


@netflix_config_api_v2.errorhandler(500)
def internal_error(error):
    return create_error_response("服务器内部错误", "INTERNAL_ERROR", 500)


# 初始化函数
def init_netflix_config_api_v2(app):
    """初始化Netflix V2配置管理API"""
    if not CONFIG_MANAGER_AVAILABLE:
        logger.warning("Netflix V2配置管理器不可用，跳过API注册")
        return
    
    try:
        # 注册Blueprint
        app.register_blueprint(netflix_config_api_v2)
        
        # 初始化配置管理器
        get_config_manager()
        
        logger.info("Netflix V2配置管理API初始化成功")
        
    except Exception as e:
        logger.error(f"Netflix V2配置管理API初始化失败: {e}")
        raise


if __name__ == "__main__":
    # 测试API功能
    from flask import Flask
    
    print("🧪 Netflix V2配置管理API测试")
    print("=" * 50)
    
    app = Flask(__name__)
    init_netflix_config_api_v2(app)
    
    with app.test_client() as client:
        # 测试健康检查
        response = client.get('/api/v2/netflix/config/health')
        print(f"健康检查: {response.status_code}")
        
        # 测试获取系统信息
        response = client.get('/api/v2/netflix/config/info')
        if response.status_code == 200:
            data = response.get_json()
            print(f"系统信息获取成功: {data['data']['config_manager_version']}")
        
        # 测试列出配置
        response = client.get('/api/v2/netflix/config/configs')
        if response.status_code == 200:
            data = response.get_json()
            print(f"配置列表: {len(data['data']['templates'])}个模板")
    
    print("\n✅ Netflix V2配置管理API测试完成！")