"""
手动分割数据管理API
处理前端的换行分割数据的持久化存储
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class SplitSegment:
    """分割段落数据结构"""
    index: int
    content: str
    char_count: int
    estimated_duration: float = 0.0
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

@dataclass
class SlideSplit:
    """单个幻灯片的分割数据"""
    original_remark: str
    manual_splits: List[SplitSegment]
    split_mode: str = "manual"
    char_limit: int = 20
    last_modified: Optional[str] = None
    
    def __post_init__(self):
        if self.last_modified is None:
            self.last_modified = datetime.now().isoformat()

@dataclass
class ManualSplitData:
    """完整的手动分割数据结构"""
    project_name: str
    version: str = "1.0"
    created_at: Optional[str] = None
    splits: Optional[Dict[str, SlideSplit]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.splits is None:
            self.splits = {}

class ManualSplitManager:
    """手动分割数据管理器"""
    
    def __init__(self, base_path: str = "flask_backend/output/manual_splits"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_split_file_path(self, project_name: str) -> Path:
        """获取分割数据文件路径"""
        return self.base_path / f"{project_name}_splits.json"
    
    def load_splits(self, project_name: str) -> Optional[ManualSplitData]:
        """加载项目的分割数据"""
        file_path = self.get_split_file_path(project_name)
        
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建数据结构
            splits = {}
            for slide_id, slide_data in data.get('splits', {}).items():
                segments = [
                    SplitSegment(**seg) for seg in slide_data.get('manual_splits', [])
                ]
                splits[slide_id] = SlideSplit(
                    original_remark=slide_data.get('original_remark', ''),
                    manual_splits=segments,
                    split_mode=slide_data.get('split_mode', 'manual'),
                    char_limit=slide_data.get('char_limit', 20),
                    last_modified=slide_data.get('last_modified')
                )
            
            return ManualSplitData(
                project_name=data.get('project_name', project_name),
                version=data.get('version', '1.0'),
                created_at=data.get('created_at'),
                splits=splits
            )
            
        except Exception as e:
            print(f"Error loading splits for {project_name}: {e}")
            return None
    
    def save_splits(self, split_data: ManualSplitData) -> bool:
        """保存分割数据"""
        file_path = self.get_split_file_path(split_data.project_name)
        
        try:
            # 转换为可序列化的字典
            data = asdict(split_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving splits for {split_data.project_name}: {e}")
            return False
    
    def update_slide_splits(self, project_name: str, slide_id: str, 
                           segments: List[Dict], original_remark: str = "",
                           char_limit: int = 20) -> bool:
        """更新特定幻灯片的分割数据"""
        
        # 加载现有数据或创建新数据
        split_data = self.load_splits(project_name)
        if split_data is None:
            split_data = ManualSplitData(project_name=project_name)
        
        # 创建分割段落
        split_segments = []
        for i, seg in enumerate(segments, 1):
            split_segments.append(SplitSegment(
                index=i,
                content=seg.get('content', ''),
                char_count=seg.get('char_count', len(seg.get('content', ''))),
                estimated_duration=seg.get('estimated_duration', 0.0),
                warnings=seg.get('warnings', [])
            ))
        
        # 更新幻灯片数据
        if split_data.splits is None:
            split_data.splits = {}
        split_data.splits[slide_id] = SlideSplit(
            original_remark=original_remark,
            manual_splits=split_segments,
            char_limit=char_limit,
            last_modified=datetime.now().isoformat()
        )
        
        return self.save_splits(split_data)
    
    def get_slide_content(self, project_name: str, slide_id: str) -> Optional[List[Dict]]:
        """获取幻灯片的分割内容，用于音频生成等工作流"""
        split_data = self.load_splits(project_name)
        
        if split_data and split_data.splits and slide_id in split_data.splits:
            slide_split = split_data.splits[slide_id]
            return [
                {
                    'content': seg.content,
                    'char_count': seg.char_count,
                    'index': seg.index,
                    'estimated_duration': seg.estimated_duration
                }
                for seg in slide_split.manual_splits
            ]
        
        return None
    
    def delete_slide_splits(self, project_name: str, slide_id: str) -> bool:
        """删除特定幻灯片的分割数据"""
        split_data = self.load_splits(project_name)
        
        if split_data and split_data.splits and slide_id in split_data.splits:
            del split_data.splits[slide_id]
            return self.save_splits(split_data)
        
        return False
    
    def list_projects(self) -> List[str]:
        """列出所有有分割数据的项目"""
        projects = []
        for file_path in self.base_path.glob("*_splits.json"):
            project_name = file_path.stem.replace("_splits", "")
            projects.append(project_name)
        return projects

# 全局实例
split_manager = ManualSplitManager()