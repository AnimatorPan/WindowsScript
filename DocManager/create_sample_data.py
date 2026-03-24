"""
创建示例数据用于测试
"""
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent))

from core.database import create_database
from core.library import LibraryManager
from core.importer import Importer
from core.category import CategoryManager
from core.tag import TagManager


def create_sample_library():
    """创建示例库"""
    print("创建示例库...")
    
    # 创建临时目录
    temp_dir = Path(tempfile.gettempdir()) / "docmanager_sample"
    temp_dir.mkdir(exist_ok=True)
    
    storage_path = temp_dir / "storage"
    storage_path.mkdir(exist_ok=True)
    
    db_path = temp_dir / "sample.db"
    
    # 创建数据库
    db = create_database(str(db_path))
    
    # 创建库
    lib_manager = LibraryManager(db)
    library_id = lib_manager.create("示例库", str(storage_path), "这是一个示例库")
    
    print(f"✓ 库已创建: {db_path}")
    print(f"✓ 库 ID: {library_id}")
    print(f"✓ 存储路径: {storage_path}")
    
    # 创建示例文件
    print("\n创建示例文件...")
    test_files_dir = temp_dir / "test_files"
    test_files_dir.mkdir(exist_ok=True)
    
    sample_files = [
        ("项目计划书.docx", "这是项目计划书的内容"),
        ("年度报告.pdf", "这是年度报告的内容"),
        ("数据分析.xlsx", "这是数据分析的内容"),
        ("会议纪要.txt", "这是会议纪要的内容"),
        ("合同文档.pdf", "这是合同文档的内容"),
    ]
    
    file_paths = []
    for filename, content in sample_files:
        file_path = test_files_dir / filename
        file_path.write_text(content, encoding='utf-8')
        file_paths.append(str(file_path))
    
    print(f"✓ 创建了 {len(file_paths)} 个示例文件")
    
    # 导入文件
    print("\n导入文件...")
    importer = Importer(db, library_id, str(storage_path))
    result = importer.import_batch(file_paths)
    
    print(f"✓ 成功: {result.success}")
    print(f"✓ 重复: {result.duplicate}")
    print(f"✓ 失败: {result.failed}")
    
    # 创建分类
    print("\n创建分类...")
    cat_manager = CategoryManager(db, library_id)
    cat_report = cat_manager.create("报告类")
    cat_contract = cat_manager.create("合同类")
    cat_meeting = cat_manager.create("会议类")
    
    print(f"✓ 创建了 3 个分类")
    
    # 创建标签
    print("\n创建标签...")
    tag_manager = TagManager(db, library_id)
    tag_important = tag_manager.create("重要", color="#FF0000")
    tag_2024 = tag_manager.create("2024", color="#0000FF")
    tag_draft = tag_manager.create("草稿", color="#FFA500")
    
    print(f"✓ 创建了 3 个标签")
    
    db.close()
    
    print("\n" + "="*50)
    print("示例库创建完成!")
    print(f"数据库路径: {db_path}")
    print('\n启动 GUI 后，选择"打开已有库"，然后选择上面的数据库文件')
    print("="*50)


if __name__ == "__main__":
    create_sample_library()