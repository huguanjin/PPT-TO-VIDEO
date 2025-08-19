"""
配置API路由
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_config_manager
from config.manager import ConfigManager
from ..exceptions import ConfigurationException, ValidationException

router = APIRouter(prefix="/config", tags=["Configuration"])

# 请求模型
class ConfigUpdateRequest(BaseModel):
    config_type: str
    updates: Dict[str, Any]

class ConfigItem(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

# 响应模型
class ConfigResponse(BaseModel):
    config_type: str
    config: Dict[str, Any]

@router.get("/types")
async def get_config_types(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取配置类型列表"""
    
    return {
        "config_types": [
            {
                "name": "tts",
                "display_name": "TTS配置",
                "description": "Text-to-Speech引擎配置"
            },
            {
                "name": "fish_tts", 
                "display_name": "Fish TTS配置",
                "description": "Fish TTS专用配置"
            },
            {
                "name": "workflow",
                "display_name": "工作流配置",
                "description": "工作流处理配置"
            },
            {
                "name": "video",
                "display_name": "视频配置", 
                "description": "视频生成配置"
            },
            {
                "name": "subtitle",
                "display_name": "字幕配置",
                "description": "字幕生成配置"
            },
            {
                "name": "app",
                "display_name": "应用配置",
                "description": "应用程序配置"
            }
        ]
    }

@router.get("/all")
async def get_all_configs(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取所有配置"""
    
    try:
        all_configs = config_manager.get_all_configs()
        return {"configs": all_configs}
        
    except Exception as e:
        raise ConfigurationException(f"获取配置失败: {str(e)}")

@router.get("/{config_type}", response_model=ConfigResponse)
async def get_config(
    config_type: str,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取指定类型的配置"""
    
    try:
        config = config_manager.get_config(config_type)
        
        return ConfigResponse(
            config_type=config_type,
            config=config
        )
        
    except Exception as e:
        raise ConfigurationException(f"获取配置失败: {str(e)}")

@router.get("/{config_type}/{key}")
async def get_config_value(
    config_type: str,
    key: str,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取配置项的值"""
    
    try:
        value = config_manager.get_config(config_type, key)
        
        return {
            "config_type": config_type,
            "key": key,
            "value": value
        }
        
    except Exception as e:
        raise ConfigurationException(f"获取配置值失败: {str(e)}")

@router.put("/{config_type}")
async def update_config(
    config_type: str,
    updates: Dict[str, Any],
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """更新配置"""
    
    if not updates:
        raise ValidationException("更新数据不能为空", "updates")
    
    try:
        success = config_manager.update_config(config_type, updates)
        
        if not success:
            raise ConfigurationException(f"更新配置失败: {config_type}")
        
        return {
            "config_type": config_type,
            "updated": True,
            "message": "配置更新成功"
        }
        
    except Exception as e:
        raise ConfigurationException(f"更新配置失败: {str(e)}")

@router.post("/{config_type}/reload")
async def reload_config(
    config_type: str,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """重新加载配置"""
    
    try:
        success = config_manager.reload_config(config_type)
        
        if not success:
            raise ConfigurationException(f"重新加载配置失败: {config_type}")
        
        return {
            "config_type": config_type,
            "reloaded": True,
            "message": "配置重新加载成功"
        }
        
    except Exception as e:
        raise ConfigurationException(f"重新加载配置失败: {str(e)}")

@router.get("/{config_type}/validate")
async def validate_config(
    config_type: str,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """验证配置"""
    
    try:
        is_valid = config_manager.validate_config(config_type)
        
        return {
            "config_type": config_type,
            "valid": is_valid,
            "message": "配置有效" if is_valid else "配置无效"
        }
        
    except Exception as e:
        raise ConfigurationException(f"验证配置失败: {str(e)}")

# TTS配置的专用端点
@router.get("/tts/engines")
async def get_tts_engines_config(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取TTS引擎配置"""
    
    try:
        tts_config = config_manager.get_config("tts")
        fish_tts_config = config_manager.get_config("fish_tts")
        
        return {
            "engines": {
                "general": tts_config,
                "fish_tts": fish_tts_config
            }
        }
        
    except Exception as e:
        raise ConfigurationException(f"获取TTS引擎配置失败: {str(e)}")

@router.put("/tts/engines/{engine_name}")
async def update_tts_engine_config(
    engine_name: str,
    config_updates: Dict[str, Any],
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """更新TTS引擎配置"""
    
    if not config_updates:
        raise ValidationException("配置更新不能为空", "config_updates")
    
    try:
        if engine_name == "fish_tts":
            success = config_manager.update_config("fish_tts", config_updates)
        else:
            # 更新通用TTS配置中的特定引擎
            tts_config = config_manager.get_config("tts") or {}
            tts_config[engine_name] = config_updates
            success = config_manager.update_config("tts", tts_config)
        
        if not success:
            raise ConfigurationException(f"更新{engine_name}配置失败")
        
        return {
            "engine": engine_name,
            "updated": True,
            "message": f"{engine_name}配置更新成功"
        }
        
    except Exception as e:
        raise ConfigurationException(f"更新{engine_name}配置失败: {str(e)}")

# 应用配置的专用端点
@router.get("/app/settings")
async def get_app_settings(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取应用设置"""
    
    try:
        app_config = config_manager.get_config("app")
        
        # 提供默认设置
        default_settings = {
            "auto_save_interval": 300,  # 5分钟
            "max_file_size": 100,       # 100MB
            "theme": "light",
            "language": "zh-CN"
        }
        
        # 合并默认设置和用户设置
        settings = {**default_settings, **app_config}
        
        return {"settings": settings}
        
    except Exception as e:
        raise ConfigurationException(f"获取应用设置失败: {str(e)}")

@router.put("/app/settings")
async def update_app_settings(
    settings: Dict[str, Any],
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """更新应用设置"""
    
    if not settings:
        raise ValidationException("设置不能为空", "settings")
    
    try:
        success = config_manager.update_config("app", settings)
        
        if not success:
            raise ConfigurationException("更新应用设置失败")
        
        return {
            "updated": True,
            "message": "应用设置更新成功"
        }
        
    except Exception as e:
        raise ConfigurationException(f"更新应用设置失败: {str(e)}")
