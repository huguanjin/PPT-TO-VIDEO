"""
Enhanced Netflix字幕API V2 - Phase 2核心功能集成
升级现有字幕生成API，集成Netflix V2标准功能
确保向后兼容性的同时提供Netflix级字幕处理能力
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import json

from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError

# Phase 1 Netflix核心组件 (V2版本)
try:
    from flask_backend.core.netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from flask_backend.core.netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2
    from flask_backend.core.netflix_semantic_splitter_v2 import NetflixSemanticSplitterV2, SemanticSplitConfig
    from flask_backend.core.netflix_quality_validator_v2 import NetflixQualityValidatorV2, ValidationLevel
    from flask_backend.core.netflix_api_integration import NetflixSubtitleProcessor
except ImportError:
    # 备用导入路径
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent / "core"))
    from netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2
    from netflix_semantic_splitter_v2 import NetflixSemanticSplitterV2, SemanticSplitConfig
    from netflix_quality_validator_v2 import NetflixQualityValidatorV2, ValidationLevel
    from netflix_api_integration import NetflixSubtitleProcessor

# 现有字幕生成器
try:
    from flask_backend.core.step04_subtitle_generator import SubtitleGenerator
    from flask_backend.core.step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator
except ImportError:
    SubtitleGenerator = None
    EnhancedSubtitleGenerator = None

logger = logging.getLogger(__name__)

# 创建Blueprint
enhanced_netflix_bp = Blueprint('enhanced_netflix_subtitle', __name__, url_prefix='/api/v2/netflix-subtitle')


class EnhancedNetflixSubtitleAPI:
    """
    Enhanced Netflix字幕API V2
    集成Phase 1技术基础建设成果，提供Netflix级字幕处理API
    """
    
    def __init__(self):
        self.netflix_processor = None
        self.legacy_generator = None
        self.enhanced_generator = None
        self._init_components()
    
    def _init_components(self):
        """初始化所有组件"""
        try:
            # 初始化Netflix处理器
            self.netflix_processor = NetflixSubtitleProcessor()
            logger.info("Netflix V2处理器初始化成功")
            
            # 初始化传统字幕生成器（向后兼容）
            if SubtitleGenerator:
                # 项目目录需要从配置或环境变量获取
                project_dir = Path.cwd()  # 临时解决方案
                self.legacy_generator = SubtitleGenerator(project_dir)
                logger.info("传统字幕生成器初始化成功")
            
            if EnhancedSubtitleGenerator:
                project_dir = Path.cwd()  # 临时解决方案
                self.enhanced_generator = EnhancedSubtitleGenerator(project_dir)
                logger.info("增强字幕生成器初始化成功")
                
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            # 确保至少有基本的Netflix处理器
            if self.netflix_processor is None:
                self.netflix_processor = NetflixSubtitleProcessor()
            logger.warning("使用备用Netflix处理器")
    
    def process_subtitle_v2(self, text: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理字幕文本 - V2 API
        
        Args:
            text: 字幕文本
            config: 处理配置
            
        Returns:
            处理结果字典
        """
        try:
            # 确保Netflix处理器可用
            if self.netflix_processor is None:
                raise RuntimeError("Netflix处理器未初始化")
            
            # 默认配置
            default_config = {
                "style_preset": "videolingo_netflix",
                "enable_splitting": True,
                "enable_validation": True,
                "output_format": ["ass", "webvtt", "srt"]
            }
            
            if config:
                default_config.update(config)
            
            # 使用Netflix V2处理器
            result = self.netflix_processor.process_subtitle(
                text, 
                default_config["style_preset"]
            )
            
            # 增强结果格式
            enhanced_result = {
                "api_version": "v2",
                "processor_type": "netflix_v2",
                "processing_time": datetime.now().isoformat(),
                "input_text": text,
                "config": default_config,
                "netflix_result": result,
                "legacy_compatible": True
            }
            
            # 如果需要输出多种格式
            if "output_format" in default_config:
                formats = default_config["output_format"]
                enhanced_result["output_formats"] = {}
                
                for fmt in formats:
                    if fmt in ["ass", "webvtt"]:
                        # 从Netflix处理器获取格式化样式
                        if fmt == "ass" and "style_strings" in result:
                            enhanced_result["output_formats"]["ass"] = result["style_strings"]["ass"]
                        elif fmt == "webvtt" and "style_strings" in result:
                            enhanced_result["output_formats"]["webvtt"] = result["style_strings"]["webvtt"]
                    elif fmt == "srt":
                        # 生成SRT格式（简化版）
                        enhanced_result["output_formats"]["srt"] = self._generate_srt_format(result)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"V2字幕处理失败: {e}")
            return {
                "api_version": "v2",
                "status": "error",
                "error_message": str(e),
                "input_text": text
            }
    
    def batch_process_v2(self, texts: List[str], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        批量处理字幕文本 - V2 API
        
        Args:
            texts: 字幕文本列表
            config: 处理配置
            
        Returns:
            批量处理结果
        """
        try:
            # 确保Netflix处理器可用
            if self.netflix_processor is None:
                raise RuntimeError("Netflix处理器未初始化")
                
            batch_config = config or {}
            batch_config.setdefault("style_preset", "videolingo_netflix")
            
            # 使用Netflix处理器批量处理
            batch_results = self.netflix_processor.batch_process_subtitles(
                texts, 
                batch_config["style_preset"]
            )
            
            # 统计信息
            total_count = len(texts)
            success_count = sum(1 for r in batch_results if r.get("status") == "success")
            error_count = total_count - success_count
            
            # 聚合质量评分
            quality_scores = [r["validation"]["total_score"] for r in batch_results 
                            if r.get("status") == "success" and "validation" in r]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            return {
                "api_version": "v2",
                "batch_processing": True,
                "statistics": {
                    "total_count": total_count,
                    "success_count": success_count,
                    "error_count": error_count,
                    "success_rate": success_count / total_count if total_count > 0 else 0,
                    "average_quality_score": avg_quality
                },
                "results": batch_results,
                "processing_time": datetime.now().isoformat(),
                "config": batch_config
            }
            
        except Exception as e:
            logger.error(f"V2批量处理失败: {e}")
            return {
                "api_version": "v2",
                "status": "error",
                "error_message": str(e)
            }
    
    def validate_netflix_compliance_v2(self, text: str) -> Dict[str, Any]:
        """
        Netflix标准兼容性验证 - V2 API
        
        Args:
            text: 字幕文本
            
        Returns:
            兼容性验证结果
        """
        try:
            # 确保Netflix处理器可用
            if self.netflix_processor is None:
                raise RuntimeError("Netflix处理器未初始化")
                
            result = self.netflix_processor.validate_netflix_compliance(text)
            
            return {
                "api_version": "v2",
                "validation_type": "netflix_compliance",
                "input_text": text,
                "result": result,
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"V2兼容性验证失败: {e}")
            return {
                "api_version": "v2",
                "status": "error",
                "error_message": str(e)
            }
    
    def get_style_presets_v2(self) -> Dict[str, Any]:
        """
        获取可用样式预设 - V2 API
        
        Returns:
            样式预设信息
        """
        try:
            # 确保Netflix处理器可用
            if self.netflix_processor is None:
                raise RuntimeError("Netflix处理器未初始化")
                
            result = self.netflix_processor.get_available_styles()
            
            return {
                "api_version": "v2",
                "feature": "style_presets",
                "result": result,
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"V2样式预设获取失败: {e}")
            return {
                "api_version": "v2",
                "status": "error",
                "error_message": str(e)
            }
    
    def get_processing_stats_v2(self) -> Dict[str, Any]:
        """
        获取处理器统计信息 - V2 API
        
        Returns:
            统计信息
        """
        try:
            # 确保Netflix处理器可用
            if self.netflix_processor is None:
                raise RuntimeError("Netflix处理器未初始化")
                
            result = self.netflix_processor.get_processing_stats()
            
            return {
                "api_version": "v2",
                "feature": "processing_stats",
                "result": result,
                "processing_time": datetime.now().isoformat(),
                "api_capabilities": {
                    "netflix_v2_integration": True,
                    "legacy_compatibility": bool(self.legacy_generator),
                    "enhanced_mode": bool(self.enhanced_generator),
                    "batch_processing": True,
                    "multiple_formats": ["ass", "webvtt", "srt"],
                    "real_time_validation": True
                }
            }
            
        except Exception as e:
            logger.error(f"V2统计信息获取失败: {e}")
            return {
                "api_version": "v2",
                "status": "error",
                "error_message": str(e)
            }
    
    def _generate_srt_format(self, netflix_result: Dict[str, Any]) -> str:
        """
        生成SRT格式字幕 (简化版本)
        
        Args:
            netflix_result: Netflix处理结果
            
        Returns:
            SRT格式字符串
        """
        try:
            if "split_result" not in netflix_result:
                return ""
            
            segments = netflix_result["split_result"]["segments"]
            srt_content = ""
            
            # 为每个分段生成SRT条目（使用默认时间）
            for i, segment in enumerate(segments, 1):
                start_time = f"00:00:{i*2:02d},000"  # 简化时间计算
                end_time = f"00:00:{i*2+2:02d},000"
                
                srt_content += f"{i}\n"
                srt_content += f"{start_time} --> {end_time}\n"
                srt_content += f"{segment}\n\n"
            
            return srt_content.strip()
            
        except Exception as e:
            logger.error(f"SRT格式生成失败: {e}")
            return ""


# 全局API实例
api_instance = EnhancedNetflixSubtitleAPI()


# API路由定义
@enhanced_netflix_bp.route('/process', methods=['POST'])
def process_subtitle():
    """处理单条字幕文本"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            raise BadRequest("缺少必要的'text'参数")
        
        text = data['text']
        config = data.get('config', {})
        
        result = api_instance.process_subtitle_v2(text, config)
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({"error": str(e), "api_version": "v2"}), 400
    except Exception as e:
        logger.error(f"处理字幕API错误: {e}")
        return jsonify({"error": "内部服务器错误", "api_version": "v2"}), 500


@enhanced_netflix_bp.route('/batch-process', methods=['POST'])
def batch_process_subtitles():
    """批量处理字幕文本"""
    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            raise BadRequest("缺少必要的'texts'参数")
        
        texts = data['texts']
        if not isinstance(texts, list):
            raise BadRequest("'texts'参数必须是列表")
        
        config = data.get('config', {})
        
        result = api_instance.batch_process_v2(texts, config)
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({"error": str(e), "api_version": "v2"}), 400
    except Exception as e:
        logger.error(f"批量处理字幕API错误: {e}")
        return jsonify({"error": "内部服务器错误", "api_version": "v2"}), 500


@enhanced_netflix_bp.route('/validate-compliance', methods=['POST'])
def validate_netflix_compliance():
    """Netflix标准兼容性验证"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            raise BadRequest("缺少必要的'text'参数")
        
        text = data['text']
        
        result = api_instance.validate_netflix_compliance_v2(text)
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({"error": str(e), "api_version": "v2"}), 400
    except Exception as e:
        logger.error(f"兼容性验证API错误: {e}")
        return jsonify({"error": "内部服务器错误", "api_version": "v2"}), 500


@enhanced_netflix_bp.route('/style-presets', methods=['GET'])
def get_style_presets():
    """获取可用样式预设"""
    try:
        result = api_instance.get_style_presets_v2()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"样式预设API错误: {e}")
        return jsonify({"error": "内部服务器错误", "api_version": "v2"}), 500


@enhanced_netflix_bp.route('/stats', methods=['GET'])
def get_processing_stats():
    """获取处理器统计信息"""
    try:
        result = api_instance.get_processing_stats_v2()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"统计信息API错误: {e}")
        return jsonify({"error": "内部服务器错误", "api_version": "v2"}), 500


@enhanced_netflix_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        return jsonify({
            "api_version": "v2",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "netflix_processor": api_instance.netflix_processor is not None,
                "legacy_generator": api_instance.legacy_generator is not None,
                "enhanced_generator": api_instance.enhanced_generator is not None
            }
        })
        
    except Exception as e:
        logger.error(f"健康检查API错误: {e}")
        return jsonify({
            "api_version": "v2",
            "status": "unhealthy",
            "error": str(e)
        }), 500


# 向后兼容性路由 - 映射到V1 API格式
@enhanced_netflix_bp.route('/v1/split', methods=['POST'])
def legacy_split_compatibility():
    """V1 API兼容性接口 - 分割功能"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            raise BadRequest("缺少必要的'text'参数")
        
        text = data['text']
        
        # 使用V2处理器但返回V1格式
        v2_result = api_instance.process_subtitle_v2(text)
        
        # 转换为V1格式
        if v2_result.get("status") == "error":
            return jsonify({
                "success": False,
                "error": v2_result.get("error_message", "未知错误")
            }), 500
        
        netflix_data = v2_result.get("netflix_result", {})
        split_data = netflix_data.get("split_result", {})
        
        return jsonify({
            "success": True,
            "segments": split_data.get("segments", []),
            "segment_count": split_data.get("segment_count", 0),
            "quality_score": split_data.get("quality_score", 0),
            "netflix_compliant": split_data.get("netflix_compliant", False)
        })
        
    except BadRequest as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"V1兼容性API错误: {e}")
        return jsonify({"success": False, "error": "内部服务器错误"}), 500


# 注册蓝图到应用
def register_enhanced_netflix_api(app):
    """注册Enhanced Netflix字幕API到Flask应用"""
    try:
        app.register_blueprint(enhanced_netflix_bp)
        logger.info("Enhanced Netflix字幕API V2注册成功")
        return True
    except Exception as e:
        logger.error(f"Enhanced Netflix字幕API V2注册失败: {e}")
        return False


if __name__ == "__main__":
    # 测试API功能
    print("🧪 Enhanced Netflix字幕API V2测试")
    print("=" * 50)
    
    # 创建API实例
    test_api = EnhancedNetflixSubtitleAPI()
    
    # 测试字幕处理
    test_text = "这是一个Enhanced Netflix字幕API V2的测试示例，集成了Phase 1的所有技术成果！"
    result = test_api.process_subtitle_v2(test_text)
    
    print(f"测试文本: {test_text}")
    print(f"API版本: {result['api_version']}")
    print(f"处理器类型: {result['processor_type']}")
    print(f"兼容性: {result['legacy_compatible']}")
    
    if 'netflix_result' in result:
        netflix_data = result['netflix_result']
        split_data = netflix_data.get('split_result', {})
        print(f"分割段数: {split_data.get('segment_count', 0)}")
        print(f"Netflix兼容: {split_data.get('netflix_compliant', False)}")
        print(f"质量评分: {netflix_data.get('validation', {}).get('total_score', 0)}")
    
    print("\n✅ Enhanced Netflix字幕API V2测试完成！")