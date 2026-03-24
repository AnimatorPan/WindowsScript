"""
pytest 配置文件
"""
import pytest
import sys
from pathlib import Path
import tempfile
import shutil

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """创建临时测试目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # 测试结束后清理
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def test_db_path(temp_dir):
    """创建测试数据库路径"""
    db_path = temp_dir / "test.db"
    yield str(db_path)


@pytest.fixture
def test_db(test_db_path):
    """创建测试数据库实例"""
    from core.database import Database
    
    db = Database(test_db_path)
    db.connect()
    db.init_database()
    
    yield db
    
    db.close()