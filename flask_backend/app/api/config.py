"""
配置管理API接口
处理应用程序配置的读取和保存
"""
import os
import sys
import json
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from utils.logger import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

# 导入新的配置管理器
try:
    from flask_backend.app.utils.config_manager import config_manager
except ImportError:
    # 如果导入失败，创建一个简单的配置管理器
    class SimpleConfigManager:
        def __init__(self):
            self.config_file = project_root / "config_data" / "app_config.json"
        
        def load_config(self):
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        
        def save_config(self, config):
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        
        def get_section(self, section):
            config = self.load_config()
            return config.get(section, {})
        
        def update_section(self, section, data):
            config = self.load_config()
            if section not in config:
                config[section] = {}
            config[section].update(data)
            return self.save_config(config)
        
        def get_subtitle_config_for_ffmpeg(self):
            subtitle_config = self.get_section('subtitle')
            return {
                "font_family": subtitle_config.get("font_family", "Microsoft YaHei"),
                "font_size": subtitle_config.get("font_size", 40),
                "font_color": subtitle_config.get("font_color", "#FFFFFF"),
                "background_color": subtitle_config.get("background_color", "rgba(0,0,0,0.8)"),
                "position": subtitle_config.get("position", "bottom")
            }
    
    config_manager = SimpleConfigManager()

# 创建配置管理蓝图
bp = Blueprint('config', __name__)
logger = get_logger(__name__)

@bp.route('', methods=['GET'])
def get_config():
    """获取应用配置"""
    try:
        # 使用新的配置管理器
        config = config_manager.load_config()
        
        logger.info("获取配置成功")
        return jsonify({
            'success': True,
            'data': {
                'config': config
            }
        })
            
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('', methods=['POST'])
def save_config():
    """保存应用配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少配置数据'
            }), 400
        
        # 使用新的配置管理器保存配置
        success = config_manager.save_config(data)
        
        if success:
            logger.info(f"配置已保存到: {config_manager.config_file}")
            return jsonify({
                'success': True,
                'message': '配置保存成功',
                'data': {
                    'config_file': str(config_manager.config_file)
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '配置保存失败'
            }), 500
            
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/reset', methods=['POST'])
def reset_config():
    """重置配置为默认值"""
    try:
        # 删除现有配置文件并重新创建
        if config_manager.config_file.exists():
            config_manager.config_file.unlink()
        
        config_manager._create_default_config()
        
        logger.info("配置已重置为默认值")
        return jsonify({
            'success': True,
            'message': '配置已重置为默认值'
        })
        
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/subtitle/ffmpeg', methods=['GET'])
def get_subtitle_config_for_ffmpeg():
    """获取适用于FFmpeg的字幕配置格式"""
    try:
        subtitle_config = config_manager.get_subtitle_config_for_ffmpeg()
        
        logger.info("获取FFmpeg字幕配置成功")
        return jsonify({
            'success': True,
            'data': subtitle_config,
            'message': '获取FFmpeg字幕配置成功'
        })
        
    except Exception as e:
        logger.error(f"获取FFmpeg字幕配置失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/<section>', methods=['GET'])
def get_config_section(section):
    """获取配置的某个部分"""
    try:
        section_config = config_manager.get_section(section)
        
        logger.info(f"获取配置部分 {section} 成功")
        return jsonify({
            'success': True,
            'data': section_config,
            'message': f'获取配置部分 {section} 成功'
        })
        
    except Exception as e:
        logger.error(f"获取配置部分 {section} 失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/<section>', methods=['PUT'])
def update_config_section(section):
    """更新配置的某个部分"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少配置数据'
            }), 400
        
        success = config_manager.update_section(section, data)
        if success:
            logger.info(f"配置部分 {section} 更新成功")
            return jsonify({
                'success': True,
                'message': f'配置部分 {section} 更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '配置更新失败'
            }), 500
            
    except Exception as e:
        logger.error(f"更新配置部分 {section} 失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
