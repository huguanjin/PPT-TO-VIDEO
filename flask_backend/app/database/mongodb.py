"""
MongoDB 连接管理模块
实现单例模式的数据库连接管理，支持连接池和重试机制
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Optional
from threading import Lock

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoDBClient:
    """
    MongoDB 客户端单例类
    确保整个应用只有一个数据库连接实例
    """
    
    _instance: Optional['MongoDBClient'] = None
    _lock: Lock = Lock()
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls) -> 'MongoDBClient':
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化（只执行一次）"""
        if self._client is None:
            self._connect()
    
    def _load_config(self) -> dict:
        """
        加载 MongoDB 配置
        优先级: 环境变量 > mongo_config.yaml
        """
        config = {
            'connection_string': None,
            'database_name': 'PPTTOVideo'
        }
        
        # 1. 尝试从环境变量读取
        if os.environ.get('MONGODB_URI'):
            config['connection_string'] = os.environ['MONGODB_URI']
            config['database_name'] = os.environ.get('MONGODB_DATABASE', 'PPTTOVideo')
            logger.info("从环境变量加载 MongoDB 配置")
            return config
        
        # 2. 尝试从配置文件读取
        config_paths = [
            Path(__file__).parent.parent.parent / 'mongo_config.yaml',
            Path(__file__).parent.parent.parent / 'mongodb_config.yaml',
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        yaml_config = yaml.safe_load(f)
                    
                    if yaml_config and 'mongodb' in yaml_config:
                        mongo_cfg = yaml_config['mongodb']
                        config['connection_string'] = mongo_cfg.get('connection_string')
                        config['database_name'] = mongo_cfg.get('database_name', 'PPTTOVideo')
                        logger.info(f"从配置文件加载 MongoDB 配置: {config_path}")
                        return config
                except Exception as e:
                    logger.warning(f"读取配置文件失败 {config_path}: {e}")
        
        return config
    
    def _connect(self) -> None:
        """建立数据库连接"""
        config = self._load_config()
        
        if not config['connection_string']:
            logger.error("MongoDB 连接字符串未配置")
            raise ValueError(
                "MongoDB 连接字符串未配置。\n"
                "请设置环境变量 MONGODB_URI 或在 flask_backend/mongo_config.yaml 中配置。"
            )
        
        try:
            # 创建客户端，配置连接池参数
            self._client = MongoClient(
                config['connection_string'],
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=30000,  # 增加到30秒（Atlas网络延迟）
                connectTimeoutMS=30000,          # 增加到30秒
                socketTimeoutMS=30000,           # Socket超时30秒
                retryWrites=True,
                retryReads=True
            )
            
            # 测试连接
            self._client.admin.command('ping')
            
            # 获取数据库实例
            self._db = self._client[config['database_name']]
            
            logger.info(f"✅ MongoDB 连接成功: {config['database_name']}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB 连接失败: {e}")
            self._client = None
            self._db = None
            raise ConnectionError(f"无法连接到 MongoDB: {e}")
        except Exception as e:
            logger.error(f"❌ MongoDB 初始化错误: {e}")
            self._client = None
            self._db = None
            raise
    
    @property
    def client(self) -> Optional[MongoClient]:
        """获取 MongoDB 客户端"""
        return self._client
    
    @property
    def db(self) -> Optional[Database]:
        """获取数据库实例"""
        if self._db is None:
            self._connect()
        return self._db
    
    def is_connected(self) -> bool:
        """检查数据库是否已连接"""
        if self._client is None:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def reconnect(self) -> bool:
        """重新连接数据库"""
        logger.info("尝试重新连接 MongoDB...")
        self.close()
        try:
            self._connect()
            return True
        except Exception as e:
            logger.error(f"重新连接失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB 连接已关闭")
    
    def health_check(self) -> dict:
        """健康检查"""
        result = {
            'status': 'unknown',
            'connected': False,
            'database': None,
            'error': None
        }
        
        try:
            if self.is_connected():
                result['status'] = 'healthy'
                result['connected'] = True
                result['database'] = self._db.name if self._db else None
                
                # 获取集合统计
                collections = self._db.list_collection_names() if self._db else []
                result['collections'] = collections
            else:
                result['status'] = 'disconnected'
                result['error'] = '数据库未连接'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result


# 便捷函数
def get_db() -> Database:
    """获取数据库实例（便捷方法）"""
    return MongoDBClient().db


def get_client() -> MongoClient:
    """获取 MongoDB 客户端（便捷方法）"""
    return MongoDBClient().client


def check_connection() -> bool:
    """检查数据库连接状态"""
    try:
        return MongoDBClient().is_connected()
    except Exception:
        return False
