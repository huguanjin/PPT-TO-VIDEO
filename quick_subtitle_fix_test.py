#!/usr/bin/env python3
"""
快速字幕修复测试脚本
使用现有的输出文件快速测试字幕配置修复效果
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import time

def quick_subtitle_fix_test():
    """快速测试字幕修复效果"""
    print("🔧 快速字幕修复测试")
    print("=" * 40)
    
    # 设置路径
    output_dir = Path("flask_backend/output")
    
    # 查找视频和字幕文件
    final_dir = output_dir / "final"
    subtitle_file = output_dir / "subtitles" / "combined_subtitle.srt"
    
    if not final_dir.exists() or not subtitle_file.exists():
        print("❌ 未找到必需的文件")
        return
    
    video_files = list(final_dir.glob("*.mp4"))
    if not video_files:
        print("❌ 未找到视频文件")
        return
    
    video_file = video_files[0]
    print(f"📹 使用视频: {video_file.name}")
    print(f"📝 使用字幕: {subtitle_file.name}")
    
    # 创建测试输出目录
    test_dir = output_dir / "quick_fix_test"
    test_dir.mkdir(exist_ok=True)
    
    # 测试不同字体大小
    font_sizes = [20, 24, 28]  # 重点测试24px（Netflix标准）
    
    for font_size in font_sizes:
        print(f"\n🔤 测试字体大小: {font_size}px")
        
        output_file = test_dir / f"fixed_subtitle_{font_size}px.mp4"
        
        # 使用简化的FFmpeg命令
        subtitle_path_fixed = str(subtitle_file).replace('\\', '/')
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_file),
            '-vf', f"subtitles={subtitle_path_fixed}:force_style='FontSize={font_size},FontName=Microsoft YaHei,PrimaryColour=&HFFFFFF'",
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-preset', 'ultrafast',  # 快速预设
            '-t', '30',  # 只处理前30秒
            str(output_file)
        ]
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            elapsed_time = time.time() - start_time
            
            if result.returncode == 0 and output_file.exists():
                file_size = output_file.stat().st_size
                print(f"✅ 成功: {output_file.name} ({file_size//1024//1024}MB, {elapsed_time:.1f}s)")
            else:
                print(f"❌ 失败: {result.stderr[:100]}...")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ 超时")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print(f"\n📂 测试文件保存在: {test_dir}")
    print("💡 建议: 对比观看不同字体大小的效果，选择最合适的")
    
    # 输出当前配置信息
    metadata_file = output_dir / "subtitles" / "subtitles_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            current_font_size = metadata.get('subtitle_config', {}).get('smart_processing', {}).get('font_size', '未知')
            print(f"\n📋 当前配置中的字体大小: {current_font_size}px")
            print("🎯 如果24px效果最佳，说明修复生效了！")
        except Exception as e:
            print(f"⚠️ 无法读取当前配置: {e}")

if __name__ == "__main__":
    quick_subtitle_fix_test()