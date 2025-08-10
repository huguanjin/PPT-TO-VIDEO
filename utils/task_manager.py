"""
任务管理器 - 管理工作流任务执行状态和持久化记录
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import streamlit as st

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "未执行"
    RUNNING = "执行中"
    COMPLETED = "已完成" 
    FAILED = "执行失败"

class TaskManager:
    """任务管理器"""
    
    def __init__(self, project_dir: Path):
        """初始化任务管理器"""
        self.project_dir = project_dir
        self.task_file = project_dir / "task_records.xlsx"
        self.task_meta_file = project_dir / "task_metadata.json"
        
        # 确保项目目录存在
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化任务表结构
        self.task_columns = [
            "步骤ID", "步骤名称", "任务ID", "任务名称", "任务描述", 
            "输入文件", "输出文件", "任务状态", "开始时间", "完成时间", 
            "执行时长(秒)", "错误信息", "执行结果"
        ]
    
    def initialize_tasks(self, slides_data: List[Dict]) -> bool:
        """根据PPT解析结果初始化任务表"""
        try:
            tasks = []
            total_slides = len(slides_data)
            
            # 步骤1: PPT解析任务（已完成）
            tasks.append({
                "步骤ID": "步骤1",
                "步骤名称": "PPT解析",
                "任务ID": "parse_ppt",
                "任务名称": "PPT文件解析",
                "任务描述": f"解析PPT文件，提取{total_slides}张幻灯片",
                "输入文件": "uploaded_ppt_file",
                "输出文件": "slides/, scripts/",
                "任务状态": TaskStatus.COMPLETED.value,
                "开始时间": datetime.now().isoformat(),
                "完成时间": datetime.now().isoformat(),
                "执行时长(秒)": 0,
                "错误信息": "",
                "执行结果": f"成功解析{total_slides}张幻灯片"
            })
            
            # 步骤2: 语音合成任务
            for i, slide in enumerate(slides_data, 1):
                slide_num = slide.get('slide_number', i)
                notes = slide.get('notes_text', '')
                word_count = slide.get('notes_word_count', 0)
                
                tasks.append({
                    "步骤ID": "步骤2",
                    "步骤名称": "语音合成",
                    "任务ID": f"tts_slide_{slide_num:03d}",
                    "任务名称": f"幻灯片{slide_num}语音合成",
                    "任务描述": f"将第{slide_num}张幻灯片备注转换为语音({word_count}字)",
                    "输入文件": f"scripts/script_{slide_num:03d}.txt",
                    "输出文件": f"audio/audio_{slide_num:03d}.wav",
                    "任务状态": TaskStatus.PENDING.value,
                    "开始时间": "",
                    "完成时间": "",
                    "执行时长(秒)": 0,
                    "错误信息": "",
                    "执行结果": ""
                })
            
            # 步骤3: 视频生成任务
            for i, slide in enumerate(slides_data, 1):
                slide_num = slide.get('slide_number', i)
                
                tasks.append({
                    "步骤ID": "步骤3",
                    "步骤名称": "视频生成",
                    "任务ID": f"video_slide_{slide_num:03d}",
                    "任务名称": f"幻灯片{slide_num}视频生成",
                    "任务描述": f"基于第{slide_num}张幻灯片图片和音频生成视频片段",
                    "输入文件": f"slides/slide_{slide_num:03d}.png, audio/audio_{slide_num:03d}.wav",
                    "输出文件": f"video_clips/video_{slide_num:03d}.mp4",
                    "任务状态": TaskStatus.PENDING.value,
                    "开始时间": "",
                    "完成时间": "",
                    "执行时长(秒)": 0,
                    "错误信息": "",
                    "执行结果": ""
                })
            
            # 步骤4: 字幕生成任务
            for i, slide in enumerate(slides_data, 1):
                slide_num = slide.get('slide_number', i)
                
                tasks.append({
                    "步骤ID": "步骤4",
                    "步骤名称": "字幕生成",
                    "任务ID": f"subtitle_slide_{slide_num:03d}",
                    "任务名称": f"幻灯片{slide_num}字幕生成",
                    "任务描述": f"基于第{slide_num}张幻灯片讲话稿和时间轴生成SRT字幕",
                    "输入文件": f"scripts/script_{slide_num:03d}.txt, audio/audio_{slide_num:03d}.wav",
                    "输出文件": f"subtitles/subtitle_{slide_num:03d}.srt",
                    "任务状态": TaskStatus.PENDING.value,
                    "开始时间": "",
                    "完成时间": "",
                    "执行时长(秒)": 0,
                    "错误信息": "",
                    "执行结果": ""
                })
            
            # 步骤5: 最终合并任务
            tasks.append({
                "步骤ID": "步骤5",
                "步骤名称": "最终合并",
                "任务ID": "final_merge",
                "任务名称": "最终视频合并",
                "任务描述": f"将{total_slides}个视频片段、音频和字幕合并成最终视频",
                "输入文件": "video_clips/*.mp4, audio/*.wav, subtitles/*.srt",
                "输出文件": "final/final_video.mp4",
                "任务状态": TaskStatus.PENDING.value,
                "开始时间": "",
                "完成时间": "",
                "执行时长(秒)": 0,
                "错误信息": "",
                "执行结果": ""
            })
            
            # 保存任务表
            df = pd.DataFrame(tasks)
            df.to_excel(self.task_file, index=False, engine='openpyxl')
            
            # 保存元数据
            metadata = {
                "total_slides": total_slides,
                "created_time": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "project_status": "initialized"
            }
            
            with open(self.task_meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"❌ 初始化任务表失败: {e}")
            return False
    
    def load_tasks(self) -> Optional[pd.DataFrame]:
        """加载任务表"""
        try:
            if self.task_file.exists():
                df = pd.read_excel(self.task_file, engine='openpyxl')
                return df
            else:
                return None
        except Exception as e:
            st.error(f"❌ 加载任务表失败: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          start_time: str = None, end_time: str = None,
                          duration: float = 0, error_msg: str = "",
                          result: str = "") -> bool:
        """更新任务状态"""
        try:
            df = self.load_tasks()
            if df is None:
                return False
            
            # 找到对应的任务
            task_index = df[df['任务ID'] == task_id].index
            if len(task_index) == 0:
                st.warning(f"⚠️ 未找到任务ID: {task_id}")
                return False
            
            idx = task_index[0]
            
            # 更新任务状态
            df.loc[idx, '任务状态'] = status.value
            
            if start_time:
                df.loc[idx, '开始时间'] = start_time
            if end_time:
                df.loc[idx, '完成时间'] = end_time
            if duration > 0:
                df.loc[idx, '执行时长(秒)'] = round(duration, 2)
            if error_msg:
                df.loc[idx, '错误信息'] = error_msg
            if result:
                df.loc[idx, '执行结果'] = result
            
            # 保存更新后的任务表
            df.to_excel(self.task_file, index=False, engine='openpyxl')
            
            # 更新元数据
            self._update_metadata()
            
            return True
            
        except Exception as e:
            st.error(f"❌ 更新任务状态失败: {e}")
            return False
    
    def get_step_tasks(self, step_id: str) -> List[Dict]:
        """获取指定步骤的所有任务"""
        df = self.load_tasks()
        if df is None:
            return []
        
        step_tasks = df[df['步骤ID'] == step_id]
        return step_tasks.to_dict('records')
    
    def get_pending_tasks(self, step_id: str) -> List[Dict]:
        """获取指定步骤的待执行任务"""
        df = self.load_tasks()
        if df is None:
            return []
        
        pending_tasks = df[(df['步骤ID'] == step_id) & 
                          (df['任务状态'] == TaskStatus.PENDING.value)]
        return pending_tasks.to_dict('records')
    
    def get_step_summary(self) -> Dict[str, Dict]:
        """获取各步骤执行摘要"""
        df = self.load_tasks()
        if df is None:
            return {}
        
        summary = {}
        
        for step in ["步骤1", "步骤2", "步骤3", "步骤4", "步骤5"]:
            step_tasks = df[df['步骤ID'] == step]
            
            if len(step_tasks) > 0:
                total = len(step_tasks)
                completed = len(step_tasks[step_tasks['任务状态'] == TaskStatus.COMPLETED.value])
                running = len(step_tasks[step_tasks['任务状态'] == TaskStatus.RUNNING.value])
                failed = len(step_tasks[step_tasks['任务状态'] == TaskStatus.FAILED.value])
                pending = len(step_tasks[step_tasks['任务状态'] == TaskStatus.PENDING.value])
                
                summary[step] = {
                    "total": total,
                    "completed": completed,
                    "running": running,
                    "failed": failed,
                    "pending": pending,
                    "progress": round(completed / total * 100, 1) if total > 0 else 0
                }
        
        return summary
    
    def is_step_completed(self, step_id: str) -> bool:
        """检查步骤是否完全完成"""
        summary = self.get_step_summary()
        if step_id not in summary:
            return False
        
        step_info = summary[step_id]
        return step_info['pending'] == 0 and step_info['failed'] == 0 and step_info['completed'] > 0
    
    def _update_metadata(self):
        """更新元数据"""
        try:
            if self.task_meta_file.exists():
                with open(self.task_meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            metadata['last_updated'] = datetime.now().isoformat()
            
            with open(self.task_meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            st.warning(f"⚠️ 更新元数据失败: {e}")
    
    def export_task_report(self) -> Optional[Path]:
        """导出任务执行报告"""
        try:
            df = self.load_tasks()
            if df is None:
                return None
            
            # 生成报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.project_dir / f"task_report_{timestamp}.xlsx"
            
            # 创建多个工作表
            with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
                # 详细任务表
                df.to_excel(writer, sheet_name='详细任务', index=False)
                
                # 步骤摘要
                summary = self.get_step_summary()
                summary_df = pd.DataFrame(summary).T
                summary_df.to_excel(writer, sheet_name='步骤摘要')
                
                # 失败任务
                failed_tasks = df[df['任务状态'] == TaskStatus.FAILED.value]
                if not failed_tasks.empty:
                    failed_tasks.to_excel(writer, sheet_name='失败任务', index=False)
            
            return report_file
            
        except Exception as e:
            st.error(f"❌ 导出任务报告失败: {e}")
            return None
