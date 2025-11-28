"""
文件管理器
提供文件操作的统一接口
"""
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FileManager:
    """文件管理器类"""
    
    def __init__(self, base_path: str | Path = "."):
        """
        初始化文件管理器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        
        # 定义项目目录结构
        self.slides_dir = self.base_path / "slides"
        self.audio_dir = self.base_path / "audios"  # TTS生成的音频
        self.temp_dir = self.base_path / "temp"
        self.subtitles_dir = self.base_path / "subtitles"
        self.video_clips_dir = self.base_path / "video_clips"
        self.final_dir = self.base_path / "final"
        
    def ensure_dir(self, path: str | Path) -> Path:
        """
        确保目录存在
        
        Args:
            path: 目录路径
            
        Returns:
            Path对象
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    def save_json(self, data: Dict[str, Any], file_path: str | Path) -> bool:
        """
        保存JSON数据到文件
        
        Args:
            data: 要保存的数据
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            file_path = Path(file_path)
            self.ensure_dir(file_path.parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON数据已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            return False
    
    def load_json(self, file_path: str | Path) -> Optional[Dict[str, Any]]:
        """
        从文件加载JSON数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            加载的数据，失败时返回None
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"JSON文件不存在: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"JSON数据已从文件加载: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            return None
    
    def copy_file(self, src: str | Path, dst: str | Path) -> bool:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否复制成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            self.ensure_dir(dst_path.parent)
            shutil.copy2(src_path, dst_path)
            
            logger.info(f"文件已复制: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return False
    
    def move_file(self, src: str | Path, dst: str | Path) -> bool:
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否移动成功
        """
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            self.ensure_dir(dst_path.parent)
            shutil.move(str(src_path), str(dst_path))
            
            logger.info(f"文件已移动: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            logger.error(f"移动文件失败: {e}")
            return False
    
    def delete_file(self, file_path: str | Path) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否删除成功
        """
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"文件已删除: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在: {file_path}")
                return False
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    def list_files(self, directory: str | Path, pattern: str = "*") -> List[Path]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件模式
            
        Returns:
            文件路径列表
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"目录不存在: {dir_path}")
                return []
            
            files = list(dir_path.glob(pattern))
            logger.info(f"在目录 {dir_path} 中找到 {len(files)} 个文件")
            return files
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    def get_file_size(self, file_path: str | Path) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            file_path = Path(file_path)
            if file_path.exists():
                return file_path.stat().st_size
            else:
                logger.warning(f"文件不存在: {file_path}")
                return 0
        except Exception as e:
            logger.error(f"获取文件大小失败: {e}")
            return 0
    
    def create_directory_structure(self):
        """创建项目目录结构"""
        try:
            self.ensure_dir(self.slides_dir)
            self.ensure_dir(self.audio_dir)  # audios/
            self.ensure_dir(self.temp_dir)
            self.ensure_dir(self.subtitles_dir)
            self.ensure_dir(self.video_clips_dir)
            self.ensure_dir(self.final_dir)
            logger.info("项目目录结构创建完成")
        except Exception as e:
            logger.error(f"创建目录结构失败: {e}")
    
    def save_project_metadata(self, metadata: Dict[str, Any], filename: str = "project_metadata.json"):
        """保存项目元数据"""
        metadata_path = self.base_path / filename
        return self.save_json(metadata, metadata_path)
    
    def load_project_metadata(self, filename: str = "project_metadata.json") -> Optional[Dict[str, Any]]:
        """加载项目元数据"""
        metadata_path = self.base_path / filename
        return self.load_json(metadata_path)
    
    def save_slides_metadata(self, slides_data: Dict[str, Any], filename: str = "slides_metadata.json"):
        """保存幻灯片元数据"""
        slides_path = self.base_path / filename
        return self.save_json(slides_data, slides_path)
    
    def load_slides_metadata(self, filename: str = "slides_metadata.json") -> Optional[Dict[str, Any]]:
        """加载幻灯片元数据"""
        # 首先尝试从slides目录加载
        slides_path = self.slides_dir / filename
        if slides_path.exists():
            return self.load_json(slides_path)
        
        # 如果slides目录没有，尝试从base_path加载
        base_path = self.base_path / filename
        return self.load_json(base_path)
    
    def save_scripts_metadata(self, scripts_data: Dict[str, Any], filename: str = "scripts_metadata.json"):
        """保存脚本元数据"""
        scripts_path = self.base_path / filename
        return self.save_json(scripts_data, scripts_path)
    
    def load_scripts_metadata(self, filename: str = "scripts_metadata.json") -> Optional[Dict[str, Any]]:
        """加载脚本元数据"""
        scripts_path = self.base_path / filename
        return self.load_json(scripts_path)
    
    def save_audio_metadata(self, audio_data: Dict[str, Any], filename: str = "audio_metadata.json"):
        """保存音频元数据"""
        audio_path = self.base_path / filename
        return self.save_json(audio_data, audio_path)
    
    def load_audio_metadata(self, filename: str = "audio_metadata.json") -> Optional[Dict[str, Any]]:
        """加载音频元数据"""
        audio_path = self.base_path / filename
        return self.load_json(audio_path)
    
    def save_video_metadata(self, video_data: Dict[str, Any], filename: str = "video_metadata.json"):
        """保存视频元数据"""
        video_path = self.base_path / filename
        return self.save_json(video_data, video_path)
    
    def load_video_metadata(self, filename: str = "video_metadata.json") -> Optional[Dict[str, Any]]:
        """加载视频元数据"""
        video_path = self.base_path / filename
        return self.load_json(video_path)
    
    def save_subtitles_metadata(self, subtitles_data: Dict[str, Any], filename: str = "subtitles_metadata.json"):
        """保存字幕元数据"""
        subtitles_path = self.base_path / filename
        return self.save_json(subtitles_data, subtitles_path)
    
    def load_subtitles_metadata(self, filename: str = "subtitles_metadata.json") -> Optional[Dict[str, Any]]:
        """加载字幕元数据"""
        subtitles_path = self.base_path / filename
        return self.load_json(subtitles_path)
    
    def save_merge_metadata(self, merge_data: Dict[str, Any], filename: str = "merge_metadata.json"):
        """保存合并元数据"""
        merge_path = self.base_path / filename
        return self.save_json(merge_data, merge_path)
    
    def load_merge_metadata(self, filename: str = "merge_metadata.json") -> Optional[Dict[str, Any]]:
        """加载合并元数据"""
        merge_path = self.base_path / filename
        return self.load_json(merge_path)