"""
HTML备注处理器 - 替代手动分割处理器
直接从ppt_data.json的remark字段解析HTML内容
"""
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# 添加项目路径到sys.path
current_dir = Path(__file__).parent
project_dir = current_dir.parent
sys.path.insert(0, str(project_dir))

from utils.remark_parser import RemarkParser, RemarkAnalysis, RemarkSegment


@dataclass
class ProcessedSegment:
    """处理后的段落数据"""
    index: int
    content: str
    char_count: int
    estimated_duration: float
    is_over_limit: bool
    warnings: List[str]


class HtmlRemarkProcessor:
    """HTML备注处理器"""
    
    def __init__(self, char_limit: int = 20, words_per_second: float = 3.5):
        self.char_limit = char_limit
        self.words_per_second = words_per_second
        self.logger = logging.getLogger(__name__)
    
    def process_remark_html(self, html_content: str, slide_id: Optional[str] = None) -> Dict[str, Any]:
        """
        处理HTML格式的备注内容
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            slide_id: 幻灯片ID（用于日志）
            
        Returns:
            处理结果字典
        """
        if not html_content or not html_content.strip():
            return {
                "success": False,
                "error": "备注内容为空",
                "segments": [],
                "segment_count": 0
            }
        
        try:
            # 使用备注解析器分析内容
            analysis = RemarkParser.analyze_remark(html_content, self.char_limit)
            
            if not analysis.segments:
                return {
                    "success": False,
                    "error": "解析后没有有效段落",
                    "segments": [],
                    "segment_count": 0
                }
            
            # 转换为处理后的段落格式
            processed_segments = []
            for segment in analysis.segments:
                warnings = []
                if segment.is_over_limit:
                    warnings.append(f"超出字符限制({self.char_limit}字符)")
                
                processed_segment = ProcessedSegment(
                    index=segment.index,
                    content=segment.content,
                    char_count=segment.char_count,
                    estimated_duration=self._estimate_duration(segment.content),
                    is_over_limit=segment.is_over_limit,
                    warnings=warnings
                )
                processed_segments.append(processed_segment)
            
            # 构建返回结果
            result = {
                "success": True,
                "segments": [
                    {
                        "index": s.index,
                        "content": s.content,
                        "char_count": s.char_count,
                        "estimated_duration": s.estimated_duration,
                        "is_over_limit": s.is_over_limit,
                        "warnings": s.warnings
                    }
                    for s in processed_segments
                ],
                "segment_count": len(processed_segments),
                "total_chars": analysis.total_chars,
                "over_limit_count": analysis.over_limit_count,
                "script_content": analysis.script_content,
                "analysis": {
                    "has_manual_splits": analysis.paragraph_count > 1,
                    "char_limit": self.char_limit,
                    "average_chars": analysis.total_chars / analysis.paragraph_count if analysis.paragraph_count > 0 else 0
                }
            }
            
            # 记录处理结果
            if slide_id:
                self.logger.info(f"幻灯片 {slide_id}: 解析出 {len(processed_segments)} 个段落，总字符数 {analysis.total_chars}")
                if analysis.over_limit_count > 0:
                    self.logger.warning(f"幻灯片 {slide_id}: 有 {analysis.over_limit_count} 个段落超出字符限制")
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理HTML备注失败: {e}")
            return {
                "success": False,
                "error": f"解析HTML备注时出错: {str(e)}",
                "segments": [],
                "segment_count": 0
            }
    
    def _estimate_duration(self, text: str) -> float:
        """
        估算文本的朗读时长
        
        Args:
            text: 文本内容
            
        Returns:
            估算的朗读时长（秒）
        """
        if not text:
            return 0.0
        
        # 基于字符数和语速估算
        char_count = len(text)
        # 中文大约每秒3.5个字符，英文每秒7个字符，这里取中间值
        estimated_duration = char_count / self.words_per_second
        
        # 设置最小和最大时长限制
        min_duration = 0.5  # 最短0.5秒
        max_duration = 10.0  # 最长10秒
        
        return max(min_duration, min(estimated_duration, max_duration))
    
    def extract_script_for_tts(self, html_content: str) -> str:
        """
        提取用于TTS的纯文本脚本
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            
        Returns:
            用于TTS的纯文本内容
        """
        return RemarkParser.extract_script_content(html_content)
    
    def is_manually_split(self, html_content: str) -> bool:
        """
        检查备注是否包含手动分割
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            
        Returns:
            是否包含手动分割
        """
        return RemarkParser.is_manually_split(html_content)
    
    def get_segment_texts(self, html_content: str) -> List[str]:
        """
        获取段落文本列表（用于配音）
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            
        Returns:
            段落文本列表
        """
        return RemarkParser.parse_html(html_content)


# 便捷函数，保持向后兼容
def process_html_remark(html_content: str, char_limit: int = 20) -> Dict[str, Any]:
    """便捷函数：处理HTML备注"""
    processor = HtmlRemarkProcessor(char_limit=char_limit)
    return processor.process_remark_html(html_content)


def extract_tts_script(html_content: str) -> str:
    """便捷函数：提取TTS脚本"""
    processor = HtmlRemarkProcessor()
    return processor.extract_script_for_tts(html_content)


if __name__ == "__main__":
    # 测试代码
    test_html = '<p style="">are you ok，</p><p style="">我的朋友们，</p><p style="">今天来教大家安装cherry studio</p><p style="">你哈啊</p><p style=""><br class="ProseMirror-trailingBreak"></p>'
    
    processor = HtmlRemarkProcessor(char_limit=20)
    result = processor.process_remark_html(test_html, "test_slide")
    
    print("=== HTML备注处理结果 ===")
    print(f"成功: {result['success']}")
    print(f"段落数: {result.get('segment_count', 0)}")
    print(f"总字符数: {result.get('total_chars', 0)}")
    print(f"超限段落数: {result.get('over_limit_count', 0)}")
    
    if result['success']:
        print(f"\nTTS脚本:")
        print(f"'{result.get('script_content', '')}'")
        
        print(f"\n段落详情:")
        for segment in result.get('segments', []):
            status = "❌" if segment['is_over_limit'] else "✅"
            print(f"{segment['index'] + 1}. {status} '{segment['content']}' ({segment['char_count']}字符)")