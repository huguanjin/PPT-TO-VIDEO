"""
配置管理器 - 处理配置的持久化存储和加载
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import streamlit as st

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Path = None):
        """初始化配置管理器"""
        if config_dir is None:
            config_dir = Path("config_data")
        
        self.config_dir = config_dir
        self.config_file = self.config_dir / "app_config.json"
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "project_name": "ppt_video_project",
            "output_format": "MP4 (推荐)",
            "tts_voice": "zh-CN-XiaoxiaoNeural",
            "speech_rate": "medium",
            "speech_pitch": "medium",
            "video_resolution": "1920x1080 (Full HD)",
            "video_fps": 24,
            "video_bitrate": 2000,
            "video_codec": "libx264",
            "include_subtitles": True,
            "subtitle_fontsize": 50,
            "subtitle_color": "white",
            "subtitle_position": "bottom",
            "last_updated": None,
            "auto_save": True
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置（处理新增的配置项）
                merged_config = self.default_config.copy()
                merged_config.update(config)
                
                return merged_config
            else:
                # 首次运行，创建默认配置文件
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            st.warning(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            # 添加保存时间戳
            config = config.copy()
            config['last_updated'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"❌ 保存配置失败: {e}")
            return False
    
    def get_config_display_info(self) -> Dict[str, str]:
        """获取配置显示信息"""
        config = self.load_config()
        
        if config.get('last_updated'):
            last_updated = datetime.fromisoformat(config['last_updated'])
            update_time = last_updated.strftime("%Y-%m-%d %H:%M:%S")
        else:
            update_time = "未保存"
        
        return {
            "配置文件路径": str(self.config_file),
            "最后更新时间": update_time,
            "项目名称": config.get('project_name', '未设置'),
            "TTS语音": config.get('tts_voice', '未设置'),
            "视频分辨率": config.get('video_resolution', '未设置')
        }
    
    def reset_config(self) -> bool:
        """重置为默认配置"""
        try:
            return self.save_config(self.default_config)
        except Exception as e:
            st.error(f"❌ 重置配置失败: {e}")
            return False
