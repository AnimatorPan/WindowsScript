"""
完整流程集成测试
测试从创建库到导入文档、分类管理的完整流程
"""
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent))

from core.database import create_database
from core.library import LibraryManager
from core.importer import Importer
from core.document import DocumentManager
from core.category import CategoryManager


def test_complete_workflow():
    """测试完整工作流程"""
    print("=" * 60)
    print("DocManager 完整流程集成测试")
    print("=" * 60)
    
    # 准备临时环境
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.db"
    storage_path = temp_dir / "storage"
    test_files_dir = temp_dir / "test_files"
    test_files_dir.mkdir()
    
    try:
        # 1. 创建数据库
        print("\n1. 创建数据库...")
        db = create_database(str(db_path))
        print("   ✓ 数据库创建成功")
        
        # 2. 创建库
        print("\n2. 创建文档库...")
        lib_manager = LibraryManager(db)
        library_id = lib_manager.create("我的文档库", str(storage_path))
        print(f"   ✓ 库创建成功，ID: {library_id}")
        
        # 3. 准备测试文件
        print("\n3. 准备测试文件...")
        test_files = []
        for i in range(5):
            file_path = test_files_dir / f"文档_{i}.txt"
            file_path.write_text(f"这是第 {i} 个测试文档")
            test_files.append(str(file_path))
        print(f"   ✓ 创建了 {len(test_files)} 个测试文件")
        
        # 4. 导入文档
        print("\n4. 导入文档...")
        importer = Importer(db, library_id, str(storage_path))
        
        def progress(current, total):
            print(f"   进度: {current}/{total}")
        
        result = importer.import_batch(test_files, progress_callback=progress)
        print(f"   ✓ 导入完成")
        print(f"   - 总数: {result.total}")
        print(f"   - 成功: {result.success}")
        print(f"   - 重复: {result.duplicate}")
        print(f"   - 失败: {result.failed}")
        
        # 5. 查看文档列表
        print("\n5. 查看文档列表...")
        doc_manager = DocumentManager(db, library_id)
        docs = doc_manager.list_all()
        print(f"   ✓ 找到 {len(docs)} 个文档")
        for doc in docs[:3]:
            print(f"   - {doc['filename']}")
        
        # 6. 创建分类
        print("\n6. 创建分类结构...")
        cat_manager = CategoryManager(db, library_id)
        cat_work = cat_manager.create("工作文档")
        cat_personal = cat_manager.create("个人文档")
        cat_archive = cat_manager.create("归档", parent_id=cat_work)
        print(f"   ✓ 创建了 3 个分类")
        
        # 7. 文档归类
        print("\n7. 文档归类...")
        if docs:
            cat_manager.add_document(cat_work, docs[0]['id'])
            cat_manager.add_document(cat_personal, docs[1]['id'])
            print(f"   ✓ 已将文档归类")
        
        # 8. 查询分类文档
        print("\n8. 查询分类文档...")
        work_docs = doc_manager.list_by_category(cat_work)
        print(f"   ✓ '工作文档' 分类下有 {len(work_docs)} 个文档")
        
        # 9. 查询未分类文档
        print("\n9. 查询未分类文档...")
        uncategorized = doc_manager.list_uncategorized()
        print(f"   ✓ 未分类文档: {len(uncategorized)} 个")
        
        # 10. 统计信息
        print("\n10. 统计信息...")
        stats = lib_manager.get_statistics(library_id)
        print(f"   ✓ 文档总数: {stats['total_documents']}")
        print(f"   ✓ 分类总数: {stats['total_categories']}")
        print(f"   ✓ 未分类文档: {stats['uncategorized_documents']}")
        
        print("\n" + "=" * 60)
        print("✓ 完整流程测试通过")
        print("=" * 60)
        
    finally:
        # 清理
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n清理完成")


if __name__ == "__main__":
    test_complete_workflow()