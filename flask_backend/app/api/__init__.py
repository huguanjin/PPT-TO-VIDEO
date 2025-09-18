# API模块初始化

# 导入所有API蓝图
try:
    from .smart_subtitle_api import smart_subtitle_bp
except ImportError:
    smart_subtitle_bp = None

try:
    from .ai_config_api import ai_config_api
except ImportError:
    ai_config_api = None

try:
    from .ai_config_test_api import ai_test_bp
except ImportError:
    ai_test_bp = None

try:
    from .prompt_api import prompt_api
except ImportError:
    prompt_api = None

try:
    from .custom_ai_api import custom_ai_api
except ImportError:
    custom_ai_api = None

__all__ = [
    'smart_subtitle_bp',
    'ai_config_api', 
    'ai_test_bp',
    'prompt_api',
    'custom_ai_api'
]