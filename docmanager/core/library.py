"""
库管理模块（修复版）
"""
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging

from .database import Database
from .models import Library

logger = logging.getLogger(__name__)


class LibraryManager:
    """库管理器"""
    
    def __init__(self, db: Database):
        """
        初始化库管理器
        
        Args:
            db: 数据库连接对象
        """
        self.db = db
    
    def create(self, name: str, storage_path: str, description: str = "") -> int:
        """
        创建新库
        
        Args:
            name: 库名称
            storage_path: 文档存储路径
            description: 库描述
            
        Returns:
            新创建的库 ID
        """
        # 确保存储路径存在
        storage_path = Path(storage_path).absolute()
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # 数据库文件路径（修复：确保数据库目录存在）
        db_path = storage_path / f"{name}.db"
        
        # 确保数据库所在目录存在
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        sql = """
            INSERT INTO libraries (name, storage_path, db_path, description)
            VALUES (?, ?, ?, ?)
        """
        
        library_id = self.db.insert(sql, (name, str(storage_path), str(db_path), description))
        
        logger.info(f"创建库成功: {name} (ID: {library_id})")
        return library_id
    
    def get(self, library_id: int) -> Optional[Dict]:
        """
        获取库信息
        
        Args:
            library_id: 库 ID
            
        Returns:
            库信息字典
        """
        sql = "SELECT * FROM libraries WHERE id = ?"
        return self.db.fetch_one(sql, (library_id,))
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """
        根据名称获取库
        
        Args:
            name: 库名称
            
        Returns:
            库信息字典
        """
        sql = "SELECT * FROM libraries WHERE name = ?"
        return self.db.fetch_one(sql, (name,))
    
    def list_all(self) -> List[Dict]:
        """
        获取所有库列表
        
        Returns:
            库列表
        """
        sql = "SELECT * FROM libraries ORDER BY updated_at DESC"
        return self.db.fetch_all(sql)
    
    def update(self, library_id: int, **kwargs):
        """
        更新库信息
        
        Args:
            library_id: 库 ID
            **kwargs: 要更新的字段
        """
        allowed_fields = ['name', 'description', 'status']
        update_fields = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return
        
        # 更新时间
        update_fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        params.append(library_id)
        
        sql = f"UPDATE libraries SET {', '.join(update_fields)} WHERE id = ?"
        self.db.update(sql, tuple(params))
        
        logger.info(f"更新库信息: {library_id}")
    
    def delete(self, library_id: int):
        """
        删除库（注意：会级联删除所有关联数据）
        
        Args:
            library_id: 库 ID
        """
        sql = "DELETE FROM libraries WHERE id = ?"
        self.db.delete(sql, (library_id,))
        
        logger.warning(f"删除库: {library_id}")
    
    def get_statistics(self, library_id: int) -> Dict:
        """
        获取库统计信息
        
        Args:
            library_id: 库 ID
            
        Returns:
            统计信息字典
        """
        stats = {}
        
        # 文档总数
        sql = "SELECT COUNT(*) as count FROM documents WHERE library_id = ?"
        result = self.db.fetch_one(sql, (library_id,))
        stats['total_documents'] = result['count'] if result else 0
        
        # 总大小
        sql = "SELECT SUM(file_size) as total_size FROM documents WHERE library_id = ?"
        result = self.db.fetch_one(sql, (library_id,))
        stats['total_size'] = result['total_size'] if result and result['total_size'] else 0
        
        # 分类数
        sql = "SELECT COUNT(*) as count FROM categories WHERE library_id = ?"
        result = self.db.fetch_one(sql, (library_id,))
        stats['total_categories'] = result['count'] if result else 0
        
        # 标签数
        sql = "SELECT COUNT(*) as count FROM tags WHERE library_id = ?"
        result = self.db.fetch_one(sql, (library_id,))
        stats['total_tags'] = result['count'] if result else 0
        
        # 未分类文档数
        sql = """
            SELECT COUNT(*) as count FROM documents d
            WHERE d.library_id = ? 
            AND NOT EXISTS (
                SELECT 1 FROM document_categories dc WHERE dc.document_id = d.id
            )
        """
        result = self.db.fetch_one(sql, (library_id,))
        stats['uncategorized_documents'] = result['count'] if result else 0
        
        # 重复文档数
        sql = "SELECT COUNT(*) as count FROM documents WHERE library_id = ? AND is_duplicate = 1"
        result = self.db.fetch_one(sql, (library_id,))
        stats['duplicate_documents'] = result['count'] if result else 0
        
        return stats