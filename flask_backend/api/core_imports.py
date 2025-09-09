"""
导入配置 - 确保正确导入核心模块
"""
import sys
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Type

# 获取flask_backend目录
FLASK_BACKEND_DIR = Path(__file__).parent.parent
CORE_DIR = FLASK_BACKEND_DIR / "core"

# 添加到Python路径
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# 类型检查时导入类型
if TYPE_CHECKING:
    from config_storage import ConfigStorageManager, ConfigRecord as _ConfigRecord
    from smart_config_loader import SmartSubtitleConfigLoader as _SmartSubtitleConfigLoader, ConfigContext as _ConfigContext
    from videolingo_integrator import VideoLingoIntegrator as _VideoLingoIntegrator, ProcessingResult as _ProcessingResult
    from config_presets import ConfigPresets as _ConfigPresets
else:
    # 运行时导入
    _ConfigRecord = Type[Any]
    _SmartSubtitleConfigLoader = Type[Any]
    _ConfigContext = Type[Any]
    _VideoLingoIntegrator = Type[Any]
    _ProcessingResult = Type[Any]
    _ConfigPresets = Type[Any]

# 导入核心模块
def import_core_modules():
    """导入所有核心模块，避免循环导入"""
    modules = {}
    try:
        import config_storage
        modules.update({
            'storage_manager': getattr(config_storage, 'storage_manager', None),
            'ConfigRecord': getattr(config_storage, 'ConfigRecord', None),
        })
    except ImportError as e:
        print(f"Warning: Could not import config_storage: {e}")
    
    try:
        import smart_config_loader
        modules.update({
            'SmartSubtitleConfigLoader': getattr(smart_config_loader, 'SmartSubtitleConfigLoader', None),
            'ConfigContext': getattr(smart_config_loader, 'ConfigContext', None),
        })
    except ImportError as e:
        print(f"Warning: Could not import smart_config_loader: {e}")
    
    try:
        import videolingo_integrator
        modules.update({
            'VideoLingoIntegrator': getattr(videolingo_integrator, 'VideoLingoIntegrator', None),
            'ProcessingResult': getattr(videolingo_integrator, 'ProcessingResult', None),
        })
    except ImportError as e:
        print(f"Warning: Could not import videolingo_integrator: {e}")
    
    try:
        import config_presets
        modules.update({
            'ConfigPresets': getattr(config_presets, 'ConfigPresets', None),
        })
    except ImportError as e:
        print(f"Warning: Could not import config_presets: {e}")
    
    return modules

# 导入核心模块
_core_modules = import_core_modules()

# 导出模块 - 使用更精确的类型注释
storage_manager: Any = _core_modules.get('storage_manager')
ConfigRecord: Optional[_ConfigRecord] = _core_modules.get('ConfigRecord')
SmartSubtitleConfigLoader: Optional[_SmartSubtitleConfigLoader] = _core_modules.get('SmartSubtitleConfigLoader')
ConfigContext: Optional[_ConfigContext] = _core_modules.get('ConfigContext')
VideoLingoIntegrator: Optional[_VideoLingoIntegrator] = _core_modules.get('VideoLingoIntegrator')
ProcessingResult: Optional[_ProcessingResult] = _core_modules.get('ProcessingResult')
ConfigPresets: Optional[_ConfigPresets] = _core_modules.get('ConfigPresets')

# 提供安全的实例化函数
def create_config_loader():
    """安全创建配置加载器实例"""
    if SmartSubtitleConfigLoader and callable(SmartSubtitleConfigLoader):
        try:
            return SmartSubtitleConfigLoader()
        except Exception as e:
            print(f"Error creating SmartSubtitleConfigLoader: {e}")
    return None

def create_videolingo_integrator():
    """安全创建VideoLingo集成器实例"""
    if VideoLingoIntegrator and callable(VideoLingoIntegrator):
        try:
            return VideoLingoIntegrator()
        except Exception as e:
            print(f"Error creating VideoLingoIntegrator: {e}")
    return None

def safe_call(obj, method_name, *args, **kwargs):
    """安全调用对象方法"""
    if obj and hasattr(obj, method_name):
        try:
            method = getattr(obj, method_name)
            if callable(method):
                return method(*args, **kwargs)
        except Exception as e:
            print(f"Error calling {method_name}: {e}")
    return None

def safe_presets_call(method_name, *args, **kwargs):
    """安全调用ConfigPresets类方法"""
    if ConfigPresets and hasattr(ConfigPresets, method_name):
        try:
            method = getattr(ConfigPresets, method_name)
            if callable(method):
                return method(*args, **kwargs)
        except Exception as e:
            print(f"Error calling ConfigPresets.{method_name}: {e}")
    return None

def safe_config_loader_call(method_name, *args, **kwargs):
    """安全调用config_loader方法"""
    # 延迟导入避免循环导入
    import sys
    if 'videolingo_config_api' in sys.modules:
        from . import videolingo_config_api
        config_loader = getattr(videolingo_config_api, 'config_loader', None)
        if config_loader and hasattr(config_loader, method_name):
            try:
                method = getattr(config_loader, method_name)
                if callable(method):
                    return method(*args, **kwargs)
            except Exception as e:
                print(f"Error calling config_loader.{method_name}: {e}")
    return None

def safe_integrator_call(method_name, *args, **kwargs):
    """安全调用videolingo_integrator方法"""
    # 延迟导入避免循环导入
    import sys
    if 'videolingo_config_api' in sys.modules:
        from . import videolingo_config_api
        videolingo_integrator = getattr(videolingo_config_api, 'videolingo_integrator', None)
        if videolingo_integrator and hasattr(videolingo_integrator, method_name):
            try:
                method = getattr(videolingo_integrator, method_name)
                if callable(method):
                    return method(*args, **kwargs)
            except Exception as e:
                print(f"Error calling videolingo_integrator.{method_name}: {e}")
    return None

def create_safe_config_context(**kwargs):
    """安全创建ConfigContext实例"""
    if ConfigContext and callable(ConfigContext):
        try:
            return ConfigContext(**kwargs)
        except Exception as e:
            print(f"Error creating ConfigContext: {e}")
    return None
