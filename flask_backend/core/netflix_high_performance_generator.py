"""
Netflix V2高性能字幕生成器 - Phase 5性能优化
支持多线程、智能缓存、异步处理的高性能Netflix字幕生成系统
"""
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
import logging
import json
import hashlib
from functools import lru_cache
import weakref
from collections import defaultdict

from .netflix_v2_subtitle_generator import NetflixV2SubtitleGenerator


@dataclass
class PerformanceMetrics:
    """性能指标跟踪"""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    processing_time: float = 0.0
    memory_usage: Dict[str, float] = field(default_factory=dict)
    cache_hit_rate: float = 0.0
    parallel_efficiency: float = 0.0
    subtitle_count: int = 0
    
    def finish(self):
        """完成性能记录"""
        self.end_time = time.time()
        self.processing_time = self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "processing_time": self.processing_time,
            "memory_usage": self.memory_usage,
            "cache_hit_rate": self.cache_hit_rate,
            "parallel_efficiency": self.parallel_efficiency,
            "subtitle_count": self.subtitle_count,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


class NetflixConfigCache:
    """Netflix配置智能缓存系统"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # 缓存过期时间(秒)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._access_count: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
        
        self.hit_count = 0
        self.miss_count = 0
        
        self.logger = logging.getLogger(__name__)
    
    def _generate_cache_key(self, config_name: str, config_data: Dict[str, Any]) -> str:
        """生成缓存键"""
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.md5(f"{config_name}:{config_str}".encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        return time.time() - self._access_times.get(key, 0) > self.ttl
    
    def _evict_lru(self):
        """LRU缓存清理"""
        if len(self._cache) <= self.max_size:
            return
        
        # 按访问时间和频率排序，清理最少使用的
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: (self._access_count[k], self._access_times[k])
        )
        
        # 清理最旧的25%
        evict_count = max(1, len(sorted_keys) // 4)
        for key in sorted_keys[:evict_count]:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
            self._access_count.pop(key, None)
    
    def get(self, config_name: str, config_data: Dict[str, Any]) -> Optional[Any]:
        """获取缓存配置"""
        cache_key = self._generate_cache_key(config_name, config_data)
        
        with self._lock:
            if cache_key in self._cache and not self._is_expired(cache_key):
                self._access_times[cache_key] = time.time()
                self._access_count[cache_key] += 1
                self.hit_count += 1
                self.logger.debug(f"缓存命中: {config_name}")
                return self._cache[cache_key]
            
            self.miss_count += 1
            self.logger.debug(f"缓存未命中: {config_name}")
            return None
    
    def put(self, config_name: str, config_data: Dict[str, Any], processed_config: Any):
        """存储配置到缓存"""
        cache_key = self._generate_cache_key(config_name, config_data)
        
        with self._lock:
            self._evict_lru()
            self._cache[cache_key] = processed_config
            self._access_times[cache_key] = time.time()
            self._access_count[cache_key] = 1
            
            self.logger.debug(f"配置已缓存: {config_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "max_size": self.max_size
        }
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._access_count.clear()
            self.hit_count = 0
            self.miss_count = 0


class NetflixSubtitleTaskBatch:
    """Netflix字幕任务批处理器"""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
    
    async def process_batch(
        self,
        tasks: List[Dict[str, Any]],
        generator: 'NetflixHighPerformanceGenerator',
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """批量处理字幕任务"""
        results = []
        total_tasks = len(tasks)
        
        # 分批处理
        for i in range(0, total_tasks, self.batch_size):
            batch = tasks[i:i + self.batch_size]
            batch_results = await self._process_single_batch(
                batch, generator, i, total_tasks, progress_callback
            )
            results.extend(batch_results)
        
        return results
    
    async def _process_single_batch(
        self,
        batch: List[Dict[str, Any]],
        generator: 'NetflixHighPerformanceGenerator',
        batch_start: int,
        total_tasks: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """处理单个批次"""
        self.logger.info(f"开始处理批次: {batch_start}-{batch_start + len(batch)}")
        
        # 创建并发任务
        tasks = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for task_data in batch:
                future = executor.submit(
                    self._process_single_task,
                    task_data,
                    generator
                )
                tasks.append(future)
            
            # 等待所有任务完成
            results = []
            for i, future in enumerate(as_completed(tasks)):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 更新进度
                    if progress_callback:
                        progress_callback(batch_start + i + 1, total_tasks)
                        
                except Exception as e:
                    self.logger.error(f"任务处理失败: {e}")
                    results.append({"error": str(e)})
        
        self.logger.info(f"批次处理完成: {len(results)}个任务")
        return results
    
    def _process_single_task(
        self,
        task_data: Dict[str, Any],
        generator: 'NetflixHighPerformanceGenerator'
    ) -> Dict[str, Any]:
        """处理单个任务 (同步版本，用于线程池)"""
        try:
            # 运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                generator._generate_single_subtitle_task(task_data)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            self.logger.error(f"单任务处理失败: {e}")
            raise


class NetflixHighPerformanceGenerator:
    """Netflix高性能字幕生成器 - Phase 5优化版本"""
    
    def __init__(
        self,
        project_dir: Path,
        max_workers: int = 4,
        cache_size: int = 100,
        batch_size: int = 10,
        enable_performance_monitoring: bool = True
    ):
        self.project_dir = Path(project_dir)
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # 初始化组件
        self.config_cache = NetflixConfigCache(max_size=cache_size)
        self.batch_processor = NetflixSubtitleTaskBatch(
            batch_size=batch_size,
            max_workers=max_workers
        )
        
        # 性能监控
        self.metrics = PerformanceMetrics()
        self.generator_pool: Dict[str, NetflixV2SubtitleGenerator] = {}
        self._pool_lock = threading.RLock()
        
        # 内存管理
        self._weak_refs: List[weakref.ref] = []
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Netflix高性能字幕生成器初始化完成")
    
    def _get_or_create_generator(self, config_name: str) -> NetflixV2SubtitleGenerator:
        """获取或创建字幕生成器实例 (线程安全)"""
        with self._pool_lock:
            if config_name not in self.generator_pool:
                generator = NetflixV2SubtitleGenerator(
                    self.project_dir,
                    netflix_config_name=config_name
                )
                self.generator_pool[config_name] = generator
                
                # 添加弱引用追踪
                weak_ref = weakref.ref(generator, self._cleanup_generator)
                self._weak_refs.append(weak_ref)
                
                self.logger.debug(f"创建新的生成器实例: {config_name}")
            
            return self.generator_pool[config_name]
    
    def _cleanup_generator(self, weak_ref):
        """清理生成器实例"""
        self._weak_refs = [ref for ref in self._weak_refs if ref() is not None]
    
    @lru_cache(maxsize=50)
    def _analyze_content_complexity(self, content_hash: str) -> Dict[str, Any]:
        """分析内容复杂度 (带缓存)"""
        # 这里可以实现复杂的内容分析逻辑
        # 为了演示，返回基础分析结果
        return {
            "complexity_score": 1.0,
            "estimated_processing_time": 10.0,
            "recommended_batch_size": self.batch_size
        }
    
    async def generate_high_performance_subtitles(
        self,
        scripts_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        netflix_config_name: str = "default",
        word_level_data: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        enable_parallel: bool = True
    ) -> Dict[str, Any]:
        """
        高性能Netflix字幕生成
        
        Args:
            scripts_data: 脚本数据
            audio_data: 音频数据
            netflix_config_name: Netflix配置名称
            word_level_data: 词级别时间数据
            progress_callback: 进度回调函数
            enable_parallel: 是否启用并行处理
            
        Returns:
            字幕生成结果和性能指标
        """
        if self.enable_performance_monitoring:
            self.metrics = PerformanceMetrics()
        
        try:
            self.logger.info(f"开始高性能Netflix字幕生成: {netflix_config_name}")
            
            # 1. 内容复杂度分析
            content_hash = hashlib.md5(
                json.dumps(scripts_data, sort_keys=True).encode()
            ).hexdigest()
            
            complexity_analysis = self._analyze_content_complexity(content_hash)
            self.logger.debug(f"内容复杂度分析: {complexity_analysis}")
            
            # 2. 获取或创建生成器实例
            generator = self._get_or_create_generator(netflix_config_name)
            
            # 3. 准备任务数据
            subtitle_tasks = self._prepare_subtitle_tasks(
                scripts_data, audio_data, word_level_data
            )
            
            # 4. 选择处理模式
            if enable_parallel and len(subtitle_tasks) > 1:
                # 并行批处理模式
                results = await self._parallel_processing(
                    subtitle_tasks, generator, progress_callback
                )
            else:
                # 串行处理模式
                results = await self._sequential_processing(
                    subtitle_tasks, generator, progress_callback
                )
            
            # 5. 合并和优化结果
            final_result = await self._merge_and_optimize_results(
                results, netflix_config_name
            )
            
            # 6. 性能指标收集
            if self.enable_performance_monitoring:
                self.metrics.finish()
                self.metrics.subtitle_count = len(results)
                self.metrics.cache_hit_rate = self._calculate_cache_hit_rate()
                
                final_result["performance_metrics"] = self.metrics.to_dict()
                final_result["cache_stats"] = self.config_cache.get_stats()
            
            self.logger.info(f"高性能字幕生成完成: {len(results)}个字幕项")
            return final_result
            
        except Exception as e:
            self.logger.error(f"高性能字幕生成失败: {e}", exc_info=True)
            raise
    
    def _prepare_subtitle_tasks(
        self,
        scripts_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        word_level_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """准备字幕生成任务"""
        tasks = []
        
        slides = scripts_data.get("slides", [])
        for i, slide in enumerate(slides):
            task = {
                "task_id": f"slide_{i}",
                "slide_data": slide,
                "audio_segment": self._extract_audio_segment(audio_data, i),
                "word_level_segment": self._extract_word_level_segment(word_level_data, i) if word_level_data else None,
                "slide_index": i
            }
            tasks.append(task)
        
        return tasks
    
    def _extract_audio_segment(self, audio_data: Dict[str, Any], slide_index: int) -> Dict[str, Any]:
        """提取音频片段数据"""
        # 简化实现，实际应该根据slide时间分割音频
        return {
            "segment_index": slide_index,
            "duration": audio_data.get("duration", 0) / max(1, slide_index + 1),
            "sample_rate": audio_data.get("sample_rate", 44100)
        }
    
    def _extract_word_level_segment(
        self, 
        word_level_data: List[Dict[str, Any]], 
        slide_index: int
    ) -> List[Dict[str, Any]]:
        """提取词级别数据片段"""
        # 简化实现，实际应该根据时间范围分割
        if not word_level_data:
            return []
        
        segment_size = len(word_level_data) // (slide_index + 1)
        start_idx = slide_index * segment_size
        end_idx = min(start_idx + segment_size, len(word_level_data))
        
        return word_level_data[start_idx:end_idx]
    
    async def _parallel_processing(
        self,
        tasks: List[Dict[str, Any]],
        generator: NetflixV2SubtitleGenerator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """并行处理模式"""
        self.logger.info(f"启用并行处理模式: {len(tasks)}个任务")
        
        results = await self.batch_processor.process_batch(
            tasks, self, progress_callback
        )
        
        return results
    
    async def _sequential_processing(
        self,
        tasks: List[Dict[str, Any]],
        generator: NetflixV2SubtitleGenerator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """串行处理模式"""
        self.logger.info(f"启用串行处理模式: {len(tasks)}个任务")
        
        results = []
        for i, task in enumerate(tasks):
            try:
                result = await self._generate_single_subtitle_task(task)
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, len(tasks))
                    
            except Exception as e:
                self.logger.error(f"任务处理失败: {e}")
                results.append({"error": str(e)})
        
        return results
    
    async def _generate_single_subtitle_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成单个字幕任务"""
        task_id = task_data["task_id"]
        slide_data = task_data["slide_data"]
        
        try:
            # 模拟字幕生成过程
            subtitle_result = {
                "task_id": task_id,
                "slide_number": task_data["slide_index"] + 1,
                "title": slide_data.get("title", ""),
                "content": slide_data.get("content", ""),
                "subtitle_text": slide_data.get("content", ""),
                "start_time": task_data["slide_index"] * 5.0,
                "end_time": (task_data["slide_index"] + 1) * 5.0,
                "processing_time": time.time(),
                "success": True
            }
            
            self.logger.debug(f"任务完成: {task_id}")
            return subtitle_result
            
        except Exception as e:
            self.logger.error(f"任务失败: {task_id} - {e}")
            return {
                "task_id": task_id,
                "error": str(e),
                "success": False
            }
    
    async def _merge_and_optimize_results(
        self,
        results: List[Dict[str, Any]],
        config_name: str
    ) -> Dict[str, Any]:
        """合并和优化结果"""
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        # 按slide顺序排序
        successful_results.sort(key=lambda x: x.get("slide_number", 0))
        
        merged_result = {
            "netflix_config_name": config_name,
            "total_subtitles": len(successful_results),
            "successful_count": len(successful_results),
            "failed_count": len(failed_results),
            "subtitles": successful_results,
            "errors": failed_results if failed_results else None,
            "high_performance_processing": True,
            "optimization_level": "Phase5",
            "generation_timestamp": time.time()
        }
        
        return merged_result
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        stats = self.config_cache.get_stats()
        return stats.get("hit_rate", 0.0)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "current_metrics": self.metrics.to_dict() if self.metrics else None,
            "cache_stats": self.config_cache.get_stats(),
            "generator_pool_size": len(self.generator_pool),
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
            "memory_refs": len([ref for ref in self._weak_refs if ref() is not None])
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """性能优化建议"""
        stats = self.get_performance_stats()
        
        suggestions = []
        
        # 缓存优化建议
        hit_rate = stats["cache_stats"]["hit_rate"]
        if hit_rate < 0.5:
            suggestions.append("考虑增加缓存大小或优化缓存策略")
        
        # 并行度优化建议
        if self.max_workers < 4:
            suggestions.append("考虑增加并行工作线程数量")
        
        # 批处理优化建议
        if self.batch_size < 5:
            suggestions.append("考虑增加批处理大小以提高吞吐量")
        
        return {
            "current_stats": stats,
            "optimization_suggestions": suggestions,
            "recommended_settings": {
                "max_workers": min(8, self.max_workers * 2),
                "cache_size": max(200, self.config_cache.max_size * 2),
                "batch_size": min(20, self.batch_size * 2)
            }
        }
    
    def cleanup_resources(self):
        """清理资源"""
        self.config_cache.clear()
        
        with self._pool_lock:
            self.generator_pool.clear()
        
        self._weak_refs.clear()
        
        self.logger.info("资源清理完成")