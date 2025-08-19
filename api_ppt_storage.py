#!/usr/bin/env python3
"""
PPT持久化存储API
支持PPT项目的保存、加载、自动保存等功能
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response
from pydantic import BaseModel
from pathlib import Path
import logging
import shutil

# 配置日志
logger = logging.getLogger(__name__)

# 存储配置
STORAGE_BASE_DIR = Path("ppt_projects")
STORAGE_BASE_DIR.mkdir(exist_ok=True)

class PPTProject(BaseModel):
    """PPT项目数据模型"""
    project_id: str
    project_name: str
    slides: List[Dict[str, Any]]
    theme: Dict[str, Any] = {}
    viewport_ratio: float = 16/9
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    
class PPTProjectSummary(BaseModel):
    """PPT项目摘要信息"""
    project_id: str
    project_name: str
    slide_count: int
    created_at: str
    updated_at: str
    thumbnail: Optional[str] = None

class AutoSaveRequest(BaseModel):
    """自动保存请求模型"""
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    slides: List[Dict[str, Any]] = []
    theme: Dict[str, Any] = {}
    viewport_ratio: float = 16/9
    metadata: Dict[str, Any] = {}

class PPTStorageManager:
    """PPT存储管理器"""
    
    def __init__(self, base_dir: Path = STORAGE_BASE_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True)
    
    def _get_project_dir(self, project_id: str) -> Path:
        """获取项目目录"""
        return self.base_dir / project_id
    
    def _get_project_file(self, project_id: str) -> Path:
        """获取项目文件路径"""
        return self._get_project_dir(project_id) / "project.json"
    
    async def save_project(self, project: PPTProject) -> bool:
        """保存PPT项目"""
        try:
            project_dir = self._get_project_dir(project.project_id)
            project_dir.mkdir(exist_ok=True)
            
            # 更新时间戳
            project.updated_at = datetime.now().isoformat()
            
            # 保存项目文件
            project_file = self._get_project_file(project.project_id)
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"项目 {project.project_id} 保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存项目失败: {e}")
            return False
    
    async def load_project(self, project_id: str) -> Optional[PPTProject]:
        """加载PPT项目"""
        try:
            project_file = self._get_project_file(project_id)
            if not project_file.exists():
                return None
            
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return PPTProject(**data)
            
        except Exception as e:
            logger.error(f"加载项目失败: {e}")
            return None
    
    async def list_projects(self) -> List[PPTProjectSummary]:
        """列出所有项目"""
        projects = []
        try:
            for project_dir in self.base_dir.iterdir():
                if project_dir.is_dir():
                    project_file = project_dir / "project.json"
                    if project_file.exists():
                        with open(project_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        summary = PPTProjectSummary(
                            project_id=data['project_id'],
                            project_name=data['project_name'],
                            slide_count=len(data.get('slides', [])),
                            created_at=data['created_at'],
                            updated_at=data['updated_at'],
                            thumbnail=self._get_thumbnail_path(data['project_id'])
                        )
                        projects.append(summary)
            
            # 按更新时间排序
            projects.sort(key=lambda x: x.updated_at, reverse=True)
            return projects
            
        except Exception as e:
            logger.error(f"列出项目失败: {e}")
            return []
    
    async def delete_project(self, project_id: str) -> bool:
        """删除PPT项目"""
        try:
            project_dir = self._get_project_dir(project_id)
            if project_dir.exists():
                shutil.rmtree(project_dir)
                logger.info(f"项目 {project_id} 删除成功")
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return False
    
    async def duplicate_project(self, project_id: str, new_name: str) -> Optional[str]:
        """复制项目"""
        try:
            # 加载原项目
            original_project = await self.load_project(project_id)
            if not original_project:
                return None
            
            # 创建新项目
            new_project_id = str(uuid.uuid4())
            new_project = PPTProject(
                project_id=new_project_id,
                project_name=new_name,
                slides=original_project.slides.copy(),
                theme=original_project.theme.copy(),
                viewport_ratio=original_project.viewport_ratio,
                metadata=original_project.metadata.copy(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # 保存新项目
            success = await self.save_project(new_project)
            if success:
                return new_project_id
            return None
            
        except Exception as e:
            logger.error(f"复制项目失败: {e}")
            return None
    
    def _get_thumbnail_path(self, project_id: str) -> Optional[str]:
        """获取缩略图路径"""
        thumbnail_file = self._get_project_dir(project_id) / "thumbnail.png"
        if thumbnail_file.exists():
            return f"/api/ppt/thumbnail/{project_id}"
        return None
    
    async def get_project_stats(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        try:
            projects = await self.list_projects()
            total_slides = sum(project.slide_count for project in projects)
            
            return {
                "total_projects": len(projects),
                "total_slides": total_slides,
                "storage_size": self._calculate_storage_size(),
                "last_updated": projects[0].updated_at if projects else None
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def _calculate_storage_size(self) -> str:
        """计算存储大小"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            # 转换为人类可读格式
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
        except Exception:
            return "未知"

# 创建存储管理器实例
storage_manager = PPTStorageManager()

# 创建API路由
router = APIRouter(prefix="/api/ppt", tags=["PPT存储"])

@router.post("/save")
async def save_ppt_project(project_data: Dict[str, Any]):
    """保存PPT项目"""
    try:
        # 生成项目ID（如果没有）
        if 'project_id' not in project_data or not project_data['project_id']:
            project_data['project_id'] = str(uuid.uuid4())
        
        # 设置默认项目名
        if 'project_name' not in project_data or not project_data['project_name']:
            project_data['project_name'] = f"PPT项目 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 设置时间戳
        now = datetime.now().isoformat()
        if 'created_at' not in project_data:
            project_data['created_at'] = now
        project_data['updated_at'] = now
        
        # 设置默认值
        project_data.setdefault('slides', [])
        project_data.setdefault('theme', {})
        project_data.setdefault('viewport_ratio', 16/9)
        project_data.setdefault('metadata', {})
        
        # 创建项目对象
        project = PPTProject(**project_data)
        
        # 保存项目
        success = await storage_manager.save_project(project)
        
        if success:
            return {
                "success": True,
                "message": "项目保存成功",
                "project_id": project.project_id,
                "project_name": project.project_name
            }
        else:
            raise HTTPException(status_code=500, detail="保存失败")
            
    except Exception as e:
        logger.error(f"保存项目API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/load/{project_id}")
async def load_ppt_project(project_id: str):
    """加载PPT项目"""
    try:
        project = await storage_manager.load_project(project_id)
        
        if project:
            return {
                "success": True,
                "data": project.dict()
            }
        else:
            raise HTTPException(status_code=404, detail="项目不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载项目API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_ppt_projects():
    """获取项目列表"""
    try:
        projects = await storage_manager.list_projects()
        return {
            "success": True,
            "data": [project.dict() for project in projects]
        }
        
    except Exception as e:
        logger.error(f"获取项目列表API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{project_id}")
async def delete_ppt_project(project_id: str):
    """删除PPT项目"""
    try:
        success = await storage_manager.delete_project(project_id)
        
        if success:
            return {
                "success": True,
                "message": "项目删除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="项目不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/duplicate/{project_id}")
async def duplicate_ppt_project(project_id: str, request: Dict[str, str]):
    """复制PPT项目"""
    try:
        new_name = request.get('new_name', f"副本 - {project_id[:8]}")
        new_project_id = await storage_manager.duplicate_project(project_id, new_name)
        
        if new_project_id:
            return {
                "success": True,
                "message": "项目复制成功",
                "project_id": new_project_id
            }
        else:
            raise HTTPException(status_code=404, detail="原项目不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"复制项目API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-save")
async def auto_save_ppt_project(
    request: AutoSaveRequest,
    background_tasks: BackgroundTasks
):
    """自动保存PPT项目（后台任务）"""
    try:
        # 如果没有项目ID，生成一个新的
        if not request.project_id:
            request.project_id = str(uuid.uuid4())
        
        # 构建项目数据
        now = datetime.now().isoformat()
        project_data = {
            "project_id": request.project_id,
            "project_name": request.project_name or f"自动保存 {datetime.now().strftime('%H:%M')}",
            "slides": request.slides,
            "theme": request.theme,
            "viewport_ratio": request.viewport_ratio,
            "metadata": request.metadata,
            "created_at": now,
            "updated_at": now
        }
        
        project = PPTProject(**project_data)
        
        # 添加到后台任务队列
        background_tasks.add_task(storage_manager.save_project, project)
        
        return {
            "success": True,
            "message": "自动保存任务已启动",
            "project_id": request.project_id
        }
        
    except Exception as e:
        logger.error(f"自动保存API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_storage_stats():
    """获取存储统计信息"""
    try:
        stats = await storage_manager.get_project_stats()
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取统计信息API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/thumbnail/{project_id}")
async def get_project_thumbnail(project_id: str):
    """获取项目缩略图"""
    try:
        thumbnail_path = storage_manager._get_project_dir(project_id) / "thumbnail.png"
        
        if thumbnail_path.exists():
            with open(thumbnail_path, 'rb') as f:
                content = f.read()
            return Response(content=content, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="缩略图不存在")
            
    except Exception as e:
        logger.error(f"获取缩略图API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 测试存储管理器
    import asyncio
    
    async def test():
        # 创建测试项目
        test_project = PPTProject(
            project_id=str(uuid.uuid4()),
            project_name="测试项目",
            slides=[
                {"id": "1", "content": "第一页"},
                {"id": "2", "content": "第二页"}
            ],
            theme={"color": "blue"},
            viewport_ratio=16/9,
            metadata={"author": "测试用户"},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # 保存项目
        manager = PPTStorageManager()
        success = await manager.save_project(test_project)
        print(f"保存结果: {success}")
        
        # 列出项目
        projects = await manager.list_projects()
        print(f"项目列表: {len(projects)} 个项目")
        
        for project in projects:
            print(f"  - {project.project_name} ({project.slide_count} 页)")
    
    asyncio.run(test())
