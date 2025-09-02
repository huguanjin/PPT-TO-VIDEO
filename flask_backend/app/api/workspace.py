#!/usr/bin/env python3
"""
工作空间管理API
支持单一工作区模式和智能归档功能
"""

from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logger = logging.getLogger(__name__)

workspace_bp = Blueprint('workspace', __name__)

class WorkspaceManager:
    def __init__(self):
        # 使用flask_backend/output目录，而不是项目根目录
        from pathlib import Path
        flask_backend_dir = Path(__file__).parent.parent.parent
        self.output_dir = flask_backend_dir / 'output'
        self.history_dir = flask_backend_dir / 'history'
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """确保目录存在"""
        self.output_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
        
        # 创建output子目录
        for subdir in ['slides', 'audio', 'video_clips', 'subtitles', 'final', 'scripts', 'temp']:
            (self.output_dir / subdir).mkdir(exist_ok=True)
    
    def has_workspace_content(self) -> bool:
        """检查工作空间是否有内容"""
        workspace_file = self.output_dir / 'workspace.json'
        slides_dir = self.output_dir / 'slides'
        ppt_data_file = self.output_dir / 'ppt_data.json'
        
        return (workspace_file.exists() or 
                ppt_data_file.exists() or
                (slides_dir.exists() and any(slides_dir.iterdir())))
    
    def load_workspace(self) -> dict:
        """加载工作空间数据"""
        workspace_file = self.output_dir / 'workspace.json'
        ppt_data_file = self.output_dir / 'ppt_data.json'
        
        # 优先从workspace.json加载
        if workspace_file.exists():
            try:
                with open(workspace_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载workspace.json失败: {e}")
        
        # 兼容现有的ppt_data.json
        if ppt_data_file.exists():
            try:
                with open(ppt_data_file, 'r', encoding='utf-8') as f:
                    ppt_data = json.load(f)
                    return {
                        'title': ppt_data.get('project_name', '我的演示文稿'),
                        'slides': json.dumps(ppt_data.get('slides', [])),
                        'last_modified': datetime.fromtimestamp(
                            ppt_data_file.stat().st_mtime
                        ).isoformat()
                    }
            except Exception as e:
                logger.error(f"加载ppt_data.json失败: {e}")
        
        return {}
    
    def save_workspace(self, slides: str, title: str) -> bool:
        """保存工作空间"""
        try:
            workspace_data = {
                'slides': slides,
                'title': title,
                'last_modified': datetime.now().isoformat()
            }
            
            workspace_file = self.output_dir / 'workspace.json'
            with open(workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, ensure_ascii=False, indent=2)
            
            # 同时保存为ppt_data.json格式以兼容现有流程
            try:
                slides_data = json.loads(slides) if isinstance(slides, str) else slides
                ppt_data = {
                    'project_name': title,
                    'slides': slides_data,
                    'created_at': datetime.now().isoformat()
                }
                
                ppt_data_file = self.output_dir / 'ppt_data.json'
                with open(ppt_data_file, 'w', encoding='utf-8') as f:
                    json.dump(ppt_data, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                logger.warning(f"保存ppt_data.json失败: {e}")
            
            return True
        except Exception as e:
            logger.error(f"保存工作空间失败: {e}")
            return False
    
    def archive_workspace(self, archive_name: str) -> tuple[bool, str]:
        """归档当前工作空间"""
        try:
            if not self.has_workspace_content():
                return False, "当前工作空间没有内容"
            
            # 清理归档名称
            safe_name = "".join(c for c in archive_name if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_name:
                safe_name = "未命名项目"
            
            # 创建归档目录
            archive_dir = self.history_dir / safe_name
            counter = 1
            original_name = safe_name
            while archive_dir.exists():
                archive_dir = self.history_dir / f"{original_name}_{counter}"
                counter += 1
            
            archive_dir.mkdir(parents=True)
            
            # 移动所有文件到归档目录
            moved_items = []
            for item in self.output_dir.iterdir():
                if item.name.startswith('.'):  # 跳过隐藏文件
                    continue
                    
                dest_path = archive_dir / item.name
                if item.is_file():
                    shutil.move(str(item), str(dest_path))
                    moved_items.append(item.name)
                elif item.is_dir():
                    shutil.move(str(item), str(dest_path))
                    moved_items.append(f"{item.name}/")
            
            # 添加归档元数据
            metadata = {
                'name': archive_name,
                'archived_at': datetime.now().isoformat(),
                'moved_items': moved_items,
                'folder_name': archive_dir.name
            }
            
            with open(archive_dir / 'archive_info.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 重新创建工作目录
            self._ensure_dirs()
            
            logger.info(f"成功归档项目: {archive_dir.name}")
            return True, f"已归档到: {archive_dir.name}"
            
        except Exception as e:
            logger.error(f"归档失败: {e}")
            return False, f"归档失败: {str(e)}"
    
    def get_archives(self) -> list:
        """获取归档列表"""
        archives = []
        
        if not self.history_dir.exists():
            return archives
        
        for archive_dir in self.history_dir.iterdir():
            if not archive_dir.is_dir():
                continue
            
            try:
                info_file = archive_dir / 'archive_info.json'
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                else:
                    # 兼容没有元数据的旧归档
                    info = {
                        'name': archive_dir.name,
                        'archived_at': datetime.fromtimestamp(
                            archive_dir.stat().st_mtime
                        ).isoformat(),
                        'folder_name': archive_dir.name
                    }
                
                # 统计信息
                slides_dir = archive_dir / 'slides'
                slide_count = 0
                if slides_dir.exists():
                    slide_count = len([f for f in slides_dir.iterdir() 
                                     if f.suffix.lower() in ['.jpg', '.jpeg', '.png']])
                
                final_dir = archive_dir / 'final'
                has_video = False
                if final_dir.exists():
                    has_video = any(f.suffix.lower() in ['.mp4', '.avi', '.mov'] 
                                  for f in final_dir.iterdir())
                
                # 获取文件大小
                total_size = sum(f.stat().st_size for f in archive_dir.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)  # 转换为MB
                
                archives.append({
                    'name': info['name'],
                    'archived_at': info['archived_at'],
                    'slide_count': slide_count,
                    'has_video': has_video,
                    'folder_name': info.get('folder_name', archive_dir.name),
                    'size_mb': round(size_mb, 2)
                })
                
            except Exception as e:
                logger.warning(f"读取归档信息失败 {archive_dir.name}: {e}")
                # 添加基本信息
                archives.append({
                    'name': archive_dir.name,
                    'archived_at': datetime.fromtimestamp(
                        archive_dir.stat().st_mtime
                    ).isoformat(),
                    'slide_count': 0,
                    'has_video': False,
                    'folder_name': archive_dir.name,
                    'size_mb': 0
                })
        
        # 按归档时间倒序排列
        archives.sort(key=lambda x: x['archived_at'], reverse=True)
        return archives
    
    def restore_archive(self, folder_name: str) -> tuple[bool, str]:
        """恢复归档"""
        try:
            archive_dir = self.history_dir / folder_name
            if not archive_dir.exists():
                return False, f"未找到归档: {folder_name}"
            
            # 清空当前工作空间
            for item in self.output_dir.iterdir():
                if item.name.startswith('.'):  # 跳过隐藏文件
                    continue
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            
            # 复制归档内容到工作空间
            for item in archive_dir.iterdir():
                if item.name == 'archive_info.json':
                    continue
                
                dest_path = self.output_dir / item.name
                if item.is_file():
                    shutil.copy2(str(item), str(dest_path))
                elif item.is_dir():
                    shutil.copytree(str(item), str(dest_path))
            
            logger.info(f"成功恢复归档: {folder_name}")
            return True, f"已恢复归档"
            
        except Exception as e:
            logger.error(f"恢复归档失败: {e}")
            return False, f"恢复失败: {str(e)}"
    
    def delete_archive(self, folder_name: str) -> tuple[bool, str]:
        """删除归档"""
        try:
            archive_dir = self.history_dir / folder_name
            if not archive_dir.exists():
                return False, f"未找到归档: {folder_name}"
            
            shutil.rmtree(archive_dir)
            logger.info(f"成功删除归档: {folder_name}")
            return True, "归档已删除"
            
        except Exception as e:
            logger.error(f"删除归档失败: {e}")
            return False, f"删除失败: {str(e)}"

# 全局实例
workspace_manager = WorkspaceManager()

@workspace_bp.route('/check', methods=['GET'])
def check_workspace():
    """检查工作空间是否有内容"""
    try:
        exists = workspace_manager.has_workspace_content()
        return jsonify({'success': True, 'exists': exists})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/load', methods=['GET'])
def load_workspace():
    """加载工作空间数据"""
    try:
        data = workspace_manager.load_workspace()
        return jsonify({'success': True, **data})
    except Exception as e:
        logger.error(f"加载工作空间失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/save', methods=['POST'])
def save_workspace():
    """保存工作空间 - 无限制（支持频繁保存）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
            
        slides = data.get('slides', '[]')
        title = data.get('title', '我的演示文稿')
        
        success = workspace_manager.save_workspace(slides, title)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"保存工作空间失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/archive', methods=['POST'])
def archive_workspace():
    """归档当前工作空间"""
    try:
        data = request.get_json()
        if not data or not data.get('archive_name'):
            return jsonify({'success': False, 'error': '归档名称不能为空'}), 400
            
        archive_name = data.get('archive_name').strip()
        
        success, message = workspace_manager.archive_workspace(archive_name)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        logger.error(f"归档工作空间失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/archives', methods=['GET'])
def get_archives():
    """获取归档列表"""
    try:
        archives = workspace_manager.get_archives()
        return jsonify({'success': True, 'archives': archives})
    except Exception as e:
        logger.error(f"获取归档列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/restore', methods=['POST'])
def restore_archive():
    """恢复归档"""
    try:
        data = request.get_json()
        if not data or not data.get('folder_name'):
            return jsonify({'success': False, 'error': '归档文件夹名称不能为空'}), 400
            
        folder_name = data.get('folder_name')
        
        success, message = workspace_manager.restore_archive(folder_name)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        logger.error(f"恢复归档失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workspace_bp.route('/delete', methods=['DELETE'])
def delete_archive():
    """删除归档"""
    try:
        data = request.get_json()
        if not data or not data.get('folder_name'):
            return jsonify({'success': False, 'error': '归档文件夹名称不能为空'}), 400
            
        folder_name = data.get('folder_name')
        
        success, message = workspace_manager.delete_archive(folder_name)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        logger.error(f"删除归档失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
