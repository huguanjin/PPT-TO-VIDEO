"""
简化版字幕生成器 - 强制单行模式，删除所有复杂分割逻辑
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

# 导入配置桥接模块
try:
    from .system_config_bridge import get_single_line_mode
    USE_CONFIG_BRIDGE = True
except ImportError:
    USE_CONFIG_BRIDGE = False

class SimpleSubtitleGenerator:
    """简化的字幕生成器 - 只执行单行分割"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.logger = logging.getLogger(__name__)
        
        # 加载单行模式配置
        self.single_line_mode = True  # 默认强制单行
        self.load_config()
        
    def load_config(self):
        """加载配置 - 使用配置桥接模块"""
        try:
            # 🔄 优先使用配置桥接（从 MongoDB 读取）
            if USE_CONFIG_BRIDGE:
                self.single_line_mode = get_single_line_mode(self.project_dir)
                self.logger.info(f"🔄 从配置桥接加载 single_line_mode = {self.single_line_mode}")
                return
            
            # 回退：从文件读取配置
            manual_config_path = self.project_dir / "flask_backend" / "config_data" / "manual_split_config.json"
            if manual_config_path.exists():
                with open(manual_config_path, 'r', encoding='utf-8') as f:
                    manual_config = json.load(f)
                
                display_mode = manual_config.get("manual_split_config", {}).get("subtitle_display_mode", {})
                self.single_line_mode = display_mode.get("single_line_mode", True)
                
                self.logger.info(f"🔥 配置加载: single_line_mode = {self.single_line_mode}")
            else:
                self.logger.warning("配置文件不存在，使用默认单行模式")
                self.single_line_mode = True
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self.single_line_mode = True
    
    async def split_text(self, text: str) -> List[str]:
        """
        强制单行分割
        """
        text = text.strip()
        if not text:
            return []
        
        self.logger.info(f"🔥 强制单行模式处理文本: '{text[:50]}...'")
        
        if '\n' in text:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            self.logger.info(f"📋 分割为 {len(lines)} 个单行字幕")
            for i, line in enumerate(lines, 1):
                self.logger.info(f"  第{i}行: '{line}'")
            return lines
        else:
            self.logger.info("📝 单行文本，直接返回")
            return [text]