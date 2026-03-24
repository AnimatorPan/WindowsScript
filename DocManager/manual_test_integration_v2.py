"""
完整流程集成测试 v2
包含标签、搜索、智能文件夹、去重功能
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
from core.tag import TagManager
from core.search import SearchEngine
from core.smart_folder import SmartFolderManager
from core.duplicate_detector import DuplicateDetector


def test_complete_workflow_v2():
    """测试完整工作流程 v2"""
    print("=" * 60)
    print("DocManager 完整流程集成测试 v2")
    print("=" * 60)
    
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.db"
    storage_path = temp_dir / "storage"
    test_files_dir = temp_dir / "test_files"
    test_files_dir.mkdir()
    
    try:
        # 1. 初始化
        print("\n【1】初始化数据库和库...")
        db = create_database(str(db_path))
        lib_manager = LibraryManager(db)
        library_id = lib_manager.create("我的文档库", str(storage_path))
        print(f"   ✓ 库 ID: {library_id}")
        
        # 2. 准备测试文件
        print("\n【2】准备测试文件...")
        test_files = []
        file_types = [
            ("合同文档.pdf", "pdf"),
            ("项目方案.docx", "docx"),
            ("数据报表.xlsx", "xlsx"),
            ("会议纪要.txt", "txt"),
            ("设计稿.psd", "psd"),
        ]
        
        for filename, _ in file_types:
            file_path = test_files_dir / filename
            file_path.write_text(f"这是{filename}的内容")
            test_files.append(str(file_path))
        
        # 创建一个重复文件
        dup_file = test_files_dir / "合同文档_副本.pdf"
        dup_file.write_text("这是合同文档.pdf的内容")  # 内容相同
        test_files.append(str(dup_file))
        
        print(f"   ✓ 创建了 {len(test_files)} 个测试文件")
        
        # 3. 导入文档
        print("\n【3】导入文档...")
        importer = Importer(db, library_id, str(storage_path))
        result = importer.import_batch(test_files)
        print(f"   ✓ 成功: {result.success}")
        print(f"   ✓ 重复: {result.duplicate}")
        print(f"   ✓ 失败: {result.failed}")
        
        # 4. 创建标签
        print("\n【4】创建标签体系...")
        tag_manager = TagManager(db, library_id)
        tag_important = tag_manager.create("重要", color="#FF0000")
        tag_urgent = tag_manager.create("紧急", color="#FFA500")
        tag_2024 = tag_manager.create("2024")
        print(f"   ✓ 创建了 3 个标签")
        
        # 5. 创建分类
        print("\n【5】创建分类结构...")
        cat_manager = CategoryManager(db, library_id)
        cat_contract = cat_manager.create("合同类")
        cat_report = cat_manager.create("报告类")
        print(f"   ✓ 创建了 2 个分类")
        
        # 6. 文档打标签和归类
        print("\n【6】文档打标签和归类...")
        doc_manager = DocumentManager(db, library_id)
        docs = doc_manager.list_all(limit=10)
        
        if docs:
            # 给第一个文档打标签
            tag_manager.add_to_document(tag_important, docs[0]['id'])
            tag_manager.add_to_document(tag_2024, docs[0]['id'])
            
            # 归类
            cat_manager.add_document(cat_contract, docs[0]['id'])
            
            print(f"   ✓ 已对文档进行标签和分类")
        
        # 7. 搜索测试
        print("\n【7】搜索测试...")
        search = SearchEngine(db, library_id)
        
        # 按文件名搜索
        results = search.search_by_filename("合同")
        print(f"   ✓ 搜索'合同': {len(results)} 个结果")
        
        # 按类型筛选
        pdf_docs = search.filter_by_type(['pdf'])
        print(f"   ✓ PDF文档: {len(pdf_docs)} 个")
        
        # 按标签筛选
        important_docs = search.filter_by_tags([tag_important])
        print(f"   ✓ '重要'标签: {len(important_docs)} 个文档")
        
        # 8. 智能文件夹
        print("\n【8】创建智能文件夹...")
        sf_manager = SmartFolderManager(db, library_id)
        
        # 创建预设智能文件夹
        sf_recent = sf_manager.create_preset_folder('recent')
        sf_uncat = sf_manager.create_preset_folder('uncategorized')
        
        # 自定义智能文件夹
        sf_pdf = sf_manager.create("所有PDF", {
            'operator': 'AND',
            'conditions': [
                {'type': 'file_type', 'operator': 'equals', 'value': 'pdf'}
            ]
        })
        
        print(f"   ✓ 创建了 3 个智能文件夹")
        
        # 查看匹配结果
        pdf_matches = sf_manager.get_matched_documents(sf_pdf)
        print(f"   ✓ 'PDF文档'匹配: {len(pdf_matches)} 个")
        
        # 9. 去重检测
        print("\n【9】去重检测...")
        detector = DuplicateDetector(db, library_id)
        
        duplicates = detector.find_exact_duplicates()
        print(f"   ✓ 找到 {len(duplicates)} 组重复文档")
        
        if duplicates:
            for group in duplicates:
                print(f"      - 重复组: {len(group)} 个文档")
                # 标记重复，保留第一个
                doc_ids = [doc['id'] for doc in group]
                detector.mark_as_duplicate(doc_ids, keep_id=doc_ids[0])
        
        stats = detector.get_duplicate_statistics()
        print(f"   ✓ 重复文档统计:")
        print(f"      - 总文档: {stats['total_documents']}")
        print(f"      - 重复数: {stats['duplicate_count']}")
        print(f"      - 浪费空间: {stats['wasted_space']} 字节")
        
        # 10. 最终统计
        print("\n【10】最终统计...")
        final_stats = lib_manager.get_statistics(library_id)
        print(f"   ✓ 文档总数: {final_stats['total_documents']}")
        print(f"   ✓ 分类总数: {final_stats['total_categories']}")
        print(f"   ✓ 标签总数: {final_stats['total_tags']}")
        print(f"   ✓ 未分类: {final_stats['uncategorized_documents']}")
        
        # 11. 标签统计
        print("\n【11】标签使用统计...")
        popular_tags = tag_manager.get_popular_tags(limit=5)
        for tag in popular_tags:
            print(f"   - {tag['name']}: {tag['usage_count']} 次使用")
        
        print("\n" + "=" * 60)
        print("✓ 完整流程测试通过")
        print("=" * 60)
        
    finally:
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n清理完成")


if __name__ == "__main__":
    test_complete_workflow_v2()