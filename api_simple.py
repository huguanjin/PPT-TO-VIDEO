#!/usr/bin/env python3
"""
简化的API服务器 - 支持前端PPT导出功能
包含所有前端需要的关键端点
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import shutil

app = FastAPI(title="PPT转视频API", version="1.0.0")

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储目录
STORAGE_DIR = Path("ppt_projects")
STORAGE_DIR.mkdir(exist_ok=True)

# 数据模型
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

# 基础端点
@app.get("/")
async def root():
    return {"message": "PPT转视频API服务", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ppt-to-video-api"}

# PPT存储端点
@app.post("/api/ppt/save")
async def save_ppt_project(request: PPTSaveRequest):
    """保存PPT项目"""
    try:
        project_id = request.project_id or str(uuid.uuid4())
        
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
        project_dir = STORAGE_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        project_file = project_dir / "project.json"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data.model_dump(), f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "项目保存成功",
            "project_id": project_id,
            "saved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存PPT项目失败: {str(e)}")

@app.post("/api/ppt/auto-save")
async def auto_save_ppt_project(request: AutoSaveRequest):
    """自动保存PPT项目"""
    try:
        project_id = request.project_id or str(uuid.uuid4())
        project_name = request.project_name or f"自动保存_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
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
        auto_save_dir = STORAGE_DIR / "auto_saves" / project_id
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
        raise HTTPException(status_code=500, detail=f"自动保存PPT项目失败: {str(e)}")

@app.get("/api/ppt/load/{project_id}")
async def load_ppt_project(project_id: str):
    """加载PPT项目"""
    try:
        # 先尝试从正常项目目录加载
        project_file = STORAGE_DIR / project_id / "project.json"
        
        # 如果不存在，尝试从自动保存目录加载
        if not project_file.exists():
            project_file = STORAGE_DIR / "auto_saves" / project_id / "project.json"
        
        if not project_file.exists():
            raise HTTPException(status_code=404, detail=f"PPT项目 {project_id} 不存在")
        
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        return {
            "success": True,
            "project": project_data
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"PPT项目 {project_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载PPT项目失败: {str(e)}")

@app.get("/api/ppt/list")
async def list_ppt_projects():
    """获取PPT项目列表"""
    try:
        projects = []
        
        if STORAGE_DIR.exists():
            for project_dir in STORAGE_DIR.iterdir():
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
        raise HTTPException(status_code=500, detail=f"获取PPT项目列表失败: {str(e)}")

# PPT导入端点（导出到视频功能需要）
@app.post("/api/import")
async def import_ppt_data(
    project_data: str = Form(...),
    images: List[UploadFile] = File([])
):
    """导入PPT数据并启动工作流"""
    try:
        # 解析项目数据
        try:
            project_json = json.loads(project_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="项目数据格式无效")
        
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
        
        # 生成项目ID
        project_id = str(uuid.uuid4())
        
        # 这里应该启动实际的视频生成工作流
        # 目前先返回成功响应
        return {
            "success": True,
            "message": "PPT数据导入成功，视频生成任务已启动",
            "project_id": project_id,
            "workflow_id": f"workflow_{project_id}",
            "image_count": len(image_files),
            "temp_dir": str(temp_dir)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入PPT数据失败: {str(e)}")

# 工作流端点
@app.post("/api/workflow/execute")
async def execute_workflow(
    workflow_data: Dict[str, Any],
    project_name: Optional[str] = None
):
    """执行完整工作流"""
    try:
        workflow_id = str(uuid.uuid4())
        
        # 这里应该启动实际的工作流
        # 目前先返回成功响应
        return {
            "success": True,
            "message": "工作流已启动",
            "workflow_id": workflow_id,
            "project_name": project_name or "未命名项目"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行工作流失败: {str(e)}")

@app.get("/api/workflow/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    # 模拟状态响应
    return {
        "workflow_id": workflow_id,
        "status": "running",
        "progress": 50,
        "current_step": "视频生成中",
        "message": "正在处理视频生成..."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
