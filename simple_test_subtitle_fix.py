"""
简化版字幕修复测试
"""

from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer

# 创建修复器实例
fixer = SubtitleMultilineFixer()

# 测试案例
test_cases = [
    "这是一个很长的测试句子，用来验证字幕分割功能是否能够正确处理多行显示的问题。",
    "第一行\n第二行\n第三行\n第四行",
    "短句测试"
]

print("字幕多行显示修复测试")
print("=" * 30)

for i, text in enumerate(test_cases, 1):
    print(f"\n测试案例 {i}:")
    print(f"原始: {text}")
    
    # 计算权重
    weight = fixer.calculate_enhanced_char_weight(text)
    print(f"权重: {weight:.2f}")
    
    # 优化文本
    optimized = fixer.optimize_subtitle_text(text)
    lines = optimized.split('\n')
    print(f"优化后: {optimized}")
    print(f"行数: {len(lines)}")
    
    # 验证每行权重
    for j, line in enumerate(lines, 1):
        line_weight = fixer.calculate_enhanced_char_weight(line)
        print(f"  第{j}行权重: {line_weight:.2f}")

print("\n测试完成！")
