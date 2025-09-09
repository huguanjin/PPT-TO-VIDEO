"""
配置管理器 - 处理配置的持久化存储和加载
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import streamlit as st

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Path = None):
        """初始化配置管理器"""
        if config_dir is None:
            # 相对于当前文件所在目录的config_data目录
            current_file_dir = Path(__file__).parent.parent  # flask_backend目录
            config_dir = current_file_dir / "config_data"
        
        self.config_dir = config_dir
        self.config_file = self.config_dir / "app_config.json"
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "project_name": "ppt_video_project",
            "output_format": "MP4 (推荐)",
            "tts_voice": "zh-CN-XiaoxiaoNeural",
            "speech_rate": "medium",
            "speech_pitch": "medium",
            "video_resolution": "1920x1080 (Full HD)",
            "video_fps": 24,
            "video_bitrate": 2000,
            "video_codec": "libx264",
            "include_subtitles": True,
            "subtitle_fontsize": 50,
            "subtitle_color": "white",
            "subtitle_position": "bottom",
            "last_updated": None,
            "auto_save": True,
            # AI配置部分
            "ai": {
                "openai": {
                    "api_key": "",
                    "base_url": "https://api.openai.com",
                    "model": "gpt-3.5-turbo",
                    "timeout": 300,
                    "max_retries": 3,
                    "support_json": True
                },
                "anthropic": {
                    "api_key": "",
                    "base_url": "https://api.anthropic.com",
                    "model": "claude-3-sonnet-20240229",
                    "timeout": 300,
                    "max_retries": 3
                },
                "custom": {
                    "api_key": "",
                    "base_url": "",
                    "model": "",
                    "timeout": 300,
                    "max_retries": 3,
                    "support_json": True
                },
                "default_service": "openai",
                # 可用服务和模型配置（用于前端展示和验证）
                "services_config": {
                    "openai": {
                        "name": "OpenAI",
                        "description": "OpenAI GPT模型服务",
                        "default_base_url": "https://api.openai.com",
                        "supports_json": True,
                        "models": [
                            {
                                "value": "gpt-3.5-turbo",
                                "label": "GPT-3.5 Turbo",
                                "description": "快速高效的对话模型",
                                "is_default": True
                            },
                            {
                                "value": "gpt-4o-mini",
                                "label": "GPT-4o Mini",
                                "description": "轻量版GPT-4模型"
                            },
                            {
                                "value": "gpt-4o",
                                "label": "GPT-4o",
                                "description": "最新的多模态模型"
                            },
                            {
                                "value": "gpt-4",
                                "label": "GPT-4",
                                "description": "高质量语言理解模型"
                            },
                            {
                                "value": "gpt-4-turbo",
                                "label": "GPT-4 Turbo",
                                "description": "更快的GPT-4版本"
                            }
                        ]
                    },
                    "anthropic": {
                        "name": "Anthropic",
                        "description": "Anthropic Claude模型服务",
                        "default_base_url": "https://api.anthropic.com",
                        "supports_json": False,
                        "models": [
                            {
                                "value": "claude-3-haiku-20240307",
                                "label": "Claude 3 Haiku",
                                "description": "快速响应的轻量模型"
                            },
                            {
                                "value": "claude-3-sonnet-20240229",
                                "label": "Claude 3 Sonnet",
                                "description": "平衡性能的推荐模型",
                                "is_default": True
                            },
                            {
                                "value": "claude-3-opus-20240229",
                                "label": "Claude 3 Opus",
                                "description": "最高质量的复杂任务模型"
                            }
                        ]
                    },
                    "custom": {
                        "name": "自定义API",
                        "description": "兼容OpenAI格式的自定义API服务",
                        "default_base_url": "",
                        "supports_json": True,
                        "models": [],
                        "note": "请确保API服务兼容OpenAI接口格式，模型名称需要手动输入"
                    }
                }
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置（处理新增的配置项）
                merged_config = self.default_config.copy()
                merged_config.update(config)
                
                return merged_config
            else:
                # 首次运行，创建默认配置文件
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            st.warning(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            # 添加保存时间戳
            config = config.copy()
            config['last_updated'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"❌ 保存配置失败: {e}")
            return False
    
    def get_config_display_info(self) -> Dict[str, str]:
        """获取配置显示信息"""
        config = self.load_config()
        
        if config.get('last_updated'):
            last_updated = datetime.fromisoformat(config['last_updated'])
            update_time = last_updated.strftime("%Y-%m-%d %H:%M:%S")
        else:
            update_time = "未保存"
        
        return {
            "配置文件路径": str(self.config_file),
            "最后更新时间": update_time,
            "项目名称": config.get('project_name', '未设置'),
            "TTS语音": config.get('tts_voice', '未设置'),
            "视频分辨率": config.get('video_resolution', '未设置')
        }
    
    def reset_config(self) -> bool:
        """重置为默认配置"""
        try:
            return self.save_config(self.default_config)
        except Exception as e:
            st.error(f"❌ 重置配置失败: {e}")
            return False
    
    # AI配置管理方法
    def load_key(self, key: str) -> Any:
        """
        加载指定键的值（支持点分隔的嵌套路径）
        
        Args:
            key: 配置键，如 'ai.openai.api_key'
            
        Returns:
            配置值
        """
        config = self.load_config()
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def update_key(self, key: str, new_value: Any) -> bool:
        """
        更新指定键的值
        
        Args:
            key: 配置键，支持点分隔的嵌套路径
            new_value: 新值
            
        Returns:
            是否更新成功
        """
        config = self.load_config()
        keys = key.split('.')
        current = config
        
        # 导航到目标位置
        for k in keys[:-1]:
            if isinstance(current, dict):
                if k not in current:
                    current[k] = {}
                current = current[k]
            else:
                return False
        
        # 更新最终的键值
        if isinstance(current, dict):
            current[keys[-1]] = new_value
            return self.save_config(config)
        else:
            return False
    
    def get_ai_config(self, service: str = None) -> Dict[str, Any]:
        """
        获取AI服务配置
        
        Args:
            service: AI服务名称，如 'openai'、'anthropic' 或 'custom'
            
        Returns:
            AI配置
        """
        if service is None:
            service = self.load_key('ai.default_service') or 'openai'
        
        ai_config = self.load_key(f'ai.{service}') or {}
        
        # 确保必要的字段存在
        defaults = {
            'api_key': '',
            'base_url': '',
            'model': '',
            'timeout': 300,
            'max_retries': 3,
            'support_json': True
        }
        
        for key, default_value in defaults.items():
            if key not in ai_config:
                ai_config[key] = default_value
        
        return ai_config
    
    def update_ai_config(self, service: str, config: Dict[str, Any]) -> bool:
        """
        更新AI服务配置
        
        Args:
            service: AI服务名称
            config: 配置字典
            
        Returns:
            是否更新成功
        """
        success = True
        for key, value in config.items():
            if not self.update_key(f'ai.{service}.{key}', value):
                success = False
        return success
    
    def validate_ai_config(self, service: str = None) -> Dict[str, Any]:
        """
        验证AI配置
        
        Args:
            service: AI服务名称
            
        Returns:
            验证结果
        """
        if service is None:
            service = self.load_key('ai.default_service') or 'openai'
        
        config = self.get_ai_config(service)
        issues = []
        
        # 检查必要字段
        if not config.get('api_key'):
            issues.append(f"{service} API key is missing")
        
        if not config.get('base_url'):
            issues.append(f"{service} base URL is missing")
        
        if not config.get('model'):
            issues.append(f"{service} model is missing")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'config': config
        }
    
    def get_ai_display_info(self, service: str = None) -> Dict[str, str]:
        """获取AI配置显示信息"""
        if service is None:
            service = self.load_key('ai.default_service') or 'openai'
        
        config = self.get_ai_config(service)
        
        # 隐藏API密钥的部分字符
        api_key = config.get('api_key', '')
        if api_key:
            if len(api_key) > 8:
                masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
            else:
                masked_key = '*' * len(api_key)
        else:
            masked_key = "未设置"
        
        return {
            "AI服务": service.upper(),
            "API密钥": masked_key,
            "Base URL": config.get('base_url', '未设置'),
            "模型": config.get('model', '未设置'),
            "超时时间": f"{config.get('timeout', 300)}秒",
            "JSON支持": "是" if config.get('support_json', False) else "否"
        }
    
    def get_available_services(self) -> Dict[str, Any]:
        """获取可用的AI服务配置"""
        return self.load_key('ai.services_config') or {}
    
    def get_service_models(self, service: str) -> List[Dict[str, Any]]:
        """获取指定服务的可用模型列表"""
        services_config = self.get_available_services()
        return services_config.get(service, {}).get('models', [])
    
    def get_default_model(self, service: str) -> str:
        """获取指定服务的默认模型"""
        models = self.get_service_models(service)
        for model in models:
            if model.get('is_default', False):
                return model['value']
        
        # 如果没有标记默认的，返回第一个
        if models:
            return models[0]['value']
            
        # 兜底默认值
        defaults = {
            'openai': 'gpt-3.5-turbo',
            'anthropic': 'claude-3-sonnet-20240229',
            'custom': ''
        }
        return defaults.get(service, '')
    
    def get_default_base_url(self, service: str) -> str:
        """获取指定服务的默认Base URL"""
        services_config = self.get_available_services()
        return services_config.get(service, {}).get('default_base_url', '')
    
    def add_custom_model(self, service: str, model_config: Dict[str, str]) -> bool:
        """添加自定义模型配置"""
        try:
            services_config = self.get_available_services()
            if service not in services_config:
                return False
            
            models = services_config[service].get('models', [])
            
            # 检查是否已存在
            for existing_model in models:
                if existing_model['value'] == model_config['value']:
                    # 更新现有模型
                    existing_model.update(model_config)
                    break
            else:
                # 添加新模型
                models.append(model_config)
            
            # 保存配置
            return self.update_key(f'ai.services_config.{service}.models', models)
        except Exception as e:
            st.error(f"添加自定义模型失败: {e}")
            return False
    
    def reset_to_defaults(self, service: str = None) -> bool:
        """重置AI配置为默认值"""
        try:
            if service:
                # 重置特定服务
                default_config = self.default_config['ai'][service]
                return self.update_ai_config(service, default_config)
            else:
                # 重置所有AI配置
                default_ai_config = self.default_config['ai']
                return self.update_key('ai', default_ai_config)
        except Exception as e:
            st.error(f"重置配置失败: {e}")
            return False
