"""
Step 01.5: 图片上传处理器
专门负责处理前端上传的PPT图片文件
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class ImageUploadStatus:
    """图片上传状态"""
    slide_index: int
    image_filename: str
    upload_status: str  # 'pending', 'uploading', 'completed', 'failed'
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    uploaded_at: Optional[str] = None

@dataclass
class ProjectImageStatus:
    """项目图片状态"""
    project_name: str
    project_path: str
    total_slides: int
    uploaded_images: List[ImageUploadStatus]
    upload_complete: bool = False
    last_updated: Optional[str] = None

class ImageUploadManager:
    """图片上传管理器"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.slides_dir = project_dir / "slides"
        self.status_file = self.slides_dir / "image_upload_status.json"
        
        # 确保目录存在
        self.slides_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化状态
        self.status = self._load_status()
        
        logger.info(f"图片上传管理器初始化: {project_dir}")
    
    def _load_status(self) -> ProjectImageStatus:
        """加载上传状态"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换为对象
                uploaded_images = [
                    ImageUploadStatus(**img) for img in data.get('uploaded_images', [])
                ]
                
                return ProjectImageStatus(
                    project_name=data.get('project_name', ''),
                    project_path=str(self.project_dir),
                    total_slides=data.get('total_slides', 0),
                    uploaded_images=uploaded_images,
                    upload_complete=data.get('upload_complete', False),
                    last_updated=data.get('last_updated')
                )
                
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        
        # 默认状态
        return ProjectImageStatus(
            project_name=self.project_dir.name,
            project_path=str(self.project_dir),
            total_slides=0,
            uploaded_images=[]
        )
    
    def _save_status(self):
        """保存上传状态"""
        try:
            self.status.last_updated = datetime.now().isoformat()
            
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.status), f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def initialize_for_slides(self, total_slides: int) -> Dict[str, Any]:
        """为指定数量的slides初始化上传状态"""
        logger.info(f"初始化图片上传状态: {total_slides} 个slides")
        
        self.status.total_slides = total_slides
        self.status.uploaded_images = []
        
        # 为每个slide创建初始状态
        for i in range(total_slides):
            image_status = ImageUploadStatus(
                slide_index=i,
                image_filename=f"slide_{str(i + 1).zfill(3)}.jpg",
                upload_status='pending'
            )
            self.status.uploaded_images.append(image_status)
        
        self.status.upload_complete = False
        self._save_status()
        
        return {
            "total_slides": total_slides,
            "initialized_images": len(self.status.uploaded_images),
            "status_file": str(self.status_file)
        }
    
    def update_image_status(self, slide_index: int, status: str, file_size: Optional[int] = None, error_message: Optional[str] = None):
        """更新单个图片的上传状态"""
        if 0 <= slide_index < len(self.status.uploaded_images):
            image_status = self.status.uploaded_images[slide_index]
            image_status.upload_status = status
            
            if file_size is not None:
                image_status.file_size = file_size
            
            if error_message:
                image_status.error_message = error_message
            
            if status == 'completed':
                image_status.uploaded_at = datetime.now().isoformat()
            
            logger.info(f"更新图片状态: slide_{slide_index + 1} -> {status}")
            
            # 检查是否全部完成
            self._check_upload_complete()
            self._save_status()
    
    def _check_upload_complete(self):
        """检查是否所有图片都已上传完成"""
        if not self.status.uploaded_images:
            return
        
        completed_count = sum(1 for img in self.status.uploaded_images if img.upload_status == 'completed')
        self.status.upload_complete = (completed_count == self.status.total_slides)
        
        if self.status.upload_complete:
            logger.info(f"所有图片上传完成: {completed_count}/{self.status.total_slides}")
    
    def get_upload_progress(self) -> Dict[str, Any]:
        """获取上传进度"""
        if not self.status.uploaded_images:
            return {
                "total_slides": 0,
                "completed": 0,
                "pending": 0,
                "failed": 0,
                "progress_percent": 0,
                "upload_complete": False
            }
        
        completed = sum(1 for img in self.status.uploaded_images if img.upload_status == 'completed')
        pending = sum(1 for img in self.status.uploaded_images if img.upload_status in ['pending', 'uploading'])
        failed = sum(1 for img in self.status.uploaded_images if img.upload_status == 'failed')
        
        progress_percent = (completed / self.status.total_slides * 100) if self.status.total_slides > 0 else 0
        
        return {
            "total_slides": self.status.total_slides,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "progress_percent": round(progress_percent, 2),
            "upload_complete": self.status.upload_complete,
            "images": [asdict(img) for img in self.status.uploaded_images]
        }
    
    def verify_uploaded_images(self) -> Dict[str, Any]:
        """验证已上传的图片文件"""
        logger.info("验证已上传的图片文件...")
        
        verification_result = {
            "verified_images": [],
            "missing_images": [],
            "total_expected": self.status.total_slides,
            "total_found": 0,
            "verification_complete": False
        }
        
        for image_status in self.status.uploaded_images:
            image_path = self.slides_dir / image_status.image_filename
            
            if image_path.exists() and image_path.is_file():
                file_size = image_path.stat().st_size
                verification_result["verified_images"].append({
                    "slide_index": image_status.slide_index,
                    "filename": image_status.image_filename,
                    "file_size": file_size,
                    "upload_status": image_status.upload_status
                })
                
                # 更新实际文件大小
                self.update_image_status(image_status.slide_index, 'completed', file_size)
                
            else:
                verification_result["missing_images"].append({
                    "slide_index": image_status.slide_index,
                    "filename": image_status.image_filename,
                    "upload_status": image_status.upload_status
                })
                
                # 标记为失败
                self.update_image_status(image_status.slide_index, 'failed', error_message="文件不存在")
        
        verification_result["total_found"] = len(verification_result["verified_images"])
        verification_result["verification_complete"] = (verification_result["total_found"] == verification_result["total_expected"])
        
        logger.info(f"图片验证完成: {verification_result['total_found']}/{verification_result['total_expected']} 个文件")
        
        return verification_result
    
    def get_missing_images(self) -> List[Dict[str, Any]]:
        """获取缺失的图片列表"""
        missing = []
        
        for image_status in self.status.uploaded_images:
            if image_status.upload_status != 'completed':
                image_path = self.slides_dir / image_status.image_filename
                
                if not image_path.exists():
                    missing.append({
                        "slide_index": image_status.slide_index,
                        "filename": image_status.image_filename,
                        "expected_path": str(image_path),
                        "status": image_status.upload_status,
                        "error": image_status.error_message
                    })
        
        return missing
    
    def generate_fallback_images(self) -> Dict[str, Any]:
        """为缺失的图片生成回退图片"""
        logger.info("开始生成回退图片...")
        
        missing_images = self.get_missing_images()
        generated_count = 0
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            for missing in missing_images:
                slide_index = missing["slide_index"]
                filename = missing["filename"]
                image_path = self.slides_dir / filename
                
                # 创建简单的回退图片
                img = Image.new('RGB', (1920, 1080), color='white')
                draw = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 72)
                except:
                    font = ImageFont.load_default()
                
                # 绘制内容
                draw.text((500, 400), f"Slide {slide_index + 1}", fill='black', font=font)
                draw.text((500, 500), "图片生成失败", fill='red', font=font)
                draw.text((500, 600), "使用回退图片", fill='gray', font=font)
                
                # 保存图片
                img.save(image_path, 'JPEG', quality=85)
                file_size = image_path.stat().st_size
                
                # 更新状态
                self.update_image_status(slide_index, 'completed', file_size)
                generated_count += 1
                
                logger.info(f"生成回退图片: {filename} ({file_size} bytes)")
                
        except Exception as e:
            logger.error(f"生成回退图片失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "generated_count": generated_count
            }
        
        return {
            "success": True,
            "generated_count": generated_count,
            "missing_before": len(missing_images),
            "total_images": self.status.total_slides
        }

def process_image_upload_step(project_dir: Path, force_verify: bool = False) -> Dict[str, Any]:
    """
    处理图片上传步骤
    
    Args:
        project_dir: 项目目录
        force_verify: 是否强制验证所有图片
    
    Returns:
        处理结果
    """
    logger.info(f"开始处理图片上传步骤: {project_dir}")
    
    try:
        # 初始化图片上传管理器
        upload_manager = ImageUploadManager(project_dir)
        
        # 从slides_metadata.json读取slides信息
        metadata_file = project_dir / "slides" / "slides_metadata.json"
        if not metadata_file.exists():
            return {
                "success": False,
                "error": "slides_metadata.json 文件不存在",
                "project_dir": str(project_dir)
            }
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        slides = metadata.get('slides', [])
        total_slides = len(slides)
        
        if total_slides == 0:
            return {
                "success": False,
                "error": "没有找到slides数据",
                "metadata_file": str(metadata_file)
            }
        
        # 初始化上传状态
        init_result = upload_manager.initialize_for_slides(total_slides)
        logger.info(f"初始化结果: {init_result}")
        
        # 验证现有图片
        verification_result = upload_manager.verify_uploaded_images()
        logger.info(f"验证结果: {verification_result}")
        
        # 获取上传进度
        progress = upload_manager.get_upload_progress()
        
        result = {
            "success": True,
            "project_dir": str(project_dir),
            "total_slides": total_slides,
            "verification": verification_result,
            "progress": progress,
            "upload_manager_status": str(upload_manager.status_file)
        }
        
        # 如果有缺失的图片，生成回退图片
        if verification_result["missing_images"]:
            logger.warning(f"发现 {len(verification_result['missing_images'])} 个缺失图片，生成回退图片...")
            fallback_result = upload_manager.generate_fallback_images()
            result["fallback_generated"] = fallback_result
            
            # 重新验证
            final_verification = upload_manager.verify_uploaded_images()
            result["final_verification"] = final_verification
        
        logger.info(f"图片上传步骤完成: {result}")
        return result
        
    except Exception as e:
        logger.error(f"图片上传步骤失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_dir": str(project_dir)
        }

async def async_process_image_upload_step(project_dir: Path, force_verify: bool = False) -> Dict[str, Any]:
    """异步版本的图片上传处理"""
    return await asyncio.get_event_loop().run_in_executor(
        None, process_image_upload_step, project_dir, force_verify
    )

if __name__ == "__main__":
    # 测试代码
    import sys
    if len(sys.argv) > 1:
        test_project_dir = Path(sys.argv[1])
        result = process_image_upload_step(test_project_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python step01_5_image_uploader.py <project_dir>")
