"""
配置验证和优化建议系统
提供智能的配置验证、性能分析和个性化优化建议
类似VideoLingo的智能配置体验
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """验证级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class OptimizationType(Enum):
    """优化类型"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    USER_EXPERIENCE = "user_experience"
    COMPATIBILITY = "compatibility"
    ACCESSIBILITY = "accessibility"

@dataclass
class ValidationResult:
    """验证结果"""
    level: ValidationLevel
    message: str
    field: str
    current_value: Any
    suggested_value: Optional[Any] = None
    reason: Optional[str] = None
    impact: Optional[str] = None

@dataclass
class OptimizationSuggestion:
    """优化建议"""
    type: OptimizationType
    title: str
    description: str
    before_config: Dict[str, Any]
    after_config: Dict[str, Any]
    expected_improvement: str
    difficulty: str  # "easy", "medium", "hard"
    priority: int  # 1-10, 10最高优先级

class ConfigValidator:
    """配置验证器 - 智能配置验证和优化建议"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.optimization_patterns = self._load_optimization_patterns()
        
    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            "max_length": {
                "type": "integer",
                "min": 10,
                "max": 200,
                "optimal_range": (40, 75),
                "netflix_standard": 40,
                "warnings": {
                    "too_short": "字幕长度过短可能导致阅读困难",
                    "too_long": "字幕长度过长可能影响观看体验",
                    "non_netflix": "不符合Netflix标准长度"
                }
            },
            
            "target_multiplier": {
                "type": "float",
                "min": 0.5,
                "max": 3.0,
                "optimal_range": (1.0, 1.5),
                "default": 1.2,
                "warnings": {
                    "too_low": "倍数过低可能导致字幕过短",
                    "too_high": "倍数过高可能影响字幕质量"
                }
            },
            
            "font_size": {
                "type": "integer",
                "min": 12,
                "max": 48,
                "optimal_range": (18, 28),
                "accessibility_min": 20,
                "warnings": {
                    "too_small": "字体过小影响可读性",
                    "too_large": "字体过大影响画面美观",
                    "accessibility": "不符合无障碍访问标准"
                }
            },
            
            "processing_mode": {
                "type": "enum",
                "values": ["fast", "balanced", "quality"],
                "recommended": "balanced",
                "performance_impact": {
                    "fast": "低质量但快速",
                    "balanced": "质量和速度平衡",
                    "quality": "高质量但耗时"
                }
            }
        }
    
    def _load_optimization_patterns(self) -> List[Dict[str, Any]]:
        """加载优化模式"""
        return [
            {
                "name": "netflix_optimization",
                "type": OptimizationType.QUALITY,
                "title": "Netflix级别优化",
                "description": "应用Netflix专业字幕标准",
                "triggers": ["max_length > 75", "font_size < 18"],
                "adjustments": {
                    "max_length": 40,
                    "font_size": 22,
                    "font_family": "Helvetica Neue",
                    "background_opacity": 0.85,
                    "outline_width": 3
                },
                "expected_improvement": "专业级字幕质量，提升观看体验",
                "difficulty": "easy",
                "priority": 9
            },
            
            {
                "name": "performance_optimization",
                "type": OptimizationType.PERFORMANCE,
                "title": "性能优化",
                "description": "优化处理速度和资源使用",
                "triggers": ["use_spacy == True", "processing_mode == 'quality'"],
                "adjustments": {
                    "use_spacy": False,
                    "processing_mode": "balanced",
                    "use_dp_algorithm": True,
                    "ai_splitting": False
                },
                "expected_improvement": "处理速度提升50-70%",
                "difficulty": "easy",
                "priority": 7
            },
            
            {
                "name": "accessibility_optimization",
                "type": OptimizationType.ACCESSIBILITY,
                "title": "无障碍访问优化",
                "description": "提升视觉障碍用户的使用体验",
                "triggers": ["font_size < 20", "outline_width < 2"],
                "adjustments": {
                    "font_size": 24,
                    "outline_width": 3,
                    "outline_color": "#000000",
                    "background_opacity": 0.9,
                    "high_contrast": True
                },
                "expected_improvement": "符合WCAG 2.1 AA标准",
                "difficulty": "easy",
                "priority": 8
            },
            
            {
                "name": "mobile_optimization",
                "type": OptimizationType.USER_EXPERIENCE,
                "title": "移动端优化",
                "description": "优化移动设备观看体验",
                "triggers": ["font_size < 18", "max_length > 50"],
                "adjustments": {
                    "font_size": 20,
                    "max_length": 35,
                    "target_multiplier": 1.0,
                    "smart_line_breaking": True,
                    "mobile_friendly": True
                },
                "expected_improvement": "移动端可读性提升60%",
                "difficulty": "medium",
                "priority": 6
            },
            
            {
                "name": "ai_enhancement",
                "type": OptimizationType.QUALITY,
                "title": "AI智能增强",
                "description": "启用AI功能提升字幕质量",
                "triggers": ["ai_splitting == False", "smart_processing == False"],
                "adjustments": {
                    "ai_splitting": True,
                    "smart_processing": True,
                    "auto_timing": True,
                    "quality_assurance": True,
                    "smart_line_breaking": True
                },
                "expected_improvement": "字幕质量和智能化程度显著提升",
                "difficulty": "medium",
                "priority": 8
            }
        ]
    
    def validate_config(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """
        验证配置
        
        Args:
            config: 待验证的配置
            
        Returns:
            验证结果列表
        """
        results = []
        
        for field, rules in self.validation_rules.items():
            if field not in config:
                continue
                
            value = config[field]
            field_results = self._validate_field(field, value, rules)
            results.extend(field_results)
        
        # 添加组合验证
        combo_results = self._validate_combinations(config)
        results.extend(combo_results)
        
        return results
    
    def _validate_field(self, field: str, value: Any, rules: Dict[str, Any]) -> List[ValidationResult]:
        """验证单个字段"""
        results = []
        
        # 类型验证
        if rules["type"] == "integer" and not isinstance(value, int):
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"{field} 必须是整数",
                field=field,
                current_value=value,
                suggested_value=int(value) if str(value).isdigit() else rules.get("default")
            ))
            return results
        
        # 范围验证
        if "min" in rules and value < rules["min"]:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"{field} 值过小",
                field=field,
                current_value=value,
                suggested_value=rules["min"],
                reason=f"最小值应为 {rules['min']}"
            ))
        
        if "max" in rules and value > rules["max"]:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"{field} 值过大",
                field=field,
                current_value=value,
                suggested_value=rules["max"],
                reason=f"最大值应为 {rules['max']}"
            ))
        
        # 最优范围检查
        if "optimal_range" in rules:
            min_opt, max_opt = rules["optimal_range"]
            if not (min_opt <= value <= max_opt):
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"{field} 不在最优范围内",
                    field=field,
                    current_value=value,
                    suggested_value=(min_opt + max_opt) // 2,
                    reason=f"建议范围: {min_opt}-{max_opt}",
                    impact="可能影响效果"
                ))
        
        # Netflix标准检查
        if "netflix_standard" in rules and value != rules["netflix_standard"]:
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message=f"{field} 不符合Netflix标准",
                field=field,
                current_value=value,
                suggested_value=rules["netflix_standard"],
                reason="Netflix标准可提供更专业的体验"
            ))
        
        return results
    
    def _validate_combinations(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """验证字段组合"""
        results = []
        
        # 性能vs质量冲突检查
        if config.get("processing_mode") == "quality" and config.get("use_spacy", False):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="高质量模式+Spacy会显著影响性能",
                field="processing_mode",
                current_value="quality + spacy",
                suggested_value="balanced",
                reason="建议使用平衡模式或关闭Spacy",
                impact="处理时间可能增加2-3倍"
            ))
        
        # 字体大小和长度匹配检查
        font_size = config.get("font_size", 18)
        max_length = config.get("max_length", 75)
        if font_size >= 24 and max_length > 40:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="大字体配长字幕可能导致显示问题",
                field="font_size",
                current_value=f"字体{font_size}, 长度{max_length}",
                suggested_value="调整其中一项",
                reason="大字体应配较短字幕",
                impact="可能出现换行或遮挡问题"
            ))
        
        return results
    
    def generate_optimization_suggestions(self, config: Dict[str, Any], 
                                        user_preferences: Optional[Dict[str, Any]] = None) -> List[OptimizationSuggestion]:
        """
        生成优化建议
        
        Args:
            config: 当前配置
            user_preferences: 用户偏好（性能优先、质量优先等）
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        for pattern in self.optimization_patterns:
            if self._should_apply_optimization(config, pattern, user_preferences):
                suggestion = self._create_optimization_suggestion(config, pattern)
                suggestions.append(suggestion)
        
        # 按优先级排序
        suggestions.sort(key=lambda x: x.priority, reverse=True)
        
        return suggestions
    
    def _should_apply_optimization(self, config: Dict[str, Any], 
                                 pattern: Dict[str, Any],
                                 user_preferences: Optional[Dict[str, Any]] = None) -> bool:
        """检查是否应该应用优化"""
        triggers = pattern.get("triggers", [])
        
        for trigger in triggers:
            if self._evaluate_trigger(config, trigger):
                return True
        
        # 考虑用户偏好
        if user_preferences:
            pattern_type = pattern.get("type")
            if pattern_type and user_preferences.get(f"prefer_{pattern_type.value}", False):
                return True
        
        return False
    
    def _evaluate_trigger(self, config: Dict[str, Any], trigger: str) -> bool:
        """评估触发条件"""
        try:
            # 简单的条件评估
            if ">" in trigger:
                field, value = trigger.split(" > ")
                return config.get(field.strip(), 0) > float(value.strip())
            elif "<" in trigger:
                field, value = trigger.split(" < ")
                return config.get(field.strip(), 0) < float(value.strip())
            elif "==" in trigger:
                field, value = trigger.split(" == ")
                field_value = config.get(field.strip())
                expected_value = value.strip().strip("'\"")
                if expected_value == "True":
                    expected_value = True
                elif expected_value == "False":
                    expected_value = False
                return field_value == expected_value
            
        except Exception as e:
            logger.warning(f"评估触发条件失败: {trigger}, 错误: {e}")
            
        return False
    
    def _create_optimization_suggestion(self, config: Dict[str, Any], 
                                      pattern: Dict[str, Any]) -> OptimizationSuggestion:
        """创建优化建议"""
        before_config = {k: config.get(k) for k in pattern["adjustments"].keys() if k in config}
        after_config = pattern["adjustments"].copy()
        
        return OptimizationSuggestion(
            type=pattern["type"],
            title=pattern["title"],
            description=pattern["description"],
            before_config=before_config,
            after_config=after_config,
            expected_improvement=pattern["expected_improvement"],
            difficulty=pattern["difficulty"],
            priority=pattern["priority"]
        )
    
    def apply_optimization(self, config: Dict[str, Any], 
                          suggestion: OptimizationSuggestion) -> Dict[str, Any]:
        """
        应用优化建议
        
        Args:
            config: 原始配置
            suggestion: 优化建议
            
        Returns:
            优化后的配置
        """
        optimized_config = config.copy()
        optimized_config.update(suggestion.after_config)
        
        # 添加优化元数据
        if "_optimizations" not in optimized_config:
            optimized_config["_optimizations"] = []
        
        optimized_config["_optimizations"].append({
            "type": suggestion.type.value,
            "title": suggestion.title,
            "applied_at": datetime.now().isoformat(),
            "changes": suggestion.after_config
        })
        
        return optimized_config
    
    def generate_validation_report(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整的验证报告
        
        Args:
            config: 配置
            
        Returns:
            验证报告
        """
        validation_results = self.validate_config(config)
        optimization_suggestions = self.generate_optimization_suggestions(config)
        
        # 统计信息
        error_count = sum(1 for r in validation_results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in validation_results if r.level == ValidationLevel.WARNING)
        
        # 生成评分
        score = self._calculate_config_score(validation_results, config)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_score": score,
            "status": "excellent" if score >= 90 else "good" if score >= 70 else "needs_improvement",
            "summary": {
                "total_issues": len(validation_results),
                "errors": error_count,
                "warnings": warning_count,
                "suggestions": len(optimization_suggestions)
            },
            "validation_results": [
                {
                    "level": r.level.value,
                    "message": r.message,
                    "field": r.field,
                    "current_value": r.current_value,
                    "suggested_value": r.suggested_value,
                    "reason": r.reason,
                    "impact": r.impact
                }
                for r in validation_results
            ],
            "optimization_suggestions": [
                {
                    "type": s.type.value,
                    "title": s.title,
                    "description": s.description,
                    "before_config": s.before_config,
                    "after_config": s.after_config,
                    "expected_improvement": s.expected_improvement,
                    "difficulty": s.difficulty,
                    "priority": s.priority
                }
                for s in optimization_suggestions
            ],
            "recommendations": self._generate_recommendations(validation_results, optimization_suggestions)
        }
    
    def _calculate_config_score(self, validation_results: List[ValidationResult], 
                               config: Dict[str, Any]) -> int:
        """计算配置评分"""
        base_score = 100
        
        for result in validation_results:
            if result.level == ValidationLevel.ERROR:
                base_score -= 15
            elif result.level == ValidationLevel.WARNING:
                base_score -= 5
            elif result.level == ValidationLevel.INFO:
                base_score -= 2
        
        # 功能完整性加分
        if config.get("ai_splitting", False):
            base_score += 5
        if config.get("smart_processing", False):
            base_score += 5
        if config.get("quality_assurance", False):
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _generate_recommendations(self, validation_results: List[ValidationResult],
                                 optimization_suggestions: List[OptimizationSuggestion]) -> List[str]:
        """生成推荐建议"""
        recommendations = []
        
        # 错误级别建议
        errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
        if errors:
            recommendations.append(f"发现 {len(errors)} 个严重问题，建议立即修复")
        
        # 高优先级优化建议
        high_priority = [s for s in optimization_suggestions if s.priority >= 8]
        if high_priority:
            recommendations.append(f"有 {len(high_priority)} 个高优先级优化建议值得考虑")
        
        # Netflix标准建议
        netflix_issues = [r for r in validation_results if "Netflix" in r.message]
        if netflix_issues:
            recommendations.append("考虑应用Netflix标准以获得专业级字幕质量")
        
        # 性能优化建议
        performance_suggestions = [s for s in optimization_suggestions if s.type == OptimizationType.PERFORMANCE]
        if performance_suggestions:
            recommendations.append("可通过性能优化提升处理速度")
        
        return recommendations
