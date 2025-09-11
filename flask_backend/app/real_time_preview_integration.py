"""
任务3.3: 实时预览功能 - 集成到Flask应用

将实时预览功能API注册到主Flask应用中
提供完整的路由和中间件支持
"""

from flask import Flask
from flask_socketio import SocketIO

def register_real_time_preview_apis(app: Flask, socketio = None):
    """
    注册实时预览相关的API路由
    
    Args:
        app: Flask应用实例
        socketio: SocketIO实例（可选，用于WebSocket支持）
    """
    
    # 导入API蓝图
    from .api.real_time_preview_api import bp as real_time_preview_bp
    from .api.real_time_preview_api import setup_websocket_events
    
    # 注册API蓝图
    app.register_blueprint(real_time_preview_bp)
    
    # 如果提供了SocketIO实例，设置WebSocket事件
    if socketio:
        setup_websocket_events(socketio)
        
        # 添加WebSocket错误处理
        @socketio.on_error_default
        def default_error_handler(e):
            app.logger.error(f'WebSocket error: {e}')
            return False
    
    # 添加健康检查端点
    @app.route('/api/real-time-preview/health')
    def real_time_preview_health():
        """实时预览功能健康检查"""
        return {
            "status": "healthy",
            "service": "real-time-preview",
            "version": "3.3.0",
            "features": [
                "real_time_preview",
                "wysiwyg_editing", 
                "instant_quality_feedback",
                "intelligent_splitting_integration",
                "multilingual_support_integration"
            ]
        }
    
    app.logger.info("✅ 实时预览功能API已注册到Flask应用")


def setup_real_time_preview_middleware(app: Flask):
    """
    设置实时预览功能的中间件
    
    Args:
        app: Flask应用实例
    """
    
    @app.before_request
    def before_real_time_preview_request():
        """实时预览请求前处理"""
        from flask import request
        
        # 记录实时预览API调用
        if request.path.startswith('/api/real-time-preview/'):
            app.logger.debug(f"Real-time preview API call: {request.method} {request.path}")
    
    @app.after_request  
    def after_real_time_preview_request(response):
        """实时预览请求后处理"""
        from flask import request
        
        # 为实时预览API添加CORS头
        if request.path.startswith('/api/real-time-preview/'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
    
    app.logger.info("✅ 实时预览功能中间件已设置")


# 在主应用工厂函数中使用
def create_app_with_real_time_preview(config_class):
    """
    创建包含实时预览功能的Flask应用
    
    Args:
        config_class: 配置类
        
    Returns:
        Flask应用实例
    """
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 设置中间件
    setup_real_time_preview_middleware(app)
    
    # 创建SocketIO实例（可选）
    socketio = None
    if app.config.get('ENABLE_WEBSOCKET', False):
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*")
    
    # 注册实时预览API
    register_real_time_preview_apis(app, socketio)
    
    # 注册其他必要的API
    from .api import enhanced_workflow, tts, enhanced_tts
    
    app.register_blueprint(enhanced_workflow.bp)
    app.register_blueprint(tts.bp)
    app.register_blueprint(enhanced_tts.bp)
    
    app.logger.info("🎬 实时预览功能已完全集成到Flask应用")
    
    return app, socketio
