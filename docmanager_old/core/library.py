"""
库管理模块 - 管理文档库的创建、打开、删除等操作
"""

import os
import shutil
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

from .database import Database


class LibraryInfo:
    """库信息数据类"""
    
    def __init__(self, id: int, name: str, path: str, description: str = '',
                 created_at: str = '', updated_at: str = ''):
        self.id = id
        self.name = name
        self.path = path
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at
    
    @property
    def db_path(self) -> str:
        """获取数据库文件路径"""
        return os.path.join(self.path, 'library.db')
    
    @property
    def files_path(self) -> str:
        """获取文档存储路径"""
        return os.path.join(self.path, 'files')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class LibraryManager:
    """库管理器"""
    
    # 配置文件名
    CONFIG_FILE = 'library_config.json'
    
    def __init__(self, app_data_dir: Optional[str] = None):
        """
        初始化库管理器
        
        Args:
            app_data_dir: 应用数据目录，默认为用户目录下的 .docmanager
        """
        if app_data_dir is None:
            app_data_dir = os.path.join(Path.home(), '.docmanager')
        
        self.app_data_dir = app_data_dir
        self._ensure_app_data_dir()
        
        # 全局数据库（存储所有库的列表）
        self.global_db_path = os.path.join(app_data_dir, 'libraries.db')
        self._init_global_db()
    
    def _ensure_app_data_dir(self):
        """确保应用数据目录存在"""
        os.makedirs(self.app_data_dir, exist_ok=True)
    
    def _init_global_db(self):
        """初始化全局数据库"""
        db = Database(self.global_db_path).connect()
        
        # 创建库列表表
        db.execute('''
            CREATE TABLE IF NOT EXISTS library_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                description TEXT,
                last_opened TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        db.close()
    
    def create_library(self, name: str, path: str, description: str = '') -> LibraryInfo:
        """
        创建新库
        
        Args:
            name: 库名称
            path: 库路径
            description: 库描述
            
        Returns:
            创建的库信息
            
        Raises:
            FileExistsError: 如果库路径已存在且不为空
            PermissionError: 如果没有权限创建目录
        """
        print(f"[DEBUG] 开始创建库: name={name}, path={path}")
        
        # 检查路径是否已存在且不为空
        if os.path.exists(path) and os.listdir(path):
            raise FileExistsError(f'路径已存在且不为空: {path}')
        
        # 创建库目录结构
        try:
            os.makedirs(path, exist_ok=True)
            files_dir = os.path.join(path, 'files')
            os.makedirs(files_dir, exist_ok=True)
            print(f"[DEBUG] 创建目录成功: {path}")
        except PermissionError:
            raise PermissionError(f'没有权限创建目录: {path}')
        
        # 创建库数据库
        db_path = os.path.join(path, 'library.db')
        print(f"[DEBUG] 数据库路径: {db_path}")
        db = Database(db_path).connect()
        db.init_schema()
        print(f"[DEBUG] 数据库初始化完成")
        
        # 插入库信息到库数据库
        library_data = {
            'name': name,
            'path': path,
            'description': description
        }
        print(f"[DEBUG] 插入库数据: {library_data}")
        library_id = db.insert('libraries', library_data)
        print(f"[DEBUG] 插入成功, library_id={library_id}")
        db.close()
        
        # 添加到全局库列表
        print(f"[DEBUG] 添加到全局库列表, 全局数据库: {self.global_db_path}")
        try:
            global_db = Database(self.global_db_path).connect()
            row_id = global_db.insert('library_list', {
                'name': name,
                'path': path,
                'description': description,
                'last_opened': datetime.now().isoformat()
            })
            print(f"[DEBUG] 全局库列表插入成功, row_id={row_id}")
            global_db.close()
        except Exception as e:
            print(f"[DEBUG] 添加到全局库列表失败: {e}")
            import traceback
            print(traceback.format_exc())
        print(f"[DEBUG] 库创建完成")
        
        return LibraryInfo(
            id=library_id,
            name=name,
            path=path,
            description=description
        )
    
    def open_library(self, path: str) -> Optional[LibraryInfo]:
        """
        打开已有库
        
        Args:
            path: 库路径
            
        Returns:
            库信息，如果库不存在或无效返回None
        """
        import traceback
        
        db_path = os.path.join(path, 'library.db')
        
        # 检查库是否存在
        if not os.path.exists(db_path):
            print(f"[DEBUG] 库数据库不存在: {db_path}")
            return None
        
        try:
            db = Database(db_path).connect()
            
            # 检查必要的表是否存在
            if not db.table_exists('libraries'):
                print(f"[DEBUG] libraries 表不存在")
                db.close()
                return None
            
            # 获取库信息
            row = db.fetchone('SELECT * FROM libraries LIMIT 1')
            db.close()
            
            if not row:
                print(f"[DEBUG] libraries 表为空")
                return None
            
            # 调试信息
            print(f"[DEBUG] 库数据: id={row['id']}, name={row['name']}, path={row['path']}")
            
            # 更新或添加库到全局列表
            global_db = Database(self.global_db_path).connect()
            
            # 检查库是否已在全局列表中
            existing = global_db.fetchone(
                'SELECT id FROM library_list WHERE path = ?',
                (path,)
            )
            
            if existing:
                # 更新最后打开时间
                global_db.update(
                    'library_list',
                    {'last_opened': datetime.now().isoformat()},
                    'path = ?',
                    (path,)
                )
                print(f"[DEBUG] 更新库的最后打开时间")
            else:
                # 插入新记录
                description = row['description'] if 'description' in row.keys() else ''
                global_db.insert('library_list', {
                    'name': row['name'],
                    'path': path,
                    'description': description,
                    'last_opened': datetime.now().isoformat()
                })
                print(f"[DEBUG] 添加库到全局列表")
            
            global_db.close()
            
            # sqlite3.Row 不支持 .get()，使用条件表达式
            description = row['description'] if 'description' in row.keys() else ''
            created_at = row['created_at'] if 'created_at' in row.keys() else ''
            updated_at = row['updated_at'] if 'updated_at' in row.keys() else ''
            
            return LibraryInfo(
                id=row['id'],
                name=row['name'],
                path=row['path'],
                description=description,
                created_at=created_at,
                updated_at=updated_at
            )
            
        except Exception as e:
            print(f"[DEBUG] 打开库时出错: {e}")
            print(traceback.format_exc())
            return None
    
    def get_recent_libraries(self, limit: int = 10) -> List[LibraryInfo]:
        """
        获取最近打开的库列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            库信息列表
        """
        print(f"[DEBUG] 获取最近使用的库，全局数据库路径: {self.global_db_path}")
        
        db = Database(self.global_db_path).connect()
        rows = db.fetchall(
            'SELECT * FROM library_list ORDER BY last_opened DESC LIMIT ?',
            (limit,)
        )
        db.close()
        
        print(f"[DEBUG] 从数据库获取到 {len(rows)} 条记录")
        
        libraries = []
        for row in rows:
            print(f"[DEBUG] 检查库: {row['name']}, 路径: {row['path']}, 存在: {os.path.exists(row['path'])}")
            # 检查库是否仍然存在
            if os.path.exists(row['path']):
                # sqlite3.Row 不支持 .get()，使用 dict.get 的方式
                description = row['description'] if 'description' in row.keys() else ''
                created_at = row['created_at'] if 'created_at' in row.keys() else ''
                libraries.append(LibraryInfo(
                    id=row['id'],
                    name=row['name'],
                    path=row['path'],
                    description=description,
                    created_at=created_at
                ))
        
        print(f"[DEBUG] 返回 {len(libraries)} 个有效库")
        return libraries
    
    def delete_library(self, path: str, remove_files: bool = False) -> bool:
        """
        删除库
        
        Args:
            path: 库路径
            remove_files: 是否同时删除文件
            
        Returns:
            是否成功删除
        """
        try:
            # 从全局列表中删除
            global_db = Database(self.global_db_path).connect()
            global_db.delete('library_list', 'path = ?', (path,))
            global_db.close()
            
            # 如果需要，删除文件
            if remove_files and os.path.exists(path):
                shutil.rmtree(path)
            
            return True
        except Exception:
            return False
    
    def is_valid_library(self, path: str) -> bool:
        """
        检查路径是否是有效的库
        
        Args:
            path: 要检查的路径
            
        Returns:
            是否是有效的库
        """
        db_path = os.path.join(path, 'library.db')
        
        if not os.path.exists(db_path):
            return False
        
        try:
            db = Database(db_path).connect()
            exists = db.table_exists('libraries')
            db.close()
            return exists
        except Exception:
            return False
    
    def get_library_stats(self, path: str) -> Dict[str, Any]:
        """
        获取库统计信息
        
        Args:
            path: 库路径
            
        Returns:
            统计信息字典
        """
        db_path = os.path.join(path, 'library.db')
        
        if not os.path.exists(db_path):
            return {}
        
        try:
            db = Database(db_path).connect()
            
            # 获取各种统计
            doc_count = db.get_row_count('documents')
            category_count = db.get_row_count('categories')
            tag_count = db.get_row_count('tags')
            
            # 获取总文件大小
            row = db.fetchone('SELECT SUM(size) FROM documents')
            total_size = row[0] if row and row[0] else 0
            
            db.close()
            
            return {
                'document_count': doc_count,
                'category_count': category_count,
                'tag_count': tag_count,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception:
            return {}
