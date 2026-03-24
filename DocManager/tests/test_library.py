"""
库管理模块测试
"""
import pytest
from pathlib import Path
from core.library import LibraryManager


class TestLibraryManager:
    """库管理器测试"""
    
    @pytest.fixture
    def library_manager(self, test_db):
        """创建库管理器实例"""
        return LibraryManager(test_db)
    
    def test_create_library(self, library_manager, temp_dir):
        """测试创建库"""
        storage_path = temp_dir / "test_library"
        
        library_id = library_manager.create(
            name="测试库",
            storage_path=str(storage_path),
            description="这是一个测试库"
        )
        
        assert library_id > 0
        
        # 验证存储路径已创建
        assert storage_path.exists()
        
        # 验证数据库记录
        library = library_manager.get(library_id)
        assert library is not None
        assert library['name'] == "测试库"
        assert library['description'] == "这是一个测试库"
    
    def test_get_library(self, library_manager, temp_dir):
        """测试获取库信息"""
        storage_path = temp_dir / "test_library"
        library_id = library_manager.create("测试库", str(storage_path))
        
        library = library_manager.get(library_id)
        
        assert library is not None
        assert library['id'] == library_id
        assert library['name'] == "测试库"
    
    def test_get_by_name(self, library_manager, temp_dir):
        """测试根据名称获取库"""
        storage_path = temp_dir / "test_library"
        library_manager.create("测试库", str(storage_path))
        
        library = library_manager.get_by_name("测试库")
        
        assert library is not None
        assert library['name'] == "测试库"
    
    def test_list_all(self, library_manager, temp_dir):
        """测试获取所有库"""
        # 创建多个库
        for i in range(3):
            storage_path = temp_dir / f"library_{i}"
            library_manager.create(f"库{i}", str(storage_path))
        
        libraries = library_manager.list_all()
        
        assert len(libraries) == 3
        assert all('name' in lib for lib in libraries)
    
    def test_update_library(self, library_manager, temp_dir):
        """测试更新库信息"""
        storage_path = temp_dir / "test_library"
        library_id = library_manager.create("原名称", str(storage_path))
        
        # 更新
        library_manager.update(
            library_id,
            name="新名称",
            description="新描述"
        )
        
        # 验证
        library = library_manager.get(library_id)
        assert library['name'] == "新名称"
        assert library['description'] == "新描述"
    
    def test_delete_library(self, library_manager, temp_dir):
        """测试删除库"""
        storage_path = temp_dir / "test_library"
        library_id = library_manager.create("待删除库", str(storage_path))
        
        # 删除
        library_manager.delete(library_id)
        
        # 验证
        library = library_manager.get(library_id)
        assert library is None
    
    def test_get_statistics_empty(self, library_manager, temp_dir):
        """测试获取空库统计"""
        storage_path = temp_dir / "test_library"
        library_id = library_manager.create("测试库", str(storage_path))
        
        stats = library_manager.get_statistics(library_id)
        
        assert stats['total_documents'] == 0
        assert stats['total_size'] == 0
        assert stats['total_categories'] == 0
        assert stats['total_tags'] == 0
        assert stats['uncategorized_documents'] == 0
        assert stats['duplicate_documents'] == 0
    
    def test_get_statistics_with_data(self, library_manager, test_db, temp_dir):
        """测试获取有数据的库统计"""
        storage_path = temp_dir / "test_library"
        library_id = library_manager.create("测试库", str(storage_path))
        
        # 插入测试数据
        # 文档
        for i in range(5):
            test_db.insert(
                "INSERT INTO documents (library_id, filename, filepath, file_hash, file_size) VALUES (?, ?, ?, ?, ?)",
                (library_id, f"doc{i}.pdf", f"/doc{i}.pdf", f"hash{i}", 1024)
            )
        
        # 分类
        for i in range(3):
            test_db.insert(
                "INSERT INTO categories (library_id, name) VALUES (?, ?)",
                (library_id, f"分类{i}")
            )
        
        # 标签
        for i in range(2):
            test_db.insert(
                "INSERT INTO tags (library_id, name) VALUES (?, ?)",
                (library_id, f"标签{i}")
            )
        
        stats = library_manager.get_statistics(library_id)
        
        assert stats['total_documents'] == 5
        assert stats['total_size'] == 5120  # 5 * 1024
        assert stats['total_categories'] == 3
        assert stats['total_tags'] == 2