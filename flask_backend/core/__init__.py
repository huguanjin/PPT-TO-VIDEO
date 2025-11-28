# flask_backend core package

# 导出配置桥接模块
from .system_config_bridge import (
    get_manual_split_config,
    get_single_line_mode,
    get_time_allocation_config,
    get_app_config,
    get_render_config,
    get_tts_config,
    get_feature_flags,
    get_subtitle_multiline_config,
    get_phase3_alignment_config,
    load_config_file,
    get_config_source_info
)

__all__ = [
    'get_manual_split_config',
    'get_single_line_mode', 
    'get_time_allocation_config',
    'get_app_config',
    'get_render_config',
    'get_tts_config',
    'get_feature_flags',
    'get_subtitle_multiline_config',
    'get_phase3_alignment_config',
    'load_config_file',
    'get_config_source_info'
]
