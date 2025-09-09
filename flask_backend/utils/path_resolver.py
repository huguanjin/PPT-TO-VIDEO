"""
动态路径解析工具
自动适配 flask_backend 和 backend 两种目录结构
"""
import os
from pathlib import Path

def get_backend_root():
    """
    获取后端根目录
    自动适配 flask_backend 和 backend 两种结构
    """
    current_file = Path(__file__)
    
    # 方法1: 从当前文件向上查找包含app.py的目录
    for parent in current_file.parents:
        if (parent / "app.py").exists():
            return parent
    
    # 方法2: 基于目录名判断
    for parent in current_file.parents:
        if parent.name in ["flask_backend", "backend"]:
            return parent
    
    # 方法3: 基于特征文件判断
    for parent in current_file.parents:
        # 检查是否包含后端特征文件
        if all((parent / path).exists() for path in ["core", "app", "utils"]):
            return parent
    
    # 默认回退：当前文件的父级目录
    return current_file.parent

def get_config_dir():
    """获取配置目录"""
    return get_backend_root() / "config_data"

def get_output_dir():
    """获取输出目录"""
    return get_backend_root() / "output"

def get_logs_dir():
    """获取日志目录"""
    return get_backend_root() / "logs"
