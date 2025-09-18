"""
Netflix V2配置管理系统
集成Phase 1和Phase 2成果，提供Netflix标准的配置模板、用户自定义配置、配置验证等功能
优化现有配置管理系统，支持Netflix级字幕配置
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum
import copy

# 导入Netflix V2核心组件
try:
    from flask_backend.core.netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2
    from flask_backend.core.netflix_char_weight_calculator_v2 import NetflixCharacterConfig
    from flask_backend.core.netflix_quality_validator_v2 import ValidationLevel
    NETFLIX_V2_AVAILABLE = True
except ImportError:
    NETFLIX_V2_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    """配置作用域"""
    GLOBAL = "global"       # 全局配置
    PROJECT = "project"     # 项目级配置
    USER = "user"          # 用户配置
    TEMPLATE = "template"   # 配置模板


class ConfigCategory(Enum):
    """配置分类"""
    NETFLIX_SUBTITLE = "netflix_subtitle"     # Netflix字幕配置
    STYLE_PRESETS = "style_presets"          # 样式预设
    CHARACTER_WEIGHTS = "character_weights"   # 字符权重配置
    QUALITY_VALIDATION = "quality_validation" # 质量验证配置
    SEMANTIC_SPLITTING = "semantic_splitting" # 语义分割配置
    GENERAL = "general"                      # 通用配置


@dataclass
class ConfigMetadata:
    """配置元数据"""
    name: str
    description: str
    version: str
    category: ConfigCategory
    scope: ConfigScope
    created_time: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_time: str = field(default_factory=lambda: datetime.now().isoformat())
    author: str = "Netflix V2 Config System"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class NetflixSubtitleConfig:
    """Netflix字幕完整配置"""
    # 基本设置
    enabled: bool = True
    style_preset: str = "videolingo_netflix"
    max_chars_per_line: int = 36
    validation_level: str = "netflix"
    
    # 字符权重设置
    chinese_weight: float = 1.75
    english_weight: float = 1.0
    punctuation_weight: float = 0.5
    
    # 分割设置
    enable_semantic_splitting: bool = True
    max_optimization_rounds: int = 5
    quality_threshold: float = 0.7
    
    # 输出格式
    output_formats: List[str] = field(default_factory=lambda: ["srt", "ass", "webvtt"])
    
    # 样式配置
    font_color: str = "&H00FFFF"  # Netflix黄色
    font_size: int = 17
    outline_color: str = "&H000000"  # 黑色描边
    outline_width: int = 1
    background_alpha: float = 0.8
    
    # 时间轴设置
    min_duration: float = 1.0
    max_duration: float = 8.0
    gap_threshold: float = 0.3
    
    # 质量控制
    enable_quality_validation: bool = True
    auto_fix_issues: bool = True
    strict_netflix_compliance: bool = True


class NetflixV2ConfigManager:
    """
    Netflix V2配置管理器
    提供Netflix级字幕配置的全生命周期管理
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        # 配置目录设置
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / "config_data"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.netflix_config_file = self.config_dir / "netflix_v2_config.json"
        self.templates_dir = self.config_dir / "netflix_templates"
        self.user_configs_dir = self.config_dir / "user_configs" 
        
        # 创建必要目录
        self.templates_dir.mkdir(exist_ok=True)
        self.user_configs_dir.mkdir(exist_ok=True)
        
        # 初始化Netflix样式管理器
        self.style_manager = None
        if NETFLIX_V2_AVAILABLE:
            self.style_manager = NetflixStylePresetsV2()
        
        # 初始化配置
        self._init_default_configs()
        
        logger.info(f"Netflix V2配置管理器初始化完成 - 配置目录: {self.config_dir}")
    
    def _init_default_configs(self):
        """初始化默认配置"""
        try:
            # 创建默认Netflix配置
            if not self.netflix_config_file.exists():
                self._create_default_netflix_config()
            
            # 创建预设模板
            self._create_builtin_templates()
            
            logger.info("默认配置初始化完成")
            
        except Exception as e:
            logger.error(f"默认配置初始化失败: {e}")
            raise
    
    def _create_default_netflix_config(self):
        """创建默认Netflix配置文件"""
        default_config = NetflixSubtitleConfig()
        
        config_data = {
            "metadata": {
                "name": "Default Netflix V2 Config",
                "description": "Netflix V2字幕系统默认配置",
                "version": "2.0",
                "category": ConfigCategory.NETFLIX_SUBTITLE.value,  # 转换为字符串值
                "scope": ConfigScope.GLOBAL.value,  # 转换为字符串值
                "created_time": datetime.now().isoformat(),
                "modified_time": datetime.now().isoformat(),
                "author": "Netflix V2 Config System",
                "tags": ["netflix", "v2", "default"],
                "dependencies": []
            },
            "config": asdict(default_config)
        }
        
        with open(self.netflix_config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"默认Netflix配置文件已创建: {self.netflix_config_file}")
    
    def _create_builtin_templates(self):
        """创建内置配置模板"""
        templates = {
            "netflix_standard": {
                "metadata": {
                    "name": "Netflix Standard",
                    "description": "Netflix标准配置模板",
                    "version": "2.0",
                    "category": ConfigCategory.NETFLIX_SUBTITLE.value,
                    "scope": ConfigScope.TEMPLATE.value,
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat(),
                    "author": "Netflix V2 Config System",
                    "tags": ["netflix", "standard", "professional"],
                    "dependencies": []
                },
                "config": NetflixSubtitleConfig(
                    style_preset="netflix_standard",
                    font_color="&H00FFFF",
                    strict_netflix_compliance=True
                )
            },
            
            "netflix_hd": {
                "metadata": {
                    "name": "Netflix HD",
                    "description": "Netflix高清配置模板",
                    "version": "2.0",
                    "category": ConfigCategory.NETFLIX_SUBTITLE.value,
                    "scope": ConfigScope.TEMPLATE.value,
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat(),
                    "author": "Netflix V2 Config System",
                    "tags": ["netflix", "hd", "high-quality"],
                    "dependencies": []
                },
                "config": NetflixSubtitleConfig(
                    style_preset="netflix_hd",
                    font_size=19,
                    outline_width=2,
                    enable_quality_validation=True
                )
            },
            
            "videolingo_netflix": {
                "metadata": {
                    "name": "VideoLingo Netflix",
                    "description": "VideoLingo集成Netflix配置模板",
                    "version": "2.0",
                    "category": ConfigCategory.NETFLIX_SUBTITLE.value,
                    "scope": ConfigScope.TEMPLATE.value,
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat(),
                    "author": "Netflix V2 Config System",
                    "tags": ["videolingo", "netflix", "integrated"],
                    "dependencies": []
                },
                "config": NetflixSubtitleConfig(
                    style_preset="videolingo_netflix",
                    chinese_weight=1.75,
                    max_chars_per_line=36,
                    enable_semantic_splitting=True,
                    max_optimization_rounds=5
                )
            },
            
            "accessibility": {
                "metadata": {
                    "name": "Netflix Accessibility",
                    "description": "Netflix无障碍配置模板",
                    "version": "2.0",
                    "category": ConfigCategory.NETFLIX_SUBTITLE.value,
                    "scope": ConfigScope.TEMPLATE.value,
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat(),
                    "author": "Netflix V2 Config System",
                    "tags": ["netflix", "accessibility", "inclusive"],
                    "dependencies": []
                },
                "config": NetflixSubtitleConfig(
                    style_preset="netflix_high_contrast",
                    font_size=20,
                    outline_width=3,
                    background_alpha=0.9,
                    enable_quality_validation=True
                )
            }
        }
        
        for template_name, template_data in templates.items():
            template_file = self.templates_dir / f"{template_name}.json"
            
            if not template_file.exists():
                # 转换为可序列化的数据
                serializable_data = {
                    "metadata": template_data["metadata"],
                    "config": asdict(template_data["config"])
                }
                
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"创建配置模板: {template_name}")
    
    def load_netflix_config(self, config_name: Optional[str] = None) -> NetflixSubtitleConfig:
        """
        加载Netflix配置
        
        Args:
            config_name: 配置名称，None表示加载默认配置
            
        Returns:
            Netflix字幕配置对象
        """
        try:
            if config_name is None:
                # 加载默认配置
                config_file = self.netflix_config_file
            else:
                # 查找用户配置或模板
                user_config_file = self.user_configs_dir / f"{config_name}.json"
                template_file = self.templates_dir / f"{config_name}.json"
                
                if user_config_file.exists():
                    config_file = user_config_file
                elif template_file.exists():
                    config_file = template_file
                else:
                    raise FileNotFoundError(f"配置不存在: {config_name}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 创建配置对象
            config_dict = data.get("config", {})
            config = NetflixSubtitleConfig(**config_dict)
            
            logger.info(f"Netflix配置加载成功: {config_name or 'default'}")
            return config
            
        except Exception as e:
            logger.error(f"Netflix配置加载失败: {e}")
            # 返回默认配置
            return NetflixSubtitleConfig()
    
    def save_netflix_config(
        self, 
        config: NetflixSubtitleConfig, 
        config_name: str,
        scope: ConfigScope = ConfigScope.USER,
        metadata: Optional[ConfigMetadata] = None
    ) -> bool:
        """
        保存Netflix配置
        
        Args:
            config: Netflix配置对象
            config_name: 配置名称
            scope: 配置作用域
            metadata: 配置元数据
            
        Returns:
            保存是否成功
        """
        try:
            # 确定保存路径
            if scope == ConfigScope.USER:
                config_file = self.user_configs_dir / f"{config_name}.json"
            elif scope == ConfigScope.TEMPLATE:
                config_file = self.templates_dir / f"{config_name}.json"
            else:
                config_file = self.netflix_config_file
            
            # 创建元数据
            if metadata is None:
                metadata_dict = {
                    "name": config_name,
                    "description": f"用户自定义Netflix配置: {config_name}",
                    "version": "2.0",
                    "category": ConfigCategory.NETFLIX_SUBTITLE.value,
                    "scope": scope.value,
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat(),
                    "author": "Netflix V2 Config System",
                    "tags": [],
                    "dependencies": []
                }
            else:
                metadata_dict = {
                    "name": metadata.name,
                    "description": metadata.description,
                    "version": metadata.version,
                    "category": metadata.category.value,
                    "scope": metadata.scope.value,
                    "created_time": metadata.created_time,
                    "modified_time": datetime.now().isoformat(),
                    "author": metadata.author,
                    "tags": metadata.tags,
                    "dependencies": metadata.dependencies
                }
            
            # 准备保存数据
            save_data = {
                "metadata": metadata_dict,
                "config": asdict(config)
            }
            
            # 保存文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Netflix配置保存成功: {config_name} -> {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Netflix配置保存失败: {e}")
            return False
    
    def validate_config(self, config: NetflixSubtitleConfig) -> Dict[str, Any]:
        """
        验证Netflix配置
        
        Args:
            config: Netflix配置对象
            
        Returns:
            验证结果字典
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            
            # 基本验证
            if config.max_chars_per_line <= 0:
                validation_result["errors"].append("每行最大字符数必须大于0")
                validation_result["valid"] = False
            
            if config.max_chars_per_line > 50:
                validation_result["warnings"].append("每行字符数过多，建议不超过36字符以符合Netflix标准")
            
            # Netflix标准验证
            if config.strict_netflix_compliance:
                if config.max_chars_per_line != 36:
                    validation_result["errors"].append("Netflix严格模式要求每行36个有效中文字符")
                    validation_result["valid"] = False
                
                if config.chinese_weight != 1.75:
                    validation_result["warnings"].append("建议使用1.75中文字符权重以符合VideoLingo标准")
            
            # 字符权重验证
            if config.chinese_weight <= 0 or config.english_weight <= 0:
                validation_result["errors"].append("字符权重必须大于0")
                validation_result["valid"] = False
            
            # 样式验证
            if self.style_manager:
                available_presets = self.style_manager.get_all_presets()
                if config.style_preset not in available_presets:
                    validation_result["warnings"].append(f"样式预设'{config.style_preset}'不存在，将使用默认样式")
            
            # 时间轴验证
            if config.min_duration >= config.max_duration:
                validation_result["errors"].append("最小显示时间必须小于最大显示时间")
                validation_result["valid"] = False
            
            # 质量阈值验证
            if not (0.0 <= config.quality_threshold <= 1.0):
                validation_result["errors"].append("质量阈值必须在0.0-1.0之间")
                validation_result["valid"] = False
            
            # 提供建议
            if config.enable_semantic_splitting and config.max_optimization_rounds < 3:
                validation_result["suggestions"].append("建议将优化轮数设置为3-5以获得更好的分割效果")
            
            logger.info(f"配置验证完成 - 有效: {validation_result['valid']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return {
                "valid": False,
                "errors": [f"验证过程出错: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }
    
    def list_available_configs(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        列出所有可用配置
        
        Returns:
            按作用域分组的配置列表
        """
        try:
            configs = {
                "templates": [],
                "user_configs": [],
                "global_config": []
            }
            
            # 扫描模板
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get("metadata", {})
                    configs["templates"].append({
                        "name": template_file.stem,
                        "display_name": metadata.get("name", template_file.stem),
                        "description": metadata.get("description", ""),
                        "version": metadata.get("version", ""),
                        "tags": metadata.get("tags", []),
                        "file_path": str(template_file)
                    })
                except Exception as e:
                    logger.warning(f"读取模板配置失败: {template_file} - {e}")
            
            # 扫描用户配置
            for user_file in self.user_configs_dir.glob("*.json"):
                try:
                    with open(user_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get("metadata", {})
                    configs["user_configs"].append({
                        "name": user_file.stem,
                        "display_name": metadata.get("name", user_file.stem),
                        "description": metadata.get("description", ""),
                        "version": metadata.get("version", ""),
                        "modified_time": metadata.get("modified_time", ""),
                        "file_path": str(user_file)
                    })
                except Exception as e:
                    logger.warning(f"读取用户配置失败: {user_file} - {e}")
            
            # 全局配置
            if self.netflix_config_file.exists():
                try:
                    with open(self.netflix_config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get("metadata", {})
                    configs["global_config"].append({
                        "name": "default",
                        "display_name": metadata.get("name", "默认配置"),
                        "description": metadata.get("description", "系统默认Netflix配置"),
                        "version": metadata.get("version", ""),
                        "file_path": str(self.netflix_config_file)
                    })
                except Exception as e:
                    logger.warning(f"读取全局配置失败: {e}")
            
            return configs
            
        except Exception as e:
            logger.error(f"列出配置失败: {e}")
            return {"templates": [], "user_configs": [], "global_config": []}
    
    def create_config_from_template(self, template_name: str, new_config_name: str, customizations: Optional[Dict[str, Any]] = None) -> bool:
        """
        从模板创建新配置
        
        Args:
            template_name: 模板名称
            new_config_name: 新配置名称
            customizations: 自定义设置
            
        Returns:
            创建是否成功
        """
        try:
            # 加载模板
            template_config = self.load_netflix_config(template_name)
            
            # 应用自定义设置
            if customizations:
                for key, value in customizations.items():
                    if hasattr(template_config, key):
                        setattr(template_config, key, value)
            
            # 创建新的元数据
            new_metadata_dict = {
                "name": new_config_name,
                "description": f"基于{template_name}模板的自定义配置",
                "version": "2.0",
                "category": ConfigCategory.NETFLIX_SUBTITLE.value,
                "scope": ConfigScope.USER.value,
                "created_time": datetime.now().isoformat(),
                "modified_time": datetime.now().isoformat(),
                "author": "Netflix V2 Config System",
                "tags": ["custom", "user", template_name],
                "dependencies": []
            }
            
            # 保存新配置
            config_file = self.user_configs_dir / f"{new_config_name}.json"
            save_data = {
                "metadata": new_metadata_dict,
                "config": asdict(template_config)
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"从模板'{template_name}'创建配置'{new_config_name}'成功")
            return True
            
        except Exception as e:
            logger.error(f"从模板创建配置失败: {e}")
            return False
    
    def export_config(self, config_name: str, export_path: Path) -> bool:
        """
        导出配置到指定路径
        
        Args:
            config_name: 配置名称
            export_path: 导出路径
            
        Returns:
            导出是否成功
        """
        try:
            config = self.load_netflix_config(config_name)
            
            # 创建导出数据
            export_data = {
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "config_manager_version": "2.0",
                    "original_config_name": config_name
                },
                "metadata": asdict(ConfigMetadata(
                    name=f"Exported {config_name}",
                    description=f"导出的Netflix配置: {config_name}",
                    version="2.0",
                    category=ConfigCategory.NETFLIX_SUBTITLE,
                    scope=ConfigScope.USER
                )),
                "config": asdict(config)
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置导出成功: {config_name} -> {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"配置导出失败: {e}")
            return False
    
    def import_config(self, import_path: Path, config_name: Optional[str] = None) -> bool:
        """
        导入配置文件
        
        Args:
            import_path: 导入文件路径
            config_name: 新配置名称，None表示使用原名
            
        Returns:
            导入是否成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取配置
            config_dict = data.get("config", {})
            config = NetflixSubtitleConfig(**config_dict)
            
            # 确定配置名称
            if config_name is None:
                original_name = data.get("export_info", {}).get("original_config_name")
                metadata = data.get("metadata", {})
                config_name = original_name or metadata.get("name", "imported_config")
            
            # 确保config_name不为None
            if not config_name:
                config_name = "imported_config"
            
            # 创建新元数据
            new_metadata = ConfigMetadata(
                name=config_name,
                description=f"导入的Netflix配置",
                version="2.0",
                category=ConfigCategory.NETFLIX_SUBTITLE,
                scope=ConfigScope.USER,
                tags=["imported"]
            )
            
            # 保存配置
            success = self.save_netflix_config(config, config_name, ConfigScope.USER, new_metadata)
            
            if success:
                logger.info(f"配置导入成功: {import_path} -> {config_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置管理器信息
        
        Returns:
            配置管理器信息字典
        """
        available_configs = self.list_available_configs()
        
        return {
            "config_manager_version": "2.0",
            "netflix_v2_available": NETFLIX_V2_AVAILABLE,
            "config_directory": str(self.config_dir),
            "templates_directory": str(self.templates_dir),
            "user_configs_directory": str(self.user_configs_dir),
            "available_configs": available_configs,
            "total_templates": len(available_configs["templates"]),
            "total_user_configs": len(available_configs["user_configs"]),
            "supported_features": [
                "Netflix V2标准配置",
                "配置模板系统", 
                "用户自定义配置",
                "配置验证",
                "配置导入导出",
                "配置继承与覆盖"
            ]
        }


# 工厂函数
def create_netflix_config_manager(config_dir: Optional[Path] = None) -> NetflixV2ConfigManager:
    """
    创建Netflix V2配置管理器实例
    
    Args:
        config_dir: 配置目录路径
        
    Returns:
        Netflix V2配置管理器实例
    """
    return NetflixV2ConfigManager(config_dir)


if __name__ == "__main__":
    # 测试配置管理器
    print("🧪 Netflix V2配置管理系统测试")
    print("=" * 50)
    
    # 创建配置管理器
    config_manager = create_netflix_config_manager()
    
    # 显示系统信息
    info = config_manager.get_config_info()
    print(f"配置管理器版本: {info['config_manager_version']}")
    print(f"Netflix V2可用: {info['netflix_v2_available']}")
    print(f"模板数量: {info['total_templates']}")
    print(f"用户配置数量: {info['total_user_configs']}")
    
    # 测试加载默认配置
    default_config = config_manager.load_netflix_config()
    print(f"\n默认配置加载成功:")
    print(f"  样式预设: {default_config.style_preset}")
    print(f"  每行字符数: {default_config.max_chars_per_line}")
    print(f"  中文权重: {default_config.chinese_weight}")
    
    # 测试配置验证
    validation = config_manager.validate_config(default_config)
    print(f"\n配置验证结果: {'通过' if validation['valid'] else '失败'}")
    if validation['warnings']:
        print(f"  警告: {validation['warnings']}")
    if validation['suggestions']:
        print(f"  建议: {validation['suggestions']}")
    
    print("\n✅ Netflix V2配置管理系统测试完成！")