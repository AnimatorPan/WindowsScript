"""
分类管理对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QTextEdit,
    QLabel, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
import logging

from core.category import CategoryManager

logger = logging.getLogger(__name__)


class CategoryDialog(QDialog):
    """分类管理对话框"""
    
    def __init__(self, db, library_id, parent=None):
        super().__init__(parent)
        
        self.db = db
        self.library_id = library_id
        self.cat_manager = CategoryManager(db, library_id)
        
        self.init_ui()
        self.load_categories()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("分类管理")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加分类")
        add_btn.clicked.connect(self.add_category)
        toolbar_layout.addWidget(add_btn)
        
        add_sub_btn = QPushButton("添加子分类")
        add_sub_btn.clicked.connect(self.add_subcategory)
        toolbar_layout.addWidget(add_sub_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_category)
        toolbar_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_category)
        toolbar_layout.addWidget(delete_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 分类树
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["分类名称", "描述"])
        self.tree.setColumnWidth(0, 300)
        layout.addWidget(self.tree)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_categories(self):
        """加载分类树"""
        self.tree.clear()
        
        try:
            categories = self.cat_manager.get_tree()
            
            for category in categories:
                self.add_tree_item(None, category)
            
            self.tree.expandAll()
        
        except Exception as e:
            logger.error(f"加载分类失败: {e}")
            QMessageBox.critical(self, "错误", f"加载分类失败: {str(e)}")
    
    def add_tree_item(self, parent_item, category):
        """递归添加树节点"""
        if parent_item is None:
            item = QTreeWidgetItem(self.tree)
        else:
            item = QTreeWidgetItem(parent_item)
        
        item.setText(0, category['name'])
        item.setText(1, category.get('description', ''))
        item.setData(0, Qt.ItemDataRole.UserRole, category['id'])
        
        # 添加子分类
        for child in category.get('children', []):
            self.add_tree_item(item, child)
    
    def add_category(self):
        """添加分类"""
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称:")
        
        if ok and name:
            try:
                self.cat_manager.create(name)
                self.load_categories()
                QMessageBox.information(self, "成功", "分类创建成功")
            except Exception as e:
                logger.error(f"创建分类失败: {e}")
                QMessageBox.critical(self, "错误", f"创建分类失败: {str(e)}")
    
    def add_subcategory(self):
        """添加子分类"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择父分类")
            return
        
        parent_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        name, ok = QInputDialog.getText(self, "添加子分类", "子分类名称:")
        
        if ok and name:
            try:
                self.cat_manager.create(name, parent_id=parent_id)
                self.load_categories()
                QMessageBox.information(self, "成功", "子分类创建成功")
            except Exception as e:
                logger.error(f"创建子分类失败: {e}")
                QMessageBox.critical(self, "错误", f"创建子分类失败: {str(e)}")
    
    def edit_category(self):
        """编辑分类"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要编辑的分类")
            return
        
        category_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        old_name = current_item.text(0)
        
        name, ok = QInputDialog.getText(self, "编辑分类", "分类名称:", text=old_name)
        
        if ok and name:
            try:
                self.cat_manager.update(category_id, name=name)
                self.load_categories()
                QMessageBox.information(self, "成功", "分类更新成功")
            except Exception as e:
                logger.error(f"更新分类失败: {e}")
                QMessageBox.critical(self, "错误", f"更新分类失败: {str(e)}")
    
    def delete_category(self):
        """删除分类"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要删除的分类")
            return
        
        category_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        category_name = current_item.text(0)
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除分类 '{category_name}' 吗？\n\n"
            "注意：子分类将被移到根级别",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cat_manager.delete(category_id, cascade=False)
                self.load_categories()
                QMessageBox.information(self, "成功", "分类删除成功")
            except Exception as e:
                logger.error(f"删除分类失败: {e}")
                QMessageBox.critical(self, "错误", f"删除分类失败: {str(e)}")