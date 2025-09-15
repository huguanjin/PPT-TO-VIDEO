"""
多语言支持系统 REST API
任务3.2: 提供完整的多语言字幕处理API接口
"""

from flask import Blueprint, request, jsonify
import asyncio
import logging
from typing import Dict, Any, List, Optional

# 导入多语言支持模块
from .multilingual_support import (
    SupportedLanguage,
    AdvancedLanguageDetector,
    MultilingualSplittingEngine,
    CrossLanguageSubtitleManager,
    MultilingualConfigManager
)

from .multilingual_integration import (
    MultilingualSubtitleIntegrator,
    MultilingualConfigIntegrator
)

logger = logging.getLogger(__name__)

# 创建蓝图
multilingual_api = Blueprint('multilingual_api', __name__, url_prefix='/api/multilingual')

# 全局实例
language_detector = AdvancedLanguageDetector()
splitting_engine = MultilingualSplittingEngine()
subtitle_manager = CrossLanguageSubtitleManager()
config_manager = MultilingualConfigManager()
subtitle_integrator = MultilingualSubtitleIntegrator()
config_integrator = MultilingualConfigIntegrator()

@multilingual_api.route('/languages', methods=['GET'])
def get_supported_languages():
    """获取支持的语言列表"""
    try:
        languages = config_manager.get_supported_languages()
        
        return jsonify({
            "success": True,
            "data": {
                "supported_languages": languages,
                "total_count": len(languages)
            }
        })
        
    except Exception as e:
        logger.error(f"获取支持语言列表失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/detect-language', methods=['POST'])
def detect_language():
    """检测文本语言"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                "success": False,
                "error": "文本不能为空"
            }), 400
        
        # 检测主要语言
        language, confidence = language_detector.detect_language(text)
        
        # 检测多语言段落
        multilang_segments = language_detector.detect_multiple_languages(text)
        
        return jsonify({
            "success": True,
            "data": {
                "primary_language": {
                    "code": language.value,
                    "confidence": confidence
                },
                "multilingual_segments": [
                    {
                        "language": lang.value,
                        "confidence": conf,
                        "start_pos": start,
                        "end_pos": end,
                        "text": text[start:end]
                    } for lang, conf, start, end in multilang_segments
                ],
                "is_mixed_language": language == SupportedLanguage.MIXED_LANGUAGE,
                "text_length": len(text)
            }
        })
        
    except Exception as e:
        logger.error(f"语言检测失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/split-multilingual', methods=['POST'])
def split_multilingual_text():
    """多语言智能分割"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_language = data.get('target_language', 'auto')
        context_config = data.get('context', {})
        
        if not text:
            return jsonify({
                "success": False,
                "error": "文本不能为空"
            }), 400
        
        # 转换语言代码
        try:
            if target_language == 'auto':
                target_lang = None
            else:
                target_lang = SupportedLanguage(target_language)
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"不支持的语言代码: {target_language}"
            }), 400
        
        # 异步执行分割
        async def process_splitting():
            segments = await splitting_engine.split_multilingual_text(
                text, 
                target_language=target_lang
            )
            
            return [
                {
                    "text": seg.text,
                    "start_pos": seg.start_pos,
                    "end_pos": seg.end_pos,
                    "confidence": seg.confidence,
                    "language": seg.language.value,
                    "semantic_weight": seg.semantic_weight,
                    "readability_score": seg.readability_score
                } for seg in segments
            ]
        
        segments_data = asyncio.run(process_splitting())
        
        return jsonify({
            "success": True,
            "data": {
                "segments": segments_data,
                "segment_count": len(segments_data),
                "original_text": text,
                "target_language": target_language,
                "processing_stats": {
                    "total_chars": len(text),
                    "avg_confidence": sum(seg["confidence"] for seg in segments_data) / len(segments_data) if segments_data else 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"多语言分割失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/generate-multilingual-subtitles', methods=['POST'])
def generate_multilingual_subtitles():
    """生成多语言字幕"""
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        primary_language = data.get('primary_language', 'auto')
        secondary_languages = data.get('secondary_languages', [])
        sync_config = data.get('sync_config', {})
        
        if not texts:
            return jsonify({
                "success": False,
                "error": "文本列表不能为空"
            }), 400
        
        # 转换语言代码
        try:
            primary_lang = SupportedLanguage(primary_language) if primary_language != 'auto' else SupportedLanguage.AUTO_DETECT
            secondary_langs = [SupportedLanguage(lang) for lang in secondary_languages]
        except ValueError as e:
            return jsonify({
                "success": False,
                "error": f"语言代码错误: {str(e)}"
            }), 400
        
        # 异步执行字幕生成
        async def process_subtitles():
            # 检测主要语言（如果设为auto）
            if primary_lang == SupportedLanguage.AUTO_DETECT:
                combined_text = " ".join(texts)
                detected_lang, _ = language_detector.detect_language(combined_text)
                working_primary = detected_lang if detected_lang != SupportedLanguage.UNKNOWN else SupportedLanguage.ENGLISH
            else:
                working_primary = primary_lang
            
            # 生成多语言字幕
            multilingual_subtitles = await subtitle_manager.create_multilingual_subtitles(
                texts=texts,
                primary_language=working_primary,
                secondary_languages=secondary_langs
            )
            
            # 转换为可序列化的格式
            result = {}
            for language, subtitles in multilingual_subtitles.items():
                result[language.value] = [
                    {
                        "text": sub.text,
                        "start_time": sub.start_time,
                        "end_time": sub.end_time,
                        "language": sub.language.value,
                        "confidence": sub.confidence,
                        "sync_group_id": sub.sync_group_id,
                        "readability_score": sub.readability_score
                    } for sub in subtitles
                ]
            
            return result
        
        subtitles_data = asyncio.run(process_subtitles())
        
        return jsonify({
            "success": True,
            "data": {
                "multilingual_subtitles": subtitles_data,
                "languages_generated": list(subtitles_data.keys()),
                "subtitle_counts": {lang: len(subs) for lang, subs in subtitles_data.items()},
                "total_texts_processed": len(texts)
            }
        })
        
    except Exception as e:
        logger.error(f"多语言字幕生成失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/enhance-subtitle-generation', methods=['POST'])
def enhance_subtitle_generation():
    """增强字幕生成（完整的多语言处理）"""
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        config = data.get('config', {})
        
        if not texts:
            return jsonify({
                "success": False,
                "error": "文本列表不能为空"
            }), 400
        
        # 异步执行完整处理
        async def process_enhanced():
            # 使用进度回调（这里简化处理）
            progress_log = []
            
            def progress_callback(message):
                progress_log.append(message)
                logger.info(f"多语言处理进度: {message}")
            
            result = await subtitle_integrator.enhance_subtitle_generation_multilingual(
                texts=texts,
                config=config,
                progress_callback=progress_callback
            )
            
            # 转换多语言字幕为可序列化格式
            serializable_subtitles = {}
            for language, subtitles in result["multilingual_subtitles"].items():
                serializable_subtitles[language.value] = [
                    {
                        "text": sub.text,
                        "start_time": sub.start_time,
                        "end_time": sub.end_time,
                        "language": sub.language.value,
                        "confidence": sub.confidence,
                        "sync_group_id": sub.sync_group_id,
                        "readability_score": sub.readability_score
                    } for sub in subtitles
                ]
            
            # 转换语言分析结果
            lang_analysis = result["language_analysis"].copy()
            lang_analysis["detected_languages"] = [lang.value for lang in lang_analysis["detected_languages"]]
            if lang_analysis.get("primary_language"):
                lang_analysis["primary_language"] = lang_analysis["primary_language"].value
            
            return {
                "enhanced_texts": result["enhanced_texts"],
                "multilingual_subtitles": serializable_subtitles,
                "language_analysis": lang_analysis,
                "optimized_config": result["optimized_config"],
                "processing_stats": result["processing_stats"],
                "progress_log": progress_log
            }
        
        result = asyncio.run(process_enhanced())
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"增强字幕生成失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/language-config/<language_code>', methods=['GET'])
def get_language_config(language_code):
    """获取特定语言的配置"""
    try:
        config = config_manager.get_language_config(language_code)
        
        if not config:
            return jsonify({
                "success": False,
                "error": f"不支持的语言: {language_code}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": {
                "language_code": config.language_code,
                "language_name": config.language_name,
                "rtl": config.rtl,
                "max_subtitle_length": config.max_subtitle_length,
                "target_subtitle_length": config.target_subtitle_length,
                "voice_mapping": config.voice_mapping,
                "tts_engine_preference": config.tts_engine_preference,
                "language_features": {
                    "needs_word_segmentation": config.needs_word_segmentation,
                    "has_capitalization": config.has_capitalization,
                    "has_spaces": config.has_spaces,
                    "sov_order": config.sov_order,
                    "agglutinative": config.agglutinative,
                    "tonal": config.tonal
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取语言配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/optimize-config', methods=['POST'])
def optimize_config_for_language():
    """为特定语言优化配置"""
    try:
        data = request.get_json()
        base_config = data.get('config', {})
        target_language = data.get('target_language', '')
        
        if not target_language:
            return jsonify({
                "success": False,
                "error": "目标语言不能为空"
            }), 400
        
        try:
            lang = SupportedLanguage(target_language)
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"不支持的语言: {target_language}"
            }), 400
        
        # 异步优化配置
        async def optimize():
            return await config_manager.optimize_config_for_language(base_config, lang)
        
        optimized_config = asyncio.run(optimize())
        
        return jsonify({
            "success": True,
            "data": {
                "optimized_config": optimized_config,
                "target_language": target_language,
                "optimization_applied": True
            }
        })
        
    except Exception as e:
        logger.error(f"配置优化失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/batch-language-detection', methods=['POST'])
def batch_language_detection():
    """批量语言检测"""
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        
        if not texts:
            return jsonify({
                "success": False,
                "error": "文本列表不能为空"
            }), 400
        
        results = []
        language_stats = {}
        
        for i, text in enumerate(texts):
            lang, confidence = language_detector.detect_language(text)
            
            results.append({
                "index": i,
                "text": text,
                "detected_language": lang.value,
                "confidence": confidence,
                "text_length": len(text)
            })
            
            # 统计语言分布
            if lang.value not in language_stats:
                language_stats[lang.value] = {"count": 0, "avg_confidence": 0.0}
            language_stats[lang.value]["count"] += 1
        
        # 计算平均置信度
        for lang_code, stats in language_stats.items():
            lang_confidences = [r["confidence"] for r in results if r["detected_language"] == lang_code]
            stats["avg_confidence"] = sum(lang_confidences) / len(lang_confidences) if lang_confidences else 0.0
        
        return jsonify({
            "success": True,
            "data": {
                "detection_results": results,
                "language_statistics": language_stats,
                "total_texts": len(texts),
                "unique_languages": len(language_stats)
            }
        })
        
    except Exception as e:
        logger.error(f"批量语言检测失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/export-multilingual-config', methods=['POST'])
def export_multilingual_config():
    """导出多语言配置"""
    try:
        data = request.get_json()
        config = data.get('config', {})
        filename = data.get('filename', 'multilingual_config.json')
        
        success = config_manager.save_multilingual_config(config, filename)
        
        if success:
            return jsonify({
                "success": True,
                "data": {
                    "message": "多语言配置已保存",
                    "filename": filename
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "配置保存失败"
            }), 500
        
    except Exception as e:
        logger.error(f"导出多语言配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/import-multilingual-config', methods=['POST'])
def import_multilingual_config():
    """导入多语言配置"""
    try:
        data = request.get_json()
        filename = data.get('filename', 'multilingual_config.json')
        
        config = config_manager.load_multilingual_config(filename)
        
        if config:
            return jsonify({
                "success": True,
                "data": {
                    "config": config,
                    "message": "多语言配置已加载",
                    "filename": filename
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "配置文件不存在或加载失败"
            }), 404
        
    except Exception as e:
        logger.error(f"导入多语言配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@multilingual_api.route('/health', methods=['GET'])
def health_check():
    """多语言系统健康检查"""
    try:
        # 测试各个组件
        health_status = {
            "language_detector": True,
            "splitting_engine": True,
            "subtitle_manager": True,
            "config_manager": True
        }
        
        # 简单的功能测试
        test_text = "Hello world. 你好世界。"
        lang, confidence = language_detector.detect_language(test_text)
        
        supported_languages = config_manager.get_supported_languages()
        
        return jsonify({
            "success": True,
            "data": {
                "status": "healthy",
                "components": health_status,
                "test_results": {
                    "language_detection": {
                        "detected": lang.value,
                        "confidence": confidence
                    }
                },
                "supported_languages_count": len(supported_languages),
                "timestamp": "2025-09-09"
            }
        })
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 错误处理
@multilingual_api.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "API端点不存在"
    }), 404

@multilingual_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "内部服务器错误"
    }), 500

# 导出蓝图
__all__ = ['multilingual_api']
