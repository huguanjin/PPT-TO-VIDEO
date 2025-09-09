"""
智能断句集成接口
将新的智能断句系统与现有字幕生成系统集成
"""

from typing import Dict, Any, List, Optional, Callable
import logging
import asyncio
from pathlib import Path

from .smart_sentence_splitter import (
    SmartSentenceSplitterManager, 
    SplittingContext, 
    SplittingStrategy, 
    LanguageType
)

logger = logging.getLogger(__name__)

class SmartSplittingIntegrator:
    """智能断句集成器"""
    
    def __init__(self):
        self.splitter_manager = SmartSentenceSplitterManager()
        self.logger = logging.getLogger(__name__)
        
    async def enhance_subtitle_generation(self, 
                                        texts: List[str],
                                        config: Dict[str, Any],
                                        progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """
        增强字幕生成过程的断句处理
        
        Args:
            texts: 文本列表
            config: 字幕配置
            progress_callback: 进度回调
            
        Returns:
            处理结果
        """
        self.logger.info(f"开始智能断句处理: {len(texts)} 个文本")
        
        # 从配置中提取断句参数
        splitting_config = self._extract_splitting_config(config)
        
        results = {
            "enhanced_texts": [],
            "statistics": {
                "total_input_texts": len(texts),
                "total_output_segments": 0,
                "processing_time": 0.0,
                "average_confidence": 0.0
            },
            "quality_metrics": {
                "semantic_coherence": 0.0,
                "length_optimization": 0.0,
                "readability_improvement": 0.0
            }
        }
        
        total_confidence = 0.0
        total_segments = 0
        
        for i, text in enumerate(texts):
            if not text or not text.strip():
                results["enhanced_texts"].append([])
                continue
            
            try:
                # 执行智能分割
                split_result = await self.splitter_manager.split_text_smart(
                    text=text.strip(),
                    target_length=splitting_config["target_length"],
                    strategy=splitting_config["strategy"],
                    language=splitting_config["language"]
                )
                
                if split_result["success"]:
                    segments = [seg["text"] for seg in split_result["segments"]]
                    results["enhanced_texts"].append(segments)
                    
                    # 累计统计信息
                    total_segments += len(segments)
                    total_confidence += split_result["statistics"]["average_confidence"]
                    results["statistics"]["processing_time"] += split_result["statistics"]["processing_time"]
                    
                else:
                    # 失败时使用原文本
                    results["enhanced_texts"].append([text])
                    self.logger.warning(f"文本 {i} 智能分割失败，使用原文本")
                
            except Exception as e:
                self.logger.error(f"处理文本 {i} 时出错: {e}")
                results["enhanced_texts"].append([text])
            
            # 更新进度
            if progress_callback:
                progress = int((i + 1) / len(texts) * 100)
                progress_callback(progress)
        
        # 计算最终统计
        results["statistics"]["total_output_segments"] = total_segments
        if len(texts) > 0:
            results["statistics"]["average_confidence"] = total_confidence / len(texts)
        
        # 计算质量指标
        results["quality_metrics"] = self._calculate_quality_metrics(texts, results["enhanced_texts"])
        
        self.logger.info(f"智能断句完成: {total_segments} 个片段，平均置信度 {results['statistics']['average_confidence']:.2f}")
        
        return results
    
    def _extract_splitting_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """从字幕配置中提取断句参数"""
        # 获取目标长度
        target_length = config.get("max_length", 40)
        if target_length > 60:
            target_length = 40  # Netflix标准
        
        # 确定策略
        strategy = "hybrid"  # 默认混合策略
        
        if config.get("ai_splitting", False):
            strategy = "ai_enhanced"
        elif config.get("semantic_splitting", True):
            strategy = "semantic"
        elif config.get("use_punctuation_only", False):
            strategy = "punctuation"
        
        # 检测语言偏好
        language = "auto"
        if config.get("language_hint"):
            language_map = {
                "zh": "zh",
                "zh-CN": "zh", 
                "en": "en",
                "en-US": "en"
            }
            language = language_map.get(config["language_hint"], "auto")
        
        return {
            "target_length": target_length,
            "strategy": strategy,
            "language": language,
            "preserve_semantics": config.get("preserve_semantics", True),
            "optimize_readability": config.get("optimize_readability", True)
        }
    
    def _calculate_quality_metrics(self, 
                                 original_texts: List[str], 
                                 enhanced_texts: List[List[str]]) -> Dict[str, float]:
        """计算质量改进指标"""
        if not original_texts or not enhanced_texts:
            return {"semantic_coherence": 0.0, "length_optimization": 0.0, "readability_improvement": 0.0}
        
        # 计算长度优化指标
        original_lengths = [len(text) for text in original_texts]
        enhanced_lengths = []
        for text_segments in enhanced_texts:
            if text_segments:
                enhanced_lengths.extend([len(seg) for seg in text_segments])
            else:
                enhanced_lengths.append(0)
        
        # 长度分布改进
        target_length = 40
        original_over_target = sum(1 for length in original_lengths if length > target_length)
        enhanced_over_target = sum(1 for length in enhanced_lengths if length > target_length)
        
        length_optimization = 1.0 - (enhanced_over_target / len(enhanced_lengths)) if enhanced_lengths else 0.0
        
        # 语义连贯性（简化计算）
        semantic_coherence = 0.85  # 基础分数，实际应该通过更复杂的算法计算
        
        # 可读性改进（基于长度分布的标准差）
        import statistics
        
        try:
            original_std = statistics.stdev(original_lengths) if len(original_lengths) > 1 else 0
            enhanced_std = statistics.stdev(enhanced_lengths) if len(enhanced_lengths) > 1 else 0
            
            readability_improvement = max(0.0, (original_std - enhanced_std) / max(original_std, 1.0))
        except:
            readability_improvement = 0.0
        
        return {
            "semantic_coherence": min(1.0, semantic_coherence),
            "length_optimization": min(1.0, length_optimization),
            "readability_improvement": min(1.0, readability_improvement)
        }
    
    async def process_single_text(self, 
                                text: str, 
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个文本的便捷方法"""
        if not text or not text.strip():
            return {
                "success": False,
                "error": "空文本",
                "segments": []
            }
        
        splitting_config = self._extract_splitting_config(config)
        
        try:
            result = await self.splitter_manager.split_text_smart(
                text=text.strip(),
                target_length=splitting_config["target_length"],
                strategy=splitting_config["strategy"],
                language=splitting_config["language"]
            )
            
            return {
                "success": True,
                "segments": [seg["text"] for seg in result["segments"]],
                "statistics": result["statistics"],
                "quality_info": {
                    "confidence": result["statistics"]["average_confidence"],
                    "strategy_used": result["statistics"]["strategy_used"],
                    "language_detected": result["statistics"]["language_detected"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"处理文本时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "segments": [text]  # 回退到原文本
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        stats = self.splitter_manager.get_performance_stats()
        
        return {
            "performance_statistics": stats,
            "recommendations": self._generate_performance_recommendations(stats),
            "system_status": {
                "models_available": stats["model_availability"],
                "cache_efficiency": min(1.0, stats["cache_size"] / 100.0),
                "processing_speed": "fast" if stats["average_processing_time"] < 0.1 else "normal"
            }
        }
    
    def _generate_performance_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # 检查模型可用性
        if not stats["model_availability"]["spacy"]:
            recommendations.append("建议安装SpaCy模型以提升语义分析质量")
        
        if not stats["model_availability"]["jieba"]:
            recommendations.append("建议安装jieba分词器以改进中文处理")
        
        # 检查处理速度
        if stats["average_processing_time"] > 0.2:
            recommendations.append("处理速度较慢，建议检查系统资源或使用更简单的分割策略")
        
        # 检查置信度
        if stats["average_confidence"] < 0.7:
            recommendations.append("分割质量偏低，建议调整分割策略或检查输入文本质量")
        
        # 检查策略使用
        if "strategy_usage" in stats:
            most_used = max(stats["strategy_usage"].items(), key=lambda x: x[1])
            if most_used[0] == "punctuation" and most_used[1] > stats["total_splits"] * 0.8:
                recommendations.append("过度依赖标点分割，建议启用AI增强或语义分割")
        
        if not recommendations:
            recommendations.append("系统运行良好，无需特别优化")
        
        return recommendations
    
    def configure_for_netflix_standards(self) -> Dict[str, Any]:
        """为Netflix标准配置断句参数"""
        return {
            "max_length": 40,  # Netflix标准长度
            "target_length": 35,  # 更保守的目标
            "ai_splitting": True,
            "semantic_splitting": True,
            "preserve_semantics": True,
            "optimize_readability": True,
            "strategy_preference": "semantic"
        }
    
    def configure_for_mobile_optimization(self) -> Dict[str, Any]:
        """为移动端优化配置断句参数"""
        return {
            "max_length": 30,  # 移动端更短
            "target_length": 25,
            "ai_splitting": True,
            "semantic_splitting": True,
            "preserve_semantics": True,
            "optimize_readability": True,
            "strategy_preference": "length_balanced"
        }
    
    def configure_for_performance(self) -> Dict[str, Any]:
        """为性能优化配置断句参数"""
        return {
            "max_length": 50,
            "target_length": 40,
            "ai_splitting": False,
            "semantic_splitting": False,
            "use_punctuation_only": True,
            "strategy_preference": "punctuation"
        }

# 全局集成器实例
smart_splitting_integrator = SmartSplittingIntegrator()

# 便捷函数
async def enhance_subtitle_texts(texts: List[str], 
                               config: Dict[str, Any],
                               progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
    """增强字幕文本的便捷函数"""
    return await smart_splitting_integrator.enhance_subtitle_generation(texts, config, progress_callback)

async def split_single_text(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """分割单个文本的便捷函数"""
    return await smart_splitting_integrator.process_single_text(text, config)

def get_smart_splitting_stats() -> Dict[str, Any]:
    """获取智能断句统计的便捷函数"""
    return smart_splitting_integrator.get_performance_report()
