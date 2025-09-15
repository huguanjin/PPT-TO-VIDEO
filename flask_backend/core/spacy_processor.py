"""
Spacy NLP处理器
基于VideoLingo项目的语义分割技术，实现多层次文本分割
"""
import re
import spacy
import logging
from typing import List, Dict, Any, Optional, Tuple
import time
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


class SpacyProcessor:
    """Spacy NLP处理器 - 基于VideoLingo技术实现"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Spacy处理器
        
        Args:
            config: 配置参数，包含语言模型设置等
        """
        self.config = config or {}
        self.models = {
            'zh': 'zh_core_web_md',
            'en': 'en_core_web_sm'  # 英文模型备用
        }
        self.nlp_cache = {}
        self.logger = logging.getLogger(__name__)
        
        # 性能配置
        self.max_sentence_length = self.config.get('max_sentence_length', 100)
        self.min_split_length = self.config.get('min_split_length', 10)
        self.enable_cache = self.config.get('enable_cache', True)
        
        # 预加载常用语言模型
        self._preload_models()
    
    def _preload_models(self):
        """预加载常用语言模型"""
        try:
            # 预加载中文模型
            self.get_nlp_model('zh')
            self.logger.info("Spacy中文模型预加载成功")
        except Exception as e:
            self.logger.warning(f"Spacy模型预加载失败: {e}")
    
    @lru_cache(maxsize=8)
    def get_nlp_model(self, language: str):
        """
        获取语言模型（带缓存）
        
        Args:
            language: 语言代码（zh, en等）
            
        Returns:
            spacy.Language: Spacy语言模型
        """
        if language not in self.nlp_cache:
            model_name = self.models.get(language, 'zh_core_web_md')
            
            try:
                self.logger.info(f"加载Spacy模型: {model_name}")
                nlp = spacy.load(model_name)
                
                # 优化模型配置
                nlp.max_length = 2000000  # 增加最大文本长度
                
                # 禁用不需要的组件以提升性能
                if 'ner' in nlp.pipe_names:
                    nlp.disable_pipes('ner')
                
                self.nlp_cache[language] = nlp
                self.logger.info(f"Spacy模型 {model_name} 加载成功")
                
            except OSError as e:
                self.logger.error(f"无法加载Spacy模型 {model_name}: {e}")
                # 降级到基础模型
                if language == 'zh' and model_name != 'zh_core_web_sm':
                    self.models[language] = 'zh_core_web_sm'
                    return self.get_nlp_model(language)
                raise
        
        return self.nlp_cache[language]
    
    def split_by_sentences(self, text: str, language: str = 'zh') -> List[str]:
        """
        基于句子边界分割（对应VideoLingo的split_by_mark）
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            List[str]: 分割后的句子列表
        """
        if not text or not text.strip():
            return []
        
        try:
            start_time = time.time()
            nlp = self.get_nlp_model(language)
            doc = nlp(text.strip())
            
            # 检查是否有句子边界注解
            if not doc.has_annotation("SENT_START"):
                self.logger.warning("文档缺少句子边界注解，使用备用分割方法")
                return self._fallback_sentence_split(text)
            
            sentences = []
            current_sentence = []
            
            # 遍历所有句子（基于VideoLingo的逻辑）
            for sent in doc.sents:
                sent_text = sent.text.strip()
                
                if not sent_text:
                    continue
                
                # 处理连字符和省略号的特殊情况
                if current_sentence and self._should_merge_with_previous(sent_text, current_sentence):
                    current_sentence.append(sent_text)
                else:
                    # 保存之前的句子
                    if current_sentence:
                        sentences.append(' '.join(current_sentence))
                        current_sentence = []
                    current_sentence.append(sent_text)
            
            # 添加最后的句子
            if current_sentence:
                sentences.append(' '.join(current_sentence))
            
            # 后处理：合并过短的句子和处理标点符号
            sentences = self._post_process_sentences(sentences, language)
            
            process_time = time.time() - start_time
            self.logger.debug(f"句子分割完成: {len(sentences)}个句子, 耗时: {process_time:.3f}秒")
            
            return sentences
            
        except Exception as e:
            self.logger.error(f"句子分割失败: {e}")
            return self._fallback_sentence_split(text)
    
    def _should_merge_with_previous(self, current_text: str, previous_sentences: List[str]) -> bool:
        """
        判断当前句子是否应该与前一个句子合并
        （基于VideoLingo的连字符和省略号处理逻辑）
        """
        if not previous_sentences:
            return False
        
        prev_text = previous_sentences[-1]
        
        # 检查连字符和省略号的情况
        return (current_text.startswith('-') or 
                current_text.startswith('...') or
                current_text.startswith('—') or
                prev_text.endswith('-') or
                prev_text.endswith('...') or
                prev_text.endswith('—'))
    
    def _post_process_sentences(self, sentences: List[str], language: str) -> List[str]:
        """
        后处理句子列表（基于VideoLingo的后处理逻辑）
        """
        if not sentences:
            return []
        
        processed = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            
            if not sentence:
                continue
            
            # 处理单独的标点符号（针对中文、日文等）
            if i > 0 and sentence in [',', '.', '，', '。', '？', '！', '；', '：']:
                # 将标点符号合并到前一个句子
                if processed:
                    processed[-1] += sentence
                continue
            
            processed.append(sentence)
        
        return processed
    
    def _fallback_sentence_split(self, text: str) -> List[str]:
        """备用句子分割方法"""
        # 简单的基于标点符号的分割
        sentences = re.split(r'[。！？；\.\!\?;]\s*', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def split_by_syntax(self, text: str, language: str = 'zh') -> List[str]:
        """
        基于句法分析分割长句（对应VideoLingo的split_long_by_root）
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            List[str]: 分割后的文本片段
        """
        if not text or not text.strip():
            return []
        
        # 短句不需要句法分割
        if len(text) <= self.min_split_length:
            return [text]
        
        try:
            nlp = self.get_nlp_model(language)
            doc = nlp(text.strip())
            
            # 检查句子长度，决定分割策略
            if len(doc) <= 30:  # 短句保持不变
                return [text]
            elif len(doc) <= 60:  # 中等长度使用动态规划
                return self._dp_split_by_syntax(doc, language)
            else:  # 超长句子使用强制分割
                return self._force_split_long_sentence(doc, language)
        
        except Exception as e:
            self.logger.error(f"句法分割失败: {e}")
            return [text]  # 失败时返回原文
    
    def _dp_split_by_syntax(self, doc, language: str) -> List[str]:
        """
        使用动态规划算法进行句法分割（基于VideoLingo算法）
        """
        tokens = [token.text for token in doc]
        n = len(tokens)
        
        if n <= 10:
            return [' '.join(tokens)]
        
        # 动态规划数组，dp[i] 表示从开始到第i个token的最优分割方案
        dp = [float('inf')] * (n + 1)
        dp[0] = 0
        
        # 记录最优分割点
        prev = [0] * (n + 1)
        
        for i in range(1, n + 1):
            # 限制搜索范围避免过长句子
            search_start = max(0, i - 50)
            
            for j in range(search_start, i):
                # 确保句子最小长度
                if i - j >= 5:
                    token = doc[i-1]
                    
                    # 在合适的位置分割：句子结束、动词、辅助动词或根节点
                    can_split = (j == 0 or 
                               token.is_sent_end or 
                               token.pos_ in ['VERB', 'AUX'] or 
                               token.dep_ == 'ROOT' or
                               self._is_good_split_point(token))
                    
                    if can_split and dp[j] + 1 < dp[i]:
                        dp[i] = dp[j] + 1
                        prev[i] = j
        
        # 重建分割结果
        sentences = []
        i = n
        joiner = self._get_language_joiner(language)
        
        while i > 0:
            j = prev[i]
            sentence = joiner.join(tokens[j:i]).strip()
            if sentence:
                sentences.append(sentence)
            i = j
        
        # 返回正确顺序
        return sentences[::-1] if sentences else [' '.join(tokens)]
    
    def _is_good_split_point(self, token) -> bool:
        """判断是否是好的分割点"""
        # 连词、标点符号等适合分割的位置
        good_pos = ['CCONJ', 'SCONJ', 'PUNCT']
        good_deps = ['cc', 'mark', 'punct']
        
        return (token.pos_ in good_pos or 
                token.dep_ in good_deps or
                token.text in ['，', ',', '；', ';', '但是', '然而', '因此', '所以'])
    
    def _force_split_long_sentence(self, doc, language: str) -> List[str]:
        """
        强制分割超长句子（基于VideoLingo的极长句处理）
        """
        tokens = [token.text for token in doc]
        n = len(tokens)
        
        # 计算分割段数（每60个token一段）
        num_parts = (n + 59) // 60
        part_length = n // num_parts
        
        sentences = []
        joiner = self._get_language_joiner(language)
        
        for i in range(num_parts):
            start = i * part_length
            end = start + part_length if i < num_parts - 1 else n
            
            sentence = joiner.join(tokens[start:end])
            if sentence.strip():
                sentences.append(sentence.strip())
        
        return sentences
    
    def _get_language_joiner(self, language: str) -> str:
        """获取语言的连接符"""
        # 中文、日文等不需要空格连接
        no_space_languages = ['zh', 'ja']
        return '' if language in no_space_languages else ' '
    
    def analyze_text_complexity(self, text: str, language: str = 'zh') -> Dict[str, Any]:
        """
        分析文本复杂度
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            Dict: 复杂度分析结果
        """
        if not text or not text.strip():
            return {'complexity_score': 0, 'needs_splitting': False}
        
        try:
            nlp = self.get_nlp_model(language)
            doc = nlp(text.strip())
            
            # 计算复杂度指标
            complexity_metrics = {
                'token_count': len(doc),
                'sentence_count': len(list(doc.sents)),
                'avg_sentence_length': len(doc) / max(len(list(doc.sents)), 1),
                'complex_structures': self._count_complex_structures(doc),
                'dependency_depth': self._calculate_dependency_depth(doc),
                'pos_diversity': len(set(token.pos_ for token in doc)) / len(doc) if doc else 0
            }
            
            # 计算综合复杂度分数
            complexity_score = self._calculate_complexity_score(complexity_metrics)
            
            # 判断是否需要分割
            needs_splitting = (complexity_score > 0.6 or 
                             complexity_metrics['token_count'] > 30 or
                             complexity_metrics['avg_sentence_length'] > 20)
            
            return {
                'complexity_score': complexity_score,
                'needs_splitting': needs_splitting,
                'metrics': complexity_metrics,
                'recommendations': self._generate_split_recommendations(complexity_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"文本复杂度分析失败: {e}")
            return {'complexity_score': 0.5, 'needs_splitting': len(text) > 50}
    
    def _count_complex_structures(self, doc) -> int:
        """计算复杂语法结构数量"""
        complex_count = 0
        
        # 检测复杂句式标志
        complex_patterns = [
            r'因为.*所以', r'虽然.*但是', r'不仅.*而且',
            r'如果.*那么', r'当.*时', r'由于.*因此'
        ]
        
        text = doc.text
        for pattern in complex_patterns:
            complex_count += len(re.findall(pattern, text))
        
        # 检测从句数量
        subordinate_markers = ['SCONJ', 'mark']
        for token in doc:
            if token.pos_ == 'SCONJ' or token.dep_ == 'mark':
                complex_count += 1
        
        return complex_count
    
    def _calculate_dependency_depth(self, doc) -> float:
        """计算依存关系深度"""
        max_depth = 0
        
        def get_depth(token, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            for child in token.children:
                get_depth(child, current_depth + 1)
        
        for sent in doc.sents:
            get_depth(sent.root)
        
        return max_depth
    
    def _calculate_complexity_score(self, metrics: Dict[str, Any]) -> float:
        """计算综合复杂度分数"""
        # 标准化各项指标
        token_score = min(metrics['token_count'] / 100.0, 1.0)
        length_score = min(metrics['avg_sentence_length'] / 30.0, 1.0)
        structure_score = min(metrics['complex_structures'] / 5.0, 1.0)
        depth_score = min(metrics['dependency_depth'] / 10.0, 1.0)
        diversity_score = metrics['pos_diversity']
        
        # 加权计算
        weights = {
            'token': 0.3,
            'length': 0.25,
            'structure': 0.2,
            'depth': 0.15,
            'diversity': 0.1
        }
        
        complexity_score = (
            token_score * weights['token'] +
            length_score * weights['length'] +
            structure_score * weights['structure'] +
            depth_score * weights['depth'] +
            diversity_score * weights['diversity']
        )
        
        return min(complexity_score, 1.0)
    
    def _generate_split_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """生成分割建议"""
        recommendations = []
        
        if metrics['token_count'] > 50:
            recommendations.append("文本过长，建议进行句法分割")
        
        if metrics['avg_sentence_length'] > 25:
            recommendations.append("平均句长过长，建议在连词处分割")
        
        if metrics['complex_structures'] > 2:
            recommendations.append("包含复杂句式，建议在逻辑连接处分割")
        
        if metrics['dependency_depth'] > 8:
            recommendations.append("依存关系复杂，建议简化句子结构")
        
        if not recommendations:
            recommendations.append("文本结构良好，无需额外分割")
        
        return recommendations
    
    def batch_process(self, texts: List[str], 
                     method: str = 'sentences', 
                     language: str = 'zh') -> List[List[str]]:
        """
        批量处理文本列表
        
        Args:
            texts: 文本列表
            method: 处理方法 ('sentences' 或 'syntax')
            language: 语言代码
            
        Returns:
            List[List[str]]: 每个文本的分割结果
        """
        results = []
        
        for i, text in enumerate(texts):
            try:
                if method == 'sentences':
                    result = self.split_by_sentences(text, language)
                elif method == 'syntax':
                    result = self.split_by_syntax(text, language)
                else:
                    raise ValueError(f"不支持的处理方法: {method}")
                
                results.append(result)
                
                if i % 10 == 0:  # 每处理10个文本记录一次进度
                    self.logger.debug(f"批量处理进度: {i+1}/{len(texts)}")
                    
            except Exception as e:
                self.logger.error(f"批量处理第{i+1}个文本失败: {e}")
                results.append([text])  # 失败时返回原文
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            'loaded_models': list(self.nlp_cache.keys()),
            'available_models': self.models,
            'cache_size': len(self.nlp_cache),
            'config': self.config
        }
        
        # 获取已加载模型的详细信息
        for lang, nlp in self.nlp_cache.items():
            info[f'{lang}_model_info'] = {
                'meta': nlp.meta,
                'pipe_names': nlp.pipe_names,
                'disabled': nlp.disabled,
                'max_length': nlp.max_length
            }
        
        return info


# 便捷函数
def create_spacy_processor(config: Optional[Dict[str, Any]] = None) -> SpacyProcessor:
    """创建Spacy处理器的便捷函数"""
    return SpacyProcessor(config)


def quick_sentence_split(text: str, language: str = 'zh') -> List[str]:
    """快速句子分割的便捷函数"""
    processor = create_spacy_processor()
    return processor.split_by_sentences(text, language)


def quick_syntax_split(text: str, language: str = 'zh') -> List[str]:
    """快速句法分割的便捷函数"""
    processor = create_spacy_processor()
    return processor.split_by_syntax(text, language)