"""
配置优化管理器
整合配置验证、优化建议和自动优化功能
提供类似VideoLingo的智能配置体验
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import logging
from datetime import datetime
from .config_validator import ConfigValidator, ValidationLevel, OptimizationType, OptimizationSuggestion
from .config_presets import ConfigPresets

logger = logging.getLogger(__name__)

class ConfigOptimizer:
    """配置优化管理器 - 智能配置优化和建议"""
    
    def __init__(self):
        self.validator = ConfigValidator()
        self.presets = ConfigPresets()
        self.optimization_history = []
        
    def analyze_config(self, config: Dict[str, Any], 
                      user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        全面分析配置
        
        Args:
            config: 待分析的配置
            user_context: 用户上下文（使用场景、偏好等）
            
        Returns:
            分析结果
        """
        # 基础验证
        validation_report = self.validator.generate_validation_report(config)
        
        # 用户上下文分析
        context_analysis = self._analyze_user_context(config, user_context)
        
        # 智能建议生成
        smart_suggestions = self._generate_smart_suggestions(config, user_context, validation_report)
        
        # 预设匹配
        preset_recommendations = self._recommend_presets(config)
        
        return {
            "config_analysis": {
                "timestamp": datetime.now().isoformat(),
                "config_hash": self._calculate_config_hash(config),
                "validation_report": validation_report,
                "context_analysis": context_analysis,
                "smart_suggestions": smart_suggestions,
                "preset_recommendations": preset_recommendations,
                "overall_assessment": self._generate_overall_assessment(validation_report, context_analysis)
            }
        }
    
    def _analyze_user_context(self, config: Dict[str, Any], 
                             user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """分析用户上下文"""
        if not user_context:
            return {"status": "no_context", "recommendations": []}
        
        analysis = {
            "use_case": user_context.get("use_case", "general"),
            "target_audience": user_context.get("target_audience", "general"),
            "platform": user_context.get("platform", "web"),
            "quality_priority": user_context.get("quality_priority", "balanced"),
            "performance_priority": user_context.get("performance_priority", "balanced"),
            "recommendations": []
        }
        
        # 基于使用场景的建议
        use_case = user_context.get("use_case")
        if use_case == "education":
            analysis["recommendations"].extend([
                "建议使用较大字体提升可读性",
                "启用高对比度模式",
                "考虑无障碍访问优化"
            ])
        elif use_case == "entertainment":
            analysis["recommendations"].extend([
                "应用Netflix级别样式",
                "优化视觉效果",
                "启用智能字幕分割"
            ])
        elif use_case == "business":
            analysis["recommendations"].extend([
                "使用专业字体",
                "确保跨平台兼容性",
                "启用质量保证功能"
            ])
        
        # 基于平台的建议
        platform = user_context.get("platform")
        if platform == "mobile":
            analysis["recommendations"].extend([
                "优化移动端显示",
                "调整字体大小适配小屏幕",
                "启用智能换行"
            ])
        elif platform == "tv":
            analysis["recommendations"].extend([
                "使用电视优化字体",
                "调整对比度适配远距离观看",
                "使用较大字体尺寸"
            ])
        
        return analysis
    
    def _generate_smart_suggestions(self, config: Dict[str, Any],
                                   user_context: Optional[Dict[str, Any]],
                                   validation_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成智能建议"""
        suggestions = []
        
        # 基于验证结果的建议
        errors = [r for r in validation_report["validation_results"] if r["level"] == "error"]
        if errors:
            suggestions.append({
                "type": "fix_errors",
                "priority": 10,
                "title": "修复配置错误",
                "description": f"发现 {len(errors)} 个配置错误需要修复",
                "action": "auto_fix",
                "details": errors[:3]  # 只显示前3个
            })
        
        # 基于评分的建议
        score = validation_report["overall_score"]
        if score < 70:
            suggestions.append({
                "type": "improve_quality",
                "priority": 8,
                "title": "提升配置质量",
                "description": f"当前评分 {score}/100，建议进行优化",
                "action": "apply_optimization",
                "target_score": 85
            })
        
        # Netflix标准建议
        if not self._is_netflix_compliant(config):
            suggestions.append({
                "type": "netflix_upgrade",
                "priority": 7,
                "title": "升级到Netflix标准",
                "description": "应用Netflix级别字幕标准，提升专业度",
                "action": "apply_preset",
                "preset": "netflix_standard"
            })
        
        # 性能优化建议
        if self._needs_performance_optimization(config):
            suggestions.append({
                "type": "performance_boost",
                "priority": 6,
                "title": "性能优化",
                "description": "优化配置以提升处理速度",
                "action": "apply_optimization",
                "optimization_type": "performance"
            })
        
        # AI功能建议
        if not self._has_ai_features(config):
            suggestions.append({
                "type": "ai_enhancement",
                "priority": 5,
                "title": "启用AI功能",
                "description": "启用AI智能处理功能提升字幕质量",
                "action": "enable_ai",
                "features": ["ai_splitting", "smart_processing", "auto_timing"]
            })
        
        return sorted(suggestions, key=lambda x: x["priority"], reverse=True)
    
    def _recommend_presets(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """推荐预设"""
        recommendations = []
        
        # 获取所有预设
        presets = self.presets.list_presets()
        
        for preset in presets:
            preset_config = self.presets.get_preset_config(preset["name"])
            if preset_config:
                similarity = self._calculate_config_similarity(config, preset_config)
                
                if similarity < 0.8:  # 如果相似度低于80%，推荐
                    recommendations.append({
                        "preset": preset,
                        "similarity": similarity,
                        "benefits": self._analyze_preset_benefits(config, preset_config),
                        "recommendation_reason": self._get_recommendation_reason(config, preset_config)
                    })
        
        # 按相似度和收益排序
        recommendations.sort(key=lambda x: (x["similarity"], len(x["benefits"])), reverse=True)
        
        return recommendations[:3]  # 只返回前3个推荐
    
    def _calculate_config_similarity(self, config1: Dict[str, Any], 
                                   config2: Dict[str, Any]) -> float:
        """计算配置相似度"""
        common_keys = set(config1.keys()) & set(config2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if config1[key] == config2[key]:
                matches += 1
        
        return matches / len(common_keys)
    
    def _analyze_preset_benefits(self, current_config: Dict[str, Any],
                               preset_config: Dict[str, Any]) -> List[str]:
        """分析预设的好处"""
        benefits = []
        
        # Netflix标准检查
        if preset_config.get("max_length") == 40 and current_config.get("max_length", 75) > 40:
            benefits.append("符合Netflix专业字幕长度标准")
        
        # 字体优化
        if preset_config.get("font_family") == "Helvetica Neue":
            benefits.append("使用专业字体提升可读性")
        
        # AI功能
        if preset_config.get("ai_splitting") and not current_config.get("ai_splitting", False):
            benefits.append("启用AI智能字幕分割")
        
        # 质量保证
        if preset_config.get("quality_assurance") and not current_config.get("quality_assurance", False):
            benefits.append("启用质量保证功能")
        
        return benefits
    
    def _get_recommendation_reason(self, current_config: Dict[str, Any],
                                 preset_config: Dict[str, Any]) -> str:
        """获取推荐理由"""
        if preset_config.get("style") == "netflix_professional":
            return "提供Netflix级别的专业字幕体验"
        elif preset_config.get("processing_mode") == "fast":
            return "快速处理模式，适合批量操作"
        elif preset_config.get("ai_splitting"):
            return "AI增强模式，提供智能字幕处理"
        else:
            return "平衡的配置选择，适合大多数场景"
    
    def auto_optimize_config(self, config: Dict[str, Any],
                           optimization_level: str = "balanced",
                           user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        自动优化配置
        
        Args:
            config: 原始配置
            optimization_level: 优化级别 ("conservative", "balanced", "aggressive")
            user_preferences: 用户偏好
            
        Returns:
            优化后的配置
        """
        optimized_config = config.copy()
        applied_optimizations = []
        
        # 获取优化建议
        suggestions = self.validator.generate_optimization_suggestions(config, user_preferences)
        
        # 根据优化级别筛选建议
        filtered_suggestions = self._filter_suggestions_by_level(suggestions, optimization_level)
        
        # 应用优化
        for suggestion in filtered_suggestions:
            optimized_config = self.validator.apply_optimization(optimized_config, suggestion)
            applied_optimizations.append({
                "type": suggestion.type.value,
                "title": suggestion.title,
                "improvement": suggestion.expected_improvement
            })
        
        # 记录优化历史
        self.optimization_history.append({
            "timestamp": datetime.now().isoformat(),
            "original_config_hash": self._calculate_config_hash(config),
            "optimized_config_hash": self._calculate_config_hash(optimized_config),
            "optimization_level": optimization_level,
            "applied_optimizations": applied_optimizations
        })
        
        return optimized_config
    
    def _filter_suggestions_by_level(self, suggestions: List[OptimizationSuggestion],
                                   level: str) -> List[OptimizationSuggestion]:
        """根据优化级别筛选建议"""
        if level == "conservative":
            # 只应用优先级8+且简单的优化
            return [s for s in suggestions if s.priority >= 8 and s.difficulty == "easy"]
        elif level == "balanced":
            # 应用优先级6+的优化
            return [s for s in suggestions if s.priority >= 6]
        elif level == "aggressive":
            # 应用所有优化
            return suggestions
        else:
            return []
    
    def suggest_workflow_optimizations(self, config: Dict[str, Any],
                                     workflow_stats: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        基于工作流统计数据建议优化
        
        Args:
            config: 当前配置
            workflow_stats: 工作流统计数据
            
        Returns:
            工作流优化建议
        """
        suggestions = []
        
        if not workflow_stats:
            return suggestions
        
        # 处理时间分析
        avg_time = workflow_stats.get("average_processing_time", 0)
        if avg_time > 300:  # 5分钟以上
            suggestions.append({
                "type": "performance",
                "title": "处理时间过长",
                "description": f"平均处理时间 {avg_time//60} 分钟，建议启用性能优化",
                "suggestion": "切换到快速模式或关闭重型功能",
                "config_changes": {
                    "processing_mode": "fast",
                    "use_spacy": False,
                    "ai_splitting": False
                }
            })
        
        # 错误率分析
        error_rate = workflow_stats.get("error_rate", 0)
        if error_rate > 0.1:  # 10%以上错误率
            suggestions.append({
                "type": "reliability",
                "title": "错误率偏高",
                "description": f"错误率 {error_rate*100:.1f}%，建议启用质量保证",
                "suggestion": "启用质量保证和智能处理功能",
                "config_changes": {
                    "quality_assurance": True,
                    "smart_processing": True,
                    "strict_timing": True
                }
            })
        
        # 输出质量分析
        quality_score = workflow_stats.get("average_quality_score", 0)
        if quality_score < 0.8:  # 80%以下质量分数
            suggestions.append({
                "type": "quality",
                "title": "输出质量有待提升",
                "description": f"平均质量分数 {quality_score*100:.1f}%，建议应用高质量配置",
                "suggestion": "启用AI功能和Netflix标准",
                "config_changes": {
                    "ai_splitting": True,
                    "max_length": 40,
                    "quality_level": "excellent"
                }
            })
        
        return suggestions
    
    def _generate_overall_assessment(self, validation_report: Dict[str, Any],
                                   context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成总体评估"""
        score = validation_report["overall_score"]
        error_count = validation_report["summary"]["errors"]
        warning_count = validation_report["summary"]["warnings"]
        
        if error_count > 0:
            status = "critical"
            message = f"配置存在 {error_count} 个严重错误，需要立即修复"
            priority = "high"
        elif score >= 90:
            status = "excellent"
            message = "配置质量优秀，可以直接使用"
            priority = "low"
        elif score >= 70:
            status = "good"
            message = f"配置质量良好，有 {warning_count} 个小问题可以优化"
            priority = "medium"
        else:
            status = "needs_improvement"
            message = f"配置需要改进，当前评分 {score}/100"
            priority = "high"
        
        return {
            "status": status,
            "message": message,
            "priority": priority,
            "score": score,
            "next_steps": self._get_next_steps(status, error_count, warning_count)
        }
    
    def _get_next_steps(self, status: str, error_count: int, warning_count: int) -> List[str]:
        """获取下一步建议"""
        steps = []
        
        if status == "critical":
            steps.extend([
                "立即修复所有配置错误",
                "重新验证配置",
                "考虑使用预设配置"
            ])
        elif status == "needs_improvement":
            steps.extend([
                "应用推荐的优化建议",
                "考虑升级到专业预设",
                "启用AI增强功能"
            ])
        elif status == "good":
            steps.extend([
                "可选择性修复警告",
                "考虑性能优化",
                "评估是否需要Netflix标准"
            ])
        else:  # excellent
            steps.extend([
                "配置已优化",
                "可以开始处理",
                "定期检查更新"
            ])
        
        return steps
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """计算配置哈希值"""
        import hashlib
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    def _is_netflix_compliant(self, config: Dict[str, Any]) -> bool:
        """检查是否符合Netflix标准"""
        return (config.get("max_length", 75) <= 40 and
                config.get("font_family") in ["Helvetica Neue", "Arial"] and
                config.get("background_opacity", 0) >= 0.8)
    
    def _needs_performance_optimization(self, config: Dict[str, Any]) -> bool:
        """检查是否需要性能优化"""
        return (config.get("processing_mode") == "quality" and
                config.get("use_spacy", False) and
                config.get("ai_splitting", False))
    
    def _has_ai_features(self, config: Dict[str, Any]) -> bool:
        """检查是否启用AI功能"""
        return any([
            config.get("ai_splitting", False),
            config.get("smart_processing", False),
            config.get("auto_timing", False)
        ])
