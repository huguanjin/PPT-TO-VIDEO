"""
配置工具模块
支持TTS配置的加载和管理

注意: 此模块现已迁移到使用 system_config_bridge
优先从 MongoDB 读取配置，文件读取作为回退方案
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 尝试导入配置桥接模块
try:
    from .system_config_bridge import get_tts_config as bridge_get_tts_config
    USE_CONFIG_BRIDGE = True
    logger.debug("配置桥接模块已加载")
except ImportError:
    USE_CONFIG_BRIDGE = False
    logger.debug("配置桥接模块不可用，使用文件读取")


def load_key(key: str) -> Dict[str, Any]:
    """
    从配置中加载指定的键值
    
    优先级:
    1. MongoDB system_config 表（通过配置桥接）
    2. 本地 config_data/*.json 文件
    3. 默认配置
    
    Args:
        key: 配置键名 (edge_tts, fish_tts, openai_tts, azure_tts)
        
    Returns:
        配置字典
    """
    # 1. 尝试使用配置桥接（优先从 MongoDB 读取）
    if USE_CONFIG_BRIDGE:
        try:
            config = bridge_get_tts_config(key)
            if config:
                logger.debug(f"从配置桥接加载 {key} 配置")
                return config
        except Exception as e:
            logger.debug(f"配置桥接读取失败: {e}")
    
    # 2. 默认配置（用于回退）
    default_config = {
        "edge_tts": {
            "voice": "zh-CN-XiaoxiaoNeural",
            "rate": "medium",
            "pitch": "medium"
        },
        "fish_tts": {
            "api_key": "f9515b8c22e74f49a8ac8b7a487b42e9",
            "character": "雷军",
            "character_id_dict": {
                "AD学姐": "7f92f8afb8ec43bf81429cc1c9199cb1",
                "丁真": "54a5170264694bfc8e9ad98df7bd89c3",
                "赛马娘": "0eb38bc974e1459facca38b359e13511",
                "蔡徐坤": "e4642e5edccd4d9ab61a69e82d4f8a14",
                "雷军": "738d0cc1a3e9430a9de2b544a466a7fc"
            }
        },
        "openai_tts": {
            "api_key": "",
            "voice": "alloy"
        },
        "azure_tts": {
            "api_key": "",
            "region": "",
            "voice": "zh-CN-XiaoxiaoNeural"
        }
    }
    
    # 优先从app_config.json加载配置
    # 尝试多个可能的路径
    possible_paths = [
        Path(__file__).parent.parent / "config_data" / "app_config.json",  # 首选路径
        Path("flask_backend/config_data/app_config.json"),  # 从项目根目录运行时
        Path("config_data/app_config.json")  # 从flask_backend目录运行时（兼容性）
    ]
    
    for app_config_file in possible_paths:
        if app_config_file.exists():
            try:
                with open(app_config_file, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
                    tts_config = app_config.get("tts", {})
                    
                    # 根据key映射到具体的配置
                    if key == "edge_tts":
                        return {
                            "voice": tts_config.get("edge_voice", "zh-CN-XiaoxiaoNeural"),
                            "rate": tts_config.get("edge_rate", "medium"),
                            "pitch": tts_config.get("edge_pitch", "medium")
                        }
                    elif key == "openai_tts":
                        return {
                            "api_key": tts_config.get("openai_api_key", ""),
                            "voice": tts_config.get("openai_voice", "alloy"),
                            "model": tts_config.get("openai_model", "tts-1")
                        }
                    elif key == "azure_tts":
                        return {
                            "api_key": tts_config.get("azure_api_key", ""),
                            "region": tts_config.get("azure_region", ""),
                            "voice": tts_config.get("azure_voice", "zh-CN-XiaoxiaoNeural")
                        }
            except Exception as e:
                print(f"加载app_config.json配置文件失败 ({app_config_file}): {e}")
                continue  # 尝试下一个路径
    
    # 尝试从tts_config.json加载其他配置（向后兼容）
    config_file = Path(__file__).parent.parent / "config_data" / "tts_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                if key in file_config:
                    return file_config[key]
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    # 返回默认配置
    return default_config.get(key, {})

def save_config(config: Dict[str, Any], key: Optional[str] = None):
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        key: 配置键名（如果指定，只保存该键的配置）
    """
    config_dir = Path("config_data")
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "tts_config.json"
    
    # 如果文件存在，先加载现有配置
    existing_config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
        except Exception:
            pass
    
    # 更新配置
    if key:
        existing_config[key] = config
    else:
        existing_config.update(config)
    
    # 保存配置
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)
        print(f"配置已保存到: {config_file}")
    except Exception as e:
        print(f"保存配置失败: {e}")

if __name__ == "__main__":
    # 测试配置加载
    edge_config = load_key("edge_tts")
    print(f"Edge TTS配置: {edge_config}")
