#!/usr/bin/env python3
"""
轻量级Flask服务器启动脚本
专门用于解决字幕生成卡死问题，禁用AI模型加载
"""
import os
import sys
from pathlib import Path

# 设置环境变量（在导入任何模块之前）
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['AI_MODELS_DISABLED'] = '1'  # 禁用AI模型标志

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app
from config.settings import ProductionConfig

def main():
    """轻量级Flask应用启动"""
    print("🚀 PPT转视频工具 - 轻量级模式启动")
    print("⚠️  AI功能已禁用，专注于核心工作流")
    
    # 创建Flask应用（生产模式）
    app = create_app(ProductionConfig)
    
    # 禁用自动重载和调试模式
    print("\n" + "="*60)
    print("🎥 PPT转视频工具 - 轻量级Flask服务")
    print("="*60)
    print(f"📱 服务器地址: http://localhost:5000")
    print(f"📖 API文档: http://localhost:5000/docs")
    print(f"🔗 健康检查: http://localhost:5000/health")
    print(f"⚡ 模式: 轻量级（无AI模型）")
    print("="*60)
    
    # 启动服务器（无重载）
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,        # 禁用调试模式
        use_reloader=False, # 禁用自动重载
        threaded=True
    )

if __name__ == '__main__':
    main()