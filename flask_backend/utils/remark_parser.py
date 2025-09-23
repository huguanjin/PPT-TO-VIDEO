"""
备注HTML解析工具
解析PPTist编辑器生成的HTML格式备注，提取分段文本
"""
import re
import html
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class RemarkSegment:
    """备注段落数据结构"""
    index: int
    content: str
    char_count: int
    is_over_limit: bool
    
    @classmethod
    def from_text(cls, index: int, text: str, char_limit: int = 20):
        """从文本创建段落对象"""
        return cls(
            index=index,
            content=text,
            char_count=len(text),
            is_over_limit=len(text) > char_limit
        )


@dataclass
class RemarkAnalysis:
    """备注分析结果"""
    segments: List[RemarkSegment]
    total_chars: int
    paragraph_count: int
    over_limit_count: int
    char_limit: int
    script_content: str  # 用于配音的纯文本内容


class RemarkParser:
    """备注HTML解析器"""
    
    @staticmethod
    def parse_html(html_content: str) -> List[str]:
        """
        解析remark HTML，提取段落文本
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            
        Returns:
            段落文本列表
        """
        if not html_content:
            return []
        
        # 提取所有<p>标签内的文本
        pattern = r'<p[^>]*>(.*?)</p>'
        matches = re.findall(pattern, html_content, re.DOTALL)
        
        paragraphs = []
        for match in matches:
            # 清理HTML标签
            text = re.sub(r'<[^>]+>', '', match)
            # 解码HTML实体
            text = html.unescape(text)
            # 清理空白字符
            text = text.strip()
            
            if text:  # 过滤空段落
                paragraphs.append(text)
        
        return paragraphs
    
    @staticmethod
    def analyze_remark(html_content: str, char_limit: int = 20) -> RemarkAnalysis:
        """
        分析备注内容，生成完整的分析结果
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            char_limit: 字符数限制
            
        Returns:
            备注分析结果
        """
        paragraphs = RemarkParser.parse_html(html_content)
        
        # 创建段落对象
        segments = [
            RemarkSegment.from_text(i, text, char_limit) 
            for i, text in enumerate(paragraphs)
        ]
        
        # 统计信息
        total_chars = sum(len(p) for p in paragraphs)
        over_limit_count = sum(1 for s in segments if s.is_over_limit)
        
        # 生成配音脚本内容
        script_content = '\n'.join(paragraphs)
        
        return RemarkAnalysis(
            segments=segments,
            total_chars=total_chars,
            paragraph_count=len(paragraphs),
            over_limit_count=over_limit_count,
            char_limit=char_limit,
            script_content=script_content
        )
    
    @staticmethod
    def extract_script_content(html_content: str) -> str:
        """
        快速提取用于配音的纯文本内容
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            
        Returns:
            用于配音的纯文本内容（段落用换行符分隔）
        """
        paragraphs = RemarkParser.parse_html(html_content)
        return '\n'.join(paragraphs)
    
    @staticmethod
    def is_manually_split(html_content: str) -> bool:
        """
        检查备注是否包含手动分割（多个段落）
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            
        Returns:
            是否包含手动分割
        """
        paragraphs = RemarkParser.parse_html(html_content)
        return len(paragraphs) > 1
    
    @staticmethod
    def get_segment_stats(html_content: str, char_limit: int = 20) -> Dict[str, Any]:
        """
        获取段落统计信息的字典格式
        
        Args:
            html_content: PPTist编辑器生成的HTML内容
            char_limit: 字符数限制
            
        Returns:
            统计信息字典
        """
        analysis = RemarkParser.analyze_remark(html_content, char_limit)
        
        return {
            'paragraph_count': analysis.paragraph_count,
            'total_chars': analysis.total_chars,
            'over_limit_count': analysis.over_limit_count,
            'char_limit': analysis.char_limit,
            'has_manual_splits': analysis.paragraph_count > 1,
            'segments': [
                {
                    'index': s.index,
                    'content': s.content,
                    'char_count': s.char_count,
                    'is_over_limit': s.is_over_limit
                }
                for s in analysis.segments
            ]
        }


# 便捷函数
def parse_remark_to_script(html_content: str) -> str:
    """便捷函数：将HTML备注转换为配音脚本"""
    return RemarkParser.extract_script_content(html_content)


def analyze_remark_segments(html_content: str, char_limit: int = 20) -> Dict[str, Any]:
    """便捷函数：分析备注段落"""
    return RemarkParser.get_segment_stats(html_content, char_limit)


if __name__ == "__main__":
    # 测试代码
    test_html = '<p style="">are you ok，</p><p style="">我的朋友们，</p><p style="">今天来教大家安装cherry studio</p><p style="">你哈啊</p><p style=""><br class="ProseMirror-trailingBreak"></p>'
    
    print("测试HTML解析:")
    print(f"原始HTML: {test_html}")
    
    analysis = RemarkParser.analyze_remark(test_html, char_limit=20)
    print(f"\n解析结果:")
    print(f"段落数: {analysis.paragraph_count}")
    print(f"总字符数: {analysis.total_chars}")
    print(f"超限段落数: {analysis.over_limit_count}")
    print(f"配音脚本:\n{analysis.script_content}")
    
    print(f"\n段落详情:")
    for segment in analysis.segments:
        status = "❌" if segment.is_over_limit else "✅"
        print(f"{segment.index + 1}. {status} '{segment.content}' ({segment.char_count}字符)")