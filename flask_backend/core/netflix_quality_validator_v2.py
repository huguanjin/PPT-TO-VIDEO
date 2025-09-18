"""
Netflix字幕质量验证系统 V2 - 全面质量保证
基于VideoLingo标准，实现多维度自动化质量检查
集成字符权重、样式标准、语义分割的完整验证体系
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# 导入我们创建的核心模块
try:
    from .netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from .netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2
    from .netflix_semantic_splitter_v2 import NetflixSemanticSplitterV2, SplitResult
except ImportError:
    from netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2
    from netflix_semantic_splitter_v2 import NetflixSemanticSplitterV2, SplitResult

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    BASIC = "basic"           # 基础验证
    STANDARD = "standard"     # 标准验证
    NETFLIX = "netflix"       # Netflix级验证
    STRICT = "strict"         # 严格验证


class ValidationStatus(Enum):
    """验证状态"""
    PASSED = "passed"         # 通过
    WARNING = "warning"       # 警告
    FAILED = "failed"         # 失败
    ERROR = "error"           # 错误


@dataclass
class ValidationRule:
    """验证规则"""
    name: str                          # 规则名称
    description: str                   # 规则描述
    level: ValidationLevel             # 验证级别
    weight: float = 1.0                # 规则权重
    enabled: bool = True               # 是否启用
    auto_fix: bool = False             # 是否支持自动修复


@dataclass
class ValidationIssue:
    """验证问题"""
    rule_name: str                     # 规则名称
    status: ValidationStatus           # 状态
    message: str                       # 问题描述
    segment_index: Optional[int] = None # 问题段落索引
    segment_text: Optional[str] = None  # 问题段落文本
    suggested_fix: Optional[str] = None # 建议修复
    severity: float = 1.0              # 严重程度 (0-1)


@dataclass
class ValidationReport:
    """验证报告"""
    original_text: str                 # 原始文本
    segments: List[str]                # 分割段落
    total_score: float                 # 总分 (0-100)
    netflix_compliant: bool            # Netflix兼容性
    issues: List[ValidationIssue]      # 问题列表
    suggestions: List[str]             # 改进建议
    validation_time: datetime          # 验证时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class NetflixQualityValidatorV2:
    """Netflix字幕质量验证器 V2 - VideoLingo集成版本"""
    
    def __init__(
        self,
        char_calculator: Optional[NetflixCharWeightCalculatorV2] = None,
        style_manager: Optional[NetflixStylePresetsV2] = None,
        splitter: Optional[NetflixSemanticSplitterV2] = None,
        validation_level: ValidationLevel = ValidationLevel.NETFLIX
    ):
        # 初始化组件
        self.char_calculator = char_calculator or NetflixCharWeightCalculatorV2()
        self.style_manager = style_manager or NetflixStylePresetsV2()
        self.splitter = splitter or NetflixSemanticSplitterV2()
        self.validation_level = validation_level
        
        # 初始化验证规则
        self.validation_rules = self._init_validation_rules()
        
        logger.info(f"Netflix质量验证器V2已初始化 - 验证级别: {validation_level.value}")
    
    def _init_validation_rules(self) -> Dict[str, ValidationRule]:
        """初始化验证规则库"""
        rules = {
            # 字符长度验证
            "char_length_limit": ValidationRule(
                name="字符长度限制",
                description="检查每行是否超出36个有效中文字符限制",
                level=ValidationLevel.BASIC,
                weight=2.0,
                auto_fix=True
            ),
            
            # Netflix样式验证
            "netflix_font_color": ValidationRule(
                name="Netflix字体颜色",
                description="验证字体颜色是否为Netflix标准黄色(&H00FFFF)",
                level=ValidationLevel.NETFLIX,
                weight=1.5
            ),
            
            "netflix_font_size": ValidationRule(
                name="Netflix字体大小",
                description="验证字体大小是否为Netflix标准17px",
                level=ValidationLevel.NETFLIX,
                weight=1.0
            ),
            
            "netflix_outline": ValidationRule(
                name="Netflix描边样式",
                description="验证黑色描边和半透明背景配置",
                level=ValidationLevel.NETFLIX,
                weight=1.0
            ),
            
            # 语义完整性验证
            "semantic_completeness": ValidationRule(
                name="语义完整性",
                description="检查段落是否语义完整，避免断句不当",
                level=ValidationLevel.STANDARD,
                weight=1.5,
                auto_fix=True
            ),
            
            # 阅读速度验证
            "reading_speed": ValidationRule(
                name="阅读速度",
                description="检查字幕显示时间是否符合阅读速度要求",
                level=ValidationLevel.STANDARD,
                weight=1.2
            ),
            
            # 长度平衡验证
            "length_balance": ValidationRule(
                name="长度平衡",
                description="检查多行字幕的长度是否平衡",
                level=ValidationLevel.STANDARD,
                weight=1.0,
                auto_fix=True
            ),
            
            # 标点符号验证
            "punctuation_usage": ValidationRule(
                name="标点符号使用",
                description="检查标点符号使用是否规范",
                level=ValidationLevel.BASIC,
                weight=0.8
            ),
            
            # 字符质量验证
            "character_quality": ValidationRule(
                name="字符质量",
                description="检查是否包含异常字符或乱码",
                level=ValidationLevel.BASIC,
                weight=1.0
            ),
            
            # 行数限制验证
            "line_count_limit": ValidationRule(
                name="行数限制",
                description="检查字幕行数是否超出Netflix标准(最多2行)",
                level=ValidationLevel.NETFLIX,
                weight=1.5
            ),
            
            # 单行偏好验证
            "single_line_preference": ValidationRule(
                name="单行显示偏好",
                description="验证是否优先使用单行显示",
                level=ValidationLevel.NETFLIX,
                weight=1.0,
                auto_fix=True
            )
        }
        
        # 根据验证级别过滤规则
        if self.validation_level == ValidationLevel.BASIC:
            return {k: v for k, v in rules.items() if v.level in [ValidationLevel.BASIC]}
        elif self.validation_level == ValidationLevel.STANDARD:
            return {k: v for k, v in rules.items() if v.level in [ValidationLevel.BASIC, ValidationLevel.STANDARD]}
        elif self.validation_level == ValidationLevel.NETFLIX:
            return {k: v for k, v in rules.items() if v.level in [ValidationLevel.BASIC, ValidationLevel.STANDARD, ValidationLevel.NETFLIX]}
        else:  # STRICT
            return rules
    
    def validate_character_length(self, segments: List[str]) -> List[ValidationIssue]:
        """验证字符长度限制"""
        issues = []
        
        for i, segment in enumerate(segments):
            effective_chars = self.char_calculator.get_effective_chinese_chars(segment)
            is_compliant = self.char_calculator.is_netflix_compliant(segment)
            
            if not is_compliant:
                severity = min(1.0, (effective_chars - 36) / 10)  # 超出越多越严重
                
                issue = ValidationIssue(
                    rule_name="char_length_limit",
                    status=ValidationStatus.FAILED if effective_chars > 45 else ValidationStatus.WARNING,
                    message=f"第{i+1}段超出36字符限制 ({effective_chars}字符)",
                    segment_index=i,
                    segment_text=segment,
                    suggested_fix="建议重新分割或缩短文本",
                    severity=severity
                )
                issues.append(issue)
        
        return issues
    
    def validate_netflix_style(self, style_preset: str = "videolingo_netflix") -> List[ValidationIssue]:
        """验证Netflix样式标准"""
        issues = []
        
        style_config = self.style_manager.get_style_preset(style_preset)
        if not style_config:
            issues.append(ValidationIssue(
                rule_name="netflix_font_color",
                status=ValidationStatus.ERROR,
                message="无法获取样式配置",
                suggested_fix="检查样式预设配置",
                severity=1.0
            ))
            return issues
        
        # 验证字体颜色
        if style_config.font_color != "&H00FFFF":
            issues.append(ValidationIssue(
                rule_name="netflix_font_color",
                status=ValidationStatus.WARNING,
                message=f"字体颜色 {style_config.font_color} 不是Netflix标准黄色",
                suggested_fix="使用Netflix标准黄色 &H00FFFF",
                severity=0.8
            ))
        
        # 验证字体大小
        if style_config.font_size != 17:
            issues.append(ValidationIssue(
                rule_name="netflix_font_size",
                status=ValidationStatus.WARNING,
                message=f"字体大小 {style_config.font_size}px 不是Netflix标准17px",
                suggested_fix="使用Netflix标准字体大小 17px",
                severity=0.6
            ))
        
        # 验证描边样式
        if style_config.outline_color != "&H000000" or style_config.outline_width != 1:
            issues.append(ValidationIssue(
                rule_name="netflix_outline",
                status=ValidationStatus.WARNING,
                message="描边样式不符合Netflix标准",
                suggested_fix="使用黑色1px描边 + 半透明背景",
                severity=0.5
            ))
        
        return issues
    
    def validate_semantic_completeness(self, segments: List[str]) -> List[ValidationIssue]:
        """验证语义完整性"""
        issues = []
        
        for i, segment in enumerate(segments):
            segment_clean = segment.strip()
            
            # 检查是否以不完整的标点结尾
            if segment_clean and segment_clean[-1] in '，、':
                issues.append(ValidationIssue(
                    rule_name="semantic_completeness",
                    status=ValidationStatus.WARNING,
                    message=f"第{i+1}段可能语义不完整 (以逗号结尾)",
                    segment_index=i,
                    segment_text=segment,
                    suggested_fix="考虑与下一段合并或调整断句",
                    severity=0.4
                ))
            
            # 检查是否过短 (可能是断句不当)
            if len(segment_clean) < 3:
                issues.append(ValidationIssue(
                    rule_name="semantic_completeness",
                    status=ValidationStatus.WARNING,
                    message=f"第{i+1}段过短，可能断句不当",
                    segment_index=i,
                    segment_text=segment,
                    suggested_fix="考虑与相邻段落合并",
                    severity=0.6
                ))
        
        return issues
    
    def validate_length_balance(self, segments: List[str]) -> List[ValidationIssue]:
        """验证长度平衡"""
        issues = []
        
        if len(segments) <= 1:
            return issues
        
        # 计算长度差异
        lengths = [self.char_calculator.calc_precise_length(seg) for seg in segments]
        max_length = max(lengths)
        min_length = min(lengths)
        
        if max_length > 0:
            balance_ratio = min_length / max_length
            
            if balance_ratio < 0.5:  # 长度差异过大
                issues.append(ValidationIssue(
                    rule_name="length_balance",
                    status=ValidationStatus.WARNING,
                    message=f"段落长度不平衡 (比例: {balance_ratio:.2f})",
                    suggested_fix="调整段落分割以平衡长度",
                    severity=1.0 - balance_ratio
                ))
        
        return issues
    
    def validate_punctuation_usage(self, segments: List[str]) -> List[ValidationIssue]:
        """验证标点符号使用"""
        issues = []
        
        # 检查标点符号模式
        problematic_patterns = [
            (r'[。！？]{2,}', "重复句末标点"),
            (r'[，、]{2,}', "重复逗号或顿号"),
            (r'[""]{2,}', "重复引号"),
            (r'\.{3,}', "过多省略号"),
        ]
        
        for i, segment in enumerate(segments):
            for pattern, description in problematic_patterns:
                if re.search(pattern, segment):
                    issues.append(ValidationIssue(
                        rule_name="punctuation_usage",
                        status=ValidationStatus.WARNING,
                        message=f"第{i+1}段标点问题: {description}",
                        segment_index=i,
                        segment_text=segment,
                        suggested_fix="检查并修正标点符号使用",
                        severity=0.3
                    ))
        
        return issues
    
    def validate_character_quality(self, segments: List[str]) -> List[ValidationIssue]:
        """验证字符质量"""
        issues = []
        
        # 检查异常字符
        problematic_chars = ['�', '\x00', '\x01', '\x02', '\x03']  # 常见乱码字符
        
        for i, segment in enumerate(segments):
            for char in problematic_chars:
                if char in segment:
                    issues.append(ValidationIssue(
                        rule_name="character_quality",
                        status=ValidationStatus.ERROR,
                        message=f"第{i+1}段包含异常字符或乱码",
                        segment_index=i,
                        segment_text=segment,
                        suggested_fix="清理文本，移除异常字符",
                        severity=1.0
                    ))
        
        return issues
    
    def validate_line_count(self, segments: List[str]) -> List[ValidationIssue]:
        """验证行数限制"""
        issues = []
        
        max_lines = 2  # Netflix标准最多2行
        
        if len(segments) > max_lines:
            issues.append(ValidationIssue(
                rule_name="line_count_limit",
                status=ValidationStatus.WARNING,
                message=f"字幕行数 ({len(segments)}) 超出Netflix标准 (最多{max_lines}行)",
                suggested_fix="重新分割或合并段落以减少行数",
                severity=min(1.0, (len(segments) - max_lines) / 3)
            ))
        
        return issues
    
    def validate_single_line_preference(self, segments: List[str]) -> List[ValidationIssue]:
        """验证单行显示偏好"""
        issues = []
        
        if len(segments) > 1:
            # 检查是否可以合并为单行
            combined_text = ''.join(segments)
            if self.char_calculator.is_netflix_compliant(combined_text):
                issues.append(ValidationIssue(
                    rule_name="single_line_preference",
                    status=ValidationStatus.WARNING,
                    message="可以合并为单行显示以符合Netflix偏好",
                    suggested_fix=f"合并为: {combined_text}",
                    severity=0.3
                ))
        
        return issues
    
    def comprehensive_validate(
        self, 
        text: str, 
        segments: Optional[List[str]] = None,
        style_preset: str = "videolingo_netflix"
    ) -> ValidationReport:
        """全面质量验证"""
        # 如果没有提供分割结果，自动分割
        if segments is None:
            split_result = self.splitter.smart_split(text, style_preset)
            segments = split_result.segments
        
        all_issues = []
        
        # 执行所有启用的验证规则
        if "char_length_limit" in self.validation_rules and self.validation_rules["char_length_limit"].enabled:
            all_issues.extend(self.validate_character_length(segments))
        
        if any(rule in self.validation_rules for rule in ["netflix_font_color", "netflix_font_size", "netflix_outline"]):
            all_issues.extend(self.validate_netflix_style(style_preset))
        
        if "semantic_completeness" in self.validation_rules and self.validation_rules["semantic_completeness"].enabled:
            all_issues.extend(self.validate_semantic_completeness(segments))
        
        if "length_balance" in self.validation_rules and self.validation_rules["length_balance"].enabled:
            all_issues.extend(self.validate_length_balance(segments))
        
        if "punctuation_usage" in self.validation_rules and self.validation_rules["punctuation_usage"].enabled:
            all_issues.extend(self.validate_punctuation_usage(segments))
        
        if "character_quality" in self.validation_rules and self.validation_rules["character_quality"].enabled:
            all_issues.extend(self.validate_character_quality(segments))
        
        if "line_count_limit" in self.validation_rules and self.validation_rules["line_count_limit"].enabled:
            all_issues.extend(self.validate_line_count(segments))
        
        if "single_line_preference" in self.validation_rules and self.validation_rules["single_line_preference"].enabled:
            all_issues.extend(self.validate_single_line_preference(segments))
        
        # 计算总分
        total_score = self._calculate_total_score(all_issues)
        
        # 判断Netflix兼容性
        netflix_compliant = all(
            issue.status != ValidationStatus.FAILED 
            for issue in all_issues 
            if issue.rule_name in ["char_length_limit", "netflix_font_color", "line_count_limit"]
        )
        
        # 生成改进建议
        suggestions = self._generate_suggestions(all_issues)
        
        return ValidationReport(
            original_text=text,
            segments=segments,
            total_score=total_score,
            netflix_compliant=netflix_compliant,
            issues=all_issues,
            suggestions=suggestions,
            validation_time=datetime.now(),
            metadata={
                'validation_level': self.validation_level.value,
                'total_rules_checked': len([r for r in self.validation_rules.values() if r.enabled]),
                'style_preset': style_preset,
                'segment_count': len(segments)
            }
        )
    
    def _calculate_total_score(self, issues: List[ValidationIssue]) -> float:
        """计算总质量评分 (0-100)"""
        if not issues:
            return 100.0
        
        total_deduction = 0.0
        total_weight = 0.0
        
        for issue in issues:
            rule = self.validation_rules.get(issue.rule_name)
            if rule:
                weight = rule.weight
                total_weight += weight
                
                # 根据状态计算扣分
                if issue.status == ValidationStatus.ERROR:
                    deduction = weight * issue.severity * 0.8
                elif issue.status == ValidationStatus.FAILED:
                    deduction = weight * issue.severity * 0.6
                elif issue.status == ValidationStatus.WARNING:
                    deduction = weight * issue.severity * 0.3
                else:
                    deduction = 0
                
                total_deduction += deduction
        
        # 计算最终得分
        if total_weight > 0:
            score = max(0, 100 - (total_deduction / total_weight * 100))
        else:
            score = 100.0
        
        return round(score, 1)
    
    def _generate_suggestions(self, issues: List[ValidationIssue]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 按严重程度排序问题
        critical_issues = [i for i in issues if i.status in [ValidationStatus.ERROR, ValidationStatus.FAILED]]
        warning_issues = [i for i in issues if i.status == ValidationStatus.WARNING]
        
        if critical_issues:
            suggestions.append("🚨 发现严重问题，需要立即修复:")
            for issue in critical_issues[:3]:  # 只显示前3个最严重的
                if issue.suggested_fix:
                    suggestions.append(f"  • {issue.suggested_fix}")
        
        if warning_issues:
            suggestions.append("⚠️ 发现可优化项:")
            for issue in warning_issues[:3]:  # 只显示前3个警告
                if issue.suggested_fix:
                    suggestions.append(f"  • {issue.suggested_fix}")
        
        # 通用建议
        if not critical_issues and not warning_issues:
            suggestions.append("✅ 字幕质量优秀，符合Netflix标准！")
        elif len(critical_issues) == 0:
            suggestions.append("💡 建议进一步优化警告项以达到完美质量")
        
        return suggestions


# 工厂函数
def create_netflix_validator(
    validation_level: ValidationLevel = ValidationLevel.NETFLIX,
    char_config: Optional[NetflixCharacterConfig] = None
) -> NetflixQualityValidatorV2:
    """创建Netflix质量验证器"""
    char_calculator = NetflixCharWeightCalculatorV2(char_config)
    style_manager = NetflixStylePresetsV2()
    splitter = NetflixSemanticSplitterV2(char_calculator, style_manager)
    
    return NetflixQualityValidatorV2(
        char_calculator=char_calculator,
        style_manager=style_manager,
        splitter=splitter,
        validation_level=validation_level
    )


# 测试函数
def test_netflix_quality_validator():
    """测试Netflix质量验证器"""
    validator = create_netflix_validator(ValidationLevel.NETFLIX)
    
    print("✅ Netflix质量验证器V2测试结果：")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "优质字幕",
            "text": "这是一个符合Netflix标准的优质字幕。"
        },
        {
            "name": "过长字幕",
            "text": "这是一个非常长的字幕文本，超出了Netflix的36个中文字符限制，需要进行分割处理才能符合标准要求。"
        },
        {
            "name": "标点问题",
            "text": "这个字幕有标点问题，，，比如重复的逗号和省略号......"
        },
        {
            "name": "多段字幕",
            "text": "第一段字幕内容比较短。第二段字幕内容稍微长一些，但是仍然在合理范围内。"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 测试案例 {i}: {case['name']}")
        print(f"   原文: {case['text']}")
        
        report = validator.comprehensive_validate(case['text'])
        
        print(f"   质量评分: {report.total_score}/100")
        print(f"   Netflix兼容: {'✅' if report.netflix_compliant else '❌'}")
        print(f"   分割段数: {len(report.segments)}")
        
        for j, segment in enumerate(report.segments, 1):
            effective_chars = validator.char_calculator.get_effective_chinese_chars(segment)
            print(f"     第{j}段: {segment} ({effective_chars}字符)")
        
        if report.issues:
            print(f"   发现问题: {len(report.issues)}个")
            for issue in report.issues[:3]:  # 只显示前3个问题
                status_icon = {"failed": "❌", "error": "🚨", "warning": "⚠️"}.get(issue.status.value, "ℹ️")
                print(f"     {status_icon} {issue.message}")
        
        if report.suggestions:
            print(f"   改进建议:")
            for suggestion in report.suggestions[:2]:  # 只显示前2个建议
                print(f"     {suggestion}")


if __name__ == "__main__":
    test_netflix_quality_validator()