"""
存储服务层
"""
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from datetime import datetime
import shutil

from .base import BaseService, ServiceResult

class StorageService(BaseService):
    """存储服务管理器"""
    
    def _initialize(self) -> None:
        """初始化存储服务"""
        self.base_path = Path(__file__).parent.parent.parent
        self.output_path = self.base_path / "output"
        self.uploads_path = self.base_path / "uploads"
        
        # 确保目录存在
        self.output_path.mkdir(exist_ok=True)
        self.uploads_path.mkdir(exist_ok=True)
        
        self.logger.info("存储服务初始化完成")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            output_size = sum(f.stat().st_size for f in self.output_path.rglob('*') if f.is_file())
            uploads_size = sum(f.stat().st_size for f in self.uploads_path.rglob('*') if f.is_file())
            
            return {
                "service": "Storage",
                "status": "healthy",
                "output_path": str(self.output_path),
                "uploads_path": str(self.uploads_path),
                "output_size_mb": round(output_size / (1024 * 1024), 2),
                "uploads_size_mb": round(uploads_size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {
                "service": "Storage",
                "status": "error",
                "error": str(e)
            }
    
    def save_file(self, file_data: bytes, filename: str, 
                  directory: str = "uploads") -> ServiceResult:
        """保存文件"""
        try:
            if directory == "uploads":
                target_dir = self.uploads_path
            elif directory == "output":
                target_dir = self.output_path
            else:
                target_dir = self.base_path / directory
            
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            self.logger.info(f"文件已保存: {file_path}")
            
            return ServiceResult.success_result({
                "file_path": str(file_path),
                "filename": filename,
                "size": len(file_data),
                "directory": directory
            })
            
        except Exception as e:
            self.logger.error(f"保存文件失败: {e}")
            return ServiceResult.error_result(f"保存文件失败: {e}")
    
    def get_file(self, filename: str, directory: str = "uploads") -> ServiceResult:
        """获取文件"""
        try:
            if directory == "uploads":
                target_dir = self.uploads_path
            elif directory == "output":
                target_dir = self.output_path
            else:
                target_dir = self.base_path / directory
            
            file_path = target_dir / filename
            
            if not file_path.exists():
                return ServiceResult.error_result(f"文件不存在: {filename}", 404)
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            return ServiceResult.success_result({
                "file_data": file_data,
                "filename": filename,
                "size": len(file_data),
                "file_path": str(file_path)
            })
            
        except Exception as e:
            self.logger.error(f"获取文件失败: {e}")
            return ServiceResult.error_result(f"获取文件失败: {e}")
    
    def delete_file(self, filename: str, directory: str = "uploads") -> ServiceResult:
        """删除文件"""
        try:
            if directory == "uploads":
                target_dir = self.uploads_path
            elif directory == "output":
                target_dir = self.output_path
            else:
                target_dir = self.base_path / directory
            
            file_path = target_dir / filename
            
            if not file_path.exists():
                return ServiceResult.error_result(f"文件不存在: {filename}", 404)
            
            file_path.unlink()
            self.logger.info(f"文件已删除: {file_path}")
            
            return ServiceResult.success_result({
                "filename": filename,
                "deleted": True
            })
            
        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
            return ServiceResult.error_result(f"删除文件失败: {e}")
    
    def list_files(self, directory: str = "uploads", 
                   pattern: str = "*") -> ServiceResult:
        """列出文件"""
        try:
            if directory == "uploads":
                target_dir = self.uploads_path
            elif directory == "output":
                target_dir = self.output_path
            else:
                target_dir = self.base_path / directory
            
            if not target_dir.exists():
                return ServiceResult.success_result([])
            
            files = []
            for file_path in target_dir.glob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": str(file_path.relative_to(self.base_path))
                    })
            
            # 按修改时间排序
            files.sort(key=lambda x: x["modified"], reverse=True)
            
            return ServiceResult.success_result(files)
            
        except Exception as e:
            self.logger.error(f"列出文件失败: {e}")
            return ServiceResult.error_result(f"列出文件失败: {e}")
    
    def create_project_directory(self, project_name: str) -> ServiceResult:
        """创建项目目录"""
        try:
            # 生成唯一的项目目录名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_dir_name = f"{project_name}_{timestamp}"
            project_path = self.output_path / project_dir_name
            
            # 创建项目目录结构
            directories = [
                "slides",      # 幻灯片图片
                "audio",       # 音频文件
                "videos",      # 视频文件
                "subtitles",   # 字幕文件
                "final"        # 最终输出
            ]
            
            for dir_name in directories:
                (project_path / dir_name).mkdir(parents=True, exist_ok=True)
            
            # 创建项目元数据文件
            metadata = {
                "project_name": project_name,
                "created_time": datetime.now().isoformat(),
                "project_id": project_dir_name,
                "status": "created",
                "directories": directories
            }
            
            metadata_path = project_path / "project_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"项目目录已创建: {project_path}")
            
            return ServiceResult.success_result({
                "project_id": project_dir_name,
                "project_path": str(project_path),
                "metadata": metadata
            })
            
        except Exception as e:
            self.logger.error(f"创建项目目录失败: {e}")
            return ServiceResult.error_result(f"创建项目目录失败: {e}")
    
    def get_project_info(self, project_id: str) -> ServiceResult:
        """获取项目信息"""
        try:
            project_path = self.output_path / project_id
            metadata_path = project_path / "project_metadata.json"
            
            if not project_path.exists():
                return ServiceResult.error_result(f"项目不存在: {project_id}", 404)
            
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {"project_id": project_id}
            
            # 计算项目大小
            project_size = sum(f.stat().st_size for f in project_path.rglob('*') if f.is_file())
            
            metadata.update({
                "project_size_mb": round(project_size / (1024 * 1024), 2),
                "file_count": len(list(project_path.rglob('*')))
            })
            
            return ServiceResult.success_result(metadata)
            
        except Exception as e:
            self.logger.error(f"获取项目信息失败: {e}")
            return ServiceResult.error_result(f"获取项目信息失败: {e}")
    
    def cleanup_old_files(self, days: int = 7) -> ServiceResult:
        """清理旧文件"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            deleted_files = []
            deleted_size = 0
            
            for file_path in self.output_path.rglob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        file_size = file_path.stat().st_size
                        deleted_files.append(str(file_path.relative_to(self.base_path)))
                        deleted_size += file_size
                        file_path.unlink()
            
            # 删除空目录
            for dir_path in list(self.output_path.rglob('*')):
                if dir_path.is_dir() and not list(dir_path.iterdir()):
                    dir_path.rmdir()
            
            self.logger.info(f"已清理 {len(deleted_files)} 个文件，释放 {deleted_size / (1024*1024):.2f} MB")
            
            return ServiceResult.success_result({
                "deleted_files": len(deleted_files),
                "deleted_size_mb": round(deleted_size / (1024 * 1024), 2),
                "cutoff_days": days
            })
            
        except Exception as e:
            self.logger.error(f"清理文件失败: {e}")
            return ServiceResult.error_result(f"清理文件失败: {e}")
