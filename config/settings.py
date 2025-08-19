"""
项目配置管理
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 输出目录配置
OUTPUT_BASE_DIR = PROJECT_ROOT / "output"
TEMP_DIR = OUTPUT_BASE_DIR / "temp"
LOGS_DIR = OUTPUT_BASE_DIR / "logs"

# 工作流步骤配置
WORKFLOW_STEPS = {
    "ppt_parsing": {"name": "PPT解析", "order": 1},
    "script_extraction": {"name": "讲话稿提取", "order": 2},
    "audio_generation": {"name": "音频生成", "order": 3},
    "video_generation": {"name": "视频生成", "order": 4},
    "subtitle_generation": {"name": "字幕生成", "order": 5},
    "final_merge": {"name": "最终合并", "order": 6}
}

# TTS配置
TTS_CONFIG = {
    "engine": "edge-tts",
    "voice": "zh-CN-XiaoxiaoNeural",
    "rate": "medium",
    "pitch": "medium"
}

# 视频配置
VIDEO_CONFIG = {
    "resolution": "1920x1080",
    "fps": 24,
    "codec": "libx264"
}

# 字幕配置
SUBTITLE_CONFIG = {
    "font_family": "Arial",
    "font_size": 24,
    "max_chars_per_line": 40,
    "max_lines": 2,
    "position": "bottom"
}

def get_project_config() -> Dict[str, Any]:
    """获取项目配置"""
    return {
        "project_root": PROJECT_ROOT,
        "output_dir": OUTPUT_BASE_DIR,
        "workflow_steps": WORKFLOW_STEPS,
        "tts_config": TTS_CONFIG,
        "video_config": VIDEO_CONFIG,
        "subtitle_config": SUBTITLE_CONFIG
    }

def load_app_config() -> Dict[str, Any]:
    """加载应用配置"""
    config_path = PROJECT_ROOT / "config_data" / "app_config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 返回默认配置
        return {
            "project_name": "",
            "ppt_file_path": "",
            "tts_engine": "Edge TTS",
            "tts_voice": "zh-CN-YunxiNeural",
            "speech_rate": "medium",
            "speech_pitch": "medium",
            "fish_api_key": "",
            "fish_character_id": "",
            "openai_api_key": "",
            "openai_voice": "alloy",
            "azure_api_key": "",
            "azure_region": "",
            "video_resolution": "1920x1080 (Full HD)",
            "video_fps": 24,
            "video_bitrate": 2000,
            "video_codec": "libx264",
            "output_format": "MP4 (推荐)",
            "include_subtitles": True,
            "subtitle_fontsize": 50,
            "subtitle_color": "white",
            "subtitle_position": "bottom"
        }

def save_app_config(config: Dict[str, Any]) -> None:
    """保存应用配置"""
    config_path = PROJECT_ROOT / "config_data" / "app_config.json"
    # 确保目录存在
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
