"""
文档列表组件（完整版）
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DocumentListWidget(QWidget):
    """文档列表组件"""
    
    document_selected = pyqtSignal(int)
    selection_changed = pyqtSignal(int)
    documents_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_window = parent
        self.documents = []
        self.current_view = 'list'
        
        self.init_ui()
    
    def get_main_window(self):
        """获取主窗口"""
        # 如果 parent 是 DocumentArea，需要找到 MainWindow
        parent = self.main_window
        while parent:
            if hasattr(parent, 'db') and hasattr(parent, 'library_id'):
                return parent
            parent = parent.parent()
        return None
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 表格视图
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "文件名", "类型", "大小", "修改时间", "导入时间", "状态"
        ])
        
        # 设置表格属性
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)  # 多选
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        # 连接信号
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
    
    def load_documents(self, documents):
        """加载文档列表"""
        self.documents = documents
        self.table.setRowCount(len(documents))
        
        for row, doc in enumerate(documents):
            # 文件名
            self.table.setItem(row, 0, QTableWidgetItem(doc['filename']))
            
            # 类型
            file_type = doc.get('file_type', '') or '未知'
            self.table.setItem(row, 1, QTableWidgetItem(file_type.upper()))
            
            # 大小
            size = self.format_size(doc.get('file_size', 0))
            self.table.setItem(row, 2, QTableWidgetItem(size))
            
            # 修改时间
            modified_at = self.format_datetime(doc.get('modified_at'))
            self.table.setItem(row, 3, QTableWidgetItem(modified_at))
            
            # 导入时间
            imported_at = self.format_datetime(doc.get('imported_at'))
            self.table.setItem(row, 4, QTableWidgetItem(imported_at))
            
            # 状态
            status = "重复" if doc.get('is_duplicate') else "正常"
            self.table.setItem(row, 5, QTableWidgetItem(status))
            
            # 存储文档ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, doc['id'])
        
        logger.info(f"加载了 {len(documents)} 个文档")
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes is None:
            return "-"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def format_datetime(self, dt_str):
        """格式化日期时间"""
        if not dt_str:
            return "-"
        
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return dt_str
    
    def on_selection_changed(self):
        """选择变化"""
        selected_rows = self.table.selectionModel().selectedRows()
        count = len(selected_rows)
        
        self.selection_changed.emit(count)
        
        if count == 1:
            row = selected_rows[0].row()
            doc_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.document_selected.emit(doc_id)
    
    def on_cell_double_clicked(self, row, column):
        """单元格双击"""
        doc_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.open_document(doc_id)
    
    def open_document(self, doc_id):
        """打开文档"""
        # 获取主窗口
        main_window = self.get_main_window()
        if not main_window or not main_window.db or not main_window.library_id:
            return
        
        from core.document import DocumentManager
        import os
        import subprocess
        import platform
        
        try:
            doc_manager = DocumentManager(main_window.db, main_window.library_id)
            doc = doc_manager.get(doc_id)
            
            if not doc:
                return
            
            # 构建完整路径
            from pathlib import Path
            storage_path = Path(main_window.current_library['storage_path'])
            file_path = storage_path / doc['filepath']
            
            if not file_path.exists():
                QMessageBox.warning(self, "错误", f"文件不存在: {file_path}")
                return
            
            # 使用系统默认程序打开
            if platform.system() == 'Windows':
                os.startfile(str(file_path))
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', str(file_path)])
            else:  # Linux
                subprocess.call(['xdg-open', str(file_path)])
            
            logger.info(f"打开文档: {doc['filename']}")
        
        except Exception as e:
            logger.error(f"打开文档失败: {e}")
            QMessageBox.critical(self, "错误", f"打开文档失败: {str(e)}")
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        if self.table.rowCount() == 0:
            return
        
        menu = QMenu(self)
        
        # 获取选中的文档
        selected_rows = self.table.selectionModel().selectedRows()
        selected_ids = [
            self.table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
            for row in selected_rows
        ]
        
        if len(selected_ids) == 0:
            return
        
        # 打开
        if len(selected_ids) == 1:
            open_action = QAction("打开", self)
            open_action.triggered.connect(lambda: self.open_document(selected_ids[0]))
            menu.addAction(open_action)
            
            menu.addSeparator()
        
        # 添加到分类
        add_category_action = QAction("添加到分类...", self)
        add_category_action.triggered.connect(lambda: self.add_to_category(selected_ids))
        menu.addAction(add_category_action)
        
        # 添加标签
        add_tag_action = QAction("添加标签...", self)
        add_tag_action.triggered.connect(lambda: self.add_tags(selected_ids))
        menu.addAction(add_tag_action)
        
        menu.addSeparator()
        
        # 批量操作
        if len(selected_ids) > 1:
            batch_action = QAction(f"批量操作 ({len(selected_ids)} 个文档)...", self)
            batch_action.triggered.connect(lambda: self.batch_operation(selected_ids))
            menu.addAction(batch_action)
            
            menu.addSeparator()
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_documents(selected_ids))
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self.table.viewport().mapToGlobal(pos))
    
    def add_to_category(self, document_ids):
        """添加到分类"""
        from gui.dialogs.batch_operation_dialog import BatchOperationDialog
        
        main_window = self.get_main_window()
        if not main_window:
            return
        
        dialog = BatchOperationDialog(
            main_window.db,
            main_window.library_id,
            document_ids,
            self
        )
        
        if dialog.exec():
            self.documents_updated.emit()
    
    def add_tags(self, document_ids):
        """添加标签"""
        from gui.dialogs.batch_operation_dialog import BatchOperationDialog
        
        main_window = self.get_main_window()
        if not main_window:
            return
        
        dialog = BatchOperationDialog(
            main_window.db,
            main_window.library_id,
            document_ids,
            self
        )
        
        if dialog.exec():
            self.documents_updated.emit()
    
    def batch_operation(self, document_ids):
        """批量操作"""
        from gui.dialogs.batch_operation_dialog import BatchOperationDialog
        
        main_window = self.get_main_window()
        if not main_window:
            return
        
        dialog = BatchOperationDialog(
            main_window.db,
            main_window.library_id,
            document_ids,
            self
        )
        
        if dialog.exec():
            self.documents_updated.emit()
    
    def delete_documents(self, document_ids):
        """删除文档"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {len(document_ids)} 个文档吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from core.document import DocumentManager
            
            main_window = self.get_main_window()
            if not main_window:
                return
            
            doc_manager = DocumentManager(main_window.db, main_window.library_id)
            
            for doc_id in document_ids:
                try:
                    doc_manager.delete(doc_id)
                except Exception as e:
                    logger.error(f"删除文档失败: {e}")
            
            QMessageBox.information(self, "完成", f"已删除 {len(document_ids)} 个文档")
            self.documents_updated.emit()
    
    def get_selected_document_ids(self):
        """获取选中的文档ID列表"""
        selected_rows = self.table.selectionModel().selectedRows()
        return [
            self.table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
            for row in selected_rows
        ]
    
    def switch_view(self, view_type):
        """切换视图"""
        # TODO: 实现网格视图
        self.current_view = view_type
        logger.info(f"切换到 {view_type} 视图")