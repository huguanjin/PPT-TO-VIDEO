"""
API依赖注入
"""
from fastapi import Depends
import logging
from typing import Annotated
from config.manager import ConfigManager
from .services.tts_service import TTSService
from .services.workflow_service import WorkflowService
from .services.storage_service import StorageService

# 全局配置管理器
_config_manager = None
_tts_service = None
_workflow_service = None
_storage_service = None

def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_logger() -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(__name__)

def get_tts_service(
    config_manager: Annotated[ConfigManager, Depends(get_config_manager)]
) -> TTSService:
    """获取TTS服务实例"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService(config_manager)
    return _tts_service

def get_workflow_service(
    config_manager: Annotated[ConfigManager, Depends(get_config_manager)]
) -> WorkflowService:
    """获取工作流服务实例"""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService(config_manager)
    return _workflow_service

def get_storage_service(
    config_manager: Annotated[ConfigManager, Depends(get_config_manager)]
) -> StorageService:
    """获取存储服务实例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService(config_manager)
    return _storage_service
