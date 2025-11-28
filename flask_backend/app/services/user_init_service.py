"""
用户初始化服务
负责新用户登录后的工作目录初始化和默认配置创建
"""
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from app.services.storage_service import StorageService
from app.models.user_config import get_user_config_service
from app.services.system_config_service import get_system_config_service

logger = logging.getLogger(__name__)


class UserInitService:
    """用户初始化服务 - 处理新用户的工作目录和配置初始化"""
    
    def __init__(self):
        self.storage_service = StorageService()
        self.user_config_service = get_user_config_service()
        self.system_config_service = get_system_config_service()
        
        # 模板资源目录
        self.templates_dir = self.storage_service.base_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # 默认模板文件
        self.default_ppt_template = self.templates_dir / "default_ppt_data.json"
    
    def initialize_user(self, user_id: str, username: str = None) -> Dict[str, Any]:
        """
        初始化新用户的完整环境
        
        Args:
            user_id: 用户ID
            username: 用户名（用于日志）
            
        Returns:
            初始化结果信息
        """
        result = {
            "user_id": user_id,
            "username": username,
            "work_dir_created": False,
            "config_created": False,
            "template_copied": False,
            "errors": []
        }
        
        try:
            # 1. 初始化工作目录
            work_dir = self._init_work_directory(user_id)
            result["work_dir"] = str(work_dir)
            result["work_dir_created"] = True
            logger.info(f"✅ 用户 {username or user_id} 工作目录初始化完成: {work_dir}")
            
        except Exception as e:
            result["errors"].append(f"工作目录初始化失败: {str(e)}")
            logger.error(f"❌ 用户 {username or user_id} 工作目录初始化失败: {e}")
        
        try:
            # 2. 初始化用户配置
            config = self._init_user_config(user_id)
            result["config_created"] = config is not None
            if config:
                logger.info(f"✅ 用户 {username or user_id} 配置初始化完成")
            
        except Exception as e:
            result["errors"].append(f"用户配置初始化失败: {str(e)}")
            logger.error(f"❌ 用户 {username or user_id} 配置初始化失败: {e}")
        
        try:
            # 3. 复制默认模板到工作目录
            template_copied = self._copy_default_template(user_id)
            result["template_copied"] = template_copied
            if template_copied:
                logger.info(f"✅ 用户 {username or user_id} 默认模板初始化完成")
            
        except Exception as e:
            result["errors"].append(f"默认模板初始化失败: {str(e)}")
            logger.error(f"❌ 用户 {username or user_id} 默认模板初始化失败: {e}")
        
        return result
    
    def _init_work_directory(self, user_id: str) -> Path:
        """
        初始化用户工作目录
        
        Args:
            user_id: 用户ID
            
        Returns:
            工作目录路径
        """
        work_dir = self.storage_service.get_user_work_dir(user_id)
        
        # 确保所有子目录存在
        subdirs = [
            "slides",       # 幻灯片图片
            "scripts",      # 解说词
            "audio",        # 音频文件
            "video_clips",  # 视频片段
            "subtitles",    # 字幕文件
            "final",        # 最终视频
            "temp",         # 临时文件
            "logs",         # 日志文件
        ]
        
        for subdir in subdirs:
            (work_dir / subdir).mkdir(exist_ok=True)
        
        return work_dir
    
    def _init_user_config(self, user_id: str):
        """
        初始化用户配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            创建的配置对象
        """
        # 检查是否已存在配置
        existing = self.user_config_service.get_by_user_id(user_id)
        if existing:
            logger.info(f"用户 {user_id} 已有配置，跳过初始化")
            return existing
        
        # 获取系统默认配置
        default_config = self.system_config_service.get_default_user_config()
        
        # 创建用户配置
        config = self.user_config_service.create_config(user_id, default_config)
        
        return config
    
    def _copy_default_template(self, user_id: str) -> bool:
        """
        复制默认PPT模板到用户工作目录
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功复制
        """
        work_dir = self.storage_service.get_user_work_dir(user_id)
        target_file = work_dir / "ppt_data.json"
        
        # 如果目标已存在，不覆盖
        if target_file.exists():
            logger.info(f"用户 {user_id} 已有 ppt_data.json，跳过模板复制")
            return False
        
        # 检查模板文件是否存在
        if self.default_ppt_template.exists():
            shutil.copy(self.default_ppt_template, target_file)
            logger.info(f"从模板复制 ppt_data.json: {self.default_ppt_template}")
            return True
        
        # 如果没有模板文件，创建一个默认的空项目
        default_ppt_data = self._create_default_ppt_data()
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(default_ppt_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"创建默认空项目 ppt_data.json")
        return True
    
    def _create_default_ppt_data(self) -> Dict[str, Any]:
        """
        创建默认的PPT数据结构
        
        Returns:
            默认PPT数据
        """
        return {
            "project_name": "我的演示文稿",
            "slides": [
                {
                    "id": "default_slide_1",
                    "elements": [
                        {
                            "type": "text",
                            "id": "title_1",
                            "left": 100,
                            "top": 200,
                            "width": 800,
                            "height": 100,
                            "content": "<p style=\"text-align: center;\"><strong><span style=\"font-size: 48px;\">欢迎使用 PPT 转视频工具</span></strong></p>",
                            "rotate": 0,
                            "defaultFontName": "Microsoft YaHei",
                            "defaultColor": "#333333"
                        },
                        {
                            "type": "text",
                            "id": "subtitle_1",
                            "left": 150,
                            "top": 350,
                            "width": 700,
                            "height": 60,
                            "content": "<p style=\"text-align: center;\"><span style=\"font-size: 24px; color: #666666;\">请在 PPTist 编辑器中创建您的演示文稿</span></p>",
                            "rotate": 0,
                            "defaultFontName": "Microsoft YaHei",
                            "defaultColor": "#666666"
                        }
                    ],
                    "background": {
                        "type": "solid",
                        "color": "#ffffff"
                    },
                    "script": "欢迎使用 PPT 转视频工具。这是一个默认的演示文稿，您可以在 PPTist 编辑器中自由创建和编辑您的内容。",
                    "notes": "这是默认的首页幻灯片"
                }
            ],
            "theme": {
                "themeColor": "#5b9bd5",
                "fontColor": "#333333",
                "fontName": "Microsoft YaHei",
                "backgroundColor": "#ffffff"
            },
            "viewportSize": {
                "width": 1000,
                "height": 562.5
            },
            "viewportRatio": 0.5625,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def check_user_initialized(self, user_id: str) -> Dict[str, bool]:
        """
        检查用户是否已完成初始化
        
        Args:
            user_id: 用户ID
            
        Returns:
            初始化状态检查结果
        """
        work_dir = self.storage_service.output_dir / user_id
        
        return {
            "work_dir_exists": work_dir.exists(),
            "has_ppt_data": (work_dir / "ppt_data.json").exists() if work_dir.exists() else False,
            "has_config": self.user_config_service.get_by_user_id(user_id) is not None
        }
    
    def ensure_user_initialized(self, user_id: str, username: str = None) -> Dict[str, Any]:
        """
        确保用户已初始化（如果未初始化则执行初始化）
        
        Args:
            user_id: 用户ID
            username: 用户名
            
        Returns:
            初始化状态/结果
        """
        status = self.check_user_initialized(user_id)
        
        # 如果全部已初始化，返回状态
        if all(status.values()):
            return {
                "already_initialized": True,
                "status": status
            }
        
        # 执行初始化
        result = self.initialize_user(user_id, username)
        result["already_initialized"] = False
        
        return result


# 便捷函数
_user_init_service = None

def get_user_init_service() -> UserInitService:
    """获取用户初始化服务单例"""
    global _user_init_service
    if _user_init_service is None:
        _user_init_service = UserInitService()
    return _user_init_service
