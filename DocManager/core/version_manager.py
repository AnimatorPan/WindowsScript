"""
版本管理模块
"""
from typing import List, Dict, Optional
import logging

from .database import Database

logger = logging.getLogger(__name__)


class VersionManager:
    """版本管理器"""

    def __init__(self, db: Database, library_id: int):
        self.db = db
        self.library_id = library_id

    def create_version(self, document_id: int, version_number: int = 1,
                       is_current: bool = True, note: str = "") -> int:
        if is_current:
            self.db.update(
                "UPDATE document_versions SET is_current=0 WHERE document_id=?",
                (document_id,))

        sql = """
            INSERT INTO document_versions
            (document_id, version_number, is_current, version_note)
            VALUES (?, ?, ?, ?)
        """
        return self.db.insert(
            sql, (document_id, version_number, 1 if is_current else 0, note))

    def get_versions(self, document_id: int) -> List[Dict]:
        sql = """
            SELECT * FROM document_versions
            WHERE document_id=? ORDER BY version_number DESC
        """
        return self.db.fetch_all(sql, (document_id,))

    def get_current_version(self, document_id: int) -> Optional[Dict]:
        sql = """
            SELECT * FROM document_versions
            WHERE document_id=? AND is_current=1 LIMIT 1
        """
        return self.db.fetch_one(sql, (document_id,))

    def set_current_version(self, version_id: int):
        version = self.db.fetch_one(
            "SELECT document_id FROM document_versions WHERE id=?",
            (version_id,))
        if not version:
            return
        self.db.update(
            "UPDATE document_versions SET is_current=0 WHERE document_id=?",
            (version['document_id'],))
        self.db.update(
            "UPDATE document_versions SET is_current=1 WHERE id=?",
            (version_id,))

    def delete_version(self, version_id: int):
        version = self.db.fetch_one(
            "SELECT * FROM document_versions WHERE id=?", (version_id,))
        if not version:
            return
        if version['is_current']:
            raise ValueError("不能删除当前版本")
        self.db.delete("DELETE FROM document_versions WHERE id=?", (version_id,))