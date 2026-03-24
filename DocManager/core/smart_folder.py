"""
智能文件夹模块
"""
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from .database import Database
from .models import SmartFolder

logger = logging.getLogger(__name__)


class SmartFolderManager:
    """智能文件夹管理器"""
    
    def __init__(self, db: Database, library_id: int):
        """
        初始化智能文件夹管理器
        
        Args:
            db: 数据库连接
            library_id: 库 ID
        """
        self.db = db
        self.library_id = library_id
    
    def create(self, name: str, rules: Dict, is_enabled: bool = True) -> int:
        """
        创建智能文件夹
        
        Args:
            name: 文件夹名称
            rules: 规则字典
            is_enabled: 是否启用
            
        Returns:
            新智能文件夹 ID
        """
        rules_json = json.dumps(rules, ensure_ascii=False)
        
        sql = """
            INSERT INTO smart_folders (library_id, name, rules_json, is_enabled)
            VALUES (?, ?, ?, ?)
        """
        folder_id = self.db.insert(sql, (self.library_id, name, rules_json, 1 if is_enabled else 0))
        
        logger.info(f"创建智能文件夹: {name} (ID: {folder_id})")
        return folder_id
    
    def get(self, folder_id: int) -> Optional[Dict]:
        """获取智能文件夹"""
        sql = "SELECT * FROM smart_folders WHERE id = ? AND library_id = ?"
        folder = self.db.fetch_one(sql, (folder_id, self.library_id))
        
        if folder:
            folder['rules'] = json.loads(folder['rules_json'])
        
        return folder
    
    def list_all(self, enabled_only: bool = False) -> List[Dict]:
        """
        获取所有智能文件夹
        
        Args:
            enabled_only: 是否仅返回启用的
            
        Returns:
            智能文件夹列表
        """
        if enabled_only:
            sql = """
                SELECT * FROM smart_folders 
                WHERE library_id = ? AND is_enabled = 1
                ORDER BY order_index, name
            """
        else:
            sql = """
                SELECT * FROM smart_folders 
                WHERE library_id = ?
                ORDER BY order_index, name
            """
        
        folders = self.db.fetch_all(sql, (self.library_id,))
        
        # 解析 rules_json
        for folder in folders:
            folder['rules'] = json.loads(folder['rules_json'])
        
        return folders
    
    def update(self, folder_id: int, **kwargs):
        """
        更新智能文件夹
        
        Args:
            folder_id: 文件夹 ID
            **kwargs: 要更新的字段
        """
        allowed_fields = ['name', 'is_enabled', 'order_index']
        update_fields = []
        params = []
        
        for field, value in kwargs.items():
            if field == 'rules':
                update_fields.append("rules_json = ?")
                params.append(json.dumps(value, ensure_ascii=False))
            elif field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return
        
        # 更新时间
        update_fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        params.extend([self.library_id, folder_id])
        
        sql = f"""
            UPDATE smart_folders SET {', '.join(update_fields)} 
            WHERE library_id = ? AND id = ?
        """
        self.db.update(sql, tuple(params))
        
        logger.info(f"更新智能文件夹: {folder_id}")
    
    def delete(self, folder_id: int):
        """删除智能文件夹"""
        sql = "DELETE FROM smart_folders WHERE id = ? AND library_id = ?"
        self.db.delete(sql, (folder_id, self.library_id))
        
        logger.info(f"删除智能文件夹: {folder_id}")
    
    def get_matched_documents(self, folder_id: int, limit: int = 1000) -> List[Dict]:
        """
        获取匹配规则的文档
        
        Args:
            folder_id: 智能文件夹 ID
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        folder = self.get(folder_id)
        if not folder or not folder['is_enabled']:
            return []
        
        rules = folder['rules']
        sql, params = self._build_query_from_rules(rules, limit)
        
        return self.db.fetch_all(sql, params)
    
    def count_matches(self, folder_id: int) -> int:
        """
        统计匹配的文档数量
        
        Args:
            folder_id: 智能文件夹 ID
            
        Returns:
            文档数量
        """
        folder = self.get(folder_id)
        if not folder:
            return 0
        
        rules = folder['rules']
        sql, params = self._build_query_from_rules(rules, count_only=True)
        
        result = self.db.fetch_one(sql, params)
        return result['count'] if result else 0
    
    def _build_query_from_rules(self, rules: Dict, limit: int = 1000, count_only: bool = False) -> tuple:
        """
        从规则构建 SQL 查询
        
        Args:
            rules: 规则字典
            limit: 返回数量限制
            count_only: 是否仅统计数量
            
        Returns:
            (SQL语句, 参数元组)
        """
        operator = rules.get('operator', 'AND')
        conditions_list = rules.get('conditions', [])
        
        conditions = []
        params = [self.library_id]
        joins = []
        
        for condition in conditions_list:
            cond_type = condition.get('type')
            cond_operator = condition.get('operator')
            cond_value = condition.get('value')
            
            if cond_type == 'file_type':
                if cond_operator == 'in' and isinstance(cond_value, list):
                    placeholders = ','.join('?' * len(cond_value))
                    conditions.append(f"d.file_type IN ({placeholders})")
                    params.extend(cond_value)
                elif cond_operator == 'equals':
                    conditions.append("d.file_type = ?")
                    params.append(cond_value)
            
            elif cond_type == 'filename':
                if cond_operator == 'contains':
                    conditions.append("d.filename LIKE ?")
                    params.append(f"%{cond_value}%")
                elif cond_operator == 'starts_with':
                    conditions.append("d.filename LIKE ?")
                    params.append(f"{cond_value}%")
                elif cond_operator == 'ends_with':
                    conditions.append("d.filename LIKE ?")
                    params.append(f"%{cond_value}")
            
            elif cond_type == 'tag':
                if isinstance(cond_value, list) and cond_value:
                    placeholders = ','.join('?' * len(cond_value))
                    if 'document_tags' not in ' '.join(joins):
                        joins.append("INNER JOIN document_tags dt ON d.id = dt.document_id")
                    conditions.append(f"dt.tag_id IN ({placeholders})")
                    params.extend(cond_value)
            
            elif cond_type == 'category':
                if isinstance(cond_value, list) and cond_value:
                    placeholders = ','.join('?' * len(cond_value))
                    if 'document_categories' not in ' '.join(joins):
                        joins.append("INNER JOIN document_categories dc ON d.id = dc.document_id")
                    conditions.append(f"dc.category_id IN ({placeholders})")
                    params.extend(cond_value)
            
            elif cond_type == 'file_size':
                if cond_operator == 'greater_than':
                    conditions.append("d.file_size > ?")
                    params.append(cond_value)
                elif cond_operator == 'less_than':
                    conditions.append("d.file_size < ?")
                    params.append(cond_value)
                elif cond_operator == 'between' and isinstance(cond_value, list) and len(cond_value) == 2:
                    conditions.append("d.file_size BETWEEN ? AND ?")
                    params.extend(cond_value)
            
            elif cond_type in ['created_date', 'modified_date', 'imported_date']:
                date_field_map = {
                    'created_date': 'created_at',
                    'modified_date': 'modified_at',
                    'imported_date': 'imported_at'
                }
                date_field = date_field_map[cond_type]
                
                if cond_operator == 'within_days':
                    cutoff = (datetime.now() - timedelta(days=cond_value)).isoformat()
                    conditions.append(f"d.{date_field} >= ?")
                    params.append(cutoff)
                elif cond_operator == 'after':
                    conditions.append(f"d.{date_field} >= ?")
                    params.append(cond_value)
                elif cond_operator == 'before':
                    conditions.append(f"d.{date_field} <= ?")
                    params.append(cond_value)
            
            elif cond_type == 'is_uncategorized':
                if cond_value:
                    conditions.append("""
                        NOT EXISTS (
                            SELECT 1 FROM document_categories dc2 WHERE dc2.document_id = d.id
                        )
                    """)
            
            elif cond_type == 'is_untagged':
                if cond_value:
                    conditions.append("""
                        NOT EXISTS (
                            SELECT 1 FROM document_tags dt2 WHERE dt2.document_id = d.id
                        )
                    """)
            
            elif cond_type == 'is_duplicate':
                conditions.append("d.is_duplicate = ?")
                params.append(1 if cond_value else 0)
        
        # 构建查询
        join_clause = ' '.join(joins)
        where_clause = f" {operator} ".join(conditions) if conditions else "1=1"
        
        if count_only:
            sql = f"""
                SELECT COUNT(DISTINCT d.id) as count FROM documents d
                {join_clause}
                WHERE d.library_id = ? AND ({where_clause})
            """
        else:
            sql = f"""
                SELECT DISTINCT d.* FROM documents d
                {join_clause}
                WHERE d.library_id = ? AND ({where_clause})
                ORDER BY d.imported_at DESC
                LIMIT ?
            """
            params.append(limit)
        
        return sql, tuple(params)
    
    def create_preset_folder(self, preset_type: str) -> int:
        """
        创建预设智能文件夹
        
        Args:
            preset_type: 预设类型
                - recent: 最近导入
                - uncategorized: 未分类
                - untagged: 未打标签
                - duplicates: 重复文档
                - large_files: 大文件
                
        Returns:
            智能文件夹 ID
        """
        presets = {
            'recent': {
                'name': '最近导入（7天内）',
                'rules': {
                    'operator': 'AND',
                    'conditions': [
                        {'type': 'imported_date', 'operator': 'within_days', 'value': 7}
                    ]
                }
            },
            'uncategorized': {
                'name': '未分类文档',
                'rules': {
                    'operator': 'AND',
                    'conditions': [
                        {'type': 'is_uncategorized', 'operator': 'equals', 'value': True}
                    ]
                }
            },
            'untagged': {
                'name': '未打标签',
                'rules': {
                    'operator': 'AND',
                    'conditions': [
                        {'type': 'is_untagged', 'operator': 'equals', 'value': True}
                    ]
                }
            },
            'duplicates': {
                'name': '重复文档',
                'rules': {
                    'operator': 'AND',
                    'conditions': [
                        {'type': 'is_duplicate', 'operator': 'equals', 'value': True}
                    ]
                }
            },
            'large_files': {
                'name': '大文件（>10MB）',
                'rules': {
                    'operator': 'AND',
                    'conditions': [
                        {'type': 'file_size', 'operator': 'greater_than', 'value': 10 * 1024 * 1024}
                    ]
                }
            }
        }
        
        if preset_type not in presets:
            raise ValueError(f"未知的预设类型: {preset_type}")
        
        preset = presets[preset_type]
        return self.create(preset['name'], preset['rules'])