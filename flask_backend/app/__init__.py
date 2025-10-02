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
    
    # 配置请求限制（放宽限制以支持前端频繁操作）
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["10000 per day", "1000 per hour"]
    )
    
    # 配置日志
    setup_logging(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 创建必要的目录
    create_directories(app)
    
    # 初始化Netflix监控系统 (Phase 2)
    initialize_netflix_monitoring(app)
    
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
    from app.api.unified_tts import bp as unified_tts_bp
    from app.api.download import bp as download_bp
    from app.api.pptist_export import pptist_export_bp
    from app.api.workspace import workspace_bp
    
    # 导入VideoLingo集成蓝图
    videolingo_bp = None
    try:
        from app.api.videolingo import bp as videolingo_bp
        print("✅ videolingo集成模块导入成功")
    except ImportError as e:
        print(f"❌ videolingo集成模块导入失败: {e}")
    except Exception as e:
        print(f"❌ videolingo集成模块加载错误: {e}")

    # 导入Phase 3智能对齐API蓝图
    phase3_bp = None
    try:
        from app.api.phase3_alignment import bp as phase3_bp
        print("✅ Phase 3智能对齐API模块导入成功")
    except ImportError as e:
        print(f"❌ Phase 3智能对齐API模块导入失败: {e}")
    except Exception as e:
        print(f"❌ Phase 3智能对齐API模块加载错误: {e}")

    # 导入增强的API蓝图（带详细错误处理）
    enhanced_apis_available = True
    enhanced_workflow_bp = None
    enhanced_tts_bp = None
    enhanced_workspace_bp = None
    
    try:
        from app.api.enhanced_workflow import bp as enhanced_workflow_bp
        print("✅ enhanced_workflow模块导入成功")
    except ImportError as e:
        print(f"❌ enhanced_workflow模块导入失败: {e}")
        enhanced_apis_available = False
    except Exception as e:
        print(f"❌ enhanced_workflow模块加载错误: {e}")
        enhanced_apis_available = False
    
    try:
        from app.api.enhanced_tts import bp as enhanced_tts_bp
        print("✅ enhanced_tts模块导入成功")
    except ImportError as e:
        print(f"❌ enhanced_tts模块导入失败: {e}")
        enhanced_apis_available = False
    except Exception as e:
        print(f"❌ enhanced_tts模块加载错误: {e}")
        enhanced_apis_available = False
    
    try:
        from app.api.enhanced_workspace import bp as enhanced_workspace_bp
        print("✅ enhanced_workspace模块导入成功")
    except ImportError as e:
        print(f"❌ enhanced_workspace模块导入失败: {e}")
        enhanced_apis_available = False
    except Exception as e:
        print(f"❌ enhanced_workspace模块加载错误: {e}")
        enhanced_apis_available = False
    
    # 导入智能字幕API
    smart_subtitle_bp = None
    try:
        from app.api.smart_subtitle_api import smart_subtitle_bp
        print("✅ smart_subtitle_api模块导入成功")
    except ImportError as e:
        print(f"❌ smart_subtitle_api模块导入失败: {e}")
    except Exception as e:
        print(f"❌ smart_subtitle_api模块加载错误: {e}")
    
    # 导入AI配置API
    ai_config_api = None
    try:
        from app.api.ai_config_api import ai_config_api
        print("✅ ai_config_api模块导入成功")
    except ImportError as e:
        print(f"❌ ai_config_api模块导入失败: {e}")
    except Exception as e:
        print(f"❌ ai_config_api模块加载错误: {e}")
    
    # 导入AI连接测试API
    ai_test_bp = None
    try:
        from app.api.ai_config_test_api import ai_test_bp
        print("✅ ai_config_test_api模块导入成功")
    except ImportError as e:
        print(f"❌ ai_config_test_api模块导入失败: {e}")
    except Exception as e:
        print(f"❌ ai_config_test_api模块加载错误: {e}")
    
    # 导入提示词管理API
    prompt_api = None
    try:
        from app.api.prompt_api import prompt_api
        print("✅ prompt_api模块导入成功")
    except ImportError as e:
        print(f"❌ prompt_api模块导入失败: {e}")
    except Exception as e:
        print(f"❌ prompt_api模块加载错误: {e}")
    
    # 导入自定义AI模型管理API
    custom_ai_api = None
    try:
        from app.api.custom_ai_api import custom_ai_api
        print("✅ custom_ai_api模块导入成功")
    except ImportError as e:
        print(f"❌ custom_ai_api模块导入失败: {e}")
    except Exception as e:
        print(f"❌ custom_ai_api模块加载错误: {e}")
    
    # 导入Netflix字幕API (Phase 2)
    netflix_subtitle_bp = None
    try:
        from app.api.netflix_subtitle_api import bp as netflix_subtitle_bp
        print("✅ netflix_subtitle_api模块导入成功")
    except ImportError as e:
        print(f"❌ netflix_subtitle_api模块导入失败: {e}")
    except Exception as e:
        print(f"❌ netflix_subtitle_api模块加载错误: {e}")
    
    # 导入模板API
    template_api = None
    try:
        from app.api.template_api import template_api
        print("✅ template_api模块导入成功")
    except ImportError as e:
        print(f"❌ template_api模块导入失败: {e}")
    except Exception as e:
        print(f"❌ template_api模块加载错误: {e}")
    
    # 注册原有蓝图
    app.register_blueprint(common_bp)
    app.register_blueprint(pptist_bp, url_prefix='/api/pptist')
    app.register_blueprint(workflow_bp, url_prefix='/api/workflow')
    app.register_blueprint(project_bp, url_prefix='/api/project')  # 恢复为单数
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(tts_bp, url_prefix='/api/tts')
    app.register_blueprint(unified_tts_bp)  # unified_tts已在蓝图内定义url_prefix
    app.register_blueprint(download_bp, url_prefix='/api/download')
    app.register_blueprint(pptist_export_bp, url_prefix='/api/pptist_export')
    app.register_blueprint(workspace_bp, url_prefix='/api/workspace')
    
    # 注册批量导入API蓝图（前端批量导出功能）
    try:
        from flask_backend.api.batch_import import batch_import_bp
        app.register_blueprint(batch_import_bp)
        print("✅ batch_import蓝图注册成功: /api/import-slides-batch")
    except ImportError as e:
        print(f"❌ batch_import蓝图导入失败: {e}")
    except Exception as e:
        print(f"❌ batch_import蓝图注册失败: {e}")
    
    # 注册VideoLingo集成蓝图
    if videolingo_bp is not None:
        try:
            app.register_blueprint(videolingo_bp, url_prefix='/api/videolingo')
            print("✅ videolingo蓝图注册成功: /api/videolingo/*")
            
            # 尝试注册VideoLingo的具体API
            from app.api.videolingo import register_videolingo_apis
            register_videolingo_apis(app)
            
        except Exception as e:
            print(f"❌ videolingo蓝图注册失败: {e}")
    
    # 注册Phase 3智能对齐API蓝图
    if phase3_bp is not None:
        try:
            app.register_blueprint(phase3_bp)
            print("✅ Phase 3智能对齐API蓝图注册成功: /api/phase3/*")
        except Exception as e:
            print(f"❌ Phase 3智能对齐API蓝图注册失败: {e}")
    
    # 注册智能字幕API
    if smart_subtitle_bp is not None:
        try:
            app.register_blueprint(smart_subtitle_bp)
            print("✅ smart_subtitle蓝图注册成功: /api/smart-subtitle/*")
        except Exception as e:
            print(f"❌ smart_subtitle蓝图注册失败: {e}")
    
    # 注册AI配置API
    if ai_config_api is not None:
        try:
            app.register_blueprint(ai_config_api)
            print("✅ ai_config_api蓝图注册成功: /api/ai-config/*")
        except Exception as e:
            print(f"❌ ai_config_api蓝图注册失败: {e}")
    
    # 注册AI连接测试API
    if ai_test_bp is not None:
        try:
            app.register_blueprint(ai_test_bp, url_prefix='/api/ai')
            print("✅ ai_test_bp蓝图注册成功: /api/ai/*")
        except Exception as e:
            print(f"❌ ai_test_bp蓝图注册失败: {e}")
    
    # 注册提示词管理API
    if prompt_api is not None:
        try:
            app.register_blueprint(prompt_api)
            print("✅ prompt_api蓝图注册成功: /api/prompts/*")
        except Exception as e:
            print(f"❌ prompt_api蓝图注册失败: {e}")
    
    # 注册自定义AI模型管理API
    if custom_ai_api is not None:
        try:
            app.register_blueprint(custom_ai_api)
            print("✅ custom_ai_api蓝图注册成功: /api/custom-ai/*")
        except Exception as e:
            print(f"❌ custom_ai_api蓝图注册失败: {e}")
    
    # 注册Netflix字幕API (Phase 2)
    if netflix_subtitle_bp is not None:
        try:
            app.register_blueprint(netflix_subtitle_bp)
            print("✅ netflix_subtitle_api蓝图注册成功: /api/netflix-subtitle/*")
        except Exception as e:
            print(f"❌ netflix_subtitle_api蓝图注册失败: {e}")
    
    # 注册模板API
    if template_api is not None:
        try:
            app.register_blueprint(template_api)
            print("✅ template_api蓝图注册成功: /data/*, /img/*, /templates/*")
        except Exception as e:
            print(f"❌ template_api蓝图注册失败: {e}")
    
    # 手动分割API已通过直接路由注册
    
    # 注册增强的API蓝图（只注册成功导入的）
    enhanced_count = 0
    
    if enhanced_workflow_bp is not None:
        try:
            app.register_blueprint(enhanced_workflow_bp, url_prefix='/api/enhanced_workflow')
            print("✅ enhanced_workflow蓝图注册成功: /api/enhanced_workflow/*")
            enhanced_count += 1
        except Exception as e:
            print(f"❌ enhanced_workflow蓝图注册失败: {e}")
    
    if enhanced_tts_bp is not None:
        try:
            app.register_blueprint(enhanced_tts_bp, url_prefix='/api/enhanced_tts')
            print("✅ enhanced_tts蓝图注册成功: /api/enhanced_tts/*")
            enhanced_count += 1
        except Exception as e:
            print(f"❌ enhanced_tts蓝图注册失败: {e}")
    
    if enhanced_workspace_bp is not None:
        try:
            app.register_blueprint(enhanced_workspace_bp, url_prefix='/api/enhanced_workspace')
            print("✅ enhanced_workspace蓝图注册成功: /api/enhanced_workspace/*")
            enhanced_count += 1
        except Exception as e:
            print(f"❌ enhanced_workspace蓝图注册失败: {e}")
    
    if enhanced_count > 0:
        print(f"✅ 成功注册 {enhanced_count} 个增强API模块")
    else:
        print("⚠️  没有增强的API模块可用，使用原有的基础功能")
    
    # 添加静态文件服务支持
    from flask import send_from_directory, Response
    import mimetypes
    
    @app.route('/temp/<path:filename>')
    def serve_temp_files(filename):
        """提供临时文件访问，如音频预览文件"""
        temp_dir = Path(app.root_path).parent / "temp"
        file_path = temp_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists():
            return {'success': False, 'message': '文件不存在'}, 404
            
        # 确定MIME类型
        mime_type = None
        if filename.lower().endswith('.wav'):
            mime_type = 'audio/wav'
        elif filename.lower().endswith('.mp3'):
            mime_type = 'audio/mpeg'
        elif filename.lower().endswith('.ogg'):
            mime_type = 'audio/ogg'
        else:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
        # 发送文件并设置正确的MIME类型
        response = send_from_directory(temp_dir, filename)
        if mime_type:
            response.headers['Content-Type'] = mime_type
        
        # 添加CORS头部以支持跨域访问
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
    
    # 添加音频测试页面
    @app.route('/audio-test')
    def audio_test():
        """音频播放测试页面"""
        test_html_path = Path(app.root_path).parent / "test_audio_player.html"
        if test_html_path.exists():
            return send_from_directory(Path(app.root_path).parent, "test_audio_player.html")
        else:
            return {'success': False, 'message': '测试页面不存在'}, 404
    
    # 添加调试页面
    @app.route('/debug-audio')
    def debug_audio():
        """音频播放调试页面"""
        debug_html_path = Path(app.root_path).parent / "debug_audio.html"
        if debug_html_path.exists():
            return send_from_directory(Path(app.root_path).parent, "debug_audio.html")
        else:
            return {'success': False, 'message': '调试页面不存在'}, 404
    
    print("✅ 静态文件服务已启用: /temp/*")

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

def initialize_netflix_monitoring(app):
    """初始化Netflix监控系统"""
    try:
        # 导入监控管理器
        import sys
        from pathlib import Path
        
        # 添加项目根目录到路径
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from ..utils.netflix_monitoring_manager import init_flask_monitoring
        
        # 初始化监控
        success = init_flask_monitoring(app, project_root)
        
        if success:
            app.logger.info("✅ Netflix监控系统初始化成功")
        else:
            app.logger.warning("⚠️ Netflix监控系统初始化失败，但应用将继续运行")
        
        return success
        
    except ImportError as e:
        app.logger.warning(f"Netflix监控模块不可用: {e}")
        return False
    except Exception as e:
        app.logger.error(f"Netflix监控系统初始化错误: {e}")
        return False
