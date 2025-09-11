"""
字幕修复验证API
直接测试字幕多行显示修复功能
"""
import sys
import json
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

app = Flask(__name__)
CORS(app, origins=['*'])

# HTML测试页面模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>字幕修复测试工具</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .test-area { margin: 20px 0; padding: 15px; border: 1px solid #ccc; border-radius: 5px; }
        .result { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }
        .success { background: #d4edda; border-color: #c3e6cb; color: #155724; }
        .error { background: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        textarea { width: 100%; height: 100px; margin: 5px 0; }
        button { padding: 10px 20px; margin: 5px; }
        .weight-info { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>字幕多行显示修复测试工具</h1>
        
        <div class="test-area">
            <h3>1. 快速测试</h3>
            <button onclick="runQuickTest()">运行快速测试</button>
            <div id="quickResult" class="result"></div>
        </div>
        
        <div class="test-area">
            <h3>2. 自定义文本测试</h3>
            <textarea id="customText" placeholder="输入要测试的字幕文本...">这是一个很长的测试句子，用来验证字幕分割功能是否能够正确处理多行显示的问题，确保不会出现超过两行的情况。</textarea>
            <button onclick="testCustomText()">测试字幕处理</button>
            <div id="customResult" class="result"></div>
        </div>
        
        <div class="test-area">
            <h3>3. 分辨率测试</h3>
            <label>宽度: <input type="number" id="width" value="1920"></label>
            <label>高度: <input type="number" id="height" value="1080"></label>
            <button onclick="testResolution()">测试分辨率适应</button>
            <div id="resolutionResult" class="result"></div>
        </div>
        
        <div class="test-area">
            <h3>4. 配置状态</h3>
            <button onclick="checkConfig()">检查配置状态</button>
            <div id="configResult" class="result"></div>
        </div>
    </div>

    <script>
        async function runQuickTest() {
            const result = document.getElementById('quickResult');
            result.innerHTML = '正在测试...';
            
            try {
                const response = await fetch('/api/quick-test');
                const data = await response.json();
                
                if (data.status === 'success') {
                    result.className = 'result success';
                    result.innerHTML = `
                        <h4>快速测试通过 ✓</h4>
                        <p><strong>原文:</strong> ${data.test_text}</p>
                        <p><strong>优化后:</strong> ${data.optimized_text}</p>
                        <p><strong>行数:</strong> ${data.lines_count} (限制: 2行)</p>
                        <p><strong>总权重:</strong> ${data.total_weight.toFixed(2)}</p>
                    `;
                } else {
                    result.className = 'result error';
                    result.innerHTML = `<p>测试失败: ${data.error}</p>`;
                }
            } catch (error) {
                result.className = 'result error';
                result.innerHTML = `<p>请求失败: ${error.message}</p>`;
            }
        }
        
        async function testCustomText() {
            const text = document.getElementById('customText').value;
            const result = document.getElementById('customResult');
            result.innerHTML = '正在处理...';
            
            try {
                const response = await fetch('/api/test-text', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                const data = await response.json();
                
                result.className = data.fix_applied ? 'result success' : 'result error';
                result.innerHTML = `
                    <h4>处理结果</h4>
                    <p><strong>原文:</strong> ${data.original_text}</p>
                    <p><strong>优化后:</strong> ${data.optimized_text}</p>
                    <p><strong>行数:</strong> ${data.lines_count}</p>
                    <p><strong>修复状态:</strong> ${data.fix_applied ? '✓ 成功控制在2行内' : '✗ 超过2行'}</p>
                    <div class="weight-info">
                        ${data.line_weights.map((line, i) => 
                            `第${i+1}行: "${line.text}" (权重: ${line.weight.toFixed(2)})`
                        ).join('<br>')}
                    </div>
                `;
            } catch (error) {
                result.className = 'result error';
                result.innerHTML = `<p>处理失败: ${error.message}</p>`;
            }
        }
        
        async function testResolution() {
            const width = document.getElementById('width').value;
            const height = document.getElementById('height').value;
            const result = document.getElementById('resolutionResult');
            result.innerHTML = '正在测试...';
            
            try {
                const response = await fetch('/api/test-resolution', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({width: parseInt(width), height: parseInt(height)})
                });
                const data = await response.json();
                
                result.className = 'result success';
                result.innerHTML = `
                    <h4>分辨率适应结果</h4>
                    <p><strong>分辨率:</strong> ${data.resolution.width}x${data.resolution.height} (${data.resolution.class})</p>
                    <p><strong>基础字体:</strong> ${data.font_recommendations.base_font_size}px</p>
                    <p><strong>自适应字体:</strong> ${data.font_recommendations.adaptive_font_size}px</p>
                    <p><strong>缩放比例:</strong> ${data.font_recommendations.scale_factor.toFixed(2)}</p>
                    <p><strong>字符权重限制:</strong> 中文${data.subtitle_limits.chinese_char_weight}, 每行${data.subtitle_limits.max_chars_per_line}权重单位</p>
                `;
            } catch (error) {
                result.className = 'result error';
                result.innerHTML = `<p>测试失败: ${error.message}</p>`;
            }
        }
        
        async function checkConfig() {
            const result = document.getElementById('configResult');
            result.innerHTML = '正在检查...';
            
            try {
                const response = await fetch('/api/config-status');
                const data = await response.json();
                
                result.className = 'result success';
                result.innerHTML = `
                    <h4>配置状态</h4>
                    <p><strong>修复模块:</strong> ${data.multiline_fix_available ? '✓ 可用' : '✗ 不可用'}</p>
                    <p><strong>Netflix配置:</strong> ${data.netflix_config_loaded ? '✓ 已加载' : '✗ 未加载'}</p>
                    <p><strong>字符权重:</strong> 中文${data.character_weights.chinese || 'N/A'}, 标点${data.character_weights.punctuation || 'N/A'}</p>
                    <p><strong>行数限制:</strong> ${data.line_limits.max_lines || 'N/A'}行, 每行${data.line_limits.max_chars_per_line || 'N/A'}权重</p>
                `;
            } catch (error) {
                result.className = 'result error';
                result.innerHTML = `<p>检查失败: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """显示测试页面"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/quick-test')
def quick_test():
    """快速测试字幕修复功能"""
    try:
        from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
        
        fixer = SubtitleMultilineFixer()
        test_text = "这是一个用于快速验证字幕修复功能的测试句子，应该能够正确控制在两行以内显示，确保不会出现多行显示问题。"
        
        # 计算权重和优化
        original_weight = fixer.calculate_enhanced_char_weight(test_text)
        optimized_text = fixer.optimize_subtitle_text(test_text)
        lines = optimized_text.split('\n')
        
        return jsonify({
            "status": "success",
            "test_text": test_text,
            "optimized_text": optimized_text,
            "lines_count": len(lines),
            "total_weight": original_weight,
            "fix_applied": len(lines) <= 2
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/test-text', methods=['POST'])
def test_text():
    """测试自定义文本"""
    try:
        from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
        
        data = request.get_json()
        text = data.get('text', '')
        
        fixer = SubtitleMultilineFixer()
        
        # 处理文本
        optimized_text = fixer.optimize_subtitle_text(text)
        lines = optimized_text.split('\n')
        
        # 分析每行权重
        line_weights = []
        for line in lines:
            weight = fixer.calculate_enhanced_char_weight(line)
            line_weights.append({"text": line, "weight": weight})
        
        return jsonify({
            "original_text": text,
            "optimized_text": optimized_text,
            "lines_count": len(lines),
            "line_weights": line_weights,
            "fix_applied": len(lines) <= 2,
            "character_weights": fixer.config.get("character_weight_adjustments", {})
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-resolution', methods=['POST'])
def test_resolution():
    """测试分辨率适应"""
    try:
        from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
        
        data = request.get_json()
        width = data.get('width', 1920)
        height = data.get('height', 1080)
        
        fixer = SubtitleMultilineFixer()
        
        # 计算字体大小
        base_font_size = 24
        adaptive_font_size = fixer.get_resolution_adaptive_font_size((width, height), base_font_size)
        
        # 分辨率分类
        resolution_class = "4K" if width >= 3840 else "1080p" if width >= 1920 else "720p" if width >= 1280 else "低分辨率"
        
        return jsonify({
            "resolution": {
                "width": width,
                "height": height,
                "class": resolution_class
            },
            "font_recommendations": {
                "base_font_size": base_font_size,
                "adaptive_font_size": adaptive_font_size,
                "scale_factor": adaptive_font_size / base_font_size
            },
            "subtitle_limits": {
                "max_chars_per_line": 30,
                "max_lines": 2,
                "chinese_char_weight": 2.0
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config-status')
def config_status():
    """检查配置状态"""
    try:
        from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
        
        fixer = SubtitleMultilineFixer()
        
        # 检查Netflix配置
        netflix_config_path = project_root / "flask_backend/config_data/netflix_subtitle_config.json"
        netflix_config_loaded = netflix_config_path.exists()
        
        return jsonify({
            "multiline_fix_available": True,
            "netflix_config_loaded": netflix_config_loaded,
            "character_weights": fixer.config.get("character_weight_adjustments", {}),
            "line_limits": fixer.config.get("line_control_rules", {}),
            "config_file": str(fixer.config_path),
            "fix_config_loaded": fixer.config_path.exists()
        })
        
    except Exception as e:
        return jsonify({
            "multiline_fix_available": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🔧 字幕修复验证API启动")
    print("🌐 测试页面: http://localhost:5003/")
    print("📋 API接口:")
    print("   - 快速测试: http://localhost:5003/api/quick-test")
    print("   - 配置状态: http://localhost:5003/api/config-status")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
