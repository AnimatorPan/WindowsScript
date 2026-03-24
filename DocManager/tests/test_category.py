"""
分类管理测试
"""
import pytest
from core.category import CategoryManager


class TestCategoryManager:
    """分类管理器测试"""
    
    @pytest.fixture
    def library_id(self, test_db, temp_dir):
        """创建测试库"""
        from core.library import LibraryManager
        
        manager = LibraryManager(test_db)
        storage_path = temp_dir / "library_storage"
        return manager.create("测试库", str(storage_path))
    
    @pytest.fixture
    def cat_manager(self, test_db, library_id):
        """创建分类管理器"""
        return CategoryManager(test_db, library_id)
    
    def test_create_category(self, cat_manager):
        """测试创建分类"""
        cat_id = cat_manager.create("测试分类", description="测试描述")
        
        assert cat_id > 0
        
        cat = cat_manager.get(cat_id)
        assert cat['name'] == "测试分类"
        assert cat['description'] == "测试描述"
    
    def test_create_subcategory(self, cat_manager):
        """测试创建子分类"""
        parent_id = cat_manager.create("父分类")
        child_id = cat_manager.create("子分类", parent_id=parent_id)
        
        child = cat_manager.get(child_id)
        assert child['parent_id'] == parent_id
    
    def test_get_category(self, cat_manager):
        """测试获取分类"""
        cat_id = cat_manager.create("测试分类")
        cat = cat_manager.get(cat_id)
        
        assert cat is not None
        assert cat['id'] == cat_id
    
    def test_list_all(self, cat_manager):
        """测试列出所有分类"""
        for i in range(3):
            cat_manager.create(f"分类{i}")
        
        categories = cat_manager.list_all()
        
        assert len(categories) == 3
    
    def test_get_tree(self, cat_manager):
        """测试获取分类树"""
        # 创建层级结构
        parent_id = cat_manager.create("父分类")
        child1_id = cat_manager.create("子分类1", parent_id=parent_id)
        child2_id = cat_manager.create("子分类2", parent_id=parent_id)
        
        tree = cat_manager.get_tree()
        
        assert len(tree) == 1
        assert tree[0]['name'] == "父分类"
        assert len(tree[0]['children']) == 2
    
    def test_get_children(self, cat_manager):
        """测试获取子分类"""
        parent_id = cat_manager.create("父分类")
        cat_manager.create("子分类1", parent_id=parent_id)
        cat_manager.create("子分类2", parent_id=parent_id)
        
        children = cat_manager.get_children(parent_id)
        
        assert len(children) == 2
    
    def test_get_root_categories(self, cat_manager):
        """测试获取根分类"""
        cat_manager.create("根分类1")
        cat_manager.create("根分类2")
        parent_id = cat_manager.create("父分类")
        cat_manager.create("子分类", parent_id=parent_id)
        
        roots = cat_manager.get_children(None)
        
        assert len(roots) == 3
    
    def test_update_category(self, cat_manager):
        """测试更新分类"""
        cat_id = cat_manager.create("原名称")
        
        cat_manager.update(cat_id, name="新名称", description="新描述")
        
        cat = cat_manager.get(cat_id)
        assert cat['name'] == "新名称"
        assert cat['description'] == "新描述"
    
    def test_delete_category(self, cat_manager):
        """测试删除分类"""
        cat_id = cat_manager.create("待删除分类")
        
        cat_manager.delete(cat_id)
        
        cat = cat_manager.get(cat_id)
        assert cat is None
    
    def test_delete_category_cascade(self, cat_manager):
        """测试级联删除"""
        parent_id = cat_manager.create("父分类")
        child_id = cat_manager.create("子分类", parent_id=parent_id)
        
        cat_manager.delete(parent_id, cascade=True)
        
        assert cat_manager.get(parent_id) is None
        assert cat_manager.get(child_id) is None
    
    def test_delete_category_preserve_children(self, cat_manager):
        """测试删除分类但保留子分类"""
        parent_id = cat_manager.create("父分类")
        child_id = cat_manager.create("子分类", parent_id=parent_id)
        
        cat_manager.delete(parent_id, cascade=False)
        
        child = cat_manager.get(child_id)
        assert child is not None
        assert child['parent_id'] is None
    
    def test_add_document_to_category(self, cat_manager, test_db, library_id):
        """测试添加文档到分类"""
        cat_id = cat_manager.create("测试分类")
        
        # 创建文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        cat_manager.add_document(cat_id, doc_id)
        
        # 验证关联
        result = test_db.fetch_one(
            "SELECT * FROM document_categories WHERE document_id = ? AND category_id = ?",
            (doc_id, cat_id)
        )
        
        assert result is not None
    
    def test_remove_document_from_category(self, cat_manager, test_db, library_id):
        """测试从分类移除文档"""
        cat_id = cat_manager.create("测试分类")
        
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        cat_manager.add_document(cat_id, doc_id)
        cat_manager.remove_document(cat_id, doc_id)
        
        # 验证已移除
        result = test_db.fetch_one(
            "SELECT * FROM document_categories WHERE document_id = ? AND category_id = ?",
            (doc_id, cat_id)
        )
        
        assert result is None
    
    def test_get_document_count(self, cat_manager, test_db, library_id):
        """测试获取分类文档数量"""
        cat_id = cat_manager.create("测试分类")
        
        # 添加多个文档
        for i in range(3):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"doc_{i}.pdf", f"/doc_{i}.pdf", f"hash_{i}")
            )
            cat_manager.add_document(cat_id, doc_id)
        
        count = cat_manager.get_document_count(cat_id)
        
        assert count == 3
    
    def test_get_document_count_with_children(self, cat_manager, test_db, library_id):
        """测试获取分类及子分类的文档总数"""
        parent_id = cat_manager.create("父分类")
        child_id = cat_manager.create("子分类", parent_id=parent_id)
        
        # 父分类添加 2 个文档
        for i in range(2):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"parent_{i}.pdf", f"/parent_{i}.pdf", f"hash_p_{i}")
            )
            cat_manager.add_document(parent_id, doc_id)
        
        # 子分类添加 3 个文档
        for i in range(3):
            doc_id = test_db.insert(
                """INSERT INTO documents 
                   (library_id, filename, filepath, file_hash) 
                   VALUES (?, ?, ?, ?)""",
                (library_id, f"child_{i}.pdf", f"/child_{i}.pdf", f"hash_c_{i}")
            )
            cat_manager.add_document(child_id, doc_id)
        
        # 仅父分类
        count_parent = cat_manager.get_document_count(parent_id, include_children=False)
        assert count_parent == 2
        
        # 包含子分类
        count_total = cat_manager.get_document_count(parent_id, include_children=True)
        assert count_total == 5