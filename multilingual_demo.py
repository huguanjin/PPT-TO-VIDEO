"""
多语言支持系统使用示例
任务3.2: 展示完整的多语言字幕处理工作流
"""

import asyncio
import json
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def demo_basic_language_detection():
    """演示基础语言检测功能"""
    print("🌍 === 基础语言检测功能演示 ===")
    
    from flask_backend.core.multilingual_support import AdvancedLanguageDetector
    
    detector = AdvancedLanguageDetector()
    
    demo_texts = {
        "中文商务": "欢迎大家参加今天的产品发布会，我们将为大家介绍最新的PPT转视频解决方案。",
        "英文技术": "Welcome to our product demonstration. We will showcase the latest PPT to video conversion technology.",
        "日文介绍": "本日は貴重なお時間をいただき、ありがとうございます。新しいプレゼンテーション技術をご紹介いたします。",
        "混合场景": "Today我们要discuss一个very important的topic关于multilingual processing。"
    }
    
    for scenario, text in demo_texts.items():
        language, confidence = detector.detect_language(text)
        print(f"📝 {scenario}")
        print(f"   文本: {text}")
        print(f"   检测结果: {language.value} (置信度: {confidence:.3f})")
        print()

async def demo_multilingual_splitting():
    """演示多语言智能分割功能"""
    print("✂️ === 多语言智能分割功能演示 ===")
    
    from flask_backend.core.multilingual_support import MultilingualSplittingEngine, SupportedLanguage
    
    engine = MultilingualSplittingEngine()
    
    demo_scenarios = {
        "教育场景": {
            "text": "人工智能技术正在快速发展，它在教育、医疗、金融等各个领域都有着广泛的应用前景，我们需要深入了解其原理和实现方式，才能更好地利用这项技术为社会创造价值。",
            "language": SupportedLanguage.CHINESE_SIMPLIFIED
        },
        "商务演示": {
            "text": "Our company has achieved remarkable growth this quarter, with revenue increasing by 35% compared to last year, and we are excited to announce the launch of three new product lines that will revolutionize the market.",
            "language": SupportedLanguage.ENGLISH
        },
        "技术文档": {
            "text": "この新しいアルゴリズムは、従来の手法と比較して処理速度が50%向上し、精度も大幅に改善されています。実装においては、メモリ使用量の最適化にも重点を置いています。",
            "language": SupportedLanguage.JAPANESE
        }
    }
    
    for scenario, data in demo_scenarios.items():
        print(f"📋 {scenario} ({data['language'].value})")
        print(f"   原文: {data['text']}")
        
        segments = await engine.split_multilingual_text(
            data['text'], 
            target_language=data['language']
        )
        
        print(f"   分割结果 ({len(segments)} 个片段):")
        for i, segment in enumerate(segments):
            print(f"     {i+1}: '{segment.text}' (置信度: {segment.confidence:.3f})")
        print()

async def demo_multilingual_subtitle_generation():
    """演示多语言字幕生成功能"""
    print("🎬 === 多语言字幕生成功能演示 ===")
    
    from flask_backend.core.multilingual_support import CrossLanguageSubtitleManager, SupportedLanguage
    
    manager = CrossLanguageSubtitleManager()
    
    # 模拟PPT幻灯片内容
    slide_contents = [
        "欢迎使用我们的多语言PPT转视频系统",
        "该系统支持智能断句和语言检测功能",
        "可以生成高质量的多语言字幕",
        "支持中文、英文、日文等多种语言",
        "具有跨语言同步和时间对齐功能"
    ]
    
    print(f"📖 幻灯片内容 ({len(slide_contents)} 张):")
    for i, content in enumerate(slide_contents):
        print(f"   第{i+1}张: {content}")
    print()
    
    # 生成多语言字幕
    multilingual_subtitles = await manager.create_multilingual_subtitles(
        texts=slide_contents,
        primary_language=SupportedLanguage.CHINESE_SIMPLIFIED,
        secondary_languages=[SupportedLanguage.ENGLISH, SupportedLanguage.JAPANESE]
    )
    
    print("🎯 多语言字幕生成结果:")
    for language, subtitles in multilingual_subtitles.items():
        print(f"\n   {language.value} 字幕:")
        for i, subtitle in enumerate(subtitles):
            print(f"     [{subtitle.start_time:.1f}s-{subtitle.end_time:.1f}s] {subtitle.text}")

async def demo_complete_workflow():
    """演示完整的多语言处理工作流"""
    print("🚀 === 完整多语言处理工作流演示 ===")
    
    from flask_backend.core.multilingual_integration import MultilingualSubtitleIntegrator
    
    integrator = MultilingualSubtitleIntegrator()
    
    # 模拟真实的PPT内容（混合语言）
    mixed_content = [
        "Welcome to AI Innovation Conference 2025",
        "今天我们将探讨人工智能的最新发展",
        "This presentation covers machine learning, deep learning, and neural networks",
        "我们的研究团队开发了革命性的算法",
        "The results show 95% accuracy improvement",
        "感谢大家的参与，期待未来的合作机会"
    ]
    
    # 配置多语言处理参数
    config = {
        "source_language": "auto",
        "target_languages": ["zh-CN", "en", "ja"],
        "auto_detect_language": True,
        "cross_language_sync": True,
        "generate_separate_files": True,
        "subtitle": {
            "max_length": 40,
            "target_length": 35,
            "netflix_standard": True
        },
        "tts": {
            "multilingual_voices": True,
            "auto_voice_selection": True
        }
    }
    
    print(f"📝 输入内容 ({len(mixed_content)} 条):")
    for i, content in enumerate(mixed_content):
        print(f"   {i+1}: {content}")
    print()
    
    print("⚙️ 处理配置:")
    print(f"   源语言: {config['source_language']}")
    print(f"   目标语言: {', '.join(config['target_languages'])}")
    print(f"   自动检测: {config['auto_detect_language']}")
    print(f"   跨语言同步: {config['cross_language_sync']}")
    print()
    
    # 执行完整处理
    print("🔄 开始处理...")
    
    def progress_callback(message):
        print(f"   ⏳ {message}")
    
    start_time = time.time()
    result = await integrator.enhance_subtitle_generation_multilingual(
        texts=mixed_content,
        config=config,
        progress_callback=progress_callback
    )
    processing_time = time.time() - start_time
    
    print(f"✅ 处理完成! 耗时: {processing_time:.2f}秒")
    print()
    
    # 展示处理结果
    print("📊 处理结果分析:")
    lang_analysis = result["language_analysis"]
    print(f"   检测到的主要语言: {lang_analysis['primary_language']}")
    print(f"   平均检测置信度: {lang_analysis['average_confidence']:.3f}")
    print(f"   语言分布:")
    for lang, dist in lang_analysis['language_distribution'].items():
        print(f"     {lang}: {dist['count']} 条 ({dist['percentage']:.1f}%)")
    print()
    
    # 展示多语言字幕
    print("🎬 生成的多语言字幕:")
    for lang_code, subtitles in result["multilingual_subtitles"].items():
        print(f"\n   {lang_code} 字幕 ({len(subtitles)} 条):")
        for i, subtitle in enumerate(subtitles[:3]):  # 只显示前3条
            if hasattr(subtitle, 'start_time'):
                # 如果是对象，直接访问属性
                print(f"     [{subtitle.start_time:.1f}s-{subtitle.end_time:.1f}s] {subtitle.text}")
            else:
                # 如果是字典，用字典方式访问
                print(f"     [{subtitle['start_time']:.1f}s-{subtitle['end_time']:.1f}s] {subtitle['text']}")
    
    # 展示处理统计
    print("\n📈 处理统计:")
    stats = result["processing_stats"]
    print(f"   总语言数: {stats['total_languages']}")
    for lang, count in stats['subtitle_counts'].items():
        print(f"   {lang}: {count} 条字幕")

async def demo_api_integration():
    """演示API集成使用"""
    print("🔌 === API集成使用演示 ===")
    
    # 模拟API调用数据
    api_demo_data = {
        "language_detection": {
            "text": "Hello everyone! 今天我们来学习machine learning基础知识。",
            "expected_result": "mixed language detection"
        },
        "multilingual_splitting": {
            "text": "人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。",
            "target_language": "zh-CN",
            "expected_segments": 2
        },
        "subtitle_generation": {
            "texts": ["这是第一句", "This is the second sentence", "これは三番目の文です"],
            "config": {
                "primary_language": "auto",
                "secondary_languages": ["zh-CN", "en", "ja"]
            }
        }
    }
    
    print("🎯 API集成功能演示:")
    print(f"   语言检测: '{api_demo_data['language_detection']['text']}'")
    print(f"   智能分割: 中文长句分割处理")
    print(f"   字幕生成: 3条多语言内容处理")
    print("   (实际API调用需要启动Flask服务)")
    print()
    
    # 展示API端点
    api_endpoints = [
        "GET  /api/multilingual/languages - 获取支持的语言列表",
        "POST /api/multilingual/detect-language - 检测文本语言",
        "POST /api/multilingual/split-multilingual - 多语言智能分割",
        "POST /api/multilingual/generate-multilingual-subtitles - 生成多语言字幕",
        "POST /api/multilingual/enhance-subtitle-generation - 完整处理流程",
        "GET  /api/multilingual/language-config/<code> - 获取语言配置",
        "POST /api/multilingual/optimize-config - 优化配置",
        "GET  /api/multilingual/health - 健康检查"
    ]
    
    print("📋 可用的API端点:")
    for endpoint in api_endpoints:
        print(f"   {endpoint}")

async def demo_performance_showcase():
    """演示性能优化特性"""
    print("⚡ === 性能优化特性演示 ===")
    
    from flask_backend.core.multilingual_support import AdvancedLanguageDetector, MultilingualSplittingEngine
    
    detector = AdvancedLanguageDetector()
    engine = MultilingualSplittingEngine()
    
    # 性能测试数据
    test_cases = [
        "短句测试",
        "这是一个中等长度的句子，用来测试处理性能。",
        "This is a longer sentence that contains more words and characters to test the processing performance of our multilingual system.",
        "これは非常に長い日本語の文章で、多言語処理システムの性能をテストするために使用されます。複数の文が含まれており、処理時間と精度の両方を評価できます。"
    ]
    
    print("🔍 语言检测性能测试:")
    total_chars = sum(len(text) for text in test_cases)
    
    start_time = time.time()
    for text in test_cases * 50:  # 重复50次
        detector.detect_language(text)
    detection_time = time.time() - start_time
    
    print(f"   处理字符数: {total_chars * 50:,}")
    print(f"   总耗时: {detection_time:.3f}秒")
    print(f"   处理速度: {total_chars * 50 / detection_time:.0f} 字符/秒")
    print()
    
    print("✂️ 智能分割性能测试:")
    start_time = time.time()
    total_segments = 0
    
    for text in test_cases * 20:  # 重复20次
        segments = await engine.split_multilingual_text(text)
        total_segments += len(segments)
    
    splitting_time = time.time() - start_time
    
    print(f"   处理文本数: {len(test_cases) * 20}")
    print(f"   生成片段数: {total_segments}")
    print(f"   总耗时: {splitting_time:.3f}秒")
    print(f"   处理速度: {len(test_cases) * 20 / splitting_time:.1f} 文本/秒")
    print()
    
    print("💾 缓存优化演示:")
    # 重复相同文本的处理，展示缓存效果
    repeated_text = "这是一个重复的测试文本，用于演示缓存优化效果。"
    
    # 第一次处理（无缓存）
    start_time = time.time()
    for _ in range(100):
        detector.detect_language(repeated_text)
    first_run = time.time() - start_time
    
    # 第二次处理（有缓存）
    start_time = time.time()
    for _ in range(100):
        detector.detect_language(repeated_text)
    second_run = time.time() - start_time
    
    print(f"   第一次运行: {first_run:.4f}秒")
    print(f"   第二次运行: {second_run:.4f}秒")
    print(f"   性能提升: {first_run / second_run:.1f}x")

async def run_multilingual_demo():
    """运行完整的多语言支持演示"""
    print("🌍 多语言支持增强系统 - 功能演示")
    print("=" * 60)
    print(f"📅 演示时间: 2025年9月9日")
    print(f"🎯 任务版本: 3.2 - 多语言支持增强")
    print("=" * 60)
    
    demos = [
        ("基础语言检测", demo_basic_language_detection),
        ("多语言智能分割", demo_multilingual_splitting),
        ("多语言字幕生成", demo_multilingual_subtitle_generation),
        ("完整处理工作流", demo_complete_workflow),
        ("API集成使用", demo_api_integration),
        ("性能优化特性", demo_performance_showcase)
    ]
    
    total_start = time.time()
    
    for demo_name, demo_func in demos:
        print(f"\n🎪 {demo_name}")
        print("-" * 40)
        
        start_time = time.time()
        await demo_func()
        duration = time.time() - start_time
        
        print(f"⏱️  演示耗时: {duration:.2f}秒")
        print()
    
    total_duration = time.time() - total_start
    
    print("=" * 60)
    print("🎉 多语言支持系统演示完成")
    print("=" * 60)
    print(f"⏱️  总演示时间: {total_duration:.2f}秒")
    print()
    print("✨ 系统特性总结:")
    print("   🌏 支持20+种语言的智能检测")
    print("   ✂️  基于语义的智能文本分割")
    print("   📝 多语言字幕生成和同步")
    print("   ⚙️  语言特定的配置优化")
    print("   🔌 完整的REST API接口")
    print("   ⚡ 毫秒级的高性能处理")
    print("   💾 智能缓存和性能优化")
    print("   🔄 与现有系统无缝集成")
    print()
    print("🚀 任务3.2 - 多语言支持增强 已完成!")

if __name__ == "__main__":
    # 运行多语言支持演示
    asyncio.run(run_multilingual_demo())
