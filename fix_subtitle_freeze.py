#!/usr/bin/env python3
"""
字幕生成卡死问题修复脚本
临时禁用Flask自动重载和AI模型，确保工作流正常运行
"""
import os
import sys
from pathlib import Path

def fix_flask_reload_issue():
    """修复Flask自动重载导致的字幕生成卡死问题"""
    
    project_root = Path(__file__).parent
    
    # 1. 设置环境变量禁用自动重载
    env_vars = {
        'FLASK_ENV': 'production',  # 切换到生产模式
        'FLASK_DEBUG': '0',         # 禁用调试模式
        'HF_HUB_DISABLE_SYMLINKS_WARNING': '1',  # 禁用symlinks警告
        'HF_HUB_CACHE': str(project_root / 'cache' / 'huggingface'),  # 设置缓存目录
        'TRANSFORMERS_CACHE': str(project_root / 'cache' / 'transformers')
    }
    
    print("🔧 设置环境变量...")
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    # 2. 创建缓存目录
    cache_dir = project_root / 'cache'
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / 'huggingface').mkdir(exist_ok=True)
    (cache_dir / 'transformers').mkdir(exist_ok=True)
    
    print("📁 缓存目录创建完成")
    
    # 3. 创建临时配置文件禁用AI功能
    temp_config = {
        "semantic_analysis": {
            "enabled": False,  # 临时禁用语义分析
            "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "use_local_fallback": True  # 使用本地回退方案
        },
        "subtitle_generation": {
            "mode": "basic",  # 使用基础模式
            "ai_enhanced": False  # 禁用AI增强
        }
    }
    
    config_file = project_root / 'flask_backend' / 'config_data' / 'temp_fix_config.json'
    config_file.parent.mkdir(exist_ok=True)
    
    import json
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(temp_config, f, indent=2, ensure_ascii=False)
    
    print("⚙️ 临时配置文件已创建")
    
    print("\n✅ 修复完成！请重启Flask服务器:")
    print("   1. 停止当前Flask服务")
    print("   2. 运行: python flask_backend/unified_app.py")
    print("   3. 或使用任务: '启动统一Flask后端服务器 (推荐)'")

if __name__ == '__main__':
    fix_flask_reload_issue()