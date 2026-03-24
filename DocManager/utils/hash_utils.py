"""
文件哈希计算工具
"""
import hashlib
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str, algorithm: str = "sha256", chunk_size: int = 8192) -> Optional[str]:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法（md5, sha1, sha256）
        chunk_size: 读取块大小
        
    Returns:
        哈希值字符串，失败返回 None
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    except Exception as e:
        logger.error(f"计算文件哈希失败: {file_path}, {e}")
        return None


def calculate_quick_hash(file_path: str, sample_size: int = 1024 * 1024) -> Optional[str]:
    """
    快速哈希（仅计算文件头部和大小，适合大文件）
    
    Args:
        file_path: 文件路径
        sample_size: 采样大小（字节）
        
    Returns:
        哈希值字符串
    """
    try:
        file_size = Path(file_path).stat().st_size
        
        hash_obj = hashlib.sha256()
        hash_obj.update(str(file_size).encode())
        
        with open(file_path, 'rb') as f:
            # 读取前 N 字节
            sample = f.read(sample_size)
            hash_obj.update(sample)
        
        return hash_obj.hexdigest()
    
    except Exception as e:
        logger.error(f"快速哈希计算失败: {file_path}, {e}")
        return None