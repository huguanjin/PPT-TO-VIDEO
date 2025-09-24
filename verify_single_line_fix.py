#!/usr/bin/env python3
"""
验证单行模式修复效果 - 直接测试修复后的逻辑
"""
import sys
import os
from pathlib import Path
import asyncio
import json

# 添加 flask_backend 到路径中
project_root = Path(__file__).parent
flask_backend_path = project_root / "flask_backend"
sys.path.insert(0, str(flask_backend_path))

def main():
    """主测试函数"""
    print("🧪 验证单行模式修复效果")
    print("="*60)
    
    # 1. 验证配置文件
    print("\n📋 步骤1: 验证配置文件")
    config_path = project_root / "flask_backend" / "config_data" / "manual_split_config.json"
    
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    single_line_mode = config.get('single_line_mode', False)
    print(f"✅ 配置文件存在")
    print(f"🔍 single_line_mode: {single_line_mode}")
    
    if not single_line_mode:
        print("❌ single_line_mode未启用，请设置为true")
        return
    
    # 2. 导入并测试SubtitleGenerator
    print("\n🔧 步骤2: 测试SubtitleGenerator")
    try:
        from core.step04_subtitle_generator import SubtitleGenerator
        generator = SubtitleGenerator(project_root)
        print(f"✅ SubtitleGenerator创建成功")
        print(f"🔍 generator.single_line_mode: {generator.single_line_mode}")
        
        if not generator.single_line_mode:
            print("❌ SubtitleGenerator中single_line_mode未正确加载")
            return
            
    except Exception as e:
        print(f"❌ SubtitleGenerator创建失败: {e}")
        return
    
    # 3. 测试_split_text_to_segments方法
    print("\n🧪 步骤3: 测试文本分割逻辑")
    
    # 测试用例1: 多行文本 
    test_text_1 = "第一行内容\n第二行内容\n第三行内容"
    print(f"📝 测试用例1: '{test_text_1}'")
    
    try:
        segments_1 = asyncio.run(generator._split_text_to_segments(test_text_1))
        print(f"🔄 分割结果 ({len(segments_1)} 个片段):")
        for i, segment in enumerate(segments_1, 1):
            print(f"   片段{i}: '{segment}'")
            
        # 验证结果
        expected_segments = ["第一行内容", "第二行内容", "第三行内容"]
        if segments_1 == expected_segments:
            print("✅ 测试用例1通过: 多行文本正确拆分为单行")
        else:
            print("❌ 测试用例1失败: 分割结果不符合预期")
            print(f"   预期: {expected_segments}")
            print(f"   实际: {segments_1}")
            
    except Exception as e:
        print(f"❌ 测试用例1执行失败: {e}")
    
    # 测试用例2: 单行文本
    test_text_2 = "这是单行文本内容"
    print(f"\n📝 测试用例2: '{test_text_2}'")
    
    try:
        segments_2 = asyncio.run(generator._split_text_to_segments(test_text_2))
        print(f"🔄 分割结果 ({len(segments_2)} 个片段):")
        for i, segment in enumerate(segments_2, 1):
            print(f"   片段{i}: '{segment}'")
            
        # 验证结果
        if len(segments_2) == 1 and segments_2[0] == test_text_2:
            print("✅ 测试用例2通过: 单行文本保持不变")
        else:
            print("❌ 测试用例2失败: 单行文本被错误处理")
            
    except Exception as e:
        print(f"❌ 测试用例2执行失败: {e}")
    
    # 4. 测试step05最终合并器
    print("\n🔧 步骤4: 测试Step05最终合并器")
    try:
        from core.step05_final_merger import FFmpegFinalMerger
        merger = FFmpegFinalMerger(project_root)
        print(f"✅ FFmpegFinalMerger创建成功")
        print(f"🔍 merger.single_line_mode: {merger.single_line_mode}")
        
        if merger.single_line_mode:
            print("✅ Step05正确加载单行模式配置，将跳过多行修复")
        else:
            print("❌ Step05未正确加载单行模式配置")
            
    except Exception as e:
        print(f"❌ Step05测试失败: {e}")
    
    print("\n" + "="*60)
    print("✅ 单行模式修复效果验证完成")
    print("🔧 如果所有测试通过，说明修复生效")
    print("🎯 现在可以运行完整工作流测试实际效果")

if __name__ == "__main__":
    main()