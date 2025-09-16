#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动生成slides_metadata.json文件
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import re

def generate_slides_metadata():
    """从ppt_data.json生成slides_metadata.json"""
    project_root = Path(__file__).parent
    output_dir = project_root / "output"
    ppt_data_path = output_dir / "ppt_data.json"
    slides_dir = output_dir / "slides"
    slides_metadata_path = slides_dir / "slides_metadata.json"
    
    print("🔧 开始生成slides_metadata.json文件...")
    
    if not ppt_data_path.exists():
        print(f"❌ 找不到ppt_data.json文件: {ppt_data_path}")
        return False
    
    # 读取ppt_data.json
    print(f"📖 读取ppt_data.json: {ppt_data_path}")
    with open(ppt_data_path, 'r', encoding='utf-8') as f:
        ppt_data = json.load(f)
    
    # 将PPTist格式转换为标准格式
    print("🔄 转换为标准slides_metadata.json格式...")
    slides_data = {
        "total_slides": len(ppt_data.get("slides", [])),
        "parsing_completed": True,
        "parsing_timestamp": datetime.now().isoformat(),
        "source_file": "ppt_data.json",
        "source_type": "PPTist",
        "slides": []
    }
    
    for i, slide in enumerate(ppt_data.get("slides", []), 1):
        # 从PPTist content JSON中提取remark文本
        content_str = slide.get("content", "{}")
        try:
            content_json = json.loads(content_str)
            raw_remark = content_json.get("remark", "")
            # 使用正则表达式去除HTML标签，提取纯文本
            clean_remark = re.sub(r'<[^>]+>', '', raw_remark) if raw_remark else ""
        except:
            clean_remark = ""
        
        standard_slide = {
            "slide_number": i,
            "title": f"幻灯片 {i}",
            "image_file": slide.get("image", f"slide_{i:03d}.jpg"),
            "notes": clean_remark,
            "remark": clean_remark
        }
        slides_data["slides"].append(standard_slide)
        print(f"  📄 处理幻灯片 {i}: {standard_slide['image_file']}")
    
    # 确保slides目录存在
    slides_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存slides_metadata.json
    print(f"💾 保存slides_metadata.json: {slides_metadata_path}")
    with open(slides_metadata_path, 'w', encoding='utf-8') as f:
        json.dump(slides_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ slides_metadata.json生成成功!")
    print(f"   📊 幻灯片总数: {slides_data['total_slides']}")
    print(f"   📁 文件路径: {slides_metadata_path}")
    
    return True

if __name__ == "__main__":
    success = generate_slides_metadata()
    if success:
        print("\n🎉 slides_metadata.json文件生成完成!")
    else:
        print("\n💥 slides_metadata.json文件生成失败!")
        sys.exit(1)