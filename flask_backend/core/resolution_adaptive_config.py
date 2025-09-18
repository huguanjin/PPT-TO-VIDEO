"""
分辨率自适应配置管理器
集成字体大小自适应功能到现有配置系统
"""
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ResolutionAdaptiveConfigManager:
    """分辨率自适应配置管理器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.config_dir = self.project_dir / "flask_backend" / "config_data"
        
    def get_adaptive_subtitle_config(self, 
                                   video_resolution: Optional[Tuple[int, int]] = None,
                                   base_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取分辨率自适应字幕配置
        
        Args:
            video_resolution: 视频分辨率 (width, height)
            base_config: 基础配置，如果为None则加载默认配置
        """
        if base_config is None:
            base_config = self._load_base_config()
        
        # 克隆配置避免修改原配置
        adaptive_config = base_config.copy()
        
        if video_resolution:
            # 计算自适应字体大小
            from .subtitle_multiline_fixer import get_fixed_font_size
            
            # 获取基础字体大小
            base_font_size = base_config.get("subtitle", {}).get("font_size", 18)
            adaptive_font_size = get_fixed_font_size(video_resolution, base_font_size)
            
            # 更新字幕配置
            if "subtitle" not in adaptive_config:
                adaptive_config["subtitle"] = {}
            
            adaptive_config["subtitle"]["font_size"] = adaptive_font_size
            adaptive_config["subtitle"]["resolution_adapted"] = True
            adaptive_config["subtitle"]["source_resolution"] = f"{video_resolution[0]}x{video_resolution[1]}"
            adaptive_config["subtitle"]["base_font_size"] = base_font_size
            
            # 同时更新旧格式配置
            adaptive_config["subtitle_fontsize"] = adaptive_font_size
            
            logger.info(f"分辨率自适应配置生成: {video_resolution} → 字体{base_font_size}px→{adaptive_font_size}px")
        
        return adaptive_config
    
    def _load_base_config(self) -> Dict[str, Any]:
        """加载基础配置"""
        app_config_path = self.config_dir / "backend_app_config.json"
        
        try:
            with open(app_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载基础配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "subtitle_fontsize": 18,
            "subtitle": {
                "enabled": True,
                "font_family": "Arial",
                "font_size": 18,
                "font_color": "#FFFFFF",
                "background_color": "rgba(0,0,0,0.75)",
                "position": "bottom",
                "max_chars_per_line": 30,
                "max_lines": 2,
                "enforce_line_limit": True
            }
        }
    
    def save_adaptive_config(self, adaptive_config: Dict[str, Any], 
                           target_path: Optional[Path] = None) -> bool:
        """
        保存自适应配置到指定路径
        
        Args:
            adaptive_config: 自适应配置
            target_path: 目标路径，如果为None则保存到临时配置
        """
        if target_path is None:
            target_path = self.config_dir / "app_config_adaptive.json"
        
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(adaptive_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"自适应配置已保存: {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存自适应配置失败: {e}")
            return False
    
    def get_resolution_presets(self) -> Dict[str, Tuple[int, int]]:
        """获取分辨率预设"""
        return {
            "4K": (3840, 2160),
            "2K": (2560, 1440),
            "Full HD": (1920, 1080),
            "HD Ready": (1366, 768),
            "HD 720p": (1280, 720),
            "SD 480p": (854, 480),
            "Low Res": (640, 360),
        }
    
    def test_all_resolutions(self, base_font_size: int = 18) -> Dict[str, Dict[str, Any]]:
        """
        测试所有分辨率预设的字体大小
        
        Returns:
            各分辨率的字体大小映射
        """
        results = {}
        presets = self.get_resolution_presets()
        
        for name, resolution in presets.items():
            from .subtitle_multiline_fixer import get_fixed_font_size
            adaptive_size = get_fixed_font_size(resolution, base_font_size)
            
            results[name] = {
                "resolution": resolution,
                "base_font_size": base_font_size,
                "adaptive_font_size": adaptive_size,
                "scale_factor": adaptive_size / base_font_size,
                "pixels": resolution[0] * resolution[1]
            }
        
        return results


def create_adaptive_config_for_project(project_dir: Path, 
                                     video_resolution: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
    """
    便捷函数：为项目创建自适应配置
    
    Args:
        project_dir: 项目目录
        video_resolution: 视频分辨率
    
    Returns:
        自适应配置字典
    """
    manager = ResolutionAdaptiveConfigManager(project_dir)
    return manager.get_adaptive_subtitle_config(video_resolution)


if __name__ == "__main__":
    # 测试功能
    from pathlib import Path
    
    project_dir = Path(__file__).parent.parent.parent
    manager = ResolutionAdaptiveConfigManager(project_dir)
    
    print("🔍 分辨率自适应配置测试")
    print("=" * 40)
    
    # 测试所有分辨率
    results = manager.test_all_resolutions()
    
    for name, info in results.items():
        res = info["resolution"]
        print(f"{name:10} {res[0]:4}x{res[1]:4} → {info['base_font_size']:2}px → {info['adaptive_font_size']:2}px (x{info['scale_factor']:.2f})")
    
    print("\n✅ 分辨率自适应配置管理器测试完成")