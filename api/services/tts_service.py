"""
TTS服务层
"""
from typing import Dict, Any, List, Optional
import asyncio
from pathlib import Path
import importlib.util
import sys

from .base import BaseService, ServiceResult

class TTSService(BaseService):
    """TTS服务管理器"""
    
    def _initialize(self) -> None:
        """初始化TTS服务"""
        self.tts_engines = {}
        self.current_engine = "edge_tts"  # 默认引擎
        self._load_tts_engines()
    
    def _load_tts_engines(self) -> None:
        """加载TTS引擎"""
        try:
            # 动态加载TTS引擎
            tts_path = Path(__file__).parent.parent.parent / "all_tts_functions"
            
            # 预定义的TTS引擎映射
            engine_files = {
                "edge_tts": "edge_tts.py",
                "fish_tts": "fish_tts.py", 
                "azure_tts": "azure_tts.py",
                "openai_tts": "openai_tts.py",
                "gpt_sovits_tts": "gpt_sovits_tts.py",
                "siliconflow_fish_tts": "siliconflow_fish_tts.py"
            }
            
            for engine_name, filename in engine_files.items():
                engine_path = tts_path / filename
                if engine_path.exists():
                    try:
                        spec = importlib.util.spec_from_file_location(engine_name, engine_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self.tts_engines[engine_name] = module
                        self.logger.info(f"已加载TTS引擎: {engine_name}")
                    except Exception as e:
                        self.logger.error(f"加载TTS引擎失败 {engine_name}: {e}")
                
        except Exception as e:
            self.logger.error(f"TTS引擎初始化失败: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "service": "TTS",
            "status": "healthy",
            "engines_loaded": len(self.tts_engines),
            "available_engines": list(self.tts_engines.keys()),
            "current_engine": self.current_engine
        }
    
    def get_available_engines(self) -> ServiceResult:
        """获取可用的TTS引擎"""
        try:
            engines = []
            for engine_name, module in self.tts_engines.items():
                engine_info = {
                    "name": engine_name,
                    "display_name": getattr(module, "DISPLAY_NAME", engine_name),
                    "description": getattr(module, "DESCRIPTION", ""),
                    "supported_languages": getattr(module, "SUPPORTED_LANGUAGES", ["zh-CN"])
                }
                engines.append(engine_info)
            
            return ServiceResult.success_result(engines)
            
        except Exception as e:
            self.logger.error(f"获取TTS引擎失败: {e}")
            return ServiceResult.error_result(f"获取TTS引擎失败: {e}")
    
    def set_current_engine(self, engine_name: str) -> ServiceResult:
        """设置当前TTS引擎"""
        try:
            if engine_name not in self.tts_engines:
                return ServiceResult.error_result(f"TTS引擎不存在: {engine_name}", 404)
            
            self.current_engine = engine_name
            self.logger.info(f"已切换到TTS引擎: {engine_name}")
            
            return ServiceResult.success_result({"current_engine": engine_name})
            
        except Exception as e:
            self.logger.error(f"设置TTS引擎失败: {e}")
            return ServiceResult.error_result(f"设置TTS引擎失败: {e}")
    
    async def generate_audio(self, text: str, voice: str = None, output_path: str = None, 
                           engine: str = None) -> ServiceResult:
        """生成音频"""
        try:
            target_engine = engine or self.current_engine
            
            if target_engine not in self.tts_engines:
                return ServiceResult.error_result(f"TTS引擎不存在: {target_engine}", 404)
            
            tts_module = self.tts_engines[target_engine]
            
            # 根据不同引擎调用不同的生成函数
            if hasattr(tts_module, "generate_speech_async"):
                result = await tts_module.generate_speech_async(text, voice, output_path)
            elif hasattr(tts_module, "generate_speech"):
                # 同步函数包装为异步
                result = await asyncio.to_thread(tts_module.generate_speech, text, voice, output_path)
            else:
                return ServiceResult.error_result(f"TTS引擎 {target_engine} 缺少生成函数")
            
            return ServiceResult.success_result({
                "audio_path": result,
                "engine": target_engine,
                "text_length": len(text)
            })
            
        except Exception as e:
            self.logger.error(f"TTS生成失败: {e}")
            return ServiceResult.error_result(f"TTS生成失败: {e}")
    
    def get_engine_config(self, engine_name: str = None) -> ServiceResult:
        """获取引擎配置"""
        try:
            target_engine = engine_name or self.current_engine
            
            if target_engine == "fish_tts":
                config = self.get_config("fish_tts")
            else:
                config = self.get_config("tts", target_engine)
            
            return ServiceResult.success_result({
                "engine": target_engine,
                "config": config
            })
            
        except Exception as e:
            self.logger.error(f"获取引擎配置失败: {e}")
            return ServiceResult.error_result(f"获取引擎配置失败: {e}")
    
    def update_engine_config(self, config_updates: Dict[str, Any], 
                           engine_name: str = None) -> ServiceResult:
        """更新引擎配置"""
        try:
            target_engine = engine_name or self.current_engine
            
            if target_engine == "fish_tts":
                success = self.update_config("fish_tts", config_updates)
            else:
                current_config = self.get_config("tts") or {}
                current_config[target_engine] = config_updates
                success = self.update_config("tts", current_config)
            
            if success:
                return ServiceResult.success_result({
                    "engine": target_engine,
                    "updated": True
                })
            else:
                return ServiceResult.error_result("配置更新失败")
                
        except Exception as e:
            self.logger.error(f"更新引擎配置失败: {e}")
            return ServiceResult.error_result(f"更新引擎配置失败: {e}")
