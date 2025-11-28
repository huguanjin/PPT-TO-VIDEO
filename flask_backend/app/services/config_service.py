"""
配置服务
提供统一的配置访问接口，实现配置继承机制
"""

from typing import Optional, Dict, Any
from datetime import datetime
import copy

from app.models.user_config import get_user_config_service, UserConfig
from app.models.system_config import get_system_config_service


class ConfigService:
    """
    配置服务
    
    配置继承机制:
    1. 读取 system_config.default_user_config (系统默认)
    2. 读取 user_configs.{user_id} (用户自定义)
    3. 深度合并: 用户配置覆盖系统默认
    4. 返回最终配置
    """
    
    def __init__(self):
        self.user_config_service = get_user_config_service()
        self.system_config_service = get_system_config_service()
    
    def get_user_config(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的完整配置（合并系统默认和用户自定义）
        
        Args:
            user_id: 用户ID，如果为 'anonymous' 则返回系统默认配置
            
        Returns:
            合并后的完整配置
        """
        # 获取系统默认配置
        default_config = self.system_config_service.get_default_user_config()
        
        # 匿名用户直接返回默认配置
        if user_id == 'anonymous':
            return default_config
        
        # 获取用户配置
        user_config = self.user_config_service.get_by_user_id(user_id)
        
        if not user_config:
            # 用户没有自定义配置，返回默认配置
            return default_config
        
        # 深度合并配置
        merged_config = self._deep_merge(default_config, user_config.to_dict())
        
        return merged_config
    
    def get_user_config_section(self, user_id: str, section: str) -> Dict[str, Any]:
        """
        获取用户配置的某个部分
        
        Args:
            user_id: 用户ID
            section: 配置部分 (ai, tts, video, subtitle 等)
            
        Returns:
            配置部分数据
        """
        full_config = self.get_user_config(user_id)
        return full_config.get(section, {})
    
    def update_user_config(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新用户配置
        
        Args:
            user_id: 用户ID
            updates: 要更新的配置字段
            
        Returns:
            是否更新成功
        """
        if user_id == 'anonymous':
            return False
        
        return self.user_config_service.update_config(user_id, updates)
    
    def update_user_config_section(self, user_id: str, section: str, 
                                   data: Dict[str, Any]) -> bool:
        """
        更新用户配置的某个部分
        
        Args:
            user_id: 用户ID
            section: 配置部分
            data: 要更新的数据
            
        Returns:
            是否更新成功
        """
        if user_id == 'anonymous':
            return False
        
        return self.user_config_service.update_section(user_id, section, data)
    
    def reset_user_config(self, user_id: str) -> bool:
        """
        重置用户配置为默认值
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否重置成功
        """
        if user_id == 'anonymous':
            return False
        
        return self.user_config_service.reset_to_default(user_id)
    
    def get_system_settings(self) -> Dict[str, Any]:
        """获取系统设置"""
        return self.system_config_service.get_system_settings()
    
    def update_system_settings(self, updates: Dict[str, Any], 
                               updated_by: str = None) -> bool:
        """更新系统设置（需要管理员权限）"""
        return self.system_config_service.update_system_settings(updates, updated_by)
    
    def get_default_user_config(self) -> Dict[str, Any]:
        """获取默认用户配置模板"""
        return self.system_config_service.get_default_user_config()
    
    def update_default_user_config(self, config: Dict[str, Any], 
                                   updated_by: str = None) -> bool:
        """更新默认用户配置模板（需要管理员权限）"""
        return self.system_config_service.set_config(
            'default_user_config', config, updated_by
        )
    
    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """
        深度合并两个字典
        updates 中的值会覆盖 base 中的值
        """
        result = copy.deepcopy(base)
        
        for key, value in updates.items():
            # 跳过元数据字段
            if key in ['id', 'user_id', 'updated_at', '_id']:
                continue
            
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif value is not None:
                result[key] = value
        
        return result
    
    def ensure_user_config_exists(self, user_id: str) -> None:
        """
        确保用户配置存在
        如果不存在则创建默认配置
        """
        if user_id == 'anonymous':
            return
        
        existing = self.user_config_service.get_by_user_id(user_id)
        if not existing:
            self.user_config_service.create_config(user_id)


# 便捷函数
def get_config_service() -> ConfigService:
    """获取配置服务实例"""
    return ConfigService()


# ============================================================
# 兼容函数：替代原有的 JSON 文件读取
# ============================================================

def get_ai_config(user_id: str = 'anonymous') -> Dict[str, Any]:
    """获取 AI 配置"""
    service = get_config_service()
    return service.get_user_config_section(user_id, 'ai')


def get_tts_config(user_id: str = 'anonymous') -> Dict[str, Any]:
    """获取 TTS 配置"""
    service = get_config_service()
    return service.get_user_config_section(user_id, 'tts')


def get_video_config(user_id: str = 'anonymous') -> Dict[str, Any]:
    """获取视频配置"""
    service = get_config_service()
    return service.get_user_config_section(user_id, 'video')


def get_subtitle_config(user_id: str = 'anonymous') -> Dict[str, Any]:
    """获取字幕配置"""
    service = get_config_service()
    return service.get_user_config_section(user_id, 'subtitle')


def get_advanced_features(user_id: str = 'anonymous') -> Dict[str, Any]:
    """获取高级功能配置"""
    service = get_config_service()
    return service.get_user_config_section(user_id, 'advanced_features')
