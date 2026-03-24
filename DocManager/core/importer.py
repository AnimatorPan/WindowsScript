"""
文档导入模块
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging

from .database import Database
from .models import Document, ImportTask
from utils.hash_utils import calculate_file_hash
from utils.file_utils import (
    get_file_type, get_mime_type, get_file_size,
    get_relative_path, scan_directory, copy_file, is_supported_file
)

logger = logging.getLogger(__name__)


class ImportResult:
    """导入结果"""
    def __init__(self):
        self.total = 0
        self.success = 0
        self.duplicate = 0
        self.failed = 0
        self.skipped = 0
        self.errors: List[str] = []


class Importer:
    """文档导入器"""
    
    def __init__(self, db: Database, library_id: int, storage_path: str):
        """
        初始化导入器
        
        Args:
            db: 数据库连接
            library_id: 库 ID
            storage_path: 文档存储路径
        """
        self.db = db
        self.library_id = library_id
        self.storage_path = Path(storage_path)
    
    def scan_files(self, path: str, include_subdirs: bool = True) -> List[str]:
        """
        扫描文件或文件夹
        
        Args:
            path: 文件或文件夹路径
            include_subdirs: 是否包含子目录
            
        Returns:
            文件路径列表
        """
        path_obj = Path(path)
        
        if path_obj.is_file():
            return [str(path_obj.absolute())]
        elif path_obj.is_dir():
            return scan_directory(str(path_obj), include_subdirs)
        else:
            logger.warning(f"路径不存在: {path}")
            return []
    
    def check_duplicate(self, file_hash: str) -> Optional[int]:
        """
        检查文件是否重复
        
        Args:
            file_hash: 文件哈希值
            
        Returns:
            重复文档的 ID，不重复返回 None
        """
        sql = """
            SELECT id FROM documents 
            WHERE library_id = ? AND file_hash = ? 
            LIMIT 1
        """
        result = self.db.fetch_one(sql, (self.library_id, file_hash))
        return result['id'] if result else None
    
    def import_file(
        self, 
        file_path: str, 
        copy_to_storage: bool = True,
        check_duplicate: bool = True
    ) -> Dict:
        """
        导入单个文件
        
        Args:
            file_path: 文件路径
            copy_to_storage: 是否复制到存储目录
            check_duplicate: 是否检查重复
            
        Returns:
            导入结果字典
        """
        result = {
            'success': False,
            'document_id': None,
            'duplicate': False,
            'error': None
        }
        
        try:
            file_path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not file_path_obj.exists():
                result['error'] = "文件不存在"
                return result
            
            # 检查文件类型
            if not is_supported_file(file_path):
                result['error'] = "不支持的文件类型"
                result['skipped'] = True
                return result
            
            # 计算文件哈希
            file_hash = calculate_file_hash(file_path)
            if not file_hash:
                result['error'] = "计算文件哈希失败"
                return result
            
            # 检查重复
            if check_duplicate:
                duplicate_id = self.check_duplicate(file_hash)
                if duplicate_id:
                    result['duplicate'] = True
                    result['duplicate_id'] = duplicate_id
                    logger.info(f"文件重复: {file_path}, 原文档ID: {duplicate_id}")
                    return result
            
            # 准备文件信息
            filename = file_path_obj.name
            file_size = get_file_size(file_path)
            file_type = get_file_type(file_path)
            mime_type = get_mime_type(file_path)
            
            file_stat = file_path_obj.stat()
            created_at = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # 目标路径
            if copy_to_storage:
                # 按类型组织目录
                target_dir = self.storage_path / file_type if file_type else self.storage_path / "other"
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成唯一文件名（避免冲突）
                target_path = target_dir / filename
                counter = 1
                while target_path.exists():
                    stem = file_path_obj.stem
                    suffix = file_path_obj.suffix
                    target_path = target_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # 复制文件
                if not copy_file(file_path, str(target_path)):
                    result['error'] = "复制文件失败"
                    return result
                
                filepath = get_relative_path(str(target_path), str(self.storage_path))
            else:
                filepath = str(file_path_obj.absolute())
            
            # 插入数据库
            sql = """
                INSERT INTO documents (
                    library_id, filename, filepath, file_hash, file_size,
                    file_type, mime_type, created_at, modified_at, import_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            document_id = self.db.insert(sql, (
                self.library_id, filename, filepath, file_hash, file_size,
                file_type, mime_type, created_at, modified_at, file_path
            ))
            
            result['success'] = True
            result['document_id'] = document_id
            
            logger.info(f"导入文件成功: {filename} (ID: {document_id})")
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"导入文件失败: {file_path}, {e}")
        
        return result
    
    def import_batch(
        self,
        file_list: List[str],
        copy_to_storage: bool = True,
        check_duplicate: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ImportResult:
        """
        批量导入文件
        
        Args:
            file_list: 文件路径列表
            copy_to_storage: 是否复制到存储目录
            check_duplicate: 是否检查重复
            progress_callback: 进度回调函数 (当前索引, 总数)
            
        Returns:
            ImportResult 对象
        """
        result = ImportResult()
        result.total = len(file_list)
        
        logger.info(f"开始批量导入，共 {result.total} 个文件")
        
        for idx, file_path in enumerate(file_list):
            try:
                import_result = self.import_file(file_path, copy_to_storage, check_duplicate)
                
                if import_result['success']:
                    result.success += 1
                elif import_result.get('duplicate'):
                    result.duplicate += 1
                elif import_result.get('skipped'):
                    result.skipped += 1
                else:
                    result.failed += 1
                    if import_result.get('error'):
                        result.errors.append(f"{file_path}: {import_result['error']}")
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(idx + 1, result.total)
            
            except Exception as e:
                result.failed += 1
                result.errors.append(f"{file_path}: {str(e)}")
                logger.error(f"导入失败: {file_path}, {e}")
        
        logger.info(
            f"批量导入完成: 成功 {result.success}, "
            f"重复 {result.duplicate}, 失败 {result.failed}, 跳过 {result.skipped}"
        )
        
        return result
    
    def create_import_task(self, source_path: str) -> int:
        """
        创建导入任务记录
        
        Args:
            source_path: 导入来源路径
            
        Returns:
            任务 ID
        """
        sql = """
            INSERT INTO import_tasks (library_id, source_path, status, started_at)
            VALUES (?, ?, ?, ?)
        """
        task_id = self.db.insert(sql, (
            self.library_id,
            source_path,
            'running',
            datetime.now().isoformat()
        ))
        return task_id
    
    def update_import_task(self, task_id: int, result: ImportResult, status: str = 'completed'):
        """
        更新导入任务结果
        
        Args:
            task_id: 任务 ID
            result: 导入结果
            status: 任务状态
        """
        sql = """
            UPDATE import_tasks SET
                total_count = ?,
                success_count = ?,
                duplicate_count = ?,
                failed_count = ?,
                status = ?,
                completed_at = ?,
                error_message = ?
            WHERE id = ?
        """
        error_message = "\n".join(result.errors[:10]) if result.errors else None
        
        self.db.update(sql, (
            result.total,
            result.success,
            result.duplicate,
            result.failed,
            status,
            datetime.now().isoformat(),
            error_message,
            task_id
        ))