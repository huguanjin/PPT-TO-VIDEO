"""
数据库模块
提供 MongoDB 连接管理和数据库初始化功能
"""

from .mongodb import MongoDBClient, get_db
from .init_db import init_database

__all__ = ['MongoDBClient', 'get_db', 'init_database']
