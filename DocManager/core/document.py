"""
文档管理模块
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .database import Database
from .models import Document

logger = logging.getLogger(__name__)


class DocumentManager:
    """文档管理器"""
    
    def __init__(self, db: Database, library_id: int):
        """
        初始化文档管理器
        
        Args:
            db: 数据库连接
            library_id: 库 ID
        """
        self.db = db
        self.library_id = library_id
    
    def get(self, document_id: int) -> Optional[Dict]:
        """
        获取文档信息
        
        Args:
            document_id: 文档 ID
            
        Returns:
            文档信息字典
        """
        sql = "SELECT * FROM documents WHERE id = ? AND library_id = ?"
        return self.db.fetch_one(sql, (document_id, self.library_id))
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        获取文档列表（分页）
        
        Args:
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            文档列表
        """
        sql = """
            SELECT * FROM documents 
            WHERE library_id = ? 
            ORDER BY imported_at DESC 
            LIMIT ? OFFSET ?
        """
        return self.db.fetch_all(sql, (self.library_id, limit, offset))
    
    def list_by_category(self, category_id: int) -> List[Dict]:
        """
        获取指定分类下的文档
        
        Args:
            category_id: 分类 ID
            
        Returns:
            文档列表
        """
        sql = """
            SELECT d.* FROM documents d
            INNER JOIN document_categories dc ON d.id = dc.document_id
            WHERE d.library_id = ? AND dc.category_id = ?
            ORDER BY d.filename
        """
        return self.db.fetch_all(sql, (self.library_id, category_id))
    
    def list_by_tag(self, tag_id: int) -> List[Dict]:
        """
        获取指定标签的文档
        
        Args:
            tag_id: 标签 ID
            
        Returns:
            文档列表
        """
        sql = """
            SELECT d.* FROM documents d
            INNER JOIN document_tags dt ON d.id = dt.document_id
            WHERE d.library_id = ? AND dt.tag_id = ?
            ORDER BY d.filename
        """
        return self.db.fetch_all(sql, (self.library_id, tag_id))
    
    def list_uncategorized(self) -> List[Dict]:
        """
        获取未分类文档
        
        Returns:
            文档列表
        """
        sql = """
            SELECT d.* FROM documents d
            WHERE d.library_id = ? 
            AND NOT EXISTS (
                SELECT 1 FROM document_categories dc WHERE dc.document_id = d.id
            )
            ORDER BY d.imported_at DESC
        """
        return self.db.fetch_all(sql, (self.library_id,))
    
    def list_untagged(self) -> List[Dict]:
        """
        获取未打标签文档
        
        Returns:
            文档列表
        """
        sql = """
            SELECT d.* FROM documents d
            WHERE d.library_id = ? 
            AND NOT EXISTS (
                SELECT 1 FROM document_tags dt WHERE dt.document_id = d.id
            )
            ORDER BY d.imported_at DESC
        """
        return self.db.fetch_all(sql, (self.library_id,))
    
    def list_duplicates(self) -> List[Dict]:
        """
        获取重复文档
        
        Returns:
            文档列表（按哈希分组）
        """
        sql = """
            SELECT * FROM documents
            WHERE library_id = ? AND file_hash IN (
                SELECT file_hash FROM documents
                WHERE library_id = ?
                GROUP BY file_hash
                HAVING COUNT(*) > 1
            )
            ORDER BY file_hash, imported_at
        """
        return self.db.fetch_all(sql, (self.library_id, self.library_id))
    
    def update(self, document_id: int, **kwargs):
        """
        更新文档信息
        
        Args:
            document_id: 文档 ID
            **kwargs: 要更新的字段
        """
        allowed_fields = ['filename', 'note', 'status']
        update_fields = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return
        
        params.extend([self.library_id, document_id])
        
        sql = f"""
            UPDATE documents SET {', '.join(update_fields)} 
            WHERE library_id = ? AND id = ?
        """
        self.db.update(sql, tuple(params))
        
        logger.info(f"更新文档信息: {document_id}")
    
    def delete(self, document_id: int):
        """
        删除文档
        
        Args:
            document_id: 文档 ID
        """
        sql = "DELETE FROM documents WHERE id = ? AND library_id = ?"
        self.db.delete(sql, (document_id, self.library_id))
        
        logger.info(f"删除文档: {document_id}")
    
    def mark_as_duplicate(self, document_id: int, is_duplicate: bool = True):
        """
        标记为重复
        
        Args:
            document_id: 文档 ID
            is_duplicate: 是否重复
        """
        sql = "UPDATE documents SET is_duplicate = ? WHERE id = ? AND library_id = ?"
        self.db.update(sql, (1 if is_duplicate else 0, document_id, self.library_id))
    
    def get_categories(self, document_id: int) -> List[Dict]:
        """
        获取文档所属分类
        
        Args:
            document_id: 文档 ID
            
        Returns:
            分类列表
        """
        sql = """
            SELECT c.* FROM categories c
            INNER JOIN document_categories dc ON c.id = dc.category_id
            WHERE dc.document_id = ?
        """
        return self.db.fetch_all(sql, (document_id,))
    
    def get_tags(self, document_id: int) -> List[Dict]:
        """
        获取文档标签
        
        Args:
            document_id: 文档 ID
            
        Returns:
            标签列表
        """
        sql = """
            SELECT t.* FROM tags t
            INNER JOIN document_tags dt ON t.id = dt.tag_id
            WHERE dt.document_id = ?
        """
        return self.db.fetch_all(sql, (document_id,))
    
    def count_total(self) -> int:
        """获取文档总数"""
        sql = "SELECT COUNT(*) as count FROM documents WHERE library_id = ?"
        result = self.db.fetch_one(sql, (self.library_id,))
        return result['count'] if result else 0
    
    def count_by_type(self) -> Dict[str, int]:
        """按类型统计文档数量"""
        sql = """
            SELECT file_type, COUNT(*) as count 
            FROM documents 
            WHERE library_id = ? 
            GROUP BY file_type
        """
        results = self.db.fetch_all(sql, (self.library_id,))
        return {r['file_type'] or 'unknown': r['count'] for r in results}