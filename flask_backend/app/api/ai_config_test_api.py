"""
AI配置测试API模块
提供AI连接测试功能
"""
from flask import Blueprint, jsonify, request
import logging

# 创建蓝图
ai_test_bp = Blueprint('ai_test', __name__, url_prefix='/api/ai-test')

logger = logging.getLogger(__name__)

@ai_test_bp.route('/status', methods=['GET'])
def get_status():
    """获取AI测试API状态"""
    return jsonify({
        "status": "active",
        "module": "ai_config_test_api",
        "message": "AI测试API模块已加载"
    })

@ai_test_bp.route('/connection', methods=['POST'])
def test_connection():
    """测试AI连接（占位符）"""
    return jsonify({
        "status": "placeholder",
        "message": "AI连接测试功能尚未实现"
    })

logger.info("AI测试API模块初始化完成")