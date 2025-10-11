"""
音频任务数据模型

定义音频生成任务的数据结构和状态管理
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
    """音频生成任务
    
    包含任务的完整信息：基本信息、执行状态、重试记录、结果数据等
    """
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
        """转换为字典，用于序列化存储"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AudioTask':
        """从字典创建任务对象"""
        data = data.copy()
        data['status'] = TaskStatus(data['status'])
        
        # 转换时间字段
        for time_field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
            if data.get(time_field):
                data[time_field] = datetime.fromisoformat(data[time_field])
        
        return cls(**data)
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"AudioTask(id={self.task_id}, page={self.page_number}, "
                f"status={self.status.value}, retries={self.retry_count})")
