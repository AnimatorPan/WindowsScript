"""
核心复制逻辑模块
"""
import shutil
import hashlib
from pathlib import Path
from typing import List, Tuple, Callable, Optional
from dataclasses import dataclass


@dataclass
class CopyTask:
    """复制任务数据类"""
    source: Path
    target: Path
    relative_path: str
    duplicate_sources: List[Path] = None  # 记录被去重的其他源文件
    is_different: bool = True  # 标记文件是否有差异
    diff_type: str = ""  # 差异类型：'content'内容不同, 'size'大小不同, 'new'新文件
    
    def __post_init__(self):
        if self.duplicate_sources is None:
            self.duplicate_sources = []


@dataclass
class CopyResult:
    """复制结果数据类"""
    success: int
    failed: int
    skipped: int
    errors: List[str]


class FileCopier:
    """文件复制器类"""
    
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        self._cancelled = False
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._ignore_extensions: set = set()
        self._compare_content: bool = True  # 是否比较文件内容，只复制有变化的文件
    
    def set_ignore_extensions(self, extensions: set):
        """设置要忽略的文件扩展名集合
        
        Args:
            extensions: 要忽略的扩展名集合（小写，包含点，如 {'.jpg', '.png'}）
        """
        self._ignore_extensions = {ext.lower() for ext in extensions}
    
    def set_compare_content(self, compare: bool):
        """设置是否比较文件内容
        
        Args:
            compare: True表示只复制有变化的文件，False表示复制所有同名文件
        """
        self._compare_content = compare
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """检查文件是否应该被忽略
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 如果应该忽略返回 True
        """
        if not self._ignore_extensions:
            return False
        return file_path.suffix.lower() in self._ignore_extensions
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """设置进度回调函数
        
        Args:
            callback: 回调函数(current, total, message)
        """
        self._progress_callback = callback
    
    def cancel(self):
        """取消操作"""
        self._cancelled = True
    
    def _get_file_key(self, file_path: Path) -> str:
        """获取文件匹配键（文件名小写，用于不区分大小写匹配）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 小写的文件名
        """
        return file_path.name.lower()
    
    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件的MD5哈希值
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, IOError):
            return ""
    
    def _compare_files(self, source_file: Path, target_file: Path) -> Tuple[bool, str]:
        """比较两个文件是否有差异
        
        Args:
            source_file: 源文件路径
            target_file: 目标文件路径
            
        Returns:
            Tuple[bool, str]: (是否有差异, 差异类型)
        """
        try:
            # 首先比较文件大小
            source_stat = source_file.stat()
            target_stat = target_file.stat()
            
            if source_stat.st_size != target_stat.st_size:
                return True, "size"
            
            # 大小相同，比较修改时间
            if source_stat.st_mtime != target_stat.st_mtime:
                # 时间不同，再比较内容哈希
                source_hash = self._get_file_hash(source_file)
                target_hash = self._get_file_hash(target_file)
                
                if source_hash != target_hash:
                    return True, "content"
                else:
                    # 内容相同但时间不同，视为无差异
                    return False, ""
            else:
                # 时间和大小都相同，视为无差异
                return False, ""
                
        except (OSError, IOError):
            # 无法比较，默认有差异
            return True, "error"
    
    def find_copy_tasks(self) -> List[CopyTask]:
        """查找所有需要复制的文件任务
        
        逻辑：
        1. 遍历源文件夹所有文件，按文件名（不区分大小写）分组
        2. 对于同名文件，选择修改日期最新的
        3. 在目标文件夹及其所有子文件夹中查找同名文件（不区分大小写）
        4. 如果目标中有多个同名文件，每个都会被复制（源的最新版本）
        
        Returns:
            List[CopyTask]: 复制任务列表
        """
        from collections import defaultdict
        
        # 第一步：按文件名（小写）分组收集所有源文件（过滤掉忽略的文件）
        source_files_by_name = defaultdict(list)
        ignored_source_count = 0
        
        for source_file in self.source_dir.rglob('*'):
            if not source_file.is_file():
                continue
            
            # 检查是否应该忽略
            if self._should_ignore_file(source_file):
                ignored_source_count += 1
                continue
            
            # 使用小写文件名作为键（不区分大小写）
            file_key = self._get_file_key(source_file)
            try:
                mtime = source_file.stat().st_mtime
                source_files_by_name[file_key].append((source_file, mtime))
            except (OSError, IOError):
                continue
        
        # 第二步：在目标文件夹中建立小写文件名到所有路径的映射（也过滤忽略的文件）
        target_files_by_name = defaultdict(list)
        ignored_target_count = 0
        
        for target_file in self.target_dir.rglob('*'):
            if not target_file.is_file():
                continue
            
            # 检查是否应该忽略
            if self._should_ignore_file(target_file):
                ignored_target_count += 1
                continue
            
            file_key = self._get_file_key(target_file)
            try:
                relative_path = target_file.relative_to(self.target_dir)
                target_files_by_name[file_key].append((target_file, str(relative_path)))
            except (OSError, IOError, ValueError):
                continue
        
        # 第三步：对每个源文件名，找到最新的源文件，然后复制到所有目标位置
        tasks = []
        
        for file_key, file_list in source_files_by_name.items():
            # 按修改时间排序，最新的排在前面
            file_list.sort(key=lambda x: x[1], reverse=True)
            
            # 获取最新文件
            newest_file, newest_mtime = file_list[0]
            
            # 获取该文件在源文件夹中的相对路径
            try:
                source_relative = str(newest_file.relative_to(self.source_dir))
            except ValueError:
                source_relative = newest_file.name
            
            # 查找目标文件夹中所有同名文件（不区分大小写）
            target_files = target_files_by_name.get(file_key, [])
            
            if target_files:
                # 收集被去重的其他源文件
                duplicates = [f[0] for f in file_list[1:]]
                
                # 为每个目标文件创建一个复制任务
                for target_file, target_relative in target_files:
                    # 检查是否需要比较文件内容
                    if self._compare_content:
                        is_different, diff_type = self._compare_files(newest_file, target_file)
                        if not is_different:
                            # 文件相同，跳过
                            continue
                    else:
                        diff_type = ""
                        is_different = True
                    
                    tasks.append(CopyTask(
                        source=newest_file,
                        target=target_file,
                        relative_path=f"{source_relative} -> {target_relative}",
                        duplicate_sources=duplicates,
                        is_different=is_different,
                        diff_type=diff_type
                    ))
        
        # 按源文件路径排序，便于查看
        tasks.sort(key=lambda x: x.source.name.lower())
        
        return tasks
    
    def execute_copy(self, tasks: List[CopyTask]) -> CopyResult:
        """执行复制操作
        
        Args:
            tasks: 复制任务列表
            
        Returns:
            CopyResult: 复制结果
        """
        result = CopyResult(success=0, failed=0, skipped=0, errors=[])
        total = len(tasks)
        
        for i, task in enumerate(tasks, 1):
            if self._cancelled:
                result.errors.append("操作已取消")
                break
            
            # 报告进度
            if self._progress_callback:
                self._progress_callback(i, total, f"正在复制: {task.relative_path}")
            
            try:
                # 确保目标目录存在
                task.target.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件（覆盖）
                shutil.copy2(task.source, task.target)
                result.success += 1
                
            except Exception as e:
                result.failed += 1
                result.errors.append(f"复制失败 {task.relative_path}: {str(e)}")
        
        return result
    
    def get_preview_info(self, tasks: List[CopyTask]) -> dict:
        """获取预览信息
        
        Args:
            tasks: 复制任务列表
            
        Returns:
            dict: 预览信息字典
        """
        total_size = sum(task.source.stat().st_size for task in tasks)
        
        return {
            'file_count': len(tasks),
            'total_size': self._format_size(total_size),
            'total_size_bytes': total_size,
            'tasks': tasks
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
