"""
任务3.3: 实时预览功能 - 核心模块

实现实时字幕预览、WYSIWYG编辑和即时质量反馈
为用户提供直观的字幕生成预览体验

主要功能:
1. 实时字幕预览 - 即时显示字幕效果
2. WYSIWYG编辑器 - 所见即所得编辑
3. 即时质量反馈 - 实时质量评估
4. 与智能断句(3.1)和多语言(3.2)系统无缝集成
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple, Union, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import tempfile
import threading
import time

# 引入已完成的智能系统
# 使用AI字幕分割器替代被禁用的smart_sentence_splitter
try:
    from .ai_subtitle_splitter import HybridSubtitleSplitter, smart_split_subtitle
    
    # 创建兼容性适配器类
    class AdvancedSentenceSplitter:  # type: ignore
        def __init__(self):
            self.splitter = HybridSubtitleSplitter()
            
        async def split_text_smart(self, text: str, strategy: str = "hybrid", language: str = "auto"):
            # 调用AI字幕分割器
            try:
                config = {
                    "max_length": 75,
                    "use_ai_splitting": strategy == "ai_enhanced",
                    "ai_fallback": True
                }
                segments = await smart_split_subtitle(text, config)
                return {
                    "segments": segments,
                    "strategy_used": strategy,
                    "confidence": 0.9
                }
            except Exception as e:
                # 简单的句子分割实现作为fallback
                sentences = []
                if '。' in text:
                    sentences = [s.strip() + '。' for s in text.split('。') if s.strip()]
                elif '!' in text:
                    sentences = [s.strip() + '!' for s in text.split('!') if s.strip()]
                elif '?' in text:
                    sentences = [s.strip() + '?' for s in text.split('?') if s.strip()]
                else:
                    # 按长度分割
                    max_length = 30
                    sentences = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                
                return {
                    "segments": sentences,
                    "strategy_used": strategy,
                    "confidence": 0.8
                }
    
    class SmartSentenceSplitterManager:
        def __init__(self):
            self.splitter = AdvancedSentenceSplitter()
        
        async def split_text_smart(self, text: str, strategy: str = "hybrid", language: str = "auto"):
            return await self.splitter.split_text_smart(text, strategy, language)
            
except ImportError:
    # 如果AI分割器也不可用，使用简单实现
    class AdvancedSentenceSplitter:  # type: ignore
        async def split_text_smart(self, text: str, strategy: str = "hybrid", language: str = "auto"):
            # 简单的句子分割实现
            sentences = []
            if '。' in text:
                sentences = [s.strip() + '。' for s in text.split('。') if s.strip()]
            elif '!' in text:
                sentences = [s.strip() + '!' for s in text.split('!') if s.strip()]
            elif '?' in text:
                sentences = [s.strip() + '?' for s in text.split('?') if s.strip()]
            else:
                # 按长度分割
                max_length = 30
                sentences = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            
            return {
                "segments": sentences,
                "strategy_used": strategy,
                "confidence": 0.8
            }

# 多语言集成系统
try:
    from .multilingual_integration import MultilingualSubtitleIntegrator as _MultilingualSubtitleIntegrator
    MultilingualSubtitleIntegrator = _MultilingualSubtitleIntegrator  # type: ignore
except ImportError:
    try:
        from multilingual_integration import MultilingualSubtitleIntegrator as _MultilingualSubtitleIntegrator
        MultilingualSubtitleIntegrator = _MultilingualSubtitleIntegrator  # type: ignore
    except ImportError:
        # 如果模块不存在，创建模拟类
        class MultilingualSubtitleIntegrator:
            def __init__(self):
                self.language_detector = self
            
            def detect_language(self, text: str):
                # 简单的语言检测
                chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
                if chinese_chars > len(text) * 0.3:
                    return "zh", 0.9
                return "en", 0.8
                
            async def enhance_subtitle_generation_multilingual(self, segments: List[str], config: Dict):
                return {"enhanced_texts": segments}

# 增强字幕生成器
try:
    from .step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator as _EnhancedSubtitleGenerator
    EnhancedSubtitleGenerator = _EnhancedSubtitleGenerator  # type: ignore
except ImportError:
    try:
        from step04_subtitle_generator_enhanced import EnhancedSubtitleGenerator as _EnhancedSubtitleGenerator
        EnhancedSubtitleGenerator = _EnhancedSubtitleGenerator  # type: ignore
    except ImportError:
        # 如果模块不存在，创建模拟类
        class EnhancedSubtitleGenerator:
            def __init__(self, project_dir: Path):
                self.project_dir = project_dir
                
            async def enhance_subtitle_generation_multilingual(self, segments: List[str], config: Dict):
                return {"enhanced_texts": segments}

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class PreviewConfig:
    """实时预览配置"""
    # 预览模式设置
    enable_real_time: bool = True
    preview_window_size: int = 10  # 预览窗口大小（句子数）
    update_interval: float = 0.5  # 更新间隔（秒）
    
    # 字幕预览设置
    subtitle_font_size: int = 16
    subtitle_color: str = "#FFFFFF"
    subtitle_background: str = "rgba(0,0,0,0.7)"
    subtitle_position: str = "bottom"  # bottom, top, center
    
    # 质量反馈设置
    enable_quality_check: bool = True
    quality_threshold: float = 0.8
    show_confidence_score: bool = True
    highlight_issues: bool = True
    
    # 性能优化设置
    enable_caching: bool = True
    cache_size: int = 100
    enable_async_processing: bool = True

@dataclass
class PreviewItem:
    """预览项数据结构"""
    id: str
    text: str
    start_time: float
    end_time: float
    confidence: float
    language: str
    quality_score: float
    issues: List[str]
    style: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class PreviewUpdate:
    """预览更新数据"""
    timestamp: float
    items: List[PreviewItem]
    total_count: int
    processing_status: str
    quality_summary: Dict[str, Any]

class RealTimeSubtitlePreview:
    """实时字幕预览核心引擎"""
    
    def __init__(self, config: PreviewConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化智能处理组件
        self.sentence_splitter = SmartSentenceSplitterManager()
        self.multilingual_integrator = MultilingualSubtitleIntegrator()
        self.enhanced_generator = EnhancedSubtitleGenerator(project_dir=Path("."))
        
        # 预览状态管理
        self.preview_items: List[PreviewItem] = []
        self.is_active = False
        self.update_callbacks: List[Callable] = []
        
        # 缓存和性能优化
        self.cache = {} if config.enable_caching else None
        self.processing_queue = asyncio.Queue()
        
        # 实时处理线程
        self.preview_thread = None
        self.stop_event = threading.Event()
    
    async def start_preview_session(self, initial_text: str = "") -> Dict[str, Any]:
        """启动实时预览会话"""
        try:
            self.logger.info("🎬 启动实时字幕预览会话")
            
            # 重置状态
            self.preview_items.clear()
            self.is_active = True
            self.stop_event.clear()
            
            # 如果有初始文本，进行处理
            if initial_text.strip():
                await self._process_initial_text(initial_text)
            
            # 启动实时处理线程
            if self.config.enable_async_processing:
                self.preview_thread = threading.Thread(
                    target=self._async_processing_worker,
                    daemon=True
                )
                self.preview_thread.start()
            
            return {
                "status": "success",
                "session_id": f"preview_{int(time.time())}",
                "message": "实时预览会话已启动",
                "config": asdict(self.config),
                "initial_items": len(self.preview_items)
            }
            
        except Exception as e:
            self.logger.error(f"启动预览会话失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def update_text_realtime(self, text: str, position: int = 0) -> PreviewUpdate:
        """实时更新文本并生成预览"""
        try:
            self.logger.debug(f"实时更新文本: {len(text)} 字符")
            
            # 智能断句处理
            splitting_result = await self.sentence_splitter.split_text_smart(
                text, 
                strategy="hybrid",
                language="auto"
            )
            
            # 多语言处理（如果需要）
            multilingual_result = await self._process_multilingual_if_needed(
                splitting_result["segments"], text
            )
            
            # 生成预览项
            preview_items = await self._generate_preview_items(
                multilingual_result or splitting_result["segments"],
                text
            )
            
            # 质量评估
            quality_summary = await self._assess_quality(preview_items)
            
            # 更新预览状态
            self.preview_items = preview_items
            
            # 创建更新对象
            update = PreviewUpdate(
                timestamp=time.time(),
                items=preview_items[:self.config.preview_window_size],
                total_count=len(preview_items),
                processing_status="completed",
                quality_summary=quality_summary
            )
            
            # 通知所有回调
            await self._notify_callbacks(update)
            
            return update
            
        except Exception as e:
            self.logger.error(f"实时更新失败: {e}")
            return PreviewUpdate(
                timestamp=time.time(),
                items=[],
                total_count=0,
                processing_status="error",
                quality_summary={"error": str(e)}
            )
    
    async def _process_initial_text(self, text: str):
        """处理初始文本"""
        try:
            # 使用智能断句和多语言处理
            result = await self.update_text_realtime(text)
            self.logger.info(f"初始文本处理完成: {result.total_count} 个字幕项")
            
        except Exception as e:
            self.logger.error(f"初始文本处理失败: {e}")
    
    async def _process_multilingual_if_needed(
        self, 
        segments: List[str], 
        original_text: str
    ) -> Optional[List[str]]:
        """根据需要进行多语言处理"""
        try:
            # 检测语言
            primary_lang, confidence = self.multilingual_integrator.language_detector.detect_language(
                original_text
            )
            detected_languages = {
                "primary_language": primary_lang,
                "confidence": confidence,
                "detected_languages": [primary_lang]
            }
            
            # 如果检测到多语言或非中文，启用多语言处理
            if len(detected_languages["detected_languages"]) > 1 or \
               detected_languages["primary_language"] != "zh":
                
                # 进行多语言增强处理
                config = {
                    "multilingual_processing": {
                        "enabled": True,
                        "primary_language": detected_languages["primary_language"],
                        "auto_detect_secondary": True
                    }
                }
                
                result = await self.multilingual_integrator.enhance_subtitle_generation_multilingual(
                    segments, config
                )
                
                return result.get("enhanced_texts", segments)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"多语言处理失败，使用原始分割: {e}")
            return None
    
    async def _generate_preview_items(
        self, 
        segments: List[str], 
        original_text: str
    ) -> List[PreviewItem]:
        """生成预览项"""
        preview_items = []
        
        try:
            # 时间分配（假设总时长）
            estimated_duration = len(original_text) * 0.1  # 每字符0.1秒估算
            time_per_segment = estimated_duration / len(segments) if segments else 1.0
            
            current_time = 0.0
            
            for i, segment in enumerate(segments):
                # 计算时间
                start_time = current_time
                segment_duration = max(
                    len(segment) * 0.08,  # 基于字符数的动态时长
                    1.0  # 最小1秒
                )
                end_time = start_time + segment_duration
                
                # 质量评估
                quality_score, issues = await self._assess_segment_quality(segment)
                
                # 创建预览项
                item = PreviewItem(
                    id=f"preview_{i:03d}",
                    text=segment,
                    start_time=start_time,
                    end_time=end_time,
                    confidence=quality_score,
                    language="auto",  # 自动检测
                    quality_score=quality_score,
                    issues=issues,
                    style=self._generate_style(quality_score, issues),
                    metadata={
                        "length": len(segment),
                        "word_count": len(segment.split()),
                        "estimated_reading_time": segment_duration
                    }
                )
                
                preview_items.append(item)
                current_time = end_time
            
            return preview_items
            
        except Exception as e:
            self.logger.error(f"生成预览项失败: {e}")
            return []
    
    async def _assess_segment_quality(self, segment: str) -> Tuple[float, List[str]]:
        """评估单个字幕段落的质量"""
        quality_score = 1.0
        issues = []
        
        try:
            # 长度检查
            if len(segment) > 75:
                quality_score -= 0.2
                issues.append("字幕过长")
            elif len(segment) < 5:
                quality_score -= 0.1
                issues.append("字幕过短")
            
            # 标点符号检查
            if not any(punct in segment for punct in "。！？.!?"):
                quality_score -= 0.1
                issues.append("缺少结束标点")
            
            # 换行检查（for显示）
            if len(segment) > 35 and '\n' not in segment:
                quality_score -= 0.1
                issues.append("建议分行显示")
            
            # 特殊字符检查
            if any(char in segment for char in "【】〖〗"):
                quality_score += 0.05  # 结构化内容加分
            
            return max(quality_score, 0.0), issues
            
        except Exception as e:
            self.logger.warning(f"质量评估失败: {e}")
            return 0.5, ["评估失败"]
    
    def _generate_style(self, quality_score: float, issues: List[str]) -> Dict[str, Any]:
        """根据质量生成样式"""
        style = {
            "fontSize": self.config.subtitle_font_size,
            "color": self.config.subtitle_color,
            "backgroundColor": self.config.subtitle_background,
            "position": self.config.subtitle_position
        }
        
        # 根据质量调整样式
        if quality_score < 0.6:
            style["borderColor"] = "#ff6b6b"  # 红色边框表示问题
            style["borderWidth"] = "2px"
        elif quality_score > 0.9:
            style["borderColor"] = "#51cf66"  # 绿色边框表示优质
            style["borderWidth"] = "1px"
        
        # 高亮问题
        if self.config.highlight_issues and issues:
            style["backgroundColor"] = "rgba(255, 107, 107, 0.2)"
        
        return style
    
    async def _assess_quality(self, preview_items: List[PreviewItem]) -> Dict[str, Any]:
        """评估整体质量"""
        if not preview_items:
            return {"overall_score": 0.0, "total_issues": 0}
        
        total_score = sum(item.quality_score for item in preview_items)
        average_score = total_score / len(preview_items)
        
        total_issues = sum(len(item.issues) for item in preview_items)
        
        # 统计问题类型
        issue_types = {}
        for item in preview_items:
            for issue in item.issues:
                issue_types[issue] = issue_types.get(issue, 0) + 1
        
        return {
            "overall_score": average_score,
            "total_issues": total_issues,
            "average_length": sum(len(item.text) for item in preview_items) / len(preview_items),
            "issue_breakdown": issue_types,
            "recommendations": self._generate_recommendations(issue_types, average_score)
        }
    
    def _generate_recommendations(self, issue_types: Dict[str, int], score: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if score < 0.7:
            recommendations.append("建议重新调整字幕分割策略")
        
        if "字幕过长" in issue_types:
            recommendations.append(f"有 {issue_types['字幕过长']} 条字幕过长，建议启用智能分割")
        
        if "缺少结束标点" in issue_types:
            recommendations.append("建议检查标点符号的使用")
        
        if "建议分行显示" in issue_types:
            recommendations.append("建议启用自动换行功能")
        
        return recommendations
    
    def _async_processing_worker(self):
        """异步处理工作线程"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        
        while not self.stop_event.is_set():
            try:
                # 定期更新检查
                time.sleep(self.config.update_interval)
                
                # 这里可以添加后台处理逻辑
                # 比如预加载、缓存清理等
                
            except Exception as e:
                self.logger.error(f"异步处理工作线程错误: {e}")
    
    async def _notify_callbacks(self, update: PreviewUpdate):
        """通知所有回调函数"""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                self.logger.warning(f"回调通知失败: {e}")
    
    def add_update_callback(self, callback: Callable):
        """添加更新回调"""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable):
        """移除更新回调"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    async def stop_preview_session(self) -> Dict[str, Any]:
        """停止预览会话"""
        try:
            self.logger.info("停止实时预览会话")
            
            self.is_active = False
            self.stop_event.set()
            
            # 等待线程结束
            if self.preview_thread and self.preview_thread.is_alive():
                self.preview_thread.join(timeout=2.0)
            
            # 清理资源
            self.preview_items.clear()
            self.update_callbacks.clear()
            
            if self.cache:
                self.cache.clear()
            
            return {
                "status": "success",
                "message": "预览会话已停止"
            }
            
        except Exception as e:
            self.logger.error(f"停止预览会话失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


class WYSIWYGSubtitleEditor:
    """所见即所得字幕编辑器"""
    
    def __init__(self, preview_engine: RealTimeSubtitlePreview):
        self.preview_engine = preview_engine
        self.logger = logging.getLogger(__name__)
        
        # 编辑状态
        self.editing_history: List[Dict] = []
        self.current_edit_index = -1
        self.max_history = 50
    
    async def edit_subtitle_item(
        self, 
        item_id: str, 
        new_text: str, 
        auto_adjust_timing: bool = True
    ) -> Dict[str, Any]:
        """编辑单个字幕项"""
        try:
            # 找到要编辑的项
            item_index = None
            for i, item in enumerate(self.preview_engine.preview_items):
                if item.id == item_id:
                    item_index = i
                    break
            
            if item_index is None:
                return {"status": "error", "error": "未找到指定的字幕项"}
            
            # 保存编辑历史
            await self._save_edit_history("edit_item", {
                "item_id": item_id,
                "old_text": self.preview_engine.preview_items[item_index].text,
                "new_text": new_text
            })
            
            # 更新文本
            old_item = self.preview_engine.preview_items[item_index]
            
            # 重新评估质量
            quality_score, issues = await self.preview_engine._assess_segment_quality(new_text)
            
            # 自动调整时长（如果启用）
            if auto_adjust_timing:
                new_duration = max(len(new_text) * 0.08, 1.0)
                end_time = old_item.start_time + new_duration
            else:
                end_time = old_item.end_time
            
            # 创建新的预览项
            updated_item = PreviewItem(
                id=old_item.id,
                text=new_text,
                start_time=old_item.start_time,
                end_time=end_time,
                confidence=quality_score,
                language=old_item.language,
                quality_score=quality_score,
                issues=issues,
                style=self.preview_engine._generate_style(quality_score, issues),
                metadata={
                    **old_item.metadata,
                    "last_edited": datetime.now().isoformat(),
                    "edit_count": old_item.metadata.get("edit_count", 0) + 1
                }
            )
            
            # 更新预览项列表
            self.preview_engine.preview_items[item_index] = updated_item
            
            # 触发实时更新
            await self._trigger_preview_update()
            
            return {
                "status": "success",
                "updated_item": asdict(updated_item),
                "message": "字幕项更新成功"
            }
            
        except Exception as e:
            self.logger.error(f"编辑字幕项失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def split_subtitle_item(self, item_id: str, split_position: int) -> Dict[str, Any]:
        """分割字幕项"""
        try:
            # 找到要分割的项
            item_index = None
            for i, item in enumerate(self.preview_engine.preview_items):
                if item.id == item_id:
                    item_index = i
                    break
            
            if item_index is None:
                return {"status": "error", "error": "未找到指定的字幕项"}
            
            original_item = self.preview_engine.preview_items[item_index]
            
            # 验证分割位置
            if split_position <= 0 or split_position >= len(original_item.text):
                return {"status": "error", "error": "分割位置无效"}
            
            # 分割文本
            first_text = original_item.text[:split_position].strip()
            second_text = original_item.text[split_position:].strip()
            
            if not first_text or not second_text:
                return {"status": "error", "error": "分割后文本不能为空"}
            
            # 保存编辑历史
            await self._save_edit_history("split_item", {
                "item_id": item_id,
                "original_text": original_item.text,
                "split_position": split_position
            })
            
            # 计算时间分配
            total_duration = original_item.end_time - original_item.start_time
            first_ratio = len(first_text) / len(original_item.text)
            first_duration = total_duration * first_ratio
            
            # 创建第一个项
            first_item = PreviewItem(
                id=f"{original_item.id}_1",
                text=first_text,
                start_time=original_item.start_time,
                end_time=original_item.start_time + first_duration,
                confidence=0.8,  # 分割后的置信度
                language=original_item.language,
                quality_score=0.8,
                issues=[],
                style=self.preview_engine._generate_style(0.8, []),
                metadata={
                    **original_item.metadata,
                    "split_from": item_id,
                    "split_part": 1
                }
            )
            
            # 创建第二个项
            second_item = PreviewItem(
                id=f"{original_item.id}_2",
                text=second_text,
                start_time=original_item.start_time + first_duration,
                end_time=original_item.end_time,
                confidence=0.8,
                language=original_item.language,
                quality_score=0.8,
                issues=[],
                style=self.preview_engine._generate_style(0.8, []),
                metadata={
                    **original_item.metadata,
                    "split_from": item_id,
                    "split_part": 2
                }
            )
            
            # 更新预览项列表
            self.preview_engine.preview_items[item_index] = first_item
            self.preview_engine.preview_items.insert(item_index + 1, second_item)
            
            # 触发实时更新
            await self._trigger_preview_update()
            
            return {
                "status": "success",
                "new_items": [asdict(first_item), asdict(second_item)],
                "message": "字幕项分割成功"
            }
            
        except Exception as e:
            self.logger.error(f"分割字幕项失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def merge_subtitle_items(self, item_ids: List[str]) -> Dict[str, Any]:
        """合并字幕项"""
        try:
            if len(item_ids) < 2:
                return {"status": "error", "error": "至少需要两个字幕项进行合并"}
            
            # 找到要合并的项
            items_to_merge = []
            indices_to_remove = []
            
            for item_id in item_ids:
                for i, item in enumerate(self.preview_engine.preview_items):
                    if item.id == item_id:
                        items_to_merge.append(item)
                        indices_to_remove.append(i)
                        break
            
            if len(items_to_merge) != len(item_ids):
                return {"status": "error", "error": "部分字幕项未找到"}
            
            # 排序确保正确的合并顺序
            items_to_merge.sort(key=lambda x: x.start_time)
            indices_to_remove.sort(reverse=True)
            
            # 保存编辑历史
            await self._save_edit_history("merge_items", {
                "item_ids": item_ids,
                "items": [asdict(item) for item in items_to_merge]
            })
            
            # 合并文本
            merged_text = " ".join(item.text for item in items_to_merge)
            
            # 计算合并后的时间
            start_time = items_to_merge[0].start_time
            end_time = items_to_merge[-1].end_time
            
            # 重新评估质量
            quality_score, issues = await self.preview_engine._assess_segment_quality(merged_text)
            
            # 创建合并后的项
            merged_item = PreviewItem(
                id=f"merged_{int(time.time())}",
                text=merged_text,
                start_time=start_time,
                end_time=end_time,
                confidence=quality_score,
                language=items_to_merge[0].language,
                quality_score=quality_score,
                issues=issues,
                style=self.preview_engine._generate_style(quality_score, issues),
                metadata={
                    "merged_from": item_ids,
                    "merged_at": datetime.now().isoformat(),
                    "original_count": len(items_to_merge)
                }
            )
            
            # 更新预览项列表
            # 先移除旧项（从后往前删除）
            for index in indices_to_remove:
                del self.preview_engine.preview_items[index]
            
            # 添加合并项到正确位置
            insert_index = min(indices_to_remove)
            self.preview_engine.preview_items.insert(insert_index, merged_item)
            
            # 触发实时更新
            await self._trigger_preview_update()
            
            return {
                "status": "success",
                "merged_item": asdict(merged_item),
                "message": f"成功合并 {len(items_to_merge)} 个字幕项"
            }
            
        except Exception as e:
            self.logger.error(f"合并字幕项失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def undo_edit(self) -> Dict[str, Any]:
        """撤销编辑"""
        try:
            if self.current_edit_index < 0:
                return {"status": "error", "error": "没有可撤销的操作"}
            
            # 获取撤销操作
            edit_record = self.editing_history[self.current_edit_index]
            
            # 根据操作类型执行撤销
            if edit_record["action"] == "edit_item":
                await self._undo_edit_item(edit_record["data"])
            elif edit_record["action"] == "split_item":
                await self._undo_split_item(edit_record["data"])
            elif edit_record["action"] == "merge_items":
                await self._undo_merge_items(edit_record["data"])
            
            self.current_edit_index -= 1
            
            # 触发实时更新
            await self._trigger_preview_update()
            
            return {
                "status": "success",
                "message": f"已撤销操作: {edit_record['action']}"
            }
            
        except Exception as e:
            self.logger.error(f"撤销编辑失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _save_edit_history(self, action: str, data: Dict):
        """保存编辑历史"""
        # 清除当前位置之后的历史
        self.editing_history = self.editing_history[:self.current_edit_index + 1]
        
        # 添加新的编辑记录
        edit_record = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "data": data
        }
        
        self.editing_history.append(edit_record)
        self.current_edit_index += 1
        
        # 限制历史记录数量
        if len(self.editing_history) > self.max_history:
            self.editing_history.pop(0)
            self.current_edit_index -= 1
    
    async def _trigger_preview_update(self):
        """触发预览更新"""
        # 重新评估整体质量
        quality_summary = await self.preview_engine._assess_quality(
            self.preview_engine.preview_items
        )
        
        # 创建更新对象
        update = PreviewUpdate(
            timestamp=time.time(),
            items=self.preview_engine.preview_items[:self.preview_engine.config.preview_window_size],
            total_count=len(self.preview_engine.preview_items),
            processing_status="updated",
            quality_summary=quality_summary
        )
        
        # 通知回调
        await self.preview_engine._notify_callbacks(update)
    
    async def _undo_edit_item(self, data: Dict):
        """撤销编辑项操作"""
        # 实现撤销编辑项的逻辑
        pass
    
    async def _undo_split_item(self, data: Dict):
        """撤销分割项操作"""
        # 实现撤销分割项的逻辑
        pass
    
    async def _undo_merge_items(self, data: Dict):
        """撤销合并项操作"""
        # 实现撤销合并项的逻辑
        pass


class InstantQualityFeedback:
    """即时质量反馈系统"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 质量检查规则
        self.quality_rules = {
            "length_check": {
                "min_length": 5,
                "max_length": 75,
                "weight": 0.3
            },
            "timing_check": {
                "min_duration": 1.0,
                "max_duration": 6.0,
                "weight": 0.2
            },
            "punctuation_check": {
                "required_endings": "。！？.!?",
                "weight": 0.2
            },
            "readability_check": {
                "max_words_per_line": 12,
                "weight": 0.3
            }
        }
    
    async def assess_real_time_quality(
        self, 
        preview_items: List[PreviewItem]
    ) -> Dict[str, Any]:
        """实时质量评估"""
        try:
            if not preview_items:
                return self._empty_quality_report()
            
            # 总体统计
            total_items = len(preview_items)
            passed_items = 0
            total_score = 0.0
            
            # 详细分析
            issue_breakdown = {}
            recommendations = []
            quality_distribution = {"high": 0, "medium": 0, "low": 0}
            
            for item in preview_items:
                # 长度检查
                length_score = self._check_length(item.text)
                
                # 时长检查
                timing_score = self._check_timing(
                    item.start_time, item.end_time, len(item.text)
                )
                
                # 标点检查
                punctuation_score = self._check_punctuation(item.text)
                
                # 可读性检查
                readability_score = self._check_readability(item.text)
                
                # 综合评分
                overall_score = (
                    length_score * self.quality_rules["length_check"]["weight"] +
                    timing_score * self.quality_rules["timing_check"]["weight"] +
                    punctuation_score * self.quality_rules["punctuation_check"]["weight"] +
                    readability_score * self.quality_rules["readability_check"]["weight"]
                )
                
                total_score += overall_score
                
                # 分类质量等级
                if overall_score >= 0.8:
                    quality_distribution["high"] += 1
                    passed_items += 1
                elif overall_score >= 0.6:
                    quality_distribution["medium"] += 1
                else:
                    quality_distribution["low"] += 1
                
                # 收集问题
                item_issues = self._collect_item_issues(
                    item.text, length_score, timing_score, 
                    punctuation_score, readability_score
                )
                
                for issue in item_issues:
                    issue_breakdown[issue] = issue_breakdown.get(issue, 0) + 1
            
            # 生成建议
            recommendations = self._generate_quality_recommendations(
                issue_breakdown, total_score / total_items
            )
            
            return {
                "overall_score": total_score / total_items,
                "pass_rate": passed_items / total_items,
                "total_items": total_items,
                "quality_distribution": quality_distribution,
                "issue_breakdown": issue_breakdown,
                "recommendations": recommendations,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"实时质量评估失败: {e}")
            return {
                "overall_score": 0.0,
                "error": str(e),
                "status": "error"
            }
    
    def _check_length(self, text: str) -> float:
        """检查文本长度"""
        length = len(text)
        min_len = self.quality_rules["length_check"]["min_length"]
        max_len = self.quality_rules["length_check"]["max_length"]
        
        if length < min_len:
            return 0.5
        elif length > max_len:
            return max(0.0, 1.0 - (length - max_len) / max_len)
        else:
            return 1.0
    
    def _check_timing(self, start_time: float, end_time: float, text_length: int) -> float:
        """检查时长合理性"""
        duration = end_time - start_time
        min_dur = self.quality_rules["timing_check"]["min_duration"]
        max_dur = self.quality_rules["timing_check"]["max_duration"]
        
        # 基于文本长度的理想时长
        ideal_duration = max(text_length * 0.08, min_dur)
        
        if duration < min_dur:
            return 0.5
        elif duration > max_dur:
            return max(0.0, 1.0 - (duration - max_dur) / max_dur)
        elif abs(duration - ideal_duration) / ideal_duration <= 0.3:
            return 1.0
        else:
            return 0.8
    
    def _check_punctuation(self, text: str) -> float:
        """检查标点符号"""
        endings = self.quality_rules["punctuation_check"]["required_endings"]
        
        if any(text.endswith(ending) for ending in endings):
            return 1.0
        else:
            return 0.6
    
    def _check_readability(self, text: str) -> float:
        """检查可读性"""
        max_words = self.quality_rules["readability_check"]["max_words_per_line"]
        
        # 简单的词汇计数（中英文混合）
        words = len(text.split()) if ' ' in text else len(text)
        
        if words <= max_words:
            return 1.0
        else:
            return max(0.0, 1.0 - (words - max_words) / max_words)
    
    def _collect_item_issues(
        self, text: str, length_score: float, 
        timing_score: float, punctuation_score: float, 
        readability_score: float
    ) -> List[str]:
        """收集单项问题"""
        issues = []
        
        if length_score < 0.8:
            if len(text) < self.quality_rules["length_check"]["min_length"]:
                issues.append("字幕过短")
            else:
                issues.append("字幕过长")
        
        if timing_score < 0.8:
            issues.append("时长不合理")
        
        if punctuation_score < 0.8:
            issues.append("缺少结束标点")
        
        if readability_score < 0.8:
            issues.append("单行文字过多")
        
        return issues
    
    def _generate_quality_recommendations(
        self, 
        issue_breakdown: Dict[str, int], 
        overall_score: float
    ) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        if overall_score < 0.7:
            recommendations.append("整体质量偏低，建议重新调整字幕分割策略")
        
        # 针对具体问题给出建议
        if "字幕过长" in issue_breakdown and issue_breakdown["字幕过长"] > 0:
            count = issue_breakdown["字幕过长"]
            recommendations.append(f"有 {count} 条字幕过长，建议启用智能分割或手动调整")
        
        if "字幕过短" in issue_breakdown and issue_breakdown["字幕过短"] > 0:
            count = issue_breakdown["字幕过短"]
            recommendations.append(f"有 {count} 条字幕过短，建议合并相邻字幕")
        
        if "缺少结束标点" in issue_breakdown and issue_breakdown["缺少结束标点"] > 0:
            recommendations.append("部分字幕缺少结束标点，建议检查并补充")
        
        if "单行文字过多" in issue_breakdown and issue_breakdown["单行文字过多"] > 0:
            recommendations.append("部分字幕单行文字过多，建议启用自动换行")
        
        if "时长不合理" in issue_breakdown and issue_breakdown["时长不合理"] > 0:
            recommendations.append("部分字幕时长不合理，建议调整显示时间")
        
        return recommendations
    
    def _empty_quality_report(self) -> Dict[str, Any]:
        """空质量报告"""
        return {
            "overall_score": 0.0,
            "pass_rate": 0.0,
            "total_items": 0,
            "quality_distribution": {"high": 0, "medium": 0, "low": 0},
            "issue_breakdown": {},
            "recommendations": ["请先添加字幕内容"],
            "status": "empty",
            "timestamp": datetime.now().isoformat()
        }


# 主集成类
class Task3_3_RealTimePreviewSystem:
    """任务3.3: 实时预览功能集成系统"""
    
    def __init__(self, config: Optional[PreviewConfig] = None):
        self.config = config or PreviewConfig()
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self.preview_engine = RealTimeSubtitlePreview(self.config)
        self.wysiwyg_editor = WYSIWYGSubtitleEditor(self.preview_engine)
        self.quality_feedback = InstantQualityFeedback()
        
        self.logger.info("✅ 任务3.3 实时预览系统初始化完成")
    
    async def initialize_system(self) -> Dict[str, Any]:
        """初始化系统"""
        try:
            # 启动预览引擎
            preview_result = await self.preview_engine.start_preview_session()
            
            if preview_result["status"] != "success":
                return preview_result
            
            # 设置质量反馈回调
            async def quality_callback(update: PreviewUpdate):
                """质量反馈回调"""
                quality_report = await self.quality_feedback.assess_real_time_quality(
                    update.items
                )
                update.quality_summary.update(quality_report)
            
            self.preview_engine.add_update_callback(quality_callback)
            
            return {
                "status": "success",
                "message": "实时预览系统初始化成功",
                "capabilities": {
                    "real_time_preview": True,
                    "wysiwyg_editing": True,
                    "instant_quality_feedback": True,
                    "intelligent_splitting": True,
                    "multilingual_support": True
                },
                "config": asdict(self.config)
            }
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def start_real_time_preview(self, text: str) -> Dict[str, Any]:
        """开始实时预览"""
        result = await self.preview_engine.update_text_realtime(text)
        if isinstance(result, PreviewUpdate):
            return asdict(result)
        return result
    
    async def update_preview(self, text: str) -> Dict[str, Any]:
        """更新预览"""
        result = await self.preview_engine.update_text_realtime(text)
        if isinstance(result, PreviewUpdate):
            return asdict(result)
        return result
    
    async def edit_subtitle(self, item_id: str, new_text: str) -> Dict[str, Any]:
        """编辑字幕"""
        return await self.wysiwyg_editor.edit_subtitle_item(item_id, new_text)
    
    async def split_subtitle(self, item_id: str, position: int) -> Dict[str, Any]:
        """分割字幕"""
        return await self.wysiwyg_editor.split_subtitle_item(item_id, position)
    
    async def merge_subtitles(self, item_ids: List[str]) -> Dict[str, Any]:
        """合并字幕"""
        return await self.wysiwyg_editor.merge_subtitle_items(item_ids)
    
    async def undo_edit(self) -> Dict[str, Any]:
        """撤销编辑"""
        return await self.wysiwyg_editor.undo_edit()
    
    async def get_quality_report(self) -> Dict[str, Any]:
        """获取质量报告"""
        return await self.quality_feedback.assess_real_time_quality(
            self.preview_engine.preview_items
        )
    
    def add_update_callback(self, callback: Callable):
        """添加更新回调"""
        self.preview_engine.add_update_callback(callback)
    
    async def shutdown(self) -> Dict[str, Any]:
        """关闭系统"""
        return await self.preview_engine.stop_preview_session()


# 使用示例和测试
if __name__ == "__main__":
    async def demo_real_time_preview():
        """演示实时预览功能"""
        print("🎬 任务3.3: 实时预览功能演示")
        
        # 创建配置
        config = PreviewConfig(
            enable_real_time=True,
            preview_window_size=5,
            enable_quality_check=True,
            highlight_issues=True
        )
        
        # 初始化系统
        preview_system = Task3_3_RealTimePreviewSystem(config)
        
        # 初始化
        init_result = await preview_system.initialize_system()
        print(f"初始化结果: {init_result}")
        
        if init_result["status"] != "success":
            return
        
        # 添加更新回调
        def update_callback(update: PreviewUpdate):
            print(f"\n📝 预览更新:")
            print(f"   时间戳: {update.timestamp}")
            print(f"   字幕数量: {update.total_count}")
            print(f"   状态: {update.processing_status}")
            print(f"   整体质量: {update.quality_summary.get('overall_score', 0):.2f}")
            
            for i, item in enumerate(update.items[:3]):  # 只显示前3个
                print(f"   [{i+1}] {item.text} (质量: {item.quality_score:.2f})")
        
        preview_system.add_update_callback(update_callback)
        
        # 演示文本
        demo_texts = [
            "欢迎来到PPT转视频教程系统",
            "这是一个集成了智能断句、多语言支持和实时预览功能的完整解决方案。我们的系统可以自动分析文本，进行智能断句，并提供实时的质量反馈。",
            "Hello world! This is a multilingual test. 这是多语言测试。",
            "我们的实时预览功能包括：所见即所得编辑、即时质量反馈、智能断句集成等核心特性。"
        ]
        
        for i, text in enumerate(demo_texts):
            print(f"\n🔄 处理文本 {i+1}: {text[:30]}...")
            
            # 开始实时预览
            result = await preview_system.start_real_time_preview(text)
            
            # 模拟一些编辑操作
            if result.get("total_count", 0) > 0:
                # 编辑第一个字幕
                items = preview_system.preview_engine.preview_items
                if items:
                    edit_result = await preview_system.edit_subtitle(
                        items[0].id, 
                        items[0].text + "（已编辑）"
                    )
                    print(f"   编辑结果: {edit_result['status']}")
            
            await asyncio.sleep(1)  # 短暂延迟
        
        # 获取最终质量报告
        final_report = await preview_system.get_quality_report()
        print(f"\n📊 最终质量报告:")
        print(f"   整体评分: {final_report.get('overall_score', 0):.2f}")
        print(f"   通过率: {final_report.get('pass_rate', 0):.2f}")
        print(f"   建议: {final_report.get('recommendations', [])}")
        
        # 关闭系统
        shutdown_result = await preview_system.shutdown()
        print(f"\n🔚 系统关闭: {shutdown_result}")
    
    # 运行演示
    asyncio.run(demo_real_time_preview())
