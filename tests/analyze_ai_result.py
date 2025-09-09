#!/usr/bin/env python3
"""
验证AI优化结果
"""
import json
from pathlib import Path

def analyze_ai_optimization_result():
    """分析AI优化结果"""
    print("🔍 分析AI前置断句内容优化结果")
    print("=" * 60)
    
    result_file = Path("test_ai_optimization/ai_optimization_test_result.json")
    
    if not result_file.exists():
        print("❌ 结果文件不存在")
        return
    
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_data = data.get('original_data', {})
    optimized_data = data.get('optimized_data', {})
    
    print("📊 优化结果分析:")
    
    original_scripts = original_data.get('scripts', [])
    optimized_scripts = optimized_data.get('scripts', [])
    
    print(f"   原始页面数: {len(original_scripts)}")
    print(f"   优化后分段数: {len(optimized_scripts)}")
    
    # 按页面分组显示
    page_segments = {}
    for segment in optimized_scripts:
        page_num = segment.get('slide_number', 0)
        if page_num not in page_segments:
            page_segments[page_num] = []
        page_segments[page_num].append(segment)
    
    print("\n📝 分段详情:")
    for page_num in sorted(page_segments.keys()):
        segments = page_segments[page_num]
        print(f"\n   第{page_num}页: {len(segments)} 个分段")
        
        for i, segment in enumerate(segments):
            content = segment.get('script_content', '')
            length = segment.get('word_count', len(content))
            segment_type = segment.get('segment_type', 'unknown')
            print(f"     分段{i+1}({segment_type}): {length}字 - {content}")
    
    # 统计分析
    total_original_segments = len(original_scripts)
    total_optimized_segments = len(optimized_scripts)
    
    print(f"\n📈 统计结果:")
    print(f"   分段总数: {total_original_segments} → {total_optimized_segments}")
    
    if total_optimized_segments > total_original_segments:
        print("✅ AI前置断句内容优化功能正常工作！")
        print("✅ 成功将长句拆分为较短的分段")
        
        # 检查分段长度
        lengths = [seg.get('word_count', 0) for seg in optimized_scripts]
        max_length = max(lengths)
        min_length = min(lengths)
        avg_length = sum(lengths) / len(lengths)
        
        print(f"✅ 分段长度控制:")
        print(f"   最短: {min_length}字")
        print(f"   最长: {max_length}字") 
        print(f"   平均: {avg_length:.1f}字")
        
        if max_length <= 35:
            print("✅ 所有分段都符合35字符限制")
            print("✅ 应该能完全解决多行字幕问题！")
        else:
            print(f"⚠️  存在超过35字符的分段 (最长{max_length}字)")
    else:
        print("❌ AI优化没有增加分段数量")
    
    # 检查原始内容长度
    print(f"\n📋 原始内容长度:")
    for script in original_scripts:
        content = script.get('script_content', '')
        length = len(content)
        print(f"   第{script.get('slide_number')}页: {length}字 - {content[:50]}...")
    
    print("=" * 60)
    print("🏁 分析完成")

if __name__ == "__main__":
    analyze_ai_optimization_result()
