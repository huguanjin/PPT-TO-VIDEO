# 音频任务队列系统 - 快速实施指南

## 🎯 实施目标

将当前的静默音频fallback方案替换为可靠的任务队列管理系统，确保每个音频都能成功生成。

---

## 📋 实施步骤

### 第1步: 创建数据模型 (Day 1, 上午)

#### 1.1 创建文件: `flask_backend/core/audio_task_models.py`

```python
"""
音频任务数据模型
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    RETRYING = "retrying"         # 重试中
    CANCELLED = "cancelled"       # 已取消

@dataclass
class AudioTask:
    """音频生成任务"""
    # 基本信息
    task_id: str
    session_id: str
    page_number: int
    segment_index: Optional[int] = None
    
    # 任务内容
    script_content: str = ""
    audio_filename: str = ""
    
    # 任务状态
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 重试信息
    retry_count: int = 0
    max_retries: int = 10
    last_error: Optional[str] = None
    error_history: List[Dict] = field(default_factory=list)
    
    # 执行结果
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    engine_used: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AudioTask':
        """从字典创建"""
        data = data.copy()
        data['status'] = TaskStatus(data['status'])
        
        for time_field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
            if data.get(time_field):
                data[time_field] = datetime.fromisoformat(data[time_field])
        
        return cls(**data)
```

#### 1.2 创建文件: `flask_backend/core/audio_task_storage.py`

```python
"""
音频任务存储适配器
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .audio_task_models import AudioTask, TaskStatus
from app.utils.logger import get_logger

class TaskStorage:
    """任务存储基类"""
    
    def save_task(self, task: AudioTask) -> bool:
        raise NotImplementedError
    
    def get_task(self, task_id: str) -> Optional[AudioTask]:
        raise NotImplementedError
    
    def get_all_tasks(self, session_id: str) -> List[AudioTask]:
        raise NotImplementedError
    
    def get_tasks_by_status(self, session_id: str, status: TaskStatus) -> List[AudioTask]:
        raise NotImplementedError
    
    def get_next_pending_task(self, session_id: str) -> Optional[AudioTask]:
        raise NotImplementedError


class SQLiteTaskStorage(TaskStorage):
    """SQLite任务存储"""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_tasks (
                task_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                segment_index INTEGER,
                script_content TEXT NOT NULL,
                audio_filename TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 10,
                last_error TEXT,
                error_history TEXT,
                audio_path TEXT,
                duration_seconds REAL,
                file_size_bytes INTEGER,
                engine_used TEXT,
                metadata TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON audio_tasks(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON audio_tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_status ON audio_tasks(priority DESC, status)')
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"SQLite数据库初始化完成: {self.db_path}")
    
    def save_task(self, task: AudioTask) -> bool:
        """保存任务"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        task_dict = task.to_dict()
        
        # 序列化复杂字段
        task_dict['error_history'] = json.dumps(task_dict['error_history'])
        task_dict['metadata'] = json.dumps(task_dict['metadata'])
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO audio_tasks VALUES (
                    :task_id, :session_id, :page_number, :segment_index,
                    :script_content, :audio_filename, :status, :priority,
                    :created_at, :updated_at, :started_at, :completed_at,
                    :retry_count, :max_retries, :last_error, :error_history,
                    :audio_path, :duration_seconds, :file_size_bytes,
                    :engine_used, :metadata
                )
            ''', task_dict)
            
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"保存任务失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_task(self, task_id: str) -> Optional[AudioTask]:
        """获取任务"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM audio_tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            task_dict = dict(row)
            task_dict['error_history'] = json.loads(task_dict['error_history'])
            task_dict['metadata'] = json.loads(task_dict['metadata'])
            return AudioTask.from_dict(task_dict)
        
        return None
    
    def get_all_tasks(self, session_id: str) -> List[AudioTask]:
        """获取会话的所有任务"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM audio_tasks WHERE session_id = ? ORDER BY page_number', 
                      (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            task_dict = dict(row)
            task_dict['error_history'] = json.loads(task_dict['error_history'])
            task_dict['metadata'] = json.loads(task_dict['metadata'])
            tasks.append(AudioTask.from_dict(task_dict))
        
        return tasks
    
    def get_tasks_by_status(self, session_id: str, status: TaskStatus) -> List[AudioTask]:
        """获取指定状态的任务"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audio_tasks 
            WHERE session_id = ? AND status = ?
            ORDER BY page_number
        ''', (session_id, status.value))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            task_dict = dict(row)
            task_dict['error_history'] = json.loads(task_dict['error_history'])
            task_dict['metadata'] = json.loads(task_dict['metadata'])
            tasks.append(AudioTask.from_dict(task_dict))
        
        return tasks
    
    def get_next_pending_task(self, session_id: str) -> Optional[AudioTask]:
        """获取下一个待执行任务（按优先级和创建时间）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audio_tasks 
            WHERE session_id = ? AND status = ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        ''', (session_id, TaskStatus.PENDING.value))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            task_dict = dict(row)
            task_dict['error_history'] = json.loads(task_dict['error_history'])
            task_dict['metadata'] = json.loads(task_dict['metadata'])
            return AudioTask.from_dict(task_dict)
        
        return None
```

### 第2步: 实现任务队列管理器 (Day 1, 下午)

#### 创建文件: `flask_backend/core/audio_task_queue.py`

```python
"""
音频任务队列管理器
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .audio_task_models import AudioTask, TaskStatus
from .audio_task_storage import SQLiteTaskStorage
from app.utils.logger import get_logger

class AudioTaskQueue:
    """音频任务队列管理器"""
    
    def __init__(self, session_id: str, project_dir: Path):
        """
        初始化任务队列
        
        Args:
            session_id: 会话ID
            project_dir: 项目目录
        """
        self.session_id = session_id
        self.project_dir = Path(project_dir)
        self.logger = get_logger(__name__, project_dir / "logs")
        
        # 初始化存储
        db_path = project_dir / "output" / "task_queue.db"
        self.storage = SQLiteTaskStorage(db_path)
        
        self.logger.info(f"任务队列初始化: session_id={session_id}")
    
    def create_tasks_from_scripts(self, scripts_data: Dict) -> int:
        """
        从讲话稿数据创建任务
        
        Args:
            scripts_data: 讲话稿数据
            
        Returns:
            创建的任务数量
        """
        scripts = scripts_data.get("scripts", [])
        tasks_created = 0
        
        for i, script in enumerate(scripts):
            # 获取页码
            page_number = script.get("slide_number", script.get("slide_id", i + 1))
            
            # 获取文本内容
            script_content = script.get("text", script.get("script_content", script.get("content", "")))
            
            # 创建任务
            task = AudioTask(
                task_id=f"audio_{page_number:03d}",
                session_id=self.session_id,
                page_number=page_number,
                segment_index=None,
                script_content=script_content,
                audio_filename=f"audio_{page_number:03d}.wav",
                status=TaskStatus.PENDING,
                priority=5,
                max_retries=10
            )
            
            self.storage.save_task(task)
            tasks_created += 1
        
        self.logger.info(f"创建了 {tasks_created} 个音频任务")
        return tasks_created
    
    def get_next_task(self) -> Optional[AudioTask]:
        """获取下一个待执行的任务"""
        return self.storage.get_next_pending_task(self.session_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        """更新任务状态"""
        task = self.storage.get_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
            
            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            self.storage.save_task(task)
            self.logger.debug(f"任务 {task_id} 状态更新为 {status.value}")
    
    def mark_task_completed(self, task_id: str, **kwargs):
        """标记任务完成"""
        self.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            completed_at=datetime.now(),
            **kwargs
        )
    
    def mark_task_failed(self, task_id: str, error: str):
        """标记任务失败"""
        task = self.storage.get_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.last_error = error
            task.error_history.append({
                "timestamp": datetime.now().isoformat(),
                "error": error,
                "retry_count": task.retry_count
            })
            task.updated_at = datetime.now()
            self.storage.save_task(task)
            
            self.logger.error(f"任务 {task_id} 标记为失败: {error}")
    
    def get_failed_tasks(self) -> List[AudioTask]:
        """获取所有失败的任务"""
        return self.storage.get_tasks_by_status(self.session_id, TaskStatus.FAILED)
    
    def get_statistics(self) -> Dict:
        """获取队列统计信息"""
        all_tasks = self.storage.get_all_tasks(self.session_id)
        
        total = len(all_tasks)
        completed = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in all_tasks if t.status == TaskStatus.FAILED])
        pending = len([t for t in all_tasks if t.status == TaskStatus.PENDING])
        running = len([t for t in all_tasks if t.status == TaskStatus.RUNNING])
        
        total_duration = sum(t.duration_seconds for t in all_tasks if t.duration_seconds)
        
        return {
            "session_id": self.session_id,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "success_rate": completed / total if total > 0 else 0.0,
            "average_retries": sum(t.retry_count for t in all_tasks) / total if total > 0 else 0.0,
            "total_duration": total_duration
        }
```

### 第3步: 实现任务执行器 (Day 2)

#### 创建文件: `flask_backend/core/audio_task_executor.py`

```python
"""
音频任务执行器
"""
import asyncio
from pathlib import Path
from typing import Set
from datetime import datetime

from .audio_task_models import AudioTask, TaskStatus
from .audio_task_queue import AudioTaskQueue
from app.utils.integrated_tts_manager import IntegratedTTSManager
from app.utils.logger import get_logger

class RetryStrategy:
    """重试策略"""
    
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
        return RetryStrategy.ERROR_CONFIGS.get(
            error_type,
            RetryStrategy.ERROR_CONFIGS["Default"]
        )


class AudioTaskExecutor:
    """音频任务执行器"""
    
    def __init__(self, task_queue: AudioTaskQueue,
                 tts_manager: IntegratedTTSManager,
                 max_concurrent: int = 3):
        """
        初始化任务执行器
        
        Args:
            task_queue: 任务队列
            tts_manager: TTS管理器
            max_concurrent: 最大并发任务数
        """
        self.task_queue = task_queue
        self.tts_manager = tts_manager
        self.max_concurrent = max_concurrent
        self.logger = get_logger(__name__)
        self.running_tasks: Set[str] = set()
        self.is_running = False
    
    async def start(self):
        """启动任务执行器"""
        self.is_running = True
        self.logger.info(f"任务执行器启动 (最大并发: {self.max_concurrent})")
        
        # 创建工作线程池
        workers = []
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i + 1))
            workers.append(worker)
        
        # 等待所有worker完成
        await asyncio.gather(*workers)
        
        self.logger.info("任务执行器停止")
    
    async def _worker(self, worker_id: int):
        """工作线程"""
        self.logger.info(f"Worker-{worker_id} 启动")
        
        while self.is_running:
            # 获取下一个待执行任务
            task = self.task_queue.get_next_task()
            
            if task is None:
                # 没有待执行任务
                stats = self.task_queue.get_statistics()
                if stats['pending'] == 0 and stats['running'] == 0:
                    self.logger.info(f"Worker-{worker_id}: 所有任务已完成")
                    break
                
                # 等待后重试
                await asyncio.sleep(1)
                continue
            
            # 执行任务
            self.logger.info(f"Worker-{worker_id} 开始执行: {task.task_id}")
            await self._execute_task(task)
            
            # 短暂延迟
            await asyncio.sleep(0.5)
        
        self.logger.info(f"Worker-{worker_id} 停止")
    
    async def _execute_task(self, task: AudioTask):
        """执行单个任务"""
        self.running_tasks.add(task.task_id)
        
        # 更新状态为运行中
        self.task_queue.update_task_status(
            task.task_id,
            TaskStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            # 生成音频文件路径
            audio_path = self.task_queue.project_dir / "output" / "audios" / task.audio_filename
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 调用TTS生成音频
            self.logger.info(f"合成语音: {task.script_content[:50]}...")
            
            result = await self.tts_manager.synthesize_speech(
                text=task.script_content,
                output_path=audio_path
            )
            
            if result["success"]:
                # 成功
                self.logger.info(f"✅ {task.task_id} 完成: {result['engine']}, {result['duration']:.2f}s")
                
                self.task_queue.mark_task_completed(
                    task.task_id,
                    audio_path=str(audio_path),
                    duration_seconds=result['duration'],
                    file_size_bytes=result['file_size'],
                    engine_used=result['engine']
                )
            else:
                # 失败，处理重试
                await self._handle_task_failure(task, result.get('error', '未知错误'))
        
        except Exception as e:
            self.logger.error(f"❌ {task.task_id} 异常: {e}", exc_info=True)
            await self._handle_task_failure(task, str(e))
        
        finally:
            self.running_tasks.remove(task.task_id)
    
    async def _handle_task_failure(self, task: AudioTask, error: str):
        """处理任务失败"""
        # 分类错误
        error_type = self._classify_error(error)
        retry_config = RetryStrategy.get_retry_config(error_type)
        
        # 判断是否可以重试
        if task.retry_count < min(task.max_retries, retry_config['max_retries']):
            # 可以重试
            task.retry_count += 1
            
            # 计算延迟
            delay = self._calculate_retry_delay(
                task.retry_count,
                retry_config['retry_delay'],
                retry_config['backoff_multiplier']
            )
            
            self.logger.warning(
                f"⚠️ {task.task_id} 失败 (重试{task.retry_count}/{retry_config['max_retries']}), "
                f"{delay}秒后重试: {error}"
            )
            
            # 更新为重试中
            self.task_queue.update_task_status(
                task.task_id,
                TaskStatus.RETRYING,
                retry_count=task.retry_count,
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
            # 达到最大重试次数
            self.logger.error(
                f"❌ {task.task_id} 失败 (达到最大重试次数 {task.retry_count}): {error}"
            )
            
            self.task_queue.mark_task_failed(task.task_id, error)
    
    def _classify_error(self, error: str) -> str:
        """分类错误类型"""
        error_lower = error.lower()
        if "ssl" in error_lower:
            return "SSLError"
        elif "timeout" in error_lower:
            return "TimeoutError"
        elif "connection" in error_lower:
            return "ConnectionError"
        else:
            return "Default"
    
    def _calculate_retry_delay(self, retry_count: int, base_delay: int,
                               multiplier: float) -> int:
        """计算重试延迟"""
        max_delay = 300
        delay = base_delay * (multiplier ** (retry_count - 1))
        return min(int(delay), max_delay)
    
    def stop(self):
        """停止执行器"""
        self.is_running = False
```

### 第4步: 集成到TTS生成器 (Day 3)

#### 修改: `flask_backend/core/step02_tts_generator.py`

```python
# 在文件开头添加导入
from .audio_task_queue import AudioTaskQueue
from .audio_task_executor import AudioTaskExecutor

class TTSGenerator:
    def __init__(self, ...):
        # 现有代码...
        
        # 添加任务队列支持开关
        self.use_task_queue = True  # 默认启用
    
    async def generate_audio(self, scripts_data: Optional[Dict[str, Any]] = None, 
                             text: Optional[str] = None,
                             output_file: Optional[str] = None,
                             progress_callback: Optional[Callable[[int], None]] = None,
                             use_task_queue: Optional[bool] = None) -> Dict[str, Any]:
        """
        生成所有讲话稿的音频文件
        
        Args:
            scripts_data: 讲话稿数据
            text: 单一文本（测试用）
            output_file: 输出文件（测试用）
            progress_callback: 进度回调
            use_task_queue: 是否使用任务队列（None=使用默认配置）
        """
        # 兼容性处理
        if text is not None and scripts_data is None:
            scripts_data = self._create_scripts_from_text(text)
        
        # 决定使用哪种方式
        if use_task_queue is None:
            use_task_queue = self.use_task_queue
        
        if use_task_queue:
            return await self._generate_with_task_queue(scripts_data, progress_callback)
        else:
            return await self._generate_legacy(scripts_data, progress_callback)
    
    async def _generate_with_task_queue(self, scripts_data: Dict,
                                       progress_callback: Optional[Callable] = None) -> Dict:
        """使用任务队列生成音频"""
        self.logger.info("使用任务队列方式生成音频")
        
        # 创建会话ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建任务队列
        task_queue = AudioTaskQueue(session_id, self.project_dir)
        
        # 创建任务
        num_tasks = task_queue.create_tasks_from_scripts(scripts_data)
        self.logger.info(f"创建了 {num_tasks} 个音频任务")
        
        # 创建执行器
        executor = AudioTaskExecutor(
            task_queue=task_queue,
            tts_manager=self.tts_manager,
            max_concurrent=3
        )
        
        # 执行任务
        await executor.start()
        
        # 获取统计信息
        stats = task_queue.get_statistics()
        self.logger.info(f"任务完成: {stats['completed']}/{stats['total_tasks']}, 成功率: {stats['success_rate']*100:.1f}%")
        
        # 检查失败的任务
        if stats['failed'] > 0:
            failed_tasks = task_queue.get_failed_tasks()
            error_msg = f"有 {len(failed_tasks)} 个音频生成失败:\n"
            for task in failed_tasks:
                error_msg += f"  - {task.task_id}: {task.last_error}\n"
            
            self.logger.error(error_msg)
            
            # 抛出异常，让上层处理
            raise Exception(error_msg)
        
        # 构建返回数据
        return self._build_audio_data_from_queue(task_queue)
    
    def _build_audio_data_from_queue(self, task_queue: AudioTaskQueue) -> Dict:
        """从任务队列构建音频数据"""
        all_tasks = task_queue.storage.get_all_tasks(task_queue.session_id)
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
        
        audio_files = []
        total_duration = 0.0
        
        for task in sorted(completed_tasks, key=lambda t: t.page_number):
            audio_info = {
                "audio_id": task.task_id,
                "slide_number": task.page_number,
                "audio_file": task.audio_filename,
                "duration_seconds": task.duration_seconds or 0.0,
                "file_size_bytes": task.file_size_bytes or 0,
                "engine_used": task.engine_used,
                "script_content": task.script_content,
                "retry_count": task.retry_count
            }
            audio_files.append(audio_info)
            total_duration += task.duration_seconds or 0.0
        
        return {
            "total_audio_files": len(completed_tasks),
            "generation_completed": True,
            "generation_timestamp": datetime.now().isoformat(),
            "audio_files": audio_files,
            "total_duration_seconds": total_duration,
            "session_id": task_queue.session_id
        }
    
    async def _generate_legacy(self, scripts_data: Dict,
                               progress_callback: Optional[Callable] = None) -> Dict:
        """旧的生成方式（兼容）"""
        self.logger.warning("使用旧的音频生成方式（兼容模式）")
        # 调用原来的逻辑...
        # （保留现有代码）
```

### 第5步: 添加重试命令 (Day 3)

#### 创建文件: `flask_backend/scripts/retry_failed_audio.py`

```python
"""
重试失败的音频任务脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask_backend.core.audio_task_queue import AudioTaskQueue
from flask_backend.core.audio_task_executor import AudioTaskExecutor
from flask_backend.core.audio_task_models import TaskStatus
from flask_backend.app.utils.integrated_tts_manager import IntegratedTTSManager, load_tts_config_from_app_config

async def retry_failed_tasks(session_id: str, project_dir: Path):
    """重试失败的任务"""
    
    print(f"正在加载会话: {session_id}")
    
    # 加载任务队列
    task_queue = AudioTaskQueue(session_id, project_dir)
    
    # 获取失败的任务
    failed_tasks = task_queue.get_failed_tasks()
    
    if not failed_tasks:
        print("✅ 没有失败的任务")
        return
    
    print(f"发现 {len(failed_tasks)} 个失败任务:")
    for task in failed_tasks:
        print(f"  - {task.task_id}: {task.last_error}")
    
    # 重置失败任务
    for task in failed_tasks:
        print(f"重置任务: {task.task_id}")
        task_queue.update_task_status(
            task.task_id,
            TaskStatus.PENDING,
            retry_count=0,
            last_error=None
        )
    
    # 重新执行
    print("\n开始重试...")
    tts_config = load_tts_config_from_app_config()
    tts_manager = IntegratedTTSManager(tts_config)
    
    executor = AudioTaskExecutor(
        task_queue=task_queue,
        tts_manager=tts_manager,
        max_concurrent=2
    )
    
    await executor.start()
    
    # 查看结果
    stats = task_queue.get_statistics()
    print(f"\n重试完成:")
    print(f"  总计: {stats['total_tasks']}")
    print(f"  成功: {stats['completed']}")
    print(f"  失败: {stats['failed']}")
    print(f"  成功率: {stats['success_rate']*100:.1f}%")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python retry_failed_audio.py <session_id> [project_dir]")
        sys.exit(1)
    
    session_id = sys.argv[1]
    project_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
    
    asyncio.run(retry_failed_tasks(session_id, project_dir))
```

---

## 测试步骤

### 1. 单元测试

创建: `tests/test_audio_task_queue.py`

```python
import pytest
from pathlib import Path
from datetime import datetime

from flask_backend.core.audio_task_models import AudioTask, TaskStatus
from flask_backend.core.audio_task_queue import AudioTaskQueue

def test_create_tasks():
    """测试创建任务"""
    session_id = f"test_{datetime.now().timestamp()}"
    project_dir = Path("test_output")
    
    task_queue = AudioTaskQueue(session_id, project_dir)
    
    scripts_data = {
        "scripts": [
            {"slide_number": 1, "text": "测试文本1"},
            {"slide_number": 2, "text": "测试文本2"}
        ]
    }
    
    num_tasks = task_queue.create_tasks_from_scripts(scripts_data)
    assert num_tasks == 2
    
    stats = task_queue.get_statistics()
    assert stats['total_tasks'] == 2
    assert stats['pending'] == 2

def test_update_task_status():
    """测试更新任务状态"""
    session_id = f"test_{datetime.now().timestamp()}"
    task_queue = AudioTaskQueue(session_id, Path("test_output"))
    
    # 创建任务
    scripts_data = {"scripts": [{"slide_number": 1, "text": "测试"}]}
    task_queue.create_tasks_from_scripts(scripts_data)
    
    # 更新状态
    task_queue.update_task_status("audio_001", TaskStatus.COMPLETED)
    
    # 验证
    stats = task_queue.get_statistics()
    assert stats['completed'] == 1
    assert stats['pending'] == 0
```

### 2. 集成测试

```python
# 运行完整流程
async def test_full_workflow():
    from flask_backend.core.step02_tts_generator import TTSGenerator
    
    project_dir = Path("test_project")
    tts_gen = TTSGenerator(project_dir)
    
    scripts_data = {
        "scripts": [
            {"slide_number": 1, "text": "测试音频生成1"},
            {"slide_number": 2, "text": "测试音频生成2"}
        ]
    }
    
    result = await tts_gen.generate_audio(scripts_data, use_task_queue=True)
    
    print(f"生成完成: {result['total_audio_files']} 个文件")
    print(f"总时长: {result['total_duration_seconds']:.2f} 秒")
```

---

## ✅ 验收标准

- [ ] 所有任务持久化到数据库
- [ ] 失败任务自动重试（最多10次）
- [ ] 不生成静默音频
- [ ] 支持断点续传
- [ ] 支持并发执行（3个并发）
- [ ] 完整的错误历史记录
- [ ] 可以查看任务统计信息
- [ ] 可以手动重试失败的任务
- [ ] 所有测试通过

---

## 📝 使用文档

### 基本使用

```python
# 1. 生成音频（自动使用任务队列）
tts_gen = TTSGenerator(project_dir)
result = await tts_gen.generate_audio(scripts_data)

# 2. 查看失败任务
# 从日志中获取session_id
session_id = result['session_id']

# 3. 重试失败任务
python flask_backend/scripts/retry_failed_audio.py <session_id>
```

---

**实施指南完成**  
**预计时间**: 3-4天  
**难度**: ⭐⭐⭐⭐
