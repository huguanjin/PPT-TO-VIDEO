"""
统一API入口模块
PPT转视频工作流API服务
"""
from fastapi import FastAPI, Form, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from .routers import tts_router, workflow_router, storage_router, config_router
from .middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from .exceptions import setup_exception_handlers
import logging

def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title="PPT转视频API",
        description="PPT转视频工作流API服务",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 设置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加中间件
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 设置异常处理器
    setup_exception_handlers(app)
    
    # 注册路由
    app.include_router(tts_router, prefix="/api")
    app.include_router(workflow_router, prefix="/api")
    app.include_router(storage_router, prefix="/api")
    app.include_router(config_router, prefix="/api")
    
    # 为了兼容前端的 /api/import 路径，添加别名路由
    @app.post("/api/import")
    async def import_ppt_data_alias(
        project_data: str = Form(...),
        images: List[UploadFile] = File([])
    ):
        """PPT导入接口别名（兼容性）"""
        from .dependencies import get_workflow_service
        from .routers.workflow import import_ppt_data
        
        # 调用工作流中的导入函数
        workflow_service = get_workflow_service()
        return await import_ppt_data(project_data, images, workflow_service)
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "healthy", "service": "ppt-to-video-api"}
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "PPT转视频API服务",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    return app

# 创建应用实例
app = create_app()
