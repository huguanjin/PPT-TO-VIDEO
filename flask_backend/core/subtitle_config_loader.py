"""
智能字幕配置加载器
集成Netflix级字幕配置和智能处理参数
支持简化配置预设系统
已集成多行显示修复功能
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from flask_backend.core.unified_config_manager import UnifiedConfigManager, ConfigContext, ConfigModuleType, ConfigComplexityLevel
from .config_presets import ConfigPresets, SimpleConfigManager
from .subtitle_multiline_fixer import SubtitleMultilineFixer


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
        
        # 初始化多行修复器
        self.multiline_fixer = SubtitleMultilineFixer()
        
        # 加载配置
        self.config = self.config_manager.get_config(self.context)
        self._ensure_backward_compatibility()
        self._apply_multiline_fix_config()
        
        # 记录配置信息
        config_summary = self.get_config_summary()
        self.logger.info(
            f"字幕配置加载完成 - 预设: {config_summary.get('preset', 'default')}, "
            f"复杂度: {self.context.complexity_level.value}"
        )
        self.logger.info("多行显示修复功能已集成到配置系统")
    
    def _ensure_backward_compatibility(self):
        """确保向后兼容性"""
        # 确保存在必要的配置节
        if "smart_subtitle_processing" not in self.config:
            self.config["smart_subtitle_processing"] = {}
        
        # 如果使用预设，将预设配置映射到传统配置结构
        if self.config_manager:
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
    
    def _apply_multiline_fix_config(self):
        """应用多行显示修复配置"""
        try:
            # 获取修复配置
            fix_config = self.multiline_fixer.config
            
            # 更新字符权重配置
            if "character_weight_adjustments" in fix_config:
                if "smart_subtitle_processing" not in self.config:
                    self.config["smart_subtitle_processing"] = {}
                
                self.config["smart_subtitle_processing"]["character_weights"] = fix_config["character_weight_adjustments"]
                
            # 更新行控制规则
            if "line_control_rules" in fix_config:
                line_rules = fix_config["line_control_rules"]
                self.config.update({
                    "max_chars_per_line": line_rules.get("max_chars_per_line_chinese", 30),
                    "max_lines": line_rules.get("max_lines_strict", 2),
                    "enforce_line_limit": line_rules.get("enforce_line_limit", True),
                    "multiline_fix_enabled": True
                })
            
            self.logger.info("多行修复配置已应用到字幕配置系统")
            
        except Exception as e:
            self.logger.warning(f"应用多行修复配置失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def get_simple_config(self) -> Dict[str, Any]:
        """获取简化配置（仅包含常用设置）"""
        # 返回简化的配置字典，只包含最常用的设置
        simple_keys = [
            'font_family', 'font_size', 'font_color', 'background_color',
            'max_chars_per_line', 'max_lines', 'position_y', 'alignment',
            'language_code', 'voice_name', 'speech_rate'
        ]
        return {key: self.config.get(key) for key in simple_keys if key in self.config}
    
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
        current_overrides = {}
        if keep_overrides and hasattr(self, 'config'):
            current_overrides = self.config.copy()
        
        # 创建新的配置上下文
        self.context = ConfigContext(
            module_type=ConfigModuleType.SUBTITLE,
            complexity_level=ConfigComplexityLevel.STANDARD,
            preset_name=preset_name
        )
        
        # 重新加载配置
        self.config = self.config_manager.get_config(self.context)
        
        # 如果需要保留重写配置，则应用它们
        if keep_overrides and current_overrides:
            self.config.update(current_overrides)
        
        self.preset = preset_name
        self._ensure_backward_compatibility()
        
        self.logger.info(f"字幕配置已切换到预设: {preset_name}")
    
    def get_preset_info(self) -> Dict[str, Any]:
        """获取当前预设信息"""
        return {
            'preset_name': self.preset or 'default',
            'module_type': self.context.module_type.value,
            'complexity_level': self.context.complexity_level.value,
            'config_count': len(self.config),
            'has_custom_config': self.preset != self.context.preset_name
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """验证当前配置"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 检查必需的配置项
        required_keys = ['font_family', 'font_size', 'language_code']
        for key in required_keys:
            if key not in self.config or self.config[key] is None:
                validation_result['errors'].append(f"缺少必需的配置项: {key}")
                validation_result['is_valid'] = False
        
        # 检查配置值的有效性
        if 'font_size' in self.config:
            try:
                size = int(self.config['font_size'])
                if size < 8 or size > 72:
                    validation_result['warnings'].append("字体大小建议在8-72之间")
            except (ValueError, TypeError):
                validation_result['errors'].append("字体大小必须是数字")
                validation_result['is_valid'] = False
        
        return validation_result
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'preset': self.preset or 'default',
            'total_settings': len(self.config),
            'font_settings': {
                'family': self.config.get('font_family', 'default'),
                'size': self.config.get('font_size', 16),
                'color': self.config.get('font_color', '#FFFFFF')
            },
            'layout_settings': {
                'max_chars_per_line': self.config.get('max_chars_per_line', 40),
                'max_lines': self.config.get('max_lines', 2),
                'position_y': self.config.get('position_y', 0.8)
            },
            'language': self.config.get('language_code', 'zh-CN'),
            'has_custom_overrides': self.preset != self.context.preset_name
        }
    
    def save_config(self, filepath: Optional[str] = None):
        """保存配置到文件"""
        try:
            save_path = Path(filepath) if filepath else self.config_file
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            raise
    
    def export_for_sharing(self, include_metadata: bool = True) -> str:
        """导出配置用于分享"""
        export_data = {
            'config': self.config.copy(),
            'preset': self.preset
        }
        
        if include_metadata:
            export_data['metadata'] = {
                'exported_at': datetime.now().isoformat(),
                'module_type': self.context.module_type.value,
                'complexity_level': self.context.complexity_level.value,
                'version': '2.0'
            }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def import_shared_config(self, config_str: str) -> bool:
        """导入分享的配置"""
        try:
            import_data = json.loads(config_str)
            
            if 'config' not in import_data:
                self.logger.error("导入数据缺少config字段")
                return False
            
            # 验证导入的配置
            imported_config = import_data['config']
            if not isinstance(imported_config, dict):
                self.logger.error("导入的配置格式无效")
                return False
            
            # 应用导入的配置
            self.update_config(imported_config, save=True)
            
            # 如果有预设信息，也更新预设
            if 'preset' in import_data:
                self.preset = import_data['preset']
            
            self.logger.info("配置导入成功")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"配置导入失败，JSON格式错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"配置导入失败: {e}")
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
    loader = SmartSubtitleConfigLoader(config_dir)
    return loader.get_config()


def create_config_loader(config_dir: Optional[Path] = None, 
                        preset: Optional[str] = None) -> SmartSubtitleConfigLoader:
    """创建配置加载器的便捷函数"""
    return SmartSubtitleConfigLoader(config_dir, preset)
