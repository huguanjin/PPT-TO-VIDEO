"""
调试API - 用于检查类和方法的可用性
"""
from flask import Blueprint, jsonify
import inspect
import sys
from pathlib import Path

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/check-classes', methods=['GET'])
def check_classes():
    """检查关键类的方法"""
    result = {
        'python_path': sys.path,
        'current_dir': str(Path.cwd()),
        'classes': {}
    }
    
    try:
        # 检查TTSGenerator
        from core.step02_tts_generator import TTSGenerator
        tts_methods = [method for method in dir(TTSGenerator) if not method.startswith('_')]
        result['classes']['TTSGenerator'] = {
            'available': True,
            'methods': tts_methods,
            'has_generate_audio': 'generate_audio' in tts_methods,
            'file_path': inspect.getfile(TTSGenerator)
        }
    except Exception as e:
        result['classes']['TTSGenerator'] = {
            'available': False,
            'error': str(e)
        }
    
    try:
        # 检查SubtitleGenerator
        from core.step04_subtitle_generator import SubtitleGenerator
        sub_methods = [method for method in dir(SubtitleGenerator) if not method.startswith('_')]
        result['classes']['SubtitleGenerator'] = {
            'available': True,
            'methods': sub_methods,
            'has_generate_subtitles': 'generate_subtitles' in sub_methods,
            'file_path': inspect.getfile(SubtitleGenerator)
        }
    except Exception as e:
        result['classes']['SubtitleGenerator'] = {
            'available': False,
            'error': str(e)
        }
    
    try:
        # 检查工作流执行器
        from core.enhanced_workflow_executor import EnhancedWorkflowExecutor
        executor_methods = [method for method in dir(EnhancedWorkflowExecutor) if not method.startswith('_')]
        result['classes']['EnhancedWorkflowExecutor'] = {
            'available': True,
            'methods': executor_methods,
            'file_path': inspect.getfile(EnhancedWorkflowExecutor)
        }
    except Exception as e:
        result['classes']['EnhancedWorkflowExecutor'] = {
            'available': False,
            'error': str(e)
        }
    
    # 检查核心文件是否存在
    backend_root = Path.cwd()
    core_files = [
        'core/step02_tts_generator.py',
        'core/step04_subtitle_generator.py',
        'core/enhanced_workflow_executor.py'
    ]
    
    result['files'] = {}
    for file_path in core_files:
        full_path = backend_root / file_path
        if full_path.exists():
            result['files'][file_path] = {
                'exists': True,
                'size': full_path.stat().st_size,
                'modified': str(full_path.stat().st_mtime)
            }
        else:
            result['files'][file_path] = {'exists': False}
    
    return jsonify(result)

@debug_bp.route('/reload-modules', methods=['POST'])
def reload_modules():
    """重新加载核心模块"""
    try:
        # 清除模块缓存
        modules_to_reload = [
            'core.step02_tts_generator',
            'core.step04_subtitle_generator',
            'core.enhanced_workflow_executor'
        ]
        
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # 重新导入
        from core.step02_tts_generator import TTSGenerator
        from core.step04_subtitle_generator import SubtitleGenerator
        from core.enhanced_workflow_executor import EnhancedWorkflowExecutor
        
        return jsonify({
            'success': True,
            'message': '模块重新加载成功',
            'reloaded_modules': modules_to_reload
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
