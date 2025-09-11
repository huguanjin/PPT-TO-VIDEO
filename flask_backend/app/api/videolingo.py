"""
VideoLingo集成API蓝图
从videolingo_integration_app.py中提取的功能
"""

from flask import Blueprint, jsonify, request, render_template_string
import logging
import os
from datetime import datetime
from pathlib import Path

# 创建蓝图
bp = Blueprint('videolingo', __name__)
logger = logging.getLogger(__name__)

# 添加VideoLingo核心模块路径
current_dir = Path(__file__).parent.parent.parent
core_dir = current_dir / "core"

# 导入VideoLingo API模块
try:
    import sys
    sys.path.insert(0, str(core_dir))
    from api.videolingo_config_api import register_videolingo_config_api
    from api.config_management_api import register_config_management_api
    VIDEOLINGO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"VideoLingo API模块导入失败: {e}")
    VIDEOLINGO_AVAILABLE = False

@bp.route('/health', methods=['GET'])
def videolingo_health():
    """VideoLingo服务健康检查"""
    status = {
        'service': 'videolingo',
        'status': 'ok' if VIDEOLINGO_AVAILABLE else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'config_api': VIDEOLINGO_AVAILABLE,
            'management_api': VIDEOLINGO_AVAILABLE,
        }
    }
    
    if not VIDEOLINGO_AVAILABLE:
        status['message'] = 'VideoLingo模块未完全可用'
    
    return jsonify(status)

@bp.route('/version', methods=['GET'])
def videolingo_version():
    """VideoLingo版本信息"""
    return jsonify({
        'service': 'videolingo-integration',
        'version': '3.0.0',
        'description': 'VideoLingo技术融合 - 第三阶段系统集成',
        'build_date': '2025-09-11',
        'available_apis': {
            'config': '/api/videolingo/config/*',
            'management': '/api/videolingo/management/*',
            'health': '/api/videolingo/health'
        }
    })

@bp.route('/test', methods=['GET'])
def videolingo_test_page():
    """VideoLingo API测试页面"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VideoLingo API 测试</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            h1 { 
                text-align: center; 
                margin-bottom: 30px;
                font-size: 2.2em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .test-section { 
                margin: 20px 0; 
                padding: 20px; 
                background: rgba(255,255,255,0.1);
                border-radius: 10px; 
                backdrop-filter: blur(5px);
            }
            button { 
                padding: 10px 20px; 
                margin: 5px; 
                background: linear-gradient(45deg, #28a745, #20c997); 
                color: white; 
                border: none; 
                border-radius: 6px; 
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .result { 
                background: rgba(0,0,0,0.3); 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 6px; 
                white-space: pre-wrap;
                font-family: 'Courier New', monospace;
                max-height: 300px;
                overflow-y: auto;
            }
            .error { background: rgba(220, 53, 69, 0.3); }
            .success { background: rgba(40, 167, 69, 0.3); }
            input, select { 
                padding: 8px; 
                margin: 5px; 
                border: 1px solid rgba(255,255,255,0.3); 
                border-radius: 4px;
                background: rgba(255,255,255,0.1);
                color: white;
            }
            input::placeholder {
                color: rgba(255,255,255,0.7);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎥 VideoLingo API 测试工具</h1>
            
            <div class="test-section">
                <h3>🔍 基础测试</h3>
                <button onclick="testAPI('/api/videolingo/health', 'GET')">健康检查</button>
                <button onclick="testAPI('/api/videolingo/version', 'GET')">版本信息</button>
                <button onclick="testAPI('/api/health', 'GET')">主服务健康检查</button>
            </div>
            
            <div class="test-section">
                <h3>⚙️ 配置管理测试</h3>
                <button onclick="testAPI('/api/config', 'GET')">获取主配置</button>
                <button onclick="testAPI('/api/config/presets', 'GET')">获取配置预设</button>
                <div>
                    <input type="text" id="configSection" placeholder="配置段名称 (如: video, tts, ai)" />
                    <button onclick="testConfigSection()">获取配置段</button>
                </div>
            </div>
            
            <div class="test-section">
                <h3>🎯 工作流测试</h3>
                <button onclick="testAPI('/api/workflow/status', 'GET')">工作流状态</button>
                <button onclick="testAPI('/api/tts/voices', 'GET')">TTS语音列表</button>
                <button onclick="testAPI('/api/projects', 'GET')">项目列表</button>
            </div>
            
            <div class="test-section">
                <h3>📊 测试结果</h3>
                <div id="result" class="result">准备就绪，点击上方按钮开始测试...</div>
            </div>
        </div>
        
        <script>
            async function testAPI(endpoint, method = 'GET', data = null) {
                const resultDiv = document.getElementById('result');
                resultDiv.className = 'result';
                resultDiv.textContent = `正在测试: ${method} ${endpoint}...`;
                
                try {
                    const options = {
                        method: method,
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    };
                    
                    if (data) {
                        options.body = JSON.stringify(data);
                    }
                    
                    const response = await fetch(endpoint, options);
                    const result = await response.json();
                    
                    resultDiv.className = response.ok ? 'result success' : 'result error';
                    resultDiv.textContent = `状态: ${response.status} ${response.statusText}\\n\\n` +
                        JSON.stringify(result, null, 2);
                        
                } catch (error) {
                    resultDiv.className = 'result error';
                    resultDiv.textContent = `错误: ${error.message}`;
                }
            }
            
            function testConfigSection() {
                const section = document.getElementById('configSection').value;
                if (section) {
                    testAPI(`/api/config/${section}`, 'GET');
                } else {
                    alert('请输入配置段名称');
                }
            }
        </script>
    </body>
    </html>
    """)

@bp.route('/status', methods=['GET'])
def videolingo_status():
    """VideoLingo整体状态"""
    return jsonify({
        'videolingo': {
            'available': VIDEOLINGO_AVAILABLE,
            'core_path': str(core_dir),
            'apis': {
                'config': VIDEOLINGO_AVAILABLE,
                'management': VIDEOLINGO_AVAILABLE
            }
        },
        'integration': {
            'status': 'active',
            'endpoints': [
                '/api/videolingo/health',
                '/api/videolingo/version', 
                '/api/videolingo/test',
                '/api/videolingo/status'
            ]
        }
    })

def register_videolingo_apis(app):
    """注册VideoLingo相关API到主应用"""
    try:
        if VIDEOLINGO_AVAILABLE:
            # 导入并注册VideoLingo的API
            register_videolingo_config_api(app)
            register_config_management_api(app)
            logger.info("✅ VideoLingo API模块注册成功")
        else:
            logger.warning("⚠️ VideoLingo API模块不可用，跳过注册")
    except Exception as e:
        logger.error(f"❌ VideoLingo API注册失败: {e}")
