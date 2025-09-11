"""
简化版字幕修复测试Flask应用
"""
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

app = Flask(__name__)
CORS(app, origins=['*'])

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 测试导入修复模块
        from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
        
        fixer = SubtitleMultilineFixer()
        test_text = "这是一个测试字幕，用来验证修复功能是否正常工作，应该被控制在两行以内显示。"
        optimized = fixer.optimize_subtitle_text(test_text)
        lines_count = len(optimized.split('\n'))
        
        return jsonify({
            "status": "healthy",
            "subtitle_fix_test": {
                "original": test_text,
                "optimized": optimized,
                "lines_count": lines_count,
                "test_passed": lines_count <= 2
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "import_error": True
        }), 500

@app.route('/api/test-subtitle-weights', methods=['POST'])
def test_subtitle_weights():
    """测试字符权重计算"""
    try:
        from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
        
        data = request.get_json() or {}
        test_text = data.get('text', '这是测试文本 with English words 和标点符号！？。')
        
        fixer = SubtitleMultilineFixer()
        
        # 计算字符权重
        total_weight = fixer.calculate_enhanced_char_weight(test_text)
        
        # 分析每个字符
        char_analysis = []
        for char in test_text:
            if '\u4e00' <= char <= '\u9fff':
                weight = 2.0  # 中文
                char_type = "中文"
            elif char.isalpha():
                weight = 1.0  # 英文
                char_type = "英文"
            elif char in "，。！？；：":
                weight = 0.6  # 标点
                char_type = "标点"
            elif char == ' ':
                weight = 0.3  # 空格
                char_type = "空格"
            else:
                weight = 1.0  # 其他
                char_type = "其他"
            
            char_analysis.append({
                "char": char,
                "weight": weight,
                "type": char_type
            })
        
        return jsonify({
            "text": test_text,
            "total_weight": total_weight,
            "char_analysis": char_analysis,
            "weight_config": fixer.config.get("character_weight_adjustments", {})
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🔧 简化版字幕修复测试服务启动")
    print("📖 健康检查: http://localhost:5002/health") 
    print("⚖️ 权重测试: http://localhost:5002/api/test-subtitle-weights")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
