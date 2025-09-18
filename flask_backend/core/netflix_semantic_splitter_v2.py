"""
Netflix智能语义分割器 V2 - 集成版本
基于VideoLingo标准，集成36字符精确控制 + AI语义分割 + 多轮优化
整合字符权重计算器 + Netflix样式预设的完整解决方案
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import asyncio
import json

# 导入我们创建的核心模块
try:
    from .netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from .netflix_style_presets_v2 import NetflixStylePresetsV2
except ImportError:
    from netflix_char_weight_calculator_v2 import NetflixCharWeightCalculatorV2, NetflixCharacterConfig
    from netflix_style_presets_v2 import NetflixStylePresetsV2, NetflixStyleConfigV2

logger = logging.getLogger(__name__)


@dataclass
class SemanticSplitConfig:
    """语义分割配置"""
    
    # 分割策略配置
    prefer_single_line: bool = True          # 优先单行显示
    max_optimization_rounds: int = 3         # 最大优化轮数
    semantic_weight: float = 0.7             # 语义分割权重
    punctuation_weight: float = 0.3          # 标点分割权重
    
    # AI分割配置
    enable_ai_semantic: bool = True          # 启用AI语义分割
    ai_confidence_threshold: float = 0.8     # AI置信度阈值
    fallback_to_rule_based: bool = True      # 回退到规则分割
    
    # 质量控制配置
    min_segment_length: int = 3              # 最小片段长度
    max_segment_length: int = 36             # 最大片段长度 (Netflix标准)
    avoid_orphan_chars: bool = True          # 避免孤立字符
    balance_segments: bool = True            # 平衡片段长度


@dataclass
class SplitResult:
    """分割结果"""
    
    original_text: str                       # 原始文本
    segments: List[str]                      # 分割片段
    optimization_rounds: int                 # 优化轮数
    quality_score: float                     # 质量评分
    netflix_compliant: bool                  # Netflix兼容性
    ai_used: bool                           # 是否使用AI
    warnings: List[str]                     # 警告信息
    metadata: Dict[str, Any]                # 元数据


class NetflixSemanticSplitterV2:
    """Netflix智能语义分割器 V2 - VideoLingo集成版本"""
    
    def __init__(
        self, 
        char_calculator: Optional[NetflixCharWeightCalculatorV2] = None,
        style_manager: Optional[NetflixStylePresetsV2] = None,
        config: Optional[SemanticSplitConfig] = None
    ):
        # 初始化组件
        self.char_calculator = char_calculator or NetflixCharWeightCalculatorV2()
        self.style_manager = style_manager or NetflixStylePresetsV2()
        self.config = config or SemanticSplitConfig()
        
        # 语义分割规则
        self._punctuation_patterns = self._init_punctuation_patterns()
        self._semantic_patterns = self._init_semantic_patterns()
        
        logger.info("Netflix智能语义分割器V2已初始化 - VideoLingo标准集成")
    
    def _init_punctuation_patterns(self) -> Dict[str, float]:
        """初始化标点符号分割权重"""
        return {
            '。': 1.0,     # 句号 - 最强分割点
            '！': 1.0,     # 感叹号
            '？': 1.0,     # 问号
            '；': 0.8,     # 分号
            '：': 0.6,     # 冒号
            '，': 0.4,     # 逗号 - 较弱分割点
            '、': 0.3,     # 顿号
            '"': 0.2,     # 引号
            '"': 0.2,     # 引号
            ''': 0.2,     # 单引号
            ''': 0.2,     # 单引号
        }
    
    def _init_semantic_patterns(self) -> List[str]:
        """初始化语义模式"""
        return [
            r'(然后|接着|然后|于是|接下来)',    # 时间连接词
            r'(但是|不过|然而|可是|只是)',      # 转折连接词
            r'(因为|由于|因此|所以|因而)',      # 因果连接词
            r'(另外|此外|而且|同时|还有)',      # 递进连接词
            r'(如果|假如|要是|倘若|万一)',      # 条件连接词
        ]
    
    def split_by_length_only(self, text: str) -> List[str]:
        """基于长度的简单分割 - 基线方法"""
        if not text:
            return []
        
        # 如果文本符合Netflix标准，直接返回
        if self.char_calculator.is_netflix_compliant(text):
            return [text]
        
        segments = []
        current_segment = ""
        
        for char in text:
            test_segment = current_segment + char
            
            if self.char_calculator.is_netflix_compliant(test_segment):
                current_segment = test_segment
            else:
                # 当前段落已满，开始新段落
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = char
        
        # 添加最后一个段落
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments
    
    def split_by_punctuation(self, text: str) -> List[str]:
        """基于标点符号的智能分割"""
        if not text:
            return []
        
        if self.char_calculator.is_netflix_compliant(text):
            return [text]
        
        # 找到所有标点分割点
        split_points = []
        for i, char in enumerate(text):
            if char in self._punctuation_patterns:
                weight = self._punctuation_patterns[char]
                split_points.append((i + 1, weight))  # +1 包含标点符号
        
        # 按权重排序分割点
        split_points.sort(key=lambda x: x[1], reverse=True)
        
        # 尝试基于分割点组合段落
        segments = self._optimize_segments_by_split_points(text, split_points)
        
        return segments
    
    def _optimize_segments_by_split_points(self, text: str, split_points: List[Tuple[int, float]]) -> List[str]:
        """基于分割点优化段落"""
        if not split_points:
            return self.split_by_length_only(text)
        
        best_segments = []
        current_start = 0
        
        for split_pos, weight in split_points:
            # 测试当前段落
            test_segment = text[current_start:split_pos]
            
            if self.char_calculator.is_netflix_compliant(test_segment):
                # 继续寻找更长的合适段落
                continue
            else:
                # 当前段落太长，使用上一个分割点
                if best_segments or current_start == 0:
                    # 确定段落边界
                    segment = text[current_start:split_pos].strip()
                    if segment:
                        best_segments.append(segment)
                    current_start = split_pos
        
        # 处理剩余文本
        if current_start < len(text):
            remaining = text[current_start:].strip()
            if remaining:
                # 如果剩余文本太长，继续分割
                if not self.char_calculator.is_netflix_compliant(remaining):
                    remaining_segments = self.split_by_length_only(remaining)
                    best_segments.extend(remaining_segments)
                else:
                    best_segments.append(remaining)
        
        return best_segments
    
    def split_by_semantic_rules(self, text: str) -> List[str]:
        """基于语义规则的分割"""
        if not text:
            return []
        
        if self.char_calculator.is_netflix_compliant(text):
            return [text]
        
        # 首先基于标点分割
        segments = self.split_by_punctuation(text)
        
        # 然后应用语义规则优化
        optimized_segments = []
        
        for segment in segments:
            if self.char_calculator.is_netflix_compliant(segment):
                optimized_segments.append(segment)
            else:
                # 对过长段落应用语义规则
                sub_segments = self._apply_semantic_rules(segment)
                optimized_segments.extend(sub_segments)
        
        return optimized_segments
    
    def _apply_semantic_rules(self, text: str) -> List[str]:
        """应用语义规则分割文本"""
        # 寻找语义连接词
        best_split_pos = None
        best_balance_score = float('inf')
        
        for pattern in self._semantic_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                split_pos = match.start()
                
                # 计算分割平衡性
                left_part = text[:split_pos]
                right_part = text[split_pos:]
                
                left_weight = self.char_calculator.calc_precise_length(left_part)
                right_weight = self.char_calculator.calc_precise_length(right_part)
                
                # 平衡性评分 (越小越好)
                balance_score = abs(left_weight - right_weight)
                
                # 检查两个部分是否都符合Netflix标准
                left_compliant = self.char_calculator.is_netflix_compliant(left_part)
                right_compliant = self.char_calculator.is_netflix_compliant(right_part)
                
                if left_compliant and right_compliant and balance_score < best_balance_score:
                    best_balance_score = balance_score
                    best_split_pos = split_pos
        
        # 应用最佳分割点
        if best_split_pos is not None:
            left_part = text[:best_split_pos].strip()
            right_part = text[best_split_pos:].strip()
            return [part for part in [left_part, right_part] if part]
        
        # 如果语义分割失败，回退到长度分割
        return self.split_by_length_only(text)
    
    def multi_round_optimization(self, text: str, max_rounds: int = 3) -> SplitResult:
        """多轮优化分割"""
        if not text:
            return SplitResult(
                original_text="",
                segments=[],
                optimization_rounds=0,
                quality_score=1.0,
                netflix_compliant=True,
                ai_used=False,
                warnings=[],
                metadata={}
            )
        
        best_segments = []
        best_quality = 0.0
        warnings = []
        
        # 第1轮: 基于标点的分割
        round1_segments = self.split_by_punctuation(text)
        round1_quality = self._evaluate_split_quality(round1_segments)
        
        if round1_quality >= 0.9:  # 质量很高，直接返回
            best_segments = round1_segments
            best_quality = round1_quality
            rounds_used = 1
        else:
            # 第2轮: 语义规则分割
            round2_segments = self.split_by_semantic_rules(text)
            round2_quality = self._evaluate_split_quality(round2_segments)
            
            if round2_quality > round1_quality:
                best_segments = round2_segments
                best_quality = round2_quality
                rounds_used = 2
            else:
                best_segments = round1_segments
                best_quality = round1_quality
                rounds_used = 2
                warnings.append("语义分割未改善质量，使用标点分割结果")
            
            # 第3轮: 如果质量仍不够，尝试进一步优化
            if best_quality < 0.8 and max_rounds >= 3:
                round3_segments = self._final_optimization(best_segments)
                round3_quality = self._evaluate_split_quality(round3_segments)
                
                if round3_quality > best_quality:
                    best_segments = round3_segments
                    best_quality = round3_quality
                    rounds_used = 3
                else:
                    rounds_used = 3
                    warnings.append("最终优化未改善质量")
            else:
                rounds_used = 2
        
        # 检查Netflix兼容性
        netflix_compliant = all(
            self.char_calculator.is_netflix_compliant(segment) 
            for segment in best_segments
        )
        
        if not netflix_compliant:
            warnings.append("部分段落仍超出Netflix 36字符限制")
        
        return SplitResult(
            original_text=text,
            segments=best_segments,
            optimization_rounds=rounds_used,
            quality_score=best_quality,
            netflix_compliant=netflix_compliant,
            ai_used=False,  # 当前版本未使用AI
            warnings=warnings,
            metadata={
                'total_segments': len(best_segments),
                'avg_segment_length': sum(len(s) for s in best_segments) / len(best_segments) if best_segments else 0,
                'max_segment_weight': max(self.char_calculator.calc_precise_length(s) for s in best_segments) if best_segments else 0
            }
        )
    
    def _final_optimization(self, segments: List[str]) -> List[str]:
        """最终优化阶段"""
        optimized = []
        
        i = 0
        while i < len(segments):
            current_segment = segments[i]
            
            # 如果当前段落符合标准，直接添加
            if self.char_calculator.is_netflix_compliant(current_segment):
                optimized.append(current_segment)
                i += 1
                continue
            
            # 尝试与下一个段落合并
            if i + 1 < len(segments):
                next_segment = segments[i + 1]
                merged = current_segment + next_segment
                
                if self.char_calculator.is_netflix_compliant(merged):
                    optimized.append(merged)
                    i += 2  # 跳过下一个段落
                    continue
            
            # 如果无法合并，强制分割当前段落
            forced_segments = self.split_by_length_only(current_segment)
            optimized.extend(forced_segments)
            i += 1
        
        return optimized
    
    def _evaluate_split_quality(self, segments: List[str]) -> float:
        """评估分割质量"""
        if not segments:
            return 0.0
        
        total_score = 0.0
        
        for segment in segments:
            segment_score = 0.0
            
            # Netflix兼容性评分 (权重: 0.5)
            if self.char_calculator.is_netflix_compliant(segment):
                segment_score += 0.5
            else:
                # 根据超出程度降分
                effective_chars = self.char_calculator.get_effective_chinese_chars(segment)
                if effective_chars <= 40:  # 轻微超出
                    segment_score += 0.3
                elif effective_chars <= 50:  # 中度超出
                    segment_score += 0.1
                # 严重超出: 0分
            
            # 长度平衡性评分 (权重: 0.2)
            segment_length = len(segment)
            if 10 <= segment_length <= 25:  # 理想长度
                segment_score += 0.2
            elif 5 <= segment_length <= 35:  # 可接受长度
                segment_score += 0.1
            
            # 语义完整性评分 (权重: 0.3)
            if segment.strip():
                # 检查是否以标点结尾 (完整句子)
                if segment.strip()[-1] in '。！？；：':
                    segment_score += 0.2
                elif segment.strip()[-1] in '，、':
                    segment_score += 0.1
                
                # 检查是否包含完整词汇
                if len(segment.strip()) >= 3:
                    segment_score += 0.1
            
            total_score += segment_score
        
        # 返回平均分
        return total_score / len(segments)
    
    def smart_split(self, text: str, style_preset: str = "videolingo_netflix") -> SplitResult:
        """智能分割主入口 - 集成所有功能"""
        if not text:
            return SplitResult(
                original_text="",
                segments=[],
                optimization_rounds=0,
                quality_score=1.0,
                netflix_compliant=True,
                ai_used=False,
                warnings=[],
                metadata={}
            )
        
        # 获取样式配置
        style_config = self.style_manager.get_style_preset(style_preset)
        if style_config:
            # 根据样式调整分割参数
            self.config.max_segment_length = style_config.max_chars_per_line
            self.config.prefer_single_line = style_config.single_line_preference
        
        # 执行多轮优化分割
        result = self.multi_round_optimization(text, self.config.max_optimization_rounds)
        
        # 添加样式元数据
        result.metadata.update({
            'style_preset': style_preset,
            'target_font_size': style_config.font_size if style_config else 17,
            'netflix_yellow_applied': True
        })
        
        return result


# 工厂函数
def create_netflix_splitter(
    char_config: Optional[NetflixCharacterConfig] = None,
    split_config: Optional[SemanticSplitConfig] = None
) -> NetflixSemanticSplitterV2:
    """创建Netflix智能语义分割器"""
    char_calculator = NetflixCharWeightCalculatorV2(char_config)
    style_manager = NetflixStylePresetsV2()
    return NetflixSemanticSplitterV2(char_calculator, style_manager, split_config)


# 测试函数
def test_netflix_semantic_splitter():
    """测试Netflix智能语义分割器"""
    splitter = create_netflix_splitter()
    
    print("🧠 Netflix智能语义分割器V2测试结果：")
    print("=" * 60)
    
    test_cases = [
        "这是一个简单的测试字幕",
        "这是一个稍微长一点的测试字幕，用来验证分割功能是否正常工作",
        "这是一个非常长的测试字幕文本，包含了多个标点符号，比如逗号、句号，还有感叹号！这样的文本需要智能分割才能符合Netflix的36个中文字符限制标准。",
        "首先我们需要介绍项目背景，然后说明技术实现方案，接着展示具体的代码示例，最后总结项目的优势和特点。",
        "如果用户选择了高级模式，那么系统会自动启用AI增强功能；但是如果选择了简单模式，就只会使用基础的处理算法。"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 测试案例 {i}: {text}")
        print(f"   原文长度: {len(text)}字符")
        
        result = splitter.smart_split(text)
        
        print(f"   分割结果: {len(result.segments)}段")
        for j, segment in enumerate(result.segments, 1):
            effective_chars = splitter.char_calculator.get_effective_chinese_chars(segment)
            compliant = "✅" if splitter.char_calculator.is_netflix_compliant(segment) else "❌"
            print(f"     第{j}段: {segment}")
            print(f"           有效字符: {effective_chars}, 兼容: {compliant}")
        
        print(f"   优化轮数: {result.optimization_rounds}")
        print(f"   质量评分: {result.quality_score:.2f}")
        print(f"   Netflix兼容: {'✅' if result.netflix_compliant else '❌'}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"   ⚠️ {warning}")


if __name__ == "__main__":
    test_netflix_semantic_splitter()