#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试配置加载问题
"""

import json
import sys
import os
from pathlib import Path

# 添加flask_backend路径
sys.path.insert(0, str(Path(__file__).parent / 'flask_backend'))

def debug_config_loading():
    """调试配置加载过程"""
    
    # 模拟SubtitleGenerator的初始化过程
    project_dir = Path(__file__).parent / 'flask_backend'
    print(f"项目目录: {project_dir}")
    
    # 1. 加载单行模式配置
    single_line_mode = False
    single_line_config = {}
    
    try:
        manual_config_path = project_dir / "config_data" / "manual_split_config.json"
        print(f"配置文件路径: {manual_config_path}")
        print(f"配置文件存在: {manual_config_path.exists()}")
        
        if manual_config_path.exists():
            with open(manual_config_path, 'r', encoding='utf-8') as f:
                manual_config = json.load(f)
            
            print("配置文件内容加载成功")
            
            display_mode = manual_config.get("manual_split_config", {}).get("subtitle_display_mode", {})
            print(f"display_mode: {display_mode}")
            
            single_line_mode = display_mode.get("single_line_mode", False)
            single_line_config = display_mode.get("time_allocation", {
                "method": "proportional",
                "based_on": "character_count",
                "min_line_duration": 1.0,
                "max_line_duration": 8.0
            })
            
            print(f"single_line_mode: {single_line_mode}")
            print(f"single_line_config: {single_line_config}")
            
            if single_line_mode:
                print("✅ 单行字幕模式已启用 - 多行字幕将被拆分为连续单行")
            else:
                print("📝 多行字幕模式 - 保持原有换行显示")
                
    except Exception as e:
        print(f"读取单行模式配置失败: {e}")
        single_line_mode = False
    
    print(f"\n最终结果:")
    print(f"single_line_mode = {single_line_mode}")
    print(f"类型: {type(single_line_mode)}")

if __name__ == "__main__":
    debug_config_loading()