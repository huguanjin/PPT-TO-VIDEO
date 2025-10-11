"""
音频任务存储适配器

使用SQLite持久化存储任务状态，支持断点续传和任务查询
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .audio_task_models import AudioTask, TaskStatus
from app.utils.logger import get_logger


class TaskStorage:
    """任务存储基类（抽象接口）"""
    
    def save_task(self, task: AudioTask) -> bool:
        """保存任务"""
        raise NotImplementedError
    
    def get_task(self, task_id: str) -> Optional[AudioTask]:
        """获取单个任务"""
        raise NotImplementedError
    
    def get_all_tasks(self, session_id: str) -> List[AudioTask]:
        """获取会话的所有任务"""
        raise NotImplementedError
    
    def get_tasks_by_status(self, session_id: str, status: TaskStatus) -> List[AudioTask]:
        """获取指定状态的任务"""
        raise NotImplementedError
    
    def get_next_pending_task(self, session_id: str) -> Optional[AudioTask]:
        """获取下一个待执行的任务"""
        raise NotImplementedError


class SQLiteTaskStorage(TaskStorage):
    """SQLite任务存储实现
    
    使用SQLite数据库持久化存储任务，支持：
    - 完整的CRUD操作
    - 高效的索引查询
    - 事务安全
    """
    
    def __init__(self, db_path: Path):
        """初始化存储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表和索引"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 创建任务表
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
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON audio_tasks(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON audio_tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_status ON audio_tasks(priority DESC, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_page ON audio_tasks(session_id, page_number)')
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"✅ SQLite数据库初始化完成: {self.db_path}")
    
    def save_task(self, task: AudioTask) -> bool:
        """保存任务到数据库
        
        Args:
            task: 任务对象
            
        Returns:
            是否保存成功
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        task_dict = task.to_dict()
        
        # 序列化复杂字段为JSON
        task_dict['error_history'] = json.dumps(task_dict['error_history'], ensure_ascii=False)
        task_dict['metadata'] = json.dumps(task_dict['metadata'], ensure_ascii=False)
        
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
            self.logger.error(f"❌ 保存任务失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_task(self, task_id: str) -> Optional[AudioTask]:
        """获取单个任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM audio_tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_task(row)
        
        return None
    
    def get_all_tasks(self, session_id: str) -> List[AudioTask]:
        """获取会话的所有任务
        
        Args:
            session_id: 会话ID
            
        Returns:
            任务列表（按页码排序）
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audio_tasks 
            WHERE session_id = ? 
            ORDER BY page_number, segment_index
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def get_tasks_by_status(self, session_id: str, status: TaskStatus) -> List[AudioTask]:
        """获取指定状态的任务
        
        Args:
            session_id: 会话ID
            status: 任务状态
            
        Returns:
            任务列表
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audio_tasks 
            WHERE session_id = ? AND status = ?
            ORDER BY page_number, segment_index
        ''', (session_id, status.value))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def get_next_pending_task(self, session_id: str) -> Optional[AudioTask]:
        """获取下一个待执行任务（按优先级和创建时间排序）
        
        Args:
            session_id: 会话ID
            
        Returns:
            下一个待执行的任务，如果没有则返回None
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audio_tasks 
            WHERE session_id = ? AND status = ?
            ORDER BY priority DESC, page_number ASC, created_at ASC
            LIMIT 1
        ''', (session_id, TaskStatus.PENDING.value))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_task(row)
        
        return None
    
    def _row_to_task(self, row: sqlite3.Row) -> AudioTask:
        """将数据库行转换为任务对象
        
        Args:
            row: 数据库行
            
        Returns:
            任务对象
        """
        task_dict = dict(row)
        # 反序列化JSON字段
        task_dict['error_history'] = json.loads(task_dict['error_history'])
        task_dict['metadata'] = json.loads(task_dict['metadata'])
        return AudioTask.from_dict(task_dict)
    
    def get_statistics(self, session_id: str) -> dict:
        """获取任务统计信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 按状态统计
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM audio_tasks
            WHERE session_id = ?
            GROUP BY status
        ''', (session_id,))
        
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 总计和平均值
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(retry_count) as avg_retries,
                SUM(duration_seconds) as total_duration
            FROM audio_tasks
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total': row[0] or 0,
            'avg_retries': row[1] or 0.0,
            'total_duration': row[2] or 0.0,
            'by_status': status_counts
        }
