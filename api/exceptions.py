"""
API异常处理
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging

class APIException(HTTPException):
    """自定义API异常"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code

class ValidationException(APIException):
    """验证异常"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
        self.field = field

class ResourceNotFoundException(APIException):
    """资源未找到异常"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND"
        )
        self.resource_type = resource_type
        self.resource_id = resource_id

class ServiceUnavailableException(APIException):
    """服务不可用异常"""
    
    def __init__(self, service_name: str, detail: Optional[str] = None):
        message = f"Service '{service_name}' is currently unavailable"
        if detail:
            message += f": {detail}"
        
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
            error_code="SERVICE_UNAVAILABLE"
        )
        self.service_name = service_name

class ConfigurationException(APIException):
    """配置异常"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration error: {detail}",
            error_code="CONFIGURATION_ERROR"
        )

class TTSException(APIException):
    """TTS服务异常"""
    
    def __init__(self, detail: str, engine: Optional[str] = None):
        message = f"TTS error: {detail}"
        if engine:
            message += f" (engine: {engine})"
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="TTS_ERROR"
        )
        self.engine = engine

class WorkflowException(APIException):
    """工作流异常"""
    
    def __init__(self, detail: str, workflow_id: Optional[str] = None, step: Optional[str] = None):
        message = f"Workflow error: {detail}"
        if workflow_id:
            message += f" (workflow: {workflow_id})"
        if step:
            message += f" (step: {step})"
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="WORKFLOW_ERROR"
        )
        self.workflow_id = workflow_id
        self.step = step

class StorageException(APIException):
    """存储异常"""
    
    def __init__(self, detail: str, file_path: Optional[str] = None):
        message = f"Storage error: {detail}"
        if file_path:
            message += f" (file: {file_path})"
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="STORAGE_ERROR"
        )
        self.file_path = file_path

# 异常处理器
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API异常处理器"""
    
    logger = logging.getLogger(__name__)
    logger.error(f"API异常: {exc.detail}")
    
    response_data = {
        "error": {
            "code": exc.error_code or "API_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    }
    
    # 添加额外的错误信息
    if hasattr(exc, 'field') and exc.field:
        response_data["error"]["field"] = exc.field
    
    if hasattr(exc, 'resource_type') and exc.resource_type:
        response_data["error"]["resource_type"] = exc.resource_type
    
    if hasattr(exc, 'resource_id') and exc.resource_id:
        response_data["error"]["resource_id"] = exc.resource_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    
    logger = logging.getLogger(__name__)
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "status_code": 500
            }
        }
    )

def setup_exception_handlers(app):
    """设置异常处理器"""
    
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
