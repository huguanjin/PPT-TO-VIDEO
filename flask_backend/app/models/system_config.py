"""
系统配置数据模型
存储全局系统设置，只有管理员可修改
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from bson import ObjectId
import json
from pathlib import Path

from app.database.mongodb import get_db


@dataclass
class SystemConfig:
    """系统配置数据模型"""
    config_key: str
    config_value: Dict[str, Any]
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[ObjectId] = None
    _id: Optional[ObjectId] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'config_key': self.config_key,
            'config_value': self.config_value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': str(self.updated_by) if self.updated_by else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """从字典创建"""
        updated_by = data.get('updated_by')
        if isinstance(updated_by, str):
            updated_by = ObjectId(updated_by)
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            config_key=data.get('config_key', ''),
            config_value=data.get('config_value', {}),
            updated_at=updated_at or datetime.utcnow(),
            updated_by=updated_by,
            _id=data.get('_id')
        )


class SystemConfigService:
    """系统配置服务"""
    
    # 预定义的配置键
    CONFIG_KEYS = {
        'default_user_config': '新用户的默认配置模板',
        'system_settings': '系统全局设置',
        'tts_voices_cache': 'TTS语音列表缓存',
    }
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.system_config
    
    def get_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """获取系统配置"""
        doc = self.collection.find_one({'config_key': config_key})
        if doc:
            return doc.get('config_value')
        return None
    
    def set_config(self, config_key: str, config_value: Dict[str, Any], 
                   updated_by: str = None) -> bool:
        """设置系统配置"""
        update_data = {
            'config_key': config_key,
            'config_value': config_value,
            'updated_at': datetime.utcnow()
        }
        
        if updated_by:
            update_data['updated_by'] = ObjectId(updated_by)
        
        result = self.collection.update_one(
            {'config_key': config_key},
            {'$set': update_data},
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    def get_default_user_config(self) -> Dict[str, Any]:
        """获取新用户的默认配置"""
        config = self.get_config('default_user_config')
        
        if config:
            return config
        
        # 如果数据库中没有，从文件读取
        return self._load_default_from_file()
    
    def _load_default_from_file(self) -> Dict[str, Any]:
        """从文件加载默认配置"""
        config_path = Path(__file__).parent.parent.parent / "config_data" / "app_config.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = json.load(f)
            
            # 提取用户配置相关字段
            return {
                'ai': full_config.get('ai', {}),
                'tts': full_config.get('tts', {}),
                'video': full_config.get('video', {}),
                'subtitle': full_config.get('subtitle', {}),
                'smart_subtitle': full_config.get('smart_subtitle', {}),
                'netflix_v2': full_config.get('netflix_v2', {}),
                'advanced_features': full_config.get('advanced_features', {})
            }
        
        return {}
    
    def get_system_settings(self) -> Dict[str, Any]:
        """获取系统设置"""
        config = self.get_config('system_settings')
        
        if config:
            return config
        
        # 返回默认系统设置
        return {
            'allow_registration': False,
            'max_video_duration': 3600,
            'max_slides_count': 100,
            'maintenance_mode': False
        }
    
    def update_system_settings(self, updates: Dict[str, Any], updated_by: str = None) -> bool:
        """更新系统设置"""
        current = self.get_system_settings()
        current.update(updates)
        return self.set_config('system_settings', current, updated_by)
    
    def get_tts_voices_cache(self) -> Optional[Dict[str, Any]]:
        """获取TTS语音列表缓存"""
        return self.get_config('tts_voices_cache')
    
    def set_tts_voices_cache(self, voices_data: Dict[str, Any]) -> bool:
        """设置TTS语音列表缓存"""
        return self.set_config('tts_voices_cache', voices_data)
    
    def list_all_configs(self) -> List[Dict[str, Any]]:
        """列出所有系统配置"""
        configs = []
        for doc in self.collection.find():
            configs.append(SystemConfig.from_dict(doc).to_dict())
        return configs
    
    def delete_config(self, config_key: str) -> bool:
        """删除系统配置"""
        result = self.collection.delete_one({'config_key': config_key})
        return result.deleted_count > 0
    
    def init_default_configs(self) -> None:
        """初始化默认系统配置（首次启动时调用）"""
        # 初始化默认用户配置
        if not self.get_config('default_user_config'):
            default_config = self._load_default_from_file()
            if default_config:
                self.set_config('default_user_config', default_config)
        
        # 初始化系统设置
        if not self.get_config('system_settings'):
            self.set_config('system_settings', {
                'allow_registration': False,
                'max_video_duration': 3600,
                'max_slides_count': 100,
                'maintenance_mode': False
            })


# 便捷函数
def get_system_config_service() -> SystemConfigService:
    """获取系统配置服务实例"""
    return SystemConfigService()
