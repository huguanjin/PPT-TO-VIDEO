"""
任务数据模型
记录正在执行的工作流任务
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from bson import ObjectId

from app.database.mongodb import get_db


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    SKIPPED = "skipped"       # 已跳过


@dataclass
class TaskStep:
    """任务步骤"""
    name: str                            # 步骤标识符
    display_name: str                    # 显示名称
    status: str = StepStatus.PENDING.value
    progress: int = 0                    # 0-100
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskStep':
        """从字典创建"""
        started_at = data.get('started_at')
        completed_at = data.get('completed_at')
        
        # 处理日期时间转换
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
            
        return cls(
            name=data.get('name', ''),
            display_name=data.get('display_name', ''),
            status=data.get('status', StepStatus.PENDING.value),
            progress=data.get('progress', 0),
            message=data.get('message', ''),
            started_at=started_at,
            completed_at=completed_at
        )


# 默认的工作流步骤定义
DEFAULT_WORKFLOW_STEPS = [
    {"name": "step01_data_preparation", "display_name": "数据准备"},
    {"name": "step02_tts_generation", "display_name": "TTS音频生成"},
    {"name": "step03_video_generation", "display_name": "视频片段生成"},
    {"name": "step04_subtitle_generation", "display_name": "字幕生成"},
    {"name": "step05_final_merge", "display_name": "最终合成"},
]


@dataclass
class Task:
    """任务数据模型"""
    user_id: ObjectId                    # 关联用户
    project_name: str                    # 项目名称
    status: str = TaskStatus.PENDING.value
    progress: int = 0                    # 0-100 总进度
    current_step: Optional[str] = None   # 当前步骤标识
    current_step_name: Optional[str] = None  # 当前步骤显示名称
    total_steps: int = 5
    steps: List[TaskStep] = field(default_factory=list)
    work_dir: Optional[str] = None       # 工作目录
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    _id: Optional[ObjectId] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 如果没有步骤，初始化默认步骤
        if not self.steps:
            self.steps = [
                TaskStep(name=s['name'], display_name=s['display_name'])
                for s in DEFAULT_WORKFLOW_STEPS
            ]
            self.total_steps = len(self.steps)
    
    def to_dict(self, include_id: bool = True) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'user_id': str(self.user_id),
            'project_name': self.project_name,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'current_step_name': self.current_step_name,
            'total_steps': self.total_steps,
            'steps': [s.to_dict() for s in self.steps],
            'work_dir': self.work_dir,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        if include_id and self._id:
            data['id'] = str(self._id)
        return data
    
    def to_db_dict(self) -> Dict[str, Any]:
        """转换为数据库文档格式"""
        return {
            'user_id': self.user_id,
            'project_name': self.project_name,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'current_step_name': self.current_step_name,
            'total_steps': self.total_steps,
            'steps': [s.to_dict() for s in self.steps],
            'work_dir': self.work_dir,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建任务对象"""
        # 处理 user_id
        user_id = data.get('user_id')
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        # 处理步骤
        steps_data = data.get('steps', [])
        steps = [TaskStep.from_dict(s) for s in steps_data]
        
        # 处理日期
        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                return datetime.fromisoformat(val)
            return val
        
        return cls(
            user_id=user_id,
            project_name=data.get('project_name', ''),
            status=data.get('status', TaskStatus.PENDING.value),
            progress=data.get('progress', 0),
            current_step=data.get('current_step'),
            current_step_name=data.get('current_step_name'),
            total_steps=data.get('total_steps', 5),
            steps=steps,
            work_dir=data.get('work_dir'),
            error_message=data.get('error_message'),
            created_at=parse_date(data.get('created_at')) or datetime.utcnow(),
            updated_at=parse_date(data.get('updated_at')) or datetime.utcnow(),
            started_at=parse_date(data.get('started_at')),
            completed_at=parse_date(data.get('completed_at')),
            _id=data.get('_id')
        )


class TaskService:
    """任务服务类"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.tasks
    
    def create_task(self, user_id: str, project_name: str, work_dir: Optional[str] = None) -> Optional[Task]:
        """
        创建新任务
        
        Args:
            user_id: 用户ID
            project_name: 项目名称
            work_dir: 工作目录
            
        Returns:
            创建的任务对象
        """
        task = Task(
            user_id=ObjectId(user_id),
            project_name=project_name,
            work_dir=work_dir or f"output/{user_id}"
        )
        
        task_doc = task.to_db_dict()
        result = self.collection.insert_one(task_doc)
        
        if result.inserted_id:
            task._id = result.inserted_id
            return task
        
        return None
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        try:
            task_doc = self.collection.find_one({'_id': ObjectId(task_id)})
            if task_doc:
                return Task.from_dict(task_doc)
        except Exception:
            pass
        return None
    
    def get_user_tasks(self, user_id: str, status: Optional[str] = None, 
                       skip: int = 0, limit: int = 20) -> List[Task]:
        """
        获取用户的任务列表
        
        Args:
            user_id: 用户ID
            status: 可选，按状态筛选
            skip: 跳过数量
            limit: 返回数量限制
        """
        query = {'user_id': ObjectId(user_id)}
        if status:
            query['status'] = status
        
        tasks = []
        cursor = self.collection.find(query).sort('created_at', -1).skip(skip).limit(limit)
        for doc in cursor:
            tasks.append(Task.from_dict(doc))
        return tasks
    
    def get_user_active_task(self, user_id: str) -> Optional[Task]:
        """获取用户当前活动的任务（正在执行的）"""
        task_doc = self.collection.find_one({
            'user_id': ObjectId(user_id),
            'status': {'$in': [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]}
        })
        if task_doc:
            return Task.from_dict(task_doc)
        return None
    
    def start_task(self, task_id: str) -> bool:
        """启动任务"""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'status': TaskStatus.RUNNING.value,
                'started_at': now,
                'updated_at': now
            }}
        )
        return result.modified_count > 0
    
    def update_step_progress(self, task_id: str, step_name: str, 
                            status: str, progress: int, message: str = "") -> bool:
        """
        更新步骤进度
        
        Args:
            task_id: 任务ID
            step_name: 步骤名称
            status: 步骤状态
            progress: 步骤进度 (0-100)
            message: 进度消息
        """
        task = self.get_by_id(task_id)
        if not task:
            return False
        
        now = datetime.utcnow()
        
        # 更新步骤
        for step in task.steps:
            if step.name == step_name:
                step.status = status
                step.progress = progress
                step.message = message
                
                if status == StepStatus.RUNNING.value and not step.started_at:
                    step.started_at = now
                elif status in [StepStatus.COMPLETED.value, StepStatus.FAILED.value]:
                    step.completed_at = now
                break
        
        # 计算总进度
        total_progress = 0
        completed_steps = 0
        current_step = None
        current_step_name = None
        
        for step in task.steps:
            if step.status == StepStatus.COMPLETED.value:
                total_progress += 100
                completed_steps += 1
            elif step.status == StepStatus.RUNNING.value:
                total_progress += step.progress
                current_step = step.name
                current_step_name = step.display_name
            elif step.status == StepStatus.SKIPPED.value:
                completed_steps += 1
        
        overall_progress = int(total_progress / len(task.steps)) if task.steps else 0
        
        # 更新数据库
        result = self.collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'steps': [s.to_dict() for s in task.steps],
                'progress': overall_progress,
                'current_step': current_step,
                'current_step_name': current_step_name,
                'updated_at': now
            }}
        )
        return result.modified_count > 0
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'status': TaskStatus.COMPLETED.value,
                'progress': 100,
                'completed_at': now,
                'updated_at': now
            }}
        )
        return result.modified_count > 0
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务失败"""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'status': TaskStatus.FAILED.value,
                'error_message': error_message,
                'completed_at': now,
                'updated_at': now
            }}
        )
        return result.modified_count > 0
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'status': TaskStatus.CANCELLED.value,
                'completed_at': now,
                'updated_at': now
            }}
        )
        return result.modified_count > 0
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        result = self.collection.delete_one({'_id': ObjectId(task_id)})
        return result.deleted_count > 0
    
    def delete_completed_tasks(self, user_id: str, before_date: Optional[datetime] = None) -> int:
        """
        删除已完成的任务
        
        Args:
            user_id: 用户ID
            before_date: 可选，只删除此日期之前的任务
            
        Returns:
            删除的任务数量
        """
        query = {
            'user_id': ObjectId(user_id),
            'status': {'$in': [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]}
        }
        if before_date:
            query['completed_at'] = {'$lt': before_date}
        
        result = self.collection.delete_many(query)
        return result.deleted_count
    
    def count_user_tasks(self, user_id: str, status: Optional[str] = None) -> int:
        """统计用户任务数量"""
        query = {'user_id': ObjectId(user_id)}
        if status:
            query['status'] = status
        return self.collection.count_documents(query)


# 便捷函数
def get_task_service() -> TaskService:
    """获取任务服务实例"""
    return TaskService()
