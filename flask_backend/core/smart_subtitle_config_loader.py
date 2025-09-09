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
from .enhanced_config_loader import EnhancedSubtitleConfigLoader
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
        
        # 初始化增强配置加载器
        self.enhanced_loader = EnhancedSubtitleConfigLoader(
            str(self.config_file) if self.config_file.exists() else None,
            self.preset
        )
        
        # 加载配置
        self.config = self.enhanced_loader.get_config()
        self._ensure_backward_compatibility()
        
        # 记录配置信息
        config_summary = self.enhanced_loader.get_config_summary()
        self.logger.info(
            f"字幕配置加载完成 - 预设: {config_summary['preset_display_name']}, "
            f"复杂度: {config_summary['complexity_level']}"
        )
    
    def _ensure_backward_compatibility(self):
        """确保向后兼容性"""
        # 确保存在必要的配置节
        if "smart_subtitle_processing" not in self.config:
            self.config["smart_subtitle_processing"] = {}
        
        # 如果使用预设，将预设配置映射到传统配置结构
        if hasattr(self.enhanced_loader, 'config_manager') and self.enhanced_loader.config_manager:
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
        return self.enhanced_loader.get_simple_config()
    
    def update_config(self, updates: Dict[str, Any], save: bool = True):
        """
        更新配置
        
        Args:
            updates: 更新的配置项
            save: 是否保存到文件
        """
        self.enhanced_loader.update_config(updates, save)
        self.config = self.enhanced_loader.get_config()
        self._ensure_backward_compatibility()
    
    def switch_preset(self, preset_name: str, keep_overrides: bool = True):
        """
        切换到不同预设
        
        Args:
            preset_name: 新预设名称
            keep_overrides: 是否保留当前的自定义配置
        """
        self.enhanced_loader.switch_preset(preset_name, keep_overrides)
        self.config = self.enhanced_loader.get_config()
        self.preset = preset_name
        self._ensure_backward_compatibility()
        
        self.logger.info(f"字幕配置已切换到预设: {preset_name}")
    
    def get_preset_info(self) -> Dict[str, Any]:
        """获取当前预设信息"""
        return self.enhanced_loader.get_preset_info()
    
    def validate_config(self) -> Dict[str, Any]:
        """验证当前配置"""
        return self.enhanced_loader.validate_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return self.enhanced_loader.get_config_summary()
    
    def save_config(self, filepath: Optional[str] = None):
        """保存配置到文件"""
        self.enhanced_loader.save_config(filepath or str(self.config_file))
    
    def export_for_sharing(self, include_metadata: bool = True) -> str:
        """导出配置用于分享"""
        return self.enhanced_loader.export_for_sharing(include_metadata)
    
    def import_shared_config(self, config_str: str) -> bool:
        """导入分享的配置"""
        success = self.enhanced_loader.import_shared_config(config_str)
        if success:
            self.config = self.enhanced_loader.get_config()
            self._ensure_backward_compatibility()
        return success
    
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
    loader = SmartSubtitleConfigLoader(config_dir)
    return loader.get_config()


def create_config_loader(config_dir: Optional[Path] = None, 
                        preset: Optional[str] = None) -> SmartSubtitleConfigLoader:
    """创建配置加载器的便捷函数"""
    return SmartSubtitleConfigLoader(config_dir, preset)
