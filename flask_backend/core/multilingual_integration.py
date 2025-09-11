"""
多语言支持系统集成接口
任务3.2: 与现有字幕系统的深度集成
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass
import json
import os

# 导入多语言核心模块
from .multilingual_support import (
    SupportedLanguage,
    LanguageConfig,
    MultilingualSubtitle,
    CrossLanguageSync,
    AdvancedLanguageDetector,
    MultilingualSplittingEngine,
    CrossLanguageSubtitleManager,
    MultilingualConfigManager
)

# 导入智能断句模块
from .smart_sentence_splitter import SplittingContext, SplittingStrategy

logger = logging.getLogger(__name__)

@dataclass
class MultilingualProcessingConfig:
    """多语言处理配置"""
    primary_language: SupportedLanguage
    secondary_languages: Optional[List[SupportedLanguage]] = None
    auto_detect_language: bool = True
    cross_language_sync: bool = True
    sync_tolerance: float = 0.5
    
    # 质量控制
    min_confidence: float = 0.7
    optimize_for_target: bool = True
    preserve_timing: bool = True
    
    # 输出控制
    generate_separate_files: bool = True
    include_language_metadata: bool = True

class MultilingualSubtitleIntegrator:
    """多语言字幕系统集成器"""
    
    def __init__(self):
        self.language_detector = AdvancedLanguageDetector()
        self.splitting_engine = MultilingualSplittingEngine()
        self.subtitle_manager = CrossLanguageSubtitleManager()
        self.config_manager = MultilingualConfigManager()
        
        # 缓存
        self._language_cache = {}
        self._config_cache = {}
        
    async def enhance_subtitle_generation_multilingual(
        self,
        texts: List[str],
        config: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """增强字幕生成：多语言支持版本"""
        
        if progress_callback:
            progress_callback("开始多语言字幕处理...")
        
        try:
            # 1. 解析处理配置
            processing_config = self._extract_multilingual_config(config)
            
            # 2. 语言检测和分析
            language_analysis = await self._analyze_text_languages(texts)
            
            if progress_callback:
                progress_callback("语言检测完成...")
            
            # 3. 调整配置以适应检测到的语言
            optimized_config = await self._optimize_config_for_detected_languages(
                config, language_analysis, processing_config
            )
            
            # 4. 多语言文本分割处理
            multilingual_segments = await self._process_multilingual_splitting(
                texts, language_analysis, processing_config, progress_callback
            )
            
            # 5. 生成多语言字幕
            multilingual_subtitles = await self._generate_multilingual_subtitles(
                multilingual_segments, processing_config, progress_callback
            )
            
            # 6. 跨语言同步（如果需要）
            if processing_config.cross_language_sync and len(processing_config.secondary_languages or []) > 0:
                multilingual_subtitles = await self._apply_cross_language_sync(
                    multilingual_subtitles, processing_config
                )
            
            if progress_callback:
                progress_callback("多语言字幕处理完成!")
            
            return {
                "enhanced_texts": multilingual_segments,
                "multilingual_subtitles": multilingual_subtitles,
                "language_analysis": language_analysis,
                "optimized_config": optimized_config,
                "processing_stats": self._calculate_processing_stats(multilingual_subtitles)
            }
            
        except Exception as e:
            logger.error(f"多语言字幕处理失败: {e}")
            if progress_callback:
                progress_callback(f"处理失败: {str(e)}")
            raise
    
    def _extract_multilingual_config(self, config: Dict[str, Any]) -> MultilingualProcessingConfig:
        """从配置中提取多语言处理参数"""
        
        # 获取语言设置
        primary_lang_code = config.get("source_language", "auto")
        secondary_lang_codes = config.get("target_languages", [])
        
        # 转换为SupportedLanguage枚举
        try:
            if primary_lang_code == "auto":
                primary_language = SupportedLanguage.AUTO_DETECT
            else:
                primary_language = SupportedLanguage(primary_lang_code)
        except ValueError:
            primary_language = SupportedLanguage.AUTO_DETECT
        
        secondary_languages = []
        for code in secondary_lang_codes:
            try:
                secondary_languages.append(SupportedLanguage(code))
            except ValueError:
                continue
        
        return MultilingualProcessingConfig(
            primary_language=primary_language,
            secondary_languages=secondary_languages,
            auto_detect_language=config.get("auto_detect_language", True),
            cross_language_sync=config.get("cross_language_sync", True),
            sync_tolerance=config.get("sync_tolerance", 0.5),
            min_confidence=config.get("min_language_confidence", 0.7),
            optimize_for_target=config.get("optimize_for_target", True),
            preserve_timing=config.get("preserve_timing", True),
            generate_separate_files=config.get("generate_separate_files", True),
            include_language_metadata=config.get("include_language_metadata", True)
        )
    
    async def _analyze_text_languages(self, texts: List[str]) -> Dict[str, Any]:
        """分析文本语言特征"""
        
        analysis = {
            "detected_languages": [],
            "confidence_scores": [],
            "mixed_language_segments": [],
            "primary_language": None,
            "language_distribution": {},
            "total_texts": len(texts)
        }
        
        language_counts = {}
        total_confidence = 0.0
        
        for i, text in enumerate(texts):
            # 检测主要语言
            lang, confidence = self.language_detector.detect_language(text)
            analysis["detected_languages"].append(lang)
            analysis["confidence_scores"].append(confidence)
            
            # 统计语言分布
            if lang not in language_counts:
                language_counts[lang] = 0
            language_counts[lang] += 1
            total_confidence += confidence
            
            # 检测混合语言段落
            if lang == SupportedLanguage.MIXED_LANGUAGE:
                multilang_segments = self.language_detector.detect_multiple_languages(text)
                analysis["mixed_language_segments"].append({
                    "text_index": i,
                    "segments": multilang_segments
                })
        
        # 确定主要语言
        if language_counts:
            analysis["primary_language"] = max(language_counts, key=lambda x: language_counts.get(x, 0))  # type: ignore
        
        # 计算语言分布百分比
        total_texts = len(texts)
        for lang, count in language_counts.items():
            analysis["language_distribution"][lang.value] = {
                "count": count,
                "percentage": (count / total_texts) * 100
            }
        
        analysis["average_confidence"] = total_confidence / len(texts) if texts else 0.0
        
        return analysis
    
    async def _optimize_config_for_detected_languages(
        self,
        base_config: Dict[str, Any],
        language_analysis: Dict[str, Any],
        processing_config: MultilingualProcessingConfig
    ) -> Dict[str, Any]:
        """根据检测到的语言优化配置"""
        
        optimized = base_config.copy()
        
        # 如果设置了自动检测，使用检测到的主要语言
        if processing_config.auto_detect_language and language_analysis.get("primary_language"):
            detected_primary = language_analysis["primary_language"]
            
            if detected_primary != SupportedLanguage.UNKNOWN:
                # 为检测到的语言优化配置
                lang_optimized = await self.config_manager.optimize_config_for_language(
                    optimized, detected_primary
                )
                optimized.update(lang_optimized)
                
                # 更新语言设置
                optimized["detected_primary_language"] = detected_primary.value
        
        # 添加多语言处理参数
        optimized["multilingual_processing"] = {
            "enabled": True,
            "primary_language": processing_config.primary_language.value,
            "secondary_languages": [lang.value for lang in (processing_config.secondary_languages or [])],
            "cross_language_sync": processing_config.cross_language_sync,
            "language_detection_confidence": language_analysis.get("average_confidence", 0.0)
        }
        
        return optimized
    
    async def _process_multilingual_splitting(
        self,
        texts: List[str],
        language_analysis: Dict[str, Any],
        processing_config: MultilingualProcessingConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """处理多语言文本分割"""
        
        enhanced_texts = []
        total_texts = len(texts)
        
        for i, text in enumerate(texts):
            if progress_callback:
                progress = (i + 1) / total_texts * 50  # 分割处理占50%进度
                progress_callback(f"处理文本分割 {i+1}/{total_texts} ({progress:.1f}%)")
            
            # 获取该文本的检测语言
            detected_lang = language_analysis["detected_languages"][i]
            
            # 选择处理语言
            if processing_config.primary_language == SupportedLanguage.AUTO_DETECT:
                target_language = detected_lang
            else:
                target_language = processing_config.primary_language
            
            # 执行多语言分割
            segments = await self.splitting_engine.split_multilingual_text(
                text, target_language=target_language
            )
            
            # 构建增强文本信息
            enhanced_text = {
                "original_text": text,
                "segments": [
                    {
                        "text": seg.text,
                        "start_pos": seg.start_pos,
                        "end_pos": seg.end_pos,
                        "confidence": seg.confidence,
                        "language": seg.language.value,
                        "semantic_weight": seg.semantic_weight,
                        "readability_score": seg.readability_score
                    } for seg in segments
                ],
                "detected_language": detected_lang.value,
                "target_language": target_language.value,
                "processing_confidence": language_analysis["confidence_scores"][i]
            }
            
            enhanced_texts.append(enhanced_text)
        
        return enhanced_texts
    
    async def _generate_multilingual_subtitles(
        self,
        multilingual_segments: List[Dict[str, Any]],
        processing_config: MultilingualProcessingConfig,
        progress_callback: Optional[Callable] = None
    ) -> Dict[SupportedLanguage, List[MultilingualSubtitle]]:
        """生成多语言字幕"""
        
        # 提取原始文本
        texts = [item["original_text"] for item in multilingual_segments]
        
        # 确定要生成的语言
        languages_to_process = [processing_config.primary_language]
        if processing_config.secondary_languages:
            languages_to_process.extend(processing_config.secondary_languages)
        
        # 移除AUTO_DETECT，用实际检测到的语言替换
        if SupportedLanguage.AUTO_DETECT in languages_to_process:
            languages_to_process.remove(SupportedLanguage.AUTO_DETECT)
            # 添加检测到的主要语言
            main_detected = multilingual_segments[0].get("detected_language")
            if main_detected:
                try:
                    detected_lang = SupportedLanguage(main_detected)
                    if detected_lang not in languages_to_process:
                        languages_to_process.append(detected_lang)
                except ValueError:
                    pass
        
        if progress_callback:
            progress_callback(f"生成 {len(languages_to_process)} 种语言的字幕...")
        
        # 生成多语言字幕
        secondary_langs = languages_to_process[1:] if len(languages_to_process) > 1 else []
        multilingual_subtitles = await self.subtitle_manager.create_multilingual_subtitles(
            texts=texts,
            primary_language=languages_to_process[0],
            secondary_languages=secondary_langs
        )
        
        return multilingual_subtitles
    
    async def _apply_cross_language_sync(
        self,
        multilingual_subtitles: Dict[SupportedLanguage, List[MultilingualSubtitle]],
        processing_config: MultilingualProcessingConfig
    ) -> Dict[SupportedLanguage, List[MultilingualSubtitle]]:
        """应用跨语言同步"""
        
        if not processing_config.secondary_languages:
            return multilingual_subtitles
        
        # 创建同步配置
        sync_config = CrossLanguageSync(
            primary_language=processing_config.primary_language,
            secondary_languages=processing_config.secondary_languages,
            sync_tolerance=processing_config.sync_tolerance,
            time_based_sync=processing_config.preserve_timing,
            content_based_sync=True,
            min_confidence=processing_config.min_confidence
        )
        
        # 应用同步
        synchronized_subtitles = await self.subtitle_manager._synchronize_multilingual_subtitles(
            multilingual_subtitles, sync_config
        )
        
        return synchronized_subtitles
    
    def _calculate_processing_stats(
        self,
        multilingual_subtitles: Dict[SupportedLanguage, List[MultilingualSubtitle]]
    ) -> Dict[str, Any]:
        """计算处理统计信息"""
        
        stats = {
            "total_languages": len(multilingual_subtitles),
            "subtitle_counts": {},
            "average_confidence": {},
            "total_duration": {},
            "quality_metrics": {}
        }
        
        for language, subtitles in multilingual_subtitles.items():
            lang_code = language.value
            stats["subtitle_counts"][lang_code] = len(subtitles)
            
            if subtitles:
                # 平均置信度
                avg_confidence = sum(sub.confidence for sub in subtitles) / len(subtitles)
                stats["average_confidence"][lang_code] = avg_confidence
                
                # 总时长
                total_duration = subtitles[-1].end_time if subtitles else 0.0
                stats["total_duration"][lang_code] = total_duration
                
                # 质量指标
                avg_readability = sum(
                    sub.readability_score for sub in subtitles 
                    if sub.readability_score is not None
                ) / len([sub for sub in subtitles if sub.readability_score is not None])
                
                stats["quality_metrics"][lang_code] = {
                    "average_readability": avg_readability,
                    "confidence_above_threshold": len([
                        sub for sub in subtitles if sub.confidence > 0.7
                    ]) / len(subtitles) * 100
                }
        
        return stats

class MultilingualConfigIntegrator:
    """多语言配置集成器"""
    
    def __init__(self):
        self.config_manager = MultilingualConfigManager()
        
    def integrate_with_existing_config(
        self,
        existing_config: Dict[str, Any],
        multilingual_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将多语言设置集成到现有配置"""
        
        integrated = existing_config.copy()
        
        # 添加多语言支持配置
        integrated["multilingual"] = {
            "enabled": True,
            "supported_languages": self.config_manager.get_supported_languages(),
            "settings": multilingual_settings
        }
        
        # 更新字幕配置以支持多语言
        if "subtitle" in integrated:
            integrated["subtitle"]["multilingual_support"] = True
            integrated["subtitle"]["language_specific_optimization"] = True
        
        # 更新TTS配置以支持多语言
        if "tts" in integrated:
            integrated["tts"]["multilingual_voices"] = True
            integrated["tts"]["auto_voice_selection"] = True
        
        return integrated
    
    def generate_language_specific_configs(
        self,
        base_config: Dict[str, Any],
        target_languages: List[SupportedLanguage]
    ) -> Dict[str, Dict[str, Any]]:
        """生成语言特定的配置"""
        
        language_configs = {}
        
        for language in target_languages:
            lang_config = asyncio.run(
                self.config_manager.optimize_config_for_language(base_config, language)
            )
            language_configs[language.value] = lang_config
        
        return language_configs

# 导出主要类
__all__ = [
    'MultilingualProcessingConfig',
    'MultilingualSubtitleIntegrator', 
    'MultilingualConfigIntegrator'
]
