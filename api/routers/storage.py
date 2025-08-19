"""
存储API路由
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

from ..dependencies import get_storage_service
from ..services import StorageService, ServiceResult
from ..exceptions import StorageException, ResourceNotFoundException, ValidationException

router = APIRouter(prefix="/storage", tags=["Storage"])

# PPT项目相关模型
class PPTProject(BaseModel):
    project_id: str
    project_name: str
    slides: List[Dict[str, Any]]
    theme: Dict[str, Any] = {}
    viewport_ratio: float = 16/9
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str

class PPTSaveRequest(BaseModel):
    project_id: Optional[str] = None
    project_name: str
    slides: List[Dict[str, Any]]
    theme: Dict[str, Any] = {}
    viewport_ratio: float = 16/9
    metadata: Dict[str, Any] = {}

class AutoSaveRequest(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    slides: List[Dict[str, Any]] = []
    theme: Dict[str, Any] = {}
    viewport_ratio: float = 16/9
    metadata: Dict[str, Any] = {}

# 响应模型
class FileInfo(BaseModel):
    filename: str
    size: int
    modified: str
    path: str

class ProjectInfo(BaseModel):
    project_id: str
    project_name: Optional[str] = None
    created_time: Optional[str] = None
    status: Optional[str] = None
    project_size_mb: Optional[float] = None
    file_count: Optional[int] = None

class UploadResponse(BaseModel):
    filename: str
    size: int
    file_path: str
    directory: str

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    directory: str = Form("uploads"),
    storage_service: StorageService = Depends(get_storage_service)
):
    """上传文件"""
    
    if not file.filename:
        raise ValidationException("文件名不能为空", "filename")
    
    # 检查文件大小（限制100MB）
    if file.size and file.size > 100 * 1024 * 1024:
        raise ValidationException("文件大小不能超过100MB", "file")
    
    try:
        # 读取文件内容
        file_data = await file.read()
        
        result = storage_service.save_file(
            file_data=file_data,
            filename=file.filename,
            directory=directory
        )
        
        if not result.success:
            raise StorageException(result.error)
        
        return result.data
        
    except Exception as e:
        raise StorageException(f"上传文件失败: {str(e)}")
    finally:
        await file.close()

@router.get("/download/{directory}/{filename}")
async def download_file(
    directory: str,
    filename: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """下载文件"""
    
    result = storage_service.get_file(filename=filename, directory=directory)
    
    if not result.success:
        if result.code == 404:
            raise ResourceNotFoundException("File", filename)
        else:
            raise StorageException(result.error)
    
    # 创建临时文件用于下载
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(result.data["file_data"])
        temp_path = temp_file.name
    
    return FileResponse(
        path=temp_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.delete("/files/{directory}/{filename}")
async def delete_file(
    directory: str,
    filename: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """删除文件"""
    
    result = storage_service.delete_file(filename=filename, directory=directory)
    
    if not result.success:
        if result.code == 404:
            raise ResourceNotFoundException("File", filename)
        else:
            raise StorageException(result.error)
    
    return result.data

@router.get("/files", response_model=List[FileInfo])
async def list_files(
    directory: str = "uploads",
    pattern: str = "*",
    storage_service: StorageService = Depends(get_storage_service)
):
    """列出文件"""
    
    result = storage_service.list_files(directory=directory, pattern=pattern)
    
    if not result.success:
        raise StorageException(result.error)
    
    return result.data

@router.post("/projects", response_model=ProjectInfo)
async def create_project(
    project_name: str = Form(...),
    storage_service: StorageService = Depends(get_storage_service)
):
    """创建项目目录"""
    
    if not project_name.strip():
        raise ValidationException("项目名称不能为空", "project_name")
    
    result = storage_service.create_project_directory(project_name)
    
    if not result.success:
        raise StorageException(result.error)
    
    return result.data

@router.get("/projects/{project_id}", response_model=ProjectInfo)
async def get_project_info(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """获取项目信息"""
    
    result = storage_service.get_project_info(project_id)
    
    if not result.success:
        if result.code == 404:
            raise ResourceNotFoundException("Project", project_id)
        else:
            raise StorageException(result.error)
    
    return result.data

@router.post("/cleanup")
async def cleanup_old_files(
    days: int = 7,
    storage_service: StorageService = Depends(get_storage_service)
):
    """清理旧文件"""
    
    if days < 1:
        raise ValidationException("天数必须大于0", "days")
    
    result = storage_service.cleanup_old_files(days=days)
    
    if not result.success:
        raise StorageException(result.error)
    
    return result.data

@router.get("/health")
async def storage_health_check(
    storage_service: StorageService = Depends(get_storage_service)
):
    """存储服务健康检查"""
    
    return storage_service.health_check()

# PPT项目存储路由
@router.post("/ppt/save")
async def save_ppt_project(
    request: PPTSaveRequest,
    storage_service: StorageService = Depends(get_storage_service)
):
    """保存PPT项目"""
    
    try:
        # 生成项目ID（如果没有提供）
        project_id = request.project_id or str(uuid.uuid4())
        
        # 创建项目数据
        project_data = PPTProject(
            project_id=project_id,
            project_name=request.project_name,
            slides=request.slides,
            theme=request.theme,
            viewport_ratio=request.viewport_ratio,
            metadata=request.metadata,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # 保存项目数据
        ppt_storage_dir = Path("ppt_projects") / project_id
        ppt_storage_dir.mkdir(parents=True, exist_ok=True)
        
        project_file = ppt_storage_dir / "project.json"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data.model_dump(), f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "项目保存成功",
            "project_id": project_id,
            "saved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise StorageException(f"保存PPT项目失败: {str(e)}")

@router.post("/ppt/auto-save")
async def auto_save_ppt_project(
    request: AutoSaveRequest,
    storage_service: StorageService = Depends(get_storage_service)
):
    """自动保存PPT项目"""
    
    try:
        # 如果没有项目ID，生成一个新的
        project_id = request.project_id or str(uuid.uuid4())
        project_name = request.project_name or f"自动保存_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建项目数据
        project_data = PPTProject(
            project_id=project_id,
            project_name=project_name,
            slides=request.slides,
            theme=request.theme,
            viewport_ratio=request.viewport_ratio,
            metadata=request.metadata,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # 保存到自动保存目录
        auto_save_dir = Path("ppt_projects") / "auto_saves" / project_id
        auto_save_dir.mkdir(parents=True, exist_ok=True)
        
        project_file = auto_save_dir / "project.json"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data.model_dump(), f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "自动保存成功",
            "project_id": project_id,
            "auto_saved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise StorageException(f"自动保存PPT项目失败: {str(e)}")

@router.get("/ppt/load/{project_id}")
async def load_ppt_project(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """加载PPT项目"""
    
    try:
        # 先尝试从正常项目目录加载
        project_file = Path("ppt_projects") / project_id / "project.json"
        
        # 如果不存在，尝试从自动保存目录加载
        if not project_file.exists():
            project_file = Path("ppt_projects") / "auto_saves" / project_id / "project.json"
        
        if not project_file.exists():
            raise ResourceNotFoundException("PPT项目", project_id)
        
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        return {
            "success": True,
            "project": project_data
        }
        
    except FileNotFoundError:
        raise ResourceNotFoundException("PPT项目", project_id)
    except Exception as e:
        raise StorageException(f"加载PPT项目失败: {str(e)}")

@router.get("/ppt/list")
async def list_ppt_projects(
    storage_service: StorageService = Depends(get_storage_service)
):
    """获取PPT项目列表"""
    
    try:
        projects = []
        ppt_projects_dir = Path("ppt_projects")
        
        if ppt_projects_dir.exists():
            for project_dir in ppt_projects_dir.iterdir():
                if project_dir.is_dir() and project_dir.name != "auto_saves":
                    project_file = project_dir / "project.json"
                    if project_file.exists():
                        try:
                            with open(project_file, 'r', encoding='utf-8') as f:
                                project_data = json.load(f)
                                projects.append({
                                    "project_id": project_data.get("project_id"),
                                    "project_name": project_data.get("project_name"),
                                    "slide_count": len(project_data.get("slides", [])),
                                    "created_at": project_data.get("created_at"),
                                    "updated_at": project_data.get("updated_at")
                                })
                        except Exception:
                            continue  # 跳过损坏的项目文件
        
        return {
            "success": True,
            "projects": projects
        }
        
    except Exception as e:
        raise StorageException(f"获取PPT项目列表失败: {str(e)}")

@router.delete("/ppt/delete/{project_id}")
async def delete_ppt_project(
    project_id: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """删除PPT项目"""
    
    try:
        import shutil
        
        # 删除正常项目目录
        project_dir = Path("ppt_projects") / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)
        
        # 删除自动保存目录
        auto_save_dir = Path("ppt_projects") / "auto_saves" / project_id
        if auto_save_dir.exists():
            shutil.rmtree(auto_save_dir)
        
        return {
            "success": True,
            "message": "项目删除成功",
            "project_id": project_id
        }
        
    except Exception as e:
        raise StorageException(f"删除PPT项目失败: {str(e)}")
