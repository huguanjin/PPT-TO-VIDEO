"""
Flask后端配置管理器
统一管理所有应用配置，包括TTS、视频、字幕等设置
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # 使用项目根目录下的config_data
            self.config_dir = Path(__file__).parent.parent.parent / "config_data"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "app_config.json"
        
        # 确保配置文件存在
        if not self.config_file.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "subtitle": {
                "auto_punctuation_removal": True,
                "background_color": "rgba(0,0,0,0.8)",
                "enable_gap_filling": True,
                "enable_precise_alignment": True,
                "enabled": True,
                "font_color": "#FFFFFF",
                "font_family": "Microsoft YaHei",
                "font_size": 40,
                "max_chars_per_line": 20,
                "position": "bottom",
                "use_enhanced_mode": True
            },
            "tts": {
                "preferred_engine": "edge_tts",
                "edge_voice": "zh-CN-XiaoxiaoNeural",
                "edge_rate": "+0%",
                "edge_pitch": "+0Hz",
                "fish_api_key": "",
                "fish_character": "雷军",
                "fish_character_id": "",
                "fish_character_name": "",
                "openai_api_key": "",
                "openai_voice": "alloy",
                "openai_model": "tts-1",
                "azure_api_key": "",
                "azure_region": "",
                "azure_voice": "zh-CN-XiaoxiaoNeural",
                "sample_rate": 22050,
                "max_retries": 3,
                "timeout": 30
            },
            "video": {
                "background_color": "#000000",
                "fps": 30,
                "include_subtitles": True,
                "resolution": "1920x1080",
                "video_bitrate": "5000k"
            }
        }
        
        self.save_config(default_config)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载配置失败: {e}")
            self._create_default_config()
            return self.load_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        try:
            # 添加更新时间戳
            config['_updated_at'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置的某个部分"""
        config = self.load_config()
        return config.get(section, {})
    
    def update_section(self, section: str, data: Dict[str, Any]) -> bool:
        """更新配置的某个部分"""
        config = self.load_config()
        if section not in config:
            config[section] = {}
        config[section].update(data)
        return self.save_config(config)
    
    def get_subtitle_config_for_ffmpeg(self) -> Dict[str, Any]:
        """获取适用于FFmpeg字幕处理的配置格式"""
        subtitle_config = self.get_section('subtitle')
        
        # 转换为FFmpeg期望的扁平化格式
        return {
            "font_family": subtitle_config.get("font_family", "Microsoft YaHei"),
            "font_size": subtitle_config.get("font_size", 40),
            "font_color": subtitle_config.get("font_color", "#FFFFFF"),
            "background_color": subtitle_config.get("background_color", "rgba(0,0,0,0.8)"),
            "position": subtitle_config.get("position", "bottom")
        }
    
    def get_tts_config(self) -> Dict[str, Any]:
        """获取TTS配置"""
        return self.get_section('tts')
    
    def get_video_config(self) -> Dict[str, Any]:
        """获取视频配置"""
        return self.get_section('video')

# 全局配置管理器实例
config_manager = ConfigManager()

# 向后兼容的函数
def load_app_config() -> Dict[str, Any]:
    """向后兼容：加载应用配置"""
    return config_manager.load_config()

def get_subtitle_config_for_merger() -> Dict[str, Any]:
    """为字幕合并器提供配置"""
    return config_manager.get_subtitle_config_for_ffmpeg()
