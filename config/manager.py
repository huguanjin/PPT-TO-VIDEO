"""
统一配置管理器
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json
import logging
from dataclasses import dataclass

@dataclass
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config_data"
        
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._config_files = {
            "tts": "tts_config.json",
            "fish_tts": "fish_tts_config.json",
            "workflow": "workflow_config.json", 
            "video": "video_config.json",
            "subtitle": "subtitle_config.json",
            "app": "app_config.json"
        }
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """加载所有配置文件"""
        for key, filename in self._config_files.items():
            config_path = self.config_dir / filename
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._configs[key] = json.load(f)
                    self.logger.info(f"已加载配置: {filename}")
                except Exception as e:
                    self.logger.error(f"加载配置失败 {filename}: {e}")
                    self._configs[key] = {}
            else:
                self.logger.warning(f"配置文件不存在: {filename}")
                self._configs[key] = {}
    
    def get_config(self, config_type: str, key: Optional[str] = None) -> Any:
        """
        获取配置值
        
        Args:
            config_type: 配置类型 (tts, fish_tts, workflow等)
            key: 配置键，如果为None则返回整个配置
            
        Returns:
            配置值
        """
        config = self._configs.get(config_type, {})
        if key:
            return config.get(key)
        return config
    
    def update_config(self, config_type: str, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config_type: 配置类型
            updates: 要更新的配置项
            
        Returns:
            是否更新成功
        """
        try:
            if config_type not in self._configs:
                self._configs[config_type] = {}
            
            # 更新内存中的配置
            self._configs[config_type].update(updates)
            
            # 保存到文件
            if config_type in self._config_files:
                config_path = self.config_dir / self._config_files[config_type]
                
                # 确保目录存在
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._configs[config_type], f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"配置已保存: {self._config_files[config_type]}")
                return True
            else:
                self.logger.error(f"未知的配置类型: {config_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False
    
    def reload_config(self, config_type: str) -> bool:
        """
        重新加载指定配置
        
        Args:
            config_type: 配置类型
            
        Returns:
            是否加载成功
        """
        if config_type not in self._config_files:
            self.logger.error(f"未知的配置类型: {config_type}")
            return False
        
        filename = self._config_files[config_type]
        config_path = self.config_dir / filename
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._configs[config_type] = json.load(f)
                self.logger.info(f"重新加载配置: {filename}")
                return True
            except Exception as e:
                self.logger.error(f"重新加载配置失败 {filename}: {e}")
                return False
        else:
            self.logger.warning(f"配置文件不存在: {filename}")
            return False
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置"""
        return self._configs.copy()
    
    def validate_config(self, config_type: str) -> bool:
        """
        验证配置有效性
        
        Args:
            config_type: 配置类型
            
        Returns:
            配置是否有效
        """
        config = self._configs.get(config_type, {})
        
        # 基本验证逻辑
        if config_type == "fish_tts":
            required_keys = ["api_key", "character", "character_id_dict"]
            return all(key in config for key in required_keys)
        elif config_type == "tts":
            return isinstance(config, dict)
        elif config_type == "workflow":
            return isinstance(config, dict)
        
        return True
