#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字幕单行模式转换工具
将多行字幕转换为连续的单行字幕
"""

import re
from pathlib import Path

def parse_srt_time(time_str):
    """解析SRT时间格式为毫秒"""
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

def format_srt_time(ms):
    """将毫秒格式化为SRT时间"""
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    ms = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def convert_to_single_line(input_file, output_file):
    """将多行字幕转换为单行字幕"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析字幕条目
    entries = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\Z)', content, re.DOTALL)
    
    new_entries = []
    new_id = 1
    
    for entry_id, start_time, end_time, text in entries:
        text = text.strip()
        
        # 检查是否包含换行符
        if '\n' in text:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) > 1:
                print(f"转换条目 {entry_id}: {len(lines)} 行")
                
                # 计算每行的时长分配
                start_ms = parse_srt_time(start_time)
                end_ms = parse_srt_time(end_time)
                total_duration = end_ms - start_ms
                
                # 按字符数比例分配时间
                char_counts = [len(line) for line in lines]
                total_chars = sum(char_counts)
                
                current_start = start_ms
                
                for i, line in enumerate(lines):
                    # 计算这一行的时长
                    if i == len(lines) - 1:  # 最后一行
                        line_end = end_ms
                    else:
                        line_duration = int(total_duration * char_counts[i] / total_chars)
                        line_duration = max(line_duration, 1000)  # 最小1秒
                        line_end = min(current_start + line_duration, end_ms)
                    
                    # 添加新的字幕条目
                    new_entries.append({
                        'id': new_id,
                        'start': format_srt_time(current_start),
                        'end': format_srt_time(line_end),
                        'text': line
                    })
                    
                    print(f"  第 {i+1} 行: '{line}' ({format_srt_time(current_start)} --> {format_srt_time(line_end)})")
                    
                    current_start = line_end
                    new_id += 1
            else:
                # 单行，直接添加
                new_entries.append({
                    'id': new_id,
                    'start': start_time,
                    'end': end_time,
                    'text': text
                })
                new_id += 1
        else:
            # 没有换行符，直接添加
            new_entries.append({
                'id': new_id,
                'start': start_time,
                'end': end_time,
                'text': text
            })
            new_id += 1
    
    # 生成新的SRT内容
    srt_content = []
    for entry in new_entries:
        srt_content.append(f"{entry['id']}")
        srt_content.append(f"{entry['start']} --> {entry['end']}")
        srt_content.append(entry['text'])
        srt_content.append("")
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    print(f"\n转换完成！")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"原始条目数: {len(entries)}")
    print(f"转换后条目数: {len(new_entries)}")

def main():
    """主函数"""
    input_file = Path("flask_backend/output/subtitles/combined_subtitle_multiline_enhanced.srt")
    output_file = Path("flask_backend/output/subtitles/combined_subtitle_single_line_demo.srt")
    
    if not input_file.exists():
        print(f"错误：输入文件不存在 - {input_file}")
        return
    
    print("=" * 50)
    print("字幕单行模式转换演示")
    print("=" * 50)
    
    convert_to_single_line(input_file, output_file)
    
    print("\n" + "=" * 50)
    print("转换演示完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()