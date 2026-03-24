"""
去重检测测试
"""
import pytest
from core.duplicate_detector import DuplicateDetector


class TestDuplicateDetector:
    """去重检测器测试"""
    
    @pytest.fixture
    def library_id(self, test_db, temp_dir):
        """创建测试库"""
        from core.library import LibraryManager
        
        manager = LibraryManager(test_db)
        storage_path = temp_dir / "library_storage"
        return manager.create("测试库", str(storage_path))
    
    @pytest.fixture
    def detector(self, test_db, library_id):
        """创建去重检测器"""
        return DuplicateDetector(test_db, library_id)
    
    def test_find_exact_duplicates(self, detector, test_db, library_id):
        """测试查找完全重复"""
        # 创建重复文档
        same_hash = "duplicate_hash"
        for i in range(3):
            test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"dup_{i}.pdf", f"/dup_{i}.pdf", same_hash)
            )
        
        # 创建不重复文档
        test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "unique.pdf", "/unique.pdf", "unique_hash")
        )
        
        duplicates = detector.find_exact_duplicates()
        
        assert len(duplicates) == 1  # 一个重复组
        assert len(duplicates[0]) == 3  # 包含3个文档
    
    def test_find_similar_by_name(self, detector, test_db, library_id):
        """测试查找文件名相似的文档"""
        # 创建相似命名的文档
        similar_names = [
            "项目报告.pdf",
            "项目报告_v2.pdf",
            "项目报告_final.pdf",
        ]
        
        for name in similar_names:
            test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, name, f"/{name}", f"hash_{name}")
            )
        
        similar = detector.find_similar_by_name(similarity_threshold=0.6)
        
        assert len(similar) >= 1
        assert len(similar[0]) >= 2
    
    def test_find_similar_by_size(self, detector, test_db, library_id):
        """测试查找大小相近的文档"""
        # 创建大小相近的文档
        base_size = 10000
        for i in range(3):
            test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash, file_size) 
                   VALUES (?, ?, ?, ?, ?)""",
                (library_id, f"file_{i}.pdf", f"/file_{i}.pdf", f"hash_{i}", base_size + i * 100)
            )
        
        similar = detector.find_similar_by_size(size_tolerance=500)
        
        assert len(similar) >= 1
        assert len(similar[0]) >= 2
    
    def test_mark_as_duplicate(self, detector, test_db, library_id):
        """测试标记为重复"""
        # 创建文档
        doc_ids = []
        for i in range(3):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"doc_{i}.pdf", f"/doc_{i}.pdf", "same_hash")
            )
            doc_ids.append(doc_id)
        
        # 标记为重复，保留第一个
        detector.mark_as_duplicate(doc_ids, keep_id=doc_ids[0])
        
        # 验证
        for doc_id in doc_ids[1:]:
            doc = test_db.fetch_one("SELECT * FROM documents WHERE id = ?", (doc_id,))
            assert doc['is_duplicate'] == 1
        
        # 保留的文档不应被标记
        kept_doc = test_db.fetch_one("SELECT * FROM documents WHERE id = ?", (doc_ids[0],))
        assert kept_doc['is_duplicate'] == 0
    
    def test_unmark_duplicate(self, detector, test_db, library_id):
        """测试取消重复标记"""
        # 创建已标记为重复的文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, is_duplicate) 
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, "dup.pdf", "/dup.pdf", "hash123", 1)
        )
        
        # 取消标记
        detector.unmark_duplicate(doc_id)
        
        # 验证
        doc = test_db.fetch_one("SELECT * FROM documents WHERE id = ?", (doc_id,))
        assert doc['is_duplicate'] == 0
    
    def test_get_duplicate_statistics(self, detector, test_db, library_id):
        """测试获取重复统计"""
        # 创建文档
        # 3个重复
        for i in range(3):
            test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash, file_size, is_duplicate) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (library_id, f"dup_{i}.pdf", f"/dup_{i}.pdf", "dup_hash", 1024, 1 if i > 0 else 0)
            )
        
        # 1个不重复
        test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, file_size) 
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, "unique.pdf", "/unique.pdf", "unique_hash", 1024)
        )
        
        stats = detector.get_duplicate_statistics()
        
        assert stats['total_documents'] == 4
        assert stats['duplicate_count'] == 2
        assert stats['duplicate_groups'] == 1
        assert stats['wasted_space'] == 2048  # 2 * 1024