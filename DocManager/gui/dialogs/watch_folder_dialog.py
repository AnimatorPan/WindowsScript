"""
监控文件夹配置对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QCheckBox, QFileDialog,
    QMessageBox, QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtCore import Qt
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WatchFolderDialog(QDialog):
    """监控文件夹配置对话框"""
    
    def __init__(self, db, library_id, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        
        self.init_ui()
        self.load_watched_folders()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("文件夹监控配置")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明
        info_label = QLabel(
            "配置需要监控的文件夹，系统会自动导入这些文件夹中新增的文件。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 监控列表
        layout.addWidget(QLabel("当前监控的文件夹:"))
        
        self.folder_list = QListWidget()
        layout.addWidget(self.folder_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加监控")
        add_btn.clicked.connect(self.add_watch)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("移除监控")
        remove_btn.clicked.connect(self.remove_watch)
        btn_layout.addWidget(remove_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_watch)
        btn_layout.addWidget(edit_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_watched_folders(self):
        """加载监控文件夹列表"""
        self.folder_list.clear()
        
        try:
            sql = """
                SELECT * FROM watched_folders 
                WHERE library_id = ?
                ORDER BY created_at DESC
            """
            folders = self.db.fetch_all(sql, (self.library_id,))
            
            for folder in folders:
                status = "✓" if folder['is_active'] else "✗"
                auto = "自动" if folder['auto_import'] else "手动"
                sub = "+子文件夹" if folder['include_subfolders'] else ""
                
                text = f"{status} {folder['path']} ({auto} {sub})"
                
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, folder['id'])
                self.folder_list.addItem(item)
            
            logger.info(f"加载了 {len(folders)} 个监控文件夹")
        
        except Exception as e:
            logger.error(f"加载监控文件夹失败: {e}")
    
    def add_watch(self):
        """添加监控"""
        dialog = AddWatchFolderDialog(self.db, self.library_id, self)
        if dialog.exec():
            self.load_watched_folders()
    
    def remove_watch(self):
        """移除监控"""
        current_item = self.folder_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请选择要移除的监控文件夹")
            return
        
        folder_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要移除此监控吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                sql = "DELETE FROM watched_folders WHERE id = ?"
                self.db.delete(sql, (folder_id,))
                
                self.load_watched_folders()
                QMessageBox.information(self, "成功", "监控已移除")
            
            except Exception as e:
                logger.error(f"移除监控失败: {e}")
                QMessageBox.critical(self, "错误", f"移除失败:\n\n{str(e)}")
    
    def edit_watch(self):
        """编辑监控"""
        current_item = self.folder_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请选择要编辑的监控文件夹")
            return
        
        folder_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        # 获取当前配置
        sql = "SELECT * FROM watched_folders WHERE id = ?"
        folder = self.db.fetch_one(sql, (folder_id,))
        
        if folder:
            dialog = AddWatchFolderDialog(self.db, self.library_id, self, folder)
            if dialog.exec():
                self.load_watched_folders()


class AddWatchFolderDialog(QDialog):
    """添加/编辑监控文件夹对话框"""
    
    def __init__(self, db, library_id, parent=None, folder_data=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.folder_data = folder_data
        
        self.init_ui()
        
        if folder_data:
            self.load_folder_data()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("添加监控文件夹" if not self.folder_data else "编辑监控文件夹")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # 路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)
        
        form_layout.addRow("监控路径:", path_layout)
        
        # 选项
        self.auto_import = QCheckBox("自动导入新文件")
        self.auto_import.setChecked(True)
        form_layout.addRow("", self.auto_import)
        
        self.include_subfolders = QCheckBox("包含子文件夹")
        self.include_subfolders.setChecked(True)
        form_layout.addRow("", self.include_subfolders)
        
        self.is_active = QCheckBox("启用监控")
        self.is_active.setChecked(True)
        form_layout.addRow("", self.is_active)
        
        # 文件模式
        self.patterns_edit = QLineEdit()
        self.patterns_edit.setPlaceholderText("留空表示所有文件，例如: *.pdf,*.docx")
        form_layout.addRow("文件过滤:", self.patterns_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.on_ok)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.on_cancel)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    