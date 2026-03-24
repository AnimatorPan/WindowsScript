"""
批量操作对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QListWidget, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import Qt
import logging

from core.category import CategoryManager
from core.tag import TagManager

logger = logging.getLogger(__name__)


class BatchOperationDialog(QDialog):
    """批量操作对话框"""
    
    def __init__(self, db, library_id, document_ids, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.document_ids = document_ids
        
        self.cat_manager = CategoryManager(db, library_id)
        self.tag_manager = TagManager(db, library_id)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"批量操作 - {len(self.document_ids)} 个文档")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明
        info_label = QLabel(f"已选择 {len(self.document_ids)} 个文档")
        layout.addWidget(info_label)
        
        # 操作选择
        operation_layout = QHBoxLayout()
        operation_layout.addWidget(QLabel("操作类型:"))
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "添加到分类",
            "添加标签",
            "移除标签",
            "删除文档"
        ])
        self.operation_combo.currentIndexChanged.connect(self.on_operation_changed)
        operation_layout.addWidget(self.operation_combo)
        
        layout.addLayout(operation_layout)
        
        # 选择区域
        self.selection_label = QLabel("选择分类:")
        layout.addWidget(self.selection_label)
        
        self.selection_list = QListWidget()
        layout.addWidget(self.selection_list)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.execute_btn = QPushButton("执行")
        self.execute_btn.clicked.connect(self.execute_operation)
        button_layout.addWidget(self.execute_btn)
        
        layout.addLayout(button_layout)
        
        # 加载初始数据
        self.on_operation_changed()
    
    def on_operation_changed(self):
        """操作类型变化"""
        operation = self.operation_combo.currentText()
        
        self.selection_list.clear()
        
        if operation in ["添加到分类"]:
            self.selection_label.setText("选择分类:")
            self.load_categories()
        elif operation in ["添加标签", "移除标签"]:
            self.selection_label.setText("选择标签:")
            self.load_tags()
        elif operation == "删除文档":
            self.selection_label.setText("确认删除:")
            self.selection_list.setVisible(False)
        else:
            self.selection_list.setVisible(True)
    
    def load_categories(self):
        """加载分类"""
        try:
            categories = self.cat_manager.list_all()
            
            for category in categories:
                self.selection_list.addItem(category['name'])
                item = self.selection_list.item(self.selection_list.count() - 1)
                item.setData(Qt.ItemDataRole.UserRole, category['id'])
        
        except Exception as e:
            logger.error(f"加载分类失败: {e}")
    
    def load_tags(self):
        """加载标签"""
        try:
            tags = self.tag_manager.list_all()
            
            for tag in tags:
                self.selection_list.addItem(tag['name'])
                item = self.selection_list.item(self.selection_list.count() - 1)
                item.setData(Qt.ItemDataRole.UserRole, tag['id'])
        
        except Exception as e:
            logger.error(f"加载标签失败: {e}")
    
    def execute_operation(self):
        """执行操作"""
        operation = self.operation_combo.currentText()
        
        if operation == "删除文档":
            self.delete_documents()
        else:
            selected_item = self.selection_list.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "提示", "请选择一个选项")
                return
            
            target_id = selected_item.data(Qt.ItemDataRole.UserRole)
            
            if operation == "添加到分类":
                self.add_to_category(target_id)
            elif operation == "添加标签":
                self.add_tags(target_id)
            elif operation == "移除标签":
                self.remove_tags(target_id)
    
    def add_to_category(self, category_id):
        """添加到分类"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.document_ids))
        
        success_count = 0
        
        for i, doc_id in enumerate(self.document_ids):
            try:
                self.cat_manager.add_document(category_id, doc_id)
                success_count += 1
            except Exception as e:
                logger.error(f"添加文档到分类失败: {e}")
            
            self.progress_bar.setValue(i + 1)
        
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(
            self,
            "完成",
            f"成功将 {success_count} 个文档添加到分类"
        )
        
        self.accept()
    
    def add_tags(self, tag_id):
        """添加标签"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.document_ids))
        
        success_count = 0
        
        for i, doc_id in enumerate(self.document_ids):
            try:
                self.tag_manager.add_to_document(tag_id, doc_id)
                success_count += 1
            except Exception as e:
                logger.error(f"添加标签失败: {e}")
            
            self.progress_bar.setValue(i + 1)
        
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(
            self,
            "完成",
            f"成功为 {success_count} 个文档添加标签"
        )
        
        self.accept()
    
    def remove_tags(self, tag_id):
        """移除标签"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.document_ids))
        
        success_count = 0
        
        for i, doc_id in enumerate(self.document_ids):
            try:
                self.tag_manager.remove_from_document(tag_id, doc_id)
                success_count += 1
            except Exception as e:
                logger.error(f"移除标签失败: {e}")
            
            self.progress_bar.setValue(i + 1)
        
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(
            self,
            "完成",
            f"成功为 {success_count} 个文档移除标签"
        )
        
        self.accept()
    
    def delete_documents(self):
        """删除文档"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {len(self.document_ids)} 个文档吗？\n\n"
            "此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from core.document import DocumentManager
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(self.document_ids))
            
            doc_manager = DocumentManager(self.db, self.library_id)
            success_count = 0
            
            for i, doc_id in enumerate(self.document_ids):
                try:
                    doc_manager.delete(doc_id)
                    success_count += 1
                except Exception as e:
                    logger.error(f"删除文档失败: {e}")
                
                self.progress_bar.setValue(i + 1)
            
            self.progress_bar.setVisible(False)
            
            QMessageBox.information(
                self,
                "完成",
                f"成功删除 {success_count} 个文档"
            )
            
            self.accept()