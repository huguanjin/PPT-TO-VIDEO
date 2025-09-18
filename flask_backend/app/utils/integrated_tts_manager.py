"""
集成TTS管理器
统一管理多种TTS引擎：Edge TTS、Fish TTS、OpenAI TTS、Azure TTS
"""
import os
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class TTSEngine(Enum):
    """TTS引擎枚举"""
    EDGE_TTS = "edge_tts"
    FISH_TTS = "fish_tts"
    OPENAI_TTS = "openai_tts"
    AZURE_TTS = "azure_tts"

@dataclass
class TTSConfig:
    """TTS配置类"""
    # 通用配置
    preferred_engine: TTSEngine = TTSEngine.EDGE_TTS
    output_format: str = "wav"
    sample_rate: int = 22050  # 添加采样率配置
    
    # Edge TTS 配置
    edge_voice: str = "zh-CN-XiaoxiaoNeural"
    edge_rate: str = "+0%"
    edge_pitch: str = "+0Hz"
    
    # Fish TTS 配置
    fish_api_key: str = ""
    fish_character_name: str = "雷军"
    fish_character_id: str = ""
    
    # OpenAI TTS 配置
    openai_api_key: str = ""
    openai_voice: str = "alloy"
    openai_model: str = "tts-1"
    
    # Azure TTS 配置
    azure_api_key: str = ""
    azure_region: str = "eastus"
    azure_voice: str = "zh-CN-XiaoxiaoNeural"

class IntegratedTTSManager:
    """集成TTS管理器"""
    
    def __init__(self, config: TTSConfig):
        """
        初始化TTS管理器
        
        Args:
            config: TTS配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化各引擎
        self._init_engines()
    
    def _init_engines(self):
        """初始化各TTS引擎"""
        try:
            # 导入各TTS引擎
            from all_tts_functions import edge_tts, fish_tts, openai_tts, azure_tts
            self.engines = {
                TTSEngine.EDGE_TTS: edge_tts,
                TTSEngine.FISH_TTS: fish_tts, 
                TTSEngine.OPENAI_TTS: openai_tts,
                TTSEngine.AZURE_TTS: azure_tts
            }
            self.logger.info("TTS引擎初始化成功")
        except ImportError as e:
            self.logger.warning(f"部分TTS引擎导入失败: {e}")
            self.engines = {}
    
    async def synthesize_speech(self, text: str, 
                               preferred_engine: Optional[TTSEngine] = None,
                               output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        异步语音合成
        
        Args:
            text: 要合成的文本
            preferred_engine: 首选引擎
            output_path: 输出文件路径
            
        Returns:
            合成结果字典
        """
        engine = preferred_engine or self.config.preferred_engine
        
        try:
            if engine == TTSEngine.EDGE_TTS:
                return await self._synthesize_edge_tts(text, output_path)
            elif engine == TTSEngine.FISH_TTS:
                return await self._synthesize_fish_tts(text, output_path)
            elif engine == TTSEngine.OPENAI_TTS:
                return await self._synthesize_openai_tts(text, output_path)
            elif engine == TTSEngine.AZURE_TTS:
                return await self._synthesize_azure_tts(text, output_path)
            else:
                return {"success": False, "error": f"不支持的TTS引擎: {engine}"}
                
        except Exception as e:
            self.logger.error(f"TTS合成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_audio_metadata(self, audio_path: str, text: str) -> Dict[str, Any]:
        """
        获取音频文件的元数据（时长、文件大小等）
        支持WAV、MP3等多种音频格式
        
        Args:
            audio_path: 音频文件路径
            text: 原始文本（用于估算时长）
            
        Returns:
            包含音频元数据的字典
        """
        import os
        
        if not os.path.exists(audio_path):
            return {"duration": 0.0, "file_size": 0}
        
        # 获取文件大小
        file_size = os.path.getsize(audio_path)
        
        # 获取音频时长 - 使用多种方法尝试
        duration = self._get_audio_duration(audio_path, text)
        
        return {
            "duration": duration,
            "file_size": file_size
        }
    
    def _get_audio_duration(self, audio_path: str, text: str) -> float:
        """
        获取音频时长，使用多种方法回退
        
        Args:
            audio_path: 音频文件路径
            text: 原始文本（用于估算）
            
        Returns:
            音频时长（秒）
        """
        import os
        
        # 首先检查文件是否存在
        if not os.path.exists(audio_path):
            # 文件不存在，直接使用文本估算
            chars_per_second = 3.5 if self._is_chinese_text(text) else 12
            return max(1.0, len(text) / chars_per_second)
        
        duration = 0.0
        
        # 方法1: 使用wave模块（适用于WAV格式）
        try:
            import wave
            with wave.open(audio_path, 'rb') as audio_file:
                frame_rate = audio_file.getframerate()
                frame_count = audio_file.getnframes()
                duration = frame_count / float(frame_rate)
                return duration
        except Exception:
            pass
        
        # 方法2: 使用mutagen（适用于MP3等格式）
        try:
            # 尝试使用mutagen的通用接口
            # 为了避免Pylance警告，我们使用动态导入
            import importlib
            mutagen_module = importlib.import_module('mutagen')
            if hasattr(mutagen_module, 'File'):
                audio_file = mutagen_module.File(audio_path)
                if audio_file is not None and hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
                    duration = float(audio_file.info.length)
                    return duration
        except (ImportError, AttributeError, TypeError, Exception):
            pass
        
        # 方法3: 使用librosa（通用但需要额外依赖）
        try:
            import librosa
            y, sr = librosa.load(audio_path)
            duration = len(y) / sr
            return duration
        except (ImportError, Exception):
            pass
        
        # 方法4: 使用pydub（如果可用）
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000.0  # pydub返回毫秒
            return duration
        except (ImportError, Exception):
            pass
        
        # 最后回退: 根据文本长度估算时长
        self.logger.warning(f"无法获取音频时长，使用文本长度估算: {audio_path}")
        # 中文大约每秒3-4个字符，英文约每秒10-15个字符
        chars_per_second = 3.5 if self._is_chinese_text(text) else 12
        duration = max(1.0, len(text) / chars_per_second)
        
        return duration
    
    def _is_chinese_text(self, text: str) -> bool:
        """判断文本是否主要为中文"""
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        return chinese_chars > len(text) * 0.5

    async def _synthesize_edge_tts(self, text: str, output_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """Edge TTS合成"""
        try:
            from all_tts_functions.edge_tts import edge_tts
            
            # Edge TTS使用save_path参数
            save_path = str(output_path) if output_path else None
            result = edge_tts(text, save_path)
            
            # 检查文件是否成功生成
            if save_path and os.path.exists(save_path):
                metadata = self._get_audio_metadata(save_path, text)
                
                return {
                    "success": True,
                    "message": "Edge TTS合成成功",
                    "audio_path": save_path,
                    "duration": metadata["duration"],
                    "file_size": metadata["file_size"],
                    "engine": "edge_tts",
                    "estimated": False
                }
            else:
                return {"success": False, "error": "Edge TTS音频文件生成失败"}
            
        except Exception as e:
            return {"success": False, "error": f"Edge TTS合成失败: {e}"}
    
    async def _synthesize_fish_tts(self, text: str, output_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """Fish TTS合成"""
        try:
            from all_tts_functions.fish_tts import fish_tts
            
            # Fish TTS使用save_path参数
            save_path = str(output_path) if output_path else None
            result = fish_tts(text, save_path, self.config.fish_character_name)
            
            # 检查文件是否成功生成
            if save_path and os.path.exists(save_path):
                metadata = self._get_audio_metadata(save_path, text)
                
                return {
                    "success": True,
                    "message": "Fish TTS合成成功",
                    "audio_path": save_path,
                    "duration": metadata["duration"],
                    "file_size": metadata["file_size"],
                    "engine": "fish_tts",
                    "estimated": False
                }
            else:
                return {"success": False, "error": "Fish TTS音频文件生成失败"}
            
        except Exception as e:
            return {"success": False, "error": f"Fish TTS合成失败: {e}"}
    
    async def _synthesize_openai_tts(self, text: str, output_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """OpenAI TTS合成"""
        try:
            from all_tts_functions.openai_tts import openai_tts
            
            # OpenAI TTS使用save_path参数
            save_path = str(output_path) if output_path else None
            result = openai_tts(text, save_path)
            
            # 检查文件是否成功生成
            if save_path and os.path.exists(save_path):
                metadata = self._get_audio_metadata(save_path, text)
                
                return {
                    "success": True,
                    "message": "OpenAI TTS合成成功",
                    "audio_path": save_path,
                    "duration": metadata["duration"],
                    "file_size": metadata["file_size"],
                    "engine": "openai_tts",
                    "estimated": False
                }
            else:
                return {"success": False, "error": "OpenAI TTS音频文件生成失败"}
            
        except Exception as e:
            return {"success": False, "error": f"OpenAI TTS合成失败: {e}"}
    
    async def _synthesize_azure_tts(self, text: str, output_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """Azure TTS合成"""
        try:
            from all_tts_functions.azure_tts import azure_tts
            
            # Azure TTS已经返回统一格式
            result = azure_tts(
                text=text,
                voice=self.config.azure_voice,
                output_path=str(output_path) if output_path else None
            )
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Azure TTS合成失败: {e}"}
    
    def get_available_engines(self) -> list:
        """获取可用的TTS引擎列表"""
        available = []
        
        # 检查Edge TTS
        try:
            import edge_tts
            available.append(TTSEngine.EDGE_TTS)
        except ImportError:
            pass
        
        # 检查Fish TTS
        if self.config.fish_api_key:
            available.append(TTSEngine.FISH_TTS)
        
        # 检查OpenAI TTS
        if self.config.openai_api_key:
            available.append(TTSEngine.OPENAI_TTS)
        
        # 检查Azure TTS
        if self.config.azure_api_key:
            available.append(TTSEngine.AZURE_TTS)
        
        return available
    
    def get_voices_for_engine(self, engine: TTSEngine) -> list:
        """获取指定引擎的可用语音列表"""
        try:
            if engine == TTSEngine.EDGE_TTS:
                # 返回常用Edge TTS语音
                return [
                    "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural",
                    "zh-CN-XiaochenNeural", "zh-CN-XiaohanNeural"
                ]
            elif engine == TTSEngine.FISH_TTS:
                # 返回Fish TTS角色
                return ["雷军", "丁真", "四川话", "东北话"]
            elif engine == TTSEngine.OPENAI_TTS:
                # 返回OpenAI TTS语音
                return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            elif engine == TTSEngine.AZURE_TTS:
                # 返回Azure TTS语音
                return [
                    "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural",
                    "zh-CN-XiaochenNeural", "zh-CN-XiaohanNeural"
                ]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"获取语音列表失败: {e}")
            return []
    
    def get_available_voices(self) -> Dict[str, list]:
        """获取所有引擎的可用语音列表
        
        Returns:
            字典，键为引擎名称，值为该引擎的语音列表
        """
        voices = {}
        for engine in TTSEngine:
            voices[engine.value] = self.get_voices_for_engine(engine)
        return voices
    
    def get_engine_status(self, engine: Optional[TTSEngine] = None) -> Dict[str, Any]:
        """获取引擎状态信息
        
        Args:
            engine: 指定引擎，如果为None则返回所有引擎的状态
            
        Returns:
            单个引擎状态或所有引擎状态汇总
        """
        if engine is None:
            # 返回所有引擎的状态汇总
            available_engines = self.get_available_engines()
            all_statuses = {}
            for eng in TTSEngine:
                all_statuses[eng.value] = self._get_single_engine_status(eng)
            
            return {
                "available_engines": [eng.value for eng in available_engines],
                "engine_statuses": all_statuses,
                "total_engines": len(TTSEngine),
                "available_count": len(available_engines)
            }
        else:
            # 返回单个引擎状态
            return self._get_single_engine_status(engine)
    
    def _get_single_engine_status(self, engine: TTSEngine) -> Dict[str, Any]:
        """获取指定引擎的状态信息"""
        try:
            available_engines = self.get_available_engines()
            status = {
                "engine": engine.value,
                "available": engine in available_engines,
                "configured": False,
                "error": None
            }
            
            # 检查引擎配置状态
            if engine == TTSEngine.EDGE_TTS:
                status["configured"] = True  # Edge TTS 不需要特殊配置
            elif engine == TTSEngine.FISH_TTS:
                status["configured"] = bool(self.config.fish_api_key)
            elif engine == TTSEngine.OPENAI_TTS:
                status["configured"] = bool(self.config.openai_api_key)
            elif engine == TTSEngine.AZURE_TTS:
                status["configured"] = bool(self.config.azure_api_key)
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取引擎状态失败: {e}")
            return {
                "engine": engine.value,
                "available": False,
                "configured": False,
                "error": str(e)
            }
    
    def get_all_engine_statuses(self) -> Dict[str, Dict[str, Any]]:
        """获取所有引擎的状态信息"""
        statuses = {}
        for engine in TTSEngine:
            statuses[engine.value] = self.get_engine_status(engine)
        return statuses

def load_tts_config_from_app_config() -> TTSConfig:
    """从应用配置加载TTS配置"""
    try:
        from app.utils.config_manager import config_manager
        
        app_config = config_manager.load_config()
        tts_section = app_config.get("tts", {})
        
        # 构建TTSConfig
        config = TTSConfig()
        
        # 基础配置
        preferred_engine_str = tts_section.get("preferred_engine", "edge_tts")
        try:
            config.preferred_engine = TTSEngine(preferred_engine_str)
        except ValueError:
            config.preferred_engine = TTSEngine.EDGE_TTS
        
        # Edge TTS配置
        config.edge_voice = tts_section.get("edge_voice", "zh-CN-XiaoxiaoNeural")
        config.edge_rate = tts_section.get("edge_rate", "+0%")
        config.edge_pitch = tts_section.get("edge_pitch", "+0Hz")
        
        # Fish TTS配置
        config.fish_api_key = tts_section.get("fish_api_key", "")
        config.fish_character_name = tts_section.get("fish_character", "雷军")
        
        # OpenAI TTS配置
        config.openai_api_key = tts_section.get("openai_api_key", "")
        config.openai_voice = tts_section.get("openai_voice", "alloy")
        config.openai_model = tts_section.get("openai_model", "tts-1")
        
        # Azure TTS配置
        config.azure_api_key = tts_section.get("azure_api_key", "")
        config.azure_region = tts_section.get("azure_region", "eastus")
        config.azure_voice = tts_section.get("azure_voice", "zh-CN-XiaoxiaoNeural")
        
        logger.info(f"成功加载TTS配置: preferred_engine={config.preferred_engine}")
        return config
        
    except Exception as e:
        logger.warning(f"加载TTS配置失败，使用默认配置: {e}")
        return TTSConfig()

# 同步包装器，用于在非异步环境中调用异步方法
def run_sync_tts(manager: IntegratedTTSManager, text: str, 
                preferred_engine: Optional[TTSEngine] = None,
                output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    同步版本的TTS合成
    
    Args:
        manager: TTS管理器实例
        text: 要合成的文本
        preferred_engine: 首选引擎
        output_path: 输出文件路径
        
    Returns:
        合成结果字典
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        manager.synthesize_speech(text, preferred_engine, output_path)
    )