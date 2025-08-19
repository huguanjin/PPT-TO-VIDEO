"""
完整工作流API - 替代Streamlit界面
提供PPT到视频的完整处理流程API
"""
import os
import json
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# 导入核心模块
from core.step01_ppt_parser import PPTParser
from core.step02_tts_generator import TTSGenerator
from core.step03_video_generator import VideoGenerator
from core.step04_subtitle_generator import SubtitleGenerator
from core.step05_final_merger import FFmpegFinalMerger
from utils.task_manager import TaskManager
from utils.file_manager import FileManager
from utils.logger import get_logger
from config.settings import load_app_config, save_app_config

# 导入PPT存储API
from api_ppt_storage import router as ppt_storage_router

app = FastAPI(title="PPT转视频完整工作流API", version="1.0.0")

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
project_tasks = {}  # 存储项目任务状态
workflow_status = {}  # 存储工作流状态

# 包含PPT存储路由
app.include_router(ppt_storage_router)

class VideoConfig(BaseModel):
    """视频配置"""
    resolution: str = "1920x1080"
    fps: int = 24
    video_bitrate: str = "2000k"
    include_subtitles: bool = True
    background_color: str = "#FFFFFF"

class TTSConfig(BaseModel):
    """TTS配置"""
    preferred_engine: str = "edge_tts"
    edge_voice: str = "zh-CN-XiaoxiaoNeural"
    edge_rate: str = "medium"
    edge_pitch: str = "medium"
    fish_api_key: str = ""
    fish_character: str = "雷军"
    fish_character_id: str = ""
    fish_character_name: str = ""
    openai_api_key: str = ""
    openai_voice: str = "alloy"
    openai_model: str = "tts-1"
    azure_api_key: str = ""
    azure_region: str = ""
    azure_voice: str = "zh-CN-XiaoxiaoNeural"
    sample_rate: int = 22050
    max_retries: int = 3
    timeout: float = 30.0

class SubtitleConfig(BaseModel):
    """字幕配置"""
    font_family: str = "微软雅黑"
    font_size: int = 24
    font_color: str = "#FFFFFF"
    background_color: str = "#000000"
    position: str = "bottom"
    enabled: bool = True

class WorkflowConfig(BaseModel):
    """完整工作流配置"""
    video: VideoConfig
    tts: TTSConfig
    subtitle: SubtitleConfig

class ProjectImportRequest(BaseModel):
    """项目导入请求"""
    project_name: str
    slides_metadata: Dict[str, Any]
    slides_images: List[Dict[str, str]]

class WorkflowRequest(BaseModel):
    """工作流执行请求"""
    project_name: str
    config: Optional[WorkflowConfig] = None

@app.get("/")
async def root():
    return {"message": "PPT转视频完整工作流API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "ppt-to-video-api"}

@app.get("/api/config")
async def get_config():
    """获取当前配置"""
    try:
        # 读取应用配置
        app_config = load_app_config()
        
        # 读取TTS配置
        tts_config_path = Path("config_data/tts_config.json")
        if tts_config_path.exists():
            with open(tts_config_path, 'r', encoding='utf-8') as f:
                tts_config = json.load(f)
        else:
            tts_config = TTSConfig().dict()
        
        # 构建完整配置
        config = {
            "video": {
                "resolution": app_config.get("video_resolution", "1920x1080"),
                "fps": app_config.get("video_fps", 24),
                "video_bitrate": app_config.get("video_bitrate", "2000k"),
                "include_subtitles": app_config.get("include_subtitles", True),
                "background_color": app_config.get("background_color", "#FFFFFF")
            },
            "tts": tts_config,
            "subtitle": {
                "font_family": app_config.get("subtitle_font_family", "微软雅黑"),
                "font_size": app_config.get("subtitle_font_size", 24),
                "font_color": app_config.get("subtitle_font_color", "#FFFFFF"),
                "background_color": app_config.get("subtitle_background_color", "#000000"),
                "position": app_config.get("subtitle_position", "bottom"),
                "enabled": app_config.get("subtitle_enabled", True)
            }
        }
        
        return {"success": True, "config": config}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@app.post("/api/config")
async def update_config(request: Request):
    """更新配置"""
    try:
        # 先获取原始数据进行调试
        raw_data = await request.json()
        print(f"收到的配置数据: {json.dumps(raw_data, indent=2, ensure_ascii=False)}")
        
        # 尝试解析为WorkflowConfig
        config = WorkflowConfig(**raw_data)
        
        # 更新应用配置
        app_config = load_app_config()
        
        # 更新视频配置
        app_config.update({
            "video_resolution": config.video.resolution,
            "video_fps": config.video.fps,
            "video_bitrate": config.video.video_bitrate,
            "include_subtitles": config.video.include_subtitles,
            "background_color": config.video.background_color,
            "subtitle_font_family": config.subtitle.font_family,
            "subtitle_font_size": config.subtitle.font_size,
            "subtitle_font_color": config.subtitle.font_color,
            "subtitle_background_color": config.subtitle.background_color,
            "subtitle_position": config.subtitle.position,
            "subtitle_enabled": config.subtitle.enabled
        })
        
        save_app_config(app_config)
        
        # 更新TTS配置
        tts_config_path = Path("config_data/tts_config.json")
        tts_config_data = config.tts.dict()
        tts_config_data["last_updated"] = datetime.now().isoformat()
        
        with open(tts_config_path, 'w', encoding='utf-8') as f:
            json.dump(tts_config_data, f, ensure_ascii=False, indent=2)
        
        # 如果是Fish TTS，同时更新fish_tts_config.json
        if config.tts.preferred_engine == "fish_tts":
            fish_config_path = Path("config_data/fish_tts_config.json")
            
            # 读取现有的fish配置
            if fish_config_path.exists():
                with open(fish_config_path, 'r', encoding='utf-8') as f:
                    fish_config = json.load(f)
            else:
                fish_config = {
                    "api_key": "",
                    "character": "雷军",
                    "character_id_dict": {
                        "AD学姐": "7f92f8afb8ec43bf81429cc1c9199cb1",
                        "丁真": "54a5170264694bfc8e9ad98df7bd89c3",
                        "赛马娘": "0eb38bc974e1459facca38b359e13511",
                        "蔡徐坤": "e4642e5edccd4d9ab61a69e82d4f8a14",
                        "雷军": "738d0cc1a3e9430a9de2b544a466a7fc"
                    }
                }
            
            # 更新fish配置
            fish_config["api_key"] = config.tts.fish_api_key
            fish_config["character"] = config.tts.fish_character
            
            # 保存更新后的fish配置
            with open(fish_config_path, 'w', encoding='utf-8') as f:
                json.dump(fish_config, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": "配置更新成功"}
        
    except Exception as e:
        print(f"配置更新错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@app.post("/api/import")
async def import_project(request: Request):
    """导入PPT项目 - 使用Request直接处理FormData"""
    try:
        print("开始处理导入请求")
        form = await request.form()
        print(f"表单字段: {list(form.keys())}")
        
        # 获取项目数据
        project_data_str = form.get("project_data")
        if not project_data_str:
            print("错误: 缺少project_data参数")
            raise HTTPException(status_code=400, detail="缺少project_data参数")
        
        print(f"项目数据长度: {len(project_data_str)}")
        
        # 解析项目数据
        import json
        try:
            project_metadata = json.loads(project_data_str)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            raise HTTPException(status_code=400, detail=f"项目数据JSON格式错误: {e}")
        
        project_name = project_metadata.get("project_name")
        
        if not project_name:
            # 生成项目名称
            project_name = f"pptist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"项目名称: {project_name}")
        
        project_dir = Path("output") / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存slides_metadata
        slides_dir = project_dir / "slides"
        slides_dir.mkdir(exist_ok=True)
        
        metadata_path = slides_dir / "slides_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(project_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"元数据已保存到: {metadata_path}")
        
        # 保存图片文件
        image_files = form.getlist("images")
        print(f"接收到 {len(image_files)} 个图片文件")
        
        for i, image_file in enumerate(image_files):
            if hasattr(image_file, 'filename') and hasattr(image_file, 'read'):
                print(f"处理图片 {i+1}: {image_file.filename}")
                content = await image_file.read()
                img_path = slides_dir / image_file.filename
                with open(img_path, 'wb') as f:
                    f.write(content)
                print(f"图片已保存到: {img_path}")
            else:
                print(f"跳过无效的图片文件: {type(image_file)}")
        
        # 初始化任务管理器
        task_manager = TaskManager(project_dir)
        
        # 从项目元数据提取slides数据来初始化任务
        slides_data = project_metadata.get("slides", [])
        if slides_data:
            task_manager.initialize_tasks(slides_data)
            task_id = "project_import"
        else:
            # 如果没有slides数据，创建一个简单的导入记录
            task_id = "project_import_simple"
        
        project_tasks[project_name] = task_manager
        
        print(f"项目导入成功: {project_name}")
        return {
            "success": True,
            "message": f"项目 {project_name} 导入成功",
            "project_name": project_name,
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"项目导入失败: {e}")
        print(f"详细错误信息: {error_details}")
        raise HTTPException(status_code=500, detail=f"项目导入失败: {str(e)}")

@app.post("/api/workflow/execute")
async def execute_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """执行完整工作流"""
    try:
        print(f"开始执行工作流，项目名称: {request.project_name}")
        project_name = request.project_name
        project_dir = Path("output") / project_name
        
        if not project_dir.exists():
            print(f"错误: 项目目录不存在: {project_dir}")
            raise HTTPException(status_code=404, detail=f"项目 {project_name} 不存在")
        
        print(f"项目目录存在: {project_dir}")
        
        # 初始化工作流状态
        workflow_id = f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"创建工作流ID: {workflow_id}")
        
        workflow_status[workflow_id] = {
            "status": "running",
            "current_step": 1,
            "total_steps": 5,
            "steps": {
                1: {"name": "解析PPT数据", "status": "running", "progress": 0.0},
                2: {"name": "生成语音", "status": "pending", "progress": 0.0},
                3: {"name": "生成视频", "status": "pending", "progress": 0.0},
                4: {"name": "生成字幕", "status": "pending", "progress": 0.0},
                5: {"name": "合并最终视频", "status": "pending", "progress": 0.0}
            },
            "start_time": datetime.now().isoformat(),
            "project_name": project_name
        }
        
        # 在后台执行工作流
        background_tasks.add_task(run_complete_workflow, project_name, workflow_id, request.config)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "工作流开始执行",
            "status_url": f"/api/workflow/status/{workflow_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流启动失败: {str(e)}")

async def run_complete_workflow(project_name: str, workflow_id: str, config: Optional[WorkflowConfig]):
    """运行完整工作流"""
    try:
        project_dir = Path("output") / project_name
        logger = get_logger(__name__, project_dir / "logs")
        
        # 更新配置（如果提供）
        if config:
            await update_config_internal(config)
        
        def update_step_progress(step: int, status: str, progress: float, message: str = ""):
            workflow_status[workflow_id]["current_step"] = step
            workflow_status[workflow_id]["steps"][step] = {
                "name": workflow_status[workflow_id]["steps"][step]["name"],
                "status": status,
                "progress": progress,
                "message": message
            }
        
        try:
            # 步骤1：解析PPT数据（转换格式）
            update_step_progress(1, "running", 0.0, "正在转换数据格式...")
            
            # 读取slides_metadata.json并转换为scripts_metadata.json
            slides_metadata_path = project_dir / "slides" / "slides_metadata.json"
            if not slides_metadata_path.exists():
                raise Exception("slides_metadata.json文件不存在")
            
            with open(slides_metadata_path, 'r', encoding='utf-8') as f:
                slides_data = json.load(f)
            
            # 转换数据格式
            scripts_data = convert_slides_to_scripts(slides_data)
            
            # 保存scripts_metadata.json
            scripts_dir = project_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            scripts_metadata_path = scripts_dir / "scripts_metadata.json"
            
            with open(scripts_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(scripts_data, f, ensure_ascii=False, indent=2)
            
            update_step_progress(1, "completed", 1.0, "数据格式转换完成")
            
            # 步骤2：生成语音
            update_step_progress(2, "running", 0.0, "正在生成语音...")
            
            tts_generator = TTSGenerator(project_dir)
            
            def tts_progress_callback(progress: int):
                update_step_progress(2, "running", progress / 100.0, f"正在生成语音 {progress}%")
            
            tts_result = await tts_generator.generate_audio(
                scripts_data=scripts_data,
                progress_callback=tts_progress_callback
            )
            
            # 检查TTS结果
            if not tts_result or not tts_result.get("generation_completed"):
                raise Exception(f"语音生成失败: 生成未完成")
            
            update_step_progress(2, "completed", 1.0, "语音生成完成")
            
            # 步骤3：生成视频
            update_step_progress(3, "running", 0.0, "正在生成视频...")
            
            video_generator = VideoGenerator(project_dir)
            
            def video_progress_callback(progress: int):
                update_step_progress(3, "running", progress / 100.0, f"正在生成视频 {progress}%")
            
            video_result = await video_generator.generate_video_clips(
                slides_data=slides_data,
                audio_data=tts_result,
                progress_callback=video_progress_callback
            )
            
            if not video_result or not video_result.get("generation_completed"):
                raise Exception(f"视频生成失败: 生成未完成")
            
            update_step_progress(3, "completed", 1.0, "视频生成完成")
            
            # 步骤4：生成字幕
            update_step_progress(4, "running", 0.0, "正在生成字幕...")
            
            subtitle_generator = SubtitleGenerator(project_dir)
            
            def subtitle_progress_callback(progress: int):
                update_step_progress(4, "running", progress / 100.0, f"正在生成字幕 {progress}%")
            
            subtitle_result = await subtitle_generator.generate_subtitles(
                scripts_data=scripts_data,
                audio_data=tts_result,
                progress_callback=subtitle_progress_callback
            )
            
            if not subtitle_result or not subtitle_result.get("subtitle_generation_completed"):
                raise Exception(f"字幕生成失败: 生成未完成")
            
            update_step_progress(4, "completed", 1.0, "字幕生成完成")
            
            # 步骤5：合并最终视频
            update_step_progress(5, "running", 0.0, "正在合并最终视频...")
            
            final_merger = FFmpegFinalMerger(project_dir)
            
            def merge_progress_callback(progress: int):
                update_step_progress(5, "running", progress / 100.0, f"正在合并视频 {progress}%")
            
            final_result = final_merger.merge_final_video(
                video_data=video_result,
                audio_data=tts_result,
                subtitle_data=subtitle_result,
                progress_callback=merge_progress_callback
            )
            
            if not final_result.get("success"):
                raise Exception(f"最终视频合并失败: {final_result.get('error', '未知错误')}")
            
            update_step_progress(5, "completed", 1.0, "最终视频合并完成")
            
            # 工作流完成
            workflow_status[workflow_id]["status"] = "completed"
            workflow_status[workflow_id]["end_time"] = datetime.now().isoformat()
            workflow_status[workflow_id]["final_video"] = final_result.get("output_file")
            
            logger.info(f"工作流 {workflow_id} 完成")
            
        except Exception as e:
            # 工作流失败
            current_step = workflow_status[workflow_id]["current_step"]
            update_step_progress(current_step, "failed", 0.0, str(e))
            workflow_status[workflow_id]["status"] = "failed"
            workflow_status[workflow_id]["error"] = str(e)
            workflow_status[workflow_id]["end_time"] = datetime.now().isoformat()
            
            logger.error(f"工作流 {workflow_id} 失败: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"工作流执行异常: {str(e)}")

def convert_slides_to_scripts(slides_data: Dict[str, Any]) -> Dict[str, Any]:
    """将slides_metadata转换为scripts_metadata格式"""
    scripts_data = {
        "project_info": slides_data.get("project_info", {}),
        "scripts": []
    }
    
    slides = slides_data.get("slides", [])
    for i, slide in enumerate(slides):
        script = {
            "script_id": f"script_{i+1:03d}",
            "slide_index": i,
            "slide_number": slide.get("slide_number", i + 1),  # 使用原有字段或默认值
            "slide_id": slide.get("id", f"slide_{i+1}"),
            "title": slide.get("title", ""),
            "content": slide.get("remark", ""),  # 使用remark作为主要内容
            "script_content": slide.get("remark", ""),  # TTS需要的脚本内容
            "text": slide.get("remark", ""),  # TTS需要的文本内容
            "duration": slide.get("duration", 3.0),
            "image_file": slide.get("image_file", f"slide_{i+1:03d}.png")
        }
        scripts_data["scripts"].append(script)
    
    return scripts_data

async def update_config_internal(config: WorkflowConfig):
    """内部配置更新函数"""
    try:
        # 更新应用配置
        app_config = load_app_config()
        
        app_config.update({
            "video_resolution": config.video.resolution,
            "video_fps": config.video.fps,
            "video_bitrate": config.video.video_bitrate,
            "include_subtitles": config.video.include_subtitles,
            "background_color": config.video.background_color,
            "subtitle_font_family": config.subtitle.font_family,
            "subtitle_font_size": config.subtitle.font_size,
            "subtitle_font_color": config.subtitle.font_color,
            "subtitle_background_color": config.subtitle.background_color,
            "subtitle_position": config.subtitle.position,
            "subtitle_enabled": config.subtitle.enabled
        })
        
        save_app_config(app_config)
        
        # 更新TTS配置
        tts_config_path = Path("config_data/tts_config.json")
        tts_config_data = config.tts.dict()
        tts_config_data["last_updated"] = datetime.now().isoformat()
        
        with open(tts_config_path, 'w', encoding='utf-8') as f:
            json.dump(tts_config_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        raise Exception(f"配置更新失败: {str(e)}")

@app.get("/api/workflow/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    if workflow_id not in workflow_status:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    return {"success": True, "workflow": workflow_status[workflow_id]}

@app.get("/api/projects")
async def list_projects():
    """列出所有项目"""
    try:
        output_dir = Path("output")
        if not output_dir.exists():
            return {"success": True, "projects": []}
        
        projects = []
        for project_dir in output_dir.iterdir():
            if project_dir.is_dir():
                # 检查是否有slides_metadata.json
                slides_metadata_path = project_dir / "slides" / "slides_metadata.json"
                if slides_metadata_path.exists():
                    with open(slides_metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # 检查是否有最终视频
                    final_dir = project_dir / "final"
                    final_videos = []
                    if final_dir.exists():
                        for video_file in final_dir.glob("*.mp4"):
                            final_videos.append({
                                "filename": video_file.name,
                                "size": video_file.stat().st_size,
                                "created": datetime.fromtimestamp(video_file.stat().st_ctime).isoformat()
                            })
                    
                    projects.append({
                        "name": project_dir.name,
                        "title": metadata.get("project_info", {}).get("title", project_dir.name),
                        "created": datetime.fromtimestamp(project_dir.stat().st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(project_dir.stat().st_mtime).isoformat(),
                        "slide_count": len(metadata.get("slides", [])),
                        "final_videos": final_videos
                    })
        
        projects.sort(key=lambda x: x["modified"], reverse=True)
        return {"success": True, "projects": projects}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@app.get("/api/download/{project_name}/{filename}")
async def download_video(project_name: str, filename: str):
    """下载视频文件"""
    try:
        video_path = Path("output") / project_name / "final" / filename
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="视频文件不存在")
        
        return FileResponse(
            path=video_path,
            filename=filename,
            media_type='video/mp4'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

class TTSTestRequest(BaseModel):
    """TTS试听请求"""
    text: str
    engine: str = "edge_tts"
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "medium"
    pitch: str = "medium"
    fish_api_key: str = ""
    fish_character: str = "雷军"

@app.post("/api/tts/preview")
async def tts_preview(request: TTSTestRequest):
    """
    TTS配音试听接口
    生成指定文本和语音参数的音频文件供试听
    """
    try:
        from utils.integrated_tts_manager import IntegratedTTSManager, TTSConfig, TTSEngine
        
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        audio_filename = f"preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        audio_path = temp_dir / audio_filename
        
        # 如果是Fish TTS，需要获取角色ID
        fish_character_id = ""
        if request.engine == "fish_tts":
            # 读取Fish TTS配置文件获取角色ID映射
            fish_config_path = Path("config_data/fish_tts_config.json")
            if fish_config_path.exists():
                with open(fish_config_path, 'r', encoding='utf-8') as f:
                    fish_config = json.load(f)
                    character_id_dict = fish_config.get("character_id_dict", {})
                    fish_character_id = character_id_dict.get(request.fish_character, "")
        
        # 创建TTS配置
        tts_config = TTSConfig(
            edge_voice=request.voice,
            edge_rate=request.rate,
            edge_pitch=request.pitch,
            fish_api_key=request.fish_api_key,
            fish_character_name=request.fish_character,
            fish_character_id=fish_character_id
        )
        
        # 初始化TTS管理器
        tts_manager = IntegratedTTSManager(tts_config)
        
        # 根据选择的引擎设置首选引擎
        preferred_engine = None
        if request.engine == "edge_tts":
            preferred_engine = TTSEngine.EDGE_TTS
        elif request.engine == "fish_tts":
            preferred_engine = TTSEngine.FISH_TTS
        
        # 生成音频
        result = await tts_manager.synthesize_speech(
            request.text,
            audio_path,
            preferred_engine=preferred_engine
        )
        
        if result["success"] and audio_path.exists():
            # 返回音频文件
            return FileResponse(
                path=audio_path,
                filename=audio_filename,
                media_type='audio/wav',
                headers={
                    "Content-Disposition": f"attachment; filename={audio_filename}",
                    "Cache-Control": "no-cache"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="音频生成失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试听失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8502)
