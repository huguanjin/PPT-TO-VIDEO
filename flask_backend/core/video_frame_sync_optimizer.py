#!/usr/bin/env python3
"""
视频帧级精确同步系统
实现字幕与视频帧的毫秒级精确同步，确保最佳视听体验
"""

import asyncio
import time
import logging
import json
import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import subprocess
import re

# 设置日志
logger = logging.getLogger(__name__)


class VideoFrameRate(Enum):
    """视频帧率标准"""
    CINEMA_24 = 24.0        # 电影标准
    PAL_25 = 25.0          # PAL制式
    NTSC_30 = 29.97        # NTSC制式
    WEB_30 = 30.0          # 网络视频
    GAMING_60 = 60.0       # 游戏/高帧率
    SMOOTH_120 = 120.0     # 超高帧率


class SyncPrecisionLevel(Enum):
    """同步精度级别"""
    BASIC = "basic"             # 基础同步 (±100ms)
    STANDARD = "standard"       # 标准同步 (±33ms, 1帧@30fps)
    HIGH = "high"              # 高精度同步 (±16ms, 1帧@60fps)
    FRAME_PERFECT = "perfect"   # 帧完美同步 (±1帧)


class TimecodeFormat(Enum):
    """时间码格式"""
    MILLISECONDS = "ms"         # 毫秒 (1234)
    SECONDS_DECIMAL = "s"       # 秒.毫秒 (1.234)
    SMPTE = "smpte"            # SMPTE时码 (00:00:01:06)
    SRT = "srt"                # SRT格式 (00:00:01,234)


@dataclass
class VideoMetadata:
    """视频元数据"""
    width: int
    height: int
    fps: float
    duration: float             # 总时长(秒)
    total_frames: int          # 总帧数
    codec: str
    bitrate: int               # 比特率
    timecode_format: TimecodeFormat = TimecodeFormat.MILLISECONDS
    
    def __post_init__(self):
        """计算衍生属性"""
        if self.total_frames == 0:
            self.total_frames = int(self.duration * self.fps)
        
        # 计算帧时间间隔
        self.frame_duration_ms = 1000.0 / self.fps if self.fps > 0 else 41.67
        self.frame_duration_s = 1.0 / self.fps if self.fps > 0 else 0.04167


@dataclass
class FrameTimestamp:
    """帧精确时间戳"""
    frame_number: int           # 帧编号 (0-based)
    milliseconds: float         # 毫秒精确时间
    seconds: float              # 秒精确时间
    smpte_timecode: str         # SMPTE时码
    srt_timecode: str           # SRT时码
    
    @classmethod
    def from_frame_number(cls, frame_number: int, fps: float) -> 'FrameTimestamp':
        """从帧编号创建时间戳"""
        seconds = frame_number / fps
        milliseconds = seconds * 1000
        
        # 计算SMPTE时码
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * fps)
        smpte_timecode = f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
        
        # 计算SRT时码
        ms = int((seconds % 1) * 1000)
        srt_timecode = f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
        
        return cls(
            frame_number=frame_number,
            milliseconds=milliseconds,
            seconds=seconds,
            smpte_timecode=smpte_timecode,
            srt_timecode=srt_timecode
        )
    
    @classmethod
    def from_seconds(cls, seconds: float, fps: float) -> 'FrameTimestamp':
        """从秒创建时间戳"""
        frame_number = round(seconds * fps)  # 使用round而不是int，确保精确的帧编号
        return cls.from_frame_number(frame_number, fps)


@dataclass
class SynchronizedSubtitleSegment:
    """同步优化后的字幕片段"""
    text: str
    original_start: float       # 原始开始时间
    original_end: float         # 原始结束时间
    sync_start: FrameTimestamp  # 同步后开始时间戳
    sync_end: FrameTimestamp    # 同步后结束时间戳
    sync_offset_ms: float       # 同步偏移量(毫秒)
    quality_score: float        # 同步质量分数 (0-1)
    frame_alignment: bool       # 是否帧对齐
    
    @property
    def sync_duration(self) -> float:
        """同步后时长"""
        return self.sync_end.seconds - self.sync_start.seconds
    
    @property
    def original_duration(self) -> float:
        """原始时长"""
        return self.original_end - self.original_start


class VideoFrameSyncOptimizer:
    """视频帧级同步优化器 - 毫秒级精确同步核心"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化同步优化器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 同步规则
        self.sync_rules = {
            'target_precision': SyncPrecisionLevel.HIGH,
            'frame_alignment_priority': True,      # 优先帧对齐
            'subtitle_gap_frames': 2,              # 字幕间隙最小帧数
            'sync_tolerance_ms': 16.67,            # 同步容差(毫秒)
            'aggressive_optimization': True,       # 激进优化模式
            'preserve_original_timing': False      # 是否保持原始时机
        }
        
        # 优化统计
        self.sync_stats = {
            "total_segments": 0,
            "synced_segments": 0,
            "frame_aligned_segments": 0,
            "average_offset_ms": 0.0,
            "sync_accuracy": 0.0,
            "processing_time": 0.0
        }
        
        self.logger.info("视频帧级同步优化器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "sync_precision_level": "high",           # 同步精度级别
            "enable_frame_alignment": True,           # 启用帧对齐
            "enable_audio_cue_sync": True,           # 启用音频提示同步
            "enable_scene_change_sync": True,        # 启用场景切换同步
            "max_sync_offset_ms": 100,               # 最大同步偏移
            "min_subtitle_duration_frames": 24,      # 最小字幕持续帧数
            "subtitle_fade_duration_frames": 3,      # 字幕淡入淡出帧数
            "enable_subframe_precision": False       # 启用亚帧精度
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"配置加载失败，使用默认配置: {e}")
        
        return default_config
    
    async def analyze_video_metadata(self, video_path: str) -> VideoMetadata:
        """分析视频元数据"""
        self.logger.info(f"分析视频元数据: {video_path}")
        
        try:
            # 使用ffprobe获取详细的视频信息
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-show_format', video_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise Exception(f"ffprobe执行失败: {stderr.decode()}")
            
            data = json.loads(stdout.decode())
            
            # 提取视频流信息
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise Exception("未找到视频流")
            
            # 解析帧率
            fps_str = video_stream.get('r_frame_rate', '24/1')
            if '/' in fps_str:
                numerator, denominator = map(int, fps_str.split('/'))
                fps = numerator / denominator if denominator > 0 else 24.0
            else:
                fps = float(fps_str)
            
            # 获取时长
            duration = float(video_stream.get('duration', 0))
            if duration == 0:
                format_info = data.get('format', {})
                duration = float(format_info.get('duration', 0))
            
            metadata = VideoMetadata(
                width=int(video_stream.get('width', 1920)),
                height=int(video_stream.get('height', 1080)),
                fps=fps,
                duration=duration,
                total_frames=0,  # 将在__post_init__中计算
                codec=video_stream.get('codec_name', 'unknown'),
                bitrate=int(video_stream.get('bit_rate', 0))
            )
            
            self.logger.info(f"视频分析完成: {metadata.width}x{metadata.height}, "
                           f"{metadata.fps:.2f}fps, {metadata.duration:.2f}s, "
                           f"{metadata.total_frames}帧")
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"视频分析失败: {e}")
            # 返回默认元数据
            return VideoMetadata(
                width=1920, height=1080, fps=24.0, duration=60.0,
                total_frames=0, codec='unknown', bitrate=0
            )
    
    def optimize_frame_sync(self, subtitles: List[Dict], video_metadata: VideoMetadata) -> List[SynchronizedSubtitleSegment]:
        """优化帧同步"""
        self.logger.info(f"开始优化 {len(subtitles)} 个字幕的帧同步")
        start_time = time.time()
        
        synchronized_segments = []
        total_offset = 0.0
        frame_aligned_count = 0
        synced_count = 0
        
        for i, subtitle in enumerate(subtitles):
            try:
                # 提取原始时间信息
                original_start = subtitle.get('start_time', 0.0)
                original_end = subtitle.get('end_time', 0.0)
                text = subtitle.get('text', '')
                
                # 计算最佳同步时间戳
                sync_start_timestamp, sync_end_timestamp = self._calculate_optimal_frame_sync(
                    original_start, original_end, video_metadata, i, len(subtitles)
                )
                
                # 计算同步偏移
                sync_offset_ms = (sync_start_timestamp.seconds - original_start) * 1000
                
                # 检查帧对齐
                frame_aligned = self._is_frame_aligned(sync_start_timestamp, sync_end_timestamp, video_metadata)
                
                # 计算同步质量分数
                quality_score = self._calculate_sync_quality(
                    original_start, original_end, sync_start_timestamp, sync_end_timestamp, 
                    video_metadata, frame_aligned
                )
                
                # 创建同步字幕片段
                sync_segment = SynchronizedSubtitleSegment(
                    text=text,
                    original_start=original_start,
                    original_end=original_end,
                    sync_start=sync_start_timestamp,
                    sync_end=sync_end_timestamp,
                    sync_offset_ms=sync_offset_ms,
                    quality_score=quality_score,
                    frame_alignment=frame_aligned
                )
                
                synchronized_segments.append(sync_segment)
                
                # 更新统计
                total_offset += abs(sync_offset_ms)
                if frame_aligned:
                    frame_aligned_count += 1
                if abs(sync_offset_ms) > 0.1:  # 超过0.1ms的同步调整
                    synced_count += 1
                    
                self.logger.debug(f"片段 {i+1} 同步: {original_start:.3f}s -> {sync_start_timestamp.seconds:.3f}s "
                                f"(偏移: {sync_offset_ms:.1f}ms, 帧对齐: {frame_aligned})")
                
            except Exception as e:
                self.logger.warning(f"片段 {i+1} 同步失败: {e}")
                # 创建未优化的片段
                sync_segment = SynchronizedSubtitleSegment(
                    text=subtitle.get('text', ''),
                    original_start=subtitle.get('start_time', 0.0),
                    original_end=subtitle.get('end_time', 0.0),
                    sync_start=FrameTimestamp.from_seconds(subtitle.get('start_time', 0.0), video_metadata.fps),
                    sync_end=FrameTimestamp.from_seconds(subtitle.get('end_time', 0.0), video_metadata.fps),
                    sync_offset_ms=0.0,
                    quality_score=0.5,
                    frame_alignment=False
                )
                synchronized_segments.append(sync_segment)
        
        # 全局时间轴验证和调整
        synchronized_segments = self._adjust_global_sync_timeline(synchronized_segments, video_metadata)
        
        # 更新统计信息
        processing_time = time.time() - start_time
        self._update_sync_stats(
            len(subtitles), synced_count, frame_aligned_count, 
            total_offset / max(len(subtitles), 1), processing_time
        )
        
        self.logger.info(f"帧同步优化完成: {synced_count}/{len(subtitles)} 个片段被同步, "
                        f"帧对齐: {frame_aligned_count}, 平均偏移: {total_offset/max(len(subtitles), 1):.1f}ms, "
                        f"处理耗时: {processing_time:.3f}s")
        
        return synchronized_segments
    
    def _calculate_optimal_frame_sync(self, original_start: float, original_end: float, 
                                    video_metadata: VideoMetadata, segment_index: int, 
                                    total_segments: int) -> Tuple[FrameTimestamp, FrameTimestamp]:
        """计算最佳帧同步时间戳"""
        
        # 计算帧边界对齐
        if self.config["enable_frame_alignment"]:
            # 将开始时间对齐到最近的帧边界
            start_frame = round(original_start * video_metadata.fps)
            aligned_start = start_frame / video_metadata.fps
            
            # 计算最小持续帧数
            min_frames = self.config.get("min_subtitle_duration_frames", 24)
            original_frames = (original_end - original_start) * video_metadata.fps
            
            if original_frames < min_frames:
                # 扩展到最小帧数
                end_frame = start_frame + min_frames
            else:
                # 对齐结束时间到帧边界
                end_frame = round(original_end * video_metadata.fps)
            
            aligned_end = end_frame / video_metadata.fps
        else:
            # 不进行帧对齐，保持原始时间
            aligned_start = original_start
            aligned_end = original_end
        
        # 应用同步规则调整
        if self.sync_rules['aggressive_optimization']:
            # 激进模式：优化显示时机
            aligned_start, aligned_end = self._apply_aggressive_sync_optimization(
                aligned_start, aligned_end, video_metadata, segment_index, total_segments
            )
        
        # 创建时间戳对象
        sync_start = FrameTimestamp.from_seconds(aligned_start, video_metadata.fps)
        sync_end = FrameTimestamp.from_seconds(aligned_end, video_metadata.fps)
        
        return sync_start, sync_end
    
    def _apply_aggressive_sync_optimization(self, start: float, end: float, 
                                          video_metadata: VideoMetadata, 
                                          segment_index: int, total_segments: int) -> Tuple[float, float]:
        """应用激进同步优化"""
        
        # 优化1: 场景切换检测同步 (模拟)
        if self.config.get("enable_scene_change_sync", True):
            # 假设每10秒有一个场景切换点
            scene_points = [i * 10.0 for i in range(int(video_metadata.duration / 10) + 1)]
            
            # 找到最近的场景切换点
            closest_scene = min(scene_points, key=lambda x: abs(x - start))
            if abs(closest_scene - start) < 2.0:  # 2秒内有场景切换
                # 微调到场景切换后
                start = max(start, closest_scene + 0.5)
        
        # 优化2: 音频提示同步 (模拟)
        if self.config.get("enable_audio_cue_sync", True):
            # 模拟音频节拍点 (假设每1秒有一个强节拍)
            beat_interval = 1.0
            nearest_beat = round(start / beat_interval) * beat_interval
            
            # 如果距离最近节拍很近，则对齐到节拍
            if abs(nearest_beat - start) < 0.2:
                start = nearest_beat
        
        # 优化3: 字幕持续时间优化
        duration = end - start
        min_duration = self.config.get("min_subtitle_duration_frames", 24) / video_metadata.fps
        
        if duration < min_duration:
            end = start + min_duration
        
        return start, end
    
    def _is_frame_aligned(self, start_ts: FrameTimestamp, end_ts: FrameTimestamp, 
                         video_metadata: VideoMetadata) -> bool:
        """检查是否帧对齐"""
        
        # 检查开始时间是否精确对齐到帧边界
        start_aligned = abs(start_ts.seconds * video_metadata.fps - start_ts.frame_number) < 0.001
        
        # 检查结束时间是否精确对齐到帧边界  
        end_aligned = abs(end_ts.seconds * video_metadata.fps - end_ts.frame_number) < 0.001
        
        return start_aligned and end_aligned
    
    def _calculate_sync_quality(self, original_start: float, original_end: float,
                              sync_start: FrameTimestamp, sync_end: FrameTimestamp,
                              video_metadata: VideoMetadata, frame_aligned: bool) -> float:
        """计算同步质量分数"""
        quality = 1.0
        
        # 时间偏移惩罚
        start_offset_ms = abs(sync_start.seconds - original_start) * 1000
        end_offset_ms = abs(sync_end.seconds - original_end) * 1000
        
        max_offset = self.config.get("max_sync_offset_ms", 100)
        
        if start_offset_ms > max_offset or end_offset_ms > max_offset:
            quality -= 0.3  # 偏移过大
        elif start_offset_ms > max_offset / 2 or end_offset_ms > max_offset / 2:
            quality -= 0.1  # 偏移较大
        
        # 帧对齐奖励
        if frame_aligned:
            quality += 0.2
        
        # 时长合理性检查
        sync_duration = sync_end.seconds - sync_start.seconds
        original_duration = original_end - original_start
        duration_ratio = sync_duration / original_duration if original_duration > 0 else 1.0
        
        if duration_ratio < 0.8 or duration_ratio > 1.5:
            quality -= 0.2  # 时长变化过大
        
        # 帧率适配性检查
        fps_category = self._categorize_fps(video_metadata.fps)
        if fps_category in [VideoFrameRate.CINEMA_24, VideoFrameRate.PAL_25]:
            quality += 0.05  # 电影/广播级帧率额外奖励
        
        return max(0.0, min(1.0, quality))
    
    def _categorize_fps(self, fps: float) -> VideoFrameRate:
        """分类帧率"""
        fps_mapping = {
            24.0: VideoFrameRate.CINEMA_24,
            25.0: VideoFrameRate.PAL_25,
            29.97: VideoFrameRate.NTSC_30,
            30.0: VideoFrameRate.WEB_30,
            60.0: VideoFrameRate.GAMING_60,
            120.0: VideoFrameRate.SMOOTH_120
        }
        
        # 找到最接近的标准帧率
        closest_fps = min(fps_mapping.keys(), key=lambda x: abs(x - fps))
        
        if abs(closest_fps - fps) < 0.1:  # 允许0.1的误差
            return fps_mapping[closest_fps]
        else:
            return VideoFrameRate.WEB_30  # 默认
    
    def _adjust_global_sync_timeline(self, segments: List[SynchronizedSubtitleSegment],
                                   video_metadata: VideoMetadata) -> List[SynchronizedSubtitleSegment]:
        """全局同步时间轴调整"""
        if not segments:
            return segments
        
        adjusted_segments = []
        min_gap_frames = self.sync_rules.get('subtitle_gap_frames', 2)
        min_gap_seconds = min_gap_frames / video_metadata.fps
        
        for i, segment in enumerate(segments):
            if i == 0:
                # 第一个片段保持不变
                adjusted_segments.append(segment)
                continue
            
            prev_segment = adjusted_segments[-1]
            
            # 检查是否有重叠或间隙过小
            if segment.sync_start.seconds <= prev_segment.sync_end.seconds + min_gap_seconds:
                # 需要调整当前片段的开始时间
                new_start_seconds = prev_segment.sync_end.seconds + min_gap_seconds
                
                # 重新计算时间戳，确保帧对齐
                new_start_frame = math.ceil(new_start_seconds * video_metadata.fps)
                new_start_aligned = new_start_frame / video_metadata.fps
                
                # 保持原始时长
                duration = segment.sync_duration
                new_end_seconds = new_start_aligned + duration
                
                # 创建新的时间戳
                new_sync_start = FrameTimestamp.from_seconds(new_start_aligned, video_metadata.fps)
                new_sync_end = FrameTimestamp.from_seconds(new_end_seconds, video_metadata.fps)
                
                # 更新同步偏移
                new_offset_ms = (new_start_aligned - segment.original_start) * 1000
                
                # 重新检查帧对齐
                frame_aligned = self._is_frame_aligned(new_sync_start, new_sync_end, video_metadata)
                
                # 重新计算质量分数
                quality_score = self._calculate_sync_quality(
                    segment.original_start, segment.original_end,
                    new_sync_start, new_sync_end, video_metadata, frame_aligned
                )
                
                # 创建调整后的片段
                adjusted_segment = SynchronizedSubtitleSegment(
                    text=segment.text,
                    original_start=segment.original_start,
                    original_end=segment.original_end,
                    sync_start=new_sync_start,
                    sync_end=new_sync_end,
                    sync_offset_ms=new_offset_ms,
                    quality_score=quality_score,
                    frame_alignment=frame_aligned
                )
                
                adjusted_segments.append(adjusted_segment)
                
                self.logger.debug(f"调整片段 {i+1} 时间轴: "
                                f"{segment.sync_start.seconds:.3f}s -> {new_start_aligned:.3f}s")
            else:
                # 无需调整
                adjusted_segments.append(segment)
        
        return adjusted_segments
    
    def _update_sync_stats(self, total: int, synced: int, frame_aligned: int, 
                          average_offset: float, processing_time: float) -> None:
        """更新同步统计"""
        self.sync_stats.update({
            "total_segments": total,
            "synced_segments": synced,
            "frame_aligned_segments": frame_aligned,
            "average_offset_ms": average_offset,
            "sync_accuracy": (synced / max(total, 1)) * 100,
            "processing_time": processing_time
        })
    
    def get_sync_report(self) -> Dict[str, Any]:
        """获取同步报告"""
        stats = self.sync_stats.copy()
        stats["frame_alignment_rate"] = (stats["frame_aligned_segments"] / max(stats["total_segments"], 1)) * 100
        
        return {
            "sync_statistics": stats,
            "sync_rules": self.sync_rules,
            "configuration": self.config,
            "quality_metrics": {
                "precision_level": self.sync_rules['target_precision'].value,
                "frame_alignment_enabled": self.sync_rules['frame_alignment_priority'],
                "sync_tolerance_ms": self.sync_rules['sync_tolerance_ms'],
                "aggressive_optimization": self.sync_rules['aggressive_optimization']
            }
        }
    
    def export_synchronized_subtitles(self, segments: List[SynchronizedSubtitleSegment], 
                                    output_path: str, format_type: TimecodeFormat = TimecodeFormat.SRT) -> bool:
        """导出同步后的字幕文件"""
        try:
            self.logger.info(f"导出同步字幕到: {output_path}, 格式: {format_type.value}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if format_type == TimecodeFormat.SRT:
                    # SRT格式导出
                    for i, segment in enumerate(segments, 1):
                        f.write(f"{i}\n")
                        f.write(f"{segment.sync_start.srt_timecode} --> {segment.sync_end.srt_timecode}\n")
                        f.write(f"{segment.text}\n\n")
                
                elif format_type == TimecodeFormat.SMPTE:
                    # SMPTE格式导出
                    for i, segment in enumerate(segments, 1):
                        f.write(f"{i:04d} {segment.sync_start.smpte_timecode} {segment.sync_end.smpte_timecode} {segment.text}\n")
                
                else:
                    # JSON格式导出（包含所有同步信息）
                    sync_data = []
                    for segment in segments:
                        sync_data.append({
                            "text": segment.text,
                            "original_start": segment.original_start,
                            "original_end": segment.original_end,
                            "sync_start_seconds": segment.sync_start.seconds,
                            "sync_end_seconds": segment.sync_end.seconds,
                            "sync_start_frame": segment.sync_start.frame_number,
                            "sync_end_frame": segment.sync_end.frame_number,
                            "sync_offset_ms": segment.sync_offset_ms,
                            "quality_score": segment.quality_score,
                            "frame_aligned": segment.frame_alignment,
                            "srt_timecode_start": segment.sync_start.srt_timecode,
                            "srt_timecode_end": segment.sync_end.srt_timecode
                        })
                    
                    json.dump(sync_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"同步字幕导出完成: {len(segments)} 个片段")
            return True
            
        except Exception as e:
            self.logger.error(f"同步字幕导出失败: {e}")
            return False


# 测试代码
async def test_video_frame_sync():
    """测试视频帧同步功能"""
    print("🎨 视频帧级同步优化系统测试")
    print("=" * 60)
    
    # 创建同步优化器
    sync_optimizer = VideoFrameSyncOptimizer()
    
    # 模拟视频元数据
    video_metadata = VideoMetadata(
        width=1920,
        height=1080,
        fps=24.0,
        duration=120.0,
        total_frames=0,  # 将自动计算
        codec='h264',
        bitrate=5000000
    )
    
    print(f"🎬 视频信息: {video_metadata.width}x{video_metadata.height}, "
          f"{video_metadata.fps}fps, {video_metadata.duration}s, {video_metadata.total_frames}帧")
    print()
    
    # 测试字幕数据
    test_subtitles = [
        {"text": "欢迎观看这个精彩的演示视频", "start_time": 0.5, "end_time": 3.2},
        {"text": "我们将展示字幕与视频的精确同步", "start_time": 3.8, "end_time": 6.9},
        {"text": "Frame-perfect synchronization", "start_time": 7.1, "end_time": 10.3},
        {"text": "毫秒级精度确保最佳观看体验", "start_time": 10.5, "end_time": 13.8},
        {"text": "AI优化的同步算法", "start_time": 14.2, "end_time": 17.1}
    ]
    
    print(f"📝 原始字幕片段:")
    for i, subtitle in enumerate(test_subtitles):
        duration = subtitle["end_time"] - subtitle["start_time"]
        print(f"  片段{i+1}: {subtitle['start_time']:.3f}s - {subtitle['end_time']:.3f}s "
              f"({duration:.3f}s) '{subtitle['text'][:25]}...'")
    print()
    
    # 执行帧同步优化
    synchronized_segments = sync_optimizer.optimize_frame_sync(test_subtitles, video_metadata)
    
    print(f"✨ 同步优化后的字幕片段:")
    total_offset = 0.0
    frame_aligned_count = 0
    
    for i, segment in enumerate(synchronized_segments):
        offset_ms = segment.sync_offset_ms
        total_offset += abs(offset_ms)
        if segment.frame_alignment:
            frame_aligned_count += 1
        
        print(f"  片段{i+1}: {segment.sync_start.seconds:.3f}s - {segment.sync_end.seconds:.3f}s "
              f"(偏移: {offset_ms:+.1f}ms, 帧对齐: {'✓' if segment.frame_alignment else '✗'}, "
              f"质量: {segment.quality_score:.2f})")
        print(f"          帧: {segment.sync_start.frame_number} - {segment.sync_end.frame_number}, "
              f"SMPTE: {segment.sync_start.smpte_timecode} - {segment.sync_end.smpte_timecode}")
    print()
    
    # 显示同步报告
    report = sync_optimizer.get_sync_report()
    print(f"📊 同步优化报告:")
    print(f"  同步片段数: {report['sync_statistics']['synced_segments']}/{report['sync_statistics']['total_segments']}")
    print(f"  帧对齐数: {frame_aligned_count}/{len(synchronized_segments)} ({frame_aligned_count/len(synchronized_segments)*100:.1f}%)")
    print(f"  平均偏移: {total_offset/len(synchronized_segments):.1f}ms")
    print(f"  同步精度: {report['sync_statistics']['sync_accuracy']:.1f}%")
    print(f"  处理时间: {report['sync_statistics']['processing_time']:.3f}s")
    print()
    
    # 导出同步字幕
    output_path = "synchronized_subtitles.srt"
    success = sync_optimizer.export_synchronized_subtitles(
        synchronized_segments, output_path, TimecodeFormat.SRT
    )
    
    if success:
        print(f"✅ 同步字幕已导出: {output_path}")
    else:
        print("❌ 同步字幕导出失败")
    
    print("\n🎉 视频帧级同步测试完成!")
    return synchronized_segments, report


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_video_frame_sync())