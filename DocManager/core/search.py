"""
搜索引擎模块
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .database import Database

logger = logging.getLogger(__name__)


class SearchEngine:
    """搜索引擎"""
    
    def __init__(self, db: Database, library_id: int):
        """
        初始化搜索引擎
        
        Args:
            db: 数据库连接
            library_id: 库 ID
        """
        self.db = db
        self.library_id = library_id
    
    def search_by_filename(self, keyword: str, limit: int = 100) -> List[Dict]:
        """
        按文件名搜索
        
        Args:
            keyword: 关键词
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        sql = """
            SELECT * FROM documents 
            WHERE library_id = ? AND filename LIKE ?
            ORDER BY imported_at DESC
            LIMIT ?
        """
        return self.db.fetch_all(sql, (self.library_id, f"%{keyword}%", limit))
    
    def filter_by_type(self, file_types: List[str], limit: int = 100) -> List[Dict]:
        """
        按文件类型筛选
        
        Args:
            file_types: 文件类型列表（如 ['pdf', 'docx']）
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        if not file_types:
            return []
        
        placeholders = ','.join('?' * len(file_types))
        sql = f"""
            SELECT * FROM documents 
            WHERE library_id = ? AND file_type IN ({placeholders})
            ORDER BY filename
            LIMIT ?
        """
        params = [self.library_id] + file_types + [limit]
        return self.db.fetch_all(sql, tuple(params))
    
    def filter_by_tags(self, tag_ids: List[int], match_all: bool = False, limit: int = 100) -> List[Dict]:
        """
        按标签筛选
        
        Args:
            tag_ids: 标签 ID 列表
            match_all: True=匹配所有标签(AND)，False=匹配任一标签(OR)
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        if not tag_ids:
            return []
        
        if match_all:
            # 匹配所有标签
            placeholders = ' AND '.join([f"""
                EXISTS (
                    SELECT 1 FROM document_tags dt{i} 
                    WHERE dt{i}.document_id = d.id AND dt{i}.tag_id = ?
                )
            """ for i in range(len(tag_ids))])
            
            sql = f"""
                SELECT d.* FROM documents d
                WHERE d.library_id = ? AND {placeholders}
                ORDER BY d.filename
                LIMIT ?
            """
            params = [self.library_id] + tag_ids + [limit]
        else:
            # 匹配任一标签
            placeholders = ','.join('?' * len(tag_ids))
            sql = f"""
                SELECT DISTINCT d.* FROM documents d
                INNER JOIN document_tags dt ON d.id = dt.document_id
                WHERE d.library_id = ? AND dt.tag_id IN ({placeholders})
                ORDER BY d.filename
                LIMIT ?
            """
            params = [self.library_id] + tag_ids + [limit]
        
        return self.db.fetch_all(sql, tuple(params))
    
    def filter_by_category(self, category_id: int, include_subcategories: bool = False, limit: int = 100) -> List[Dict]:
        """
        按分类筛选
        
        Args:
            category_id: 分类 ID
            include_subcategories: 是否包含子分类
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        if include_subcategories:
            # 获取所有子分类 ID
            from .category import CategoryManager
            cat_manager = CategoryManager(self.db, self.library_id)
            category_ids = [category_id]
            cat_manager._collect_child_ids(category_id, category_ids)
            
            placeholders = ','.join('?' * len(category_ids))
            sql = f"""
                SELECT DISTINCT d.* FROM documents d
                INNER JOIN document_categories dc ON d.id = dc.document_id
                WHERE d.library_id = ? AND dc.category_id IN ({placeholders})
                ORDER BY d.filename
                LIMIT ?
            """
            params = [self.library_id] + category_ids + [limit]
        else:
            sql = """
                SELECT d.* FROM documents d
                INNER JOIN document_categories dc ON d.id = dc.document_id
                WHERE d.library_id = ? AND dc.category_id = ?
                ORDER BY d.filename
                LIMIT ?
            """
            params = (self.library_id, category_id, limit)
        
        return self.db.fetch_all(sql, params)
    
    def filter_by_date_range(
        self, 
        date_field: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        按日期范围筛选
        
        Args:
            date_field: 日期字段名（imported_at, created_at, modified_at）
            start_date: 开始日期（ISO格式）
            end_date: 结束日期（ISO格式）
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        allowed_fields = ['imported_at', 'created_at', 'modified_at']
        if date_field not in allowed_fields:
            logger.warning(f"无效的日期字段: {date_field}")
            return []
        
        conditions = ["library_id = ?"]
        params = [self.library_id]
        
        if start_date:
            conditions.append(f"{date_field} >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append(f"{date_field} <= ?")
            params.append(end_date)
        
        params.append(limit)
        
        sql = f"""
            SELECT * FROM documents 
            WHERE {' AND '.join(conditions)}
            ORDER BY {date_field} DESC
            LIMIT ?
        """
        return self.db.fetch_all(sql, tuple(params))
    
    def filter_by_size_range(
        self,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        按文件大小范围筛选
        
        Args:
            min_size: 最小大小（字节）
            max_size: 最大大小（字节）
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        conditions = ["library_id = ?"]
        params = [self.library_id]
        
        if min_size is not None:
            conditions.append("file_size >= ?")
            params.append(min_size)
        
        if max_size is not None:
            conditions.append("file_size <= ?")
            params.append(max_size)
        
        params.append(limit)
        
        sql = f"""
            SELECT * FROM documents 
            WHERE {' AND '.join(conditions)}
            ORDER BY file_size DESC
            LIMIT ?
        """
        return self.db.fetch_all(sql, tuple(params))
    
    def complex_search(self, filters: Dict, limit: int = 100) -> List[Dict]:
        """
        复杂组合搜索
        
        Args:
            filters: 筛选条件字典，支持以下键：
                - keyword: 文件名关键词
                - file_types: 文件类型列表
                - tag_ids: 标签 ID 列表
                - category_id: 分类 ID
                - date_field: 日期字段名
                - start_date: 开始日期
                - end_date: 结束日期
                - min_size: 最小文件大小
                - max_size: 最大文件大小
                - is_duplicate: 是否重复
                - is_uncategorized: 是否未分类
                - is_untagged: 是否未打标签
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        conditions = ["d.library_id = ?"]
        params = [self.library_id]
        joins = []
        
        # 文件名关键词
        if filters.get('keyword'):
            conditions.append("d.filename LIKE ?")
            params.append(f"%{filters['keyword']}%")
        
        # 文件类型
        if filters.get('file_types'):
            file_types = filters['file_types']
            placeholders = ','.join('?' * len(file_types))
            conditions.append(f"d.file_type IN ({placeholders})")
            params.extend(file_types)
        
        # 标签
        if filters.get('tag_ids'):
            tag_ids = filters['tag_ids']
            placeholders = ','.join('?' * len(tag_ids))
            joins.append("INNER JOIN document_tags dt ON d.id = dt.document_id")
            conditions.append(f"dt.tag_id IN ({placeholders})")
            params.extend(tag_ids)
        
        # 分类
        if filters.get('category_id'):
            joins.append("INNER JOIN document_categories dc ON d.id = dc.document_id")
            conditions.append("dc.category_id = ?")
            params.append(filters['category_id'])
        
        # 日期范围
        date_field = filters.get('date_field', 'imported_at')
        if filters.get('start_date'):
            conditions.append(f"d.{date_field} >= ?")
            params.append(filters['start_date'])
        if filters.get('end_date'):
            conditions.append(f"d.{date_field} <= ?")
            params.append(filters['end_date'])
        
        # 文件大小
        if filters.get('min_size') is not None:
            conditions.append("d.file_size >= ?")
            params.append(filters['min_size'])
        if filters.get('max_size') is not None:
            conditions.append("d.file_size <= ?")
            params.append(filters['max_size'])
        
        # 重复状态
        if filters.get('is_duplicate') is not None:
            conditions.append("d.is_duplicate = ?")
            params.append(1 if filters['is_duplicate'] else 0)
        
        # 未分类
        if filters.get('is_uncategorized'):
            conditions.append("""
                NOT EXISTS (
                    SELECT 1 FROM document_categories dc2 WHERE dc2.document_id = d.id
                )
            """)
        
        # 未打标签
        if filters.get('is_untagged'):
            conditions.append("""
                NOT EXISTS (
                    SELECT 1 FROM document_tags dt2 WHERE dt2.document_id = d.id
                )
            """)
        
        params.append(limit)
        
        join_clause = ' '.join(joins)
        where_clause = ' AND '.join(conditions)
        
        sql = f"""
            SELECT DISTINCT d.* FROM documents d
            {join_clause}
            WHERE {where_clause}
            ORDER BY d.imported_at DESC
            LIMIT ?
        """
        
        return self.db.fetch_all(sql, tuple(params))
    
    def get_recent_documents(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """
        获取最近导入的文档
        
        Args:
            days: 最近天数
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        from datetime import timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        sql = """
            SELECT * FROM documents 
            WHERE library_id = ? AND imported_at >= ?
            ORDER BY imported_at DESC
            LIMIT ?
        """
        return self.db.fetch_all(sql, (self.library_id, cutoff_date, limit))