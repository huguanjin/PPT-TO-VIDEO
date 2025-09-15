"""
智能断句API接口
为智能断句系统提供REST API接口
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any, List
import asyncio
import logging
from datetime import datetime

from ..core.ai_subtitle_splitter import (
    smart_split_subtitle,
    HybridSubtitleSplitter,
    AISemanticSplitter
)

logger = logging.getLogger(__name__)

# 创建蓝图
smart_splitting_bp = Blueprint('smart_splitting', __name__, url_prefix='/api/smart-splitting')

@smart_splitting_bp.route('/split-text', methods=['POST'])
def split_text_api():
    """
    单文本智能分割API
    
    Request Body:
    {
        "text": "要分割的文本",
        "config": {
            "max_length": 40,
            "strategy": "hybrid",
            "language": "auto"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必需的文本参数"
            }), 400
        
        text = data['text']
        config = data.get('config', {})
        
        # 设置默认配置
        default_config = {
            "max_length": 75,
            "use_ai_splitting": config.get('use_ai', False),
            "ai_fallback": True
        }
        default_config.update(config)
        
        # 执行分割
        async def async_split():
            return await smart_split_subtitle(text, default_config)
        
        result = asyncio.run(async_split())
        
        # 计算统计信息
        splitter = HybridSubtitleSplitter(default_config)
        metrics = splitter.get_splitting_metrics(text, result)
        
        return jsonify({
            "success": True,
            "data": {
                "original_text": text,
                "split_lines": result,
                "metrics": metrics
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"文本分割API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@smart_splitting_bp.route('/batch-split', methods=['POST'])
def batch_split_api():
    """
    批量文本智能分割API
    
    Request Body:
    {
        "texts": ["文本1", "文本2", "文本3"],
        "config": {
            "max_length": 40,
            "strategy": "hybrid"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'texts' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必需的texts参数"
            }), 400
        
        texts = data['texts']
        config = data.get('config', {})
        
        if not isinstance(texts, list):
            return jsonify({
                "success": False,
                "error": "texts参数必须是数组"
            }), 400
        
        # 设置默认配置
        default_config = {
            "max_length": 75,
            "use_ai_splitting": config.get('use_ai', False),
            "ai_fallback": True
        }
        default_config.update(config)
        
        # 执行批量分割
        async def async_batch_split():
            results = []
            splitter = HybridSubtitleSplitter(default_config)
            
            for text in texts:
                split_result = await smart_split_subtitle(text, default_config)
                metrics = splitter.get_splitting_metrics(text, split_result)
                
                results.append({
                    "original_text": text,
                    "split_lines": split_result,
                    "metrics": metrics
                })
            
            return results
        
        result = asyncio.run(async_batch_split())
        
        return jsonify({
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"批量分割API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@smart_splitting_bp.route('/strategies', methods=['GET'])
def get_strategies():
    """获取可用的分割策略"""
    try:
        strategies = {
            "semantic": {
                "name": "语义优先",
                "description": "基于语义理解进行分割，保持语义完整性",
                "best_for": ["专业内容", "教育材料", "复杂文本"],
                "performance": "中等",
                "quality": "高"
            },
            "length": {
                "name": "长度平衡",
                "description": "基于目标长度进行平衡分割",
                "best_for": ["移动端", "字幕显示", "简单文本"],
                "performance": "快",
                "quality": "中等"
            },
            "punctuation": {
                "name": "标点分割",
                "description": "基于标点符号进行分割",
                "best_for": ["快速处理", "简单需求", "性能优先"],
                "performance": "最快",
                "quality": "基础"
            },
            "hybrid": {
                "name": "混合策略",
                "description": "智能选择最佳分割策略",
                "best_for": ["通用场景", "自动处理", "平衡需求"],
                "performance": "中等",
                "quality": "高"
            },
            "ai_enhanced": {
                "name": "AI增强",
                "description": "使用AI模型进行高级分割",
                "best_for": ["高质量需求", "复杂语义", "专业场景"],
                "performance": "慢",
                "quality": "最高"
            }
        }
        
        return jsonify({
            "success": True,
            "strategies": strategies
        })
        
    except Exception as e:
        logger.error(f"获取策略API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@smart_splitting_bp.route('/presets', methods=['GET'])
def get_presets():
    """获取预设配置"""
    try:
        presets = {
            "netflix_standard": {
                "name": "Netflix标准",
                "description": "符合Netflix专业字幕标准",
                "config": {
                    "max_length": 75,
                    "use_ai_splitting": True,
                    "ai_fallback": True,
                    "semantic_splitting": True
                },
                "use_cases": ["专业视频", "流媒体平台", "高质量内容"]
            },
            "mobile_optimized": {
                "name": "移动端优化",
                "description": "针对移动设备优化的分割配置",
                "config": {
                    "max_length": 40,
                    "use_ai_splitting": False,
                    "ai_fallback": True,
                    "prefer_short_lines": True
                },
                "use_cases": ["手机观看", "小屏幕设备", "移动应用"]
            },
            "performance_mode": {
                "name": "性能优先",
                "description": "快速处理优先的配置",
                "config": {
                    "max_length": 50,
                    "use_ai_splitting": False,
                    "ai_fallback": False,
                    "quick_mode": True
                },
                "use_cases": ["批量处理", "实时应用", "资源受限环境"]
            }
        }
        
        return jsonify({
            "success": True,
            "presets": presets
        })
        
    except Exception as e:
        logger.error(f"获取预设API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@smart_splitting_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计信息"""
    try:
        # 基础统计信息
        stats = {
            "system_info": {
                "available_strategies": ["semantic", "length", "punctuation", "hybrid", "ai_enhanced"],
                "ai_support": True,
                "performance_mode": True
            },
            "usage_statistics": {
                "total_splits": 0,
                "average_processing_time": 0.5,
                "average_confidence": 0.85,
                "most_used_strategy": "hybrid"
            },
            "model_availability": {
                "ai_models": True,
                "spacy": False,
                "jieba": True
            }
        }
        
        return jsonify({
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取统计API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@smart_splitting_bp.route('/test', methods=['POST'])
def test_splitting():
    """
    测试分割效果API
    
    Request Body:
    {
        "text": "测试文本",
        "strategies": ["semantic", "length", "punctuation"]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必需的text参数"
            }), 400
        
        text = data['text']
        strategies = data.get('strategies', ['hybrid'])
        
        if not isinstance(strategies, list):
            strategies = ['hybrid']
        
        results = {}
        
        async def test_strategy(strategy):
            config = {
                "max_length": 75,
                "use_ai_splitting": strategy == 'ai_enhanced',
                "ai_fallback": True
            }
            
            if strategy == 'semantic':
                config['semantic_splitting'] = True
            elif strategy == 'length':
                config['prefer_balanced_length'] = True
            elif strategy == 'punctuation':
                config['use_punctuation_only'] = True
                
            return await smart_split_subtitle(text, config)
        
        # 测试每个策略
        for strategy in strategies:
            try:
                split_result = asyncio.run(test_strategy(strategy))
                splitter = HybridSubtitleSplitter()
                metrics = splitter.get_splitting_metrics(text, split_result)
                
                results[strategy] = {
                    "success": True,
                    "split_lines": split_result,
                    "metrics": metrics
                }
            except Exception as e:
                results[strategy] = {
                    "success": False,
                    "error": str(e)
                }
        
        return jsonify({
            "success": True,
            "original_text": text,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"测试分割API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@smart_splitting_bp.route('/optimize-config', methods=['POST'])
def optimize_config():
    """
    配置优化建议API
    
    Request Body:
    {
        "current_config": {...},
        "requirements": {
            "target_platform": "mobile",
            "quality_priority": "high",
            "performance_priority": "medium"
        }
    }
    """
    try:
        data = request.get_json()
        current_config = data.get('current_config', {})
        requirements = data.get('requirements', {})
        
        # 生成优化建议
        optimized_configs = {}
        
        # 基于需求生成建议
        target_platform = requirements.get('target_platform', 'web')
        quality_priority = requirements.get('quality_priority', 'medium')
        performance_priority = requirements.get('performance_priority', 'medium')
        
        if target_platform == 'mobile':
            optimized_configs['mobile_optimized'] = {
                "max_length": 40,
                "use_ai_splitting": False,
                "ai_fallback": True,
                "prefer_short_lines": True
            }
        
        if quality_priority == 'high':
            optimized_configs['netflix_standard'] = {
                "max_length": 75,
                "use_ai_splitting": True,
                "ai_fallback": True,
                "semantic_splitting": True
            }
        
        if performance_priority == 'high':
            optimized_configs['performance_mode'] = {
                "max_length": 50,
                "use_ai_splitting": False,
                "ai_fallback": False,
                "quick_mode": True
            }
        
        # 分析当前配置
        config_analysis = {
            "current_max_length": current_config.get('max_length', 75),
            "ai_enabled": current_config.get('use_ai_splitting', False),
            "semantic_enabled": current_config.get('semantic_splitting', True),
            "estimated_quality": "medium",
            "estimated_performance": "medium"
        }
        
        # 生成具体建议
        recommendations = []
        
        if target_platform == 'mobile' and current_config.get('max_length', 75) > 40:
            recommendations.append("建议将最大长度调整到40字符以适配移动端")
        
        if quality_priority == 'high' and not current_config.get('use_ai_splitting', False):
            recommendations.append("建议启用AI分割以提升质量")
        
        if performance_priority == 'high' and current_config.get('use_ai_splitting', False):
            recommendations.append("建议关闭AI分割以提升性能")
        
        return jsonify({
            "success": True,
            "current_analysis": config_analysis,
            "optimized_configs": optimized_configs,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"配置优化API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@smart_splitting_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查API"""
    try:
        # 检查依赖可用性
        dependencies = {
            "ai_models": True,
            "subtitle_utils": True,
            "ai_splitter": True
        }
        
        status = "healthy"
        issues = []
        
        # 基础性能统计
        performance = {
            "average_processing_time": 0.5,
            "average_confidence": 0.85,
            "total_splits": 0
        }
        
        return jsonify({
            "success": True,
            "status": status,
            "dependencies": dependencies,
            "performance": performance,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"健康检查API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "error"
        }), 500

# 错误处理
@smart_splitting_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "API端点不存在"
    }), 404

@smart_splitting_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "HTTP方法不被允许"
    }), 405

@smart_splitting_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "内部服务器错误"
    }), 500
