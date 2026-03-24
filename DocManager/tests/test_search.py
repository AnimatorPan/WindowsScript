"""
搜索引擎测试
"""
import pytest
from datetime import datetime, timedelta
from core.search import SearchEngine


class TestSearchEngine:
    """搜索引擎测试"""
    
    @pytest.fixture
    def library_id(self, test_db, temp_dir):
        """创建测试库"""
        from core.library import LibraryManager
        
        manager = LibraryManager(test_db)
        storage_path = temp_dir / "library_storage"
        return manager.create("测试库", str(storage_path))
    
    @pytest.fixture
    def search_engine(self, test_db, library_id):
        """创建搜索引擎"""
        return SearchEngine(test_db, library_id)
    
    @pytest.fixture
    def sample_documents(self, test_db, library_id):
        """创建示例文档"""
        doc_ids = []
        
        # 创建不同类型的文档
        documents = [
            ("合同文档.pdf", "pdf"),
            ("项目方案.docx", "docx"),
            ("数据报表.xlsx", "xlsx"),
            ("会议纪要.txt", "txt"),
            ("设计稿.psd", "psd"),
        ]
        
        for filename, file_type in documents:
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash, file_type, file_size) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (library_id, filename, f"/{filename}", f"hash_{filename}", file_type, 1024 * 100)
            )
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def test_search_by_filename(self, search_engine, sample_documents):
        """测试按文件名搜索"""
        results = search_engine.search_by_filename("合同")
        
        assert len(results) == 1
        assert "合同" in results[0]['filename']
    
    def test_search_by_filename_partial(self, search_engine, sample_documents):
        """测试部分匹配"""
        results = search_engine.search_by_filename("文档")
        
        assert len(results) == 1
        assert "合同文档" in results[0]['filename']
    
    def test_filter_by_type(self, search_engine, sample_documents):
        """测试按类型筛选"""
        results = search_engine.filter_by_type(['pdf', 'docx'])
        
        assert len(results) == 2
        assert all(doc['file_type'] in ['pdf', 'docx'] for doc in results)
    
    def test_filter_by_type_single(self, search_engine, sample_documents):
        """测试单一类型筛选"""
        results = search_engine.filter_by_type(['pdf'])
        
        assert len(results) == 1
        assert results[0]['file_type'] == 'pdf'
    
    def test_filter_by_tags(self, search_engine, test_db, library_id, sample_documents):
        """测试按标签筛选"""
        from core.tag import TagManager
        
        tag_manager = TagManager(test_db, library_id)
        tag_id = tag_manager.create("重要")
        
        # 给前两个文档打标签
        tag_manager.add_to_document(tag_id, sample_documents[0])
        tag_manager.add_to_document(tag_id, sample_documents[1])
        
        results = search_engine.filter_by_tags([tag_id])
        
        assert len(results) == 2
    
    def test_filter_by_tags_match_all(self, search_engine, test_db, library_id, sample_documents):
        """测试匹配所有标签"""
        from core.tag import TagManager
        
        tag_manager = TagManager(test_db, library_id)
        tag1_id = tag_manager.create("重要")
        tag2_id = tag_manager.create("紧急")
        
        # 第一个文档有两个标签
        tag_manager.add_to_document(tag1_id, sample_documents[0])
        tag_manager.add_to_document(tag2_id, sample_documents[0])
        
        # 第二个文档只有一个标签
        tag_manager.add_to_document(tag1_id, sample_documents[1])
        
        results = search_engine.filter_by_tags([tag1_id, tag2_id], match_all=True)
        
        assert len(results) == 1
        assert results[0]['id'] == sample_documents[0]
    
    def test_filter_by_category(self, search_engine, test_db, library_id, sample_documents):
        """测试按分类筛选"""
        from core.category import CategoryManager
        
        cat_manager = CategoryManager(test_db, library_id)
        cat_id = cat_manager.create("合同类")
        
        # 添加文档到分类
        cat_manager.add_document(cat_id, sample_documents[0])
        cat_manager.add_document(cat_id, sample_documents[1])
        
        results = search_engine.filter_by_category(cat_id)
        
        assert len(results) == 2
    
    def test_filter_by_date_range(self, search_engine, test_db, library_id):
        """测试按日期范围筛选"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # 创建不同日期的文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, imported_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, "today.pdf", "/today.pdf", "hash_today", now.isoformat())
        )
        
        results = search_engine.filter_by_date_range(
            'imported_at',
            start_date=yesterday.isoformat(),
            end_date=tomorrow.isoformat()
        )
        
        assert len(results) >= 1
        assert any(doc['id'] == doc_id for doc in results)
    
    def test_filter_by_size_range(self, search_engine, test_db, library_id):
        """测试按大小范围筛选"""
        # 创建不同大小的文档
        small_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, file_size) 
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, "small.pdf", "/small.pdf", "hash_small", 100)
        )
        
        large_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, file_size) 
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, "large.pdf", "/large.pdf", "hash_large", 10000000)
        )
        
        # 筛选大文件
        results = search_engine.filter_by_size_range(min_size=1000000)
        
        assert len(results) >= 1
        assert any(doc['id'] == large_id for doc in results)
        assert not any(doc['id'] == small_id for doc in results)
    
    def test_complex_search(self, search_engine, test_db, library_id):
        """测试复杂组合搜索"""
        from core.tag import TagManager
        
        # 创建文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, file_type, file_size) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (library_id, "重要合同.pdf", "/重要合同.pdf", "hash_contract", "pdf", 5000)
        )
        
        # 添加标签
        tag_manager = TagManager(test_db, library_id)
        tag_id = tag_manager.create("重要")
        tag_manager.add_to_document(tag_id, doc_id)
        
        # 复杂搜索
        results = search_engine.complex_search({
            'keyword': '合同',
            'file_types': ['pdf'],
            'tag_ids': [tag_id],
            'min_size': 1000,
            'max_size': 10000
        })
        
        assert len(results) >= 1
        assert any(doc['id'] == doc_id for doc in results)
    
    def test_complex_search_uncategorized(self, search_engine, test_db, library_id):
        """测试搜索未分类文档"""
        # 创建未分类文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "uncategorized.pdf", "/uncategorized.pdf", "hash_uncat")
        )
        
        results = search_engine.complex_search({
            'is_uncategorized': True
        })
        
        assert len(results) >= 1
        assert any(doc['id'] == doc_id for doc in results)
    
    def test_get_recent_documents(self, search_engine, sample_documents):
        """测试获取最近文档"""
        results = search_engine.get_recent_documents(days=30)
        
        assert len(results) >= len(sample_documents)