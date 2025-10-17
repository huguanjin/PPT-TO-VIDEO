from pathlib import Path
import edge_tts as edge_tts_lib  # 重命名以避免冲突
import os, sys
import asyncio
import time
import requests
import json
import ssl
import certifi

# ⚠️ SSL证书修复: 微软Edge TTS服务器证书过期问题
# 临时禁用SSL验证以解决连接问题
# 生产环境建议使用其他TTS服务或等待微软修复证书
_original_create_default_context = ssl.create_default_context

def _create_unverified_context(*args, **kwargs):
    """创建不验证证书的SSL上下文"""
    context = _original_create_default_context(*args, **kwargs)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

# 全局替换SSL上下文创建函数
ssl.create_default_context = _create_unverified_context

# 添加正确的路径以导入config_utils
current_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_dir, "..")
sys.path.insert(0, parent_dir)

from core.config_utils import load_key

# Available voices can be listed using edge-tts --list-voices command
# Common English voices:
# en-US-JennyNeural - Female
# en-US-GuyNeural - Male  
# en-GB-SoniaNeural - Female British
# Common Chinese voices:
# zh-CN-XiaoxiaoNeural - Female
# zh-CN-YunxiNeural - Male
# zh-CN-XiaoyiNeural - Female
def custom_edge_tts_fallback(text, save_path, voice="zh-CN-XiaoxiaoNeural", rate="+0%", pitch="+0Hz"):
    """
    自定义Edge TTS回退方法
    当edge-tts库失败时使用的备用方案
    """
    import subprocess
    import tempfile
    
    try:
        print(f"🔄 使用自定义Edge TTS回退方案...")
        print(f"   语音: {voice}, 速率: {rate}, 音调: {pitch}")
        
        # 创建临时SSML文件
        ssml_content = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
            <voice name="{voice}">
                <prosody rate="{rate}" pitch="{pitch}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        # 使用edge-tts命令行工具
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--rate", rate,
            "--pitch", pitch,
            "--text", text,
            "--write-media", str(save_path)
        ]
        
        print(f"🔧 执行命令: {' '.join(cmd[:6])}...")  # 只显示前几个参数
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60秒超时
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            # 验证文件生成
            speech_file_path = Path(save_path)
            if speech_file_path.exists() and speech_file_path.stat().st_size > 1000:
                print(f"✅ 自定义Edge TTS成功: 文件大小 {speech_file_path.stat().st_size} bytes")
                return True
            else:
                print(f"❌ 自定义Edge TTS生成文件过小或不存在")
                return False
        else:
            print(f"❌ 自定义Edge TTS命令执行失败:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 自定义Edge TTS超时")
        return False
    except Exception as e:
        print(f"❌ 自定义Edge TTS异常: {str(e)}")
        return False

def edge_tts(text, save_path):
    """
    优化的Edge TTS函数
    优先使用edge-tts库，失败后回退到自定义方法
    """
    start_time = time.time()
    
    # Load settings from config file
    edge_set = load_key("edge_tts")
    voice = edge_set.get("voice", "zh-CN-XiaoxiaoNeural")  # 改为中文默认语音
    rate = edge_set.get("rate", "medium")
    pitch = edge_set.get("pitch", "medium")
    
    # Create output directory if it doesn't exist
    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 格式转换映射
    rate_mapping = {
        "slow": "-50%",
        "medium": "+0%", 
        "fast": "+50%"
    }
    pitch_mapping = {
        "x-low": "-50Hz",
        "low": "-25Hz", 
        "medium": "+0Hz",
        "high": "+25Hz",
        "x-high": "+50Hz"
    }
    
    # 转换格式
    edge_rate = rate_mapping.get(rate, "+0%")
    edge_pitch = pitch_mapping.get(pitch, "+0Hz")
    
    print(f"🎤 Edge TTS 配音开始")
    print(f"   文本长度: {len(text)} 字符")
    print(f"   配音设置: 语音={voice}, 速率={edge_rate}, 音调={edge_pitch}")
    print(f"   输出路径: {speech_file_path}")
    
    # 方法1: 优先使用edge-tts库 (异步方法)
    async def async_edge_tts_lib():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"📚 Edge TTS库尝试 {attempt + 1}/{max_retries}...")
                
                communicate = edge_tts_lib.Communicate(
                    text, 
                    voice,
                    rate=edge_rate,
                    pitch=edge_pitch
                )
                
                # 添加超时控制
                await asyncio.wait_for(
                    communicate.save(str(speech_file_path)), 
                    timeout=30.0
                )
                
                # 验证文件生成
                if speech_file_path.exists() and speech_file_path.stat().st_size > 1000:
                    duration = time.time() - start_time
                    print(f"✅ Edge TTS库成功: 文件大小 {speech_file_path.stat().st_size} bytes, 耗时 {duration:.2f}s")
                    return True
                else:
                    print(f"⚠️ Edge TTS库生成文件过小或不存在，重试...")
                    
            except Exception as e:
                print(f"❌ Edge TTS库尝试 {attempt + 1} 失败: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"   等待2秒后重试...")
                    await asyncio.sleep(2)
        
        return False
    
    # 尝试方法1: edge-tts库 (避免在已运行的事件循环中使用asyncio.run)
    try:
        # 检查是否已有运行的事件循环
        try:
            current_loop = asyncio.get_running_loop()
            print("⚠️ 检测到运行的事件循环，使用新线程执行Edge TTS")
            # 在新线程中运行asyncio.run以避免事件循环冲突
            import threading
            import concurrent.futures
            
            def run_edge_tts():
                return asyncio.run(async_edge_tts_lib())
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_edge_tts)
                success = future.result(timeout=30)  # 30秒超时
                
            if success:
                print("✅ Edge TTS库成功生成音频")
                return True
        except RuntimeError:
            # 没有运行的事件循环，可以安全使用asyncio.run
            print("🔄 使用asyncio.run执行Edge TTS")
            success = asyncio.run(async_edge_tts_lib())
            if success:
                print("✅ Edge TTS库成功生成音频")
                return True
    except Exception as e:
        print(f"❌ Edge TTS库失败: {str(e)}")
        success = False
    
    # 方法2: 回退到自定义Edge TTS方法
    print(f"🔄 Edge TTS库失败，尝试自定义方法...")
    success = custom_edge_tts_fallback(text, save_path, voice, edge_rate, edge_pitch)
    
    if success:
        duration = time.time() - start_time
        print(f"✅ Edge TTS最终成功 (自定义方法), 总耗时 {duration:.2f}s")
        return
    
    # 方法3: 最后的回退 - 简化参数重试
    print(f"🔄 自定义方法也失败，尝试简化参数...")
    simple_success = custom_edge_tts_fallback(
        text, 
        save_path, 
        "zh-CN-XiaoxiaoNeural",  # 使用最稳定的语音
        "+0%",  # 默认速率
        "+0Hz"  # 默认音调
    )
    
    if simple_success:
        duration = time.time() - start_time
        print(f"✅ Edge TTS最终成功 (简化参数), 总耗时 {duration:.2f}s")
        return
    
    # 所有方法都失败
    duration = time.time() - start_time
    error_msg = f"❌ Edge TTS所有方法都失败, 总耗时 {duration:.2f}s"
    print(error_msg)
    raise Exception(error_msg)

if __name__ == "__main__":
    # 测试用例
    test_text = "大家好，这是Edge TTS优化版本的测试。我们现在有了多重回退机制，确保配音功能的稳定性。"
    test_output = "test_edge_optimized.wav"
    
    print("🧪 Edge TTS 优化版本测试")
    print("="*50)
    print(f"测试文本: {test_text}")
    print(f"输出文件: {test_output}")
    print()
    
    try:
        edge_tts(test_text, test_output)
        print("\n✅ Edge TTS 优化版本测试成功！")
        
        # 验证生成的文件
        if Path(test_output).exists():
            size = Path(test_output).stat().st_size
            print(f"📁 生成文件: {Path(test_output).absolute()}")
            print(f"📊 文件大小: {size:,} 字节 ({size/1024:.1f} KB)")
        
    except Exception as e:
        print(f"\n❌ Edge TTS 优化版本测试失败: {e}")
