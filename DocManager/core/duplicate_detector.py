"""
去重检测模块
"""
from typing import List, Dict, Optional, Tuple
import logging

from .database import Database

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """去重检测器"""
    
    def __init__(self, db: Database, library_id: int):
        """
        初始化去重检测器
        
        Args:
            db: 数据库连接
            library_id: 库 ID
        """
        self.db = db
        self.library_id = library_id
    
    def find_exact_duplicates(self) -> List[List[Dict]]:
        """
        查找完全重复的文档（基于文件哈希）
        
        Returns:
            重复组列表，每组包含多个重复文档
        """
        # 找出所有重复的哈希值
        sql = """
            SELECT file_hash, COUNT(*) as count 
            FROM documents 
            WHERE library_id = ? AND file_hash IS NOT NULL
            GROUP BY file_hash 
            HAVING count > 1
        """
        duplicate_hashes = self.db.fetch_all(sql, (self.library_id,))
        
        # 获取每个哈希对应的文档
        duplicate_groups = []
        for row in duplicate_hashes:
            file_hash = row['file_hash']
            sql = """
                SELECT * FROM documents 
                WHERE library_id = ? AND file_hash = ?
                ORDER BY imported_at
            """
            docs = self.db.fetch_all(sql, (self.library_id, file_hash))
            duplicate_groups.append(docs)
        
        logger.info(f"找到 {len(duplicate_groups)} 组完全重复的文档")
        return duplicate_groups
    
    def find_similar_by_name(self, similarity_threshold: float = 0.8) -> List[List[Dict]]:
        """
        查找文件名相似的文档
        
        Args:
            similarity_threshold: 相似度阈值（0-1）
            
        Returns:
            相似文档组列表
        """
        # 获取所有文档
        sql = "SELECT * FROM documents WHERE library_id = ? ORDER BY filename"
        all_docs = self.db.fetch_all(sql, (self.library_id,))
        
        # 简单的相似度检测（基于文件名）
        similar_groups = []
        processed = set()
        
        for i, doc1 in enumerate(all_docs):
            if doc1['id'] in processed:
                continue
            
            group = [doc1]
            processed.add(doc1['id'])
            
            for doc2 in all_docs[i+1:]:
                if doc2['id'] in processed:
                    continue
                
                similarity = self._calculate_name_similarity(doc1['filename'], doc2['filename'])
                if similarity >= similarity_threshold:
                    group.append(doc2)
                    processed.add(doc2['id'])
            
            if len(group) > 1:
                similar_groups.append(group)
        
        logger.info(f"找到 {len(similar_groups)} 组文件名相似的文档")
        return similar_groups
    
    def find_similar_by_size(self, size_tolerance: int = 1024) -> List[List[Dict]]:
        """
        查找大小相近的文档
        
        Args:
            size_tolerance: 大小容差（字节）
            
        Returns:
            相似文档组列表
        """
        sql = """
            SELECT * FROM documents 
            WHERE library_id = ? AND file_size IS NOT NULL
            ORDER BY file_size
        """
        all_docs = self.db.fetch_all(sql, (self.library_id,))
        
        similar_groups = []
        processed = set()
        
        for i, doc1 in enumerate(all_docs):
            if doc1['id'] in processed:
                continue
            
            group = [doc1]
            processed.add(doc1['id'])
            
            for doc2 in all_docs[i+1:]:
                if doc2['id'] in processed:
                    continue
                
                size_diff = abs(doc1['file_size'] - doc2['file_size'])
                if size_diff <= size_tolerance:
                    group.append(doc2)
                    processed.add(doc2['id'])
                else:
                    break  # 因为已排序，后续文档大小差异只会更大
            
            if len(group) > 1:
                similar_groups.append(group)
        
        logger.info(f"找到 {len(similar_groups)} 组大小相近的文档")
        return similar_groups
    
    def mark_as_duplicate(self, document_ids: List[int], keep_id: Optional[int] = None):
        """
        标记文档为重复
        
        Args:
            document_ids: 要标记的文档 ID 列表
            keep_id: 保留的文档 ID（不标记为重复）
        """
        ids_to_mark = [doc_id for doc_id in document_ids if doc_id != keep_id]
        
        if not ids_to_mark:
            return
        
        placeholders = ','.join('?' * len(ids_to_mark))
        sql = f"""
            UPDATE documents 
            SET is_duplicate = 1 
            WHERE library_id = ? AND id IN ({placeholders})
        """
        params = [self.library_id] + ids_to_mark
        self.db.update(sql, tuple(params))
        
        logger.info(f"标记 {len(ids_to_mark)} 个文档为重复")
    
    def unmark_duplicate(self, document_id: int):
        """
        取消重复标记
        
        Args:
            document_id: 文档 ID
        """
        sql = "UPDATE documents SET is_duplicate = 0 WHERE id = ? AND library_id = ?"
        self.db.update(sql, (document_id, self.library_id))
    
    def get_duplicate_statistics(self) -> Dict:
        """
        获取重复文档统计
        
        Returns:
            统计信息字典
        """
        stats = {}
        
        # 总文档数
        sql = "SELECT COUNT(*) as count FROM documents WHERE library_id = ?"
        result = self.db.fetch_one(sql, (self.library_id,))
        stats['total_documents'] = result['count'] if result else 0
        
        # 重复文档数
        sql = "SELECT COUNT(*) as count FROM documents WHERE library_id = ? AND is_duplicate = 1"
        result = self.db.fetch_one(sql, (self.library_id,))
        stats['duplicate_count'] = result['count'] if result else 0
        
        # 重复组数
        duplicate_groups = self.find_exact_duplicates()
        stats['duplicate_groups'] = len(duplicate_groups)
        
        # 可节省空间
        sql = """
            SELECT SUM(file_size) as total_size 
            FROM documents 
            WHERE library_id = ? AND is_duplicate = 1
        """
        result = self.db.fetch_one(sql, (self.library_id,))
        stats['wasted_space'] = result['total_size'] if result and result['total_size'] else 0
        
        return stats
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        计算文件名相似度
        
        Args:
            name1: 文件名1
            name2: 文件名2
            
        Returns:
            相似度（0-1）
        """
        from pathlib import Path
        from difflib import SequenceMatcher
        
        # 去除扩展名
        stem1 = Path(name1).stem.lower()
        stem2 = Path(name2).stem.lower()
        
        # 使用简单的字符串相似度
        if stem1 == stem2:
            return 1.0
        
        # 使用 SequenceMatcher 计算相似度
        similarity = SequenceMatcher(None, stem1, stem2).ratio()
        
        return similarity