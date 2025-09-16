"""
VideoLingo配置API占位模块
提供VideoLingo特定的配置管理功能
"""
import logging

logger = logging.getLogger(__name__)

def register_videolingo_config_api(app):
    """
    注册VideoLingo配置API
    
    Args:
        app: Flask应用实例
    """
    logger.info("VideoLingo配置API已注册（占位实现）")
    
    # 这里可以添加VideoLingo特定的配置路由
    # 例如：
    # @app.route('/api/videolingo/config', methods=['GET', 'POST'])
    # def videolingo_config():
    #     pass
    
    # 暂时使用占位实现
    pass