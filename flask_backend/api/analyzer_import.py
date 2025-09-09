"""
智能内容分析器导入模块
解决不同运行环境下的模块导入问题

Author: Assistant
Date: 2025-09-09
Version: 1.0.0
"""

import sys
import os
from pathlib import Path

def get_analyzer_module():
    """
    智能获取内容分析器模块
    支持多种运行环境和路径配置
    """
    # 获取当前文件的绝对路径
    current_file = Path(__file__).resolve()
    
    # 可能的模块路径
    search_paths = [
        # 标准项目结构：api/../core/
        current_file.parent.parent / 'core',
        # 同级目录
        current_file.parent / 'core',
        # 项目根目录下的flask_backend/core
        current_file.parent.parent.parent / 'flask_backend' / 'core',
        # 当前目录
        current_file.parent,
    ]
    
    # 目标文件名
    target_module = 'task4_2_smart_content_analyzer.py'
    
    for search_path in search_paths:
        if search_path.exists():
            module_file = search_path / target_module
            if module_file.exists():
                # 添加到Python路径
                str_path = str(search_path)
                if str_path not in sys.path:
                    sys.path.insert(0, str_path)
                
                try:
                    # 动态导入模块
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        "task4_2_smart_content_analyzer", 
                        str(module_file)
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        return module, True
                except Exception as e:
                    print(f"动态导入失败: {e}")
                    continue
    
    # 如果都失败了，返回模拟模块
    return create_mock_module(), False

def create_mock_module():
    """创建模拟模块，确保API可以运行"""
    
    class MockModule:
        """模拟的智能内容分析器模块"""
        
        class SmartContentAnalyzer:
            def __init__(self):
                self.content_elements = []
                self.analyzed_structure = None
                self.layout_recommendations = []
                self.color_recommendations = []
            
            async def analyze_content_structure(self, ppt_data):
                """模拟内容结构分析"""
                return self.MockContentStructure()
            
            async def generate_layout_recommendations(self):
                """模拟布局推荐生成"""
                return [
                    self.MockLayoutRecommendation(0, "centered", 0.8, "模拟推荐", [])
                ]
            
            async def generate_color_recommendations(self):
                """模拟配色推荐生成"""
                return [
                    self.MockColorRecommendation("professional", "#3498db", "#2980b9", "#e74c3c", "#ffffff", "#2c3e50", 0.8, "模拟配色")
                ]
            
            def get_analysis_summary(self):
                """模拟分析摘要"""
                return {
                    "content_elements_count": 0,
                    "key_concepts": [],
                    "logical_relations_count": 0,
                    "warning": "使用模拟数据 - 智能分析模块未正确加载"
                }
            
            class MockContentStructure:
                def __init__(self):
                    self.slide_hierarchy = {0: 1}
                    self.logical_flow = []
                    self.key_concepts = ["模拟概念"]
                    self.content_density = {0: 0.5}
                    self.visual_balance = {0: 0.7}
            
            class MockLayoutRecommendation:
                def __init__(self, slide_index, layout, confidence, reasoning, adjustments):
                    self.slide_index = slide_index
                    self.recommended_layout = MockModule.LayoutType()
                    self.recommended_layout.value = layout
                    self.confidence = confidence
                    self.reasoning = reasoning
                    self.adjustments = adjustments
            
            class MockColorRecommendation:
                def __init__(self, theme, primary, secondary, accent, bg, text, confidence, reasoning):
                    self.theme = MockModule.ColorTheme()
                    self.theme.value = theme
                    self.primary_color = primary
                    self.secondary_color = secondary
                    self.accent_color = accent
                    self.background_color = bg
                    self.text_color = text
                    self.confidence = confidence
                    self.reasoning = reasoning
        
        class ContentType:
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
        
        class ImportanceLevel:
            CRITICAL = "critical"
            HIGH = "high"
            MEDIUM = "medium"
            LOW = "low"
            MINIMAL = "minimal"
        
        class LayoutType:
            CENTERED = "centered"
            LEFT_ALIGNED = "left_aligned"
            RIGHT_ALIGNED = "right_aligned"
            GRID_LAYOUT = "grid_layout"
            HIERARCHICAL = "hierarchical"
            FLOW_LAYOUT = "flow_layout"
            
            def __init__(self):
                self.value = "centered"
        
        class ColorTheme:
            PROFESSIONAL = "professional"
            CREATIVE = "creative"
            ACADEMIC = "academic"
            TECH = "tech"
            WARM = "warm"
            COOL = "cool"
            
            def __init__(self):
                self.value = "professional"
        
        class LogicalRelation:
            SEQUENCE = "sequence"
            HIERARCHY = "hierarchy"
            COMPARISON = "comparison"
            CAUSATION = "causation"
            ELABORATION = "elaboration"
            SUMMARY = "summary"
    
    return MockModule()

# 全局模块实例
_analyzer_module = None
_import_success = False

def get_smart_content_analyzer():
    """获取智能内容分析器类"""
    global _analyzer_module, _import_success
    
    if _analyzer_module is None:
        _analyzer_module, _import_success = get_analyzer_module()
        
        if not _import_success:
            print("⚠️  警告: 智能内容分析器模块未找到，使用模拟模式")
            print("   请确保 task4_2_smart_content_analyzer.py 文件存在于正确位置")
    
    return _analyzer_module.SmartContentAnalyzer

def get_content_types():
    """获取内容类型枚举"""
    global _analyzer_module
    if _analyzer_module is None:
        get_smart_content_analyzer()
    return _analyzer_module.ContentType

def get_importance_levels():
    """获取重要性级别枚举"""
    global _analyzer_module
    if _analyzer_module is None:
        get_smart_content_analyzer()
    return _analyzer_module.ImportanceLevel

def get_layout_types():
    """获取布局类型枚举"""
    global _analyzer_module
    if _analyzer_module is None:
        get_smart_content_analyzer()
    return _analyzer_module.LayoutType

def get_color_themes():
    """获取配色主题枚举"""
    global _analyzer_module
    if _analyzer_module is None:
        get_smart_content_analyzer()
    return _analyzer_module.ColorTheme

def get_logical_relations():
    """获取逻辑关系枚举"""
    global _analyzer_module
    if _analyzer_module is None:
        get_smart_content_analyzer()
    return _analyzer_module.LogicalRelation

def is_import_successful():
    """检查导入是否成功"""
    global _import_success
    return _import_success

if __name__ == "__main__":
    # 测试导入功能
    print("🧪 测试智能内容分析器导入...")
    
    analyzer_class = get_smart_content_analyzer()
    print(f"✅ 分析器类: {analyzer_class}")
    
    content_types = get_content_types()
    print(f"✅ 内容类型: {content_types}")
    
    print(f"✅ 导入成功: {is_import_successful()}")
    
    # 创建实例测试
    analyzer = analyzer_class()
    print(f"✅ 实例创建: {analyzer}")
    
    print("🎉 导入测试完成!")
