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
            # 使用Flask后端本地的config_data目录
            self.config_dir = Path(__file__).parent.parent.parent / "config_data"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "app_config.json"
        
        # 手动分割配置文件路径
        self.manual_split_config_file = Path(__file__).parent.parent.parent / "config_data" / "manual_split_config.json"
        
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
            },
            "ai": {
                "default_model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 30
            },
            "api": {
                "base_url": "http://localhost:5000",
                "timeout": 30,
                "retry_attempts": 3
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
        """获取适用于FFmpeg字幕处理的配置格式，统一使用Netflix配置"""
        config = self.load_config()
        
        # 🎯 统一使用Netflix配置作为字幕标准
        netflix_v2 = config.get('netflix_v2', {})
        
        # 转换Netflix配置为FFmpeg格式
        # Netflix使用ASS/SSA格式的颜色代码，需要转换为十六进制
        netflix_font_color = netflix_v2.get('font_color', '&H00FFFF')
        if netflix_font_color.startswith('&H'):
            # 转换 &H00FFFF 为 #FFFF00 (BGR -> RGB)
            bgr_hex = netflix_font_color[2:]  # 去掉 &H
            if len(bgr_hex) == 6:
                # BGR转RGB: FFFF00 -> 00FFFF
                b, g, r = bgr_hex[0:2], bgr_hex[2:4], bgr_hex[4:6]
                rgb_color = f"#{r}{g}{b}"
            else:
                rgb_color = "#00FFFF"  # 默认青色
        else:
            rgb_color = netflix_font_color
        
        return {
            "font_family": "Arial",  # Netflix标准字体
            "font_size": netflix_v2.get('font_size', 17),
            "font_color": rgb_color,
            "background_color": f"rgba(0,0,0,{netflix_v2.get('background_alpha', 0.8)})",
            "position": "bottom",
            "outline_color": "#000000",
            "outline_width": netflix_v2.get('outline_width', 1),
            "enabled": netflix_v2.get('enabled', True),
            # 从Netflix配置中提取其他字幕相关设置
            "max_chars_per_line": netflix_v2.get('max_chars_per_line', 36),
            "max_lines": 2,
            "use_enhanced_mode": True,
            "enable_precise_alignment": True,
            "netflix_compliance": netflix_v2.get('strict_netflix_compliance', True)
        }
    
    def get_subtitle_config(self) -> Dict[str, Any]:
        """获取字幕配置，统一返回Netflix配置格式"""
        # 重用FFmpeg配置方法，保持一致性
        return self.get_subtitle_config_for_ffmpeg()
    
    def get_tts_config(self) -> Dict[str, Any]:
        """获取TTS配置"""
        return self.get_section('tts')
    
    def get_video_config(self) -> Dict[str, Any]:
        """获取视频配置"""
        return self.get_section('video')
    
    def get_default_base_url(self) -> str:
        """获取默认的API基础URL"""
        config = self.load_config()
        return config.get('api', {}).get('base_url', 'http://localhost:5000')
    
    def get_default_model(self) -> str:
        """获取默认的AI模型"""
        config = self.load_config()
        return config.get('ai', {}).get('default_model', 'gpt-3.5-turbo')
    
    def load_key(self, key: str, default: Any = None) -> Any:
        """加载指定键的配置值"""
        config = self.load_config()
        
        # 支持点分隔的嵌套键
        keys = key.split('.')
        value = config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def save_key(self, key: str, value: Any) -> bool:
        """保存指定键的配置值"""
        config = self.load_config()
        keys = key.split('.')
        
        # 创建嵌套结构
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置最终值
        current[keys[-1]] = value
        return self.save_config(config)
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return self.get_section('ai')
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.get_section('api')
    
    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            if self.config_file.exists():
                # 备份当前配置
                backup_file = self.config_file.with_suffix('.backup.json')
                self.config_file.rename(backup_file)
            
            self._create_default_config()
            return True
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False
    
    def load_manual_split_config(self) -> Dict[str, Any]:
        """加载手动分割配置"""
        try:
            if self.manual_split_config_file.exists():
                with open(self.manual_split_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"手动分割配置文件不存在: {self.manual_split_config_file}")
                return self._get_default_manual_split_config()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载手动分割配置失败: {e}")
            return self._get_default_manual_split_config()
    
    def _get_default_manual_split_config(self) -> Dict[str, Any]:
        """获取默认的手动分割配置"""
        return {
            "manual_split_config": {
                "enabled": False,  # 默认关闭，避免影响现有功能
                "split_strategy": {
                    "method": "newline_split",
                    "fallback_to_auto": True
                },
                "newline_split": {
                    "enabled": True,
                    "audio_processing": {
                        "strategy": "separate_generation",
                        "normalize_volume": True,
                        "add_segment_gap": 0.1
                    }
                },
                "quality_control": {
                    "min_segment_length": 5,
                    "max_segments_per_slide": 8,
                    "min_segment_duration": 1.0,
                    "validate_split_points": True
                }
            }
        }
    
    def get_manual_split_config(self) -> Dict[str, Any]:
        """获取手动分割配置"""
        config = self.load_manual_split_config()
        return config.get('manual_split_config', {})
    
    def is_manual_split_enabled(self) -> bool:
        """检查手动分割功能是否启用"""
        config = self.get_manual_split_config()
        return config.get('enabled', False)
    
    def update_manual_split_config(self, updates: Dict[str, Any]) -> bool:
        """更新手动分割配置"""
        try:
            config = self.load_manual_split_config()
            if 'manual_split_config' not in config:
                config['manual_split_config'] = self._get_default_manual_split_config()['manual_split_config']
            
            # 深度更新配置
            def deep_update(base_dict: Dict, update_dict: Dict):
                for key, value in update_dict.items():
                    if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                        deep_update(base_dict[key], value)
                    else:
                        base_dict[key] = value
            
            deep_update(config['manual_split_config'], updates)
            
            # 保存回文件
            with open(self.manual_split_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"更新手动分割配置失败: {e}")
            return False

# 全局配置管理器实例
config_manager = ConfigManager()

# 向后兼容的函数
def load_app_config() -> Dict[str, Any]:
    """向后兼容：加载应用配置"""
    return config_manager.load_config()

def get_subtitle_config_for_merger() -> Dict[str, Any]:
    """为字幕合并器提供配置"""
    return config_manager.get_subtitle_config_for_ffmpeg()
