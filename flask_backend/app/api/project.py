"""
项目管理API接口
处理项目创建、更新、删除等操作

注意：多用户版本使用用户独立工作目录架构
- 每个用户的数据存储在 flask_backend/output/{user_id}/ 目录
- 历史项目归档到 flask_backend/history/{user_id}/ 目录
- 匿名用户使用 'anonymous' 作为 user_id
"""
import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, g

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# 导入认证装饰器和存储服务
from app.auth.decorators import optional_login, get_current_user_id
from app.services.storage_service import StorageService

try:
    from app.utils.file_manager import FileManager  # type: ignore
    from app.utils.logger import get_logger  # type: ignore
except ImportError as e:
    print(f"Warning: Could not import utils modules: {e}")
    # 提供模拟类
    class FileManager:
        def __init__(self, project_name):
            self.project_name = project_name
    
    def get_logger(name):
        import logging
        return logging.getLogger(name)

bp = Blueprint('project', __name__)
logger = get_logger(__name__)


def get_user_output_dir() -> Path:
    """获取当前用户的工作目录"""
    user_id = get_current_user_id()
    storage_service = StorageService()
    return storage_service.get_user_work_dir(user_id)


@bp.route('/list', methods=['GET'])
@optional_login
def list_projects():
    """获取所有项目列表"""
    try:
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        projects = []
        
        if output_dir.exists():
            for project_dir in output_dir.iterdir():
                if project_dir.is_dir():
                    try:
                        # 读取项目元数据
                        metadata_file = project_dir / "project_metadata.json"
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            project_info = {
                                "project_name": project_dir.name,
                                "title": metadata.get("import_info", {}).get("title", project_dir.name),
                                "source": metadata.get("source", "unknown"),
                                "created_at": metadata.get("import_info", {}).get("imported_at", ""),
                                "status": "ready" if metadata.get("processing_ready") else "incomplete",
                                "slides_count": metadata.get("import_info", {}).get("total_slides", 0)
                            }
                            
                            # 检查视频文件是否存在
                            video_file = project_dir / "final_video.mp4"
                            if video_file.exists():
                                project_info["has_video"] = True
                                project_info["video_size"] = video_file.stat().st_size
                            else:
                                project_info["has_video"] = False
                            
                            projects.append(project_info)
                        else:
                            # 没有元数据的项目
                            projects.append({
                                "project_name": project_dir.name,
                                "title": project_dir.name,
                                "source": "unknown",
                                "status": "incomplete",
                                "created_at": "",
                                "slides_count": 0,
                                "has_video": False
                            })
                            
                    except Exception as e:
                        logger.warning(f"读取项目信息失败 {project_dir.name}: {e}")
        
        # 按创建时间排序
        projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'projects': projects,
                'total_count': len(projects)
            }
        })
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/<project_name>', methods=['GET'])
@optional_login
def get_project_detail(project_name):
    """获取项目详细信息"""
    try:
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        project_dir = output_dir  # 用户级别：使用用户工作目录
        
        if not project_dir.exists():
            return jsonify({
                'success': False,
                'message': '项目不存在'
            }), 404
        
        # 读取项目元数据
        metadata_file = project_dir / "project_info.json"
        ppt_data_file = project_dir / "ppt_data.json"
        
        project_info = {
            'project_name': project_name,
            'project_dir': str(project_dir)
        }
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            project_info.update(metadata)
        
        # 读取PPT数据（slides_data）
        if ppt_data_file.exists():
            with open(ppt_data_file, 'r', encoding='utf-8') as f:
                slides_data = json.load(f)
            project_info['slides_data'] = slides_data
        
        # 检查各种文件
        files_info = {}
        
        # 检查图片文件
        slides_dir = project_dir / "slides"
        if slides_dir.exists():
            image_files = list(slides_dir.glob("*.jpg")) + list(slides_dir.glob("*.png"))
            files_info['images'] = {
                'count': len(image_files),
                'files': [f.name for f in image_files]
            }
        
        # 检查音频文件
        audios_dir = project_dir / "audios"
        if audios_dir.exists():
            audio_files = list(audios_dir.glob("*.wav")) + list(audios_dir.glob("*.mp3"))
            files_info['audios'] = {
                'count': len(audio_files),
                'files': [f.name for f in audio_files]
            }
        
        # 检查字幕文件
        subtitles_dir = project_dir / "subtitles"
        if subtitles_dir.exists():
            subtitle_files = list(subtitles_dir.glob("*.srt"))
            files_info['subtitles'] = {
                'count': len(subtitle_files),
                'files': [f.name for f in subtitle_files]
            }
        
        # 检查视频文件
        video_files = list(project_dir.glob("*.mp4"))
        if video_files:
            files_info['videos'] = {
                'count': len(video_files),
                'files': [{'name': f.name, 'size': f.stat().st_size} for f in video_files]
            }
        
        project_info['files'] = files_info
        
        return jsonify({
            'success': True,
            'data': project_info
        })
        
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/<project_name>', methods=['PUT'])
@optional_login
def update_project(project_name):
    """更新项目信息，如果项目不存在则创建"""
    try:
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        project_dir = output_dir  # 用户级别：使用用户工作目录
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        # 如果项目不存在，创建项目目录结构
        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)
            (project_dir / "slides").mkdir(exist_ok=True)
            (project_dir / "audios").mkdir(exist_ok=True)
            (project_dir / "subtitles").mkdir(exist_ok=True)
        
        # 读取现有的元数据或创建新的
        metadata_file = project_dir / "project_info.json"
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"读取项目元数据失败: {e}")
        else:
            # 创建新项目的基础元数据
            metadata = {
                "project_name": project_name,
                "source": "manual",
                "created_at": datetime.now().isoformat(),
                "import_info": {
                    "title": data.get('title', project_name),
                    "description": data.get('description', ''),
                    "imported_at": datetime.now().isoformat(),
                    "total_slides": 0
                }
            }
        
        # 更新元数据
        if 'title' in data:
            if 'import_info' not in metadata:
                metadata['import_info'] = {}
            metadata['import_info']['title'] = data['title']
            metadata['import_info']['title'] = data['title']
        
        # 处理slides_data
        if 'slides_data' in data:
            slides_data = data['slides_data']
            
            # 保存PPT数据到文件
            ppt_data_file = project_dir / "ppt_data.json"
            try:
                with open(ppt_data_file, 'w', encoding='utf-8') as f:
                    json.dump(slides_data, f, ensure_ascii=False, indent=2)
                logger.info(f"PPT数据已保存到: {ppt_data_file}")
                
                # 更新slides数量
                if 'slides' in slides_data:
                    metadata['import_info']['total_slides'] = len(slides_data['slides'])
                
            except Exception as e:
                logger.error(f"保存PPT数据失败: {e}")
                return jsonify({
                    'success': False,
                    'message': f'保存PPT数据失败: {str(e)}'
                }), 500
        
        # 更新最后修改时间
        metadata['last_updated'] = datetime.now().isoformat()
        
        # 保存更新后的元数据
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存项目元数据失败: {e}")
            return jsonify({
                'success': False,
                'message': f'保存项目元数据失败: {str(e)}'
            }), 500
        
        logger.info(f"项目更新成功: {project_name}")
        return jsonify({
            'success': True,
            'message': '项目更新成功',
            'data': {
                'project_name': project_name,
                'title': metadata.get('import_info', {}).get('title', project_name),
                'created_at': metadata.get('created_at'),
                'updated_at': metadata.get('last_updated')
            }
        })
        
    except Exception as e:
        logger.error(f"更新项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/<project_name>', methods=['DELETE'])
@optional_login
def delete_project(project_name):
    """删除项目"""
    try:
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        project_dir = output_dir  # 用户级别：使用用户工作目录
        
        if not project_dir.exists():
            return jsonify({
                'success': False,
                'message': '项目不存在'
            }), 404
        
        # 删除项目目录
        shutil.rmtree(project_dir)
        
        logger.info(f"删除项目: {project_name}")
        
        return jsonify({
            'success': True,
            'message': f'项目 {project_name} 已成功删除'
        })
        
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/<project_name>/download', methods=['GET'])
@optional_login
def download_project_video(project_name):
    """下载项目生成的视频"""
    try:
        from flask import send_file
        
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        project_dir = output_dir  # 用户级别：使用用户工作目录
        
        if not project_dir.exists():
            return jsonify({
                'success': False,
                'message': '项目不存在'
            }), 404
        
        # 查找视频文件
        video_file = project_dir / "final_video.mp4"
        if not video_file.exists():
            # 尝试其他可能的视频文件名
            video_files = list(project_dir.glob("*.mp4"))
            if video_files:
                video_file = video_files[0]
            else:
                return jsonify({
                    'success': False,
                    'message': '项目视频文件不存在'
                }), 404
        
        return send_file(
            video_file,
            as_attachment=True,
            download_name=f"{project_name}_video.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"下载项目视频失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/create', methods=['POST'])
@optional_login
def create_project():
    """创建新项目"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        project_name = data.get('project_name')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称不能为空'
            }), 400
        
        # 清理项目名称
        clean_project_name = "".join(c for c in project_name if c.isalnum() or c in "._-")
        if not clean_project_name:
            return jsonify({
                'success': False,
                'message': '无效的项目名称'
            }), 400
        
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        project_dir = output_dir  # 用户级别：使用用户工作目录
        
        if project_dir.exists():
            return jsonify({
                'success': False,
                'message': '项目已存在'
            }), 409
        
        # 创建项目目录结构
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "slides").mkdir(exist_ok=True)
        (project_dir / "audios").mkdir(exist_ok=True)
        (project_dir / "subtitles").mkdir(exist_ok=True)
        
        # 创建项目元数据
        metadata = {
            "project_name": clean_project_name,
            "source": "manual",
            "created_at": datetime.now().isoformat(),
            "import_info": {
                "title": data.get('title', clean_project_name),
                "description": data.get('description', ''),
                "imported_at": datetime.now().isoformat(),
                "total_slides": 0
            },
            "processing_ready": False
        }
        
        metadata_file = project_dir / "project_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"创建新项目: {clean_project_name}")
        
        return jsonify({
            'success': True,
            'message': f'项目 {clean_project_name} 创建成功',
            'data': {
                'project_name': clean_project_name,
                'project_dir': str(project_dir)
            }
        })
        
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/<project_name>/upload-image', methods=['POST'])
@optional_login
def upload_project_image(project_name):
    """上传项目图片"""
    try:
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        project_dir = output_dir  # 用户级别：使用用户工作目录
        
        if not project_dir.exists():
            # 自动创建项目目录
            project_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"自动创建项目目录: {project_dir}")
        
        # 检查是否有上传的文件
        if 'image' not in request.files:
            logger.warning(f"图片上传请求缺少image字段: {project_name}")
            return jsonify({
                'success': False,
                'message': '没有上传图片文件'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            logger.warning(f"图片上传请求文件名为空: {project_name}")
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        # 获取幻灯片索引
        slide_index = request.form.get('slide_index', '0')
        try:
            slide_index_int = int(slide_index)
        except ValueError:
            logger.error(f"无效的slide_index: {slide_index}")
            return jsonify({
                'success': False,
                'message': f'无效的幻灯片索引: {slide_index}'
            }), 400
        
        # 确保slides目录存在
        slides_dir = project_dir / "slides"
        slides_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        filename = f"slide_{str(slide_index_int + 1).zfill(3)}.jpg"
        file_path = slides_dir / filename
        
        # 检查文件大小
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置到文件开头
        
        if file_size == 0:
            logger.error(f"上传的图片文件为空: {filename}")
            return jsonify({
                'success': False,
                'message': '上传的图片文件为空'
            }), 400
        
        if file_size > 50 * 1024 * 1024:  # 50MB限制
            logger.error(f"上传的图片文件过大: {filename}, 大小: {file_size}")
            return jsonify({
                'success': False,
                'message': '图片文件过大，请压缩后重试'
            }), 400
        
        # 验证文件类型
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        file_ext = Path(file.filename or '').suffix.lower() if file.filename else ''
        if file_ext not in allowed_extensions:
            logger.error(f"不支持的文件类型: {file.filename}")
            return jsonify({
                'success': False,
                'message': f'不支持的文件类型: {file_ext}'
            }), 400
        
        # 保存文件
        try:
            file.save(str(file_path))
            
            # 验证保存的文件
            saved_size = file_path.stat().st_size
            if saved_size == 0:
                file_path.unlink()  # 删除空文件
                raise Exception("保存的文件为空")
            
            # 尝试打开图片验证完整性
            from PIL import Image
            try:
                with Image.open(file_path) as img:
                    img_format = img.format
                    img_size = img.size
                    logger.info(f"图片验证成功: {filename}, 格式: {img_format}, 尺寸: {img_size}")
            except Exception as img_error:
                logger.error(f"图片文件损坏: {filename}, 错误: {img_error}")
                file_path.unlink()  # 删除损坏的文件
                return jsonify({
                    'success': False,
                    'message': f'图片文件损坏或格式不正确: {img_error}'
                }), 400
            
        except Exception as save_error:
            logger.error(f"保存图片文件失败: {filename}, 错误: {save_error}")
            return jsonify({
                'success': False,
                'message': f'保存图片文件失败: {save_error}'
            }), 500
        
        logger.info(f"图片上传成功: {project_name}/{filename} ({file_size:,} bytes -> {saved_size:,} bytes)")
        
        return jsonify({
            'success': True,
            'message': '图片上传成功',
            'data': {
                'filename': filename,
                'file_path': str(file_path),
                'slide_index': slide_index,
                'file_size': saved_size,
                'original_size': file_size
            }
        })
        
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        return jsonify({
            'success': False,
            'message': f'图片上传失败: {str(e)}'
        }), 500


@bp.route('/<project_name>/upload-images-chunked', methods=['POST'])
@optional_login
def upload_project_images_chunked(project_name):
    """分片上传项目图片"""
    try:
        # 使用用户专属工作目录
        output_dir = get_user_output_dir()
        project_dir = output_dir  # 用户级别：使用用户工作目录
        
        if not project_dir.exists():
            return jsonify({
                'success': False,
                'message': f'项目 {project_name} 不存在'
            }), 404
        
        # 获取分片信息
        slide_index = request.form.get('slide_index')
        upload_id = request.form.get('upload_id')
        
        if not slide_index or not upload_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        # 分片上传逻辑（简化实现）
        # 这里可以实现更复杂的分片合并逻辑
        
        logger.info(f"分片上传处理: {project_name}, slide_index={slide_index}, upload_id={upload_id}")
        
        return jsonify({
            'success': True,
            'message': '分片上传处理成功',
            'data': {
                'slide_index': slide_index,
                'upload_id': upload_id
            }
        })
        
    except Exception as e:
        logger.error(f"分片上传失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ===== 历史记录管理 API =====

def get_user_history_dir() -> Path:
    """获取当前用户的历史记录目录"""
    user_id = get_current_user_id()
    flask_backend_dir = Path(__file__).parent.parent.parent
    return flask_backend_dir / "history" / user_id


@bp.route('/history', methods=['GET'])
@optional_login
def get_history_list():
    """
    获取用户的历史项目列表
    
    返回格式:
    {
        "success": true,
        "data": [
            {
                "archive_id": "项目名_20231128_120000",
                "project_name": "项目名",
                "archived_at": "2023-11-28T12:00:00",
                "video_available": true,
                "thumbnail": "slides/slide_001.jpg",
                "duration_seconds": 120.5
            },
            ...
        ]
    }
    """
    try:
        history_dir = get_user_history_dir()
        
        if not history_dir.exists():
            return jsonify({
                'success': True,
                'data': [],
                'message': '暂无历史记录'
            })
        
        history_list = []
        
        # 遍历历史目录
        for archive_dir in sorted(history_dir.iterdir(), reverse=True):
            if not archive_dir.is_dir():
                continue
            
            metadata_path = archive_dir / "archive_metadata.json"
            if not metadata_path.exists():
                continue
            
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 检查视频是否存在
                video_path = archive_dir / "final_video.mp4"
                video_available = video_path.exists()
                
                # 获取缩略图
                thumbnail = None
                slides_dir = archive_dir / "slides"
                if slides_dir.exists():
                    thumbnails = list(slides_dir.glob("*.jpg"))
                    if thumbnails:
                        thumbnail = f"history/{get_current_user_id()}/{archive_dir.name}/slides/{thumbnails[0].name}"
                
                history_item = {
                    "archive_id": archive_dir.name,
                    "project_name": metadata.get("project_name", "未命名项目"),
                    "archived_at": metadata.get("archived_at"),
                    "video_available": video_available,
                    "thumbnail": thumbnail,
                    "duration_seconds": metadata.get("total_duration_seconds"),
                    "execution_id": metadata.get("execution_id"),
                    "workflow_status": metadata.get("workflow_status", "unknown")
                }
                
                history_list.append(history_item)
                
            except Exception as e:
                logger.warning(f"读取历史记录失败: {archive_dir.name}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'data': history_list,
            'total': len(history_list)
        })
        
    except Exception as e:
        logger.error(f"获取历史记录列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/history/<archive_id>', methods=['GET'])
@optional_login
def get_history_detail(archive_id):
    """获取历史项目详情"""
    try:
        history_dir = get_user_history_dir()
        archive_dir = history_dir / archive_id
        
        if not archive_dir.exists():
            return jsonify({
                'success': False,
                'message': '历史记录不存在'
            }), 404
        
        metadata_path = archive_dir / "archive_metadata.json"
        if not metadata_path.exists():
            return jsonify({
                'success': False,
                'message': '历史记录元数据不存在'
            }), 404
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 检查各文件是否存在
        video_path = archive_dir / "final_video.mp4"
        ppt_data_path = archive_dir / "ppt_data.json"
        
        detail = {
            **metadata,
            "video_available": video_path.exists(),
            "video_size_mb": video_path.stat().st_size / (1024 * 1024) if video_path.exists() else 0,
            "ppt_data_available": ppt_data_path.exists(),
            "archive_dir": str(archive_dir)
        }
        
        # 列出字幕文件
        subtitles_dir = archive_dir / "subtitles"
        if subtitles_dir.exists():
            detail["subtitle_files"] = [f.name for f in subtitles_dir.glob("*.srt")]
        
        # 列出幻灯片预览
        slides_dir = archive_dir / "slides"
        if slides_dir.exists():
            detail["slide_thumbnails"] = [f.name for f in slides_dir.glob("*.jpg")]
        
        return jsonify({
            'success': True,
            'data': detail
        })
        
    except Exception as e:
        logger.error(f"获取历史记录详情失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/history/<archive_id>', methods=['DELETE'])
@optional_login
def delete_history(archive_id):
    """删除历史记录"""
    try:
        history_dir = get_user_history_dir()
        archive_dir = history_dir / archive_id
        
        if not archive_dir.exists():
            return jsonify({
                'success': False,
                'message': '历史记录不存在'
            }), 404
        
        # 删除整个归档目录
        shutil.rmtree(archive_dir)
        
        logger.info(f"已删除历史记录: {archive_id}")
        
        return jsonify({
            'success': True,
            'message': '历史记录已删除'
        })
        
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/history/<archive_id>/preview', methods=['GET'])
@optional_login
def preview_history_video(archive_id):
    """预览历史视频（流式播放）"""
    from flask import send_file, request, Response
    
    try:
        history_dir = get_user_history_dir()
        archive_dir = history_dir / archive_id
        video_path = archive_dir / "final_video.mp4"
        
        if not video_path.exists():
            return jsonify({
                'success': False,
                'message': '视频文件不存在'
            }), 404
        
        # 支持 Range 请求，用于视频拖动
        file_size = video_path.stat().st_size
        range_header = request.headers.get('Range')
        
        if range_header:
            # 解析 Range 请求
            byte_start = 0
            byte_end = file_size - 1
            
            if range_header.startswith('bytes='):
                range_spec = range_header[6:]
                if '-' in range_spec:
                    start_str, end_str = range_spec.split('-', 1)
                    if start_str:
                        byte_start = int(start_str)
                    if end_str:
                        byte_end = int(end_str)
            
            # 确保范围有效
            byte_end = min(byte_end, file_size - 1)
            content_length = byte_end - byte_start + 1
            
            def generate():
                with open(video_path, 'rb') as f:
                    f.seek(byte_start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            response = Response(
                generate(),
                status=206,
                mimetype='video/mp4',
                direct_passthrough=True
            )
            response.headers['Content-Range'] = f'bytes {byte_start}-{byte_end}/{file_size}'
            response.headers['Content-Length'] = content_length
            response.headers['Accept-Ranges'] = 'bytes'
            return response
        else:
            # 完整文件响应
            return send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=False
            )
        
    except Exception as e:
        logger.error(f"预览历史视频失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/history/<archive_id>/download', methods=['GET'])
@optional_login
def download_history_video(archive_id):
    """下载历史视频"""
    from flask import send_file
    
    try:
        history_dir = get_user_history_dir()
        archive_dir = history_dir / archive_id
        video_path = archive_dir / "final_video.mp4"
        
        if not video_path.exists():
            return jsonify({
                'success': False,
                'message': '视频文件不存在'
            }), 404
        
        # 获取项目名用于下载文件名
        metadata_path = archive_dir / "archive_metadata.json"
        download_name = f"{archive_id}.mp4"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    project_name = metadata.get("project_name", archive_id)
                    download_name = f"{project_name}.mp4"
            except:
                pass
        
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        logger.error(f"下载历史视频失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/history/<archive_id>/download-bundle', methods=['GET'])
@optional_login
def download_history_bundle(archive_id):
    """下载历史项目打包（视频+ppt_data.json）"""
    from flask import send_file
    import zipfile
    import tempfile
    
    try:
        history_dir = get_user_history_dir()
        archive_dir = history_dir / archive_id
        
        if not archive_dir.exists():
            return jsonify({
                'success': False,
                'message': '归档不存在'
            }), 404
        
        video_path = archive_dir / "final_video.mp4"
        ppt_data_path = archive_dir / "ppt_data.json"
        
        # 获取项目名用于 ZIP 文件名
        metadata_path = archive_dir / "archive_metadata.json"
        project_name = archive_id
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    project_name = metadata.get("project_name", archive_id)
            except:
                pass
        
        # 创建临时 ZIP 文件
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip_path = temp_zip.name
        temp_zip.close()
        
        try:
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加视频文件
                if video_path.exists():
                    zipf.write(video_path, f"{project_name}.mp4")
                
                # 添加 ppt_data.json
                if ppt_data_path.exists():
                    zipf.write(ppt_data_path, "ppt_data.json")
                
                # 添加元数据
                if metadata_path.exists():
                    zipf.write(metadata_path, "archive_metadata.json")
            
            return send_file(
                temp_zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{project_name}.zip"
            )
        finally:
            # 延迟删除临时文件（Flask 会在响应完成后处理）
            import atexit
            atexit.register(lambda: os.unlink(temp_zip_path) if os.path.exists(temp_zip_path) else None)
        
    except Exception as e:
        logger.error(f"下载历史项目打包失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/history/<archive_id>/restore', methods=['POST'])
@optional_login
def restore_history_to_workspace(archive_id):
    """
    将历史项目恢复到工作区
    用于重新编辑或重新生成视频
    """
    try:
        history_dir = get_user_history_dir()
        archive_dir = history_dir / archive_id
        
        if not archive_dir.exists():
            return jsonify({
                'success': False,
                'message': '历史记录不存在'
            }), 404
        
        # 获取用户工作目录
        output_dir = get_user_output_dir()
        
        # 恢复 ppt_data.json
        ppt_data_src = archive_dir / "ppt_data.json"
        ppt_data_dst = output_dir / "ppt_data.json"
        
        if ppt_data_src.exists():
            shutil.copy2(ppt_data_src, ppt_data_dst)
            logger.info(f"已恢复 ppt_data.json 到工作区")
        else:
            return jsonify({
                'success': False,
                'message': '归档中没有 ppt_data.json'
            }), 400
        
        return jsonify({
            'success': True,
            'message': '历史项目已恢复到工作区',
            'data': {
                'restored_to': str(output_dir),
                'archive_id': archive_id
            }
        })
        
    except Exception as e:
        logger.error(f"恢复历史项目失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
