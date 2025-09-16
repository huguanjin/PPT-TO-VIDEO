"""
日志记录器模块
提供统一的日志记录功能
"""
import logging
import os
from pathlib import Path
from datetime import datetime

def get_logger(name: str, log_dir: str | Path = "logs", level: int = logging.INFO) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录路径
        level: 日志级别
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建文件处理器
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{name.replace('.', '_')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def setup_logging(level: int = logging.INFO):
    """设置全局日志配置"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/application.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )