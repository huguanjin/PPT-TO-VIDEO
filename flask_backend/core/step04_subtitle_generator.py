"""
步骤4: 字幕生成器
基于讲话稿内容和音频时间轴生成SRT字幕文件
支持传统模式和Netflix级增强模式
"""
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
import logging
import re
import html

import pysrt

from app.utils.logger import get_logger
from app.utils.file_manager import FileManager

# 导入增强版字幕生成器
try:
    from core.step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator
    ENHANCED_SUBTITLE_AVAILABLE = True
except ImportError:
    ENHANCED_SUBTITLE_AVAILABLE = False

# 暂时禁用所有高级功能模块以避免NumPy兼容性问题
ENHANCED_SEMANTIC_SPLITTER_AVAILABLE = False
VIDEO_FRAME_SYNC_AVAILABLE = False  
AUDIO_INTELLIGENT_SYNC_AVAILABLE = False
AI_CONTENT_UNDERSTANDING_AVAILABLE = False
PHASE3_INTELLIGENT_ALIGNMENT_AVAILABLE = False

print("🔧 已禁用所有高级功能模块，专注测试单行模式配置")

# 临时VideoMetadata类定义，用于兼容性
class VideoMetadata:
    """临时视频元数据类，用于兼容性"""
    def __init__(self, width: int = 1920, height: int = 1080, fps: float = 24.0, 
                 duration: float = 300.0, total_frames: int = 0, 
                 codec: str = 'h264', bitrate: int = 5000000):
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.total_frames = total_frames
        self.codec = codec
        self.bitrate = bitrate

# 类型检查导入
if TYPE_CHECKING:
    try:
        from core.intelligent_alignment_system import AlignmentReport
    except ImportError:
        pass

class SubtitleGenerator:
    """字幕生成器 - 支持传统和增强模式"""
    
    # 类型注解
    frame_sync_optimizer: Optional[Any]
    audio_sync_optimizer: Optional[Any]
    semantic_alignment_optimizer: Optional[Any]
    intelligent_alignment_system: Optional[Any]
    
    def __init__(self, project_dir: Path, use_enhanced: bool = False, enable_frame_sync: bool = True, 
                 enable_audio_sync: bool = True, enable_ai_content_understanding: bool = False,
                 enable_phase3_alignment: bool = False):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # 根据配置和依赖可用性决定是否启用AI功能
        try:
            # 尝试加载应用配置
            app_config_path = self.project_dir / "flask_backend" / "config_data" / "app_config.json"
            if app_config_path.exists():
                import json
                with open(app_config_path, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
                
                # 从配置文件读取功能开关
                features = app_config.get("features", {})
                ai_models = app_config.get("ai_models", {})
                
                self.use_enhanced = features.get("enhanced_subtitle_generation", True)
                self.enable_frame_sync = features.get("video_frame_sync", True)
                self.enable_audio_sync = features.get("audio_intelligent_sync", True)
                self.enable_ai_content_understanding = features.get("ai_semantic_enhancement", True)
                self.enable_phase3_alignment = features.get("phase3_integration", True)
                
                # 检查是否强制启用AI模式
                force_ai_mode = ai_models.get("force_ai_mode", False)
                if force_ai_mode:
                    self.use_enhanced = True
                    self.enable_ai_content_understanding = True
                
                if self.use_enhanced or self.enable_ai_content_understanding:
                    self.logger.info("🤖 字幕生成器启动 - 完整AI模式（所有高级功能已启用）")
                else:
                    self.logger.info("🚀 字幕生成器启动 - 基础模式")
            else:
                # 配置文件不存在时的默认设置
                self.use_enhanced = use_enhanced
                self.enable_frame_sync = enable_frame_sync
                self.enable_audio_sync = enable_audio_sync
                self.enable_ai_content_understanding = enable_ai_content_understanding
                self.enable_phase3_alignment = enable_phase3_alignment
                self.logger.info("🚀 字幕生成器启动 - 使用默认配置")
                
        except Exception as e:
            self.logger.warning(f"配置加载失败，使用默认设置: {e}")
            self.use_enhanced = use_enhanced
            self.enable_frame_sync = enable_frame_sync
            self.enable_audio_sync = enable_audio_sync
            self.enable_ai_content_understanding = enable_ai_content_understanding
            self.enable_phase3_alignment = enable_phase3_alignment
        
        # 加载智能字幕配置
        try:
            from core.subtitle_config_loader import create_config_loader
            smart_config_loader = create_config_loader(
                config_dir=self.project_dir / "config_data"
            )
            smart_config = smart_config_loader.get_config()
            self.logger.info("成功加载智能字幕配置，AI分割功能已启用")
        except Exception as e:
            self.logger.warning(f"加载智能字幕配置失败，使用默认配置: {e}")
            smart_config = {
                "enabled": True,
                "max_length": 75,
                "target_multiplier": 1.2,
                "smart_split": True,
                "use_ai_splitting": False
            }
        
        # 字幕配置 - 从统一配置管理器获取
        try:
            from app.utils.config_manager import config_manager
            unified_subtitle_config = config_manager.get_subtitle_config()
            max_chars_per_line = unified_subtitle_config.get("max_chars_per_line", 36)
            self.logger.info(f"从统一配置管理器获取字符限制: {max_chars_per_line}")
        except Exception as e:
            self.logger.warning(f"获取统一配置失败，使用默认值: {e}")
            max_chars_per_line = 36  # 使用与前端一致的默认值
        
        # 加载单行模式配置
        self.single_line_mode = False
        self.single_line_config = {}
        try:
            # 🔧 修复配置文件路径：如果当前目录是output，则向上查找配置
            manual_config_path = self.project_dir / "flask_backend" / "config_data" / "manual_split_config.json"
            
            # 如果路径不存在，尝试从父目录查找（处理output目录的情况）
            if not manual_config_path.exists() and self.project_dir.name == "output":
                parent_project_dir = self.project_dir.parent.parent  # output -> flask_backend -> 项目根
                manual_config_path = parent_project_dir / "flask_backend" / "config_data" / "manual_split_config.json"
                self.logger.info(f"🔧 从父目录查找配置: {manual_config_path}")
            
            self.logger.info(f"🔍 尝试加载单行模式配置: {manual_config_path}")
            self.logger.info(f"🔍 配置文件存在: {manual_config_path.exists()}")
            
            if manual_config_path.exists():
                import json
                with open(manual_config_path, 'r', encoding='utf-8') as f:
                    manual_config = json.load(f)
                
                self.logger.info(f"🔍 配置文件加载成功")
                display_mode = manual_config.get("manual_split_config", {}).get("subtitle_display_mode", {})
                self.logger.info(f"🔍 subtitle_display_mode: {display_mode}")
                
                self.single_line_mode = display_mode.get("single_line_mode", False)
                self.single_line_config = display_mode.get("time_allocation", {
                    "method": "proportional",
                    "based_on": "character_count",
                    "min_line_duration": 1.0,
                    "max_line_duration": 8.0
                })
                
                self.logger.info(f"🔍 解析出 single_line_mode: {self.single_line_mode} (类型: {type(self.single_line_mode)})")
                
                # 🔥 强制调试：确保配置正确解析
                if self.single_line_mode:
                    self.logger.info("✅ 单行字幕模式已启用 - 多行字幕将被拆分为连续单行")
                    self.logger.info("🔧 强制设置 single_line_mode = True")
                else:
                    # 如果配置文件中是 true 但这里还是 False，需要强制修正
                    raw_single_line = display_mode.get("single_line_mode")
                    self.logger.warning(f"⚠️ single_line_mode 配置异常！原始值: {raw_single_line} (类型: {type(raw_single_line)})")
                    
                    # 强制转换为布尔值
                    if raw_single_line is True or str(raw_single_line).lower() == 'true':
                        self.single_line_mode = True
                        self.logger.info("🔧 强制修正 single_line_mode = True")
                    else:
                        self.logger.info("📝 多行字幕模式 - 保持原有换行显示")
            else:
                self.logger.warning(f"🔍 配置文件不存在: {manual_config_path}")
        except Exception as e:
            self.logger.error(f"读取单行模式配置失败: {e}")
            import traceback
            self.logger.error(f"异常详情: {traceback.format_exc()}")
            self.single_line_mode = False

        self.subtitle_config = {
            "max_chars_per_line": 28 if self.single_line_mode else max_chars_per_line,  # 单行模式下使用更严格的限制
            "max_lines": 2 if not self.single_line_mode else 1,  # 根据single_line_mode动态设置
            "min_display_time": 1.0,      # 最小显示时间1秒，确保可读性
            "max_display_time": 8.0,      # 合理的最大显示时间
            "words_per_second": 3.5,      # 标准阅读速度
            "line_break_chars": "。！？；",    # 主要断句标点（移除逗号避免过度分割）
            "use_enhanced_mode": self.use_enhanced,  # 是否使用增强模式
            
            # 智能字幕处理配置
            "smart_processing": smart_config
        }
        
        # 智能断句系统启用逻辑 - 根据配置决定
        try:
            # 检查配置是否禁用Flask重载问题规避
            subtitle_config_path = self.project_dir / "flask_backend" / "config_data" / "subtitle_multiline_fix_config.json"
            disable_for_flask = True  # 默认禁用
            
            if subtitle_config_path.exists():
                import json
                with open(subtitle_config_path, 'r', encoding='utf-8') as f:
                    subtitle_config = json.load(f)
                
                intelligent_breaking = subtitle_config.get("intelligent_sentence_breaking", {})
                disable_for_flask = intelligent_breaking.get("disable_for_flask", False)
            
            if not disable_for_flask and self.use_enhanced:
                self.logger.info("✅ 智能断句系统已启用（完整功能模式）")
                # 这里可以初始化智能断句相关组件
                self.smart_processor = None  # 实际实现时替换为真实组件
                self.hybrid_splitter = None
                self.smart_integrator = None
                self.multiline_fixer = None
            else:
                self.logger.info("⚠️ 智能断句系统已禁用以避免Flask重载问题")
                self.logger.info("⚠️ 使用轻量级断句模式确保稳定运行")
                self.smart_processor = None
                self.hybrid_splitter = None
                self.smart_integrator = None
                self.multiline_fixer = None
                
        except Exception as e:
            self.logger.warning(f"智能断句系统配置加载失败: {e}")
            # 🔧 临时禁用智能字幕处理器以避免Flask重载问题
            # jieba分词器会触发Flask自动重载，导致字幕生成卡死
            self.logger.info("⚠️ 智能断句系统已禁用以避免Flask重载问题")
            self.logger.info("⚠️ 使用轻量级断句模式确保稳定运行")
            
            self.smart_processor = None
            self.hybrid_splitter = None
            self.smart_integrator = None
            self.multiline_fixer = None
        
        # 初始化增强版生成器
        if self.use_enhanced:
            if ENHANCED_SUBTITLE_AVAILABLE:
                self.enhanced_generator = EnhancedSubtitleGenerator(project_dir)
                self.logger.info("✅ Netflix级增强字幕生成器已启用")
            else:
                self.enhanced_generator = None
                self.logger.warning("增强版字幕生成器不可用，将使用传统模式")
        else:
            self.enhanced_generator = None
            self.logger.info("使用传统字幕生成模式")
        
        # 初始化视频帧同步优化器
        if self.enable_frame_sync and VIDEO_FRAME_SYNC_AVAILABLE:
            try:
                config_path = self.project_dir / "flask_backend" / "config_data" / "video_frame_sync_config.json"
                # VideoFrameSyncOptimizer类暂时不可用
                # self.frame_sync_optimizer = VideoFrameSyncOptimizer(str(config_path) if config_path.exists() else None)
                self.frame_sync_optimizer = None
                self.logger.info("🎨 视频帧级同步优化器已启用")
            except Exception as e:
                self.logger.warning(f"视频帧同步优化器初始化失败，将跳过帧同步: {e}")
                self.frame_sync_optimizer = None
                self.enable_frame_sync = False
        else:
            self.frame_sync_optimizer = None
            if not VIDEO_FRAME_SYNC_AVAILABLE:
                self.logger.info("视频帧同步优化器不可用")

        # 初始化音频智能同步优化器
        if self.enable_audio_sync and AUDIO_INTELLIGENT_SYNC_AVAILABLE:
            try:
                config_path = self.project_dir / "flask_backend" / "config_data" / "audio_intelligent_sync_config.json"
                # AudioIntelligentSyncOptimizer类暂时不可用
                # self.audio_sync_optimizer = AudioIntelligentSyncOptimizer(str(config_path) if config_path.exists() else None)
                self.audio_sync_optimizer = None
                self.logger.info("🎵 音频智能同步优化器已启用")
            except Exception as e:
                self.logger.warning(f"音频智能同步优化器初始化失败，将跳过音频同步: {e}")
                self.audio_sync_optimizer = None
                self.enable_audio_sync = False
        else:
            self.audio_sync_optimizer = None
            if not AUDIO_INTELLIGENT_SYNC_AVAILABLE:
                self.logger.info("音频智能同步优化器不可用")

        # 初始化AI内容理解增强系统
        if self.enable_ai_content_understanding and AI_CONTENT_UNDERSTANDING_AVAILABLE:
            try:
                config_path = self.project_dir / "flask_backend" / "config_data" / "ai_content_understanding_config.json"
                # SemanticAlignmentOptimizer类暂时不可用
                # self.semantic_alignment_optimizer = SemanticAlignmentOptimizer(str(config_path) if config_path.exists() else None)
                self.semantic_alignment_optimizer = None
                self.logger.info("🤖 AI内容理解增强系统已启用")
            except Exception as e:
                self.logger.warning(f"AI内容理解系统初始化失败，将跳过语义对齐: {e}")
                self.semantic_alignment_optimizer = None
                self.enable_ai_content_understanding = False
        else:
            self.semantic_alignment_optimizer = None
            if not AI_CONTENT_UNDERSTANDING_AVAILABLE:
                self.logger.info("AI内容理解增强系统不可用")

        # 初始化Phase 3智能对齐系统
        if self.enable_phase3_alignment and PHASE3_INTELLIGENT_ALIGNMENT_AVAILABLE:
            try:
                # 创建智能对齐系统配置
                # IntelligentAlignmentConfig和IntelligentAlignmentSystem类暂时不可用
                # alignment_config = IntelligentAlignmentConfig()
                # self.intelligent_alignment_system = IntelligentAlignmentSystem(alignment_config)
                self.intelligent_alignment_system = None
                self.logger.info("✅ Phase 3智能对齐系统已启用")
            except Exception as e:
                self.logger.warning(f"Phase 3智能对齐系统初始化失败，将跳过智能对齐: {e}")
                self.intelligent_alignment_system = None
                self.enable_phase3_alignment = False
        else:
            self.intelligent_alignment_system = None
            if not PHASE3_INTELLIGENT_ALIGNMENT_AVAILABLE:
                self.logger.info("Phase 3智能对齐系统不可用")
            else:
                self.logger.info("Phase 3智能对齐系统已禁用")
    
    async def generate_subtitles(self, scripts_data: Dict[str, Any], audio_data: Dict[str, Any], 
                               progress_callback: Optional[Callable[[int], None]] = None,
                               word_level_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        生成所有页面的字幕文件 - 支持传统和Netflix级增强模式
        
        Args:
            scripts_data: 讲话稿数据
            audio_data: 音频数据
            progress_callback: 进度回调函数
            word_level_data: 词级别时间数据（用于增强模式）
            
        Returns:
            字幕数据字典
        """
        try:
            # 如果启用增强模式，直接使用增强生成器
            if self.use_enhanced and self.enhanced_generator:
                self.logger.info("使用Netflix级增强字幕生成模式")
                return await self.enhanced_generator.generate_enhanced_subtitles(
                    scripts_data, audio_data, word_level_data, progress_callback
                )
            
            # 传统字幕生成模式
            self.logger.info("使用传统字幕生成模式")
            return await self._generate_traditional_subtitles(
                scripts_data, audio_data, progress_callback
            )
            
        except Exception as e:
            self.logger.error(f"字幕生成失败: {e}", exc_info=True)
            raise
    
    async def _generate_traditional_subtitles(self, scripts_data: Dict[str, Any], audio_data: Dict[str, Any], 
                                           progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """
        传统字幕生成方法
        """
        try:
            self.logger.info("开始生成传统字幕文件")
            
            # 确保字幕目录存在
            self.file_manager.subtitles_dir.mkdir(parents=True, exist_ok=True)
            
            scripts = scripts_data.get("scripts", [])
            audio_files = audio_data.get("audio_files", [])
            total_scripts = len(scripts)
            
            # 创建音频文件映射，兼容不同的字段名
            audio_map = {}
            for audio in audio_files:
                # 尝试不同的字段名以兼容不同的数据格式
                key = audio.get("slide_number") or audio.get("script_id") or audio.get("slide_id")
                if key:
                    audio_map[key] = audio
            
            subtitle_data = {
                "subtitle_generation_completed": False,
                "generation_timestamp": datetime.now().isoformat(),
                "subtitle_config": self.subtitle_config.copy(),
                "subtitle_files": [],
                "combined_subtitle_info": None,
                "enhanced_features_used": False
            }
            
            # 用于合并字幕的全局字幕列表
            all_subtitles = []
            subtitle_index = 1
            
            for i, script in enumerate(scripts):
                if progress_callback:
                    progress = int((i / total_scripts) * 80)  # 80%用于单个字幕生成
                    progress_callback(progress)
                
                slide_id = script.get("slide_number") or script.get("slide_id") or script.get("script_id")
                self.logger.info(f"生成第 {slide_id} 页字幕")
                
                # 获取对应的音频信息
                audio_info = audio_map.get(slide_id)
                if not audio_info:
                    self.logger.warning(f"未找到第 {slide_id} 页的音频信息，跳过字幕生成")
                    continue
                
                # 生成单个字幕文件
                subtitle_info, slide_subtitles = await self._generate_single_subtitle(
                    script, audio_info, subtitle_index
                )
                subtitle_data["subtitle_files"].append(subtitle_info)
                
                # 添加到全局字幕列表
                all_subtitles.extend(slide_subtitles)
                subtitle_index += len(slide_subtitles)
                
                # 模拟处理延迟
                await asyncio.sleep(0.2)
            
            # 生成合并的字幕文件
            if progress_callback:
                progress_callback(85)
            
            # 应用视频帧同步优化
            if self.enable_frame_sync and self.frame_sync_optimizer and VIDEO_FRAME_SYNC_AVAILABLE:
                self.logger.info("🎨 开始视频帧级同步优化...")
                
                # 获取视频元数据（如果可用）
                video_metadata = await self._get_video_metadata_for_sync()
                
                if video_metadata:
                    # 转换字幕为同步格式
                    subtitle_segments = self._convert_subtitles_for_sync(all_subtitles)
                    
                    # 执行帧同步优化
                    synchronized_segments = self.frame_sync_optimizer.optimize_frame_sync(
                        subtitle_segments, video_metadata
                    )
                    
                    # 转换回字幕格式
                    all_subtitles = self._convert_sync_segments_to_subtitles(synchronized_segments)
                    
                    # 获取同步报告
                    sync_report = self.frame_sync_optimizer.get_sync_report()
                    self.logger.info(f"🎨 视频帧同步完成: 同步率{sync_report['sync_statistics']['sync_accuracy']:.1f}%, "
                                   f"帧对齐率{sync_report['sync_statistics']['frame_aligned_segments']}/{sync_report['sync_statistics']['total_segments']}")
                    
                    # 保存同步报告
                    subtitle_data["frame_sync_report"] = sync_report
                    subtitle_data["frame_sync_applied"] = True
                else:
                    self.logger.warning("未找到视频元数据，跳过帧同步优化")
                    subtitle_data["frame_sync_applied"] = False
            
            # 应用音频智能同步优化
            if self.enable_audio_sync and self.audio_sync_optimizer and AUDIO_INTELLIGENT_SYNC_AVAILABLE:
                self.logger.info("🎵 开始音频智能同步优化...")
                
                if progress_callback:
                    progress_callback(90)
                
                # 获取音频文件路径用于分析
                audio_analysis_path = await self._get_audio_file_for_analysis(audio_data)
                
                if audio_analysis_path:
                    # 执行音频内容分析
                    audio_analysis = await self.audio_sync_optimizer.analyze_audio_content(audio_analysis_path)
                    
                    # 转换字幕为音频同步格式
                    subtitle_for_audio_sync = self._convert_subtitles_for_audio_sync(all_subtitles)
                    
                    # 执行音频智能同步优化
                    audio_sync_results = await self.audio_sync_optimizer.optimize_audio_sync(
                        subtitle_for_audio_sync, audio_analysis
                    )
                    
                    # 转换回字幕格式并应用同步结果
                    all_subtitles = self._apply_audio_sync_results_to_subtitles(all_subtitles, audio_sync_results)
                    
                    # 获取音频同步报告
                    audio_sync_report = self.audio_sync_optimizer.get_audio_sync_report()
                    self.logger.info(f"🎵 音频智能同步完成: "
                                   f"节拍对齐率{audio_sync_report['audio_sync_statistics']['beat_alignment_rate']:.1f}%, "
                                   f"情感增强率{audio_sync_report['audio_sync_statistics']['emotion_enhancement_rate']:.1f}%, "
                                   f"平均置信度{audio_sync_report['audio_sync_statistics']['average_confidence']:.2f}")
                    
                    # 保存音频同步报告
                    subtitle_data["audio_sync_report"] = audio_sync_report
                    subtitle_data["audio_sync_applied"] = True
                else:
                    self.logger.warning("未找到音频文件，跳过音频智能同步优化")
                    subtitle_data["audio_sync_applied"] = False

            # 应用AI内容理解增强系统
            if self.enable_ai_content_understanding and self.semantic_alignment_optimizer and AI_CONTENT_UNDERSTANDING_AVAILABLE:
                self.logger.info("🤖 开始AI内容理解增强处理...")
                
                if progress_callback:
                    progress_callback(95)
                
                try:
                    # 收集所有文本内容用于语义分析
                    all_text_content = self._collect_content_for_semantic_analysis(scripts_data, all_subtitles)
                    
                    # 构建音频时间段信息 - 修复SubRipTime转换
                    def get_seconds_from_subrip_time(srt_time):
                        """将SubRipTime转换为秒数"""
                        return srt_time.hours * 3600 + srt_time.minutes * 60 + srt_time.seconds + srt_time.milliseconds / 1000.0
                    
                    audio_segments = [(get_seconds_from_subrip_time(sub.start), get_seconds_from_subrip_time(sub.end)) for sub in all_subtitles]
                    
                    # 执行内容语义分析
                    semantic_profile = await self.semantic_alignment_optimizer.analyze_content_semantics(
                        all_text_content, audio_segments
                    )
                    
                    # 转换字幕为语义对齐格式
                    subtitle_for_semantic_sync = self._convert_subtitles_for_semantic_sync(all_subtitles)
                    
                    # 获取之前的音频分析结果 (如果可用)
                    previous_audio_analysis = subtitle_data.get("audio_sync_report", {}).get("audio_analysis")
                    
                    # 执行语义对齐优化
                    semantic_sync_results = await self.semantic_alignment_optimizer.optimize_semantic_alignment(
                        subtitle_for_semantic_sync, semantic_profile, previous_audio_analysis
                    )
                    
                    # 应用语义对齐结果
                    all_subtitles = self._apply_semantic_sync_results_to_subtitles(all_subtitles, semantic_sync_results)
                    
                    # 获取语义同步报告
                    semantic_sync_report = self.semantic_alignment_optimizer.get_semantic_sync_report()
                    self.logger.info(f"🤖 AI内容理解完成: "
                                   f"语义对齐率{semantic_sync_report['semantic_sync_statistics']['semantic_alignment_rate']:.1f}%, "
                                   f"概念映射率{semantic_sync_report['semantic_sync_statistics']['concept_mapping_rate']:.1f}%, "
                                   f"平均置信度{semantic_sync_report['semantic_sync_statistics']['average_semantic_confidence']:.3f}")
                    
                    # 保存AI内容理解报告
                    subtitle_data["ai_content_understanding_report"] = semantic_sync_report
                    subtitle_data["ai_content_understanding_applied"] = True
                    subtitle_data["semantic_profile"] = {
                        "key_topics": semantic_profile.key_topics,
                        "complexity_score": semantic_profile.complexity_score,
                        "readability_score": semantic_profile.readability_score,
                        "emotional_profile": semantic_profile.emotional_profile
                    }
                    
                except Exception as e:
                    self.logger.error(f"AI内容理解处理失败: {e}")
                    subtitle_data["ai_content_understanding_applied"] = False
                    subtitle_data["ai_content_understanding_error"] = str(e)
            else:
                if not self.enable_ai_content_understanding:
                    self.logger.info("AI内容理解增强系统未启用")
                subtitle_data["ai_content_understanding_applied"] = False

            # 应用Phase 3智能对齐系统
            if self.enable_phase3_alignment and self.intelligent_alignment_system and PHASE3_INTELLIGENT_ALIGNMENT_AVAILABLE:
                self.logger.info("🚀 开始Phase 3智能对齐处理...")
                
                if progress_callback:
                    progress_callback(97)
                
                try:
                    # 获取音频文件路径用于分析
                    audio_file_path = await self._get_audio_file_for_analysis(audio_data)
                    
                    if audio_file_path and Path(audio_file_path).exists():
                        # 准备文本段落数据
                        text_segments = []
                        for script in scripts:
                            if "content" in script and script["content"]:
                                text_segments.append({
                                    "text": script["content"],
                                    "slide_number": script.get("slide_number", 1),
                                    "expected_duration": script.get("estimated_duration", 3.0)
                                })
                        
                        # 转换现有字幕为智能对齐格式
                        subtitle_entries = self._convert_pysrt_to_subtitle_entries(all_subtitles)
                        
                        # 执行智能对齐
                        aligned_subtitles, alignment_report = self.intelligent_alignment_system.align_subtitles(
                            audio_path=audio_file_path,
                            subtitles=subtitle_entries
                        )
                        
                        # 将对齐结果转换回pysrt格式
                        if aligned_subtitles:
                            all_subtitles = self._convert_subtitle_entries_to_pysrt(aligned_subtitles)
                            
                            # 计算对齐改进信息
                            improvement_stats = {
                                'precision_improvement': alignment_report.quality_metrics.precision_score * 100,
                                'consistency_improvement': alignment_report.quality_metrics.consistency_score * 100,
                                'overall_quality_score': alignment_report.quality_metrics.overall_quality,
                                'boundary_accuracy': alignment_report.quality_metrics.boundary_accuracy * 100,
                                'dtw_alignment_score': alignment_report.quality_metrics.dtw_alignment_score * 100
                            }
                            
                            self.logger.info(f"🚀 Phase 3智能对齐完成: "
                                           f"对齐精度{improvement_stats.get('precision_improvement', 0):.1f}%, "
                                           f"一致性评分{improvement_stats.get('consistency_improvement', 0):.1f}%, "
                                           f"整体质量评分{improvement_stats.get('overall_quality_score', 0):.2f}")
                            
                            # 保存智能对齐报告
                            subtitle_data["phase3_alignment_report"] = {
                                "input_subtitles_count": alignment_report.input_subtitles_count,
                                "output_subtitles_count": alignment_report.output_subtitles_count,
                                "successful_alignments": alignment_report.successful_alignments,
                                "processing_time": alignment_report.processing_time,
                                "quality_metrics": {
                                    "precision_score": alignment_report.quality_metrics.precision_score,
                                    "boundary_accuracy": alignment_report.quality_metrics.boundary_accuracy,
                                    "dtw_alignment_score": alignment_report.quality_metrics.dtw_alignment_score,
                                    "overall_confidence": alignment_report.quality_metrics.overall_confidence,
                                    "consistency_score": alignment_report.quality_metrics.consistency_score,
                                    "overall_quality": alignment_report.quality_metrics.overall_quality
                                },
                                "alignment_adjustments": alignment_report.alignment_adjustments,
                                "boundaries_detected": alignment_report.boundaries_detected,
                                "improvements": improvement_stats
                            }
                            subtitle_data["phase3_alignment_applied"] = True
                        else:
                            self.logger.warning("Phase 3智能对齐未产生改进结果，保持原始字幕")
                            subtitle_data["phase3_alignment_applied"] = False
                    else:
                        self.logger.warning("未找到音频文件，跳过Phase 3智能对齐")
                        subtitle_data["phase3_alignment_applied"] = False
                        
                except Exception as e:
                    self.logger.error(f"Phase 3智能对齐处理失败: {e}")
                    subtitle_data["phase3_alignment_applied"] = False
                    subtitle_data["phase3_alignment_error"] = str(e)
            else:
                if not self.enable_phase3_alignment:
                    self.logger.info("Phase 3智能对齐系统未启用")
                subtitle_data["phase3_alignment_applied"] = False
            
            combined_info = await self._generate_combined_subtitle(all_subtitles)
            subtitle_data["combined_subtitle_info"] = combined_info
            
            subtitle_data["subtitle_generation_completed"] = True
            
            # 保存字幕元数据
            self.file_manager.save_subtitles_metadata(subtitle_data)
            
            if progress_callback:
                progress_callback(100)
            
            self.logger.info("字幕生成完成")
            return subtitle_data
            
        except Exception as e:
            self.logger.error(f"字幕生成失败: {e}", exc_info=True)
            raise
    
    async def _generate_single_subtitle(self, script: Dict[str, Any], audio_info: Dict[str, Any], 
                                      start_index: int) -> Tuple[Dict[str, Any], List[pysrt.SubRipItem]]:
        """
        生成单个页面的字幕文件
        
        Args:
            script: 讲话稿数据
            audio_info: 音频信息
            start_index: 字幕起始索引
            
        Returns:
            (字幕信息字典, 字幕项列表)
        """
        slide_number = script.get("slide_number") or script.get("slide_id") or script.get("script_id") or 1
        # 支持多种字段名格式以保持兼容性：text（新格式）、script_content、content
        script_content = script.get("text", script.get("script_content", script.get("content", "")))
        
        # 清理HTML标签
        script_content = self._clean_html_tags(script_content)
        
        # 字幕文件路径
        subtitle_filename = f"subtitle_{slide_number:03d}.srt"
        subtitle_path = self.file_manager.subtitles_dir / subtitle_filename
        
        if not script_content or not script_content.strip():
            # 如果没有讲话稿内容，创建空字幕文件
            empty_subs = pysrt.SubRipFile()
            empty_subs.save(str(subtitle_path), encoding='utf-8')
            
            subtitle_info = {
                "subtitle_id": f"{slide_number:03d}",
                "slide_number": slide_number,
                "subtitle_file": subtitle_filename,
                "start_time": audio_info["start_time"],
                "end_time": audio_info["end_time"],
                "line_count": 0,
                "generation_timestamp": datetime.now().isoformat()
            }
            
            return subtitle_info, []
        
        try:
            # 🔥 强制单行检查：在分割前检查配置
            config_single_line_mode = False
            try:
                manual_config_path = self.project_dir / "flask_backend" / "config_data" / "manual_split_config.json"
                
                # 🔧 修复配置文件路径：如果当前目录是output，则向上查找配置
                if not manual_config_path.exists() and self.project_dir.name == "output":
                    parent_project_dir = self.project_dir.parent.parent  # output -> flask_backend -> 项目根
                    manual_config_path = parent_project_dir / "flask_backend" / "config_data" / "manual_split_config.json"
                
                if manual_config_path.exists():
                    import json
                    with open(manual_config_path, 'r', encoding='utf-8') as f:
                        manual_config = json.load(f)
                    config_single_line_mode = manual_config.get("manual_split_config", {}).get("subtitle_display_mode", {}).get("single_line_mode", False)
                    self.logger.info(f"🔥 字幕生成前配置检查: single_line_mode = {config_single_line_mode}")
            except Exception as e:
                self.logger.error(f"配置检查失败: {e}")
            
            # 🔥 如果是单行模式，强制按行分割
            if config_single_line_mode:
                self.logger.info("🔥 执行强制单行分割")
                if '\n' in script_content:
                    subtitle_segments = [line.strip() for line in script_content.split('\n') if line.strip()]
                    self.logger.info(f"🔄 强制单行分割结果: {len(subtitle_segments)} 个单行字幕")
                    for i, seg in enumerate(subtitle_segments, 1):
                        self.logger.info(f"  第{i}行: '{seg}'")
                else:
                    subtitle_segments = [script_content]
                    self.logger.info("📝 单行文本直接使用")
            else:
                # 分割文本为字幕片段 - 支持异步智能分割
                subtitle_segments = await self._split_text_to_segments(script_content)
            
            # 计算时间分配
            start_time = audio_info["start_time"]
            duration = audio_info["duration_seconds"]
            
            # 创建字幕项 - 精确时间分配，避免重叠
            subtitles = []
            current_time = start_time
            
            # 预计算所有片段的字符数以优化时间分配
            total_chars = sum(len(seg.strip()) for seg in subtitle_segments)
            self._total_chars_cache = total_chars
            
            # 计算每个片段的精确时间 - 支持单行模式的比例分配
            for i, segment in enumerate(subtitle_segments):
                # 计算这个片段的时长 - 在单行模式下提供更精确的比例分配
                if self.single_line_mode:
                    segment_duration = self._calculate_single_line_duration(segment, duration, subtitle_segments, i)
                else:
                    segment_duration = self._calculate_segment_duration(segment, duration, len(subtitle_segments), i)
                
                # 确保最后一个字幕的结束时间不超过音频结束时间
                if i == len(subtitle_segments) - 1:
                    segment_end_time = start_time + duration
                else:
                    segment_end_time = current_time + segment_duration
                
                # 创建字幕项
                subtitle_item = pysrt.SubRipItem(
                    index=start_index + i,
                    start=self._seconds_to_srt_time(current_time),
                    end=self._seconds_to_srt_time(segment_end_time),
                    text=segment
                )
                
                subtitles.append(subtitle_item)
                current_time = segment_end_time  # 下一个字幕从当前字幕结束时间开始
            
            # 清理缓存
            if hasattr(self, '_total_chars_cache'):
                delattr(self, '_total_chars_cache')
            
            # 保存SRT文件
            srt_file = pysrt.SubRipFile(subtitles)
            srt_file.save(str(subtitle_path), encoding='utf-8')
            
            self.logger.info(f"字幕文件生成成功: {subtitle_path}, 片段数: {len(subtitles)}")
            
            subtitle_info = {
                "subtitle_id": f"{slide_number:03d}",
                "slide_number": slide_number,
                "subtitle_file": subtitle_filename,
                "start_time": start_time,
                "end_time": audio_info["end_time"],
                "line_count": len(subtitles),
                "generation_timestamp": datetime.now().isoformat(),
                "script_content": script_content
            }
            
            return subtitle_info, subtitles
            
        except Exception as e:
            self.logger.error(f"生成字幕文件失败 {subtitle_filename}: {e}")
            raise
    
    async def _split_text_to_segments(self, text: str) -> List[str]:
        """
        将文本分割为合适的字幕片段 - 优先支持单行模式，严格遵守配置
        
        Args:
            text: 输入文本（可能包含\n换行符表示段落分割）
            
        Returns:
            字幕片段列表
        """
        # 清理文本
        text = text.strip()
        if not text:
            return []

        # ✨ 单行模式处理：绝对优先，严格单行，不执行任何其他分割逻辑
        if self.single_line_mode:
            self.logger.info("🔥 单行模式已启用 - 严格单行处理，跳过所有其他分割逻辑")
            
            if '\n' in text:
                self.logger.info("🔄 单行模式：将多行文本拆分为连续单行字幕")
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                self.logger.info(f"📋 单行模式结果: {len(lines)} 个独立单行字幕")
                return lines
            else:
                self.logger.info("� 单行模式：文本已为单行，直接返回")
                return [text]

        # ✨ 非单行模式：执行原有的多行分割逻辑
        self.logger.info("📝 多行模式：执行标准分割逻辑")
        
        # 优先处理手动换行：如果文本包含\n换行符，先按段落分割
        if '\n' in text:
            self.logger.info("📝 检测到手动换行，按段落优先分割")
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            
            if len(paragraphs) > 1:
                self.logger.info(f"🎯 发现 {len(paragraphs)} 个手动段落，将创建对应数量的字幕条目")
                all_segments = []
                
                # 对每个段落分别应用智能分割
                for i, paragraph in enumerate(paragraphs):
                    self.logger.info(f"  处理段落 {i+1}/{len(paragraphs)}: {paragraph[:30]}...")
                    paragraph_segments = await self._split_single_paragraph(paragraph)
                    all_segments.extend(paragraph_segments)
                
                self.logger.info(f"✅ 手动分割完成，共生成 {len(all_segments)} 个字幕片段")
                return all_segments

        # 🤖 使用增强语义分割器 - 保护URL和技术术语
        if ENHANCED_SEMANTIC_SPLITTER_AVAILABLE:
            try:
                self.logger.info("🤖 使用AI增强语义分割器处理文本")
                from core.enhanced_semantic_splitter import EnhancedSemanticSplitter
                
                # 创建分割器实例
                splitter = EnhancedSemanticSplitter()
                splitter.max_chars_per_line = self.subtitle_config["max_chars_per_line"]
                
                # 使用异步AI分割
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    segments = loop.run_until_complete(splitter.split_with_semantic_awareness(text))
                    if segments and len(segments) > 0:
                        self.logger.info(f"✅ AI语义分割成功，生成 {len(segments)} 个片段")
                        return segments
                    else:
                        self.logger.warning("⚠️ AI分割返回空结果，使用备用方案")
                finally:
                    loop.close()
                    
            except Exception as e:
                self.logger.warning(f"增强语义分割器失败，回退到轻量级方法: {e}")
        
        # 🔧 回退：使用轻量级断句方法
        self.logger.info("使用轻量级断句方法处理文本")
        return self._lightweight_split_text(text)

    async def _split_single_paragraph(self, paragraph: str) -> List[str]:
        """
        对单个段落应用智能分割逻辑
        
        Args:
            paragraph: 单个段落文本
            
        Returns:
            该段落的字幕片段列表
        """
        # 对单个段落应用现有的轻量级分割逻辑
        return self._lightweight_split_text(paragraph)

    def _legacy_split_text(self, text: str) -> List[str]:
        """
        智能文本分割方法 - 优化单行显示和语义断句
        
        Args:
            text: 输入文本
            
        Returns:
            字幕片段列表
        """
        segments = []
        max_chars = self.subtitle_config["max_chars_per_line"]
        
        # 首先按主要标点符号分割成完整语义单元
        # 使用正则表达式保留分隔符
        pattern = f'([{re.escape(self.subtitle_config["line_break_chars"])}])'
        parts = re.split(pattern, text)
        
        current_segment = ""
        i = 0
        
        while i < len(parts):
            part = parts[i].strip()
            
            if not part:
                i += 1
                continue
            
            # 检查这个部分是否是标点符号
            if part in self.subtitle_config["line_break_chars"]:
                # 这是标点符号，添加到当前片段并结束这个语义单元
                if current_segment:
                    current_segment += part
                    # 完整的语义单元，检查长度
                    if len(current_segment) <= max_chars:
                        segments.append(current_segment.strip())
                        current_segment = ""
                    else:
                        # 语义单元过长，需要分割
                        long_segments = self._smart_split_long_sentence(current_segment)
                        segments.extend(long_segments)
                        current_segment = ""
            else:
                # 这是文本内容
                if current_segment:
                    # 检查是否可以继续添加
                    test_segment = current_segment + part
                    # 预先检查后面是否有标点
                    next_punct = ""
                    if i + 1 < len(parts) and parts[i + 1] in self.subtitle_config["line_break_chars"]:
                        next_punct = parts[i + 1]
                    
                    if len(test_segment + next_punct) <= max_chars:
                        current_segment = test_segment
                    else:
                        # 当前片段需要结束
                        if current_segment:
                            segments.append(current_segment.strip())
                        current_segment = part
                else:
                    current_segment = part
            
            i += 1
        
        # 添加最后的片段
        if current_segment:
            segments.append(current_segment.strip())
        
        # 如果没有有效分割，按字符数硬切分
        if not segments:
            segments = [text[i:i+max_chars].strip() for i in range(0, len(text), max_chars)]
            segments = [s for s in segments if s]  # 移除空字符串
        
        return [seg for seg in segments if seg.strip()]
    
    def _lightweight_split_text(self, text: str) -> List[str]:
        """
        轻量级文本分割 - 专门解决Flask重载问题
        单行模式：严格按行拆分，无其他逻辑
        多行模式：执行智能语义分割
        
        Args:
            text: 输入文本
            
        Returns:
            断句后的片段列表
        """
        self.logger.info(f"🔧 轻量级分割器启动 - 输入文本: '{text}'")
        self.logger.info(f"🔧 轻量级分割器 - 单行模式: {self.single_line_mode}")
        
        if not text.strip():
            return []
        
        # ✨ 单行模式：严格单行处理，无任何其他逻辑
        if self.single_line_mode:
            self.logger.info("� 轻量级分割器 - 单行模式严格处理")
            if '\n' in text:
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                self.logger.info(f"🔄 单行模式分割结果: {len(lines)} 个单行字幕")
                for i, line in enumerate(lines):
                    self.logger.info(f"  单行片段 {i+1}: '{line}'")
                return lines
            else:
                self.logger.info("📝 单行模式：文本本身就是单行")
                return [text]

        # 🔧 多行模式：执行完整的智能分割逻辑
        self.logger.info("📝 多行模式：执行智能语义分割")
        
        segments = []
        max_chars = self.subtitle_config["max_chars_per_line"]
        
        # 🛡️ URL保护：先识别并保护URL
        protected_text, url_map = self._protect_urls_in_text(text)
        self.logger.info(f"🔧 URL保护后文本: '{protected_text}'")
        
        # 1. 先检查是否真的需要分割 - 语义完整性优先
        if len(protected_text) <= max_chars * 1.5:  # 增加到50%的容忍度
            # 如果只是稍微超出限制，且包含重要元素，优先保持完整
            if self._should_keep_intact(protected_text, url_map):
                sentences = [text]  # 保持完整，不分割
                final_segments = [self._restore_urls_in_text(protected_text, url_map)]
                return final_segments
        
        # 2. 首先按句号分割成完整语义单元
        sentences = protected_text.split("。")
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 添加句号（除了最后一个且原文不以句号结尾）
            if i < len(sentences) - 1:
                sentence += "。"
            elif text.endswith("。"):
                sentence += "。"
            
            # 2. 处理每个句子的长度
            if len(sentence) <= max_chars:
                segments.append(sentence)
            else:
                # 3. 智能分割长句子 - 保护URL的多级分割策略
                sentence_segments = self._smart_split_long_sentence_with_protection(sentence, max_chars, url_map)
                segments.extend(sentence_segments)
        
        # 🔄 还原URL保护
        final_segments = []
        for segment in segments:
            restored_segment = self._restore_urls_in_text(segment, url_map)
            if restored_segment.strip():
                final_segments.append(restored_segment.strip())
        
        return final_segments
    
    def _protect_urls_in_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        保护文本中的URL，避免被分割
        
        Args:
            text: 原始文本
            
        Returns:
            Tuple[保护后的文本, URL映射表]
        """
        import re
        
        # URL正则表达式 - 匹配http/https URL
        url_pattern = r'https?://[^\s，。！？；：\'"]*'
        
        url_map = {}
        counter = 0
        
        def replace_url(match):
            nonlocal counter
            url = match.group(0)
            placeholder = f"__URL_{counter}__"
            url_map[placeholder] = url
            counter += 1
            return placeholder
        
        protected_text = re.sub(url_pattern, replace_url, text)
        return protected_text, url_map
    
    def _restore_urls_in_text(self, text: str, url_map: Dict[str, str]) -> str:
        """
        还原文本中的URL
        
        Args:
            text: 保护后的文本
            url_map: URL映射表
            
        Returns:
            还原后的文本
        """
        for placeholder, url in url_map.items():
            text = text.replace(placeholder, url)
        return text
    
    def _should_keep_intact(self, text: str, url_map: Dict[str, str]) -> bool:
        """
        判断文本是否应该保持完整，不进行分割
        
        Args:
            text: 文本内容
            url_map: URL映射表
            
        Returns:
            是否应该保持完整
        """
        # 1. 包含URL的句子优先保持完整
        if url_map:
            return True
        
        # 2. 包含技术术语的句子（如软件名）
        tech_terms = ["studio", "客户端", "程序", "下载", "安装", "cherry"]
        if any(term in text.lower() for term in tech_terms):
            return True
        
        # 3. 包含特殊格式的句子（如带冒号的说明）
        if "：" in text or ":" in text:
            return True
        
        # 4. 中等长度句子也倾向保持完整（<=45字符）
        if len(text) <= 45:
            return True
            
        return False
    
    def _smart_split_long_sentence_with_protection(self, sentence: str, max_chars: int, url_map: Dict[str, str]) -> List[str]:
        """
        保护URL的智能长句分割策略
        
        Args:
            sentence: 要分割的句子
            max_chars: 最大字符数
            url_map: URL映射表
            
        Returns:
            分割后的句子列表
        """
        segments = []
        remaining = sentence
        
        # 分割优先级：逗号 > 冒号 > 连词 > 介词 > 的字 > 强制分割
        split_patterns = [
            {"patterns": ["，"], "priority": 1},
            {"patterns": ["："], "priority": 2},  # 添加冒号优先级
            {"patterns": ["、"], "priority": 3},
            {"patterns": ["和", "与", "或", "但", "然后", "接下来", "因此", "所以"], "priority": 4},
            {"patterns": ["在", "对", "的", "了"], "priority": 5},
            {"patterns": ["如果", "当", "将", "进行"], "priority": 6}
        ]
        
        while len(remaining) > max_chars:
            best_split_pos = -1
            
            # 🛡️ 特殊处理：如果包含URL占位符，优先在URL前分割
            for placeholder in url_map.keys():
                if placeholder in remaining:
                    placeholder_pos = remaining.find(placeholder)
                    # 在URL前的合适位置分割
                    for i in range(placeholder_pos - 1, max(0, placeholder_pos - 20), -1):
                        if i < len(remaining) and remaining[i] in "，：、 ":
                            best_split_pos = i + 1
                            break
                    if best_split_pos != -1:
                        break
            
            # 按优先级查找分割点
            if best_split_pos == -1:
                for pattern_group in split_patterns:
                    for pattern in pattern_group["patterns"]:
                        # 在允许范围内查找最后一个分割点
                        search_end = min(max_chars - len(pattern), len(remaining))
                        
                        for pos in range(search_end, max_chars // 3, -1):
                            if pos + len(pattern) <= len(remaining):
                                if remaining[pos:pos + len(pattern)] == pattern:
                                    best_split_pos = pos + len(pattern)
                                    break
                        
                        if best_split_pos != -1:
                            break
                    
                    if best_split_pos != -1:
                        break
            
            # 如果没找到合适的分割点，寻找空格
            if best_split_pos == -1:
                for pos in range(min(max_chars - 1, len(remaining) - 1), max_chars // 2, -1):
                    if pos < len(remaining) and remaining[pos] == ' ':
                        best_split_pos = pos + 1
                        break
            
            # 最后手段：强制在3/4位置分割
            if best_split_pos == -1:
                best_split_pos = max_chars * 3 // 4
            
            # 执行分割
            if best_split_pos > 0 and best_split_pos < len(remaining):
                segment = remaining[:best_split_pos].strip()
                if segment:
                    segments.append(segment)
                remaining = remaining[best_split_pos:].strip()
            else:
                # 极端情况，直接按最大长度切分
                segment = remaining[:max_chars].strip()
                if segment:
                    segments.append(segment)
                remaining = remaining[max_chars:].strip()
        
        # 添加剩余部分
        if remaining.strip():
            segments.append(remaining.strip())
        
        return segments
    
    def _smart_split_long_sentence_enhanced(self, sentence: str, max_chars: int) -> List[str]:
        """
        增强版智能长句分割 - 多级分割策略
        """
        segments = []
        remaining = sentence
        
        # 分割优先级：逗号 > 连词 > 介词 > 的字 > 强制分割
        split_patterns = [
            {"patterns": ["，"], "priority": 1},
            {"patterns": ["、"], "priority": 2},
            {"patterns": ["和", "与", "或", "但", "然后", "接下来", "因此", "所以"], "priority": 3},
            {"patterns": ["在", "对", "的", "了"], "priority": 4},
            {"patterns": ["如果", "当", "将", "进行"], "priority": 5}
        ]
        
        while len(remaining) > max_chars:
            best_split_pos = -1
            
            # 按优先级查找分割点
            for pattern_group in split_patterns:
                for pattern in pattern_group["patterns"]:
                    # 在允许范围内查找最后一个分割点
                    search_end = min(max_chars - len(pattern), len(remaining))
                    
                    for pos in range(search_end, max_chars // 3, -1):
                        if pos + len(pattern) <= len(remaining):
                            if remaining[pos:pos + len(pattern)] == pattern:
                                best_split_pos = pos + len(pattern)
                                break
                    
                    if best_split_pos != -1:
                        break
                
                if best_split_pos != -1:
                    break
            
            # 如果没找到合适的分割点，寻找空格
            if best_split_pos == -1:
                for pos in range(min(max_chars - 1, len(remaining) - 1), max_chars // 2, -1):
                    if pos < len(remaining) and remaining[pos] == ' ':
                        best_split_pos = pos + 1
                        break
            
            # 最后手段：强制在3/4位置分割
            if best_split_pos == -1:
                best_split_pos = max_chars * 3 // 4
            
            # 执行分割
            if best_split_pos > 0:
                segment = remaining[:best_split_pos].strip()
                if segment:
                    segments.append(segment)
                remaining = remaining[best_split_pos:].strip()
            else:
                # 极端情况，直接按最大长度切分
                segment = remaining[:max_chars].strip()
                if segment:
                    segments.append(segment)
                remaining = remaining[max_chars:].strip()
        
        # 添加剩余部分
        if remaining.strip():
            segments.append(remaining.strip())
        
        return segments
    
    def _hard_split_sentence(self, sentence: str, max_chars: int, segments: List[str]) -> None:
        """
        硬切分长句子
        
        Args:
            sentence: 要分割的句子
            max_chars: 最大字符数
            segments: 结果列表
        """
        for i in range(0, len(sentence), max_chars):
            part = sentence[i:i + max_chars]
            if part.strip():
                segments.append(part.strip())
    
    def _smart_split_long_sentence(self, sentence: str) -> List[str]:
        """
        智能分割长句 - 优先在语义停顿处分割
        
        Args:
            sentence: 长句子
            
        Returns:
            分割后的片段列表
        """
        max_chars = self.subtitle_config["max_chars_per_line"]
        
        if len(sentence) <= max_chars:
            return [sentence]
        
        segments = []
        
        # 优先级分割点：逗号、的、了、在、与、和、或、但、然后、接下来等
        split_points = ["，", "的", "了", "在", "与", "和", "或", "但", "然后", "接下来", "因此", "所以", "如果", "当", "将"]
        
        remaining = sentence
        while len(remaining) > max_chars:
            # 寻找最佳分割点
            best_split = -1
            
            # 从后往前找分割点，确保不超过长度限制
            for i in range(max_chars - 1, max_chars // 2, -1):
                if i < len(remaining):
                    # 检查是否在分割点上
                    for point in split_points:
                        if remaining[i - len(point) + 1:i + 1] == point:
                            best_split = i + 1
                            break
                    if best_split != -1:
                        break
            
            # 如果没找到合适分割点，从中间位置向后找空格或标点
            if best_split == -1:
                for i in range(max_chars // 2, max_chars):
                    if i < len(remaining) and remaining[i] in " ，。！？；：":
                        best_split = i + 1
                        break
            
            # 如果还是没找到，就硬切分
            if best_split == -1:
                best_split = max_chars
            
            # 分割并继续处理剩余部分
            segment = remaining[:best_split].strip()
            if segment:
                segments.append(segment)
            remaining = remaining[best_split:].strip()
        
        # 添加最后的片段
        if remaining:
            segments.append(remaining)
        
        return segments
    
    def _clean_html_tags(self, text: str) -> str:
        """
        清理HTML标签和实体
        
        Args:
            text: 包含HTML标签的文本
            
        Returns:
            清理后的纯文本
        """
        if not text:
            return ""
        
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 解码HTML实体
        clean_text = html.unescape(clean_text)
        
        # ✨ 单行模式下保留换行符，否则清理多余空白
        if self.single_line_mode:
            # 单行模式：保留换行符，但清理其他多余空白
            # 先将多个连续空格/制表符替换为单个空格
            clean_text = re.sub(r'[ \t]+', ' ', clean_text)
            # 清理换行符前后的空格，但保留换行符本身
            clean_text = re.sub(r' *\n *', '\n', clean_text)
            clean_text = clean_text.strip()
            self.logger.info(f"🧹 单行模式HTML清理 - 保留换行符: '{clean_text}'")
        else:
            # 常规模式：清理所有多余空白（包括换行符）
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        分割过长的句子
        
        Args:
            sentence: 长句子
            
        Returns:
            分割后的片段列表
        """
        max_length = self.subtitle_config["max_chars_per_line"]
        segments = []
        
        # 首先尝试按逗号分割
        parts = sentence.split('，')
        current_part = ""
        
        for part in parts:
            if len(current_part + part + '，') <= max_length:
                current_part += part + '，'
            else:
                if current_part:
                    segments.append(current_part.rstrip('，'))
                
                if len(part) <= max_length:
                    current_part = part + '，'
                else:
                    # 强制分割
                    segments.extend([part[i:i+max_length] for i in range(0, len(part), max_length)])
                    current_part = ""
        
        if current_part:
            segments.append(current_part.rstrip('，'))
        
        return segments
    
    def _calculate_segment_duration(self, segment: str, total_duration: float, 
                                  total_segments: int, segment_index: int) -> float:
        """
        计算字幕片段的显示时长 - 精确匹配音频时间，避免重叠
        
        Args:
            segment: 字幕片段文本
            total_duration: 总时长
            total_segments: 总片段数
            segment_index: 当前片段索引
            
        Returns:
            片段时长（秒）
        """
        # 如果只有一个片段，使用总时长
        if total_segments == 1:
            return total_duration
        
        # 多个片段时，精确按音频时间分配，避免重叠
        # 计算所有片段的字符数权重
        segment_char_count = len(segment.strip())
        
        # 基于字符数权重分配时间
        if hasattr(self, '_total_chars_cache') and self._total_chars_cache > 0:
            total_chars = self._total_chars_cache
        else:
            # 这里无法获取其他片段信息，使用平均分配
            total_chars = segment_char_count * total_segments
        
        # 按字符数比例分配时间
        time_ratio = segment_char_count / total_chars if total_chars > 0 else (1.0 / total_segments)
        calculated_duration = total_duration * time_ratio
        
        # 确保最小和最大时间限制
        min_duration = self.subtitle_config["min_display_time"]
        max_duration = min(self.subtitle_config["max_display_time"], total_duration * 0.8)
        
        # 但优先保证总时长匹配，避免重叠
        return max(min_duration, min(calculated_duration, max_duration))
    
    def _calculate_single_line_duration(self, segment: str, total_duration: float, 
                                      all_segments: List[str], segment_index: int) -> float:
        """
        单行模式专用时间分配 - 基于字符数比例精确分配时间
        
        Args:
            segment: 当前字幕片段文本
            total_duration: 总时长
            all_segments: 所有字幕片段列表
            segment_index: 当前片段索引
            
        Returns:
            片段时长（秒）
        """
        if len(all_segments) == 1:
            return total_duration
        
        # 计算当前片段字符数
        current_chars = len(segment.strip())
        
        # 计算所有片段的总字符数
        total_chars = sum(len(seg.strip()) for seg in all_segments)
        
        if total_chars == 0:
            # 如果没有字符，平均分配
            return total_duration / len(all_segments)
        
        # 按字符数比例分配时间
        base_duration = total_duration * (current_chars / total_chars)
        
        # 应用单行模式的时间限制
        min_duration = self.single_line_config.get("min_line_duration", 1.0)
        max_duration = self.single_line_config.get("max_line_duration", 8.0)
        
        # 确保不超过总时长的合理比例
        max_allowed = total_duration * 0.6  # 单个字幕最多占60%
        final_max = min(max_duration, max_allowed)
        
        calculated_duration = max(min_duration, min(base_duration, final_max))
        
        self.logger.debug(f"单行模式时间分配 - 片段{segment_index+1}: '{segment[:20]}...' "
                         f"字符数:{current_chars}, 分配时间:{calculated_duration:.2f}s")
        
        return calculated_duration
    
    def _srt_time_to_seconds(self, srt_time: pysrt.SubRipTime) -> float:
        """
        将SRT时间格式转换为秒数
        
        Args:
            srt_time: SubRipTime对象
            
        Returns:
            秒数
        """
        return (srt_time.hours * 3600 + 
                srt_time.minutes * 60 + 
                srt_time.seconds + 
                srt_time.milliseconds / 1000.0)
    
    def _seconds_to_srt_time(self, seconds: float) -> pysrt.SubRipTime:
        """
        将秒数转换为SRT时间格式
        
        Args:
            seconds: 秒数
            
        Returns:
            SubRipTime对象
        """
        total_seconds = int(seconds)
        milliseconds = int((seconds - total_seconds) * 1000)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        return pysrt.SubRipTime(hours=hours, minutes=minutes, seconds=secs, milliseconds=milliseconds)
    
    def _seconds_to_timedelta(self, seconds: float) -> timedelta:
        """
        将秒数转换为timedelta对象（保留用于其他用途）
        
        Args:
            seconds: 秒数
            
        Returns:
            timedelta对象
        """
        return timedelta(seconds=seconds)
    
    async def _generate_combined_subtitle(self, all_subtitles: List[pysrt.SubRipItem]) -> Dict[str, Any]:
        """
        生成合并的字幕文件
        
        Args:
            all_subtitles: 所有字幕项列表
            
        Returns:
            合并字幕信息
        """
        combined_filename = "combined_subtitle.srt"
        combined_path = self.file_manager.subtitles_dir / combined_filename
        
        try:
            # 重新排序索引
            for i, subtitle in enumerate(all_subtitles, 1):
                subtitle.index = i
            
            # 保存合并的字幕文件
            combined_srt = pysrt.SubRipFile(all_subtitles)
            combined_srt.save(str(combined_path), encoding='utf-8')
            
            # 计算统计信息
            total_duration = 0
            if all_subtitles:
                last_subtitle = max(all_subtitles, key=lambda x: self._srt_time_to_seconds(x.end))
                total_duration = self._srt_time_to_seconds(last_subtitle.end)
            
            self.logger.info(f"合并字幕文件生成成功: {combined_path}, 字幕数: {len(all_subtitles)}")
            
            combined_info = {
                "combined_subtitle_file": combined_filename,
                "total_subtitle_count": len(all_subtitles),
                "total_duration_seconds": total_duration,
                "generation_timestamp": datetime.now().isoformat()
            }
            
            return combined_info
            
        except Exception as e:
            self.logger.error(f"生成合并字幕文件失败: {e}")
            raise
    
    def validate_subtitle_file(self, subtitle_path: Path) -> bool:
        """
        验证字幕文件是否有效
        
        Args:
            subtitle_path: 字幕文件路径
            
        Returns:
            是否有效
        """
        try:
            srt_file = pysrt.open(str(subtitle_path), encoding='utf-8')
            return len(srt_file) >= 0  # 允许空字幕文件
        except Exception as e:
            self.logger.warning(f"字幕文件验证失败 {subtitle_path}: {e}")
            return False
    
    async def _get_video_metadata_for_sync(self) -> Optional[VideoMetadata]:
        """获取视频元数据用于帧同步"""
        try:
            # 查找项目中的视频文件
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
            
            # 检查输出目录中的视频文件
            output_dir = self.project_dir / "output"
            if output_dir.exists():
                for ext in video_extensions:
                    video_files = list(output_dir.glob(f"*{ext}"))
                    if video_files:
                        video_path = str(video_files[0])
                        self.logger.info(f"🎬 找到视频文件进行帧同步: {video_path}")
                        if self.frame_sync_optimizer is not None:
                            # 由于帧同步优化器暂时不可用，直接返回默认元数据
                            self.logger.warning("帧同步优化器暂时不可用，使用默认视频元数据")
                        else:
                            self.logger.warning("帧同步优化器未初始化，无法分析视频元数据")
            
            # 如果没找到实际视频文件，使用默认元数据
            self.logger.info("未找到视频文件，使用默认视频元数据 (1920x1080, 24fps)")
            return VideoMetadata(
                width=1920, height=1080, fps=24.0, duration=300.0,  # 默认5分钟
                total_frames=0, codec='h264', bitrate=5000000
            )
            
        except Exception as e:
            self.logger.error(f"获取视频元数据失败: {e}")
            return None
    
    def _convert_subtitles_for_sync(self, subtitles: List[pysrt.SubRipItem]) -> List[Dict[str, Any]]:
        """转换字幕为同步格式"""
        subtitle_segments = []
        
        for subtitle in subtitles:
            # 将pysrt时间转换为秒
            start_seconds = (subtitle.start.hours * 3600 + 
                           subtitle.start.minutes * 60 + 
                           subtitle.start.seconds + 
                           subtitle.start.milliseconds / 1000.0)
            
            end_seconds = (subtitle.end.hours * 3600 + 
                         subtitle.end.minutes * 60 + 
                         subtitle.end.seconds + 
                         subtitle.end.milliseconds / 1000.0)
            
            subtitle_segments.append({
                "text": subtitle.text,
                "start_time": start_seconds,
                "end_time": end_seconds
            })
        
        return subtitle_segments
    
    def _convert_sync_segments_to_subtitles(self, sync_segments: List[Any]) -> List[pysrt.SubRipItem]:
        """转换同步片段回字幕格式"""
        subtitles = []
        
        for i, segment in enumerate(sync_segments, 1):
            # 转换同步时间回pysrt格式
            start_time = self._seconds_to_srt_time(segment.sync_start.seconds)
            end_time = self._seconds_to_srt_time(segment.sync_end.seconds)
            
            subtitle = pysrt.SubRipItem(
                index=i,
                start=start_time,
                end=end_time,
                text=segment.text
            )
            
            subtitles.append(subtitle)
        
        return subtitles
    
    def get_subtitle_stats(self, subtitle_path: Path) -> Dict[str, Any]:
        """
        获取字幕文件统计信息
        
        Args:
            subtitle_path: 字幕文件路径
            
        Returns:
            统计信息字典
        """
        try:
            srt_file = pysrt.open(str(subtitle_path), encoding='utf-8')
            
            if not srt_file:
                return {"subtitle_count": 0, "total_duration": 0, "avg_duration": 0}
            
            total_duration = self._srt_time_to_seconds(srt_file[-1].end) if srt_file else 0
            avg_duration = total_duration / len(srt_file) if srt_file else 0
            
            return {
                "subtitle_count": len(srt_file),
                "total_duration": total_duration,
                "avg_duration": avg_duration,
                "first_start": self._srt_time_to_seconds(srt_file[0].start) if srt_file else 0,
                "last_end": self._srt_time_to_seconds(srt_file[-1].end) if srt_file else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取字幕统计信息失败: {e}")
            return {"error": str(e)}

    # 音频智能同步辅助方法
    async def _get_audio_file_for_analysis(self, audio_data: Dict[str, Any]) -> Optional[str]:
        """获取用于音频分析的音频文件路径"""
        try:
            # 尝试找到合并的音频文件
            audio_files = audio_data.get("audio_files", [])
            if not audio_files:
                return None
            
            # 查找第一个有效的音频文件路径
            for audio_info in audio_files:
                audio_path = audio_info.get("audio_path")
                if audio_path and Path(audio_path).exists():
                    return audio_path
            
            # 如果没有找到单独文件，尝试查找合并音频
            combined_audio = audio_data.get("combined_audio_info", {})
            combined_path = combined_audio.get("combined_audio_path")
            if combined_path and Path(combined_path).exists():
                return combined_path
            
            return None
            
        except Exception as e:
            self.logger.warning(f"获取音频文件路径失败: {e}")
            return None
    
    def _convert_subtitles_for_audio_sync(self, subtitles: List[pysrt.SubRipItem]) -> List[Dict[str, Any]]:
        """转换字幕为音频同步格式"""
        subtitle_segments = []
        
        for subtitle in subtitles:
            # 转换时间为秒
            start_seconds = self._srt_time_to_seconds(subtitle.start)
            end_seconds = self._srt_time_to_seconds(subtitle.end)
            
            subtitle_segments.append({
                "text": subtitle.text,
                "start_time": start_seconds,
                "end_time": end_seconds,
                "index": subtitle.index
            })
        
        return subtitle_segments
    
    def _apply_audio_sync_results_to_subtitles(self, subtitles: List[pysrt.SubRipItem], 
                                             sync_results: List[Any]) -> List[pysrt.SubRipItem]:
        """将音频同步结果应用到字幕"""
        if len(subtitles) != len(sync_results):
            self.logger.warning(f"字幕数量({len(subtitles)})与同步结果数量({len(sync_results)})不匹配")
            return subtitles
        
        updated_subtitles = []
        
        for i, (subtitle, sync_result) in enumerate(zip(subtitles, sync_results)):
            try:
                # 应用同步时间
                new_start = self._seconds_to_srt_time(sync_result.synced_start)
                new_end = self._seconds_to_srt_time(sync_result.synced_end)
                
                updated_subtitle = pysrt.SubRipItem(
                    index=subtitle.index,
                    start=new_start,
                    end=new_end,
                    text=subtitle.text
                )
                
                updated_subtitles.append(updated_subtitle)
                
                # 记录显著的时间调整
                if abs(sync_result.sync_offset) > 50:  # 偏移超过50ms
                    self.logger.debug(f"字幕{i+1}音频同步调整: {sync_result.sync_offset:+.1f}ms "
                                    f"(置信度: {sync_result.confidence:.2f}, 原因: {sync_result.sync_reason})")
                
            except Exception as e:
                self.logger.warning(f"应用音频同步结果到字幕{i+1}失败: {e}")
                updated_subtitles.append(subtitle)  # 保持原始字幕
        
        return updated_subtitles

    # AI内容理解增强辅助方法
    def _collect_content_for_semantic_analysis(self, scripts_data: Dict[str, Any], 
                                             subtitles: List[pysrt.SubRipItem]) -> str:
        """收集用于语义分析的内容"""
        try:
            # 收集原始脚本内容
            scripts = scripts_data.get("scripts", [])
            script_texts = []
            
            for script in scripts:
                # 支持多种字段名格式以保持兼容性：text（新格式）、script_content、content
                script_content = script.get("text", script.get("script_content", script.get("content", "")))
                # 清理HTML标签
                clean_content = self._clean_html_tags(script_content)
                if clean_content.strip():
                    script_texts.append(clean_content.strip())
            
            # 如果没有脚本内容，使用字幕文本
            if not script_texts:
                subtitle_texts = [sub.text for sub in subtitles if sub.text.strip()]
                return " ".join(subtitle_texts)
            
            return " ".join(script_texts)
            
        except Exception as e:
            self.logger.warning(f"收集语义分析内容失败: {e}")
            # 降级到字幕文本
            subtitle_texts = [sub.text for sub in subtitles if sub.text.strip()]
            return " ".join(subtitle_texts)
    
    def _convert_subtitles_for_semantic_sync(self, subtitles: List[pysrt.SubRipItem]) -> List[Dict[str, Any]]:
        """转换字幕为语义同步格式"""
        subtitle_segments = []
        
        for subtitle in subtitles:
            # 转换时间为秒
            start_seconds = self._srt_time_to_seconds(subtitle.start)
            end_seconds = self._srt_time_to_seconds(subtitle.end)
            
            subtitle_segments.append({
                "text": subtitle.text,
                "start_time": start_seconds,
                "end_time": end_seconds,
                "index": subtitle.index,
                "duration": end_seconds - start_seconds
            })
        
        return subtitle_segments
    
    def _apply_semantic_sync_results_to_subtitles(self, subtitles: List[pysrt.SubRipItem], 
                                                sync_results: List[Any]) -> List[pysrt.SubRipItem]:
        """将语义同步结果应用到字幕"""
        if len(subtitles) != len(sync_results):
            self.logger.warning(f"字幕数量({len(subtitles)})与语义同步结果数量({len(sync_results)})不匹配")
            return subtitles
        
        updated_subtitles = []
        
        for i, (subtitle, sync_result) in enumerate(zip(subtitles, sync_results)):
            try:
                # 应用语义对齐时间
                new_start = self._seconds_to_srt_time(sync_result.semantic_start)
                new_end = self._seconds_to_srt_time(sync_result.semantic_end)
                
                # 应用内容增强 (如果有)
                enhanced_text = subtitle.text
                if sync_result.content_enhancement:
                    enhanced_text = self._apply_content_enhancement(
                        subtitle.text, sync_result.content_enhancement
                    )
                
                updated_subtitle = pysrt.SubRipItem(
                    index=subtitle.index,
                    start=new_start,
                    end=new_end,
                    text=enhanced_text
                )
                
                updated_subtitles.append(updated_subtitle)
                
                # 记录显著的语义调整
                original_start = self._srt_time_to_seconds(subtitle.start)
                time_adjustment = (sync_result.semantic_start - original_start) * 1000  # 转换为毫秒
                
                if abs(time_adjustment) > 10 or sync_result.semantic_confidence > 0.9:  # 显著调整或高置信度
                    self.logger.debug(f"字幕{i+1}语义同步: {time_adjustment:+.1f}ms, "
                                    f"精度{sync_result.sync_precision:.1f}ms, "
                                    f"置信度{sync_result.semantic_confidence:.3f}, "
                                    f"质量{sync_result.alignment_quality}")
                
            except Exception as e:
                self.logger.warning(f"应用语义同步结果到字幕{i+1}失败: {e}")
                updated_subtitles.append(subtitle)  # 保持原始字幕
        
        return updated_subtitles
    
    def _apply_content_enhancement(self, original_text: str, 
                                 enhancement_info: Dict[str, Any]) -> str:
        """应用内容增强"""
        enhanced_text = original_text
        
        try:
            # 关键概念高亮
            if 'key_concepts' in enhancement_info:
                key_concepts = enhancement_info['key_concepts']
                for concept in key_concepts:
                    if concept.lower() in enhanced_text.lower():
                        # 简单的概念标记 (可以在UI层面进一步处理)
                        enhanced_text = enhanced_text.replace(concept, f"**{concept}**")
            
            # 情感色调标记
            if 'emotional_tone' in enhancement_info:
                emotion = enhancement_info['emotional_tone']
                if emotion in ['excitement', 'emphasis']:
                    # 为兴奋和强调内容添加标记
                    enhanced_text = f"{enhanced_text}!"
                elif emotion == 'question':
                    # 确保问句有问号
                    if not enhanced_text.endswith('?') and not enhanced_text.endswith('？'):
                        enhanced_text = f"{enhanced_text}?"
            
        except Exception as e:
            self.logger.warning(f"应用内容增强失败: {e}")
            return original_text
        
        return enhanced_text

    def _convert_pysrt_to_subtitle_entries(self, subtitles: List[pysrt.SubRipItem]):
        """将pysrt字幕转换为智能对齐系统的SubtitleEntry格式"""
        from core.intelligent_alignment_system import SubtitleEntry
        
        subtitle_entries = []
        for sub in subtitles:
            start_seconds = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000.0
            end_seconds = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000.0
            
            entry = SubtitleEntry(
                start_time=start_seconds,
                end_time=end_seconds,
                text=sub.text,
                confidence=1.0,  # 原始字幕默认置信度为1.0
                metadata={"original_index": sub.index}
            )
            subtitle_entries.append(entry)
        
        return subtitle_entries

    def _convert_subtitle_entries_to_pysrt(self, subtitle_entries) -> List[pysrt.SubRipItem]:
        """将智能对齐系统的SubtitleEntry格式转换回pysrt字幕"""
        pysrt_subtitles = []
        
        for i, entry in enumerate(subtitle_entries):
            # 将秒数转换回SubRipTime格式
            start_time = self._seconds_to_srt_time(entry.start_time)
            end_time = self._seconds_to_srt_time(entry.end_time)
            
            subtitle = pysrt.SubRipItem(
                index=i + 1,
                start=start_time,
                end=end_time,
                text=entry.text
            )
            pysrt_subtitles.append(subtitle)
        
        return pysrt_subtitles

