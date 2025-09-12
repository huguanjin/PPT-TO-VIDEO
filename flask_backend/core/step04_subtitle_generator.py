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

from utils.logger import get_logger
from utils.file_manager import FileManager

# 导入增强版字幕生成器
try:
    from core.step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator
    ENHANCED_SUBTITLE_AVAILABLE = True
except ImportError:
    ENHANCED_SUBTITLE_AVAILABLE = False

# 导入视频帧同步优化器
try:
    from core.video_frame_sync_optimizer import VideoFrameSyncOptimizer, VideoMetadata, TimecodeFormat
    VIDEO_FRAME_SYNC_AVAILABLE = True
except ImportError:
    VIDEO_FRAME_SYNC_AVAILABLE = False

# 导入音频智能同步优化器
try:
    from core.audio_intelligent_sync_optimizer import AudioIntelligentSyncOptimizer, AudioSyncPrecision
    AUDIO_INTELLIGENT_SYNC_AVAILABLE = True
except ImportError:
    AUDIO_INTELLIGENT_SYNC_AVAILABLE = False

# 导入AI内容理解增强系统
try:
    from core.semantic_alignment_optimizer import SemanticAlignmentOptimizer, SemanticAlignmentPrecision
    AI_CONTENT_UNDERSTANDING_AVAILABLE = True
except ImportError:
    AI_CONTENT_UNDERSTANDING_AVAILABLE = False

class SubtitleGenerator:
    """字幕生成器 - 支持传统和增强模式"""
    
    def __init__(self, project_dir: Path, use_enhanced: bool = False, enable_frame_sync: bool = True, 
                 enable_audio_sync: bool = True, enable_ai_content_understanding: bool = True):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        self.use_enhanced = use_enhanced and ENHANCED_SUBTITLE_AVAILABLE
        self.enable_frame_sync = enable_frame_sync and VIDEO_FRAME_SYNC_AVAILABLE
        self.enable_audio_sync = enable_audio_sync and AUDIO_INTELLIGENT_SYNC_AVAILABLE
        self.enable_ai_content_understanding = enable_ai_content_understanding and AI_CONTENT_UNDERSTANDING_AVAILABLE
        
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
        
        # 字幕配置
        self.subtitle_config = {
            "max_chars_per_line": 40,     # 每行最大字符数
            "max_lines": 2,               # 最大行数
            "min_display_time": 1.0,      # 最小显示时间（秒）
            "max_display_time": 8.0,      # 最大显示时间（秒）
            "words_per_second": 3.5,      # 阅读速度（字/秒）
            "line_break_chars": "，。！？；：",  # 断行标点符号
            "use_enhanced_mode": self.use_enhanced,  # 是否使用增强模式
            
            # 智能字幕处理配置
            "smart_processing": smart_config
        }
        
        # 初始化智能字幕处理器
        try:
            from core.subtitle_utils import SmartSubtitleProcessor
            from core.ai_subtitle_splitter import HybridSubtitleSplitter
            
            self.smart_processor = SmartSubtitleProcessor(self.subtitle_config["smart_processing"])
            self.hybrid_splitter = HybridSubtitleSplitter(self.subtitle_config["smart_processing"])
            self.logger.info("智能字幕处理器初始化成功")
        except ImportError as e:
            self.logger.warning(f"智能字幕处理器不可用: {e}")
            self.smart_processor = None
            self.hybrid_splitter = None
        
        # 初始化增强版生成器
        if self.use_enhanced:
            self.enhanced_generator = EnhancedSubtitleGenerator(project_dir)
            self.logger.info("已启用Netflix级增强字幕生成模式")
        else:
            self.enhanced_generator = None
            if not ENHANCED_SUBTITLE_AVAILABLE:
                self.logger.info("增强版字幕生成器不可用")
        
        # 初始化视频帧同步优化器
        if self.enable_frame_sync:
            try:
                config_path = self.project_dir / "config_data" / "video_frame_sync_config.json"
                self.frame_sync_optimizer = VideoFrameSyncOptimizer(str(config_path) if config_path.exists() else None)
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
        if self.enable_audio_sync:
            try:
                config_path = self.project_dir / "config_data" / "audio_intelligent_sync_config.json"
                self.audio_sync_optimizer = AudioIntelligentSyncOptimizer(str(config_path) if config_path.exists() else None)
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
        if self.enable_ai_content_understanding:
            try:
                config_path = self.project_dir / "config_data" / "ai_content_understanding_config.json"
                self.semantic_alignment_optimizer = SemanticAlignmentOptimizer(str(config_path) if config_path.exists() else None)
                self.logger.info("🤖 AI内容理解增强系统已启用")
            except Exception as e:
                self.logger.warning(f"AI内容理解系统初始化失败，将跳过语义对齐: {e}")
                self.semantic_alignment_optimizer = None
                self.enable_ai_content_understanding = False
        else:
            self.semantic_alignment_optimizer = None
            if not AI_CONTENT_UNDERSTANDING_AVAILABLE:
                self.logger.info("AI内容理解增强系统不可用")
                self.logger.warning("增强字幕生成器不可用，使用传统模式")
            else:
                self.logger.info("使用传统字幕生成模式")
    
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
            
            # 创建音频文件映射
            audio_map = {audio["slide_number"]: audio for audio in audio_files}
            
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
                
                slide_number = script["slide_number"]
                self.logger.info(f"生成第 {slide_number} 页字幕")
                
                # 获取对应的音频信息
                audio_info = audio_map.get(slide_number)
                if not audio_info:
                    self.logger.warning(f"未找到第 {slide_number} 页的音频信息，跳过字幕生成")
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
            if self.enable_frame_sync and self.frame_sync_optimizer:
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
            if self.enable_audio_sync and self.audio_sync_optimizer:
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
            if self.enable_ai_content_understanding and self.semantic_alignment_optimizer:
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
        slide_number = script["slide_number"]
        script_content = script["script_content"]
        
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
            # 分割文本为字幕片段 - 支持异步智能分割
            subtitle_segments = await self._split_text_to_segments(script_content)
            
            # 计算时间分配
            start_time = audio_info["start_time"]
            duration = audio_info["duration_seconds"]
            
            # 创建字幕项
            subtitles = []
            current_time = start_time
            
            for i, segment in enumerate(subtitle_segments):
                # 计算这个片段的时长
                segment_duration = self._calculate_segment_duration(segment, duration, len(subtitle_segments), i)
                
                # 创建字幕项
                subtitle_item = pysrt.SubRipItem(
                    index=start_index + i,
                    start=self._seconds_to_srt_time(current_time),
                    end=self._seconds_to_srt_time(current_time + segment_duration),
                    text=segment
                )
                
                subtitles.append(subtitle_item)
                current_time += segment_duration
            
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
        将文本分割为合适的字幕片段 - 支持智能分割
        
        Args:
            text: 输入文本
            
        Returns:
            字幕片段列表
        """
        # 清理文本
        text = text.strip()
        if not text:
            return []
        
        # 优先使用智能字幕处理器
        if self.hybrid_splitter:
            try:
                segments = await self.hybrid_splitter.split_subtitle_text(text)
                if segments:
                    self.logger.debug(f"智能分割成功: {len(segments)} 个片段")
                    return segments
            except Exception as e:
                self.logger.warning(f"智能分割失败，使用传统方法: {e}")
        
        # 传统分割方法作为fallback
        return self._legacy_split_text(text)
    
    def _legacy_split_text(self, text: str) -> List[str]:
        """
        传统文本分割方法
        
        Args:
            text: 输入文本
            
        Returns:
            字幕片段列表
        """
        segments = []
        current_segment = ""
        
        # 按标点符号分割
        sentences = re.split(f'([{self.subtitle_config["line_break_chars"]}])', text)
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i].strip()
                punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
                
                if sentence:
                    sentence_with_punct = sentence + punctuation
                    
                    # 检查当前片段加上新句子是否超过长度限制
                    if len(current_segment + sentence_with_punct) <= self.subtitle_config["max_chars_per_line"]:
                        current_segment += sentence_with_punct
                    else:
                        # 如果当前片段不为空，保存它
                        if current_segment:
                            segments.append(current_segment.strip())
                        
                        # 检查单个句子是否过长
                        if len(sentence_with_punct) <= self.subtitle_config["max_chars_per_line"]:
                            current_segment = sentence_with_punct
                        else:
                            # 句子过长，需要进一步分割
                            long_segments = self._split_long_sentence(sentence_with_punct)
                            segments.extend(long_segments[:-1])
                            current_segment = long_segments[-1] if long_segments else ""
        
        # 添加最后的片段
        if current_segment:
            segments.append(current_segment.strip())
        
        # 如果没有有效分割，返回原文本的截断版本
        if not segments:
            max_length = self.subtitle_config["max_chars_per_line"]
            segments = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        return [seg for seg in segments if seg.strip()]
    
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
        
        # 清理多余空白
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
        计算字幕片段的显示时长
        
        Args:
            segment: 字幕片段文本
            total_duration: 总时长
            total_segments: 总片段数
            segment_index: 当前片段索引
            
        Returns:
            片段时长（秒）
        """
        # 基于字符数计算基础时长
        char_count = len(segment.replace(" ", ""))
        base_duration = char_count / self.subtitle_config["words_per_second"]
        
        # 确保在合理范围内
        min_duration = self.subtitle_config["min_display_time"]
        max_duration = self.subtitle_config["max_display_time"]
        
        # 如果只有一个片段，使用总时长
        if total_segments == 1:
            return min(max(total_duration, min_duration), max_duration)
        
        # 多个片段时，按比例分配
        if total_segments > 1:
            # 简单平均分配，但考虑字符数权重
            avg_duration = total_duration / total_segments
            
            # 基于字符数调整
            weight = char_count / (sum(len(seg) for seg in [segment]) / total_segments)
            adjusted_duration = avg_duration * weight
            
            return min(max(adjusted_duration, min_duration), max_duration)
        
        return min(max(base_duration, min_duration), max_duration)
    
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
    
    async def _get_video_metadata_for_sync(self) -> Optional['VideoMetadata']:
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
                            return await self.frame_sync_optimizer.analyze_video_metadata(video_path)
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
                script_content = script.get("script_content", "")
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
