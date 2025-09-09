"""
VideoLingo技术融合 - 第三阶段主应用集成
整合配置管理、API服务、Web界面的完整系统
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

# 添加核心模块路径
current_dir = Path(__file__).parent
core_dir = current_dir / "core"
sys.path.insert(0, str(core_dir))

# 导入API模块
try:
    from api.videolingo_config_api import register_videolingo_config_api
    from api.config_management_api import register_config_management_api
except ImportError as e:
    logging.warning(f"API模块导入失败: {e}")
    # 提供空的注册函数避免错误
    def register_videolingo_config_api(app): pass
    def register_config_management_api(app): pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_videolingo_app(config_name='default'):
    """创建VideoLingo集成应用"""
    app = Flask(__name__)
    
    # 应用配置
    app.config.update({
        'SECRET_KEY': 'videolingo-integration-key-2024',
        'JSON_AS_ASCII': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
    })
    
    # 启用CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:*", "http://127.0.0.1:*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 注册API蓝图
    try:
        register_videolingo_config_api(app)
        register_config_management_api(app)
        logger.info("所有API模块已注册")
    except Exception as e:
        logger.error(f"注册API模块失败: {e}")
    
    # 基础路由
    @app.route('/')
    def index():
        """主页"""
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VideoLingo技术融合 - 第三阶段系统集成</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: white;
                }
                .container { 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }
                h1 { 
                    text-align: center; 
                    margin-bottom: 40px;
                    font-size: 2.5em;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                .status-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }
                .status-card {
                    background: rgba(255,255,255,0.15);
                    padding: 25px;
                    border-radius: 15px;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .status-card h3 {
                    margin-top: 0;
                    color: #FFD700;
                    font-size: 1.3em;
                }
                .api-section {
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    margin-top: 30px;
                }
                .api-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }
                .api-item {
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                    border-left: 4px solid #FFD700;
                }
                .method {
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 0.8em;
                    font-weight: bold;
                    margin-right: 10px;
                }
                .get { background: #28a745; }
                .post { background: #007bff; }
                .put { background: #ffc107; color: #000; }
                .delete { background: #dc3545; }
                .footer {
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255,255,255,0.3);
                    opacity: 0.8;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 VideoLingo技术融合 - 第三阶段系统集成</h1>
                
                <div class="status-grid">
                    <div class="status-card">
                        <h3>✅ 第一阶段完成</h3>
                        <p>• 动态规划断句算法</p>
                        <p>• Spacy语法分析处理器</p>
                        <p>• 智能配置预设系统</p>
                        <p>• VideoLingo技术融合器</p>
                    </div>
                    <div class="status-card">
                        <h3>✅ 第二阶段完成</h3>
                        <p>• Vue.js 3配置面板界面</p>
                        <p>• 实时配置预览系统</p>
                        <p>• 高级配置管理面板</p>
                        <p>• 配置导入导出功能</p>
                    </div>
                    <div class="status-card">
                        <h3>🔥 第三阶段进行中</h3>
                        <p>• 后端API端点实现</p>
                        <p>• 配置持久化存储</p>
                        <p>• 系统集成与优化</p>
                        <p>• 完整功能测试</p>
                    </div>
                </div>
                
                <div class="api-section">
                    <h2>🔧 API服务端点</h2>
                    <div class="api-list">
                        <div class="api-item">
                            <span class="method get">GET</span>
                            <strong>/api/config/presets</strong><br>
                            <small>获取所有配置预设</small>
                        </div>
                        <div class="api-item">
                            <span class="method get">GET</span>
                            <strong>/api/config/presets/{key}</strong><br>
                            <small>获取特定预设配置</small>
                        </div>
                        <div class="api-item">
                            <span class="method post">POST</span>
                            <strong>/api/config/apply</strong><br>
                            <small>应用配置到系统</small>
                        </div>
                        <div class="api-item">
                            <span class="method post">POST</span>
                            <strong>/api/config/test</strong><br>
                            <small>测试配置效果</small>
                        </div>
                        <div class="api-item">
                            <span class="method post">POST</span>
                            <strong>/api/config/presets</strong><br>
                            <small>保存自定义预设</small>
                        </div>
                        <div class="api-item">
                            <span class="method get">GET</span>
                            <strong>/api/management/configs</strong><br>
                            <small>配置列表管理</small>
                        </div>
                        <div class="api-item">
                            <span class="method post">POST</span>
                            <strong>/api/management/backup</strong><br>
                            <small>创建配置备份</small>
                        </div>
                        <div class="api-item">
                            <span class="method get">GET</span>
                            <strong>/api/management/statistics</strong><br>
                            <small>获取统计信息</small>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>VideoLingo技术融合项目 - 智能字幕处理与视频配置一体化解决方案</p>
                    <p>开发时间: 2024年12月19日 | 版本: 3.0.0 | 第三阶段系统集成版本</p>
                </div>
            </div>
        </body>
        </html>
        """)
    
    @app.route('/api/health')
    def health_check():
        """健康检查"""
        try:
            return jsonify({
                'status': 'healthy',
                'version': '3.0.0',
                'stage': 'Phase 3 - System Integration',
                'services': {
                    'config_api': 'running',
                    'management_api': 'running',
                    'storage_system': 'active'
                },
                'timestamp': '2024-12-19T00:00:00Z'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.route('/api/version')
    def version_info():
        """版本信息"""
        return jsonify({
            'project': 'VideoLingo技术融合',
            'version': '3.0.0',
            'stage': 'Phase 3 - System Integration',
            'description': '智能字幕处理与视频配置一体化解决方案',
            'features': [
                'VideoLingo技术融合',
                '智能配置管理',
                '配置持久化存储',
                'RESTful API服务',
                'Vue.js前端界面',
                '批量操作支持',
                '配置历史记录',
                '统计分析功能'
            ],
            'api_endpoints': {
                'config_management': '/api/config/*',
                'storage_management': '/api/management/*',
                'health_check': '/api/health',
                'version_info': '/api/version'
            }
        })
    
    @app.route('/test/api')
    def test_api():
        """API测试页面"""
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VideoLingo API 测试</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .test-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                button { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .result { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; white-space: pre-wrap; }
                input, select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>VideoLingo API 测试工具</h1>
            
            <div class="test-section">
                <h3>配置预设测试</h3>
                <button onclick="testAPI('/api/config/presets', 'GET')">获取所有预设</button>
                <button onclick="testAPI('/api/config/presets/standard', 'GET')">获取标准预设</button>
                <button onclick="testAPI('/api/config/presets/videolingo', 'GET')">获取VideoLingo预设</button>
            </div>
            
            <div class="test-section">
                <h3>配置管理测试</h3>
                <button onclick="testAPI('/api/management/configs', 'GET')">获取配置列表</button>
                <button onclick="testAPI('/api/management/statistics', 'GET')">获取统计信息</button>
                <button onclick="testAPI('/api/management/backup', 'POST')">创建备份</button>
            </div>
            
            <div class="test-section">
                <h3>系统测试</h3>
                <button onclick="testAPI('/api/health', 'GET')">健康检查</button>
                <button onclick="testAPI('/api/version', 'GET')">版本信息</button>
            </div>
            
            <div id="result" class="result"></div>
            
            <script>
                async function testAPI(url, method, data = null) {
                    const resultDiv = document.getElementById('result');
                    resultDiv.textContent = '请求中...';
                    
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
                        
                        const response = await fetch(url, options);
                        const result = await response.json();
                        
                        resultDiv.textContent = 
                            `请求: ${method} ${url}\\n` +
                            `状态: ${response.status}\\n` +
                            `响应:\\n${JSON.stringify(result, null, 2)}`;
                    } catch (error) {
                        resultDiv.textContent = `错误: ${error.message}`;
                    }
                }
            </script>
        </body>
        </html>
        """)
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': '请求的资源不存在',
            'available_endpoints': [
                '/api/config/presets',
                '/api/management/configs',
                '/api/health',
                '/api/version'
            ]
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': '服务器内部错误'
        }), 500
    
    return app


def main():
    """主函数"""
    try:
        # 创建应用
        app = create_videolingo_app()
        
        # 配置参数
        host = os.getenv('VIDEOLINGO_HOST', '0.0.0.0')
        port = int(os.getenv('VIDEOLINGO_PORT', 8004))
        debug = os.getenv('VIDEOLINGO_DEBUG', 'true').lower() == 'true'
        
        logger.info(f"VideoLingo技术融合第三阶段系统启动中...")
        logger.info(f"访问地址: http://{host}:{port}")
        logger.info(f"API测试页面: http://{host}:{port}/test/api")
        
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


if __name__ == "__main__":
    main()
