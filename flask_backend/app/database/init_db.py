"""
数据库初始化模块
- 首次启动自动创建管理员账户
- 创建必要的数据库索引
- 初始化系统配置
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

from .mongodb import get_db

logger = logging.getLogger(__name__)


def generate_salt() -> str:
    """生成随机盐值（32字符十六进制）"""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """
    使用 SHA256 哈希密码
    返回格式: salt:hash
    """
    hash_obj = hashlib.sha256((salt + password).encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, stored_password: str) -> bool:
    """
    验证密码
    stored_password 格式: salt:hash
    """
    try:
        salt, stored_hash = stored_password.split(':', 1)
        hash_obj = hashlib.sha256((salt + password).encode('utf-8'))
        return hash_obj.hexdigest() == stored_hash
    except Exception:
        return False


def generate_random_password(length: int = 16) -> str:
    """生成随机密码"""
    # 使用字母和数字，避免特殊字符以方便复制
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_admin_user(db) -> Tuple[bool, Optional[str]]:
    """
    创建管理员用户
    返回: (是否新创建, 密码或None)
    """
    users_collection = db.users
    
    # 检查是否已存在管理员
    existing_admin = users_collection.find_one({'username': 'admin'})
    if existing_admin:
        logger.info("管理员账户已存在，跳过创建")
        return False, None
    
    # 生成随机密码
    raw_password = generate_random_password(16)
    
    # 加密密码
    salt = generate_salt()
    password_hash = hash_password(raw_password, salt)
    
    # 创建管理员文档
    admin_user = {
        'username': 'admin',
        'password': password_hash,
        'role': 'admin',
        'created_at': datetime.utcnow(),
        'last_login': None
    }
    
    # 插入数据库
    result = users_collection.insert_one(admin_user)
    
    if result.inserted_id:
        logger.info(f"✅ 管理员账户创建成功，ID: {result.inserted_id}")
        return True, raw_password
    else:
        logger.error("❌ 管理员账户创建失败")
        return False, None


def save_admin_credentials(password: str, base_path: Optional[Path] = None) -> str:
    """
    保存管理员凭据到文件
    返回文件路径
    """
    if base_path is None:
        # 默认保存到 flask_backend 目录
        base_path = Path(__file__).parent.parent.parent
    
    credentials_file = base_path / 'admin_credentials.txt'
    
    content = f"""===========================================
PPT-TO-VIDEO 管理员凭据
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===========================================

用户名: admin
密码: {password}

⚠️ 重要提示:
1. 请立即登录并修改此密码
2. 请妥善保管此文件或删除
3. 此密码仅在首次初始化时生成

===========================================
"""
    
    with open(credentials_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 尝试设置文件权限（仅限Unix系统）
    try:
        os.chmod(credentials_file, 0o600)
    except Exception:
        pass  # Windows 系统忽略
    
    logger.info(f"✅ 管理员凭据已保存到: {credentials_file}")
    return str(credentials_file)


def create_indexes(db) -> None:
    """创建数据库索引"""
    logger.info("创建数据库索引...")
    
    # users 集合索引
    db.users.create_index('username', unique=True)
    logger.info("  - users.username (unique)")
    
    # user_configs 集合索引
    db.user_configs.create_index('user_id', unique=True)
    logger.info("  - user_configs.user_id (unique)")
    
    # tasks 集合索引
    db.tasks.create_index('user_id')
    db.tasks.create_index([('user_id', 1), ('status', 1)])
    logger.info("  - tasks.user_id")
    logger.info("  - tasks.(user_id, status)")
    
    # system_config 集合索引
    db.system_config.create_index('config_key', unique=True)
    logger.info("  - system_config.config_key (unique)")
    
    logger.info("✅ 索引创建完成")


def init_system_config(db) -> None:
    """
    初始化系统配置
    从模板文件加载配置到 system_config 表
    """
    import json
    
    logger.info("初始化系统配置...")
    
    system_config = db.system_config
    
    # 从模板文件加载配置
    template_path = Path(__file__).parent.parent.parent / "templates" / "default_system_config.json"
    
    if not template_path.exists():
        logger.warning(f"系统配置模板文件不存在: {template_path}")
        # 使用最小化的默认配置
        configs_to_init = {
            'system_settings': {
                'allow_registration': False,
                'max_video_duration': 3600,
                'max_slides_count': 100,
                'maintenance_mode': False
            },
            'default_user_config': {}
        }
    else:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        # 提取需要初始化的配置（排除 _meta）
        configs_to_init = {}
        for key, value in template_data.items():
            if not key.startswith('_'):
                configs_to_init[key] = value.get('config_value', value)
    
    # 初始化每个配置项
    for config_key, config_value in configs_to_init.items():
        config_doc = {
            'config_key': config_key,
            'config_value': config_value,
            'updated_at': datetime.utcnow()
        }
        
        # 使用 $setOnInsert 确保只在首次创建时设置值
        result = system_config.update_one(
            {'config_key': config_key},
            {'$setOnInsert': config_doc},
            upsert=True
        )
        
        if result.upserted_id:
            logger.info(f"  - 创建配置: {config_key}")
        else:
            logger.info(f"  - 配置已存在: {config_key}")
    
    logger.info("✅ 系统配置初始化完成")


def init_database() -> dict:
    """
    初始化数据库
    - 创建索引
    - 创建管理员账户（如果不存在）
    - 初始化系统配置
    
    返回初始化结果
    """
    result = {
        'success': False,
        'admin_created': False,
        'credentials_file': None,
        'indexes_created': False,
        'system_config_initialized': False,
        'error': None
    }
    
    try:
        logger.info("=" * 50)
        logger.info("开始数据库初始化...")
        logger.info("=" * 50)
        
        # 获取数据库连接
        db = get_db()
        
        if db is None:
            raise ConnectionError("无法连接到数据库")
        
        # 1. 创建索引
        create_indexes(db)
        result['indexes_created'] = True
        
        # 2. 创建管理员账户
        admin_created, password = create_admin_user(db)
        result['admin_created'] = admin_created
        
        if admin_created and password:
            # 保存凭据文件
            credentials_file = save_admin_credentials(password)
            result['credentials_file'] = credentials_file
            
            logger.info("")
            logger.info("=" * 50)
            logger.info("🎉 管理员账户已创建！")
            logger.info(f"   用户名: admin")
            logger.info(f"   密码已保存到: {credentials_file}")
            logger.info("=" * 50)
            logger.info("")
        
        # 3. 初始化系统配置
        init_system_config(db)
        result['system_config_initialized'] = True
        
        result['success'] = True
        logger.info("✅ 数据库初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        result['error'] = str(e)
    
    return result


# 密码工具函数（供其他模块使用）
__all__ = [
    'init_database',
    'hash_password',
    'verify_password',
    'generate_salt',
    'generate_random_password'
]
