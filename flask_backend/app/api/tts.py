"""
TTS语音合成API接口
处理语音试听和生成相关操作
"""
import os
import sys
import tempfile
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    import edge_tts as edge_tts_lib
    import asyncio
    from all_tts_functions.edge_tts import edge_tts
    from all_tts_functions.openai_tts import openai_tts
    from all_tts_functions.azure_tts import azure_tts
    from all_tts_functions.fish_tts import fish_tts
    from utils.logger import get_logger
except ImportError as e:
    print(f"Warning: Could not import TTS modules: {e}")
    # 提供模拟函数
    edge_tts_lib = None
    def edge_tts(text, output_path):
        return False
    def openai_tts(text, output_path):
        return False
    def azure_tts(text, output_path):
        return False
    def fish_tts(text, output_path):
        return False
    
    def get_logger(name):
        import logging
        return logging.getLogger(name)

# 为Preview专用的简化Edge TTS函数
def preview_edge_tts(text, output_path, voice="zh-CN-XiaoxiaoNeural", rate="+0%", pitch="+0Hz"):
    """专为Preview使用的简化Edge TTS函数，使用命令行方式避免异步问题"""
    import subprocess
    import sys
    
    print(f"DEBUG: preview_edge_tts called with text='{text}', voice={voice}, rate={rate}, pitch={pitch}")
    print(f"DEBUG: output_path={output_path}")
    
    try:
        # 使用edge-tts命令行工具
        cmd = [
            sys.executable, "-m", "edge_tts",
            "--voice", voice,
            "--rate", rate,
            "--pitch", pitch,
            "--text", text,
            "--write-media", output_path
        ]
        
        print(f"DEBUG: Command: {' '.join(cmd)}")
        
        # 运行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        print(f"DEBUG: Return code: {result.returncode}")
        print(f"DEBUG: Stdout: {result.stdout}")
        print(f"DEBUG: Stderr: {result.stderr}")
        
        if result.returncode == 0:
            # 检查文件是否生成
            file_exists = os.path.exists(output_path)
            file_size = os.path.getsize(output_path) if file_exists else 0
            print(f"DEBUG: File exists: {file_exists}, size: {file_size}")
            
            if file_exists and file_size > 1000:
                logger.info(f"Edge TTS command line success: {output_path}")
                return True
            else:
                logger.error(f"Edge TTS file check failed: exists={file_exists}, size={file_size}")
                return False
        else:
            logger.error(f"Edge TTS command failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("DEBUG: Subprocess timeout")
        logger.error("Edge TTS command timeout")
        return False
    except Exception as e:
        print(f"DEBUG: Exception in subprocess: {e}")
        logger.error(f"Edge TTS command error: {e}")
        return False

# 简化版Edge TTS函数已废弃，改用优化版 all_tts_functions.edge_tts.edge_tts
# def simple_edge_tts(text, output_path, voice="zh-CN-XiaoxiaoNeural"):
#     """简化版Edge TTS，直接使用edge-tts库"""
#     if not edge_tts_lib:
#         raise Exception("edge-tts库未安装")
#     
#     async def async_edge_tts():
#         communicate = edge_tts_lib.Communicate(text, voice)
#         await communicate.save(output_path)
#     
#     # 运行异步函数
#     try:
#         # 尝试获取现有事件循环
#         loop = asyncio.get_event_loop()
#         if loop.is_running():
#             # 如果在运行中的循环内，创建新的循环
#             import threading
#             result = [None]
#             exception = [None]
#             
#             def run_tts():
#                 try:
#                     new_loop = asyncio.new_event_loop()
#                     asyncio.set_event_loop(new_loop)
#                     new_loop.run_until_complete(async_edge_tts())
#                     result[0] = True
#                 except Exception as e:
#                     exception[0] = e
#                 finally:
#                     new_loop.close()
#             
#             thread = threading.Thread(target=run_tts)
#             thread.start()
#             thread.join()
#             
#             if exception[0]:
#                 raise exception[0]
#             return result[0]
#         else:
#             loop.run_until_complete(async_edge_tts())
#             return True
#     except RuntimeError:
#         # 没有事件循环，创建新的
#         asyncio.run(async_edge_tts())
#         return True

bp = Blueprint('tts', __name__)
logger = get_logger(__name__)

@bp.route('/preview', methods=['POST'])
def preview_tts():
    """TTS试听功能"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        # 验证必需参数
        required_fields = ['text', 'engine']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必需参数: {field}'
                }), 400
        
        text = data['text']
        engine = data['engine']
        
        if not text.strip():
            return jsonify({
                'success': False,
                'message': '文本内容不能为空'
            }), 400
        
        # 限制试听文本长度
        if len(text) > 200:
            text = text[:200] + "..."
        
        # 准备TTS参数
        tts_config = {
            'engine': engine,
            'voice': data.get('voice', 'zh-CN-XiaoxiaoNeural'),  # Edge TTS默认声音
            'rate': data.get('rate', 0),
            'pitch': data.get('pitch', 0),
            'volume': data.get('volume', 100)
        }
        
        # 根据引擎添加特定配置
        if engine == 'fish':
            tts_config.update({
                'api_key': data.get('fish_api_key', ''),
                'character': data.get('fish_character', 'default')
            })
        elif engine == 'openai':
            tts_config.update({
                'api_key': data.get('openai_api_key', ''),
                'model': data.get('openai_model', 'tts-1'),
                'voice': data.get('openai_voice', 'alloy')
            })
        elif engine == 'azure':
            tts_config.update({
                'api_key': data.get('azure_api_key', ''),
                'region': data.get('azure_region', 'eastus'),
                'voice': data.get('azure_voice', 'zh-CN-XiaoxiaoNeural')
            })
        
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            output_path = temp_file.name
        
        try:
            # 根据引擎调用对应的TTS函数
            success = False
            
            if engine in ['edge', 'edge_tts']:
                # Edge TTS - 使用专为Preview设计的函数
                voice = tts_config.get('voice', 'zh-CN-XiaoxiaoNeural')
                rate = tts_config.get('rate', 0)
                pitch = tts_config.get('pitch', 0)
                
                # 转换前端参数到Edge TTS格式
                edge_rate = f"{rate:+d}%" if rate != 0 else "+0%"
                edge_pitch = f"{pitch:+d}Hz" if pitch != 0 else "+0Hz"
                
                try:
                    print(f"DEBUG: Calling preview_edge_tts with voice={voice}, rate={edge_rate}, pitch={edge_pitch}")
                    success = preview_edge_tts(text, output_path, voice, edge_rate, edge_pitch)
                    print(f"DEBUG: preview_edge_tts returned: {success}")
                    # 双重检查：函数返回值和文件存在性
                    if success and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        print(f"DEBUG: File check passed - size: {os.path.getsize(output_path)}")
                        success = True
                    else:
                        file_exists = os.path.exists(output_path)
                        file_size = os.path.getsize(output_path) if file_exists else 0
                        print(f"DEBUG: File check failed - success={success}, exists={file_exists}, size={file_size}")
                        logger.error(f"Edge TTS check failed: success={success}, exists={file_exists}, size={file_size}")
                        success = False
                except Exception as e:
                    print(f"DEBUG: Exception in Edge TTS: {e}")
                    logger.error(f"Edge TTS failed: {e}")
                    import traceback
                    logger.error(f"Edge TTS traceback: {traceback.format_exc()}")
                    success = False
                    
            elif engine in ['openai', 'openai_tts']:
                # OpenAI TTS
                try:
                    openai_tts(text, output_path)
                    success = os.path.exists(output_path)
                except Exception as e:
                    logger.error(f"OpenAI TTS failed: {e}")
                    success = False
                    
            elif engine in ['azure', 'azure_tts']:
                # Azure TTS
                try:
                    azure_tts(text, output_path)
                    success = os.path.exists(output_path)
                except Exception as e:
                    logger.error(f"Azure TTS failed: {e}")
                    success = False
                    
            elif engine in ['fish', 'fish_tts']:
                # Fish Audio TTS
                try:
                    fish_tts(text, output_path)
                    success = os.path.exists(output_path)
                except Exception as e:
                    logger.error(f"Fish TTS failed: {e}")
                    success = False
            else:
                raise Exception(f"不支持的TTS引擎: {engine}")
            
            if not success or not os.path.exists(output_path):
                raise Exception("TTS音频生成失败")
            
            # 检查生成的文件大小
            file_size = os.path.getsize(output_path)
            if file_size < 1024:  # 小于1KB可能是无效文件
                raise Exception("生成的音频文件过小，可能无效")
            
            # 返回音频文件
            def remove_file(response):
                try:
                    os.unlink(output_path)
                except:
                    pass
                return response
            
            response = send_file(
                output_path,
                mimetype='audio/wav',
                as_attachment=False,
                download_name='preview.wav'
            )
            
            # 注册回调来清理临时文件
            response.call_on_close(lambda: os.unlink(output_path) if os.path.exists(output_path) else None)
            
            return response
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise e
        
    except Exception as e:
        logger.error(f"TTS试听失败: {e}")
        return jsonify({
            'success': False,
            'message': f'TTS试听失败: {str(e)}'
        }), 500

@bp.route('/voices', methods=['GET'])
def get_voices():
    """获取可用的TTS声音列表"""
    try:
        engine = request.args.get('engine', 'edge')
        
        # 根据引擎返回不同的声音列表
        if engine == 'edge':
            voices = [
                {'id': 'zh-CN-XiaoxiaoNeural', 'name': '晓晓 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-YunxiNeural', 'name': '云希 (男声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-YunyangNeural', 'name': '云扬 (男声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaochenNeural', 'name': '晓辰 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaohanNeural', 'name': '晓涵 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaomoNeural', 'name': '晓墨 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaoqiuNeural', 'name': '晓秋 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaoruiNeural', 'name': '晓睿 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaoshuangNeural', 'name': '晓双 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaoxuanNeural', 'name': '晓萱 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaoyanNeural', 'name': '晓颜 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-XiaoyouNeural', 'name': '晓悠 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-YunfengNeural', 'name': '云枫 (男声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-YunjianNeural', 'name': '云健 (男声)', 'language': 'zh-CN'},
            ]
        elif engine == 'openai':
            voices = [
                {'id': 'alloy', 'name': 'Alloy', 'language': 'en-US'},
                {'id': 'echo', 'name': 'Echo', 'language': 'en-US'},
                {'id': 'fable', 'name': 'Fable', 'language': 'en-US'},
                {'id': 'onyx', 'name': 'Onyx', 'language': 'en-US'},
                {'id': 'nova', 'name': 'Nova', 'language': 'en-US'},
                {'id': 'shimmer', 'name': 'Shimmer', 'language': 'en-US'},
            ]
        elif engine == 'azure':
            voices = [
                {'id': 'zh-CN-XiaoxiaoNeural', 'name': '晓晓 (女声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-YunxiNeural', 'name': '云希 (男声)', 'language': 'zh-CN'},
                {'id': 'zh-CN-YunyangNeural', 'name': '云扬 (男声)', 'language': 'zh-CN'},
            ]
        elif engine == 'fish':
            voices = [
                {'id': 'default', 'name': '默认角色', 'language': 'zh-CN'},
                {'id': 'female1', 'name': '女声1', 'language': 'zh-CN'},
                {'id': 'male1', 'name': '男声1', 'language': 'zh-CN'},
            ]
        else:
            voices = []
        
        return jsonify({
            'success': True,
            'data': {
                'engine': engine,
                'voices': voices
            }
        })
        
    except Exception as e:
        logger.error(f"获取声音列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/engines', methods=['GET'])
def get_engines():
    """获取可用的TTS引擎列表"""
    try:
        engines = [
            {
                'id': 'edge',
                'name': 'Edge TTS',
                'description': '微软Edge浏览器内置TTS，免费且质量较高',
                'requires_api_key': False,
                'supported_languages': ['zh-CN', 'en-US', 'ja-JP', 'ko-KR']
            },
            {
                'id': 'openai',
                'name': 'OpenAI TTS',
                'description': 'OpenAI的高质量语音合成服务',
                'requires_api_key': True,
                'supported_languages': ['en-US', 'zh-CN']
            },
            {
                'id': 'azure',
                'name': 'Azure Cognitive Services',
                'description': '微软Azure认知服务TTS',
                'requires_api_key': True,
                'supported_languages': ['zh-CN', 'en-US', 'ja-JP', 'ko-KR']
            },
            {
                'id': 'fish',
                'name': 'Fish Audio',
                'description': 'Fish Audio语音克隆服务',
                'requires_api_key': True,
                'supported_languages': ['zh-CN', 'en-US']
            }
        ]
        
        return jsonify({
            'success': True,
            'data': engines
        })
        
    except Exception as e:
        logger.error(f"获取TTS引擎列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
