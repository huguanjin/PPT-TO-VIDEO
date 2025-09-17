"""
增强型AI内容优化器
集成自适应字体和语义分割功能
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import re

from .ai_content_optimizer import AIContentOptimizer
from .adaptive_font_calculator import AdaptiveFontSizeCalculator, get_adaptive_subtitle_config
from .enhanced_semantic_splitter import EnhancedSemanticSplitter
from app.utils.logger import get_logger

class EnhancedAIContentOptimizer(AIContentOptimizer):
    """增强型AI内容优化器 - 集成自适应字体和语义分割"""
    
    def __init__(self, project_dir: Path, ai_config: Optional[Dict[str, Any]] = None, 
                 video_config: Optional[Dict[str, Any]] = None):
        super().__init__(project_dir, ai_config)
        
        # 视频配置
        self.video_config = video_config or {}
        
        # 初始化新组件
        self.font_calculator = AdaptiveFontSizeCalculator()
        self.semantic_splitter = EnhancedSemanticSplitter()
        
        # 更新优化配置以使用新的参数
        self.optimization_config.update({
            "max_chars_per_segment": 26,        # 统一为26字符
            "enable_adaptive_font": True,       # 启用自适应字体
            "enable_semantic_splitting": True,  # 启用语义分割
            "protect_special_content": True,    # 保护特殊内容
        })
        
        self.logger.info("✅ 增强型AI内容优化器初始化完成")
    
    async def optimize_scripts_content_enhanced(self, scripts_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强版内容优化处理
        
        Args:
            scripts_data: 原始讲话稿数据
            
        Returns:
            优化后的分段讲话稿数据，包含自适应字体配置
        """
        try:
            self.logger.info("🚀 开始增强型AI内容优化处理")
            
            scripts = scripts_data.get("scripts", [])
            optimized_scripts = []
            
            # 获取视频分辨率
            resolution = self._get_video_resolution()
            
            for script in scripts:
                slide_number = script["slide_number"]
                original_content = script["script_content"]
                
                if not original_content or not original_content.strip():
                    # 空内容直接跳过
                    optimized_scripts.append(script)
                    continue
                
                self.logger.info(f"🎯 优化第 {slide_number} 页内容: {original_content[:30]}...")
                
                # 增强型单个脚本优化
                optimized_segments = await self._optimize_single_script_enhanced(
                    original_content, slide_number, resolution
                )
                
                # 生成优化后的脚本数据
                for i, segment in enumerate(optimized_segments):
                    segment_script = {
                        "slide_number": slide_number,
                        "segment_index": i + 1,
                        "script_content": segment["text"],
                        "word_count": len(segment["text"]),
                        "estimated_duration": segment["estimated_duration"],
                        "optimization_applied": True,
                        "original_content": original_content if i == 0 else "",
                        "segment_type": segment.get("type", "enhanced"),
                        # 新增字体配置
                        "font_config": segment.get("font_config", {}),
                        "subtitle_config": segment.get("subtitle_config", {}),
                        "semantic_quality": segment.get("semantic_quality", 0.8)
                    }
                    optimized_scripts.append(segment_script)
            
            # 生成增强优化后的数据结构
            optimized_data = {
                "scripts": optimized_scripts,
                "total_scripts": len(optimized_scripts),
                "optimization_applied": True,
                "enhancement_level": "advanced",
                "optimization_timestamp": datetime.now().isoformat(),
                "optimization_config": self.optimization_config.copy(),
                "video_config": {
                    "resolution": resolution,
                    "adaptive_font_enabled": True,
                    "semantic_splitting_enabled": True
                },
                "ai_config_used": {
                    "service_type": self.ai_config.get('service_type', 'unknown'),
                    "model": self.ai_config.get('model', 'unknown'),
                    "semantic_model": "gemini-2.0-flash"
                }
            }
            
            self.logger.info(f"✅ 增强型AI内容优化完成: {len(scripts)} 页 → {len(optimized_scripts)} 段")
            return optimized_data
            
        except Exception as e:
            self.logger.error(f"❌ 增强型AI内容优化失败: {e}")
            # 返回原始数据
            return scripts_data
    
    async def _optimize_single_script_enhanced(
        self, 
        content: str, 
        slide_number: int, 
        resolution: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """
        增强版单个讲话稿优化
        
        Args:
            content: 原始内容
            slide_number: 页码
            resolution: 视频分辨率
            
        Returns:
            优化后的分段列表
        """
        try:
            # 清理内容
            content = self._clean_content(content)
            
            # 1. 语义感知分割
            lines = await self._semantic_aware_split(content)
            
            # 2. 为每行计算最优配置
            segments = []
            for i, line in enumerate(lines):
                # 计算自适应字体配置
                subtitle_config = get_adaptive_subtitle_config(
                    line, resolution, video_duration=None
                )
                
                # 估算时长
                estimated_duration = max(
                    len(line) / self.optimization_config["target_reading_speed"], 
                    1.0
                )
                
                segment = {
                    "text": line,
                    "char_count": len(line),
                    "estimated_duration": estimated_duration,
                    "type": "enhanced_semantic",
                    "font_config": {
                        "font_size": subtitle_config["font_size"],
                        "adaptive": True
                    },
                    "subtitle_config": subtitle_config,
                    "semantic_quality": 0.9,  # 高质量语义分割
                    "line_index": i + 1,
                    "total_lines": len(lines)
                }
                
                segments.append(segment)
            
            self.logger.info(f"✅ 第 {slide_number} 页优化成功: {len(segments)} 个语义段")
            return segments
            
        except Exception as e:
            self.logger.error(f"❌ 单个讲话稿增强优化失败: {e}")
            # 使用原始优化方法作为备用
            return await super()._optimize_single_script(content, slide_number)
    
    async def _semantic_aware_split(self, content: str) -> List[str]:
        """语义感知的分割"""
        try:
            if self.optimization_config.get("enable_semantic_splitting", True):
                # 使用增强语义分割器
                lines = await self.semantic_splitter.split_with_semantic_awareness(content)
                
                if lines and len(lines) > 0:
                    self.logger.info(f"🎯 语义分割成功: {len(lines)} 行")
                    return lines
            
            # 备用：使用父类的方法
            self.logger.info("使用备用分割方案")
            return await self._fallback_segmentation(content)
            
        except Exception as e:
            self.logger.error(f"语义分割失败: {e}")
            return [content]  # 最后的保底
    
    def _get_video_resolution(self) -> Tuple[int, int]:
        """获取视频分辨率"""
        try:
            # 从视频配置获取
            resolution_str = self.video_config.get("resolution", "1920x1080")
            
            if "x" in resolution_str:
                width, height = map(int, resolution_str.split("x"))
                return (width, height)
            
            # 默认1080p
            return (1920, 1080)
            
        except Exception as e:
            self.logger.error(f"获取分辨率失败: {e}")
            return (1920, 1080)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            "adaptive_font_enabled": self.optimization_config.get("enable_adaptive_font", False),
            "semantic_splitting_enabled": self.optimization_config.get("enable_semantic_splitting", False),
            "max_chars_per_segment": self.optimization_config.get("max_chars_per_segment", 26),
            "font_calculator_available": self.font_calculator is not None,
            "semantic_splitter_available": self.semantic_splitter is not None,
            "ai_model_available": self.ai_client is not None
        }


# 便捷函数
async def optimize_content_with_enhancements(
    scripts_data: Dict[str, Any],
    project_dir: Path,
    ai_config: Optional[Dict[str, Any]] = None,
    video_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    使用增强功能优化内容的便捷函数
    
    Args:
        scripts_data: 脚本数据
        project_dir: 项目目录
        ai_config: AI配置
        video_config: 视频配置
        
    Returns:
        优化后的数据
    """
    optimizer = EnhancedAIContentOptimizer(project_dir, ai_config, video_config)
    return await optimizer.optimize_scripts_content_enhanced(scripts_data)


if __name__ == "__main__":
    # 测试用例
    async def test_enhanced_optimizer():
        from pathlib import Path
        
        # 测试数据
        test_scripts = {
            "scripts": [
                {
                    "slide_number": 1,
                    "script_content": "欢迎使用PPT转视频工具，请访问https://www.example.com了解更多信息"
                },
                {
                    "slide_number": 2,
                    "script_content": "本工具支持多种格式，包括API接口调用和JSON数据处理功能"
                }
            ]
        }
        
        # AI配置
        ai_config = {
            "service_type": "custom",
            "api_key": "test-key",
            "base_url": "https://test-api.com",
            "model": "test-model"
        }
        
        # 视频配置
        video_config = {
            "resolution": "1920x1080",
            "fps": 30
        }
        
        # 测试优化
        optimizer = EnhancedAIContentOptimizer(
            Path("./test"), ai_config, video_config
        )
        
        result = await optimizer.optimize_scripts_content_enhanced(test_scripts)
        
        print("优化结果:")
        for script in result["scripts"]:
            print(f"  页面 {script['slide_number']}: {script['script_content']}")
            if "font_config" in script:
                print(f"    字体大小: {script['font_config'].get('font_size', 'N/A')}")
            print()
    
    # 运行测试
    # asyncio.run(test_enhanced_optimizer())