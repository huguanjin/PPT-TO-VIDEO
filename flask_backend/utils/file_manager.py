"""
文件管理工具
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class FileManager:
    """文件管理器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.slides_dir = self.project_dir / "slides"
        self.scripts_dir = self.project_dir / "scripts"
        self.audio_dir = self.project_dir / "audio"
        self.video_clips_dir = self.project_dir / "video_clips"
        self.subtitles_dir = self.project_dir / "subtitles"
        self.temp_dir = self.project_dir / "temp"
        self.final_dir = self.project_dir / "final"
        self.logs_dir = self.project_dir / "logs"
        
    def create_directory_structure(self):
        """创建目录结构"""
        directories = [
            self.project_dir,
            self.slides_dir,
            self.scripts_dir, 
            self.audio_dir,
            self.video_clips_dir,
            self.subtitles_dir,
            self.temp_dir,
            self.final_dir,
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {directory}")
    
    def save_json(self, data: Dict[str, Any], file_path: Path):
        """保存JSON数据"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存JSON文件: {file_path}")
        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {e}")
            raise
    
    def load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载JSON数据"""
        try:
            if not file_path.exists():
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"加载JSON文件: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            return None
    
    def save_project_metadata(self, metadata: Dict[str, Any]):
        """保存项目元数据"""
        file_path = self.project_dir / "project_metadata.json"
        self.save_json(metadata, file_path)
    
    def load_project_metadata(self) -> Optional[Dict[str, Any]]:
        """加载项目元数据"""
        file_path = self.project_dir / "project_metadata.json"
        return self.load_json(file_path)
    
    def save_slides_metadata(self, metadata: Dict[str, Any]):
        """保存幻灯片元数据"""
        file_path = self.slides_dir / "slides_metadata.json"
        self.save_json(metadata, file_path)
    
    def load_slides_metadata(self) -> Optional[Dict[str, Any]]:
        """加载幻灯片元数据"""
        file_path = self.slides_dir / "slides_metadata.json"
        return self.load_json(file_path)
    
    def save_scripts_metadata(self, metadata: Dict[str, Any]):
        """保存讲话稿元数据"""
        file_path = self.scripts_dir / "scripts_metadata.json"
        self.save_json(metadata, file_path)
        
        # 同时保存为Excel格式（可选）
        try:
            self._save_scripts_to_excel(metadata)
        except Exception as e:
            logger.warning(f"保存Excel格式失败，但不影响主要功能: {e}")
        
    def load_scripts_metadata(self) -> Optional[Dict[str, Any]]:
        """加载讲话稿元数据"""
        file_path = self.scripts_dir / "scripts_metadata.json"
        return self.load_json(file_path)
    
    def _save_scripts_to_excel(self, metadata: Dict[str, Any]):
        """
        将讲话稿数据保存为Excel格式
        """
        try:
            import pandas as pd
            
            # 准备数据
            scripts_list = []
            for script in metadata.get("scripts", []):
                scripts_list.append({
                    "页面编号": script["slide_number"],
                    "页面标题": script["slide_title"],
                    "讲话稿内容": script["script_content"],
                    "字数": script["word_count"],
                    "预估时长(秒)": script["estimated_duration_seconds"],
                    "提取时间": script["extracted_at"]
                })
            
            # 创建DataFrame
            df = pd.DataFrame(scripts_list)
            
            # 保存为Excel文件
            excel_path = self.scripts_dir / "scripts_data.xlsx"
            df.to_excel(excel_path, index=False, engine='openpyxl')
            
            logger.info(f"保存Excel文件: {excel_path}")
            
        except ImportError:
            logger.info("pandas或openpyxl未安装，跳过Excel文件生成")
        except Exception as e:
            logger.warning(f"生成Excel文件失败: {e}")
    
    def save_audio_metadata(self, metadata: Dict[str, Any]):
        """保存音频元数据"""
        file_path = self.audio_dir / "audio_metadata.json"
        self.save_json(metadata, file_path)
        
    def load_audio_metadata(self) -> Optional[Dict[str, Any]]:
        """加载音频元数据"""
        file_path = self.audio_dir / "audio_metadata.json"
        return self.load_json(file_path)
    
    def save_video_metadata(self, metadata: Dict[str, Any]):
        """保存视频元数据"""
        file_path = self.video_clips_dir / "video_metadata.json"
        self.save_json(metadata, file_path)
        
    def load_video_metadata(self) -> Optional[Dict[str, Any]]:
        """加载视频元数据"""
        file_path = self.video_clips_dir / "video_metadata.json"
        return self.load_json(file_path)
        
    def save_subtitles_metadata(self, metadata: Dict[str, Any]):
        """保存字幕元数据"""
        file_path = self.subtitles_dir / "subtitles_metadata.json"
        self.save_json(metadata, file_path)
        
    def load_subtitles_metadata(self) -> Optional[Dict[str, Any]]:
        """加载字幕元数据"""
        file_path = self.subtitles_dir / "subtitles_metadata.json"
        return self.load_json(file_path)
    
    def save_merge_metadata(self, metadata: Dict[str, Any]):
        """保存合并元数据"""
        file_path = self.final_dir / "merge_metadata.json"
        self.save_json(metadata, file_path)
        
    def load_merge_metadata(self) -> Optional[Dict[str, Any]]:
        """加载合并元数据"""
        file_path = self.final_dir / "merge_metadata.json"
        return self.load_json(file_path)
    
    def save_final_result(self, result: Dict[str, Any]):
        """保存最终结果"""
        file_path = self.final_dir / "export_info.json"
        self.save_json(result, file_path)
        
    def load_final_result(self) -> Optional[Dict[str, Any]]:
        """加载最终结果"""
        file_path = self.final_dir / "export_info.json"
        return self.load_json(file_path)
