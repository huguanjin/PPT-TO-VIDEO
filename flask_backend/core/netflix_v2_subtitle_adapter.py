"""
Netflix V2字幕生成器适配器 - Phase 4工作流集成
为现有PPT转视频工作流提供Netflix V2字幕生成能力
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union
import logging

from .netflix_v2_subtitle_generator import NetflixV2SubtitleGenerator


class NetflixV2SubtitleAdapter:
    """
    Netflix V2字幕生成器适配器
    
    功能:
    - 适配现有step04_subtitle_generator_enhanced接口
    - 提供Netflix配置动态切换
    - 保持向后兼容性
    - 集成配置验证流程
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.logger = logging.getLogger(__name__)
        
        # 初始化Netflix V2字幕生成器
        self.netflix_generator = None
        self.current_netflix_config = None
        
        # 适配器状态
        self.is_netflix_mode = False
        self.validation_enabled = True
        
        self.logger.info("Netflix V2字幕生成器适配器初始化")
    
    def set_netflix_config(self, config_name: Optional[str] = None) -> bool:
        """
        设置Netflix配置
        
        Args:
            config_name: Netflix配置名称，None表示使用默认配置
            
        Returns:
            是否设置成功
        """
        try:
            # 创建或更新Netflix生成器
            if self.netflix_generator is None:
                self.netflix_generator = NetflixV2SubtitleGenerator(
                    self.project_dir, 
                    netflix_config_name=config_name
                )
            else:
                if config_name:
                    success = self.netflix_generator.switch_netflix_config(config_name)
                    if not success:
                        self.logger.error(f"切换Netflix配置失败: {config_name}")
                        return False
            
            self.current_netflix_config = config_name or "default"
            self.is_netflix_mode = True
            
            self.logger.info(f"Netflix配置设置成功: {self.current_netflix_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置Netflix配置失败: {e}")
            return False
    
    def disable_netflix_mode(self):
        """禁用Netflix模式，回退到传统字幕生成"""
        self.is_netflix_mode = False
        self.logger.info("已禁用Netflix模式，回退到传统字幕生成")
    
    def get_netflix_config_status(self) -> Dict[str, Any]:
        """
        获取Netflix配置状态
        
        Returns:
            配置状态信息
        """
        if not self.netflix_generator:
            return {
                "netflix_enabled": False,
                "config_name": None,
                "validation_status": None
            }
        
        return {
            "netflix_enabled": self.is_netflix_mode,
            "config_name": self.current_netflix_config,
            "available_configs": self.netflix_generator.get_available_netflix_configs(),
            "available_templates": self.netflix_generator.get_netflix_templates(),
            "validation_status": self.netflix_generator.validate_current_netflix_config(),
            "config_summary": self.netflix_generator.get_current_config_summary()
        }
    
    async def generate_subtitles_with_netflix_config(
        self,
        scripts_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        word_level_data: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        netflix_config_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用Netflix配置生成字幕
        
        Args:
            scripts_data: 脚本数据
            audio_data: 音频数据
            word_level_data: 词级别时间数据（可选）
            progress_callback: 进度回调函数
            netflix_config_name: Netflix配置名称（可选）
            
        Returns:
            字幕生成结果
        """
        try:
            self.logger.info("开始Netflix V2字幕生成流程")
            
            # 如果指定了配置名称，切换配置
            if netflix_config_name and netflix_config_name != self.current_netflix_config:
                if not self.set_netflix_config(netflix_config_name):
                    raise ValueError(f"无法设置Netflix配置: {netflix_config_name}")
            
            # 确保Netflix生成器已初始化
            if not self.netflix_generator:
                if not self.set_netflix_config():
                    raise ValueError("Netflix生成器初始化失败")
            
            # 配置验证（如果启用）
            if self.validation_enabled and self.netflix_generator:
                validation_result = self.netflix_generator.validate_current_netflix_config()
                if not validation_result.get("valid", False):
                    self.logger.warning(f"Netflix配置验证警告: {validation_result.get('errors', [])}")
                    # 可以选择继续或停止，这里选择继续但记录警告
            
            # 生成字幕
            if self.netflix_generator:
                result = await self.netflix_generator.generate_enhanced_subtitles(
                    scripts_data=scripts_data,
                    audio_data=audio_data,
                    word_level_data=word_level_data,
                    progress_callback=progress_callback
                )
            else:
                raise ValueError("Netflix生成器未初始化")
            
            # 添加适配器信息
            result.update({
                "adapter_version": "1.0",
                "netflix_config_adapter": True,
                "netflix_config_used": self.current_netflix_config,
                "netflix_mode_enabled": self.is_netflix_mode
            })
            
            self.logger.info("Netflix V2字幕生成完成")
            return result
            
        except Exception as e:
            self.logger.error(f"Netflix字幕生成失败: {e}", exc_info=True)
            raise
    
    async def generate_subtitles_adaptive(
        self,
        scripts_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        word_level_data: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        subtitle_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        自适应字幕生成 - 根据配置选择Netflix或传统模式
        
        Args:
            scripts_data: 脚本数据
            audio_data: 音频数据
            word_level_data: 词级别时间数据（可选）
            progress_callback: 进度回调函数
            subtitle_config: 字幕配置（包含Netflix配置信息）
            
        Returns:
            字幕生成结果
        """
        try:
            # 检查是否启用Netflix模式
            netflix_enabled = False
            netflix_config_name = None
            
            if subtitle_config:
                netflix_enabled = subtitle_config.get("use_enhanced_mode", False)
                netflix_config_name = subtitle_config.get("netflix_config_name")
            
            if netflix_enabled and self.is_netflix_mode:
                # 使用Netflix V2生成器
                self.logger.info("使用Netflix V2增强字幕生成")
                return await self.generate_subtitles_with_netflix_config(
                    scripts_data=scripts_data,
                    audio_data=audio_data,
                    word_level_data=word_level_data,
                    progress_callback=progress_callback,
                    netflix_config_name=netflix_config_name
                )
            else:
                # 使用传统字幕生成器
                self.logger.info("使用传统字幕生成")
                return await self._generate_traditional_subtitles(
                    scripts_data=scripts_data,
                    audio_data=audio_data,
                    word_level_data=word_level_data,
                    progress_callback=progress_callback,
                    subtitle_config=subtitle_config
                )
                
        except Exception as e:
            self.logger.error(f"自适应字幕生成失败: {e}", exc_info=True)
            raise
    
    async def _generate_traditional_subtitles(
        self,
        scripts_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        word_level_data: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        subtitle_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        传统字幕生成的后备实现
        """
        try:
            # 导入传统的字幕生成器
            from .step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator
            
            traditional_generator = EnhancedSubtitleGenerator(self.project_dir)
            
            # 应用字幕配置
            if subtitle_config:
                traditional_generator.update_config(subtitle_config)
            
            # 生成字幕
            result = await traditional_generator.generate_enhanced_subtitles(
                scripts_data=scripts_data,
                audio_data=audio_data,
                word_level_data=word_level_data,
                progress_callback=progress_callback
            )
            
            # 添加适配器标识
            result.update({
                "adapter_version": "1.0",
                "netflix_config_adapter": False,
                "traditional_mode": True
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"传统字幕生成失败: {e}", exc_info=True)
            raise
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """获取适配器信息"""
        return {
            "adapter_version": "1.0",
            "project_dir": str(self.project_dir),
            "netflix_mode_available": self.netflix_generator is not None,
            "netflix_mode_enabled": self.is_netflix_mode,
            "current_netflix_config": self.current_netflix_config,
            "validation_enabled": self.validation_enabled,
            "status": self.get_netflix_config_status()
        }