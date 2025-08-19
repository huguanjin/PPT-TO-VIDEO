"""
API路由器模块
"""

from .tts import router as tts_router
from .workflow import router as workflow_router
from .storage import router as storage_router
from .config import router as config_router

__all__ = [
    "tts_router",
    "workflow_router", 
    "storage_router",
    "config_router"
]
