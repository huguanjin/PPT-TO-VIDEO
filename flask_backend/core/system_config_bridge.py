"""
系统配置桥接模块
为 core 模块提供统一的配置访问接口

优先级:
1. MongoDB system_config 表（推荐）
2. 本地 config_data/*.json 文件（兼容/回退）

这个模块确保:
- core 模块可以无缝迁移到 MongoDB 配置
- 当 MongoDB 不可用时自动回退到文件配置
- 保持与现有代码的兼容性
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# 配置文件名到 MongoDB config_key 的映射
CONFIG_KEY_MAPPING = {
    "app_config.json": None,  # app_config 内容分布在多个配置中
    "manual_split_config.json": "manual_split_config",
    "render_config.json": "render_config",
    "edge_tts_voices.json": None,  # 静态数据，保持文件读取
    "fish_tts_voices.json": None,  # 静态数据，保持文件读取
    "server_config.json": "system_settings",
    "subtitle_multiline_fix_config.json": None,  # 待迁移
    "video_frame_sync_config.json": None,  # 待迁移
    "audio_intelligent_sync_config.json": None,  # 待迁移
    "ai_content_understanding_config.json": "ai_services",
}


def _get_mongodb_service():
    """
    尝试获取 MongoDB 配置服务
    
    Returns:
        SystemConfigService 实例或 None
    """
    try:
        # 确保路径正确
        import sys
        from pathlib import Path
        flask_backend_path = str(Path(__file__).parent.parent)
        if flask_backend_path not in sys.path:
            sys.path.insert(0, flask_backend_path)
        
        from app.services.system_config_service import get_system_config_service
        return get_system_config_service()
    except Exception as e:
        logger.debug(f"MongoDB 配置服务不可用: {e}")
        return None


def _get_config_data_path(project_dir: Optional[Path] = None) -> Path:
    """
    获取 config_data 目录路径
    
    Args:
        project_dir: 项目目录，如果为 None 则自动检测
        
    Returns:
        config_data 目录的 Path
    """
    if project_dir:
        project_dir = Path(project_dir)
        # 处理 output 目录的情况
        if project_dir.name == "output":
            project_dir = project_dir.parent.parent
        config_path = project_dir / "flask_backend" / "config_data"
        if config_path.exists():
            return config_path
    
    # 尝试多个可能的路径
    possible_paths = [
        Path(__file__).parent.parent / "config_data",  # flask_backend/core -> flask_backend/config_data
        Path("flask_backend/config_data"),  # 从项目根目录运行
        Path("config_data"),  # 从 flask_backend 目录运行
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # 返回默认路径（可能不存在）
    return Path(__file__).parent.parent / "config_data"


def _load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    加载 JSON 文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        解析后的字典或 None
    """
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载配置文件失败 {file_path}: {e}")
    return None


# ============ 配置获取函数 ============

def get_manual_split_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    获取手动分割配置
    
    Args:
        project_dir: 项目目录
        
    Returns:
        手动分割配置字典
    """
    # 1. 尝试从 MongoDB 读取
    service = _get_mongodb_service()
    if service:
        try:
            config = service.get_manual_split_config()
            if config:
                logger.debug("从 MongoDB 加载 manual_split_config")
                return {"manual_split_config": config}
        except Exception as e:
            logger.debug(f"MongoDB 读取失败: {e}")
    
    # 2. 回退到文件读取
    config_path = _get_config_data_path(project_dir) / "manual_split_config.json"
    file_config = _load_json_file(config_path)
    if file_config:
        logger.debug(f"从文件加载 manual_split_config: {config_path}")
        return file_config
    
    # 3. 返回默认配置
    logger.debug("使用默认 manual_split_config")
    return {
        "manual_split_config": {
            "enabled": True,
            "split_strategy": {"method": "newline_split", "fallback_to_auto": True},
            "subtitle_display_mode": {
                "single_line_mode": True,
                "time_allocation": {
                    "method": "proportional",
                    "based_on": "character_count",
                    "min_line_duration": 1.0,
                    "max_line_duration": 8.0
                }
            }
        }
    }


def get_single_line_mode(project_dir: Optional[Path] = None) -> bool:
    """
    获取单行模式配置
    
    Args:
        project_dir: 项目目录
        
    Returns:
        是否启用单行模式
    """
    config = get_manual_split_config(project_dir)
    return config.get("manual_split_config", {}).get(
        "subtitle_display_mode", {}
    ).get("single_line_mode", True)


def get_time_allocation_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    获取时间分配配置
    
    Args:
        project_dir: 项目目录
        
    Returns:
        时间分配配置字典
    """
    config = get_manual_split_config(project_dir)
    return config.get("manual_split_config", {}).get(
        "subtitle_display_mode", {}
    ).get("time_allocation", {
        "method": "proportional",
        "based_on": "character_count",
        "min_line_duration": 1.0,
        "max_line_duration": 8.0
    })


def get_app_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    获取应用配置（合并多个来源）
    
    Args:
        project_dir: 项目目录
        
    Returns:
        应用配置字典
    """
    result = {}
    service = _get_mongodb_service()
    
    # 1. 尝试从 MongoDB 读取各部分配置
    if service:
        try:
            # 获取默认用户配置作为基础
            default_config = service.get_default_user_config()
            if default_config:
                result = {
                    "features": default_config.get("advanced_features", {}),
                    "tts": default_config.get("tts", {}),
                    "ai_models": default_config.get("ai", {}),
                    "subtitle": default_config.get("subtitle", {}),
                    "smart_subtitle": default_config.get("smart_subtitle", {}),
                }
                logger.debug("从 MongoDB 组装 app_config")
                return result
        except Exception as e:
            logger.debug(f"MongoDB 读取失败: {e}")
    
    # 2. 回退到文件读取
    config_path = _get_config_data_path(project_dir) / "app_config.json"
    file_config = _load_json_file(config_path)
    if file_config:
        logger.debug(f"从文件加载 app_config: {config_path}")
        return file_config
    
    # 3. 返回默认配置
    logger.debug("使用默认 app_config")
    return {
        "features": {
            "enhanced_subtitle_generation": True,
            "video_frame_sync": True,
            "audio_intelligent_sync": True,
            "ai_semantic_enhancement": True,
            "phase3_integration": True
        },
        "tts": {
            "preferred_engine": "edge_tts",
            "edge_voice": "zh-CN-XiaoxiaoNeural",
            "edge_rate": "+0%",
            "edge_pitch": "+0Hz"
        },
        "ai_models": {
            "force_ai_mode": False
        }
    }


def get_render_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    获取渲染配置
    
    Args:
        project_dir: 项目目录
        
    Returns:
        渲染配置字典
    """
    # 1. 尝试从 MongoDB 读取
    service = _get_mongodb_service()
    if service:
        try:
            config = service.get_render_config()
            if config:
                logger.debug("从 MongoDB 加载 render_config")
                return config
        except Exception as e:
            logger.debug(f"MongoDB 读取失败: {e}")
    
    # 2. 回退到文件读取
    config_path = _get_config_data_path(project_dir) / "render_config.json"
    file_config = _load_json_file(config_path)
    if file_config:
        logger.debug(f"从文件加载 render_config: {config_path}")
        return file_config
    
    # 3. 返回默认配置
    logger.debug("使用默认 render_config")
    return {
        "render_engine": {
            "type": "headless_browser",
            "enabled": True,
            "quality": 95,
            "format": "jpeg",
            "width": 1600,
            "height": 900
        }
    }


def get_tts_config(key: str, project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    获取 TTS 配置
    
    Args:
        key: TTS 引擎名称 (edge_tts, fish_tts, openai_tts, azure_tts)
        project_dir: 项目目录
        
    Returns:
        TTS 配置字典
    """
    # 默认配置
    default_configs = {
        "edge_tts": {
            "voice": "zh-CN-XiaoxiaoNeural",
            "rate": "+0%",
            "pitch": "+0Hz"
        },
        "fish_tts": {
            "api_key": "",
            "character": "",
            "character_id": ""
        },
        "openai_tts": {
            "api_key": "",
            "voice": "alloy",
            "model": "tts-1"
        },
        "azure_tts": {
            "api_key": "",
            "region": "eastus",
            "voice": "zh-CN-XiaoxiaoNeural"
        }
    }
    
    # 1. 尝试从 MongoDB 读取
    service = _get_mongodb_service()
    if service:
        try:
            # 从默认用户配置中获取 TTS 设置
            default_user_config = service.get_default_user_config()
            if default_user_config:
                tts_config = default_user_config.get("tts", {})
                if key == "edge_tts":
                    return {
                        "voice": tts_config.get("edge_voice", "zh-CN-XiaoxiaoNeural"),
                        "rate": tts_config.get("edge_rate", "+0%"),
                        "pitch": tts_config.get("edge_pitch", "+0Hz")
                    }
                elif key == "fish_tts":
                    return {
                        "api_key": tts_config.get("fish_api_key", ""),
                        "character": tts_config.get("fish_character", ""),
                        "character_id": tts_config.get("fish_character_id", "")
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
                        "region": tts_config.get("azure_region", "eastus"),
                        "voice": tts_config.get("azure_voice", "zh-CN-XiaoxiaoNeural")
                    }
        except Exception as e:
            logger.debug(f"MongoDB 读取 TTS 配置失败: {e}")
    
    # 2. 回退到文件读取 (app_config.json)
    app_config = get_app_config(project_dir)
    tts_config = app_config.get("tts", {})
    
    if key == "edge_tts":
        return {
            "voice": tts_config.get("edge_voice", "zh-CN-XiaoxiaoNeural"),
            "rate": tts_config.get("edge_rate", "+0%"),
            "pitch": tts_config.get("edge_pitch", "+0Hz")
        }
    elif key == "fish_tts":
        return {
            "api_key": tts_config.get("fish_api_key", ""),
            "character": tts_config.get("fish_character", ""),
            "character_id": tts_config.get("fish_character_id", "")
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
            "region": tts_config.get("azure_region", "eastus"),
            "voice": tts_config.get("azure_voice", "zh-CN-XiaoxiaoNeural")
        }
    
    # 3. 返回默认配置
    return default_configs.get(key, {})


def get_feature_flags(project_dir: Optional[Path] = None) -> Dict[str, bool]:
    """
    获取功能开关配置
    
    Args:
        project_dir: 项目目录
        
    Returns:
        功能开关字典
    """
    app_config = get_app_config(project_dir)
    features = app_config.get("features", {})
    
    # 确保返回所有标准功能开关
    return {
        "enhanced_subtitle_generation": features.get("enhanced_subtitle_generation", True),
        "video_frame_sync": features.get("video_frame_sync", True),
        "audio_intelligent_sync": features.get("audio_intelligent_sync", True),
        "ai_semantic_enhancement": features.get("ai_semantic_enhancement", True),
        "phase3_integration": features.get("phase3_integration", True),
        "force_ai_mode": app_config.get("ai_models", {}).get("force_ai_mode", False)
    }


def get_subtitle_multiline_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    获取多行字幕修复配置
    
    Args:
        project_dir: 项目目录
        
    Returns:
        多行字幕配置字典
    """
    # 目前这个配置还没有迁移到 MongoDB，直接读取文件
    config_path = _get_config_data_path(project_dir) / "subtitle_multiline_fix_config.json"
    file_config = _load_json_file(config_path)
    if file_config:
        return file_config
    
    return {
        "intelligent_sentence_breaking": {
            "enabled": True,
            "disable_for_flask": True
        }
    }


def get_phase3_alignment_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    获取 Phase3 智能对齐配置
    
    Args:
        project_dir: 项目目录
        
    Returns:
        Phase3 配置字典
    """
    # 1. 尝试从 MongoDB 读取
    service = _get_mongodb_service()
    if service:
        try:
            config = service.get_config("phase3_intelligent_alignment")
            if config:
                logger.debug("从 MongoDB 加载 phase3_intelligent_alignment")
                return config
        except Exception as e:
            logger.debug(f"MongoDB 读取失败: {e}")
    
    # 2. 返回默认配置
    return {
        "enabled": True,
        "precision_level": "enhanced",
        "audio_analysis": {
            "sample_rate": 16000,
            "frame_length": 1024,
            "hop_length": 512
        }
    }


# ============ 兼容性函数 ============

def load_config_file(filename: str, project_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    通用配置文件加载函数（兼容旧代码）
    
    Args:
        filename: 配置文件名
        project_dir: 项目目录
        
    Returns:
        配置字典或 None
    """
    # 映射到专门的获取函数
    if filename == "manual_split_config.json":
        return get_manual_split_config(project_dir)
    elif filename == "app_config.json":
        return get_app_config(project_dir)
    elif filename == "render_config.json":
        return get_render_config(project_dir)
    
    # 其他文件直接读取
    config_path = _get_config_data_path(project_dir) / filename
    return _load_json_file(config_path)


# ============ 配置来源检测 ============

def get_config_source_info() -> Dict[str, str]:
    """
    获取各配置的来源信息（用于调试）
    
    Returns:
        配置名到来源的映射
    """
    service = _get_mongodb_service()
    mongodb_available = service is not None
    
    sources = {}
    if mongodb_available:
        try:
            # 检查 MongoDB 中有哪些配置
            all_configs = service.get_all_configs()
            for key in all_configs:
                sources[key] = "mongodb"
        except Exception:
            pass
    
    # 检查文件系统中的配置
    config_path = _get_config_data_path()
    if config_path.exists():
        for file in config_path.glob("*.json"):
            if file.stem not in sources:
                sources[file.stem] = "file"
    
    return sources


if __name__ == "__main__":
    # 测试配置加载
    print("=== 配置桥接模块测试 ===\n")
    
    # 检查 MongoDB 服务是否可用
    service = _get_mongodb_service()
    print(f"MongoDB 服务状态: {'可用' if service else '不可用'}")
    
    if service:
        try:
            all_configs = service.get_all_configs()
            print(f"MongoDB 中的配置数量: {len(all_configs)}")
            print("MongoDB 配置键:", list(all_configs.keys()))
        except Exception as e:
            print(f"获取 MongoDB 配置失败: {e}")
    
    print("\n1. 配置来源信息:")
    sources = get_config_source_info()
    for key, source in sources.items():
        print(f"   {key}: {source}")
    
    print("\n2. 单行模式配置:")
    single_line = get_single_line_mode()
    print(f"   single_line_mode = {single_line}")
    
    print("\n3. 功能开关:")
    features = get_feature_flags()
    for key, value in features.items():
        print(f"   {key}: {value}")
    
    print("\n4. TTS 配置 (edge_tts):")
    tts = get_tts_config("edge_tts")
    for key, value in tts.items():
        print(f"   {key}: {value}")
