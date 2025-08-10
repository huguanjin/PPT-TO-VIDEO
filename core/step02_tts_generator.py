"""
步骤2: 讲话稿配音生成器
基于讲话稿内容生成语音文件 - 支持多种TTS引擎
"""
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging

import edge_tts
import wave
import audioop

from utils.logger import get_logger
from utils.file_manager import FileManager
from utils.integrated_tts_manager import IntegratedTTSManager, TTSConfig, TTSEngine, load_tts_config_from_file

class TTSGenerator:
    """TTS语音合成器 - 支持多引擎"""
    
    def __init__(self, project_dir: Path, voice: str = "zh-CN-XiaoxiaoNeural", 
                 preferred_engine: Optional[TTSEngine] = None):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # 加载TTS配置
        try:
            self.tts_config = load_tts_config_from_file()
            # 如果传入了voice参数，更新edge_voice
            if voice != "zh-CN-XiaoxiaoNeural":
                self.tts_config.edge_voice = voice
        except Exception as e:
            self.logger.warning(f"加载TTS配置失败，使用默认配置: {str(e)}")
            self.tts_config = TTSConfig(edge_voice=voice)
        
        # 初始化集成TTS管理器
        self.tts_manager = IntegratedTTSManager(self.tts_config)
        self.preferred_engine = preferred_engine
        
        # 记录引擎状态
        engine_status = self.tts_manager.get_engine_status()
        self.logger.info(f"TTS引擎初始化完成: {engine_status}")
        
        # 兼容性：保留旧的配置格式
        self.voice = self.tts_config.edge_voice
        
        # 兼容性：保留旧的配置格式
        self.voice = self.tts_config.edge_voice
        
        # TTS配置（保留向后兼容）
        self.tts_config_legacy = {
            "voice": self.tts_config.edge_voice,
            "rate": self.tts_config.edge_rate,
            "pitch": self.tts_config.edge_pitch
        }
    
    async def generate_audio(self, scripts_data: Dict[str, Any], progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """
        生成所有讲话稿的音频文件 - 支持多引擎
        
        Args:
            scripts_data: 讲话稿数据
            progress_callback: 进度回调函数
            
        Returns:
            音频数据字典
        """
        try:
            self.logger.info("开始生成音频文件")
            
            # 确保音频目录存在
            self.file_manager.audio_dir.mkdir(parents=True, exist_ok=True)
            
            scripts = scripts_data.get("scripts", [])
            total_scripts = len(scripts)
            
            audio_data = {
                "total_audio_files": total_scripts,
                "generation_completed": False,
                "generation_timestamp": datetime.now().isoformat(),
                "tts_config": self.tts_config.copy(),
                "audio_files": [],
                "total_duration_seconds": 0.0
            }
            
            cumulative_time = 0.0
            
            for i, script in enumerate(scripts):
                if progress_callback:
                    progress = int((i / total_scripts) * 100)
                    progress_callback(progress)
                
                self.logger.info(f"生成第 {script['slide_number']} 页音频")
                
                # 生成单个音频文件
                audio_info = await self._generate_single_audio(script, cumulative_time)
                audio_data["audio_files"].append(audio_info)
                
                # 更新累积时间
                cumulative_time += audio_info["duration_seconds"]
                
                # 模拟处理延迟
                await asyncio.sleep(0.5)
            
            # 计算总时长
            audio_data["total_duration_seconds"] = cumulative_time
            audio_data["generation_completed"] = True
            
            # 保存音频元数据
            self.file_manager.save_audio_metadata(audio_data)
            
            if progress_callback:
                progress_callback(100)
            
            self.logger.info(f"音频生成完成，总时长: {cumulative_time:.2f} 秒")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"音频生成失败: {e}", exc_info=True)
            raise
    
    async def _generate_single_audio(self, script: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """
        生成单个讲话稿的音频文件 - 支持多引擎
        
        Args:
            script: 单个讲话稿数据
            start_time: 开始时间（累积时间）
            
        Returns:
            音频信息字典
        """
        slide_number = script["slide_number"]
        script_content = script["script_content"]
        
        if not script_content or not script_content.strip():
            # 如果没有讲话稿内容，生成静默音频
            return await self._generate_silence_audio(script, start_time)
        
        # 音频文件路径
        audio_filename = f"audio_{slide_number:03d}.wav"
        audio_path = self.file_manager.audio_dir / audio_filename
        
        try:
            # 使用集成TTS管理器生成音频
            self.logger.info(f"正在合成语音: {script_content}")
            
            # 使用多引擎TTS合成音频
            result = await self.tts_manager.synthesize_speech(
                script_content, 
                audio_path, 
                preferred_engine=self.preferred_engine
            )
            
            if result["success"]:
                duration = result["duration"]
                file_size = result["file_size"]
                engine_used = result["engine"]
                
                self.logger.info(f"音频生成成功: {audio_path}, 引擎: {engine_used}, 时长: {duration:.2f}秒")
                
                audio_info = {
                    "audio_id": f"{slide_number:03d}",
                    "slide_number": slide_number,
                    "audio_file": audio_filename,
                    "duration_seconds": duration,
                    "file_size_bytes": file_size,
                    "sample_rate": self.tts_config.sample_rate,
                    "channels": 1,
                    "start_time": start_time,
                    "end_time": start_time + duration,
                    "generation_timestamp": datetime.now().isoformat(),
                    "script_content": script_content,
                    "voice_used": self.tts_config.edge_voice,
                    "engine_used": engine_used,
                    "estimated_from_text": result.get("estimated", False),
                    "retry_count": result.get("retry_count", 0)
                }
            
            return audio_info
            
        except Exception as e:
            self.logger.error(f"生成音频失败 {audio_filename}: {e}")
            # 如果TTS失败，生成静默音频作为备选
            return await self._generate_silence_audio(script, start_time, error=str(e))
    
    async def _generate_silence_audio(self, script: Dict[str, Any], start_time: float, error: str = None) -> Dict[str, Any]:
        """
        生成静默音频（当没有讲话稿内容或TTS失败时）
        
        Args:
            script: 讲话稿数据
            start_time: 开始时间
            error: 错误信息（如果有）
            
        Returns:
            音频信息字典
        """
        slide_number = script["slide_number"]
        audio_filename = f"audio_{slide_number:03d}.wav"
        audio_path = self.file_manager.audio_dir / audio_filename
        
        # 根据讲话稿内容估算时长，如果没有内容则使用3秒
        script_content = script.get("script_content", "")
        if script_content and script_content.strip():
            # 基于字数估算时长 (3.5字/秒)
            char_count = len(script_content.replace(" ", "").replace("\n", ""))
            duration = max(char_count / 3.5, 1.0)  # 最少1秒
        else:
            duration = 3.0  # 默认3秒
        
        duration = round(duration, 2)
        sample_rate = 22050
        
        try:
            # 创建静默音频数据
            silence_samples = int(duration * sample_rate)
            silence_data = b'\x00\x00' * silence_samples  # 16位静默数据
            
            # 保存为WAV文件
            with wave.open(str(audio_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silence_data)
            
            file_size = audio_path.stat().st_size
            
            if error:
                self.logger.warning(f"TTS失败，生成静默音频: {audio_filename} (时长: {duration}s), 错误: {error}")
            else:
                self.logger.info(f"生成静默音频: {audio_filename} (时长: {duration}s, 无讲话稿内容)")
            
            audio_info = {
                "audio_id": f"{slide_number:03d}",
                "slide_number": slide_number,
                "audio_file": audio_filename,
                "duration_seconds": duration,
                "file_size_bytes": file_size,
                "sample_rate": sample_rate,
                "channels": 1,
                "start_time": start_time,
                "end_time": start_time + duration,
                "generation_timestamp": datetime.now().isoformat(),
                "script_content": script_content,
                "voice_used": "silence",
                "is_silence": True,
                "error": error,
                "estimated_from_text": bool(script_content and script_content.strip())
            }
            
            return audio_info
            
        except Exception as e:
            self.logger.error(f"生成静默音频失败: {e}")
            raise
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        获取音频文件时长
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频时长（秒）
        """
        try:
            with wave.open(str(audio_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                return round(duration, 2)
        except Exception as e:
            self.logger.warning(f"获取音频时长失败: {e}")
            # 如果无法获取真实时长，使用估算时长
            return 3.0
    
    def get_available_voices(self) -> List[str]:
        """
        获取可用的语音列表
        
        Returns:
            语音名称列表
        """
        # 常用的中文语音
        chinese_voices = [
            "zh-CN-XiaoxiaoNeural",  # 晓晓 (女)
            "zh-CN-YunxiNeural",     # 云希 (男)
            "zh-CN-YunyangNeural",   # 云扬 (男)
            "zh-CN-XiaochenNeural",  # 晓辰 (女)
            "zh-CN-XiaohanNeural",   # 晓涵 (女)
            "zh-CN-XiaomengNeural",  # 晓梦 (女)
            "zh-CN-XiaomoNeural",    # 晓墨 (女)
            "zh-CN-XiaoqiuNeural",   # 晓秋 (女)
            "zh-CN-XiaoruiNeural",   # 晓睿 (女)
            "zh-CN-XiaoshuangNeural", # 晓双 (女)
            "zh-CN-XiaoxuanNeural",  # 晓萱 (女)
            "zh-CN-XiaoyanNeural",   # 晓颜 (女)
            "zh-CN-XiaoyouNeural",   # 晓悠 (女)
            "zh-CN-YunfengNeural",   # 云枫 (男)
            "zh-CN-YunhaoNeural",    # 云皓 (男)
            "zh-CN-YunjianNeural",   # 云健 (男)
        ]
        return chinese_voices
    
    async def test_voice(self, text: str = "这是语音测试") -> bool:
        """
        测试当前语音是否可用
        
        Args:
            text: 测试文本
            
        Returns:
            是否测试成功
        """
        try:
            test_path = self.file_manager.temp_dir / "voice_test.wav"
            test_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用集成TTS管理器测试
            result = await self.tts_manager.synthesize_speech(text, test_path)
            
            # 检查文件是否生成
            if result["success"] and test_path.exists() and test_path.stat().st_size > 0:
                test_path.unlink()  # 删除测试文件
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"语音测试失败: {e}")
            return False
    
    def get_available_engines(self) -> List[str]:
        """获取可用的TTS引擎列表"""
        status = self.tts_manager.get_engine_status()
        return status["available_engines"]
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取TTS引擎状态信息"""
        return self.tts_manager.get_engine_status()
    
    def get_available_voices(self) -> Dict[str, List[str]]:
        """获取各引擎可用的语音列表"""
        return self.tts_manager.get_available_voices()
    
    def set_preferred_engine(self, engine: TTSEngine):
        """设置首选TTS引擎"""
        self.preferred_engine = engine
        self.logger.info(f"设置首选TTS引擎: {engine.value}")
    
    def update_tts_config(self, **kwargs):
        """更新TTS配置"""
        for key, value in kwargs.items():
            if hasattr(self.tts_config, key):
                setattr(self.tts_config, key, value)
                self.logger.info(f"更新TTS配置: {key} = {value}")
        
        # 重新初始化TTS管理器
        self.tts_manager = IntegratedTTSManager(self.tts_config)
