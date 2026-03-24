"""
文档管家 - 核心模块
包含数据库、库管理、文档模型等核心功能
"""

from .database import Database
from .library import LibraryManager

__all__ = ['Database', 'LibraryManager']
