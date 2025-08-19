"""
TTS API路由
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio

from ..dependencies import get_tts_service
from ..services import TTSService, ServiceResult
from ..exceptions import TTSException, ValidationException

router = APIRouter(prefix="/tts", tags=["TTS"])

# 请求模型
class TTSGenerateRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    engine: Optional[str] = None
    output_path: Optional[str] = None

class TTSConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]
    engine: Optional[str] = None

# 响应模型
class TTSEngineInfo(BaseModel):
    name: str
    display_name: str
    description: str
    supported_languages: list

class TTSGenerateResponse(BaseModel):
    audio_path: str
    engine: str
    text_length: int

@router.get("/engines", response_model=list[TTSEngineInfo])
async def get_available_engines(
    tts_service: TTSService = Depends(get_tts_service)
):
    """获取可用的TTS引擎"""
    
    result = tts_service.get_available_engines()
    
    if not result.success:
        raise TTSException(result.error)
    
    return result.data

@router.get("/engines/current")
async def get_current_engine(
    tts_service: TTSService = Depends(get_tts_service)
):
    """获取当前TTS引擎"""
    
    return {
        "current_engine": tts_service.current_engine,
        "status": "active"
    }

@router.post("/engines/current")
async def set_current_engine(
    engine_name: str,
    tts_service: TTSService = Depends(get_tts_service)
):
    """设置当前TTS引擎"""
    
    result = tts_service.set_current_engine(engine_name)
    
    if not result.success:
        if result.code == 404:
            raise HTTPException(status_code=404, detail=result.error)
        else:
            raise TTSException(result.error)
    
    return result.data

@router.post("/generate", response_model=TTSGenerateResponse)
async def generate_audio(
    request: TTSGenerateRequest,
    background_tasks: BackgroundTasks,
    tts_service: TTSService = Depends(get_tts_service)
):
    """生成音频"""
    
    if not request.text.strip():
        raise ValidationException("文本内容不能为空", "text")
    
    if len(request.text) > 10000:
        raise ValidationException("文本长度不能超过10000字符", "text")
    
    result = await tts_service.generate_audio(
        text=request.text,
        voice=request.voice,
        output_path=request.output_path,
        engine=request.engine
    )
    
    if not result.success:
        raise TTSException(result.error, request.engine)
    
    return result.data

@router.get("/config")
async def get_engine_config(
    engine: Optional[str] = None,
    tts_service: TTSService = Depends(get_tts_service)
):
    """获取引擎配置"""
    
    result = tts_service.get_engine_config(engine)
    
    if not result.success:
        raise TTSException(result.error)
    
    return result.data

@router.put("/config")
async def update_engine_config(
    request: TTSConfigUpdateRequest,
    tts_service: TTSService = Depends(get_tts_service)
):
    """更新引擎配置"""
    
    if not request.config:
        raise ValidationException("配置不能为空", "config")
    
    result = tts_service.update_engine_config(
        config_updates=request.config,
        engine_name=request.engine
    )
    
    if not result.success:
        raise TTSException(result.error)
    
    return result.data

@router.get("/health")
async def tts_health_check(
    tts_service: TTSService = Depends(get_tts_service)
):
    """TTS服务健康检查"""
    
    return tts_service.health_check()
