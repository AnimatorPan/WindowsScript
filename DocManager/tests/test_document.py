"""
文档管理测试
"""
import pytest
from core.document import DocumentManager


class TestDocumentManager:
    """文档管理器测试"""
    
    @pytest.fixture
    def library_id(self, test_db, temp_dir):
        """创建测试库"""
        from core.library import LibraryManager
        
        manager = LibraryManager(test_db)
        storage_path = temp_dir / "library_storage"
        return manager.create("测试库", str(storage_path))
    
    @pytest.fixture
    def doc_manager(self, test_db, library_id):
        """创建文档管理器"""
        return DocumentManager(test_db, library_id)
    
    @pytest.fixture
    def sample_documents(self, test_db, library_id):
        """创建示例文档"""
        doc_ids = []
        for i in range(5):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash, file_type) 
                   VALUES (?, ?, ?, ?, ?)""",
                (library_id, f"doc_{i}.pdf", f"/doc_{i}.pdf", f"hash_{i}", "pdf")
            )
            doc_ids.append(doc_id)
        return doc_ids
    
    def test_get_document(self, doc_manager, sample_documents):
        """测试获取文档"""
        doc_id = sample_documents[0]
        doc = doc_manager.get(doc_id)
        
        assert doc is not None
        assert doc['id'] == doc_id
        assert 'filename' in doc
    
    def test_list_all(self, doc_manager, sample_documents):
        """测试列出所有文档"""
        docs = doc_manager.list_all(limit=10)
        
        assert len(docs) == 5
    
    def test_list_all_pagination(self, doc_manager, sample_documents):
        """测试分页"""
        page1 = doc_manager.list_all(limit=2, offset=0)
        page2 = doc_manager.list_all(limit=2, offset=2)
        
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]['id'] != page2[0]['id']
    
    def test_list_uncategorized(self, doc_manager, sample_documents):
        """测试获取未分类文档"""
        uncategorized = doc_manager.list_uncategorized()
        
        # 所有文档都应该未分类
        assert len(uncategorized) == 5
    
    def test_list_untagged(self, doc_manager, sample_documents):
        """测试获取未打标签文档"""
        untagged = doc_manager.list_untagged()
        
        # 所有文档都应该未打标签
        assert len(untagged) == 5
    
    def test_update_document(self, doc_manager, sample_documents):
        """测试更新文档"""
        doc_id = sample_documents[0]
        
        doc_manager.update(doc_id, filename="新文件名.pdf", note="测试备注")
        
        doc = doc_manager.get(doc_id)
        assert doc['filename'] == "新文件名.pdf"
        assert doc['note'] == "测试备注"
    
    def test_delete_document(self, doc_manager, sample_documents):
        """测试删除文档"""
        doc_id = sample_documents[0]
        
        doc_manager.delete(doc_id)
        
        doc = doc_manager.get(doc_id)
        assert doc is None
    
    def test_mark_as_duplicate(self, doc_manager, sample_documents):
        """测试标记为重复"""
        doc_id = sample_documents[0]
        
        doc_manager.mark_as_duplicate(doc_id, True)
        
        doc = doc_manager.get(doc_id)
        assert doc['is_duplicate'] == 1
    
    def test_list_duplicates(self, doc_manager, test_db, library_id):
        """测试获取重复文档列表"""
        # 插入重复哈希的文档
        same_hash = "duplicate_hash"
        for i in range(3):
            test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"dup_{i}.pdf", f"/dup_{i}.pdf", same_hash)
            )
        
        duplicates = doc_manager.list_duplicates()
        
        assert len(duplicates) >= 3
        assert all(d['file_hash'] == same_hash for d in duplicates)
    
    def test_count_total(self, doc_manager, sample_documents):
        """测试统计文档总数"""
        count = doc_manager.count_total()
        
        assert count == 5
    
    def test_count_by_type(self, doc_manager, test_db, library_id, sample_documents):
        """测试按类型统计"""
        # 插入不同类型文档
        test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, file_type) 
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, "doc.docx", "/doc.docx", "hash_docx", "docx")
        )
        
        counts = doc_manager.count_by_type()
        
        assert 'pdf' in counts
        assert 'docx' in counts
        assert counts['pdf'] >= 5
        assert counts['docx'] >= 1