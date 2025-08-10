"""
验证Edge TTS速率修复
"""
import asyncio
from pathlib import Path
from utils.integrated_tts_manager import IntegratedTTSManager, TTSConfig, TTSEngine

async def test_edge_tts_fixed():
    """测试修复后的Edge TTS"""
    print("🔄 测试修复后的Edge TTS...")
    
    # 创建配置
    config = TTSConfig(
        edge_voice="zh-CN-XiaoxiaoNeural",
        edge_rate="medium", 
        edge_pitch="medium"
    )
    
    # 创建管理器
    tts_manager = IntegratedTTSManager(config)
    
    # 测试文本
    test_text = "你好，这是修复后的Edge TTS测试。"
    output_file = Path("output/test_edge_fixed.wav")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 直接调用library方法
        result = await tts_manager._edge_tts_library_method(test_text, output_file)
        
        if result["success"]:
            print(f"✅ Edge TTS修复成功!")
            print(f"   方法: {result['method']}")
            print(f"   时长: {result['duration']:.2f} 秒")
            print(f"   文件: {output_file}")
            print(f"   大小: {result['file_size']} 字节")
        else:
            print(f"❌ Edge TTS仍然失败")
            
    except Exception as e:
        print(f"❌ Edge TTS异常: {e}")
        
        # 测试整体合成方法
        print("🔄 测试整体合成方法（包含fallback）...")
        try:
            result = await tts_manager.synthesize_speech(test_text, output_file)
            
            if result["success"]:
                print(f"✅ 合成成功（使用引擎: {result['engine']}）")
                print(f"   时长: {result['duration']:.2f} 秒")
            else:
                print(f"❌ 合成失败")
                
        except Exception as e2:
            print(f"❌ 合成异常: {e2}")

if __name__ == "__main__":
    asyncio.run(test_edge_tts_fixed())
