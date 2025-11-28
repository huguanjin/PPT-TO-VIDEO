"""
日志记录器模块
提供统一的日志记录功能
"""
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# 全局变量：跟踪已清理的日志目录
_cleared_log_dirs: set = set()

def clear_log_directory(log_dir: str | Path) -> None:
    """
    清理日志目录中的所有日志文件
    
    Args:
        log_dir: 日志目录路径
    """
    log_dir = Path(log_dir)
    if log_dir.exists():
        for log_file in log_dir.glob("*.log"):
            try:
                log_file.unlink()
            except Exception:
                pass  # 忽略删除失败的文件

def reset_logger_cleared_state():
    """
    重置日志清理状态，允许下次工作流重新清理日志
    在新工作流启动前调用
    """
    global _cleared_log_dirs
    _cleared_log_dirs.clear()

def get_logger(name: str, log_dir: str | Path = "logs", level: int = logging.INFO, 
               clear_on_first_use: bool = False) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录路径
        level: 日志级别
        clear_on_first_use: 是否在首次使用时清空该目录的日志（用于新工作流）
    
    Returns:
        配置好的日志记录器
    """
    global _cleared_log_dirs
    
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建日志目录
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 如果需要清空日志且该目录还未清理过
    log_dir_str = str(log_dir.resolve())
    if clear_on_first_use and log_dir_str not in _cleared_log_dirs:
        clear_log_directory(log_dir)
        _cleared_log_dirs.add(log_dir_str)
    
    # 创建文件处理器 - 使用写入模式覆盖旧日志
    log_file = log_dir / f"{name.replace('.', '_')}.log"
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
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