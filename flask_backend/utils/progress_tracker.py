"""
进度跟踪工具
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.progress_file = self.project_dir / "progress.json"
        
    def initialize(self):
        """初始化进度跟踪"""
        progress_data = {
            "initialized_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "steps_completed": {
                "ppt_parsing": False,
                "script_extraction": False,
                "audio_generation": False,
                "video_generation": False,
                "subtitle_generation": False,
                "final_merge": False
            },
            "current_step": "ppt_parsing",
            "overall_progress": 0
        }
        
        self._save_progress(progress_data)
        logger.info("初始化进度跟踪")
    
    def is_step_completed(self, step_name: str) -> bool:
        """检查步骤是否已完成"""
        progress = self._load_progress()
        if not progress:
            return False
        return progress.get("steps_completed", {}).get(step_name, False)
    
    def mark_step_completed(self, step_name: str):
        """标记步骤已完成"""
        progress = self._load_progress()
        if not progress:
            self.initialize()
            progress = self._load_progress()
        
        progress["steps_completed"][step_name] = True
        progress["last_updated"] = datetime.now().isoformat()
        
        # 计算总体进度
        completed_steps = sum(1 for completed in progress["steps_completed"].values() if completed)
        total_steps = len(progress["steps_completed"])
        progress["overall_progress"] = int((completed_steps / total_steps) * 100)
        
        # 更新当前步骤
        if completed_steps < total_steps:
            remaining_steps = [step for step, completed in progress["steps_completed"].items() if not completed]
            if remaining_steps:
                progress["current_step"] = remaining_steps[0]
        else:
            progress["current_step"] = "completed"
        
        self._save_progress(progress)
        logger.info(f"标记步骤已完成: {step_name}")
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """获取进度信息"""
        return self._load_progress()
    
    def reset_progress(self):
        """重置进度"""
        if self.progress_file.exists():
            self.progress_file.unlink()
        self.initialize()
        logger.info("重置进度跟踪")
    
    def _save_progress(self, progress_data: Dict[str, Any]):
        """保存进度数据"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
            raise
    
    def _load_progress(self) -> Optional[Dict[str, Any]]:
        """加载进度数据"""
        try:
            if not self.progress_file.exists():
                return None
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载进度失败: {e}")
            return None
