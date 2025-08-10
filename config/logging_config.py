"""
日志配置
"""
import logging
import os
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: Path = None, log_level: str = "INFO"):
    """
    设置日志配置
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "output" / "logs"
    
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件名包含时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ppt_to_video_{timestamp}.log"
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置根logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    return logging.getLogger(__name__)
