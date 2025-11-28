"""
项目管理系统 - PPT项目和工作流的统一管理
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from app.utils.logger import get_logger
from app.utils.file_manager import FileManager
from core.workflow_persistence import WorkflowPersistenceManager

@dataclass
class PPTProject:
    """PPT项目数据模型"""
    project_id: str
    title: str
    description: str = ""
    slides_data: Optional[Dict[str, Any]] = None
    slides_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    last_opened: str = ""
    is_active: bool = True
    project_path: str = ""
    pptist_data: Optional[Dict[str, Any]] = None
    auto_save_enabled: bool = True
    workflow_executions: Optional[List[str]] = None  # 工作流执行ID列表
    
    def __post_init__(self):
        if self.workflow_executions is None:
            self.workflow_executions = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

class ProjectManager:
    """项目管理器"""
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        if workspace_dir is None:
            workspace_dir = Path("projects_workspace")
        
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        # 项目索引文件
        self.projects_index_file = self.workspace_dir / "projects_index.json"
        
        self.logger = get_logger(__name__, self.workspace_dir / "logs")
        
        # 初始化项目索引
        self._init_projects_index()
    
    def _init_projects_index(self):
        """初始化项目索引文件"""
        if not self.projects_index_file.exists():
            self._save_projects_index({})
    
    def _load_projects_index(self) -> Dict[str, Any]:
        """加载项目索引"""
        try:
            if self.projects_index_file.exists():
                with open(self.projects_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"加载项目索引失败: {e}")
            return {}
    
    def _save_projects_index(self, index_data: Dict[str, Any]):
        """保存项目索引"""
        try:
            with open(self.projects_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存项目索引失败: {e}")
    
    def create_project(self, title: str, description: str = "", 
                      slides_data: Optional[Dict[str, Any]] = None,
                      pptist_data: Optional[Dict[str, Any]] = None) -> PPTProject:
        """创建新项目"""
        project_id = str(uuid.uuid4())
        
        # 创建项目目录
        project_dir = self.workspace_dir / project_id
        project_dir.mkdir(exist_ok=True)
        
        # 创建项目子目录
        for subdir in ["slides", "scripts", "audio", "video_clips", "subtitles", "final", "logs"]:
            (project_dir / subdir).mkdir(exist_ok=True)
        
        # 创建项目对象
        project = PPTProject(
            project_id=project_id,
            title=title,
            description=description,
            slides_data=slides_data,
            slides_count=len(slides_data.get("slides", [])) if slides_data else 0,
            project_path=str(project_dir),
            pptist_data=pptist_data
        )
        
        # 保存项目数据
        self._save_project_data(project)
        
        # 更新项目索引
        self._update_project_index(project)
        
        # 如果有PPTist数据，保存到项目目录
        if pptist_data:
            self._save_pptist_data(project_dir, pptist_data)
        
        # 如果有slides数据，保存slides metadata
        if slides_data:
            self._save_slides_metadata(project_dir, slides_data)
        
        self.logger.info(f"创建项目成功: {title} ({project_id})")
        return project
    
    def load_project(self, project_id: str) -> Optional[PPTProject]:
        """加载项目"""
        project_dir = self.workspace_dir / project_id
        project_file = project_dir / "project.json"
        
        if not project_file.exists():
            return None
        
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            project = PPTProject(**data)
            
            # 更新最后打开时间
            project.last_opened = datetime.now().isoformat()
            self._save_project_data(project)
            
            return project
            
        except Exception as e:
            self.logger.error(f"加载项目失败: {e}")
            return None
    
    def save_project(self, project: PPTProject) -> bool:
        """保存项目"""
        try:
            project.updated_at = datetime.now().isoformat()
            self._save_project_data(project)
            self._update_project_index(project)
            return True
        except Exception as e:
            self.logger.error(f"保存项目失败: {e}")
            return False
    
    def _save_project_data(self, project: PPTProject):
        """保存项目数据到文件"""
        project_dir = Path(project.project_path)
        project_file = project_dir / "project.json"
        
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(project), f, ensure_ascii=False, indent=2)
    
    def _update_project_index(self, project: PPTProject):
        """更新项目索引"""
        index_data = self._load_projects_index()
        
        index_data[project.project_id] = {
            "title": project.title,
            "description": project.description,
            "slides_count": project.slides_count,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "last_opened": project.last_opened,
            "is_active": project.is_active,
            "project_path": project.project_path
        }
        
        self._save_projects_index(index_data)
    
    def list_projects(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """获取项目列表"""
        index_data = self._load_projects_index()
        projects = []
        
        for project_id, project_info in index_data.items():
            if active_only and not project_info.get("is_active", True):
                continue
            
            # 加载完整项目信息
            project = self.load_project(project_id)
            if project:
                # 添加工作流执行统计信息
                workflow_manager = WorkflowPersistenceManager(Path(project.project_path))
                executions = workflow_manager.list_project_executions(project.title)
                
                project_info.update({
                    "project_id": project_id,
                    "workflow_count": len(executions),
                    "last_workflow_status": executions[0].workflow_status.value if executions else None,
                    "last_workflow_time": executions[0].start_time if executions else None
                })
                
                projects.append(project_info)
        
        # 按最后更新时间排序
        projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return projects
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目（软删除）"""
        project = self.load_project(project_id)
        if not project:
            return False
        
        try:
            project.is_active = False
            self._save_project_data(project)
            self._update_project_index(project)
            self.logger.info(f"项目已删除: {project.title}")
            return True
        except Exception as e:
            self.logger.error(f"删除项目失败: {e}")
            return False
    
    def duplicate_project(self, project_id: str, new_title: str) -> Optional[PPTProject]:
        """复制项目"""
        original_project = self.load_project(project_id)
        if not original_project:
            return None
        
        try:
            # 创建新项目
            new_project = self.create_project(
                title=new_title,
                description=f"复制自: {original_project.title}",
                slides_data=original_project.slides_data,
                pptist_data=original_project.pptist_data
            )
            
            # 复制文件
            original_dir = Path(original_project.project_path)
            new_dir = Path(new_project.project_path)
            
            # 复制slides文件
            if (original_dir / "slides").exists():
                import shutil
                shutil.copytree(original_dir / "slides", new_dir / "slides", dirs_exist_ok=True)
            
            self.logger.info(f"项目复制成功: {original_project.title} -> {new_title}")
            return new_project
            
        except Exception as e:
            self.logger.error(f"复制项目失败: {e}")
            return None
    
    def update_project_slides(self, project_id: str, slides_data: Dict[str, Any]) -> bool:
        """更新项目的PPT数据"""
        project = self.load_project(project_id)
        if not project:
            return False
        
        try:
            project.slides_data = slides_data
            project.slides_count = len(slides_data.get("slides", []))
            
            # 保存slides metadata到项目目录
            self._save_slides_metadata(Path(project.project_path), slides_data)
            
            return self.save_project(project)
            
        except Exception as e:
            self.logger.error(f"更新项目PPT数据失败: {e}")
            return False
    
    def update_project_pptist_data(self, project_id: str, pptist_data: Dict[str, Any]) -> bool:
        """更新项目的PPTist数据"""
        project = self.load_project(project_id)
        if not project:
            return False
        
        try:
            project.pptist_data = pptist_data
            
            # 保存PPTist数据到项目目录
            self._save_pptist_data(Path(project.project_path), pptist_data)
            
            return self.save_project(project)
            
        except Exception as e:
            self.logger.error(f"更新项目PPTist数据失败: {e}")
            return False
    
    def _save_pptist_data(self, project_dir: Path, pptist_data: Dict[str, Any]):
        """保存PPTist数据到项目目录"""
        pptist_file = project_dir / "pptist_data.json"
        
        # 添加详细日志
        slides_count = len(pptist_data.get("slides", []))
        self.logger.info(f"💾 正在保存PPTist数据到文件: {pptist_file}")
        self.logger.info(f"📊 PPTist数据包含 {slides_count} 个slides")
        if slides_count > 0:
            first_slide_id = pptist_data["slides"][0].get("id", "unknown")
            self.logger.info(f"🎯 第一个slide ID: {first_slide_id}")
        
        with open(pptist_file, 'w', encoding='utf-8') as f:
            json.dump(pptist_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ PPTist数据已成功写入文件: {pptist_file}")
        
        # 验证写入的文件内容
        with open(pptist_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            saved_slides_count = len(saved_data.get("slides", []))
            self.logger.info(f"🔍 验证：文件中的slides数量 = {saved_slides_count}")
            if saved_slides_count != slides_count:
                self.logger.error(f"❌ 数据不一致！预期: {slides_count}, 实际: {saved_slides_count}")
    
    def _save_slides_metadata(self, project_dir: Path, slides_data: Dict[str, Any]):
        """保存slides metadata到项目目录"""
        slides_dir = project_dir / "slides"
        slides_dir.mkdir(exist_ok=True)
        
        metadata_file = slides_dir / "slides_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(slides_data, f, ensure_ascii=False, indent=2)
    
    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """获取项目统计信息"""
        project = self.load_project(project_id)
        if not project:
            return {}
        
        project_dir = Path(project.project_path)
        workflow_manager = WorkflowPersistenceManager(project_dir)
        executions = workflow_manager.list_project_executions(project.title)
        
        # 读取最新的pptist_data
        pptist_file = project_dir / "pptist_data.json"
        if pptist_file.exists():
            try:
                with open(pptist_file, 'r', encoding='utf-8') as f:
                    pptist_data = json.load(f)
                # 更新项目的pptist_data和slides_count
                project.pptist_data = pptist_data
                project.slides_count = len(pptist_data.get("slides", []))
                self.logger.info(f"📊 从pptist_data.json更新slides_count: {project.slides_count}")
            except Exception as e:
                self.logger.error(f"读取pptist_data.json失败: {e}")
        
        # 读取最新的slides_data
        slides_metadata_file = project_dir / "slides" / "slides_metadata.json"
        if slides_metadata_file.exists():
            try:
                with open(slides_metadata_file, 'r', encoding='utf-8') as f:
                    slides_data = json.load(f)
                # 更新项目的slides_data
                project.slides_data = slides_data
                self.logger.info(f"📊 从slides_metadata.json更新数据")
            except Exception as e:
                self.logger.error(f"读取slides_metadata.json失败: {e}")
        
        # 统计工作流执行情况
        workflow_stats = {
            "total_executions": len(executions),
            "completed_executions": len([e for e in executions if e.workflow_status.value == "completed"]),
            "failed_executions": len([e for e in executions if e.workflow_status.value == "failed"]),
            "running_executions": len([e for e in executions if e.workflow_status.value == "running"])
        }
        
        # 统计项目文件
        file_stats = {
            "slides_count": len(list((project_dir / "slides").glob("*.png"))) if (project_dir / "slides").exists() else 0,
            "audio_files": len(list((project_dir / "audios").glob("*.wav"))) if (project_dir / "audios").exists() else 0,
            "video_files": len(list((project_dir / "video_clips").glob("*.mp4"))) if (project_dir / "video_clips").exists() else 0,
            "subtitle_files": len(list((project_dir / "subtitles").glob("*.srt"))) if (project_dir / "subtitles").exists() else 0
        }
        
        return {
            "project_info": asdict(project),
            "workflow_statistics": workflow_stats,
            "file_statistics": file_stats,
            "last_execution": asdict(executions[0]) if executions else None
        }
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """搜索项目"""
        all_projects = self.list_projects(active_only=True)
        
        if not query:
            return all_projects
        
        query = query.lower()
        filtered_projects = []
        
        for project in all_projects:
            if (query in project.get("title", "").lower() or 
                query in project.get("description", "").lower()):
                filtered_projects.append(project)
        
        return filtered_projects

