"""
统一的Flask应用启动脚本
整合了原有app.py和videolingo_integration_app.py的功能
"""
import os
import sys
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app
from config.settings import DevelopmentConfig, ProductionConfig

def main():
    """主函数 - 统一启动入口"""
    
    # 设置环境
    environment = os.getenv('FLASK_ENV', 'development')
    
    # 选择配置
    if environment == 'production':
        config = ProductionConfig
        print("🚀 生产模式启动")
    else:
        config = DevelopmentConfig
        print("🔧 开发模式启动")
    
    # 创建Flask应用
    app = create_app(config)
    
    # 配置日志
    if environment == 'production':
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    
    # 启动信息
    print("\n" + "="*60)
    print("🎥 PPT转视频工具 - 统一Flask后端服务")
    print("="*60)
    print(f"📱 服务器地址: http://localhost:5000")
    print(f"📖 API文档: http://localhost:5000/docs")
    print(f"🔗 健康检查: http://localhost:5000/health")
    print(f"🎯 VideoLingo集成: http://localhost:5000/api/videolingo/test")
    print(f"⚙️ 环境模式: {environment}")
    
    # 显示可用的API端点
    print("\n📋 主要API端点:")
    endpoints = [
        ("基础功能", [
            "GET  /health - 服务健康检查",
            "GET  /api/config - 配置管理",
            "GET  /api/workflow/status - 工作流状态",
        ]),
        ("PPTist集成", [
            "POST /api/pptist/import - PPT导入",
            "GET  /api/pptist_export/slides - 幻灯片导出",
            "POST /api/pptist_export/generate_video - 视频生成",
        ]),
        ("VideoLingo集成", [
            "GET  /api/videolingo/health - VideoLingo健康检查", 
            "GET  /api/videolingo/version - VideoLingo版本信息",
            "GET  /api/videolingo/test - VideoLingo测试界面",
        ]),
        ("TTS & 音频", [
            "GET  /api/tts/voices - 获取可用语音",
            "POST /api/tts/synthesize - 语音合成",
            "POST /api/tts/batch - 批量合成",
        ]),
        ("项目管理", [
            "GET  /api/project - 项目列表",
            "POST /api/project/create - 创建项目",
            "GET  /api/workspace/status - 工作空间状态",
        ])
    ]
    
    for category, apis in endpoints:
        print(f"\n  {category}:")
        for api in apis:
            print(f"    {api}")
    
    print("\n" + "="*60)
    
    try:
        # 启动开发服务器
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=(environment != 'production'),
            threaded=True,
            use_reloader=(environment != 'production')
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
