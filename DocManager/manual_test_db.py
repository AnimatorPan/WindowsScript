"""
数据库手动测试脚本
用于快速验证数据库功能
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.database import create_database


def test_database_basic():
    """基础数据库测试"""
    print("=" * 60)
    print("数据库基础功能测试")
    print("=" * 60)
    
    # 创建测试数据库
    db_path = "test_manual.db"
    print(f"\n1. 创建数据库: {db_path}")
    db = create_database(db_path)
    print("   ✓ 数据库创建成功")
    
    # 检查表
    print("\n2. 检查数据表:")
    tables = ['libraries', 'documents', 'categories', 'tags']
    for table in tables:
        exists = db.table_exists(table)
        status = "✓" if exists else "✗"
        print(f"   {status} {table}")
    
    # 插入测试数据
    print("\n3. 插入测试数据:")
    library_id = db.insert(
        "INSERT INTO libraries (name, storage_path, db_path) VALUES (?, ?, ?)",
        ("测试库", "/test/storage", "/test/db")
    )
    print(f"   ✓ 插入库记录，ID: {library_id}")
    
    # 查询数据
    print("\n4. 查询数据:")
    library = db.fetch_one("SELECT * FROM libraries WHERE id = ?", (library_id,))
    print(f"   ✓ 库名称: {library['name']}")
    print(f"   ✓ 存储路径: {library['storage_path']}")
    
    # 更新数据
    print("\n5. 更新数据:")
    db.update(
        "UPDATE libraries SET name = ? WHERE id = ?",
        ("新库名", library_id)
    )
    library = db.fetch_one("SELECT * FROM libraries WHERE id = ?", (library_id,))
    print(f"   ✓ 更新后名称: {library['name']}")
    
    # 统计
    print("\n6. 统计信息:")
    count = db.get_table_count('libraries')
    print(f"   ✓ 库总数: {count}")
    
    # 清理
    db.close()
    Path(db_path).unlink()
    print("\n7. 清理测试数据")
    print("   ✓ 已删除测试数据库")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_library_manager():
    """库管理器测试"""
    print("\n" + "=" * 60)
    print("库管理器功能测试")
    print("=" * 60)
    
    from core.database import create_database
    from core.library import LibraryManager
    import tempfile
    import shutil
    
    # 准备
    db_path = "test_library.db"
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        db = create_database(db_path)
        manager = LibraryManager(db)
        
        print("\n1. 创建库:")
        storage_path = temp_dir / "my_library"
        library_id = manager.create(
            name="我的文档库",
            storage_path=str(storage_path),
            description="测试用文档库"
        )
        print(f"   ✓ 库 ID: {library_id}")
        print(f"   ✓ 存储路径: {storage_path}")
        print(f"   ✓ 路径已创建: {storage_path.exists()}")
        
        print("\n2. 获取库信息:")
        library = manager.get(library_id)
        print(f"   ✓ 名称: {library['name']}")
        print(f"   ✓ 描述: {library['description']}")
        print(f"   ✓ 状态: {library['status']}")
        
        print("\n3. 获取统计信息:")
        stats = manager.get_statistics(library_id)
        print(f"   ✓ 文档数: {stats['total_documents']}")
        print(f"   ✓ 分类数: {stats['total_categories']}")
        print(f"   ✓ 标签数: {stats['total_tags']}")
        
        print("\n4. 更新库信息:")
        manager.update(library_id, name="更新后的名称")
        library = manager.get(library_id)
        print(f"   ✓ 新名称: {library['name']}")
        
        print("\n5. 列出所有库:")
        libraries = manager.list_all()
        print(f"   ✓ 库总数: {len(libraries)}")
        
    finally:
        # 清理
        db.close()
        Path(db_path).unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n6. 清理完成")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    print("\nDocManager 第一部分手动测试\n")
    
    # 运行测试
    test_database_basic()
    test_library_manager()
    
    print("\n✓ 所有手动测试完成\n")