"""
Netflix监控管理器 - Flask集成模块
"""

import logging
from pathlib import Path
from typing import Optional

from .netflix_error_monitoring import NetflixErrorHandler, NetflixPerformanceMonitor, NetflixHealthChecker

def init_flask_monitoring(app, project_root: Optional[Path] = None) -> bool:
    """
    初始化Flask监控
    
    Args:
        app: Flask应用实例
        project_root: 项目根目录
        
    Returns:
        bool: 是否成功初始化
    """
    try:
        # 创建监控组件
        error_handler = NetflixErrorHandler()
        performance_monitor = NetflixPerformanceMonitor()
        health_checker = NetflixHealthChecker(error_handler, performance_monitor)
        
        # 存储到应用上下文
        app.netflix_error_handler = error_handler
        app.netflix_performance_monitor = performance_monitor
        app.netflix_health_checker = health_checker
        
        logging.info("Netflix监控系统初始化成功")
        return True
        
    except Exception as e:
        logging.error(f"Netflix监控系统初始化失败: {e}")
        return False