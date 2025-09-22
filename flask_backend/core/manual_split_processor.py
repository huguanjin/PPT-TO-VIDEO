"""
手动分割处理器 - 核心模块
实现换行分割的内容解析和处理逻辑
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentSegment:
    """内容片段数据结构"""
    index: int
    content: str
    estimated_duration: float
    start_position: int
    end_position: int
    quality_score: int
    warnings: List[str]
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

class NewlineSplitProcessor:
    """换行分割处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.quality_control = self.config.get('quality_control', {})
        self.advanced_options = self.config.get('advanced_options', {})
        
        # 质量控制参数
        self.min_segment_length = self.quality_control.get('min_segment_length', 5)
        self.max_segments_per_slide = self.quality_control.get('max_segments_per_slide', 8)
        self.min_segment_duration = self.quality_control.get('min_segment_duration', 1.0)
        self.max_segment_duration = self.quality_control.get('max_segment_duration', 10.0)
        
        # 高级选项
        self.preserve_empty_lines = self.advanced_options.get('preserve_empty_lines', False)
        self.trim_whitespace = self.advanced_options.get('trim_whitespace', True)
        self.filter_short_segments = self.advanced_options.get('filter_short_segments', True)
        
        logger.info("换行分割处理器初始化完成")
    
    def parse_content(self, content: str, slide_id: Optional[str] = None) -> List[ContentSegment]:
        """
        解析内容，按换行进行分割
        
        Args:
            content: 需要分割的内容
            slide_id: 幻灯片ID（可选）
        
        Returns:
            分割后的内容片段列表
        """
        if not content or not content.strip():
            logger.warning("内容为空，无法进行分割")
            return []
        
        logger.info(f"开始解析内容，长度: {len(content)} 字符")
        
        # 按换行分割
        lines = content.split('\n')
        segments = []
        
        for line_index, line in enumerate(lines):
            # 处理空行
            if not line.strip():
                if self.preserve_empty_lines:
                    # 保留空行作为分割标记
                    continue
                else:
                    # 跳过空行
                    continue
            
            # 处理空白字符
            processed_line = line.strip() if self.trim_whitespace else line
            
            # 过滤过短的片段
            if self.filter_short_segments and len(processed_line) < self.min_segment_length:
                logger.debug(f"过滤过短片段: {processed_line[:20]}...")
                continue
            
            # 计算位置信息
            start_pos = content.find(line)
            end_pos = start_pos + len(line)
            
            # 创建片段
            segment = ContentSegment(
                index=len(segments) + 1,
                content=processed_line,
                estimated_duration=self._estimate_duration(processed_line),
                start_position=start_pos,
                end_position=end_pos,
                quality_score=self._calculate_quality_score(processed_line),
                warnings=self._validate_segment(processed_line)
            )
            
            segments.append(segment)
        
        # 检查分割结果
        if len(segments) > self.max_segments_per_slide:
            logger.warning(f"分割片段数量过多: {len(segments)} > {self.max_segments_per_slide}")
        
        logger.info(f"分割完成，共生成 {len(segments)} 个片段")
        return segments
    
    def _estimate_duration(self, text: str) -> float:
        """
        估算文本的配音时长
        
        Args:
            text: 文本内容
        
        Returns:
            预估时长（秒）
        """
        if not text:
            return 0.0
        
        # 中文字符约2字符/秒，英文约4字符/秒
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        other_chars = len(text) - chinese_chars - english_chars
        
        # 计算预估时长
        duration = (chinese_chars * 0.5 + english_chars * 0.25 + other_chars * 0.3)
        
        # 应用最小和最大时长限制
        duration = max(self.min_segment_duration, duration)
        if duration > self.max_segment_duration:
            duration = self.max_segment_duration
        
        return round(duration, 2)
    
    def _calculate_quality_score(self, content: str) -> int:
        """
        计算内容片段的质量评分
        
        Args:
            content: 内容文本
        
        Returns:
            质量评分 (0-100)
        """
        score = 100
        
        # 长度检查
        if len(content) < 5:
            score -= 30
        elif len(content) > 200:
            score -= 20
        
        # 标点符号检查
        if not re.search(r'[。！？，；：]', content):
            score -= 15
        
        # 完整性检查
        if content.startswith(('，', '。', '！', '？')):
            score -= 20
        
        # 内容质量检查
        if content.strip() == '':
            score -= 50
        
        # 特殊字符过多
        special_char_ratio = len(re.findall(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', content)) / len(content)
        if special_char_ratio > 0.3:
            score -= 10
        
        return max(0, score)
    
    def _validate_segment(self, content: str) -> List[str]:
        """
        验证片段并生成警告信息
        
        Args:
            content: 内容文本
        
        Returns:
            警告信息列表
        """
        warnings = []
        
        if len(content) < self.min_segment_length:
            warnings.append(f"内容过短 (< {self.min_segment_length} 字符)")
        
        if len(content) > 200:
            warnings.append("内容过长，建议进一步分割")
        
        if not content.strip():
            warnings.append("内容为空")
        
        if content.startswith(('，', '。', '！', '？')):
            warnings.append("以标点符号开头，可能不完整")
        
        estimated_duration = self._estimate_duration(content)
        if estimated_duration < self.min_segment_duration:
            warnings.append(f"预估时长过短 (< {self.min_segment_duration}s)")
        
        if estimated_duration > self.max_segment_duration:
            warnings.append(f"预估时长过长 (> {self.max_segment_duration}s)")
        
        return warnings
    
    def create_split_result(self, slide_id: str, original_content: str, segments: List[ContentSegment]) -> Dict[str, Any]:
        """
        创建分割结果数据结构
        
        Args:
            slide_id: 幻灯片ID
            original_content: 原始内容
            segments: 分割后的片段
        
        Returns:
            分割结果字典
        """
        total_duration = sum(segment.estimated_duration for segment in segments)
        
        return {
            "slide_id": slide_id,
            "original_content": original_content,
            "split_method": "newline",
            "is_manual_split": True,
            "segments": [
                {
                    "index": segment.index,
                    "content": segment.content,
                    "estimated_duration": segment.estimated_duration,
                    "start_position": segment.start_position,
                    "end_position": segment.end_position,
                    "quality_score": segment.quality_score,
                    "warnings": segment.warnings,
                    "has_warnings": segment.has_warnings
                }
                for segment in segments
            ],
            "segment_count": len(segments),
            "total_estimated_duration": round(total_duration, 2),
            "average_segment_duration": round(total_duration / len(segments), 2) if segments else 0,
            "quality_summary": self._generate_quality_summary(segments),
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _generate_quality_summary(self, segments: List[ContentSegment]) -> Dict[str, Any]:
        """生成质量摘要"""
        if not segments:
            return {}
        
        scores = [segment.quality_score for segment in segments]
        warning_count = sum(1 for segment in segments if segment.has_warnings)
        
        return {
            "average_quality_score": round(sum(scores) / len(scores), 1),
            "min_quality_score": min(scores),
            "max_quality_score": max(scores),
            "segments_with_warnings": warning_count,
            "warning_rate": round(warning_count / len(segments) * 100, 1)
        }

class ManualSplitManager:
    """手动分割管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.processor = NewlineSplitProcessor(self.config)
        logger.info("手动分割管理器初始化完成")
    
    def process_slide_content(self, slide_id: str, content: str) -> Dict[str, Any]:
        """
        处理幻灯片内容的分割
        
        Args:
            slide_id: 幻灯片ID
            content: 幻灯片内容
        
        Returns:
            分割处理结果
        """
        logger.info(f"处理幻灯片 {slide_id} 的内容分割")
        
        try:
            segments = self.processor.parse_content(content, slide_id)
            result = self.processor.create_split_result(slide_id, content, segments)
            
            logger.info(f"幻灯片 {slide_id} 分割完成，生成 {len(segments)} 个片段")
            return result
            
        except Exception as e:
            logger.error(f"处理幻灯片 {slide_id} 分割时发生错误: {e}")
            return {
                "slide_id": slide_id,
                "original_content": content,
                "error": str(e),
                "success": False,
                "processing_timestamp": datetime.now().isoformat()
            }
    
    def validate_split_config(self) -> Tuple[bool, List[str]]:
        """验证分割配置的有效性"""
        errors = []
        
        # 检查质量控制参数
        if self.processor.min_segment_length <= 0:
            errors.append("最小片段长度必须大于0")
        
        if self.processor.max_segments_per_slide <= 0:
            errors.append("最大片段数必须大于0")
        
        if self.processor.min_segment_duration <= 0:
            errors.append("最小片段时长必须大于0")
        
        if self.processor.min_segment_duration >= self.processor.max_segment_duration:
            errors.append("最小片段时长不能大于等于最大片段时长")
        
        is_valid = len(errors) == 0
        return is_valid, errors

# 工厂函数
def create_manual_split_manager(config: Optional[Dict[str, Any]] = None) -> ManualSplitManager:
    """创建手动分割管理器实例"""
    return ManualSplitManager(config)

# 便捷函数
def split_content_by_newline(content: str, slide_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """便捷函数：按换行分割内容"""
    manager = create_manual_split_manager(config)
    return manager.process_slide_content(slide_id or "unknown", content)