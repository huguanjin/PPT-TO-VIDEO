"""
增强版混合字幕分割器
集成VideoLingo的Spacy NLP处理能力与Netflix级字符权重标准
实现多层次分割策略：规则分割 -> NLP分割 -> AI语义分割
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

# 导入现有组件
from .ai_subtitle_splitter import AISemanticSplitter, HybridSubtitleSplitter
from .spacy_processor import SpacyProcessor
from .netflix_weight_calculator import NetflixCharacterWeightCalculator, CharacterWeightConfig

logger = logging.getLogger(__name__)


class EnhancedHybridSplitter(HybridSubtitleSplitter):
    """增强版混合字幕分割器 - 集成VideoLingo技术与Netflix标准"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化增强版混合分割器
        
        Args:
            config: 配置参数，支持NLP分割配置和Netflix权重配置
        """
        super().__init__(config)
        
        # NLP分割配置
        self.enable_nlp = self.config.get('enable_nlp_splitting', True)
        self.nlp_language = self.config.get('nlp_language', 'zh')
        self.nlp_complexity_threshold = self.config.get('nlp_complexity_threshold', 0.5)
        
        # 分割策略配置
        self.splitting_strategy = self.config.get('splitting_strategy', 'multi_level')  # 'rule_only', 'nlp_only', 'ai_only', 'multi_level'
        self.nlp_syntax_threshold = self.config.get('nlp_syntax_threshold', 40)  # 超过此长度启用句法分割
        
        # Netflix标准配置
        self.enable_netflix_standards = self.config.get('enable_netflix_standards', True)
        self.netflix_max_line_length = self.config.get('netflix_max_line_length', 42)
        self.cjk_weight_multiplier = self.config.get('cjk_weight_multiplier', 1.75)
        
        # 初始化Netflix权重计算器
        if self.enable_netflix_standards:
            try:
                netflix_config = CharacterWeightConfig(
                    max_line_length=self.netflix_max_line_length,
                    cjk_weight=self.cjk_weight_multiplier,
                    chinese_weight=self.cjk_weight_multiplier,
                    japanese_weight=self.cjk_weight_multiplier,
                    korean_weight=self.cjk_weight_multiplier
                )
                self.netflix_calculator = NetflixCharacterWeightCalculator(netflix_config)
                self.logger.info(f"Netflix权重计算器初始化成功 - CJK权重: {self.cjk_weight_multiplier}")
            except Exception as e:
                self.logger.warning(f"Netflix权重计算器初始化失败: {e}，将禁用Netflix标准")
                self.netflix_calculator = None
                self.enable_netflix_standards = False
        else:
            self.netflix_calculator = None
        
        # 初始化Spacy处理器
        if self.enable_nlp:
            try:
                nlp_config = {
                    'enable_cache': True,
                    'max_sentence_length': self.config.get('max_sentence_length', 100),
                    'min_split_length': self.config.get('min_split_length', 10)
                }
                self.spacy_processor = SpacyProcessor(nlp_config)
                self.logger.info("Spacy处理器初始化成功")
            except Exception as e:
                self.logger.warning(f"Spacy处理器初始化失败: {e}，将禁用NLP分割")
                self.spacy_processor = None
                self.enable_nlp = False
        else:
            self.spacy_processor = None
        
        self.logger.info(f"增强版分割器初始化完成 - 策略: {self.splitting_strategy}, NLP: {self.enable_nlp}")
    
    async def split_subtitle_text(self, text: str, strategy: Optional[str] = None) -> List[str]:
        """
        增强版字幕文本分割 - 支持多层次策略
        
        Args:
            text: 原始文本
            strategy: 分割策略，覆盖默认配置
            
        Returns:
            分割后的文本行列表
        """
        if not text or not text.strip():
            return []
        
        # 确定分割策略
        current_strategy = strategy or self.splitting_strategy
        
        self.logger.debug(f"开始分割字幕文本 (策略: {current_strategy}): {text}")
        
        # 根据策略执行分割
        if current_strategy == 'rule_only':
            return await self._rule_only_split(text)
        elif current_strategy == 'nlp_only':
            return await self._nlp_only_split(text)
        elif current_strategy == 'ai_only':
            return await self._ai_only_split(text)
        elif current_strategy == 'multi_level':
            return await self._multi_level_split(text)
        else:
            self.logger.warning(f"未知分割策略: {current_strategy}，使用多层次分割")
            return await self._multi_level_split(text)
    
    async def _rule_only_split(self, text: str) -> List[str]:
        """仅使用规则分割"""
        if hasattr(self, 'rule_processor'):
            return self.rule_processor.process_subtitle_text(text)
        else:
            # 简单的基于标点符号分割
            return self._simple_punctuation_split(text)
    
    async def _nlp_only_split(self, text: str) -> List[str]:
        """仅使用NLP分割"""
        if not self.spacy_processor:
            self.logger.warning("Spacy处理器未可用，降级到规则分割")
            return await self._rule_only_split(text)
        
        try:
            # 分析文本复杂度
            complexity = self.spacy_processor.analyze_text_complexity(text, self.nlp_language)
            
            if complexity['needs_splitting']:
                if len(text) > self.nlp_syntax_threshold:
                    # 使用句法分割
                    return self.spacy_processor.split_by_syntax(text, self.nlp_language)
                else:
                    # 使用句子分割
                    return self.spacy_processor.split_by_sentences(text, self.nlp_language)
            else:
                return [text]
                
        except Exception as e:
            self.logger.error(f"NLP分割失败: {e}")
            return await self._rule_only_split(text)
    
    async def _ai_only_split(self, text: str) -> List[str]:
        """仅使用AI分割"""
        if not self.ai_splitter:
            self.logger.warning("AI分割器未可用，降级到NLP分割")
            return await self._nlp_only_split(text)
        
        try:
            return await self.ai_splitter.split_text_semantically(text, self.max_weight)
        except Exception as e:
            self.logger.error(f"AI分割失败: {e}")
            return await self._nlp_only_split(text)
    
    async def _multi_level_split(self, text: str) -> List[str]:
        """
        多层次分割策略 (基于VideoLingo的四阶段分割思想)
        阶段1: 句子边界分割
        阶段2: 句法分析分割
        阶段3: AI语义分割
        阶段4: 质量验证与修正
        """
        try:
            current_text = text
            split_history = []
            
            # 阶段1: 句子边界分割
            if self.spacy_processor:
                stage1_result = self.spacy_processor.split_by_sentences(current_text, self.nlp_language)
                split_history.append(('sentence_split', stage1_result))
                self.logger.debug(f"阶段1-句子分割: {len(stage1_result)}个片段")
            else:
                stage1_result = [current_text]
                split_history.append(('no_nlp', stage1_result))
            
            # 阶段2: 检查是否需要进一步分割
            stage2_result = []
            for segment in stage1_result:
                if self._needs_further_splitting(segment):
                    if self.spacy_processor and len(segment) > self.nlp_syntax_threshold:
                        # 使用句法分割
                        syntax_splits = self.spacy_processor.split_by_syntax(segment, self.nlp_language)
                        stage2_result.extend(syntax_splits)
                    else:
                        stage2_result.append(segment)
                else:
                    stage2_result.append(segment)
            
            split_history.append(('syntax_split', stage2_result))
            self.logger.debug(f"阶段2-句法分割: {len(stage2_result)}个片段")
            
            # 阶段3: AI语义优化（可选）
            stage3_result = []
            if self.use_ai and self.ai_splitter:
                for segment in stage2_result:
                    if self._needs_ai_splitting(segment):
                        try:
                            ai_splits = await self.ai_splitter.split_text_semantically(segment, self.max_weight)
                            if ai_splits and len(ai_splits) > 1:
                                stage3_result.extend(ai_splits)
                            else:
                                stage3_result.append(segment)
                        except Exception as e:
                            self.logger.warning(f"AI分割失败，保持原片段: {e}")
                            stage3_result.append(segment)
                    else:
                        stage3_result.append(segment)
                split_history.append(('ai_split', stage3_result))
                self.logger.debug(f"阶段3-AI分割: {len(stage3_result)}个片段")
            else:
                stage3_result = stage2_result
            
            # 阶段4: 质量验证与修正
            final_result = await self._validate_and_correct_splits(stage3_result)
            split_history.append(('validation', final_result))
            self.logger.debug(f"阶段4-质量验证: {len(final_result)}个片段")
            
            # 记录分割历史
            self._log_split_history(text, split_history)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"多层次分割失败: {e}")
            return await self._rule_only_split(text)
    
    def _needs_further_splitting(self, text: str) -> bool:
        """判断是否需要进一步分割（包含Netflix权重标准）"""
        # Netflix权重检查（优先级最高）
        if self.netflix_calculator:
            text_weight = self.netflix_calculator.calculate_text_weight(text)
            if text_weight > self.netflix_calculator.config.max_line_length:
                return True
        
        # 检查文本长度
        if len(text) > self.max_weight:
            return True
        
        # 检查字符权重（如果有权重计算函数）
        if hasattr(self, 'rule_processor') and hasattr(self.rule_processor, 'validate_subtitle_line'):
            return not self.rule_processor.validate_subtitle_line(text)
        
        # 简单的长度检查
        return len(text) > 50
    
    def _needs_ai_splitting(self, text: str) -> bool:
        """判断是否需要AI分割"""
        # 文本长度超过阈值
        if len(text) > 35:
            return True
        
        # 检查是否有复杂结构
        if self.spacy_processor:
            try:
                complexity = self.spacy_processor.analyze_text_complexity(text, self.nlp_language)
                return complexity['complexity_score'] > self.nlp_complexity_threshold
            except:
                pass
        
        # 检查复杂句式标志
        complex_patterns = ['因为', '虽然', '不仅', '如果', '当', '由于']
        return any(pattern in text for pattern in complex_patterns)
    
    async def _validate_and_correct_splits(self, splits: List[str]) -> List[str]:
        """验证和修正分割结果"""
        corrected_splits = []
        
        for split in splits:
            # 检查是否符合长度要求
            if self._is_valid_split(split):
                corrected_splits.append(split)
            else:
                # 尝试进一步分割
                corrected = await self._try_correct_split(split)
                corrected_splits.extend(corrected)
        
        return corrected_splits
    
    def _is_valid_split(self, text: str) -> bool:
        """检查分割是否有效（包含Netflix标准验证）"""
        # 基本长度检查
        if len(text) <= 5:  # 太短
            return False
        
        # Netflix权重验证
        if self.netflix_calculator:
            text_weight = self.netflix_calculator.calculate_text_weight(text)
            if text_weight > self.netflix_calculator.config.max_line_length:
                return False
        
        # 传统长度检查（向后兼容）
        if len(text) > self.max_weight * 1.5:  # 太长
            return False
        
        # 如果有权重验证函数，使用它
        if hasattr(self, 'rule_processor') and hasattr(self.rule_processor, 'validate_subtitle_line'):
            return self.rule_processor.validate_subtitle_line(text)
        
        return True
    
    async def _try_correct_split(self, text: str) -> List[str]:
        """尝试修正无效的分割"""
        try:
            # 简单的中点分割
            mid = len(text) // 2
            
            # 寻找最近的分割点
            split_chars = ['，', ',', '。', '.', '；', ';', '！', '!', '？', '?']
            best_split = mid
            
            for i in range(max(0, mid - 10), min(len(text), mid + 10)):
                if text[i] in split_chars:
                    best_split = i + 1
                    break
            
            if best_split > 5 and best_split < len(text) - 5:
                return [text[:best_split].strip(), text[best_split:].strip()]
            else:
                return [text]  # 无法分割，返回原文
                
        except Exception as e:
            self.logger.error(f"修正分割失败: {e}")
            return [text]
    
    def _simple_punctuation_split(self, text: str) -> List[str]:
        """简单的标点符号分割"""
        import re
        
        # 基于主要标点符号分割
        splits = re.split(r'([。！？；\.\!\?;])', text)
        
        result = []
        current = ""
        
        for part in splits:
            if part.strip():
                current += part
                if part in ['。', '！', '？', '；', '.', '!', '?', ';']:
                    if current.strip():
                        result.append(current.strip())
                        current = ""
        
        if current.strip():
            result.append(current.strip())
        
        return result if result else [text]
    
    def _log_split_history(self, original_text: str, split_history: List[tuple]):
        """记录分割历史"""
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"分割历史 - 原文: {original_text}")
            for stage, result in split_history:
                self.logger.debug(f"  {stage}: {len(result)}个片段 - {result}")
    
    def get_enhanced_metrics(self, text: str, split_result: List[str]) -> Dict[str, Any]:
        """获取增强的分割度量（包含Netflix权重分析）"""
        # 获取基础度量
        basic_metrics = super().get_splitting_metrics(text, split_result)
        
        # 添加NLP分析
        enhanced_metrics = basic_metrics.copy()
        enhanced_metrics.update({
            'nlp_enabled': self.enable_nlp,
            'netflix_enabled': self.enable_netflix_standards,
            'splitting_strategy': self.splitting_strategy,
            'nlp_analysis': {},
            'complexity_analysis': {},
            'netflix_analysis': {}
        })
        
        # Netflix权重分析
        if self.netflix_calculator:
            try:
                # 原文Netflix分析
                original_analysis = self.netflix_calculator.get_detailed_analysis(text)
                enhanced_metrics['netflix_analysis']['original'] = original_analysis
                
                # 分割结果Netflix验证
                netflix_validation = self.netflix_calculator.validate_netflix_standards(split_result)
                enhanced_metrics['netflix_analysis']['validation'] = netflix_validation
                
                # 每行权重分析
                line_weights = []
                for line in split_result:
                    line_metrics = self.netflix_calculator.calculate_text_metrics(line)
                    line_weights.append(line_metrics)
                
                enhanced_metrics['netflix_analysis']['line_weights'] = line_weights
                
                # 总体权重统计
                total_original_weight = original_analysis['text_metrics']['total_weight']
                total_split_weight = sum(lw['total_weight'] for lw in line_weights)
                
                enhanced_metrics['netflix_analysis']['weight_summary'] = {
                    'original_weight': total_original_weight,
                    'split_total_weight': total_split_weight,
                    'weight_preservation': total_split_weight / total_original_weight if total_original_weight > 0 else 1.0,
                    'avg_line_weight': total_split_weight / len(split_result) if split_result else 0,
                    'max_line_weight': max((lw['total_weight'] for lw in line_weights), default=0),
                    'weight_balance': min((lw['total_weight'] for lw in line_weights), default=0) / max((lw['total_weight'] for lw in line_weights), default=1) if line_weights else 1.0
                }
                
                # 时长分析
                duration_analysis = self.netflix_calculator.calculate_subtitle_duration(split_result)
                enhanced_metrics['netflix_analysis']['duration'] = duration_analysis
                
            except Exception as e:
                self.logger.warning(f"Netflix分析失败: {e}")
        
        # 如果启用了NLP，添加复杂度分析
        if self.spacy_processor:
            try:
                # 原文复杂度分析
                original_complexity = self.spacy_processor.analyze_text_complexity(text, self.nlp_language)
                enhanced_metrics['complexity_analysis']['original'] = original_complexity
                
                # 分割结果复杂度分析
                split_complexities = []
                for split in split_result:
                    split_complexity = self.spacy_processor.analyze_text_complexity(split, self.nlp_language)
                    split_complexities.append(split_complexity)
                
                enhanced_metrics['complexity_analysis']['splits'] = split_complexities
                
                # 计算平均复杂度
                avg_complexity = sum(sc['complexity_score'] for sc in split_complexities) / len(split_complexities) if split_complexities else 0
                enhanced_metrics['complexity_analysis']['average_split_complexity'] = avg_complexity
                enhanced_metrics['complexity_analysis']['complexity_reduction'] = original_complexity['complexity_score'] - avg_complexity
                
            except Exception as e:
                self.logger.warning(f"复杂度分析失败: {e}")
        
        return enhanced_metrics
    
    async def batch_split(self, texts: List[str], strategy: Optional[str] = None) -> List[List[str]]:
        """批量分割文本"""
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = await self.split_subtitle_text(text, strategy)
                results.append(result)
                
                if i % 5 == 0:  # 每5个文本记录一次进度
                    self.logger.debug(f"批量分割进度: {i+1}/{len(texts)}")
                    
            except Exception as e:
                self.logger.error(f"批量分割第{i+1}个文本失败: {e}")
                results.append([text])
        
        return results
    
    def get_processor_info(self) -> Dict[str, Any]:
        """获取处理器信息"""
        info = {
            'class': 'EnhancedHybridSplitter',
            'nlp_enabled': self.enable_nlp,
            'ai_enabled': self.use_ai,
            'splitting_strategy': self.splitting_strategy,
            'max_weight': self.max_weight,
            'nlp_language': self.nlp_language,
            'config': self.config
        }
        
        if self.spacy_processor:
            info['spacy_info'] = self.spacy_processor.get_model_info()
        
        return info


# 便捷函数
async def enhanced_split_subtitle(text: str, config: Optional[Dict[str, Any]] = None, strategy: Optional[str] = None) -> List[str]:
    """
    增强版字幕分割便捷函数
    
    Args:
        text: 原始文本
        config: 配置参数
        strategy: 分割策略
        
    Returns:
        分割后的文本行列表
    """
    splitter = EnhancedHybridSplitter(config)
    return await splitter.split_subtitle_text(text, strategy)


def create_enhanced_splitter(config: Optional[Dict[str, Any]] = None) -> EnhancedHybridSplitter:
    """创建增强版分割器的便捷函数"""
    return EnhancedHybridSplitter(config)


# 预设配置
ENHANCED_SPLITTER_PRESETS = {
    'simple': {
        'splitting_strategy': 'rule_only',
        'enable_nlp_splitting': False,
        'enable_netflix_standards': False,
        'use_ai_splitting': False,
        'max_length': 50
    },
    'standard': {
        'splitting_strategy': 'multi_level',
        'enable_nlp_splitting': True,
        'enable_netflix_standards': False,
        'use_ai_splitting': False,
        'max_length': 75,
        'nlp_complexity_threshold': 0.5
    },
    'professional': {
        'splitting_strategy': 'multi_level',
        'enable_nlp_splitting': True,
        'enable_netflix_standards': True,
        'use_ai_splitting': True,
        'max_length': 42,  # Netflix标准
        'netflix_max_line_length': 42,
        'cjk_weight_multiplier': 1.75,
        'nlp_complexity_threshold': 0.3,
        'ai_fallback': True
    },
    'netflix': {
        'splitting_strategy': 'multi_level',
        'enable_nlp_splitting': True,
        'enable_netflix_standards': True,
        'use_ai_splitting': True,
        'max_length': 42,
        'netflix_max_line_length': 42,
        'cjk_weight_multiplier': 1.75,
        'nlp_complexity_threshold': 0.3,
        'ai_fallback': True
    },
    'ai_enhanced': {
        'splitting_strategy': 'ai_only',
        'enable_nlp_splitting': True,
        'enable_netflix_standards': True,
        'use_ai_splitting': True,
        'max_length': 42,
        'netflix_max_line_length': 42,
        'cjk_weight_multiplier': 1.75,
        'nlp_complexity_threshold': 0.4
    }
}


if __name__ == "__main__":
    # 测试增强版分割器
    import asyncio
    
    async def test_enhanced_splitter():
        # 测试配置
        test_config = ENHANCED_SPLITTER_PRESETS['standard'].copy()
        
        test_texts = [
            "这是一个简单的测试句子。",
            "人工智能技术正在快速发展，它不仅改变了我们的生活方式，还深刻影响着各个行业的发展，我们需要积极拥抱这种变化。",
            "虽然自动化技术带来了很多便利，但是我们也需要考虑其对就业市场的影响，因此需要制定相应的政策来应对这些挑战。",
            "PPT转视频是一个复杂的任务，涉及到文本处理、语音合成、视频生成等多个技术领域，每个环节都需要精心设计和优化。"
        ]
        
        print("=" * 60)
        print("增强版混合分割器测试")
        print("=" * 60)
        
        splitter = EnhancedHybridSplitter(test_config)
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n测试文本 {i}: {text}")
            
            try:
                result = await splitter.split_subtitle_text(text)
                print(f"分割结果 ({len(result)} 行):")
                for j, line in enumerate(result, 1):
                    print(f"  {j}. {line}")
                
                # 获取增强度量
                metrics = splitter.get_enhanced_metrics(text, result)
                print(f"分割策略: {metrics['splitting_strategy']}")
                print(f"权重分布: {metrics['weight_distribution']}")
                
                if 'complexity_analysis' in metrics and metrics['complexity_analysis']:
                    orig_score = metrics['complexity_analysis'].get('original', {}).get('complexity_score', 0)
                    reduction = metrics['complexity_analysis'].get('complexity_reduction', 0)
                    print(f"复杂度: {orig_score:.3f} -> 降低: {reduction:.3f}")
                
            except Exception as e:
                print(f"  错误: {e}")
        
        # 测试不同策略
        print(f"\n" + "=" * 60)
        print("测试不同分割策略")
        print("=" * 60)
        
        test_text = "当我们讨论人工智能在教育领域的应用时，需要考虑到它不仅能够提供个性化的学习体验，还能够帮助教师更好地了解学生的学习进度。"
        strategies = ['rule_only', 'nlp_only', 'multi_level']
        
        for strategy in strategies:
            print(f"\n策略: {strategy}")
            try:
                result = await splitter.split_subtitle_text(test_text, strategy)
                print(f"结果 ({len(result)} 行): {result}")
            except Exception as e:
                print(f"  错误: {e}")
        
        print(f"\n" + "=" * 60)
        print("处理器信息")
        print("=" * 60)
        
        info = splitter.get_processor_info()
        print(f"NLP启用: {info['nlp_enabled']}")
        print(f"AI启用: {info['ai_enabled']}")
        print(f"默认策略: {info['splitting_strategy']}")
        print(f"最大权重: {info['max_weight']}")
    
    # 运行测试
    asyncio.run(test_enhanced_splitter())