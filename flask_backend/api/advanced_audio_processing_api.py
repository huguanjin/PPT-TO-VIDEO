"""
高级音频处理 Flask API
提供完整的音频处理和分析服务

API功能:
1. 音频上传和分析
2. 音频处理流水线
3. 噪音消除服务
4. 音量归一化
5. 音质增强
6. 背景音乐混合
7. 空间音效处理
8. 音频格式转换
9. 批量音频处理
10. 实时处理状态

Author: Assistant
Date: 2025-09-09
Version: 1.0.0
"""

from flask import Flask, request, jsonify, send_file
import asyncio
import json
import os
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import time
import logging
from typing import Dict, List, Optional, Any

# 导入高级音频处理器
PROCESSOR_AVAILABLE = False
AdvancedAudioProcessor = None
AudioFormat = None
AudioQuality = None
NoiseType = None
EffectType = None
EmotionType = None
AudioProcessingConfig = None
MultiTrackConfig = None
AudioMetadata = None
AudioAnalysisResult = None

try:
    # 尝试从core目录导入
    import sys
    import os
    
    # 添加core目录到Python路径
    core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core')
    if core_path not in sys.path:
        sys.path.insert(0, core_path)
    
    from task4_3_advanced_audio_processor import (  # type: ignore
        AdvancedAudioProcessor, AudioFormat, AudioQuality, NoiseType, 
        EffectType, EmotionType, AudioProcessingConfig, MultiTrackConfig,
        AudioMetadata, AudioAnalysisResult
    )
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  音频处理器模块未找到，将使用模拟功能: {e}")
    PROCESSOR_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB限制

# 线程池执行器
executor = ThreadPoolExecutor(max_workers=4)

# 音频处理器实例
if PROCESSOR_AVAILABLE:
    audio_processor = AdvancedAudioProcessor()
else:
    audio_processor = None

# 任务状态跟踪
task_status: Dict[str, Dict] = {}
task_results: Dict[str, Any] = {}

# 允许的音频文件扩展名
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'aac', 'ogg', 'm4a'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_task_id():
    """生成唯一的任务ID"""
    return f"audio_task_{uuid.uuid4().hex[:12]}_{int(time.time())}"

def update_task_status(task_id: str, status: str, progress: float = 0.0, 
                      message: str = "", error: str = ""):
    """更新任务状态"""
    task_status[task_id] = {
        'status': status,
        'progress': progress,
        'message': message,
        'error': error,
        'timestamp': datetime.now().isoformat(),
        'updated_at': time.time()
    }

def cleanup_old_tasks():
    """清理旧任务"""
    current_time = time.time()
    old_tasks = []
    
    for task_id, status in task_status.items():
        if current_time - status.get('updated_at', 0) > 3600:  # 1小时
            old_tasks.append(task_id)
    
    for task_id in old_tasks:
        if task_id in task_status:
            del task_status[task_id]
        if task_id in task_results:
            del task_results[task_id]

async def process_audio_async(task_id: str, audio_file_path: str, config: dict):
    """异步音频处理"""
    try:
        if not PROCESSOR_AVAILABLE:
            # 模拟处理
            update_task_status(task_id, 'processing', 0.0, "开始音频处理...")
            await asyncio.sleep(1)
            
            update_task_status(task_id, 'processing', 0.5, "处理中...")
            await asyncio.sleep(1)
            
            update_task_status(task_id, 'completed', 1.0, "音频处理完成")
            task_results[task_id] = {
                'output_file': audio_file_path,
                'analysis': {
                    'rms_energy': 0.15,
                    'peak_amplitude': 0.85,
                    'dominant_frequency': 440.0,
                    'emotion_scores': {'neutral': 1.0}
                }
            }
            return
        
        # 设置进度回调
        def progress_callback(progress: float, message: str):
            update_task_status(task_id, 'processing', progress, message)
        
        audio_processor.set_progress_callback(progress_callback)
        
        # 加载音频
        update_task_status(task_id, 'processing', 0.0, "加载音频文件...")
        audio_data, metadata = await audio_processor.load_audio(audio_file_path)
        
        # 分析音频
        update_task_status(task_id, 'processing', 0.1, "分析音频...")
        analysis_result = await audio_processor.analyze_audio(audio_data, metadata.sample_rate)
        
        # 创建处理配置
        processing_config = AudioProcessingConfig(
            enable_noise_reduction=config.get('enable_noise_reduction', True),
            enable_volume_normalization=config.get('enable_volume_normalization', True),
            enable_quality_enhancement=config.get('enable_quality_enhancement', True),
            enable_spatial_effects=config.get('enable_spatial_effects', False),
            noise_reduction_strength=config.get('noise_reduction_strength', 0.7),
            normalization_target=config.get('normalization_target', -20.0),
            enhancement_level=config.get('enhancement_level', 0.5)
        )
        
        # 处理音频
        update_task_status(task_id, 'processing', 0.2, "处理音频...")
        processed_audio = await audio_processor.process_audio_pipeline(audio_data, processing_config)
        
        # 保存处理后的音频
        update_task_status(task_id, 'processing', 0.9, "保存音频...")
        output_format = AudioFormat(config.get('output_format', 'wav'))
        output_quality = AudioQuality(config.get('output_quality', 'high'))
        
        output_path = audio_file_path.replace('.', '_processed.')
        await audio_processor.save_audio(processed_audio, output_path, output_format, output_quality)
        
        # 完成
        update_task_status(task_id, 'completed', 1.0, "音频处理完成")
        task_results[task_id] = {
            'output_file': output_path,
            'metadata': {
                'sample_rate': metadata.sample_rate,
                'channels': metadata.channels,
                'duration': metadata.duration,
                'format': metadata.format.value,
                'quality': metadata.quality.value
            },
            'analysis': {
                'rms_energy': analysis_result.rms_energy,
                'peak_amplitude': analysis_result.peak_amplitude,
                'dominant_frequency': analysis_result.dominant_frequency,
                'noise_level': analysis_result.noise_level,
                'speech_rate': analysis_result.speech_rate,
                'emotion_scores': analysis_result.emotion_scores,
                'pause_count': len(analysis_result.pause_locations)
            }
        }
        
    except Exception as e:
        logger.error(f"音频处理失败: {e}")
        update_task_status(task_id, 'failed', 0.0, "", str(e))

@app.route('/api/audio/info', methods=['GET'])
def get_audio_info():
    """获取音频处理器信息"""
    try:
        info = {
            'processor_available': PROCESSOR_AVAILABLE,
            'supported_formats': [fmt.value for fmt in AudioFormat] if PROCESSOR_AVAILABLE else ['wav'],
            'supported_qualities': [q.value for q in AudioQuality] if PROCESSOR_AVAILABLE else ['high'],
            'noise_types': [nt.value for nt in NoiseType] if PROCESSOR_AVAILABLE else ['background'],
            'effect_types': [et.value for et in EffectType] if PROCESSOR_AVAILABLE else ['reverb'],
            'emotion_types': [em.value for em in EmotionType] if PROCESSOR_AVAILABLE else ['neutral'],
            'max_file_size': app.config['MAX_CONTENT_LENGTH'],
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        }
        
        return jsonify({
            'success': True,
            'data': info
        })
        
    except Exception as e:
        logger.error(f"获取音频信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/upload', methods=['POST'])
def upload_audio():
    """上传音频文件"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有文件被上传'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'不支持的文件格式，支持的格式: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        upload_dir = tempfile.mkdtemp(prefix="audio_upload_")
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        return jsonify({
            'success': True,
            'data': {
                'file_path': file_path,
                'filename': filename,
                'file_size': file_size,
                'file_format': file_ext,
                'upload_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"音频上传失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/analyze', methods=['POST'])
def analyze_audio():
    """分析音频文件"""
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                'success': False,
                'error': '缺少文件路径'
            }), 400
        
        file_path = data['file_path']
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
        
        task_id = generate_task_id()
        update_task_status(task_id, 'pending', 0.0, "任务已创建")
        
        # 异步分析音频
        async def analyze_async():
            try:
                if not PROCESSOR_AVAILABLE:
                    # 模拟分析
                    update_task_status(task_id, 'processing', 0.5, "分析中...")
                    await asyncio.sleep(1)
                    
                    analysis_result = {
                        'rms_energy': 0.15,
                        'peak_amplitude': 0.85,
                        'zero_crossing_rate': 0.1,
                        'spectral_centroid': 2500.0,
                        'dominant_frequency': 440.0,
                        'noise_level': 0.05,
                        'speech_rate': 120.0,
                        'emotion_scores': {
                            'neutral': 0.7,
                            'happy': 0.2,
                            'calm': 0.1
                        },
                        'pause_count': 3
                    }
                else:
                    # 真实分析
                    update_task_status(task_id, 'processing', 0.1, "加载音频...")
                    audio_data, metadata = await audio_processor.load_audio(file_path)
                    
                    update_task_status(task_id, 'processing', 0.5, "分析音频...")
                    analysis = await audio_processor.analyze_audio(audio_data, metadata.sample_rate)
                    
                    analysis_result = {
                        'rms_energy': analysis.rms_energy,
                        'peak_amplitude': analysis.peak_amplitude,
                        'zero_crossing_rate': analysis.zero_crossing_rate,
                        'spectral_centroid': analysis.spectral_centroid,
                        'spectral_bandwidth': analysis.spectral_bandwidth,
                        'dominant_frequency': analysis.dominant_frequency,
                        'noise_level': analysis.noise_level,
                        'speech_rate': analysis.speech_rate,
                        'emotion_scores': analysis.emotion_scores,
                        'pause_count': len(analysis.pause_locations),
                        'mfcc_features': analysis.mfcc_features[:5] if analysis.mfcc_features else []
                    }
                
                update_task_status(task_id, 'completed', 1.0, "分析完成")
                task_results[task_id] = analysis_result
                
            except Exception as e:
                logger.error(f"音频分析失败: {e}")
                update_task_status(task_id, 'failed', 0.0, "", str(e))
        
        # 在新线程中运行异步任务
        def run_analyze():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(analyze_async())
            finally:
                loop.close()
        
        executor.submit(run_analyze)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'pending',
                'message': '分析任务已创建'
            }
        })
        
    except Exception as e:
        logger.error(f"创建分析任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/process', methods=['POST'])
def process_audio():
    """处理音频文件"""
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                'success': False,
                'error': '缺少文件路径'
            }), 400
        
        file_path = data['file_path']
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
        
        # 处理配置
        config = data.get('config', {})
        
        task_id = generate_task_id()
        update_task_status(task_id, 'pending', 0.0, "任务已创建")
        
        # 异步处理音频
        def run_process():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_audio_async(task_id, file_path, config))
            finally:
                loop.close()
        
        executor.submit(run_process)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'pending',
                'message': '处理任务已创建'
            }
        })
        
    except Exception as e:
        logger.error(f"创建处理任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/noise-reduction', methods=['POST'])
def reduce_noise():
    """噪音消除"""
    try:
        data = request.get_json()
        required_fields = ['file_path']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少字段: {field}'
                }), 400
        
        file_path = data['file_path']
        noise_type = data.get('noise_type', 'background')
        strength = data.get('strength', 0.7)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
        
        task_id = generate_task_id()
        update_task_status(task_id, 'pending', 0.0, "噪音消除任务已创建")
        
        # 异步噪音消除
        async def reduce_noise_async():
            try:
                if not PROCESSOR_AVAILABLE:
                    # 模拟处理
                    update_task_status(task_id, 'processing', 0.5, "降噪中...")
                    await asyncio.sleep(1)
                    output_path = file_path.replace('.', '_denoised.')
                else:
                    # 真实处理
                    update_task_status(task_id, 'processing', 0.1, "加载音频...")
                    audio_data, metadata = await audio_processor.load_audio(file_path)
                    
                    update_task_status(task_id, 'processing', 0.5, "降噪处理...")
                    noise_enum = NoiseType(noise_type)
                    processed_audio = await audio_processor.reduce_noise(audio_data, noise_enum, strength)
                    
                    update_task_status(task_id, 'processing', 0.9, "保存音频...")
                    output_path = file_path.replace('.', '_denoised.')
                    await audio_processor.save_audio(processed_audio, output_path)
                
                update_task_status(task_id, 'completed', 1.0, "降噪完成")
                task_results[task_id] = {'output_file': output_path}
                
            except Exception as e:
                logger.error(f"降噪失败: {e}")
                update_task_status(task_id, 'failed', 0.0, "", str(e))
        
        def run_denoise():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(reduce_noise_async())
            finally:
                loop.close()
        
        executor.submit(run_denoise)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'pending',
                'message': '降噪任务已创建'
            }
        })
        
    except Exception as e:
        logger.error(f"创建降噪任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/normalize', methods=['POST'])
def normalize_volume():
    """音量归一化"""
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                'success': False,
                'error': '缺少文件路径'
            }), 400
        
        file_path = data['file_path']
        target_db = data.get('target_db', -20.0)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
        
        task_id = generate_task_id()
        update_task_status(task_id, 'pending', 0.0, "音量归一化任务已创建")
        
        # 异步音量归一化
        async def normalize_async():
            try:
                if not PROCESSOR_AVAILABLE:
                    # 模拟处理
                    update_task_status(task_id, 'processing', 0.5, "归一化中...")
                    await asyncio.sleep(1)
                    output_path = file_path.replace('.', '_normalized.')
                else:
                    # 真实处理
                    update_task_status(task_id, 'processing', 0.1, "加载音频...")
                    audio_data, metadata = await audio_processor.load_audio(file_path)
                    
                    update_task_status(task_id, 'processing', 0.5, "归一化处理...")
                    normalized_audio = await audio_processor.normalize_volume(audio_data, target_db)
                    
                    update_task_status(task_id, 'processing', 0.9, "保存音频...")
                    output_path = file_path.replace('.', '_normalized.')
                    await audio_processor.save_audio(normalized_audio, output_path)
                
                update_task_status(task_id, 'completed', 1.0, "归一化完成")
                task_results[task_id] = {'output_file': output_path}
                
            except Exception as e:
                logger.error(f"归一化失败: {e}")
                update_task_status(task_id, 'failed', 0.0, "", str(e))
        
        def run_normalize():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(normalize_async())
            finally:
                loop.close()
        
        executor.submit(run_normalize)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'pending',
                'message': '归一化任务已创建'
            }
        })
        
    except Exception as e:
        logger.error(f"创建归一化任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/mix-background', methods=['POST'])
def mix_background_music():
    """背景音乐混合"""
    try:
        data = request.get_json()
        required_fields = ['voice_file_path', 'music_file_path']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少字段: {field}'
                }), 400
        
        voice_path = data['voice_file_path']
        music_path = data['music_file_path']
        music_volume = data.get('music_volume', 0.3)
        
        for path in [voice_path, music_path]:
            if not os.path.exists(path):
                return jsonify({
                    'success': False,
                    'error': f'文件不存在: {path}'
                }), 404
        
        task_id = generate_task_id()
        update_task_status(task_id, 'pending', 0.0, "背景音乐混合任务已创建")
        
        # 异步背景音乐混合
        async def mix_async():
            try:
                if not PROCESSOR_AVAILABLE:
                    # 模拟处理
                    update_task_status(task_id, 'processing', 0.5, "混合中...")
                    await asyncio.sleep(2)
                    output_path = voice_path.replace('.', '_mixed.')
                else:
                    # 真实处理
                    update_task_status(task_id, 'processing', 0.1, "加载语音...")
                    voice_data, voice_metadata = await audio_processor.load_audio(voice_path)
                    
                    update_task_status(task_id, 'processing', 0.3, "加载音乐...")
                    music_data, music_metadata = await audio_processor.load_audio(music_path)
                    
                    update_task_status(task_id, 'processing', 0.6, "混合音频...")
                    mixed_audio = await audio_processor.mix_background_music(
                        voice_data, music_data, music_volume
                    )
                    
                    update_task_status(task_id, 'processing', 0.9, "保存音频...")
                    output_path = voice_path.replace('.', '_mixed.')
                    await audio_processor.save_audio(mixed_audio, output_path)
                
                update_task_status(task_id, 'completed', 1.0, "混合完成")
                task_results[task_id] = {'output_file': output_path}
                
            except Exception as e:
                logger.error(f"背景音乐混合失败: {e}")
                update_task_status(task_id, 'failed', 0.0, "", str(e))
        
        def run_mix():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(mix_async())
            finally:
                loop.close()
        
        executor.submit(run_mix)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'pending',
                'message': '混合任务已创建'
            }
        })
        
    except Exception as e:
        logger.error(f"创建混合任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/batch-process', methods=['POST'])
def batch_process():
    """批量处理音频"""
    try:
        data = request.get_json()
        if not data or 'files' not in data:
            return jsonify({
                'success': False,
                'error': '缺少文件列表'
            }), 400
        
        files = data['files']
        config = data.get('config', {})
        
        if not isinstance(files, list) or len(files) == 0:
            return jsonify({
                'success': False,
                'error': '文件列表为空'
            }), 400
        
        # 验证文件存在
        for file_path in files:
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'error': f'文件不存在: {file_path}'
                }), 404
        
        batch_task_id = generate_task_id()
        update_task_status(batch_task_id, 'pending', 0.0, f"批量处理任务已创建 ({len(files)}个文件)")
        
        # 异步批量处理
        async def batch_process_async():
            try:
                total_files = len(files)
                completed_files = 0
                results = []
                
                for i, file_path in enumerate(files):
                    update_task_status(
                        batch_task_id, 'processing', 
                        completed_files / total_files, 
                        f"处理文件 {i+1}/{total_files}: {os.path.basename(file_path)}"
                    )
                    
                    try:
                        if PROCESSOR_AVAILABLE:
                            # 加载和处理音频
                            audio_data, metadata = await audio_processor.load_audio(file_path)
                            
                            processing_config = AudioProcessingConfig(
                                enable_noise_reduction=config.get('enable_noise_reduction', True),
                                enable_volume_normalization=config.get('enable_volume_normalization', True),
                                enable_quality_enhancement=config.get('enable_quality_enhancement', True),
                                noise_reduction_strength=config.get('noise_reduction_strength', 0.7),
                                normalization_target=config.get('normalization_target', -20.0)
                            )
                            
                            processed_audio = await audio_processor.process_audio_pipeline(audio_data, processing_config)
                            
                            # 保存处理后的音频
                            output_path = file_path.replace('.', '_batch_processed.')
                            await audio_processor.save_audio(processed_audio, output_path)
                            
                            results.append({
                                'input_file': file_path,
                                'output_file': output_path,
                                'status': 'success'
                            })
                        else:
                            # 模拟处理
                            await asyncio.sleep(0.5)
                            output_path = file_path.replace('.', '_batch_processed.')
                            results.append({
                                'input_file': file_path,
                                'output_file': output_path,
                                'status': 'success'
                            })
                        
                        completed_files += 1
                        
                    except Exception as file_error:
                        logger.error(f"处理文件失败 {file_path}: {file_error}")
                        results.append({
                            'input_file': file_path,
                            'output_file': None,
                            'status': 'failed',
                            'error': str(file_error)
                        })
                        completed_files += 1
                
                update_task_status(batch_task_id, 'completed', 1.0, f"批量处理完成: {completed_files}/{total_files}")
                task_results[batch_task_id] = {
                    'total_files': total_files,
                    'completed_files': completed_files,
                    'results': results
                }
                
            except Exception as e:
                logger.error(f"批量处理失败: {e}")
                update_task_status(batch_task_id, 'failed', 0.0, "", str(e))
        
        def run_batch():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(batch_process_async())
            finally:
                loop.close()
        
        executor.submit(run_batch)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': batch_task_id,
                'status': 'pending',
                'message': f'批量处理任务已创建 ({len(files)}个文件)'
            }
        })
        
    except Exception as e:
        logger.error(f"创建批量处理任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    try:
        if task_id not in task_status:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        status = task_status[task_id].copy()
        
        # 如果任务完成，添加结果
        if status['status'] == 'completed' and task_id in task_results:
            status['result'] = task_results[task_id]
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    try:
        cleanup_old_tasks()  # 清理旧任务
        
        tasks = []
        for task_id, status in task_status.items():
            task_info = status.copy()
            task_info['task_id'] = task_id
            tasks.append(task_info)
        
        # 按时间排序
        tasks.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks,
                'total_count': len(tasks)
            }
        })
        
    except Exception as e:
        logger.error(f"列出任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/download/<task_id>', methods=['GET'])
def download_result(task_id):
    """下载处理结果"""
    try:
        if task_id not in task_status:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        if task_status[task_id]['status'] != 'completed':
            return jsonify({
                'success': False,
                'error': '任务未完成'
            }), 400
        
        if task_id not in task_results:
            return jsonify({
                'success': False,
                'error': '没有可用的结果'
            }), 404
        
        result = task_results[task_id]
        if 'output_file' not in result:
            return jsonify({
                'success': False,
                'error': '没有输出文件'
            }), 404
        
        output_file = result['output_file']
        if not os.path.exists(output_file):
            return jsonify({
                'success': False,
                'error': '输出文件不存在'
            }), 404
        
        return send_file(
            output_file,
            as_attachment=True,
            download_name=os.path.basename(output_file)
        )
        
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        health_info = {
            'status': 'healthy',
            'processor_available': PROCESSOR_AVAILABLE,
            'active_tasks': len([t for t in task_status.values() if t['status'] in ['pending', 'processing']]),
            'total_tasks': len(task_status),
            'executor_threads': executor._threads if hasattr(executor, '_threads') else 0
        }
        
        return jsonify({
            'success': True,
            'data': health_info
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 错误处理
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({
        'success': False,
        'error': '文件太大',
        'max_size': app.config['MAX_CONTENT_LENGTH']
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': '内部服务器错误'
    }), 500

if __name__ == '__main__':
    print("🎵 高级音频处理 Flask API 服务器")
    print("=" * 50)
    print(f"处理器状态: {'可用' if PROCESSOR_AVAILABLE else '模拟模式'}")
    print(f"支持的格式: {', '.join(ALLOWED_EXTENSIONS)}")
    print("可用的API端点:")
    print("  GET  /api/audio/info           - 获取音频处理器信息")
    print("  POST /api/audio/upload         - 上传音频文件")
    print("  POST /api/audio/analyze        - 分析音频文件")
    print("  POST /api/audio/process        - 处理音频文件")
    print("  POST /api/audio/noise-reduction- 噪音消除")
    print("  POST /api/audio/normalize      - 音量归一化")
    print("  POST /api/audio/mix-background - 背景音乐混合")
    print("  POST /api/audio/batch-process  - 批量处理")
    print("  GET  /api/audio/task/<id>      - 获取任务状态")
    print("  GET  /api/audio/tasks          - 列出所有任务")
    print("  GET  /api/audio/download/<id>  - 下载处理结果")
    print("  GET  /api/audio/health         - 健康检查")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8003, debug=True, threaded=True)
