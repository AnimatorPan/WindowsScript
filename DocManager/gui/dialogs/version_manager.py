"""
版本管理模块
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .database import Database

logger = logging.getLogger(__name__)


class VersionManager:
    """版本管理器"""
    
    def __init__(self, db: Database, library_id: int):
        """
        初始化版本管理器
        
        Args:
            db: 数据库连接
            library_id: 库 ID
        """
        self.db = db
        self.library_id = library_id
    
    def create_version(
        self,
        document_id: int,
        version_number: int = 1,
        is_current: bool = True,
        note: str = ""
    ) -> int:
        """
        创建版本记录
        
        Args:
            document_id: 文档 ID
            version_number: 版本号
            is_current: 是否为当前版本
            note: 版本说明
            
        Returns:
            版本 ID
        """
        # 如果设置为当前版本，将其他版本设为非当前
        if is_current:
            sql = """
                UPDATE document_versions 
                SET is_current = 0 
                WHERE document_id = ?
            """
            self.db.update(sql, (document_id,))
        
        # 创建新版本
        sql = """
            INSERT INTO document_versions 
            (document_id, version_number, is_current, version_note)
            VALUES (?, ?, ?, ?)
        """
        
        version_id = self.db.insert(
            sql,
            (document_id, version_number, 1 if is_current else 0, note)
        )
        
        logger.info(f"创建版本: 文档={document_id}, 版本={version_number}")
        
        return version_id
    
    def get_versions(self, document_id: int) -> List[Dict]:
        """
        获取文档的所有版本
        
        Args:
            document_id: 文档 ID
            
        Returns:
            版本列表
        """
        sql = """
            SELECT * FROM document_versions 
            WHERE document_id = ?
            ORDER BY version_number DESC
        """
        
        return self.db.fetch_all(sql, (document_id,))
    
    def get_current_version(self, document_id: int) -> Optional[Dict]:
        """
        获取当前版本
        
        Args:
            document_id: 文档 ID
            
        Returns:
            当前版本信息
        """
        sql = """
            SELECT * FROM document_versions 
            WHERE document_id = ? AND is_current = 1
            LIMIT 1
        """
        
        return self.db.fetch_one(sql, (document_id,))
    
    def set_current_version(self, version_id: int):
        """
        设置当前版本
        
        Args:
            version_id: 版本 ID
        """
        # 获取版本所属文档
        version = self.db.fetch_one(
            "SELECT document_id FROM document_versions WHERE id = ?",
            (version_id,)
        )
        
        if not version:
            return
        
        document_id = version['document_id']
        
        # 清除当前标记
        sql = """
            UPDATE document_versions 
            SET is_current = 0 
            WHERE document_id = ?
        """
        self.db.update(sql, (document_id,))
        
        # 设置新的当前版本
        sql = """
            UPDATE document_versions 
            SET is_current = 1 
            WHERE id = ?
        """
        self.db.update(sql, (version_id,))
        
        logger.info(f"设置当前版本: {version_id}")
    
    def delete_version(self, version_id: int):
        """
        删除版本
        
        Args:
            version_id: 版本 ID
        """
        # 检查是否为当前版本
        version = self.db.fetch_one(
            "SELECT * FROM document_versions WHERE id = ?",
            (version_id,)
        )
        
        if not version:
            return
        
        if version['is_current']:
            raise ValueError("不能删除当前版本")
        
        sql = "DELETE FROM document_versions WHERE id = ?"
        self.db.delete(sql, (version_id,))
        
        logger.info(f"删除版本: {version_id}")
    
    def link_documents(self, document_ids: List[int], base_doc_id: int = None):
        """
        将多个文档链接为版本链
        
        Args:
            document_ids: 文档 ID 列表（按版本顺序）
            base_doc_id: 基准文档 ID（如果为 None，使用第一个）
        """
        if not document_ids:
            return
        
        if base_doc_id is None:
            base_doc_id = document_ids[0]
        
        # 为每个文档创建版本记录
        for idx, doc_id in enumerate(document_ids):
            version_number = idx + 1
            is_current = (doc_id == document_ids[-1])  # 最后一个为当前版本
            
            self.create_version(
                doc_id,
                version_number,
                is_current,
                f"版本 {version_number}"
            )