"""
文件工具测试
"""
import pytest
from pathlib import Path
from utils.file_utils import (
    get_file_type, get_mime_type, get_file_size, format_file_size,
    get_relative_path, scan_directory, copy_file, is_supported_file
)


class TestFileUtils:
    """文件工具测试"""
    
    @pytest.fixture
    def test_files(self, temp_dir):
        """创建测试文件"""
        files = {
            'pdf': temp_dir / "test.pdf",
            'docx': temp_dir / "test.docx",
            'txt': temp_dir / "test.txt",
            'jpg': temp_dir / "test.jpg",
        }
        
        for file_path in files.values():
            file_path.write_text("test content")
        
        return files
    
    def test_get_file_type(self, test_files):
        """测试获取文件类型"""
        assert get_file_type(str(test_files['pdf'])) == 'pdf'
        assert get_file_type(str(test_files['docx'])) == 'docx'
        assert get_file_type(str(test_files['txt'])) == 'txt'
        assert get_file_type(str(test_files['jpg'])) == 'jpg'
    
    def test_get_file_type_no_extension(self, temp_dir):
        """测试无扩展名文件"""
        file_path = temp_dir / "noext"
        file_path.write_text("content")
        
        assert get_file_type(str(file_path)) == ''
    
    def test_get_mime_type(self, test_files):
        """测试获取 MIME 类型"""
        assert get_mime_type(str(test_files['pdf'])) == 'application/pdf'
        assert get_mime_type(str(test_files['txt'])) == 'text/plain'
    
    def test_get_file_size(self, temp_dir):
        """测试获取文件大小"""
        file_path = temp_dir / "size_test.txt"
        content = "A" * 1000
        file_path.write_text(content)
        
        size = get_file_size(str(file_path))
        assert size == 1000
    
    def test_format_file_size(self):
        """测试格式化文件大小"""
        assert "1.00 KB" in format_file_size(1024)
        assert "1.00 MB" in format_file_size(1024 * 1024)
        assert "1.00 GB" in format_file_size(1024 * 1024 * 1024)
        assert "B" in format_file_size(100)
    
    def test_get_relative_path(self, temp_dir):
        """测试获取相对路径"""
        base = temp_dir
        file_path = temp_dir / "subdir" / "file.txt"
        
        relative = get_relative_path(str(file_path), str(base))
        assert relative == str(Path("subdir") / "file.txt")
    
    def test_scan_directory_flat(self, temp_dir):
        """测试扫描目录（不包含子目录）"""
        # 创建文件
        (temp_dir / "file1.txt").write_text("1")
        (temp_dir / "file2.pdf").write_text("2")
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("3")
        
        files = scan_directory(str(temp_dir), include_subdirs=False)
        
        assert len(files) == 2
        assert any("file1.txt" in f for f in files)
        assert any("file2.pdf" in f for f in files)
        assert not any("file3.txt" in f for f in files)
    
    def test_scan_directory_recursive(self, temp_dir):
        """测试扫描目录（包含子目录）"""
        # 创建文件结构
        (temp_dir / "file1.txt").write_text("1")
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("2")
        
        files = scan_directory(str(temp_dir), include_subdirs=True)
        
        assert len(files) == 2
        assert any("file1.txt" in f for f in files)
        assert any("file2.txt" in f for f in files)
    
    def test_scan_directory_with_patterns(self, temp_dir):
        """测试文件模式匹配"""
        (temp_dir / "doc1.pdf").write_text("1")
        (temp_dir / "doc2.txt").write_text("2")
        (temp_dir / "doc3.pdf").write_text("3")
        
        files = scan_directory(str(temp_dir), file_patterns=['*.pdf'])
        
        assert len(files) == 2
        assert all(f.endswith('.pdf') for f in files)
    
    def test_copy_file(self, temp_dir):
        """测试复制文件"""
        src = temp_dir / "source.txt"
        dst = temp_dir / "dest.txt"
        
        src.write_text("test content")
        
        success = copy_file(str(src), str(dst))
        
        assert success is True
        assert dst.exists()
        assert dst.read_text() == "test content"
    
    def test_copy_file_overwrite(self, temp_dir):
        """测试覆盖已存在文件"""
        src = temp_dir / "source.txt"
        dst = temp_dir / "dest.txt"
        
        src.write_text("new content")
        dst.write_text("old content")
        
        # 不覆盖
        success = copy_file(str(src), str(dst), overwrite=False)
        assert success is False
        assert dst.read_text() == "old content"
        
        # 覆盖
        success = copy_file(str(src), str(dst), overwrite=True)
        assert success is True
        assert dst.read_text() == "new content"
    
    def test_is_supported_file(self):
        """测试支持的文件类型"""
        assert is_supported_file("doc.pdf") is True
        assert is_supported_file("doc.docx") is True
        assert is_supported_file("doc.txt") is True
        assert is_supported_file("doc.xyz") is False
        assert is_supported_file("doc.exe") is False