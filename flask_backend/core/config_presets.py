"""
配置预设管理器
提供简化的配置模式，类似VideoLingo的简洁配置体验
支持从简单到专业的多层次配置预设
集成Netflix级别字幕配置预设
"""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 可选的 yaml 支持
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

# 导入Netflix预设（延迟导入避免循环依赖）
try:
    from .netflix_subtitle_presets import NetflixSubtitlePresets, NetflixConfigIntegrator
except ImportError:
    NetflixSubtitlePresets = None
    NetflixConfigIntegrator = None
    logger.warning("Netflix字幕预设模块未找到，Netflix功能将不可用")


class ConfigPresets:
    """配置预设管理器 - 提供简化配置模式"""
    
    # 预设配置模板
    PRESETS = {
        "simple": {
            "name": "简化模式",
            "description": "类似VideoLingo的简洁配置，适合快速使用",
            "target_users": ["初学者", "快速使用"],
            "config": {
                # 基础字幕设置
                "max_length": 75,
                "target_multiplier": 1.2,
                "processing_mode": "fast",
                
                # 算法选择（简化）
                "use_dp_algorithm": True,
                "use_spacy": False,  # 关闭Spacy减少复杂度
                "use_enhanced_weight": True,
                
                # 显示样式（简化）
                "style": "netflix_minimal",
                "font_size": 24,
                "font_family": "Arial",
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "background_opacity": 0.7,
                
                # 智能功能（关闭部分复杂功能）
                "ai_splitting": False,
                "smart_processing": True,
                "auto_timing": True,
                
                # 质量设置
                "quality_level": "balanced",
                "performance_priority": True
            }
        },
        
        "standard": {
            "name": "标准模式",
            "description": "平衡质量和效率，适合大多数使用场景",
            "target_users": ["普通用户", "日常使用"],
            "config": {
                # 基础字幕设置
                "max_length": 75,
                "target_multiplier": 1.2,
                "processing_mode": "balanced",
                
                # 算法选择（标准）
                "use_dp_algorithm": True,
                "use_spacy": True,
                "use_enhanced_weight": True,
                
                # 显示样式（标准）
                "style": "netflix_standard",
                "font_size": 24,
                "font_family": "Arial",
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "background_opacity": 0.8,
                "outline_color": "#000000",
                "outline_width": 2,
                
                # 智能功能（启用主要功能）
                "ai_splitting": True,
                "smart_processing": True,
                "auto_timing": True,
                "smart_line_breaking": True,
                
                # 质量设置
                "quality_level": "good",
                "performance_priority": False
            }
        },
        
        "professional": {
            "name": "专业模式",
            "description": "完整Netflix级别配置，适合专业用户",
            "target_users": ["专业用户", "高质量需求"],
            "config": {
                # 基础字幕设置（专业级）
                "max_length": 40,  # Netflix标准
                "target_multiplier": 1.0,
                "processing_mode": "quality",
                
                # 算法选择（全开）
                "use_dp_algorithm": True,
                "use_spacy": True,
                "use_enhanced_weight": True,
                
                # 显示样式（Netflix级别）
                "style": "netflix_professional",
                "font_size": 22,
                "font_family": "Helvetica Neue",
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "background_opacity": 0.85,
                "outline_color": "#000000",
                "outline_width": 3,
                "shadow_enabled": True,
                "shadow_color": "#000000",
                "shadow_offset": {"x": 2, "y": 2},
                
                # 智能功能（全开）
                "ai_splitting": True,
                "smart_processing": True,
                "auto_timing": True,
                "smart_line_breaking": True,
                "quality_assurance": True,
                "advanced_formatting": True,
                
                # 质量设置（最高）
                "quality_level": "excellent",
                "performance_priority": False,
                "strict_timing": True,
                "character_limit_strict": True
            }
        },

        # === VideoLingo兼容模式 ===
        "videolingo_compat": {
            "name": "VideoLingo兼容模式",
            "description": "完全兼容VideoLingo配置，无缝迁移现有项目",
            "target_users": ["VideoLingo用户", "迁移项目"],
            "config": {
                # === VideoLingo核心配置 ===
                "max_length": 75,
                "max_chars_per_line": 20,
                "target_multiplier": 1.2,
                "line_break_chars": "。！？；.,!?;",
                
                # === VideoLingo算法配置 ===
                "use_dp_algorithm": True,
                "dp_max_length": 60,
                "dp_min_length": 30,
                "dp_search_range": 100,
                "use_spacy": True,
                "spacy_model": "auto",
                
                # === VideoLingo分割策略 ===
                "split_strategy": "hybrid",
                "semantic_priority": True,
                "punctuation_weights": {
                    "。": 1.0, "！": 1.0, "？": 1.0,
                    "，": 0.6, "；": 0.8, ",": 0.6, ";": 0.8
                },
                
                # === 兼容性特殊设置 ===
                "videolingo_mode": True,
                "legacy_support": True,
                "migration_mode": True,
                "fallback_enabled": True,
                
                # === 样式配置 ===
                "style": "videolingo_default",
                "font_size": 24,
                "font_family": "Microsoft YaHei",
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "background_opacity": 0.75,
                
                # === 处理配置 ===
                "processing_mode": "balanced",
                "max_workers": 4,
                "timeout_seconds": 600,
                "enable_cache": True
            }
        },

        # === 高性能模式 ===
        "performance": {
            "name": "高性能模式",
            "description": "优化速度和资源使用，适合批量处理",
            "target_users": ["批量处理", "服务器部署"],
            "config": {
                # 性能优化配置
                "max_length": 80,
                "target_multiplier": 1.3,
                "processing_mode": "fast",
                
                # 算法选择（性能优先）
                "use_dp_algorithm": True,
                "use_spacy": False,  # 关闭Spacy提高速度
                "use_enhanced_weight": False,
                
                # 并发配置
                "max_workers": 8,
                "enable_parallel_processing": True,
                "chunk_size": 100,
                
                # 缓存优化
                "enable_cache": True,
                "cache_size": 1000,
                "aggressive_caching": True,
                
                # 简化功能
                "ai_splitting": False,
                "smart_processing": False,
                "quality_assurance": False,
                
                # 样式简化
                "style": "simple",
                "font_size": 24,
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "background_opacity": 0.7
            }
        },
        
        "custom": {
            "name": "自定义模式",
            "description": "基于现有配置的自定义模式",
            "target_users": ["高级用户", "特殊需求"],
            "config": {
                # 将基于用户现有配置动态生成
                "inherit_from": "standard",
                "allow_override": True
            }
        }
    }
    
    # 配置分组定义
    CONFIG_GROUPS = {
        "basic": {
            "name": "基础设置",
            "description": "核心字幕配置",
            "fields": [
                "max_length", "target_multiplier", "processing_mode",
                "font_size", "font_family", "text_color"
            ]
        },
        
        "algorithm": {
            "name": "算法设置",
            "description": "处理算法选择",
            "fields": [
                "use_dp_algorithm", "use_spacy", "use_enhanced_weight",
                "ai_splitting", "smart_processing"
            ]
        },
        
        "style": {
            "name": "样式设置", 
            "description": "字幕外观配置",
            "fields": [
                "style", "background_color", "background_opacity",
                "outline_color", "outline_width", "shadow_enabled"
            ]
        },
        
        "quality": {
            "name": "质量设置",
            "description": "质量和性能配置",
            "fields": [
                "quality_level", "performance_priority", "auto_timing",
                "quality_assurance", "strict_timing"
            ]
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        获取预设配置
        
        Args:
            preset_name: 预设名称 (simple, standard, professional, custom)
            
        Returns:
            预设配置字典，如果不存在返回None
        """
        return cls.PRESETS.get(preset_name)
    
    @classmethod
    def get_preset_config(cls, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        获取预设的配置部分
        
        Args:
            preset_name: 预设名称
            
        Returns:
            配置字典，如果不存在返回None
        """
        preset = cls.get_preset(preset_name)
        return preset.get("config") if preset else None
    
    @classmethod
    def list_presets(cls) -> List[Dict[str, str]]:
        """
        列出所有可用预设
        
        Returns:
            预设信息列表
        """
        return [
            {
                "name": name,
                "display_name": preset["name"],
                "description": preset["description"],
                "target_users": preset.get("target_users", [])
            }
            for name, preset in cls.PRESETS.items()
        ]
    
    @classmethod
    def create_config_from_preset(cls, preset_name: str, 
                                  overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        基于预设创建配置
        
        Args:
            preset_name: 预设名称
            overrides: 覆盖配置
            
        Returns:
            完整配置字典
        """
        preset_config = cls.get_preset_config(preset_name)
        if not preset_config:
            raise ValueError(f"未知预设: {preset_name}")
        
        # 复制预设配置
        config = preset_config.copy()
        
        # 应用覆盖配置
        if overrides:
            config.update(overrides)
        
        # 添加元数据
        config["_metadata"] = {
            "preset": preset_name,
            "created_time": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        return config
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any], 
                       preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        验证配置有效性
        
        Args:
            config: 待验证配置
            preset_name: 基础预设名称
            
        Returns:
            验证结果
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # 基础验证
        required_fields = ["max_length", "processing_mode"]
        for field in required_fields:
            if field not in config:
                result["errors"].append(f"缺少必需字段: {field}")
                result["valid"] = False
        
        # 值范围验证
        if "max_length" in config:
            if not isinstance(config["max_length"], (int, float)) or config["max_length"] <= 0:
                result["errors"].append("max_length必须是正数")
                result["valid"] = False
            elif config["max_length"] > 200:
                result["warnings"].append("max_length过大可能影响显示效果")
        
        if "target_multiplier" in config:
            if not isinstance(config["target_multiplier"], (int, float)) or config["target_multiplier"] <= 0:
                result["errors"].append("target_multiplier必须是正数")
                result["valid"] = False
        
        # 样式验证
        if "font_size" in config:
            if not isinstance(config["font_size"], (int, float)) or config["font_size"] <= 0:
                result["errors"].append("font_size必须是正数")
                result["valid"] = False
            elif config["font_size"] < 12:
                result["warnings"].append("字体大小过小可能影响可读性")
            elif config["font_size"] > 48:
                result["warnings"].append("字体大小过大可能影响显示效果")
        
        # 兼容性检查
        if config.get("use_spacy") and not config.get("use_dp_algorithm"):
            result["warnings"].append("建议在启用Spacy时同时启用动态规划算法")
        
        # 性能建议
        if config.get("ai_splitting") and config.get("performance_priority"):
            result["suggestions"].append("AI分割可能影响性能，建议关闭性能优先模式")
        
        return result
    
    @classmethod
    def get_config_groups(cls, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        将配置按组分类
        
        Args:
            config: 配置字典
            
        Returns:
            分组后的配置
        """
        grouped = {}
        
        for group_name, group_info in cls.CONFIG_GROUPS.items():
            group_config = {}
            for field in group_info["fields"]:
                if field in config:
                    group_config[field] = config[field]
            
            if group_config:  # 只包含非空组
                grouped[group_name] = {
                    "name": group_info["name"],
                    "description": group_info["description"],
                    "config": group_config
                }
        
        return grouped
    
    @classmethod
    def merge_configs(cls, base_config: Dict[str, Any], 
                     override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并两个配置
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            合并后的配置
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # 递归合并字典
                merged[key] = cls.merge_configs(merged[key], value)
            else:
                # 直接覆盖
                merged[key] = value
        
        return merged
    
    @classmethod
    def export_config(cls, config: Dict[str, Any], format: str = "json") -> str:
        """
        导出配置
        
        Args:
            config: 配置字典
            format: 导出格式 (json, yaml)
            
        Returns:
            配置字符串
        """
        if format.lower() == "json":
            return json.dumps(config, indent=2, ensure_ascii=False)
        elif format.lower() == "yaml":
            if YAML_AVAILABLE and yaml is not None:
                return yaml.dump(config, default_flow_style=False, allow_unicode=True)
            else:
                logger.warning("yaml模块不可用，使用json格式")
                return json.dumps(config, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    @classmethod
    def import_config(cls, config_str: str, format: str = "auto") -> Dict[str, Any]:
        """
        导入配置
        
        Args:
            config_str: 配置字符串
            format: 配置格式 (json, yaml, auto)
            
        Returns:
            配置字典
        """
        if format == "auto":
            # 自动检测格式
            config_str = config_str.strip()
            if config_str.startswith("{"):
                format = "json"
            else:
                format = "yaml"
        
        if format.lower() == "json":
            return json.loads(config_str)
        elif format.lower() == "yaml":
            if YAML_AVAILABLE and yaml is not None:
                return yaml.safe_load(config_str)
            else:
                raise ImportError("yaml模块不可用，请安装pyyaml或使用json格式")
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    # Netflix预设集成方法
    @staticmethod
    def get_netflix_presets() -> List[Dict[str, str]]:
        """获取Netflix预设列表"""
        if NetflixSubtitlePresets is None:
            logger.warning("Netflix预设模块不可用")
            return []
        
        return NetflixSubtitlePresets.list_presets()
    
    @staticmethod
    def create_netflix_config(preset_name: str, base_preset: str = "professional") -> Dict[str, Any]:
        """
        创建基于Netflix预设的配置
        
        Args:
            preset_name: Netflix预设名称
            base_preset: 基础预设名称
            
        Returns:
            集成Netflix预设的配置
        """
        if NetflixSubtitlePresets is None or NetflixConfigIntegrator is None:
            raise ValueError("Netflix预设模块不可用")
        
        # 获取基础预设配置
        base_config = ConfigPresets.create_config_from_preset(base_preset)
        
        # 创建Netflix集成器并应用预设
        integrator = NetflixConfigIntegrator()
        netflix_config = integrator.integrate_with_existing_config(base_config, preset_name)
        
        # 添加Netflix预设元数据
        netflix_config["_metadata"] = netflix_config.get("_metadata", {})
        netflix_config["_metadata"].update({
            "netflix_preset": preset_name,
            "base_preset": base_preset,
            "type": "netflix_integrated",
            "created_at": datetime.now().isoformat()
        })
        
        return netflix_config
    
    @staticmethod
    def validate_netflix_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """验证Netflix配置"""
        if NetflixSubtitlePresets is None:
            return {
                "valid": False,
                "errors": ["Netflix预设模块不可用"],
                "warnings": [],
                "netflix_compliant": False
            }
        
        return NetflixSubtitlePresets.validate_netflix_config(config)
    
    @staticmethod
    def list_all_presets() -> Dict[str, List[Dict[str, str]]]:
        """获取所有可用预设（包括基础预设和Netflix预设）"""
        all_presets = {
            "basic": ConfigPresets.list_presets(),
            "netflix": ConfigPresets.get_netflix_presets()
        }
        
        return all_presets


class SimpleConfigManager:
    """简化配置管理器 - 提供简洁的配置接口"""
    
    def __init__(self, preset_name: str = "standard"):
        """
        初始化简化配置管理器
        
        Args:
            preset_name: 默认预设名称
        """
        self.preset_name = preset_name
        self.config = ConfigPresets.create_config_from_preset(preset_name)
        self.logger = logging.getLogger(__name__)
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            updates: 更新的配置项
        """
        self.config.update(updates)
        
        # 验证配置
        validation = ConfigPresets.validate_config(self.config, self.preset_name)
        if not validation["valid"]:
            self.logger.warning(f"配置验证失败: {validation['errors']}")
        if validation["warnings"]:
            self.logger.info(f"配置警告: {validation['warnings']}")
    
    def reset_to_preset(self, preset_name: Optional[str] = None) -> None:
        """
        重置到预设配置
        
        Args:
            preset_name: 预设名称，None表示重置到当前预设
        """
        preset_name = preset_name or self.preset_name
        self.config = ConfigPresets.create_config_from_preset(preset_name)
        self.preset_name = preset_name
    
    def get_simple_settings(self) -> Dict[str, Any]:
        """
        获取简化设置（只包含常用配置）
        
        Returns:
            简化设置字典
        """
        simple_keys = [
            "max_length", "processing_mode", "font_size", 
            "text_color", "background_opacity", "quality_level"
        ]
        
        return {key: self.config.get(key) for key in simple_keys if key in self.config}
    
    def update_simple_settings(self, settings: Dict[str, Any]) -> None:
        """
        更新简化设置
        
        Args:
            settings: 简化设置
        """
        allowed_keys = [
            "max_length", "processing_mode", "font_size",
            "text_color", "background_opacity", "quality_level"
        ]
        
        filtered_settings = {k: v for k, v in settings.items() if k in allowed_keys}
        self.update_config(filtered_settings)
    
    def get_preset_info(self) -> Dict[str, Any]:
        """获取当前预设信息"""
        return ConfigPresets.get_preset(self.preset_name) or {}
    
    def save_config(self, filepath: str) -> None:
        """
        保存配置到文件
        
        Args:
            filepath: 文件路径
        """
        try:
            config_str = ConfigPresets.export_config(self.config)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(config_str)
            self.logger.info(f"配置已保存到: {filepath}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            raise
    
    def load_config(self, filepath: str) -> None:
        """
        从文件加载配置
        
        Args:
            filepath: 文件路径
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_str = f.read()
            
            loaded_config = ConfigPresets.import_config(config_str)
            self.config = loaded_config
            self.logger.info(f"配置已从文件加载: {filepath}")
            
            # 验证加载的配置
            validation = ConfigPresets.validate_config(self.config)
            if not validation["valid"]:
                self.logger.warning(f"加载的配置验证失败: {validation['errors']}")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            raise


class NetflixAwareConfigManager(SimpleConfigManager):
    """支持Netflix预设的配置管理器"""
    
    def __init__(self, preset_name: str = "standard", netflix_preset: Optional[str] = None):
        """
        初始化Netflix感知配置管理器
        
        Args:
            preset_name: 基础预设名称
            netflix_preset: Netflix预设名称（可选）
        """
        self.netflix_preset = netflix_preset
        
        if netflix_preset:
            # 创建Netflix集成配置
            self.preset_config = ConfigPresets.create_netflix_config(netflix_preset, preset_name)
            self.preset_name = f"{preset_name}_netflix_{netflix_preset}"
        else:
            # 使用标准预设
            super().__init__(preset_name)
            return
        
        self.user_overrides = {}
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"已创建Netflix感知配置管理器: {self.preset_name}")
    
    def get_netflix_style_config(self) -> Optional[Dict[str, Any]]:
        """获取Netflix样式配置"""
        if not self.netflix_preset:
            return None
        
        return self.preset_config.get("smart_subtitle_processing", {}).get("netflix_style", {})
    
    def get_netflix_display_config(self) -> Optional[Dict[str, Any]]:
        """获取Netflix显示配置"""
        if not self.netflix_preset:
            return None
        
        subtitle_config = self.preset_config.get("smart_subtitle_processing", {})
        return {
            "max_length": subtitle_config.get("max_length"),
            "max_lines": subtitle_config.get("max_lines"),
            "reading_speed_wpm": subtitle_config.get("reading_speed_wpm"),
            "min_duration_ms": subtitle_config.get("min_duration_ms"),
            "max_duration_ms": subtitle_config.get("max_duration_ms"),
            "subtitle_gap_ms": subtitle_config.get("subtitle_gap_ms")
        }
    
    def validate_netflix_compliance(self) -> Dict[str, Any]:
        """验证Netflix合规性"""
        if not self.netflix_preset:
            return {
                "valid": True,
                "netflix_compliant": False,
                "message": "未使用Netflix预设"
            }
        
        config = self.get_config()
        return ConfigPresets.validate_netflix_config(config)
    
    def export_netflix_srt_style(self) -> Optional[str]:
        """导出Netflix SRT样式"""
        if not self.netflix_preset or NetflixConfigIntegrator is None:
            return None
        
        integrator = NetflixConfigIntegrator()
        netflix_config = {
            "style": self.get_netflix_style_config(),
            "display": self.get_netflix_display_config()
        }
        
        return integrator.export_to_srt_style(netflix_config)
    
    def export_netflix_ass_style(self) -> Optional[str]:
        """导出Netflix ASS样式"""
        if not self.netflix_preset or NetflixConfigIntegrator is None:
            return None
        
        integrator = NetflixConfigIntegrator()
        netflix_config = {
            "style": self.get_netflix_style_config(),
            "display": self.get_netflix_display_config()
        }
        
        return integrator.export_to_ass_style(netflix_config)
    
    def optimize_for_content_type(self, content_type: str):
        """根据内容类型优化配置"""
        if not self.netflix_preset or NetflixSubtitlePresets is None:
            self.logger.warning("Netflix预设不可用，无法进行内容优化")
            return
        
        # 获取当前配置
        current_config = self.get_config()
        
        # 优化配置
        optimized_config = NetflixSubtitlePresets.optimize_for_content_type(
            content_type, current_config
        )
        
        # 应用优化配置
        self.preset_config = optimized_config
        self.logger.info(f"已为内容类型 '{content_type}' 优化配置")
    
    def get_preset_info(self) -> Dict[str, Any]:
        """获取预设信息（包括Netflix信息）"""
        info = super().get_preset_info()
        
        if self.netflix_preset:
            info.update({
                "netflix_preset": self.netflix_preset,
                "netflix_metadata": self.preset_config.get("_metadata", {}).get("netflix_metadata", {}),
                "type": "netflix_integrated"
            })
        
        return info


# 便捷函数
def create_netflix_config_manager(preset_name: str, netflix_preset: str) -> NetflixAwareConfigManager:
    """创建Netflix配置管理器的便捷函数"""
    return NetflixAwareConfigManager(preset_name, netflix_preset)


def get_all_available_presets() -> Dict[str, List[Dict[str, str]]]:
    """获取所有可用预设的便捷函数"""
    return ConfigPresets.list_all_presets()
