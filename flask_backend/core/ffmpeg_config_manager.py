"""
FFmpeg配置管理器 - 解决硬编码问题的具体实现
基于现有的config_storage.py SQLite基础设施
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from flask_backend.core.config_storage import ConfigStorageManager
except ImportError:
    # 如果模块路径有问题，尝试相对导入
    from .config_storage import ConfigStorageManager

logger = logging.getLogger(__name__)

class FFmpegConfigManager:
    """FFmpeg动态配置管理器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化FFmpeg配置管理器
        
        Args:
            storage_path: 存储路径，默认使用config_data/storage
        """
        if storage_path is None:
            storage_path = "config_data/storage"
        self.storage_manager = ConfigStorageManager(storage_path)
        self.module_name = "ffmpeg"
        
        # 确保初始化默认配置
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """初始化默认FFmpeg配置到数据库"""
        
        # 检查是否已经初始化
        existing_configs = self.storage_manager.list_configs(preset_key="ffmpeg_base_config")
        if existing_configs:
            return
        
        # 基础配置
        base_config = {
            "video_codec": "libx264",
            "audio_codec": "aac", 
            "pixel_format": "yuv420p",
            "movflags": "+faststart"
        }
        
        # 质量预设配置
        quality_presets = {
            "ultra_high": {
                "name": "超高质量",
                "preset": "veryslow",
                "crf": "16",
                "video_bitrate": "6000k",
                "audio_bitrate": "256k",
                "description": "最高质量输出，适合专业用途，编码时间较长"
            },
            "high": {
                "name": "高质量", 
                "preset": "slow",
                "crf": "18",
                "video_bitrate": "4000k",
                "audio_bitrate": "192k",
                "description": "高质量输出，适合重要演示，编码时间中等"
            },
            "medium": {
                "name": "标准质量",
                "preset": "medium",
                "crf": "23", 
                "video_bitrate": "2000k",
                "audio_bitrate": "128k",
                "description": "平衡质量和速度，日常使用推荐"
            },
            "fast": {
                "name": "快速编码",
                "preset": "fast",
                "crf": "26",
                "video_bitrate": "1000k", 
                "audio_bitrate": "96k",
                "description": "快速编码，适合预览和测试"
            },
            "ultra_fast": {
                "name": "极速编码",
                "preset": "ultrafast",
                "crf": "28",
                "video_bitrate": "800k",
                "audio_bitrate": "64k",
                "description": "最快编码速度，质量较低，仅用于快速测试"
            }
        }
        
        # 保存到数据库
        try:
            # 保存基础配置
            base_config_id = self.storage_manager.save_config(
                name="FFmpeg基础配置",
                preset_key="ffmpeg_base_config",
                config_data=base_config,
                description="FFmpeg编码器基础配置参数",
                tags=["ffmpeg", "base", "codec"]
            )
            
            # 保存质量预设
            presets_config_id = self.storage_manager.save_config(
                name="FFmpeg质量预设",
                preset_key="ffmpeg_quality_presets",
                config_data=quality_presets,
                description="FFmpeg编码质量预设配置",
                tags=["ffmpeg", "quality", "presets"]
            )
            
            logger.info("✅ FFmpeg默认配置初始化完成")
            
        except Exception as e:
            logger.error(f"❌ FFmpeg配置初始化失败: {e}")
    
    def get_ffmpeg_config(self, 
                         quality_preset: str = "medium",
                         custom_settings: Optional[Dict[str, Any]] = None,
                         output_format: str = "mp4") -> Dict[str, str]:
        """
        获取动态FFmpeg配置
        
        Args:
            quality_preset: 质量预设 (ultra_high, high, medium, fast, ultra_fast)
            custom_settings: 自定义设置，会覆盖预设
            output_format: 输出格式 (mp4, avi, mov)
            
        Returns:
            完整的FFmpeg配置字典
        """
        try:
            # 1. 获取基础配置
            base_configs = self.storage_manager.list_configs(preset_key="ffmpeg_base_config")
            if not base_configs:
                logger.warning("基础配置未找到，使用内置默认配置")
                base_config = {
                    "video_codec": "libx264",
                    "audio_codec": "aac",
                    "pixel_format": "yuv420p", 
                    "movflags": "+faststart"
                }
            else:
                # 加载完整配置数据
                base_config_record = self.storage_manager.load_config(base_configs[0].id)
                if base_config_record:
                    base_config = base_config_record.config_data
                else:
                    base_config = {}
            
            # 2. 获取质量预设配置
            preset_configs = self.storage_manager.list_configs(preset_key="ffmpeg_quality_presets")
            if not preset_configs:
                logger.warning("质量预设未找到，使用内置默认")
                quality_config = {
                    "preset": "medium",
                    "crf": "23",
                    "video_bitrate": "2000k",
                    "audio_bitrate": "128k"
                }
            else:
                # 加载完整预设数据
                presets_record = self.storage_manager.load_config(preset_configs[0].id)
                if presets_record:
                    all_presets = presets_record.config_data
                    quality_config = all_presets.get(quality_preset, all_presets.get("medium", {}))
                    
                    # 移除非FFmpeg参数
                    quality_config = {k: v for k, v in quality_config.items() 
                                    if k not in ["name", "description"]}
                else:
                    quality_config = {}
            
            # 3. 获取用户自定义配置
            user_configs = self.storage_manager.list_configs(preset_key="ffmpeg_user_settings")
            if user_configs:
                user_config_record = self.storage_manager.load_config(user_configs[0].id)
                user_config = user_config_record.config_data if user_config_record else {}
            else:
                user_config = {}
            
            # 4. 格式特定配置
            format_config = self._get_format_specific_config(output_format)
            
            # 5. 合并配置 (优先级: 自定义 > 格式特定 > 质量预设 > 基础)
            final_config = {}
            final_config.update(base_config)
            final_config.update(quality_config) 
            final_config.update(format_config)
            final_config.update(user_config)
            
            # 6. 应用临时自定义设置
            if custom_settings:
                final_config.update(custom_settings)
            
            # 7. 记录使用统计
            self._update_usage_stats(quality_preset)
            
            logger.info(f"✅ FFmpeg配置生成完成: 质量={quality_preset}, 格式={output_format}")
            return final_config
            
        except Exception as e:
            logger.error(f"❌ FFmpeg配置获取失败: {e}")
            # 返回安全的默认配置
            return self._get_safe_default_config()
    
    def _get_format_specific_config(self, output_format: str) -> Dict[str, str]:
        """获取格式特定的配置"""
        format_configs = {
            "mp4": {
                "movflags": "+faststart",
                "f": "mp4"
            },
            "avi": {
                "f": "avi",
                "video_codec": "libx264"  # AVI格式推荐设置
            },
            "mov": {
                "movflags": "+faststart",
                "f": "mov"
            },
            "webm": {
                "video_codec": "libvpx-vp9",
                "audio_codec": "libvorbis",
                "f": "webm"
            }
        }
        return format_configs.get(output_format.lower(), {})
    
    def _get_safe_default_config(self) -> Dict[str, str]:
        """获取安全的默认配置"""
        return {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "audio_bitrate": "128k",
            "video_bitrate": "2000k",
            "preset": "medium",
            "crf": "23",
            "pixel_format": "yuv420p",
            "movflags": "+faststart"
        }
    
    def save_user_settings(self, settings: Dict[str, Any]) -> bool:
        """
        保存用户自定义FFmpeg设置
        
        Args:
            settings: 用户自定义设置
            
        Returns:
            是否保存成功
        """
        try:
            self.storage_manager.save_config(
                name="用户自定义FFmpeg设置",
                preset_key="ffmpeg_user_settings",
                config_data=settings,
                description=f"用户于{datetime.now().strftime('%Y-%m-%d %H:%M')}保存的自定义设置",
                tags=["ffmpeg", "user", "custom"]
            )
            logger.info("✅ 用户FFmpeg设置保存成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 用户FFmpeg设置保存失败: {e}")
            return False
    
    def get_available_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的质量预设"""
        try:
            preset_configs = self.storage_manager.list_configs(preset_key="ffmpeg_quality_presets")
            if preset_configs:
                presets_record = self.storage_manager.load_config(preset_configs[0].id)
                if presets_record:
                    return presets_record.config_data
            return {}
        except Exception as e:
            logger.error(f"❌ 获取质量预设失败: {e}")
            return {}
    
    def _update_usage_stats(self, preset_name: str):
        """更新使用统计"""
        try:
            # 这里可以记录使用统计，用于分析用户偏好
            # 暂时简单记录日志
            logger.debug(f"FFmpeg预设使用: {preset_name}")
        except Exception:
            pass

# 使用示例
if __name__ == "__main__":
    # 创建配置管理器
    ffmpeg_manager = FFmpegConfigManager()
    
    # 获取不同质量的配置
    high_quality_config = ffmpeg_manager.get_ffmpeg_config("high")
    print("高质量配置:", high_quality_config)
    
    # 获取带自定义设置的配置
    custom_config = ffmpeg_manager.get_ffmpeg_config(
        quality_preset="medium",
        custom_settings={"crf": "20", "video_bitrate": "3000k"},
        output_format="mp4"
    )
    print("自定义配置:", custom_config)
    
    # 保存用户设置
    user_settings = {
        "preferred_preset": "medium",
        "always_use_gpu": False,
        "custom_crf": "22"
    }
    ffmpeg_manager.save_user_settings(user_settings)