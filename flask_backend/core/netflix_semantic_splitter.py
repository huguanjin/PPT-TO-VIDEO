"""
Netflix级别语义分割器 - Phase 2核心实现
集成双层分割架构：NLP预处理 + AI语义优化
"""

# 导入NumPy兼容性修复
try:
    from ..utils.numpy_compatibility_fix import *
except ImportError:
    pass

import asyncio
import time
import json
from typing import List, Dict, Optional, Any, Tuple
from difflib import SequenceMatcher
from pathlib import Path
import logging

# Phase 1基础设施
from ..utils.nlp_preprocessor import NetflixStyleNLPPreprocessor
from ..utils.netflix_config_loader import NetflixConfigLoader
from ..utils.netflix_quality_metrics import NetflixQualityMetrics

# 现有AI管理器（假设存在）
try:
    from ..utils.ai_model_manager import CustomAIModelManager, AIAnalysisRequest
except ImportError:
    # 如果不存在，创建模拟版本
    class CustomAIModelManager:
        def __init__(self):
            self.models = ["gemini-2.0-flash-custom"]
        
        async def analyze_content(self, request, model_name):
            # 模拟AI响应
            class MockResponse:
                def __init__(self):
                    self.success = True
                    self.content = '{"choice": "1", "split1": "测试[分割]内容", "analysis": "分析结果"}'
            return MockResponse()
    
    class AIAnalysisRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

class NetflixStyleSemanticSplitter:
    """Netflix级别语义分割器 - 双层架构实现"""
    
    def __init__(self, config_loader: Optional[NetflixConfigLoader] = None, 
                 ai_manager: Optional[CustomAIModelManager] = None,
                 quality_metrics: Optional[NetflixQualityMetrics] = None):
        """
        初始化Netflix级别语义分割器
        
        Args:
            config_loader: 配置加载器
            ai_manager: AI模型管理器
            quality_metrics: 质量监控器
        """
        self.logger = logging.getLogger(__name__)
        
        # 配置管理
        self.config = config_loader or NetflixConfigLoader()
        self.netflix_standards = self.config.netflix_standards
        self.ai_settings = self.config.ai_settings
        
        # Phase 1基础设施
        self.nlp_preprocessor = NetflixStyleNLPPreprocessor()
        self.quality_metrics = quality_metrics or NetflixQualityMetrics(self.config)
        
        # AI模型管理
        self.ai_manager = ai_manager
        self.model_name = self.ai_settings.get('preferred_model', 'gemini-2.0-flash-custom')
        self.fallback_model = self.ai_settings.get('fallback_model', 'gemini-1.5-pro')
        
        # Netflix质量标准
        self.similarity_threshold = self.netflix_standards.get('similarity_threshold', 0.9)
        self.max_retry_attempts = self.netflix_standards.get('max_retry_attempts', 3)
        self.max_chars_per_line = self.netflix_standards.get('max_chars_per_line', 20)
        self.min_chars_per_line = self.netflix_standards.get('min_chars_per_line', 3)
        
        # 性能设置
        self.enable_caching = self.config.is_feature_enabled('caching')
        self.cache = {} if self.enable_caching else None
        
        self.logger.info(f"Netflix语义分割器初始化完成，使用模型: {self.model_name}")
    
    async def netflix_style_split(self, text: str, target_lines: int = 2) -> Dict[str, Any]:
        """
        Netflix级别的双层分割处理
        
        Args:
            text: 输入文本
            target_lines: 目标行数
            
        Returns:
            分割结果字典，包含分割文本、方法、质量信息等
        """
        start_time = time.time()
        
        try:
            # 缓存检查
            cache_key = f"{hash(text)}_{target_lines}"
            if self.enable_caching and cache_key in self.cache:
                self.logger.debug(f"从缓存返回结果: {text[:20]}...")
                return self.cache[cache_key]
            
            # 第一层：NLP预处理
            preprocessing_start = time.time()
            preprocessed_segments = self.nlp_preprocessor.preprocess_text(text)
            preprocessing_time = time.time() - preprocessing_start
            
            if not preprocessed_segments:
                return self._create_result(
                    original=text,
                    segments=[text] if text.strip() else [],
                    method='fallback_empty',
                    processing_time=time.time() - start_time,
                    error="空文本或预处理失败"
                )
            
            # 判断是否需要AI优化
            needs_ai_optimization = any(segment['need_ai_split'] for segment in preprocessed_segments)
            
            if not needs_ai_optimization:
                # 简单情况：仅使用NLP预处理结果
                result = self._create_simple_nlp_result(text, preprocessed_segments, start_time)
                self._cache_result(cache_key, result)
                return result
            
            # 第二层：AI语义优化
            ai_start = time.time()
            ai_result = await self._netflix_ai_split(text, preprocessed_segments, target_lines)
            ai_time = time.time() - ai_start
            
            if ai_result['success']:
                # AI分割成功
                result = self._create_result(
                    original=text,
                    segments=ai_result['segments'],
                    method='ai_enhanced',
                    processing_time=time.time() - start_time,
                    preprocessing_time=preprocessing_time,
                    ai_time=ai_time,
                    quality_info=ai_result.get('quality_info', {}),
                    ai_analysis=ai_result.get('analysis', '')
                )
            else:
                # AI失败，回退到NLP分割
                result = self._create_nlp_fallback_result(text, preprocessed_segments, start_time, ai_result.get('error'))
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            # 记录质量指标
            self._record_quality_metrics(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分割处理异常: {e}")
            return self._create_result(
                original=text,
                segments=[text] if text.strip() else [],
                method='error_fallback',
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _netflix_ai_split(self, text: str, preprocessed_segments: List[Dict], 
                               target_lines: int) -> Dict[str, Any]:
        """Netflix标准的AI分割处理"""
        if not self.ai_manager or self.model_name not in self.ai_manager.models:
            return {'success': False, 'error': 'AI模型不可用'}
        
        # 提取保护单元
        protected_units = []
        for segment in preprocessed_segments:
            protected_units.extend(segment.get('semantic_units', []))
        
        # 构建Netflix提示词
        prompt = self._build_netflix_prompt(text, preprocessed_segments, protected_units, target_lines)
        
        # AI分割尝试（带重试）
        for attempt in range(self.max_retry_attempts):
            try:
                # 创建AI请求
                request = AIAnalysisRequest(
                    text=prompt,
                    task_type="netflix_subtitle_split",
                    language="zh",
                    max_output_length=self.ai_settings.get('max_tokens', 800),
                    temperature=self.ai_settings.get('temperature', 0.3)
                )
                
                # 选择模型
                current_model = self.model_name if attempt == 0 else self.fallback_model
                
                # 调用AI
                ai_response = await self.ai_manager.analyze_content(request, current_model)
                
                if ai_response and ai_response.success:
                    # 解析AI响应
                    parsed_result = self._parse_netflix_ai_response(ai_response.content)
                    
                    if parsed_result:
                        # 序列匹配验证
                        validated_segments = self._sequence_matching_validation(
                            text, parsed_result['segments'], protected_units
                        )
                        
                        if validated_segments:
                            return {
                                'success': True,
                                'segments': validated_segments,
                                'quality_info': {
                                    'similarity_score': parsed_result.get('similarity_score', 0.0),
                                    'netflix_compliant': parsed_result.get('netflix_compliant', False),
                                    'attempt': attempt + 1,
                                    'model_used': current_model
                                },
                                'analysis': parsed_result.get('analysis', ''),
                                'method_details': {
                                    'split_method': parsed_result.get('split_method', ''),
                                    'reasoning': parsed_result.get('reasoning', '')
                                }
                            }
                        else:
                            self.logger.warning(f"序列匹配验证失败，尝试 {attempt + 1}")
                    else:
                        self.logger.warning(f"AI响应解析失败，尝试 {attempt + 1}")
                else:
                    self.logger.warning(f"AI调用失败，尝试 {attempt + 1}")
                
                # 重试前的延迟
                if attempt < self.max_retry_attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    
            except Exception as e:
                self.logger.error(f"AI分割尝试 {attempt + 1} 异常: {e}")
                if attempt < self.max_retry_attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
        
        return {'success': False, 'error': f'AI分割失败，已尝试{self.max_retry_attempts}次'}
    
    def _build_netflix_prompt(self, text: str, preprocessed_segments: List[Dict], 
                             protected_units: List[Dict], target_lines: int) -> str:
        """构建Netflix标准的专业提示词"""
        
        # 分析预处理结果
        complexity_scores = [seg['complexity'] for seg in preprocessed_segments]
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        # 收集分割候选点
        all_candidates = []
        for segment in preprocessed_segments:
            all_candidates.extend(segment.get('split_candidates', []))
        
        # 保护单元信息
        protected_terms = [unit['text'] for unit in protected_units]
        protected_types = list(set(unit['type'] for unit in protected_units))
        
        # 语言学特征
        linguistic_info = []
        for segment in preprocessed_segments:
            features = segment.get('linguistic_features', {})
            if features:
                linguistic_info.append({
                    'verb_count': features.get('verb_count', 0),
                    'noun_count': features.get('noun_count', 0),
                    'sentence_count': features.get('sentence_count', 0)
                })
        
        prompt = f"""## Role
你是一位专业的Netflix中文字幕分割专家，专门负责教育内容的字幕优化。

## Task
将给定的字幕文本分割成{target_lines}行，确保符合Netflix单行显示标准，同时保持语义完整性。

## Netflix Standards
1. 单行显示优先：每行独立完整，避免跨行阅读
2. 字符限制：每行{self.min_chars_per_line}-{self.max_chars_per_line}个字符
3. 长度均衡：各行长度尽量均衡（最大比例2.5:1）
4. 语义连贯：保持句子意思的完整性
5. 自然分割：在标点符号、连词或语法边界处分割
6. 保护特殊内容：确保URL、邮箱、技术术语完整

## Text Analysis
**原文**：{text}
**字符数**：{len(text)}
**复杂度评分**：{avg_complexity:.2f}/10
**保护单元**：{protected_terms}
**保护类型**：{protected_types}
**语言学特征**：动词 {sum(info.get('verb_count', 0) for info in linguistic_info)}个，名词 {sum(info.get('noun_count', 0) for info in linguistic_info)}个

## Candidate Split Points
基于NLP分析的推荐分割点：
{self._format_split_candidates(all_candidates, text)}

## Steps
1. **Structure Analysis**: 分析句子结构、识别关键分割挑战
2. **Generate Approaches**: 生成两种不同的分割方案
3. **Quality Assessment**: 从可读性、语义保持、Netflix标准三个维度评估
4. **Select Best**: 选择最佳方案并说明理由

## Output Format (JSON Only)
```json
{{
    "analysis": "句子结构分析和主要分割挑战的简要描述",
    "split1": "第一种分割方案，用[分割]标记分割位置",
    "split2": "第二种分割方案，用[分割]标记分割位置", 
    "assessment": "两种方案的详细比较，突出各自的优缺点",
    "choice": "1 或 2",
    "reasoning": "选择该方案的具体理由",
    "netflix_compliant": true/false,
    "protected_terms_preserved": true/false,
    "split_method": "所使用的主要分割策略（如：标点分割、语法分割、语义分割）"
}}
```

请严格按照JSON格式输出，确保结构完整且语法正确。"""
        
        return prompt
    
    def _format_split_candidates(self, candidates: List[Dict], text: str) -> str:
        """格式化分割候选点信息"""
        if not candidates:
            return "未发现明显的分割候选点"
        
        formatted = []
        for i, candidate in enumerate(candidates[:5]):  # 只显示前5个
            pos = candidate.get('char_position', 0)
            token = candidate.get('token', '')
            score = candidate.get('score', 0)
            reasons = candidate.get('reasons', [])
            
            context_start = max(0, pos - 5)
            context_end = min(len(text), pos + 6)
            context = text[context_start:context_end]
            
            formatted.append(f"  {i+1}. 位置{pos}: '{token}' (评分:{score:.2f}, 原因:{','.join(reasons)}) 上下文:'{context}'")
        
        return '\n'.join(formatted)
    
    def _parse_netflix_ai_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """解析Netflix AI响应"""
        try:
            # 清理响应内容
            cleaned_content = response_content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            
            # 解析JSON
            data = json.loads(cleaned_content)
            
            # 验证必需字段
            required_fields = ['choice', 'split1', 'split2', 'analysis']
            if not all(field in data for field in required_fields):
                self.logger.error(f"AI响应缺少必需字段: {required_fields}")
                return None
            
            # 选择最佳分割方案
            choice = str(data['choice']).strip()
            if choice == '1':
                chosen_split = data['split1']
            elif choice == '2':
                chosen_split = data['split2']
            else:
                self.logger.error(f"无效的选择: {choice}")
                return None
            
            # 解析分割文本
            segments = [seg.strip() for seg in chosen_split.split('[分割]') if seg.strip()]
            
            if not segments:
                self.logger.error("分割结果为空")
                return None
            
            return {
                'segments': segments,
                'analysis': data.get('analysis', ''),
                'split_method': data.get('split_method', 'ai_semantic'),
                'reasoning': data.get('reasoning', ''),
                'netflix_compliant': data.get('netflix_compliant', False),
                'protected_terms_preserved': data.get('protected_terms_preserved', True),
                'choice': choice,
                'all_splits': {
                    '1': data['split1'],
                    '2': data['split2']
                },
                'assessment': data.get('assessment', '')
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"AI响应JSON解析失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"AI响应解析异常: {e}")
            return None
    
    def _sequence_matching_validation(self, original: str, segments: List[str], 
                                    protected_units: List[Dict]) -> Optional[List[str]]:
        """序列匹配验证算法 - Netflix质量标准"""
        
        # 重构分割文本
        reconstructed = ''.join(segments)
        
        # 计算相似度
        similarity = SequenceMatcher(None, original.replace(' ', ''), reconstructed.replace(' ', '')).ratio()
        
        # 相似度检查
        if similarity < self.similarity_threshold:
            self.logger.warning(f"相似度不足: {similarity:.3f} < {self.similarity_threshold}")
            return None
        
        # 保护单元完整性检查
        for unit in protected_units:
            unit_text = unit['text']
            if unit_text not in reconstructed:
                self.logger.warning(f"保护单元丢失: {unit_text}")
                return None
        
        # Netflix合规性检查
        compliance_result = self._check_netflix_compliance_detailed(segments)
        if not compliance_result['is_acceptable']:
            self.logger.warning(f"Netflix合规性检查失败: {compliance_result['violations']}")
            return None
        
        self.logger.info(f"序列匹配验证通过，相似度: {similarity:.3f}")
        return segments
    
    def _check_netflix_compliance_detailed(self, segments: List[str]) -> Dict[str, Any]:
        """详细的Netflix合规性检查"""
        result = {
            'is_acceptable': True,
            'violations': [],
            'warnings': [],
            'scores': {}
        }
        
        if not segments:
            result['is_acceptable'] = False
            result['violations'].append('empty_segments')
            return result
        
        # 长度检查
        lengths = [len(seg.strip()) for seg in segments]
        result['scores']['lengths'] = lengths
        
        for i, length in enumerate(lengths):
            if length > self.max_chars_per_line:
                # 严重违规：超过最大长度
                if length > self.max_chars_per_line * 1.2:  # 超过20%
                    result['is_acceptable'] = False
                    result['violations'].append(f'line_{i+1}_severely_too_long_{length}')
                else:
                    # 轻微超长，警告但可接受
                    result['warnings'].append(f'line_{i+1}_slightly_too_long_{length}')
            elif length < self.min_chars_per_line and length > 0:
                result['warnings'].append(f'line_{i+1}_too_short_{length}')
        
        # 长度均衡检查
        if len(lengths) > 1:
            max_length = max(lengths)
            min_length = min([l for l in lengths if l > 0])  # 忽略空行
            if min_length > 0:
                balance_ratio = max_length / min_length
                result['scores']['balance_ratio'] = balance_ratio
                
                if balance_ratio > 3.0:  # Netflix建议2.5，我们放宽到3.0
                    result['warnings'].append(f'unbalanced_lengths_{balance_ratio:.2f}')
        
        return result
    
    def _create_result(self, original: str, segments: List[str], method: str, 
                      processing_time: float, **kwargs) -> Dict[str, Any]:
        """创建标准化的分割结果"""
        return {
            'original': original,
            'segments': segments,
            'method': method,
            'processing_time': processing_time,
            'timestamp': time.time(),
            'quality_metrics': {
                'segment_count': len(segments),
                'avg_length': sum(len(seg) for seg in segments) / len(segments) if segments else 0,
                'total_chars': sum(len(seg) for seg in segments),
                'original_chars': len(original)
            },
            **kwargs
        }
    
    def _create_simple_nlp_result(self, text: str, preprocessed_segments: List[Dict], 
                                 start_time: float) -> Dict[str, Any]:
        """创建简单NLP结果"""
        segments = [seg['text'] for seg in preprocessed_segments]
        return self._create_result(
            original=text,
            segments=segments,
            method='nlp_only',
            processing_time=time.time() - start_time,
            complexity_scores=[seg['complexity'] for seg in preprocessed_segments]
        )
    
    def _create_nlp_fallback_result(self, text: str, preprocessed_segments: List[Dict], 
                                   start_time: float, ai_error: str) -> Dict[str, Any]:
        """创建NLP回退结果"""
        # 智能NLP分割策略
        best_segments = self._intelligent_nlp_split(preprocessed_segments)
        
        return self._create_result(
            original=text,
            segments=best_segments,
            method='nlp_fallback',
            processing_time=time.time() - start_time,
            ai_error=ai_error,
            fallback_reason='ai_failed'
        )
    
    def _intelligent_nlp_split(self, preprocessed_segments: List[Dict]) -> List[str]:
        """智能NLP分割策略"""
        result_segments = []
        
        for segment in preprocessed_segments:
            text = segment['text']
            
            if not segment['need_ai_split']:
                # 简单片段直接使用
                result_segments.append(text)
            else:
                # 复杂片段使用NLP候选点分割
                candidates = segment.get('split_candidates', [])
                if candidates and len(text) > self.max_chars_per_line:
                    # 选择最佳分割点
                    best_candidate = candidates[0]  # 第一个候选点（评分最高）
                    split_pos = best_candidate['char_position']
                    
                    # 分割文本
                    part1 = text[:split_pos].strip()
                    part2 = text[split_pos:].strip()
                    
                    if part1 and part2:
                        result_segments.extend([part1, part2])
                    else:
                        result_segments.append(text)
                else:
                    result_segments.append(text)
        
        return result_segments
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """缓存结果"""
        if self.enable_caching and self.cache is not None:
            # 限制缓存大小
            cache_limit = self.config.performance_settings.get('cache_size', 1000)
            if len(self.cache) >= cache_limit:
                # 移除最旧的条目
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[cache_key] = result
    
    def _record_quality_metrics(self, result: Dict[str, Any]):
        """记录质量指标"""
        if self.quality_metrics:
            self.quality_metrics.record_split_result(
                original=result['original'],
                result=result['segments'],
                method=result['method'],
                processing_time=result['processing_time'],
                error=result.get('error')
            )
    
    def get_splitter_stats(self) -> Dict[str, Any]:
        """获取分割器统计信息"""
        stats = {
            'config': {
                'model_name': self.model_name,
                'similarity_threshold': self.similarity_threshold,
                'max_chars_per_line': self.max_chars_per_line,
                'enable_caching': self.enable_caching
            },
            'performance': {
                'cache_size': len(self.cache) if self.cache else 0,
                'cache_hit_rate': 0.0  # TODO: 实现缓存命中率统计
            }
        }
        
        if self.quality_metrics:
            stats['quality'] = self.quality_metrics.get_quality_report()
        
        return stats