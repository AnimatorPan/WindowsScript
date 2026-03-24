"""
标签管理模块
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .database import Database
from .models import Tag

logger = logging.getLogger(__name__)


class TagManager:
    """标签管理器"""
    
    def __init__(self, db: Database, library_id: int):
        """
        初始化标签管理器
        
        Args:
            db: 数据库连接
            library_id: 库 ID
        """
        self.db = db
        self.library_id = library_id
    
    def create(
        self, 
        name: str, 
        parent_id: Optional[int] = None, 
        color: Optional[str] = None,
        description: str = ""
    ) -> int:
        """
        创建标签
        
        Args:
            name: 标签名称
            parent_id: 父标签 ID
            color: 标签颜色（十六进制，如 #FF5733）
            description: 描述
            
        Returns:
            新标签 ID
        """
        sql = """
            INSERT INTO tags (library_id, name, parent_id, color, description)
            VALUES (?, ?, ?, ?, ?)
        """
        tag_id = self.db.insert(sql, (self.library_id, name, parent_id, color, description))
        
        logger.info(f"创建标签: {name} (ID: {tag_id})")
        return tag_id
    
    def get(self, tag_id: int) -> Optional[Dict]:
        """获取标签信息"""
        sql = "SELECT * FROM tags WHERE id = ? AND library_id = ?"
        return self.db.fetch_one(sql, (tag_id, self.library_id))
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取标签"""
        sql = "SELECT * FROM tags WHERE name = ? AND library_id = ?"
        return self.db.fetch_one(sql, (name, self.library_id))
    
    def list_all(self) -> List[Dict]:
        """获取所有标签"""
        sql = """
            SELECT * FROM tags 
            WHERE library_id = ? 
            ORDER BY name
        """
        return self.db.fetch_all(sql, (self.library_id,))
    
    def get_tree(self) -> List[Dict]:
        """
        获取标签树结构
        
        Returns:
            树形结构列表
        """
        all_tags = self.list_all()
        
        # 构建索引
        tag_dict = {tag['id']: {**tag, 'children': []} for tag in all_tags}
        
        # 构建树
        tree = []
        for tag in all_tags:
            if tag['parent_id'] is None:
                tree.append(tag_dict[tag['id']])
            else:
                parent = tag_dict.get(tag['parent_id'])
                if parent:
                    parent['children'].append(tag_dict[tag['id']])
        
        return tree
    
    def get_children(self, parent_id: Optional[int] = None) -> List[Dict]:
        """
        获取子标签
        
        Args:
            parent_id: 父标签 ID，None 表示获取根标签
            
        Returns:
            子标签列表
        """
        if parent_id is None:
            sql = """
                SELECT * FROM tags 
                WHERE library_id = ? AND parent_id IS NULL
                ORDER BY name
            """
            return self.db.fetch_all(sql, (self.library_id,))
        else:
            sql = """
                SELECT * FROM tags 
                WHERE library_id = ? AND parent_id = ?
                ORDER BY name
            """
            return self.db.fetch_all(sql, (self.library_id, parent_id))
    
    def update(self, tag_id: int, **kwargs):
        """
        更新标签
        
        Args:
            tag_id: 标签 ID
            **kwargs: 要更新的字段
        """
        allowed_fields = ['name', 'parent_id', 'color', 'description']
        update_fields = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return
        
        params.extend([self.library_id, tag_id])
        
        sql = f"""
            UPDATE tags SET {', '.join(update_fields)} 
            WHERE library_id = ? AND id = ?
        """
        self.db.update(sql, tuple(params))
        
        logger.info(f"更新标签: {tag_id}")
    
    def delete(self, tag_id: int, cascade: bool = False):
        """
        删除标签
        
        Args:
            tag_id: 标签 ID
            cascade: 是否级联删除子标签
        """
        if cascade:
            # 递归删除子标签
            children = self.get_children(tag_id)
            for child in children:
                self.delete(child['id'], cascade=True)
        else:
            # 将子标签的 parent_id 设为 NULL
            sql = "UPDATE tags SET parent_id = NULL WHERE parent_id = ?"
            self.db.update(sql, (tag_id,))
        
        # 删除标签
        sql = "DELETE FROM tags WHERE id = ? AND library_id = ?"
        self.db.delete(sql, (tag_id, self.library_id))
        
        logger.info(f"删除标签: {tag_id}")
    
    def add_to_document(self, tag_id: int, document_id: int):
        """
        给文档添加标签
        
        Args:
            tag_id: 标签 ID
            document_id: 文档 ID
        """
        sql = """
            INSERT OR IGNORE INTO document_tags (document_id, tag_id)
            VALUES (?, ?)
        """
        self.db.insert(sql, (document_id, tag_id))
        
        logger.info(f"添加标签到文档: 文档 {document_id} + 标签 {tag_id}")
    
    def remove_from_document(self, tag_id: int, document_id: int):
        """
        从文档移除标签
        
        Args:
            tag_id: 标签 ID
            document_id: 文档 ID
        """
        sql = "DELETE FROM document_tags WHERE document_id = ? AND tag_id = ?"
        self.db.delete(sql, (document_id, tag_id))
        
        logger.info(f"从文档移除标签: 文档 {document_id} - 标签 {tag_id}")
    
    def get_document_count(self, tag_id: int, include_children: bool = False) -> int:
        """
        获取标签关联的文档数量
        
        Args:
            tag_id: 标签 ID
            include_children: 是否包含子标签
            
        Returns:
            文档数量
        """
        if include_children:
            # 获取所有子标签 ID
            tag_ids = [tag_id]
            self._collect_child_ids(tag_id, tag_ids)
            
            placeholders = ','.join('?' * len(tag_ids))
            sql = f"""
                SELECT COUNT(DISTINCT document_id) as count
                FROM document_tags
                WHERE tag_id IN ({placeholders})
            """
            result = self.db.fetch_one(sql, tuple(tag_ids))
        else:
            sql = """
                SELECT COUNT(*) as count
                FROM document_tags
                WHERE tag_id = ?
            """
            result = self.db.fetch_one(sql, (tag_id,))
        
        return result['count'] if result else 0
    
    def get_popular_tags(self, limit: int = 10) -> List[Dict]:
        """
        获取热门标签（按使用频率排序）
        
        Args:
            limit: 返回数量
            
        Returns:
            标签列表（包含使用次数）
        """
        sql = """
            SELECT t.*, COUNT(dt.document_id) as usage_count
            FROM tags t
            LEFT JOIN document_tags dt ON t.id = dt.tag_id
            WHERE t.library_id = ?
            GROUP BY t.id
            ORDER BY usage_count DESC
            LIMIT ?
        """
        return self.db.fetch_all(sql, (self.library_id, limit))
    
    def get_unused_tags(self) -> List[Dict]:
        """
        获取未使用的标签
        
        Returns:
            标签列表
        """
        sql = """
            SELECT t.* FROM tags t
            WHERE t.library_id = ?
            AND NOT EXISTS (
                SELECT 1 FROM document_tags dt WHERE dt.tag_id = t.id
            )
            ORDER BY t.name
        """
        return self.db.fetch_all(sql, (self.library_id,))
    
    def merge_tags(self, source_tag_id: int, target_tag_id: int):
        """
        合并标签（将源标签的所有文档关联转移到目标标签）
        
        Args:
            source_tag_id: 源标签 ID
            target_tag_id: 目标标签 ID
        """
        # 获取源标签的所有文档
        sql = "SELECT document_id FROM document_tags WHERE tag_id = ?"
        docs = self.db.fetch_all(sql, (source_tag_id,))
        
        # 转移到目标标签
        for doc in docs:
            self.add_to_document(target_tag_id, doc['document_id'])
        
        # 删除源标签
        self.delete(source_tag_id)
        
        logger.info(f"合并标签: {source_tag_id} -> {target_tag_id}")
    
    def _collect_child_ids(self, parent_id: int, result: List[int]):
        """递归收集所有子标签 ID"""
        children = self.get_children(parent_id)
        for child in children:
            result.append(child['id'])
            self._collect_child_ids(child['id'], result)