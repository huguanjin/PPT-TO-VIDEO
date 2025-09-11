"""
增强的TTS试听API - 合并FastAPI的多引擎支持到Flask
"""
import os
import sys
import json
import tempfile
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from utils.logger import get_logger  # type: ignore
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

# 创建蓝图
bp = Blueprint('enhanced_tts', __name__)
logger = get_logger(__name__)

@bp.route('/preview', methods=['POST'])
def enhanced_tts_preview():
    """
    增强的TTS配音试听接口 - 合并FastAPI的多引擎支持
    生成指定文本和语音参数的音频文件供试听
    """
    print("🎵 Enhanced TTS Preview API 被调用")
    try:
        data = request.get_json()
        print(f"📝 接收到数据: {data}")
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        text = data.get('text')
        engine = data.get('engine', 'edge_tts')
        voice = data.get('voice', 'zh-CN-XiaoxiaoNeural')
        rate = data.get('rate', 'medium')
        pitch = data.get('pitch', 'medium')
        fish_api_key = data.get('fish_api_key', '')
        fish_character = data.get('fish_character', '雷军')
        openai_api_key = data.get('openai_api_key', '')
        openai_voice = data.get('openai_voice', 'alloy')
        openai_model = data.get('openai_model', 'tts-1')
        azure_api_key = data.get('azure_api_key', '')
        azure_region = data.get('azure_region', '')
        azure_voice = data.get('azure_voice', 'zh-CN-XiaoxiaoNeural')
        
        if not text.strip():
            return jsonify({
                'success': False,
                'message': '文本内容不能为空'
            }), 400
        
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        audio_filename = f"preview_{engine}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        audio_path = temp_dir / audio_filename
        
        try:
            # 使用集成的TTS管理器（如果可用）
            try:
                from utils.integrated_tts_manager import IntegratedTTSManager, TTSConfig, TTSEngine
                
                # 如果是Fish TTS，需要获取角色ID
                fish_character_id = ""
                if engine == "fish_tts":
                    # 读取Fish TTS配置文件获取角色ID映射
                    fish_config_path = Path(__file__).parent.parent.parent / "config_data" / "fish_tts_config.json"
                    if fish_config_path.exists():
                        with open(fish_config_path, 'r', encoding='utf-8') as f:
                            fish_config = json.load(f)
                            character_id_dict = fish_config.get("character_id_dict", {})
                            fish_character_id = character_id_dict.get(fish_character, "")
                
                # 创建TTS配置对象
                integrated_config = TTSConfig(
                    edge_voice=voice,
                    edge_rate=rate,
                    edge_pitch=pitch,
                    fish_api_key=fish_api_key,
                    fish_character_name=fish_character,
                    fish_character_id=fish_character_id,
                    openai_api_key=openai_api_key,
                    openai_voice=openai_voice,
                    openai_model=openai_model,
                    azure_api_key=azure_api_key,
                    azure_region=azure_region,
                    azure_voice=azure_voice
                )
                
                # 初始化TTS管理器
                tts_manager = IntegratedTTSManager(integrated_config)
                
                # 根据选择的引擎设置首选引擎
                preferred_engine = None
                if engine == "edge_tts":
                    preferred_engine = TTSEngine.EDGE_TTS
                elif engine == "fish_tts":
                    preferred_engine = TTSEngine.FISH_TTS
                elif engine == "openai_tts":
                    preferred_engine = TTSEngine.OPENAI_TTS
                elif engine == "azure_tts":
                    preferred_engine = TTSEngine.AZURE_TTS
                
                # 在Flask中运行异步TTS
                result = run_async_in_flask(
                    tts_manager.synthesize_speech(
                        text,
                        audio_path,
                        preferred_engine=preferred_engine
                    )
                )
                
                if result and result.get("success") and audio_path.exists():
                    # 返回音频文件
                    return send_file(
                        str(audio_path),
                        as_attachment=True,
                        download_name=audio_filename,
                        mimetype='audio/wav'
                    )
                else:
                    error_msg = result.get("error", "未知错误") if result else "TTS处理失败"
                    return jsonify({
                        'success': False,
                        'message': f'音频生成失败: {error_msg}'
                    }), 500
                    
            except ImportError:
                # 如果集成TTS管理器不可用，使用原有的简单实现
                logger.warning("集成TTS管理器不可用，使用简化实现")
                
                if engine == 'edge_tts':
                    success = simple_edge_tts(text, str(audio_path), voice, rate, pitch)
                elif engine == 'openai_tts':
                    success = simple_openai_tts(text, str(audio_path), openai_api_key, openai_voice, openai_model)
                elif engine == 'azure_tts':
                    success = simple_azure_tts(text, str(audio_path), azure_api_key, azure_region, azure_voice)
                elif engine == 'fish_tts':
                    success = simple_fish_tts(text, str(audio_path), fish_api_key, fish_character)
                else:
                    return jsonify({
                        'success': False,
                        'message': f'不支持的TTS引擎: {engine}'
                    }), 400
                
                if not success:
                    return jsonify({
                        'success': False,
                        'message': f'{engine}生成失败'
                    }), 500
                
                # 返回音频文件
                if audio_path.exists():
                    return send_file(
                        str(audio_path),
                        as_attachment=True,
                        download_name=audio_filename,
                        mimetype='audio/wav'
                    )
                else:
                    return jsonify({
                        'success': False,
                        'message': '音频文件生成失败'
                    }), 500
            
        except Exception as e:
            logger.error(f"TTS生成过程中出错: {e}")
            return jsonify({
                'success': False,
                'message': f'TTS生成失败: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"TTS预览失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def run_async_in_flask(coro):
    """在Flask中运行异步协程"""
    try:
        # 尝试获取现有事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果循环正在运行，在新线程中执行
            result = [None]
            exception = [None]
            
            def run_in_thread():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result[0] = new_loop.run_until_complete(coro)
                except Exception as e:
                    exception[0] = e  # type: ignore
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if exception[0]:
                raise exception[0]
            return result[0]
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # 没有事件循环，创建新的
        return asyncio.run(coro)

def simple_edge_tts(text, output_path, voice="zh-CN-XiaoxiaoNeural", rate="medium", pitch="medium"):
    """简化版Edge TTS"""
    try:
        import edge_tts
        
        async def async_edge_tts():
            # 构建SSML速率和音调
            rate_value = {"slow": "-20%", "medium": "0%", "fast": "+20%"}.get(rate, "0%")
            pitch_value = {"low": "-10%", "medium": "0%", "high": "+10%"}.get(pitch, "0%")
            
            ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN"><voice name="{voice}"><prosody rate="{rate_value}" pitch="{pitch_value}">{text}</prosody></voice></speak>'
            
            communicate = edge_tts.Communicate(ssml_text, voice)
            await communicate.save(output_path)
        
        return run_async_in_flask(async_edge_tts())
        
    except Exception as e:
        logger.error(f"Edge TTS失败: {e}")
        return False

def simple_openai_tts(text, output_path, api_key, voice="alloy", model="tts-1"):
    """简化版OpenAI TTS"""
    try:
        if not api_key:
            logger.error("OpenAI API密钥未提供")
            return False
        
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        response.stream_to_file(output_path)
        return True
        
    except Exception as e:
        logger.error(f"OpenAI TTS失败: {e}")
        return False

def simple_azure_tts(text, output_path, api_key, region, voice="zh-CN-XiaoxiaoNeural"):
    """简化版Azure TTS"""
    try:
        if not api_key or not region:
            logger.error("Azure API密钥或区域未提供")
            return False
        
        import azure.cognitiveservices.speech as speechsdk
        
        speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
        speech_config.speech_synthesis_voice_name = voice
        
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        
        if result and hasattr(result, 'reason') and result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            with open(output_path, "wb") as audio_file:
                audio_file.write(result.audio_data)
            return True
        else:
            error_reason = result.reason if result and hasattr(result, 'reason') else "未知错误"
            logger.error(f"Azure TTS失败: {error_reason}")
            return False
        
    except Exception as e:
        logger.error(f"Azure TTS失败: {e}")
        return False

def simple_fish_tts(text, output_path, api_key, character="雷军"):
    """简化版Fish TTS"""
    try:
        if not api_key:
            logger.error("Fish API密钥未提供")
            return False
        
        # 这里需要根据实际的Fish TTS API实现
        # 暂时返回False，表示未实现
        logger.warning("Fish TTS简化版未实现")
        return False
        
    except Exception as e:
        logger.error(f"Fish TTS失败: {e}")
        return False
