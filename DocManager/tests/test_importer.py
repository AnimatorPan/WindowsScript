"""
文档导入测试
"""
import pytest
from pathlib import Path
from core.importer import Importer, ImportResult


class TestImporter:
    """文档导入器测试"""
    
    @pytest.fixture
    def library_id(self, test_db, temp_dir):
        """创建测试库"""
        from core.library import LibraryManager
        
        manager = LibraryManager(test_db)
        storage_path = temp_dir / "library_storage"
        return manager.create("测试库", str(storage_path))
    
    @pytest.fixture
    def importer(self, test_db, library_id, temp_dir):
        """创建导入器实例"""
        storage_path = temp_dir / "library_storage"
        return Importer(test_db, library_id, str(storage_path))
    
    @pytest.fixture
    def test_files(self, temp_dir):
        """创建测试文件"""
        files_dir = temp_dir / "test_files"
        files_dir.mkdir()
        
        files = []
        for i in range(5):
            file_path = files_dir / f"document_{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(str(file_path))
        
        return files
    
    def test_scan_single_file(self, importer, test_files):
        """测试扫描单个文件"""
        files = importer.scan_files(test_files[0])
        
        assert len(files) == 1
        assert files[0] == test_files[0]
    
    def test_scan_directory(self, importer, temp_dir):
        """测试扫描目录"""
        files_dir = temp_dir / "scan_test"
        files_dir.mkdir()
        
        # 创建文件
        for i in range(3):
            (files_dir / f"file_{i}.txt").write_text(f"content {i}")
        
        files = importer.scan_files(str(files_dir))
        
        assert len(files) == 3
    
    def test_check_duplicate(self, importer, test_db, library_id):
        """测试重复检测"""
        # 插入一个文档
        test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        # 检查重复
        duplicate_id = importer.check_duplicate("hash123")
        assert duplicate_id is not None
        
        # 检查不存在的哈希
        no_duplicate = importer.check_duplicate("hash999")
        assert no_duplicate is None
    
    def test_import_single_file(self, importer, temp_dir):
        """测试导入单个文件"""
        # 创建测试文件
        file_path = temp_dir / "import_test.txt"
        file_path.write_text("Test content for import")
        
        result = importer.import_file(str(file_path))
        
        assert result['success'] is True
        assert result['document_id'] is not None
        assert result['duplicate'] is False
        assert result['error'] is None
    
    def test_import_duplicate_file(self, importer, temp_dir):
        """测试导入重复文件"""
        file_path = temp_dir / "duplicate_test.txt"
        file_path.write_text("Duplicate content")
        
        # 第一次导入
        result1 = importer.import_file(str(file_path))
        assert result1['success'] is True
        
        # 第二次导入（应该检测到重复）
        result2 = importer.import_file(str(file_path), check_duplicate=True)
        assert result2['duplicate'] is True
        assert 'duplicate_id' in result2
    
    def test_import_unsupported_file(self, importer, temp_dir):
        """测试导入不支持的文件类型"""
        file_path = temp_dir / "unsupported.xyz"
        file_path.write_text("content")
        
        result = importer.import_file(str(file_path))
        
        assert result['success'] is False
        assert result.get('skipped') is True
    
    def test_import_nonexistent_file(self, importer):
        """测试导入不存在的文件"""
        result = importer.import_file("/nonexistent/file.txt")
        
        assert result['success'] is False
        assert result['error'] is not None
    
    def test_import_batch(self, importer, test_files):
        """测试批量导入"""
        result = importer.import_batch(test_files)
        
        assert isinstance(result, ImportResult)
        assert result.total == len(test_files)
        assert result.success > 0
        assert result.failed == 0
    
    def test_import_batch_with_progress(self, importer, test_files):
        """测试带进度回调的批量导入"""
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        result = importer.import_batch(
            test_files,
            progress_callback=progress_callback
        )
        
        assert len(progress_calls) == len(test_files)
        assert progress_calls[-1] == (len(test_files), len(test_files))
    
    def test_import_batch_with_duplicates(self, importer, temp_dir):
        """测试批量导入包含重复文件"""
        # 创建相同内容的文件
        file1 = temp_dir / "dup1.txt"
        file2 = temp_dir / "dup2.txt"
        
        file1.write_text("same content")
        file2.write_text("same content")
        
        result = importer.import_batch([str(file1), str(file2)])
        
        assert result.success == 1
        assert result.duplicate == 1
        assert result.total == 2
    
    def test_import_with_copy_to_storage(self, importer, temp_dir):
        """测试复制文件到存储目录"""
        src_file = temp_dir / "source.txt"
        src_file.write_text("content")
        
        result = importer.import_file(str(src_file), copy_to_storage=True)
        
        assert result['success'] is True
        
        # 验证文件已复制到存储目录
        # 注意：这里需要根据实际存储路径验证
    
    def test_import_without_copy(self, importer, temp_dir):
        """测试不复制文件（仅记录路径）"""
        file_path = temp_dir / "nocopy.txt"
        file_path.write_text("content")
        
        result = importer.import_file(str(file_path), copy_to_storage=False)
        
        assert result['success'] is True
    
    def test_create_import_task(self, importer):
        """测试创建导入任务"""
        task_id = importer.create_import_task("/test/source")
        
        assert task_id > 0
    
    def test_update_import_task(self, importer):
        """测试更新导入任务"""
        task_id = importer.create_import_task("/test/source")
        
        result = ImportResult()
        result.total = 10
        result.success = 8
        result.duplicate = 1
        result.failed = 1
        
        importer.update_import_task(task_id, result)
        
        # 验证任务已更新
        task = importer.db.fetch_one(
            "SELECT * FROM import_tasks WHERE id = ?",
            (task_id,)
        )
        
        assert task['total_count'] == 10
        assert task['success_count'] == 8
        assert task['duplicate_count'] == 1
        assert task['failed_count'] == 1
        assert task['status'] == 'completed'