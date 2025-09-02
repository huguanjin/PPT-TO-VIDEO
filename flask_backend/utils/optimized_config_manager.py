"""
优化后的配置管理器
支持层次化配置和引用机制
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class OptimizedConfigManager:
    """优化的配置管理器"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / 'config_data'
        self.config_dir = Path(config_dir)
        
        # 缓存配置文件
        self._cache = {}
        
    def load_config(self, config_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """加载配置文件"""
        if use_cache and config_name in self._cache:
            return self._cache[config_name]
            
        config_path = self.config_dir / f"{config_name}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            if use_cache:
                self._cache[config_name] = config
                
            return config
        except Exception as e:
            raise ValueError(f"加载配置文件失败 {config_path}: {e}")
    
    def get_app_config(self) -> Dict[str, Any]:
        """获取应用主配置"""
        return self.load_config('app_config_optimized')
    
    def get_tts_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """获取指定TTS引擎的完整配置"""
        tts_config = self.load_config('tts_config_optimized')
        
        if engine_name not in tts_config['engines']:
            raise ValueError(f"不支持的TTS引擎: {engine_name}")
            
        engine_config = tts_config['engines'][engine_name].copy()
        
        # 解析引用的配置文件
        if 'config_file' in engine_config:
            try:
                external_config = self.load_config(engine_config['config_file'].replace('.json', ''))
                engine_config['external_config'] = external_config
            except FileNotFoundError:
                pass
                
        # 解析API密钥引用
        credentials = tts_config['credentials']
        for key, value in list(engine_config.items()):  # 使用list()避免字典大小变化错误
            if key.endswith('_ref') and value in credentials:
                actual_key = key.replace('_ref', '')
                engine_config[actual_key] = credentials[value]
                
        # 添加通用配置
        engine_config.update(tts_config['common'])
        
        return engine_config
    
    def get_current_tts_config(self) -> Dict[str, Any]:
        """获取当前选择的TTS引擎配置"""
        app_config = self.get_app_config()
        preferred_engine = app_config['tts']['preferred_engine']
        
        engine_config = self.get_tts_engine_config(preferred_engine)
        
        # 合并应用级别的TTS配置
        result = engine_config.copy()
        result.update({
            'preferred_engine': preferred_engine,
            'preferred_voice': app_config['tts'].get('preferred_voice', 
                                                  engine_config.get('default_voice', ''))
        })
        
        return result
    
    def save_app_config(self, config: Dict[str, Any]) -> None:
        """保存应用配置"""
        config_path = self.config_dir / 'app_config_optimized.json'
        
        # 添加更新时间戳
        from datetime import datetime
        config['_updated_at'] = datetime.now().isoformat()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        # 清除缓存
        if 'app_config_optimized' in self._cache:
            del self._cache['app_config_optimized']
    
    def update_tts_preference(self, engine: str, voice: str = None) -> None:
        """更新TTS引擎偏好设置"""
        app_config = self.get_app_config()
        app_config['tts']['preferred_engine'] = engine
        
        if voice:
            app_config['tts']['preferred_voice'] = voice
            
        self.save_app_config(app_config)
    
    def get_available_engines(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的TTS引擎"""
        tts_config = self.load_config('tts_config_optimized')
        return {name: info for name, info in tts_config['engines'].items() 
                if info.get('enabled', False)}

# 全局配置管理器实例
config_manager = OptimizedConfigManager()

def load_optimized_tts_config() -> Dict[str, Any]:
    """向后兼容的TTS配置加载函数"""
    return config_manager.get_current_tts_config()

def load_optimized_app_config() -> Dict[str, Any]:
    """优化的应用配置加载函数"""
    return config_manager.get_app_config()
