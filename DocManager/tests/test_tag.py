"""
标签管理测试
"""
import pytest
from core.tag import TagManager


class TestTagManager:
    """标签管理器测试"""
    
    @pytest.fixture
    def library_id(self, test_db, temp_dir):
        """创建测试库"""
        from core.library import LibraryManager
        
        manager = LibraryManager(test_db)
        storage_path = temp_dir / "library_storage"
        return manager.create("测试库", str(storage_path))
    
    @pytest.fixture
    def tag_manager(self, test_db, library_id):
        """创建标签管理器"""
        return TagManager(test_db, library_id)
    
    def test_create_tag(self, tag_manager):
        """测试创建标签"""
        tag_id = tag_manager.create("测试标签", color="#FF5733", description="测试描述")
        
        assert tag_id > 0
        
        tag = tag_manager.get(tag_id)
        assert tag['name'] == "测试标签"
        assert tag['color'] == "#FF5733"
        assert tag['description'] == "测试描述"
    
    def test_create_subtag(self, tag_manager):
        """测试创建子标签"""
        parent_id = tag_manager.create("父标签")
        child_id = tag_manager.create("子标签", parent_id=parent_id)
        
        child = tag_manager.get(child_id)
        assert child['parent_id'] == parent_id
    
    def test_get_tag(self, tag_manager):
        """测试获取标签"""
        tag_id = tag_manager.create("测试标签")
        tag = tag_manager.get(tag_id)
        
        assert tag is not None
        assert tag['id'] == tag_id
    
    def test_get_tag_by_name(self, tag_manager):
        """测试根据名称获取标签"""
        tag_manager.create("测试标签")
        tag = tag_manager.get_by_name("测试标签")
        
        assert tag is not None
        assert tag['name'] == "测试标签"
    
    def test_list_all(self, tag_manager):
        """测试列出所有标签"""
        for i in range(3):
            tag_manager.create(f"标签{i}")
        
        tags = tag_manager.list_all()
        
        assert len(tags) == 3
    
    def test_get_tree(self, tag_manager):
        """测试获取标签树"""
        parent_id = tag_manager.create("项目")
        tag_manager.create("2024", parent_id=parent_id)
        tag_manager.create("2023", parent_id=parent_id)
        
        tree = tag_manager.get_tree()
        
        assert len(tree) == 1
        assert tree[0]['name'] == "项目"
        assert len(tree[0]['children']) == 2
    
    def test_get_children(self, tag_manager):
        """测试获取子标签"""
        parent_id = tag_manager.create("父标签")
        tag_manager.create("子标签1", parent_id=parent_id)
        tag_manager.create("子标签2", parent_id=parent_id)
        
        children = tag_manager.get_children(parent_id)
        
        assert len(children) == 2
    
    def test_update_tag(self, tag_manager):
        """测试更新标签"""
        tag_id = tag_manager.create("原名称", color="#000000")
        
        tag_manager.update(tag_id, name="新名称", color="#FFFFFF")
        
        tag = tag_manager.get(tag_id)
        assert tag['name'] == "新名称"
        assert tag['color'] == "#FFFFFF"
    
    def test_delete_tag(self, tag_manager):
        """测试删除标签"""
        tag_id = tag_manager.create("待删除标签")
        
        tag_manager.delete(tag_id)
        
        tag = tag_manager.get(tag_id)
        assert tag is None
    
    def test_delete_tag_cascade(self, tag_manager):
        """测试级联删除"""
        parent_id = tag_manager.create("父标签")
        child_id = tag_manager.create("子标签", parent_id=parent_id)
        
        tag_manager.delete(parent_id, cascade=True)
        
        assert tag_manager.get(parent_id) is None
        assert tag_manager.get(child_id) is None
    
    def test_delete_tag_preserve_children(self, tag_manager):
        """测试删除标签但保留子标签"""
        parent_id = tag_manager.create("父标签")
        child_id = tag_manager.create("子标签", parent_id=parent_id)
        
        tag_manager.delete(parent_id, cascade=False)
        
        child = tag_manager.get(child_id)
        assert child is not None
        assert child['parent_id'] is None
    
    def test_add_tag_to_document(self, tag_manager, test_db, library_id):
        """测试给文档添加标签"""
        tag_id = tag_manager.create("测试标签")
        
        # 创建文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        tag_manager.add_to_document(tag_id, doc_id)
        
        # 验证关联
        result = test_db.fetch_one(
            "SELECT * FROM document_tags WHERE document_id = ? AND tag_id = ?",
            (doc_id, tag_id)
        )
        
        assert result is not None
    
    def test_remove_tag_from_document(self, tag_manager, test_db, library_id):
        """测试从文档移除标签"""
        tag_id = tag_manager.create("测试标签")
        
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        tag_manager.add_to_document(tag_id, doc_id)
        tag_manager.remove_from_document(tag_id, doc_id)
        
        # 验证已移除
        result = test_db.fetch_one(
            "SELECT * FROM document_tags WHERE document_id = ? AND tag_id = ?",
            (doc_id, tag_id)
        )
        
        assert result is None
    
    def test_get_document_count(self, tag_manager, test_db, library_id):
        """测试获取标签文档数量"""
        tag_id = tag_manager.create("测试标签")
        
        # 添加多个文档
        for i in range(3):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"doc_{i}.pdf", f"/doc_{i}.pdf", f"hash_{i}")
            )
            tag_manager.add_to_document(tag_id, doc_id)
        
        count = tag_manager.get_document_count(tag_id)
        
        assert count == 3
    
    def test_get_popular_tags(self, tag_manager, test_db, library_id):
        """测试获取热门标签"""
        tag1_id = tag_manager.create("热门标签")
        tag2_id = tag_manager.create("冷门标签")
        
        # tag1 添加 5 个文档
        for i in range(5):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"doc_{i}.pdf", f"/doc_{i}.pdf", f"hash_{i}")
            )
            tag_manager.add_to_document(tag1_id, doc_id)
        
        # tag2 添加 1 个文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "doc_x.pdf", "/doc_x.pdf", "hash_x")
        )
        tag_manager.add_to_document(tag2_id, doc_id)
        
        popular = tag_manager.get_popular_tags(limit=10)
        
        assert len(popular) == 2
        assert popular[0]['id'] == tag1_id
        assert popular[0]['usage_count'] == 5
    
    def test_get_unused_tags(self, tag_manager):
        """测试获取未使用标签"""
        tag_manager.create("未使用标签1")
        tag_manager.create("未使用标签2")
        
        unused = tag_manager.get_unused_tags()
        
        assert len(unused) == 2
    
    def test_merge_tags(self, tag_manager, test_db, library_id):
        """测试合并标签"""
        source_tag_id = tag_manager.create("源标签")
        target_tag_id = tag_manager.create("目标标签")
        
        # 给源标签添加文档
        for i in range(3):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"doc_{i}.pdf", f"/doc_{i}.pdf", f"hash_{i}")
            )
            tag_manager.add_to_document(source_tag_id, doc_id)
        
        # 合并
        tag_manager.merge_tags(source_tag_id, target_tag_id)
        
        # 验证源标签已删除
        assert tag_manager.get(source_tag_id) is None
        
        # 验证目标标签包含所有文档
        count = tag_manager.get_document_count(target_tag_id)
        assert count == 3