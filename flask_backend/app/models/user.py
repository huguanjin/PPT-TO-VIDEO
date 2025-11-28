"""
用户数据模型
提供用户的创建、查询、验证等功能
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from bson import ObjectId

from app.database.mongodb import get_db
from app.database.init_db import hash_password, verify_password, generate_salt


@dataclass
class User:
    """用户数据模型"""
    username: str
    password: str  # 存储格式: salt:hash
    role: str = "user"  # admin | user
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    _id: Optional[ObjectId] = None
    
    def to_dict(self, exclude_password: bool = True) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        if self._id:
            data['id'] = str(self._id)
        if not exclude_password:
            data['password'] = self.password
        return data
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return verify_password(password, self.password)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """从字典创建用户对象"""
        return cls(
            username=data.get('username', ''),
            password=data.get('password', ''),
            role=data.get('role', 'user'),
            created_at=data.get('created_at', datetime.utcnow()),
            last_login=data.get('last_login'),
            _id=data.get('_id')
        )


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.users
    
    def create_user(self, username: str, password: str, role: str = "user") -> Optional[User]:
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 明文密码
            role: 角色 (admin/user)
            
        Returns:
            创建的用户对象，失败返回 None
        """
        # 检查用户名是否已存在
        if self.get_by_username(username):
            return None
        
        # 哈希密码
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        
        # 创建用户文档
        user_doc = {
            'username': username,
            'password': password_hash,
            'role': role,
            'created_at': datetime.utcnow(),
            'last_login': None
        }
        
        result = self.collection.insert_one(user_doc)
        
        if result.inserted_id:
            user_doc['_id'] = result.inserted_id
            return User.from_dict(user_doc)
        
        return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_doc = self.collection.find_one({'username': username})
        if user_doc:
            return User.from_dict(user_doc)
        return None
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        try:
            user_doc = self.collection.find_one({'_id': ObjectId(user_id)})
            if user_doc:
                return User.from_dict(user_doc)
        except Exception:
            pass
        return None
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        
        Returns:
            验证成功返回用户对象，失败返回 None
        """
        user = self.get_by_username(username)
        if user and user.verify_password(password):
            # 更新最后登录时间
            self.update_last_login(str(user._id))
            return user
        return None
    
    def update_last_login(self, user_id: str) -> bool:
        """更新最后登录时间"""
        try:
            result = self.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def update_password(self, user_id: str, new_password: str) -> bool:
        """更新用户密码"""
        try:
            salt = generate_salt()
            password_hash = hash_password(new_password, salt)
            
            result = self.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'password': password_hash}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            # 不允许删除 admin
            user = self.get_by_id(user_id)
            if user and user.username == 'admin':
                return False
            
            result = self.collection.delete_one({'_id': ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        users = []
        cursor = self.collection.find().skip(skip).limit(limit)
        for user_doc in cursor:
            users.append(User.from_dict(user_doc))
        return users
    
    def count_users(self) -> int:
        """获取用户总数"""
        return self.collection.count_documents({})


# 便捷函数
def get_user_service() -> UserService:
    """获取用户服务实例"""
    return UserService()
