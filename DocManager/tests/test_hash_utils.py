"""
哈希工具测试
"""
import pytest
from pathlib import Path
from utils.hash_utils import calculate_file_hash, calculate_quick_hash


class TestHashUtils:
    """哈希工具测试"""
    
    @pytest.fixture
    def test_file(self, temp_dir):
        """创建测试文件"""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Hello DocManager!", encoding='utf-8')
        return str(file_path)
    
    @pytest.fixture
    def large_file(self, temp_dir):
        """创建大文件"""
        file_path = temp_dir / "large.bin"
        # 创建 10MB 文件
        with open(file_path, 'wb') as f:
            f.write(b'0' * (10 * 1024 * 1024))
        return str(file_path)
    
    def test_calculate_file_hash_sha256(self, test_file):
        """测试 SHA256 哈希计算"""
        hash_value = calculate_file_hash(test_file, algorithm='sha256')
        
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 是 64 位十六进制
        assert isinstance(hash_value, str)
    
    def test_calculate_file_hash_md5(self, test_file):
        """测试 MD5 哈希计算"""
        hash_value = calculate_file_hash(test_file, algorithm='md5')
        
        assert hash_value is not None
        assert len(hash_value) == 32  # MD5 是 32 位十六进制
    
    def test_calculate_file_hash_consistency(self, test_file):
        """测试哈希一致性"""
        hash1 = calculate_file_hash(test_file)
        hash2 = calculate_file_hash(test_file)
        
        assert hash1 == hash2
    
    def test_calculate_file_hash_different_files(self, temp_dir):
        """测试不同文件哈希不同"""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        hash1 = calculate_file_hash(str(file1))
        hash2 = calculate_file_hash(str(file2))
        
        assert hash1 != hash2
    
    def test_calculate_file_hash_nonexistent(self):
        """测试不存在的文件"""
        hash_value = calculate_file_hash("/nonexistent/file.txt")
        
        assert hash_value is None
    
    def test_calculate_quick_hash(self, large_file):
        """测试快速哈希"""
        hash_value = calculate_quick_hash(large_file)
        
        assert hash_value is not None
        assert len(hash_value) == 64
    
    def test_quick_hash_vs_full_hash_speed(self, large_file):
        """测试快速哈希与完整哈希的速度差异"""
        import time
        
        # 快速哈希
        start = time.time()
        quick_hash = calculate_quick_hash(large_file)
        quick_time = time.time() - start
        
        # 完整哈希
        start = time.time()
        full_hash = calculate_file_hash(large_file)
        full_time = time.time() - start
        
        assert quick_hash is not None
        assert full_hash is not None
        assert quick_time < full_time  # 快速哈希应该更快
        
        print(f"\n快速哈希耗时: {quick_time:.4f}s")
        print(f"完整哈希耗时: {full_time:.4f}s")