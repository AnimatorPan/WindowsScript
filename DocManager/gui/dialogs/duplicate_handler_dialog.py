"""
去重处理对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox,
    QGroupBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import logging

logger = logging.getLogger(__name__)


class DuplicateHandlerDialog(QDialog):
    """去重处理对话框"""
    
    documents_updated = pyqtSignal()
    
    def __init__(self, db, library_id, duplicate_groups, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.duplicate_groups = duplicate_groups
        self.current_group_index = 0
        
        self.setWindowTitle("重复文档处理")
        self.setMinimumSize(900, 600)
        
        self.init_ui()
        self.load_current_group()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🔄 重复文档处理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 进度信息
        self.progress_label = QLabel()
        layout.addWidget(self.progress_label)
        
        # 当前组信息
        group_box = QGroupBox("当前重复组")
        group_layout = QVBoxLayout(group_box)
        
        self.group_info_label = QLabel()
        self.group_info_label.setStyleSheet("color: #888;")
        group_layout.addWidget(self.group_info_label)
        
        # 文档表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "选择保留", "文件名", "类型", "大小", "导入时间", "路径"
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        group_layout.addWidget(self.table)
        
        layout.addWidget(group_box)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        self.keep_selected_btn = QPushButton("保留选中，删除其他")
        self.keep_selected_btn.clicked.connect(self.keep_selected)
        action_layout.addWidget(self.keep_selected_btn)
        
        self.keep_all_btn = QPushButton("全部保留")
        self.keep_all_btn.clicked.connect(self.keep_all)
        action_layout.addWidget(self.keep_all_btn)
        
        self.skip_btn = QPushButton("跳过此组")
        self.skip_btn.clicked.connect(self.skip_group)
        action_layout.addWidget(self.skip_btn)
        
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("上一组")
        self.prev_btn.clicked.connect(self.prev_group)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("下一组")
        self.next_btn.clicked.connect(self.next_group)
        nav_layout.addWidget(self.next_btn)
        
        nav_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        nav_layout.addWidget(close_btn)
        
        layout.addLayout(nav_layout)
    
    def load_current_group(self):
        """加载当前重复组"""
        if not self.duplicate_groups:
            self.progress_label.setText("没有重复文档")
            self.table.setRowCount(0)
            return
        
        total = len(self.duplicate_groups)
        self.progress_label.setText(f"第 {self.current_group_index + 1} 组 / 共 {total} 组")
        
        group = self.duplicate_groups[self.current_group_index]
        
        # 显示组信息
        self.group_info_label.setText(
            f"发现 {len(group)} 个重复文档（内容相同）"
        )
        
        # 填充表格
        self.table.setRowCount(len(group))
        self.button_group = QButtonGroup(self)
        
        for row, doc in enumerate(group):
            # 单选按钮（选择保留）
            radio = QRadioButton()
            if row == 0:
                radio.setChecked(True)
            self.button_group.addButton(radio, row)
            self.table.setCellWidget(row, 0, radio)
            
            # 文件名
            name_item = QTableWidgetItem(doc['filename'])
            self.table.setItem(row, 1, name_item)
            
            # 类型
            type_item = QTableWidgetItem(doc.get('file_type', '未知'))
            self.table.setItem(row, 2, type_item)
            
            # 大小
            size = doc.get('file_size', 0)
            size_item = QTableWidgetItem(self.format_size(size))
            self.table.setItem(row, 3, size_item)
            
            # 导入时间
            date_item = QTableWidgetItem(str(doc.get('imported_at', '')))
            self.table.setItem(row, 4, date_item)
            
            # 路径
            path_item = QTableWidgetItem(doc.get('filepath', ''))
            self.table.setItem(row, 5, path_item)
            
            # 存储文档ID
            for col in range(6):
                item = self.table.item(row, col) if col > 0 else None
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, doc['id'])
        
        # 更新导航按钮状态
        self.prev_btn.setEnabled(self.current_group_index > 0)
        self.next_btn.setEnabled(self.current_group_index < total - 1)
    
    def format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def keep_selected(self):
        """保留选中，删除其他"""
        if not self.duplicate_groups:
            return
        
        group = self.duplicate_groups[self.current_group_index]
        selected_row = self.button_group.checkedId()
        
        if selected_row < 0:
            QMessageBox.warning(self, "提示", "请选择要保留的文档")
            return
        
        keep_doc = group[selected_row]
        delete_docs = [doc for i, doc in enumerate(group) if i != selected_row]
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定保留 '{keep_doc['filename']}'，删除其他 {len(delete_docs)} 个文档吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.document import DocumentManager
                
                doc_manager = DocumentManager(self.db, self.library_id)
                
                for doc in delete_docs:
                    doc_manager.delete(doc['id'])
                    logger.info(f"删除重复文档: {doc['filename']}")
                
                QMessageBox.information(self, "成功", f"已删除 {len(delete_docs)} 个重复文档")
                self.documents_updated.emit()
                self.remove_current_group()
                
            except Exception as e:
                logger.error(f"删除重复文档失败: {e}")
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def keep_all(self):
        """全部保留"""
        reply = QMessageBox.question(
            self, "确认保留",
            "确定保留当前组的所有文档吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_current_group()
    
    def skip_group(self):
        """跳过此组"""
        self.remove_current_group()
    
    def remove_current_group(self):
        """移除当前组并加载下一组"""
        self.duplicate_groups.pop(self.current_group_index)
        
        if self.current_group_index >= len(self.duplicate_groups):
            self.current_group_index = max(0, len(self.duplicate_groups) - 1)
        
        if not self.duplicate_groups:
            QMessageBox.information(self, "完成", "所有重复文档已处理完毕")
            self.accept()
        else:
            self.load_current_group()
    
    def prev_group(self):
        """上一组"""
        if self.current_group_index > 0:
            self.current_group_index -= 1
            self.load_current_group()
    
    def next_group(self):
        """下一组"""
        if self.current_group_index < len(self.duplicate_groups) - 1:
            self.current_group_index += 1
            self.load_current_group()
