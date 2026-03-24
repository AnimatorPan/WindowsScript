"""
智能文件夹测试
"""
import pytest
from datetime import datetime, timedelta
from core.smart_folder import SmartFolderManager


class TestSmartFolderManager:
    """智能文件夹管理器测试"""
    
    @pytest.fixture
    def library_id(self, test_db, temp_dir):
        """创建测试库"""
        from core.library import LibraryManager
        
        manager = LibraryManager(test_db)
        storage_path = temp_dir / "library_storage"
        return manager.create("测试库", str(storage_path))
    
    @pytest.fixture
    def sf_manager(self, test_db, library_id):
        """创建智能文件夹管理器"""
        return SmartFolderManager(test_db, library_id)
    
    @pytest.fixture
    def sample_documents(self, test_db, library_id):
        """创建示例文档"""
        doc_ids = []
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # 创建不同类型和时间的文档
        documents = [
            ("recent.pdf", "pdf", now.isoformat()),
            ("old.docx", "docx", (now - timedelta(days=10)).isoformat()),
            ("contract.pdf", "pdf", yesterday.isoformat()),
        ]
        
        for filename, file_type, imported_at in documents:
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash, file_type, imported_at) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (library_id, filename, f"/{filename}", f"hash_{filename}", file_type, imported_at)
            )
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def test_create_smart_folder(self, sf_manager):
        """测试创建智能文件夹"""
        rules = {
            'operator': 'AND',
            'conditions': [
                {'type': 'file_type', 'operator': 'equals', 'value': 'pdf'}
            ]
        }
        
        folder_id = sf_manager.create("PDF文档", rules)
        
        assert folder_id > 0
        
        folder = sf_manager.get(folder_id)
        assert folder['name'] == "PDF文档"
        assert folder['rules']['operator'] == 'AND'
    
    def test_get_smart_folder(self, sf_manager):
        """测试获取智能文件夹"""
        rules = {'operator': 'AND', 'conditions': []}
        folder_id = sf_manager.create("测试文件夹", rules)
        
        folder = sf_manager.get(folder_id)
        
        assert folder is not None
        assert folder['id'] == folder_id
        assert 'rules' in folder
    
    def test_list_all(self, sf_manager):
        """测试列出所有智能文件夹"""
        rules = {'operator': 'AND', 'conditions': []}
        
        sf_manager.create("文件夹1", rules)
        sf_manager.create("文件夹2", rules)
        sf_manager.create("文件夹3", rules, is_enabled=False)
        
        all_folders = sf_manager.list_all()
        assert len(all_folders) == 3
        
        enabled_only = sf_manager.list_all(enabled_only=True)
        assert len(enabled_only) == 2
    
    def test_update_smart_folder(self, sf_manager):
        """测试更新智能文件夹"""
        rules = {'operator': 'AND', 'conditions': []}
        folder_id = sf_manager.create("原名称", rules)
        
        new_rules = {
            'operator': 'OR',
            'conditions': [
                {'type': 'file_type', 'operator': 'equals', 'value': 'pdf'}
            ]
        }
        
        sf_manager.update(folder_id, name="新名称", rules=new_rules, is_enabled=False)
        
        folder = sf_manager.get(folder_id)
        assert folder['name'] == "新名称"
        assert folder['rules']['operator'] == 'OR'
        assert folder['is_enabled'] == 0
    
    def test_delete_smart_folder(self, sf_manager):
        """测试删除智能文件夹"""
        rules = {'operator': 'AND', 'conditions': []}
        folder_id = sf_manager.create("待删除", rules)
        
        sf_manager.delete(folder_id)
        
        folder = sf_manager.get(folder_id)
        assert folder is None
    
    def test_match_by_file_type(self, sf_manager, sample_documents):
        """测试按文件类型匹配"""
        rules = {
            'operator': 'AND',
            'conditions': [
                {'type': 'file_type', 'operator': 'in', 'value': ['pdf']}
            ]
        }
        
        folder_id = sf_manager.create("PDF文档", rules)
        
        docs = sf_manager.get_matched_documents(folder_id)
        
        assert len(docs) == 2  # recent.pdf 和 contract.pdf
        assert all(doc['file_type'] == 'pdf' for doc in docs)
    
    def test_match_by_filename(self, sf_manager, sample_documents):
        """测试按文件名匹配"""
        rules = {
            'operator': 'AND',
            'conditions': [
                {'type': 'filename', 'operator': 'contains', 'value': 'contract'}
            ]
        }
        
        folder_id = sf_manager.create("合同文档", rules)
        
        docs = sf_manager.get_matched_documents(folder_id)
        
        assert len(docs) >= 1
        assert any('contract' in doc['filename'] for doc in docs)
    
    def test_match_by_date(self, sf_manager, sample_documents):
        """测试按日期匹配"""
        rules = {
            'operator': 'AND',
            'conditions': [
                {'type': 'imported_date', 'operator': 'within_days', 'value': 7}
            ]
        }
        
        folder_id = sf_manager.create("最近导入", rules)
        
        docs = sf_manager.get_matched_documents(folder_id)
        
        assert len(docs) >= 2  # recent.pdf 和 contract.pdf
    
    def test_match_uncategorized(self, sf_manager, sample_documents):
        """测试匹配未分类文档"""
        rules = {
            'operator': 'AND',
            'conditions': [
                {'type': 'is_uncategorized', 'operator': 'equals', 'value': True}
            ]
        }
        
        folder_id = sf_manager.create("未分类", rules)
        
        docs = sf_manager.get_matched_documents(folder_id)
        
        # 所有示例文档都应该未分类
        assert len(docs) >= 3
    
    def test_match_combined_rules(self, sf_manager, sample_documents):
        """测试组合规则"""
        rules = {
            'operator': 'AND',
            'conditions': [
                {'type': 'file_type', 'operator': 'equals', 'value': 'pdf'},
                {'type': 'imported_date', 'operator': 'within_days', 'value': 7}
            ]
        }
        
        folder_id = sf_manager.create("最近PDF", rules)
        
        docs = sf_manager.get_matched_documents(folder_id)
        
        assert len(docs) >= 2
        assert all(doc['file_type'] == 'pdf' for doc in docs)
    
    def test_count_matches(self, sf_manager, sample_documents):
        """测试统计匹配数量"""
        rules = {
            'operator': 'AND',
            'conditions': [
                {'type': 'file_type', 'operator': 'equals', 'value': 'pdf'}
            ]
        }
        
        folder_id = sf_manager.create("PDF文档", rules)
        
        count = sf_manager.count_matches(folder_id)
        
        assert count == 2
    
    def test_create_preset_recent(self, sf_manager, sample_documents):
        """测试创建预设：最近导入"""
        folder_id = sf_manager.create_preset_folder('recent')
        
        folder = sf_manager.get(folder_id)
        assert folder is not None
        assert '最近导入' in folder['name']
        
        docs = sf_manager.get_matched_documents(folder_id)
        assert len(docs) >= 2
    
    def test_create_preset_uncategorized(self, sf_manager, sample_documents):
        """测试创建预设：未分类"""
        folder_id = sf_manager.create_preset_folder('uncategorized')
        
        docs = sf_manager.get_matched_documents(folder_id)
        assert len(docs) >= 3
    
    def test_create_preset_large_files(self, sf_manager, test_db, library_id):
        """测试创建预设：大文件"""
        # 创建大文件
        test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash, file_size) 
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, "large.zip", "/large.zip", "hash_large", 15 * 1024 * 1024)
        )
        
        folder_id = sf_manager.create_preset_folder('large_files')
        
        docs = sf_manager.get_matched_documents(folder_id)
        assert len(docs) >= 1