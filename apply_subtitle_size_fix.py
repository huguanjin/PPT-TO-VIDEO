#!/usr/bin/env python3
"""
字幕大小修复应用脚本 v2.0
使用修复后的配置重新生成最终视频，解决字幕过大问题
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import time
import shutil

def apply_subtitle_size_fix():
    """应用字幕大小修复"""
    print("🔧 应用字幕大小修复")
    print("=" * 50)
    
    # 设置路径
    project_root = Path(__file__).parent
    output_dir = project_root / "flask_backend" / "output"
    
    if not output_dir.exists():
        print("❌ 输出目录不存在")
        return False
    
    # 1. 检查必需文件
    final_dir = output_dir / "final"
    video_clips_dir = output_dir / "video_clips"
    audios_dir = output_dir / "audios"
    subtitle_file = output_dir / "subtitles" / "combined_subtitle.srt"
    
    print("📁 检查文件...")
    
    if not subtitle_file.exists():
        print("❌ 字幕文件不存在")
        return False
    
    # 查找音频和视频文件
    audio_files = list(audios_dir.glob("combined_audio.*")) if audios_dir.exists() else []
    video_files = list(video_clips_dir.glob("combined_video.*")) if video_clips_dir.exists() else []
    
    if not audio_files or not video_files:
        print("❌ 未找到音频或视频源文件")
        print("   请确保工作流已完成前面的步骤")
        return False
    
    audio_file = audio_files[0]
    video_file = video_files[0]
    
    print(f"✅ 音频文件: {audio_file.name}")
    print(f"✅ 视频文件: {video_file.name}")
    print(f"✅ 字幕文件: {subtitle_file.name}")
    
    # 2. 读取字幕配置
    metadata_file = output_dir / "subtitles" / "subtitles_metadata.json"
    font_size = 24  # 默认使用24px（Netflix标准）
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            font_size = metadata.get('subtitle_config', {}).get('smart_processing', {}).get('font_size', 24)
            print(f"📋 使用配置文件中的字体大小: {font_size}px")
        except Exception as e:
            print(f"⚠️ 读取配置失败，使用默认24px: {e}")
    else:
        print("📋 使用默认字体大小: 24px")
    
    # 3. 生成修复后的视频
    print("\n🎬 生成修复后的最终视频...")
    
    # 确保输出目录存在
    final_dir.mkdir(exist_ok=True)
    
    # 生成输出文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = final_dir / f"fixed_final_video_{timestamp}.mp4"
    
    # 获取视频分辨率
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(video_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = stream.get('width', 1920)
                    height = stream.get('height', 1080)
                    print(f"📹 检测到视频分辨率: {width}x{height}")
                    break
        else:
            width, height = 1920, 1080
            print("📹 使用默认分辨率: 1920x1080")
    except Exception as e:
        width, height = 1920, 1080
        print(f"📹 分辨率检测失败，使用默认: 1920x1080 ({e})")
    
    # 构造FFmpeg命令
    subtitle_path_fixed = str(subtitle_file).replace('\\', '/')
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_file),
        '-i', str(audio_file),
        '-vf', (
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"subtitles={subtitle_path_fixed}:force_style='"
            f"FontSize={font_size},FontName=Microsoft YaHei,"
            f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,OutlineWidth=1,"
            f"ShadowColour=&H80000000,BorderStyle=1,Alignment=2'"
        ),
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-preset', 'medium',
        '-crf', '23',
        '-b:a', '128k',
        str(output_file)
    ]
    
    print(f"🚀 开始处理...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=600  # 10分钟超时
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0 and output_file.exists():
            file_size = output_file.stat().st_size
            print(f"\n✅ 修复成功!")
            print(f"   📁 输出文件: {output_file}")
            print(f"   📏 文件大小: {file_size//1024//1024}MB")
            print(f"   ⏱️  处理时间: {elapsed_time:.1f}秒")
            print(f"   🔤 字体大小: {font_size}px")
            
            # 备份原文件（如果存在）
            original_files = list(final_dir.glob("final_video_*.mp4"))
            if original_files:
                backup_dir = final_dir / "backup"
                backup_dir.mkdir(exist_ok=True)
                for original_file in original_files:
                    if "fixed_" not in original_file.name:
                        backup_path = backup_dir / original_file.name
                        try:
                            shutil.move(str(original_file), str(backup_path))
                            print(f"📦 原文件已备份: {backup_path}")
                        except Exception as e:
                            print(f"⚠️ 备份失败: {e}")
            
            return True
            
        else:
            print(f"\n❌ 处理失败:")
            print(f"   返回码: {result.returncode}")
            if result.stderr:
                print(f"   错误信息: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏰ 处理超时")
        return False
    except Exception as e:
        print(f"\n❌ 处理异常: {e}")
        return False

def main():
    """主函数"""
    print("🎬 PPT转视频 - 字幕大小修复工具 v2.0")
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
    success = apply_subtitle_size_fix()
    
    if success:
        print("\n🎉 字幕大小修复完成！")
        print("💡 建议:")
        print("   1. 播放修复后的视频，检查字幕大小是否合适")
        print("   2. 如果满意，可以删除backup目录中的原文件")
        print("   3. 下次运行工作流时，会自动使用修复后的配置")
    else:
        print("\n❌ 修复失败")
        print("💡 请检查:")
        print("   1. 是否已运行完整的工作流")
        print("   2. FFmpeg是否正常工作")
        print("   3. 输出目录中的文件是否完整")

if __name__ == "__main__":
    main()