#!/usr/bin/env python3
"""
字幕修复调试脚本
详细输出FFmpeg处理过程，帮助诊断问题
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import time

def debug_subtitle_fix():
    """调试字幕修复过程"""
    print("🔍 字幕修复调试")
    print("=" * 50)
    
    # 设置路径
    project_root = Path(__file__).parent
    output_dir = project_root / "flask_backend" / "output"
    
    # 检查文件
    final_dir = output_dir / "final"
    subtitle_file = output_dir / "subtitles" / "combined_subtitle.srt"
    
    if not final_dir.exists():
        print("❌ 最终视频目录不存在")
        return
    
    if not subtitle_file.exists():
        print("❌ 字幕文件不存在")
        return
    
    video_files = list(final_dir.glob("*.mp4"))
    if not video_files:
        print("❌ 未找到视频文件")
        return
    
    video_file = video_files[0]
    print(f"✅ 视频文件: {video_file}")
    print(f"✅ 字幕文件: {subtitle_file}")
    
    # 检查文件完整性
    print("\\n📊 文件信息:")
    print(f"   视频大小: {video_file.stat().st_size // 1024 // 1024}MB")
    print(f"   字幕大小: {subtitle_file.stat().st_size}bytes")
    
    # 检查字幕文件内容
    print("\\n📝 字幕文件内容（前5行）:")
    try:
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:5]
            for i, line in enumerate(lines, 1):
                print(f"   {i}: {line.strip()}")
    except Exception as e:
        print(f"   ❌ 读取字幕失败: {e}")
        return
    
    # 检查视频信息
    print("\\n📹 检查视频信息:")
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(video_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # 视频流信息
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    print(f"   视频编码: {stream.get('codec_name')}")
                    print(f"   分辨率: {stream.get('width')}x{stream.get('height')}")
                    print(f"   帧率: {stream.get('r_frame_rate')}")
                elif stream.get('codec_type') == 'audio':
                    print(f"   音频编码: {stream.get('codec_name')}")
                    print(f"   采样率: {stream.get('sample_rate')}")
            
            # 格式信息
            format_info = data.get('format', {})
            duration = format_info.get('duration', '未知')
            print(f"   时长: {duration}秒")
            
        else:
            print(f"   ❌ 获取视频信息失败: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ 检查视频信息异常: {e}")
    
    # 测试简单的FFmpeg命令
    print("\\n🧪 测试FFmpeg基本功能:")
    
    test_output = final_dir / "test_output.mp4"
    
    # 测试1: 简单复制
    print("   测试1: 视频流复制...")
    copy_cmd = ['ffmpeg', '-y', '-i', str(video_file), '-c', 'copy', '-t', '5', str(test_output)]
    
    try:
        result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("   ✅ 视频流复制成功")
            test_output.unlink()  # 清理
        else:
            print(f"   ❌ 视频流复制失败: {result.stderr[:100]}...")
    except Exception as e:
        print(f"   ❌ 视频流复制异常: {e}")
    
    # 测试2: 字幕处理
    print("   测试2: 字幕处理...")
    
    # 使用绝对路径和简化的字幕参数
    subtitle_path = str(subtitle_file).replace('\\', '\\\\')  # 转义反斜杠
    
    subtitle_cmd = [
        'ffmpeg', '-y',
        '-i', str(video_file),
        '-vf', f"subtitles='{subtitle_path}':force_style='FontSize=20'",
        '-c:v', 'libx264', '-preset', 'ultrafast',
        '-t', '10',  # 只处理前10秒
        str(test_output)
    ]
    
    try:
        result = subprocess.run(subtitle_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("   ✅ 字幕处理成功")
            if test_output.exists():
                size = test_output.stat().st_size
                print(f"      生成文件大小: {size // 1024 // 1024}MB")
                test_output.unlink()  # 清理
        else:
            print(f"   ❌ 字幕处理失败:")
            print(f"      返回码: {result.returncode}")
            print(f"      标准输出: {result.stdout[:200]}...")
            print(f"      错误输出: {result.stderr[:200]}...")
    except Exception as e:
        print(f"   ❌ 字幕处理异常: {e}")
    
    # 给出建议
    print("\\n💡 调试建议:")
    print("   1. 检查FFmpeg版本是否支持字幕滤镜")
    print("   2. 尝试使用不同的字幕文件路径格式")
    print("   3. 检查字幕文件编码是否为UTF-8")
    print("   4. 考虑使用外部字幕轨道而非硬编码字幕")

if __name__ == "__main__":
    debug_subtitle_fix()