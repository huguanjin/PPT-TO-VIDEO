"""
集成的多引擎TTS管理器
支持多种TTS引擎：Edge TTS、Fish TTS、OpenAI TTS等
"""
import asyncio
import logging
import tempfile
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import os
import json
import wave
import struct

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from scipy.io.wavfile import write as wav_write
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# 导入自定义Edge TTS函数
try:
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from all_tts_functions.edge_tts import edge_tts as custom_edge_tts
    CUSTOM_EDGE_TTS_AVAILABLE = True
except ImportError:
    CUSTOM_EDGE_TTS_AVAILABLE = False

# 导入自定义Fish TTS函数
try:
    from all_tts_functions.fish_tts import fish_tts as custom_fish_tts
    CUSTOM_FISH_TTS_AVAILABLE = True
except ImportError:
    CUSTOM_FISH_TTS_AVAILABLE = False

try:
    from moviepy.editor import AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    AudioFileClip = None

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

class TTSEngine(Enum):
    """TTS引擎枚举"""
    EDGE_TTS = "edge_tts"
    FISH_TTS = "fish_tts"
    OPENAI_TTS = "openai_tts"
    AZURE_TTS = "azure_tts"
    SILENT = "silent"

@dataclass
class TTSConfig:
    """TTS配置类"""
    # Edge TTS配置
    edge_voice: str = "zh-CN-XiaoxiaoNeural"
    edge_rate: str = "medium"
    edge_pitch: str = "medium"
    
    # Fish TTS配置
    fish_api_key: str = ""
    fish_character_id: str = ""
    fish_character_name: str = ""
    
    # OpenAI TTS配置
    openai_api_key: str = ""
    openai_voice: str = "alloy"
    openai_model: str = "tts-1"
    
    # Azure TTS配置
    azure_api_key: str = ""
    azure_region: str = ""
    azure_voice: str = "zh-CN-XiaoxiaoNeural"
    
    # 通用配置
    sample_rate: int = 22050
    max_retries: int = 3
    timeout: float = 30.0

class IntegratedTTSManager:
    """集成的TTS管理器"""
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.engines = self._get_available_engines()
        
    def _get_available_engines(self) -> List[TTSEngine]:
        """获取可用的TTS引擎列表"""
        engines = []
        
        # 检查Edge TTS
        if EDGE_TTS_AVAILABLE:
            engines.append(TTSEngine.EDGE_TTS)
            self.logger.info("Edge TTS 可用")
        
        # 检查Fish TTS
        if self.config.fish_api_key:
            engines.append(TTSEngine.FISH_TTS)
            self.logger.info("Fish TTS 可用")
        
        # 检查OpenAI TTS
        if self.config.openai_api_key:
            engines.append(TTSEngine.OPENAI_TTS)
            self.logger.info("OpenAI TTS 可用")
        
        # 检查Azure TTS
        if self.config.azure_api_key:
            engines.append(TTSEngine.AZURE_TTS)
            self.logger.info("Azure TTS 可用")
        
        # 静默音频总是可用
        engines.append(TTSEngine.SILENT)
        
        return engines
    
    async def synthesize_speech(self, text: str, output_path: Path, 
                              preferred_engine: Optional[TTSEngine] = None) -> Dict[str, Any]:
        """
        合成语音，支持引擎优先级和自动fallback
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            preferred_engine: 首选引擎
            
        Returns:
            合成结果信息
        """
        if not text or not text.strip():
            return await self._generate_silent_audio(text, output_path, duration=1.0)
        
        # 清理文本
        cleaned_text = self._clean_text_for_tts(text)
        
        # 准备引擎列表
        engines_to_try = []
        if preferred_engine and preferred_engine in self.engines:
            engines_to_try.append(preferred_engine)
            
        # 添加其他可用引擎
        for engine in self.engines:
            if engine not in engines_to_try:
                engines_to_try.append(engine)
        
        # 逐个尝试引擎
        for attempt, engine in enumerate(engines_to_try):
            try:
                self.logger.info(f"尝试使用 {engine.value} 引擎合成语音 (尝试 {attempt + 1}/{len(engines_to_try)})")
                
                result = await self._synthesize_with_engine(engine, cleaned_text, output_path)
                
                if result["success"]:
                    self.logger.info(f"使用 {engine.value} 引擎合成成功")
                    return result
                    
            except Exception as e:
                self.logger.warning(f"{engine.value} 引擎失败: {str(e)}")
                continue
        
        # 如果所有引擎都失败，生成静默音频
        self.logger.warning("所有TTS引擎都失败，生成静默音频")
        return await self._generate_silent_audio(cleaned_text, output_path)
    
    def _clean_text_for_tts(self, text: str) -> str:
        """清理文本，移除TTS问题字符"""
        import re
        
        # 移除有问题的字符
        chars_to_remove = ['&', '®', '™', '©', '°', '±', '§']
        for char in chars_to_remove:
            text = text.replace(char, '')
        
        # 处理特殊符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:\"\'()（）。，！？；：""'']+', '', text)
        
        return text.strip()
    
    async def _synthesize_with_engine(self, engine: TTSEngine, text: str, output_path: Path) -> Dict[str, Any]:
        """使用指定引擎合成语音"""
        
        if engine == TTSEngine.EDGE_TTS:
            return await self._edge_tts_synthesize(text, output_path)
            
        elif engine == TTSEngine.FISH_TTS:
            return await self._fish_tts_synthesize(text, output_path)
            
        elif engine == TTSEngine.OPENAI_TTS:
            return await self._openai_tts_synthesize(text, output_path)
            
        elif engine == TTSEngine.AZURE_TTS:
            return await self._azure_tts_synthesize(text, output_path)
            
        elif engine == TTSEngine.SILENT:
            return await self._generate_silent_audio(text, output_path)
            
        else:
            raise ValueError(f"不支持的引擎: {engine}")
    
    async def _edge_tts_synthesize(self, text: str, output_path: Path) -> Dict[str, Any]:
        """Edge TTS合成 - 使用自定义实现"""
        
        # 优先使用自定义Edge TTS实现
        if CUSTOM_EDGE_TTS_AVAILABLE:
            try:
                self.logger.info("使用自定义Edge TTS实现")
                
                # 确保输出目录存在
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 在线程池中运行同步的自定义Edge TTS函数
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    custom_edge_tts,
                    text, 
                    str(output_path)
                )
                
                # 检查生成的文件
                if output_path.exists() and output_path.stat().st_size > 1000:
                    duration = self._get_audio_duration(output_path)
                    return {
                        "success": True,
                        "engine": "custom_edge_tts",
                        "duration": duration,
                        "file_size": output_path.stat().st_size,
                        "method": "custom_implementation"
                    }
                else:
                    self.logger.warning("自定义Edge TTS生成的文件无效或过小")
                    
            except Exception as e:
                self.logger.warning(f"自定义Edge TTS失败: {str(e)}")
                
        # 如果自定义实现失败，回退到原始库方法
        self.logger.info("回退到原始Edge TTS库方法")
        if EDGE_TTS_AVAILABLE:
            return await self._edge_tts_library_method(text, output_path)
        else:
            raise ImportError("Edge TTS 不可用：自定义实现和官方库都无法使用")
            # Fallback to library method
            return await self._edge_tts_library_method(text, output_path)
    
    async def _edge_tts_library_method(self, text: str, output_path: Path) -> Dict[str, Any]:
        """Edge TTS库方法 - 作为命令行的fallback"""
        for retry in range(self.config.max_retries):
            try:
                # 转换速率格式
                rate_mapping = {
                    "slow": "-50%",
                    "medium": "+0%", 
                    "fast": "+50%"
                }
                rate = rate_mapping.get(self.config.edge_rate, "+0%")
                
                # 转换音调格式
                pitch_mapping = {
                    "x-low": "-50Hz",
                    "low": "-25Hz",
                    "medium": "+0Hz",
                    "high": "+25Hz", 
                    "x-high": "+50Hz"
                }
                pitch = pitch_mapping.get(self.config.edge_pitch, "+0Hz")
                
                communicate = edge_tts.Communicate(
                    text, 
                    self.config.edge_voice,
                    rate=rate,
                    pitch=pitch
                )
                
                await asyncio.wait_for(
                    communicate.save(str(output_path)), 
                    timeout=self.config.timeout
                )
                
                if output_path.exists() and output_path.stat().st_size > 1000:
                    duration = self._get_audio_duration(output_path)
                    return {
                        "success": True,
                        "engine": "edge_tts",
                        "duration": duration,
                        "file_size": output_path.stat().st_size,
                        "method": "library",
                        "retry_count": retry
                    }
                    
            except Exception as e:
                self.logger.warning(f"Edge TTS 库方法失败 (重试 {retry + 1}/{self.config.max_retries}): {str(e)}")
                if retry < self.config.max_retries - 1:
                    await asyncio.sleep(1)
        
        raise Exception("Edge TTS 库方法多次重试后失败")
    
    async def _fish_tts_synthesize(self, text: str, output_path: Path) -> Dict[str, Any]:
        """Fish TTS合成 - 使用自定义实现"""
        
        # 优先使用自定义Fish TTS实现
        if CUSTOM_FISH_TTS_AVAILABLE:
            try:
                self.logger.info("使用自定义Fish TTS实现")
                
                # 确保输出目录存在
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 在线程池中运行同步的自定义Fish TTS函数
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    custom_fish_tts,
                    text, 
                    str(output_path)
                )
                
                # 检查生成的文件
                if output_path.exists() and output_path.stat().st_size > 1000:
                    duration = self._get_audio_duration(output_path)
                    return {
                        "success": True,
                        "engine": "custom_fish_tts",
                        "duration": duration,
                        "file_size": output_path.stat().st_size,
                        "method": "custom_implementation"
                    }
                else:
                    self.logger.warning("自定义Fish TTS生成的文件无效或过小")
                    
            except Exception as e:
                self.logger.warning(f"自定义Fish TTS失败: {str(e)}")
                
        # 如果自定义实现失败，回退到原始实现
        self.logger.info("回退到原始Fish TTS实现")
        return await self._fish_tts_original_method(text, output_path)
    
    async def _fish_tts_original_method(self, text: str, output_path: Path) -> Dict[str, Any]:
        """原始Fish TTS实现作为备选方案"""
        if not self.config.fish_api_key:
            raise ValueError("Fish TTS API密钥未配置")
        
        url = "https://api.fish.audio/v1/tts"
        
        payload = {
            "text": text,
            "format": "mp3",
            "mp3_bitrate": 128,
            "normalize": True,
            "reference_id": self.config.fish_character_id
        }
        
        headers = {
            "Authorization": f"Bearer {self.config.fish_api_key}",
            "Content-Type": "application/json"
        }
        
        for retry in range(self.config.max_retries):
            try:
                # 异步HTTP请求
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(url, json=payload, headers=headers, timeout=self.config.timeout)
                )
                
                if response.status_code == 200:
                    # 保存和转换音频
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 先保存MP3
                    temp_mp3_path = output_path.with_suffix('.mp3')
                    with open(temp_mp3_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 转换为WAV
                    if MOVIEPY_AVAILABLE:
                        audio_clip = AudioFileClip(str(temp_mp3_path))
                        audio_clip.write_audiofile(str(output_path), verbose=False, logger=None)
                        audio_clip.close()
                    elif PYDUB_AVAILABLE:
                        audio = AudioSegment.from_mp3(str(temp_mp3_path))
                        audio.export(str(output_path), format="wav")
                    else:
                        # 如果没有转换工具，直接重命名
                        temp_mp3_path.rename(output_path)
                    
                    # 清理临时文件
                    if temp_mp3_path.exists():
                        temp_mp3_path.unlink()
                    
                    duration = self._get_audio_duration(output_path)
                    return {
                        "success": True,
                        "engine": "fish_tts",
                        "duration": duration,
                        "file_size": output_path.stat().st_size,
                        "character_id": self.config.fish_character_id,
                        "retry_count": retry,
                        "method": "original_api"
                    }
                else:
                    self.logger.warning(f"Fish TTS API请求失败，状态码: {response.status_code}")
                    
            except Exception as e:
                self.logger.warning(f"Fish TTS 失败 (重试 {retry + 1}/{self.config.max_retries}): {str(e)}")
                if retry < self.config.max_retries - 1:
                    await asyncio.sleep(2)
        
        raise Exception("Fish TTS 多次重试后失败")
    
    async def _openai_tts_synthesize(self, text: str, output_path: Path) -> Dict[str, Any]:
        """OpenAI TTS合成"""
        if not self.config.openai_api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        try:
            try:
                import openai
            except ImportError:
                raise Exception("OpenAI库未安装，请运行: pip install openai")
                
            client = openai.OpenAI(api_key=self.config.openai_api_key)
            
            response = client.audio.speech.create(
                model=self.config.openai_model,
                voice=self.config.openai_voice,
                input=text
            )
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            response.stream_to_file(str(output_path))
            
            duration = self._get_audio_duration(output_path)
            return {
                "success": True,
                "engine": "openai_tts",
                "duration": duration,
                "file_size": output_path.stat().st_size,
                "model": self.config.openai_model,
                "voice": self.config.openai_voice
            }
            
        except Exception as e:
            raise Exception(f"OpenAI TTS 失败: {str(e)}")
    
    async def _azure_tts_synthesize(self, text: str, output_path: Path) -> Dict[str, Any]:
        """Azure TTS合成"""
        if not self.config.azure_api_key or not self.config.azure_region:
            raise ValueError("Azure TTS 配置未完整")
        
        try:
            try:
                import azure.cognitiveservices.speech as speechsdk
            except ImportError:
                raise Exception("Azure Speech库未安装，请运行: pip install azure-cognitiveservices-speech")
            
            speech_config = speechsdk.SpeechConfig(
                subscription=self.config.azure_api_key, 
                region=self.config.azure_region
            )
            speech_config.speech_synthesis_voice_name = self.config.azure_voice
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
            
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                duration = self._get_audio_duration(output_path)
                return {
                    "success": True,
                    "engine": "azure_tts",
                    "duration": duration,
                    "file_size": output_path.stat().st_size,
                    "voice": self.config.azure_voice
                }
            else:
                raise Exception(f"Azure TTS 合成失败: {result.reason}")
                
        except Exception as e:
            raise Exception(f"Azure TTS 失败: {str(e)}")
    
    async def _generate_silent_audio(self, text: str, output_path: Path, duration: Optional[float] = None) -> Dict[str, Any]:
        """生成静默音频"""
        if duration is None:
            # 根据文本长度估算时长（中文约3.5字/秒）
            estimated_duration = max(1.0, len(text) / 3.5)
        else:
            estimated_duration = duration
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用标准库生成静默音频
        sample_rate = self.config.sample_rate
        samples = int(sample_rate * estimated_duration)
        
        if SCIPY_AVAILABLE and NUMPY_AVAILABLE:
            # 优先使用scipy和numpy
            silence = np.zeros(samples, dtype=np.int16)
            wav_write(str(output_path), sample_rate, silence)
        else:
            # 使用标准库wave模块生成静默音频
            with wave.open(str(output_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # 生成静默数据
                silence_data = b'\x00\x00' * samples  # 16-bit静默
                wav_file.writeframes(silence_data)
        
        return {
            "success": True,
            "engine": "silent",
            "duration": estimated_duration,
            "file_size": output_path.stat().st_size,
            "estimated": True
        }
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长"""
        try:
            if PYDUB_AVAILABLE:
                audio = AudioSegment.from_file(str(audio_path))
                return len(audio) / 1000.0  # 转换为秒
            
            import wave
            with wave.open(str(audio_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                return duration
                
        except Exception:
            # 如果无法读取，根据文件大小估算
            file_size = audio_path.stat().st_size
            estimated_duration = file_size / (2 * self.config.sample_rate)
            return max(1.0, estimated_duration)
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态信息"""
        return {
            "available_engines": [engine.value for engine in self.engines],
            "total_engines": len(self.engines),
            "edge_tts_available": EDGE_TTS_AVAILABLE,
            "moviepy_available": MOVIEPY_AVAILABLE,
            "pydub_available": PYDUB_AVAILABLE,
            "config": {
                "edge_voice": self.config.edge_voice,
                "fish_character_name": self.config.fish_character_name,
                "openai_voice": self.config.openai_voice,
                "azure_voice": self.config.azure_voice,
                "sample_rate": self.config.sample_rate
            }
        }
    
    def get_available_voices(self) -> Dict[str, List[str]]:
        """获取各引擎可用的语音列表"""
        voices = {}
        
        if TTSEngine.EDGE_TTS in self.engines:
            voices["edge_tts"] = [
                "zh-CN-XiaoxiaoNeural",
                "zh-CN-YunxiNeural", 
                "zh-CN-YunjianNeural",
                "zh-CN-YunxiaNeural",
                "zh-CN-YunyangNeural",
                "zh-CN-liaoning-XiaobeiNeural",
                "zh-CN-shaanxi-XiaoniNeural",
                "zh-HK-HiuGaaiNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
                "en-GB-SoniaNeural"
            ]
        
        if TTSEngine.OPENAI_TTS in self.engines:
            voices["openai_tts"] = [
                "alloy", "echo", "fable", "onyx", "nova", "shimmer"
            ]
        
        return voices

# 配置加载函数
def load_tts_config_from_file(config_file_path: str = "config_data/tts_config.json") -> TTSConfig:
    """从配置文件加载TTS配置"""
    config_path = Path(config_file_path)
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return TTSConfig(
            edge_voice=config_data.get("edge_voice", "zh-CN-XiaoxiaoNeural"),
            edge_rate=config_data.get("edge_rate", "medium"),
            edge_pitch=config_data.get("edge_pitch", "medium"),
            fish_api_key=config_data.get("fish_api_key", ""),
            fish_character_id=config_data.get("fish_character_id", ""),
            fish_character_name=config_data.get("fish_character_name", ""),
            openai_api_key=config_data.get("openai_api_key", ""),
            openai_voice=config_data.get("openai_voice", "alloy"),
            openai_model=config_data.get("openai_model", "tts-1"),
            azure_api_key=config_data.get("azure_api_key", ""),
            azure_region=config_data.get("azure_region", ""),
            azure_voice=config_data.get("azure_voice", "zh-CN-XiaoxiaoNeural"),
            sample_rate=config_data.get("sample_rate", 22050),
            max_retries=config_data.get("max_retries", 3),
            timeout=config_data.get("timeout", 30.0)
        )
    else:
        return TTSConfig()

def save_tts_config_to_file(config: TTSConfig, config_file_path: str = "config_data/tts_config.json"):
    """保存TTS配置到文件"""
    config_path = Path(config_file_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config_data = {
        "edge_voice": config.edge_voice,
        "edge_rate": config.edge_rate,
        "edge_pitch": config.edge_pitch,
        "fish_api_key": config.fish_api_key,
        "fish_character_id": config.fish_character_id,
        "fish_character_name": config.fish_character_name,
        "openai_api_key": config.openai_api_key,
        "openai_voice": config.openai_voice,
        "openai_model": config.openai_model,
        "azure_api_key": config.azure_api_key,
        "azure_region": config.azure_region,
        "azure_voice": config.azure_voice,
        "sample_rate": config.sample_rate,
        "max_retries": config.max_retries,
        "timeout": config.timeout,
        "last_updated": str(Path(__file__).stat().st_mtime)
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
