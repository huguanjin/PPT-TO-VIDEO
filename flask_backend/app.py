"""
Flask应用主入口
PPT转视频工具后端API服务
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app
from config.settings import DevelopmentConfig

def main():
    """主函数"""
    # 创建Flask应用
    app = create_app(DevelopmentConfig)
    
    # 启动开发服务器
    if __name__ == '__main__':
        print("🚀 PPT转视频工具 Flask API 启动中...")
        print(f"📖 API文档: http://localhost:5000/docs")
        print(f"🔗 健康检查: http://localhost:5000/health")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )

if __name__ == '__main__':
    main()
