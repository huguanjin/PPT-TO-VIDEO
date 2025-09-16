"""
任务管理器
提供异步任务管理功能
"""
import asyncio
import time
from typing import Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TaskManager:
    """任务管理器类"""
    
    def __init__(self, max_workers: int = 4):
        """
        初始化任务管理器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
    
    def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """
        提交任务
        
        Args:
            task_id: 任务ID
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            任务ID
        """
        try:
            future = self.executor.submit(func, *args, **kwargs)
            
            self.tasks[task_id] = {
                'future': future,
                'status': 'running',
                'start_time': time.time(),
                'result': None,
                'error': None,
                'progress': 0.0
            }
            
            logger.info(f"任务已提交: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        future = task['future']
        
        if future.done():
            if future.exception():
                task['status'] = 'failed'
                task['error'] = str(future.exception())
            else:
                task['status'] = 'completed'
                task['result'] = future.result()
                task['progress'] = 1.0
        
        return {
            'task_id': task_id,
            'status': task['status'],
            'progress': task['progress'],
            'start_time': task['start_time'],
            'result': task.get('result'),
            'error': task.get('error')
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        future = task['future']
        
        if future.cancel():
            task['status'] = 'cancelled'
            logger.info(f"任务已取消: {task_id}")
            return True
        else:
            logger.warning(f"无法取消任务: {task_id}")
            return False
    
    def cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_tasks = []
        
        for task_id, task in self.tasks.items():
            if task['status'] in ['completed', 'failed', 'cancelled']:
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.tasks[task_id]
        
        logger.info(f"清理了 {len(completed_tasks)} 个已完成的任务")
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        result = {}
        for task_id in self.tasks:
            result[task_id] = self.get_task_status(task_id)
        return result
    
    def shutdown(self):
        """关闭任务管理器"""
        self.executor.shutdown(wait=True)
        logger.info("任务管理器已关闭")

# 全局任务管理器实例
task_manager = TaskManager()

def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例"""
    return task_manager