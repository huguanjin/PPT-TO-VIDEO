"""
配置加载器增强版
集成简化配置预设系统，提供更友好的配置体验
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from .config_presets import ConfigPresets, SimpleConfigManager

logger = logging.getLogger(__name__)


class EnhancedSubtitleConfigLoader:
    """
    增强的字幕配置加载器
    支持简化配置预设和传统配置文件
    """
    
    def __init__(self, config_path: Optional[str] = None, preset: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径（可选）
            preset: 预设名称（可选，默认为'standard'）
        """
        self.config_path = config_path
        self.preset = preset or 'standard'
        self.config = {}
        self.config_manager = None
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        try:
            if self.config_path and os.path.exists(self.config_path):
                # 从文件加载传统配置
                self._load_from_file()
            else:
                # 使用预设配置
                self._load_from_preset()
        except Exception as e:
            logger.error(f"配置加载失败，使用默认配置: {e}")
            self._load_from_preset('simple')  # 降级到简化模式
    
    def _load_from_file(self):
        """从文件加载配置"""
        logger.info(f"从文件加载配置: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
        
        # 检查是否有预设信息
        if '_metadata' in file_config and 'preset' in file_config['_metadata']:
            preset_name = file_config['_metadata']['preset']
            self.config_manager = SimpleConfigManager(preset_name)
            # 应用文件中的覆盖配置
            overrides = {k: v for k, v in file_config.items() if not k.startswith('_')}
            self.config_manager.update_config(overrides)
            self.config = self.config_manager.get_config()
        else:
            # 传统配置文件
            self.config = file_config
            # 尝试迁移到预设系统
            self._migrate_legacy_config()
    
    def _load_from_preset(self, preset_name: Optional[str] = None):
        """从预设加载配置"""
        preset_name = preset_name or self.preset
        logger.info(f"使用预设配置: {preset_name}")
        
        self.config_manager = SimpleConfigManager(preset_name)
        self.config = self.config_manager.get_config()
    
    def _migrate_legacy_config(self):
        """迁移传统配置到预设系统"""
        logger.info("检测到传统配置，尝试迁移到预设系统")
        
        # 分析配置复杂度来推断适合的预设
        complexity_score = 0
        
        # 检查算法配置
        if self.config.get('use_dp_algorithm'): complexity_score += 2
        if self.config.get('use_spacy'): complexity_score += 3
        if self.config.get('ai_splitting'): complexity_score += 2
        if self.config.get('quality_assurance'): complexity_score += 2
        
        # 检查字符长度限制
        max_length = self.config.get('max_length', 75)
        if max_length <= 40: complexity_score += 2  # Netflix级别
        
        # 根据复杂度选择预设
        if complexity_score <= 3:
            suggested_preset = 'simple'
        elif complexity_score <= 6:
            suggested_preset = 'standard'
        else:
            suggested_preset = 'professional'
        
        logger.info(f"建议的预设: {suggested_preset} (复杂度评分: {complexity_score})")
        
        # 创建配置管理器并应用传统配置作为覆盖
        self.config_manager = SimpleConfigManager(suggested_preset)
        self.config_manager.update_config(self.config)
        self.config = self.config_manager.get_config()
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def get_simple_config(self) -> Dict[str, Any]:
        """获取简化配置（仅包含常用设置）"""
        if self.config_manager:
            return self.config_manager.get_simple_settings()
        else:
            # 从传统配置中提取简化设置
            simple_keys = [
                "max_length", "processing_mode", "font_size",
                "text_color", "background_opacity", "quality_level"
            ]
            return {key: self.config.get(key) for key in simple_keys if key in self.config}
    
    def update_config(self, updates: Dict[str, Any], save: bool = True):
        """
        更新配置
        
        Args:
            updates: 更新的配置项
            save: 是否保存到文件
        """
        if self.config_manager:
            self.config_manager.update_config(updates)
            self.config = self.config_manager.get_config()
        else:
            self.config.update(updates)
        
        if save and self.config_path:
            self.save_config()
    
    def save_config(self, filepath: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            filepath: 保存路径（可选，默认为当前配置路径）
        """
        filepath = filepath or self.config_path
        if not filepath:
            logger.warning("未指定保存路径，无法保存配置")
            return
        
        try:
            if self.config_manager:
                self.config_manager.save_config(filepath)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def switch_preset(self, preset_name: str, keep_overrides: bool = True):
        """
        切换到不同预设
        
        Args:
            preset_name: 新预设名称
            keep_overrides: 是否保留当前的自定义配置
        """
        if keep_overrides and self.config_manager:
            # 保存当前的自定义配置
            current_simple = self.config_manager.get_simple_settings()
            
            # 切换预设
            self.config_manager = SimpleConfigManager(preset_name)
            
            # 应用保存的自定义配置
            self.config_manager.update_simple_settings(current_simple)
        else:
            # 直接切换，不保留自定义配置
            self.config_manager = SimpleConfigManager(preset_name)
        
        self.config = self.config_manager.get_config()
        self.preset = preset_name
        
        logger.info(f"已切换到预设: {preset_name}")
    
    def get_preset_info(self) -> Dict[str, Any]:
        """获取当前预设信息"""
        if self.config_manager:
            return self.config_manager.get_preset_info()
        else:
            return {
                "name": "传统配置",
                "description": "从配置文件加载的传统配置",
                "target_users": ["传统用户"]
            }
    
    def validate_config(self) -> Dict[str, Any]:
        """验证当前配置"""
        return ConfigPresets.validate_config(self.config, self.preset)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        preset_info = self.get_preset_info()
        validation = self.validate_config()
        
        # 计算配置复杂度
        complexity_indicators = [
            self.config.get('use_dp_algorithm', False),
            self.config.get('use_spacy', False),
            self.config.get('use_enhanced_weight', False),
            self.config.get('ai_splitting', False),
            self.config.get('quality_assurance', False)
        ]
        complexity_score = sum(complexity_indicators)
        
        complexity_levels = ["极简", "简单", "中等", "复杂", "高级"]
        complexity_level = complexity_levels[min(complexity_score, len(complexity_levels) - 1)]
        
        return {
            "preset_name": self.preset,
            "preset_display_name": preset_info.get("name", "未知"),
            "description": preset_info.get("description", ""),
            "complexity_level": complexity_level,
            "complexity_score": complexity_score,
            "total_config_items": len(self.config),
            "is_valid": validation["valid"],
            "has_warnings": len(validation["warnings"]) > 0,
            "has_errors": len(validation["errors"]) > 0,
            "key_settings": {
                "max_length": self.config.get("max_length"),
                "processing_mode": self.config.get("processing_mode"),
                "quality_level": self.config.get("quality_level"),
                "ai_enabled": self.config.get("ai_splitting", False)
            }
        }
    
    def export_for_sharing(self, include_metadata: bool = True) -> str:
        """
        导出配置用于分享
        
        Args:
            include_metadata: 是否包含元数据
            
        Returns:
            配置的JSON字符串
        """
        config_to_export = self.config.copy()
        
        if not include_metadata and '_metadata' in config_to_export:
            del config_to_export['_metadata']
        
        return json.dumps(config_to_export, indent=2, ensure_ascii=False)
    
    def import_shared_config(self, config_str: str) -> bool:
        """
        导入分享的配置
        
        Args:
            config_str: 配置JSON字符串
            
        Returns:
            是否导入成功
        """
        try:
            imported_config = json.loads(config_str)
            
            # 检查是否有预设信息
            if '_metadata' in imported_config and 'preset' in imported_config['_metadata']:
                preset_name = imported_config['_metadata']['preset']
                self.switch_preset(preset_name, keep_overrides=False)
                
                # 应用导入的配置
                overrides = {k: v for k, v in imported_config.items() if not k.startswith('_')}
                self.update_config(overrides, save=False)
            else:
                # 直接应用配置
                self.config = imported_config
                self.config_manager = None
            
            logger.info("成功导入分享的配置")
            return True
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False


def create_config_loader(config_path: Optional[str] = None, 
                        preset: Optional[str] = None) -> EnhancedSubtitleConfigLoader:
    """
    创建配置加载器的便捷函数
    
    Args:
        config_path: 配置文件路径
        preset: 预设名称
        
    Returns:
        配置加载器实例
    """
    return EnhancedSubtitleConfigLoader(config_path, preset)


def get_available_presets() -> List[Dict[str, str]]:
    """获取可用预设列表"""
    return ConfigPresets.list_presets()


def create_preset_config(preset_name: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """创建基于预设的配置"""
    return ConfigPresets.create_config_from_preset(preset_name, overrides)
