"""
测试修复后的TTS管理器
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

try:
    from utils.integrated_tts_manager import IntegratedTTSManager, TTSConfig, TTSEngine
    print("✅ TTS管理器导入成功")
except ImportError as e:
    print(f"❌ TTS管理器导入失败: {e}")
    sys.exit(1)

async def test_tts_basic():
    """基本TTS测试"""
    print("🔄 开始基本TTS测试...")
    
    # 创建配置
    config = TTSConfig()
    
    # 创建管理器
    tts_manager = IntegratedTTSManager(config)
    
    # 显示状态
    status = tts_manager.get_engine_status()
    print(f"📊 引擎状态: {status}")
    
    # 测试静默音频生成
    test_text = "这是一个测试文本"
    output_file = Path("output/test_silent.wav")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔄 测试静默音频生成: {test_text}")
    
    try:
        result = await tts_manager._generate_silent_audio(test_text, output_file)
        
        if result["success"]:
            print(f"✅ 静默音频生成成功")
            print(f"   文件: {output_file}")
            print(f"   时长: {result['duration']:.2f} 秒")
            print(f"   大小: {result['file_size']} 字节")
        else:
            print(f"❌ 静默音频生成失败")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

async def test_edge_tts():
    """测试Edge TTS"""
    print("\n🔄 测试Edge TTS...")
    
    config = TTSConfig()
    tts_manager = IntegratedTTSManager(config)
    
    test_text = "你好，这是Edge TTS测试"
    output_file = Path("output/test_edge.wav")
    
    try:
        result = await tts_manager.synthesize_speech(test_text, output_file, TTSEngine.EDGE_TTS)
        
        if result["success"]:
            print(f"✅ Edge TTS测试成功")
            print(f"   引擎: {result['engine']}")
            print(f"   时长: {result['duration']:.2f} 秒")
        else:
            print(f"❌ Edge TTS测试失败")
            
    except Exception as e:
        print(f"⚠️ Edge TTS可能不可用: {e}")

def test_imports():
    """测试可选库导入"""
    print("\n🔍 测试可选库导入状态...")
    
    imports_status = {
        "numpy": False,
        "scipy": False,
        "edge_tts": False,
        "moviepy": False,
        "pydub": False,
        "openai": False,
        "azure_speech": False
    }
    
    try:
        import numpy
        imports_status["numpy"] = True
        print("✅ numpy 可用")
    except ImportError:
        print("❌ numpy 不可用")
    
    try:
        from scipy.io.wavfile import write
        imports_status["scipy"] = True
        print("✅ scipy 可用")
    except ImportError:
        print("❌ scipy 不可用")
    
    try:
        import edge_tts
        imports_status["edge_tts"] = True
        print("✅ edge_tts 可用")
    except ImportError:
        print("❌ edge_tts 不可用")
    
    try:
        from moviepy.editor import AudioFileClip
        imports_status["moviepy"] = True
        print("✅ moviepy 可用")
    except ImportError:
        print("❌ moviepy 不可用")
    
    try:
        from pydub import AudioSegment
        imports_status["pydub"] = True
        print("✅ pydub 可用")
    except ImportError:
        print("❌ pydub 不可用")
    
    try:
        import openai
        imports_status["openai"] = True
        print("✅ openai 可用")
    except ImportError:
        print("❌ openai 不可用 (可选)")
    
    try:
        import azure.cognitiveservices.speech
        imports_status["azure_speech"] = True
        print("✅ azure_speech 可用")
    except ImportError:
        print("❌ azure_speech 不可用 (可选)")
    
    return imports_status

if __name__ == "__main__":
    print("🚀 开始TTS管理器测试...")
    
    # 测试导入
    test_imports()
    
    # 运行异步测试
    asyncio.run(test_tts_basic())
    asyncio.run(test_edge_tts())
    
    print("\n✨ 测试完成！")
