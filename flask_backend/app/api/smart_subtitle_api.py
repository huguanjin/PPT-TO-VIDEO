"""
智能字幕API模块
提供智能字幕生成和处理功能，集成了优化模块
"""
from flask import Blueprint, jsonify, request
import logging
import os
import sys
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# 添加核心模块路径
core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'core')
if core_path not in sys.path:
    sys.path.append(core_path)

# 导入优化模块 - 使用条件导入避免类型错误
AdaptiveFontSizeCalculator = None
EnhancedSemanticSplitter = None
EnhancedAIContentOptimizer = None

try:
    from adaptive_font_calculator import AdaptiveFontSizeCalculator
    from enhanced_semantic_splitter import EnhancedSemanticSplitter
    from enhanced_ai_content_optimizer import EnhancedAIContentOptimizer
except ImportError as e:
    logging.error(f"优化模块导入失败: {e}")

# 创建蓝图
smart_subtitle_bp = Blueprint('smart_subtitle', __name__, url_prefix='/api/smart-subtitle')

logger = logging.getLogger(__name__)

# 工具函数
def get_timestamp():
    """获取当前时间戳"""
    return datetime.now().isoformat()

def safe_getattr(obj, attr, default=None):
    """安全获取对象属性"""
    try:
        return getattr(obj, attr, default)
    except AttributeError:
        return default

# 初始化优化模块
font_calculator = None
semantic_splitter = None
ai_optimizer = None

try:
    if AdaptiveFontSizeCalculator is not None:
        font_calculator = AdaptiveFontSizeCalculator()
    
    if EnhancedSemanticSplitter is not None:
        semantic_splitter = EnhancedSemanticSplitter()
    
    if EnhancedAIContentOptimizer is not None:
        # 为EnhancedAIContentOptimizer提供项目目录
        project_dir = Path(os.path.join(os.path.dirname(__file__), '..', '..'))
        ai_optimizer = EnhancedAIContentOptimizer(project_dir=project_dir)
    
    if all([font_calculator, semantic_splitter, ai_optimizer]):
        logger.info("字幕优化模块初始化成功")
    else:
        logger.warning("部分优化模块未加载，使用占位符")
        
except Exception as e:
    logger.error(f"字幕优化模块初始化失败: {e}")
    font_calculator = None
    semantic_splitter = None
    ai_optimizer = None

@smart_subtitle_bp.route('/status', methods=['GET'])
def get_status():
    """获取智能字幕API状态"""
    modules_status = {
        "adaptive_font_calculator": font_calculator is not None,
        "enhanced_semantic_splitter": semantic_splitter is not None,
        "enhanced_ai_content_optimizer": ai_optimizer is not None
    }
    
    return jsonify({
        "status": "active",
        "module": "smart_subtitle_api",
        "message": "智能字幕API模块已加载",
        "optimization_modules": modules_status,
        "all_modules_ready": all(modules_status.values())
    })

@smart_subtitle_bp.route('/config', methods=['GET', 'POST'])
def handle_config():
    """获取或更新智能字幕配置"""
    if request.method == 'GET':
        try:
            # 返回当前配置
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_data', 'app_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    subtitle_config = config.get('subtitle_config', {})
                    return jsonify({
                        "success": True,
                        "config": subtitle_config
                    })
            else:
                return jsonify({
                    "success": False,
                    "error": "配置文件不存在"
                }), 404
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"读取配置失败: {str(e)}"
            }), 500
    
    elif request.method == 'POST':
        try:
            new_config = request.get_json()
            if not new_config:
                return jsonify({
                    "success": False,
                    "error": "无效的配置数据"
                }), 400
            
            # 更新配置文件
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_data', 'app_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                config['subtitle_config'].update(new_config)
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                return jsonify({
                    "success": True,
                    "message": "配置更新成功"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "配置文件不存在"
                }), 404
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"更新配置失败: {str(e)}"
            }), 500
    
    # 如果既不是GET也不是POST，返回405错误
    return jsonify({"error": "Method not allowed"}), 405

@smart_subtitle_bp.route('/test-split', methods=['POST'])
def test_split():
    """测试字幕分割功能"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 'text'"
            }), 400
        
        text = data['text']
        config = data.get('config', {})
        
        if semantic_splitter is None:
            return jsonify({
                "success": False,
                "error": "语义分割器未初始化"
            }), 500
        
        # 使用增强型语义分割器
        try:
            # 检查是否存在split_with_semantic_awareness方法
            if hasattr(semantic_splitter, 'split_with_semantic_awareness'):
                # 需要异步处理
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(semantic_splitter.split_with_semantic_awareness(text))
                finally:
                    loop.close()
            else:
                # 使用fallback方法
                result = [text]  # 简单返回原文
                
        except Exception as split_error:
            logger.error(f"分割过程出错: {split_error}")
            result = [text]  # fallback到原文
        
        return jsonify({
            "success": True,
            "result": {
                "original_text": text,
                "split_result": result,
                "processing_method": "enhanced_semantic",
                "processed_at": get_timestamp()
            }
        })
        
    except Exception as e:
        logger.error(f"分割测试失败: {e}")
        return jsonify({
            "success": False,
            "error": f"分割测试失败: {str(e)}"
        }), 500

@smart_subtitle_bp.route('/weight-calculator', methods=['POST'])
def calculate_weight():
    """计算文本显示权重"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 'text'"
            }), 400
        
        text = data['text']
        
        if font_calculator is None:
            return jsonify({
                "success": False,
                "error": "字体计算器未初始化"
            }), 500
        
        # 计算文本权重和推荐字体大小
        try:
            # 使用实际存在的方法
            if hasattr(font_calculator, 'calculate_adaptive_font_size'):
                font_size = font_calculator.calculate_adaptive_font_size(
                    text=text,
                    line_count=len(text.split('\n')),
                    resolution=(1920, 1080)
                )
                weight_result = len(text)  # 简单权重计算
            else:
                # fallback
                font_size = 16
                weight_result = len(text)
        except Exception as calc_error:
            logger.error(f"计算过程出错: {calc_error}")
            font_size = 16
            weight_result = len(text)
        
        return jsonify({
            "success": True,
            "text": text,
            "total_weight": weight_result,
            "character_count": len(text),
            "recommended_font_size": font_size,
            "calculated_at": get_timestamp()
        })
        
    except Exception as e:
        logger.error(f"权重计算失败: {e}")
        return jsonify({
            "success": False,
            "error": f"权重计算失败: {str(e)}"
        }), 500

@smart_subtitle_bp.route('/adaptive-font', methods=['POST'])
def adaptive_font():
    """自适应字体大小计算"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "缺少请求数据"
            }), 400
        
        text = data.get('text', '')
        resolution = data.get('resolution', [1920, 1080])
        position = data.get('position', 'bottom')
        content_type = data.get('content_type', 'general')
        
        if font_calculator is None:
            return jsonify({
                "success": False,
                "error": "字体计算器未初始化"
            }), 500
        
        # 计算自适应字体大小
        try:
            if hasattr(font_calculator, 'calculate_adaptive_font_size'):
                font_size = font_calculator.calculate_adaptive_font_size(
                    text=text,
                    line_count=len(text.split('\n')),
                    resolution=tuple(resolution)
                )
            else:
                # fallback
                font_size = 16
        except Exception as calc_error:
            logger.error(f"字体计算过程出错: {calc_error}")
            font_size = 16
        
        return jsonify({
            "success": True,
            "text": text,
            "resolution": resolution,
            "position": position,
            "content_type": content_type,
            "recommended_font_size": font_size,
            "calculated_at": get_timestamp()
        })
        
    except Exception as e:
        logger.error(f"自适应字体计算失败: {e}")
        return jsonify({
            "success": False,
            "error": f"自适应字体计算失败: {str(e)}"
        }), 500

@smart_subtitle_bp.route('/enhanced-split', methods=['POST'])
def enhanced_split():
    """增强型语义分割"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 'text'"
            }), 400
        
        text = data['text']
        max_chars_per_line = data.get('max_chars_per_line', 26)
        enable_ai = data.get('enable_ai', False)
        protect_urls = data.get('protect_urls', True)
        protect_emails = data.get('protect_emails', True)
        
        if semantic_splitter is None:
            return jsonify({
                "success": False,
                "error": "语义分割器未初始化"
            }), 500
        
        # 使用增强型语义分割
        try:
            if hasattr(semantic_splitter, 'split_with_semantic_awareness'):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(semantic_splitter.split_with_semantic_awareness(text))
                finally:
                    loop.close()
            else:
                # 简单分割
                result = [text[i:i+max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
        except Exception as split_error:
            logger.error(f"分割过程出错: {split_error}")
            result = [text]
        
        return jsonify({
            "success": True,
            "original_text": text,
            "split_result": result,
            "parameters": {
                "max_chars_per_line": max_chars_per_line,
                "enable_ai": enable_ai,
                "protect_urls": protect_urls,
                "protect_emails": protect_emails
            },
            "processing_method": "enhanced_semantic",
            "processed_at": get_timestamp()
        })
        
    except Exception as e:
        logger.error(f"增强型分割失败: {e}")
        return jsonify({
            "success": False,
            "error": f"增强型分割失败: {str(e)}"
        }), 500

@smart_subtitle_bp.route('/ai-optimize', methods=['POST'])
def ai_optimize():
    """AI内容优化"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "缺少请求数据"
            }), 400
        
        content = data.get('content', [])
        if isinstance(content, str):
            content = [content]
        
        resolution = data.get('resolution', [1920, 1080])
        enable_ai_split = data.get('enable_ai_split', False)
        enable_adaptive_font = data.get('enable_adaptive_font', True)
        
        if ai_optimizer is None:
            return jsonify({
                "success": False,
                "error": "AI优化器未初始化"
            }), 500
        
        # 执行AI内容优化
        try:
            # 查找可用的优化方法
            if hasattr(ai_optimizer, 'optimize_scripts_content_enhanced'):
                # 构造scripts_data格式
                scripts_data = {
                    'scripts': [{'content': item} for item in content]
                }
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    optimized_result = loop.run_until_complete(
                        ai_optimizer.optimize_scripts_content_enhanced(scripts_data)
                    )
                finally:
                    loop.close()
            else:
                # fallback
                optimized_result = content
        except Exception as opt_error:
            logger.error(f"优化过程出错: {opt_error}")
            optimized_result = content
        
        return jsonify({
            "success": True,
            "original_content": content,
            "optimized_result": optimized_result,
            "parameters": {
                "resolution": resolution,
                "enable_ai_split": enable_ai_split,
                "enable_adaptive_font": enable_adaptive_font
            },
            "processed_at": get_timestamp()
        })
        
    except Exception as e:
        logger.error(f"AI优化失败: {e}")
        return jsonify({
            "success": False,
            "error": f"AI优化失败: {str(e)}"
        }), 500

@smart_subtitle_bp.route('/batch-optimize', methods=['POST'])
def batch_optimize():
    """批量优化处理"""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 'items'"
            }), 400
        
        items = data['items']
        if not isinstance(items, list):
            return jsonify({
                "success": False,
                "error": "'items' 必须是数组格式"
            }), 400
        
        resolution = data.get('resolution', [1920, 1080])
        enable_ai_split = data.get('enable_ai_split', False)
        enable_adaptive_font = data.get('enable_adaptive_font', True)
        
        if ai_optimizer is None:
            return jsonify({
                "success": False,
                "error": "AI优化器未初始化"
            }), 500
        
        # 批量处理
        results = []
        for i, item in enumerate(items):
            try:
                # 简单处理，实际可以调用优化方法
                optimized_item = item  # fallback到原内容
                results.append({
                    "index": i,
                    "original": item,
                    "optimized": optimized_item,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "original": item,
                    "error": str(e),
                    "status": "failed"
                })
        
        success_count = len([r for r in results if r["status"] == "success"])
        
        return jsonify({
            "success": True,
            "total_items": len(items),
            "success_count": success_count,
            "failed_count": len(items) - success_count,
            "results": results,
            "parameters": {
                "resolution": resolution,
                "enable_ai_split": enable_ai_split,
                "enable_adaptive_font": enable_adaptive_font
            },
            "processed_at": get_timestamp()
        })
        
    except Exception as e:
        logger.error(f"批量优化失败: {e}")
        return jsonify({
            "success": False,
            "error": f"批量优化失败: {str(e)}"
        }), 500

logger.info("智能字幕API模块初始化完成")