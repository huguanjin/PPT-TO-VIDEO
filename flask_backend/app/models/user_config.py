"""
用户配置数据模型
每个用户一条记录，存储该用户的所有个性化配置
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from bson import ObjectId

from app.database.mongodb import get_db


@dataclass
class UserConfig:
    """用户配置数据模型"""
    user_id: ObjectId
    ai: Dict[str, Any] = field(default_factory=dict)
    tts: Dict[str, Any] = field(default_factory=dict)
    video: Dict[str, Any] = field(default_factory=dict)
    subtitle: Dict[str, Any] = field(default_factory=dict)
    smart_subtitle: Dict[str, Any] = field(default_factory=dict)
    netflix_v2: Dict[str, Any] = field(default_factory=dict)
    advanced_features: Dict[str, Any] = field(default_factory=dict)
    image_generation: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = None
    
    def to_dict(self, include_id: bool = True) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'user_id': str(self.user_id),
            'ai': self.ai,
            'tts': self.tts,
            'video': self.video,
            'subtitle': self.subtitle,
            'smart_subtitle': self.smart_subtitle,
            'netflix_v2': self.netflix_v2,
            'advanced_features': self.advanced_features,
            'image_generation': self.image_generation,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_id and self._id:
            data['id'] = str(self._id)
        return data
    
    def to_db_dict(self) -> Dict[str, Any]:
        """转换为数据库文档格式"""
        return {
            'user_id': self.user_id,
            'ai': self.ai,
            'tts': self.tts,
            'video': self.video,
            'subtitle': self.subtitle,
            'smart_subtitle': self.smart_subtitle,
            'netflix_v2': self.netflix_v2,
            'advanced_features': self.advanced_features,
            'image_generation': self.image_generation,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserConfig':
        """从字典创建"""
        user_id = data.get('user_id')
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            user_id=user_id,
            ai=data.get('ai', {}),
            tts=data.get('tts', {}),
            video=data.get('video', {}),
            subtitle=data.get('subtitle', {}),
            smart_subtitle=data.get('smart_subtitle', {}),
            netflix_v2=data.get('netflix_v2', {}),
            advanced_features=data.get('advanced_features', {}),
            image_generation=data.get('image_generation', {}),
            updated_at=updated_at or datetime.utcnow(),
            _id=data.get('_id')
        )


class UserConfigService:
    """用户配置服务"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.user_configs
    
    def get_by_user_id(self, user_id: str) -> Optional[UserConfig]:
        """根据用户ID获取配置"""
        doc = self.collection.find_one({'user_id': ObjectId(user_id)})
        if doc:
            return UserConfig.from_dict(doc)
        return None
    
    def create_config(self, user_id: str, config_data: Dict[str, Any] = None) -> UserConfig:
        """
        创建用户配置
        
        Args:
            user_id: 用户ID
            config_data: 初始配置数据，如果为空则使用系统默认配置
        """
        # 检查是否已存在
        existing = self.get_by_user_id(user_id)
        if existing:
            return existing
        
        # 获取默认配置
        if config_data is None:
            from app.models.system_config import get_system_config_service
            sys_config_service = get_system_config_service()
            default_config = sys_config_service.get_default_user_config()
            config_data = default_config or {}
        
        config = UserConfig(
            user_id=ObjectId(user_id),
            ai=config_data.get('ai', {}),
            tts=config_data.get('tts', {}),
            video=config_data.get('video', {}),
            subtitle=config_data.get('subtitle', {}),
            smart_subtitle=config_data.get('smart_subtitle', {}),
            netflix_v2=config_data.get('netflix_v2', {}),
            advanced_features=config_data.get('advanced_features', {}),
            image_generation=config_data.get('image_generation', {})
        )
        
        doc = config.to_db_dict()
        result = self.collection.insert_one(doc)
        config._id = result.inserted_id
        
        return config
    
    def update_config(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新用户配置（部分更新）
        
        Args:
            user_id: 用户ID
            updates: 要更新的配置字段
        """
        # 构建更新操作
        set_fields = {'updated_at': datetime.utcnow()}
        
        # 支持的配置字段
        allowed_fields = ['ai', 'tts', 'video', 'subtitle', 'smart_subtitle', 
                         'netflix_v2', 'advanced_features', 'image_generation']
        
        for field in allowed_fields:
            if field in updates:
                set_fields[field] = updates[field]
        
        result = self.collection.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': set_fields},
            upsert=True  # 如果不存在则创建
        )
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    def update_section(self, user_id: str, section: str, data: Dict[str, Any]) -> bool:
        """
        更新配置的某个部分（深度合并）
        
        Args:
            user_id: 用户ID
            section: 配置部分 (ai, tts, video, subtitle 等)
            data: 要更新的数据
        """
        # 获取当前配置
        config = self.get_by_user_id(user_id)
        
        if config:
            # 获取现有部分数据
            current_data = getattr(config, section, {})
            # 深度合并
            merged_data = self._deep_merge(current_data, data)
        else:
            merged_data = data
        
        return self.update_config(user_id, {section: merged_data})
    
    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """深度合并两个字典"""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def delete_config(self, user_id: str) -> bool:
        """删除用户配置"""
        result = self.collection.delete_one({'user_id': ObjectId(user_id)})
        return result.deleted_count > 0
    
    def reset_to_default(self, user_id: str) -> bool:
        """重置为默认配置"""
        # 删除现有配置
        self.delete_config(user_id)
        # 重新创建（会使用默认配置）
        self.create_config(user_id)
        return True


# 便捷函数
def get_user_config_service() -> UserConfigService:
    """获取用户配置服务实例"""
    return UserConfigService()
