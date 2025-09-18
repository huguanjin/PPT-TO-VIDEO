"""
智能字幕配置加载器
集成Netflix级字幕配置和智能处理参数
支持简化配置预设系统
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from flask_backend.core.unified_config_manager import UnifiedConfigManager, ConfigContext, ConfigModuleType, ConfigComplexityLevel
from .config_presets import ConfigPresets, SimpleConfigManager


class SmartSubtitleConfigLoader:
    """智能字幕配置加载器（增强版）"""
    
    def __init__(self, config_dir: Optional[Path] = None, preset: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录
            preset: 预设名称（可选，支持 simple/standard/professional）
        """
        self.config_dir = config_dir or Path(__file__).parent.parent / "config_data"
        self.logger = logging.getLogger(__name__)
        self.preset = preset or 'standard'
        
        # 配置文件路径
        self.config_file = self.config_dir / "subtitle_config.json"
        
        # 初始化统一配置管理器
        self.config_manager = UnifiedConfigManager(
            config_root=self.config_dir
        )
        
        # 创建配置上下文
        self.context = ConfigContext(
            module_type=ConfigModuleType.SUBTITLE,
            complexity_level=ConfigComplexityLevel.STANDARD,
            preset_name=self.preset or "smart_subtitle"
        )
        
        # 加载配置
        self.config = self.config_manager.get_config(self.context)
        self._ensure_backward_compatibility()
        
        # 记录配置信息
        self.logger.info(
            f"字幕配置加载完成 - 预设: {self.preset or 'default'}, "
            f"复杂度: {self.context.complexity_level.value}"
        )
    
    def _ensure_backward_compatibility(self):
        """确保向后兼容性"""
        # 确保存在必要的配置节
        if "smart_subtitle_processing" not in self.config:
            self.config["smart_subtitle_processing"] = {}
        
        # 映射配置到传统配置结构
        subtitle_config = self.config["smart_subtitle_processing"]
        
        # 映射基础配置
        subtitle_config.update({
            "enabled": True,
            "max_length": self.config.get("max_length", 75),
            "target_multiplier": self.config.get("target_multiplier", 1.2),
            "smart_split": self.config.get("smart_split", True),
            "use_ai_splitting": self.config.get("ai_splitting", False),
            "use_dp_algorithm": self.config.get("use_dp_algorithm", True),
            "use_spacy": self.config.get("use_spacy", True),
            "use_enhanced_weight": self.config.get("use_enhanced_weight", False)
        })
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def get_simple_config(self) -> Dict[str, Any]:
        """获取简化配置（仅包含常用设置）"""
        # 从完整配置中提取简化设置
        return {
            "max_length": self.config.get("max_length", 75),
            "smart_split": self.config.get("smart_split", True),
            "use_ai_splitting": self.config.get("ai_splitting", False),
            "use_dp_algorithm": self.config.get("use_dp_algorithm", True),
            "preset": self.preset or "standard"
        }
    
    def update_config(self, updates: Dict[str, Any], save: bool = True):
        """
        更新配置
        
        Args:
            updates: 更新的配置项
            save: 是否保存到文件
        """
        # 更新本地配置
        self.config.update(updates)
        self._ensure_backward_compatibility()
        
        if save:
            self.save_config()
    
    def switch_preset(self, preset_name: str, keep_overrides: bool = True):
        """
        切换到不同预设
        
        Args:
            preset_name: 新预设名称
            keep_overrides: 是否保留当前的自定义配置
        """
        # 保存当前的自定义配置
        overrides = {} if not keep_overrides else {
            k: v for k, v in self.config.items() 
            if k not in ["preset_name", "module_type", "complexity_level"]
        }
        
        # 更新预设
        self.preset = preset_name
        self.context.preset_name = preset_name
        
        # 重新加载配置
        self.config = self.config_manager.get_config(self.context)
        
        # 应用保留的自定义配置
        if overrides:
            self.config.update(overrides)
            
        self._ensure_backward_compatibility()
        self.logger.info(f"字幕配置已切换到预设: {preset_name}")
    
    def get_preset_info(self) -> Dict[str, Any]:
        """获取当前预设信息"""
        return {
            "preset_name": self.preset or "default",
            "module_type": self.context.module_type.value,
            "complexity_level": self.context.complexity_level.value,
            "description": f"智能字幕配置预设: {self.preset}"
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """验证当前配置"""
        errors = []
        warnings = []
        
        # 基本验证
        if self.config.get("max_length", 0) <= 0:
            errors.append("max_length must be positive")
        
        if self.config.get("target_multiplier", 0) <= 0:
            errors.append("target_multiplier must be positive")
            
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "preset_name": self.preset or "default",
            "preset_display_name": f"智能字幕 - {self.preset or 'default'}",
            "complexity_level": self.context.complexity_level.value,
            "total_settings": len(self.config),
            "key_settings": {
                "max_length": self.config.get("max_length", 75),
                "smart_split": self.config.get("smart_split", True),
                "ai_splitting": self.config.get("ai_splitting", False)
            }
        }
    
    def save_config(self, filepath: Optional[str] = None):
        """保存配置到文件"""
        save_path = filepath or str(self.config_file)
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            raise
    
    def export_for_sharing(self, include_metadata: bool = True) -> str:
        """导出配置用于分享"""
        export_data = {
            "config": self.config,
            "preset": self.preset
        }
        
        if include_metadata:
            export_data["metadata"] = {
                "export_time": "2025-09-18",
                "version": "1.0",
                "type": "smart_subtitle_config"
            }
            
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def import_shared_config(self, config_str: str) -> bool:
        """导入分享的配置"""
        try:
            data = json.loads(config_str)
            
            if "config" in data:
                self.config = data["config"]
                
            if "preset" in data:
                self.preset = data["preset"]
                
            self._ensure_backward_compatibility()
            return True
            
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False
    
    @staticmethod
    def get_available_presets() -> list:
        """获取可用预设列表"""
        return ConfigPresets.list_presets()
    
    @classmethod
    def create_from_preset(cls, preset_name: str, config_dir: Optional[Path] = None, 
                          overrides: Optional[Dict[str, Any]] = None) -> 'SmartSubtitleConfigLoader':
        """
        从预设创建配置加载器
        
        Args:
            preset_name: 预设名称
            config_dir: 配置目录
            overrides: 自定义覆盖配置
            
        Returns:
            配置加载器实例
        """
        loader = cls(config_dir, preset_name)
        if overrides:
            loader.update_config(overrides, save=False)
        return loader


# 向后兼容的函数
def load_config(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """加载字幕配置（向后兼容）"""
    config_manager = UnifiedConfigManager(config_root=config_dir)
    context = ConfigContext(
        module_type=ConfigModuleType.SUBTITLE,
        complexity_level=ConfigComplexityLevel.STANDARD,
        preset_name="default"
    )
    return config_manager.get_config(context)


def create_config_loader(config_dir: Optional[Path] = None, 
                        preset: Optional[str] = None) -> SmartSubtitleConfigLoader:
    """创建配置加载器的便捷函数"""
    return SmartSubtitleConfigLoader(config_dir, preset)
