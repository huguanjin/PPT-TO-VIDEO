"""
Flask应用工厂
"""
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from pathlib import Path

def create_app(config_class=None):
    """创建Flask应用实例"""
    
    # 创建Flask应用
    app = Flask(__name__)
    
    # 加载配置
    if config_class:
        app.config.from_object(config_class)
    else:
        from config.settings import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # 配置CORS
    CORS(app, origins=['*'], supports_credentials=True)
    
    # 配置请求限制
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # 配置日志
    setup_logging(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 创建必要的目录
    create_directories(app)
    
    return app

def setup_logging(app):
    """配置日志系统"""
    if not app.debug:
        # 生产环境日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    else:
        # 开发环境日志配置
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s'
        )

def register_blueprints(app):
    """注册蓝图"""
    
    # 导入原有蓝图
    from app.api.common import bp as common_bp
    from app.api.pptist import bp as pptist_bp
    from app.api.workflow import bp as workflow_bp
    from app.api.project import bp as project_bp
    from app.api.config import bp as config_bp
    from app.api.tts import bp as tts_bp
    from app.api.download import bp as download_bp
    from app.api.pptist_export import pptist_export_bp
    from app.api.workspace import workspace_bp
    
    # 导入增强的API蓝图
    try:
        from app.api.enhanced_workflow import bp as enhanced_workflow_bp
        from app.api.enhanced_tts import bp as enhanced_tts_bp
        from app.api.enhanced_workspace import bp as enhanced_workspace_bp
        enhanced_apis_available = True
    except ImportError as e:
        print(f"Warning: 增强的API模块导入失败: {e}")
        enhanced_apis_available = False
    
    # 注册原有蓝图
    app.register_blueprint(common_bp)
    app.register_blueprint(pptist_bp, url_prefix='/api/pptist')
    app.register_blueprint(workflow_bp, url_prefix='/api/workflow')
    app.register_blueprint(project_bp, url_prefix='/api/project')  # 恢复为单数
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(tts_bp, url_prefix='/api/tts')
    app.register_blueprint(download_bp, url_prefix='/api/download')
    app.register_blueprint(pptist_export_bp, url_prefix='/api/pptist_export')
    app.register_blueprint(workspace_bp, url_prefix='/api/workspace')
    
    # 注册增强的API蓝图（如果可用）
    if enhanced_apis_available:
        # 注册增强的工作流API（替代原有工作流的高级功能）
        app.register_blueprint(enhanced_workflow_bp, url_prefix='/api/enhanced_workflow')
        # 注册增强的TTS API（多引擎支持）
        app.register_blueprint(enhanced_tts_bp, url_prefix='/api/enhanced_tts')
        # 注册增强的工作空间API（PPTist项目持久化）
        app.register_blueprint(enhanced_workspace_bp, url_prefix='/api/enhanced_workspace')
        
        print("✅ 增强的API模块已成功注册:")
        print("   - /api/enhanced_workflow/* - 完整工作流功能")
        print("   - /api/enhanced_tts/* - 多引擎TTS试听功能")
        print("   - /api/enhanced_workspace/* - PPTist项目持久化功能")
    else:
        print("⚠️  增强的API模块不可用，使用原有的基础功能")

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            'success': False,
            'error': 'Bad Request',
            'message': '请求参数错误'
        }, 400
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': 'Not Found',
            'message': '请求的资源不存在'
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            'success': False,
            'error': 'Internal Server Error',
            'message': '服务器内部错误'
        }, 500
    
    @app.errorhandler(413)
    def payload_too_large(error):
        return {
            'success': False,
            'error': 'Payload Too Large',
            'message': '上传文件过大'
        }, 413

def create_directories(app):
    """创建必要的目录"""
    # 使用Flask配置中的目录路径，而不是当前工作目录
    from config.settings import Config
    
    # 从配置中获取具体的目录路径
    directories = {
        app.config.get('OUTPUT_FOLDER', Config.OUTPUT_FOLDER): 'output',
        app.config.get('UPLOAD_FOLDER', Config.UPLOAD_FOLDER): 'uploads', 
        app.config.get('TEMP_FOLDER', Config.TEMP_FOLDER): 'temp',
        Config.LOG_FILE.parent: 'logs'
    }
    
    for dir_path, desc in directories.items():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ 创建目录: {dir_path} ({desc})")
