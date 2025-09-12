"""
API层多行修复强化中间件
确保所有字幕相关的API调用都强制应用多行修复机制
"""
import json
import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import functools

class MultilineFixEnhancementMiddleware:
    """API层多行修复强化中间件"""
    
    def __init__(self, project_dir: Path, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # 加载强化配置
        self.config = self._load_enhancement_config()
        
        # 初始化修复器
        try:
            from .subtitle_multiline_fixer import SubtitleMultilineFixer
            self.fixer = SubtitleMultilineFixer()
        except ImportError:
            self.logger.warning("无法导入SubtitleMultilineFixer，多行修复功能将被禁用")
            self.fixer = None
    
    def _load_enhancement_config(self) -> Dict[str, Any]:
        """加载强化配置"""
        try:
            config_path = self.project_dir / "flask_backend" / "config_data" / "multiline_enhancement_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("multiline_fix_enhancement", {})
        except Exception as e:
            self.logger.warning(f"多行修复强化配置加载失败: {e}")
        
        # 默认配置
        return {
            "enforcement_levels": {
                "api_processing": {
                    "enabled": True,
                    "realtime_fix": True,
                    "response_validation": True
                }
            }
        }
    
    def enhance_subtitle_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        强化字幕响应数据 - 确保所有字幕内容都经过多行修复
        
        Args:
            response_data: API响应数据
            
        Returns:
            强化后的响应数据
        """
        if not self._is_api_enhancement_enabled():
            return response_data
        
        try:
            enhanced_data = response_data.copy()
            
            # 处理不同类型的字幕响应
            if "subtitles" in enhanced_data:
                enhanced_data["subtitles"] = self._enhance_subtitle_list(enhanced_data["subtitles"])
            
            if "subtitle_segments" in enhanced_data:
                enhanced_data["subtitle_segments"] = self._enhance_subtitle_segments(enhanced_data["subtitle_segments"])
            
            if "subtitle_content" in enhanced_data:
                enhanced_data["subtitle_content"] = self._enhance_subtitle_content(enhanced_data["subtitle_content"])
            
            # 添加强化元数据
            enhanced_data["_multiline_enhancement"] = {
                "applied": True,
                "version": "1.0.0",
                "timestamp": self._get_current_timestamp()
            }
            
            self.logger.info("API响应字幕内容已应用多行修复强化")
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"API字幕响应强化失败: {e}")
            return response_data
    
    def _is_api_enhancement_enabled(self) -> bool:
        """检查API层强化是否启用"""
        return self.config.get("enforcement_levels", {}).get("api_processing", {}).get("enabled", True)
    
    def _enhance_subtitle_list(self, subtitles: list) -> list:
        """强化字幕列表"""
        if not self.fixer:
            return subtitles
        
        enhanced_subtitles = []
        for subtitle in subtitles:
            if isinstance(subtitle, dict) and "text" in subtitle:
                enhanced_subtitle = subtitle.copy()
                enhanced_subtitle["text"] = self.fixer.optimize_subtitle_text(subtitle["text"])
                enhanced_subtitle["_enhanced"] = True
                enhanced_subtitles.append(enhanced_subtitle)
            else:
                enhanced_subtitles.append(subtitle)
        
        return enhanced_subtitles
    
    def _enhance_subtitle_segments(self, segments: list) -> list:
        """强化字幕片段"""
        if not self.fixer:
            return segments
        
        enhanced_segments = []
        for segment in segments:
            if isinstance(segment, dict):
                enhanced_segment = segment.copy()
                
                # 处理各种可能的文本字段
                text_fields = ["content", "text", "script_content", "subtitle_text"]
                for field in text_fields:
                    if field in enhanced_segment and isinstance(enhanced_segment[field], str):
                        enhanced_segment[field] = self.fixer.optimize_subtitle_text(enhanced_segment[field])
                        enhanced_segment[f"_{field}_enhanced"] = True
                
                enhanced_segments.append(enhanced_segment)
            else:
                enhanced_segments.append(segment)
        
        return enhanced_segments
    
    def _enhance_subtitle_content(self, content: Any) -> Any:
        """强化字幕内容"""
        if not self.fixer:
            return content
        
        if isinstance(content, str):
            return self.fixer.optimize_subtitle_text(content)
        elif isinstance(content, dict):
            enhanced_content = content.copy()
            for key, value in content.items():
                if isinstance(value, str) and any(keyword in key.lower() for keyword in ["text", "content", "subtitle", "script"]):
                    enhanced_content[key] = self.fixer.optimize_subtitle_text(value)
            return enhanced_content
        elif isinstance(content, list):
            return [self._enhance_subtitle_content(item) for item in content]
        
        return content
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

# 装饰器工厂
def enhance_subtitle_api(project_dir: Path):
    """
    字幕API强化装饰器
    
    Usage:
        @enhance_subtitle_api(project_dir)
        def generate_subtitles():
            # API逻辑
            return response_data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原始API函数
            result = func(*args, **kwargs)
            
            # 应用多行修复强化
            try:
                middleware = MultilineFixEnhancementMiddleware(project_dir)
                
                if isinstance(result, dict):
                    result = middleware.enhance_subtitle_response(result)
                elif isinstance(result, tuple) and len(result) == 2:
                    # Flask风格响应 (data, status_code)
                    data, status = result
                    if isinstance(data, dict):
                        data = middleware.enhance_subtitle_response(data)
                    result = (data, status)
                
            except Exception as e:
                # 强化失败不应该影响API正常响应
                logging.warning(f"API字幕强化失败: {e}")
            
            return result
        
        return wrapper
    return decorator

# 批量强化处理函数
def batch_enhance_subtitle_files(subtitle_dir: Path, project_dir: Path) -> Dict[str, Any]:
    """
    批量强化字幕文件 - 用于离线处理
    
    Args:
        subtitle_dir: 字幕文件目录
        project_dir: 项目目录
    
    Returns:
        处理结果统计
    """
    try:
        from .subtitle_multiline_fixer import SubtitleMultilineFixer
        
        fixer = SubtitleMultilineFixer()
        logger = logging.getLogger(__name__)
        
        # 查找所有字幕文件
        subtitle_files = []
        for ext in ['.srt', '.ass', '.vtt']:
            subtitle_files.extend(subtitle_dir.glob(f"*{ext}"))
        
        if not subtitle_files:
            return {"success": True, "message": "未找到字幕文件", "processed": 0}
        
        # 批量处理
        results = {
            "total_files": len(subtitle_files),
            "processed": 0,
            "enhanced": 0,
            "errors": 0,
            "files": []
        }
        
        for subtitle_file in subtitle_files:
            try:
                # 生成强化版文件名
                enhanced_name = f"{subtitle_file.stem}_enhanced{subtitle_file.suffix}"
                enhanced_path = subtitle_file.parent / enhanced_name
                
                # 读取原文件
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单的文本替换强化（针对SRT格式）
                if subtitle_file.suffix.lower() == '.srt':
                    enhanced_content = _enhance_srt_content(content, fixer)
                    
                    # 保存强化版
                    with open(enhanced_path, 'w', encoding='utf-8') as f:
                        f.write(enhanced_content)
                    
                    results["enhanced"] += 1
                    results["files"].append({
                        "original": subtitle_file.name,
                        "enhanced": enhanced_name,
                        "status": "success"
                    })
                
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"处理字幕文件失败 {subtitle_file.name}: {e}")
                results["errors"] += 1
                results["files"].append({
                    "original": subtitle_file.name,
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"批量字幕强化完成: {results['enhanced']}/{results['total_files']} 个文件")
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _enhance_srt_content(content: str, fixer) -> str:
    """强化SRT内容"""
    import re
    
    # 分割SRT条目
    entries = re.split(r'\n\s*\n', content.strip())
    enhanced_entries = []
    
    for entry in entries:
        if not entry.strip():
            continue
        
        lines = entry.strip().split('\n')
        if len(lines) >= 3:
            # SRT格式: 序号, 时间轴, 字幕文本
            subtitle_text = '\n'.join(lines[2:])
            
            # 应用多行修复
            fixed_text = fixer.optimize_subtitle_text(subtitle_text)
            
            # 重建条目
            enhanced_entry = '\n'.join(lines[:2] + [fixed_text])
            enhanced_entries.append(enhanced_entry)
    
    return '\n\n'.join(enhanced_entries) + '\n'