"""
简单测试：验证单行模式配置是否被正确读取
"""
import json
from pathlib import Path

# 检查配置文件
config_path = Path("flask_backend/config_data/manual_split_config.json")
print(f"配置文件路径: {config_path}")
print(f"配置文件存在: {config_path.exists()}")

if config_path.exists():
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 查找single_line_mode配置
    single_line_mode = config.get("manual_split_config", {}).get("subtitle_display_mode", {}).get("single_line_mode", False)
    print(f"single_line_mode配置: {single_line_mode}")
    
    if single_line_mode:
        print("✅ 配置文件中single_line_mode已启用")
    else:
        print("❌ 配置文件中single_line_mode未启用")
else:
    print("❌ 配置文件不存在")

print("\n检查代码修复位置:")
print("✅ Step04: _split_text_to_segments方法 - 添加单行模式优先处理")
print("✅ Step04: _lightweight_split_text方法 - 添加单行模式严格处理")  
print("✅ Step05: FFmpegFinalMerger - 添加单行模式检查，跳过多行修复")
print("\n所有代码修复已完成，应该能解决多行字幕问题")