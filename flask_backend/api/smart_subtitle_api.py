"""
智能字幕API接口
提供字幕配置管理和处理功能的REST API
"""
# type: ignore

from flask import Blueprint, request, jsonify
from pathlib import Path
import logging
import asyncio
from typing import Dict, Any, Optional

# 创建蓝图
smart_subtitle_bp = Blueprint('smart_subtitle', __name__, url_prefix='/api/smart-subtitle')

# 获取logger
logger = logging.getLogger(__name__)


@smart_subtitle_bp.route('/config', methods=['GET'])
def get_subtitle_config():
    """获取智能字幕配置"""
    try:
        from core.subtitle_config_loader import SmartSubtitleConfigLoader
        
        # 获取配置目录
        config_dir = Path(__file__).parent.parent / "config_data"
        
        # 加载配置
        loader = SmartSubtitleConfigLoader(config_dir)
        config = loader.get_config()
        status = loader.get_config_summary()
        
        return jsonify({
            "success": True,
            "config": config,
            "status": status
        })
        
    except Exception as e:
        logger.error(f"获取字幕配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@smart_subtitle_bp.route('/config', methods=['POST'])
def update_subtitle_config():
    """更新智能字幕配置"""
    try:
        from core.subtitle_config_loader import SmartSubtitleConfigLoader
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供配置数据"
            }), 400
        
        # 获取配置目录
        config_dir = Path(__file__).parent.parent / "config_data"
        
        # 验证和保存配置
        loader = SmartSubtitleConfigLoader(config_dir)
        
        # 更新配置并验证
        loader.update_config(data, save=False)
        validation_result = loader.validate_config()
        
        if not validation_result.get('is_valid', True):
            return jsonify({
                "success": False,
                "error": "配置验证失败",
                "details": validation_result.get('errors', [])
            }), 400
        
        # 保存配置
        try:
            loader.save_config()
            return jsonify({
                "success": True,
                "message": "配置更新成功"
            })
        except Exception as save_error:
            return jsonify({
                "success": False,
                "error": "配置保存失败"
            }), 500
            
    except Exception as e:
        logger.error(f"更新字幕配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@smart_subtitle_bp.route('/test-split', methods=['POST'])
def test_subtitle_split():
    """测试字幕分割功能"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "请提供待分割的文本"
            }), 400
        
        text = data['text']
        config = data.get('config', {})
        
        # 运行异步分割测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_async_test_split(text, config))
            return jsonify({
                "success": True,
                "result": result
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"测试字幕分割失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


async def _async_test_split(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """异步测试分割功能"""
    try:
        from core.ai_subtitle_splitter import HybridSubtitleSplitter
        from core.subtitle_utils import calc_text_display_weight
        
        # 创建分割器
        splitter = HybridSubtitleSplitter(config)
        
        # 执行分割
        split_result = await splitter.split_subtitle_text(text)
        
        # 获取度量信息
        metrics = splitter.get_splitting_metrics(text, split_result)
        
        # 计算每行的详细信息
        lines_detail = []
        for line in split_result:
            weight = calc_text_display_weight(line)
            lines_detail.append({
                "text": line,
                "length": len(line),
                "weight": weight,
                "is_valid": weight <= config.get("max_length", 75)
            })
        
        return {
            "original_text": text,
            "split_result": split_result,
            "lines_detail": lines_detail,
            "metrics": metrics,
            "processing_method": "hybrid"
        }
        
    except Exception as e:
        logger.error(f"异步分割测试失败: {e}")
        raise


@smart_subtitle_bp.route('/weight-calculator', methods=['POST'])
def calculate_text_weight():
    """计算文本显示权重"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "请提供待计算的文本"
            }), 400
        
        text = data['text']
        
        from core.subtitle_utils import CharacterWeightCalculator, calc_text_display_weight
        
        # 计算总权重
        total_weight = calc_text_display_weight(text)
        
        # 计算字符详情
        calc = CharacterWeightCalculator()
        char_details = []
        
        for i, char in enumerate(text):
            weight = calc.get_char_weight(char)
            char_details.append({
                "char": char,
                "position": i,
                "weight": weight,
                "unicode": ord(char),
                "category": _get_char_category(char)
            })
        
        return jsonify({
            "success": True,
            "text": text,
            "total_weight": total_weight,
            "character_count": len(text),
            "average_weight": total_weight / len(text) if text else 0,
            "char_details": char_details
        })
        
    except Exception as e:
        logger.error(f"计算文本权重失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@smart_subtitle_bp.route('/status', methods=['GET'])
def get_subtitle_status():
    """获取智能字幕功能状态"""
    try:
        from core.subtitle_config_loader import SmartSubtitleConfigLoader
        
        # 获取配置目录
        config_dir = Path(__file__).parent.parent / "config_data"
        
        # 获取状态
        loader = SmartSubtitleConfigLoader(config_dir)
        status = loader.get_config_summary()
        
        # 检查模块可用性
        modules_status = {
            "subtitle_utils": _check_module_available("core.subtitle_utils"),
            "ai_subtitle_splitter": _check_module_available("core.ai_subtitle_splitter"),
            "subtitle_config_loader": _check_module_available("core.subtitle_config_loader")
        }
        
        return jsonify({
            "success": True,
            "config_status": status,
            "modules_status": modules_status,
            "features": {
                "smart_splitting": True,
                "character_weights": True,
                "semantic_splitting": True,
                "ai_splitting": status.get("ai_splitting_available", False),
                "config_management": True
            }
        })
        
    except Exception as e:
        logger.error(f"获取字幕状态失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@smart_subtitle_bp.route('/ai-config', methods=['GET'])
def get_ai_config():
    """获取AI分割配置"""
    try:
        from core.subtitle_config_loader import SmartSubtitleConfigLoader
        
        config_dir = Path(__file__).parent.parent / "config_data"
        loader = SmartSubtitleConfigLoader(config_dir)
        
        # 获取配置
        config = loader.get_config()
        ai_config = config.get('ai', {})
        smart_config = config.get('smart_subtitle', {})
        
        return jsonify({
            "success": True,
            "ai_config": ai_config,
            "ai_enabled": smart_config.get("use_ai_splitting", False),
            "ai_available": bool(ai_config.get("api_key"))
        })
        
    except Exception as e:
        logger.error(f"获取AI配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@smart_subtitle_bp.route('/ai-config', methods=['POST'])
def update_ai_config():
    """更新AI分割配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请提供AI配置数据"
            }), 400
        
        from core.subtitle_config_loader import SmartSubtitleConfigLoader
        
        config_dir = Path(__file__).parent.parent / "config_data"
        loader = SmartSubtitleConfigLoader(config_dir)
        
        # 加载当前配置
        config = loader.get_config()
        smart_config = config.get('smart_subtitle', {})
        
        # 更新AI相关配置
        smart_config["use_ai_splitting"] = data.get("enabled", False)
        if "ai_config" in data:
            smart_config["ai_config"] = data["ai_config"]
        
        # 保存配置
        try:
            loader.update_config({"smart_subtitle": smart_config}, save=True)
            success = True
        except Exception:
            success = False
        
        if success:
            return jsonify({
                "success": True,
                "message": "AI配置更新成功"
            })
        else:
            return jsonify({
                "success": False,
                "error": "AI配置保存失败"
            }), 500
            
    except Exception as e:
        logger.error(f"更新AI配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _get_char_category(char: str) -> str:
    """获取字符类别"""
    import unicodedata
    
    if char.isspace():
        return "space"
    elif char.isdigit():
        return "number"
    elif '\u4e00' <= char <= '\u9fff':
        return "chinese"
    elif ('\u3040' <= char <= '\u309f') or ('\u30a0' <= char <= '\u30ff'):
        return "japanese"
    elif '\uac00' <= char <= '\ud7af':
        return "korean"
    elif unicodedata.category(char).startswith('P'):
        return "punctuation"
    else:
        return "english"


def _check_module_available(module_name: str) -> bool:
    """检查模块是否可用"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


# 错误处理器
@smart_subtitle_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "API端点不存在"
    }), 404


@smart_subtitle_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500


# 注册蓝图的函数
def register_smart_subtitle_routes(app):
    """注册智能字幕路由"""
    app.register_blueprint(smart_subtitle_bp)
    logger.info("智能字幕API路由注册成功")


if __name__ == "__main__":
    # 测试代码
    from flask import Flask
    
    app = Flask(__name__)
    register_smart_subtitle_routes(app)
    
    print("智能字幕API端点:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('smart_subtitle'):
            print(f"  {rule.methods} {rule.rule}")
    
    app.run(debug=True, port=5001)
