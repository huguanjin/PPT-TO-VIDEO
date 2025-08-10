"""
测试多引擎TTS功能
"""
import asyncio
import logging
from pathlib import Path
from utils.integrated_tts_manager import IntegratedTTSManager, TTSConfig, TTSEngine

async def test_multi_engine_tts():
    """测试多引擎TTS功能"""
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("🎵 开始测试多引擎TTS功能...")
    
    # 创建TTS配置
    config = TTSConfig(
        edge_voice="zh-CN-XiaoxiaoNeural",
        edge_rate="medium",
        edge_pitch="medium",
        # 如果有API密钥，可以在这里配置
        # fish_api_key="your_fish_api_key",
        # openai_api_key="your_openai_api_key",
    )
    
    # 创建TTS管理器
    tts_manager = IntegratedTTSManager(config)
    
    # 显示引擎状态
    engine_status = tts_manager.get_engine_status()
    print(f"📊 引擎状态: {engine_status}")
    
    # 测试文本
    test_texts = [
        "你好，这是一个语音合成测试。",
        "PPT转视频工具现在支持多种TTS引擎了！",
        "包括Edge TTS、Fish TTS、OpenAI TTS等。"
    ]
    
    # 创建测试输出目录
    output_dir = Path("output/tts_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 测试每个可用引擎
    for i, text in enumerate(test_texts):
        output_file = output_dir / f"test_audio_{i+1:03d}.wav"
        
        print(f"\n🔄 测试第 {i+1} 个文本: {text}")
        
        try:
            result = await tts_manager.synthesize_speech(text, output_file)
            
            if result["success"]:
                print(f"✅ 成功使用 {result['engine']} 引擎")
                print(f"   文件: {output_file}")
                print(f"   时长: {result['duration']:.2f} 秒")
                print(f"   大小: {result['file_size']} 字节")
                
                if result.get('estimated'):
                    print("   ⚠️  使用了静默音频（估算时长）")
            else:
                print(f"❌ 合成失败: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
    
    print(f"\n🎉 测试完成！输出文件保存在: {output_dir}")

async def test_specific_engine():
    """测试特定引擎"""
    
    print("\n🎯 测试特定引擎功能...")
    
    config = TTSConfig()
    tts_manager = IntegratedTTSManager(config)
    
    test_text = "这是一个特定引擎的测试。"
    output_dir = Path("output/tts_test")
    
    # 测试每个可用引擎
    for engine in tts_manager.engines:
        if engine == TTSEngine.SILENT:
            continue  # 跳过静默引擎
            
        print(f"\n🔧 测试 {engine.value} 引擎...")
        output_file = output_dir / f"test_{engine.value}.wav"
        
        try:
            result = await tts_manager.synthesize_speech(
                test_text, 
                output_file, 
                preferred_engine=engine
            )
            
            if result["success"]:
                print(f"✅ {engine.value} 引擎测试成功")
                print(f"   实际使用引擎: {result['engine']}")
                print(f"   时长: {result['duration']:.2f} 秒")
            else:
                print(f"❌ {engine.value} 引擎测试失败")
                
        except Exception as e:
            print(f"❌ {engine.value} 引擎异常: {str(e)}")

if __name__ == "__main__":
    print("🚀 启动多引擎TTS测试...")
    
    # 运行基本测试
    asyncio.run(test_multi_engine_tts())
    
    # 运行特定引擎测试
    asyncio.run(test_specific_engine())
    
    print("\n✨ 所有测试完成！")
