#!/usr/bin/env python3
"""
统一配置管理器 - 整合所有配置加载器功能
将6个重复的配置加载器整合到一个统一的系统中

整合的加载器：
1. enhanced_config_loader.py
2. smart_config_loader.py  
3. smart_subtitle_config_loader.py
4. subtitle_config_loader.py
5. resolution_adaptive_config.py
6. netflix_config_loader.py
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from functools import lru_cache
from enum import Enum

# 导入现有的配置存储和预设系统
try:
    from .config_storage import ConfigStorageManager
    from .config_presets import ConfigPresets, SimpleConfigManager
except ImportError:
    from config_storage import ConfigStorageManager
    from config_presets import ConfigPresets, SimpleConfigManager


class ConfigModuleType(Enum):
    """配置模块类型"""
    SUBTITLE = "subtitle"
    VIDEO = "video"
    AUDIO = "audio"
    TTS = "tts"
    NETFLIX = "netflix"
    FFMPEG = "ffmpeg"
    GENERAL = "general"


class ConfigComplexityLevel(Enum):
    """配置复杂度级别"""
    SIMPLE = "simple"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    CUSTOM = "custom"


@dataclass
class ConfigContext:
    """配置上下文信息"""
    module_type: ConfigModuleType
    complexity_level: ConfigComplexityLevel
    preset_name: str = "default"
    user_overrides: Optional[Dict[str, Any]] = None
    project_type: str = "standard"
    language: str = "auto"
    target_audience: str = "general"
    resolution: Optional[Tuple[int, int]] = None

    def __post_init__(self):
        if self.user_overrides is None:
            self.user_overrides = {}


class UnifiedConfigManager:
    """
    统一配置管理器
    
    整合所有配置加载器的功能：
    - 分层配置管理 (用户设置 > 模块配置 > 系统默认)
    - 智能预设系统
    - 分辨率自适应
    - Netflix级配置支持
    - 配置缓存和优化
    """
    
    def __init__(self, config_root: Optional[Path] = None, storage_path: Optional[str] = None):
        """
        初始化统一配置管理器
        
        Args:
            config_root: 配置文件根目录
            storage_path: SQLite存储路径
        """
        self.config_root = Path(config_root) if config_root else Path("config_data")
        self.logger = logging.getLogger(__name__)
        
        # 初始化存储管理器
        storage_path_str = storage_path or "config_data/storage"
        self.storage_manager = ConfigStorageManager(storage_path_str)
        
        # 配置缓存
        self._config_cache = {}
        self._preset_cache = {}
        
        # 默认配置映射
        self._default_configs = self._load_default_configs()
        
        self.logger.info("统一配置管理器初始化完成")
    
    def get_config(self, 
                  context: ConfigContext,
                  use_cache: bool = True) -> Dict[str, Any]:
        """
        获取配置 - 统一入口
        
        Args:
            context: 配置上下文
            use_cache: 是否使用缓存
            
        Returns:
            完整的配置字典
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(context)
        
        if use_cache and cache_key in self._config_cache:
            self.logger.debug(f"从缓存获取配置: {cache_key}")
            return self._config_cache[cache_key]
        
        # 分层获取配置
        config = self._build_layered_config(context)
        
        # 应用分辨率自适应
        if context.resolution and context.module_type == ConfigModuleType.SUBTITLE:
            config = self._apply_resolution_adaptation(config, context.resolution)
        
        # 应用Netflix级配置优化
        if context.module_type == ConfigModuleType.NETFLIX:
            config = self._apply_netflix_optimizations(config, context)
        
        # 缓存配置
        if use_cache:
            self._config_cache[cache_key] = config
        
        self.logger.info(f"配置构建完成: {context.module_type.value} - {context.complexity_level.value}")
        return config
    
    def _build_layered_config(self, context: ConfigContext) -> Dict[str, Any]:
        """
        构建分层配置
        
        优先级: 用户自定义 > 模块配置 > 预设配置 > 系统默认
        """
        # 1. 系统默认配置
        base_config = self._get_system_default_config(context.module_type)
        
        # 2. 预设配置
        preset_config = self._get_preset_config(context)
        
        # 3. 模块配置文件
        module_config = self._get_module_config(context.module_type)
        
        # 4. 用户自定义配置 (SQLite)
        user_config = self._get_user_config(context)
        
        # 5. 运行时覆盖
        runtime_config = context.user_overrides
        
        # 合并配置（后面的覆盖前面的）
        final_config = {}
        for config in [base_config, preset_config, module_config, user_config, runtime_config]:
            if config:
                final_config = self._deep_merge_configs(final_config, config)
        
        return final_config
    
    def _get_simple_preset(self, preset_name: str) -> Dict[str, Any]:
        """获取简单预设配置"""
        # 简单预设的基础配置
        simple_presets = {
            "default": {
                "font_size": 18,
                "font_family": "Arial",
                "background_color": "#FFFFFF",
                "text_color": "#000000"
            },
            "dark": {
                "font_size": 18,
                "font_family": "Arial", 
                "background_color": "#000000",
                "text_color": "#FFFFFF"
            }
        }
        return simple_presets.get(preset_name, simple_presets["default"])
    
    def _get_advanced_preset(self, preset_name: str) -> Dict[str, Any]:
        """获取高级预设配置"""
        # 从存储层获取高级预设
        configs = self.storage_manager.list_configs(preset_key=f"advanced_preset_{preset_name}")
        if configs:
            # 需要加载完整配置数据
            full_config = self.storage_manager.load_config(configs[0].id)
            return full_config.config_data if full_config else {}
        
        # 返回默认高级配置
        return {
            "font_size": 20,
            "font_family": "Microsoft YaHei",
            "background_color": "#F0F0F0",
            "text_color": "#333333",
            "advanced_features": True
        }
    
    def _get_system_default_config(self, module_type: ConfigModuleType) -> Dict[str, Any]:
        """获取系统默认配置"""
        defaults = {
            ConfigModuleType.SUBTITLE: {
                "font_size": 18,
                "font_family": "Arial",
                "line_spacing": 1.2,
                "max_lines": 2,
                "max_chars_per_line": 20,
                "alignment": "center",
                "encoding": "utf-8"
            },
            ConfigModuleType.VIDEO: {
                "resolution": [1920, 1080],
                "fps": 30,
                "duration_per_slide": 5.0,
                "transition_duration": 0.5
            },
            ConfigModuleType.AUDIO: {
                "sample_rate": 44100,
                "channels": 2,
                "format": "wav",
                "volume": 1.0
            },
            ConfigModuleType.TTS: {
                "engine": "edge-tts",
                "voice": "zh-CN-XiaoxiaoNeural",
                "speed": 1.0,
                "pitch": 0,
                "volume": 1.0
            },
            ConfigModuleType.NETFLIX: {
                "max_chars_per_line": 20,
                "max_lines": 2,
                "reading_speed": 17,
                "min_duration": 1.0,
                "max_duration": 7.0,
                "quality_level": "standard"
            },
            ConfigModuleType.FFMPEG: {
                "video_codec": "libx264",
                "audio_codec": "aac",
                "preset": "medium",
                "crf": "23",
                "pixel_format": "yuv420p"
            }
        }
        return defaults.get(module_type, {})
    
    def _get_preset_config(self, context: ConfigContext) -> Dict[str, Any]:
        """获取预设配置"""
        cache_key = f"preset_{context.preset_name}_{context.complexity_level.value}"
        
        if cache_key in self._preset_cache:
            return self._preset_cache[cache_key]
        
        # 根据复杂度级别选择配置源
        if context.complexity_level == ConfigComplexityLevel.SIMPLE:
            config = self._get_simple_preset(context.preset_name)
        else:
            config = self._get_advanced_preset(context.preset_name)
        
        # 缓存预设配置
        self._preset_cache[cache_key] = config or {}
        return config or {}
    
    def _get_module_config(self, module_type: ConfigModuleType) -> Dict[str, Any]:
        """从JSON文件获取模块配置"""
        config_files = {
            ConfigModuleType.SUBTITLE: "subtitle_multiline_fix_config.json",
            ConfigModuleType.NETFLIX: "netflix_subtitle_config.json",
            ConfigModuleType.TTS: "tts_optimized_config.json",
            ConfigModuleType.VIDEO: "video_frame_sync_config.json",
            ConfigModuleType.AUDIO: "audio_intelligent_sync_config.json"
        }
        
        config_file = config_files.get(module_type)
        if not config_file:
            return {}
        
        config_path = self.config_root / config_file
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载模块配置失败 {config_file}: {e}")
        
        return {}
    
    def _get_user_config(self, context: ConfigContext) -> Dict[str, Any]:
        """从SQLite获取用户自定义配置"""
        try:
            config_key = f"{context.module_type.value}_user_settings"
            configs = self.storage_manager.list_configs(preset_key=config_key)
            
            if configs:
                # 加载完整配置数据
                full_config = self.storage_manager.load_config(configs[0].id)
                return full_config.config_data if full_config else {}
        except Exception as e:
            self.logger.warning(f"加载用户配置失败: {e}")
        
        return {}
    
    def _apply_resolution_adaptation(self, config: Dict[str, Any], resolution: Tuple[int, int]) -> Dict[str, Any]:
        """应用分辨率自适应配置"""
        adapted_config = config.copy()
        
        # 计算自适应字体大小
        base_font_size = config.get("font_size", 18)
        
        # 分辨率适配算法
        width, height = resolution
        reference_width = 1920  # 参考分辨率宽度
        
        scale_factor = width / reference_width
        adapted_font_size = max(12, int(base_font_size * scale_factor))
        
        adapted_config.update({
            "font_size": adapted_font_size,
            "resolution_adapted": True,
            "source_resolution": f"{width}x{height}",
            "scale_factor": scale_factor
        })
        
        self.logger.debug(f"分辨率自适应: {width}x{height}, 字体大小: {base_font_size} -> {adapted_font_size}")
        return adapted_config
    
    def _apply_netflix_optimizations(self, config: Dict[str, Any], context: ConfigContext) -> Dict[str, Any]:
        """应用Netflix级配置优化"""
        optimized_config = config.copy()
        
        # Netflix级字幕优化参数
        netflix_optimizations = {
            "character_weights": {
                "chinese": 2.0,
                "japanese": 2.0,
                "korean": 1.8,
                "english": 1.0,
                "punctuation": 0.6,
                "space": 0.3,
                "number": 0.8,
                "emoji": 1.5
            },
            "line_break_rules": {
                "max_lines_strict": 1 if context.complexity_level == ConfigComplexityLevel.PROFESSIONAL else 2,
                "max_chars_per_line_chinese": 18 if context.complexity_level == ConfigComplexityLevel.PROFESSIONAL else 26,
                "avoid_orphan_words": True,
                "semantic_grouping": True
            },
            "timing_rules": {
                "min_display_time": 1.0,
                "max_display_time": 7.0,
                "reading_speed_cps": 17,
                "lead_in_frames": 2,
                "lead_out_frames": 2
            }
        }
        
        optimized_config.update(netflix_optimizations)
        optimized_config["netflix_optimized"] = True
        
        return optimized_config
    
    def save_user_config(self, 
                        context: ConfigContext, 
                        config_data: Dict[str, Any], 
                        description: str = "") -> bool:
        """保存用户自定义配置"""
        try:
            config_key = f"{context.module_type.value}_user_settings"
            
            config_id = self.storage_manager.save_config(
                name=config_key,
                preset_key=config_key,
                config_data=config_data,
                description=description or f"{context.module_type.value}用户配置"
            )
            
            if config_id:
                # 清除相关缓存
                self._clear_related_cache(context)
                self.logger.info(f"用户配置保存成功: {config_key}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"保存用户配置失败: {e}")
            return False
    
    def create_preset(self, 
                     preset_name: str, 
                     config_data: Dict[str, Any], 
                     module_type: ConfigModuleType,
                     description: str = "") -> bool:
        """创建自定义预设"""
        try:
            preset_key = f"{module_type.value}_preset_{preset_name}"
            
            config_id = self.storage_manager.save_config(
                name=preset_key,
                preset_key=preset_key,
                config_data=config_data,
                description=description or f"{preset_name}预设配置"
            )
            
            if config_id:
                self.logger.info(f"预设创建成功: {preset_name}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"创建预设失败: {e}")
            return False
    
    def get_available_presets(self, module_type: ConfigModuleType) -> List[Dict[str, Any]]:
        """获取可用的预设列表"""
        try:
            preset_key_pattern = f"{module_type.value}_preset_"
            configs = self.storage_manager.list_configs()
            
            presets = []
            for config in configs:
                config_name = config.name
                if config_name.startswith(preset_key_pattern):
                    preset_name = config_name.replace(preset_key_pattern, "")
                    # 加载完整配置数据
                    full_config = self.storage_manager.load_config(config.id)
                    config_data = full_config.config_data if full_config else {}
                    
                    presets.append({
                        "name": preset_name,
                        "description": config.description,
                        "created_at": config.created_at.isoformat() if config.created_at else "",
                        "config_data": config_data
                    })
            
            return presets
        except Exception as e:
            self.logger.error(f"获取预设列表失败: {e}")
            return []
    
    def _deep_merge_configs(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置字典"""
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _generate_cache_key(self, context: ConfigContext) -> str:
        """生成配置缓存键"""
        resolution_str = f"{context.resolution[0]}x{context.resolution[1]}" if context.resolution else "default"
        
        return f"{context.module_type.value}_{context.complexity_level.value}_{context.preset_name}_{resolution_str}_{hash(str(sorted((context.user_overrides or {}).items())))}"
    
    def _clear_related_cache(self, context: ConfigContext):
        """清除相关缓存"""
        keys_to_remove = []
        cache_prefix = f"{context.module_type.value}_"
        
        for key in self._config_cache.keys():
            if key.startswith(cache_prefix):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._config_cache[key]
    
    def _load_default_configs(self) -> Dict[ConfigModuleType, Dict[str, Any]]:
        """加载所有默认配置"""
        defaults = {}
        for module_type in ConfigModuleType:
            defaults[module_type] = self._get_system_default_config(module_type)
        return defaults
    
    @lru_cache(maxsize=128)
    def get_config_schema(self, module_type: ConfigModuleType) -> Dict[str, Any]:
        """获取配置模式定义"""
        schemas = {
            ConfigModuleType.SUBTITLE: {
                "font_size": {"type": "integer", "min": 8, "max": 72, "default": 18},
                "font_family": {"type": "string", "default": "Arial"},
                "max_lines": {"type": "integer", "min": 1, "max": 4, "default": 2},
                "max_chars_per_line": {"type": "integer", "min": 10, "max": 50, "default": 20}
            }
            # 其他模块的模式定义...
        }
        return schemas.get(module_type, {})
    
    def validate_config(self, config: Dict[str, Any], module_type: ConfigModuleType) -> Tuple[bool, List[str]]:
        """验证配置的有效性"""
        schema = self.get_config_schema(module_type)
        errors = []
        
        for key, schema_def in schema.items():
            if key in config:
                value = config[key]
                value_type = schema_def.get("type")
                
                if value_type == "integer" and not isinstance(value, int):
                    errors.append(f"{key} 必须是整数")
                elif value_type == "string" and not isinstance(value, str):
                    errors.append(f"{key} 必须是字符串")
                elif "min" in schema_def and value < schema_def["min"]:
                    errors.append(f"{key} 不能小于 {schema_def['min']}")
                elif "max" in schema_def and value > schema_def["max"]:
                    errors.append(f"{key} 不能大于 {schema_def['max']}")
        
        return len(errors) == 0, errors
    
    def get_config_summary(self, context: ConfigContext) -> Dict[str, Any]:
        """获取配置摘要信息"""
        config = self.get_config(context, use_cache=False)
        
        return {
            "module_type": context.module_type.value,
            "complexity_level": context.complexity_level.value,
            "preset_name": context.preset_name,
            "config_keys_count": len(config),
            "has_user_overrides": bool(context.user_overrides),
            "resolution_adapted": config.get("resolution_adapted", False),
            "netflix_optimized": config.get("netflix_optimized", False),
            "cache_key": self._generate_cache_key(context)
        }


# 向后兼容的工厂函数
def create_enhanced_config_loader(config_path: Optional[str] = None, preset: Optional[str] = None):
    """创建增强配置加载器（向后兼容）"""
    manager = UnifiedConfigManager()
    context = ConfigContext(
        module_type=ConfigModuleType.SUBTITLE,
        complexity_level=ConfigComplexityLevel.STANDARD,
        preset_name=preset or "default"
    )
    config = manager.get_config(context)
    
    class CompatibilityWrapper:
        def __init__(self, config, manager):
            self.config = config
            self.manager = manager
        
        def get_config(self):
            return self.config
        
        def get_config_summary(self):
            return self.manager.get_config_summary(context)
    
    return CompatibilityWrapper(config, manager)


def create_smart_subtitle_config_loader(config_dir: Optional[Path] = None, preset: Optional[str] = None):
    """创建智能字幕配置加载器（向后兼容）"""
    manager = UnifiedConfigManager(config_root=config_dir)
    context = ConfigContext(
        module_type=ConfigModuleType.SUBTITLE,
        complexity_level=ConfigComplexityLevel.STANDARD,
        preset_name=preset or "standard"
    )
    return manager.get_config(context)


def create_netflix_config_loader(config_path: Optional[str] = None):
    """创建Netflix配置加载器（向后兼容）"""
    manager = UnifiedConfigManager()
    context = ConfigContext(
        module_type=ConfigModuleType.NETFLIX,
        complexity_level=ConfigComplexityLevel.PROFESSIONAL,
        preset_name="netflix_standard"
    )
    return manager.get_config(context)


def create_resolution_adaptive_manager(project_dir: Path):
    """创建分辨率自适应管理器（向后兼容）"""
    manager = UnifiedConfigManager()
    
    class ResolutionWrapper:
        def __init__(self, manager):
            self.manager = manager
        
        def get_adaptive_subtitle_config(self, video_resolution=None, base_config=None):
            context = ConfigContext(
                module_type=ConfigModuleType.SUBTITLE,
                complexity_level=ConfigComplexityLevel.STANDARD,
                resolution=video_resolution
            )
            if base_config:
                context.user_overrides = base_config
            return self.manager.get_config(context)
    
    return ResolutionWrapper(manager)


if __name__ == "__main__":
    # 测试统一配置管理器
    manager = UnifiedConfigManager()
    
    # 测试不同模块的配置
    subtitle_context = ConfigContext(
        module_type=ConfigModuleType.SUBTITLE,
        complexity_level=ConfigComplexityLevel.STANDARD,
        preset_name="netflix_optimized",
        resolution=(1920, 1080)
    )
    
    subtitle_config = manager.get_config(subtitle_context)
    print("字幕配置:", json.dumps(subtitle_config, indent=2, ensure_ascii=False))
    
    # 测试配置摘要
    summary = manager.get_config_summary(subtitle_context)
    print("配置摘要:", json.dumps(summary, indent=2, ensure_ascii=False))