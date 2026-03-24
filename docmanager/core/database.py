"""
数据库操作核心模块
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Database:
    """数据库操作封装类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """
        建立数据库连接
        
        Returns:
            数据库连接对象
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            # 使用 WAL 模式提高并发性能
            self.conn.execute("PRAGMA journal_mode=WAL")
            
            logger.info(f"数据库连接成功: {self.db_path}")
        
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")
    
    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        执行 SQL 语句
        
        Args:
            sql: SQL 语句
            params: 参数元组
            
        Returns:
            游标对象
        """
        try:
            conn = self.connect()
            cursor = conn.execute(sql, params)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"SQL 执行错误: {e}, SQL: {sql}")
            raise
    
    def fetch_one(self, sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        查询单条记录
        
        Args:
            sql: SQL 语句
            params: 参数元组
            
        Returns:
            字典形式的记录，不存在返回 None
        """
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetch_all(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        查询多条记录
        
        Args:
            sql: SQL 语句
            params: 参数元组
            
        Returns:
            字典列表
        """
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def insert(self, sql: str, params: Tuple = (), autocommit: bool = True) -> int:
        """
        插入记录
        
        Args:
            sql: SQL 语句
            params: 参数元组
            autocommit: 是否自动提交（事务中设为 False）
            
        Returns:
            新插入记录的 ID
        """
        cursor = self.execute(sql, params)
        if autocommit:
            self.commit()
        return cursor.lastrowid
    
    def update(self, sql: str, params: Tuple = (), autocommit: bool = True) -> int:
        """
        更新记录
        
        Args:
            sql: SQL 语句
            params: 参数元组
            autocommit: 是否自动提交（事务中设为 False）
            
        Returns:
            影响的行数
        """
        cursor = self.execute(sql, params)
        if autocommit:
            self.commit()
        return cursor.rowcount
    
    def delete(self, sql: str, params: Tuple = (), autocommit: bool = True) -> int:
        """
        删除记录
        
        Args:
            sql: SQL 语句
            params: 参数元组
            autocommit: 是否自动提交（事务中设为 False）
            
        Returns:
            影响的行数
        """
        cursor = self.execute(sql, params)
        if autocommit:
            self.commit()
        return cursor.rowcount
    
    def commit(self):
        """提交事务"""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """回滚事务"""
        if self.conn:
            self.conn.rollback()
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        使用方式:
            with db.transaction():
                db.execute(...)
                db.execute(...)
        """
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            logger.error(f"事务回滚: {e}")
            raise
    
    def init_database(self):
        """
        初始化数据库（创建所有表）
        """
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"数据库脚本文件不存在: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        try:
            conn = self.connect()
            conn.executescript(sql_script)
            self.commit()
            logger.info("数据库初始化成功")
            self._run_migrations()
        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _run_migrations(self):
        """运行数据库迁移"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # 检查 documents 表是否有 note 字段
            cursor.execute("PRAGMA table_info(documents)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'note' not in columns:
                cursor.execute("ALTER TABLE documents ADD COLUMN note TEXT")
                logger.info("迁移: 添加 note 字段到 documents 表")
            
            self.commit()
            logger.info("数据库迁移完成")
        except sqlite3.Error as e:
            logger.error(f"数据库迁移失败: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            是否存在
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.fetch_one(sql, (table_name,))
        return result is not None
    
    def get_table_count(self, table_name: str) -> int:
        """
        获取表记录数
        
        Args:
            table_name: 表名
            
        Returns:
            记录数
        """
        sql = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.fetch_one(sql)
        return result['count'] if result else 0


def create_database(db_path: str) -> Database:
    """
    创建并初始化数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        Database 对象
    """
    db = Database(db_path)
    db.connect()
    db.init_database()
    return db