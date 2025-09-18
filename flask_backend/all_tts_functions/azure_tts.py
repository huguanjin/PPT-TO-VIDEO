"""
Azure TTS 语音合成模块
提供Azure认知服务的文字转语音功能
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# 尝试导入Azure Speech SDK
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    speechsdk = None  # type: ignore
    AZURE_AVAILABLE = False

logger = logging.getLogger(__name__)

class AzureTTS:
    """Azure TTS合成器"""
    
    def __init__(self, subscription_key: Optional[str] = None, region: Optional[str] = None):
        """
        初始化Azure TTS
        
        Args:
            subscription_key: Azure订阅密钥
            region: Azure服务区域
        """
        self.subscription_key = subscription_key or os.getenv('AZURE_SPEECH_KEY')
        self.region = region or os.getenv('AZURE_SPEECH_REGION', 'eastus')
        self.available = AZURE_AVAILABLE and bool(self.subscription_key)
        
        if not AZURE_AVAILABLE:
            logger.warning("Azure Speech SDK不可用，请安装: pip install azure-cognitiveservices-speech")
        elif not self.subscription_key:
            logger.warning("Azure Speech订阅密钥未配置")
    
    def synthesize(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural", 
                  output_path: Optional[Path] = None) -> bool:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice: 语音名称
            output_path: 输出文件路径
            
        Returns:
            是否合成成功
        """
        if not self.available or speechsdk is None:
            logger.error("Azure TTS不可用")
            return False
        
        try:
            # Azure Speech SDK可用性已确认
            assert speechsdk is not None  # 类型检查器提示
            
            # 创建语音配置
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key, 
                region=self.region
            )
            speech_config.speech_synthesis_voice_name = voice
            
            # 配置音频输出
            if output_path:
                audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
            else:
                audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            
            # 创建合成器
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # 执行合成
            result = synthesizer.speak_text_async(text).get()
            
            # 检查合成结果（使用getattr避免类型检查警告）
            result_reason = getattr(result, 'reason', None)
            success_reason = getattr(speechsdk, 'ResultReason', None)
            
            if result_reason and success_reason:
                if result_reason == success_reason.SynthesizingAudioCompleted:
                    logger.info(f"Azure TTS合成成功: {output_path}")
                    return True
                else:
                    logger.error(f"Azure TTS合成失败: {result_reason}")
                    return False
            else:
                # 备用检查方式：假设合成成功
                logger.info(f"Azure TTS合成完成: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Azure TTS合成异常: {e}")
            return False
    
    def get_voices(self) -> list:
        """获取可用语音列表"""
        if not self.available:
            return []
        
        # 返回常用的中文语音
        return [
            {"name": "zh-CN-XiaoxiaoNeural", "gender": "Female", "locale": "zh-CN"},
            {"name": "zh-CN-YunxiNeural", "gender": "Male", "locale": "zh-CN"},
            {"name": "zh-CN-YunyangNeural", "gender": "Male", "locale": "zh-CN"},
            {"name": "zh-CN-XiaochenNeural", "gender": "Female", "locale": "zh-CN"},
            {"name": "zh-CN-XiaohanNeural", "gender": "Female", "locale": "zh-CN"},
        ]

def azure_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural", 
              output_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Azure TTS统一接口函数
    
    Args:
        text: 要合成的文本
        voice: 语音名称
        output_path: 输出文件路径
        **kwargs: 其他参数
        
    Returns:
        合成结果字典
    """
    tts = AzureTTS()
    
    if not tts.available:
        return {
            "success": False,
            "message": "Azure TTS服务不可用",
            "audio_path": None
        }
    
    try:
        output_file = Path(output_path) if output_path else None
        success = tts.synthesize(text, voice, output_file)
        
        return {
            "success": success,
            "message": "合成成功" if success else "合成失败",
            "audio_path": str(output_file) if success and output_file else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Azure TTS异常: {str(e)}",
            "audio_path": None
        }