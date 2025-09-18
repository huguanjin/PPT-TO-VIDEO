"""
Flask应用配置
"""
import os
import json
from pathlib import Path

class Config:
    """基础配置"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ppt-to-video-secret-key-2024'
    # Flask后端的基础目录
    FLASK_BASE_DIR = Path(__file__).parent.parent
    # 项目根目录
    PROJECT_ROOT = FLASK_BASE_DIR.parent
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = PROJECT_ROOT / 'uploads'
    OUTPUT_FOLDER = FLASK_BASE_DIR / 'output'  # 使用Flask后端下的output目录
    TEMP_FOLDER = PROJECT_ROOT / 'temp'
    CONFIG_FOLDER = PROJECT_ROOT / 'config_data'
    
    # JSON配置
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False
    
    # 任务管理配置
    TASK_TIMEOUT = 3600  # 1小时
    MAX_CONCURRENT_TASKS = 5
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = PROJECT_ROOT / 'logs' / 'app.log'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    LOG_LEVEL = 'DEBUG'

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def load_app_config():
    """从backend_app_config.json加载应用配置"""
    config_file = Path(__file__).parent.parent / 'config_data' / 'backend_app_config.json'
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load backend_app_config.json: {e}")
            return {}
    return {}
