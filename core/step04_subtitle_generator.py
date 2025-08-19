"""
步骤4: 字幕生成器
基于讲话稿内容和音频时间轴生成SRT字幕文件
"""
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
import logging
import re
import html

import pysrt

from utils.logger import get_logger
from utils.file_manager import FileManager

class SubtitleGenerator:
    """字幕生成器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # 字幕配置
        self.subtitle_config = {
            "max_chars_per_line": 40,     # 每行最大字符数
            "max_lines": 2,               # 最大行数
            "min_display_time": 1.0,      # 最小显示时间（秒）
            "max_display_time": 8.0,      # 最大显示时间（秒）
            "words_per_second": 3.5,      # 阅读速度（字/秒）
            "line_break_chars": "，。！？；：",  # 断行标点符号
        }
    
    async def generate_subtitles(self, scripts_data: Dict[str, Any], audio_data: Dict[str, Any], 
                               progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """
        生成所有页面的字幕文件
        
        Args:
            scripts_data: 讲话稿数据
            audio_data: 音频数据
            progress_callback: 进度回调函数
            
        Returns:
            字幕数据字典
        """
        try:
            self.logger.info("开始生成字幕文件")
            
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
                "combined_subtitle_info": None
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
            # 分割文本为字幕片段
            subtitle_segments = self._split_text_to_segments(script_content)
            
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
    
    def _split_text_to_segments(self, text: str) -> List[str]:
        """
        将文本分割为合适的字幕片段
        
        Args:
            text: 输入文本
            
        Returns:
            字幕片段列表
        """
        # 清理文本
        text = text.strip()
        if not text:
            return []
        
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
