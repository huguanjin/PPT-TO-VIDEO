"""
修复版Flask应用 - 集成字幕多行显示修复功能
确保使用最新的配置和修复模块
"""
import os
import sys
import json
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "flask_backend"))

# 导入修复模块
from flask_backend.core.subtitle_multiline_fixer import SubtitleMultilineFixer
from flask_backend.core.step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator

def create_fixed_app():
    """创建修复版Flask应用"""
    app = Flask(__name__)
    
    # 配置CORS
    CORS(app, origins=['*'], supports_credentials=True)
    
    # 初始化修复器
    subtitle_fixer = SubtitleMultilineFixer()
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查 - 包含修复状态"""
        try:
            # 测试修复器功能
            test_text = "这是一个测试字幕，用来验证修复功能是否正常工作。"
            optimized = subtitle_fixer.optimize_subtitle_text(test_text)
            lines_count = len(optimized.split('\n'))
            
            return jsonify({
                "status": "healthy",
                "timestamp": "2024-09-11T23:55:00",
                "subtitle_fix": {
                    "enabled": True,
                    "test_result": "passed" if lines_count <= 2 else "failed",
                    "test_lines_count": lines_count,
                    "test_text_optimized": optimized
                },
                "services": {
                    "subtitle_generator": "enhanced_with_fix",
                    "multiline_fixer": "active",
                    "videolingo_integration": "active"
                }
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "subtitle_fix": {"enabled": False}
            }), 500
    
    @app.route('/api/subtitle/test-fix', methods=['POST'])
    def test_subtitle_fix():
        """测试字幕修复功能"""
        try:
            data = request.get_json()
            test_text = data.get('text', '这是一个很长的测试句子，用来验证字幕分割功能是否能够正确处理多行显示的问题。')
            
            # 计算原始权重
            original_weight = subtitle_fixer.calculate_enhanced_char_weight(test_text)
            
            # 应用修复
            optimized_text = subtitle_fixer.optimize_subtitle_text(test_text)
            lines = optimized_text.split('\n')
            
            # 计算每行权重
            line_weights = []
            for line in lines:
                weight = subtitle_fixer.calculate_enhanced_char_weight(line)
                line_weights.append({"text": line, "weight": weight})
            
            return jsonify({
                "original_text": test_text,
                "original_weight": original_weight,
                "optimized_text": optimized_text,
                "lines_count": len(lines),
                "line_weights": line_weights,
                "fix_applied": len(lines) <= 2,
                "character_weights": subtitle_fixer.config.get("character_weight_adjustments", {})
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/subtitle/config', methods=['GET'])
    def get_subtitle_config():
        """获取字幕配置"""
        try:
            # 读取修复配置
            config_path = project_root / "config_data" / "subtitle_multiline_fix_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    fix_config = json.load(f)
            else:
                fix_config = {"error": "配置文件不存在"}
            
            # 读取Netflix配置
            netflix_config_path = project_root / "flask_backend/config_data/netflix_subtitle_config.json"
            if netflix_config_path.exists():
                with open(netflix_config_path, 'r', encoding='utf-8') as f:
                    netflix_config = json.load(f)
            else:
                netflix_config = {"error": "Netflix配置文件不存在"}
            
            return jsonify({
                "subtitle_fix_config": fix_config,
                "netflix_config": netflix_config,
                "config_status": "loaded"
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/subtitle/generate-test', methods=['POST'])
    def generate_test_subtitle():
        """生成测试字幕 - 验证修复效果"""
        try:
            data = request.get_json()
            text = data.get('text', '默认测试文本，这是一个比较长的句子用来测试字幕生成和多行显示修复功能是否正常工作。')
            resolution = data.get('resolution', [1920, 1080])
            
            # 创建字幕生成器实例（使用临时目录）
            temp_dir = project_root / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            generator = EnhancedSubtitleGenerator(temp_dir)
            
            # 使用增强字幕生成器处理文本
            cleaned_text = generator._clean_subtitle_text(text)
            
            # 获取自适应字体大小
            font_size = subtitle_fixer.get_resolution_adaptive_font_size(tuple(resolution))
            
            # 分析结果
            lines = cleaned_text.split('\n')
            line_analysis = []
            for i, line in enumerate(lines, 1):
                weight = subtitle_fixer.calculate_enhanced_char_weight(line)
                line_analysis.append({
                    "line_number": i,
                    "text": line,
                    "character_weight": weight,
                    "character_count": len(line)
                })
            
            return jsonify({
                "original_text": text,
                "processed_text": cleaned_text,
                "lines_count": len(lines),
                "line_analysis": line_analysis,
                "resolution": resolution,
                "adaptive_font_size": font_size,
                "fix_status": {
                    "multiline_fix_enabled": generator.subtitle_config.get("enable_multiline_fix", False),
                    "lines_within_limit": len(lines) <= 2,
                    "max_chars_per_line": generator.subtitle_config.get("max_chars_per_line", 30)
                }
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/video/resolution-info', methods=['POST'])
    def get_video_resolution_info():
        """获取视频分辨率信息和字体建议"""
        try:
            data = request.get_json()
            width = data.get('width', 1920)
            height = data.get('height', 1080)
            
            # 计算字体大小建议
            base_font_size = 24
            adaptive_font_size = subtitle_fixer.get_resolution_adaptive_font_size((width, height), base_font_size)
            
            # 分辨率分类
            if width >= 3840:
                resolution_class = "4K"
            elif width >= 1920:
                resolution_class = "1080p"
            elif width >= 1280:
                resolution_class = "720p"
            else:
                resolution_class = "低分辨率"
            
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
    
    return app

def main():
    """主函数"""
    print("🚀 修复版PPT转视频 Flask API 启动中...")
    print("🔧 已集成字幕多行显示修复功能")
    print(f"📖 健康检查: http://localhost:5001/health")
    print(f"🧪 字幕测试: http://localhost:5001/api/subtitle/test-fix")
    print(f"⚙️  配置查看: http://localhost:5001/api/subtitle/config")
    
    app = create_fixed_app()
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main()
