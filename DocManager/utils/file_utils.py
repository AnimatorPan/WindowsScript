"""
文件操作工具
"""
import os
import shutil
import mimetypes
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def get_file_type(file_path: str) -> str:
    """
    获取文件类型（扩展名）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件扩展名（小写，不含点）
    """
    ext = Path(file_path).suffix.lower()
    return ext[1:] if ext else ""


def get_mime_type(file_path: str) -> Optional[str]:
    """
    获取文件 MIME 类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        MIME 类型字符串
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节）
    """
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        logger.error(f"获取文件大小失败: {file_path}, {e}")
        return 0


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为可读字符串
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的字符串（如 "1.5 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    获取相对路径
    
    Args:
        file_path: 文件绝对路径
        base_path: 基准路径
        
    Returns:
        相对路径
    """
    try:
        return str(Path(file_path).relative_to(base_path))
    except ValueError:
        return str(Path(file_path).name)


def scan_directory(directory: str, include_subdirs: bool = True, file_patterns: Optional[List[str]] = None) -> List[str]:
    """
    扫描目录获取文件列表
    
    Args:
        directory: 目录路径
        include_subdirs: 是否包含子目录
        file_patterns: 文件匹配模式列表（如 ['*.pdf', '*.docx']）
        
    Returns:
        文件路径列表
    """
    files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        logger.warning(f"目录不存在: {directory}")
        return files
    
    try:
        if include_subdirs:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for item in dir_path.glob(pattern):
            if item.is_file():
                # 文件模式匹配
                if file_patterns:
                    if any(item.match(pattern) for pattern in file_patterns):
                        files.append(str(item.absolute()))
                else:
                    files.append(str(item.absolute()))
        
        logger.info(f"扫描目录完成: {directory}, 找到 {len(files)} 个文件")
    
    except Exception as e:
        logger.error(f"扫描目录失败: {directory}, {e}")
    
    return files


def copy_file(src: str, dst: str, overwrite: bool = False) -> bool:
    """
    复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在文件
        
    Returns:
        是否成功
    """
    try:
        dst_path = Path(dst)
        
        if dst_path.exists() and not overwrite:
            logger.warning(f"目标文件已存在: {dst}")
            return False
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        
        return True
    
    except Exception as e:
        logger.error(f"复制文件失败: {src} -> {dst}, {e}")
        return False


def is_supported_file(file_path: str) -> bool:
    """
    判断是否为支持的文件类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否支持
    """
    supported_extensions = {
        'txt', 'md', 'rtf',
        'doc', 'docx',
        'xls', 'xlsx',
        'ppt', 'pptx',
        'pdf',
        'jpg', 'jpeg', 'png', 'gif', 'bmp',
        'zip', 'rar', '7z',
    }
    
    ext = get_file_type(file_path)
    return ext in supported_extensions