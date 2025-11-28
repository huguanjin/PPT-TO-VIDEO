"""
存储服务 - 管理用户工作目录和归档
每个用户有独立的工作目录: output/{user_id}/
任务完成后归档到: history/{user_id}/{project_id}/
"""
import os
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class StorageService:
    """存储服务 - 管理用户工作目录和项目归档"""
    
    def __init__(self, base_dir: Path = None):
        """
        初始化存储服务
        
        Args:
            base_dir: 基础目录，默认为 flask_backend/
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir / "output"
        self.history_dir = self.base_dir / "history"
        
        # 确保基础目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 存储服务初始化: output={self.output_dir}, history={self.history_dir}")
    
    def get_user_work_dir(self, user_id: str) -> Path:
        """
        获取用户工作目录
        如果不存在则创建
        
        Args:
            user_id: 用户ID，匿名用户使用 'anonymous'
            
        Returns:
            用户工作目录路径
        """
        work_dir = self.output_dir / user_id
        
        if not work_dir.exists():
            self._init_work_dir_structure(work_dir)
            logger.info(f"📁 创建用户工作目录: {work_dir}")
        
        return work_dir
    
    def _init_work_dir_structure(self, work_dir: Path):
        """
        初始化工作目录结构
        创建所有必需的子目录
        """
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建标准子目录
        subdirs = [
            "slides",       # 幻灯片图片
            "scripts",      # 解说词
            "audio",        # 音频文件
            "video_clips",  # 视频片段
            "subtitles",    # 字幕文件
            "final",        # 最终视频
            "temp",         # 临时文件
            "logs",         # 日志文件
        ]
        
        for subdir in subdirs:
            (work_dir / subdir).mkdir(exist_ok=True)
    
    def get_user_history_dir(self, user_id: str) -> Path:
        """
        获取用户历史归档目录
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户历史目录路径
        """
        history_dir = self.history_dir / user_id
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir
    
    def init_work_dir(self, user_id: str, clean: bool = True) -> Path:
        """
        初始化用户工作目录
        
        Args:
            user_id: 用户ID
            clean: 是否清空现有内容
            
        Returns:
            用户工作目录路径
        """
        work_dir = self.output_dir / user_id
        
        # 如果需要清空且目录存在
        if clean and work_dir.exists():
            # 保留目录结构，只清空文件
            for item in work_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    # 清空子目录内容
                    shutil.rmtree(item)
            logger.info(f"🧹 清空用户工作目录: {work_dir}")
        
        # 重新创建目录结构
        self._init_work_dir_structure(work_dir)
        
        return work_dir
    
    def check_work_dir_busy(self, user_id: str) -> bool:
        """
        检查用户工作目录是否有进行中的项目
        
        Args:
            user_id: 用户ID
            
        Returns:
            True 如果有进行中的项目
        """
        work_dir = self.output_dir / user_id
        
        if not work_dir.exists():
            return False
        
        # 检查项目指示文件
        indicators = ["ppt_data.json", "workspace.json", "slides_metadata.json"]
        for indicator in indicators:
            if (work_dir / indicator).exists():
                return True
        
        # 检查 slides 目录是否有文件
        slides_dir = work_dir / "slides"
        if slides_dir.exists() and any(slides_dir.iterdir()):
            return True
        
        return False
    
    def get_work_dir_info(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户工作目录信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            工作目录信息字典
        """
        work_dir = self.output_dir / user_id
        
        if not work_dir.exists():
            return {
                "exists": False,
                "path": str(work_dir),
                "is_busy": False,
            }
        
        info = {
            "exists": True,
            "path": str(work_dir),
            "is_busy": self.check_work_dir_busy(user_id),
            "files": {},
        }
        
        # 统计各子目录的文件数
        for subdir in ["slides", "scripts", "audio", "video_clips", "subtitles", "final"]:
            subdir_path = work_dir / subdir
            if subdir_path.exists():
                info["files"][subdir] = len(list(subdir_path.glob("*")))
            else:
                info["files"][subdir] = 0
        
        # 检查元数据文件
        metadata_files = ["ppt_data.json", "workspace.json", "slides_metadata.json", 
                         "scripts_metadata.json", "audio_metadata.json", "video_metadata.json"]
        info["metadata"] = {f: (work_dir / f).exists() for f in metadata_files}
        
        return info
    
    def archive_project(self, user_id: str, project_name: str = None) -> str:
        """
        归档项目：将工作目录内容移动到历史目录
        
        Args:
            user_id: 用户ID
            project_name: 项目名称（可选）
            
        Returns:
            归档后的 project_id
        """
        work_dir = self.output_dir / user_id
        
        if not work_dir.exists():
            raise ValueError(f"工作目录不存在: {work_dir}")
        
        history_dir = self.get_user_history_dir(user_id)
        
        # 生成 project_id (时间戳格式)
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = history_dir / project_id
        
        # 如果没有提供项目名，尝试从 ppt_data.json 获取
        if not project_name:
            ppt_data_file = work_dir / "ppt_data.json"
            if ppt_data_file.exists():
                try:
                    with open(ppt_data_file, 'r', encoding='utf-8') as f:
                        ppt_data = json.load(f)
                        project_name = ppt_data.get("title", project_id)
                except:
                    project_name = project_id
            else:
                project_name = project_id
        
        # 移动文件到归档目录
        shutil.move(str(work_dir), str(archive_dir))
        
        # 重新创建空的工作目录
        self._init_work_dir_structure(work_dir)
        
        # 创建归档信息文件
        archive_info = {
            "project_id": project_id,
            "project_name": project_name,
            "user_id": user_id,
            "archived_at": datetime.now().isoformat(),
            "files": self._list_archive_files(archive_dir),
        }
        
        with open(archive_dir / "archive_info.json", 'w', encoding='utf-8') as f:
            json.dump(archive_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📦 项目已归档: {project_name} -> {archive_dir}")
        
        return project_id
    
    def list_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        列出用户的历史项目
        
        Args:
            user_id: 用户ID
            
        Returns:
            历史项目列表
        """
        history_dir = self.history_dir / user_id
        projects = []
        
        if not history_dir.exists():
            return projects
        
        for project_dir in sorted(history_dir.iterdir(), reverse=True):
            if project_dir.is_dir():
                archive_info_path = project_dir / "archive_info.json"
                
                if archive_info_path.exists():
                    try:
                        with open(archive_info_path, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            info['path'] = str(project_dir)
                            
                            # 检查是否有最终视频
                            final_dir = project_dir / "final"
                            if final_dir.exists():
                                videos = list(final_dir.glob("*.mp4"))
                                info['has_video'] = len(videos) > 0
                                if videos:
                                    info['video_file'] = videos[0].name
                            else:
                                info['has_video'] = False
                            
                            projects.append(info)
                    except Exception as e:
                        logger.error(f"读取归档信息失败: {archive_info_path}, {e}")
                else:
                    # 旧格式兼容
                    projects.append({
                        "project_id": project_dir.name,
                        "project_name": project_dir.name,
                        "path": str(project_dir),
                        "has_video": (project_dir / "final").exists(),
                    })
        
        return projects
    
    def get_project_video_path(self, user_id: str, project_id: str) -> Optional[Path]:
        """
        获取归档项目的视频文件路径
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            
        Returns:
            视频文件路径，如果不存在返回 None
        """
        project_dir = self.history_dir / user_id / project_id
        final_dir = project_dir / "final"
        
        if final_dir.exists():
            for video_file in final_dir.glob("*.mp4"):
                return video_file
        
        return None
    
    def delete_project(self, user_id: str, project_id: str) -> bool:
        """
        删除历史项目
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            
        Returns:
            是否成功删除
        """
        project_dir = self.history_dir / user_id / project_id
        
        if project_dir.exists():
            shutil.rmtree(project_dir)
            logger.info(f"🗑️ 删除历史项目: {project_dir}")
            return True
        
        return False
    
    def _list_archive_files(self, archive_dir: Path) -> Dict[str, List[str]]:
        """
        列出归档目录的文件
        
        Args:
            archive_dir: 归档目录路径
            
        Returns:
            各子目录的文件列表
        """
        files = {}
        for subdir in ["slides", "audio", "subtitles", "final"]:
            subdir_path = archive_dir / subdir
            if subdir_path.exists():
                files[subdir] = [f.name for f in subdir_path.iterdir() if f.is_file()]
        return files
    
    def migrate_anonymous_to_user(self, user_id: str) -> bool:
        """
        将匿名用户的工作目录迁移到登录用户
        
        Args:
            user_id: 目标用户ID
            
        Returns:
            是否成功迁移
        """
        anonymous_dir = self.output_dir / "anonymous"
        user_dir = self.output_dir / user_id
        
        if not anonymous_dir.exists() or not self.check_work_dir_busy("anonymous"):
            return False
        
        # 如果用户目录已有内容，先归档
        if user_dir.exists() and self.check_work_dir_busy(user_id):
            self.archive_project(user_id, "自动归档")
        
        # 移动匿名目录到用户目录
        if user_dir.exists():
            shutil.rmtree(user_dir)
        shutil.move(str(anonymous_dir), str(user_dir))
        
        # 重新创建匿名目录
        self._init_work_dir_structure(anonymous_dir)
        
        logger.info(f"🔄 迁移匿名工作目录到用户: {user_id}")
        return True


# 全局单例
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """获取存储服务单例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
