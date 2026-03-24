"""
数据模型定义
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Library:
    """库模型"""
    id: Optional[int] = None
    name: str = ""
    storage_path: str = ""
    db_path: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    status: str = "active"


@dataclass
class Document:
    """文档模型"""
    id: Optional[int] = None
    library_id: int = 0
    filename: str = ""
    filepath: str = ""
    file_hash: str = ""
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    imported_at: Optional[datetime] = None
    import_source: Optional[str] = None
    status: str = "normal"
    is_duplicate: bool = False
    note: Optional[str] = None


@dataclass
class Category:
    """分类模型"""
    id: Optional[int] = None
    library_id: int = 0
    name: str = ""
    parent_id: Optional[int] = None
    order_index: int = 0
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    icon: Optional[str] = None


@dataclass
class Tag:
    """标签模型"""
    id: Optional[int] = None
    library_id: int = 0
    name: str = ""
    parent_id: Optional[int] = None
    color: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class SmartFolder:
    """智能文件夹模型"""
    id: Optional[int] = None
    library_id: int = 0
    name: str = ""
    rules_json: str = ""
    is_enabled: bool = True
    order_index: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ImportTask:
    """导入任务模型"""
    id: Optional[int] = None
    library_id: int = 0
    source_path: str = ""
    total_count: int = 0
    success_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None