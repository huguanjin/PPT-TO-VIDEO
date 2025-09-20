"""
VideoLingo技术融合的智能配置加载器
基于项目优化计划，实现简化配置体验和高级功能的完美结合
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict

# 导入配置预设
try:
    from .config_presets import ConfigPresets
except ImportError:
    from config_presets import ConfigPresets

# 导入VideoLingo算法
try:
    from .algorithms.dp_sentence_splitter import DynamicProgrammingSplitter
except ImportError:
    try:
        from algorithms.dp_sentence_splitter import DynamicProgrammingSplitter
    except ImportError:
        DynamicProgrammingSplitter = None

logger = logging.getLogger(__name__)


@dataclass
class ConfigContext:
    """配置上下文信息"""
    preset_name: str
    user_overrides: Dict[str, Any]
    project_type: str
    performance_level: str
    language: str = 'auto'
    target_audience: str = 'general'


class SmartSubtitleConfigLoader:
    """
    智能字幕配置加载器
    
    基于VideoLingo技术融合的优化方案：
    1. 提供简化配置模式
    2. 智能预设选择
    3. 动态配置优化
    4. 兼容性保证
    """
    
    def __init__(self, project_dir: Optional[str] = None):
        self.project_dir = project_dir or os.getcwd()
        self.config_presets = ConfigPresets()
        self.logger = logging.getLogger(__name__)
        
        # 缓存已加载的配置
        self._config_cache = {}
        
        # 初始化默认配置路径
        self.config_paths = {
            'user_config': os.path.join(self.project_dir, 'flask_backend', 'config_data', 'subtitle_config.json'),
            'app_config': os.path.join(self.project_dir, 'flask_backend', 'config_data', 'app_config.json'),
            'presets_config': os.path.join(self.project_dir, 'flask_backend', 'config_data', 'config_presets.json')
        }
    
    def load_smart_config(self, 
                         preset_name: str = "standard",
                         user_overrides: Optional[Dict[str, Any]] = None,
                         context: Optional[ConfigContext] = None) -> Dict[str, Any]:
        """
        智能加载配置
        
        Args:
            preset_name: 预设名称
            user_overrides: 用户自定义覆盖配置
            context: 配置上下文
            
        Returns:
            最终的配置字典
        """
        try:
            # 1. 加载预设配置
            base_config = self._load_preset_config(preset_name)
            if not base_config:
                self.logger.warning(f"预设 '{preset_name}' 不存在，使用标准配置")
                base_config = self._load_preset_config("standard")
                
            # 确保base_config不为None
            if not base_config:
                raise ValueError(f"无法加载基础配置，预设: {preset_name}")
            
            # 2. 应用用户配置覆盖
            if user_overrides:
                base_config = self._merge_configs(base_config, user_overrides)
            
            # 3. 应用上下文优化
            if context:
                base_config = self._apply_context_optimization(base_config, context)
            
            # 4. 验证和修正配置
            final_config = self._validate_and_fix_config(base_config)
            
            # 5. 缓存配置
            cache_key = f"{preset_name}_{hash(str(user_overrides))}"
            self._config_cache[cache_key] = final_config
            
            self.logger.info(f"成功加载配置 - 预设: {preset_name}, 处理模式: {final_config.get('processing_mode', 'unknown')}")
            return final_config
            
        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            return self._get_fallback_config()
    
    def _load_preset_config(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """加载预设配置"""
        return self.config_presets.get_preset_config(preset_name)
    
    def _merge_configs(self, base_config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能合并配置
        支持嵌套字典合并
        """
        merged = base_config.copy()
        
        for key, value in overrides.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _apply_context_optimization(self, config: Dict[str, Any], context: ConfigContext) -> Dict[str, Any]:
        """
        根据上下文优化配置
        """
        optimized = config.copy()
        
        # 性能级别优化
        if context.performance_level == 'fast':
            optimized.update({
                'use_spacy': False,
                'ai_splitting': False,
                'quality_assurance': False,
                'max_workers': min(optimized.get('max_workers', 4), 2)
            })
        elif context.performance_level == 'quality':
            optimized.update({
                'use_spacy': True,
                'ai_splitting': True,
                'quality_assurance': True,
                'strict_timing': True
            })
        
        # 项目类型优化
        if context.project_type == 'education':
            optimized.update({
                'max_length': 80,  # 教育内容可以稍长
                'font_size': optimized.get('font_size', 24) + 2,
                'background_opacity': 0.9  # 更好的可读性
            })
        elif context.project_type == 'entertainment':
            optimized.update({
                'max_length': 60,  # 娱乐内容要简洁
                'style': 'netflix_standard'
            })
        
        # 语言特定优化
        if context.language in ['zh', 'ja', 'ko']:
            optimized.update({
                'max_chars_per_line': optimized.get('max_chars_per_line', 20) - 2,
                'use_enhanced_weight': True
            })
        
        return optimized
    
    def _validate_and_fix_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和修正配置
        """
        validated = config.copy()
        
        # 必需字段检查和默认值
        defaults = {
            'max_length': 75,
            'max_chars_per_line': 20,
            'target_multiplier': 1.2,
            'processing_mode': 'balanced',
            'use_dp_algorithm': True,
            'fallback_enabled': True
        }
        
        for key, default_value in defaults.items():
            if key not in validated:
                validated[key] = default_value
                self.logger.warning(f"配置项 '{key}' 缺失，使用默认值: {default_value}")
        
        # 数值范围检查
        if validated['max_length'] <= 0:
            validated['max_length'] = 75
            self.logger.warning("max_length 值无效，重置为 75")
        
        if validated['max_chars_per_line'] <= 0:
            validated['max_chars_per_line'] = 20
            self.logger.warning("max_chars_per_line 值无效，重置为 20")
        
        # VideoLingo兼容性检查
        if validated.get('videolingo_mode'):
            validated = self._apply_videolingo_compatibility(validated)
        
        return validated
    
    def _apply_videolingo_compatibility(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用VideoLingo兼容性设置
        """
        compat_config = config.copy()
        
        # 确保VideoLingo核心功能启用
        compat_config.update({
            'use_dp_algorithm': True,
            'dp_max_length': config.get('dp_max_length', 60),
            'dp_min_length': config.get('dp_min_length', 30),
            'split_strategy': config.get('split_strategy', 'hybrid'),
            'semantic_priority': config.get('semantic_priority', True)
        })
        
        # 特殊的VideoLingo权重配置
        if 'punctuation_weights' in config:
            compat_config['punctuation_weights'] = config['punctuation_weights']
        
        self.logger.info("已应用VideoLingo兼容性配置")
        return compat_config
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """获取备用配置"""
        return {
            'max_length': 75,
            'max_chars_per_line': 20,
            'target_multiplier': 1.2,
            'processing_mode': 'fast',
            'use_dp_algorithm': True,
            'use_spacy': False,
            'fallback_enabled': True,
            'style': 'simple',
            'font_size': 24,
            'text_color': '#FFFFFF',
            'background_color': '#000000',
            'background_opacity': 0.7
        }
    
    def get_available_presets(self) -> List[Dict[str, Any]]:
        """获取所有可用预设"""
        return self.config_presets.list_presets()
    
    def create_preset_from_config(self, 
                                config: Dict[str, Any], 
                                preset_name: str,
                                description: Optional[str] = None) -> bool:
        """
        从当前配置创建新预设
        """
        try:
            custom_preset = {
                "name": preset_name,
                "description": description or f"自定义预设 - {preset_name}",
                "target_users": ["自定义"],
                "config": config
            }
            
            # 保存到文件
            presets_file = self.config_paths['presets_config']
            os.makedirs(os.path.dirname(presets_file), exist_ok=True)
            
            existing_presets = {}
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    existing_presets = json.load(f)
            
            existing_presets[preset_name] = custom_preset
            
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(existing_presets, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"成功创建自定义预设: {preset_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建预设失败: {e}")
            return False
    
    def auto_select_preset(self, 
                          project_type: Optional[str] = None,
                          performance_requirement: str = 'balanced',
                          user_level: str = 'beginner') -> str:
        """
        智能选择最适合的预设
        
        Args:
            project_type: 项目类型 ('education', 'entertainment', 'business', etc.)
            performance_requirement: 性能要求 ('fast', 'balanced', 'quality')
            user_level: 用户水平 ('beginner', 'intermediate', 'expert')
            
        Returns:
            推荐的预设名称
        """
        
        # 初学者优先选择简化模式
        if user_level == 'beginner':
            return 'simple'
        
        # 专家用户根据需求选择
        if user_level == 'expert':
            if performance_requirement == 'quality':
                return 'professional'
            elif performance_requirement == 'fast':
                return 'performance'
        
        # 特殊项目类型
        if project_type == 'videolingo_migration':
            return 'videolingo_compat'
        
        # 默认标准模式
        return 'standard'
    
    def export_current_config(self, 
                            config: Dict[str, Any], 
                            export_path: str,
                            include_metadata: bool = True) -> bool:
        """
        导出当前配置到文件
        """
        try:
            export_data = {
                'config': config,
                'metadata': {
                    'exported_at': str(pd.Timestamp.now()),
                    'version': '2.0',
                    'generator': 'SmartSubtitleConfigLoader'
                } if include_metadata else {}
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置已导出到: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置导出失败: {e}")
            return False
    
    def import_config_from_file(self, import_path: str) -> Optional[Dict[str, Any]]:
        """
        从文件导入配置
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 兼容不同格式
            if 'config' in data:
                config = data['config']
            else:
                config = data
            
            # 验证配置
            validated_config = self._validate_and_fix_config(config)
            self.logger.info(f"成功从文件导入配置: {import_path}")
            
            return validated_config
            
        except Exception as e:
            self.logger.error(f"配置导入失败: {e}")
            return None


# 便捷函数
def create_smart_config(preset_name: str = "standard", 
                       project_dir: Optional[str] = None,
                       **overrides) -> Dict[str, Any]:
    """
    快速创建智能配置（便捷函数）
    
    Example:
        config = create_smart_config(
            preset_name="simple",
            max_length=80,
            use_spacy=False
        )
    """
    loader = SmartSubtitleConfigLoader(project_dir)
    return loader.load_smart_config(preset_name, overrides)


def create_videolingo_config(project_dir: Optional[str] = None, **overrides) -> Dict[str, Any]:
    """
    创建VideoLingo兼容配置（便捷函数）
    """
    return create_smart_config("videolingo_compat", project_dir, **overrides)


def auto_config(project_type: Optional[str] = None,
               performance: str = 'balanced',
               user_level: str = 'beginner',
               project_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    自动选择最佳配置（便捷函数）
    """
    loader = SmartSubtitleConfigLoader(project_dir)
    preset_name = loader.auto_select_preset(project_type, performance, user_level)
    return loader.load_smart_config(preset_name)


if __name__ == "__main__":
    # 测试智能配置加载器
    import pandas as pd
    
    print("=== VideoLingo技术融合配置测试 ===")
    
    # 1. 测试简化配置
    print("\n1. 简化配置测试:")
    simple_config = create_smart_config("simple")
    print(f"  - 处理模式: {simple_config['processing_mode']}")
    print(f"  - 使用Spacy: {simple_config['use_spacy']}")
    print(f"  - 动态规划: {simple_config['use_dp_algorithm']}")
    
    # 2. 测试VideoLingo兼容配置
    print("\n2. VideoLingo兼容配置测试:")
    vl_config = create_videolingo_config()
    print(f"  - VideoLingo模式: {vl_config.get('videolingo_mode', False)}")
    print(f"  - 分割策略: {vl_config.get('split_strategy', 'unknown')}")
    
    # 3. 测试自动配置选择
    print("\n3. 自动配置选择测试:")
    auto_cfg = auto_config(project_type='education', user_level='expert')
    print(f"  - 自动选择的配置模式: {auto_cfg['processing_mode']}")
    
    # 4. 测试配置覆盖
    print("\n4. 配置覆盖测试:")
    custom_config = create_smart_config(
        "standard",
        max_length=100,
        use_spacy=False,
        custom_param="test_value"
    )
    print(f"  - 自定义最大长度: {custom_config['max_length']}")
    print(f"  - 自定义参数: {custom_config.get('custom_param', 'not found')}")
    
    print("\n=== 测试完成 ===")
