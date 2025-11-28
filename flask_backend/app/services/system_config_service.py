"""
系统配置服务
从 MongoDB system_config 表读取和管理系统配置
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

from app.database.mongodb import get_db

logger = logging.getLogger(__name__)


class SystemConfigService:
    """系统配置服务 - 管理 system_config 表中的配置"""
    
    # 配置缓存 TTL (秒)
    CACHE_TTL = 300  # 5分钟
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.system_config
        self._cache = {}
        self._cache_time = {}
    
    def _is_cache_valid(self, config_key: str) -> bool:
        """检查缓存是否有效"""
        if config_key not in self._cache_time:
            return False
        elapsed = (datetime.utcnow() - self._cache_time[config_key]).total_seconds()
        return elapsed < self.CACHE_TTL
    
    def get_config(self, config_key: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取指定的系统配置
        
        Args:
            config_key: 配置键名
            use_cache: 是否使用缓存
            
        Returns:
            配置值字典，不存在返回 None
        """
        # 检查缓存
        if use_cache and self._is_cache_valid(config_key):
            return self._cache.get(config_key)
        
        # 从数据库读取
        doc = self.collection.find_one({'config_key': config_key})
        if doc:
            config_value = doc.get('config_value', {})
            # 更新缓存
            self._cache[config_key] = config_value
            self._cache_time[config_key] = datetime.utcnow()
            return config_value
        
        return None
    
    def set_config(self, config_key: str, config_value: Dict[str, Any]) -> bool:
        """
        设置系统配置
        
        Args:
            config_key: 配置键名
            config_value: 配置值
            
        Returns:
            是否成功
        """
        try:
            result = self.collection.update_one(
                {'config_key': config_key},
                {
                    '$set': {
                        'config_value': config_value,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # 清除缓存
            if config_key in self._cache:
                del self._cache[config_key]
            if config_key in self._cache_time:
                del self._cache_time[config_key]
            
            logger.info(f"系统配置已更新: {config_key}")
            return True
        except Exception as e:
            logger.error(f"更新系统配置失败: {config_key}, 错误: {e}")
            return False
    
    def update_config(self, config_key: str, updates: Dict[str, Any]) -> bool:
        """
        部分更新系统配置
        
        Args:
            config_key: 配置键名
            updates: 要更新的字段
            
        Returns:
            是否成功
        """
        try:
            # 构建更新路径
            update_dict = {}
            for key, value in updates.items():
                update_dict[f'config_value.{key}'] = value
            update_dict['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {'config_key': config_key},
                {'$set': update_dict}
            )
            
            # 清除缓存
            if config_key in self._cache:
                del self._cache[config_key]
            if config_key in self._cache_time:
                del self._cache_time[config_key]
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"部分更新系统配置失败: {config_key}, 错误: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有系统配置"""
        configs = {}
        for doc in self.collection.find():
            config_key = doc.get('config_key')
            if config_key:
                configs[config_key] = {
                    'config_value': doc.get('config_value', {}),
                    'updated_at': doc.get('updated_at')
                }
        return configs
    
    def clear_cache(self):
        """清除所有缓存"""
        self._cache.clear()
        self._cache_time.clear()
    
    # ============ 便捷方法 ============
    
    def get_system_settings(self) -> Dict[str, Any]:
        """获取系统设置"""
        return self.get_config('system_settings') or {}
    
    def get_default_user_config(self) -> Dict[str, Any]:
        """获取默认用户配置模板"""
        return self.get_config('default_user_config') or {}
    
    def get_render_config(self) -> Dict[str, Any]:
        """获取渲染配置"""
        return self.get_config('render_config') or {}
    
    def get_tts_services_config(self) -> Dict[str, Any]:
        """获取 TTS 服务配置"""
        return self.get_config('tts_services') or {}
    
    def get_ai_services_config(self) -> Dict[str, Any]:
        """获取 AI 服务配置"""
        return self.get_config('ai_services') or {}
    
    def get_manual_split_config(self) -> Dict[str, Any]:
        """获取手动分割配置"""
        return self.get_config('manual_split_config') or {}
    
    def is_maintenance_mode(self) -> bool:
        """检查是否处于维护模式"""
        settings = self.get_system_settings()
        return settings.get('maintenance_mode', False)
    
    def is_registration_allowed(self) -> bool:
        """检查是否允许用户注册"""
        settings = self.get_system_settings()
        return settings.get('allow_registration', False)


# 全局单例
_system_config_service: Optional[SystemConfigService] = None


def get_system_config_service() -> SystemConfigService:
    """获取系统配置服务单例"""
    global _system_config_service
    if _system_config_service is None:
        _system_config_service = SystemConfigService()
    return _system_config_service


# ============ 便捷函数 ============

def get_system_setting(key: str, default: Any = None) -> Any:
    """
    获取单个系统设置值
    
    Args:
        key: 设置键名
        default: 默认值
        
    Returns:
        设置值
    """
    service = get_system_config_service()
    settings = service.get_system_settings()
    return settings.get(key, default)


def get_default_config_for_new_user() -> Dict[str, Any]:
    """
    获取新用户的默认配置
    用于 user_configs 表初始化
    """
    service = get_system_config_service()
    return service.get_default_user_config()
