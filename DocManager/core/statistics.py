"""
统计数据模块
"""
from typing import Dict, List
from datetime import datetime, timedelta
import logging

from .database import Database

logger = logging.getLogger(__name__)


class StatisticsManager:
    """统计管理器"""

    def __init__(self, db: Database, library_id: int):
        self.db = db
        self.library_id = library_id

    def get_overview(self) -> Dict:
        stats = {}

        def count(sql, params=()):
            r = self.db.fetch_one(sql, params)
            return r['count'] if r else 0

        stats['total_documents'] = count(
            "SELECT COUNT(*) as count FROM documents WHERE library_id=?",
            (self.library_id,))

        r = self.db.fetch_one(
            "SELECT SUM(file_size) as s FROM documents WHERE library_id=?",
            (self.library_id,))
        stats['total_size'] = r['s'] if r and r['s'] else 0

        stats['total_categories'] = count(
            "SELECT COUNT(*) as count FROM categories WHERE library_id=?",
            (self.library_id,))

        stats['total_tags'] = count(
            "SELECT COUNT(*) as count FROM tags WHERE library_id=?",
            (self.library_id,))

        stats['uncategorized'] = count("""
            SELECT COUNT(*) as count FROM documents d
            WHERE d.library_id=?
            AND NOT EXISTS(
                SELECT 1 FROM document_categories dc WHERE dc.document_id=d.id)
        """, (self.library_id,))

        stats['duplicates'] = count(
            "SELECT COUNT(*) as count FROM documents WHERE library_id=? AND is_duplicate=1",
            (self.library_id,))

        return stats

    def get_type_distribution(self) -> List[Dict]:
        sql = """
            SELECT file_type, COUNT(*) as count, SUM(file_size) as total_size
            FROM documents WHERE library_id=?
            GROUP BY file_type ORDER BY count DESC
        """
        results = self.db.fetch_all(sql, (self.library_id,))
        return [{'type': r['file_type'] or 'unknown',
                 'count': r['count'],
                 'size': r['total_size'] or 0} for r in results]

    def get_import_trend(self, days: int = 30) -> List[Dict]:
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        sql = """
            SELECT DATE(imported_at) as date, COUNT(*) as count
            FROM documents WHERE library_id=? AND imported_at>=?
            GROUP BY DATE(imported_at) ORDER BY date
        """
        results = self.db.fetch_all(sql, (self.library_id, start))
        return [{'date': r['date'], 'count': r['count']} for r in results]

    def get_category_stats(self) -> List[Dict]:
        sql = """
            SELECT c.name, COUNT(dc.document_id) as count
            FROM categories c
            LEFT JOIN document_categories dc ON c.id=dc.category_id
            WHERE c.library_id=?
            GROUP BY c.id, c.name ORDER BY count DESC
        """
        results = self.db.fetch_all(sql, (self.library_id,))
        return [{'name': r['name'], 'count': r['count']} for r in results]

    def get_tag_stats(self, limit: int = 20) -> List[Dict]:
        sql = """
            SELECT t.name, t.color, COUNT(dt.document_id) as count
            FROM tags t
            LEFT JOIN document_tags dt ON t.id=dt.tag_id
            WHERE t.library_id=?
            GROUP BY t.id, t.name, t.color
            ORDER BY count DESC LIMIT ?
        """
        results = self.db.fetch_all(sql, (self.library_id, limit))
        return [{'name': r['name'], 'color': r['color'],
                 'count': r['count']} for r in results]

    def get_size_distribution(self) -> Dict:
        small = 1024 * 1024
        large = 10 * 1024 * 1024
        sql = """
            SELECT
                CASE
                    WHEN file_size < ? THEN 'small'
                    WHEN file_size < ? THEN 'medium'
                    ELSE 'large'
                END as size_category,
                COUNT(*) as count
            FROM documents WHERE library_id=?
            GROUP BY size_category
        """
        results = self.db.fetch_all(sql, (small, large, self.library_id))
        dist = {'small': 0, 'medium': 0, 'large': 0}
        for r in results:
            dist[r['size_category']] = r['count']
        return dist