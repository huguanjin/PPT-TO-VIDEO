"""
Netflix序列匹配验证算法 - Phase 2核心实现
确保90%+准确度的高质量分割结果验证
"""

import time
import re
import logging
from typing import List, Dict, Optional, Any, Tuple, Set
from difflib import SequenceMatcher
from dataclasses import dataclass
from collections import defaultdict

from flask_backend.core.unified_config_manager import UnifiedConfigManager, ConfigContext, ConfigModuleType, ConfigComplexityLevel

@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool
    similarity_score: float
    netflix_compliant: bool
    error_details: List[str]
    warning_details: List[str]
    quality_metrics: Dict[str, Any]
    validation_time: float
    overall_quality_score: float = 0.0
    
    def __post_init__(self):
        """后处理计算总体质量分数"""
        self.overall_quality_score = self._calculate_overall_score()
    
    def _calculate_overall_score(self) -> float:
        """计算综合质量分数 (0-100)"""
        if not self.is_valid:
            return 0.0
        
        # 基础分数：相似度分数 (70分权重)
        base_score = self.similarity_score * 70
        
        # Netflix合规性奖励 (30分权重)
        compliance_bonus = 30 if self.netflix_compliant else 0
        
        # 警告扣分 (每个警告-2分)
        warning_penalty = len(self.warning_details) * 2
        
        # 总分计算
        total_score = base_score + compliance_bonus - warning_penalty
        return max(0.0, min(100.0, total_score))

class NetflixSequenceValidator:
    """Netflix级别序列匹配验证器 - 确保90%+准确度"""
    
    def __init__(self, config_manager: Optional[UnifiedConfigManager] = None):
        """
        初始化Netflix序列验证器
        
        Args:
            config_manager: 统一配置管理器，包含Netflix标准配置
        """
        self.logger = logging.getLogger(__name__)
        
        # 配置管理
        self.config_manager = config_manager or UnifiedConfigManager()
        
        # 创建Netflix配置上下文
        self.context = ConfigContext(
            module_type=ConfigModuleType.NETFLIX,
            complexity_level=ConfigComplexityLevel.PROFESSIONAL,
            preset_name="netflix_sequence_validator"
        )
        
        # 获取配置
        config = self.config_manager.get_config(self.context)
        self.netflix_standards = config.get('netflix_standards', {})
        self.validation_settings = config.get('validation_settings', {})
        
        # Netflix质量阈值
        self.similarity_threshold = self.netflix_standards.get('similarity_threshold', 0.9)
        self.max_chars_per_line = self.netflix_standards.get('max_chars_per_line', 20)
        self.min_chars_per_line = self.netflix_standards.get('min_chars_per_line', 3)
        self.max_length_ratio = self.netflix_standards.get('max_length_ratio', 2.5)
        
        # 验证严格性设置
        self.strict_mode = self.validation_settings.get('strict_mode', True)
        self.character_tolerance = self.validation_settings.get('character_tolerance', 0.02)  # 2%容错
        self.protected_unit_strict = self.validation_settings.get('protected_unit_strict', True)
        
        # 性能设置
        self.enable_detailed_analysis = self.validation_settings.get('detailed_analysis', True)
        self.cache_validation_results = self.validation_settings.get('cache_results', False)
        
        self.logger.info(f"Netflix序列验证器初始化完成，相似度阈值: {self.similarity_threshold}")
    
    def comprehensive_validate(self, original: str, segments: List[str], 
                             protected_units: Optional[List[Dict]] = None,
                             target_compliance: str = 'netflix') -> ValidationResult:
        """
        全面的Netflix级别验证
        
        Args:
            original: 原始文本
            segments: 分割后的文本段落
            protected_units: 保护单元列表
            target_compliance: 目标合规标准 ('netflix', 'strict', 'permissive')
            
        Returns:
            详细的验证结果
        """
        start_time = time.time()
        protected_units = protected_units or []
        
        try:
            # 初始化结果收集器
            error_details = []
            warning_details = []
            quality_metrics = {}
            
            # 1. 基础完整性检查
            integrity_result = self._check_basic_integrity(original, segments)
            if not integrity_result['valid']:
                return ValidationResult(
                    is_valid=False,
                    similarity_score=0.0,
                    netflix_compliant=False,
                    error_details=integrity_result['errors'],
                    warning_details=[],
                    quality_metrics={},
                    validation_time=time.time() - start_time
                )
            
            quality_metrics['integrity'] = integrity_result['metrics']
            
            # 2. 高精度序列匹配验证
            sequence_result = self._advanced_sequence_matching(original, segments)
            similarity_score = sequence_result['similarity_score']
            
            if similarity_score < self.similarity_threshold:
                error_details.append(f'相似度不足: {similarity_score:.4f} < {self.similarity_threshold}')
            
            quality_metrics['sequence_matching'] = sequence_result
            
            # 3. 保护单元完整性深度验证
            if protected_units:
                protection_result = self._validate_protected_units_advanced(original, segments, protected_units)
                if not protection_result['all_preserved']:
                    if self.protected_unit_strict:
                        error_details.extend(protection_result['missing_errors'])
                    else:
                        warning_details.extend(protection_result['missing_warnings'])
                
                quality_metrics['protection'] = protection_result
            
            # 4. Netflix合规性详细检查
            compliance_result = self._netflix_compliance_comprehensive(segments, target_compliance)
            netflix_compliant = compliance_result['compliant']
            
            if not netflix_compliant:
                if compliance_result['critical_violations']:
                    error_details.extend(compliance_result['critical_violations'])
                warning_details.extend(compliance_result['minor_violations'])
            
            quality_metrics['compliance'] = compliance_result
            
            # 5. 语义连贯性验证 (如果启用详细分析)
            if self.enable_detailed_analysis:
                semantic_result = self._validate_semantic_coherence(original, segments)
                if semantic_result['issues']:
                    warning_details.extend(semantic_result['issues'])
                quality_metrics['semantic'] = semantic_result
            
            # 6. 字符级精确性验证
            character_result = self._character_level_validation(original, segments)
            if character_result['character_loss'] > self.character_tolerance:
                error_details.append(f'字符丢失率过高: {character_result["character_loss"]:.3f}')
            
            quality_metrics['character_precision'] = character_result
            
            # 7. 综合质量评估
            is_valid = len(error_details) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                similarity_score=similarity_score,
                netflix_compliant=netflix_compliant,
                error_details=error_details,
                warning_details=warning_details,
                quality_metrics=quality_metrics,
                validation_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"验证过程异常: {e}")
            return ValidationResult(
                is_valid=False,
                similarity_score=0.0,
                netflix_compliant=False,
                error_details=[f'验证异常: {str(e)}'],
                warning_details=[],
                quality_metrics={},
                validation_time=time.time() - start_time
            )
    
    def _check_basic_integrity(self, original: str, segments: List[str]) -> Dict[str, Any]:
        """基础完整性检查"""
        errors = []
        
        # 空值检查
        if not original.strip():
            errors.append('原始文本为空')
        
        if not segments:
            errors.append('分割结果为空')
            return {'valid': False, 'errors': errors, 'metrics': {}}
        
        # 空段落检查
        empty_segments = [i for i, seg in enumerate(segments) if not seg.strip()]
        if empty_segments:
            errors.append(f'存在空段落: 位置 {empty_segments}')
        
        # 基础长度检查
        total_chars_original = len(original.replace(' ', '').replace('\n', ''))
        total_chars_segments = len(''.join(segments).replace(' ', '').replace('\n', ''))
        
        metrics = {
            'original_chars': total_chars_original,
            'segments_chars': total_chars_segments,
            'char_difference': abs(total_chars_original - total_chars_segments),
            'empty_segments': len(empty_segments)
        }
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'metrics': metrics
        }
    
    def _advanced_sequence_matching(self, original: str, segments: List[str]) -> Dict[str, Any]:
        """高级序列匹配算法"""
        
        # 准备比较文本（规范化处理）
        original_normalized = self._normalize_text_for_comparison(original)
        segments_normalized = self._normalize_text_for_comparison(''.join(segments))
        
        # 1. 整体相似度计算
        overall_similarity = SequenceMatcher(None, original_normalized, segments_normalized).ratio()
        
        # 2. 分段相似度分析
        segment_similarities = []
        original_parts = self._smart_split_original(original, len(segments))
        
        for i, (orig_part, segment) in enumerate(zip(original_parts, segments)):
            orig_norm = self._normalize_text_for_comparison(orig_part)
            seg_norm = self._normalize_text_for_comparison(segment)
            similarity = SequenceMatcher(None, orig_norm, seg_norm).ratio()
            segment_similarities.append({
                'segment_index': i,
                'similarity': similarity,
                'original_part': orig_part,
                'segment': segment
            })
        
        # 3. 字符级匹配分析
        char_analysis = self._character_level_matching(original_normalized, segments_normalized)
        
        # 4. 词汇保持度分析
        word_preservation = self._word_preservation_analysis(original, segments)
        
        return {
            'similarity_score': overall_similarity,
            'segment_similarities': segment_similarities,
            'avg_segment_similarity': sum(s['similarity'] for s in segment_similarities) / len(segment_similarities),
            'min_segment_similarity': min(s['similarity'] for s in segment_similarities),
            'character_analysis': char_analysis,
            'word_preservation': word_preservation,
            'comparison_method': 'advanced_sequence_matching'
        }
    
    def _normalize_text_for_comparison(self, text: str) -> str:
        """文本规范化处理用于比较"""
        # 移除多余空白字符
        normalized = re.sub(r'\s+', '', text)
        # 移除常见标点符号的影响
        normalized = re.sub(r'[，。！？；：""''()（）【】\\[\\]{}｛｝]', '', normalized)
        # 转换为小写（如果包含英文）
        normalized = normalized.lower()
        return normalized
    
    def _smart_split_original(self, original: str, target_segments: int) -> List[str]:
        """智能分割原文以对应分割结果"""
        if target_segments <= 1:
            return [original]
        
        # 尝试按字符均匀分割
        chars_per_segment = len(original) // target_segments
        parts = []
        
        start = 0
        for i in range(target_segments - 1):
            end = start + chars_per_segment
            # 寻找最近的自然分割点
            for offset in range(5):  # 向前向后各找5个字符
                for direction in [1, -1]:
                    pos = end + direction * offset
                    if 0 <= pos < len(original) and original[pos] in '，。！？；：':
                        end = pos + 1
                        break
                else:
                    continue
                break
            
            parts.append(original[start:end])
            start = end
        
        # 最后一部分包含剩余所有内容
        parts.append(original[start:])
        
        return parts
    
    def _character_level_matching(self, original: str, reconstructed: str) -> Dict[str, Any]:
        """字符级匹配分析"""
        matcher = SequenceMatcher(None, original, reconstructed)
        
        # 获取匹配块
        matching_blocks = matcher.get_matching_blocks()
        total_matching_chars = sum(block.size for block in matching_blocks)
        
        # 获取操作序列
        opcodes = matcher.get_opcodes()
        
        # 分析操作类型
        operations = defaultdict(int)
        for op, a1, a2, b1, b2 in opcodes:
            operations[op] += max(a2 - a1, b2 - b1)
        
        return {
            'total_matching_chars': total_matching_chars,
            'matching_ratio': total_matching_chars / max(len(original), 1),
            'operations': dict(operations),
            'insertions': operations['insert'],
            'deletions': operations['delete'],
            'replacements': operations['replace'],
            'total_edits': operations['insert'] + operations['delete'] + operations['replace']
        }
    
    def _word_preservation_analysis(self, original: str, segments: List[str]) -> Dict[str, Any]:
        """词汇保持度分析"""
        # 提取原文词汇
        original_words = set(re.findall(r'[\u4e00-\u9fff]+|\w+', original))
        
        # 提取分割结果词汇
        segments_text = ''.join(segments)
        segments_words = set(re.findall(r'[\u4e00-\u9fff]+|\w+', segments_text))
        
        # 计算保持度
        preserved_words = original_words & segments_words
        lost_words = original_words - segments_words
        added_words = segments_words - original_words
        
        preservation_rate = len(preserved_words) / len(original_words) if original_words else 1.0
        
        return {
            'original_word_count': len(original_words),
            'preserved_word_count': len(preserved_words),
            'lost_word_count': len(lost_words),
            'added_word_count': len(added_words),
            'preservation_rate': preservation_rate,
            'lost_words': list(lost_words)[:10],  # 只记录前10个丢失词汇
            'added_words': list(added_words)[:10]  # 只记录前10个新增词汇
        }
    
    def _validate_protected_units_advanced(self, original: str, segments: List[str], 
                                         protected_units: List[Dict]) -> Dict[str, Any]:
        """高级保护单元验证"""
        reconstructed = ''.join(segments)
        
        missing_errors = []
        missing_warnings = []
        preserved_units = []
        location_changes = []
        
        for unit in protected_units:
            unit_text = unit['text']
            unit_type = unit.get('type', 'unknown')
            original_pos = original.find(unit_text)
            reconstructed_pos = reconstructed.find(unit_text)
            
            if reconstructed_pos == -1:
                # 保护单元丢失
                error_msg = f'保护单元丢失: "{unit_text}" (类型: {unit_type})'
                if self.protected_unit_strict:
                    missing_errors.append(error_msg)
                else:
                    missing_warnings.append(error_msg)
            else:
                # 保护单元存在
                preserved_units.append(unit)
                
                # 检查位置变化
                if original_pos != -1 and abs(original_pos - reconstructed_pos) > 5:
                    location_changes.append({
                        'unit': unit_text,
                        'original_pos': original_pos,
                        'new_pos': reconstructed_pos,
                        'displacement': abs(original_pos - reconstructed_pos)
                    })
        
        all_preserved = len(missing_errors) == 0
        preservation_rate = len(preserved_units) / len(protected_units) if protected_units else 1.0
        
        return {
            'all_preserved': all_preserved,
            'preservation_rate': preservation_rate,
            'preserved_count': len(preserved_units),
            'missing_count': len(missing_errors) + len(missing_warnings),
            'missing_errors': missing_errors,
            'missing_warnings': missing_warnings,
            'location_changes': location_changes,
            'significant_displacements': [lc for lc in location_changes if lc['displacement'] > 10]
        }
    
    def _netflix_compliance_comprehensive(self, segments: List[str], 
                                        target_compliance: str = 'netflix') -> Dict[str, Any]:
        """全面的Netflix合规性检查"""
        
        # 获取合规标准
        standards = self._get_compliance_standards(target_compliance)
        
        critical_violations = []
        minor_violations = []
        compliance_scores = {}
        
        # 1. 长度合规性检查
        length_result = self._check_length_compliance(segments, standards)
        if length_result['critical_violations']:
            critical_violations.extend(length_result['critical_violations'])
        if length_result['minor_violations']:
            minor_violations.extend(length_result['minor_violations'])
        compliance_scores['length'] = length_result['score']
        
        # 2. 均衡性检查
        balance_result = self._check_balance_compliance(segments, standards)
        if balance_result['violations']:
            minor_violations.extend(balance_result['violations'])
        compliance_scores['balance'] = balance_result['score']
        
        # 3. 可读性检查
        readability_result = self._check_readability_compliance(segments, standards)
        if readability_result['violations']:
            minor_violations.extend(readability_result['violations'])
        compliance_scores['readability'] = readability_result['score']
        
        # 4. 结构完整性检查
        structure_result = self._check_structure_compliance(segments, standards)
        if structure_result['violations']:
            minor_violations.extend(structure_result['violations'])
        compliance_scores['structure'] = structure_result['score']
        
        # 综合合规性评估
        overall_score = sum(compliance_scores.values()) / len(compliance_scores)
        compliant = len(critical_violations) == 0 and overall_score >= standards['min_overall_score']
        
        return {
            'compliant': compliant,
            'overall_score': overall_score,
            'compliance_scores': compliance_scores,
            'critical_violations': critical_violations,
            'minor_violations': minor_violations,
            'standards_used': target_compliance
        }
    
    def _get_compliance_standards(self, target_compliance: str) -> Dict[str, Any]:
        """获取合规标准配置"""
        standards = {
            'netflix': {
                'max_chars_per_line': 20,
                'min_chars_per_line': 3,
                'max_length_ratio': 2.5,
                'min_overall_score': 0.8
            },
            'strict': {
                'max_chars_per_line': 18,
                'min_chars_per_line': 5,
                'max_length_ratio': 2.0,
                'min_overall_score': 0.9
            },
            'permissive': {
                'max_chars_per_line': 25,
                'min_chars_per_line': 2,
                'max_length_ratio': 3.0,
                'min_overall_score': 0.7
            }
        }
        
        return standards.get(target_compliance, standards['netflix'])
    
    def _check_length_compliance(self, segments: List[str], standards: Dict) -> Dict[str, Any]:
        """长度合规性检查"""
        critical_violations = []
        minor_violations = []
        
        max_chars = standards['max_chars_per_line']
        min_chars = standards['min_chars_per_line']
        
        lengths = [len(seg.strip()) for seg in segments]
        
        for i, length in enumerate(lengths):
            if length > max_chars * 1.5:  # 严重超长
                critical_violations.append(f'第{i+1}行严重超长: {length}字符 > {max_chars*1.5}')
            elif length > max_chars:  # 轻微超长
                minor_violations.append(f'第{i+1}行超长: {length}字符 > {max_chars}')
            elif 0 < length < min_chars:  # 过短
                minor_violations.append(f'第{i+1}行过短: {length}字符 < {min_chars}')
        
        # 计算长度合规分数
        valid_lengths = [l for l in lengths if min_chars <= l <= max_chars]
        score = len(valid_lengths) / len(lengths) if lengths else 0.0
        
        return {
            'critical_violations': critical_violations,
            'minor_violations': minor_violations,
            'score': score,
            'lengths': lengths,
            'valid_count': len(valid_lengths)
        }
    
    def _check_balance_compliance(self, segments: List[str], standards: Dict) -> Dict[str, Any]:
        """均衡性合规检查"""
        violations = []
        
        lengths = [len(seg.strip()) for seg in segments if seg.strip()]
        
        if len(lengths) < 2:
            return {'violations': [], 'score': 1.0, 'ratio': 1.0}
        
        max_length = max(lengths)
        min_length = min(lengths)
        ratio = max_length / min_length if min_length > 0 else float('inf')
        
        max_ratio = standards['max_length_ratio']
        
        if ratio > max_ratio:
            violations.append(f'长度不均衡: 最大/最小比例 {ratio:.2f} > {max_ratio}')
        
        # 计算均衡分数
        score = min(1.0, max_ratio / ratio) if ratio > 0 else 0.0
        
        return {
            'violations': violations,
            'score': score,
            'ratio': ratio,
            'max_length': max_length,
            'min_length': min_length
        }
    
    def _check_readability_compliance(self, segments: List[str], standards: Dict) -> Dict[str, Any]:
        """可读性合规检查"""
        violations = []
        score_components = []
        
        for i, segment in enumerate(segments):
            segment = segment.strip()
            if not segment:
                continue
            
            # 检查标点符号使用
            if segment.endswith(('，', '、', '；')) and i == len(segments) - 1:
                violations.append(f'第{i+1}行: 最后一行不应以连接性标点结尾')
                score_components.append(0.7)
            else:
                score_components.append(1.0)
            
            # 检查是否有不完整的词汇分割
            if self._has_incomplete_word_split(segment):
                violations.append(f'第{i+1}行: 存在不完整的词汇分割')
                score_components[-1] *= 0.8
        
        # 计算可读性分数
        score = sum(score_components) / len(score_components) if score_components else 1.0
        
        return {
            'violations': violations,
            'score': score,
            'components': score_components
        }
    
    def _check_structure_compliance(self, segments: List[str], standards: Dict) -> Dict[str, Any]:
        """结构完整性检查"""
        violations = []
        
        # 检查括号匹配
        bracket_pairs = [('(', ')'), ('（', '）'), ('[', ']'), ('【', '】'), ('{', '}'), ('｛', '｝')]
        
        full_text = ''.join(segments)
        
        for open_bracket, close_bracket in bracket_pairs:
            open_count = full_text.count(open_bracket)
            close_count = full_text.count(close_bracket)
            
            if open_count != close_count:
                violations.append(f'括号不匹配: {open_bracket}{close_bracket} - 开:{open_count}, 闭:{close_count}')
        
        # 检查引号匹配
        quote_pairs = [('"', '"'), ('"', '"'), ("'", "'"), (''', ''')]
        
        for open_quote, close_quote in quote_pairs:
            if open_quote == close_quote:
                # 相同引号，检查是否成对
                count = full_text.count(open_quote)
                if count % 2 != 0:
                    violations.append(f'引号不匹配: {open_quote} 出现{count}次(奇数)')
            else:
                # 不同引号，检查数量匹配
                open_count = full_text.count(open_quote)
                close_count = full_text.count(close_quote)
                if open_count != close_count:
                    violations.append(f'引号不匹配: {open_quote}{close_quote} - 开:{open_count}, 闭:{close_count}')
        
        # 计算结构分数
        score = 1.0 if len(violations) == 0 else max(0.5, 1.0 - len(violations) * 0.1)
        
        return {
            'violations': violations,
            'score': score
        }
    
    def _has_incomplete_word_split(self, text: str) -> bool:
        """检查是否有不完整的词汇分割"""
        # 检查是否在汉字中间分割
        if len(text) > 1:
            # 检查首尾字符是否可能是词汇的一部分
            first_char = text[0]
            last_char = text[-1]
            
            # 如果以助词、介词等功能词开头或结尾，可能是不完整分割
            function_words_start = ['的', '了', '着', '过', '在', '与', '和', '或', '但', '而']
            function_words_end = ['之', '者', '等', '性', '化', '度']
            
            if first_char in function_words_start or last_char in function_words_end:
                return True
        
        return False
    
    def _validate_semantic_coherence(self, original: str, segments: List[str]) -> Dict[str, Any]:
        """语义连贯性验证"""
        issues = []
        
        # 检查每个段落的语义完整性
        for i, segment in enumerate(segments):
            segment = segment.strip()
            if not segment:
                continue
            
            # 检查是否在句子中间截断
            if not segment.endswith(('。', '！', '？', '；', '：')) and i < len(segments) - 1:
                next_segment = segments[i + 1].strip()
                if next_segment and next_segment[0].islower():
                    issues.append(f'第{i+1}行可能在句子中间截断')
            
            # 检查逻辑连接词的使用
            if segment.startswith(('但是', '然而', '因此', '所以', '而且', '并且')):
                if i == 0:
                    issues.append(f'第{i+1}行以连接词开头，但这是第一行')
        
        return {
            'issues': issues,
            'coherence_score': max(0.0, 1.0 - len(issues) * 0.2)
        }
    
    def _character_level_validation(self, original: str, segments: List[str]) -> Dict[str, Any]:
        """字符级精确性验证"""
        original_chars = len(original.replace(' ', '').replace('\n', ''))
        segments_chars = len(''.join(segments).replace(' ', '').replace('\n', ''))
        
        character_loss = abs(original_chars - segments_chars) / original_chars if original_chars > 0 else 0
        
        # 统计字符类型分布
        original_char_types = self._analyze_character_types(original)
        segments_char_types = self._analyze_character_types(''.join(segments))
        
        type_preservation = {}
        for char_type in original_char_types:
            orig_count = original_char_types[char_type]
            seg_count = segments_char_types.get(char_type, 0)
            preservation = seg_count / orig_count if orig_count > 0 else 1.0
            type_preservation[char_type] = preservation
        
        return {
            'character_loss': character_loss,
            'original_chars': original_chars,
            'segments_chars': segments_chars,
            'char_difference': abs(original_chars - segments_chars),
            'type_preservation': type_preservation,
            'precision_score': 1.0 - character_loss
        }
    
    def _analyze_character_types(self, text: str) -> Dict[str, int]:
        """分析字符类型分布"""
        char_types = defaultdict(int)
        
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                char_types['chinese'] += 1
            elif char.isalpha():
                char_types['english'] += 1
            elif char.isdigit():
                char_types['digit'] += 1
            elif char in '，。！？；：""''()（）【】[]{}｛｝':
                char_types['punctuation'] += 1
            elif char.isspace():
                char_types['whitespace'] += 1
            else:
                char_types['other'] += 1
        
        return dict(char_types)
    
    def batch_validate(self, validation_items: List[Dict[str, Any]]) -> List[ValidationResult]:
        """批量验证"""
        results = []
        
        for item in validation_items:
            result = self.comprehensive_validate(
                original=item['original'],
                segments=item['segments'],
                protected_units=item.get('protected_units', []),
                target_compliance=item.get('target_compliance', 'netflix')
            )
            results.append(result)
        
        return results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """获取验证结果汇总"""
        if not results:
            return {'error': '没有验证结果'}
        
        total_count = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        compliant_count = sum(1 for r in results if r.netflix_compliant)
        
        avg_similarity = sum(r.similarity_score for r in results) / total_count
        avg_quality = sum(r.overall_quality_score for r in results) / total_count
        avg_validation_time = sum(r.validation_time for r in results) / total_count
        
        return {
            'total_validations': total_count,
            'valid_count': valid_count,
            'valid_rate': valid_count / total_count,
            'compliant_count': compliant_count,
            'compliance_rate': compliant_count / total_count,
            'avg_similarity_score': avg_similarity,
            'avg_quality_score': avg_quality,
            'avg_validation_time': avg_validation_time,
            'performance_grade': self._calculate_performance_grade(valid_count / total_count, avg_quality)
        }
    
    def _calculate_performance_grade(self, valid_rate: float, avg_quality: float) -> str:
        """计算性能等级"""
        if valid_rate >= 0.95 and avg_quality >= 90:
            return 'A+'
        elif valid_rate >= 0.9 and avg_quality >= 85:
            return 'A'
        elif valid_rate >= 0.85 and avg_quality >= 80:
            return 'B+'
        elif valid_rate >= 0.8 and avg_quality >= 75:
            return 'B'
        elif valid_rate >= 0.7 and avg_quality >= 70:
            return 'C+'
        elif valid_rate >= 0.6 and avg_quality >= 65:
            return 'C'
        else:
            return 'D'