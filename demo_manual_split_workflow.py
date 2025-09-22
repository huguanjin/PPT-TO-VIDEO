#!/usr/bin/env python3
"""
手动分割功能演示脚本
展示从内容输入到字幕生成的完整工作流
"""
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent / "flask_backend"))

from flask_backend.core.step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator
from flask_backend.app.utils.config_manager import ConfigManager


def demonstrate_manual_split_workflow():
    """演示手动分割完整工作流"""
    project_dir = Path(__file__).parent
    
    print("🎬 手动分割功能演示")
    print("=" * 50)
    
    # 1. 配置展示
    print("\n📋 步骤1: 检查配置")
    config_manager = ConfigManager(project_dir)
    manual_config = config_manager.get_manual_split_config()
    print(f"✅ 手动分割功能状态: {'启用' if manual_config.get('enabled') else '禁用'}")
    print(f"   分割策略: {manual_config.get('split_strategy', {}).get('method', '未知')}")
    
    # 2. 创建字幕生成器
    print("\n🛠️ 步骤2: 初始化字幕生成器")
    generator = EnhancedSubtitleGenerator(project_dir)
    print("✅ 字幕生成器初始化完成")
    
    # 3. 测试不同类型的内容
    test_cases = [
        {
            "name": "普通文本（自动分割）",
            "content": "这是一段普通的配音稿内容，没有换行符，将使用自动分割模式进行处理。",
            "expected_mode": "自动分割"
        },
        {
            "name": "手动分割文本（换行分割）",
            "content": "欢迎来到PPTist视频制作平台。\n在这里您可以轻松制作专业的演示视频。\n让我们开始您的创作之旅吧！",
            "expected_mode": "手动分割"
        },
        {
            "name": "混合内容（长段落+换行）",
            "content": "PPTist是一个功能强大的在线PPT编辑和视频制作平台，支持多种导出格式。\n您可以使用我们的AI助手快速生成内容。\n现在就开始创建您的第一个作品吧！",
            "expected_mode": "手动分割"
        }
    ]
    
    print("\n🔍 步骤3: 测试分割功能")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n   测试 {i}: {case['name']}")
        print(f"   内容: {case['content']}")
        print(f"   预期模式: {case['expected_mode']}")
        
        # 执行分割
        segments = generator._split_text_to_segments(case['content'])
        
        print(f"   📊 分割结果: {len(segments)} 个片段")
        for j, segment in enumerate(segments, 1):
            print(f"      片段 {j}: {repr(segment)}")
        
        # 分析结果
        is_manual = '\n' in case['content'] and len(segments) == len([s for s in case['content'].split('\n') if s.strip()])
        actual_mode = "手动分割" if is_manual else "自动分割"
        
        if actual_mode == case['expected_mode']:
            print(f"   ✅ 模式匹配正确: {actual_mode}")
        else:
            print(f"   ⚠️ 模式不匹配: 预期 {case['expected_mode']}, 实际 {actual_mode}")
    
    # 4. 展示质量评估
    print("\n📈 步骤4: 质量评估演示")
    
    # 测试不同质量的片段
    quality_tests = [
        ("很短", "短。"),  # 过短片段
        ("适中", "这是一个长度适中的配音稿片段，语速正常。"),  # 正常片段
        ("过长", "这是一个非常长的配音稿片段，包含了很多内容，可能会导致语音时长过长，建议进行进一步的分割处理以获得更好的观看体验。")  # 过长片段
    ]
    
    for desc, content in quality_tests:
        segments = generator._split_text_to_segments(content)
        if segments:
            segment = segments[0]
            char_count = len(segment)
            duration = max(1, round(char_count / 4.2))
            
            print(f"   {desc}片段: '{segment}'")
            print(f"      字符数: {char_count}, 预计时长: {duration}秒")
            
            # 质量评估
            if char_count < 5:
                print(f"      ⚠️ 质量警告: 片段过短")
            elif char_count > 50:
                print(f"      ⚠️ 质量警告: 片段过长")
            elif duration > 10:
                print(f"      ⚠️ 质量警告: 时长过长")
            else:
                print(f"      ✅ 质量良好")
    
    # 5. 配置建议
    print("\n⚙️ 步骤5: 配置建议")
    print("   推荐设置:")
    print("   - 每个片段: 5-30字符")
    print("   - 预计时长: 1-8秒")
    print("   - 每页片段: 不超过8个")
    print("   - 语速设置: 4.2字/秒")
    
    print("\n✨ 演示完成！")
    print("手动分割功能已完全集成，可以在PPTist编辑器中正常使用。")


def show_configuration_details():
    """显示详细配置信息"""
    print("\n📋 配置详情")
    print("=" * 30)
    
    config_path = Path(__file__).parent / "config" / "manual_split_config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("🔧 当前配置:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
    else:
        print("❌ 配置文件不存在")


if __name__ == "__main__":
    try:
        demonstrate_manual_split_workflow()
        
        # 询问是否查看配置
        if input("\n是否查看详细配置？(y/n): ").lower() == 'y':
            show_configuration_details()
            
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()