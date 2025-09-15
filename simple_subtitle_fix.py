#!/usr/bin/env python3
"""
字幕大小简单修复脚本
直接基于现有最终视频重新处理字幕，修复字幕过大问题
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import time
import shutil

def simple_subtitle_size_fix():
    """简单字幕大小修复 - 基于现有最终视频"""
    print("🔧 简单字幕大小修复")
    print("=" * 50)
    
    # 设置路径
    project_root = Path(__file__).parent
    output_dir = project_root / "flask_backend" / "output"
    
    if not output_dir.exists():
        print("❌ 输出目录不存在")
        return False
    
    # 1. 检查必需文件
    final_dir = output_dir / "final"
    subtitle_file = output_dir / "subtitles" / "combined_subtitle.srt"
    
    print("📁 检查文件...")
    
    if not final_dir.exists() or not subtitle_file.exists():
        print("❌ 未找到最终视频目录或字幕文件")
        return False
    
    # 查找现有的最终视频
    video_files = list(final_dir.glob("*.mp4"))
    if not video_files:
        print("❌ 未找到最终视频文件")
        return False
    
    # 使用最新的视频文件（但排除已修复的文件）
    original_videos = [v for v in video_files if "fixed_" not in v.name]
    if not original_videos:
        print("⚠️ 只找到已修复的视频文件")
        original_videos = video_files
    
    video_file = sorted(original_videos, key=lambda x: x.stat().st_mtime)[-1]
    
    print(f"✅ 使用视频: {video_file.name}")
    print(f"✅ 字幕文件: {subtitle_file.name}")
    
    # 2. 读取字幕配置
    metadata_file = output_dir / "subtitles" / "subtitles_metadata.json"
    font_size = 24  # 修复后的字体大小
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            original_font_size = metadata.get('subtitle_config', {}).get('smart_processing', {}).get('font_size', 24)
            print(f"📋 原始字体大小: {original_font_size}px")
            print(f"📋 修复后字体大小: {font_size}px")
        except Exception as e:
            print(f"⚠️ 读取配置失败: {e}")
    
    # 3. 从原视频中移除字幕，重新添加修复后的字幕
    print("\\n🎬 重新处理字幕...")
    
    # 生成临时无字幕视频
    temp_video = final_dir / "temp_no_subtitle.mp4"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = final_dir / f"fixed_subtitle_{timestamp}.mp4"
    
    # Step 1: 如果原视频包含字幕轨道，先提取无字幕版本
    print("🔄 Step 1: 处理原视频...")
    
    # 直接复制视频流和音频流，不处理字幕
    copy_cmd = [
        'ffmpeg', '-y',
        '-i', str(video_file),
        '-c', 'copy',
        '-sn',  # 不包含字幕流
        str(temp_video)
    ]
    
    try:
        result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            # 如果复制失败，直接使用原视频
            print("⚠️ 视频复制失败，直接使用原视频")
            temp_video = video_file
    except Exception as e:
        print(f"⚠️ 视频复制异常，直接使用原视频: {e}")
        temp_video = video_file
    
    # Step 2: 添加修复后的字幕
    print("🔄 Step 2: 添加修复后字幕...")
    
    subtitle_path_fixed = str(subtitle_file).replace('\\', '/')
    
    add_subtitle_cmd = [
        'ffmpeg', '-y',
        '-i', str(temp_video),
        '-vf', f"subtitles={subtitle_path_fixed}:force_style='FontSize={font_size},FontName=Microsoft YaHei,PrimaryColour=&HFFFFFF'",
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-preset', 'medium',
        str(output_file)
    ]
    
    print(f"🚀 开始处理...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            add_subtitle_cmd, 
            capture_output=True, 
            text=True, 
            timeout=600  # 10分钟超时
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0 and output_file.exists():
            file_size = output_file.stat().st_size
            print(f"\\n✅ 修复成功!")
            print(f"   📁 输出文件: {output_file}")
            print(f"   📏 文件大小: {file_size//1024//1024}MB")
            print(f"   ⏱️  处理时间: {elapsed_time:.1f}秒")
            print(f"   🔤 修复后字体大小: {font_size}px")
            
            # 清理临时文件
            if temp_video != video_file and temp_video.exists():
                try:
                    temp_video.unlink()
                    print("🗑️ 已清理临时文件")
                except Exception:
                    pass
            
            return True
            
        else:
            print(f"\\n❌ 处理失败:")
            print(f"   返回码: {result.returncode}")
            if result.stderr:
                print(f"   错误信息: {result.stderr[:300]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\\n⏰ 处理超时")
        return False
    except Exception as e:
        print(f"\\n❌ 处理异常: {e}")
        return False
    finally:
        # 清理临时文件
        if temp_video != video_file and temp_video.exists():
            try:
                temp_video.unlink()
            except Exception:
                pass

def main():
    """主函数"""
    print("🎬 PPT转视频 - 简单字幕大小修复工具")
    print("=" * 60)
    
    # 检查FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("❌ FFmpeg不可用")
            return
    except Exception:
        print("❌ FFmpeg未安装或不在PATH中")
        return
    
    # 应用修复
    success = simple_subtitle_size_fix()
    
    if success:
        print("\\n🎉 字幕大小修复完成！")
        print("💡 建议:")
        print("   1. 播放修复后的视频，检查字幕大小是否合适")
        print("   2. 对比原视频和修复后视频的字幕效果")
        print("   3. 如果满意，可以使用修复后的视频作为最终版本")
    else:
        print("\\n❌ 修复失败")
        print("💡 请检查:")
        print("   1. 是否存在最终视频文件")
        print("   2. FFmpeg是否正常工作")
        print("   3. 字幕文件是否存在且格式正确")

if __name__ == "__main__":
    main()