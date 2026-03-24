"""
文档导入模块
处理文档导入、元数据提取、去重检测等功能
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ImportStatus(Enum):
    """导入状态"""
    SUCCESS = "success"
    DUPLICATE = "duplicate"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ImportResult:
    """导入结果"""
    file_path: str
    status: ImportStatus
    document_id: Optional[int] = None
    message: str = ""
    original_name: str = ""
    new_name: str = ""


@dataclass
class DocumentInfo:
    """文档信息"""
    id: int
    name: str
    original_path: str
    storage_path: str
    file_type: str
    file_size: int
    file_hash: str
    created_at: str
    modified_at: str
    imported_at: str
    description: str = ""
    tags: str = ""


class DocumentImporter:
    """文档导入器"""
    
    # 支持的文件类型
    SUPPORTED_TYPES = {
        '.pdf': 'PDF文档',
        '.doc': 'Word文档',
        '.docx': 'Word文档',
        '.xls': 'Excel表格',
        '.xlsx': 'Excel表格',
        '.ppt': 'PowerPoint演示',
        '.pptx': 'PowerPoint演示',
        '.txt': '文本文件',
        '.md': 'Markdown文档',
        '.png': '图片',
        '.jpg': '图片',
        '.jpeg': '图片',
        '.gif': '图片',
        '.bmp': '图片',
        '.zip': '压缩文件',
        '.rar': '压缩文件',
        '.7z': '压缩文件',
    }
    
    def __init__(self, library_path: str):
        """
        初始化导入器
        
        Args:
            library_path: 文档库路径
        """
        self.library_path = library_path
        self.files_dir = os.path.join(library_path, 'files')
        
        # 确保文件存储目录存在
        os.makedirs(self.files_dir, exist_ok=True)
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希（MD5）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_file_type(self, file_path: str) -> str:
        """
        获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型描述
        """
        ext = Path(file_path).suffix.lower()
        return self.SUPPORTED_TYPES.get(ext, '其他文件')
    
    def is_supported(self, file_path: str) -> bool:
        """
        检查文件类型是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_TYPES
    
    def generate_storage_path(self, file_path: str) -> str:
        """
        生成存储路径
        按日期组织：files/YYYY/MM/文件名
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            存储路径（相对路径）
        """
        now = datetime.now()
        date_dir = os.path.join(
            str(now.year),
            f"{now.month:02d}"
        )
        
        # 获取文件名，处理重名
        original_name = Path(file_path).name
        base_name = Path(file_path).stem
        ext = Path(file_path).suffix
        
        # 添加时间戳避免重名
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        new_name = f"{base_name}_{timestamp}{ext}"
        
        return os.path.join(date_dir, new_name)
    
    def import_file(self, file_path: str, db_connection) -> ImportResult:
        """
        导入单个文件
        
        Args:
            file_path: 文件路径
            db_connection: 数据库连接
            
        Returns:
            导入结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return ImportResult(
                    file_path=file_path,
                    status=ImportStatus.ERROR,
                    message="文件不存在"
                )
            
            # 检查文件类型
            if not self.is_supported(file_path):
                return ImportResult(
                    file_path=file_path,
                    status=ImportStatus.SKIPPED,
                    message=f"不支持的文件类型: {Path(file_path).suffix}",
                    original_name=Path(file_path).name
                )
            
            # 计算文件哈希
            file_hash = self.calculate_file_hash(file_path)
            
            # 检查是否已存在（去重）
            from core.database import Database
            if isinstance(db_connection, Database):
                existing = db_connection.fetchone(
                    'SELECT id FROM documents WHERE file_hash = ?',
                    (file_hash,)
                )
                if existing:
                    return ImportResult(
                        file_path=file_path,
                        status=ImportStatus.DUPLICATE,
                        message="文件已存在（基于内容检测）",
                        original_name=Path(file_path).name
                    )
            
            # 生成存储路径
            relative_path = self.generate_storage_path(file_path)
            storage_path = os.path.join(self.files_dir, relative_path)
            
            # 创建目标目录
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            
            # 复制文件
            shutil.copy2(file_path, storage_path)
            
            # 获取文件信息
            stat = os.stat(file_path)
            file_type = self.get_file_type(file_path)
            
            # 插入数据库
            if isinstance(db_connection, Database):
                # 检查数据库表结构（兼容旧版本）
                try:
                    # 尝试获取表信息，检查是否有 name 列
                    cursor = db_connection._connection.execute("PRAGMA table_info(documents)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if 'name' in columns:
                        # 新表结构
                        document_data = {
                            'name': Path(file_path).name,
                            'original_path': file_path,
                            'storage_path': relative_path,
                            'file_type': file_type,
                            'file_size': stat.st_size,
                            'file_hash': file_hash,
                            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'imported_at': datetime.now().isoformat(),
                            'description': '',
                            'tags': ''
                        }
                    elif 'filename' in columns:
                        # 旧表结构
                        document_data = {
                            'filename': Path(file_path).name,
                            'filepath': relative_path,
                            'file_hash': file_hash,
                            'size': stat.st_size,
                            'file_type': file_type,
                            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'imported_at': datetime.now().isoformat(),
                            'library_id': 1  # 默认库ID
                        }
                    else:
                        return ImportResult(
                            file_path=file_path,
                            status=ImportStatus.ERROR,
                            message="未知的数据库表结构"
                        )
                    
                    document_id = db_connection.insert('documents', document_data)
                    
                except Exception as e:
                    return ImportResult(
                        file_path=file_path,
                        status=ImportStatus.ERROR,
                        message=f"数据库操作失败: {str(e)}"
                    )
                
                return ImportResult(
                    file_path=file_path,
                    status=ImportStatus.SUCCESS,
                    document_id=document_id,
                    message="导入成功",
                    original_name=Path(file_path).name,
                    new_name=Path(storage_path).name
                )
            else:
                return ImportResult(
                    file_path=file_path,
                    status=ImportStatus.ERROR,
                    message="数据库连接无效"
                )
                
        except Exception as e:
            return ImportResult(
                file_path=file_path,
                status=ImportStatus.ERROR,
                message=f"导入失败: {str(e)}",
                original_name=Path(file_path).name
            )
    
    def import_files(self, file_paths: List[str], db_connection, 
                     progress_callback=None) -> List[ImportResult]:
        """
        批量导入文件
        
        Args:
            file_paths: 文件路径列表
            db_connection: 数据库连接
            progress_callback: 进度回调函数(current, total, result)
            
        Returns:
            导入结果列表
        """
        results = []
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths, 1):
            result = self.import_file(file_path, db_connection)
            results.append(result)
            
            if progress_callback:
                progress_callback(i, total, result)
        
        return results
    
    def get_import_summary(self, results: List[ImportResult]) -> Dict[str, int]:
        """
        获取导入摘要
        
        Args:
            results: 导入结果列表
            
        Returns:
            统计信息
        """
        summary = {
            'total': len(results),
            'success': 0,
            'duplicate': 0,
            'error': 0,
            'skipped': 0
        }
        
        for result in results:
            if result.status == ImportStatus.SUCCESS:
                summary['success'] += 1
            elif result.status == ImportStatus.DUPLICATE:
                summary['duplicate'] += 1
            elif result.status == ImportStatus.ERROR:
                summary['error'] += 1
            elif result.status == ImportStatus.SKIPPED:
                summary['skipped'] += 1
        
        return summary
