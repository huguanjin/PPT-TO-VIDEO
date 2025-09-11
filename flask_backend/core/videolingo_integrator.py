"""
VideoLingo技术融合集成器
基于项目优化计划的第一阶段实施
整合动态规划分割、Spacy语法分析和智能配置预设
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import time

# 导入核心组件
try:
    from .algorithms.dp_sentence_splitter import DynamicProgrammingSplitter
except ImportError:
    try:
        from algorithms.dp_sentence_splitter import DynamicProgrammingSplitter
    except ImportError:
        DynamicProgrammingSplitter = None

try:
    from .nlp_utils.spacy_processor import SpacyProcessor
except ImportError:
    try:
        from nlp_utils.spacy_processor import SpacyProcessor
    except ImportError:
        SpacyProcessor = None

try:
    from .smart_config_loader import SmartSubtitleConfigLoader, ConfigContext
except ImportError:
    try:
        from smart_config_loader import SmartSubtitleConfigLoader, ConfigContext
    except ImportError:
        SmartSubtitleConfigLoader = None
        ConfigContext = None

try:
    from .config_presets import ConfigPresets
except ImportError:
    try:
        from config_presets import ConfigPresets
    except ImportError:
        ConfigPresets = None

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    method: str
    segments: List[str]
    processing_time: float
    quality_score: float
    metadata: Dict[str, Any]


class VideoLingoIntegrator:
    """
    VideoLingo技术融合集成器
    
    主要功能：
    1. 智能配置管理（简化、标准、专业模式）
    2. 动态规划分割算法集成
    3. Spacy语法分析增强
    4. 多算法融合处理
    5. 性能优化和降级机制
    """
    
    def __init__(self, project_dir: Optional[str] = None):
        self.project_dir = project_dir or os.getcwd()
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个组件
        self._init_components()
        
        # 处理统计
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'fallback_count': 0,
            'avg_processing_time': 0.0,
            'method_usage': {}
        }
    
    def _init_components(self):
        """初始化各个组件"""
        # 1. 智能配置加载器
        if SmartSubtitleConfigLoader:
            self.config_loader = SmartSubtitleConfigLoader(self.project_dir)
            self.logger.info("智能配置加载器初始化成功")
        else:
            self.config_loader = None
            self.logger.warning("智能配置加载器不可用")
        
        # 2. 动态规划分割器
        if DynamicProgrammingSplitter:
            self.dp_splitter = DynamicProgrammingSplitter()
            self.logger.info("动态规划分割器初始化成功")
        else:
            self.dp_splitter = None
            self.logger.warning("动态规划分割器不可用")
        
        # 3. Spacy处理器
        if SpacyProcessor:
            self.spacy_processor = SpacyProcessor()
            self.logger.info("Spacy处理器初始化成功")
        else:
            self.spacy_processor = None
            self.logger.warning("Spacy处理器不可用")
        
        # 4. 配置预设管理器
        if ConfigPresets:
            self.config_presets = ConfigPresets()
            self.logger.info("配置预设管理器初始化成功")
        else:
            self.config_presets = None
            self.logger.warning("配置预设管理器不可用")
    
    def process_text_smart(self, 
                          text: str,
                          config_preset: str = "standard",
                          custom_config: Optional[Dict[str, Any]] = None,
                          context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        智能文本处理（主入口方法）
        
        Args:
            text: 要处理的文本
            config_preset: 配置预设名称
            custom_config: 自定义配置覆盖
            context: 处理上下文
            
        Returns:
            处理结果
        """
        start_time = time.time()
        
        try:
            # 1. 加载配置
            config = self._load_smart_config(config_preset, custom_config, context)
            
            # 2. 选择处理策略
            processing_method = self._select_processing_method(text, config)
            
            # 3. 执行处理
            segments = self._execute_processing(text, config, processing_method)
            
            # 4. 质量评估
            quality_score = self._evaluate_quality(segments, text, config)
            
            # 5. 更新统计
            processing_time = time.time() - start_time
            self._update_stats(processing_method, processing_time, True)
            
            return ProcessingResult(
                success=True,
                method=processing_method,
                segments=segments,
                processing_time=processing_time,
                quality_score=quality_score,
                metadata={
                    'original_length': len(text),
                    'segment_count': len(segments),
                    'config_preset': config_preset,
                    'processing_method': processing_method
                }
            )
        
        except Exception as e:
            self.logger.error(f"智能文本处理失败: {e}")
            processing_time = time.time() - start_time
            self._update_stats('fallback', processing_time, False)
            
            return ProcessingResult(
                success=False,
                method='fallback',
                segments=self._fallback_split(text),
                processing_time=processing_time,
                quality_score=0.3,
                metadata={'error': str(e)}
            )
    
    def _load_smart_config(self, 
                          preset_name: str,
                          custom_config: Optional[Dict[str, Any]] = None,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """加载智能配置"""
        if self.config_loader:
            # 创建配置上下文
            config_context = None
            if context and ConfigContext:
                config_context = ConfigContext(
                    preset_name=preset_name,
                    user_overrides=custom_config or {},
                    project_type=context.get('project_type', 'general'),
                    performance_level=context.get('performance_level', 'balanced'),
                    language=context.get('language', 'auto'),
                    target_audience=context.get('target_audience', 'general')
                )
            
            config = self.config_loader.load_smart_config(
                preset_name, custom_config, config_context
            )
        else:
            # 降级配置
            config = self._get_fallback_config(preset_name)
        
        return config
    
    def _select_processing_method(self, text: str, config: Dict[str, Any]) -> str:
        """选择处理方法"""
        text_length = len(text)
        processing_mode = config.get('processing_mode', 'balanced')
        
        # 根据配置和文本特点选择方法
        if processing_mode == 'fast':
            if text_length < 100:
                return 'simple'
            else:
                return 'dp_only'
        
        elif processing_mode == 'quality':
            if config.get('use_spacy', False) and self.spacy_processor:
                if config.get('use_dp_algorithm', False) and self.dp_splitter:
                    return 'hybrid_advanced'
                else:
                    return 'spacy_enhanced'
            elif config.get('use_dp_algorithm', False) and self.dp_splitter:
                return 'dp_enhanced'
            else:
                return 'rule_based'
        
        else:  # balanced
            if text_length > 200 and config.get('use_dp_algorithm', False) and self.dp_splitter:
                return 'dp_balanced'
            elif config.get('use_spacy', False) and self.spacy_processor:
                return 'spacy_balanced'
            else:
                return 'rule_based'
    
    def _execute_processing(self, 
                          text: str, 
                          config: Dict[str, Any], 
                          method: str) -> List[str]:
        """执行具体的处理方法"""
        max_length = config.get('max_length', 75)
        language = config.get('language', 'auto')
        
        if method == 'hybrid_advanced':
            return self._hybrid_advanced_split(text, config)
        
        elif method == 'dp_enhanced':
            return self._dp_enhanced_split(text, config)
        
        elif method == 'spacy_enhanced':
            return self._spacy_enhanced_split(text, config)
        
        elif method == 'dp_balanced':
            return self._dp_balanced_split(text, config)
        
        elif method == 'spacy_balanced':
            return self._spacy_balanced_split(text, config)
        
        elif method == 'dp_only':
            if self.dp_splitter:
                return self.dp_splitter.split_text(text, language, use_spacy=False)
            else:
                return self._rule_based_split(text, config)
        
        elif method == 'rule_based':
            return self._rule_based_split(text, config)
        
        elif method == 'simple':
            return self._simple_split(text, max_length)
        
        else:
            return self._fallback_split(text)
    
    def _hybrid_advanced_split(self, text: str, config: Dict[str, Any]) -> List[str]:
        """混合高级分割（Spacy + 动态规划）"""
        try:
            # 1. 使用Spacy进行语法分析
            if self.spacy_processor:
                language = config.get('language', 'auto')
                analysis = self.spacy_processor.analyze_sentence_structure(text, language)
                
                if analysis['success'] and analysis['method'] == 'spacy':
                    # 2. 基于Spacy分析结果，使用动态规划优化分割点
                    candidates = analysis.get('split_candidates', [])
                    if candidates and self.dp_splitter:
                        return self._dp_with_spacy_guidance(text, analysis, config)
                
                # 3. 如果Spacy分析失败，降级到动态规划
                if self.dp_splitter:
                    return self.dp_splitter.split_text(text, language)
            
            # 4. 最终降级
            return self._rule_based_split(text, config)
        
        except Exception as e:
            self.logger.warning(f"混合高级分割失败: {e}")
            return self._rule_based_split(text, config)
    
    def _dp_enhanced_split(self, text: str, config: Dict[str, Any]) -> List[str]:
        """增强动态规划分割"""
        if not self.dp_splitter:
            return self._rule_based_split(text, config)
        
        try:
            language = config.get('language', 'auto')
            use_spacy = config.get('use_spacy', False) and self.spacy_processor is not None
            
            return self.dp_splitter.split_text(text, language, use_spacy)
        
        except Exception as e:
            self.logger.warning(f"增强动态规划分割失败: {e}")
            return self._rule_based_split(text, config)
    
    def _spacy_enhanced_split(self, text: str, config: Dict[str, Any]) -> List[str]:
        """增强Spacy分割"""
        if not self.spacy_processor:
            return self._rule_based_split(text, config)
        
        try:
            language = config.get('language', 'auto')
            max_length = config.get('max_length', 75)
            
            return self.spacy_processor.smart_split_with_grammar(text, max_length, language)  # type: ignore
        
        except Exception as e:
            self.logger.warning(f"增强Spacy分割失败: {e}")
            return self._rule_based_split(text, config)
    
    def _dp_balanced_split(self, text: str, config: Dict[str, Any]) -> List[str]:
        """平衡动态规划分割"""
        if not self.dp_splitter:
            return self._rule_based_split(text, config)
        
        try:
            language = config.get('language', 'auto')
            # 平衡模式：不使用Spacy以提高速度
            return self.dp_splitter.split_text(text, language, use_spacy=False)
        
        except Exception as e:
            self.logger.warning(f"平衡动态规划分割失败: {e}")
            return self._rule_based_split(text, config)
    
    def _spacy_balanced_split(self, text: str, config: Dict[str, Any]) -> List[str]:
        """平衡Spacy分割"""
        if not self.spacy_processor:
            return self._rule_based_split(text, config)
        
        try:
            language = config.get('language', 'auto')
            max_length = config.get('max_length', 75)
            
            # 使用较简单的分析避免过度计算
            return self.spacy_processor.smart_split_with_grammar(text, max_length, language)  # type: ignore
        
        except Exception as e:
            self.logger.warning(f"平衡Spacy分割失败: {e}")
            return self._rule_based_split(text, config)
    
    def _dp_with_spacy_guidance(self, 
                              text: str, 
                              spacy_analysis: Dict[str, Any], 
                              config: Dict[str, Any]) -> List[str]:
        """
        使用Spacy指导的动态规划分割
        这是VideoLingo技术融合的核心创新点
        """
        try:
            # 从Spacy分析中提取优质分割点
            good_splits = []
            for candidate in spacy_analysis.get('split_candidates', []):
                if candidate['confidence'] > 0.7:
                    good_splits.append(candidate['position'])
            
            # 如果有好的分割点，引导动态规划
            if good_splits and self.dp_splitter:
                # 按照分割点分段处理
                segments = []
                start = 0
                
                for split_pos in sorted(good_splits):
                    if split_pos > start:
                        segment_text = text[start:split_pos].strip()
                        if segment_text:
                            # 对每个段落使用动态规划进一步优化
                            sub_segments = self.dp_splitter.split_text(
                                segment_text, 
                                config.get('language', 'auto'),
                                use_spacy=False
                            )
                            segments.extend(sub_segments)
                        start = split_pos
                
                # 处理剩余部分
                if start < len(text):
                    remaining = text[start:].strip()
                    if remaining:
                        sub_segments = self.dp_splitter.split_text(
                            remaining, 
                            config.get('language', 'auto'),
                            use_spacy=False
                        )
                        segments.extend(sub_segments)
                
                return segments
            
            # 如果没有好的分割点，直接使用动态规划
            if self.dp_splitter:
                return self.dp_splitter.split_text(text, config.get('language', 'auto'))
            else:
                return self._rule_based_split(text, config)
        
        except Exception as e:
            self.logger.warning(f"Spacy指导动态规划失败: {e}")
            return self._rule_based_split(text, config)
    
    def _rule_based_split(self, text: str, config: Dict[str, Any]) -> List[str]:
        """基于规则的分割"""
        max_length = config.get('max_length', 75)
        line_break_chars = config.get('line_break_chars', '。！？；.,!?;')
        
        if len(text) <= max_length:
            return [text.strip()]
        
        # 按标点符号分割
        import re
        segments = []
        delimiters = '|'.join(re.escape(char) for char in line_break_chars)
        parts = re.split(f'([{delimiters}])', text)
        
        current = ""
        for part in parts:
            if part.strip():
                test_segment = (current + part).strip()
                if len(test_segment) <= max_length:
                    current = test_segment
                else:
                    if current:
                        segments.append(current)
                    current = part.strip()
        
        if current:
            segments.append(current)
        
        return segments if segments else [text.strip()]
    
    def _simple_split(self, text: str, max_length: int) -> List[str]:
        """简单分割"""
        if len(text) <= max_length:
            return [text.strip()]
        
        segments = []
        current_pos = 0
        
        while current_pos < len(text):
            end_pos = min(current_pos + max_length, len(text))
            segment = text[current_pos:end_pos].strip()
            if segment:
                segments.append(segment)
            current_pos = end_pos
        
        return segments
    
    def _fallback_split(self, text: str) -> List[str]:
        """降级分割"""
        return self._simple_split(text, 75)
    
    def _evaluate_quality(self, 
                        segments: List[str], 
                        original_text: str, 
                        config: Dict[str, Any]) -> float:
        """评估分割质量"""
        if not segments:
            return 0.0
        
        score = 0.0
        max_length = config.get('max_length', 75)
        
        # 1. 长度分布评分
        length_scores = []
        for segment in segments:
            length = len(segment)
            if length <= max_length:
                length_scores.append(1.0)
            else:
                length_scores.append(max(0.0, 1.0 - (length - max_length) / max_length))
        
        score += sum(length_scores) / len(length_scores) * 0.4
        
        # 2. 完整性评分
        total_chars = sum(len(seg) for seg in segments)
        completeness = min(1.0, total_chars / len(original_text))
        score += completeness * 0.3
        
        # 3. 均匀性评分
        if len(segments) > 1:
            avg_length = total_chars / len(segments)
            variance = sum((len(seg) - avg_length) ** 2 for seg in segments) / len(segments)
            uniformity = max(0.0, 1.0 - variance / (avg_length ** 2))
            score += uniformity * 0.3
        else:
            score += 0.3
        
        return min(1.0, score)
    
    def _update_stats(self, method: str, processing_time: float, success: bool):
        """更新处理统计"""
        self.stats['total_processed'] += 1
        
        if success:
            self.stats['success_count'] += 1
        else:
            self.stats['fallback_count'] += 1
        
        # 更新平均处理时间
        total_time = self.stats['avg_processing_time'] * (self.stats['total_processed'] - 1)
        self.stats['avg_processing_time'] = (total_time + processing_time) / self.stats['total_processed']
        
        # 更新方法使用统计
        if method not in self.stats['method_usage']:
            self.stats['method_usage'][method] = 0
        self.stats['method_usage'][method] += 1
    
    def _get_fallback_config(self, preset_name: str) -> Dict[str, Any]:
        """获取降级配置"""
        fallback_configs = {
            'simple': {
                'max_length': 75,
                'processing_mode': 'fast',
                'use_dp_algorithm': False,
                'use_spacy': False
            },
            'standard': {
                'max_length': 75,
                'processing_mode': 'balanced',
                'use_dp_algorithm': True,
                'use_spacy': False
            },
            'professional': {
                'max_length': 40,
                'processing_mode': 'quality',
                'use_dp_algorithm': True,
                'use_spacy': True
            }
        }
        
        return fallback_configs.get(preset_name, fallback_configs['standard'])
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.stats.copy()
    
    def get_available_presets(self) -> List[Dict[str, Any]]:
        """获取可用配置预设"""
        if self.config_loader:
            return self.config_loader.get_available_presets()
        else:
            return [
                {"key": "simple", "name": "简化模式", "description": "快速处理"},
                {"key": "standard", "name": "标准模式", "description": "平衡质量和效率"},
                {"key": "professional", "name": "专业模式", "description": "最高质量"}
            ]
    
    def is_videolingo_ready(self) -> Dict[str, bool]:
        """检查VideoLingo技术组件可用性"""
        return {
            'config_loader': self.config_loader is not None,
            'dp_splitter': self.dp_splitter is not None,
            'spacy_processor': self.spacy_processor is not None,
            'config_presets': self.config_presets is not None,
            'full_integration': all([
                self.config_loader is not None,
                self.dp_splitter is not None,
                self.spacy_processor is not None,
                self.config_presets is not None
            ])
        }


def test_videolingo_integration():
    """测试VideoLingo技术融合"""
    integrator = VideoLingoIntegrator()
    
    print("=== VideoLingo技术融合测试 ===")
    
    # 1. 组件可用性检查
    readiness = integrator.is_videolingo_ready()
    print(f"\n组件可用性:")
    for component, available in readiness.items():
        status = "✅" if available else "❌"
        print(f"  {component}: {status}")
    
    # 2. 预设配置测试
    print(f"\n可用预设:")
    presets = integrator.get_available_presets()
    for preset in presets:
        print(f"  - {preset['name']}: {preset['description']}")
    
    # 3. 文本处理测试
    test_texts = [
        "这是一个简单的测试文本。",
        "这是一个比较复杂的测试文本，包含了多个句子和复杂的语法结构，需要进行智能分割处理来确保最佳的显示效果。",
        "This is a complex English sentence that demonstrates the advanced capabilities of the VideoLingo technology integration system."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n=== 测试文本 {i} ===")
        print(f"原文: {text}")
        
        # 测试不同预设
        for preset in ['simple', 'standard', 'professional']:
            result = integrator.process_text_smart(
                text, 
                config_preset=preset,
                context={'project_type': 'education', 'language': 'auto'}
            )
            
            print(f"\n{preset}模式结果:")
            print(f"  成功: {result.success}")
            print(f"  方法: {result.method}")
            print(f"  质量分数: {result.quality_score:.2f}")
            print(f"  处理时间: {result.processing_time:.3f}s")
            print(f"  分割结果:")
            for j, segment in enumerate(result.segments, 1):
                print(f"    {j}. {segment}")
    
    # 4. 性能统计
    print(f"\n=== 处理统计 ===")
    stats = integrator.get_processing_stats()
    print(f"总处理次数: {stats['total_processed']}")
    print(f"成功次数: {stats['success_count']}")
    print(f"降级次数: {stats['fallback_count']}")
    print(f"平均处理时间: {stats['avg_processing_time']:.3f}s")
    print(f"方法使用统计: {stats['method_usage']}")


if __name__ == "__main__":
    test_videolingo_integration()
