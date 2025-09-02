"""
增强版字幕生成器 - Netflix级字幕处理机制
基于精确时间对齐和智能间隙填充算法
"""
import os
import re
import pandas as pd
import pysrt
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime
import logging
import dataclasses

from utils.logger import get_logger
from utils.file_manager import FileManager


class EnhancedSubtitleGenerator:
    """增强版字幕生成器 - 实现Netflix级字幕处理"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # 增强的字幕配置
        self.subtitle_config = {
            "max_chars_per_line": 40,           # 每行最大字符数
            "max_lines": 2,                     # 最大行数
            "min_display_time": 1.0,            # 最小显示时间(秒)
            "max_display_time": 8.0,            # 最大显示时间(秒)
            "words_per_second": 3.5,            # 每秒字数(用于时长估算)
            "line_break_chars": "，。！？；：",   # 断句标点
            "gap_threshold": 1.0,               # 间隙填充阈值(秒)
            "enable_gap_filling": True,         # 启用间隙填充
            "enable_precise_alignment": True,   # 启用精确对齐
            "auto_punctuation_removal": True,   # 自动移除显示用标点
        }
        
        self.logger.info(f"增强版字幕生成器初始化完成: {self.subtitle_config}")
    
    def remove_punctuation(self, text: str) -> str:
        """移除标点符号，用于精确匹配"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()
    
    def convert_to_srt_format(self, start_time: float, end_time: float) -> str:
        """转换为SRT时间格式"""
        def seconds_to_hmsm(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            milliseconds = int(secs * 1000) % 1000
            return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{milliseconds:03d}"
        
        start_srt = seconds_to_hmsm(start_time)
        end_srt = seconds_to_hmsm(end_time)
        return f"{start_srt} --> {end_srt}"
    
    def show_alignment_difference(self, expected: str, actual: str) -> None:
        """显示对齐差异，用于调试"""
        min_len = min(len(expected), len(actual))
        diff_positions = []
        
        for i in range(min_len):
            if expected[i] != actual[i]:
                diff_positions.append(i)
        
        if len(expected) != len(actual):
            diff_positions.extend(range(min_len, max(len(expected), len(actual))))
        
        self.logger.debug(f"对齐差异分析:")
        self.logger.debug(f"期望文本: {expected}")
        self.logger.debug(f"实际文本: {actual}")
        self.logger.debug(f"差异位置: {diff_positions}")
    
    def get_precise_timestamps(self, word_level_data: List[Dict], sentences: List[str]) -> List[Tuple[float, float]]:
        """
        Netflix级精确时间对齐算法
        
        Args:
            word_level_data: 词级别的时间数据 [{"text": "word", "start": 0.0, "end": 1.0}, ...]
            sentences: 句子列表
            
        Returns:
            每个句子的(开始时间, 结束时间)列表
        """
        if not self.subtitle_config["enable_precise_alignment"] or not word_level_data:
            return self._fallback_timestamp_calculation(word_level_data, sentences)
        
        self.logger.info("使用精确时间对齐算法")
        timestamp_list = []
        
        # 构建完整的词汇字符串和位置映射
        full_words_str = ''
        position_to_word_idx = {}
        
        for idx, word_data in enumerate(word_level_data):
            clean_word = self.remove_punctuation(str(word_data.get('text', '')).lower())
            start_pos = len(full_words_str)
            full_words_str += clean_word
            for pos in range(start_pos, len(full_words_str)):
                position_to_word_idx[pos] = idx
        
        self.logger.debug(f"构建词汇字符串: {full_words_str[:100]}...")
        
        current_pos = 0
        for sentence_idx, sentence in enumerate(sentences):
            clean_sentence = self.remove_punctuation(sentence.lower()).replace(" ", "")
            sentence_len = len(clean_sentence)
            
            if sentence_len == 0:
                self.logger.warning(f"句子 {sentence_idx} 清理后为空: '{sentence}'")
                continue
            
            match_found = False
            search_start = current_pos
            
            # 在剩余文本中搜索匹配
            while search_start <= len(full_words_str) - sentence_len:
                if full_words_str[search_start:search_start + sentence_len] == clean_sentence:
                    start_word_idx = position_to_word_idx[search_start]
                    end_word_idx = position_to_word_idx[search_start + sentence_len - 1]
                    
                    start_time = float(word_level_data[start_word_idx].get('start', 0))
                    end_time = float(word_level_data[end_word_idx].get('end', 0))
                    
                    timestamp_list.append((start_time, end_time))
                    current_pos = search_start + sentence_len
                    match_found = True
                    
                    self.logger.debug(f"句子 {sentence_idx} 精确匹配: {start_time:.2f}-{end_time:.2f}")
                    break
                search_start += 1
            
            if not match_found:
                self.logger.warning(f"句子 {sentence_idx} 无法找到精确匹配: {sentence}")
                self.show_alignment_difference(
                    clean_sentence, 
                    full_words_str[current_pos:current_pos+len(clean_sentence)]
                )
                
                # 使用回退方案
                fallback_timestamps = self._fallback_timestamp_calculation(
                    word_level_data[max(0, current_pos-5):current_pos+15], [sentence]
                )
                if fallback_timestamps:
                    timestamp_list.append(fallback_timestamps[0])
                    current_pos += max(1, sentence_len // 2)  # 移动位置避免重复匹配
                else:
                    # 最后的回退方案
                    if timestamp_list:
                        last_end = timestamp_list[-1][1]
                        estimated_duration = len(sentence) / (self.subtitle_config["words_per_second"] * 10)
                        timestamp_list.append((last_end, last_end + max(1.0, estimated_duration)))
                    else:
                        timestamp_list.append((0.0, 3.0))
        
        self.logger.info(f"精确对齐完成，生成 {len(timestamp_list)} 个时间戳")
        return timestamp_list
    
    def fill_gaps(self, timestamps: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Netflix级间隙填充算法 - 优化观看体验
        """
        if not self.subtitle_config["enable_gap_filling"] or len(timestamps) < 2:
            return timestamps
        
        self.logger.info("应用间隙填充算法")
        filled_timestamps = []
        gap_threshold = self.subtitle_config["gap_threshold"]
        gaps_filled = 0
        
        for i, (start, end) in enumerate(timestamps):
            if i < len(timestamps) - 1:
                next_start = timestamps[i + 1][0]
                gap = next_start - end
                
                # 如果间隙小于阈值且为正数，延长当前字幕到下一个开始
                if 0 < gap < gap_threshold:
                    filled_timestamps.append((start, next_start))
                    gaps_filled += 1
                    self.logger.debug(f"填充间隙 {i}: {gap:.2f}s")
                else:
                    filled_timestamps.append((start, end))
            else:
                filled_timestamps.append((start, end))
        
        self.logger.info(f"间隙填充完成，共填充 {gaps_filled} 个间隙")
        return filled_timestamps
    
    def _fallback_timestamp_calculation(self, word_data: List[Dict], sentences: List[str]) -> List[Tuple[float, float]]:
        """回退的时间戳计算方法"""
        if not word_data or not sentences:
            self.logger.warning("回退方案: 缺少词汇数据或句子")
            return []
        
        self.logger.info("使用回退时间戳计算方法")
        
        total_duration = float(word_data[-1].get('end', 1)) - float(word_data[0].get('start', 0))
        time_per_sentence = total_duration / len(sentences) if len(sentences) > 0 else 1.0
        
        timestamps = []
        base_start = float(word_data[0].get('start', 0))
        
        for i, sentence in enumerate(sentences):
            start_time = base_start + i * time_per_sentence
            end_time = start_time + time_per_sentence
            
            # 应用最小/最大显示时间限制
            duration = end_time - start_time
            if duration < self.subtitle_config["min_display_time"]:
                end_time = start_time + self.subtitle_config["min_display_time"]
            elif duration > self.subtitle_config["max_display_time"]:
                end_time = start_time + self.subtitle_config["max_display_time"]
            
            timestamps.append((start_time, end_time))
        
        return timestamps
    
    def _estimate_timestamps_from_audio(self, sentences: List[str], start_time: float, duration: float) -> List[Tuple[float, float]]:
        """基于音频信息估算时间戳"""
        self.logger.info(f"基于音频估算时间戳: {len(sentences)} 个句子，总时长 {duration:.2f}s")
        
        timestamps = []
        current_time = start_time
        
        # 计算每个句子的相对长度权重
        total_chars = sum(len(s) for s in sentences)
        
        for i, sentence in enumerate(sentences):
            if total_chars > 0:
                sentence_ratio = len(sentence) / total_chars
            else:
                sentence_ratio = 1.0 / len(sentences)
            
            sentence_duration = duration * sentence_ratio
            
            # 确保最小和最大显示时间
            sentence_duration = max(
                self.subtitle_config["min_display_time"],
                min(sentence_duration, self.subtitle_config["max_display_time"])
            )
            
            timestamps.append((current_time, current_time + sentence_duration))
            current_time += sentence_duration
        
        return timestamps
    
    def _seconds_to_srt_time(self, seconds: float) -> pysrt.SubRipTime:
        """转换秒数为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return pysrt.SubRipTime(hours, minutes, secs, milliseconds)
    
    def _split_text_to_segments(self, text: str) -> List[str]:
        """
        智能文本分割 - 优化观看体验
        """
        text = text.strip()
        if not text:
            return []
        
        segments = []
        current_segment = ""
        max_chars = self.subtitle_config["max_chars_per_line"]
        line_break_chars = self.subtitle_config["line_break_chars"]
        
        # 首先按标点符号分割
        sentences = re.split(f'([{line_break_chars}])', text)
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i].strip()
                punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
                
                if sentence:
                    sentence_with_punct = sentence + punctuation
                    
                    # 检查是否可以合并到当前段落
                    if len(current_segment + sentence_with_punct) <= max_chars:
                        current_segment += sentence_with_punct
                    else:
                        # 保存当前段落
                        if current_segment:
                            segments.append(current_segment.strip())
                        
                        # 检查新句子是否过长
                        if len(sentence_with_punct) <= max_chars:
                            current_segment = sentence_with_punct
                        else:
                            # 分割过长句子
                            segments.extend(self._split_long_sentence(sentence_with_punct))
                            current_segment = ""
        
        # 添加最后的段落
        if current_segment:
            segments.append(current_segment.strip())
        
        # 过滤空段落
        segments = [seg for seg in segments if seg.strip()]
        
        self.logger.debug(f"文本分割完成: '{text}' -> {len(segments)} 个段落")
        return segments
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """分割过长句子"""
        max_length = self.subtitle_config["max_chars_per_line"]
        segments = []
        
        # 尝试按逗号分割
        parts = sentence.split('，')
        current_part = ""
        
        for part in parts:
            test_part = current_part + part + '，' if current_part else part + '，'
            
            if len(test_part) <= max_length:
                current_part = test_part
            else:
                # 保存当前部分
                if current_part:
                    segments.append(current_part.rstrip('，'))
                
                # 处理新部分
                if len(part) <= max_length:
                    current_part = part + '，'
                else:
                    # 强制分割
                    segments.extend([part[i:i+max_length] for i in range(0, len(part), max_length)])
                    current_part = ""
        
        # 添加最后部分
        if current_part:
            segments.append(current_part.rstrip('，'))
        
        return segments
    
    def _clean_subtitle_text(self, text: str) -> str:
        """清理字幕文本以优化显示效果"""
        if not self.subtitle_config["auto_punctuation_removal"]:
            return text
        
        # 替换某些标点符号为空格或移除
        cleaned = re.sub(r'[，。]', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    async def generate_enhanced_subtitles(
        self, 
        scripts_data: Dict[str, Any], 
        audio_data: Dict[str, Any],
        word_level_data: Optional[List[Dict]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        生成增强版字幕 - Netflix级处理
        
        Args:
            scripts_data: 脚本数据
            audio_data: 音频数据
            word_level_data: 词级别时间数据（可选，用于精确对齐）
            progress_callback: 进度回调
        """
        try:
            self.logger.info("开始生成增强版字幕")
            
            # 确保字幕目录存在
            self.file_manager.subtitles_dir.mkdir(parents=True, exist_ok=True)
            
            scripts = scripts_data.get("scripts", [])
            all_subtitles = []
            subtitle_index = 1
            total_scripts = len(scripts)
            
            # 统计信息
            stats = {
                "total_segments": 0,
                "precise_alignments": 0,
                "fallback_alignments": 0,
                "gaps_filled": 0
            }
            
            for i, script in enumerate(scripts):
                if progress_callback:
                    progress = int((i / total_scripts) * 80)
                    progress_callback(progress)
                
                slide_number = script["slide_number"]
                script_content = script["script_content"]
                
                self.logger.info(f"生成第 {slide_number} 页字幕")
                
                # 智能分割文本
                sentences = self._split_text_to_segments(script_content)
                
                if not sentences:
                    self.logger.warning(f"第 {slide_number} 页没有有效文本")
                    continue
                
                stats["total_segments"] += len(sentences)
                
                # 获取时间戳
                if word_level_data and slide_number <= len(word_level_data):
                    # 使用精确对齐
                    slide_word_data = word_level_data[slide_number - 1]
                    timestamps = self.get_precise_timestamps(slide_word_data, sentences)
                    stats["precise_alignments"] += len(timestamps)
                else:
                    # 使用音频信息进行估算
                    audio_info = next((a for a in audio_data.get("audio_files", []) 
                                     if a["slide_number"] == slide_number), None)
                    if audio_info:
                        timestamps = self._estimate_timestamps_from_audio(
                            sentences, 
                            audio_info.get("start_time", 0), 
                            audio_info.get("duration_seconds", 3.0)
                        )
                        stats["fallback_alignments"] += len(timestamps)
                    else:
                        self.logger.warning(f"第 {slide_number} 页缺少音频信息")
                        continue
                
                # 应用间隙填充
                original_count = len(timestamps)
                timestamps = self.fill_gaps(timestamps)
                
                # 生成字幕项
                for j, (sentence, (start_time, end_time)) in enumerate(zip(sentences, timestamps)):
                    # 清理字幕文本
                    cleaned_text = self._clean_subtitle_text(sentence)
                    
                    subtitle_item = pysrt.SubRipItem(
                        index=subtitle_index,
                        start=self._seconds_to_srt_time(start_time),
                        end=self._seconds_to_srt_time(end_time),
                        text=cleaned_text
                    )
                    all_subtitles.append(subtitle_item)
                    subtitle_index += 1
                    
                    self.logger.debug(f"字幕 {subtitle_index-1}: {start_time:.2f}-{end_time:.2f} '{cleaned_text}'")
            
            # 保存字幕文件
            combined_srt = pysrt.SubRipFile(all_subtitles)
            subtitle_path = self.file_manager.subtitles_dir / "enhanced_subtitle.srt"
            combined_srt.save(str(subtitle_path), encoding='utf-8')
            
            # 同时生成传统格式以保持兼容性
            traditional_path = self.file_manager.subtitles_dir / "combined_subtitle.srt"
            combined_srt.save(str(traditional_path), encoding='utf-8')
            
            subtitle_data = {
                "subtitle_generation_completed": True,
                "enhanced_features_used": True,
                "total_subtitles": len(all_subtitles),
                "subtitle_file": "enhanced_subtitle.srt",
                "traditional_subtitle_file": "combined_subtitle.srt",
                "gap_filling_enabled": self.subtitle_config["enable_gap_filling"],
                "precise_alignment_enabled": self.subtitle_config["enable_precise_alignment"],
                "generation_timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "config_used": self.subtitle_config.copy()
            }
            
            if progress_callback:
                progress_callback(100)
            
            self.logger.info(f"增强版字幕生成完成: {len(all_subtitles)} 个字幕项")
            self.logger.info(f"统计信息: {stats}")
            return subtitle_data
            
        except Exception as e:
            self.logger.error(f"增强版字幕生成失败: {e}", exc_info=True)
            raise
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新字幕配置"""
        self.subtitle_config.update(new_config)
        self.logger.info(f"字幕配置已更新: {new_config}")
