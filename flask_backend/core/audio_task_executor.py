"""
音频任务执行器

负责并发执行音频生成任务，包括智能重试和错误处理
"""
import asyncio
from pathlib import Path
from typing import Set, Dict
from datetime import datetime

from .audio_task_models import AudioTask, TaskStatus
from .audio_task_queue import AudioTaskQueue
from app.utils.integrated_tts_manager import IntegratedTTSManager
from app.utils.logger import get_logger


class RetryStrategy:
    """重试策略
    
    根据不同的错误类型采用不同的重试配置
    """
    
    # 错误类型配置
    ERROR_CONFIGS = {
        "SSLError": {
            "max_retries": 10,
            "retry_delay": 15,
            "backoff_multiplier": 1.5
        },
        "TimeoutError": {
            "max_retries": 5,
            "retry_delay": 10,
            "backoff_multiplier": 2.0
        },
        "ConnectionError": {
            "max_retries": 8,
            "retry_delay": 20,
            "backoff_multiplier": 1.5
        },
        "Default": {
            "max_retries": 5,
            "retry_delay": 15,
            "backoff_multiplier": 2.0
        }
    }
    
    @staticmethod
    def get_retry_config(error_type: str) -> Dict:
        """获取重试配置
        
        Args:
            error_type: 错误类型
            
        Returns:
            重试配置字典
        """
        return RetryStrategy.ERROR_CONFIGS.get(
            error_type,
            RetryStrategy.ERROR_CONFIGS["Default"]
        )


class AudioTaskExecutor:
    """音频任务执行器
    
    核心功能：
    - 并发执行音频生成（多个worker）
    - 智能重试机制（根据错误类型）
    - 错误分类和处理
    - 进度跟踪
    """
    
    def __init__(self, 
                 task_queue: AudioTaskQueue,
                 tts_manager: IntegratedTTSManager,
                 max_concurrent: int = 3):
        """初始化任务执行器
        
        Args:
            task_queue: 任务队列
            tts_manager: TTS管理器
            max_concurrent: 最大并发任务数
        """
        self.task_queue = task_queue
        self.tts_manager = tts_manager
        self.max_concurrent = max_concurrent
        self.logger = get_logger(__name__)
        
        # 运行时状态
        self.running_tasks: Set[str] = set()
        self.is_running = False
        
        self.logger.info(f"🚀 任务执行器初始化 (最大并发: {max_concurrent})")
    
    async def start(self):
        """启动任务执行器
        
        创建多个worker并发执行任务，直到所有任务完成
        """
        self.is_running = True
        self.logger.info(f"▶️ 任务执行器启动 (并发数: {self.max_concurrent})")
        
        # 创建worker协程池
        workers = []
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i + 1))
            workers.append(worker)
        
        # 等待所有worker完成
        await asyncio.gather(*workers)
        
        # 输出最终统计
        stats = self.task_queue.get_statistics()
        self.logger.info(
            f"⏹️ 任务执行器停止 | "
            f"总计: {stats['total_tasks']}, "
            f"完成: {stats['completed']}, "
            f"失败: {stats['failed']}, "
            f"成功率: {stats['success_rate']*100:.1f}%"
        )
    
    async def _worker(self, worker_id: int):
        """工作协程
        
        每个worker持续从队列获取任务并执行，直到没有待执行任务
        
        Args:
            worker_id: Worker编号（用于日志）
        """
        self.logger.info(f"👷 Worker-{worker_id} 启动")
        
        while self.is_running:
            # 获取下一个待执行任务
            task = self.task_queue.get_next_task()
            
            if task is None:
                # 没有待执行任务，检查是否所有任务都已完成
                stats = self.task_queue.get_statistics()
                if stats['pending'] == 0 and stats['running'] == 0 and stats['retrying'] == 0:
                    self.logger.info(f"✅ Worker-{worker_id}: 所有任务已完成")
                    break
                
                # 等待一会儿再检查（可能有任务正在重试）
                await asyncio.sleep(1)
                continue
            
            # 执行任务
            self.logger.info(f"🔨 Worker-{worker_id} 开始执行: {task.task_id} (页{task.page_number})")
            await self._execute_task(task)
            
            # 短暂延迟，避免过快请求
            await asyncio.sleep(0.5)
        
        self.logger.info(f"👋 Worker-{worker_id} 停止")
    
    async def _execute_task(self, task: AudioTask):
        """执行单个任务
        
        Args:
            task: 要执行的任务
        """
        # 标记为运行中
        self.running_tasks.add(task.task_id)
        self.task_queue.mark_task_running(task.task_id)
        
        try:
            # 生成音频文件路径
            audio_path = self.task_queue.project_dir / "output" / "audios" / task.audio_filename
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 记录日志
            self.logger.info(
                f"🎤 {task.task_id}: 开始合成语音 "
                f"(重试{task.retry_count}次) "
                f"文本: {task.script_content[:50]}..."
            )
            
            # 调用TTS生成音频
            result = await self.tts_manager.synthesize_speech(
                text=task.script_content,
                output_path=str(audio_path)
            )
            
            if result.get("success"):
                # 成功
                self.logger.info(
                    f"✅ {task.task_id} 完成: "
                    f"{result.get('engine', 'unknown')}, "
                    f"{result.get('duration', 0):.2f}s, "
                    f"{result.get('file_size', 0)/1024:.1f}KB"
                )
                
                # 标记任务完成
                self.task_queue.mark_task_completed(
                    task.task_id,
                    audio_path=str(audio_path),
                    duration_seconds=result.get('duration', 0),
                    file_size_bytes=result.get('file_size', 0),
                    engine_used=result.get('engine', 'unknown')
                )
            else:
                # 失败，进入重试逻辑
                error = result.get('error', '未知错误')
                await self._handle_task_failure(task, error)
        
        except Exception as e:
            # 捕获异常
            self.logger.error(f"❌ {task.task_id} 执行异常: {e}", exc_info=True)
            await self._handle_task_failure(task, str(e))
        
        finally:
            # 从运行集合中移除
            self.running_tasks.discard(task.task_id)
    
    async def _handle_task_failure(self, task: AudioTask, error: str):
        """处理任务失败
        
        根据错误类型和重试次数决定是否重试
        
        Args:
            task: 失败的任务
            error: 错误信息
        """
        # 分类错误
        error_type = self._classify_error(error)
        retry_config = RetryStrategy.get_retry_config(error_type)
        
        # 增加重试计数
        new_retry_count = self.task_queue.increment_retry_count(task.task_id)
        
        # 判断是否可以重试
        max_retries = min(task.max_retries, retry_config['max_retries'])
        
        if new_retry_count < max_retries:
            # 可以重试
            delay = self._calculate_retry_delay(
                new_retry_count,
                retry_config['retry_delay'],
                retry_config['backoff_multiplier']
            )
            
            self.logger.warning(
                f"⚠️ {task.task_id} 失败 [{error_type}] "
                f"(第{new_retry_count}/{max_retries}次重试), "
                f"{delay}秒后重试: {error[:100]}"
            )
            
            # 更新为重试中状态
            self.task_queue.update_task_status(
                task.task_id,
                TaskStatus.RETRYING,
                retry_count=new_retry_count,
                last_error=error
            )
            
            # 延迟
            await asyncio.sleep(delay)
            
            # 重新加入队列
            self.task_queue.update_task_status(
                task.task_id,
                TaskStatus.PENDING
            )
        else:
            # 达到最大重试次数，标记为最终失败
            self.logger.error(
                f"💀 {task.task_id} 最终失败 "
                f"(已重试{new_retry_count}次): {error}"
            )
            
            self.task_queue.mark_task_failed(task.task_id, error)
    
    def _classify_error(self, error: str) -> str:
        """分类错误类型
        
        Args:
            error: 错误信息
            
        Returns:
            错误类型字符串
        """
        error_lower = error.lower()
        
        if "ssl" in error_lower:
            return "SSLError"
        elif "timeout" in error_lower or "timed out" in error_lower:
            return "TimeoutError"
        elif "connection" in error_lower or "connect" in error_lower:
            return "ConnectionError"
        elif "auth" in error_lower or "unauthorized" in error_lower:
            return "AuthError"
        else:
            return "Default"
    
    def _calculate_retry_delay(self, 
                               retry_count: int, 
                               base_delay: int,
                               multiplier: float) -> int:
        """计算重试延迟（指数退避）
        
        Args:
            retry_count: 当前重试次数
            base_delay: 基础延迟（秒）
            multiplier: 退避倍数
            
        Returns:
            延迟时间（秒）
        """
        max_delay = 300  # 最大延迟5分钟
        delay = base_delay * (multiplier ** (retry_count - 1))
        return min(int(delay), max_delay)
    
    def stop(self):
        """停止执行器（优雅关闭）"""
        self.logger.info("⏸️ 正在停止任务执行器...")
        self.is_running = False
    
    def get_running_tasks(self) -> Set[str]:
        """获取当前正在运行的任务ID集合"""
        return self.running_tasks.copy()
