"""
工作流服务层
"""
from typing import Dict, Any, List, Optional, Callable
import asyncio
from pathlib import Path
import json
from datetime import datetime
import importlib.util

from .base import BaseService, ServiceResult

class WorkflowService(BaseService):
    """工作流服务管理器"""
    
    def _initialize(self) -> None:
        """初始化工作流服务"""
        self.workflow_steps = {}
        self.active_workflows = {}
        self._load_workflow_steps()
    
    def _load_workflow_steps(self) -> None:
        """加载工作流步骤"""
        try:
            # 动态加载核心步骤
            core_path = Path(__file__).parent.parent.parent / "core"
            
            step_files = {
                "ppt_parser": "step01_ppt_parser.py",
                "pptist_importer": "step01_pptist_importer.py", 
                "tts_generator": "step02_tts_generator.py",
                "video_generator": "step03_video_generator.py",
                "subtitle_generator": "step04_subtitle_generator.py",
                "final_merger": "step05_final_merger.py"
            }
            
            for step_name, filename in step_files.items():
                step_path = core_path / filename
                if step_path.exists():
                    try:
                        spec = importlib.util.spec_from_file_location(step_name, step_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self.workflow_steps[step_name] = module
                        self.logger.info(f"已加载工作流步骤: {step_name}")
                    except Exception as e:
                        self.logger.error(f"加载工作流步骤失败 {step_name}: {e}")
                        
        except Exception as e:
            self.logger.error(f"工作流步骤初始化失败: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "service": "Workflow",
            "status": "healthy",
            "steps_loaded": len(self.workflow_steps),
            "available_steps": list(self.workflow_steps.keys()),
            "active_workflows": len(self.active_workflows)
        }
    
    def get_workflow_steps(self) -> ServiceResult:
        """获取工作流步骤"""
        try:
            steps = []
            step_order = ["ppt_parser", "pptist_importer", "tts_generator", 
                         "video_generator", "subtitle_generator", "final_merger"]
            
            for i, step_name in enumerate(step_order):
                if step_name in self.workflow_steps:
                    module = self.workflow_steps[step_name]
                    step_info = {
                        "name": step_name,
                        "order": i + 1,
                        "display_name": getattr(module, "DISPLAY_NAME", step_name),
                        "description": getattr(module, "DESCRIPTION", ""),
                        "required_inputs": getattr(module, "REQUIRED_INPUTS", []),
                        "outputs": getattr(module, "OUTPUTS", [])
                    }
                    steps.append(step_info)
            
            return ServiceResult.success_result(steps)
            
        except Exception as e:
            self.logger.error(f"获取工作流步骤失败: {e}")
            return ServiceResult.error_result(f"获取工作流步骤失败: {e}")
    
    async def start_workflow(self, workflow_data: Dict[str, Any], 
                           progress_callback: Optional[Callable] = None) -> ServiceResult:
        """启动工作流"""
        try:
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建工作流状态
            workflow_state = {
                "id": workflow_id,
                "status": "running",
                "current_step": 0,
                "total_steps": len(self.workflow_steps),
                "data": workflow_data,
                "start_time": datetime.now().isoformat(),
                "progress": 0,
                "results": {}
            }
            
            self.active_workflows[workflow_id] = workflow_state
            
            # 异步执行工作流
            asyncio.create_task(self._execute_workflow(workflow_id, progress_callback))
            
            return ServiceResult.success_result({
                "workflow_id": workflow_id,
                "status": "started"
            })
            
        except Exception as e:
            self.logger.error(f"启动工作流失败: {e}")
            return ServiceResult.error_result(f"启动工作流失败: {e}")
    
    async def _execute_workflow(self, workflow_id: str, 
                              progress_callback: Optional[Callable] = None) -> None:
        """执行工作流"""
        try:
            workflow_state = self.active_workflows[workflow_id]
            steps = ["ppt_parser", "pptist_importer", "tts_generator", 
                    "video_generator", "subtitle_generator", "final_merger"]
            
            for i, step_name in enumerate(steps):
                if step_name not in self.workflow_steps:
                    continue
                
                # 更新状态
                workflow_state["current_step"] = i + 1
                workflow_state["progress"] = (i / len(steps)) * 100
                
                if progress_callback:
                    await progress_callback(workflow_state)
                
                # 执行步骤
                step_module = self.workflow_steps[step_name]
                step_data = workflow_state["data"]
                
                if hasattr(step_module, "execute_async"):
                    result = await step_module.execute_async(step_data)
                elif hasattr(step_module, "execute"):
                    result = await asyncio.to_thread(step_module.execute, step_data)
                else:
                    self.logger.error(f"步骤 {step_name} 缺少执行函数")
                    continue
                
                # 保存步骤结果
                workflow_state["results"][step_name] = result
                
                # 更新数据供下一步使用
                if isinstance(result, dict) and "output_data" in result:
                    workflow_state["data"].update(result["output_data"])
            
            # 工作流完成
            workflow_state["status"] = "completed"
            workflow_state["progress"] = 100
            workflow_state["end_time"] = datetime.now().isoformat()
            
            if progress_callback:
                await progress_callback(workflow_state)
                
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            workflow_state = self.active_workflows.get(workflow_id, {})
            workflow_state["status"] = "failed"
            workflow_state["error"] = str(e)
            workflow_state["end_time"] = datetime.now().isoformat()
            
            if progress_callback:
                await progress_callback(workflow_state)
    
    def get_workflow_status(self, workflow_id: str) -> ServiceResult:
        """获取工作流状态"""
        try:
            if workflow_id not in self.active_workflows:
                return ServiceResult.error_result(f"工作流不存在: {workflow_id}", 404)
            
            workflow_state = self.active_workflows[workflow_id]
            return ServiceResult.success_result(workflow_state)
            
        except Exception as e:
            self.logger.error(f"获取工作流状态失败: {e}")
            return ServiceResult.error_result(f"获取工作流状态失败: {e}")
    
    def cancel_workflow(self, workflow_id: str) -> ServiceResult:
        """取消工作流"""
        try:
            if workflow_id not in self.active_workflows:
                return ServiceResult.error_result(f"工作流不存在: {workflow_id}", 404)
            
            workflow_state = self.active_workflows[workflow_id]
            workflow_state["status"] = "cancelled"
            workflow_state["end_time"] = datetime.now().isoformat()
            
            return ServiceResult.success_result({
                "workflow_id": workflow_id,
                "status": "cancelled"
            })
            
        except Exception as e:
            self.logger.error(f"取消工作流失败: {e}")
            return ServiceResult.error_result(f"取消工作流失败: {e}")
    
    def get_active_workflows(self) -> ServiceResult:
        """获取活动工作流"""
        try:
            active = []
            for workflow_id, state in self.active_workflows.items():
                if state["status"] in ["running", "pending"]:
                    active.append({
                        "id": workflow_id,
                        "status": state["status"],
                        "progress": state["progress"],
                        "current_step": state["current_step"],
                        "start_time": state["start_time"]
                    })
            
            return ServiceResult.success_result(active)
            
        except Exception as e:
            self.logger.error(f"获取活动工作流失败: {e}")
            return ServiceResult.error_result(f"获取活动工作流失败: {e}")
