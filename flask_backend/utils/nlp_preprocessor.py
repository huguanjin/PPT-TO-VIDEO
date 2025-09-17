"""
Netflix级别的NLP预处理器
基于spaCy实现的中文文本分析和分割预处理系统
"""

# 导入NumPy兼容性修复
try:
    from .numpy_compatibility_fix import *
except ImportError:
    pass

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: spaCy导入失败: {e}")
    SPACY_AVAILABLE = False

import json
from typing import List, Dict, Tuple, Optional
import re
from pathlib import Path
import logging

class NetflixStyleNLPPreprocessor:
    """Netflix级别的NLP预处理器"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        初始化NLP预处理器
        
        Args:
            model_name: 指定的spaCy模型名称，如果为None则自动选择
        """
        self.logger = logging.getLogger(__name__)
        self.nlp = self._load_spacy_model(model_name) if SPACY_AVAILABLE else None
        
        # 标点符号分割规则
        self.split_marks = ['。', '！', '？', '；', '：', '…', '.', '!', '?']
        self.comma_patterns = [',', '，', '、']
        self.conjunction_patterns = ['但是', '然而', '不过', '而且', '并且', '同时', '因此', '所以', '由于', '因为']
        
        # 复杂度评估权重
        self.complexity_weights = {
            'length': 0.1,      # 长度因子
            'verbs': 0.3,       # 动词数量
            'roots': 0.2,       # 语法根数量
            'clauses': 0.4      # 子句数量
        }
        
        # 分割候选点评分权重
        self.split_weights = {
            'punctuation': 0.4,     # 标点符号
            'conjunction': 0.3,     # 连词
            'verb_boundary': 0.2,   # 动词边界
            'noun_phrase': 0.1      # 名词短语边界
        }
    
    def _load_spacy_model(self, model_name: Optional[str] = None):
        """加载spaCy模型"""
        if not SPACY_AVAILABLE:
            self.logger.warning("spaCy不可用，将使用基础分割功能")
            return None
            
        if model_name:
            try:
                return spacy.load(model_name)
            except OSError:
                self.logger.warning(f"无法加载指定模型 {model_name}，尝试自动选择")
        
        # 自动选择可用的中文模型
        models_to_try = [
            "zh_core_web_sm",
            "zh_core_web_md", 
            "zh_core_web_lg",
            "zh_core_web_trf"
        ]
        
        for model in models_to_try:
            try:
                nlp = spacy.load(model)
                self.logger.info(f"成功加载spaCy模型: {model}")
                return nlp
            except OSError:
                continue
        
        # 如果所有中文模型都不可用，尝试加载基础模型
        try:
            nlp = spacy.blank("zh")
            self.logger.warning("未找到完整的中文模型，使用基础中文模型")
            return nlp
        except Exception as e:
            self.logger.error(f"无法加载任何spaCy模型: {e}")
            return None
    
    def preprocess_text(self, text: str) -> List[Dict]:
        """
        NLP预处理：分割、标记、分析
        
        Args:
            text: 输入文本
            
        Returns:
            预处理结果列表，每个元素包含文本片段和分析信息
        """
        if not text.strip():
            return []
        
        # 1. 基于标点符号的基础分割
        basic_segments = self._split_by_punctuation(text)
        
        # 2. 对每个片段进行spaCy分析
        processed_segments = []
        for segment in basic_segments:
            segment = segment.strip()
            if len(segment) > 0:
                try:
                    if self.nlp is not None:
                        doc = self.nlp(segment)
                        segment_info = self._analyze_segment(segment, doc)
                    else:
                        # spaCy不可用，使用基础分析
                        segment_info = self._fallback_analysis(segment)
                    processed_segments.append(segment_info)
                except Exception as e:
                    self.logger.error(f"分析片段失败: {segment[:20]}... - {e}")
                    # 回退到基础分析
                    segment_info = self._fallback_analysis(segment)
                    processed_segments.append(segment_info)
        
        return processed_segments
    
    def _analyze_segment(self, text: str, doc) -> Dict:
        """分析单个文本片段"""
        return {
            'text': text,
            'doc': doc,
            'tokens': [token.text for token in doc],
            'token_count': len(doc),
            'char_count': len(text),
            'need_ai_split': self._need_ai_optimization(doc),
            'complexity': self._calculate_complexity(doc),
            'split_candidates': self._find_split_candidates(doc),
            'linguistic_features': self._extract_linguistic_features(doc),
            'semantic_units': self._identify_semantic_units(text)
        }
    
    def _fallback_analysis(self, text: str) -> Dict:
        """回退分析（当spaCy分析失败时使用）"""
        tokens = text.split()
        return {
            'text': text,
            'doc': None,
            'tokens': tokens,
            'token_count': len(tokens),
            'char_count': len(text),
            'need_ai_split': len(text) > 20,  # 简单的长度判断
            'complexity': min(len(text) * 0.1, 10.0),
            'split_candidates': self._find_punctuation_positions(text),
            'linguistic_features': {},
            'semantic_units': []
        }
    
    def _split_by_punctuation(self, text: str) -> List[str]:
        """基于标点符号的基础分割"""
        segments = [text]
        
        # 首先按句末标点分割
        for mark in self.split_marks:
            new_segments = []
            for segment in segments:
                if mark in segment:
                    parts = segment.split(mark)
                    for i, part in enumerate(parts):
                        if i < len(parts) - 1:
                            # 保留标点符号
                            new_segments.append(part + mark)
                        elif part.strip():
                            new_segments.append(part)
                else:
                    new_segments.append(segment)
            segments = new_segments
        
        return [seg.strip() for seg in segments if seg.strip()]
    
    def _need_ai_optimization(self, doc) -> bool:
        """判断是否需要AI优化"""
        if not doc:
            return True
        
        # 条件1: 超过20个字符
        if len(doc.text) > 20:
            return True
        
        # 条件2: 包含复杂句法结构
        complex_structures = 0
        for token in doc:
            if token.dep_ in ['ROOT', 'VERB'] and len(list(token.children)) > 2:
                complex_structures += 1
            if token.pos_ == 'VERB' and any(child.dep_ in ['DOBJ', 'IOBJ'] for child in token.children):
                complex_structures += 1
        
        # 条件3: 包含连词
        has_conjunction = any(token.text in self.conjunction_patterns for token in doc)
        
        return complex_structures > 1 or has_conjunction
    
    def _calculate_complexity(self, doc) -> float:
        """计算句子复杂度评分"""
        if not doc:
            return 1.0
        
        complexity_score = 0
        
        # 长度因子
        complexity_score += len(doc) * self.complexity_weights['length']
        
        # 动词数量
        verbs = [token for token in doc if token.pos_ in ['VERB', 'AUX']]
        complexity_score += len(verbs) * self.complexity_weights['verbs']
        
        # 语法根数量
        roots = [token for token in doc if token.dep_ == 'ROOT']
        complexity_score += len(roots) * self.complexity_weights['roots']
        
        # 子句数量（基于从属连词判断）
        clauses = sum(1 for token in doc if token.dep_ in ['SBAR', 'ADVCL', 'ACLS'])
        complexity_score += clauses * self.complexity_weights['clauses']
        
        return min(complexity_score, 10.0)  # 限制在10以内
    
    def _find_split_candidates(self, doc) -> List[Dict]:
        """找到潜在的分割候选点"""
        if not doc:
            return self._find_punctuation_positions(doc.text if hasattr(doc, 'text') else "")
        
        candidates = []
        
        for i, token in enumerate(doc):
            score = 0
            reasons = []
            
            # 标点符号边界
            if token.text in self.comma_patterns:
                score += self.split_weights['punctuation']
                reasons.append('punctuation')
            
            # 连词边界
            if token.text in self.conjunction_patterns:
                score += self.split_weights['conjunction']
                reasons.append('conjunction')
            
            # 动词边界（在动词前分割）
            if token.pos_ in ['VERB', 'AUX'] and i > 0:
                score += self.split_weights['verb_boundary']
                reasons.append('verb_boundary')
            
            # 名词短语边界
            if token.dep_ in ['ROOT', 'NSUBJ', 'DOBJ'] and i > 0:
                score += self.split_weights['noun_phrase']
                reasons.append('noun_phrase')
            
            if score > 0:
                candidates.append({
                    'position': i,
                    'token': token.text,
                    'score': score,
                    'reasons': reasons,
                    'char_position': sum(len(t.text) for t in doc[:i])
                })
        
        # 按分数排序
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates
    
    def _find_punctuation_positions(self, text: str) -> List[Dict]:
        """在回退模式下找到标点符号位置"""
        candidates = []
        for i, char in enumerate(text):
            if char in self.comma_patterns:
                candidates.append({
                    'position': i,
                    'token': char,
                    'score': 0.5,
                    'reasons': ['punctuation'],
                    'char_position': i
                })
        return candidates
    
    def _extract_linguistic_features(self, doc) -> Dict:
        """提取语言学特征"""
        if not doc:
            return {}
        
        features = {
            'pos_tags': [(token.text, token.pos_) for token in doc],
            'dep_relations': [(token.text, token.dep_) for token in doc],
            'entities': [(ent.text, ent.label_) for ent in doc.ents],
            'verb_count': len([token for token in doc if token.pos_ == 'VERB']),
            'noun_count': len([token for token in doc if token.pos_ == 'NOUN']),
            'sentence_count': len(list(doc.sents))
        }
        
        # 尝试提取名词短语，如果不支持则跳过
        try:
            features['noun_phrases'] = [chunk.text for chunk in doc.noun_chunks]
        except NotImplementedError:
            # 中文模型可能不支持noun_chunks
            features['noun_phrases'] = []
        
        return features
    
    def _identify_semantic_units(self, text: str) -> List[Dict]:
        """识别语义单元（URL、邮箱等需要保护的内容）"""
        patterns = [
            (r'https?://[^\s\u4e00-\u9fff]+', 'url'),
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'email'),
            (r'\b[A-Z][A-Z0-9_]*[A-Z0-9]\b', 'acronym'),  # 改进的首字母缩写模式
            (r'\b\d+(?:\.\d+)?[%°C℃℉]?\b', 'number'),
            (r'[A-Za-z_][A-Za-z0-9_]*\([^)]*\)', 'function_call'),
            (r'[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*', 'attribute_access'),
            (r'\b[A-Z]+_[A-Z0-9_]+\b', 'constant')  # 常量模式如API_KEY
        ]
        
        units = []
        for pattern, unit_type in patterns:
            for match in re.finditer(pattern, text):
                units.append({
                    'text': match.group(),
                    'type': unit_type,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return units
    
    def get_recommended_split_points(self, segment_info: Dict, max_parts: int = 2) -> List[int]:
        """获取推荐的分割点"""
        candidates = segment_info.get('split_candidates', [])
        
        if not candidates:
            # 如果没有候选点，返回中点
            text_length = segment_info.get('char_count', 0)
            return [text_length // 2] if text_length > 10 else []
        
        # 选择评分最高的分割点
        top_candidates = candidates[:max_parts-1]
        split_points = [c['char_position'] for c in top_candidates]
        
        # 按位置排序
        split_points.sort()
        
        return split_points
    
    def validate_split_result(self, original_text: str, split_result: List[str]) -> Dict:
        """验证分割结果的质量"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'quality_score': 1.0,
            'recommendations': []
        }
        
        # 检查内容完整性
        reconstructed = ''.join(split_result)
        if reconstructed.replace(' ', '') != original_text.replace(' ', ''):
            validation_result['is_valid'] = False
            validation_result['issues'].append('content_mismatch')
            validation_result['quality_score'] -= 0.5
        
        # 检查长度均衡性
        lengths = [len(part) for part in split_result]
        if max(lengths) > min(lengths) * 3:  # 最长部分不应超过最短部分的3倍
            validation_result['issues'].append('unbalanced_lengths')
            validation_result['quality_score'] -= 0.2
            validation_result['recommendations'].append('consider_rebalancing')
        
        # 检查单行长度
        for i, part in enumerate(split_result):
            if len(part) > 25:  # Netflix标准建议
                validation_result['issues'].append(f'line_{i+1}_too_long')
                validation_result['quality_score'] -= 0.1
        
        return validation_result
    
    def get_model_info(self) -> Dict:
        """获取当前模型信息"""
        if self.nlp is not None and hasattr(self.nlp, 'meta'):
            return {
                'name': self.nlp.meta.get('name', 'unknown'),
                'version': self.nlp.meta.get('version', 'unknown'),
                'language': self.nlp.meta.get('lang', 'zh'),
                'pipeline': list(self.nlp.pipe_names)
            }
        else:
            return {
                'name': 'basic_chinese_fallback',
                'version': 'unknown',
                'language': 'zh',
                'pipeline': [],
                'spacy_available': SPACY_AVAILABLE
            }