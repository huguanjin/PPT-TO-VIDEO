"""
VideoLingo技术融合 - 配置持久化存储系统
提供配置文件的存储、检索、版本管理功能
"""

import os
import json
import sqlite3
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ConfigRecord:
    """配置记录数据类"""
    id: str
    name: str
    preset_key: str
    config_data: Dict[str, Any]
    description: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    version: str
    is_active: bool = True
    usage_count: int = 0
    last_used: Optional[datetime] = None


class ConfigStorageManager:
    """配置存储管理器"""
    
    def __init__(self, storage_path: str = "config_data/storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = self.storage_path / "videolingo_configs.db"
        
        # 配置文件目录
        self.configs_dir = self.storage_path / "configs"
        self.configs_dir.mkdir(exist_ok=True)
        
        # 备份目录
        self.backup_dir = self.storage_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化SQLite数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建配置表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config_records (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        preset_key TEXT NOT NULL,
                        description TEXT,
                        tags TEXT,  -- JSON array as string
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        version TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        usage_count INTEGER DEFAULT 0,
                        last_used TEXT,
                        config_hash TEXT,
                        file_path TEXT
                    )
                """)
                
                # 创建配置历史表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_id TEXT NOT NULL,
                        action TEXT NOT NULL,  -- create, update, delete, use
                        timestamp TEXT NOT NULL,
                        details TEXT,  -- JSON details
                        FOREIGN KEY (config_id) REFERENCES config_records (id)
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_preset_key ON config_records (preset_key)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON config_records (created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON config_records (is_active)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_count ON config_records (usage_count)")
                
                conn.commit()
                logger.info("配置数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def save_config(self, name: str, preset_key: str, config_data: Dict[str, Any], 
                   description: str = "", tags: List[str] = None) -> str:
        """保存配置"""
        try:
            config_id = str(uuid.uuid4())
            now = datetime.now()
            tags = tags or []
            
            # 计算配置哈希
            config_hash = self._calculate_config_hash(config_data)
            
            # 保存配置文件
            config_file_path = self.configs_dir / f"{config_id}.json"
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'id': config_id,
                    'name': name,
                    'preset_key': preset_key,
                    'config_data': config_data,
                    'description': description,
                    'tags': tags,
                    'created_at': now.isoformat(),
                    'version': '3.0.0'
                }, f, ensure_ascii=False, indent=2)
            
            # 保存到数据库
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO config_records 
                    (id, name, preset_key, description, tags, created_at, updated_at, 
                     version, config_hash, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    config_id, name, preset_key, description, json.dumps(tags),
                    now.isoformat(), now.isoformat(), '3.0.0', config_hash,
                    str(config_file_path.relative_to(self.storage_path))
                ))
                
                # 记录历史
                self._record_history(cursor, config_id, 'create', {
                    'name': name,
                    'preset_key': preset_key,
                    'description': description
                })
                
                conn.commit()
            
            logger.info(f"配置 {name} 已保存，ID: {config_id}")
            return config_id
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def load_config(self, config_id: str) -> Optional[ConfigRecord]:
        """加载配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM config_records WHERE id = ? AND is_active = 1
                """, (config_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # 从文件加载配置数据
                file_path = self.storage_path / row[12]  # file_path column
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    config_data = file_data['config_data']
                else:
                    logger.warning(f"配置文件不存在: {file_path}")
                    config_data = {}
                
                # 更新使用统计
                self._update_usage_stats(cursor, config_id)
                conn.commit()
                
                return ConfigRecord(
                    id=row[0],
                    name=row[1],
                    preset_key=row[2],
                    config_data=config_data,
                    description=row[3] or "",
                    tags=json.loads(row[4]) if row[4] else [],
                    created_at=datetime.fromisoformat(row[5]),
                    updated_at=datetime.fromisoformat(row[6]),
                    version=row[7],
                    is_active=bool(row[8]),
                    usage_count=row[9],
                    last_used=datetime.fromisoformat(row[10]) if row[10] else None
                )
                
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return None
    
    def list_configs(self, preset_key: Optional[str] = None, 
                    tags: Optional[List[str]] = None,
                    limit: int = 50, offset: int = 0) -> List[ConfigRecord]:
        """列出配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询
                query = "SELECT * FROM config_records WHERE is_active = 1"
                params = []
                
                if preset_key:
                    query += " AND preset_key = ?"
                    params.append(preset_key)
                
                if tags:
                    for tag in tags:
                        query += " AND tags LIKE ?"
                        params.append(f'%"{tag}"%')
                
                query += " ORDER BY usage_count DESC, updated_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                configs = []
                for row in rows:
                    # 简化加载，不包含完整配置数据
                    config = ConfigRecord(
                        id=row[0],
                        name=row[1],
                        preset_key=row[2],
                        config_data={},  # 列表时不加载完整数据
                        description=row[3] or "",
                        tags=json.loads(row[4]) if row[4] else [],
                        created_at=datetime.fromisoformat(row[5]),
                        updated_at=datetime.fromisoformat(row[6]),
                        version=row[7],
                        is_active=bool(row[8]),
                        usage_count=row[9],
                        last_used=datetime.fromisoformat(row[10]) if row[10] else None
                    )
                    configs.append(config)
                
                return configs
                
        except Exception as e:
            logger.error(f"列出配置失败: {e}")
            return []
    
    def update_config(self, config_id: str, **updates) -> bool:
        """更新配置"""
        try:
            # 先加载当前配置
            current_config = self.load_config(config_id)
            if not current_config:
                return False
            
            # 准备更新数据
            now = datetime.now()
            update_fields = []
            update_values = []
            
            # 可更新的字段
            updatable_fields = ['name', 'description', 'tags', 'config_data']
            
            for field, value in updates.items():
                if field in updatable_fields:
                    if field == 'tags':
                        update_fields.append('tags')
                        update_values.append(json.dumps(value))
                    elif field == 'config_data':
                        # 更新配置文件
                        config_file_path = self.configs_dir / f"{config_id}.json"
                        if config_file_path.exists():
                            with open(config_file_path, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                            file_data['config_data'] = value
                            file_data['updated_at'] = now.isoformat()
                            with open(config_file_path, 'w', encoding='utf-8') as f:
                                json.dump(file_data, f, ensure_ascii=False, indent=2)
                        
                        # 更新哈希
                        update_fields.append('config_hash')
                        update_values.append(self._calculate_config_hash(value))
                    else:
                        update_fields.append(field)
                        update_values.append(value)
            
            if not update_fields:
                return True  # 没有需要更新的字段
            
            # 更新数据库
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clause = ", ".join(f"{field} = ?" for field in update_fields)
                update_values.extend([now.isoformat(), config_id])
                
                cursor.execute(f"""
                    UPDATE config_records 
                    SET {set_clause}, updated_at = ?
                    WHERE id = ?
                """, update_values)
                
                # 记录历史
                self._record_history(cursor, config_id, 'update', updates)
                
                conn.commit()
            
            logger.info(f"配置 {config_id} 已更新")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def delete_config(self, config_id: str, soft_delete: bool = True) -> bool:
        """删除配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if soft_delete:
                    # 软删除
                    cursor.execute("""
                        UPDATE config_records SET is_active = 0, updated_at = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), config_id))
                    action = 'soft_delete'
                else:
                    # 硬删除
                    cursor.execute("DELETE FROM config_records WHERE id = ?", (config_id,))
                    
                    # 删除配置文件
                    config_file_path = self.configs_dir / f"{config_id}.json"
                    if config_file_path.exists():
                        config_file_path.unlink()
                    
                    action = 'hard_delete'
                
                # 记录历史
                self._record_history(cursor, config_id, action, {})
                
                conn.commit()
            
            logger.info(f"配置 {config_id} 已删除 ({'软删除' if soft_delete else '硬删除'})")
            return True
            
        except Exception as e:
            logger.error(f"删除配置失败: {e}")
            return False
    
    def search_configs(self, query: str, search_fields: List[str] = None) -> List[ConfigRecord]:
        """搜索配置"""
        search_fields = search_fields or ['name', 'description', 'tags']
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建搜索查询
                conditions = []
                params = []
                
                for field in search_fields:
                    conditions.append(f"{field} LIKE ?")
                    params.append(f"%{query}%")
                
                where_clause = " OR ".join(conditions)
                full_query = f"""
                    SELECT * FROM config_records 
                    WHERE is_active = 1 AND ({where_clause})
                    ORDER BY usage_count DESC, updated_at DESC
                """
                
                cursor.execute(full_query, params)
                rows = cursor.fetchall()
                
                configs = []
                for row in rows:
                    config = ConfigRecord(
                        id=row[0],
                        name=row[1],
                        preset_key=row[2],
                        config_data={},  # 搜索时不加载完整数据
                        description=row[3] or "",
                        tags=json.loads(row[4]) if row[4] else [],
                        created_at=datetime.fromisoformat(row[5]),
                        updated_at=datetime.fromisoformat(row[6]),
                        version=row[7],
                        is_active=bool(row[8]),
                        usage_count=row[9],
                        last_used=datetime.fromisoformat(row[10]) if row[10] else None
                    )
                    configs.append(config)
                
                return configs
                
        except Exception as e:
            logger.error(f"搜索配置失败: {e}")
            return []
    
    def create_backup(self) -> str:
        """创建配置备份"""
        try:
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"videolingo_config_backup_{backup_timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir()
            
            # 备份数据库
            import shutil
            shutil.copy2(self.db_path, backup_path / "videolingo_configs.db")
            
            # 备份配置文件
            configs_backup_dir = backup_path / "configs"
            shutil.copytree(self.configs_dir, configs_backup_dir)
            
            # 创建备份信息文件
            backup_info = {
                'created_at': datetime.now().isoformat(),
                'version': '3.0.0',
                'total_configs': len(list(self.configs_dir.glob("*.json"))),
                'backup_type': 'full'
            }
            
            with open(backup_path / "backup_info.json", 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置备份已创建: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 基础统计
                cursor.execute("SELECT COUNT(*) FROM config_records WHERE is_active = 1")
                total_configs = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT preset_key) FROM config_records WHERE is_active = 1")
                unique_presets = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(usage_count) FROM config_records WHERE is_active = 1")
                total_usage = cursor.fetchone()[0] or 0
                
                # 最受欢迎的预设
                cursor.execute("""
                    SELECT preset_key, COUNT(*) as count 
                    FROM config_records WHERE is_active = 1 
                    GROUP BY preset_key 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                popular_presets = [{'preset': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                # 最近活跃配置
                cursor.execute("""
                    SELECT name, preset_key, usage_count 
                    FROM config_records WHERE is_active = 1 
                    ORDER BY last_used DESC 
                    LIMIT 5
                """)
                recent_configs = [{'name': row[0], 'preset': row[1], 'usage': row[2]} for row in cursor.fetchall()]
                
                return {
                    'total_configs': total_configs,
                    'unique_presets': unique_presets,
                    'total_usage': total_usage,
                    'popular_presets': popular_presets,
                    'recent_configs': recent_configs,
                    'storage_path': str(self.storage_path),
                    'database_size': os.path.getsize(self.db_path),
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def _calculate_config_hash(self, config_data: Dict[str, Any]) -> str:
        """计算配置数据哈希"""
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _update_usage_stats(self, cursor, config_id: str):
        """更新使用统计"""
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE config_records 
            SET usage_count = usage_count + 1, last_used = ?
            WHERE id = ?
        """, (now, config_id))
    
    def _record_history(self, cursor, config_id: str, action: str, details: Dict[str, Any]):
        """记录历史操作"""
        cursor.execute("""
            INSERT INTO config_history (config_id, action, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (config_id, action, datetime.now().isoformat(), json.dumps(details)))


# 全局存储管理器实例
storage_manager = ConfigStorageManager()


if __name__ == "__main__":
    # 测试存储系统
    manager = ConfigStorageManager("test_storage")
    
    # 测试保存配置
    test_config = {
        'subtitle_algorithm': 'videolingo',
        'max_subtitle_length': 80,
        'enable_smart_splitting': True
    }
    
    config_id = manager.save_config(
        name="测试配置",
        preset_key="test",
        config_data=test_config,
        description="这是一个测试配置",
        tags=["test", "videolingo"]
    )
    
    print(f"保存配置，ID: {config_id}")
    
    # 测试加载配置
    loaded_config = manager.load_config(config_id)
    print(f"加载配置: {loaded_config.name}")
    
    # 测试统计信息
    stats = manager.get_statistics()
    print(f"统计信息: {stats}")
