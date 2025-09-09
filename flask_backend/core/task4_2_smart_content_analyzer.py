"""
任务4.2: 智能内容分析系统
智能内容分析引擎 - 基于AI的PPT内容结构分析和优化

功能特性:
1. PPT结构智能识别 - 自动分析幻灯片层次结构
2. 内容层次分析 - 识别标题、正文、重点内容
3. 关键信息提取 - 提取核心概念和关键词
4. 逻辑关系识别 - 分析内容间的逻辑联系
5. 自动布局优化 - 推荐最佳视觉布局
6. 智能配色系统 - 基于内容特征的配色建议

Author: Assistant
Date: 2025-09-09
Version: 1.0.0
"""

import asyncio
import json
import re
import math
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import colorsys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentType(Enum):
    """内容类型枚举"""
    TITLE = "title"
    SUBTITLE = "subtitle"
    BODY_TEXT = "body_text"
    BULLET_POINT = "bullet_point"
    CODE_BLOCK = "code_block"
    QUOTE = "quote"
    IMAGE_CAPTION = "image_caption"
    TABLE_DATA = "table_data"
    CHART_DATA = "chart_data"
    FOOTER = "footer"

class ImportanceLevel(Enum):
    """重要性等级"""
    CRITICAL = "critical"      # 关键内容
    HIGH = "high"             # 高重要性
    MEDIUM = "medium"         # 中等重要性
    LOW = "low"              # 低重要性
    MINIMAL = "minimal"       # 最低重要性

class LayoutType(Enum):
    """布局类型"""
    CENTERED = "centered"
    LEFT_ALIGNED = "left_aligned"
    RIGHT_ALIGNED = "right_aligned"
    GRID_LAYOUT = "grid_layout"
    HIERARCHICAL = "hierarchical"
    FLOW_LAYOUT = "flow_layout"

class ColorTheme(Enum):
    """色彩主题"""
    PROFESSIONAL = "professional"    # 商务专业
    CREATIVE = "creative"           # 创意活泼
    ACADEMIC = "academic"           # 学术严谨
    TECH = "tech"                  # 科技现代
    WARM = "warm"                  # 温暖亲和
    COOL = "cool"                  # 冷静理性

@dataclass
class ContentElement:
    """内容元素类"""
    text: str
    content_type: ContentType
    importance: ImportanceLevel
    position: Tuple[int, int]  # (slide_index, element_index)
    style_info: Dict[str, Any]
    keywords: List[str]
    semantic_weight: float
    
class LogicalRelation(Enum):
    """逻辑关系类型"""
    SEQUENCE = "sequence"         # 顺序关系
    HIERARCHY = "hierarchy"       # 层次关系
    COMPARISON = "comparison"     # 对比关系
    CAUSATION = "causation"      # 因果关系
    ELABORATION = "elaboration"  # 阐述关系
    SUMMARY = "summary"          # 总结关系

@dataclass
class ContentStructure:
    """内容结构分析结果"""
    slide_hierarchy: Dict[int, int]  # slide_index -> hierarchy_level
    logical_flow: List[LogicalRelation]
    key_concepts: List[str]
    content_density: Dict[int, float]  # slide_index -> density_score
    visual_balance: Dict[int, float]   # slide_index -> balance_score

@dataclass
class LayoutRecommendation:
    """布局推荐"""
    slide_index: int
    recommended_layout: LayoutType
    confidence: float
    reasoning: str
    adjustments: List[str]

@dataclass
class ColorRecommendation:
    """配色推荐"""
    theme: ColorTheme
    primary_color: str     # 主色调
    secondary_color: str   # 辅助色
    accent_color: str      # 强调色
    background_color: str  # 背景色
    text_color: str       # 文字色
    confidence: float
    reasoning: str

class SmartContentAnalyzer:
    """智能内容分析器"""
    
    def __init__(self):
        self.content_elements: List[ContentElement] = []
        self.analyzed_structure: Optional[ContentStructure] = None
        self.layout_recommendations: List[LayoutRecommendation] = []
        self.color_recommendations: List[ColorRecommendation] = []
        
        # 关键词权重词典
        self.keyword_weights = {
            'title_indicators': ['标题', '主题', '概述', '介绍', 'title', 'overview'],
            'importance_indicators': ['重要', '关键', '核心', '主要', 'important', 'key', 'main'],
            'structure_indicators': ['第一', '第二', '首先', '其次', '最后', 'first', 'second', 'finally'],
            'emphasis_indicators': ['注意', '强调', '突出', '重点', 'note', 'emphasis', 'highlight']
        }
        
        # 色彩心理学映射
        self.color_psychology = {
            'professional': {'h': 220, 's': 0.6, 'l': 0.4},  # 蓝色系
            'creative': {'h': 45, 's': 0.8, 'l': 0.5},       # 橙色系
            'academic': {'h': 0, 's': 0, 'l': 0.3},          # 灰色系
            'tech': {'h': 200, 's': 0.7, 'l': 0.3},          # 青色系
            'warm': {'h': 15, 's': 0.7, 'l': 0.6},           # 红橙色系
            'cool': {'h': 240, 's': 0.5, 'l': 0.5}           # 紫蓝色系
        }
    
    async def analyze_content_structure(self, ppt_data: Dict[str, Any]) -> ContentStructure:
        """分析PPT内容结构"""
        logger.info("开始分析PPT内容结构...")
        
        # 1. 解析内容元素
        await self._parse_content_elements(ppt_data)
        
        # 2. 分析幻灯片层次
        slide_hierarchy = await self._analyze_slide_hierarchy()
        
        # 3. 识别逻辑关系
        logical_flow = await self._identify_logical_relations()
        
        # 4. 提取关键概念
        key_concepts = await self._extract_key_concepts()
        
        # 5. 计算内容密度
        content_density = await self._calculate_content_density()
        
        # 6. 评估视觉平衡
        visual_balance = await self._assess_visual_balance()
        
        self.analyzed_structure = ContentStructure(
            slide_hierarchy=slide_hierarchy,
            logical_flow=logical_flow,
            key_concepts=key_concepts,
            content_density=content_density,
            visual_balance=visual_balance
        )
        
        logger.info(f"内容结构分析完成: {len(key_concepts)}个关键概念, {len(logical_flow)}个逻辑关系")
        return self.analyzed_structure
    
    async def _parse_content_elements(self, ppt_data: Dict[str, Any]):
        """解析内容元素"""
        self.content_elements.clear()
        
        slides = ppt_data.get('slides', [])
        for slide_idx, slide in enumerate(slides):
            elements = slide.get('elements', [])
            
            for elem_idx, element in enumerate(elements):
                text = element.get('text', '').strip()
                if not text:
                    continue
                
                # 识别内容类型
                content_type = self._identify_content_type(text, element)
                
                # 计算重要性等级
                importance = self._calculate_importance(text, content_type, slide_idx)
                
                # 提取关键词
                keywords = self._extract_keywords(text)
                
                # 计算语义权重
                semantic_weight = self._calculate_semantic_weight(text, keywords)
                
                content_element = ContentElement(
                    text=text,
                    content_type=content_type,
                    importance=importance,
                    position=(slide_idx, elem_idx),
                    style_info=element.get('style', {}),
                    keywords=keywords,
                    semantic_weight=semantic_weight
                )
                
                self.content_elements.append(content_element)
    
    def _identify_content_type(self, text: str, element: Dict[str, Any]) -> ContentType:
        """识别内容类型"""
        # 基于文本特征和元素属性识别类型
        text_lower = text.lower()
        
        # 检查样式信息
        style = element.get('style', {})
        font_size = style.get('fontSize', 12)
        
        # 标题判断（字体大小、位置、长度）
        if font_size > 20 or len(text) < 50:
            if any(indicator in text_lower for indicator in ['标题', '主题', 'title']):
                return ContentType.TITLE
            if font_size > 16:
                return ContentType.SUBTITLE
        
        # 列表项判断
        if re.match(r'^\s*[•\-\*\d+\.]\s', text):
            return ContentType.BULLET_POINT
        
        # 代码块判断
        if re.search(r'[{}();]', text) and len(text.split('\n')) > 1:
            return ContentType.CODE_BLOCK
        
        # 引用判断
        if text.startswith('"') or text.startswith('"'):
            return ContentType.QUOTE
        
        # 默认为正文
        return ContentType.BODY_TEXT
    
    def _calculate_importance(self, text: str, content_type: ContentType, slide_index: int) -> ImportanceLevel:
        """计算重要性等级"""
        score = 0.0
        
        # 基于内容类型的基础分数
        type_scores = {
            ContentType.TITLE: 1.0,
            ContentType.SUBTITLE: 0.8,
            ContentType.BULLET_POINT: 0.6,
            ContentType.BODY_TEXT: 0.4,
            ContentType.QUOTE: 0.7,
            ContentType.CODE_BLOCK: 0.5
        }
        score += type_scores.get(content_type, 0.4)
        
        # 基于关键词的重要性
        text_lower = text.lower()
        for indicators in self.keyword_weights.values():
            for indicator in indicators:
                if indicator in text_lower:
                    score += 0.2
        
        # 基于位置的重要性（前面的幻灯片更重要）
        position_weight = max(0.1, 1.0 - slide_index * 0.1)
        score *= position_weight
        
        # 转换为重要性等级
        if score >= 0.8:
            return ImportanceLevel.CRITICAL
        elif score >= 0.6:
            return ImportanceLevel.HIGH
        elif score >= 0.4:
            return ImportanceLevel.MEDIUM
        elif score >= 0.2:
            return ImportanceLevel.LOW
        else:
            return ImportanceLevel.MINIMAL
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（可以后续集成更高级的NLP库）
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # 过滤停用词
        stop_words = {'的', '了', '在', '是', '和', '有', '不', '为', '与', '个', '中', '上', '下',
                     'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # 计算词频并返回前5个
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:5]
    
    def _calculate_semantic_weight(self, text: str, keywords: List[str]) -> float:
        """计算语义权重"""
        # 基于文本长度、关键词密度等计算语义权重
        base_weight = len(text) / 1000.0  # 基础权重
        keyword_weight = len(keywords) * 0.1  # 关键词权重
        
        return min(1.0, base_weight + keyword_weight)
    
    async def _analyze_slide_hierarchy(self) -> Dict[int, int]:
        """分析幻灯片层次结构"""
        hierarchy = {}
        
        # 按幻灯片分组内容元素
        slides_content = {}
        for element in self.content_elements:
            slide_idx = element.position[0]
            if slide_idx not in slides_content:
                slides_content[slide_idx] = []
            slides_content[slide_idx].append(element)
        
        # 分析每个幻灯片的层次级别
        for slide_idx, elements in slides_content.items():
            level = 1  # 默认层次
            
            # 基于标题等级判断层次
            for element in elements:
                if element.content_type == ContentType.TITLE:
                    # 分析标题文本判断层次
                    title_text = element.text.lower()
                    if any(word in title_text for word in ['第一', '章', 'chapter', '1.']):
                        level = 1
                    elif any(word in title_text for word in ['第二', '节', 'section', '2.']):
                        level = 2
                    elif any(word in title_text for word in ['第三', '小节', 'subsection', '3.']):
                        level = 3
                    break
            
            hierarchy[slide_idx] = level
        
        return hierarchy
    
    async def _identify_logical_relations(self) -> List[LogicalRelation]:
        """识别逻辑关系"""
        relations = []
        
        # 基于内容分析识别逻辑关系
        prev_elements = []
        for element in self.content_elements:
            if prev_elements:
                # 分析与前一个元素的关系
                relation = self._analyze_element_relation(prev_elements[-1], element)
                if relation:
                    relations.append(relation)
            
            prev_elements.append(element)
            if len(prev_elements) > 3:  # 只保留最近的3个元素
                prev_elements.pop(0)
        
        return relations
    
    def _analyze_element_relation(self, prev_element: ContentElement, curr_element: ContentElement) -> Optional[LogicalRelation]:
        """分析两个元素间的逻辑关系"""
        prev_text = prev_element.text.lower()
        curr_text = curr_element.text.lower()
        
        # 顺序关系
        if any(word in curr_text for word in ['接下来', '然后', '其次', 'next', 'then']):
            return LogicalRelation.SEQUENCE
        
        # 层次关系
        if curr_element.importance.value != prev_element.importance.value:
            return LogicalRelation.HIERARCHY
        
        # 对比关系
        if any(word in curr_text for word in ['相比', '对比', '然而', 'however', 'compared']):
            return LogicalRelation.COMPARISON
        
        # 因果关系
        if any(word in curr_text for word in ['因此', '所以', '导致', 'therefore', 'because']):
            return LogicalRelation.CAUSATION
        
        # 总结关系
        if any(word in curr_text for word in ['总结', '总之', '综上', 'summary', 'conclusion']):
            return LogicalRelation.SUMMARY
        
        return None
    
    async def _extract_key_concepts(self) -> List[str]:
        """提取关键概念"""
        all_keywords = []
        for element in self.content_elements:
            # 重要性高的元素权重更大
            weight = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0.5, 'minimal': 0.2}
            element_weight = weight.get(element.importance.value, 1)
            
            for keyword in element.keywords:
                all_keywords.extend([keyword] * int(element_weight))
        
        # 统计词频并返回前10个关键概念
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        return sorted(keyword_freq.keys(), key=lambda x: keyword_freq[x], reverse=True)[:10]
    
    async def _calculate_content_density(self) -> Dict[int, float]:
        """计算内容密度"""
        density_scores = {}
        
        # 按幻灯片计算内容密度
        slides_content = {}
        for element in self.content_elements:
            slide_idx = element.position[0]
            if slide_idx not in slides_content:
                slides_content[slide_idx] = []
            slides_content[slide_idx].append(element)
        
        for slide_idx, elements in slides_content.items():
            total_text_length = sum(len(elem.text) for elem in elements)
            element_count = len(elements)
            
            # 密度 = 文本总长度 * 元素数量 / 1000 (归一化)
            density = (total_text_length * element_count) / 1000.0
            density_scores[slide_idx] = min(1.0, density)
        
        return density_scores
    
    async def _assess_visual_balance(self) -> Dict[int, float]:
        """评估视觉平衡"""
        balance_scores = {}
        
        # 按幻灯片评估视觉平衡
        slides_content = {}
        for element in self.content_elements:
            slide_idx = element.position[0]
            if slide_idx not in slides_content:
                slides_content[slide_idx] = []
            slides_content[slide_idx].append(element)
        
        for slide_idx, elements in slides_content.items():
            # 简化的视觉平衡评估
            if not elements:
                balance_scores[slide_idx] = 0.5
                continue
            
            # 基于内容类型的分布评估平衡
            type_distribution = {}
            for element in elements:
                type_name = element.content_type.value
                type_distribution[type_name] = type_distribution.get(type_name, 0) + 1
            
            # 平衡度 = 1 - 标准差/平均值（归一化）
            if len(type_distribution) > 1:
                values = list(type_distribution.values())
                mean_val = sum(values) / len(values)
                variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                std_dev = math.sqrt(variance)
                balance = max(0.0, 1.0 - (std_dev / mean_val if mean_val > 0 else 1.0))
            else:
                balance = 0.7  # 单一类型的平衡度
            
            balance_scores[slide_idx] = balance
        
        return balance_scores
    
    async def generate_layout_recommendations(self) -> List[LayoutRecommendation]:
        """生成布局推荐"""
        if not self.analyzed_structure:
            raise ValueError("请先执行内容结构分析")
        
        self.layout_recommendations.clear()
        
        # 按幻灯片生成布局建议
        for slide_idx, density in self.analyzed_structure.content_density.items():
            balance = self.analyzed_structure.visual_balance.get(slide_idx, 0.5)
            
            # 根据密度和平衡度推荐布局
            layout, confidence, reasoning, adjustments = self._recommend_layout(density, balance)
            
            recommendation = LayoutRecommendation(
                slide_index=slide_idx,
                recommended_layout=layout,
                confidence=confidence,
                reasoning=reasoning,
                adjustments=adjustments
            )
            
            self.layout_recommendations.append(recommendation)
        
        logger.info(f"生成了{len(self.layout_recommendations)}个布局推荐")
        return self.layout_recommendations
    
    def _recommend_layout(self, density: float, balance: float) -> Tuple[LayoutType, float, str, List[str]]:
        """推荐具体布局"""
        adjustments = []
        
        # 高密度内容推荐网格布局
        if density > 0.7:
            if balance > 0.6:
                return (LayoutType.GRID_LAYOUT, 0.8, 
                       "内容密度高且分布均匀，适合网格布局", 
                       ["减少单行文字长度", "增加段落间距"])
            else:
                return (LayoutType.HIERARCHICAL, 0.7,
                       "内容密度高但分布不均，建议层次化布局",
                       ["重新组织内容层次", "突出重点内容"])
        
        # 中等密度推荐居中或流式布局
        elif density > 0.4:
            if balance > 0.5:
                return (LayoutType.CENTERED, 0.9,
                       "内容适中且平衡，居中布局效果最佳",
                       ["保持当前结构", "微调间距"])
            else:
                return (LayoutType.FLOW_LAYOUT, 0.7,
                       "内容适中但需要改善平衡性，流式布局更灵活",
                       ["调整元素位置", "优化视觉流"])
        
        # 低密度推荐左对齐
        else:
            return (LayoutType.LEFT_ALIGNED, 0.8,
                   "内容较少，左对齐布局清晰简洁",
                   ["增加视觉元素", "适当增加内容"])
    
    async def generate_color_recommendations(self) -> List[ColorRecommendation]:
        """生成配色推荐"""
        if not self.analyzed_structure:
            raise ValueError("请先执行内容结构分析")
        
        self.color_recommendations.clear()
        
        # 分析内容特征决定主题
        theme = self._analyze_content_theme()
        
        # 生成配色方案
        color_scheme = self._generate_color_scheme(theme)
        
        recommendation = ColorRecommendation(
            theme=theme,
            primary_color=color_scheme['primary'],
            secondary_color=color_scheme['secondary'],
            accent_color=color_scheme['accent'],
            background_color=color_scheme['background'],
            text_color=color_scheme['text'],
            confidence=0.8,
            reasoning=f"基于内容分析，推荐{theme.value}主题配色"
        )
        
        self.color_recommendations.append(recommendation)
        
        logger.info(f"生成配色推荐: {theme.value}主题")
        return self.color_recommendations
    
    def _analyze_content_theme(self) -> ColorTheme:
        """分析内容主题"""
        # 基于关键词分析判断主题
        tech_keywords = ['技术', '系统', '算法', '数据', 'tech', 'system', 'algorithm']
        business_keywords = ['商务', '管理', '策略', '市场', 'business', 'management', 'strategy']
        creative_keywords = ['创意', '设计', '艺术', '创新', 'creative', 'design', 'art', 'innovation']
        academic_keywords = ['研究', '学术', '理论', '分析', 'research', 'academic', 'theory', 'analysis']
        
        tech_score = self._calculate_theme_score(tech_keywords)
        business_score = self._calculate_theme_score(business_keywords)
        creative_score = self._calculate_theme_score(creative_keywords)
        academic_score = self._calculate_theme_score(academic_keywords)
        
        scores = {
            ColorTheme.TECH: tech_score,
            ColorTheme.PROFESSIONAL: business_score,
            ColorTheme.CREATIVE: creative_score,
            ColorTheme.ACADEMIC: academic_score
        }
        
        return max(scores.keys(), key=lambda x: scores[x])
    
    def _calculate_theme_score(self, theme_keywords: List[str]) -> float:
        """计算主题匹配分数"""
        score = 0.0
        for element in self.content_elements:
            element_text = element.text.lower()
            for keyword in theme_keywords:
                if keyword in element_text:
                    # 重要性越高权重越大
                    weight = {'critical': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.4, 'minimal': 0.2}
                    score += weight.get(element.importance.value, 0.6)
        
        return score
    
    def _generate_color_scheme(self, theme: ColorTheme) -> Dict[str, str]:
        """生成配色方案"""
        base_hsl = self.color_psychology.get(theme.value, {'h': 220, 's': 0.6, 'l': 0.4})
        
        # 生成完整配色方案
        schemes = {
            'primary': self._hsl_to_hex(base_hsl['h'], base_hsl['s'], base_hsl['l']),
            'secondary': self._hsl_to_hex((base_hsl['h'] + 30) % 360, base_hsl['s'] * 0.7, base_hsl['l'] + 0.2),
            'accent': self._hsl_to_hex((base_hsl['h'] + 180) % 360, base_hsl['s'] * 0.8, base_hsl['l'] + 0.1),
            'background': self._hsl_to_hex(base_hsl['h'], base_hsl['s'] * 0.1, 0.95),
            'text': self._hsl_to_hex(base_hsl['h'], base_hsl['s'] * 0.2, 0.2)
        }
        
        return schemes
    
    def _hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """HSL转换为十六进制颜色"""
        # 确保值在有效范围内
        h = max(0, min(360, h)) / 360.0
        s = max(0, min(1, s))
        l = max(0, min(1, l))
        
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        if not self.analyzed_structure:
            return {"error": "未执行内容分析"}
        
        return {
            "content_elements_count": len(self.content_elements),
            "key_concepts": self.analyzed_structure.key_concepts,
            "logical_relations_count": len(self.analyzed_structure.logical_flow),
            "slide_hierarchy": self.analyzed_structure.slide_hierarchy,
            "average_content_density": sum(self.analyzed_structure.content_density.values()) / len(self.analyzed_structure.content_density) if self.analyzed_structure.content_density else 0,
            "average_visual_balance": sum(self.analyzed_structure.visual_balance.values()) / len(self.analyzed_structure.visual_balance) if self.analyzed_structure.visual_balance else 0,
            "layout_recommendations_count": len(self.layout_recommendations),
            "color_recommendations_count": len(self.color_recommendations)
        }

# 示例使用函数
async def demo_smart_content_analyzer():
    """演示智能内容分析器"""
    print("🧠 任务4.2: 智能内容分析系统演示")
    print("=" * 60)
    
    # 创建分析器实例
    analyzer = SmartContentAnalyzer()
    
    # 模拟PPT数据
    sample_ppt_data = {
        "slides": [
            {
                "elements": [
                    {"text": "人工智能技术发展趋势", "style": {"fontSize": 24}},
                    {"text": "本演示将介绍AI技术的最新发展和未来趋势", "style": {"fontSize": 14}},
                ]
            },
            {
                "elements": [
                    {"text": "机器学习算法演进", "style": {"fontSize": 20}},
                    {"text": "• 深度学习的突破\n• 强化学习的应用\n• 联邦学习的兴起", "style": {"fontSize": 12}},
                ]
            },
            {
                "elements": [
                    {"text": "技术挑战与解决方案", "style": {"fontSize": 20}},
                    {"text": "随着AI技术的发展，我们面临数据隐私、算法偏见等挑战。因此需要制定相应的解决方案。", "style": {"fontSize": 12}},
                ]
            }
        ]
    }
    
    try:
        # 1. 内容结构分析
        print("1. 执行内容结构分析...")
        structure = await analyzer.analyze_content_structure(sample_ppt_data)
        print(f"   ✅ 分析完成: {len(structure.key_concepts)}个关键概念")
        
        # 2. 布局推荐
        print("\n2. 生成布局推荐...")
        layout_recs = await analyzer.generate_layout_recommendations()
        print(f"   ✅ 生成{len(layout_recs)}个布局推荐")
        
        # 3. 配色推荐
        print("\n3. 生成配色推荐...")
        color_recs = await analyzer.generate_color_recommendations()
        print(f"   ✅ 生成{len(color_recs)}个配色推荐")
        
        # 4. 显示分析结果
        print(f"\n📊 分析摘要:")
        summary = analyzer.get_analysis_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        # 5. 详细结果展示
        print(f"\n🔍 详细分析结果:")
        print(f"关键概念: {', '.join(structure.key_concepts[:5])}")
        
        if layout_recs:
            layout = layout_recs[0]
            print(f"推荐布局: {layout.recommended_layout.value} (置信度: {layout.confidence:.2f})")
        
        if color_recs:
            colors = color_recs[0]
            print(f"推荐主题: {colors.theme.value}")
            print(f"主色调: {colors.primary_color}")
        
        print("\n🎉 智能内容分析演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_smart_content_analyzer())
