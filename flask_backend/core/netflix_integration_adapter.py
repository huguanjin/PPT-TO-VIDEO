"""
Netflix语义分割器集成适配器 - Phase 2系统集成
将Netflix级别语义分割器无缝集成到现有字幕生成流程中
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass
import json

# 类型检查时的导入
if TYPE_CHECKING:
    from .netflix_semantic_splitter import NetflixStyleSemanticSplitter as NetflixSplitterType
else:
    NetflixSplitterType = Any

# Phase 2核心组件
NETFLIX_SPLITTER_AVAILABLE = False

# 创建模拟类
class MockNetflixStyleSemanticSplitter:
    def __init__(self, config_loader=None, ai_manager=None, quality_metrics=None, **kwargs):
        self.config_loader = config_loader
        self.ai_manager = ai_manager
        self.quality_metrics = quality_metrics
        
    async def netflix_style_split(self, text, target_lines=2):
        return {"segments": [text], "quality_score": 0.5}
        
    async def semantic_split(self, text, target_compliance='netflix'):
        return {"segments": [text], "quality_score": 0.5}

try:
    from .netflix_semantic_splitter import NetflixStyleSemanticSplitter
    NETFLIX_SPLITTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Netflix语义分割器导入失败: {e}")
    NetflixStyleSemanticSplitter = MockNetflixStyleSemanticSplitter
from .netflix_sequence_validator import NetflixSequenceValidator, ValidationResult
from .netflix_prompt_templates import NetflixPromptTemplateManager, PromptContext
from flask_backend.core.unified_config_manager import UnifiedConfigManager, ConfigContext, ConfigModuleType, ConfigComplexityLevel
from ..utils.netflix_quality_metrics import NetflixQualityMetrics

# 现有系统组件
try:
    # 注意：ai_model_manager 模块目前不可用
    # from ..utils.ai_model_manager import CustomAIModelManager
    from flask_backend.core.multiline_api_enhancement import MultilineFixEnhancementMiddleware
    from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
    CustomAIModelManager = None  # 暂时设为None
except ImportError:
    # 处理导入失败的情况
    CustomAIModelManager = None
    MultilineFixEnhancementMiddleware = None
    SubtitleMultilineFixer = None

@dataclass
class IntegrationConfig:
    """集成配置"""
    enable_netflix_splitter: bool = True
    enable_validation: bool = True
    enable_quality_monitoring: bool = True
    fallback_to_original: bool = True
    max_processing_time: float = 30.0
    compatibility_mode: str = 'enhanced'  # 'enhanced', 'compatible', 'legacy'
    
class NetflixSplitterIntegrationAdapter:
    """Netflix语义分割器集成适配器"""
    
    def __init__(self, project_dir: Optional[Path] = None, 
                 integration_config: Optional[IntegrationConfig] = None):
        """
        初始化集成适配器
        
        Args:
            project_dir: 项目目录路径
            integration_config: 集成配置
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.integration_config = integration_config or IntegrationConfig()
        self.logger = logging.getLogger(__name__)
        
        # 初始化Netflix组件
        self._init_netflix_components()
        
        # 初始化兼容性组件
        self._init_compatibility_components()
        
        # 性能监控
        self.processing_stats = {
            'total_processed': 0,
            'netflix_splits': 0,
            'fallback_splits': 0,
            'validation_failures': 0,
            'avg_processing_time': 0.0
        }
        
        self.logger.info(f"Netflix分割器集成适配器初始化完成，模式: {self.integration_config.compatibility_mode}")
    
    def _init_netflix_components(self):
        """初始化Netflix组件"""
        try:
            # 配置加载器
            self.config_loader = UnifiedConfigManager()
            
            # AI模型管理器
            if CustomAIModelManager:
                self.ai_manager = CustomAIModelManager()
            else:
                self.ai_manager = None
                self.logger.warning("AI模型管理器不可用，将使用模拟模式")
            
            # 质量监控器
            if self.integration_config.enable_quality_monitoring:
                self.quality_metrics = NetflixQualityMetrics(self.config_loader)
            else:
                self.quality_metrics = None
            
            # Netflix语义分割器
            if self.integration_config.enable_netflix_splitter and NETFLIX_SPLITTER_AVAILABLE:
                self.netflix_splitter = NetflixStyleSemanticSplitter(
                    config_manager=self.config_loader,
                    ai_manager=self.ai_manager,
                    quality_metrics=self.quality_metrics
                )
            else:
                self.netflix_splitter = NetflixStyleSemanticSplitter()  # 使用模拟版本
                if not NETFLIX_SPLITTER_AVAILABLE:
                    self.logger.warning("Netflix语义分割器不可用，使用模拟模式")
            
            # 序列验证器
            if self.integration_config.enable_validation:
                self.validator = NetflixSequenceValidator(config_manager=self.config_loader)
            else:
                self.validator = None
            
            # 提示词模板管理器
            self.prompt_manager = NetflixPromptTemplateManager(self.config_loader)
            
            self.logger.info("Netflix核心组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"Netflix组件初始化失败: {e}")
            # 设置为不可用状态
            self.netflix_splitter = None
            self.validator = None
            self.quality_metrics = None
    
    def _init_compatibility_components(self):
        """初始化兼容性组件"""
        try:
            # 多行修复增强中间件
            if MultilineFixEnhancementMiddleware:
                self.multiline_middleware = MultilineFixEnhancementMiddleware(
                    project_dir=self.project_dir
                )
            else:
                self.multiline_middleware = None
            
            # 传统字幕分割器（用于回退）
            if SubtitleMultilineFixer:
                self.legacy_fixer = SubtitleMultilineFixer()
            else:
                self.legacy_fixer = None
            
            self.logger.info("兼容性组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"兼容性组件初始化失败: {e}")
            self.multiline_middleware = None
            self.legacy_fixer = None
    
    async def enhanced_subtitle_split(self, text: str, target_lines: int = 2,
                                    context_data: Optional[Dict[str, Any]] = None,
                                    progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        增强版字幕分割 - 集成Netflix语义分割器
        
        Args:
            text: 输入文本
            target_lines: 目标行数
            context_data: 上下文数据（音频时长、位置信息等）
            progress_callback: 进度回调函数
            
        Returns:
            分割结果包含segments、method、quality_info等
        """
        start_time = time.time()
        
        # 进度通知
        if progress_callback:
            progress_callback("开始Netflix级语义分割...")
        
        try:
            # 统计更新
            self.processing_stats['total_processed'] += 1
            
            # 检查Netflix分割器可用性
            if not self.netflix_splitter:
                self.logger.info("Netflix分割器不可用，使用兼容模式")
                return await self._fallback_split(text, target_lines, "netflix_unavailable")
            
            # 预处理检查
            if not text.strip():
                return self._create_empty_result(text)
            
            # 长度检查
            netflix_context = ConfigContext(
                module_type=ConfigModuleType.NETFLIX,
                complexity_level=ConfigComplexityLevel.PROFESSIONAL
            )
            netflix_config = self.config_loader.get_config(netflix_context)
            max_chars = netflix_config.get('line_break_rules', {}).get('max_chars_per_line_chinese', 20)
            if len(text) <= max_chars:
                return self._create_simple_result(text, "text_too_short")
            
            if progress_callback:
                progress_callback("正在进行Netflix语义分割...")
            
            # 执行Netflix分割
            split_result = await self.netflix_splitter.netflix_style_split(text, target_lines)
            
            # 验证分割结果
            if self.validator and split_result.get('segments'):
                if progress_callback:
                    progress_callback("正在验证分割质量...")
                
                validation_result = self._validate_split_result(text, split_result)
                split_result['validation'] = validation_result
                
                # 如果验证失败且启用回退
                if not validation_result.is_valid and self.integration_config.fallback_to_original:
                    self.logger.warning(f"Netflix分割验证失败: {validation_result.error_details}")
                    self.processing_stats['validation_failures'] += 1
                    return await self._fallback_split(text, target_lines, "validation_failed", split_result)
            
            # 成功分割
            self.processing_stats['netflix_splits'] += 1
            processing_time = time.time() - start_time
            self._update_processing_stats(processing_time)
            
            # 应用兼容性增强
            enhanced_result = self._apply_compatibility_enhancements(split_result, context_data)
            
            if progress_callback:
                progress_callback("Netflix语义分割完成")
            
            self.logger.info(f"Netflix分割成功，处理时间: {processing_time:.2f}s")
            return enhanced_result
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Netflix分割超时 ({self.integration_config.max_processing_time}s)")
            return await self._fallback_split(text, target_lines, "timeout")
            
        except Exception as e:
            self.logger.error(f"Netflix分割异常: {e}")
            return await self._fallback_split(text, target_lines, "error", error_details=str(e))
    
    def _validate_split_result(self, original_text: str, split_result: Dict[str, Any]) -> ValidationResult:
        """验证分割结果"""
        if not self.validator:
            # 创建基础验证结果
            return ValidationResult(
                is_valid=True,
                similarity_score=1.0,
                netflix_compliant=True,
                error_details=[],
                warning_details=[],
                quality_metrics={},
                validation_time=0.0
            )
        
        segments = split_result.get('segments', [])
        
        # 从分割结果中提取保护单元信息
        protected_units = []
        if 'preprocessing_result' in split_result:
            for segment_info in split_result['preprocessing_result']:
                protected_units.extend(segment_info.get('semantic_units', []))
        
        return self.validator.comprehensive_validate(
            original=original_text,
            segments=segments,
            protected_units=protected_units,
            target_compliance='netflix'
        )
    
    async def _fallback_split(self, text: str, target_lines: int, reason: str, 
                            original_result: Optional[Dict[str, Any]] = None,
                            error_details: Optional[str] = None) -> Dict[str, Any]:
        """回退分割处理"""
        
        self.processing_stats['fallback_splits'] += 1
        
        # 尝试使用传统多行修复器
        if self.legacy_fixer:
            try:
                fallback_segments = self.legacy_fixer.optimize_subtitle_text(text).split('\n')
                fallback_segments = [seg.strip() for seg in fallback_segments if seg.strip()]
                
                if len(fallback_segments) == 0:
                    fallback_segments = [text]
                
                return {
                    'original': text,
                    'segments': fallback_segments,
                    'method': 'legacy_fallback',
                    'fallback_reason': reason,
                    'fallback_details': error_details,
                    'processing_time': 0.0,
                    'quality_metrics': {
                        'netflix_compliant': False,
                        'fallback_used': True
                    },
                    'original_netflix_result': original_result
                }
            except Exception as e:
                self.logger.error(f"传统分割器也失败: {e}")
        
        # 最终回退：简单分割
        simple_segments = self._simple_character_split(text, target_lines)
        
        return {
            'original': text,
            'segments': simple_segments,
            'method': 'simple_fallback',
            'fallback_reason': reason,
            'fallback_details': error_details,
            'processing_time': 0.0,
            'quality_metrics': {
                'netflix_compliant': False,
                'fallback_used': True,
                'final_fallback': True
            },
            'original_netflix_result': original_result
        }
    
    def _simple_character_split(self, text: str, target_lines: int) -> List[str]:
        """简单字符分割算法"""
        if target_lines <= 1:
            return [text]
        
        chars_per_line = len(text) // target_lines
        segments = []
        
        start = 0
        for i in range(target_lines - 1):
            end = start + chars_per_line
            # 尝试在标点符号处分割
            for offset in range(5):
                if end + offset < len(text) and text[end + offset] in '，。！？；：':
                    end = end + offset + 1
                    break
                if end - offset > start and text[end - offset] in '，。！？；：':
                    end = end - offset + 1
                    break
            
            segments.append(text[start:end].strip())
            start = end
        
        # 最后一段包含剩余所有内容
        if start < len(text):
            segments.append(text[start:].strip())
        
        return [seg for seg in segments if seg]
    
    def _apply_compatibility_enhancements(self, split_result: Dict[str, Any], 
                                        context_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """应用兼容性增强"""
        
        enhanced_result = split_result.copy()
        
        # 应用多行修复中间件（如果可用）
        if self.multiline_middleware:
            try:
                # 模拟API响应格式
                api_response = {
                    'subtitles': [
                        {'text': segment} for segment in split_result.get('segments', [])
                    ]
                }
                
                enhanced_response = self.multiline_middleware.enhance_subtitle_response(api_response)
                
                # 提取增强后的segments
                if 'subtitles' in enhanced_response:
                    enhanced_segments = [sub['text'] for sub in enhanced_response['subtitles']]
                    enhanced_result['segments'] = enhanced_segments
                    enhanced_result['multiline_enhanced'] = True
                
            except Exception as e:
                self.logger.warning(f"多行增强失败: {e}")
        
        # 添加兼容性元数据
        enhanced_result['integration_metadata'] = {
            'adapter_version': '2.0.0',
            'compatibility_mode': self.integration_config.compatibility_mode,
            'enhanced_features': {
                'netflix_splitter': bool(self.netflix_splitter),
                'sequence_validator': bool(self.validator),
                'quality_monitoring': bool(self.quality_metrics),
                'multiline_enhancement': bool(self.multiline_middleware)
            },
            'context_data': context_data or {}
        }
        
        return enhanced_result
    
    def _create_empty_result(self, text: str) -> Dict[str, Any]:
        """创建空文本结果"""
        return {
            'original': text,
            'segments': [] if not text.strip() else [text.strip()],
            'method': 'empty_text',
            'processing_time': 0.0,
            'quality_metrics': {
                'netflix_compliant': True,
                'empty_text': True
            }
        }
    
    def _create_simple_result(self, text: str, reason: str) -> Dict[str, Any]:
        """创建简单结果"""
        return {
            'original': text,
            'segments': [text.strip()],
            'method': 'simple_passthrough',
            'reason': reason,
            'processing_time': 0.0,
            'quality_metrics': {
                'netflix_compliant': True,
                'no_split_needed': True
            }
        }
    
    def _update_processing_stats(self, processing_time: float):
        """更新处理统计"""
        total = self.processing_stats['total_processed']
        current_avg = self.processing_stats['avg_processing_time']
        
        # 计算新的平均处理时间
        new_avg = ((current_avg * (total - 1)) + processing_time) / total
        self.processing_stats['avg_processing_time'] = new_avg
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            'netflix_components': {
                'splitter_available': bool(self.netflix_splitter),
                'validator_available': bool(self.validator),
                'quality_metrics_available': bool(self.quality_metrics),
                'prompt_manager_available': bool(self.prompt_manager)
            },
            'compatibility_components': {
                'multiline_middleware_available': bool(self.multiline_middleware),
                'legacy_fixer_available': bool(self.legacy_fixer)
            },
            'configuration': {
                'compatibility_mode': self.integration_config.compatibility_mode,
                'enable_netflix_splitter': self.integration_config.enable_netflix_splitter,
                'enable_validation': self.integration_config.enable_validation,
                'fallback_to_original': self.integration_config.fallback_to_original
            },
            'performance_stats': self.processing_stats.copy(),
            'performance_analysis': {
                'netflix_success_rate': self._calculate_netflix_success_rate(),
                'avg_processing_time': self.processing_stats['avg_processing_time'],
                'performance_grade': self._calculate_performance_grade()
            }
        }
    
    def _calculate_netflix_success_rate(self) -> float:
        """计算Netflix分割成功率"""
        total = self.processing_stats['total_processed']
        if total == 0:
            return 0.0
        
        netflix_splits = self.processing_stats['netflix_splits']
        return netflix_splits / total
    
    def _calculate_performance_grade(self) -> str:
        """计算性能等级"""
        success_rate = self._calculate_netflix_success_rate()
        avg_time = self.processing_stats['avg_processing_time']
        
        if success_rate >= 0.95 and avg_time <= 2.0:
            return 'A+'
        elif success_rate >= 0.9 and avg_time <= 3.0:
            return 'A'
        elif success_rate >= 0.85 and avg_time <= 5.0:
            return 'B+'
        elif success_rate >= 0.8 and avg_time <= 8.0:
            return 'B'
        elif success_rate >= 0.7:
            return 'C'
        else:
            return 'D'
    
    async def batch_process_subtitles(self, subtitle_items: List[Dict[str, Any]], 
                                    progress_callback: Optional[Callable[[int, str], None]] = None) -> List[Dict[str, Any]]:
        """批量处理字幕"""
        results = []
        total_items = len(subtitle_items)
        
        for i, item in enumerate(subtitle_items):
            if progress_callback:
                progress_callback(i, f"处理字幕 {i+1}/{total_items}")
            
            text = item.get('text', '')
            target_lines = item.get('target_lines', 2)
            context_data = item.get('context', {})
            
            result = await self.enhanced_subtitle_split(
                text=text,
                target_lines=target_lines,
                context_data=context_data
            )
            
            # 添加原始项目信息
            result['original_item'] = item
            result['batch_index'] = i
            
            results.append(result)
        
        if progress_callback:
            progress_callback(total_items, "批量处理完成")
        
        return results
    
    def create_enhanced_subtitle_api_response(self, split_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建增强版字幕API响应"""
        
        # 统计信息
        total_processed = len(split_results)
        netflix_splits = sum(1 for r in split_results if r.get('method') == 'ai_enhanced')
        validation_passes = sum(1 for r in split_results if r.get('validation', {}).get('is_valid', False))
        
        # 构建API响应
        api_response = {
            'subtitle_generation_completed': True,
            'netflix_enhanced': True,
            'total_subtitles': total_processed,
            'netflix_splits': netflix_splits,
            'validation_passes': validation_passes,
            'subtitle_segments': [],
            'quality_summary': {
                'netflix_success_rate': netflix_splits / total_processed if total_processed > 0 else 0,
                'validation_success_rate': validation_passes / total_processed if total_processed > 0 else 0,
                'overall_quality_grade': self._calculate_performance_grade()
            },
            'integration_info': {
                'adapter_version': '2.0.0',
                'netflix_components_active': bool(self.netflix_splitter),
                'compatibility_mode': self.integration_config.compatibility_mode
            }
        }
        
        # 转换分割结果为字幕段落
        for i, result in enumerate(split_results):
            segments = result.get('segments', [])
            
            for j, segment_text in enumerate(segments):
                subtitle_segment = {
                    'id': f"{i}_{j}",
                    'text': segment_text,
                    'original_text': result.get('original', ''),
                    'split_method': result.get('method', 'unknown'),
                    'netflix_compliant': result.get('quality_metrics', {}).get('netflix_compliant', False),
                    'validation_passed': result.get('validation', {}).get('is_valid', False),
                    'segment_index': j,
                    'total_segments': len(segments)
                }
                
                # 添加质量信息
                if 'validation' in result:
                    validation = result['validation']
                    subtitle_segment['quality_score'] = validation.overall_quality_score
                    subtitle_segment['similarity_score'] = validation.similarity_score
                
                api_response['subtitle_segments'].append(subtitle_segment)
        
        return api_response
    
    def integrate_with_enhanced_subtitle_generator(self, enhanced_generator) -> None:
        """与增强版字幕生成器集成"""
        
        # 保存原始方法
        if hasattr(enhanced_generator, '_original_split_method'):
            return  # 已经集成过
        
        original_method = getattr(enhanced_generator, 'split_subtitle_text', None)
        if original_method:
            enhanced_generator._original_split_method = original_method
        
        # 创建集成方法
        async def netflix_enhanced_split(text: str, target_lines: int = 2, **kwargs):
            """Netflix增强分割方法"""
            context_data = kwargs.get('context_data', {})
            
            # 使用Netflix分割器
            result = await self.enhanced_subtitle_split(
                text=text,
                target_lines=target_lines,
                context_data=context_data
            )
            
            # 返回兼容格式
            return result.get('segments', [text])
        
        # 替换原始方法
        enhanced_generator.split_subtitle_text = netflix_enhanced_split
        enhanced_generator._netflix_adapter = self
        
        self.logger.info("已集成到增强版字幕生成器")
    
    def __del__(self):
        """析构函数 - 清理资源"""
        try:
            if self.quality_metrics:
                # 保存最终统计
                final_report = self.quality_metrics.get_quality_report()
                self.logger.info(f"Netflix分割器适配器会话统计: {final_report}")
        except:
            pass