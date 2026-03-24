"""
数据库模块测试
"""
import pytest
from pathlib import Path
from core.database import Database, create_database


class TestDatabase:
    """数据库类测试"""
    
    def test_create_database(self, test_db_path):
        """测试创建数据库"""
        db = create_database(test_db_path)
        
        # 验证数据库文件已创建
        assert Path(test_db_path).exists()
        
        # 验证连接正常
        assert db.conn is not None
        
        db.close()
    
    def test_init_database(self, test_db):
        """测试初始化数据库表"""
        # 检查核心表是否存在
        assert test_db.table_exists('libraries')
        assert test_db.table_exists('documents')
        assert test_db.table_exists('categories')
        assert test_db.table_exists('tags')
        assert test_db.table_exists('document_categories')
        assert test_db.table_exists('document_tags')
        assert test_db.table_exists('smart_folders')
        assert test_db.table_exists('import_tasks')
    
    def test_insert_and_fetch(self, test_db):
        """测试插入和查询"""
        # 插入测试数据
        sql = """
            INSERT INTO libraries (name, storage_path, db_path)
            VALUES (?, ?, ?)
        """
        library_id = test_db.insert(sql, ("测试库", "/test/path", "/test/db"))
        
        assert library_id > 0
        
        # 查询数据
        result = test_db.fetch_one("SELECT * FROM libraries WHERE id = ?", (library_id,))
        
        assert result is not None
        assert result['name'] == "测试库"
        assert result['storage_path'] == "/test/path"
    
    def test_fetch_all(self, test_db):
        """测试查询多条记录"""
        # 插入多条数据
        for i in range(3):
            sql = "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)"
            test_db.insert(sql, (f"库{i}", f"/path{i}", f"/db{i}"))
        
        # 查询所有
        results = test_db.fetch_all("SELECT * FROM libraries")
        
        assert len(results) == 3
        assert all('name' in r for r in results)
    
    def test_update(self, test_db):
        """测试更新"""
        # 插入
        library_id = test_db.insert(
            "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
            ("原名称", "/path", "/db")
        )
        
        # 更新
        rows = test_db.update(
            "UPDATE libraries SET name = ? WHERE id = ?",
            ("新名称", library_id)
        )
        
        assert rows == 1
        
        # 验证
        result = test_db.fetch_one("SELECT * FROM libraries WHERE id = ?", (library_id,))
        assert result['name'] == "新名称"
    
    def test_delete(self, test_db):
        """测试删除"""
        # 插入
        library_id = test_db.insert(
            "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
            ("待删除", "/path", "/db")
        )
        
        # 删除
        rows = test_db.delete("DELETE FROM libraries WHERE id = ?", (library_id,))
        
        assert rows == 1
        
        # 验证已删除
        result = test_db.fetch_one("SELECT * FROM libraries WHERE id = ?", (library_id,))
        assert result is None
    
    def test_transaction_commit(self, test_db):
        """测试事务提交"""
        with test_db.transaction():
            test_db.insert(
                "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
                ("事务测试", "/path", "/db")
            )
        
        # 验证已提交
        count = test_db.get_table_count('libraries')
        assert count == 1
    
    def test_transaction_rollback(self, test_db):
        """测试事务回滚"""
        try:
            with test_db.transaction():
                test_db.insert(
                    "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
                    ("回滚测试", "/path", "/db"),
                    autocommit=False  # 事务中不自动提交
                )
                # 故意触发异常
                raise Exception("测试回滚")
        except Exception:
            pass
        
        # 验证已回滚
        count = test_db.get_table_count('libraries')
        assert count == 0
    
    def test_foreign_key_constraint(self, test_db):
        """测试外键约束"""
        # 插入库
        library_id = test_db.insert(
            "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
            ("测试库", "/path", "/db")
        )
        
        # 插入文档
        doc_id = test_db.insert(
            """INSERT INTO documents 
               (library_id, filename, filepath, file_hash) 
               VALUES (?, ?, ?, ?)""",
            (library_id, "test.pdf", "/test.pdf", "abc123")
        )
        
        assert doc_id > 0
        
        # 删除库（应该级联删除文档）
        test_db.delete("DELETE FROM libraries WHERE id = ?", (library_id,))
        
        # 验证文档已被级联删除
        result = test_db.fetch_one("SELECT * FROM documents WHERE id = ?", (doc_id,))
        assert result is None


class TestTableRelations:
    """测试表关系"""
    
    def test_category_hierarchy(self, test_db):
        """测试分类层级关系"""
        # 插入库
        library_id = test_db.insert(
            "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
            ("测试库", "/path", "/db")
        )
        
        # 插入父分类
        parent_id = test_db.insert(
            "INSERT INTO categories (library_id, name) VALUES (?, ?)",
            (library_id, "父分类")
        )
        
        # 插入子分类
        child_id = test_db.insert(
            "INSERT INTO categories (library_id, name, parent_id) VALUES (?, ?, ?)",
            (library_id, "子分类", parent_id)
        )
        
        # 验证关系
        child = test_db.fetch_one("SELECT * FROM categories WHERE id = ?", (child_id,))
        assert child['parent_id'] == parent_id
    
    def test_document_category_relation(self, test_db):
        """测试文档-分类关联"""
        # 准备数据
        library_id = test_db.insert(
            "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
            ("测试库", "/path", "/db")
        )
        
        doc_id = test_db.insert(
            "INSERT INTO documents (library_id, filename, filepath, file_hash) VALUES (?, ?, ?, ?)",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        cat_id = test_db.insert(
            "INSERT INTO categories (library_id, name) VALUES (?, ?)",
            (library_id, "测试分类")
        )
        
        # 建立关联
        test_db.insert(
            "INSERT INTO document_categories (document_id, category_id) VALUES (?, ?)",
            (doc_id, cat_id)
        )
        
        # 验证关联
        result = test_db.fetch_one(
            "SELECT * FROM document_categories WHERE document_id = ? AND category_id = ?",
            (doc_id, cat_id)
        )
        assert result is not None
    
    def test_document_tag_relation(self, test_db):
        """测试文档-标签关联"""
        # 准备数据
        library_id = test_db.insert(
            "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
            ("测试库", "/path", "/db")
        )
        
        doc_id = test_db.insert(
            "INSERT INTO documents (library_id, filename, filepath, file_hash) VALUES (?, ?, ?, ?)",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        tag_id = test_db.insert(
            "INSERT INTO tags (library_id, name) VALUES (?, ?)",
            (library_id, "测试标签")
        )
        
        # 建立关联
        test_db.insert(
            "INSERT INTO document_tags (document_id, tag_id) VALUES (?, ?)",
            (doc_id, tag_id)
        )
        
        # 验证关联
        result = test_db.fetch_one(
            "SELECT * FROM document_tags WHERE document_id = ? AND tag_id = ?",
            (doc_id, tag_id)
        )
        assert result is not None
    
    def test_unique_constraint(self, test_db):
        """测试唯一约束"""
        # 准备数据
        library_id = test_db.insert(
            "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
            ("测试库", "/path", "/db")
        )
        
        doc_id = test_db.insert(
            "INSERT INTO documents (library_id, filename, filepath, file_hash) VALUES (?, ?, ?, ?)",
            (library_id, "test.pdf", "/test.pdf", "hash123")
        )
        
        cat_id = test_db.insert(
            "INSERT INTO categories (library_id, name) VALUES (?, ?)",
            (library_id, "测试分类")
        )
        
        # 第一次插入
        test_db.insert(
            "INSERT INTO document_categories (document_id, category_id) VALUES (?, ?)",
            (doc_id, cat_id)
        )
        
        # 第二次插入相同关联（应该失败）
        with pytest.raises(Exception):
            test_db.insert(
                "INSERT INTO document_categories (document_id, category_id) VALUES (?, ?)",
                (doc_id, cat_id)
            )