"""
服务层基类和通用功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from pathlib import Path

class BaseService(ABC):
    """服务基类"""
    
    def __init__(self, config_manager, logger: Optional[logging.Logger] = None):
        self.config_manager = config_manager
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """初始化服务"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    def get_config(self, config_type: str, key: Optional[str] = None) -> Any:
        """获取配置"""
        return self.config_manager.get_config(config_type, key)
    
    def update_config(self, config_type: str, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        return self.config_manager.update_config(config_type, updates)

class ServiceResult:
    """服务返回结果"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None, code: int = 200):
        self.success = success
        self.data = data
        self.error = error
        self.code = code
    
    @classmethod
    def success_result(cls, data: Any = None, code: int = 200):
        """成功结果"""
        return cls(success=True, data=data, code=code)
    
    @classmethod
    def error_result(cls, error: str, code: int = 500):
        """错误结果"""
        return cls(success=False, error=error, code=code)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "success": self.success,
            "code": self.code
        }
        
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error
            
        return result
