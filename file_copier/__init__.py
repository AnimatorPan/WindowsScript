"""
文件批量复制工具
从源文件夹复制同名同格式文件到目标文件夹
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

from .config import get_config_manager, AppConfig, ConfigManager
from .copier import FileCopier, CopyTask, CopyResult

__all__ = [
    'get_config_manager',
    'AppConfig',
    'ConfigManager',
    'FileCopier',
    'CopyTask',
    'CopyResult',
]
