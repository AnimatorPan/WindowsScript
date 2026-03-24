"""
导入文档对话框 - Visual Studio 2019 Dark 主题
"""

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

# 修复导入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.database import Database
from core.document_importer import DocumentImporter, ImportStatus
from gui.styles.app_styles import (
    COLORS, PRIMARY_BUTTON_STYLE, DEFAULT_BUTTON_STYLE, 
    TABLE_WIDGET_STYLE
)


class ImportWorker(QThread):
    """导入工作线程"""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    import_finished = pyqtSignal(list)  # results
    
    def __init__(self, file_paths, library_path, db_path):
        super().__init__()
        self.file_paths = file_paths
        self.library_path = library_path
        self.db_path = db_path
        self.results = []
    
    def run(self):
        """执行导入"""
        importer = DocumentImporter(self.library_path)
        db = Database(self.db_path).connect()
        
        total = len(self.file_paths)
        
        def progress_callback(current, total, result):
            self.progress_updated.emit(current, total, result.message)
        
        self.results = importer.import_files(self.file_paths, db, progress_callback)
        
        db.close()
        self.import_finished.emit(self.results)


class ImportDialog(QDialog):
    """导入文档对话框"""
    
    import_completed = pyqtSignal(int)  # 成功导入的数量
    
    def __init__(self, library_path, parent=None):
        super().__init__(parent)
        self.library_path = library_path
        self.db_path = os.path.join(library_path, 'library.db')
        self.selected_files = []
        self.import_worker = None
        
        self.setWindowTitle('导入文档')
        self.setMinimumSize(700, 500)
        self.setup_ui()
        self.apply_styles()
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet(f'''
            QDialog {{
                background-color: {COLORS['bg_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
        ''')
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title = QLabel('📥 导入文档')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f'color: {COLORS["text_highlight"]};')
        layout.addWidget(title)
        
        # 说明
        desc = QLabel('选择要导入的文档文件，支持多选')
        desc.setStyleSheet(f'color: {COLORS["text_secondary"]}; font-size: 13px;')
        layout.addWidget(desc)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        self.select_btn = QPushButton('+ 选择文件')
        self.select_btn.setMinimumHeight(36)
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.select_btn.clicked.connect(self.select_files)
        toolbar.addWidget(self.select_btn)
        
        self.clear_btn = QPushButton('清空列表')
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setEnabled(False)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        self.file_count_label = QLabel('已选择 0 个文件')
        self.file_count_label.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        toolbar.addWidget(self.file_count_label)
        
        layout.addLayout(toolbar)
        
        # 文件列表
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(['文件名', '类型', '大小'])
        self.file_table.horizontalHeader().setStretchLastSection(False)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.file_table.setColumnWidth(1, 100)
        self.file_table.setColumnWidth(2, 100)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.file_table.setStyleSheet(TABLE_WIDGET_STYLE)
        self.file_table.setAlternatingRowColors(True)
        layout.addWidget(self.file_table)
        
        # 进度条
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet(f'''
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        ''')
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(16, 16, 16, 16)
        progress_layout.setSpacing(8)
        
        self.progress_label = QLabel('准备导入...')
        self.progress_label.setStyleSheet(f'color: {COLORS["text_primary"]};')
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setStyleSheet(f'''
            QProgressBar {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
                text-align: center;
                color: {COLORS['text_primary']};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 2px;
            }}
        ''')
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_frame.hide()
        layout.addWidget(self.progress_frame)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet(DEFAULT_BUTTON_STYLE)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.import_btn = QPushButton('开始导入')
        self.import_btn.setMinimumWidth(100)
        self.import_btn.setMinimumHeight(36)
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.import_btn.clicked.connect(self.start_import)
        self.import_btn.setEnabled(False)
        btn_layout.addWidget(self.import_btn)
        
        layout.addLayout(btn_layout)
    
    def select_files(self):
        """选择文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            '选择要导入的文档',
            str(Path.home()),
            '所有支持的文件 (*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt *.md *.png *.jpg *.jpeg *.gif *.bmp *.zip *.rar *.7z);;'
            'PDF文件 (*.pdf);;'
            'Word文档 (*.doc *.docx);;'
            'Excel表格 (*.xls *.xlsx);;'
            'PowerPoint (*.ppt *.pptx);;'
            '文本文件 (*.txt *.md);;'
            '图片 (*.png *.jpg *.jpeg *.gif *.bmp);;'
            '压缩文件 (*.zip *.rar *.7z);;'
            '所有文件 (*.*)'
        )
        
        if files:
            self.selected_files = files
            self.update_file_list()
            self.update_ui_state()
    
    def update_file_list(self):
        """更新文件列表显示"""
        self.file_table.setRowCount(len(self.selected_files))
        
        importer = DocumentImporter(self.library_path)
        
        for i, file_path in enumerate(self.selected_files):
            # 文件名
            name_item = QTableWidgetItem(Path(file_path).name)
            name_item.setToolTip(file_path)
            self.file_table.setItem(i, 0, name_item)
            
            # 类型
            file_type = importer.get_file_type(file_path)
            type_item = QTableWidgetItem(file_type)
            self.file_table.setItem(i, 1, type_item)
            
            # 大小
            size = os.path.getsize(file_path)
            size_str = self.format_size(size)
            size_item = QTableWidgetItem(size_str)
            size_item.setData(Qt.ItemDataRole.UserRole, size)
            self.file_table.setItem(i, 2, size_item)
        
        self.file_count_label.setText(f'已选择 {len(self.selected_files)} 个文件')
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} KB'
        elif size_bytes < 1024 * 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.1f} MB'
        else:
            return f'{size_bytes / (1024 * 1024 * 1024):.1f} GB'
    
    def clear_files(self):
        """清空文件列表"""
        self.selected_files = []
        self.file_table.setRowCount(0)
        self.update_ui_state()
    
    def update_ui_state(self):
        """更新UI状态"""
        has_files = len(self.selected_files) > 0
        self.clear_btn.setEnabled(has_files)
        self.import_btn.setEnabled(has_files)
        self.file_count_label.setText(f'已选择 {len(self.selected_files)} 个文件')
    
    def start_import(self):
        """开始导入"""
        if not self.selected_files:
            QMessageBox.warning(self, '提示', '请先选择要导入的文件')
            return
        
        # 禁用控件
        self.select_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # 显示进度
        self.progress_frame.show()
        self.progress_bar.setMaximum(len(self.selected_files))
        self.progress_bar.setValue(0)
        
        # 启动导入线程
        self.import_worker = ImportWorker(
            self.selected_files,
            self.library_path,
            self.db_path
        )
        self.import_worker.progress_updated.connect(self.on_progress_updated)
        self.import_worker.import_finished.connect(self.on_import_finished)
        self.import_worker.start()
    
    def on_progress_updated(self, current, total, message):
        """进度更新"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f'正在导入 ({current}/{total}): {message}')
    
    def on_import_finished(self, results):
        """导入完成"""
        from core.document_importer import DocumentImporter
        
        importer = DocumentImporter(self.library_path)
        summary = importer.get_import_summary(results)
        
        # 显示结果
        msg = f'''
导入完成！

总计: {summary['total']} 个文件
成功: {summary['success']} 个
重复: {summary['duplicate']} 个
跳过: {summary['skipped']} 个
失败: {summary['error']} 个
        '''.strip()
        
        QMessageBox.information(self, '导入完成', msg)
        
        # 发送信号
        self.import_completed.emit(summary['success'])
        
        # 关闭对话框
        self.accept()
