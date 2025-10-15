"""
工作流持久化和断点续传系统
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio

from app.utils.logger import get_logger
from app.utils.file_manager import FileManager

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStepResult:
    """工作流步骤执行结果"""
    step_name: str
    status: StepStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    progress: float = 0.0
    output_files: Optional[List[str]] = None
    input_files: Optional[List[str]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    can_skip: bool = False
    
    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
        if self.input_files is None:
            self.input_files = []

@dataclass
class WorkflowExecution:
    """工作流执行记录"""
    execution_id: str
    project_name: str
    workflow_status: WorkflowStatus
    start_time: str
    end_time: Optional[str] = None
    steps: Dict[str, WorkflowStepResult] = field(default_factory=dict)
    current_step: Optional[str] = None
    total_progress: float = 0.0
    config: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class WorkflowPersistenceManager:
    """工作流持久化管理器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.file_manager = FileManager(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # 工作流记录目录
        self.workflow_dir = self.project_dir / "workflow_history"
        self.workflow_dir.mkdir(exist_ok=True)
        
        # 定义工作流步骤和依赖关系
        # 🔧 移除了 step01b_ai_content_optimization (Phase 4已删除 ai_content_optimizer.py)
        self.workflow_steps = {
            "step01_data_preparation": {
                "name": "数据准备",
                "required_inputs": ["slides_metadata.json", "slides/*.png"],
                "expected_outputs": ["scripts/scripts_metadata.json"],
                "can_skip_if_complete": True
            },
            "step02_tts_generation": {
                "name": "语音生成", 
                "required_inputs": ["scripts/scripts_metadata.json"],
                "expected_outputs": ["audio/*.wav", "audio/audio_metadata.json"],
                "can_skip_if_complete": True
            },
            "step03_video_generation": {
                "name": "视频生成",
                "required_inputs": ["slides/*.png", "audio/audio_metadata.json"],
                "expected_outputs": ["video_clips/*.mp4", "video_clips/video_metadata.json"],
                "can_skip_if_complete": True
            },
            "step04_subtitle_generation": {
                "name": "字幕生成",
                "required_inputs": ["scripts/scripts_metadata.json", "audio/audio_metadata.json"], 
                "expected_outputs": ["subtitles/*.srt"],
                "can_skip_if_complete": True
            },
            "step05_final_merge": {
                "name": "最终合并",
                "required_inputs": ["video_clips/*.mp4", "audio/*.wav", "subtitles/*.srt"],
                "expected_outputs": ["final/final_video.mp4"],
                "can_skip_if_complete": False  # 合并步骤总是执行
            }
        }
    
    def create_new_execution(self, project_name: str, config: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
        """创建新的工作流执行记录"""
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            project_name=project_name,
            workflow_status=WorkflowStatus.IDLE,
            start_time=datetime.now().isoformat(),
            config=config
        )
        
        # 初始化所有步骤
        for step_name, step_info in self.workflow_steps.items():
            execution.steps[step_name] = WorkflowStepResult(
                step_name=step_name,
                status=StepStatus.PENDING
            )
        
        self.save_execution(execution)
        return execution
    
    def load_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """加载工作流执行记录"""
        execution_file = self.workflow_dir / f"{execution_id}.json"
        
        if not execution_file.exists():
            return None
        
        try:
            with open(execution_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重构步骤数据
            steps = {}
            for step_name, step_data in data.get("steps", {}).items():
                # 处理枚举值
                if isinstance(step_data.get("status"), str):
                    step_data["status"] = StepStatus(step_data["status"])
                steps[step_name] = WorkflowStepResult(**step_data)
            
            # 处理工作流状态枚举
            if isinstance(data.get("workflow_status"), str):
                data["workflow_status"] = WorkflowStatus(data["workflow_status"])
            
            execution = WorkflowExecution(**{k: v for k, v in data.items() if k != "steps"})
            execution.steps = steps
            
            return execution
            
        except Exception as e:
            self.logger.error(f"加载工作流执行记录失败: {e}")
            return None
    
    def save_execution(self, execution: WorkflowExecution):
        """保存工作流执行记录"""
        execution_file = self.workflow_dir / f"{execution.execution_id}.json"
        
        try:
            # 转换为可序列化的格式
            data = asdict(execution)
            data["workflow_status"] = execution.workflow_status.value
            
            for step_name, step_result in data["steps"].items():
                step_result["status"] = step_result["status"].value
            
            with open(execution_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存工作流执行记录失败: {e}")
    
    def get_latest_execution(self, project_name: str) -> Optional[WorkflowExecution]:
        """获取项目的最新执行记录"""
        executions = []
        
        for execution_file in self.workflow_dir.glob("*.json"):
            execution = self.load_execution(execution_file.stem)
            if execution and execution.project_name == project_name:
                executions.append(execution)
        
        if not executions:
            return None
        
        # 按开始时间排序，返回最新的
        executions.sort(key=lambda x: x.start_time, reverse=True)
        return executions[0]
    
    def check_step_can_skip(self, step_name: str, execution: WorkflowExecution) -> Tuple[bool, str]:
        """检查步骤是否可以跳过"""
        step_info = self.workflow_steps.get(step_name)
        if not step_info or not step_info["can_skip_if_complete"]:
            return False, "步骤不支持跳过"
        
        step_result = execution.steps.get(step_name)
        if not step_result or step_result.status != StepStatus.COMPLETED:
            return False, "步骤未完成"
        
        # 检查输出文件是否存在
        expected_outputs = step_info["expected_outputs"]
        for output_pattern in expected_outputs:
            if "*" in output_pattern:
                # 处理通配符模式
                output_dir = self.project_dir / output_pattern.split("*")[0].rstrip("/")
                if not output_dir.exists() or not any(output_dir.iterdir()):
                    return False, f"输出文件不存在: {output_pattern}"
            else:
                output_file = self.project_dir / output_pattern
                if not output_file.exists():
                    return False, f"输出文件不存在: {output_pattern}"
        
        return True, "可以跳过"
    
    def update_step_status(self, execution: WorkflowExecution, step_name: str, 
                          status: StepStatus, progress: float = 0.0, 
                          error_message: Optional[str] = None,
                          output_files: Optional[List[str]] = None):
        """更新步骤状态"""
        if step_name not in execution.steps:
            execution.steps[step_name] = WorkflowStepResult(
                step_name=step_name,
                status=status
            )
        
        step_result = execution.steps[step_name]
        step_result.status = status
        step_result.progress = progress
        
        if status == StepStatus.RUNNING and not step_result.start_time:
            step_result.start_time = datetime.now().isoformat()
        
        if status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
            step_result.end_time = datetime.now().isoformat()
            if step_result.start_time:
                start_dt = datetime.fromisoformat(step_result.start_time)
                end_dt = datetime.fromisoformat(step_result.end_time)
                step_result.execution_time = (end_dt - start_dt).total_seconds()
        
        if error_message:
            step_result.error_message = error_message
        
        if output_files:
            step_result.output_files = output_files
        
        # 更新执行记录的当前步骤和总进度
        execution.current_step = step_name
        
        completed_steps = sum(1 for step in execution.steps.values() 
                            if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED])
        total_steps = len(execution.steps)
        execution.total_progress = (completed_steps / total_steps) * 100
        
        self.save_execution(execution)
    
    def get_next_pending_step(self, execution: WorkflowExecution) -> Optional[str]:
        """获取下一个待执行的步骤"""
        for step_name in self.workflow_steps.keys():
            step_result = execution.steps.get(step_name)
            if not step_result or step_result.status == StepStatus.PENDING:
                return step_name
        return None
    
    def can_resume_workflow(self, execution: WorkflowExecution) -> bool:
        """检查工作流是否可以恢复"""
        return execution.workflow_status in [WorkflowStatus.FAILED, WorkflowStatus.RUNNING]
    
    def mark_workflow_completed(self, execution: WorkflowExecution):
        """标记工作流为完成状态"""
        execution.workflow_status = WorkflowStatus.COMPLETED
        execution.end_time = datetime.now().isoformat()
        self.save_execution(execution)
    
    def mark_workflow_failed(self, execution: WorkflowExecution, error_message: str):
        """标记工作流为失败状态"""
        execution.workflow_status = WorkflowStatus.FAILED
        execution.error_message = error_message
        execution.end_time = datetime.now().isoformat()
        self.save_execution(execution)

    def list_project_executions(self, project_name: str) -> List[WorkflowExecution]:
        """列出项目的所有执行记录"""
        executions = []
        
        for execution_file in self.workflow_dir.glob("*.json"):
            execution = self.load_execution(execution_file.stem)
            if execution and execution.project_name == project_name:
                executions.append(execution)
        
        # 按开始时间排序
        executions.sort(key=lambda x: x.start_time, reverse=True)
        return executions

