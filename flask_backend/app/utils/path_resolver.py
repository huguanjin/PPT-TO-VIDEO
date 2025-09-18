"""
路径解析器
提供项目路径解析功能
"""
from pathlib import Path
from typing import Optional

def get_backend_root():
    """获取后端根目录路径"""
    # 从当前文件开始，向上查找flask_backend目录
    current_path = Path(__file__).resolve()
    
    # 遍历父目录，查找flask_backend
    for parent in current_path.parents:
        if parent.name == 'flask_backend':
            return parent
        # 也支持backend目录名
        if parent.name == 'backend':
            return parent
    
    # 如果没找到，返回当前目录的父目录的父目录（默认假设）
    return current_path.parent.parent.parent

def get_project_root():
    """获取项目根目录路径"""
    backend_root = get_backend_root()
    return backend_root.parent

def resolve_path(relative_path: str, base_path: Optional[Path] = None):
    """
    解析相对路径
    
    Args:
        relative_path: 相对路径字符串
        base_path: 基础路径，默认为后端根目录
        
    Returns:
        解析后的绝对路径
    """
    if base_path is None:
        base_path = get_backend_root()
    
    return base_path / relative_path