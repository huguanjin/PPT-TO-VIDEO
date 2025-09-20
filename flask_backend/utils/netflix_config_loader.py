"""
Netflix配置加载器和管理系统
负责加载和管理Netflix级别字幕分割的所有配置参数
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

class NetflixConfigLoader:
    """Netflix配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger(__name__)
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 默认配置文件路径
            self.config_path = Path(__file__).parent.parent / "config_data" / "netflix_subtitle_config.json"
        
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"成功加载配置文件: {self.config_path}")
                return config
            else:
                self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def get_max_chars_per_line(self) -> int:
        """获取每行最大字符数"""
        return self.netflix_standards.get('max_chars_per_line', 20)
    
    def get_min_chars_per_line(self) -> int:
        """获取每行最小字符数"""
        return self.netflix_standards.get('min_chars_per_line', 3)
    
    def get_similarity_threshold(self) -> float:
        """获取相似度阈值"""
        return self.validation_settings.get('similarity_threshold', 0.9)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "netflix_standards": {
                "max_chars_per_line": 20,
                "min_chars_per_line": 3,
                "similarity_threshold": 0.9,
                "max_retry_attempts": 3,
                "enable_nlp_preprocessing": True,
                "enable_sequence_validation": True,
                "single_line_preference": True,
                "length_balance_ratio": 2.5
            },
            "nlp_settings": {
                "spacy_model": "zh_core_web_sm",
                "fallback_models": ["zh_core_web_md", "zh_core_web_lg"],
                "complexity_threshold": 5.0,
                "split_marks": ["。", "！", "？", "；", "：", "…"],
                "comma_patterns": [",", "，", "、"],
                "conjunction_patterns": ["但是", "然而", "不过", "而且", "并且", "同时"]
            },
            "ai_settings": {
                "preferred_model": "gemini-2.0-flash-custom",
                "fallback_model": "gemini-1.5-pro",
                "prompt_style": "netflix_professional",
                "response_format": "structured_json",
                "max_tokens": 800,
                "temperature": 0.3
            },
            "semantic_protection": {
                "enable_url_protection": True,
                "enable_email_protection": True,
                "enable_technical_term_protection": True,
                "custom_patterns": []
            },
            "quality_metrics": {
                "enable_similarity_tracking": True,
                "enable_compliance_tracking": True,
                "similarity_warning_threshold": 0.85,
                "compliance_target": 0.9
            }
        }
    
    def _validate_config(self):
        """验证配置的有效性"""
        # 验证必需的配置节
        required_sections = [
            "netflix_standards", 
            "nlp_settings", 
            "ai_settings"
        ]
        
        for section in required_sections:
            if section not in self._config:
                self.logger.warning(f"缺少配置节: {section}，使用默认值")
                default_config = self._get_default_config()
                self._config[section] = default_config.get(section, {})
        
        # 验证数值范围
        netflix_standards = self._config.get("netflix_standards", {})
        
        # 字符限制验证
        max_chars = netflix_standards.get("max_chars_per_line", 20)
        min_chars = netflix_standards.get("min_chars_per_line", 3)
        if max_chars <= min_chars:
            self.logger.warning("max_chars_per_line应大于min_chars_per_line，已调整")
            netflix_standards["max_chars_per_line"] = max(max_chars, min_chars + 5)
        
        # 相似度阈值验证
        similarity_threshold = netflix_standards.get("similarity_threshold", 0.9)
        if not 0.0 <= similarity_threshold <= 1.0:
            self.logger.warning("similarity_threshold应在0.0-1.0之间，已调整")
            netflix_standards["similarity_threshold"] = max(0.0, min(1.0, similarity_threshold))
    
    @property
    def netflix_standards(self) -> Dict[str, Any]:
        """获取Netflix标准配置"""
        return self._config.get("netflix_standards", {})
    
    @property
    def nlp_settings(self) -> Dict[str, Any]:
        """获取NLP设置"""
        return self._config.get("nlp_settings", {})
    
    @property 
    def ai_settings(self) -> Dict[str, Any]:
        """获取AI设置"""
        return self._config.get("ai_settings", {})
    
    @property
    def prompt_templates(self) -> Dict[str, Any]:
        """获取提示词模板配置"""
        return self._config.get("prompt_templates", {})
    
    @property
    def validation_settings(self) -> Dict[str, Any]:
        """获取验证设置"""
        return self._config.get("validation", {})
    
    @property
    def semantic_protection(self) -> Dict[str, Any]:
        """获取语义保护设置"""
        return self._config.get("semantic_protection", {})
    
    @property
    def quality_metrics(self) -> Dict[str, Any]:
        """获取质量指标设置"""
        return self._config.get("quality_metrics", {})
    
    @property
    def performance_settings(self) -> Dict[str, Any]:
        """获取性能设置"""
        return self._config.get("performance_settings", {})
    
    @property
    def logging(self) -> Dict[str, Any]:
        """获取日志设置"""
        return self._config.get("logging", {})
    
    @property
    def validation(self) -> Dict[str, Any]:
        """获取验证设置"""
        return self._config.get("validation", {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, file_path: Optional[str] = None):
        """保存配置到文件"""
        save_path = Path(file_path) if file_path else self.config_path
        
        try:
            # 确保目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            raise
    
    def reload_config(self):
        """重新加载配置"""
        self._config = self._load_config()
        self._validate_config()
        self.logger.info("配置已重新加载")
    
    def get_spacy_model_config(self) -> Dict[str, Any]:
        """获取spaCy模型配置"""
        nlp_settings = self.nlp_settings
        return {
            'preferred_model': nlp_settings.get('spacy_model', 'zh_core_web_sm'),
            'fallback_models': nlp_settings.get('fallback_models', []),
            'complexity_threshold': nlp_settings.get('complexity_threshold', 5.0),
            'complexity_weights': nlp_settings.get('complexity_weights', {}),
            'split_weights': nlp_settings.get('split_weights', {})
        }
    
    def get_ai_model_config(self) -> Dict[str, Any]:
        """获取AI模型配置"""
        ai_settings = self.ai_settings
        return {
            'model_name': ai_settings.get('preferred_model', 'gemini-2.0-flash-custom'),
            'fallback_model': ai_settings.get('fallback_model', 'gemini-1.5-pro'),
            'max_tokens': ai_settings.get('max_tokens', 800),
            'temperature': ai_settings.get('temperature', 0.3),
            'timeout': self.performance_settings.get('timeout_seconds', 30)
        }
    
    def get_semantic_patterns(self) -> List[Dict[str, str]]:
        """获取语义保护模式"""
        protection = self.semantic_protection
        patterns = []
        
        # 内置模式
        if protection.get('enable_url_protection', True):
            patterns.append({
                'pattern': r'https?://[^\s\u4e00-\u9fff]+',
                'type': 'url',
                'description': 'URL地址'
            })
        
        if protection.get('enable_email_protection', True):
            patterns.append({
                'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                'type': 'email',
                'description': '邮箱地址'
            })
        
        if protection.get('enable_technical_term_protection', True):
            patterns.extend([
                {
                    'pattern': r'\b[A-Z]{2,}(?:[A-Z][a-z]+)*\b',
                    'type': 'acronym',
                    'description': '首字母缩写'
                },
                {
                    'pattern': r'[A-Za-z_][A-Za-z0-9_]*\([^)]*\)',
                    'type': 'function_call',
                    'description': '函数调用'
                }
            ])
        
        # 自定义模式
        custom_patterns = protection.get('custom_patterns', [])
        patterns.extend(custom_patterns)
        
        return patterns
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        feature_map = {
            'nlp_preprocessing': 'netflix_standards.enable_nlp_preprocessing',
            'sequence_validation': 'netflix_standards.enable_sequence_validation',
            'quality_monitoring': 'netflix_standards.enable_quality_monitoring',
            'similarity_tracking': 'quality_metrics.enable_similarity_tracking',
            'compliance_tracking': 'quality_metrics.enable_compliance_tracking',
            'performance_tracking': 'quality_metrics.enable_performance_tracking',
            'caching': 'performance_settings.enable_caching',
            'parallel_processing': 'performance_settings.enable_parallel_processing'
        }
        
        config_key = feature_map.get(feature)
        if config_key:
            return self.get(config_key, False)
        
        return False
    
    def get_performance_limits(self) -> Dict[str, Any]:
        """获取性能限制配置"""
        netflix_standards = self.netflix_standards
        performance = self.performance_settings
        
        return {
            'max_chars_per_line': netflix_standards.get('max_chars_per_line', 20),
            'min_chars_per_line': netflix_standards.get('min_chars_per_line', 3),
            'max_retry_attempts': netflix_standards.get('max_retry_attempts', 3),
            'timeout_seconds': performance.get('timeout_seconds', 30),
            'max_workers': performance.get('max_workers', 4),
            'cache_size': performance.get('cache_size', 1000)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"NetflixConfigLoader(config_path='{self.config_path}')"