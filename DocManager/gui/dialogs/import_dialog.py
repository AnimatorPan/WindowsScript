"""
导入对话框（简化版）
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QFileDialog,
    QProgressBar, QLabel, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal, QThread, pyqtSignal as Signal
from pathlib import Path
import logging

from core.importer import Importer

logger = logging.getLogger(__name__)


class ImportThread(QThread):
    """导入线程"""
    
    progress = Signal(int, int)
    finished = Signal(object)
    
    def __init__(self, importer, file_list):
        super().__init__()
        self.importer = importer
        self.file_list = file_list
    
    def run(self):
        """运行导入"""
        def progress_callback(current, total):
            self.progress.emit(current, total)
        
        result = self.importer.import_batch(
            self.file_list,
            progress_callback=progress_callback
        )
        
        self.finished.emit(result)


class ImportDialog(QDialog):
    """导入对话框"""
    
    import_completed = pyqtSignal(object)
    
    def __init__(self, db, library_id, storage_path, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.storage_path = storage_path
        self.importer = Importer(db, library_id, storage_path)
        
        self.import_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("导入文档")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明
        info_label = QLabel("选择要导入的文件或文件夹")
        layout.addWidget(info_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        file_btn = QPushButton("选择文件...")
        file_btn.clicked.connect(self.select_files)
        button_layout.addWidget(file_btn)
        
        folder_btn = QPushButton("选择文件夹...")
        folder_btn.clicked.connect(self.select_folder)
        button_layout.addWidget(folder_btn)
        
        layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态文本
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def select_files(self):
        """选择文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            str(Path.home()),
            "所有文件 (*.*)"
        )
        
        if files:
            self.start_import(files)
    
    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            str(Path.home())
        )
        
        if folder:
            # 扫描文件夹
            files = self.importer.scan_files(folder)
            if files:
                self.start_import(files)
            else:
                self.status_text.append("文件夹中没有文件")
    
    def start_import(self, file_list):
        """开始导入"""
        self.status_text.clear()
        self.status_text.append(f"准备导入 {len(file_list)} 个文件...")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(file_list))
        self.progress_bar.setValue(0)
        
        # 创建导入线程
        self.import_thread = ImportThread(self.importer, file_list)
        self.import_thread.progress.connect(self.on_progress)
        self.import_thread.finished.connect(self.on_finished)
        self.import_thread.start()
    
    def on_progress(self, current, total):
        """进度更新"""
        self.progress_bar.setValue(current)
        self.status_text.append(f"进度: {current}/{total}")
    
    def on_finished(self, result):
        """导入完成"""
        self.progress_bar.setVisible(False)
        
        self.status_text.append("\n导入完成!")
        self.status_text.append(f"成功: {result.success}")
        self.status_text.append(f"重复: {result.duplicate}")
        self.status_text.append(f"失败: {result.failed}")
        
        if result.errors:
            self.status_text.append("\n错误:")
            for error in result.errors[:5]:
                self.status_text.append(f"  - {error}")
        
        self.import_completed.emit(result)