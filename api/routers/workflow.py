"""
工作流API路由
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio

from ..dependencies import get_workflow_service
from ..services import WorkflowService, ServiceResult
from ..exceptions import WorkflowException, ResourceNotFoundException, ValidationException

router = APIRouter(prefix="/workflow", tags=["Workflow"])

# 请求模型
class WorkflowStartRequest(BaseModel):
    workflow_data: Dict[str, Any]
    project_name: Optional[str] = None

class WorkflowStepInfo(BaseModel):
    name: str
    order: int
    display_name: str
    description: str
    required_inputs: List[str]
    outputs: List[str]

class WorkflowStatus(BaseModel):
    id: str
    status: str
    current_step: int
    total_steps: int
    progress: float
    start_time: str
    end_time: Optional[str] = None
    error: Optional[str] = None

class ActiveWorkflow(BaseModel):
    id: str
    status: str
    progress: float
    current_step: int
    start_time: str

@router.get("/steps", response_model=List[WorkflowStepInfo])
async def get_workflow_steps(
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """获取工作流步骤"""
    
    result = workflow_service.get_workflow_steps()
    
    if not result.success:
        raise WorkflowException(result.error)
    
    return result.data

@router.post("/start")
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """启动工作流"""
    
    if not request.workflow_data:
        raise ValidationException("工作流数据不能为空", "workflow_data")
    
    # 验证必要的输入数据
    if "input_file" not in request.workflow_data:
        raise ValidationException("缺少输入文件", "workflow_data.input_file")
    
    result = await workflow_service.start_workflow(
        workflow_data=request.workflow_data
    )
    
    if not result.success:
        raise WorkflowException(result.error)
    
    return result.data

@router.get("/status/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """获取工作流状态"""
    
    result = workflow_service.get_workflow_status(workflow_id)
    
    if not result.success:
        if result.code == 404:
            raise ResourceNotFoundException("Workflow", workflow_id)
        else:
            raise WorkflowException(result.error, workflow_id)
    
    return result.data

@router.post("/cancel/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """取消工作流"""
    
    result = workflow_service.cancel_workflow(workflow_id)
    
    if not result.success:
        if result.code == 404:
            raise ResourceNotFoundException("Workflow", workflow_id)
        else:
            raise WorkflowException(result.error, workflow_id)
    
    return result.data

@router.get("/active", response_model=List[ActiveWorkflow])
async def get_active_workflows(
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """获取活动工作流"""
    
    result = workflow_service.get_active_workflows()
    
    if not result.success:
        raise WorkflowException(result.error)
    
    return result.data

@router.get("/health")
async def workflow_health_check(
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """工作流服务健康检查"""
    
    return workflow_service.health_check()

# WebSocket端点用于实时进度更新
from fastapi import WebSocket, WebSocketDisconnect
import json

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_progress_update(self, workflow_id: str, progress_data: Dict[str, Any]):
        message = {
            "type": "progress_update",
            "workflow_id": workflow_id,
            "data": progress_data
        }
        
        # 发送给所有连接的客户端
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # 连接可能已断开
                pass

manager = ConnectionManager()

@router.websocket("/progress/{workflow_id}")
async def workflow_progress_websocket(
    websocket: WebSocket,
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """工作流进度WebSocket"""
    
    await manager.connect(websocket)
    
    try:
        while True:
            # 获取工作流状态
            result = workflow_service.get_workflow_status(workflow_id)
            
            if result.success:
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "workflow_id": workflow_id,
                    "data": result.data
                }))
            
            # 如果工作流完成或失败，断开连接
            if result.success and result.data.get("status") in ["completed", "failed", "cancelled"]:
                break
            
            # 等待一段时间再次检查
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 添加导入和执行端点
from fastapi import UploadFile, File, Form
from typing import List

class ImportRequest(BaseModel):
    project_data: Dict[str, Any]
    images: Optional[List[str]] = []

@router.post("/import")
async def import_ppt_data(
    project_data: str = Form(...),
    images: List[UploadFile] = File([]),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """导入PPT数据并启动工作流"""
    
    try:
        import json
        import tempfile
        import base64
        from pathlib import Path
        
        # 解析项目数据
        try:
            project_json = json.loads(project_data)
        except json.JSONDecodeError:
            raise ValidationException("项目数据格式无效", "project_data")
        
        # 创建临时目录保存图片
        temp_dir = Path(tempfile.mkdtemp(prefix="ppt_import_"))
        image_files = []
        
        # 保存上传的图片
        for i, image_file in enumerate(images):
            if image_file.filename:
                image_path = temp_dir / f"slide_{str(i + 1).zfill(3)}.png"
                with open(image_path, "wb") as f:
                    content = await image_file.read()
                    f.write(content)
                image_files.append(str(image_path))
        
        # 准备工作流数据
        workflow_data = {
            "project_data": project_json,
            "image_files": image_files,
            "temp_dir": str(temp_dir),
            "import_type": "pptist"
        }
        
        # 启动工作流
        result = workflow_service.start_workflow(
            workflow_data=workflow_data,
            project_name=project_json.get("title", "导入的PPT项目")
        )
        
        if not result.success:
            raise WorkflowException(result.error)
        
        return {
            "success": True,
            "message": "PPT数据导入成功",
            "workflow_id": result.data.get("workflow_id"),
            "project_id": result.data.get("project_id")
        }
        
    except Exception as e:
        raise WorkflowException(f"导入PPT数据失败: {str(e)}")

@router.post("/execute")
async def execute_workflow(
    workflow_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    project_name: Optional[str] = None,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """执行完整工作流"""
    
    try:
        # 启动工作流
        result = workflow_service.start_workflow(
            workflow_data=workflow_data,
            project_name=project_name or "未命名项目"
        )
        
        if not result.success:
            raise WorkflowException(result.error)
        
        return {
            "success": True,
            "message": "工作流已启动",
            "workflow_id": result.data.get("workflow_id")
        }
        
    except Exception as e:
        raise WorkflowException(f"执行工作流失败: {str(e)}")
