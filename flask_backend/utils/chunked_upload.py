"""
分片上传处理模块
支持大文件的分片上传，解决1MB文件大小限制问题
"""
import os
import json
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import HTTPException, UploadFile, Form
import aiofiles
import logging

logger = logging.getLogger(__name__)

class ChunkedUploadManager:
    """分片上传管理器"""
    
    def __init__(self, upload_dir: Path = Path("temp_uploads")):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(exist_ok=True)
        
        # 存储上传会话信息
        self.upload_sessions: Dict[str, Dict[str, Any]] = {}
    
    def generate_upload_id(self, file_info: Dict[str, Any]) -> str:
        """生成上传ID"""
        content = f"{file_info['filename']}_{file_info['size']}_{file_info['checksum']}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def init_upload(self, 
                         filename: str, 
                         total_size: int, 
                         total_chunks: int,
                         checksum: Optional[str] = None) -> str:
        """初始化分片上传"""
        try:
            file_info = {
                "filename": filename,
                "size": total_size,
                "checksum": checksum or "unknown"
            }
            
            upload_id = self.generate_upload_id(file_info)
            
            # 创建上传会话
            session_dir = self.upload_dir / upload_id
            session_dir.mkdir(exist_ok=True)
            
            self.upload_sessions[upload_id] = {
                "filename": filename,
                "total_size": total_size,
                "total_chunks": total_chunks,
                "received_chunks": set(),
                "session_dir": session_dir,
                "created_at": asyncio.get_event_loop().time()
            }
            
            logger.info(f"🚀 初始化分片上传: {upload_id}, 文件: {filename}, 大小: {total_size:,} bytes, 分片数: {total_chunks}")
            return upload_id
            
        except Exception as e:
            logger.error(f"❌ 初始化分片上传失败: {e}")
            raise HTTPException(status_code=500, detail=f"初始化上传失败: {e}")
    
    async def upload_chunk(self, 
                          upload_id: str, 
                          chunk_index: int, 
                          chunk_data: bytes) -> Dict[str, Any]:
        """上传单个分片"""
        try:
            if upload_id not in self.upload_sessions:
                raise HTTPException(status_code=404, detail="上传会话不存在")
            
            session = self.upload_sessions[upload_id]
            chunk_file = session["session_dir"] / f"chunk_{chunk_index:04d}"
            
            # 保存分片
            async with aiofiles.open(chunk_file, 'wb') as f:
                await f.write(chunk_data)
            
            # 记录已接收的分片
            session["received_chunks"].add(chunk_index)
            
            progress = len(session["received_chunks"]) / session["total_chunks"] * 100
            
            logger.info(f"📦 接收分片 {chunk_index}, 上传ID: {upload_id}, 进度: {progress:.1f}%")
            
            return {
                "upload_id": upload_id,
                "chunk_index": chunk_index,
                "progress": progress,
                "received_chunks": len(session["received_chunks"]),
                "total_chunks": session["total_chunks"],
                "completed": len(session["received_chunks"]) == session["total_chunks"]
            }
            
        except Exception as e:
            logger.error(f"❌ 上传分片失败: {e}")
            raise HTTPException(status_code=500, detail=f"上传分片失败: {e}")
    
    async def complete_upload(self, upload_id: str, target_file: Path) -> Dict[str, Any]:
        """完成分片上传，合并文件"""
        try:
            if upload_id not in self.upload_sessions:
                raise HTTPException(status_code=404, detail="上传会话不存在")
            
            session = self.upload_sessions[upload_id]
            
            # 检查是否所有分片都已接收
            if len(session["received_chunks"]) != session["total_chunks"]:
                missing_chunks = set(range(session["total_chunks"])) - session["received_chunks"]
                raise HTTPException(status_code=400, detail=f"缺少分片: {list(missing_chunks)}")
            
            # 确保目标目录存在
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 合并分片
            logger.info(f"🔗 开始合并分片: {upload_id} -> {target_file}")
            
            async with aiofiles.open(target_file, 'wb') as output_file:
                for chunk_index in range(session["total_chunks"]):
                    chunk_file = session["session_dir"] / f"chunk_{chunk_index:04d}"
                    
                    if not chunk_file.exists():
                        raise HTTPException(status_code=500, detail=f"分片文件丢失: {chunk_index}")
                    
                    async with aiofiles.open(chunk_file, 'rb') as chunk:
                        data = await chunk.read()
                        await output_file.write(data)
            
            # 验证文件大小
            actual_size = target_file.stat().st_size
            expected_size = session["total_size"]
            
            if actual_size != expected_size:
                logger.error(f"❌ 文件大小不匹配: 期望 {expected_size}, 实际 {actual_size}")
                target_file.unlink()  # 删除错误的文件
                raise HTTPException(status_code=500, detail="文件大小验证失败")
            
            # 清理临时文件
            await self.cleanup_session(upload_id)
            
            logger.info(f"✅ 分片上传完成: {session['filename']}, 大小: {actual_size:,} bytes")
            
            return {
                "upload_id": upload_id,
                "filename": session["filename"],
                "file_path": str(target_file),
                "file_size": actual_size,
                "completed": True
            }
            
        except Exception as e:
            logger.error(f"❌ 完成上传失败: {e}")
            # 清理会话
            await self.cleanup_session(upload_id)
            raise HTTPException(status_code=500, detail=f"完成上传失败: {e}")
    
    async def cleanup_session(self, upload_id: str):
        """清理上传会话"""
        try:
            if upload_id in self.upload_sessions:
                session = self.upload_sessions[upload_id]
                session_dir = session["session_dir"]
                
                # 删除临时文件
                if session_dir.exists():
                    import shutil
                    shutil.rmtree(session_dir)
                
                # 删除会话
                del self.upload_sessions[upload_id]
                
                logger.info(f"🧹 清理上传会话: {upload_id}")
                
        except Exception as e:
            logger.warning(f"⚠️ 清理会话失败: {e}")
    
    async def get_upload_status(self, upload_id: str) -> Dict[str, Any]:
        """获取上传状态"""
        if upload_id not in self.upload_sessions:
            raise HTTPException(status_code=404, detail="上传会话不存在")
        
        session = self.upload_sessions[upload_id]
        progress = len(session["received_chunks"]) / session["total_chunks"] * 100
        
        return {
            "upload_id": upload_id,
            "filename": session["filename"],
            "total_size": session["total_size"],
            "total_chunks": session["total_chunks"],
            "received_chunks": len(session["received_chunks"]),
            "progress": progress,
            "completed": len(session["received_chunks"]) == session["total_chunks"]
        }

# 全局上传管理器实例
upload_manager = ChunkedUploadManager()
