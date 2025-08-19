"""
PPTist导入API接口
提供Web API接口接收PPTist导出的数据
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from typing import List, Dict, Any, Optional
import json
import base64
import asyncio
import time
from datetime import datetime
from pathlib import Path

from core.step01_pptist_importer import PPTistImporter, PPTistImportResult
from utils.logger import get_logger
from utils.task_manager import TaskManager, TaskStatus

logger = get_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="PPT转视频工具 - PPTist导入API",
    description="接收PPTist导出数据并集成到视频生成工作流",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局任务管理器
PROJECT_DIR = Path(__file__).parent
task_manager = TaskManager(PROJECT_DIR)

# 异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger.error(f"请求验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "请求参数验证失败",
            "errors": exc.errors(),
            "detail": "请检查请求参数格式"
        }
    )

@app.get("/")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "message": "PPTist Import API is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/pptist/import")
async def import_pptist_data(
    background_tasks: BackgroundTasks,
    project_name: str = Form(..., description="项目名称"),
    json_data: str = Form(..., description="PPTist导出的JSON数据"),
    images: List[UploadFile] = File(..., description="幻灯片图片文件列表")
):
    """
    接收PPTist导出数据并保存到指定目录
    
    Args:
        project_name: 项目名称，用于创建输出目录
        json_data: PPTist导出的JSON字符串
        images: 幻灯片图片文件列表
    
    Returns:
        导入结果信息
    """
    try:
        logger.info(f"接收PPTist导入请求，项目名称: {project_name}")
        logger.info(f"接收到的图片文件数量: {len(images)}")
        
        # 验证项目名称
        if not project_name or not project_name.strip():
            raise HTTPException(status_code=400, detail="项目名称不能为空")
        
        # 验证图片文件
        if not images:
            raise HTTPException(status_code=400, detail="至少需要一个图片文件")
        
        # 验证JSON数据
        try:
            pptist_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON数据解析失败: {e}")
            raise HTTPException(status_code=400, detail=f"JSON数据格式错误: {str(e)}")
        
        # 清理项目名称
        clean_project_name = "".join(c for c in project_name if c.isalnum() or c in "._-")
        if not clean_project_name:
            clean_project_name = f"pptist_project_{int(time.time())}"
        
        # 检查文件类型
        for img in images:
            if not img.content_type or not img.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件 {img.filename} 不是有效的图片格式"
                )
        
        # 处理图片数据
        images_data = []
        for img_file in images:
            try:
                content = await img_file.read()
                base64_data = base64.b64encode(content).decode('utf-8')
                images_data.append({
                    "filename": img_file.filename,
                    "data": f"data:{img_file.content_type};base64,{base64_data}",
                    "size": len(content)
                })
                logger.info(f"处理图片: {img_file.filename} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"处理图片文件 {img_file.filename} 失败: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"处理图片文件 {img_file.filename} 失败"
                )
        
        # 创建导入器并执行导入
        importer = PPTistImporter(clean_project_name)
        
        # 异步执行导入任务
        task_id = f"pptist_import_{clean_project_name}_{int(time.time())}"
        
        async def import_task():
            """异步导入任务"""
            try:
                def progress_callback(progress: int):
                    # TaskManager暂不支持进度跟踪，记录到日志
                    logger.info(f"PPTist导入进度: {progress}%")
                
                result = await importer.import_pptist_data(
                    pptist_data, 
                    images_data,
                    progress_callback
                )
                
                end_time = datetime.now()
                task_manager.update_task_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    end_time=end_time.isoformat(),
                    result={
                        "result": result,
                        "success": result.success
                    }
                )
                
                return result
                
            except Exception as e:
                logger.error(f"导入任务失败: {e}")
                end_time = datetime.now()
                task_manager.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    end_time=end_time.isoformat(),
                    error_msg=str(e)
                )
                raise
        
        # 启动后台任务
        start_time = datetime.now()
        task_manager.update_task_status(
            task_id, 
            TaskStatus.RUNNING, 
            start_time=start_time.isoformat()
        )
        background_tasks.add_task(import_task)
        
        return JSONResponse({
            "success": True,
            "message": "PPTist数据导入任务已启动",
            "data": {
                "task_id": task_id,
                "project_name": clean_project_name,
                "slides_count": len(pptist_data.get("slides", [])),
                "images_count": len(images_data),
                "status": "processing"
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPTist导入API异常: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@app.get("/api/pptist/import/status/{task_id}")
async def get_import_status(task_id: str):
    """
    获取导入任务状态
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务状态信息
    """
    try:
        task_status = task_manager.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return JSONResponse({
            "success": True,
            "data": {
                "task_id": task_id,
                "status": task_status.status.value,
                "progress": task_status.progress,
                "message": task_status.message,
                "result": task_status.result,
                "created_at": task_status.created_at.isoformat(),
                "updated_at": task_status.updated_at.isoformat()
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pptist/projects")
async def list_imported_projects():
    """
    获取已导入的PPTist项目列表
    
    Returns:
        项目列表
    """
    try:
        output_dir = Path("output")
        projects = []
        
        if output_dir.exists():
            for project_dir in output_dir.iterdir():
                if project_dir.is_dir():
                    # 检查是否是PPTist导入的项目
                    metadata_file = project_dir / "project_metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            if metadata.get("source") == "PPTist":
                                projects.append({
                                    "project_name": project_dir.name,
                                    "title": metadata.get("import_info", {}).get("title", ""),
                                    "slides_count": metadata.get("import_info", {}).get("total_slides", 0),
                                    "imported_at": metadata.get("import_info", {}).get("imported_at", ""),
                                    "status": "ready" if metadata.get("processing_ready") else "incomplete"
                                })
                        except Exception as e:
                            logger.warning(f"读取项目元数据失败 {project_dir.name}: {e}")
        
        return JSONResponse({
            "success": True,
            "data": {
                "projects": projects,
                "total_count": len(projects)
            }
        })
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pptist/project/{project_name}")
async def get_project_info(project_name: str):
    """
    获取特定项目的详细信息
    
    Args:
        project_name: 项目名称
    
    Returns:
        项目详细信息
    """
    try:
        importer = PPTistImporter(project_name)
        status = importer.get_import_status()
        
        if status["status"] == "not_imported":
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 读取详细信息
        metadata = importer.file_manager.load_project_metadata()
        slides_metadata = importer.file_manager.load_slides_metadata()
        
        return JSONResponse({
            "success": True,
            "data": {
                "project_info": metadata,
                "slides_info": slides_metadata,
                "status": status
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/pptist/project/{project_name}")
async def delete_project(project_name: str):
    """
    删除指定的PPTist项目
    
    Args:
        project_name: 项目名称
    
    Returns:
        删除结果
    """
    try:
        import shutil
        
        project_dir = Path("output") / project_name
        
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 删除项目目录
        shutil.rmtree(project_dir)
        
        logger.info(f"删除PPTist项目: {project_name}")
        
        return JSONResponse({
            "success": True,
            "message": f"项目 {project_name} 已成功删除"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "PPT转视频工具 - PPTist导入API",
        "version": "1.0.0",
        "description": "接收PPTist导出数据并集成到视频生成工作流",
        "endpoints": {
            "import": "/api/pptist/import",
            "status": "/api/pptist/import/status/{task_id}",
            "projects": "/api/pptist/projects",
            "project_info": "/api/pptist/project/{project_name}",
            "delete_project": "/api/pptist/project/{project_name}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    import time
    
    logger.info("启动PPTist导入API服务...")
    uvicorn.run(
        "api_pptist_import:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
