#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一 TTS 配置管理 API
同时支持 Edge TTS 和 Fish TTS 的配置管理
"""

from flask import Blueprint, jsonify, request
import json
from pathlib import Path
import logging
import os
import time

# 创建蓝图
bp = Blueprint('unified_tts', __name__, url_prefix='/api/tts')

# 配置日志
logger = logging.getLogger(__name__)

def cleanup_old_audio_files(temp_dir, max_age_hours=0.083):
    """
    清理旧的音频预览文件
    :param temp_dir: 临时目录路径
    :param max_age_hours: 保留文件的最大年龄（小时，默认0.083约5分钟）
    """
    try:
        if not os.path.exists(temp_dir):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"已删除旧的音频预览文件: {filename}")
                    except Exception as e:
                        logger.warning(f"删除文件失败 {filename}: {e}")
        
        return cleaned_count
    except Exception as e:
        logger.error(f"清理音频文件时出错: {e}")
        return 0

def cleanup_all_audio_files(temp_dir):
    """
    清理所有音频预览文件
    :param temp_dir: 临时目录路径
    """
    try:
        if not os.path.exists(temp_dir):
            return 0
        
        cleaned_count = 0
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path) and filename.endswith('.mp3'):
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"已删除音频预览文件: {filename}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {filename}: {e}")
        
        return cleaned_count
    except Exception as e:
        logger.error(f"清理所有音频文件时出错: {e}")
        return 0

def load_edge_tts_config():
    """加载Edge TTS配置"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config_data" / "edge_tts_voices.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载Edge TTS配置失败: {e}")
    return None

def load_fish_tts_config():
    """加载Fish TTS配置"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config_data" / "fish_tts_voices.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载Fish TTS配置失败: {e}")
    return None
    try:
        config_path = Path(__file__).parent.parent.parent / "config_data" / "fish_tts_voices.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载Fish TTS配置失败: {e}")
    return None

def load_app_config():
    """加载应用配置"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config_data" / "app_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载应用配置失败: {e}")
    return None

@bp.route('/engines', methods=['GET'])
def get_tts_engines():
    """获取所有可用的TTS引擎"""
    try:
        engines = []
        
        # Edge TTS
        edge_config = load_edge_tts_config()
        if edge_config:
            edge_voices = edge_config.get('edge_tts_voices', {})
            total_edge_voices = sum(len(region_data.get('voices', [])) for region_data in edge_voices.values())
            
            engines.append({
                'id': 'edge_tts',
                'name': 'Edge TTS',
                'display_name': 'Microsoft Edge TTS',
                'description': '微软Edge文字转语音服务，免费使用',
                'voice_count': total_edge_voices,
                'languages': list(edge_voices.keys()),
                'available': True,
                'cost': 'free',
                'quality': 'high'
            })
        
        # Fish TTS
        fish_config = load_fish_tts_config()
        if fish_config:
            characters = fish_config.get('characters', [])
            engine_info = fish_config.get('engine_info', {})
            
            engines.append({
                'id': engine_info.get('id', 'fish_tts'),
                'name': engine_info.get('name', 'Fish TTS'),
                'display_name': 'Fish Audio TTS',
                'description': engine_info.get('description', '智能语音合成服务，提供名人声音克隆'),
                'voice_count': len(characters),
                'languages': ['zh-CN'],
                'available': True,  # 暂时设为True，可以根据API密钥配置调整
                'cost': 'paid',
                'quality': 'very_high',
                'requires_api_key': True
            })
        
        # 获取当前设置
        app_config = load_app_config()
        current_engine = 'edge_tts'
        if app_config and app_config.get('tts'):
            current_engine = app_config['tts'].get('preferred_engine', 'edge_tts')
        
        return jsonify({
            'success': True,
            'data': {
                'engines': engines,
                'current_engine': current_engine,
                'total_engines': len(engines)
            }
        })
        
    except Exception as e:
        logger.error(f"获取TTS引擎失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取TTS引擎失败: {str(e)}'
        }), 500

@bp.route('/voices/<engine_id>', methods=['GET'])
def get_voices_by_engine(engine_id):
    """根据引擎ID获取配音角色"""
    try:
        if engine_id == 'edge_tts':
            config = load_edge_tts_config()
            if not config:
                return jsonify({
                    'success': False,
                    'message': 'Edge TTS配置未找到'
                }), 404
            
            # 提取Edge TTS语音
            all_voices = []
            edge_tts_voices = config.get('edge_tts_voices', {})
            
            for region_code, region_data in edge_tts_voices.items():
                region_name = region_data.get('name', region_code)
                voices = region_data.get('voices', [])
                
                for voice in voices:
                    voice_info = {
                        'id': voice['name'],
                        'name': voice['name'],
                        'display_name': voice['display_name'],
                        'gender': voice['gender'],
                        'description': voice['description'],
                        'region': region_name,
                        'region_code': region_code,
                        'type': 'voice'
                    }
                    all_voices.append(voice_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'engine_id': engine_id,
                    'engine_name': 'Edge TTS',
                    'voices': all_voices,
                    'default_voice': config.get('default_voice', 'zh-CN-XiaoxiaoNeural'),
                    'total_count': len(all_voices)
                }
            })
            
        elif engine_id == 'fish_tts':
            config = load_fish_tts_config()
            if not config:
                return jsonify({
                    'success': False,
                    'message': 'Fish TTS配置未找到'
                }), 404
            
            # 提取Fish TTS角色并规范化字段名
            characters = config.get('characters', [])
            normalized_voices = []
            
            for character in characters:
                voice_info = {
                    'id': character.get('character', ''),  # 使用character作为id
                    'name': character.get('character', ''),  # 统一命名
                    'display_name': character.get('display_name', character.get('character', '')),
                    'gender': character.get('gender', ''),
                    'description': character.get('description', ''),
                    'character_id': character.get('character_id', ''),  # Fish TTS特有字段
                    'type': 'character'
                }
                normalized_voices.append(voice_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'engine_id': engine_id,
                    'engine_name': config.get('engine_info', {}).get('name', 'Fish TTS'),
                    'voices': normalized_voices,
                    'default_voice': config.get('default_character', '雷军'),
                    'total_count': len(normalized_voices),
                    'character_id_dict': config.get('character_id_dict', {})
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的TTS引擎: {engine_id}'
            }), 400
            
    except Exception as e:
        logger.error(f"获取{engine_id}配音角色失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取{engine_id}配音角色失败: {str(e)}'
        }), 500

@bp.route('/config', methods=['GET'])
def get_current_config():
    """获取当前TTS配置"""
    try:
        app_config = load_app_config()
        if not app_config or 'tts' not in app_config:
            return jsonify({
                'success': False,
                'message': 'TTS配置未找到'
            }), 404
        
        tts_config = app_config['tts']
        
        return jsonify({
            'success': True,
            'data': {
                'current_engine': tts_config.get('preferred_engine', 'edge_tts'),
                'edge_config': {
                    'voice': tts_config.get('edge_voice', 'zh-CN-XiaoxiaoNeural'),
                    'rate': tts_config.get('edge_rate', 'medium'),
                    'pitch': tts_config.get('edge_pitch', 'medium')
                },
                'fish_config': {
                    'character': tts_config.get('fish_character_name', '雷军'),
                    'character_id': tts_config.get('fish_character_id', ''),
                    'api_key_configured': bool(tts_config.get('fish_api_key'))
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取TTS配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取TTS配置失败: {str(e)}'
        }), 500

@bp.route('/config', methods=['POST'])
def update_tts_config():
    """更新TTS配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少配置数据'
            }), 400
        
        # 数据验证
        if 'preferred_engine' not in data:
            return jsonify({
                'success': False,
                'message': '缺少required_engine参数'
            }), 400
        
        preferred_engine = data['preferred_engine']
        if preferred_engine not in ['edge_tts', 'fish_tts', 'openai_tts']:
            return jsonify({
                'success': False,
                'message': f'不支持的TTS引擎: {preferred_engine}'
            }), 400
        
        # 验证具体引擎配置
        if preferred_engine == 'edge_tts' and 'edge_config' in data:
            edge_config = data['edge_config']
            if 'voice' not in edge_config or not edge_config['voice']:
                return jsonify({
                    'success': False,
                    'message': 'Edge TTS缺少语音角色配置'
                }), 400
        
        if preferred_engine == 'fish_tts' and 'fish_config' in data:
            fish_config = data['fish_config']
            if 'character' not in fish_config or not fish_config['character']:
                return jsonify({
                    'success': False,
                    'message': 'Fish TTS缺少角色名称配置'
                }), 400
            if 'character_id' not in fish_config or not fish_config['character_id']:
                return jsonify({
                    'success': False,
                    'message': 'Fish TTS缺少角色ID配置'
                }), 400
        
        # 加载当前应用配置
        app_config = load_app_config()
        if not app_config:
            app_config = {}
        
        if 'tts' not in app_config:
            app_config['tts'] = {}
        
        # 更新TTS配置
        tts_config = app_config['tts']
        
        # 更新引擎选择
        tts_config['preferred_engine'] = preferred_engine
            
        # 处理Edge TTS配置
        if 'edge_config' in data:
            edge_config = data['edge_config']
            if 'voice' in edge_config:
                tts_config['edge_voice'] = edge_config['voice']
            if 'rate' in edge_config:
                tts_config['edge_rate'] = edge_config['rate'] 
            if 'pitch' in edge_config:
                tts_config['edge_pitch'] = edge_config['pitch']
        
        # 处理Fish TTS配置
        if 'fish_config' in data:
            fish_config = data['fish_config']
            if 'character' in fish_config:
                tts_config['fish_character_name'] = fish_config['character']
                # 同时更新旧版本的fish_character字段以保持兼容性
                tts_config['fish_character'] = fish_config['character']
            if 'character_id' in fish_config:
                # 验证character_id是否有效（应该是32位UUID格式）
                character_id = fish_config['character_id']
                if len(character_id) >= 30 and character_id != fish_config.get('character', ''):
                    tts_config['fish_character_id'] = character_id
                else:
                    # 如果character_id无效，尝试从配置文件中获取正确的ID
                    character_name = fish_config.get('character', '')
                    try:
                        # 加载Fish TTS配置文件获取正确的character_id
                        voices_config_path = Path(__file__).parent.parent.parent / "config_data" / "fish_tts_voices.json"
                        if voices_config_path.exists():
                            with open(voices_config_path, 'r', encoding='utf-8') as f:
                                voices_config = json.load(f)
                            character_id_dict = voices_config.get('character_id_dict', {})
                            default_character = voices_config.get('default_character', '雷军')
                            
                            # 从character_id_dict中获取正确的ID
                            if character_name and character_name in character_id_dict:
                                tts_config['fish_character_id'] = character_id_dict[character_name]
                                logger.info(f"修正Fish TTS角色ID: {character_name} -> {character_id_dict[character_name]}")
                            else:
                                # 使用默认角色的ID
                                tts_config['fish_character_id'] = character_id_dict.get(default_character, '738d0cc1a3e9430a9de2b544a466a7fc')
                                logger.warning(f"使用默认Fish TTS角色ID: {default_character}")
                        else:
                            # 配置文件不存在，使用硬编码默认值
                            tts_config['fish_character_id'] = '738d0cc1a3e9430a9de2b544a466a7fc'
                            logger.warning("Fish TTS配置文件不存在，使用硬编码默认ID")
                    except Exception as e:
                        logger.error(f"获取Fish TTS配置失败: {e}")
                        tts_config['fish_character_id'] = '738d0cc1a3e9430a9de2b544a466a7fc'
        
        # 兼容旧格式数据处理 - 支持直接字段名
        for old_field, new_location in {
            'edge_voice': ('edge_voice',),
            'edge_rate': ('edge_rate',),
            'edge_pitch': ('edge_pitch',),
            'fish_character_name': ('fish_character_name', 'fish_character'),
            'fish_character_id': ('fish_character_id',)
        }.items():
            if old_field in data:
                for field in new_location:
                    tts_config[field] = data[old_field]
        
        # 更新配置元数据
        if '_updated_at' in data:
            app_config['_updated_at'] = data['_updated_at']
        else:
            from datetime import datetime
            app_config['_updated_at'] = datetime.now().isoformat()
        
        # 保存配置到文件
        config_path = Path(__file__).parent.parent.parent / "config_data" / "app_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(app_config, f, ensure_ascii=False, indent=2)
        
        # 记录更新日志
        logger.info(f"TTS配置更新成功 - 引擎: {tts_config.get('preferred_engine', 'N/A')}")
        if tts_config.get('preferred_engine') == 'edge_tts':
            logger.info(f"  Edge TTS语音: {tts_config.get('edge_voice', 'N/A')}")
        elif tts_config.get('preferred_engine') == 'fish_tts':
            logger.info(f"  Fish TTS角色: {tts_config.get('fish_character_name', 'N/A')} "
                       f"(ID: {tts_config.get('fish_character_id', 'N/A')})")
        
        return jsonify({
            'success': True,
            'message': 'TTS配置更新成功',
            'data': {
                'updated_config': tts_config,
                'preferred_engine': tts_config.get('preferred_engine'),
                'edge_config': {
                    'voice': tts_config.get('edge_voice'),
                    'rate': tts_config.get('edge_rate'), 
                    'pitch': tts_config.get('edge_pitch')
                },
                'fish_config': {
                    'character': tts_config.get('fish_character_name'),
                    'character_id': tts_config.get('fish_character_id')
                }
            }
        })
        
    except Exception as e:
        logger.error(f"更新TTS配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新TTS配置失败: {str(e)}'
        }), 500

@bp.route('/test', methods=['POST'])
def test_tts():
    """测试TTS配音"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少测试数据'
            }), 400
        
        engine_id = data.get('engine_id')
        voice_id = data.get('voice_id')
        test_text = data.get('text', '这是一个TTS配音测试。')
        
        if not engine_id or not voice_id:
            return jsonify({
                'success': False,
                'message': '缺少引擎ID或语音ID'
            }), 400
        
        # 创建临时音频文件
        import tempfile
        import os
        from datetime import datetime, timedelta
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = Path(__file__).parent.parent.parent / "temp" / "audio_preview"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理旧的音频文件（保留最近5分钟的文件）
        cleanup_old_audio_files(temp_dir)
        
        # 根据引擎类型确定文件扩展名
        if engine_id == 'edge_tts':
            file_extension = '.mp3'
        elif engine_id == 'fish_tts':
            file_extension = '.wav'
        else:
            file_extension = '.mp3'  # 默认
            
        audio_filename = f"preview_{engine_id}_{timestamp}{file_extension}"
        audio_path = temp_dir / audio_filename
        
        # 根据引擎类型调用相应的TTS功能
        success = False
        
        if engine_id == 'edge_tts':
            # 直接调用Edge TTS，传递语音参数
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent))
            
            try:
                # 导入Edge TTS核心函数
                import edge_tts as edge_tts_lib
                import asyncio
                
                # 直接使用传入的语音参数进行TTS生成，不依赖配置文件
                async def generate_preview_audio():
                    communicate = edge_tts_lib.Communicate(
                        test_text, 
                        voice_id,  # 直接使用前端传入的voice_id
                        rate="+0%",  # 可以后续从请求参数中获取
                        pitch="+0Hz"  # 可以后续从请求参数中获取
                    )
                    await communicate.save(str(audio_path))
                
                print(f"🎤 Edge TTS 预览开始")
                print(f"   文本长度: {len(test_text)} 字符")
                print(f"   语音选择: {voice_id}")
                print(f"   输出路径: {audio_path}")
                
                # 使用asyncio.run执行异步TTS生成
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(generate_preview_audio())
                    success = audio_path.exists() and audio_path.stat().st_size > 0
                    logger.info(f"Edge TTS预览结果: success={success}, 文件大小={audio_path.stat().st_size if audio_path.exists() else 0}")
                finally:
                    loop.close()
                        
            except Exception as e:
                logger.error(f"Edge TTS预览失败: {e}")
                success = False
                
        elif engine_id == 'fish_tts':
            # Fish TTS处理逻辑
            try:
                import sys
                sys.path.append(str(Path(__file__).parent.parent.parent))
                from all_tts_functions.fish_tts import fish_tts
                
                # 将voice_id转换为character名称
                # voice_id可能是character_id或者直接是character名称
                fish_config = load_fish_tts_config()
                character_name = None
                
                if fish_config and 'characters' in fish_config:
                    # 首先尝试按character_id查找
                    for char in fish_config['characters']:
                        if char.get('character_id') == voice_id:
                            character_name = char.get('character')
                            break
                    
                    # 如果没找到，再尝试按character名称查找
                    if not character_name:
                        for char in fish_config['characters']:
                            if char.get('character') == voice_id:
                                character_name = char.get('character')
                                break
                
                # 如果还是没找到，检查是否voice_id本身就是一个有效的角色名
                if not character_name and fish_config:
                    # 检查voice_id是否直接是配置中的一个角色名
                    character_id_dict = fish_config.get('character_id_dict', {})
                    if voice_id in character_id_dict:
                        character_name = voice_id
                
                if not character_name:
                    # 如果还是没找到，使用默认角色
                    character_name = fish_config.get('default_character', '雷军') if fish_config else '雷军'
                    logger.warning(f"未找到角色 {voice_id}，使用默认角色: {character_name}")
                else:
                    logger.info(f"找到角色: {character_name} (输入: {voice_id})")
                
                print(f"🐟 Fish TTS 预览开始")
                print(f"   文本长度: {len(test_text)} 字符")
                print(f"   角色选择: {character_name} (ID: {voice_id})")
                print(f"   输出路径: {audio_path}")
                
                # 调用Fish TTS，传入character名称
                fish_tts(test_text, str(audio_path), character_name)
                success = audio_path.exists() and audio_path.stat().st_size > 0
                logger.info(f"Fish TTS预览结果: success={success}, 文件大小={audio_path.stat().st_size if audio_path.exists() else 0}")
            except ImportError:
                logger.error("Fish TTS功能未实现")
                success = False
            except Exception as e:
                logger.error(f"Fish TTS预览失败: {e}")
                success = False
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的TTS引擎: {engine_id}'
            }), 400
        
        if success and audio_path.exists():
            # 返回音频文件的URL路径
            audio_url = f"/temp/audio_preview/{audio_filename}"
            return jsonify({
                'success': True,
                'message': 'TTS测试成功',
                'data': {
                    'engine_id': engine_id,
                    'voice_id': voice_id,
                    'text': test_text,
                    'audio_url': audio_url,
                    'audio_path': str(audio_path),
                    'estimated_duration': len(test_text) * 0.15
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'{engine_id}语音生成失败'
            }), 500
        
    except Exception as e:
        logger.error(f"TTS测试失败: {e}")
        return jsonify({
            'success': False,
            'message': f'TTS测试失败: {str(e)}'
        }), 500

@bp.route('/cleanup', methods=['POST'])
def cleanup_preview_files():
    """手动清理音频预览文件"""
    try:
        data = request.get_json() or {}
        cleanup_type = data.get('type', 'old')  # 'old' 或 'all'
        max_age_hours = data.get('max_age_hours', 0.083)  # 默认5分钟
        
        temp_dir = Path(__file__).parent.parent.parent / "temp" / "audio_preview"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        if cleanup_type == 'all':
            cleaned_count = cleanup_all_audio_files(str(temp_dir))
            message = f"已清理所有音频预览文件，共删除 {cleaned_count} 个文件"
        else:
            cleaned_count = cleanup_old_audio_files(str(temp_dir), max_age_hours)
            if max_age_hours >= 1:
                time_desc = f"{max_age_hours} 小时前"
            else:
                minutes = int(max_age_hours * 60)
                time_desc = f"{minutes} 分钟前"
            message = f"已清理 {time_desc} 的音频预览文件，共删除 {cleaned_count} 个文件"
        
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'cleaned_count': cleaned_count,
                'cleanup_type': cleanup_type,
                'max_age_hours': max_age_hours if cleanup_type == 'old' else 0
            }
        })
        
    except Exception as e:
        logger.error(f"手动清理音频文件失败: {e}")
        return jsonify({
            'success': False,
            'message': f'清理失败: {str(e)}'
        }), 500

@bp.route('/cleanup/status', methods=['GET'])
def get_cleanup_status():
    """获取临时文件状态"""
    try:
        temp_dir = Path(__file__).parent.parent.parent / "temp" / "audio_preview"
        
        if not temp_dir.exists():
            return jsonify({
                'success': True,
                'data': {
                    'total_files': 0,
                    'total_size': 0,
                    'oldest_file_age_hours': 0,
                    'files': []
                }
            })
        
        files_info = []
        total_size = 0
        current_time = time.time()
        oldest_age = 0
        
        for file_path in temp_dir.glob('*.mp3'):
            file_stat = file_path.stat()
            file_age_hours = (current_time - file_stat.st_mtime) / 3600
            oldest_age = max(oldest_age, file_age_hours)
            total_size += file_stat.st_size
            
            files_info.append({
                'name': file_path.name,
                'size': file_stat.st_size,
                'age_hours': round(file_age_hours, 2),
                'created_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stat.st_mtime))
            })
        
        # 按年龄排序
        files_info.sort(key=lambda x: x['age_hours'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'total_files': len(files_info),
                'total_size': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'oldest_file_age_hours': round(oldest_age, 2),
                'files': files_info
            }
        })
        
    except Exception as e:
        logger.error(f"获取清理状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500

# 错误处理
@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'TTS API接口不存在'
    }), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'TTS服务器内部错误'
    }), 500
