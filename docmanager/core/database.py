"""
数据库模块 - 管理SQLite数据库连接和操作
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> 'Database':
        """建立数据库连接"""
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        # 启用外键支持
        self._connection.execute("PRAGMA foreign_keys = ON")
        return self
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def init_schema(self):
        """初始化数据库表结构"""
        cursor = self._connection.cursor()
        
        # 库信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS libraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 文档表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                file_type TEXT,
                created_at TIMESTAMP,
                modified_at TIMESTAMP,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                library_id INTEGER NOT NULL,
                FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE
            )
        ''')
        
        # 分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                library_id INTEGER NOT NULL,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE,
                FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE
            )
        ''')
        
        # 文档-分类关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_categories (
                document_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                PRIMARY KEY (document_id, category_id),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        ''')
        
        # 标签表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                color TEXT DEFAULT '#1890ff',
                library_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES tags(id) ON DELETE CASCADE,
                FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE
            )
        ''')
        
        # 文档-标签关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_tags (
                document_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (document_id, tag_id),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')
        
        # 智能文件夹表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rules_json TEXT NOT NULL,
                library_id INTEGER NOT NULL,
                is_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE
            )
        ''')
        
        # 监控文件夹表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watched_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                library_id INTEGER NOT NULL,
                auto_import BOOLEAN DEFAULT 1,
                include_subfolders BOOLEAN DEFAULT 1,
                file_patterns TEXT DEFAULT '*.*',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_library ON documents(library_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(file_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_filename ON documents(filename)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_library ON categories(library_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_parent ON tags(parent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_library ON tags(library_id)')
        
        self._connection.commit()
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        try:
            yield self._connection
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
    
    def execute(self, sql: str, parameters: Tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句"""
        return self._connection.execute(sql, parameters)
    
    def executemany(self, sql: str, parameters: List[Tuple]) -> sqlite3.Cursor:
        """批量执行SQL语句"""
        return self._connection.executemany(sql, parameters)
    
    def fetchone(self, sql: str, parameters: Tuple = ()) -> Optional[sqlite3.Row]:
        """查询单条记录"""
        cursor = self._connection.execute(sql, parameters)
        return cursor.fetchone()
    
    def fetchall(self, sql: str, parameters: Tuple = ()) -> List[sqlite3.Row]:
        """查询多条记录"""
        cursor = self._connection.execute(sql, parameters)
        return cursor.fetchall()
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入数据
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            插入行的ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        cursor = self._connection.execute(sql, tuple(data.values()))
        return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, 
               where_params: Tuple = ()) -> int:
        """
        更新数据
        
        Args:
            table: 表名
            data: 要更新的数据
            where: WHERE条件
            where_params: WHERE参数
            
        Returns:
            受影响的行数
        """
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        sql = f'UPDATE {table} SET {set_clause} WHERE {where}'
        
        params = tuple(data.values()) + where_params
        cursor = self._connection.execute(sql, params)
        return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: Tuple = ()) -> int:
        """
        删除数据
        
        Args:
            table: 表名
            where: WHERE条件
            where_params: WHERE参数
            
        Returns:
            受影响的行数
        """
        sql = f'DELETE FROM {table} WHERE {where}'
        cursor = self._connection.execute(sql, where_params)
        return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.fetchone(sql, (table_name,))
        return result is not None
    
    def get_row_count(self, table: str, where: str = '1=1', 
                      where_params: Tuple = ()) -> int:
        """获取表行数"""
        sql = f'SELECT COUNT(*) FROM {table} WHERE {where}'
        result = self.fetchone(sql, where_params)
        return result[0] if result else 0
