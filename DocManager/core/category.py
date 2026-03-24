"""
分类管理模块
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .database import Database
from .models import Category

logger = logging.getLogger(__name__)


class CategoryManager:
    """分类管理器"""
    
    def __init__(self, db: Database, library_id: int):
        """
        初始化分类管理器
        
        Args:
            db: 数据库连接
            library_id: 库 ID
        """
        self.db = db
        self.library_id = library_id
    
    def create(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """
        创建分类
        
        Args:
            name: 分类名称
            parent_id: 父分类 ID
            description: 描述
            
        Returns:
            新分类 ID
        """
        sql = """
            INSERT INTO categories (library_id, name, parent_id, description)
            VALUES (?, ?, ?, ?)
        """
        category_id = self.db.insert(sql, (self.library_id, name, parent_id, description))
        
        logger.info(f"创建分类: {name} (ID: {category_id})")
        return category_id
    
    def get(self, category_id: int) -> Optional[Dict]:
        """获取分类信息"""
        sql = "SELECT * FROM categories WHERE id = ? AND library_id = ?"
        return self.db.fetch_one(sql, (category_id, self.library_id))
    
    def list_all(self) -> List[Dict]:
        """获取所有分类"""
        sql = """
            SELECT * FROM categories 
            WHERE library_id = ? 
            ORDER BY order_index, name
        """
        return self.db.fetch_all(sql, (self.library_id,))
    
    def get_tree(self) -> List[Dict]:
        """
        获取分类树结构
        
        Returns:
            树形结构列表
        """
        all_categories = self.list_all()
        
        # 构建索引
        cat_dict = {cat['id']: {**cat, 'children': []} for cat in all_categories}
        
        # 构建树
        tree = []
        for cat in all_categories:
            if cat['parent_id'] is None:
                tree.append(cat_dict[cat['id']])
            else:
                parent = cat_dict.get(cat['parent_id'])
                if parent:
                    parent['children'].append(cat_dict[cat['id']])
        
        return tree
    
    def get_children(self, parent_id: Optional[int] = None) -> List[Dict]:
        """
        获取子分类
        
        Args:
            parent_id: 父分类 ID，None 表示获取根分类
            
        Returns:
            子分类列表
        """
        if parent_id is None:
            sql = """
                SELECT * FROM categories 
                WHERE library_id = ? AND parent_id IS NULL
                ORDER BY order_index, name
            """
            return self.db.fetch_all(sql, (self.library_id,))
        else:
            sql = """
                SELECT * FROM categories 
                WHERE library_id = ? AND parent_id = ?
                ORDER BY order_index, name
            """
            return self.db.fetch_all(sql, (self.library_id, parent_id))
    
    def update(self, category_id: int, **kwargs):
        """
        更新分类
        
        Args:
            category_id: 分类 ID
            **kwargs: 要更新的字段
        """
        allowed_fields = ['name', 'parent_id', 'description', 'order_index', 'icon']
        update_fields = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return
        
        params.extend([self.library_id, category_id])
        
        sql = f"""
            UPDATE categories SET {', '.join(update_fields)} 
            WHERE library_id = ? AND id = ?
        """
        self.db.update(sql, tuple(params))
        
        logger.info(f"更新分类: {category_id}")
    
    def delete(self, category_id: int, cascade: bool = False):
        """
        删除分类
        
        Args:
            category_id: 分类 ID
            cascade: 是否级联删除子分类
        """
        if cascade:
            # 递归删除子分类
            children = self.get_children(category_id)
            for child in children:
                self.delete(child['id'], cascade=True)
        else:
            # 将子分类的 parent_id 设为 NULL
            sql = "UPDATE categories SET parent_id = NULL WHERE parent_id = ?"
            self.db.update(sql, (category_id,))
        
        # 删除分类
        sql = "DELETE FROM categories WHERE id = ? AND library_id = ?"
        self.db.delete(sql, (category_id, self.library_id))
        
        logger.info(f"删除分类: {category_id}")
    
    def add_document(self, category_id: int, document_id: int):
        """
        将文档添加到分类
        
        Args:
            category_id: 分类 ID
            document_id: 文档 ID
        """
        sql = """
            INSERT OR IGNORE INTO document_categories (document_id, category_id)
            VALUES (?, ?)
        """
        self.db.insert(sql, (document_id, category_id))
        
        logger.info(f"添加文档到分类: 文档 {document_id} -> 分类 {category_id}")
    
    def remove_document(self, category_id: int, document_id: int):
        """
        从分类中移除文档
        
        Args:
            category_id: 分类 ID
            document_id: 文档 ID
        """
        sql = "DELETE FROM document_categories WHERE document_id = ? AND category_id = ?"
        self.db.delete(sql, (document_id, category_id))
        
        logger.info(f"从分类移除文档: 文档 {document_id} <- 分类 {category_id}")
    
    def get_document_count(self, category_id: int, include_children: bool = False) -> int:
        """
        获取分类下的文档数量
        
        Args:
            category_id: 分类 ID
            include_children: 是否包含子分类
            
        Returns:
            文档数量
        """
        if include_children:
            # 获取所有子分类 ID
            category_ids = [category_id]
            self._collect_child_ids(category_id, category_ids)
            
            placeholders = ','.join('?' * len(category_ids))
            sql = f"""
                SELECT COUNT(DISTINCT document_id) as count
                FROM document_categories
                WHERE category_id IN ({placeholders})
            """
            result = self.db.fetch_one(sql, tuple(category_ids))
        else:
            sql = """
                SELECT COUNT(*) as count
                FROM document_categories
                WHERE category_id = ?
            """
            result = self.db.fetch_one(sql, (category_id,))
        
        return result['count'] if result else 0
    
    def _collect_child_ids(self, parent_id: int, result: List[int]):
        """递归收集所有子分类 ID"""
        children = self.get_children(parent_id)
        for child in children:
            result.append(child['id'])
            self._collect_child_ids(child['id'], result)