"""
音频任务队列管理器

负责任务的创建、状态管理和统计查询
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .audio_task_models import AudioTask, TaskStatus
from .audio_task_storage import SQLiteTaskStorage
from app.utils.logger import get_logger


class AudioTaskQueue:
    """音频任务队列管理器
    
    提供高层次的任务管理接口，包括：
    - 从讲话稿创建任务
    - 任务状态更新
    - 失败任务查询
    - 统计信息获取
    """
    
    def __init__(self, session_id: str, project_dir: Path):
        """初始化任务队列
        
        Args:
            session_id: 会话ID（唯一标识一次音频生成流程）
            project_dir: 项目目录
        """
        self.session_id = session_id
        self.project_dir = Path(project_dir)
        self.logger = get_logger(__name__, project_dir / "logs")
        
        # 初始化存储（数据库路径）
        db_path = project_dir / "output" / "task_queue.db"
        self.storage = SQLiteTaskStorage(db_path)
        
        self.logger.info(f"🎯 任务队列初始化: session_id={session_id}")
    
    def create_tasks_from_scripts(self, scripts_data: Dict) -> int:
        """从讲话稿数据创建任务
        
        Args:
            scripts_data: 讲话稿数据，格式: {"scripts": [{"slide_number": 1, "text": "..."}]}
            
        Returns:
            创建的任务数量
        """
        scripts = scripts_data.get("scripts", [])
        tasks_created = 0
        
        self.logger.info(f"开始创建任务，共 {len(scripts)} 个讲话稿")
        
        for i, script in enumerate(scripts):
            # 提取页码（支持多种字段名）
            page_number = script.get("slide_number", 
                                    script.get("slide_id", 
                                              script.get("page_number", i + 1)))
            
            # 提取文本内容（支持多种字段名）
            script_content = script.get("text", 
                                       script.get("script_content", 
                                                 script.get("content", "")))
            
            if not script_content or not script_content.strip():
                self.logger.warning(f"⚠️ 第 {page_number} 页讲话稿为空，跳过")
                continue
            
            # 创建任务
            task = AudioTask(
                task_id=f"audio_{page_number:03d}",
                session_id=self.session_id,
                page_number=page_number,
                segment_index=None,
                script_content=script_content.strip(),
                audio_filename=f"audio_{page_number:03d}.wav",
                status=TaskStatus.PENDING,
                priority=5,  # 默认优先级
                max_retries=10,
                metadata={
                    "original_index": i,
                    "script_length": len(script_content)
                }
            )
            
            # 保存到数据库
            if self.storage.save_task(task):
                tasks_created += 1
                self.logger.debug(f"✅ 创建任务: {task.task_id} (页{page_number})")
            else:
                self.logger.error(f"❌ 创建任务失败: 页{page_number}")
        
        self.logger.info(f"✅ 创建了 {tasks_created} 个音频任务")
        return tasks_created
    
    def get_next_task(self) -> Optional[AudioTask]:
        """获取下一个待执行的任务
        
        按优先级（高到低）和页码（小到大）排序
        
        Returns:
            下一个任务，如果没有则返回None
        """
        return self.storage.get_next_pending_task(self.session_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            **kwargs: 其他要更新的字段
        """
        task = self.storage.get_task(task_id)
        if not task:
            self.logger.error(f"❌ 任务不存在: {task_id}")
            return
        
        # 更新状态
        task.status = status
        task.updated_at = datetime.now()
        
        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
            else:
                self.logger.warning(f"⚠️ 任务没有字段: {key}")
        
        # 保存到数据库
        self.storage.save_task(task)
        self.logger.debug(f"🔄 任务 {task_id} 状态更新为 {status.value}")
    
    def mark_task_running(self, task_id: str):
        """标记任务为运行中"""
        self.update_task_status(
            task_id,
            TaskStatus.RUNNING,
            started_at=datetime.now()
        )
    
    def mark_task_completed(self, task_id: str, **result_data):
        """标记任务完成
        
        Args:
            task_id: 任务ID
            **result_data: 结果数据（audio_path, duration_seconds, file_size_bytes, engine_used等）
        """
        self.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            completed_at=datetime.now(),
            **result_data
        )
        self.logger.info(f"✅ 任务完成: {task_id}")
    
    def mark_task_failed(self, task_id: str, error: str):
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
        """
        task = self.storage.get_task(task_id)
        if not task:
            self.logger.error(f"❌ 任务不存在: {task_id}")
            return
        
        # 更新失败状态
        task.status = TaskStatus.FAILED
        task.last_error = error
        task.updated_at = datetime.now()
        
        # 记录错误历史
        task.error_history.append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "retry_count": task.retry_count
        })
        
        self.storage.save_task(task)
        self.logger.error(f"❌ 任务失败: {task_id} - {error}")
    
    def increment_retry_count(self, task_id: str) -> int:
        """增加任务重试次数
        
        Args:
            task_id: 任务ID
            
        Returns:
            新的重试次数
        """
        task = self.storage.get_task(task_id)
        if not task:
            return 0
        
        task.retry_count += 1
        self.storage.save_task(task)
        return task.retry_count
    
    def get_failed_tasks(self) -> List[AudioTask]:
        """获取所有失败的任务
        
        Returns:
            失败任务列表
        """
        return self.storage.get_tasks_by_status(self.session_id, TaskStatus.FAILED)
    
    def get_completed_tasks(self) -> List[AudioTask]:
        """获取所有完成的任务"""
        return self.storage.get_tasks_by_status(self.session_id, TaskStatus.COMPLETED)
    
    def get_pending_tasks(self) -> List[AudioTask]:
        """获取所有待执行的任务"""
        return self.storage.get_tasks_by_status(self.session_id, TaskStatus.PENDING)
    
    def get_all_tasks(self) -> List[AudioTask]:
        """获取所有任务"""
        return self.storage.get_all_tasks(self.session_id)
    
    def get_statistics(self) -> Dict:
        """获取队列统计信息
        
        Returns:
            统计信息字典，包括总数、各状态数量、成功率等
        """
        all_tasks = self.storage.get_all_tasks(self.session_id)
        
        # 基本统计
        total = len(all_tasks)
        completed = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in all_tasks if t.status == TaskStatus.FAILED])
        pending = len([t for t in all_tasks if t.status == TaskStatus.PENDING])
        running = len([t for t in all_tasks if t.status == TaskStatus.RUNNING])
        retrying = len([t for t in all_tasks if t.status == TaskStatus.RETRYING])
        
        # 计算成功率
        success_rate = completed / total if total > 0 else 0.0
        
        # 平均重试次数
        avg_retries = sum(t.retry_count for t in all_tasks) / total if total > 0 else 0.0
        
        # 总时长
        total_duration = sum(t.duration_seconds for t in all_tasks if t.duration_seconds)
        
        return {
            "session_id": self.session_id,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "retrying": retrying,
            "success_rate": success_rate,
            "average_retries": avg_retries,
            "total_duration_seconds": total_duration,
            "completion_percentage": (completed / total * 100) if total > 0 else 0.0
        }
    
    def reset_failed_tasks(self):
        """重置所有失败的任务为待执行状态
        
        用于手动重试所有失败的任务
        """
        failed_tasks = self.get_failed_tasks()
        reset_count = 0
        
        for task in failed_tasks:
            task.status = TaskStatus.PENDING
            task.retry_count = 0
            task.last_error = None
            task.updated_at = datetime.now()
            self.storage.save_task(task)
            reset_count += 1
        
        self.logger.info(f"🔄 重置了 {reset_count} 个失败任务")
        return reset_count
    
    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_statistics()
        return (f"AudioTaskQueue(session={self.session_id}, "
                f"total={stats['total_tasks']}, "
                f"completed={stats['completed']}, "
                f"failed={stats['failed']})")
